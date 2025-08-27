from google.cloud import documentai_v1 as documentai
from dotenv import load_dotenv
from typing import Dict, Any
import tempfile
from io import BytesIO
import os

# ===== defnine constants =====
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")
PROCESSOR_ID = os.getenv("GCP_PROCESSOR_ID")


PDF_MIME = "application/pdf"
TXT_MIME = "text/plain"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
SUPPORTED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/tiff", "image/gif"}

# ===== GCP Client Setup =====
def _processor_name() -> str:
    assert PROJECT_ID, "Set GCP_PROJECT_ID"
    assert PROCESSOR_ID, "Set GCP_PROCESSOR_ID (Layout Parser processor)"

    return f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

def _client() -> documentai.DocumentProcessorServiceClient:

    return documentai.DocumentProcessorServiceClient()


# ===== Process and parse input =====
def _process_with_layout(file_bytes: bytes, mime_type: str) -> documentai.Document:
    client = _client()
    name = _processor_name()

    process_options = documentai.ProcessOptions(
        layout_config=documentai.ProcessOptions.LayoutConfig(
            chunking_config=documentai.ProcessOptions.LayoutConfig.ChunkingConfig(
                chunk_size=1000,               
                include_ancestor_headings=True
            )
        )
    )

    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(content=file_bytes, mime_type=mime_type),
        process_options=process_options,
    )
    result = client.process_document(request=request)
    return result.document  

# ===== Convert docx to pdf bytes =====
def _docx_to_pdf(file_bytes: bytes) -> bytes:
    """
    Try converting DOCX -> PDF for better layout fidelity with Layout Parser.
    Strategy:
      1) Aspose.Words
      2) docx2pdf 
      3) Fallback: naive text extraction
    """
    # Option A: Aspose.Words
    try:
        import aspose.words as aw  
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f_in:
            f_in.write(file_bytes)
            in_path = f_in.name
        out_path = in_path[:-5] + ".pdf"
        doc = aw.Document(in_path)
        doc.save(out_path)
        with open(out_path, "rb") as f_out:
            pdf_bytes = f_out.read()
        try:
            os.remove(in_path)
            os.remove(out_path)
        except Exception:
            pass
        return pdf_bytes
    except Exception:
        pass

    # Option B: docx2pdf
    try:
        from docx2pdf import convert  # type: ignore
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f_in:
            f_in.write(file_bytes)
            in_path = f_in.name
        out_path = in_path[:-5] + ".pdf"
        convert(in_path, out_path)
        with open(out_path, "rb") as f_out:
            pdf_bytes = f_out.read()
        try:
            os.remove(in_path)
            os.remove(out_path)
        except Exception:
            pass
        return pdf_bytes
    except Exception as e:
        raise RuntimeError(f"DOCX->PDF conversion failed: {e}")
    

def _docx_text_fallback(file_bytes: bytes) -> str:
    # As a last resort, extract text without layout (for MVP continuity)
    try:
        import docx  # python-docx
        doc = docx.Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        raise RuntimeError(f"DOCX text extraction failed: {e}")
    
def _text_from_layout(full_text: str, layout) -> str:
    if not layout or not layout.text_anchor or not layout.text_anchor.text_segments:
        return ""
    parts = []
    for seg in layout.text_anchor.text_segments:
        start = int(seg.start_index) if seg.start_index is not None else 0
        end = int(seg.end_index) if seg.end_index is not None else 0
        parts.append(full_text[start:end])
    return "".join(parts)

def _cleanup_text(s: str) -> str:
    import re
    s = re.sub(r"(\w)-\n(\w)", r"\1\2", s)   # de-hyphenate at line breaks
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()

def _simple_paragraph_split(text: str):
    import re
    chunks = re.split(r"\n\s*\n|(?<=[.!?])\s+\n?", text)
    return [c.strip() for c in chunks if c.strip()]

def _simple_blocks(text: str):
    return [{"id": i, "text": t, "type": "paragraph", "page": 1} for i, t in enumerate(_simple_paragraph_split(text), 1)]

def _map_layout_to_blocks(doc: documentai.Document) -> Dict[str, Any]:
    """
    Prefer Layout Parser's chunked_document if present.
    Fallback to page paragraphs/blocks if needed.
    """
    full_text = doc.text or ""
    blocks = []
    id_counter = 1

    # 1) Use chunked_document chunks if available (ideal for rewriting)
    chunked = getattr(doc, "chunked_document", None)
    if chunked and getattr(chunked, "chunks", None):
        for ch in chunked.chunks:
            txt = _text_from_layout(full_text, ch.layout)
            txt = _cleanup_text(txt)
            if txt:
                # page index might not be present on chunk; we can omit or infer later
                blocks.append({"id": id_counter, "text": txt, "type": "chunk", "page": getattr(ch.layout, "page_number", 0)})
                id_counter += 1

    # 2) If no chunks, fall back to page paragraphs/blocks
    if not blocks and getattr(doc, "pages", None):
        for p_index, page in enumerate(doc.pages):
            para_list = getattr(page, "paragraphs", []) or getattr(page, "blocks", [])
            for para in para_list:
                txt = _text_from_layout(full_text, para.layout)
                txt = _cleanup_text(txt)
                if txt:
                    blocks.append({"id": id_counter, "text": txt, "type": "paragraph", "page": p_index + 1})
                    id_counter += 1

    # 3) Last resort: split full text
    if not blocks and full_text:
        for t in _simple_paragraph_split(full_text):
            blocks.append({"id": id_counter, "text": t, "type": "paragraph", "page": 1})
            id_counter += 1

    return {"full_text": full_text, "blocks": blocks}

# --- Public entry point ---

def extract_text_and_blocks(file_bytes: bytes, filename: str, content_type: str | None) -> Dict[str, Any]:
    """
    Always uses the Layout Parser processor when sending documents to Document AI.
    - PDF/images: send directly.
    - DOCX: convert to PDF (preferred), else text fallback.
    - TXT: use as-is, no OCR.
    Returns dict with full_text and normalized blocks for the frontend.
    """
    ext = (os.path.splitext(filename)[1] or "").lower()
    mime = (content_type or "").lower()

    # Normalize MIME by extension when missing or generic
    if ext == ".pdf":
        mime = PDF_MIME
    elif ext == ".txt":
        mime = TXT_MIME
    elif ext == ".docx":
        mime = DOCX_MIME
    elif ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif ext == ".png":
        mime = "image/png"
    elif ext in [".tif", ".tiff"]:
        mime = "image/tiff"

    # TXT: bypass OCR
    if mime == TXT_MIME:
        text = file_bytes.decode("utf-8", errors="replace")
        return {"full_text": text, "blocks": _simple_blocks(text)}

    # DOCX: convert to PDF for best results with Layout Parser
    if mime == DOCX_MIME:
        try:
            pdf_bytes = _docx_to_pdf(file_bytes)
            doc = _process_with_layout(pdf_bytes, PDF_MIME)
            return _map_layout_to_blocks(doc)
        except Exception:
            # Fallback: naive DOCX text extraction
            text = _docx_text_fallback(file_bytes)
            return {"full_text": text, "blocks": _simple_blocks(text)}

    # PDFs and supported images: send directly
    if mime == PDF_MIME or mime in SUPPORTED_IMAGE_MIMES:
        doc = _process_with_layout(file_bytes, mime)
        return _map_layout_to_blocks(doc)

    # Unknown: try as PDF; if that fails, treat as text
    try:
        doc = _process_with_layout(file_bytes, PDF_MIME)
        return _map_layout_to_blocks(doc)
    except Exception:
        text = file_bytes.decode("utf-8", errors="replace")
        return {"full_text": text, "blocks": _simple_blocks(text)}
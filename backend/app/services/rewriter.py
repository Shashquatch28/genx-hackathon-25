# backend/services/rewriter.py
import os
import re
import time
from typing import List, Tuple

# MODIFIED: Import the unified library
from google.cloud import aiplatform
# REMOVED: The problematic import from google.generativeai.types is gone.

from dotenv import load_dotenv

load_dotenv()

# --- Standardized Initialization ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("DAI_GCP_LOCATION")

if not PROJECT_ID:
    raise RuntimeError("Missing project id: set GCP_PROJECT_ID in .env")

aiplatform.init(project=PROJECT_ID, location=LOCATION)

# --- The rest of the file is the same, except for the _call_model function ---

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
MAX_CHARS = 8000
CHUNK_OVERLAP = 200

def _clean(text: str) -> str:
    if not text:
        return ""
    return _CONTROL_RE.sub("", text)

def _split_with_overlap(text: str, max_len: int = MAX_CHARS, overlap: int = CHUNK_OVERLAP) -> List[str]:
    # This entire splitting function is unchanged...
    text = text.strip()
    if len(text) <= max_len:
        return [text]
    for pattern in [r"\n\n+", r"\n+", r"(?<=[\.!?])\s+", r"\s+"]:
        parts = re.split(pattern, text)
        if len(parts) == 1:
            continue
        chunks: List[str] = []
        buf = ""
        for part in parts:
            candidate = (buf + (" " if buf else "") + part).strip()
            if len(candidate) <= max_len:
                buf = candidate
            else:
                if buf:
                    chunks.append(buf)
                if len(part) > max_len:
                    chunks.extend(_split_with_overlap(part, max_len, overlap))
                    buf = ""
                else:
                    buf = part
        if buf:
            chunks.append(buf)
        if len(chunks) > 1 and overlap > 0:
            with_overlap: List[str] = []
            for i, c in enumerate(chunks):
                if i == 0:
                    with_overlap.append(c)
                else:
                    prev_tail = chunks[i-1][-overlap:]
                    with_overlap.append((prev_tail + c)[:max_len])
            return with_overlap
        return chunks
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + max_len, len(text))
        chunk = text[i:end]
        chunks.append(chunk)
        if end == len(text):
            break
        i = end - overlap if overlap > 0 else end
        if i < 0:
            i = 0
    return chunks

LAYMAN_SYSTEM = (
    "You are an expert plain-language editor..."
)

def _build_prompt(clean: str) -> str:
    return (
        f"{LAYMAN_SYSTEM}\n\n"
        "Task: Rewrite the following text for a general audience..."
        f"<text>\n{clean}\n</text>"
    )

def _call_model(prompt: str, model_name: str, temperature: float) -> str:
    model = aiplatform.GenerativeModel(model_name)
    
    # --- MODIFIED: This is the only other change ---
    # Instead of importing GenerationConfig, we pass the parameters as a simple dictionary.
    generation_config = {
        "temperature": temperature,
    }
    
    resp = model.generate_content(contents=prompt, generation_config=generation_config)
    return (getattr(resp, "text", None) or "").strip()

def rewrite_text(
    text: str,
    mode: str = "layman",
    model: str = "gemini-1.5-flash",
    temperature: float = 0.3,
) -> Tuple[str, dict]:
    # This function is unchanged...
    t0 = time.time()
    cleaned = _clean(text)
    if not cleaned.strip():
        return "", { "model": model, "latency_ms": 0, "input_len": 0, "output_len": 0, "location": LOCATION, "chunks": 0, "chunked": False, "overlap": CHUNK_OVERLAP }
    chunks = _split_with_overlap(cleaned, MAX_CHARS, CHUNK_OVERLAP)
    outputs: List[str] = []
    for idx, ch in enumerate(chunks, start=1):
        prompt = _build_prompt(ch)
        out = _call_model(prompt, model, temperature)
        if not out:
            out = "(No rewrite produced for this segment.)"
        outputs.append(out)
    joined = "\n\n".join(outputs).strip()
    meta = { "model": model, "latency_ms": int((time.time() - t_0) * 1000), "input_len": len(cleaned), "output_len": len(joined), "location": LOCATION, "chunks": len(chunks), "chunked": len(chunks) > 1, "overlap": CHUNK_OVERLAP, "max_chars": MAX_CHARS, }
    return joined, meta
# backend/services/rewriter.py
from dotenv import load_dotenv
from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig
import os
import re
import time
from typing import List, Tuple

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = (
    os.getenv("VAI_GCP_LOCATION")
    or os.getenv("VERTEX_GENAI_LOCATION")
    or os.getenv("GOOGLE_CLOUD_LOCATION")
    or "global"
)

creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if creds_path:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

if not PROJECT_ID:
    raise RuntimeError("Missing project id: set GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT in .env")

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
    http_options=HttpOptions(api_version="v1"),
)

# Sanitation and limits
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
MAX_CHARS = 8000
CHUNK_OVERLAP = 200  # carry a bit of previous text for continuity

def _clean(text: str) -> str:
    if not text:
        return ""
    return _CONTROL_RE.sub("", text)

def _split_with_overlap(text: str, max_len: int = MAX_CHARS, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Recursive, content-aware splitter:
    1) Try paragraphs (\n\n), then lines (\n), then sentences (.!?), then spaces.
    2) If still too long, hard-slice.
    3) Add overlap between consecutive chunks for continuity.
    """
    text = text.strip()
    if len(text) <= max_len:
        return [text]

    def split_by(sep_pattern: str, s: str) -> List[str]:
        parts = re.split(sep_pattern, s)
        # Reattach separators to preserve punctuation/newlines roughly
        result = []
        acc = ""
        for i, p in enumerate(parts):
            if i < len(parts) - 1:
                # For sentence split, add the matched punctuation back
                m = re.search(sep_pattern, s)
            result.append(p)
        return parts

    # Try hierarchical split order
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
                # If single part is still larger than max, recurse
                if len(part) > max_len:
                    chunks.extend(_split_with_overlap(part, max_len, overlap))
                    buf = ""
                else:
                    buf = part
        if buf:
            chunks.append(buf)

        # Insert overlaps
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

    # Fallback: hard-slice with overlap
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
    "You are an expert plain-language editor specializing in legal and technical documents. "
    "Rewrite the input into clear, everyday English while strictly preserving the original meaning, parties, "
    "obligations, conditions, dates, and numbers. Do not add or infer facts or change defined terms. "
    "Avoid legalese and jargon; keep the tone professional, neutral, and precise. "
    "If a technical/defined term must remain, keep it and add a brief parenthetical clarification. "
    "If simplification would change meaning, keep wording close to the original. Prioritize accuracy."
)

def _build_prompt(clean: str) -> str:
    return (
        f"{LAYMAN_SYSTEM}\n\n"
        "Task: Rewrite the following text for a general audience using plain English. "
        "Preserve all parties, rights, obligations, amounts, conditions, deadlines, and numbers. "
        "If a technical/legal term is critical, keep it and add a short clarification in parentheses. "
        "Favor precision over oversimplification. Limit the output to 1–3 concise sentences unless the input is inherently a list.\n\n"
        f"<text>\n{clean}\n</text>"
    )

def _call_model(prompt: str, model: str, temperature: float) -> str:
    config = GenerateContentConfig(temperature=temperature)
    resp = client.models.generate_content(model=model, contents=prompt, config=config)
    return (getattr(resp, "text", None) or "").strip()

def rewrite_text(
    text: str,
    mode: str = "layman",
    model: str = "gemini-2.5-flash",
    temperature: float = 0.3,
) -> Tuple[str, dict]:
    t0 = time.time()
    cleaned = _clean(text)
    if not cleaned.strip():
        return "", {
            "model": model,
            "latency_ms": int((time.time() - t0) * 1000),
            "input_len": 0,
            "output_len": 0,
            "location": LOCATION,
            "chunks": 0,
            "chunked": False,
            "overlap": CHUNK_OVERLAP,
        }

    chunks = _split_with_overlap(cleaned, MAX_CHARS, CHUNK_OVERLAP)
    outputs: List[str] = []
    for idx, ch in enumerate(chunks, start=1):
        prompt = _build_prompt(ch)
        out = _call_model(prompt, model, temperature)
        if not out:
            out = "(No rewrite produced for this segment.)"
        outputs.append(out)

    # Join with a clear separator to keep chunk boundaries visible to the user
    joined = "\n\n".join(outputs).strip()

    meta = {
        "model": model,
        "latency_ms": int((time.time() - t0) * 1000),
        "input_len": len(cleaned),
        "output_len": len(joined),
        "location": LOCATION,
        "chunks": len(chunks),
        "chunked": len(chunks) > 1,
        "overlap": CHUNK_OVERLAP,
        "max_chars": MAX_CHARS,
    }
    return joined, meta

if __name__ == "__main__":
    sample = ("The party of the first part bequeaths unto the party of the second part all chattels. " * 200)
    rewritten, meta = rewrite_text(sample)
    print("Rewritten:\n", rewritten[:500], "...\n")
    print("Meta:", meta)

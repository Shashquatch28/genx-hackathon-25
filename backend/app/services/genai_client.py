# backend/app/services/genai_client.py
from __future__ import annotations

import os
from typing import Optional, Dict, Any

# Google Gen AI SDK (unified client for Vertex AI or Developer API)
from google import genai

# Make typed helpers optional to avoid import-time crashes on older SDKs
try:
    from google.genai import types as genai_types  # type: ignore
    from google.genai.types import HttpOptions      # type: ignore
except Exception:  # pragma: no cover
    genai_types = None  # type: ignore[assignment]
    HttpOptions = None  # type: ignore[assignment]

# Cached client instance
_client: Optional[genai.Client] = None

def _read_env() -> Dict[str, str]:
    # Read env at call-time so values are present even if load_dotenv ran later
    return {
        "PROJECT": os.getenv("GCP_PROJECT_ID") or "",
        "LOCATION": (os.getenv("VAI_GCP_LOCATION") or "global").strip().lower(),
        "API_KEY": os.getenv("GOOGLE_API_KEY") or "",
        "MODEL": os.getenv("GENAI_MODEL") or "gemini-2.5-flash",
    }

def get_client() -> genai.Client:
    """
    Returns a configured Google Gen AI client.
    - Vertex AI mode (recommended): uses ADC from GOOGLE_APPLICATION_CREDENTIALS,
      project from GCP_PROJECT_ID, and location from VAI_GCP_LOCATION.
    - Developer API fallback: if PROJECT is missing but GOOGLE_API_KEY is set, uses API key.
    """
    global _client
    if _client is not None:
        return _client

    env = _read_env()
    use_vertex = bool(env["PROJECT"])

    http_kwargs: Dict[str, Any] = {}
    # Pass HttpOptions only if available in your installed SDK
    if HttpOptions is not None:
        try:
            http_kwargs["http_options"] = HttpOptions(api_version="v1")
        except Exception:
            pass  # continue without http_options on mismatched versions

    if use_vertex:
        _client = genai.Client(
            vertexai=True,
            project=env["PROJECT"],
            location=env["LOCATION"] or "global",
            **http_kwargs,
        )
        return _client

    if not env["API_KEY"]:
        raise RuntimeError(
            "Configure GCP_PROJECT_ID (Vertex) or GOOGLE_API_KEY (Developer API)."
        )

    _client = genai.Client(api_key=env["API_KEY"], **http_kwargs)
    return _client

def generate_content(prompt: str, *, model: Optional[str] = None, **config_kwargs) -> str:
    """
    Teammate-compatible helper:
    client.models.generate_content(model=..., contents=..., config=...) -> str response.text
    """
    client = get_client()
    model_name = model or _read_env()["MODEL"]

    config = None
    if genai_types is not None and config_kwargs:
        try:
            config = genai_types.GenerateContentConfig(**config_kwargs)  # type: ignore[attr-defined]
        except Exception:
            config = None

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )
    return getattr(resp, "text", "") or ""

def generate_content_stream(prompt: str, *, model: Optional[str] = None, **config_kwargs):
    """
    Streaming variant using client.models.generate_content_stream(...)
    Yields text chunks.
    """
    client = get_client()
    model_name = model or _read_env()["MODEL"]

    config = None
    if genai_types is not None and config_kwargs:
        try:
            config = genai_types.GenerateContentConfig(**config_kwargs)  # type: ignore[attr-defined]
        except Exception:
            config = None

    stream = client.models.generate_content_stream(
        model=model_name,
        contents=prompt,
        config=config,
    )
    for chunk in stream:
        text = getattr(chunk, "text", "")
        if text:
            yield text

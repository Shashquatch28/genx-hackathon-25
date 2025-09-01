# backend/app/services/genai_client.py

import os
from typing import Optional

# Google Gen AI SDK (unified client for Vertex AI or Developer API)
from google import genai
from google.genai.types import HttpOptions

# ---- Environment mapping (adapted to your .env) ----
# Required for Vertex AI:
#   GOOGLE_APPLICATION_CREDENTIALS = C:/keys/....json
#   GCP_PROJECT_ID                 = genai-exhange-hackathon
#   VAI_GCP_LOCATION               = global   # or us-central1, etc.
#
# Optional (only if intentionally using Developer API):
#   GOOGLE_API_KEY                 = <your-key>

PROJECT = os.getenv("GCP_PROJECT_ID")
LOCATION = (os.getenv("VAI_GCP_LOCATION") or "global").strip().lower()
API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

# Prefer Vertex AI (service account) unless only an API key is provided.
USE_VERTEX = True if PROJECT else False

# Cache the client so callers can import get_client() and reuse it
_client: Optional[genai.Client] = None

def get_client() -> genai.Client:
    """
    Returns a configured Google Gen AI client.
    - Vertex AI mode (recommended): uses service-account auth from GOOGLE_APPLICATION_CREDENTIALS,
      project from GCP_PROJECT_ID, and location from VAI_GCP_LOCATION (default 'global').
    - Developer API fallback: if PROJECT is missing but GOOGLE_API_KEY is set, uses API key mode.
    """
    global _client
    if _client is not None:
        return _client

    http_opts = HttpOptions(api_version="v1")  # use stable v1 endpoints

    if USE_VERTEX:
        if not PROJECT:
            raise RuntimeError("Missing GCP_PROJECT_ID for Vertex AI client creation.")
        # LOCATION must be a supported Vertex location, e.g. 'global' or 'us-central1'
        _client = genai.Client(
            vertexai=True,
            project=PROJECT,
            location=LOCATION or "global",
            http_options=http_opts,
        )
        return _client

    # Fallback to Developer API (only if explicitly configured)
    if not API_KEY:
        raise RuntimeError(
            "No Vertex project configured (GCP_PROJECT_ID missing) and no GOOGLE_API_KEY found. "
            "Set GCP_PROJECT_ID and VAI_GCP_LOCATION for Vertex, or set GOOGLE_API_KEY for Developer API."
        )

    _client = genai.Client(api_key=API_KEY, http_options=http_opts)
    return _client

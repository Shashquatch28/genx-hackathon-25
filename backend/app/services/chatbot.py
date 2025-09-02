# backend/app/services/chatbot_service.py
from __future__ import annotations

from google.genai.types import GenerateContentConfig
from .genai_client import get_client
from app.models import AskResponse

# Low-latency, Vertex-supported Gemini model id
MODEL_ID = "gemini-2.5-flash"

SYSTEM_INSTRUCTIONS = (
    "You are a helpful legal assistant. Answer ONLY using the provided contract text. "
    "If the answer is not in the text, reply exactly: 'The answer is not found in the document.' "
    "After the answer, include 1 to 3 short quotes from the text that support it."
    "Return a single concise sentence; do not repeat lines or include quoted echoes."
)

def answer_question(question: str, context: str, temperature: float = 0.2) -> AskResponse:
    """
    Single-turn QA grounded on the given contract context.
    """
    client = get_client()
    cfg = GenerateContentConfig(temperature=temperature)

    prompt = f"""{SYSTEM_INSTRUCTIONS}

Contract Text:
---
{context}
---

Question: {question}

Answer:
""".strip()

    resp = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=cfg,
    )
    answer = (getattr(resp, "text", "") or "").strip()
    return AskResponse(answer=answer)

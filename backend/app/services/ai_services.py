# backend/app/services/ai_services.py

import os
import json
from typing import List, Dict, Any

# We are now using google.generativeai for everything
import google.generativeai as genai

from ..models import MapResponse, DocumentSection, TimelineEvent, AskResponse

# --- Initialization & Configuration ---
try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Configure with API key only (no project/location here)
    genai.configure(api_key=GOOGLE_API_KEY)

    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    print("Successfully initialized model using 'google-generativeai' library.")

except Exception as e:
    print(f"Error initializing google.generativeai: {e}. API calls to Gemini will fail.")
    gemini_model = None



def _call_gemini_with_json_response(prompt: str, context: str) -> List[Dict[str, Any]]:
    """Helper function to call Gemini, expecting a JSON list output."""
    if not gemini_model:
        raise RuntimeError("google.generativeai is not initialized. Cannot make API calls.")
    
    full_prompt = f"{prompt}\n\nHere is the contract text:\n---\n{context}\n---"
    try:
        # The API call is slightly different but the goal is the same
        response = gemini_model.generate_content(full_prompt)
        json_text = response.text.strip().lstrip("```json").rstrip("```").strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"An error occurred during the API call: {e}")
        return []

def generate_map(full_text: str) -> MapResponse:
    """
    Uses Gemini to extract both the document structure and timeline events.
    """
    structure_prompt = """
    Analyze the contract text provided and extract its hierarchical structure.
    Identify all main sections and their subsections.
    For each section, provide a title and a one-sentence summary of its content.
    Return the output as a JSON array of objects, where each object has "title", "content_summary", and a "subsections" array.
    Example Format:
    [
        {
            "title": "Section 1: Definitions",
            "content_summary": "This section defines key terms used throughout the agreement.",
            "subsections": []
        }
    ]
    """
    timeline_prompt = """
    Analyze the contract text provided and extract all key dates, deadlines, and time-based obligations (e.g., "within 30 days", "on January 1st", "upon termination").
    For each item found, provide a `date_description` and the `event`.
    Return the output as a JSON array of objects, where each object has "date_description" and "event".
    Example Format:
    [
        {
            "date_description": "Within 30 days of the Effective Date",
            "event": "Party B must deliver the initial report."
        }
    ]
    """
    
    raw_structure = _call_gemini_with_json_response(structure_prompt, full_text)
    raw_timeline = _call_gemini_with_json_response(timeline_prompt, full_text)

    return MapResponse(
        structure=[DocumentSection(**s) for s in raw_structure],
        timeline=[TimelineEvent(**t) for t in raw_timeline]
    )

def answer_question(question: str, context: str) -> AskResponse:
    """
    Answers a question based on the provided contract context.
    """
    if not gemini_model:
        raise RuntimeError("google.generativeai is not initialized. Cannot make API calls.")

    prompt = f"""
    You are a helpful legal assistant. Answer the following question based ONLY on the provided contract text.
    If the answer is not in the text, say "The answer is not found in the document."
    After the answer, provide a list of direct quotes or references from the text that support your answer.

    Contract Text:
    ---
    {context}
    ---

    Question: {question}
    
    Answer:
    """
    
    response = gemini_model.generate_content(prompt)
    return AskResponse(answer=response.text.strip())
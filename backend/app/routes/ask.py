# backend/app/routes/chatbot.py

from fastapi import APIRouter, HTTPException
from app.models import AskRequest, AskResponse
from app.services.chatbot import answer_question

# Set the prefix once; include this router in main.py without another prefix
router = APIRouter(tags=["chatbot"])

@router.post("/ask", response_model=AskResponse, summary="Ask Question Endpoint")
def ask_question_endpoint(request: AskRequest) -> AskResponse:
    """
    Accepts {"contract_text": "...", "question": "..."} and returns {"answer": "..."}.
    """
    try:
        # Pass the exact fields: question + contract_text (as context)
        return answer_question(question=request.question, context=request.contract_text)
    except Exception as e:
        # Temporary logging to surface the actual error in console during debugging
        print("CHATBOT ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Chatbot service error")

from fastapi import APIRouter, HTTPException
from ..models import AskRequest, AskResponse
from ..storage import document_storage
from ..services import ai_services

router = APIRouter()

# in routes/ask.py
@router.post("/ask", response_model=AskResponse, tags=["2. Core Features"])
def ask_question_endpoint(request: AskRequest):
    # Get the context directly from the request body
    context = request.contract_text
    return ai_services.answer_question(request.question, context)
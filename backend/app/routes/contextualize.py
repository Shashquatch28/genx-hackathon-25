from fastapi import APIRouter
from app.services.contextualizer.explainer import generate_contextualized_explanation
from app.models import ContextualizerRequest, ContextualizerResponse

router = APIRouter()

@router.post("/contextualize/scan", response_model=ContextualizerResponse)
def explain_clause(body: ContextualizerRequest) -> ContextualizerResponse:
    result = generate_contextualized_explanation(body.text, body.context)
    return ContextualizerResponse(**result)

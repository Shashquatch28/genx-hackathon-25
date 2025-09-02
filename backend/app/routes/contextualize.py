from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.services.contextualizer.explainer import generate_contextualized_explanation

router = APIRouter()

class ContextIn(BaseModel):
    role: str = Field(..., examples=["tenant", "employee", "HR manager", "landlord"])
    location: Optional[str] = Field(None, examples=["California", "New York"])
    contract_type: Optional[str] = Field(None, examples=["lease", "employment", "mortgage", "saas"])
    interests: Optional[List[str]] = Field(None, examples=[["financial risk", "obligations"]])
    tone: Optional[str] = Field("plain", examples=["plain", "lawyer", "exec"])

class ClauseIn(BaseModel):
    text: str
    context: ContextIn

@router.post("/contextualize/scan")
def explain_clause(body: ClauseIn) -> Dict:
    return generate_contextualized_explanation(body.text, body.context.model_dump())

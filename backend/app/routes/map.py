from fastapi import APIRouter, HTTPException, Body
from ..models import MapResponse
from ..storage import document_storage
from ..services import ai_services

router = APIRouter()

# in routes/map.py
from pydantic import BaseModel # Add this import

class MapRequest(BaseModel): # Add a request model
    contract_text: str

@router.post("/map", response_model=MapResponse, tags=["2. Core Features"])
def get_contract_map(request: MapRequest):
    # Get the text directly from the request body
    full_text = request.contract_text
    return ai_services.generate_map(full_text)
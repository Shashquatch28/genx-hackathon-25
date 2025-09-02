from fastapi import APIRouter
from pydantic import BaseModel
from app.services.risk_radar.detector import generate_risk_radar_response

router = APIRouter()

class ClauseIn(BaseModel):
    text: str

@router.post("/risk/scan")
def scan_clause(body: ClauseIn):
    return generate_risk_radar_response(body.text)

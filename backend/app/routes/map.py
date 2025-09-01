from fastapi import APIRouter, HTTPException
from app.models import MapRequest, MapResponse
from app.services.timeline import generate_map

router = APIRouter(tags=["timeline"])

@router.post("/map", response_model=MapResponse, summary="Get Contract Map")
def get_contract_map(req: MapRequest) -> MapResponse:
    """
    Accepts {"contract_text": "..."} and returns structure[] and timeline[].
    """
    try:
        return generate_map(req.contract_text)
    except Exception as e:
        import traceback
        traceback.print_exc()  # print full stack trace to your terminal logs
        # 👇 Send real error message back in response while debugging
        raise HTTPException(status_code=500, detail=str(e))

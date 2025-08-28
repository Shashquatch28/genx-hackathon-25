from fastapi import APIRouter, HTTPException
from app.models import RewriteRequest, RewriteResponse
from app.services.rewriter import rewrite_text

router = APIRouter()

@router.post("/rewrite", response_model=RewriteResponse, tags=["rewrite"])
def rewrite(req: RewriteRequest):
    try:
        out, meta = rewrite_text(req.text, req.mode)
        if not out.strip():
            raise HTTPException(status_code=400, detail="Empty output. Try a shorter or clearer selection.")
        return RewriteResponse(rewritten_text=out, meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        # Map common upstream issues to helpful messages
        msg = str(e)
        if "Default Credentials" in msg or "ADC" in msg:
            raise HTTPException(status_code=502, detail="Credentials not available. Check GOOGLE_APPLICATION_CREDENTIALS.")
        if "PERMISSION_DENIED" in msg or "403" in msg:
            raise HTTPException(status_code=502, detail="Permission denied for Vertex AI; verify roles and billing.")
        if "Not Found" in msg or "404" in msg:
            raise HTTPException(status_code=502, detail="Model or location not found; use VERTEX_GENAI_LOCATION=global or us-central1.")
        raise HTTPException(status_code=502, detail="Rewrite service temporarily unavailable.")

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.extractor import extract_text_and_blocks

router = APIRouter(tags=["upload"])

@router.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    # Basic validation
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        file_bytes = await file.read()
        result = extract_text_and_blocks(
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    # Normalize to clauses list expected by UI
    clauses = [{"id": b["id"], "text": b["text"], "rewritten": None} for b in result["blocks"]]

    # ===== Return JSON Object =====
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "full_text": result["full_text"],
        "clauses": clauses,
        "count": len(clauses),
    }

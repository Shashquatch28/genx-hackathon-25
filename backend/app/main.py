from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError



# Absolute imports so Pylance resolves from project root
from app.routes import upload
from app.routes import rewrite

app = FastAPI(title="Jargon Analyser Backend", version="0.1.0")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request body. Ensure JSON has a non-empty 'text' field.", "details": exc.errors()},
    )

# Versioned API base; both routers live under /api
app.include_router(upload.router, prefix="/api", tags=["extract"])
app.include_router(rewrite.router, prefix="/api", tags=["rewrite"])

@app.get("/", tags=["health"])
async def root():
    return {"message": "AI Contract Analyser backend is running."}


from fastapi import FastAPI

# Absolute imports so Pylance resolves from project root
from app.routes import upload
from app.routes import rewrite

app = FastAPI(title="AI Jargon Analyser Backend", version="0.1.0")

# Versioned API base; both routers live under /api
app.include_router(upload.router, prefix="/api", tags=["extract"])
app.include_router(rewrite.router, prefix="/api", tags=["rewrite"])

@app.get("/", tags=["health"])
async def root():
    return {"message": "AI Contract Analyser backend is running."}

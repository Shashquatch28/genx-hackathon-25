# main.py

from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()
# print(f"DEBUG in main.py: GCP_LOCATION is '{os.getenv('GCP_LOCATION')}'")

# Absolute imports so Pylance resolves from project root
from .routes import upload
from .routes import rewrite
from .routes import map, ask

app = FastAPI(title="AI Jargon Analyser Backend", version="0.1.0")

# Versioned API base; both routers live under /api
app.include_router(upload.router, prefix="/api", tags=["extract"])
app.include_router(rewrite.router, prefix="/api", tags=["rewrite"])
app.include_router(map.router, prefix="/api")
app.include_router(ask.router, prefix="/api")

@app.get("/", tags=["health"])
async def root():
    return {"message": "AI Contract Analyser backend is running."}


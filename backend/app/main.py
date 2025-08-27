from fastapi import FastAPI
from app.routes import upload

app = FastAPI(title = "AI Jargon Analyser Backend")

app.include_router(upload.router, prefix = "/api")

@app.get("/")
async def root():
    return {"message" : "AI Contract Analyser is backend is running."}
import os
import base64
import tempfile
from dotenv import load_dotenv

# Decode base64 Google credentials and write to temp file for Render deployment
if "GOOGLE_CREDENTIALS_BASE64" in os.environ:
    encoded_key = os.environ['GOOGLE_CREDENTIALS_BASE64']
    decoded_key = base64.b64decode(encoded_key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_json:
        temp_json.write(decoded_key)
        temp_path = temp_json.name
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path

# Load env vars from local .env if present
load_dotenv()

# Absolute imports so Pylance resolves from project root
from .routes import upload
from .routes import rewrite
from .routes import map, ask
from .routes import risk_radar 
from .routes import contextualize

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Jargon Analyser Backend", version="0.1.0")

# ---- Exception Handler ----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request body. Ensure JSON has a non-empty 'text' field.",
            "details": exc.errors(),
        },
    )


# ---- Routers ----
app.include_router(upload.router, prefix="/api", tags=["extract"])
app.include_router(rewrite.router, prefix="/api", tags=["rewrite"])
app.include_router(map.router, prefix="/api", tags=["timeline"])
app.include_router(ask.router, prefix="/api", tags=["chatbot"])
app.include_router(risk_radar.router, prefix="/api", tags=["risk"])
app.include_router(contextualize.router, prefix="/api", tags=["contextualizer"])


# ---- Health Endpoint ----
@app.get("/", tags=["health"])
async def root():
    return {"message": "AI Contract Analyser backend is running."}


# ---- CORS ----
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "*"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # exact scheme+host+port
    allow_credentials=True,          # only if sending cookies/Authorization
    allow_methods=["*"],             # dev: allow all methods
    allow_headers=["*"],             # dev: allow all request headers
    max_age=600,
)

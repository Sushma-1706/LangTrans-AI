"""Application configuration loaded only on the server."""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(500 * 1024 * 1024)))
MAX_REMOTE_BYTES = int(os.getenv("MAX_REMOTE_BYTES", str(500 * 1024 * 1024)))
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
TEMP_DIR = Path(os.getenv("TEMP_DIR", Path(__file__).resolve().parents[1] / "temp"))


def require_groq_key() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured. Add it to backend/.env before processing media.")
    return GROQ_API_KEY

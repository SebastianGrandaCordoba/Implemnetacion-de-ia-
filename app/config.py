import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    ai_service_token: str
    max_upload_bytes: int
    max_extracted_chars: int
    gemini_timeout_ms: int


def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip(),
        ai_service_token=os.getenv("AI_SERVICE_TOKEN", "").strip(),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", "10485760")),
        max_extracted_chars=int(os.getenv("MAX_EXTRACTED_CHARS", "60000")),
        gemini_timeout_ms=max(5000, min(60000, int(os.getenv("GEMINI_TIMEOUT_MS", "25000")))),
    )

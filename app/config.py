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
    generation_attempts: int = 2
    cache_entries: int = 32
    generations_per_minute: int = 12
    gemini_thinking_level: str = "LOW"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"


def _int(name: str, default: int, low: int, high: int) -> int:
    """Reads a bounded integer; a typo in Render falls back to the default instead of crashing at boot."""
    try:
        value = int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default
    return max(low, min(high, value))


QUALITY_MODEL = "gemini-3.7-flash"
LEGACY_MODELS = frozenset({"gemini-3.8-flash", "gemini-3.5-flash-lite"})


def _thinking_level(raw: str) -> str:
    """MINIMAL, LOW, MEDIUM or HIGH; OFF (or empty) leaves the model's default."""
    level = raw.strip().upper()
    return level if level in {"MINIMAL", "LOW", "MEDIUM", "HIGH"} else ""


def get_settings() -> Settings:
    configured_model = os.getenv("GEMINI_MODEL", QUALITY_MODEL).strip()
    # Render keeps old blueprint values after a code deploy: 3.8 Flash is a Live (voice) model and the
    # lite model wrote thin workshops, so both move to the current Flash model. The lite one stays as
    # the fallback when Flash is unavailable.
    if configured_model in LEGACY_MODELS:
        configured_model = QUALITY_MODEL
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=configured_model,
        ai_service_token=os.getenv("AI_SERVICE_TOKEN", "").strip(),
        max_upload_bytes=_int("MAX_UPLOAD_BYTES", 10485760, 1, 10485760),
        max_extracted_chars=_int("MAX_EXTRACTED_CHARS", 30000, 5000, 30000),
        gemini_timeout_ms=_int("GEMINI_TIMEOUT_MS", 60000, 5000, 75000),
        generation_attempts=_int("GENERATION_ATTEMPTS", 2, 1, 3),
        cache_entries=_int("GENERATION_CACHE_ENTRIES", 32, 0, 256),
        generations_per_minute=_int("GENERATIONS_PER_MINUTE", 12, 0, 120),
        gemini_thinking_level=_thinking_level(os.getenv("GEMINI_THINKING_LEVEL", "LOW")),
        gemini_fallback_model=os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite").strip(),
    )

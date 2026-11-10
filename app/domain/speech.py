"""Búho's voice: text cleanup, the style prompt and the WAV wrapper, free of FastAPI and Gemini."""

import io
import re
import wave

from pydantic import BaseModel, Field

MAX_SPEECH_CHARS = 1500
SAMPLE_RATE = 24000  # Gemini TTS returns 16-bit mono PCM at 24 kHz.
TTS_FALLBACK_MODEL = "gemini-2.5-flash-preview-tts"


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


def clean_speech_text(text: str) -> str:
    """What should be read aloud: no symbols, decimals read as Spanish speakers say them, not too long."""
    clean = re.sub(r"[•·→*#_`>|]", ", ", text)
    clean = re.sub(r"(\d),(\d)", r"\1 coma \2", clean)
    clean = re.sub(r"\s+", " ", clean).strip(" ,")
    if len(clean) <= MAX_SPEECH_CHARS:
        return clean
    cut = clean[:MAX_SPEECH_CHARS]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[: end + 1] if end > MAX_SPEECH_CHARS // 2 else cut


def build_speech_prompt(text: str) -> str:
    return (
        "Lee en voz alta el siguiente texto en español latinoamericano neutro, como un asistente cálido, cercano "
        "y tranquilo que le habla a un profesor: ritmo de conversación natural, sin prisa, sin exagerar. Lee el "
        "texto tal cual, sin agregar ni quitar palabras.\n\n"
        f"{text}"
    )


def pcm_to_wav(pcm: bytes, rate: int = SAMPLE_RATE) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm)
    return buffer.getvalue()

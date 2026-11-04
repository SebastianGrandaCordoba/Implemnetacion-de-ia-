import logging
from time import monotonic

from google import genai
from google.genai import types

from app.config import Settings
from app.domain.errors import provider_message
from app.domain.finalize import finalize_workshop
from app.domain.prompt import build_prompt, is_quiz
from app.domain.validation import InvalidWorkshop, validate_workshop
from app.schemas import WorkshopResponse

logger = logging.getLogger(__name__)


class GeminiConfigurationError(RuntimeError):
    pass


class GeminiGenerationError(RuntimeError):
    pass


MAX_OUTPUT_TOKENS = 2300


def create_client(settings: Settings) -> genai.Client:
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=settings.gemini_timeout_ms),
    )


def generate_workshop(
    settings: Settings,
    *,
    material_text: str,
    subject: str,
    target_level: str,
    learning_objective: str,
    learning_context: str = "",
    generation_type: str = "WORKSHOP",
) -> WorkshopResponse:
    if not settings.gemini_api_key:
        raise GeminiConfigurationError("Falta configurar GEMINI_API_KEY en el servicio de IA.")

    quiz_mode = is_quiz(generation_type)
    prompt = build_prompt(
        material_text=material_text,
        subject=subject,
        target_level=target_level,
        learning_objective=learning_objective,
        learning_context=learning_context,
        generation_type=generation_type,
    )

    started = monotonic()
    try:
        response = create_client(settings).models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WorkshopResponse,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        )
        if not response.text:
            raise GeminiGenerationError("El modelo no devolvió contenido.")
        workshop = WorkshopResponse.model_validate_json(response.text)
        try:
            validate_workshop(workshop, material_text)
        except InvalidWorkshop as invalid:
            raise GeminiGenerationError(str(invalid)) from invalid
        return finalize_workshop(workshop, subject=subject, target_level=target_level, quiz=quiz_mode)
    except GeminiGenerationError:
        raise
    except Exception as exc:
        logger.exception("Gemini workshop generation failed after %.2fs", monotonic() - started)
        # Keep provider diagnostics out of the response: they can contain account
        # metadata. Return only actionable, non-sensitive categories to the UI.
        message = provider_message(str(exc))
        raise GeminiGenerationError(message) from exc

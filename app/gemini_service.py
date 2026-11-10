import logging
from time import monotonic

from google import genai
from google.genai import types

from app.config import Settings
from app.domain.activity_styles import CLASS_MINUTES, EXTENDED_MINUTES, max_minutes
from app.domain.errors import provider_message
from app.domain.finalize import finalize_workshop
from app.domain.prompt import build_prompt, is_custom, is_quiz
from app.domain.repair import repair_workshop
from app.domain.rubric import (
    InvalidRubric,
    RubricRequest,
    RubricResponse,
    build_rubric_prompt,
    repair_rubric,
    validate_rubric,
)
from app.domain.validation import InvalidWorkshop, validate_workshop
from app.schemas import WorkshopResponse

logger = logging.getLogger(__name__)


class GeminiConfigurationError(RuntimeError):
    pass


class GeminiGenerationError(RuntimeError):
    pass


# Thinking tokens count against the output budget; a full workshop with hints and notes needs room.
MAX_OUTPUT_TOKENS = 8192


# The quality model gets this long before the fast one takes over; both together stay under the backend's
# 85 s budget. Gemini's own SDK retries are off: a silent retry turned a 30 s wait into 58 s and a failure.
PRIMARY_TIMEOUT_MS = 32_000
FALLBACK_TIMEOUT_MS = 40_000


def create_client(settings: Settings, timeout_ms: int | None = None) -> genai.Client:
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(
            timeout=timeout_ms or settings.gemini_timeout_ms,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def generation_config(
    settings: Settings, *, thinking: bool = True, schema=WorkshopResponse
) -> types.GenerateContentConfig:
    config = {
        "response_mime_type": "application/json",
        "response_schema": schema,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
    if thinking and settings.gemini_thinking_level:
        # A workshop is structured writing, not a puzzle: low thinking answers much faster.
        config["thinking_config"] = types.ThinkingConfig(thinking_level=settings.gemini_thinking_level)
    return types.GenerateContentConfig(**config)


def _generate_with(client, settings: Settings, model: str, prompt: str, schema=WorkshopResponse):
    try:
        return client.models.generate_content(
            model=model, contents=prompt, config=generation_config(settings, schema=schema)
        )
    except Exception as exc:
        if "thinking" not in str(exc).lower():
            raise
        # Some models reject a thinking level; fall back to their default instead of failing.
        logger.warning("Model %s rejected thinking level; retrying without it", model)
        return client.models.generate_content(
            model=model, contents=prompt, config=generation_config(settings, thinking=False, schema=schema)
        )


def _credentials(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(word in text for word in ("api key", "api_key", "permission_denied", "unauthorized", "401", "403"))


def _generate(client, settings: Settings, prompt: str, schema=WorkshopResponse):
    """Quality model first, with a short deadline; anything but a bad key moves on to the fast model.

    ``client`` is kept for tests that inject a fake; in production each model gets its own client so each
    one has its own deadline.
    """
    fallback = settings.gemini_fallback_model
    primary_client = client if client is not None else create_client(settings, PRIMARY_TIMEOUT_MS)
    started = monotonic()
    try:
        return _generate_with(primary_client, settings, settings.gemini_model, prompt, schema)
    except Exception as exc:
        if not fallback or fallback == settings.gemini_model or _credentials(exc):
            raise
        logger.warning("Model %s failed after %.1fs (%s); using %s", settings.gemini_model,
                       monotonic() - started, str(exc)[:160], fallback)
        fallback_client = client if client is not None else create_client(settings, FALLBACK_TIMEOUT_MS)
        return _generate_with(fallback_client, settings, fallback, prompt, schema)


def generate_workshop(
    settings: Settings,
    *,
    material_text: str,
    subject: str,
    target_level: str,
    learning_objective: str,
    learning_context: str = "",
    generation_type: str = "WORKSHOP",
    activity_styles: tuple[str, ...] = (),
    teacher_prompt: str = "",
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
        activity_styles=activity_styles,
        teacher_prompt=teacher_prompt,
    )
    if quiz_mode:
        limit = CLASS_MINUTES
    else:
        limit = EXTENDED_MINUTES if is_custom(generation_type) else max_minutes(activity_styles)

    started = monotonic()
    try:
        response = _generate(None, settings, prompt)
        if not response.text:
            raise GeminiGenerationError("El modelo no devolvió contenido.")
        workshop = repair_workshop(WorkshopResponse.model_validate_json(response.text), material_text, limit)
        try:
            validate_workshop(workshop, material_text, max_minutes=limit, generation_type=generation_type)
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


def generate_rubric(settings: Settings, request: RubricRequest) -> RubricResponse:
    """An analytic rubric (criteria x four levels) for an activity the teacher describes."""
    if not settings.gemini_api_key:
        raise GeminiConfigurationError("Falta configurar GEMINI_API_KEY en el servicio de IA.")
    started = monotonic()
    try:
        response = _generate(None, settings, build_rubric_prompt(request), RubricResponse)
        if not response.text:
            raise GeminiGenerationError("El modelo no devolvió contenido.")
        rubric = repair_rubric(RubricResponse.model_validate_json(response.text), request.criteriaCount)
        try:
            return validate_rubric(rubric)
        except InvalidRubric as invalid:
            raise GeminiGenerationError(str(invalid)) from invalid
    except GeminiGenerationError:
        raise
    except Exception as exc:
        logger.exception("Gemini rubric generation failed after %.2fs", monotonic() - started)
        raise GeminiGenerationError(provider_message(str(exc))) from exc

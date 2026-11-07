import hmac
import logging
from time import monotonic
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.adapters.gemini_workshop_generator import GeminiWorkshopAdapter
from app.adapters.http_middleware import RequestContextMiddleware
from app.adapters.material_extraction import DocumentMaterialAdapter
from app.adapters.resilience import (
    CachedWorkshopGenerator,
    RetryingWorkshopGenerator,
    TimedWorkshopGenerator,
)
from app.application.inspect_use_case import InspectMaterials
from app.application.workshop_use_case import GenerateWorkshop, WorkshopRequest
from app.config import get_settings
from app.document_parser import SUPPORTED_EXTENSIONS, MaterialError
from app.domain.activity_styles import STYLES
from app.domain.rate_limit import SlidingWindowLimiter
from app.domain.request_rules import (
    GENERATION_TYPES,
    MAX_CONTEXT_CHARS,
    MAX_MATERIALS,
    MAX_OBJECTIVE_CHARS,
    MAX_PROMPT_CHARS,
    InvalidRequest,
    check_material_count,
    check_teacher_prompt,
    check_text_limits,
    normalize_activity_styles,
    normalize_generation_type,
    normalize_level,
    safe_filename,
)
from app.domain.rubric import RubricRequest, RubricResponse
from app.gemini_service import (
    GeminiConfigurationError,
    GeminiGenerationError,
    generate_rubric,
)
from app.schemas import WorkshopResponse

STARTED_AT = monotonic()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="FairTeam AI Service",
    description="Genera talleres educativos a partir de material de estudio proporcionado por el docente.",
    version="1.5.0",
)

app.add_middleware(RequestContextMiddleware)


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Never leaks stack traces; gives the backend an id to find the log line."""
    request_id = getattr(request.state, "request_id", "")
    logger.exception("Unexpected error [%s]", request_id)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado en el servicio de IA.", "requestId": request_id},
        headers={"X-Request-ID": request_id} if request_id else None,
    )


# Composition root: the HTTP adapter wires application ports to infrastructure.
_startup_settings = get_settings()
generate_workshop_use_case = GenerateWorkshop(
    extract_material=DocumentMaterialAdapter(),
    generate=CachedWorkshopGenerator(
        RetryingWorkshopGenerator(
            TimedWorkshopGenerator(GeminiWorkshopAdapter()),
            attempts=_startup_settings.generation_attempts,
        ),
        max_entries=_startup_settings.cache_entries,
    ),
)


inspect_use_case = InspectMaterials(DocumentMaterialAdapter())


generation_limiter = SlidingWindowLimiter(_startup_settings.generations_per_minute)


def limit_generations() -> None:
    wait = generation_limiter.acquire("backend")
    if wait is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Se generaron muchos talleres seguidos. Espera un momento e inténtalo de nuevo.",
            headers={"Retry-After": str(max(1, round(wait)))},
        )


def get_use_case() -> GenerateWorkshop:
    """FastAPI dependency so tests can swap the composition root."""
    return generate_workshop_use_case


def get_rubric_generator():
    """FastAPI dependency so tests can replace the model call."""
    settings = get_settings()

    def generate(request: RubricRequest) -> RubricResponse:
        # A second attempt fixes most rubrics the validator rejects (missing level, weights off).
        try:
            return generate_rubric(settings, request)
        except GeminiGenerationError as first:
            logger.info("Retrying rubric generation: %s", first)
            return generate_rubric(settings, request)

    return generate


def require_backend_token(
    x_ai_service_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = get_settings().ai_service_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio no tiene configurada la autenticación interna.",
        )
    if not x_ai_service_token or not hmac.compare_digest(x_ai_service_token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado.")


async def read_materials(uploads: list[UploadFile], max_bytes: int) -> list[tuple[str, bytes]]:
    materials: list[tuple[str, bytes]] = []
    total_size = 0
    for upload in uploads:
        filename = safe_filename(upload.filename)
        raw = await upload.read(max_bytes + 1)
        if not raw:
            raise HTTPException(status_code=400, detail=f"El archivo {filename} está vacío.")
        total_size += len(raw)
        if total_size > max_bytes:
            raise HTTPException(status_code=413, detail="Los materiales juntos superan el límite de 10 MB.")
        materials.append((filename, raw))
    return materials


@app.get("/health")
def health() -> dict[str, str | int]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": app.version,
        "uptimeSeconds": int(monotonic() - STARTED_AT),
        "provider": "gemini",
        "model": settings.gemini_model,
        "generationConfigured": str(bool(settings.gemini_api_key)).lower(),
    }


@app.get("/api/v1/limits", dependencies=[Depends(require_backend_token)])
def limits() -> dict[str, object]:
    """Lets the backend show the teacher the real limits before uploading."""
    settings = get_settings()
    return {
        "maxMaterials": MAX_MATERIALS,
        "maxUploadBytes": settings.max_upload_bytes,
        "maxExtractedChars": settings.max_extracted_chars,
        "maxObjectiveChars": MAX_OBJECTIVE_CHARS,
        "maxContextChars": MAX_CONTEXT_CHARS,
        "maxPromptChars": MAX_PROMPT_CHARS,
        "formats": [extension.lstrip(".") for extension in SUPPORTED_EXTENSIONS],
        "levels": ["LOW", "MEDIUM", "HIGH"],
        "generationTypes": sorted(GENERATION_TYPES),
        "activityStyles": [
            {"id": style.id, "label": style.label, "extended": style.extended} for style in STYLES.values()
        ],
    }


@app.post("/api/v1/materials/inspect", dependencies=[Depends(require_backend_token)])
async def inspect_materials(files: list[UploadFile] = File(...)) -> dict[str, object]:
    """Shows what will be read from each file before spending a Gemini request."""
    settings = get_settings()
    try:
        check_material_count(len(files))
        materials = await read_materials(files, settings.max_upload_bytes)
        stats = await run_in_threadpool(inspect_use_case.execute, materials, settings.max_extracted_chars)
    except InvalidRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        for upload in files:
            await upload.close()
    total = sum(item.characters for item in stats)
    return {
        "totalCharacters": total,
        "maxExtractedChars": settings.max_extracted_chars,
        "fitsLimit": total <= settings.max_extracted_chars,
        "materials": [
            {
                "filename": item.filename,
                "characters": item.characters,
                "words": item.words,
                "units": item.units,
                "estimatedTokens": item.estimated_tokens,
                "preview": item.preview,
            }
            for item in stats
        ],
    }


@app.post(
    "/api/v1/workshops/generate",
    response_model=WorkshopResponse,
    dependencies=[Depends(require_backend_token), Depends(limit_generations)],
)
async def create_workshop(
    subject: Annotated[str, Form(min_length=1, max_length=120)],
    target_level: Annotated[str, Form(alias="targetLevel")],
    learning_objective: Annotated[str, Form(alias="learningObjective")] = "",
    learning_context: Annotated[str, Form(alias="learningContext")] = "",
    generation_type: Annotated[str, Form(alias="generationType")] = "WORKSHOP",
    activity_styles: Annotated[str, Form(alias="activityStyles", max_length=80)] = "",
    teacher_prompt: Annotated[str, Form(alias="teacherPrompt", max_length=4000)] = "",
    file: UploadFile | None = File(default=None),
    files: list[UploadFile] | None = File(default=None),
    use_case: GenerateWorkshop = Depends(get_use_case),
) -> WorkshopResponse:
    settings = get_settings()
    try:
        level = normalize_level(target_level)
        kind = normalize_generation_type(generation_type)
        styles = normalize_activity_styles(activity_styles)
        check_text_limits(learning_objective, learning_context)
        check_teacher_prompt(teacher_prompt, kind)
    except InvalidRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if file is not None and files:
        raise HTTPException(status_code=400, detail="Envía los materiales en un solo campo.")
    uploads = files if files else ([file] if file is not None else [])
    try:
        check_material_count(len(uploads), optional=kind == "CUSTOM")
    except InvalidRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        materials = await read_materials(uploads, settings.max_upload_bytes)
        return await run_in_threadpool(
            use_case.execute,
            settings,
            WorkshopRequest(
                filename=materials[0][0] if materials else "",
                content=materials[0][1] if materials else b"",
                subject=subject.strip(),
                target_level=level,
                learning_objective=learning_objective.strip(),
                learning_context=learning_context.strip(),
                generation_type=kind,
                activity_styles=styles,
                additional_materials=tuple(materials[1:]),
                teacher_prompt=teacher_prompt.strip(),
            ),
        )
    except InvalidRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except GeminiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GeminiGenerationError as exc:
        logger.warning("Workshop generation failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        for upload in uploads:
            await upload.close()


@app.post(
    "/generate-rubric",
    response_model=RubricResponse,
    dependencies=[Depends(require_backend_token), Depends(limit_generations)],
)
async def generate_rubric_endpoint(
    request: RubricRequest, generator=Depends(get_rubric_generator)
) -> RubricResponse:
    """Analytic rubric (3–6 criteria × Excelente/Bueno/Básico/Insuficiente) for an activity."""
    try:
        return await run_in_threadpool(generator, request)
    except GeminiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GeminiGenerationError as exc:
        logger.warning("Rubric generation failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

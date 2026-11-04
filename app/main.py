import hmac
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.adapters.gemini_workshop_generator import GeminiWorkshopAdapter
from app.adapters.material_extraction import DocumentMaterialAdapter
from app.adapters.resilience import (
    CachedWorkshopGenerator,
    RetryingWorkshopGenerator,
    TimedWorkshopGenerator,
)
from app.application.workshop_use_case import GenerateWorkshop, WorkshopRequest
from app.config import get_settings
from app.document_parser import MaterialError
from app.domain.request_rules import (
    InvalidRequest,
    check_material_count,
    check_text_limits,
    normalize_generation_type,
    normalize_level,
    safe_filename,
)
from app.gemini_service import (
    GeminiConfigurationError,
    GeminiGenerationError,
)
from app.schemas import WorkshopResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="FairTeam AI Service",
    description="Genera talleres educativos a partir de material de estudio proporcionado por el docente.",
    version="1.0.0",
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


def get_use_case() -> GenerateWorkshop:
    """FastAPI dependency so tests can swap the composition root."""
    return generate_workshop_use_case


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


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "provider": "gemini",
        "model": settings.gemini_model,
        "generationConfigured": str(bool(settings.gemini_api_key)).lower(),
    }


@app.post(
    "/api/v1/workshops/generate",
    response_model=WorkshopResponse,
    dependencies=[Depends(require_backend_token)],
)
async def create_workshop(
    subject: Annotated[str, Form(min_length=1, max_length=120)],
    target_level: Annotated[str, Form(alias="targetLevel")],
    learning_objective: Annotated[str, Form(alias="learningObjective")] = "",
    learning_context: Annotated[str, Form(alias="learningContext")] = "",
    generation_type: Annotated[str, Form(alias="generationType")] = "WORKSHOP",
    file: UploadFile | None = File(default=None),
    files: list[UploadFile] | None = File(default=None),
    use_case: GenerateWorkshop = Depends(get_use_case),
) -> WorkshopResponse:
    settings = get_settings()
    try:
        level = normalize_level(target_level)
        kind = normalize_generation_type(generation_type)
        check_text_limits(learning_objective, learning_context)
    except InvalidRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if file is not None and files:
        raise HTTPException(status_code=400, detail="Envía los materiales en un solo campo.")
    uploads = files if files else ([file] if file is not None else [])
    try:
        check_material_count(len(uploads))
    except InvalidRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        materials: list[tuple[str, bytes]] = []
        total_size = 0
        for upload in uploads:
            filename = safe_filename(upload.filename)
            raw = await upload.read(settings.max_upload_bytes + 1)
            if not raw:
                raise HTTPException(status_code=400, detail=f"El archivo {filename} está vacío.")
            total_size += len(raw)
            if total_size > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="Los materiales juntos superan el límite de 10 MB.")
            materials.append((filename, raw))

        return await run_in_threadpool(
            use_case.execute,
            settings,
            WorkshopRequest(
                filename=materials[0][0],
                content=materials[0][1],
                subject=subject.strip(),
                target_level=level,
                learning_objective=learning_objective.strip(),
                learning_context=learning_context.strip(),
                generation_type=kind,
                additional_materials=tuple(materials[1:]),
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

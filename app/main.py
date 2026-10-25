import hmac
import logging
import re
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.adapters.gemini_workshop_generator import GeminiWorkshopAdapter
from app.adapters.material_extraction import DocumentMaterialAdapter
from app.application.workshop_use_case import GenerateWorkshop, WorkshopRequest
from app.config import get_settings
from app.document_parser import MaterialError
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
generate_workshop_use_case = GenerateWorkshop(
    extract_material=DocumentMaterialAdapter(),
    generate=GeminiWorkshopAdapter(),
)


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
    file: Annotated[UploadFile, File()],
    subject: Annotated[str, Form(min_length=1, max_length=120)],
    target_level: Annotated[str, Form(alias="targetLevel")],
    learning_objective: Annotated[str, Form(alias="learningObjective")] = "",
    learning_context: Annotated[str, Form(alias="learningContext")] = "",
    generation_type: Annotated[str, Form(alias="generationType")] = "WORKSHOP",
) -> WorkshopResponse:
    settings = get_settings()
    level_map = {
        "LOW": "LOW", "BAJO": "LOW",
        "MEDIUM": "MEDIUM", "INTERMEDIO": "MEDIUM",
        "HIGH": "HIGH", "ALTO": "HIGH",
    }
    level = level_map.get(target_level.strip().upper())
    if level is None:
        raise HTTPException(status_code=400, detail="El nivel debe ser LOW, MEDIUM o HIGH.")
    if len(learning_objective) > 1000:
        raise HTTPException(status_code=400, detail="El objetivo no puede superar 1000 caracteres.")
    if len(learning_context) > 2500:
        raise HTTPException(status_code=400, detail="El contexto del curso no puede superar 2500 caracteres.")
    if generation_type.strip().upper() not in {"WORKSHOP", "QUIZ"}:
        raise HTTPException(status_code=400, detail="El tipo de generación debe ser WORKSHOP o QUIZ.")

    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if not re.fullmatch(r"[\w .()_-]{1,180}\.(pdf|docx|txt)", filename, flags=re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Adjunta un archivo PDF, DOCX o TXT con nombre válido.")
    try:
        raw = await file.read(settings.max_upload_bytes + 1)
        if not raw:
            raise HTTPException(status_code=400, detail="El archivo está vacío.")
        if len(raw) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="El archivo supera el límite de 10 MB.")

        return await run_in_threadpool(
            generate_workshop_use_case.execute,
            settings,
            WorkshopRequest(
                filename=filename,
                content=raw,
                subject=subject.strip(),
                target_level=level,
                learning_objective=learning_objective.strip(),
                learning_context=learning_context.strip(),
                generation_type=generation_type.strip().upper(),
            ),
        )
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except GeminiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GeminiGenerationError as exc:
        logger.warning("Workshop generation failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await file.close()

"""Use case for generating a workshop from teacher-provided material."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.application.ports import MaterialTextExtractor, WorkshopGenerator
from app.document_parser import MaterialError
from app.schemas import WorkshopResponse

if TYPE_CHECKING:
    from app.config import Settings


@dataclass(frozen=True)
class WorkshopRequest:
    filename: str
    content: bytes
    subject: str
    target_level: str
    learning_objective: str
    learning_context: str = ""
    generation_type: str = "WORKSHOP"
    additional_materials: tuple[tuple[str, bytes], ...] = ()


class GenerateWorkshop:
    """Coordinates ports; it knows neither FastAPI nor Gemini/PDF libraries."""

    def __init__(
        self,
        extract_material: MaterialTextExtractor,
        generate: WorkshopGenerator,
    ) -> None:
        self._extract_material = extract_material
        self._generate = generate

    def execute(self, settings: Settings, request: WorkshopRequest) -> WorkshopResponse:
        sources = ((request.filename, request.content), *request.additional_materials)
        extracted: list[str] = []
        remaining = settings.max_extracted_chars
        for index, (filename, content) in enumerate(sources, start=1):
            if remaining < 500:
                raise MaterialError(
                    "Los materiales seleccionados juntos contienen demasiado texto. Selecciona menos archivos o archivos más breves."
                )
            text = self._extract_material(filename, content, remaining)
            labeled_text = f"[Material {index}: {filename}]\n{text}"
            extracted.append(labeled_text)
            remaining -= len(labeled_text)
        material_text = "\n\n".join(extracted)
        return self._generate(
            settings,
            material_text=material_text,
            subject=request.subject,
            target_level=request.target_level,
            learning_objective=request.learning_objective,
            learning_context=request.learning_context,
            generation_type=request.generation_type,
        )

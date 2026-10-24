"""Use case for generating a workshop from teacher-provided material."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.application.ports import MaterialTextExtractor, WorkshopGenerator
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
        material_text = self._extract_material(
            request.filename,
            request.content,
            settings.max_extracted_chars,
        )
        return self._generate(
            settings,
            material_text=material_text,
            subject=request.subject,
            target_level=request.target_level,
            learning_objective=request.learning_objective,
        )

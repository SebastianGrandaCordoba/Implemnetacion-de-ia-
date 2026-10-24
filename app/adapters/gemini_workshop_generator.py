"""Gemini provider adapter."""

from app.config import Settings
from app.gemini_service import generate_workshop
from app.schemas import WorkshopResponse


class GeminiWorkshopAdapter:
    def __call__(
        self,
        settings: Settings,
        *,
        material_text: str,
        subject: str,
        target_level: str,
        learning_objective: str,
    ) -> WorkshopResponse:
        return generate_workshop(
            settings,
            material_text=material_text,
            subject=subject,
            target_level=target_level,
            learning_objective=learning_objective,
        )

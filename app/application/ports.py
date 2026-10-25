"""Ports that keep application rules independent from IO providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.schemas import WorkshopResponse

if TYPE_CHECKING:
    from app.config import Settings


class MaterialTextExtractor(Protocol):
    def __call__(self, filename: str, raw: bytes, max_chars: int) -> str: ...


class WorkshopGenerator(Protocol):
    def __call__(
        self,
        settings: Settings,
        *,
        material_text: str,
        subject: str,
        target_level: str,
        learning_objective: str,
        learning_context: str,
        generation_type: str,
    ) -> WorkshopResponse: ...

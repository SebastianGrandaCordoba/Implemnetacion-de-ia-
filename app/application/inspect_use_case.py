"""Use case: preview what the service can read from the teacher's files, without calling Gemini."""

from __future__ import annotations

from app.application.ports import MaterialTextExtractor
from app.domain.material_stats import MaterialStats, describe


class InspectMaterials:
    def __init__(self, extract_material: MaterialTextExtractor) -> None:
        self._extract_material = extract_material

    def execute(self, materials: list[tuple[str, bytes]], max_chars: int) -> list[MaterialStats]:
        return [describe(name, self._extract_material(name, raw, max_chars)) for name, raw in materials]

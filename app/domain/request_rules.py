"""Validation of the teacher's request, independent from FastAPI."""

import re

MAX_OBJECTIVE_CHARS = 1000
MAX_CONTEXT_CHARS = 2500
MAX_MATERIALS = 6
GENERATION_TYPES = frozenset({"WORKSHOP", "QUIZ"})
LEVEL_ALIASES = {
    "LOW": "LOW", "BAJO": "LOW",
    "MEDIUM": "MEDIUM", "INTERMEDIO": "MEDIUM", "MEDIO": "MEDIUM",
    "HIGH": "HIGH", "ALTO": "HIGH",
}
_FILENAME = re.compile(r"[\w .()_-]{1,180}\.(pdf|docx|txt)", flags=re.IGNORECASE)


class InvalidRequest(ValueError):
    """A request the teacher can fix; the message is shown as is."""


def normalize_level(raw: str) -> str:
    level = LEVEL_ALIASES.get(raw.strip().upper())
    if level is None:
        raise InvalidRequest("El nivel debe ser LOW, MEDIUM o HIGH.")
    return level


def normalize_generation_type(raw: str) -> str:
    kind = raw.strip().upper() or "WORKSHOP"
    if kind not in GENERATION_TYPES:
        raise InvalidRequest("El tipo de generación debe ser WORKSHOP o QUIZ.")
    return kind


def check_text_limits(learning_objective: str, learning_context: str) -> None:
    if len(learning_objective) > MAX_OBJECTIVE_CHARS:
        raise InvalidRequest(f"El objetivo no puede superar {MAX_OBJECTIVE_CHARS} caracteres.")
    if len(learning_context) > MAX_CONTEXT_CHARS:
        raise InvalidRequest(f"El contexto del curso no puede superar {MAX_CONTEXT_CHARS} caracteres.")


def safe_filename(raw: str | None) -> str:
    """Keeps only the base name and rejects anything that is not a supported document."""
    filename = (raw or "").replace("\\", "/").rsplit("/", 1)[-1]
    if not _FILENAME.fullmatch(filename):
        raise InvalidRequest("Adjunta archivos PDF, DOCX o TXT con nombre válido.")
    return filename


def check_material_count(count: int) -> None:
    if count < 1 or count > MAX_MATERIALS:
        raise InvalidRequest(f"Adjunta entre 1 y {MAX_MATERIALS} materiales.")

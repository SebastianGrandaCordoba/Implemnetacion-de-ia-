"""Validation of the teacher's request, independent from FastAPI."""

import re

MAX_OBJECTIVE_CHARS = 1000
MAX_CONTEXT_CHARS = 2500
MAX_MATERIALS = 6
MAX_PROMPT_CHARS = 2000
GENERATION_TYPES = frozenset({"WORKSHOP", "QUIZ", "CUSTOM"})
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
        raise InvalidRequest("El tipo de generación debe ser WORKSHOP, QUIZ o CUSTOM.")
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


def check_material_count(count: int, *, optional: bool = False) -> None:
    """A custom request can be written from the teacher's prompt alone; the others need material."""
    if count > MAX_MATERIALS or (count < 1 and not optional):
        raise InvalidRequest(f"Adjunta entre 1 y {MAX_MATERIALS} materiales.")


def check_teacher_prompt(prompt: str, generation_type: str) -> None:
    """The teacher's own instructions: required for CUSTOM, optional extra guidance otherwise."""
    if len(prompt) > MAX_PROMPT_CHARS:
        raise InvalidRequest(f"Las indicaciones no pueden superar {MAX_PROMPT_CHARS} caracteres.")
    if generation_type == "CUSTOM" and len(prompt.strip()) < 15:
        raise InvalidRequest("Describe con al menos una frase qué taller quieres que cree.")


def normalize_activity_styles(raw: str) -> tuple[str, ...]:
    """Accepts "CODE,DEPLOY" (any case or spacing); empty means guided exercises."""
    from app.domain.activity_styles import DEFAULT, MAX_STYLES, STYLES

    chosen = tuple(dict.fromkeys(part.strip().upper() for part in raw.split(",") if part.strip()))
    if not chosen:
        return DEFAULT
    unknown = [style for style in chosen if style not in STYLES]
    if unknown:
        raise InvalidRequest("Tipo de actividad no reconocido: " + ", ".join(unknown) + ".")
    if len(chosen) > MAX_STYLES:
        raise InvalidRequest(f"Elige hasta {MAX_STYLES} tipos de actividad.")
    return chosen

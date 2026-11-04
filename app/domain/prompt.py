"""Builds the instructions sent to the language model."""

LEVEL_GUIDANCE = {
    "LOW": "Asume que el grupo necesita apoyo inicial: explica palabras clave, resuelve un ejemplo modelo, da pistas graduales y empieza con una tarea corta.",
    "MEDIUM": "Asume que el grupo conoce lo básico: empieza con una práctica guiada y termina con una aplicación nueva sin resolver.",
    "HIGH": "Asume que el grupo domina lo esencial: evita repetir definiciones y plantea aplicación, comparación o un reto de transferencia.",
}
DEFAULT_GUIDANCE = "Ajusta la dificultad al nivel indicado y explica cualquier término necesario."


def level_guidance(target_level: str) -> str:
    """How hard the activity should be for the requested level."""
    return LEVEL_GUIDANCE.get(target_level.strip().upper(), DEFAULT_GUIDANCE)

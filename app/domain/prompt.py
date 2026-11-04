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


def is_quiz(generation_type: str) -> bool:
    return generation_type.strip().upper() == "QUIZ"


def deliverable_name(generation_type: str) -> str:
    return "quiz breve de comprobación" if is_quiz(generation_type) else "taller de refuerzo"


def deliverable_rules(generation_type: str) -> str:
    """The rule that differs between a workshop and a quiz."""
    if is_quiz(generation_type):
        return ("- El título debe comenzar con 'Quiz breve:'. El quiz es el producto principal: sus tres preguntas deben ser claras, "
                "autocontenidas y tener opciones, respuesta correcta y explicación. Las actividades describen cómo responderlo.")
    return ("- El título debe comenzar con 'Taller de refuerzo:'. Diseña una guía lista para entregar, que permita al estudiante "
            "trabajar sin que el docente tenga que completar instrucciones.")

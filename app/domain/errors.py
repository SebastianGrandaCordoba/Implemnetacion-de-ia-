"""Turns provider failures into short, actionable Spanish messages without leaking account details."""

RULES: list[tuple[tuple[str, ...], str]] = [
    (("429", "quota", "resource_exhausted", "rate limit"),
     "Gemini alcanzó el límite o la cuota disponible. "
     "Espera un momento o revisa la cuota de la API y vuelve a intentar."),
    (("api key", "api_key", "permission_denied", "unauthorized", "401", "403"),
     "Gemini rechazó la credencial. Revisa GEMINI_API_KEY en el servicio de IA."),
    (("not found", "404", "model"),
     "El modelo configurado para Gemini no está disponible. Revisa GEMINI_MODEL en el servicio de IA."),
    (("timeout", "timed out", "deadline"),
     "Gemini tardó demasiado en responder. Prueba con un material más corto e inténtalo de nuevo."),
]
DEFAULT = "Gemini no pudo generar el taller. Revisa la configuración y la cuota de la API e inténtalo de nuevo."
RETRYABLE = {RULES[0][1], RULES[3][1]}


def provider_message(diagnostic: str) -> str:
    text = diagnostic.lower()
    for markers, message in RULES:
        if any(marker in text for marker in markers):
            return message
    return DEFAULT


def is_retryable(message: str) -> bool:
    """Rate limits and timeouts may succeed on a second try; bad keys or models will not."""
    return message in RETRYABLE

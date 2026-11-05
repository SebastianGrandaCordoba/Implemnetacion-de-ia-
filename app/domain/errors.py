"""Turns provider failures into short, actionable Spanish messages without leaking account details."""

RULES: list[tuple[tuple[str, ...], str]] = [
    (("429", "quota", "resource_exhausted", "rate limit"),
     "Gemini alcanzó el límite o la cuota disponible. "
     "Espera un momento o revisa la cuota de la API y vuelve a intentar."),
    (("api key", "api_key", "permission_denied", "unauthorized", "401", "403"),
     "Gemini rechazó la credencial. Revisa GEMINI_API_KEY en el servicio de IA."),
    (("503", "overloaded", "unavailable"),
     "Gemini está saturado en este momento. Espera unos segundos y vuelve a intentar."),
    (("not found", "404"),
     "El modelo configurado para Gemini no está disponible. Revisa GEMINI_MODEL en el servicio de IA."),
    (("timeout", "timed out", "deadline"),
     "Gemini tardó demasiado en responder. Prueba con un material más corto e inténtalo de nuevo."),
]
DEFAULT = "Gemini no pudo generar el taller. Revisa la configuración y la cuota de la API e inténtalo de nuevo."
QUOTA, CREDENTIALS, OVERLOADED, MODEL, TIMEOUT = (message for _, message in RULES)
# Only failures that come back fast are worth retrying: a timeout already spent most of the
# backend's 85 s budget, so retrying it would make the teacher wait and still fail.
RETRYABLE = {QUOTA, OVERLOADED}


def provider_message(diagnostic: str) -> str:
    text = diagnostic.lower()
    for markers, message in RULES:
        if any(marker in text for marker in markers):
            return message
    return DEFAULT


def is_retryable(message: str) -> bool:
    """Rate limits and overloads may pass on a second try; timeouts, keys or models will not."""
    return message in RETRYABLE

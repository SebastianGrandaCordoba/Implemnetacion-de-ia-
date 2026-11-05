"""Kinds of work a workshop can ask for, chosen by the teacher when creating it.

Guided exercises fit one class session; code, apps, deployments and projects are longer pieces of
work that students may finish outside class, so they get a bigger time and word budget.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivityStyle:
    id: str
    label: str
    rules: str
    extended: bool


STYLES: dict[str, ActivityStyle] = {
    style.id: style
    for style in (
        ActivityStyle("GUIDED", "Ejercicios guiados",
                      "Ejercicios guiados en clase con ejemplos resueltos y práctica progresiva.", False),
        ActivityStyle("CODE", "Programar código",
                      "Al menos una actividad pide escribir código: indica el lenguaje que sugiere el material, "
                      "da un esqueleto inicial breve (firma de funciones o clases) dentro de las instrucciones, "
                      "describe entradas y salidas esperadas con dos o tres casos de prueba y pide como evidencia "
                      "el archivo o repositorio con el código y la salida de las pruebas.", True),
        ActivityStyle("APP", "Construir una aplicación",
                      "Al menos una actividad pide construir una aplicación pequeña y funcional: escribe de tres a "
                      "cinco historias de usuario, los requisitos mínimos, una sugerencia de tecnología coherente con "
                      "el material y criterios de aceptación verificables. Evidencia: repositorio, capturas y una "
                      "breve demostración.", True),
        ActivityStyle("DEPLOY", "Desplegar en internet",
                      "Al menos una actividad pide desplegar el trabajo en una plataforma gratuita (por ejemplo "
                      "GitHub Pages, Render o Vercel): pasos de despliegue, variables de entorno sin publicar claves "
                      "ni contraseñas, una lista de verificación antes de entregar y, como evidencia, la URL pública "
                      "funcionando y el enlace al repositorio.", True),
        ActivityStyle("CASE", "Caso de estudio",
                      "Plantea un caso realista basado en el material, con datos concretos y una decisión que el "
                      "estudiante debe tomar y justificar con los conceptos del material.", False),
        ActivityStyle("TEAM", "Proyecto en equipo",
                      "Organiza el trabajo para equipos de tres a cuatro personas: define roles, qué entrega cada "
                      "integrante, un punto de control intermedio y cómo se evalúa el aporte individual.", True),
    )
}
DEFAULT = ("GUIDED",)
MAX_STYLES = 3
CLASS_MINUTES = 60
EXTENDED_MINUTES = 120


def is_extended(styles: tuple[str, ...]) -> bool:
    return any(STYLES[s].extended for s in styles if s in STYLES)


def max_minutes(styles: tuple[str, ...]) -> int:
    """Longest single activity allowed: one class for guided work, two hours for code, apps or deployments."""
    return EXTENDED_MINUTES if is_extended(styles) else CLASS_MINUTES


def style_rules(styles: tuple[str, ...]) -> str:
    return "\n".join(f"- {STYLES[s].label}: {STYLES[s].rules}" for s in styles if s in STYLES)

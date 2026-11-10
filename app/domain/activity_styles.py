"""Kinds of work a workshop can ask for, chosen by the teacher when creating it.

They cover every area, not only software: problem sets for mathematics, laboratories for the sciences,
source analysis and essays for the humanities, reading, writing and speaking for languages, and code,
apps and deployments for programming. The frontend shows the ones that fit the course.
Guided exercises fit one class session; longer pieces of work get a bigger time and word budget.
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
                      "da un esqueleto inicial breve (firma de funciones o clases) entre ``` y ``` "
                      "dentro de las instrucciones, "
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
        ActivityStyle("PROBLEMS", "Resolución de problemas",
                      "Problemas de dificultad creciente con datos numéricos concretos: uno resuelto paso a paso "
                      "como modelo, los demás con su respuesta final en la clave y al menos uno de aplicación a una "
                      "situación real. Pide mostrar el procedimiento, no solo el resultado.", False),
        ActivityStyle("LAB", "Laboratorio o experimento",
                      "Una práctica de laboratorio o experimento sencillo: pregunta o hipótesis, materiales "
                      "accesibles y seguros, procedimiento numerado, tabla para registrar datos, análisis con "
                      "preguntas guiadas y conclusión. Incluye una advertencia de seguridad si aplica.", True),
        ActivityStyle("SOURCES", "Análisis de fuentes",
                      "Trabajo con fuentes (fragmentos del material, documentos, imágenes descritas o datos): "
                      "identificar autor, contexto y propósito, contrastar dos fuentes y responder preguntas "
                      "de interpretación con citas de la fuente.", False),
        ActivityStyle("ESSAY", "Ensayo o debate",
                      "Una pregunta problemática para argumentar: tesis, al menos dos argumentos con evidencia del "
                      "material, un contraargumento y su refutación. Si es debate, define posturas, turnos y "
                      "tiempos. Da la extensión esperada.", True),
        ActivityStyle("READING", "Comprensión de lectura",
                      "Un texto breve (escrito para la actividad o tomado del material) con preguntas literales, "
                      "inferenciales y críticas; incluye vocabulario clave en contexto.", False),
        ActivityStyle("WRITING", "Producción escrita",
                      "Una tarea de escritura con propósito, destinatario y extensión claros, un modelo breve, "
                      "estructura sugerida y una lista de verificación de gramática y vocabulario.", False),
        ActivityStyle("ORAL", "Expresión oral",
                      "Una actividad para hablar (presentación, diálogo o juego de roles) con preparación guiada, "
                      "frases útiles, tiempo por persona y qué se observará al evaluar.", False),
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

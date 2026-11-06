from typing import Literal

from pydantic import BaseModel, Field


class WorkshopActivity(BaseModel):
    title: str = Field(description="Título breve y concreto de la actividad, en español.")
    goal: str = Field(default="", description="Para qué sirve esta actividad, en una frase dirigida al estudiante.")
    instructions: str = Field(
        description="Pasos numerados (1., 2., 3.…) con los datos, ejemplos o código que el estudiante necesita."
    )
    hints: list[str] = Field(default_factory=list, description="De 0 a 3 pistas graduadas para quien se atasque.")
    deliverable: str = Field(default="", description="Qué entrega o muestra el estudiante al terminar, verificable.")
    estimatedMinutes: int = Field(description="Duración estimada en minutos.")


class AssessmentQuestion(BaseModel):
    question: str = Field(description="Pregunta de evaluación en español.")
    options: list[str] = Field(description="Opciones; usa una lista vacía para preguntas abiertas.")
    correctAnswer: str = Field(description="Respuesta correcta o criterios esperados.")
    explanation: str = Field(description="Explicación educativa de la respuesta.")


class WorkshopResponse(BaseModel):
    title: str = Field(description="Título claro del taller, en español.")
    subject: str = Field(description="Materia indicada en la solicitud.")
    targetLevel: Literal["LOW", "MEDIUM", "HIGH"]
    summary: str = Field(description="Resumen del propósito del taller, dos o tres frases.")
    studentIntro: str = Field(
        default="",
        description="'Antes de empezar': explicación breve del concepto clave con un ejemplo, dirigida al estudiante.",
    )
    learningObjectives: list[str] = Field(description="Entre dos y cuatro objetivos observables.")
    activities: list[WorkshopActivity] = Field(description="Actividades graduadas, con instrucciones concretas.")
    assessment: list[AssessmentQuestion] = Field(description="Preguntas para comprobar el aprendizaje.")
    teacherNotes: list[str] = Field(
        default_factory=list,
        description="De 2 a 4 notas solo para el docente: preparación, errores frecuentes y cómo cerrar.",
    )
    sourceReferences: list[str] = Field(description="Páginas o secciones del material usadas en la respuesta.")

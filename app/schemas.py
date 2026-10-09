from typing import Literal

from pydantic import BaseModel, Field


class WorkshopActivity(BaseModel):
    title: str = Field(description="Título breve de esta actividad, en español.")
    instructions: str = Field(description="Instrucciones paso a paso para el estudiante.")
    estimatedMinutes: int = Field(description="Duración estimada entre 5 y 60 minutos.")


class AssessmentQuestion(BaseModel):
    question: str = Field(description="Pregunta de evaluación en español.")
    options: list[str] = Field(description="Opciones; usa una lista vacía para preguntas abiertas.")
    correctAnswer: str = Field(description="Respuesta correcta o criterios esperados.")
    explanation: str = Field(description="Explicación educativa de la respuesta.")


class WorkshopResponse(BaseModel):
    title: str = Field(description="Título claro del taller, en español.")
    subject: str = Field(description="Materia indicada en la solicitud.")
    targetLevel: Literal["LOW", "MEDIUM", "HIGH"]
    summary: str = Field(description="Resumen del propósito del taller.")
    learningObjectives: list[str] = Field(description="Entre dos y cuatro objetivos observables.")
    activities: list[WorkshopActivity] = Field(description="Actividades graduadas, con instrucciones concretas.")
    assessment: list[AssessmentQuestion] = Field(description="Preguntas para comprobar el aprendizaje.")
    sourceReferences: list[str] = Field(description="Páginas o secciones del material usadas en la respuesta.")

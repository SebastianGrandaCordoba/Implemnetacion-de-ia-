# Reglas de calidad del taller

Cada taller generado pasa por `validate_workshop` antes de llegar al docente. Si una regla falla,
el servicio responde 502 con el mensaje de la regla y el backend puede pedir otro intento.

| Regla | Qué exige |
| --- | --- |
| `activity_count` | Entre 3 y 5 actividades |
| `question_count` | Entre 3 y 5 preguntas de evaluación |
| `objective_count` | Entre 2 y 4 objetivos de aprendizaje |
| `activity_minutes` | Cada actividad dura entre 5 y 60 minutos |
| `has_references` | Al menos una referencia al material |
| `verifiable_references` | Las páginas, secciones o líneas citadas existen en el material |
| `option_count` | Las preguntas cerradas tienen entre 2 y 5 opciones distintas |
| `answers_in_options` | La respuesta correcta de una pregunta cerrada está entre sus opciones |
| `distinct_questions` | No hay preguntas repetidas |

Para agregar una regla: escribe una función `(workshop, material_text) -> str | None`, pruébala en
`tests/test_rule_<nombre>.py` y añádela a `RULES`.

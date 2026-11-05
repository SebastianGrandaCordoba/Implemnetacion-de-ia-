# Cambios

## 1.1.0
- Capa de dominio pura: prompt, reglas de calidad, errores, reglas de la solicitud y finalización.
- Reglas nuevas para quizzes: respuestas dentro de las opciones, opciones distintas y preguntas sin repetir.
- Decoradores de caché, reintento con espera exponencial y medición de tiempo alrededor de Gemini.
- Límite de generaciones por minuto con respuesta 429 y `Retry-After`.
- Rutas `GET /api/v1/limits` y `POST /api/v1/materials/inspect`.
- Middleware con `X-Request-ID` y `Server-Timing`; errores inesperados sin detalles internos.
- Configuración numérica con rangos y valores por defecto seguros.
- Pruebas de API, lectores de documentos y adaptador Gemini; ruff y GitHub Actions.

## 1.0.0
- Generación de talleres y quizzes desde PDF, DOCX y TXT con Gemini.

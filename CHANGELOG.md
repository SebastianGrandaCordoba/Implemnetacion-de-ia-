# Cambios

## 1.3.0
- Tipos de trabajo al crear un taller: ejercicios guiados, programar código, construir una aplicación,
  desplegar en internet, caso de estudio y proyecto en equipo (hasta tres a la vez).
- Los trabajos de código, aplicación, despliegue y equipo se plantean como retos por etapas, con más tiempo
  por actividad (hasta 120 minutos) y entregables verificables (repositorio, pruebas, URL pública).

## 1.2.0
- Generación más rápida: nivel de razonamiento bajo y más margen de salida para no cortar el JSON.
- Reparación automática de defectos menores antes de validar, para rechazar menos talleres.
- Citas sin tildes ("Pagina 2") se aceptan.
- Solo se reintentan errores rápidos (cuota y saturación) y nunca después de 25 s, para no superar el tiempo del backend.
- Gemini saturado ya no se informa como modelo inexistente.

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

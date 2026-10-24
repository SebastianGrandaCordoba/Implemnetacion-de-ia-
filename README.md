#   FairTeam AI Service

Servicio Python separado que recibe material de estudio y genera un taller de refuerzo en español con actividades, evaluación y referencias al documento. El backend Java es el único consumidor previsto; el servicio requiere un token interno y mantiene la clave de Gemini del lado servidor.
 
## Arquitectura hexagonal

`Frontend → API backend → adaptador HTTP FastAPI → caso de uso → puertos → adaptadores de documentos/Gemini`

El caso de uso `GenerateWorkshop` coordina la extracción y generación mediante los puertos definidos en `app/application/ports.py`. `DocumentMaterialAdapter` y `GeminiWorkshopAdapter` son adaptadores de salida; `app/main.py` es el adaptador HTTP de entrada y el punto de composición. Esto permite probar el flujo con dependencias simuladas y cambiar el proveedor o parser sin cambiar la ruta pública.

La ruta y el DTO de respuesta permanecen compatibles con el backend Java:

`Frontend → Backend Spring Boot → este servicio → Gemini → Backend → Frontend`
 
Este servicio no recibe nombres, correos, identificadores ni calificaciones individuales. El backend puede enviar un contexto agregado de hasta 2500 caracteres (recuento por nivel, promedio del curso y tema priorizado), además del documento, la materia, el nivel de refuerzo y el objetivo didáctico.

El documento cargado se procesa en memoria y su texto se envía a la API Gemini para generar la respuesta. Usa únicamente material que el docente esté autorizado a procesar; para las primeras pruebas, usa documentos de demostración y datos ficticios, nunca calificaciones o identificadores personales.

## Requisitos y ejecución local  
 
Se requiere Python 3.11 o posterior.
 
```powershell 
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1  
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` localmente e indica `GEMINI_API_KEY` y `AI_SERVICE_TOKEN`. Nunca compartas esos valores ni subas `.env` al repositorio. El backend debe tener el mismo `AI_SERVICE_TOKEN` y la URL de este servicio en `AI_SERVICE_URL`.

Inicia el servidor:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Documentación HTTP local: `http://127.0.0.1:8000/docs`. Estado de servicio: `GET /health`.

## API compatible con el backend Java

`POST /api/v1/workshops/generate` como `multipart/form-data`, con cabecera `X-AI-Service-Token`:

- `file`: PDF, DOCX o TXT; máximo 10 MB.
- `subject`: materia, máximo 120 caracteres.
- `targetLevel`: LOW, MEDIUM o HIGH (acepta BAJO, INTERMEDIO y ALTO).
- `learningObjective`: opcional, máximo 1000 caracteres.
- `learningContext`: opcional, máximo 2500 caracteres; solo debe contener datos agregados sin identificar estudiantes.

La respuesta sigue el DTO `WorkshopGenerationResponseDTO` del backend: título, materia, nivel, resumen, objetivos, actividades, evaluación y referencias de páginas/secciones.

Los PDF escaneados sin texto seleccionable no funcionan todavía; requieren OCR. Si el documento supera el límite de texto extraído, el servicio pide subir un capítulo más corto en vez de cortar contenido silenciosamente. La generación cita referencias solicitadas, pero el docente debe revisar el taller antes de asignarlo.

## Variables para Render

El archivo `render.yaml` propone el servicio web y sus variables. Al crear el servicio desde el repositorio, configura `GEMINI_API_KEY` y `AI_SERVICE_TOKEN` como secretos, `GEMINI_MODEL=gemini-3.5-flash-lite` y las mismas variables en el backend (`AI_SERVICE_URL` y `AI_SERVICE_TOKEN`). La aplicación migra automáticamente el valor anterior `gemini-3.8-flash` al modelo rápido. No pongas la clave Gemini en el frontend ni en el backend.
# Respuesta de generación

La generación se ejecuta únicamente cuando el docente solicita un taller. Usa Gemini 3.5 Flash-Lite y un prompt breve; el tiempo máximo se controla con `GEMINI_TIMEOUT_MS` (60 segundos por defecto, hasta 75 segundos para tolerar demoras del proveedor). El tablero de alertas usa cálculos locales y no espera a Gemini. En instancias gratuitas de Render, una petición tras 15 minutos inactiva puede esperar el arranque del servicio.

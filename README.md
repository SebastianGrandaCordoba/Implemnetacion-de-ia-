# FairTeam AI Service

Servicio Python separado que recibe material de estudio y genera un taller de refuerzo en español con actividades, evaluación y referencias al documento. El backend Java es el único consumidor previsto; el servicio requiere un token interno y mantiene la clave de Gemini del lado servidor.

## Arquitectura hexagonal

`Frontend → API backend → adaptador HTTP FastAPI → caso de uso → puertos → adaptadores de documentos/Gemini`

El caso de uso `GenerateWorkshop` coordina la extracción y generación mediante los puertos definidos en `app/application/ports.py`. `DocumentMaterialAdapter` y `GeminiWorkshopAdapter` son adaptadores de salida; `app/main.py` es el adaptador HTTP de entrada y el punto de composición. Esto permite probar el flujo con dependencias simuladas y cambiar el proveedor o parser sin cambiar la ruta pública.

Más detalle en [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md) y [docs/quality-rules.md](docs/quality-rules.md).

### Estructura

```
app/
  domain/        reglas puras: prompt, validación, errores, límites, estadísticas
  application/   casos de uso (GenerateWorkshop, InspectMaterials) y puertos
  adapters/      Gemini, documentos, decoradores de resiliencia y middleware HTTP
  main.py        adaptador HTTP de entrada y raíz de composición
tests/           pruebas unitarias y de API sin llamar a Gemini
```

### Patrones de diseño

- **Puertos y adaptadores**: el caso de uso solo conoce `MaterialTextExtractor` y `WorkshopGenerator`.
- **Strategy**: `EXTRACTORS` elige el lector según la extensión (PDF, DOCX, TXT).
- **Specification**: cada regla de calidad de `app/domain/validation.py` devuelve un error o `None`.
- **Decorator**: `CachedWorkshopGenerator → RetryingWorkshopGenerator → TimedWorkshopGenerator → Gemini`.
- **Factory**: `create_client` construye el cliente Gemini y permite reemplazarlo en pruebas.

La ruta y el DTO de respuesta permanecen compatibles con el backend Java:

`Frontend → Backend Spring Boot → este servicio → Gemini → Backend → Frontend`

Este servicio no recibe nombres, correos, identificadores ni calificaciones individuales. El backend puede enviar un contexto agregado de hasta 2500 caracteres (recuento por nivel, promedio del curso y tema priorizado), además del documento, la materia, el nivel de refuerzo y el objetivo didáctico.

El documento cargado se procesa en memoria y su texto se envía a la API Gemini para generar la respuesta. Usa únicamente material que el docente esté autorizado a procesar; para las primeras pruebas, usa documentos de demostración y datos ficticios, nunca calificaciones o identificadores personales.

## Requisitos y ejecución local

Se requiere Python 3.12 o posterior.

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

### Otras rutas

- `GET /api/v1/limits`: límites vigentes (formatos, tamaño, materiales, niveles y tipos) para mostrarlos antes de subir archivos.
- `POST /api/v1/materials/inspect`: recibe `files` y devuelve, por archivo, caracteres, palabras, páginas/secciones/líneas detectadas, tokens estimados y una vista previa. No llama a Gemini.

Todas las rutas `/api/v1` exigen `X-AI-Service-Token`. Las respuestas incluyen `X-Request-ID` (se reutiliza el del backend si es válido) y `Server-Timing`.

### Códigos de error

| Código | Cuándo |
| --- | --- |
| 400 | Nivel, tipo, nombre de archivo, cantidad de materiales o textos fuera de límite |
| 401 | Token interno ausente o incorrecto |
| 413 | Los materiales juntos superan 10 MB |
| 422 | El documento no se puede leer, no tiene texto o es demasiado largo |
| 429 | Demasiadas generaciones por minuto (incluye `Retry-After`) |
| 502 | Gemini respondió con error o el taller no cumplió las reglas de calidad |
| 503 | Falta configurar el token interno o la clave de Gemini |

## Variables para Render

El archivo `render.yaml` propone el servicio web y sus variables. Al crear el servicio desde el repositorio, configura `GEMINI_API_KEY` y `AI_SERVICE_TOKEN` como secretos, `GEMINI_MODEL=gemini-3.5-flash-lite` y las mismas variables en el backend (`AI_SERVICE_URL` y `AI_SERVICE_TOKEN`). La aplicación migra automáticamente el valor anterior `gemini-3.8-flash` al modelo rápido. No pongas la clave Gemini en el frontend ni en el backend.

## Configuración

| Variable | Defecto | Rango |
| --- | --- | --- |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | — |
| `GEMINI_TIMEOUT_MS` | 60000 | 5000–75000 |
| `MAX_UPLOAD_BYTES` | 10485760 | hasta 10 MB |
| `MAX_EXTRACTED_CHARS` | 30000 | 5000–30000 |
| `GENERATION_ATTEMPTS` | 2 | 1–3 (solo reintenta cuota y tiempo de espera) |
| `GENERATION_CACHE_ENTRIES` | 32 | 0–256 (0 desactiva la caché) |
| `GENERATIONS_PER_MINUTE` | 12 | 0–120 (0 desactiva el límite) |

Un valor no numérico vuelve al valor por defecto en lugar de impedir el arranque.

## Pruebas

```bash
pip install -r requirements-dev.txt
make lint
make test
```

Las pruebas usan documentos generados en memoria y un cliente Gemini falso, así que no consumen cuota ni necesitan clave. GitHub Actions ejecuta `ruff` y `pytest` en cada push.

## Tiempo de respuesta


La generación se ejecuta únicamente cuando el docente solicita un taller. Usa Gemini 3.5 Flash-Lite y un prompt breve; el tiempo máximo se controla con `GEMINI_TIMEOUT_MS` (60 segundos por defecto, hasta 75 segundos para tolerar demoras del proveedor). El tablero de alertas usa cálculos locales y no espera a Gemini. En instancias gratuitas de Render, una petición tras 15 minutos inactiva puede esperar el arranque del servicio.

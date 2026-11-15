# FairTeam AI Service

Separate Python service that receives study material and generates a reinforcement workshop in Spanish with activities, an assessment and references to the document. The Java backend is the only intended consumer; the service requires an internal token and keeps the Gemini key on the server side.

## Hexagonal architecture

`Frontend → backend API → FastAPI HTTP adapter → use case → ports → document/Gemini adapters`

The `GenerateWorkshop` use case coordinates extraction and generation through the ports defined in `app/application/ports.py`. `DocumentMaterialAdapter` and `GeminiWorkshopAdapter` are output adapters; `app/main.py` is the input HTTP adapter and the composition point. This makes it possible to test the flow with fake dependencies and to change the provider or parser without changing the public route.

More detail in [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md) and [docs/quality-rules.md](docs/quality-rules.md).

### Structure

```
app/
  domain/        pure rules: prompt, validation, errors, limits, statistics
  application/   use cases (GenerateWorkshop, InspectMaterials) and ports
  adapters/      Gemini, documents, resilience decorators and HTTP middleware
  main.py        input HTTP adapter and composition root
tests/           unit and API tests that do not call Gemini
```

### Design patterns

- **Ports and adapters**: the use case only knows `MaterialTextExtractor` and `WorkshopGenerator`.
- **Strategy**: `EXTRACTORS` chooses the reader by extension (PDF, DOCX, TXT).
- **Specification**: each quality rule in `app/domain/validation.py` returns an error or `None`.
- **Decorator**: `CachedWorkshopGenerator → RetryingWorkshopGenerator → TimedWorkshopGenerator → Gemini`.
- **Factory**: `create_client` builds the Gemini client and lets tests replace it.

The route and the response DTO remain compatible with the Java backend:

`Frontend → Spring Boot backend → this service → Gemini → Backend → Frontend`

This service does not receive names, emails, identifiers or individual grades. The backend may send an aggregated context of up to 2500 characters (count per level, course average and prioritized topic), in addition to the document, the subject, the reinforcement level and the learning objective.

The uploaded document is processed in memory and its text is sent to the Gemini API to generate the response. Use only material the teacher is authorized to process; for the first tests, use demo documents and fictional data, never grades or personal identifiers.

## Requirements and local run

Python 3.12 or later is required.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally and set `GEMINI_API_KEY` and `AI_SERVICE_TOKEN`. Never share those values or commit `.env` to the repository. The backend must have the same `AI_SERVICE_TOKEN` and this service's URL in `AI_SERVICE_URL`.

Start the server:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Local HTTP documentation: `http://127.0.0.1:8000/docs`. Service status: `GET /health`.

## API compatible with the Java backend

`POST /api/v1/workshops/generate` as `multipart/form-data`, with the `X-AI-Service-Token` header:

- `file`: PDF, DOCX or TXT; maximum 10 MB.
- `subject`: subject, maximum 120 characters.
- `targetLevel`: LOW, MEDIUM or HIGH (also accepts the Spanish aliases BAJO, INTERMEDIO and ALTO).
- `learningObjective`: optional, maximum 1000 characters.
- `learningContext`: optional, maximum 2500 characters; it must only contain aggregated data that does not identify students.

The response follows the backend's `WorkshopGenerationResponseDTO`: title, subject, level, summary, objectives, activities, assessment and page/section references.

Scanned PDFs without selectable text do not work yet; they require OCR. If the document exceeds the extracted-text limit, the service asks for a shorter chapter instead of silently cutting content. Generation cites the requested references, but the teacher must review the workshop before assigning it.

### Other routes

- `GET /api/v1/limits`: current limits (formats, size, materials, levels and types) to show before uploading files.
- `POST /api/v1/materials/inspect`: takes `files` and returns, per file, characters, words, detected pages/sections/lines, estimated tokens and a preview. It does not call Gemini.

All `/api/v1` routes require `X-AI-Service-Token`. Responses include `X-Request-ID` (the backend's is reused if valid) and `Server-Timing`.

### Error codes

| Code | When |
| --- | --- |
| 400 | Level, type, file name, number of materials or texts out of limits |
| 401 | Internal token missing or wrong |
| 413 | The materials together exceed 10 MB |
| 422 | The document cannot be read, has no text or is too long |
| 429 | Too many generations per minute (includes `Retry-After`) |
| 502 | Gemini answered with an error or the workshop did not meet the quality rules |
| 503 | The internal token or the Gemini key is not configured |

## Render variables

The `render.yaml` file proposes the web service and its variables. When creating the service from the repository, set `GEMINI_API_KEY` and `AI_SERVICE_TOKEN` as secrets, `GEMINI_MODEL=gemini-3.5-flash-lite` and the same variables in the backend (`AI_SERVICE_URL` and `AI_SERVICE_TOKEN`). The application automatically migrates the old value `gemini-3.8-flash` to the fast model. Do not put the Gemini key in the frontend or in the backend.

## Configuration

| Variable | Default | Range |
| --- | --- | --- |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | — |
| `GEMINI_TIMEOUT_MS` | 60000 | 5000–75000 |
| `MAX_UPLOAD_BYTES` | 10485760 | up to 10 MB |
| `MAX_EXTRACTED_CHARS` | 30000 | 5000–30000 |
| `GENERATION_ATTEMPTS` | 2 | 1–3 (only retries quota and timeouts) |
| `GENERATION_CACHE_ENTRIES` | 32 | 0–256 (0 disables the cache) |
| `GENERATIONS_PER_MINUTE` | 12 | 0–120 (0 disables the limit) |
| `GEMINI_THINKING_LEVEL` | `LOW` | `MINIMAL`, `LOW`, `MEDIUM`, `HIGH` or `OFF` |

Before validating, the service fixes small defects in the workshop (extra activities, minutes out of range,
repeated questions or options, answers written as a letter, invented citations next to real ones). An
answer that matches no option turns the question into an open one instead of giving a wrong key.
Only what cannot be fixed without inventing content is rejected.

A non-numeric value falls back to the default instead of preventing startup.

## Tests

```bash
pip install -r requirements-dev.txt
make lint
make test
```

The tests use documents generated in memory and a fake Gemini client, so they use no quota and need no key. GitHub Actions runs `ruff` and `pytest` on every push.

## Response time

Generation only runs when the teacher requests a workshop. It uses Gemini 3.5 Flash-Lite and a short prompt; the maximum time is controlled with `GEMINI_TIMEOUT_MS` (60 seconds by default, up to 75 seconds to tolerate provider delays). The alerts board uses local calculations and does not wait for Gemini. On free Render instances, a request after 15 idle minutes may wait for the service to start.

# HTTP API

All `/api/v1` routes require the `X-AI-Service-Token` header.

## GET /health
No authentication. Returns `status`, `version`, `uptimeSeconds`, `provider`, `model` and
`generationConfigured`. It never includes keys.

## GET /api/v1/limits
```json
{"maxMaterials": 6, "maxUploadBytes": 10485760, "maxExtractedChars": 30000,
 "maxObjectiveChars": 1000, "maxContextChars": 2500, "formats": ["pdf", "docx", "txt"],
 "levels": ["LOW", "MEDIUM", "HIGH"], "generationTypes": ["QUIZ", "WORKSHOP"]}
```

## POST /api/v1/materials/inspect
`multipart/form-data` with one to six `files`. It does not call Gemini.
```json
{"totalCharacters": 5120, "maxExtractedChars": 30000, "fitsLimit": true,
 "materials": [{"filename": "guia.pdf", "characters": 5120, "words": 830, "units": {"Página": 4},
                "estimatedTokens": 1280, "preview": "Ecosistemas y cadenas tróficas..."}]}
```

## POST /api/v1/workshops/generate
Fields: `subject`, `targetLevel`, `learningObjective`, `learningContext`, `generationType`
(`WORKSHOP` or `QUIZ`), `activityStyles` and `file` or up to six `files`. Returns the complete workshop.

`activityStyles` is optional: up to three of `GUIDED` (guided exercises, the default), `CODE` (write
code), `APP` (build an application), `DEPLOY` (deploy to the internet), `CASE` (case study) and `TEAM`
(team project), separated by commas. `CODE`, `APP`, `DEPLOY` and `TEAM` allow activities of up to
120 minutes with stages in and out of class; the rest stay within one class session.
It may answer 429 with `Retry-After` if the generations-per-minute limit is exceeded.

## Errors
Body `{"detail": "..."}` in Spanish (the messages are shown to teachers). Unhandled errors answer 500 with
`{"detail": "...", "requestId": "..."}` so the trace can be found in the logs.

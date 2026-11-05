# API HTTP

Todas las rutas `/api/v1` requieren la cabecera `X-AI-Service-Token`.

## GET /health
Sin autenticación. Devuelve `status`, `version`, `uptimeSeconds`, `provider`, `model` y
`generationConfigured`. Nunca incluye claves.

## GET /api/v1/limits
```json
{"maxMaterials": 6, "maxUploadBytes": 10485760, "maxExtractedChars": 30000,
 "maxObjectiveChars": 1000, "maxContextChars": 2500, "formats": ["pdf", "docx", "txt"],
 "levels": ["LOW", "MEDIUM", "HIGH"], "generationTypes": ["QUIZ", "WORKSHOP"]}
```

## POST /api/v1/materials/inspect
`multipart/form-data` con uno a seis `files`. No llama a Gemini.
```json
[{"filename": "guia.pdf", "characters": 5120, "words": 830, "units": {"Página": 4},
  "estimatedTokens": 1280, "preview": "Ecosistemas y cadenas tróficas..."}]
```

## POST /api/v1/workshops/generate
Campos: `subject`, `targetLevel`, `learningObjective`, `learningContext`, `generationType`
(`WORKSHOP` o `QUIZ`) y `file` o hasta seis `files`. Responde el taller completo.
Puede responder 429 con `Retry-After` si se superan las generaciones por minuto.

## Errores
Cuerpo `{"detail": "..."}` en español. Los errores no controlados responden 500 con
`{"detail": "...", "requestId": "..."}` para buscar la traza en los registros.

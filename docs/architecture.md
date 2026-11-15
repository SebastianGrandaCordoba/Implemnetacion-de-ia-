# AI service architecture

```
Spring backend ──HTTP + X-AI-Service-Token──▶ FastAPI (app/main.py)
                                                │  RequestContextMiddleware (X-Request-ID, Server-Timing)
                                                │  require_backend_token → limit_generations
                                                ▼
                                   GenerateWorkshop (application)
                                     │                         │
                     MaterialTextExtractor              WorkshopGenerator
                                     │                         │
                     DocumentMaterialAdapter      CachedWorkshopGenerator
                       └ EXTRACTORS (PDF/DOCX/TXT)   └ RetryingWorkshopGenerator
                                                       └ TimedWorkshopGenerator
                                                         └ GeminiWorkshopAdapter
                                                           ├ build_prompt (domain)
                                                           ├ validate_workshop (domain)
                                                           └ finalize_workshop (domain)
```

## Layers

- **domain**: pure functions with no FastAPI or Gemini. Prompt, quality rules, error classification,
  request rules, material statistics and the rate limiter.
- **application**: the `GenerateWorkshop` and `InspectMaterials` use cases and the ports they need.
- **adapters**: concrete implementations (Gemini, document reading, decorators, middleware).
- **main.py**: input HTTP adapter and composition root; it is the only place that knows every piece.

## Decisions

- The service never receives students' personal data; only material and aggregated context.
- Provider errors are translated into Spanish messages with no account details.
- The cache returns copies so nobody can modify a stored result.
- Only transient errors (quota and timeout) are retried; an invalid key fails immediately.

# Arquitectura del servicio de IA

```
Backend Spring ──HTTP + X-AI-Service-Token──▶ FastAPI (app/main.py)
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

## Capas

- **domain**: funciones puras sin FastAPI ni Gemini. Prompt, reglas de calidad, clasificación de errores,
  reglas de la solicitud, estadísticas del material y limitador de ritmo.
- **application**: casos de uso `GenerateWorkshop` e `InspectMaterials` y los puertos que necesitan.
- **adapters**: implementaciones concretas (Gemini, lectura de documentos, decoradores, middleware).
- **main.py**: adaptador HTTP de entrada y raíz de composición; es el único lugar que conoce todas las piezas.

## Decisiones

- El servicio nunca recibe datos personales de estudiantes; solo material y contexto agregado.
- Los errores del proveedor se traducen a mensajes en español sin detalles de la cuenta.
- La caché devuelve copias para que nadie modifique un resultado guardado.
- Solo se reintentan errores transitorios (cuota y tiempo de espera); una clave inválida falla de inmediato.

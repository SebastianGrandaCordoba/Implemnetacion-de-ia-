# Changelog

## 1.8.1

- Búho answers any message (greetings with typos, general knowledge, writing help) instead of asking to rephrase; reply limit raised to 220 words.

## 1.8.0
- `POST /speak`: Búho's natural voice with Gemini TTS (`gemini-3.1-flash-tts-preview`, falling back to
  `gemini-2.5-flash-preview-tts`), voice `Achird` in neutral, warm Latin American Spanish. Returns WAV.
  Configured with `GEMINI_TTS_MODEL` and `GEMINI_TTS_VOICE`; it uses the same `GEMINI_API_KEY`.
- Repeated phrases (the day's summary, the voice test) are served from memory; at most 30 per minute.

## 1.7.0
- `POST /assistant/interpret`: Búho's interpreter. It reads a free-form request from the teacher together with the
  previous conversation and the course context, and returns a single action (create a workshop, quiz or custom
  activity, create a rubric for a saved activity, write to a student, open a section, answer a pedagogical question…).
- Students, activities and courses arrive as codes (E3, A2, C1); the service discards invented codes.
- The fast model answers first (12 s) and, if it fails, the quality model (15 s).
- The interpreter receives the platform manual and answers "how do I…?" with the `how_to` action and the topic
  id, without inventing features that do not exist.
- The rubric is only retried if the second attempt fits within the backend's wait.

## 1.6.0
- Workshops and quizzes also without material: they are written from the teacher's topic or objective.
- Work types for all areas: problem solving, lab work, source analysis, essay or
  debate, reading comprehension, written production and oral expression. The prompt does not ask for programming unless the
  subject or the teacher asks for it.
- Whole books: if the material exceeds the limit, the pages most related to the requested topic are sent
  (in their original order, with their page numbers) instead of rejecting the file. Up to 600 pages are read.
- Several materials split the text budget into fair parts.
- Gemini: the quality model has 32 s; if it is slow, overloaded or fails, the fast model answers (40 s).
  The SDK's internal retries are off so the backend's time limit is not exceeded.

## 1.5.0
- `POST /generate-rubric`: analytic rubric (3 to 6 criteria, weights adding up to 100 and four levels:
  Excellent, Good, Basic, Insufficient) from the description of an activity or of a generated workshop.

## 1.4.0
- Custom mode (`generationType=CUSTOM`): the teacher describes the workshop in their own words in `teacherPrompt`
  (up to 2000 characters) and the material becomes optional. Without material, the reference is "Indicaciones del docente".
- In workshops and quizzes, `teacherPrompt` serves as additional instructions from the teacher.
- More complete workshops: "Before you start" for the student, purpose, graduated hints and deliverable per
  activity, teacher-only notes and questions built from frequent mistakes.
- Each request type has its own shape: workshop (3-4 activities, 4-5 questions), quiz (5-8 questions) and
  custom (whatever the teacher asks for, 1 to 6 activities).
- Default model `gemini-3.7-flash`, with `gemini-3.5-flash-lite` as a fallback if it is unavailable.

## 1.3.0
- Work types when creating a workshop: guided exercises, writing code, building an application,
  deploying to the internet, case study and team project (up to three at once).
- Code, application, deployment and team work is posed as staged challenges, with more time
  per activity (up to 120 minutes) and verifiable deliverables (repository, tests, public URL).

## 1.2.0
- Faster generation: low reasoning level and more output headroom so the JSON is not cut off.
- Automatic repair of minor defects before validating, to reject fewer workshops.
- Citations without accents ("Pagina 2") are accepted.
- Only fast errors (quota and overload) are retried, and never after 25 s, so the backend's time limit is not exceeded.
- An overloaded Gemini is no longer reported as a nonexistent model.

## 1.1.0
- Pure domain layer: prompt, quality rules, errors, request rules and finalization.
- New quiz rules: answers within the options, distinct options and no repeated questions.
- Cache, exponential-backoff retry and timing decorators around Gemini.
- Per-minute generation limit with a 429 response and `Retry-After`.
- Routes `GET /api/v1/limits` and `POST /api/v1/materials/inspect`.
- Middleware with `X-Request-ID` and `Server-Timing`; unexpected errors without internal details.
- Numeric configuration with ranges and safe defaults.
- API, document reader and Gemini adapter tests; ruff and GitHub Actions.

## 1.0.0
- Workshop and quiz generation from PDF, DOCX and TXT with Gemini.

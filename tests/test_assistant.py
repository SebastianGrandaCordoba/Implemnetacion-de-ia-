import json
import unittest
from types import SimpleNamespace
from unittest import mock

from app import main
from app.config import get_settings
from app.domain.assistant import (
    ActivityCode,
    CourseCode,
    Interpretation,
    InterpretRequest,
    StudentCode,
    TopicAverage,
    Turn,
    build_interpret_prompt,
    clean_interpretation,
)
from app.gemini_service import GeminiGenerationError, interpret_request
from tests.api_support import FakeUseCase, client_with, close


def request(message: str = "hazle uno de reto a ella también", **overrides) -> InterpretRequest:
    data = dict(
        message=message,
        history=[Turn(role="teacher", text="crea un quiz de derivadas para E2"),
                 Turn(role="buho", text="Listo, creé el quiz.")],
        course="Cálculo I",
        summary="20 estudiantes: 3 en refuerzo.",
        topics=[TopicAverage(name="Derivadas", average=2.9), TopicAverage(name="Límites", average=None)],
        students=[StudentCode(code="E1", level="buen progreso"),
                  StudentCode(code="E2", level="refuerzo", weakest="Derivadas")],
        activities=[ActivityCode(code="A1", kind="quiz", title="Quiz de derivadas", topic="Derivadas", created="hoy")],
        courses=[CourseCode(code="C2", name="Álgebra")],
    )
    data.update(overrides)
    return InterpretRequest(**data)


class InterpretPromptTests(unittest.TestCase):
    def test_prompt_carries_context_history_and_fenced_request(self) -> None:
        prompt = build_interpret_prompt(request())
        self.assertIn("Derivadas: promedio 2.9", prompt)
        self.assertIn("Límites: sin notas", prompt)
        self.assertIn("E2: refuerzo, le cuesta Derivadas", prompt)
        self.assertIn("A1: quiz «Quiz de derivadas»", prompt)
        self.assertIn("Docente: crea un quiz de derivadas para E2", prompt)
        self.assertTrue(prompt.rstrip().endswith("</pedido>"))

    def test_only_the_last_turns_are_sent(self) -> None:
        turns = [Turn(role="teacher", text=f"mensaje {i}") for i in range(15)]
        prompt = build_interpret_prompt(request(history=turns))
        self.assertNotIn("mensaje 6\n", prompt)
        self.assertIn("mensaje 14", prompt)


class CleanInterpretationTests(unittest.TestCase):
    def test_invented_codes_are_dropped(self) -> None:
        invented = Interpretation(action="create_activity", student="E9", activity="A7", topic="x")
        clean = clean_interpretation(invented, request())
        self.assertEqual(clean.student, "")
        self.assertEqual(clean.activity, "")
        self.assertEqual(clean.kind, "workshop")

    def test_message_without_student_asks_who(self) -> None:
        clean = clean_interpretation(Interpretation(action="draft_message"), request())
        self.assertEqual(clean.action, "clarify")
        self.assertIn("estudiante", clean.reply)

    def test_unknown_course_opens_the_course_list(self) -> None:
        clean = clean_interpretation(Interpretation(action="switch_course", course="C8"), request())
        self.assertEqual((clean.action, clean.section), ("open_section", "cursos"))

    def test_how_to_needs_a_manual_entry(self) -> None:
        missing = Interpretation(action="how_to", reply="No existe todavía.")
        clean = clean_interpretation(missing, request("¿puedo pagar?"))
        self.assertEqual(clean.action, "answer")
        kept = clean_interpretation(Interpretation(action="how_to", topic="porcentajes"), request())
        self.assertEqual((kept.action, kept.topic), ("how_to", "porcentajes"))

    def test_the_manual_reaches_the_prompt(self) -> None:
        prompt = build_interpret_prompt(request(manual="- [porcentajes] Porcentajes: toca Poner porcentajes."))
        self.assertIn("[porcentajes] Porcentajes", prompt)

    def test_empty_answer_falls_back_to_the_rules(self) -> None:
        clean = clean_interpretation(Interpretation(action="answer"), request("¿cómo va?"))
        self.assertEqual((clean.action, clean.question), ("ask_course", "¿cómo va?"))


class InterpretModelTests(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "k"}, clear=True):
            self.settings = get_settings()

    def client(self, failing: set[str]):
        calls: list[str] = []

        def generate_content(model, **kwargs):
            calls.append(model)
            if model in failing:
                raise RuntimeError("503 UNAVAILABLE")
            return SimpleNamespace(text=json.dumps({"action": "create_activity", "kind": "workshop", "level": "HIGH",
                                                    "student": "E2", "topic": "Derivadas"}))

        return SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)), calls

    def test_the_fast_model_answers_first(self) -> None:
        client, calls = self.client(set())
        result = interpret_request(self.settings, request(), client)
        self.assertEqual(calls, [self.settings.gemini_fallback_model])
        self.assertEqual((result.action, result.student, result.level), ("create_activity", "E2", "HIGH"))

    def test_the_quality_model_takes_over_when_the_fast_one_fails(self) -> None:
        client, calls = self.client({self.settings.gemini_fallback_model})
        interpret_request(self.settings, request(), client)
        self.assertEqual(calls, [self.settings.gemini_fallback_model, self.settings.gemini_model])

    def test_both_failing_is_an_error(self) -> None:
        client, _ = self.client({self.settings.gemini_fallback_model, self.settings.gemini_model})
        with self.assertRaises(GeminiGenerationError):
            interpret_request(self.settings, request(), client)


class InterpretEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = client_with(FakeUseCase())
        self.seen: list[InterpretRequest] = []

        def fake(req: InterpretRequest) -> Interpretation:
            self.seen.append(req)
            return Interpretation(action="answer", reply="Usa ejemplos cotidianos.")

        main.app.dependency_overrides[main.get_interpreter] = lambda: fake

    def tearDown(self) -> None:
        close(self.client)

    def test_returns_the_interpretation(self) -> None:
        response = self.client.post("/assistant/interpret", json={"message": "¿cómo explico derivadas?"},
                                    headers={"X-AI-Service-Token": "test-token"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["action"], "answer")
        self.assertEqual(self.seen[0].message, "¿cómo explico derivadas?")

    def test_requires_the_backend_token(self) -> None:
        self.assertEqual(self.client.post("/assistant/interpret", json={"message": "hola"}).status_code, 401)


class OpenConversationTest(unittest.TestCase):
    def test_prompt_lets_the_owl_answer_anything_and_infer_typos(self) -> None:
        from app.domain.assistant import build_interpret_prompt

        prompt = build_interpret_prompt(request("hoal brother"))
        self.assertIn("cualquier cosa", prompt)
        self.assertIn("errores de ortografía", prompt)
        self.assertIn("cultura general", prompt)

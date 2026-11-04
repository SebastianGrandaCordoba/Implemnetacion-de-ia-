import json
import unittest
from types import SimpleNamespace
from unittest import mock

from app.config import get_settings
from app.gemini_service import GeminiConfigurationError, GeminiGenerationError, generate_workshop

MATERIAL = "[Línea 1] Fracciones equivalentes\n[Línea 2] Simplificación"


def payload(**overrides) -> str:
    data = {
        "title": "Taller", "subject": "Otro", "targetLevel": "HIGH", "summary": "Resumen",
        "learningObjectives": ["Comparar", "Simplificar"],
        "activities": [
            {"title": f"A{i}", "instructions": "Haz", "estimatedMinutes": 15} for i in range(3)
        ],
        "assessment": [
            {"question": f"P{i}", "options": [], "correctAnswer": "R", "explanation": "E"} for i in range(3)
        ],
        "sourceReferences": ["[Línea 1]"],
    }
    data.update(overrides)
    return json.dumps(data)


def fake_client(text: str | None = None, error: Exception | None = None):
    def generate_content(**kwargs):
        if error:
            raise error
        return SimpleNamespace(text=text)

    return SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))


class GeminiServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "k"}, clear=True):
            self.settings = get_settings()

    def run_with(self, client, **request):
        with mock.patch("app.gemini_service.create_client", return_value=client):
            return generate_workshop(self.settings, material_text=MATERIAL, subject="Matemáticas",
                                     target_level="LOW", learning_objective="", **request)

    def test_missing_key_is_a_configuration_error(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            settings = get_settings()
        with self.assertRaises(GeminiConfigurationError):
            generate_workshop(settings, material_text=MATERIAL, subject="M", target_level="LOW", learning_objective="")

    def test_valid_response_is_finalized(self) -> None:
        workshop = self.run_with(fake_client(payload()))
        self.assertEqual((workshop.subject, workshop.targetLevel), ("Matemáticas", "LOW"))

    def test_empty_response_is_reported(self) -> None:
        with self.assertRaisesRegex(GeminiGenerationError, "no devolvió contenido"):
            self.run_with(fake_client(""))

    def test_malformed_json_gets_a_generic_message(self) -> None:
        with self.assertRaises(GeminiGenerationError) as raised:
            self.run_with(fake_client("{not json"))
        self.assertNotIn("{not json", str(raised.exception))

    def test_validation_failures_are_surfaced(self) -> None:
        with self.assertRaises(GeminiGenerationError):
            self.run_with(fake_client(payload(sourceReferences=[])))

    def test_provider_errors_are_classified(self) -> None:
        with self.assertRaisesRegex(GeminiGenerationError, "cuota"):
            self.run_with(fake_client(error=RuntimeError("429 RESOURCE_EXHAUSTED")))


if __name__ == "__main__":
    unittest.main()

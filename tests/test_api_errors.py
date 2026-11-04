import unittest

from app.document_parser import MaterialError
from app.gemini_service import GeminiConfigurationError, GeminiGenerationError
from tests.api_case import ApiCase, txt
from tests.api_support import FakeUseCase, client_with, close


class ErrorMappingTests(ApiCase):
    def respond_with(self, error: Exception):
        close(self.client)
        self.use_case = FakeUseCase(error=error)
        self.client = client_with(self.use_case)
        return self.post([txt()])

    def test_unreadable_material_is_unprocessable(self) -> None:
        response = self.respond_with(MaterialError("No se encontró texto legible."))
        self.assertEqual(response.status_code, 422)
        self.assertIn("texto legible", response.json()["detail"])

    def test_missing_configuration_is_unavailable(self) -> None:
        self.assertEqual(self.respond_with(GeminiConfigurationError("Falta la clave")).status_code, 503)

    def test_provider_failure_is_bad_gateway(self) -> None:
        response = self.respond_with(GeminiGenerationError("Gemini alcanzó el límite"))
        self.assertEqual(response.status_code, 502)
        self.assertIn("límite", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

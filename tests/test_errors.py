import unittest

from app.domain.errors import DEFAULT, is_retryable, provider_message


class ProviderMessageTests(unittest.TestCase):
    def test_quota_errors_ask_to_wait(self) -> None:
        self.assertIn("cuota", provider_message("429 RESOURCE_EXHAUSTED"))

    def test_credential_errors_point_to_the_key(self) -> None:
        self.assertIn("GEMINI_API_KEY", provider_message("PERMISSION_DENIED: API key not valid"))

    def test_missing_models_point_to_the_model_setting(self) -> None:
        self.assertIn("GEMINI_MODEL", provider_message("404 models/gemini-x is not found"))

    def test_timeouts_suggest_shorter_material(self) -> None:
        self.assertIn("material más corto", provider_message("Deadline exceeded"))

    def test_unknown_errors_get_a_generic_message_without_details(self) -> None:
        message = provider_message("socket closed by peer 10.0.0.3 project=secret-123")
        self.assertEqual(message, DEFAULT)
        self.assertNotIn("secret", message)

    def test_overloaded_model_is_not_reported_as_missing(self) -> None:
        message = provider_message("503 UNAVAILABLE: The model is overloaded. Please try again later.")
        self.assertIn("saturado", message)

    def test_only_fast_transient_errors_are_retryable(self) -> None:
        self.assertTrue(is_retryable(provider_message("429")))
        self.assertTrue(is_retryable(provider_message("503 overloaded")))
        self.assertFalse(is_retryable(provider_message("timed out")))
        self.assertFalse(is_retryable(provider_message("401 unauthorized")))


if __name__ == "__main__":
    unittest.main()

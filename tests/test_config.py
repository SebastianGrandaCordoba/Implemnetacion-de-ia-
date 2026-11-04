import os
import unittest
from unittest import mock

from app.config import get_settings


class SettingsTests(unittest.TestCase):
    def test_defaults_are_safe(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
        self.assertEqual(settings.gemini_model, "gemini-3.5-flash-lite")
        self.assertEqual(settings.max_upload_bytes, 10 * 1024 * 1024)
        self.assertEqual(settings.ai_service_token, "")

    def test_legacy_model_is_upgraded(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash"}, clear=True):
            self.assertEqual(get_settings().gemini_model, "gemini-3.5-flash-lite")

    def test_limits_are_clamped(self) -> None:
        with mock.patch.dict(os.environ, {"MAX_EXTRACTED_CHARS": "999999", "GEMINI_TIMEOUT_MS": "10"}, clear=True):
            settings = get_settings()
        self.assertEqual(settings.max_extracted_chars, 30000)
        self.assertEqual(settings.gemini_timeout_ms, 5000)

    def test_values_are_trimmed(self) -> None:
        with mock.patch.dict(os.environ, {"AI_SERVICE_TOKEN": "  token  "}, clear=True):
            self.assertEqual(get_settings().ai_service_token, "token")


if __name__ == "__main__":
    unittest.main()

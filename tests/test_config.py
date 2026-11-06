import os
import unittest
from unittest import mock

from app.config import get_settings


class SettingsTests(unittest.TestCase):
    def test_defaults_are_safe(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
        self.assertEqual(settings.gemini_model, "gemini-3.7-flash")
        self.assertEqual(settings.gemini_fallback_model, "gemini-3.5-flash-lite")
        self.assertEqual(settings.max_upload_bytes, 10 * 1024 * 1024)
        self.assertEqual(settings.ai_service_token, "")

    def test_legacy_models_are_upgraded(self) -> None:
        for legacy in ("gemini-3.8-flash", "gemini-3.5-flash-lite"):
            with mock.patch.dict(os.environ, {"GEMINI_MODEL": legacy}, clear=True):
                self.assertEqual(get_settings().gemini_model, "gemini-3.7-flash")

    def test_other_models_are_respected(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.6-flash"}, clear=True):
            self.assertEqual(get_settings().gemini_model, "gemini-3.6-flash")

    def test_limits_are_clamped(self) -> None:
        with mock.patch.dict(os.environ, {"MAX_EXTRACTED_CHARS": "999999", "GEMINI_TIMEOUT_MS": "10"}, clear=True):
            settings = get_settings()
        self.assertEqual(settings.max_extracted_chars, 30000)
        self.assertEqual(settings.gemini_timeout_ms, 5000)

    def test_resilience_settings_are_clamped(self) -> None:
        with mock.patch.dict(os.environ, {"GENERATION_ATTEMPTS": "9", "GENERATION_CACHE_ENTRIES": "-4"}, clear=True):
            settings = get_settings()
        self.assertEqual(settings.generation_attempts, 3)
        self.assertEqual(settings.cache_entries, 0)

    def test_invalid_numbers_fall_back_to_defaults(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_TIMEOUT_MS": "60s", "MAX_UPLOAD_BYTES": ""}, clear=True):
            settings = get_settings()
        self.assertEqual(settings.gemini_timeout_ms, 60000)
        self.assertEqual(settings.max_upload_bytes, 10485760)

    def test_upload_limit_cannot_exceed_ten_megabytes(self) -> None:
        with mock.patch.dict(os.environ, {"MAX_UPLOAD_BYTES": "999999999"}, clear=True):
            self.assertEqual(get_settings().max_upload_bytes, 10485760)

    def test_thinking_level_defaults_to_low_and_can_be_disabled(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_settings().gemini_thinking_level, "LOW")
        with mock.patch.dict(os.environ, {"GEMINI_THINKING_LEVEL": "off"}, clear=True):
            self.assertEqual(get_settings().gemini_thinking_level, "")
        with mock.patch.dict(os.environ, {"GEMINI_THINKING_LEVEL": " minimal "}, clear=True):
            self.assertEqual(get_settings().gemini_thinking_level, "MINIMAL")

    def test_values_are_trimmed(self) -> None:
        with mock.patch.dict(os.environ, {"AI_SERVICE_TOKEN": "  token  "}, clear=True):
            self.assertEqual(get_settings().ai_service_token, "token")


if __name__ == "__main__":
    unittest.main()

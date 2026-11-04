import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.main import app


class HealthTests(unittest.TestCase):
    def test_health_reports_model_and_configuration(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k", "GEMINI_MODEL": "gemini-3.5-flash-lite"}, clear=True):
            body = TestClient(app).get("/health").json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["model"], "gemini-3.5-flash-lite")
        self.assertEqual(body["generationConfigured"], "true")

    def test_health_reports_version_and_uptime(self) -> None:
        body = TestClient(app).get("/health").json()
        self.assertEqual(body["version"], app.version)
        self.assertGreaterEqual(body["uptimeSeconds"], 0)

    def test_health_never_exposes_secrets(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "super-secret", "AI_SERVICE_TOKEN": "tok"}, clear=True):
            text = TestClient(app).get("/health").text
        self.assertNotIn("super-secret", text)
        self.assertNotIn("tok\"", text)


if __name__ == "__main__":
    unittest.main()

import unittest

from fastapi.testclient import TestClient

from app.adapters.http_middleware import HEADER, request_id_from
from app.main import app


class RequestIdTests(unittest.TestCase):
    def test_valid_incoming_ids_are_reused(self) -> None:
        self.assertEqual(request_id_from("backend-req-1234"), "backend-req-1234")

    def test_malformed_ids_are_replaced(self) -> None:
        for value in (None, "", "short", "has spaces in it", "x" * 65, "evil\nheader"):
            with self.subTest(value=value):
                generated = request_id_from(value)
                self.assertNotEqual(generated, value)
                self.assertEqual(len(generated), 32)

    def test_responses_echo_the_id_and_timing(self) -> None:
        response = TestClient(app).get("/health", headers={HEADER: "trace-abcdef12"})
        self.assertEqual(response.headers[HEADER], "trace-abcdef12")
        self.assertTrue(response.headers["Server-Timing"].startswith("app;dur="))


if __name__ == "__main__":
    unittest.main()

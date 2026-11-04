import os
import unittest
from unittest import mock

from tests.api_support import FakeUseCase, client_with, close, form, headers

URL = "/api/v1/workshops/generate"
FILE = {"file": ("tema.txt", b"Fracciones", "text/plain")}


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.use_case = FakeUseCase()
        self.client = client_with(self.use_case)

    def tearDown(self) -> None:
        close(self.client)

    def test_missing_token_is_unauthorized(self) -> None:
        self.assertEqual(self.client.post(URL, data=form(), files=FILE).status_code, 401)

    def test_wrong_token_is_unauthorized(self) -> None:
        response = self.client.post(URL, data=form(), files=FILE, headers=headers("nope"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.use_case.requests, [])

    def test_unconfigured_service_is_unavailable(self) -> None:
        with mock.patch.dict(os.environ, {"AI_SERVICE_TOKEN": ""}):
            response = self.client.post(URL, data=form(), files=FILE, headers=headers())
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()

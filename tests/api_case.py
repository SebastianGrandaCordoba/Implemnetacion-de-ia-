"""Base test case for the workshop endpoint."""

import unittest

from tests.api_support import FakeUseCase, client_with, close, form, headers

URL = "/api/v1/workshops/generate"


def txt(name: str = "tema.txt", content: bytes = b"Fracciones"):
    return ("file", (name, content, "text/plain"))


class ApiCase(unittest.TestCase):
    def setUp(self) -> None:
        self.use_case = FakeUseCase()
        self.client = client_with(self.use_case)

    def tearDown(self) -> None:
        close(self.client)

    def post(self, files, **fields):
        return self.client.post(URL, data=form(**fields), files=files, headers=headers())

    def assertRejected(self, response, status: int, fragment: str) -> None:
        self.assertEqual(response.status_code, status, response.text)
        self.assertIn(fragment, response.json()["detail"])
        self.assertEqual(self.use_case.requests, [])

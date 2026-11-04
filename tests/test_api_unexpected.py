import unittest

from tests.api_support import FakeUseCase, client_with, close, form, headers


class UnexpectedErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        use_case = FakeUseCase(error=ZeroDivisionError("secret internals"))
        self.client = client_with(use_case, raise_server_exceptions=False)

    def tearDown(self) -> None:
        close(self.client)

    def test_unexpected_errors_hide_details_and_return_an_id(self) -> None:
        response = self.client.post(
            "/api/v1/workshops/generate",
            data=form(),
            headers=headers(),
            files=[("file", ("tema.txt", b"Fracciones", "text/plain"))],
        )
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret", response.text)
        self.assertEqual(len(response.json()["requestId"]), 32)


if __name__ == "__main__":
    unittest.main()

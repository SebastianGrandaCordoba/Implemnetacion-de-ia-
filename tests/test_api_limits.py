import unittest

from tests.api_support import FakeUseCase, client_with, close, headers


class LimitsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = client_with(FakeUseCase())

    def tearDown(self) -> None:
        close(self.client)

    def test_limits_require_the_token(self) -> None:
        self.assertEqual(self.client.get("/api/v1/limits").status_code, 401)

    def test_limits_describe_formats_and_sizes(self) -> None:
        body = self.client.get("/api/v1/limits", headers=headers()).json()
        self.assertEqual(body["maxMaterials"], 6)
        self.assertEqual(body["formats"], ["pdf", "docx", "txt"])
        self.assertEqual(body["generationTypes"], ["CUSTOM", "QUIZ", "WORKSHOP"])


if __name__ == "__main__":
    unittest.main()

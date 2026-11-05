import unittest

from tests.api_support import FakeUseCase, client_with, close, headers
from tests.fixtures import docx

URL = "/api/v1/materials/inspect"


class InspectEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = client_with(FakeUseCase())

    def tearDown(self) -> None:
        close(self.client)

    def test_requires_the_token(self) -> None:
        response = self.client.post(URL, files=[("files", ("a.txt", b"x", "text/plain"))])
        self.assertEqual(response.status_code, 401)

    def test_describes_each_file(self) -> None:
        files = [
            ("files", ("tema.txt", b"Fracciones\nDecimales", "text/plain")),
            ("files", ("clase.docx", docx(["Introducción"]), "application/octet-stream")),
        ]
        result = self.client.post(URL, files=files, headers=headers()).json()
        self.assertTrue(result["fitsLimit"])
        self.assertEqual(result["totalCharacters"], sum(item["characters"] for item in result["materials"]))
        body = result["materials"]
        self.assertEqual([item["filename"] for item in body], ["tema.txt", "clase.docx"])
        self.assertEqual(body[0]["units"], {"Línea": 2})
        self.assertEqual(body[1]["units"], {"Sección": 1})
        self.assertIn("Fracciones", body[0]["preview"])

    def test_unreadable_files_are_unprocessable(self) -> None:
        files = [("files", ("roto.docx", b"nope", "application/octet-stream"))]
        self.assertEqual(self.client.post(URL, files=files, headers=headers()).status_code, 422)

    def test_bad_names_are_rejected(self) -> None:
        files = [("files", ("x.exe", b"MZ", "application/octet-stream"))]
        self.assertEqual(self.client.post(URL, files=files, headers=headers()).status_code, 400)


if __name__ == "__main__":
    unittest.main()

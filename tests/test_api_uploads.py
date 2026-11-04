import os
import unittest
from unittest import mock

from tests.api_case import ApiCase, txt


def many(count: int):
    return [("files", (f"tema{index}.txt", b"texto", "text/plain")) for index in range(count)]


class UploadTests(ApiCase):
    def test_no_material(self) -> None:
        self.assertRejected(self.post([]), 400, "entre 1 y 6")

    def test_too_many_materials(self) -> None:
        self.assertRejected(self.post(many(7)), 400, "entre 1 y 6")

    def test_mixing_file_and_files(self) -> None:
        self.assertRejected(self.post([txt(), *many(1)]), 400, "un solo campo")

    def test_unsupported_name(self) -> None:
        self.assertRejected(self.post([txt("script.sh")]), 400, "nombre válido")

    def test_empty_file(self) -> None:
        self.assertRejected(self.post([txt(content=b"")]), 400, "está vacío")

    def test_total_size_limit(self) -> None:
        with mock.patch.dict(os.environ, {"MAX_UPLOAD_BYTES": "10"}):
            self.assertRejected(self.post(many(3)), 413, "10 MB")

    def test_several_materials_reach_the_use_case_in_order(self) -> None:
        response = self.post(many(3))
        self.assertEqual(response.status_code, 200, response.text)
        request = self.use_case.requests[0]
        self.assertEqual(request.filename, "tema0.txt")
        self.assertEqual([name for name, _ in request.additional_materials], ["tema1.txt", "tema2.txt"])


if __name__ == "__main__":
    unittest.main()

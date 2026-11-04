import unittest

from app.application.inspect_use_case import InspectMaterials


class InspectTests(unittest.TestCase):
    def test_each_material_is_described_in_order(self) -> None:
        calls = []

        def extract(name, raw, max_chars):
            calls.append((name, max_chars))
            return f"[Línea 1] {raw.decode()}"

        result = InspectMaterials(extract).execute([("a.txt", b"uno"), ("b.txt", b"dos tres")], 9000)
        self.assertEqual([stats.filename for stats in result], ["a.txt", "b.txt"])
        self.assertEqual([stats.words for stats in result], [1, 2])
        self.assertEqual(calls, [("a.txt", 9000), ("b.txt", 9000)])


if __name__ == "__main__":
    unittest.main()

import unittest

from app.domain.prompt import DEFAULT_GUIDANCE, level_guidance


class LevelGuidanceTests(unittest.TestCase):
    def test_each_level_has_its_own_guidance(self) -> None:
        self.assertIn("apoyo inicial", level_guidance("LOW"))
        self.assertIn("práctica guiada", level_guidance(" medium "))
        self.assertIn("transferencia", level_guidance("high"))

    def test_unknown_levels_get_a_safe_default(self) -> None:
        self.assertEqual(level_guidance("EXPERT"), DEFAULT_GUIDANCE)


if __name__ == "__main__":
    unittest.main()

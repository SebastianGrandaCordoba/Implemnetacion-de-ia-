import unittest

from app.domain.finalize import finalize_workshop
from tests.api_support import sample_workshop


class FinalizeTests(unittest.TestCase):
    def test_subject_and_level_come_from_the_request(self) -> None:
        result = finalize_workshop(sample_workshop("HIGH"), subject="Física", target_level="LOW", quiz=False)
        self.assertEqual((result.subject, result.targetLevel), ("Física", "LOW"))
        self.assertEqual(result.title, "Taller de fracciones")

    def test_quizzes_get_a_clear_title(self) -> None:
        result = finalize_workshop(sample_workshop(), subject="Física", target_level="LOW", quiz=True)
        self.assertEqual(result.title, "Quiz breve: Física")

    def test_existing_quiz_titles_are_kept(self) -> None:
        workshop = sample_workshop().model_copy(update={"title": "Quiz de vectores"})
        result = finalize_workshop(workshop, subject="Física", target_level="LOW", quiz=True)
        self.assertEqual(result.title, "Quiz de vectores")


if __name__ == "__main__":
    unittest.main()

import unittest

from app.domain.validation import activity_minutes
from app.schemas import WorkshopActivity
from tests.workshops import workshop

MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class ActivityMinutesTests(unittest.TestCase):
    def test_each_activity_lasts_five_to_sixty_minutes(self) -> None:
        self.assertIsNone(activity_minutes(workshop(), MATERIAL))
        long = [WorkshopActivity(title="A", instructions="1.", estimatedMinutes=90)] * 3
        self.assertIsNotNone(activity_minutes(workshop(activities=long), MATERIAL))


if __name__ == "__main__":
    unittest.main()

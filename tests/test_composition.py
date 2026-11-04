import unittest

from app.adapters.gemini_workshop_generator import GeminiWorkshopAdapter
from app.adapters.resilience import CachedWorkshopGenerator, RetryingWorkshopGenerator, TimedWorkshopGenerator
from app.main import generate_workshop_use_case


class CompositionTests(unittest.TestCase):
    def test_generator_is_decorated_in_order(self) -> None:
        cached = generate_workshop_use_case._generate
        self.assertIsInstance(cached, CachedWorkshopGenerator)
        retrying = cached._inner
        self.assertIsInstance(retrying, RetryingWorkshopGenerator)
        timed = retrying._inner
        self.assertIsInstance(timed, TimedWorkshopGenerator)
        self.assertIsInstance(timed._inner, GeminiWorkshopAdapter)


if __name__ == "__main__":
    unittest.main()

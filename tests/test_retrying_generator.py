import unittest

from app.adapters.resilience import RetryingWorkshopGenerator
from app.domain.errors import provider_message
from app.gemini_service import GeminiGenerationError


class Flaky:
    def __init__(self, *errors: Exception) -> None:
        self.errors = list(errors)
        self.calls = 0

    def __call__(self, settings, **request):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return "workshop"


QUOTA = GeminiGenerationError(provider_message("429"))
BAD_KEY = GeminiGenerationError(provider_message("401"))


class RetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.delays: list[float] = []

    def wrap(self, inner, attempts: int = 3) -> RetryingWorkshopGenerator:
        return RetryingWorkshopGenerator(inner, attempts=attempts, base_delay=1, sleep=self.delays.append)

    def test_transient_errors_are_retried_with_backoff(self) -> None:
        inner = Flaky(QUOTA, QUOTA)
        self.assertEqual(self.wrap(inner)(None, subject="x"), "workshop")
        self.assertEqual(inner.calls, 3)
        self.assertEqual(self.delays, [1, 2])

    def test_permanent_errors_fail_immediately(self) -> None:
        inner = Flaky(BAD_KEY)
        with self.assertRaises(GeminiGenerationError):
            self.wrap(inner)(None)
        self.assertEqual(inner.calls, 1)
        self.assertEqual(self.delays, [])

    def test_slow_failures_are_not_retried(self) -> None:
        ticks = iter([0.0, 30.0])
        inner = Flaky(QUOTA)
        retrying = RetryingWorkshopGenerator(inner, attempts=3, base_delay=1, sleep=self.delays.append,
                                             budget_seconds=25, clock=lambda: next(ticks))
        with self.assertRaises(GeminiGenerationError):
            retrying(None)
        self.assertEqual(inner.calls, 1)

    def test_gives_up_after_the_last_attempt(self) -> None:
        inner = Flaky(QUOTA, QUOTA)
        with self.assertRaises(GeminiGenerationError):
            self.wrap(inner, attempts=2)(None)
        self.assertEqual(inner.calls, 2)


if __name__ == "__main__":
    unittest.main()

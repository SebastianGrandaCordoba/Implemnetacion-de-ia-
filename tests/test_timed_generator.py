import unittest

from app.adapters.resilience import TimedWorkshopGenerator


class TimedTests(unittest.TestCase):
    def test_records_duration_even_when_generation_fails(self) -> None:
        ticks = iter([10.0, 12.5])

        def failing(settings, **request):
            raise RuntimeError("boom")

        timed = TimedWorkshopGenerator(failing, clock=lambda: next(ticks))
        with self.assertRaises(RuntimeError):
            timed(None, generation_type="QUIZ")
        self.assertEqual(timed.last_duration, 2.5)


if __name__ == "__main__":
    unittest.main()

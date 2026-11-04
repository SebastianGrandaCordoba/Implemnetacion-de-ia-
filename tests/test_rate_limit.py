import unittest

from app.domain.rate_limit import SlidingWindowLimiter


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


class LimiterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        self.limiter = SlidingWindowLimiter(2, window_seconds=60, clock=self.clock)

    def test_allows_up_to_the_limit(self) -> None:
        self.assertIsNone(self.limiter.acquire("t"))
        self.assertIsNone(self.limiter.acquire("t"))
        self.assertEqual(self.limiter.acquire("t"), 60)

    def test_window_slides(self) -> None:
        self.limiter.acquire("t")
        self.clock.now = 30
        self.limiter.acquire("t")
        self.clock.now = 61
        self.assertIsNone(self.limiter.acquire("t"))
        self.assertAlmostEqual(self.limiter.acquire("t"), 29)

    def test_keys_are_independent(self) -> None:
        self.limiter.acquire("a")
        self.limiter.acquire("a")
        self.assertIsNone(self.limiter.acquire("b"))

    def test_zero_disables_limiting(self) -> None:
        limiter = SlidingWindowLimiter(0)
        self.assertTrue(all(limiter.acquire("t") is None for _ in range(100)))


if __name__ == "__main__":
    unittest.main()

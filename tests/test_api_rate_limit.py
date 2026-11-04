import unittest
from unittest import mock

from app.domain.rate_limit import SlidingWindowLimiter
from tests.api_case import ApiCase, txt


class RateLimitTests(ApiCase):
    def test_bursts_get_429_with_retry_after(self) -> None:
        with mock.patch("app.main.generation_limiter", SlidingWindowLimiter(1, window_seconds=60)):
            self.assertEqual(self.post([txt()]).status_code, 200)
            response = self.post([txt()])
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "60")
        self.assertEqual(len(self.use_case.requests), 1)

    def test_unauthorized_requests_do_not_spend_the_budget(self) -> None:
        limiter = SlidingWindowLimiter(1, window_seconds=60)
        with mock.patch("app.main.generation_limiter", limiter):
            self.client.post("/api/v1/workshops/generate", data={"subject": "M", "targetLevel": "LOW"}, files=[txt()])
            self.assertEqual(self.post([txt()]).status_code, 200)


if __name__ == "__main__":
    unittest.main()

import unittest

from app.adapters.resilience import CachedWorkshopGenerator
from tests.api_support import sample_workshop


class Counter:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, settings, **request):
        self.calls += 1
        return sample_workshop(request.get("target_level", "LOW"))


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inner = Counter()
        self.clock = Clock()
        self.cache = CachedWorkshopGenerator(self.inner, max_entries=2, ttl_seconds=60, clock=self.clock)

    def test_same_request_hits_the_cache(self) -> None:
        self.cache(None, material_text="a", target_level="LOW")
        self.cache(None, material_text="a", target_level="LOW")
        self.assertEqual(self.inner.calls, 1)

    def test_different_requests_miss(self) -> None:
        self.cache(None, material_text="a", target_level="LOW")
        self.cache(None, material_text="a", target_level="HIGH")
        self.assertEqual(self.inner.calls, 2)

    def test_entries_expire(self) -> None:
        self.cache(None, material_text="a")
        self.clock.now = 61
        self.cache(None, material_text="a")
        self.assertEqual(self.inner.calls, 2)

    def test_least_recently_used_entry_is_evicted(self) -> None:
        for text in ("a", "b", "c"):
            self.cache(None, material_text=text)
        self.assertEqual(len(self.cache), 2)
        self.cache(None, material_text="a")
        self.assertEqual(self.inner.calls, 4)

    def test_cached_results_are_copies(self) -> None:
        first = self.cache(None, material_text="a")
        first.title = "Editado"
        self.assertNotEqual(self.cache(None, material_text="a").title, "Editado")

    def test_disabled_cache_always_calls_through(self) -> None:
        cache = CachedWorkshopGenerator(self.inner, max_entries=0)
        cache(None, material_text="a")
        cache(None, material_text="a")
        self.assertEqual(self.inner.calls, 2)


if __name__ == "__main__":
    unittest.main()

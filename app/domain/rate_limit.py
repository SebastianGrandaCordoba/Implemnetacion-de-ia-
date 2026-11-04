"""Sliding-window limiter that protects the shared Gemini quota from bursts."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float = 60, clock: Callable[[], float] = time.monotonic):
        self._max = max_requests
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def acquire(self, key: str) -> float | None:
        """Records a request; returns None when allowed, or the seconds to wait when not."""
        if self._max <= 0:
            return None
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._max:
                return max(0.0, self._window - (now - hits[0]))
            hits.append(now)
            return None

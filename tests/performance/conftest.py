"""Performance test fixtures and benchmark utilities."""
import pytest
import time


@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer context manager."""
    class Timer:
        def __init__(self):
            self.elapsed = 0.0
        def __enter__(self):
            self._start = time.perf_counter()
            return self
        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self._start
    return Timer

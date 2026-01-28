"""Boot time benchmark."""
import pytest


@pytest.mark.performance
@pytest.mark.slow
class TestBootBenchmark:
    TARGET_SECONDS = 20
    MAX_ACCEPTABLE_SECONDS = 30

    def test_boot_time_placeholder(self, benchmark_timer):
        """Placeholder: actual boot benchmark requires emulator_core."""
        with benchmark_timer() as t:
            pass  # Will call emulator.start() and wait_for_boot()
        assert t.elapsed < self.MAX_ACCEPTABLE_SECONDS

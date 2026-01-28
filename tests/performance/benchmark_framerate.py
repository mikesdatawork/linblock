"""Frame rate benchmark."""
import pytest


@pytest.mark.performance
class TestFramerateBenchmark:
    TARGET_FPS = 30
    MIN_FPS = 24

    def test_framerate_placeholder(self):
        """Placeholder: requires display_manager integration."""
        pass

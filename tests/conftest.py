"""
Root conftest.py for LinBlock test suite.

Provides shared fixtures available to all test files.
"""

import os
import sys

import pytest

# Add src to path for module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def project_root():
    """Return the project root directory path."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def empty_config():
    """Return an empty configuration dict."""
    return {}


@pytest.fixture
def sample_config():
    """Return a basic sample configuration dict."""
    return {
        "debug": True,
        "log_level": "INFO",
        "data_dir": "/tmp/linblock-test",
    }

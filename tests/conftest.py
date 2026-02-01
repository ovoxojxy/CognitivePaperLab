"""Pytest fixtures."""

import pytest


@pytest.fixture
def golden_dir():
    """Path to golden output files."""
    from pathlib import Path
    return Path(__file__).parent / "golden"


@pytest.fixture
def sample_output():
    """Dummy output for golden comparison. Replace with real logic later."""
    return "ok\n"

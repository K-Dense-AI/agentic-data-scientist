"""Pytest configuration and fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_working_dir():
    """Create a temporary working directory for tests."""
    tmpdir = tempfile.mkdtemp(prefix="test_agentic_ds_")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a sample CSV file for testing."""
    csv_content = """name,age,city
Alice,30,NYC
Bob,25,LA
Charlie,35,Chicago"""

    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    text_content = "This is a sample text file for testing."
    text_file = tmp_path / "sample.txt"
    text_file.write_text(text_content)
    return text_file


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")

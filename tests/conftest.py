"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from notes.config import Config
from notes.search import SearchIndex
from notes.storage import FilesystemStorage


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_dir: Path) -> FilesystemStorage:
    """Provide a filesystem storage instance."""
    return FilesystemStorage(temp_dir / "notes")


@pytest.fixture
def search_index(temp_dir: Path) -> SearchIndex:
    """Provide a search index instance."""
    return SearchIndex(temp_dir / "index")


@pytest.fixture
def config(temp_dir: Path) -> Config:
    """Provide a test configuration."""
    return Config(
        notes_dir=temp_dir / "notes",
        index_dir=temp_dir / "index",
    )


@pytest.fixture
def mock_config(config: Config):
    """Patch get_config to return test configuration for MCP tool tests."""
    with (
        patch("notes.config.get_config", return_value=config),
        patch("notes.tools.notes.get_config", return_value=config),
        patch("notes.tools.search.get_config", return_value=config),
        patch("notes.tools.tags.get_config", return_value=config),
    ):
        yield config

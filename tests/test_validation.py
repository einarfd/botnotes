"""Tests for input validation and security."""

import pytest

from notes.storage.filesystem import FilesystemStorage


class TestPathSanitization:
    """Test path sanitization in FilesystemStorage."""

    def test_normal_path(self, tmp_path):
        """Normal paths should work."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("my-note")
        assert result == "my-note"

    def test_path_with_subdirectory(self, tmp_path):
        """Paths with subdirectories should work."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("folder/my-note")
        assert result == "folder/my-note"

    def test_absolute_path_stripped(self, tmp_path):
        """Absolute paths should have leading slash stripped."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("/my-note")
        assert result == "my-note"

    def test_absolute_path_etc(self, tmp_path):
        """Absolute paths to system directories should be sanitized."""
        storage = FilesystemStorage(tmp_path)
        # /etc/passwd becomes etc/passwd which is valid within base_dir
        result = storage._sanitize_path("/etc/passwd")
        assert result == "etc/passwd"

    def test_parent_traversal_rejected(self, tmp_path):
        """Parent directory traversal should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Invalid path"):
            storage._sanitize_path("../outside")

    def test_deep_parent_traversal_rejected(self, tmp_path):
        """Deep parent directory traversal should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Invalid path"):
            storage._sanitize_path("foo/../../outside")

    def test_encoded_traversal_rejected(self, tmp_path):
        """Various traversal attempts should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Invalid path"):
            storage._sanitize_path("foo/../../../etc/passwd")

    def test_empty_path_rejected(self, tmp_path):
        """Empty paths should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Path cannot be empty"):
            storage._sanitize_path("")

    def test_whitespace_only_rejected(self, tmp_path):
        """Whitespace-only paths should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Path cannot be empty"):
            storage._sanitize_path("   ")

    def test_slash_only_rejected(self, tmp_path):
        """Slash-only paths should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Path cannot be empty"):
            storage._sanitize_path("/")

    def test_whitespace_stripped(self, tmp_path):
        """Whitespace should be stripped from paths."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("  my-note  ")
        assert result == "my-note"

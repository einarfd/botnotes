"""Tests for migration logic."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from botnotes.migrations import (
    MigrationResult,
    ensure_git_initialized,
    find_overlapping_notes,
    migrate_v1_to_v2,
    run_migrations,
)


class TestMigrationResult:
    """Tests for MigrationResult dataclass."""

    def test_success_when_no_errors(self):
        """Test that success is True when no errors."""
        result = MigrationResult(from_version=1, to_version=2)
        assert result.success is True

    def test_success_false_when_errors(self):
        """Test that success is False when there are errors."""
        result = MigrationResult(
            from_version=1, to_version=2, errors=["Some error"]
        )
        assert result.success is False

    def test_defaults(self):
        """Test default values."""
        result = MigrationResult(from_version=1, to_version=2)
        assert result.notes_moved == []
        assert result.errors == []


class TestFindOverlappingNotes:
    """Tests for the find_overlapping_notes function."""

    def test_no_overlaps(self):
        """Test finding overlaps when there are none."""
        mock_service = MagicMock()
        mock_service.list_notes.return_value = ["note1", "note2", "folder/note3"]

        overlaps = find_overlapping_notes(mock_service)

        assert overlaps == []

    def test_finds_overlapping_notes(self):
        """Test finding overlapping notes."""
        mock_service = MagicMock()
        mock_service.list_notes.return_value = [
            "projects",  # This overlaps with projects/foo
            "projects/foo",
            "other",
        ]

        overlaps = find_overlapping_notes(mock_service)

        assert overlaps == [("projects", "projects/index")]

    def test_finds_multiple_overlaps(self):
        """Test finding multiple overlapping notes."""
        mock_service = MagicMock()
        mock_service.list_notes.return_value = [
            "docs",  # Overlaps
            "docs/readme",
            "projects",  # Overlaps
            "projects/foo",
            "projects/bar",
        ]

        overlaps = find_overlapping_notes(mock_service)

        assert overlaps == [("docs", "docs/index"), ("projects", "projects/index")]

    def test_skips_if_index_already_exists(self):
        """Test that overlaps are skipped if index already exists."""
        mock_service = MagicMock()
        mock_service.list_notes.return_value = [
            "projects",  # Overlaps but index exists
            "projects/index",  # Already migrated
            "projects/foo",
        ]

        overlaps = find_overlapping_notes(mock_service)

        assert overlaps == []


class TestMigrateV1ToV2:
    """Tests for the migrate_v1_to_v2 function."""

    def test_moves_notes(self):
        """Test that notes are moved correctly."""
        mock_service = MagicMock()
        overlaps = [("projects", "projects/index"), ("docs", "docs/index")]

        moved, errors = migrate_v1_to_v2(mock_service, overlaps)

        assert moved == overlaps
        assert errors == []
        assert mock_service.update_note.call_count == 2

    def test_handles_errors(self):
        """Test that errors are captured."""
        mock_service = MagicMock()
        mock_service.update_note.side_effect = ValueError("Already exists")
        overlaps = [("projects", "projects/index")]

        moved, errors = migrate_v1_to_v2(mock_service, overlaps)

        assert moved == []
        assert len(errors) == 1
        assert "Error moving projects" in errors[0]

    def test_partial_failure(self):
        """Test that some notes can succeed while others fail."""
        mock_service = MagicMock()
        mock_service.update_note.side_effect = [None, ValueError("Error")]
        overlaps = [("projects", "projects/index"), ("docs", "docs/index")]

        moved, errors = migrate_v1_to_v2(mock_service, overlaps)

        assert moved == [("projects", "projects/index")]
        assert len(errors) == 1

    def test_uses_custom_author(self):
        """Test that custom author is passed through."""
        mock_service = MagicMock()
        overlaps = [("projects", "projects/index")]

        migrate_v1_to_v2(mock_service, overlaps, author="custom-author")

        mock_service.update_note.assert_called_with(
            "projects", new_path="projects/index", author="custom-author"
        )


class TestRunMigrations:
    """Tests for the run_migrations function."""

    def test_already_at_version(self):
        """Test when already at target version."""
        mock_config = MagicMock()
        mock_config.data_version = 2
        mock_service = MagicMock()

        result = run_migrations(mock_config, mock_service)

        assert result.from_version == 2
        assert result.to_version == 2
        assert result.notes_moved == []
        mock_config.save.assert_not_called()

    def test_no_overlaps(self):
        """Test migration with no overlapping notes."""
        mock_config = MagicMock()
        mock_config.data_version = 1
        mock_service = MagicMock()
        mock_service.list_notes.return_value = ["note1", "note2"]

        result = run_migrations(mock_config, mock_service)

        assert result.from_version == 1
        assert result.to_version == 2
        assert result.notes_moved == []
        assert result.success is True
        mock_config.save.assert_called_once()
        assert mock_config.data_version == 2

    def test_with_overlaps(self):
        """Test migration with overlapping notes."""
        mock_config = MagicMock()
        mock_config.data_version = 1
        mock_service = MagicMock()
        mock_service.list_notes.return_value = ["projects", "projects/foo"]

        result = run_migrations(mock_config, mock_service)

        assert result.from_version == 1
        assert result.to_version == 2
        assert result.notes_moved == [("projects", "projects/index")]
        assert result.success is True
        mock_config.save.assert_called_once()

    def test_stops_on_error(self):
        """Test that migration stops and doesn't save on error."""
        mock_config = MagicMock()
        mock_config.data_version = 1
        mock_service = MagicMock()
        mock_service.list_notes.return_value = ["projects", "projects/foo"]
        mock_service.update_note.side_effect = ValueError("Error")

        result = run_migrations(mock_config, mock_service)

        assert result.success is False
        assert len(result.errors) == 1
        mock_config.save.assert_not_called()


class TestEnsureGitInitialized:
    """Tests for the ensure_git_initialized function."""

    def test_already_exists(self, tmp_path: Path):
        """Test when git repo already exists."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / ".git").mkdir()

        result = ensure_git_initialized(notes_dir, [])

        assert result is False

    def test_creates_repo_no_notes(self, tmp_path: Path):
        """Test creating repo with no notes."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        with patch("botnotes.migrations.GitRepository") as mock_git_class:
            mock_git = MagicMock()
            mock_git_class.return_value = mock_git

            result = ensure_git_initialized(notes_dir, [])

            assert result is True
            mock_git.ensure_initialized.assert_called_once()

    def test_creates_repo_with_notes(self, tmp_path: Path):
        """Test creating repo with existing notes creates commit."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        with (
            patch("botnotes.migrations.GitRepository") as mock_git_class,
            patch("subprocess.run") as mock_run,
        ):
            mock_git = MagicMock()
            mock_git_class.return_value = mock_git
            mock_run.return_value = MagicMock(returncode=0)

            result = ensure_git_initialized(notes_dir, ["note1", "note2"])

            assert result is True
            mock_git.ensure_initialized.assert_called_once()
            # Should call git add and git commit
            assert mock_run.call_count == 2

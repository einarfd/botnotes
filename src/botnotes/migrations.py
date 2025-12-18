"""Data migrations and initialization logic.

This module contains the core migration logic, separated from CLI concerns.
Each migration is a separate function, and run_migrations() serves as the
entrypoint that runs all pending migrations in order.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from botnotes.config import REQUIRED_DATA_VERSION, Config
from botnotes.storage.git_repo import GitRepository

if TYPE_CHECKING:
    from botnotes.services import NoteService


@dataclass
class MigrationResult:
    """Result of running migrations."""

    from_version: int
    to_version: int
    notes_moved: list[tuple[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True if migration completed without errors."""
        return len(self.errors) == 0


def find_overlapping_notes(service: NoteService) -> list[tuple[str, str]]:
    """Find notes that overlap with folders containing children.

    An overlapping note is one where:
    - A note exists at path X (e.g., 'projects')
    - Other notes exist at paths starting with X/ (e.g., 'projects/foo')

    Returns:
        List of (old_path, new_path) tuples for notes to migrate.
    """
    all_paths = set(service.list_notes())
    overlaps = []

    for path in all_paths:
        # Check if this path has any children
        prefix = path + "/"
        has_children = any(p.startswith(prefix) for p in all_paths)

        if has_children:
            # This note overlaps with a folder - needs to become {path}/index
            new_path = f"{path}/index"
            # Only add if target doesn't already exist
            if new_path not in all_paths:
                overlaps.append((path, new_path))

    return sorted(overlaps)


def migrate_v1_to_v2(
    service: NoteService,
    overlaps: list[tuple[str, str]],
    author: str = "migration",
) -> tuple[list[tuple[str, str]], list[str]]:
    """Migrate overlapping notes to {folder}/index convention.

    Args:
        service: NoteService instance.
        overlaps: List of (old_path, new_path) tuples from find_overlapping_notes().
        author: Author string for the git commit.

    Returns:
        Tuple of (moved_notes, errors) where:
        - moved_notes: List of (old_path, new_path) for successfully moved notes
        - errors: List of error messages for failed moves
    """
    moved = []
    errors = []

    for old_path, new_path in overlaps:
        try:
            service.update_note(old_path, new_path=new_path, author=author)
            moved.append((old_path, new_path))
        except Exception as e:
            errors.append(f"Error moving {old_path}: {e}")

    return moved, errors


def run_migrations(config: Config, service: NoteService) -> MigrationResult:
    """Run all pending migrations.

    This is the main entrypoint for the migration system. It checks the current
    data version and runs any migrations needed to reach REQUIRED_DATA_VERSION.

    Args:
        config: Config instance (will be modified and saved on success).
        service: NoteService instance.

    Returns:
        MigrationResult with details of what was done.
    """
    from_version = config.data_version

    # Already at target version
    if from_version >= REQUIRED_DATA_VERSION:
        return MigrationResult(from_version=from_version, to_version=from_version)

    result = MigrationResult(from_version=from_version, to_version=REQUIRED_DATA_VERSION)

    # Run v1 -> v2 migration
    if from_version < 2:
        overlaps = find_overlapping_notes(service)
        if overlaps:
            moved, errors = migrate_v1_to_v2(service, overlaps)
            result.notes_moved.extend(moved)
            result.errors.extend(errors)

            # Stop on errors - don't update version if migration failed
            if errors:
                return result

    # Update config version on success
    config.data_version = REQUIRED_DATA_VERSION
    config.save()

    return result


def ensure_git_initialized(notes_dir: Path, note_paths: list[str]) -> bool:
    """Initialize git repository for version history if needed.

    Args:
        notes_dir: Path to the notes directory.
        note_paths: List of existing note paths to commit.

    Returns:
        True if git was initialized, False if already existed.
    """
    git_dir = notes_dir / ".git"
    if git_dir.exists():
        return False

    # Create git repository
    git = GitRepository(notes_dir)
    git.ensure_initialized()

    # Create initial commit if notes exist
    if note_paths:
        subprocess.run(
            ["git", "add", "*.md"],
            cwd=notes_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Initial import of existing notes",
                "--author",
                "BotNotes System <botnotes@local>",
            ],
            cwd=notes_dir,
            capture_output=True,
            check=True,
        )

    return True

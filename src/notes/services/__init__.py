"""Service layer for notes application."""

from notes.services.note_service import (
    DeleteResult,
    NoteService,
    RebuildResult,
    UpdateResult,
)

__all__ = ["DeleteResult", "NoteService", "RebuildResult", "UpdateResult"]

"""Data models."""

from notes.models.note import Note
from notes.models.version import NoteDiff, NoteVersion

__all__ = ["Note", "NoteDiff", "NoteVersion"]

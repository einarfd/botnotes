"""Integration tests for MCP tools."""

from notes.config import Config
from notes.tools.notes import (
    create_note,
    delete_note,
    list_notes,
    list_notes_in_folder,
    read_note,
    update_note,
)
from notes.tools.search import search_notes
from notes.tools.tags import find_by_tag, list_tags

# Access underlying functions (unwrap from @mcp.tool() decorator)
_create_note = create_note.fn
_read_note = read_note.fn
_update_note = update_note.fn
_delete_note = delete_note.fn
_list_notes = list_notes.fn
_list_notes_in_folder = list_notes_in_folder.fn
_search_notes = search_notes.fn
_list_tags = list_tags.fn
_find_by_tag = find_by_tag.fn


class TestCreateNote:
    """Tests for create_note tool."""

    def test_create_note(self, mock_config: Config):
        """Test creating a note."""
        result = _create_note(
            path="test/note",
            title="Test Note",
            content="Hello world",
            tags=["test", "example"],
        )

        assert "Created note at 'test/note'" in result

    def test_create_note_without_tags(self, mock_config: Config):
        """Test creating a note without tags."""
        result = _create_note(
            path="simple",
            title="Simple Note",
            content="No tags here",
        )

        assert "Created note at 'simple'" in result


class TestReadNote:
    """Tests for read_note tool."""

    def test_read_note(self, mock_config: Config):
        """Test reading a note."""
        _create_note(path="readable", title="Readable", content="Content here")

        result = _read_note("readable")

        assert "# Readable" in result
        assert "Content here" in result
        assert "**Path:** readable" in result

    def test_read_note_not_found(self, mock_config: Config):
        """Test reading a nonexistent note."""
        result = _read_note("nonexistent")

        assert "Note not found: 'nonexistent'" in result


class TestUpdateNote:
    """Tests for update_note tool."""

    def test_update_note_title(self, mock_config: Config):
        """Test updating note title."""
        _create_note(path="updatable", title="Original", content="Content")

        result = _update_note("updatable", title="Updated Title")

        assert "Updated note at 'updatable'" in result

        # Verify the update
        read_result = _read_note("updatable")
        assert "# Updated Title" in read_result

    def test_update_note_content(self, mock_config: Config):
        """Test updating note content."""
        _create_note(path="updatable2", title="Title", content="Original content")

        _update_note("updatable2", content="New content")

        read_result = _read_note("updatable2")
        assert "New content" in read_result

    def test_update_note_tags(self, mock_config: Config):
        """Test updating note tags."""
        _create_note(path="updatable3", title="Title", content="Content", tags=["old"])

        _update_note("updatable3", tags=["new", "tags"])

        read_result = _read_note("updatable3")
        assert "new, tags" in read_result

    def test_update_note_not_found(self, mock_config: Config):
        """Test updating a nonexistent note."""
        result = _update_note("nonexistent", title="New Title")

        assert "Note not found: 'nonexistent'" in result


class TestDeleteNote:
    """Tests for delete_note tool."""

    def test_delete_note(self, mock_config: Config):
        """Test deleting a note."""
        _create_note(path="deletable", title="Delete Me", content="Bye")

        result = _delete_note("deletable")

        assert "Deleted note at 'deletable'" in result

        # Verify it's gone
        read_result = _read_note("deletable")
        assert "Note not found" in read_result

    def test_delete_note_not_found(self, mock_config: Config):
        """Test deleting a nonexistent note."""
        result = _delete_note("nonexistent")

        assert "Note not found: 'nonexistent'" in result


class TestListNotes:
    """Tests for list_notes tool."""

    def test_list_notes_empty(self, mock_config: Config):
        """Test listing notes when none exist."""
        result = _list_notes()

        assert "No notes found" in result

    def test_list_notes(self, mock_config: Config):
        """Test listing multiple notes."""
        _create_note(path="note1", title="Note 1", content="First")
        _create_note(path="note2", title="Note 2", content="Second")
        _create_note(path="folder/note3", title="Note 3", content="Third")

        result = _list_notes()

        assert "note1" in result
        assert "note2" in result
        assert "folder/note3" in result


class TestSearchNotes:
    """Tests for search_notes tool."""

    def test_search_notes(self, mock_config: Config):
        """Test searching for notes."""
        _create_note(path="python-guide", title="Python Guide", content="Learn Python")
        _create_note(path="rust-guide", title="Rust Guide", content="Learn Rust")

        result = _search_notes("Python")

        assert "Python Guide" in result
        assert "python-guide" in result

    def test_search_notes_no_results(self, mock_config: Config):
        """Test search with no matching results."""
        _create_note(path="test", title="Test", content="Nothing special")

        result = _search_notes("nonexistent")

        assert "No notes found matching" in result

    def test_search_notes_by_content(self, mock_config: Config):
        """Test searching by content."""
        _create_note(path="secret", title="Normal Title", content="Contains secret keyword")

        result = _search_notes("secret")

        assert "Normal Title" in result


class TestListTags:
    """Tests for list_tags tool."""

    def test_list_tags_empty(self, mock_config: Config):
        """Test listing tags when none exist."""
        result = _list_tags()

        assert "No tags found" in result

    def test_list_tags(self, mock_config: Config):
        """Test listing tags with counts."""
        _create_note(path="note1", title="Note 1", content="", tags=["python", "tutorial"])
        _create_note(path="note2", title="Note 2", content="", tags=["python", "guide"])
        _create_note(path="note3", title="Note 3", content="", tags=["rust"])

        result = _list_tags()

        assert "python (2 notes)" in result
        assert "tutorial (1 note)" in result
        assert "guide (1 note)" in result
        assert "rust (1 note)" in result


class TestFindByTag:
    """Tests for find_by_tag tool."""

    def test_find_by_tag(self, mock_config: Config):
        """Test finding notes by tag."""
        _create_note(path="note1", title="Python Basics", content="", tags=["python"])
        _create_note(path="note2", title="Python Advanced", content="", tags=["python"])
        _create_note(path="note3", title="Rust Intro", content="", tags=["rust"])

        result = _find_by_tag("python")

        assert "Python Basics" in result
        assert "Python Advanced" in result
        assert "Rust Intro" not in result

    def test_find_by_tag_no_results(self, mock_config: Config):
        """Test finding notes by nonexistent tag."""
        _create_note(path="note1", title="Note", content="", tags=["other"])

        result = _find_by_tag("nonexistent")

        assert "No notes found with tag 'nonexistent'" in result


class TestListNotesInFolder:
    """Tests for list_notes_in_folder tool."""

    def test_list_notes_in_folder_top_level(self, mock_config: Config):
        """Test listing only top-level notes."""
        _create_note(path="top1", title="Top 1", content="")
        _create_note(path="top2", title="Top 2", content="")
        _create_note(path="folder/nested", title="Nested", content="")

        result = _list_notes_in_folder("")

        assert "Top-level notes:" in result
        assert "top1" in result
        assert "top2" in result
        assert "folder/nested" not in result

    def test_list_notes_in_folder(self, mock_config: Config):
        """Test listing notes in a specific folder."""
        _create_note(path="top", title="Top", content="")
        _create_note(path="projects/proj1", title="Proj 1", content="")
        _create_note(path="projects/proj2", title="Proj 2", content="")
        _create_note(path="other/note", title="Other", content="")

        result = _list_notes_in_folder("projects")

        assert "Notes in 'projects':" in result
        assert "projects/proj1" in result
        assert "projects/proj2" in result
        assert "other/note" not in result

    def test_list_notes_in_folder_empty(self, mock_config: Config):
        """Test listing from a folder with no notes."""
        _create_note(path="elsewhere/note", title="Note", content="")

        result = _list_notes_in_folder("nonexistent")

        assert "No notes found in 'nonexistent'" in result

    def test_list_notes_in_folder_no_notes_top_level(self, mock_config: Config):
        """Test listing top-level when all notes are in folders."""
        _create_note(path="folder/note", title="Note", content="")

        result = _list_notes_in_folder("")

        assert "No notes found in top-level" in result

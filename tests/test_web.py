"""Tests for web API routes."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from notes.config import Config
from notes.services import NoteService
from notes.web.app import app


@pytest.fixture
def client(config: Config):
    """Create a test client with mocked service."""

    def make_test_service() -> NoteService:
        return NoteService(config)

    with patch("notes.web.routes._get_service", make_test_service):
        yield TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestNotesAPI:
    """Tests for notes CRUD API."""

    def test_list_notes_empty(self, client: TestClient):
        """Test listing notes when none exist."""
        response = client.get("/api/notes")

        assert response.status_code == 200
        assert response.json() == []

    def test_create_note(self, client: TestClient):
        """Test creating a note."""
        response = client.post(
            "/api/notes",
            json={
                "path": "test/note",
                "title": "Test Note",
                "content": "Hello world",
                "tags": ["test"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["path"] == "test/note"
        assert data["title"] == "Test Note"
        assert data["content"] == "Hello world"
        assert data["tags"] == ["test"]

    def test_get_note(self, client: TestClient):
        """Test getting a note."""
        # Create first
        client.post(
            "/api/notes",
            json={"path": "readable", "title": "Readable", "content": "Content"},
        )

        response = client.get("/api/notes/readable")

        assert response.status_code == 200
        assert response.json()["title"] == "Readable"

    def test_get_note_not_found(self, client: TestClient):
        """Test getting a nonexistent note."""
        response = client.get("/api/notes/nonexistent")

        assert response.status_code == 404

    def test_update_note(self, client: TestClient):
        """Test updating a note."""
        client.post(
            "/api/notes",
            json={"path": "updatable", "title": "Original", "content": "Content"},
        )

        response = client.put(
            "/api/notes/updatable",
            json={"title": "Updated"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_update_note_not_found(self, client: TestClient):
        """Test updating a nonexistent note."""
        response = client.put(
            "/api/notes/nonexistent",
            json={"title": "New"},
        )

        assert response.status_code == 404

    def test_delete_note(self, client: TestClient):
        """Test deleting a note."""
        client.post(
            "/api/notes",
            json={"path": "deletable", "title": "Delete Me", "content": "Bye"},
        )

        response = client.delete("/api/notes/deletable")

        assert response.status_code == 204

        # Verify it's gone
        response = client.get("/api/notes/deletable")
        assert response.status_code == 404

    def test_delete_note_not_found(self, client: TestClient):
        """Test deleting a nonexistent note."""
        response = client.delete("/api/notes/nonexistent")

        assert response.status_code == 404

    def test_list_notes(self, client: TestClient):
        """Test listing notes."""
        client.post("/api/notes", json={"path": "note1", "title": "Note 1", "content": ""})
        client.post("/api/notes", json={"path": "note2", "title": "Note 2", "content": ""})

        response = client.get("/api/notes")

        assert response.status_code == 200
        paths = response.json()
        assert "note1" in paths
        assert "note2" in paths


class TestSearchAPI:
    """Tests for search API."""

    def test_search_notes(self, client: TestClient):
        """Test searching notes."""
        client.post(
            "/api/notes",
            json={"path": "python", "title": "Python Guide", "content": "Learn Python"},
        )
        client.post(
            "/api/notes",
            json={"path": "rust", "title": "Rust Guide", "content": "Learn Rust"},
        )

        response = client.get("/api/search?q=Python")

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["title"] == "Python Guide"

    def test_search_no_results(self, client: TestClient):
        """Test search with no results."""
        client.post("/api/notes", json={"path": "test", "title": "Test", "content": ""})

        response = client.get("/api/search?q=nonexistent")

        assert response.status_code == 200
        assert response.json() == []


class TestTagsAPI:
    """Tests for tags API."""

    def test_list_tags(self, client: TestClient):
        """Test listing tags."""
        client.post(
            "/api/notes",
            json={"path": "note1", "title": "Note 1", "content": "", "tags": ["python", "guide"]},
        )
        client.post(
            "/api/notes",
            json={"path": "note2", "title": "Note 2", "content": "", "tags": ["python"]},
        )

        response = client.get("/api/tags")

        assert response.status_code == 200
        tags = response.json()
        assert tags["python"] == 2
        assert tags["guide"] == 1

    def test_list_tags_empty(self, client: TestClient):
        """Test listing tags when none exist."""
        response = client.get("/api/tags")

        assert response.status_code == 200
        assert response.json() == {}

    def test_find_by_tag(self, client: TestClient):
        """Test finding notes by tag."""
        client.post(
            "/api/notes",
            json={"path": "note1", "title": "Python 1", "content": "", "tags": ["python"]},
        )
        client.post(
            "/api/notes",
            json={"path": "note2", "title": "Python 2", "content": "", "tags": ["python"]},
        )
        client.post(
            "/api/notes",
            json={"path": "note3", "title": "Rust", "content": "", "tags": ["rust"]},
        )

        response = client.get("/api/tags/python")

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 2
        titles = [n["title"] for n in notes]
        assert "Python 1" in titles
        assert "Python 2" in titles

    def test_find_by_tag_no_results(self, client: TestClient):
        """Test finding notes by nonexistent tag."""
        client.post(
            "/api/notes",
            json={"path": "note1", "title": "Note", "content": "", "tags": ["other"]},
        )

        response = client.get("/api/tags/nonexistent")

        assert response.status_code == 200
        assert response.json() == []

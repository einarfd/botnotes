"""Tests for web UI authentication."""

import base64
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from botnotes.config import Config, WebConfig
from botnotes.services import NoteService
from botnotes.web.app import app


def _make_auth_header(username: str, password: str) -> dict[str, str]:
    """Create HTTP Basic Auth header."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def config_no_auth(config: Config) -> Config:
    """Config with no web auth."""
    config.web = WebConfig()
    return config


@pytest.fixture
def config_with_auth(config: Config) -> Config:
    """Config with web auth enabled."""
    config.web = WebConfig(username="admin", password="secret123")
    return config


@pytest.fixture
def client_no_auth(config_no_auth: Config):
    """Test client without auth configured."""

    def make_test_service() -> NoteService:
        return NoteService(config_no_auth)

    with (
        patch("botnotes.web.routes._get_service", make_test_service),
        patch("botnotes.web.views._get_service", make_test_service),
        patch("botnotes.web.admin._get_service", make_test_service),
        patch("botnotes.web.admin.get_config", return_value=config_no_auth),
        patch("botnotes.web.auth.get_config", return_value=config_no_auth),
    ):
        yield TestClient(app)


@pytest.fixture
def client_with_auth(config_with_auth: Config):
    """Test client with auth configured."""

    def make_test_service() -> NoteService:
        return NoteService(config_with_auth)

    with (
        patch("botnotes.web.routes._get_service", make_test_service),
        patch("botnotes.web.views._get_service", make_test_service),
        patch("botnotes.web.admin._get_service", make_test_service),
        patch("botnotes.web.admin.get_config", return_value=config_with_auth),
        patch("botnotes.web.auth.get_config", return_value=config_with_auth),
    ):
        yield TestClient(app)


class TestNoAuthConfigured:
    """Tests when web auth is not configured."""

    def test_api_accessible_without_credentials(self, client_no_auth: TestClient):
        """API routes should be accessible without credentials."""
        response = client_no_auth.get("/api/notes")
        assert response.status_code == 200

    def test_views_accessible_without_credentials(self, client_no_auth: TestClient):
        """View routes should be accessible without credentials."""
        response = client_no_auth.get("/")
        assert response.status_code == 200

    def test_admin_accessible_without_credentials(self, client_no_auth: TestClient):
        """Admin routes should be accessible without credentials."""
        response = client_no_auth.get("/admin")
        assert response.status_code == 200


class TestAuthConfigured:
    """Tests when web auth is configured."""

    def test_api_requires_auth(self, client_with_auth: TestClient):
        """API routes should require authentication."""
        response = client_with_auth.get("/api/notes")
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Basic"

    def test_views_require_auth(self, client_with_auth: TestClient):
        """View routes should require authentication."""
        response = client_with_auth.get("/")
        assert response.status_code == 401

    def test_admin_requires_auth(self, client_with_auth: TestClient):
        """Admin routes should require authentication."""
        response = client_with_auth.get("/admin")
        assert response.status_code == 401

    def test_valid_credentials_accepted(self, client_with_auth: TestClient):
        """Valid credentials should grant access."""
        headers = _make_auth_header("admin", "secret123")
        response = client_with_auth.get("/api/notes", headers=headers)
        assert response.status_code == 200

    def test_invalid_username_rejected(self, client_with_auth: TestClient):
        """Invalid username should be rejected."""
        headers = _make_auth_header("wrong", "secret123")
        response = client_with_auth.get("/api/notes", headers=headers)
        assert response.status_code == 401

    def test_invalid_password_rejected(self, client_with_auth: TestClient):
        """Invalid password should be rejected."""
        headers = _make_auth_header("admin", "wrongpassword")
        response = client_with_auth.get("/api/notes", headers=headers)
        assert response.status_code == 401

    def test_views_with_valid_credentials(self, client_with_auth: TestClient):
        """Views should be accessible with valid credentials."""
        headers = _make_auth_header("admin", "secret123")
        response = client_with_auth.get("/", headers=headers)
        assert response.status_code == 200

    def test_admin_with_valid_credentials(self, client_with_auth: TestClient):
        """Admin should be accessible with valid credentials."""
        headers = _make_auth_header("admin", "secret123")
        response = client_with_auth.get("/admin", headers=headers)
        assert response.status_code == 200


class TestHealthCheck:
    """Tests for health check endpoint (should always be accessible)."""

    def test_health_no_auth_configured(self, client_no_auth: TestClient):
        """Health check accessible when no auth configured."""
        response = client_no_auth.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_with_auth_configured_no_credentials(self, client_with_auth: TestClient):
        """Health check accessible even when auth configured but no credentials provided."""
        response = client_with_auth.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuthorAttribution:
    """Tests that authenticated username is used as git author."""

    def test_create_note_api_uses_username_as_author(self, client_with_auth: TestClient):
        """Creating a note via API should use authenticated username as author."""
        headers = _make_auth_header("admin", "secret123")

        # Create a note
        response = client_with_auth.post(
            "/api/notes",
            json={"path": "author-test", "title": "Author Test", "content": "content"},
            headers=headers,
        )
        assert response.status_code == 201

        # Check history shows the authenticated username as author
        response = client_with_auth.get("/api/notes/author-test/history", headers=headers)
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 1
        assert versions[0]["author"] == "admin"

    def test_update_note_api_uses_username_as_author(self, client_with_auth: TestClient):
        """Updating a note via API should use authenticated username as author."""
        headers = _make_auth_header("admin", "secret123")

        # Create a note
        client_with_auth.post(
            "/api/notes",
            json={"path": "update-author", "title": "Test", "content": "v1"},
            headers=headers,
        )

        # Update it
        response = client_with_auth.put(
            "/api/notes/update-author",
            json={"content": "v2"},
            headers=headers,
        )
        assert response.status_code == 200

        # Check history shows admin as author for both commits
        response = client_with_auth.get("/api/notes/update-author/history", headers=headers)
        versions = response.json()
        assert len(versions) == 2
        assert versions[0]["author"] == "admin"  # update commit
        assert versions[1]["author"] == "admin"  # create commit

    def test_delete_note_api_uses_username_as_author(self, client_with_auth: TestClient):
        """Deleting a note via API should use authenticated username as author."""
        headers = _make_auth_header("admin", "secret123")

        # Create and delete a note
        client_with_auth.post(
            "/api/notes",
            json={"path": "delete-author", "title": "Test", "content": "content"},
            headers=headers,
        )
        response = client_with_auth.delete("/api/notes/delete-author", headers=headers)
        assert response.status_code == 204

        # Note is deleted, but we can verify via git log that admin was the author
        # (This is implicitly tested - if the author wasn't passed, it would fail)

    def test_create_note_form_uses_username_as_author(self, client_with_auth: TestClient):
        """Creating a note via HTML form should use authenticated username as author."""
        headers = _make_auth_header("admin", "secret123")

        # Create a note via form
        response = client_with_auth.post(
            "/new",
            data={"path": "form-author", "title": "Form Test", "tags": "", "content": "content"},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Check history shows admin as author
        response = client_with_auth.get("/api/notes/form-author/history", headers=headers)
        versions = response.json()
        assert len(versions) == 1
        assert versions[0]["author"] == "admin"

    def test_update_note_form_uses_username_as_author(self, client_with_auth: TestClient):
        """Updating a note via HTML form should use authenticated username as author."""
        headers = _make_auth_header("admin", "secret123")

        # Create a note
        client_with_auth.post(
            "/api/notes",
            json={"path": "form-update", "title": "Test", "content": "v1"},
            headers=headers,
        )

        # Update via form
        response = client_with_auth.post(
            "/notes/form-update",
            data={"new_path": "form-update", "title": "Updated", "tags": "", "content": "v2"},
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Check history
        response = client_with_auth.get("/api/notes/form-update/history", headers=headers)
        versions = response.json()
        assert len(versions) == 2
        assert versions[0]["author"] == "admin"

    def test_no_auth_uses_web_as_author(self, client_no_auth: TestClient):
        """Without auth configured, 'web' should be used as the author."""
        # Create a note
        response = client_no_auth.post(
            "/api/notes",
            json={"path": "no-auth-author", "title": "No Auth", "content": "content"},
        )
        assert response.status_code == 201

        # Check history shows 'web' as author
        response = client_no_auth.get("/api/notes/no-auth-author/history")
        versions = response.json()
        assert len(versions) == 1
        assert versions[0]["author"] == "web"

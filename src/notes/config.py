"""Configuration management."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = "127.0.0.1"
    port: int = 8080
    transport: Literal["stdio", "http", "sse"] = "stdio"


class AuthConfig(BaseModel):
    """Authentication configuration."""

    keys: dict[str, str] = {}  # name -> token


class Config(BaseModel):
    """Application configuration."""

    notes_dir: Path = Path.home() / ".local" / "notes" / "notes"
    index_dir: Path = Path.home() / ".local" / "notes" / "index"
    server: ServerConfig = ServerConfig()
    auth: AuthConfig = AuthConfig()

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def validate_for_http(self) -> None:
        """Validate config for HTTP mode. Raises if auth not configured."""
        if not self.auth.keys:
            raise ValueError(
                "HTTP mode requires authentication. "
                "Add API keys to [auth.keys] in config.toml"
            )

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Load config from TOML file.

        Args:
            path: Path to config file. Defaults to ~/.local/notes/config.toml

        Returns:
            Config loaded from file, or default config if file doesn't exist.
        """
        path = path or Path.home() / ".local" / "notes" / "config.toml"
        if path.exists():
            with open(path, "rb") as f:
                data = tomllib.load(f)
            return cls.model_validate(data)
        return cls()


def get_config() -> Config:
    """Get the application configuration."""
    return Config.load()

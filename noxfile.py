"""Nox sessions for running checks."""

import nox


@nox.session(venv_backend="none")
def check(session: nox.Session) -> None:
    """Run all checks: ruff, mypy, pytest."""
    session.run("uv", "run", "ruff", "check", "src", "tests")
    session.run("uv", "run", "mypy", "src")
    session.run("uv", "run", "pytest")

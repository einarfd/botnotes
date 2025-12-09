"""FastAPI web application."""

from fastapi import FastAPI

from notes.web.routes import router

app = FastAPI(
    title="Notes",
    description="AI-friendly note-taking solution",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


def main() -> None:
    """Run the web server."""
    import uvicorn

    uvicorn.run(
        "notes.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()

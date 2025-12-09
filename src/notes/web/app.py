"""FastAPI web application."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from notes.web.routes import router as api_router
from notes.web.views import router as views_router

app = FastAPI(
    title="Notes",
    description="AI-friendly note-taking solution",
    version="0.1.0",
)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(api_router)
app.include_router(views_router)


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

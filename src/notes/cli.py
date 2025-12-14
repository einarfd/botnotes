"""CLI tools for notes administration."""

import argparse
from pathlib import Path

from notes.backup import clear_notes, export_notes, import_notes
from notes.config import Config, get_config
from notes.services import NoteService


def rebuild_indexes() -> None:
    """Rebuild all indexes from stored notes."""
    print("Rebuilding indexes...")
    service = NoteService()
    result = service.rebuild_indexes()
    print(f"Done! Processed {result.notes_processed} notes.")


def export_backup(output: str | None) -> None:
    """Export all notes to a tar.gz archive."""
    config = get_config()
    output_path = Path(output) if output else None

    print("Exporting notes...")
    result = export_notes(config.notes_dir, output_path)
    print(f"Done! Exported {result.notes_count} notes to {result.path}")


def import_backup(archive: str, replace: bool) -> None:
    """Import notes from a tar.gz archive."""
    config = get_config()
    archive_path = Path(archive)

    if replace:
        print("Importing notes (replacing existing)...")
    else:
        print("Importing notes (merging with existing)...")

    result = import_notes(config.notes_dir, archive_path, replace=replace)

    print(f"Done! Imported {result.imported_count} notes.")
    if result.skipped_count > 0:
        print(f"Skipped {result.skipped_count} existing notes (use --replace to overwrite).")

    # Rebuild indexes after import
    print("Rebuilding indexes...")
    service = NoteService()
    rebuild_result = service.rebuild_indexes()
    print(f"Indexed {rebuild_result.notes_processed} notes.")


def clear_all(force: bool) -> None:
    """Clear all notes."""
    config = get_config()

    if not force:
        print("WARNING: This will delete ALL notes permanently!")
        response = input("Type 'yes' to confirm: ")
        if response.strip().lower() != "yes":
            print("Aborted.")
            return

    print("Clearing all notes...")
    count = clear_notes(config.notes_dir)
    print(f"Deleted {count} notes.")

    # Rebuild indexes (they'll be empty)
    print("Rebuilding indexes...")
    service = NoteService()
    service.rebuild_indexes()
    print("Done!")


def serve(host: str | None, port: int | None) -> None:
    """Run MCP server in HTTP mode."""
    import asyncio

    from notes.auth import ApiKeyAuthProvider
    from notes.server import mcp

    config = Config.load()

    # HTTP mode requires auth - fail early with clear message
    config.validate_for_http()

    if host:
        config.server.host = host
    if port:
        config.server.port = port

    print(f"Starting MCP server on http://{config.server.host}:{config.server.port}")
    print(f"Auth enabled with {len(config.auth.keys)} API key(s):")
    for name in config.auth.keys:
        print(f"  - {name}")

    # Configure auth on the server
    mcp._auth = ApiKeyAuthProvider(config.auth.keys)  # type: ignore[attr-defined]

    # Run HTTP server
    asyncio.run(
        mcp.run_http_async(
            transport="http",
            host=config.server.host,
            port=config.server.port,
        )
    )


def main() -> None:
    """Main entry point for notes-admin CLI."""
    parser = argparse.ArgumentParser(
        prog="notes-admin",
        description="Notes administration tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Rebuild command
    subparsers.add_parser("rebuild", help="Rebuild search and backlinks indexes")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export notes to a tar.gz archive")
    export_parser.add_argument(
        "output",
        nargs="?",
        help="Output file path (default: notes-backup-YYYY-MM-DD.tar.gz)",
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import notes from a tar.gz archive")
    import_parser.add_argument("archive", help="Path to the archive file")
    import_parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing notes instead of merging",
    )

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Delete all notes")
    clear_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Run MCP server in HTTP mode")
    serve_parser.add_argument(
        "--host",
        help="Host to bind to (default: from config or 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        help="Port to listen on (default: from config or 8080)",
    )

    args = parser.parse_args()

    if args.command == "rebuild":
        rebuild_indexes()
    elif args.command == "export":
        export_backup(args.output)
    elif args.command == "import":
        import_backup(args.archive, args.replace)
    elif args.command == "clear":
        clear_all(args.force)
    elif args.command == "serve":
        serve(args.host, args.port)


if __name__ == "__main__":
    main()

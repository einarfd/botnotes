"""FastMCP server entry point."""

from fastmcp import FastMCP

mcp = FastMCP("notes")

# Import tools to register them with the mcp instance
from notes.tools import links, notes, search, tags  # noqa: F401, E402


def main() -> None:
    """Run the MCP server."""
    from notes.config import Config

    config = Config.load()

    if config.server.transport == "stdio":
        mcp.run()
    else:
        # HTTP mode requires auth
        config.validate_for_http()

        # Configure auth on the server
        from notes.auth import ApiKeyAuthProvider

        mcp._auth = ApiKeyAuthProvider(config.auth.keys)  # type: ignore[attr-defined]

        import asyncio

        asyncio.run(
            mcp.run_http_async(
                transport=config.server.transport,
                host=config.server.host,
                port=config.server.port,
            )
        )


if __name__ == "__main__":
    main()

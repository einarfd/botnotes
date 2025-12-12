# Notes

AI-friendly note-taking solution with MCP integration and web UI.

## Installation

```bash
uv sync
```

## Usage

### MCP Server

Run the MCP server for AI assistants:

```bash
uv run notes
```

### Web UI

Run the web interface:

```bash
uv run notes-web
uv run notes-web --port 3000        # custom port
uv run notes-web --host 127.0.0.1   # localhost only
uv run notes-web --no-reload        # disable auto-reload
```

Opens at http://localhost:8000 (or your custom port) with:
- Browse and search notes
- Create, edit, and delete notes
- Tag-based organization
- REST API at `/api/*`

### Admin CLI

Command-line tools for administration:

```bash
# Rebuild search and backlinks indexes
uv run notes-admin rebuild

# Export all notes to backup archive
uv run notes-admin export                    # → notes-backup-YYYY-MM-DD.tar.gz
uv run notes-admin export backup.tar.gz      # custom filename

# Import notes from backup archive
uv run notes-admin import backup.tar.gz              # merge with existing
uv run notes-admin import backup.tar.gz --replace    # replace all notes
```

## MCP Client Setup

### Claude Desktop

Add to your config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

Restart Claude Desktop after saving. You should see the MCP indicator in the input box.

### VS Code

Add to `.vscode/mcp.json` in your workspace or configure globally:

```json
{
  "mcp": {
    "servers": {
      "notes": {
        "command": "uv",
        "args": ["run", "--directory", "/path/to/notes", "notes"]
      }
    }
  }
}
```

Requires VS Code 1.102+ with `chat.mcp.discovery.enabled` setting.

### Cursor

Add via Cursor Settings > MCP, or edit the `mcp.json` file:

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

### Claude Code

Configure via `/mcp` command in Claude Code, or add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

### Perplexity (macOS)

Perplexity's Mac app supports local MCP servers (paid subscribers, via Mac App Store).

Open Perplexity → Settings → MCP Servers → Add Server:

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

## Development

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check src tests
```

Type checking:

```bash
uv run mypy src
```

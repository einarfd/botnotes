"""Tag management tools for MCP."""

from notes.server import mcp
from notes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


@mcp.tool()
def list_tags() -> str:
    """List all tags used across notes.

    Returns:
        A formatted list of all tags with their note counts
    """
    service = _get_service()
    tag_counts = service.list_tags()

    if not tag_counts:
        return "No tags found."

    sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))

    output = ["Tags:", ""]
    for tag, count in sorted_tags:
        output.append(f"  - {tag} ({count} note{'s' if count != 1 else ''})")

    return "\n".join(output)


@mcp.tool()
def find_by_tag(tag: str) -> str:
    """Find all notes with a specific tag.

    Args:
        tag: The tag to search for

    Returns:
        A list of notes with the specified tag
    """
    service = _get_service()
    matching_notes = service.find_by_tag(tag)

    if not matching_notes:
        return f"No notes found with tag '{tag}'"

    output = [f"Notes tagged '{tag}':", ""]
    for note in matching_notes:
        output.append(f"  - **{note.title}** ({note.path})")

    return "\n".join(output)

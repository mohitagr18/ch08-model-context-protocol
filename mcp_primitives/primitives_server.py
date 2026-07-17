# primitives_server.py
#
# Section 8.1 — Why tool use needs a standard boundary
# Section 8.2 — Schema validation and bounded execution contexts
#
# Demonstrates all three MCP primitives:
#   1. @mcp.tool()     — model-callable function (read/write action)
#   2. @mcp.resource() — read-only data at a stable URI
#   3. @mcp.prompt()   — reusable prompt template
#
# Run with:  mcp dev mcp_primitives/primitives_server.py
# Install:   mcp install mcp_primitives/primitives_server.py

# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
from mcp.server.fastmcp import FastMCP
import os

# ==============================================================================
# SECTION 2: SERVER SETUP
# ==============================================================================
mcp = FastMCP(
    name="Chapter8PrimitivesServer",
    instructions=(
        "You are a note-taking assistant. "
        "Use add_note to save notes, read_notes to retrieve them, "
        "and note_summary_prompt when the user wants a summary."
    ),
)

# Notes are persisted to a local text file so state survives server restarts.
NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")


def _ensure_notes_file() -> None:
    """Create the notes file if it does not exist."""
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w") as f:
            f.write("")


# ==============================================================================
# SECTION 3: TOOL DEFINITIONS  (Primitive #1)
#
# Tools are the primary way models take action through MCP.
# FastMCP reads the type hints and docstring to auto-generate a JSON Schema,
# so the model always knows exactly what arguments are expected and
# what types are valid — this IS the schema validation boundary (Section 8.2).
# ==============================================================================

@mcp.tool()
def add_note(message: str) -> str:
    """
    Append a new note to the persistent notes file.

    Args:
        message: The text content of the note to save.

    Returns:
        A confirmation string.
    """
    _ensure_notes_file()
    with open(NOTES_FILE, "a") as f:
        f.write(message.strip() + "\n")
    return f"Note saved: '{message.strip()}'"


@mcp.tool()
def read_notes() -> str:
    """
    Read and return all saved notes.

    Returns:
        All notes as a newline-separated string,
        or a message indicating no notes exist yet.
    """
    _ensure_notes_file()
    with open(NOTES_FILE, "r") as f:
        content = f.read().strip()
    return content if content else "No notes saved yet."


@mcp.tool()
def delete_all_notes() -> str:
    """
    Permanently delete all saved notes.

    Returns:
        A confirmation string.
    """
    _ensure_notes_file()
    with open(NOTES_FILE, "w") as f:
        f.write("")
    return "All notes deleted."


# ==============================================================================
# SECTION 4: RESOURCE DEFINITION  (Primitive #2)
#
# Resources expose read-only data at a stable URI.
# Unlike tools, resources are NOT model-callable as actions — they are
# data sources the model can READ. The URI scheme makes them addressable
# and cacheable, which is a key part of the MCP boundary contract.
# ==============================================================================

@mcp.resource("notes://latest")
def get_latest_note() -> str:
    """
    Expose the most recently added note as a readable resource.

    URI: notes://latest

    Returns:
        The last line of the notes file, or a default message.
    """
    _ensure_notes_file()
    with open(NOTES_FILE, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines[-1] if lines else "No notes saved yet."


# ==============================================================================
# SECTION 5: PROMPT DEFINITION  (Primitive #3)
#
# Prompts are reusable, parameterizable prompt templates.
# They let the server author control the framing of a task, ensuring
# the model always approaches the task with the right context —
# another form of bounded execution (Section 8.2).
# ==============================================================================

@mcp.prompt()
def note_summary_prompt() -> str:
    """
    Generate a prompt asking the model to summarize all current notes.

    Returns:
        A ready-to-use prompt string with the notes embedded.
    """
    _ensure_notes_file()
    with open(NOTES_FILE, "r") as f:
        content = f.read().strip()

    if not content:
        return "There are no notes saved yet. Nothing to summarize."

    return (
        f"Please summarize the following notes concisely.\n"
        f"Focus on key themes and action items if present.\n\n"
        f"NOTES:\n{content}"
    )


# ==============================================================================
# SECTION 6: SERVER ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Default transport is stdio, which works with Claude Desktop and mcp dev.
    mcp.run()

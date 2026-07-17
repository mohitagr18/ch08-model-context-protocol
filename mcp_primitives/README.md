# Section 8.1 & 8.2 — MCP Primitives

This module demonstrates the **three foundational MCP primitives** and how FastMCP enforces
schema validation and bounded execution contexts.

## The Three Primitives

| Primitive | Decorator | Purpose | Example |
|---|---|---|---|
| **Tool** | `@mcp.tool()` | Model-callable function that takes action or fetches data | `add_note`, `read_notes` |
| **Resource** | `@mcp.resource("uri://path")` | Read-only data exposed at a stable URI | `notes://latest` |
| **Prompt** | `@mcp.prompt()` | Reusable prompt template the model can invoke | `note_summary_prompt` |

## How Schema Validation Works

FastMCP reads the Python type hints and docstrings on your functions and **automatically generates
a JSON Schema** that the model receives. This means:

- The model cannot pass a wrong type — the server rejects it before execution
- Every parameter is self-documenting
- No manual schema writing is needed

## Running

```bash
# Inspect in the MCP development UI
mcp dev mcp_primitives/primitives_server.py

# Install into Claude Desktop
mcp install mcp_primitives/primitives_server.py --name "Chapter 8 Primitives"
```

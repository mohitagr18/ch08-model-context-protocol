# Section 8.3 — Connecting Agents to External Systems Safely

This module shows how MCP acts as a **safe boundary** between a language model
and external APIs. The model never receives raw API keys or constructs URLs —
it calls a named tool with validated arguments, and the MCP server handles
everything else.

## Tools Exposed

| Tool | External System | What the Model Provides |
|---|---|---|
| `fetch_weather` | WeatherAPI.com | `city: str` only |
| `fetch_top_headlines` | NewsAPI.org | `topic: str`, `max_results: int` |

## Why This Is Safe

- API keys live in `.env` — the model never sees them
- Return payloads are parsed and trimmed — the model gets structured data, not raw HTTP responses
- `max_results` is bounded at the server (capped to 10) so the model cannot trigger excessive API calls
- All errors are caught and returned as structured error dicts rather than crashing

## Setup

1. Copy `.env.example` → `.env` in the project root
2. Add your `WEATHER_API_KEY` and `NEWS_API_KEY`

```bash
mcp dev external_tools/external_tools_server.py
```

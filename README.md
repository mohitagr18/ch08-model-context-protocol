# Chapter 8 — The Model Context Protocol (MCP)

This repository contains all code examples for **Chapter 8: The Model Context Protocol (MCP)** from the book.

It is organized to mirror the chapter sections:

| Section | Topic | Code |
|---|---|---|
| 8.1 | Why tool use needs a standard boundary | `mcp_primitives/primitives_server.py` |
| 8.2 | Schema validation and bounded execution | `mcp_primitives/primitives_server.py` |
| 8.3 | Connecting agents to external systems safely | `external_tools/external_tools_server.py` |
| 8.4 | Building an MCP server with a smart plug example | `smart_home/kasa_smart_home_server.py` + `smart_home/client_kasa_workflow.py` |

---

## Project Structure

```
ch08-model-context-protocol/
├── mcp_primitives/           # Section 8.1 & 8.2 — MCP primitives: tools, resources, prompts
│   ├── primitives_server.py
│   └── README.md
├── external_tools/           # Section 8.3 — Connecting to external APIs safely
│   ├── external_tools_server.py
│   └── README.md
├── smart_home/               # Section 8.4 — Smart plug MCP server & LangGraph client
│   ├── kasa_smart_home_server.py
│   ├── client_kasa_workflow.py
│   └── README.md
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.12+
- A package manager: `pip` or `uv`

### Install dependencies

```bash
pip install -r requirements.txt
```

Or with `uv`:

```bash
uv pip install -r requirements.txt
```

### Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` and fill in your keys:

```dotenv
# Required for Section 8.3 external tools server
WEATHER_API_KEY="your_weatherapi_key_here"
NEWS_API_KEY="your_newsapi_key_here"

# Required for Section 8.4 smart home server
KASA_DEVICE_IP="your_kasa_device_ip_here"

# Required for Section 8.4 client workflow
GROQ_API_KEY="your_groq_api_key_here"
```

---

## Running Each Server

### Section 8.1 / 8.2 — MCP Primitives

```bash
# Development mode (MCP Inspector)
mcp dev mcp_primitives/primitives_server.py

# Install into Claude Desktop
mcp install mcp_primitives/primitives_server.py
```

### Section 8.3 — External Tools

```bash
mcp dev external_tools/external_tools_server.py
```

### Section 8.4 — Smart Home (two terminals)

**Terminal 1 — Start the MCP server:**
```bash
python smart_home/kasa_smart_home_server.py
```

**Terminal 2 — Run the agent client:**
```bash
python smart_home/client_kasa_workflow.py
```

---

## Key Concepts Covered

- **MCP primitives**: The three building blocks — `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`
- **Schema validation**: FastMCP auto-generates JSON schemas from Python type hints
- **Bounded execution**: Environment-gated configuration prevents the model from selecting arbitrary targets
- **Transport modes**: `stdio` (Claude Desktop) vs. `streamable-http` (networked agents)
- **LangGraph + MCP**: Wrapping MCP tools in a ReAct agent via `langchain_mcp_adapters`

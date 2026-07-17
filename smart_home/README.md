# Section 8.4 — Building an MCP Server with a Smart Plug Example

This module contains the capstone example for Chapter 8: an end-to-end MCP system
that lets a LangGraph ReAct agent control a **TP-Link Kasa smart plug** over your local network.

## Architecture

```
┌─────────────────────────────────┐        HTTP (streamable-http)
│  client_kasa_workflow.py        │ ──────────────────────────────►
│  LangGraph ReAct Agent          │                               │
│  (ChatGroq + MCP tools)         │ ◄──────────────────────────── │
└─────────────────────────────────┘                               │
                                                    ┌─────────────────────────────┐
                                                    │  kasa_smart_home_server.py  │
                                                    │  FastMCP Server             │
                                                    │  (localhost:8000)           │
                                                    └──────────────┬──────────────┘
                                                                   │  python-kasa
                                                                   ▼
                                                    ┌─────────────────────────────┐
                                                    │  TP-Link Kasa Smart Plug    │
                                                    │  (local network, fixed IP)  │
                                                    └─────────────────────────────┘
```

## Tools Exposed by the Server

| Tool | What It Does |
|---|---|
| `list_smart_devices` | Returns name + power state of the configured plug |
| `turn_device_on` | Turns the plug on and returns new state |
| `turn_device_off` | Turns the plug off and returns new state |
| `get_device_status` | Returns the current power state without changing it |

## Bounded Execution

The server controls exactly **one** device, specified by `KASA_DEVICE_IP` in `.env`.
The model cannot choose a different target or discover other devices on the network —
this is the **bounded execution context** discussed in Section 8.2.

## Setup

1. Find your Kasa plug's IP address in your router admin panel (assign a static IP for reliability).
2. Add it to `.env`:
   ```
   KASA_DEVICE_IP=192.168.1.42
   ```
3. Add your Groq API key:
   ```
   GROQ_API_KEY=your_key_here
   ```

## Running

**Terminal 1 — Start the MCP server:**
```bash
python smart_home/kasa_smart_home_server.py
```
Expect: `STATUS: Kasa Smart Home MCP Server running on http://localhost:8000/mcp`

**Terminal 2 — Run the agent workflow:**
```bash
python smart_home/client_kasa_workflow.py
```

The agent will list, turn on, check status, and turn off the plug in sequence.

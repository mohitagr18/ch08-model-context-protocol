# Chapter 8 — The Model Context Protocol (MCP)

This repository contains all code examples for **Chapter 8: The Model Context Protocol (MCP)** from the book.

It is organized to mirror the chapter sections:

| Section | Topic | Code |
|---|---|---|
| 8.1 | Why tool use needs a standard boundary | `mcp_primitives/primitives_server.py` |
| 8.2 | Schema validation and bounded execution | `mcp_primitives/primitives_server.py` |
| 8.3 | Connecting agents to external systems safely | `external_tools/external_tools_server.py` |
| 8.4 | Building an MCP server with a smart plug example | `smart_home/` |

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
│   ├── kasa_smart_home_server.py   # Real server — requires physical Kasa plug
│   ├── mock_kasa_server.py         # Mock server — no hardware needed
│   ├── client_kasa_workflow.py     # LangGraph ReAct agent client
│   ├── test_mock.py                # 7 automated tool-level tests
│   └── README.md
├── workflow/
│   └── workflow.md               # Mermaid diagrams for each chapter section
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites
- Python 3.12+
- A package manager: `pip` or `uv`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or with `uv`:

```bash
uv pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` with your keys (see the **API Keys** section below).

---

## API Keys

| Key | Section | Free tier | Where to get it |
|---|---|---|---|
| `GROQ_API_KEY` | 8.4 client | Yes — generous free tier | [console.groq.com](https://console.groq.com) → API Keys → Create key |
| `WEATHER_API_KEY` | 8.3 | Yes — 1M calls/month | [weatherapi.com](https://www.weatherapi.com) → sign up → dashboard |
| `NEWS_API_KEY` | 8.3 | Yes — 100 req/day | [newsapi.org](https://newsapi.org) → free developer plan |
| `KASA_DEVICE_IP` | 8.4 real server only | N/A — your device | See [Finding Your Kasa Device IP](#finding-your-kasa-device-ip) below |

> **Minimum to get started:** only `GROQ_API_KEY` is needed to run the Section 8.4 mock workflow end-to-end. No hardware required.

---

## Running the Code

### Section 8.1 / 8.2 — MCP Primitives

```bash
# Development mode (launches MCP Inspector in browser)
mcp dev mcp_primitives/primitives_server.py

# Install into Claude Desktop
mcp install mcp_primitives/primitives_server.py
```

### Section 8.3 — External Tools

```bash
mcp dev external_tools/external_tools_server.py
```

Requires `WEATHER_API_KEY` and `NEWS_API_KEY` in `.env`.

---

### Section 8.4 — Smart Home

Two paths depending on whether you have a physical Kasa plug.

---

#### 🧪 Path A — Mock server (no hardware needed)

Use this path to test the full MCP + LangGraph stack without a physical device.
The mock server simulates the plug state in memory with identical tool signatures.

**Step 1 — Add your Groq key to `.env`:**
```dotenv
GROQ_API_KEY="your_groq_key_here"
```

**Step 2 — Terminal 1: start the mock MCP server:**
```bash
python smart_home/mock_kasa_server.py
```
Expected output:
```
STATUS: Starting Mock Kasa Smart Home MCP Server...
STATUS: No physical device required — state is simulated in memory.
STATUS: Transport — streamable-http on http://localhost:8000/mcp
STATUS: Run client_kasa_workflow.py in a second terminal to test.
```

**Step 3 — Terminal 2: run the automated tool tests (no LLM needed):**
```bash
python smart_home/test_mock.py
```
Expected output:
```
=======================================================
  Chapter 8 — Mock Kasa Server Test Suite
=======================================================
  Server : http://localhost:8000/mcp
  Tests  : 7

[ TEST 1 ] Tool discovery
  ✓ PASS  All 4 tools registered
[ TEST 2 ] list_smart_devices
  ✓ PASS  Returns list with one device dict
[ TEST 3 ] get_device_status (initial state = OFF)
  ✓ PASS  Initial state is OFF
[ TEST 4 ] turn_device_on
  ✓ PASS  Device turned ON, is_on=True
[ TEST 5 ] get_device_status (after turn_on)
  ✓ PASS  Status confirmed ON (no state change)
[ TEST 6 ] turn_device_off
  ✓ PASS  Device turned OFF, is_on=False
[ TEST 7 ] get_device_status (after turn_off)
  ✓ PASS  Status confirmed OFF (no state change)

=======================================================
  ALL TESTS PASSED  (7/7)
=======================================================
```

**Step 4 — Terminal 2: run the full LangGraph agent workflow:**
```bash
python smart_home/client_kasa_workflow.py
```
The agent runs four steps (list → turn on → check status → turn off) against the mock.
Output is identical to the real plug — the agent cannot tell the difference.

---

#### 🔌 Path B — Real Kasa plug

Use this path once you have a physical TP-Link Kasa smart plug on your local network.
If you need help finding your device IP or alias, see
[Finding Your Kasa Device IP](#finding-your-kasa-device-ip) at the end of this file.

**Step 1 — Find your plug’s IP and alias** — see [Finding Your Kasa Device IP](#finding-your-kasa-device-ip).

**Step 2 — Add all required keys to `.env`:**
```dotenv
GROQ_API_KEY="your_groq_key_here"
KASA_DEVICE_IP="192.168.1.42"        # replace with your plug's IP
KASA_DEVICE_ALIAS="Smart Plug"       # replace with your plug's alias
```

**Step 3 — Terminal 1: start the real MCP server:**
```bash
python smart_home/kasa_smart_home_server.py
```
Expected output:
```
STATUS: Starting Kasa Smart Home MCP Server...
STATUS: Target device IP — 192.168.1.42
STATUS: Transport — streamable-http on http://localhost:8000/mcp
```

**Step 4 — Terminal 2: run the agent client:**
```bash
python smart_home/client_kasa_workflow.py
```
The agent will list your plug, turn it on, check its status, then turn it off.
You will see the physical plug respond to each command in real time.

---

## Key Concepts Covered

- **MCP primitives**: The three building blocks — `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`
- **Schema validation**: FastMCP auto-generates JSON schemas from Python type hints
- **Bounded execution**: Environment-gated configuration prevents the model from selecting arbitrary targets
- **Transport modes**: `stdio` (Claude Desktop) vs. `streamable-http` (networked agents)
- **LangGraph + MCP**: Wrapping MCP tools in a ReAct agent via `langchain_mcp_adapters`
- **Mock testing**: Validating the full MCP stack without hardware using an in-memory server

---

## Finding Your Kasa Device IP

This section explains how to find your TP-Link Kasa plug’s IP address and alias
and set a static IP so it doesn’t change between sessions.

### Option 1 — Use the Kasa mobile app (easiest)

1. Open the **Kasa Smart** app on your phone
2. Tap the plug device you want to use
3. Tap the **gear icon** (⚙️) in the top-right corner to open device settings
4. Scroll down to **Device Info**
5. Note the **IP Address** and **Device Name** (this is your alias)

> The device name shown in the Kasa app is the value to use for `KASA_DEVICE_ALIAS`.

### Option 2 — Use python-kasa discovery (no app needed)

python-kasa ships with a discovery CLI that scans your local network and
prints every Kasa device it finds, including IP and alias:

```bash
# Install python-kasa if not already installed
pip install python-kasa

# Run discovery (scans the local subnet automatically)
python -m kasa discover
```

Example output:
```
Discovering devices on 255.255.255.255 for 3 seconds

Found device: Smart Plug
        Host: 192.168.1.42
       Alias: Smart Plug
       Model: EP10(US)
  HW version: 1.0
  SW version: 1.0.13
   Is on    : False
```

Copy the `Host` value into `KASA_DEVICE_IP` and the `Alias` value into `KASA_DEVICE_ALIAS`.

### Option 3 — Check your router admin panel

1. Open a browser and go to your router’s admin panel
   (usually `http://192.168.1.1` or `http://192.168.0.1` — check the label on your router)
2. Log in with your router credentials
3. Find the **Connected Devices** or **DHCP Client List** section
4. Look for a device named something like `TP-LINK_Power Strip` or `Kasa`
5. Note its current IP address

### Assigning a Static IP (recommended)

By default, your router assigns a new IP to the plug each time it reconnects.
A static IP ensures the plug is always reachable at the same address.

**On most home routers:**
1. In the router admin panel, go to **DHCP Reservations** or **Address Reservation**
   (the label varies by router brand)
2. Find your Kasa plug in the list (match by MAC address, shown in the Kasa app under Device Info)
3. Enter the IP address you want to reserve (e.g. `192.168.1.42`)
4. Save and reboot the plug by unplugging it and plugging it back in
5. Confirm the plug comes back online at the reserved IP using `python -m kasa discover`

> **Why this matters:** if you skip static IP assignment, the plug’s IP may change
> after a router restart and `kasa_smart_home_server.py` will fail to connect
> until you update `KASA_DEVICE_IP` in `.env`.

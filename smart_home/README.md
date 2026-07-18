# Section 8.4 — Building an MCP Server with a Smart Plug Example

This module contains the capstone example for Chapter 8: an end-to-end MCP system
that lets a LangGraph ReAct agent control a TP-Link Kasa smart plug over your local
network — or a fully simulated mock if you don't have the hardware.

---

## Files

| File | Purpose | Hardware needed? |
|---|---|---|
| `kasa_smart_home_server.py` | Real MCP server — controls a physical Kasa plug | Yes |
| `mock_kasa_server.py` | Drop-in mock server — simulates plug state in memory | No |
| `client_kasa_workflow.py` | LangGraph ReAct agent (works with both servers) | No |
| `test_mock.py` | 7 automated tool-level tests against the mock server | No |

---

## Architecture

```
┌────────────────────────────────┐        HTTP (streamable-http, port 8000)
│  client_kasa_workflow.py        │  ──────────────────────────► ┌─────────────────────────┐
│  LangGraph ReAct Agent          │                           │ mock_kasa_server.py    │
│  ChatGroq (llama-3.1-8b-instant)│  ◄──────────────────────────  │   OR                   │
│  MultiServerMCPClient           │                           │ kasa_smart_home_server │
└────────────────────────────────┘                           └─────────────────────────┘
```

---

## API Keys Required

| Key | Used by | Free tier | Where to get it |
|---|---|---|---|
| `OPENAI_API_KEY` | `client_kasa_workflow.py` | Yes | [platform.openai.com](https://platform.openai.com/) |
| `GROQ_API_KEY` | `client_kasa_workflow.py` | Yes — generous free tier | [console.groq.com](https://console.groq.com) |
| `NVIDIA_API_KEY` | `client_kasa_workflow.py` | Yes — free credits | [build.nvidia.com](https://build.nvidia.com) |
| `KASA_DEVICE_IP` | `kasa_smart_home_server.py` only | N/A (your device) | Router admin panel |
| `KASA_DEVICE_ALIAS` | `kasa_smart_home_server.py` only | N/A (your device) | Label on your plug |

> **No API key is needed to run `mock_kasa_server.py` or `test_mock.py`.**
> `GROQ_API_KEY` is only needed when running `client_kasa_workflow.py`.

---

## Quick Start: Testing Without Hardware

### Step 1 — Add your LLM API key(s) to `.env`
```bash
# .env (in the repo root)
OPENAI_API_KEY=your_openai_key_here
# GROQ_API_KEY=your_key_here
# NVIDIA_API_KEY=your_nvidia_key_here
```
Set `OPENAI_API_KEY` for `gpt-5.4-nano`, or use `GROQ_API_KEY` if you prefer Groq. Add `NVIDIA_API_KEY` only as a fallback when the other providers are unavailable.

### Step 2 — Terminal 1: start the mock server
```bash
python smart_home/mock_kasa_server.py
```
Expected output:
```
STATUS: Starting Mock Kasa Smart Home MCP Server...
STATUS: No physical device required — state is simulated in memory.
STATUS: Transport — streamable-http on http://localhost:8000/mcp
```

### Step 3 — Terminal 2, Option A: run the automated tool tests (no LLM needed)
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

### Step 3 — Terminal 2, Option B: run the full agent workflow
```bash
python smart_home/client_kasa_workflow.py
```
The agent will run the same four steps (list → on → status → off) against the mock.
Output is identical to the real plug — the agent cannot tell the difference.

---

## Running With a Real Kasa Plug

1. Find your plug's IP in your router admin panel (assign a static IP for reliability)
2. Add to `.env` in the repo root:
   ```
   KASA_DEVICE_IP=192.168.1.42
   KASA_DEVICE_ALIAS=Smart Plug
   GROQ_API_KEY=your_key_here
   ```
3. Run:
   ```bash
   # Terminal 1
   python smart_home/kasa_smart_home_server.py

   # Terminal 2
   python smart_home/client_kasa_workflow.py
   ```

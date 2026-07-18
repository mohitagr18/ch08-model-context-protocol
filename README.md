# Chapter 8 — The Model Context Protocol (MCP)

Code examples for **Chapter 8: The Model Context Protocol (MCP)** from the book.

---

## Step 1 — Setup

**1a. Install dependencies**

```bash
pip install -r requirements.txt
```

**1b. Copy the environment file and add your keys**

```bash
cp .env.example .env
```

Open `.env` and fill in:

```dotenv
# Minimum required to run the mock workflow (no hardware needed)
GROQ_API_KEY="your_groq_key_here"

# Required only for Section 8.3 external tools
WEATHER_API_KEY="your_weatherapi_key_here"
NEWS_API_KEY="your_newsapi_key_here"

# Required only for Section 8.4 with a real Kasa plug
KASA_DEVICE_IP="192.168.1.42"
KASA_DEVICE_ALIAS="Smart Plug"
```

Where to get each key — see [API Keys](#api-keys) at the end of this file.

---

## Step 2 — Run

### Option A — No hardware (mock smart plug)

Use this if you don’t have a physical Kasa plug. Only `GROQ_API_KEY` is needed.

**Terminal 1:**
```bash
python smart_home/mock_kasa_server.py
```

**Terminal 2:**
```bash
# Validate the server tools first (no LLM needed)
python smart_home/test_mock.py

# Then run the full agent
python smart_home/client_kasa_workflow.py
```

---

### Option B — Real Kasa plug

Use this when you have a physical TP-Link Kasa plug on your local network.
Make sure `KASA_DEVICE_IP` and `KASA_DEVICE_ALIAS` are set in `.env`.
Need help finding them? See [Finding Your Kasa Device IP](#finding-your-kasa-device-ip).

**Terminal 1:**
```bash
python smart_home/kasa_smart_home_server.py
```

**Terminal 2:**
```bash
python smart_home/client_kasa_workflow.py
```

---

## Project Structure

```
ch08-model-context-protocol/
├── mcp_primitives/               # §8.1 & 8.2 — Tools, resources, prompts
│   ├── primitives_server.py
│   └── README.md
├── external_tools/               # §8.3 — External APIs
│   ├── external_tools_server.py
│   └── README.md
├── smart_home/                   # §8.4 — Smart plug example
│   ├── kasa_smart_home_server.py  # Real server (requires plug)
│   ├── mock_kasa_server.py        # Mock server (no hardware)
│   ├── client_kasa_workflow.py    # LangGraph ReAct agent
│   ├── test_mock.py               # Automated tool tests
│   └── README.md
├── workflow/
│   └── workflow.md                # Mermaid diagrams for each section
├── .env.example
├── requirements.txt
└── README.md
```

---

## API Keys

| Key | Needed for | Free tier | Where to get it |
|---|---|---|---|
| `GROQ_API_KEY` | Agent client (both options) | Yes | [console.groq.com](https://console.groq.com) → API Keys → Create key |
| `WEATHER_API_KEY` | §8.3 external tools only | Yes — 1M calls/month | [weatherapi.com](https://www.weatherapi.com) → sign up → dashboard |
| `NEWS_API_KEY` | §8.3 external tools only | Yes — 100 req/day | [newsapi.org](https://newsapi.org) → free developer plan |
| `KASA_DEVICE_IP` | Option B only | N/A | See below |
| `KASA_DEVICE_ALIAS` | Option B only | N/A | See below |

---

## Finding Your Kasa Device IP

Three ways to find your plug’s IP and alias, ordered by ease.

### Option 1 — Kasa mobile app

1. Open the **Kasa Smart** app on your phone
2. Tap your plug → tap the **gear icon** ⚙️ (top right)
3. Scroll to **Device Info**
4. Note the **IP Address** and **Device Name** (Device Name = `KASA_DEVICE_ALIAS`)

### Option 2 — python-kasa discovery CLI

```bash
python -m kasa discover
```

Example output:
```
Found device: Smart Plug
        Host: 192.168.1.42
       Alias: Smart Plug
       Model: EP10(US)
   Is on    : False
```

Copy `Host` → `KASA_DEVICE_IP` and `Alias` → `KASA_DEVICE_ALIAS`.

### Option 3 — Router admin panel

1. Go to `http://192.168.1.1` or `http://192.168.0.1` in your browser
2. Log in and open **Connected Devices** or **DHCP Client List**
3. Find the Kasa device and note its IP

### Assigning a static IP (recommended)

Without a static IP, your router may assign a new IP to the plug after a restart,
breaking the value in `.env`.

1. In your router admin panel go to **DHCP Reservations** or **Address Reservation**
2. Match your plug by MAC address (visible in the Kasa app under Device Info)
3. Reserve a fixed IP (e.g. `192.168.1.42`)
4. Unplug and replug the device to apply
5. Confirm with `python -m kasa discover`

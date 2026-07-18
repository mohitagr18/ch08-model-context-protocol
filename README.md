# Chapter 8 — The Model Context Protocol (MCP)

Code examples for **Chapter 8: The Model Context Protocol (MCP)** from the book.

---

## Step 1 — Setup

**1a. Install uv (if you don’t have it)**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**1b. Create the virtual environment and install all dependencies**

```bash
uv sync
```

**1c. Copy the environment file and add your keys**

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum one LLM key:

```dotenv
# Pick one — see API Keys table below for where to get each
OPENAI_API_KEY="your_openai_key_here"  # default
GROQ_API_KEY="your_groq_key_here"      # default
NVIDIA_API_KEY="your_nvidia_key_here"  # fallback if Groq hits rate limits
```

The client auto-selects the provider: Groq is used if `GROQ_API_KEY` is set;
if only `NVIDIA_API_KEY` is set, it switches to `ChatNVIDIA` automatically.

---

## Step 2 — Run

### Option A — No hardware (mock smart plug)

Use this if you don’t have a physical Kasa plug.

**Terminal 1:**
```bash
uv run python smart_home/mock_kasa_server.py
```

**Terminal 2:**
```bash
# Validate the server tools first (no LLM needed)
uv run python smart_home/test_mock.py

# Then run the full agent
uv run python smart_home/client_kasa_workflow.py
```

---

### Option B — Real Kasa plug

Use this when you have a physical TP-Link Kasa plug on your local network.
Make sure `KASA_DEVICE_IP` and `KASA_DEVICE_ALIAS` are set in `.env`.
Need help finding them? See [Finding Your Kasa Device IP](#finding-your-kasa-device-ip).

**Terminal 1:**
```bash
uv run python smart_home/kasa_smart_home_server.py
```

**Terminal 2:**
```bash
uv run python smart_home/client_kasa_workflow.py
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
│   └── test_mock.py               # Automated tool tests
├── workflow/
│   └── workflow.md                # Mermaid diagrams for each section
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md
```

---

## API Keys

| Key | Needed for | Free tier | Where to get it |
|---|---|---|---|
| `GROQ_API_KEY` | Agent client — default LLM | Yes | [console.groq.com](https://console.groq.com) → API Keys → Create key |
| `NVIDIA_API_KEY` | Agent client — fallback LLM | Yes — free credits | [build.nvidia.com](https://build.nvidia.com) → sign in → Get API Key |
| `WEATHER_API_KEY` | §8.3 external tools only | Yes — 1M calls/month | [weatherapi.com](https://www.weatherapi.com) → sign up → dashboard |
| `NEWS_API_KEY` | §8.3 external tools only | Yes — 100 req/day | [newsapi.org](https://newsapi.org) → free developer plan |
| `KASA_DEVICE_IP` | Option B only | N/A | See below |
| `KASA_DEVICE_ALIAS` | Option B only | N/A | See below |

> **Groq vs NVIDIA:** set `GROQ_API_KEY` for normal use. If you hit Groq’s
> rate limit, add `NVIDIA_API_KEY` to `.env` and remove or comment out `GROQ_API_KEY`.
> The client switches providers automatically — no code change needed.

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
uv run python -m kasa discover
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
5. Confirm with `uv run python -m kasa discover`

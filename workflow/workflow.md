# Chapter 8 — Workflow Diagrams

This file contains Mermaid diagrams for each section of **Chapter 8: The Model Context Protocol (MCP)**.
Each diagram is self-contained and can be dropped directly into the corresponding section of the manuscript.

---

## Section 8.1 — Why Tool Use Needs a Standard Boundary

> **Diagram 8.1a — The Problem: No Standard, No Safety**
>
> Shows what happens when agents call tools directly without a protocol boundary —
> each integration is bespoke, there is no validation, and the model can trigger
> anything. Use this as the "before" picture to motivate MCP.

```mermaid
flowchart TD
    U(["👤 User"])
    LLM["LLM\n(no boundary)"]
    T1["Tool A\nWeather API"]
    T2["Tool B\nDatabase\n(direct write)"]
    T3["Tool C\nSmart Plug\n(raw TCP)"]
    T4["Tool D\nFile System\n(unrestricted)"]

    U -->|natural language| LLM
    LLM -->|custom code, no schema| T1
    LLM -->|custom code, no schema| T2
    LLM -->|custom code, no schema| T3
    LLM -->|custom code, no schema| T4

    style LLM fill:#f87171,color:#fff
    style T2 fill:#fbbf24
    style T3 fill:#fbbf24
    style T4 fill:#fbbf24

    classDef problem stroke:#ef4444,stroke-width:2px,stroke-dasharray:5 5
    class T2,T3,T4 problem
```

> **Diagram 8.1b — The Solution: MCP as a Standard Boundary**
>
> Shows the same scenario after MCP is introduced. Every tool is registered
> on an MCP server. The model only sees named tools with documented schemas;
> it cannot bypass the boundary.

```mermaid
flowchart TD
    U(["👤 User"])
    LLM["LLM / Agent"]

    subgraph MCP_BOUNDARY ["MCP Boundary"]
        direction TB
        MCPClient["MCP Client\n(MultiServerMCPClient)"]
        MCPServer["MCP Server\n(FastMCP)"]
        Tools["Registered Tools\n• fetch_weather\n• turn_device_on\n• turn_device_off\n• get_device_status"]
        MCPClient -->|"Tool call + validated args"| MCPServer
        MCPServer --> Tools
    end

    ExtSys["External Systems\n(APIs / Devices / DBs)"]

    U -->|natural language| LLM
    LLM -->|"tool name + typed args"| MCPClient
    Tools -->|"structured result"| MCPClient
    MCPClient -->|"result"| LLM
    LLM -->|"natural language response"| U
    Tools -->|"safe, bounded calls"| ExtSys

    style MCP_BOUNDARY fill:#f0fdf4,stroke:#22c55e,stroke-width:2px
    style MCPServer fill:#22c55e,color:#fff
    style MCPClient fill:#86efac
    style LLM fill:#3b82f6,color:#fff
```

---

## Section 8.2 — Schema Validation and Bounded Execution Contexts

> **Diagram 8.2a — How FastMCP Generates a JSON Schema from Python Type Hints**
>
> Illustrates the compile-time path from a Python function signature to
> the JSON Schema the model receives. Use this to explain why the model
> can never pass a wrong type.

```mermaid
flowchart LR
    subgraph SERVER ["MCP Server (primitives_server.py)"]
        direction TB
        PY["Python function\n\n@mcp.tool()\ndef add_note(message: str) -> str"]
        SCHEMA["Auto-generated JSON Schema\n\n{\n  name: 'add_note',\n  inputSchema: {\n    type: 'object',\n    properties: {\n      message: { type: 'string' }\n    },\n    required: ['message']\n  }\n}"]
        PY -->|"FastMCP introspects\ntype hints + docstring"| SCHEMA
    end

    MODEL["LLM"]
    SCHEMA -->|"Schema advertised\nto model at startup"| MODEL
    MODEL -->|"{ message: 'Buy milk' }\n(validated before execution)"| PY

    style SERVER fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style PY fill:#dbeafe
    style SCHEMA fill:#bfdbfe
    style MODEL fill:#3b82f6,color:#fff
```

> **Diagram 8.2b — Bounded Execution: What the Model Can and Cannot Do**
>
> Shows the execution boundary enforced by the smart home server.
> The model can call exactly the four exposed tools; it cannot discover
> other devices, change the target IP, or access the network directly.

```mermaid
flowchart TD
    MODEL["LLM / Agent"]

    subgraph ALLOWED ["✅ Within the Execution Boundary"]
        T1["list_smart_devices"]
        T2["turn_device_on"]
        T3["turn_device_off"]
        T4["get_device_status"]
    end

    subgraph BLOCKED ["🚫 Outside the Execution Boundary"]
        B1["Choose a different\ndevice IP"]
        B2["Scan the local\nnetwork"]
        B3["Access the file\nsystem"]
        B4["Make raw TCP\ncalls"]
    end

    ENV[".env file\nKASA_DEVICE_IP\n(server-controlled)"]

    MODEL --> ALLOWED
    MODEL -. "blocked by MCP boundary" .-> BLOCKED
    ENV -->|"read once at startup"| T1
    ENV -->|"read once at startup"| T2
    ENV -->|"read once at startup"| T3
    ENV -->|"read once at startup"| T4

    style ALLOWED fill:#f0fdf4,stroke:#22c55e,stroke-width:2px
    style BLOCKED fill:#fef2f2,stroke:#ef4444,stroke-width:2px,stroke-dasharray:6 4
    style ENV fill:#fef9c3,stroke:#ca8a04
    style MODEL fill:#3b82f6,color:#fff
```

---

## Section 8.3 — Connecting Agents to External Systems Safely

> **Diagram 8.3 — Safe External API Gateway Pattern**
>
> Shows how the MCP server acts as an API gateway. The model supplies
> only user-facing arguments; the server handles auth, caps, parsing,
> and error handling before returning a clean structured response.

```mermaid
sequenceDiagram
    actor User
    participant Agent as LLM Agent
    participant Client as MCP Client
    participant Server as MCP Server<br/>(external_tools_server.py)
    participant WeatherAPI as WeatherAPI.com
    participant NewsAPI as NewsAPI.org

    User->>Agent: "What's the weather in Austin?<br/>And get me 3 AI news headlines."

    Note over Agent: Reasons about intent,<br/>selects tools

    Agent->>Client: fetch_weather(city="Austin")
    Client->>Server: Tool call: fetch_weather
    Note over Server: Loads WEATHER_API_KEY<br/>from env (never from model)
    Server->>WeatherAPI: GET /current.json?q=Austin
    WeatherAPI-->>Server: Raw JSON (full payload)
    Note over Server: Parses + trims:<br/>returns 7 fields only
    Server-->>Client: {city, temp_c, condition, ...}
    Client-->>Agent: Structured weather dict

    Agent->>Client: fetch_top_headlines(topic="AI agents", max_results=3)
    Client->>Server: Tool call: fetch_top_headlines
    Note over Server: Caps max_results ≤ 10<br/>server-side (model cannot override)
    Server->>NewsAPI: GET /v2/everything?q=AI+agents&pageSize=3
    NewsAPI-->>Server: Raw JSON (full payload)
    Note over Server: Extracts title, source,<br/>published_at, url only
    Server-->>Client: {topic, total_found, articles[3]}
    Client-->>Agent: Structured headlines dict

    Agent->>User: "In Austin it's 91°F and sunny.<br/>Here are 3 recent AI headlines..."
```

---

## Section 8.4 — Building an MCP Server with a Smart Plug Example

> **Diagram 8.4a — End-to-End Architecture**
>
> The full system diagram referenced in the Medium article. Shows every
> layer: user → agent → MCP client → MCP server → python-kasa → physical device.

```mermaid
flowchart TD
    U(["👤 User"])

    subgraph AGENT_SIDE ["Agent Process (client_kasa_workflow.py)"]
        direction TB
        GROQ["ChatGroq LLM\n(llama-3.1-8b-instant)"]
        REACT["LangGraph\nReAct Agent"]
        MCPC["MultiServerMCPClient\nhttp://localhost:8000/mcp"]
        GROQ <--> REACT
        REACT <--> MCPC
    end

    subgraph SERVER_SIDE ["Server Process (kasa_smart_home_server.py)"]
        direction TB
        FASTMCP["FastMCP Server\n(streamable-http, port 8000)"]
        TOOLS["Registered Tools\n• list_smart_devices\n• turn_device_on\n• turn_device_off\n• get_device_status"]
        KASA_SDK["python-kasa SDK"]
        FASTMCP --> TOOLS
        TOOLS --> KASA_SDK
    end

    PLUG["🔌 TP-Link Kasa\nSmart Plug\n(local network)"]
    ENV[".env\nKASA_DEVICE_IP\nGROQ_API_KEY"]

    U -->|"Natural language command"| REACT
    MCPC <-->|"HTTP — MCP protocol"| FASTMCP
    KASA_SDK <-->|"Wi-Fi (python-kasa)"| PLUG
    PLUG -->|"Power state feedback"| KASA_SDK
    ENV -->|"Loaded at startup"| FASTMCP
    ENV -->|"Loaded at startup"| MCPC
    REACT -->|"Natural language response"| U

    style AGENT_SIDE fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style SERVER_SIDE fill:#f0fdf4,stroke:#22c55e,stroke-width:2px
    style PLUG fill:#fef9c3,stroke:#ca8a04
    style ENV fill:#fef9c3,stroke:#ca8a04,stroke-dasharray:4 3
    style GROQ fill:#3b82f6,color:#fff
    style FASTMCP fill:#22c55e,color:#fff
```

> **Diagram 8.4b — Step-by-Step Request Lifecycle**
>
> Derived from the Medium article's "Automation Play-by-Play" section.
> Maps each of the six numbered steps in the article to a sequence diagram.
> Use this alongside the code walkthrough in section 8.4.

```mermaid
sequenceDiagram
    actor User
    participant Agent as ReAct Agent<br/>(client_kasa_workflow.py)
    participant LLM as ChatGroq LLM
    participant MCPClient as MultiServerMCPClient
    participant MCPServer as FastMCP Server<br/>(kasa_smart_home_server.py)
    participant Kasa as python-kasa SDK
    participant Plug as 🔌 Smart Plug

    Note over User,Plug: STEP 1 — User speaks their wish
    User->>Agent: "Turn on the Smart Plug."

    Note over Agent,LLM: STEP 2 — The AI thinks and plans
    Agent->>LLM: Prompt + tool schemas
    LLM-->>Agent: Tool choice: turn_device_on()

    Note over Agent,MCPServer: STEP 3 — The client makes the call
    Agent->>MCPClient: turn_device_on()
    MCPClient->>MCPServer: POST /mcp — tool: turn_device_on

    Note over MCPServer,Plug: STEP 4 — The server gets to work
    MCPServer->>Kasa: plug.turn_on()
    Kasa->>Plug: Wi-Fi command: power ON

    Note over Plug,MCPServer: STEP 5 — The plug responds
    Plug-->>Kasa: ACK (is_on: true)
    Kasa-->>MCPServer: State updated
    MCPServer-->>MCPClient: {alias, is_on: true, status: success}

    Note over MCPClient,User: STEP 6 — The AI reports back
    MCPClient-->>Agent: Structured result
    Agent->>LLM: Format response
    LLM-->>Agent: "The Smart Plug is now on."
    Agent-->>User: "The Smart Plug is now on."
```

> **Diagram 8.4c — Four-Step Agent Workflow (Client Test Sequence)**
>
> Maps directly to the four `agent.ainvoke()` calls in `client_kasa_workflow.py`.
> Use this to preview the demo output readers will see when they run the code.

```mermaid
stateDiagram-v2
    direction LR

    [*] --> Step1

    Step1 : STEP 1\nList devices
    Step1 : → list_smart_devices()
    Step1 : ← [Smart Plug, is_on: ?]

    Step2 : STEP 2\nTurn ON
    Step2 : → turn_device_on()
    Step2 : ← {is_on: true, status: success}

    Step3 : STEP 3\nStatus check
    Step3 : → get_device_status()
    Step3 : ← {is_on: true}\n(no state change)

    Step4 : STEP 4\nTurn OFF
    Step4 : → turn_device_off()
    Step4 : ← {is_on: false, status: success}

    Step1 --> Step2
    Step2 --> Step3
    Step3 --> Step4
    Step4 --> [*]
```

> **Diagram 8.4d — MCP Tool Registration and Discovery**
>
> Shows how tools move from Python `@mcp.tool()` decorators on the server
> to the agent's available tool list at runtime. Use this to explain
> the "convention over configuration" design of FastMCP.

```mermaid
flowchart LR
    subgraph SERVER ["kasa_smart_home_server.py"]
        D1["@mcp.tool()\nlist_smart_devices"]
        D2["@mcp.tool()\nturn_device_on"]
        D3["@mcp.tool()\nturn_device_off"]
        D4["@mcp.tool()\nget_device_status"]
    end

    subgraph REGISTRY ["FastMCP Tool Registry"]
        R["Internal tool manifest\n(name + JSON Schema\nper tool)"]
    end

    subgraph CLIENT ["client_kasa_workflow.py"]
        GE["client.get_tools()"]
        AGENT["create_react_agent\n(model, tools=tools)"]
        GE --> AGENT
    end

    D1 & D2 & D3 & D4 -->|"registered at\nserver startup"| R
    R -->|"served at GET /mcp\n(tool list + schemas)"| GE

    style SERVER fill:#f0fdf4,stroke:#22c55e,stroke-width:2px
    style REGISTRY fill:#dcfce7,stroke:#16a34a
    style CLIENT fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style AGENT fill:#3b82f6,color:#fff
```

---

## Section 8.5 — Summary Diagram

> **Diagram 8.5 — Chapter 8 Concept Map**
>
> A single capstone diagram that ties together all four sections.
> Use as the closing visual in the chapter summary.

```mermaid
mindmap
  root((MCP))
    Standard Boundary
      Replaces bespoke integrations
      Model sees tool names only
      No direct system access
    Three Primitives
      Tools
        Model-callable actions
        Auto JSON Schema from type hints
      Resources
        Read-only URI-addressable data
        notes://latest
      Prompts
        Reusable prompt templates
        Server controls framing
    Safe External Connections
      API keys in env only
      Trimmed response payloads
      Server-side result caps
    Smart Plug Example
      FastMCP server
      streamable-http transport
      python-kasa SDK
      LangGraph ReAct agent
      MultiServerMCPClient
```

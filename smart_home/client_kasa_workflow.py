# client_kasa_workflow.py
#
# LangGraph ReAct agent that controls a smart plug via the MCP server.
#
# LLM provider is selected by which key is present in .env:
#   GROQ_API_KEY   → ChatGroq  (default, llama-3.1-8b-instant)
#   NVIDIA_API_KEY → ChatNVIDIA (fallback, nvidia/llama-3.1-nemotron-nano-8b-v1)
#
# Requires the MCP server to be running first:
#   python smart_home/mock_kasa_server.py        (no hardware)
#   python smart_home/kasa_smart_home_server.py  (real plug)

# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
import asyncio
import os
import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# ==============================================================================
# SECTION 2: LLM SELECTION
# Auto-selects provider based on which API key is present in .env.
# ==============================================================================

def _build_llm():
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    nvidia_key = os.getenv("NVIDIA_API_KEY")

    if openai_key:
        from langchain_openai import ChatOpenAI
        model = "gpt-5.4-nano"
        print(f"LLM : ChatOpenAI — {model}")
        return ChatOpenAI(model=model, api_key=openai_key, timeout=60, max_retries=2)

    if groq_key:
        from langchain_groq import ChatGroq
        print("LLM : ChatGroq — llama-3.1-8b-instant")
        return ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key)

    if nvidia_key:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        model = "nvidia/llama-3.1-nemotron-nano-8b-v1"
        print(f"LLM : ChatNVIDIA — {model}")
        return ChatNVIDIA(model=model, api_key=nvidia_key, timeout=60)

    print("ERROR: No LLM API key found in .env.")
    print("       Set OPENAI_API_KEY, GROQ_API_KEY, or NVIDIA_API_KEY and try again.")
    sys.exit(1)


# ==============================================================================
# SECTION 3: HELPERS
# ==============================================================================

MCP_SERVER_URL = "http://localhost:8000/mcp"
STEP_TIMEOUT_SECONDS = 60

def _log(message: str) -> None:
    print(message, flush=True)


def _print_step(n: int, label: str) -> None:
    _log(f"\n{'='*55}")
    _log(f"  STEP {n}: {label}")
    _log(f"{'='*55}")

def _print_result(messages) -> None:
    if hasattr(messages, "content") and getattr(messages, "content"):
        _log(f"  Agent: {messages.content}")
        return

    if isinstance(messages, dict) and "messages" in messages:
        for msg in messages["messages"]:
            if hasattr(msg, "content") and msg.content:
                _log(f"  Agent: {msg.content}")
                return

    _log(f"  Agent: {messages}")

# ==============================================================================
# SECTION 4: AGENT WORKFLOW
# ==============================================================================

async def _run_step(agent, step_num: int, label: str, message: str):
    _print_step(step_num, label)
    _log(f"  >> Sending prompt: {message}")
    _log(f"  >> Waiting for model response (timeout: {STEP_TIMEOUT_SECONDS}s)...")
    try:
        result = await asyncio.wait_for(
            agent.ainvoke(
                {"messages": [{"role": "user", "content": message}]}
            ),
            timeout=STEP_TIMEOUT_SECONDS,
        )
        _print_result(result)
    except asyncio.TimeoutError:
        _log(f"  ERROR: Step {step_num} timed out after {STEP_TIMEOUT_SECONDS} seconds.")
        _log("  Hint: the NVIDIA chat endpoint may be slow or unreachable.")
        _log("  Suggestion: verify NVIDIA_API_KEY, network access, or use GROQ_API_KEY instead.")
        raise
    except Exception as exc:
        _log(f"  ERROR: Step {step_num} failed: {type(exc).__name__}: {exc}")
        if "SocketTimeoutError" in repr(exc) or "ReadTimeout" in repr(exc):
            _log("  Hint: timeout occurred while reading from the model endpoint.")
            _log("  Suggestion: check network connectivity or use a different LLM provider.")
        traceback.print_exc(limit=3)
        raise


async def run_workflow():
    print("\nStarting Kasa Smart Home Agent Workflow")
    print(f"Server : {MCP_SERVER_URL}")

    llm = _build_llm()

    client = MultiServerMCPClient(
        {"kasa_home": {"transport": "streamable_http", "url": MCP_SERVER_URL}}
    )
    _log("  >> Fetching tools from MCP server...")
    tools = await client.get_tools()
    _log(f"  >> Retrieved {len(tools)} tool(s)")
    agent = create_react_agent(llm, tools)

    await _run_step(agent, 1, "List all smart home devices", "List all available smart home devices.")
    await _run_step(agent, 2, "Turn the Smart Plug ON", "Turn on the Smart Plug.")
    await _run_step(agent, 3, "Check the current status", "What is the current status of the Smart Plug?")
    await _run_step(agent, 4, "Turn the Smart Plug OFF", "Turn off the Smart Plug.")

    print(f"\n{'='*55}")
    print("  Workflow complete.")
    print(f"{'='*55}\n")

# ==============================================================================
# SECTION 5: ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(run_workflow())
    except Exception as exc:
        print("\n--- WORKFLOW FAILED ---")
        print(f"{type(exc).__name__}: {exc}")
        sys.exit(1)

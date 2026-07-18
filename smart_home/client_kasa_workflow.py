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
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ==============================================================================
# SECTION 2: LLM SELECTION
# Auto-selects provider based on which API key is present in .env.
# ==============================================================================

def _build_llm():
    groq_key = os.getenv("GROQ_API_KEY")
    nvidia_key = os.getenv("NVIDIA_API_KEY")

    if groq_key:
        from langchain_groq import ChatGroq
        print("LLM : ChatGroq — llama-3.1-8b-instant")
        return ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key)

    if nvidia_key:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        model = "nvidia/llama-3.1-nemotron-nano-8b-v1"
        print(f"LLM : ChatNVIDIA — {model}")
        return ChatNVIDIA(model=model, api_key=nvidia_key)

    print("ERROR: No LLM API key found in .env.")
    print("       Set GROQ_API_KEY or NVIDIA_API_KEY and try again.")
    sys.exit(1)


# ==============================================================================
# SECTION 3: HELPERS
# ==============================================================================

MCP_SERVER_URL = "http://localhost:8000/mcp"

def _print_step(n: int, label: str) -> None:
    print(f"\n{'='*55}")
    print(f"  STEP {n}: {label}")
    print(f"{'='*55}")

def _print_result(messages) -> None:
    for msg in messages["messages"]:
        if hasattr(msg, "content") and msg.content:
            print(f"  Agent: {msg.content}")

# ==============================================================================
# SECTION 4: AGENT WORKFLOW
# ==============================================================================

async def run_workflow():
    print("\nStarting Kasa Smart Home Agent Workflow")
    print(f"Server : {MCP_SERVER_URL}")

    llm = _build_llm()

    async with MultiServerMCPClient(
        {"kasa_home": {"transport": "streamable_http", "url": MCP_SERVER_URL}}
    ) as client:
        tools = await client.get_tools()
        agent = create_react_agent(llm, tools)

        _print_step(1, "List all smart home devices")
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "List all available smart home devices."}]}
        )
        _print_result(result)

        _print_step(2, "Turn the Smart Plug ON")
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Turn on the Smart Plug."}]}
        )
        _print_result(result)

        _print_step(3, "Check the current status")
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "What is the current status of the Smart Plug?"}]}
        )
        _print_result(result)

        _print_step(4, "Turn the Smart Plug OFF")
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Turn off the Smart Plug."}]}
        )
        _print_result(result)

    print(f"\n{'='*55}")
    print("  Workflow complete.")
    print(f"{'='*55}\n")

# ==============================================================================
# SECTION 5: ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    asyncio.run(run_workflow())

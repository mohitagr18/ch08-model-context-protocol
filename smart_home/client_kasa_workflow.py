# client_kasa_workflow.py
#
# Section 8.4 — Building an MCP server with a smart plug example
#
# This script is the CLIENT side of the Chapter 8 smart home example.
# It connects to the running KasaSmartHomeServer via streamable-http,
# wraps the MCP tools into a LangGraph ReAct agent, and runs a
# four-step demonstration workflow:
#
#   Step 1 — List available smart devices
#   Step 2 — Turn the plug on
#   Step 3 — Check its current status (no state change)
#   Step 4 — Turn the plug off
#
# Prerequisites:
#   - kasa_smart_home_server.py must be running in a separate terminal
#   - GROQ_API_KEY must be set in .env
#
# Run with:  python smart_home/client_kasa_workflow.py

# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# SECTION 2: ENVIRONMENT VALIDATION
# ==============================================================================
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("CRITICAL ERROR: GROQ_API_KEY is not set.")
    print("Add GROQ_API_KEY=<your_key> to your .env file and restart.")
    sys.exit(1)
os.environ["GROQ_API_KEY"] = groq_api_key

# The alias we expect the server to report — used only for readable log messages.
DEVICE_ALIAS = os.getenv("KASA_DEVICE_ALIAS", "Smart Plug")


# ==============================================================================
# SECTION 3: HELPER — PRINT AGENT RESPONSE
# ==============================================================================

def _print_step(step_label: str, response: dict) -> None:
    """Extract and print the agent's final message for a workflow step."""
    final_message = response["messages"][-1].content
    print(f"\n{'='*60}")
    print(f"  {step_label}")
    print(f"{'='*60}")
    print(final_message)


# ==============================================================================
# SECTION 4: MAIN WORKFLOW
# ==============================================================================

async def main() -> None:
    print("STATUS: Initializing client workflow...")

    # ------------------------------------------------------------------
    # Connect to the MCP server via MultiServerMCPClient.
    # The client discovers tools automatically — no manual wiring needed.
    # ------------------------------------------------------------------
    client = MultiServerMCPClient(
        {
            "kasa_home": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp",
            }
        }
    )

    print("STATUS: Fetching tools from MCP server...")
    tools = await client.get_tools()
    if not tools:
        print("ERROR: No tools retrieved. Is kasa_smart_home_server.py running?")
        sys.exit(1)

    print(f"STATUS: {len(tools)} tool(s) available:")
    for t in tools:
        print(f"  - {t.name}: {t.description}")

    # ------------------------------------------------------------------
    # Build the ReAct agent.
    # The agent receives the MCP tools and the LLM — nothing more.
    # It decides which tools to call and in what order.
    # ------------------------------------------------------------------
    print("\nSTATUS: Building ReAct agent (ChatGroq / llama-3.1-8b-instant)...")
    model = ChatGroq(model="llama-3.1-8b-instant")
    agent = create_react_agent(model=model, tools=tools)
    print("STATUS: Agent ready.\n")

    # ------------------------------------------------------------------
    # STEP 1: List all available devices
    # ------------------------------------------------------------------
    step1 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "List all the smart home devices you can control. Do not include IP addresses."}]}
    )
    _print_step("STEP 1 — List devices", step1)

    # ------------------------------------------------------------------
    # STEP 2: Turn the plug ON
    # ------------------------------------------------------------------
    step2 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": f"Turn on the smart plug called '{DEVICE_ALIAS}'."}]}
    )
    _print_step(f"STEP 2 — Turn ON '{DEVICE_ALIAS}'", step2)

    # ------------------------------------------------------------------
    # STEP 3: Check status (read-only — no state change)
    # ------------------------------------------------------------------
    step3 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": f"What is the current power status of '{DEVICE_ALIAS}'? Do not change its state."}]}
    )
    _print_step(f"STEP 3 — Status check for '{DEVICE_ALIAS}'", step3)

    # ------------------------------------------------------------------
    # STEP 4: Turn the plug OFF
    # ------------------------------------------------------------------
    step4 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": f"Turn off the smart plug called '{DEVICE_ALIAS}'."}]}
    )
    _print_step(f"STEP 4 — Turn OFF '{DEVICE_ALIAS}'", step4)

    print("\nSTATUS: Workflow complete.")


# ==============================================================================
# SECTION 5: SCRIPT ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    asyncio.run(main())

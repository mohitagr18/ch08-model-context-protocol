# mock_kasa_server.py
#
# A drop-in replacement for kasa_smart_home_server.py that simulates
# a TP-Link Kasa smart plug entirely in memory.
#
# Use this when you do not have a physical Kasa device available.
# The mock server exposes identical MCP tools with identical return shapes,
# so client_kasa_workflow.py runs without any changes.
#
# Run with:  python smart_home/mock_kasa_server.py
# Then run:  python smart_home/client_kasa_workflow.py  (in a second terminal)

# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
from mcp.server.fastmcp import FastMCP
import sys
from typing import Dict, List

# ==============================================================================
# SECTION 2: MOCK DEVICE STATE
# In the real server this state lives inside the SmartPlug object on the device.
# Here we keep it as a plain Python variable in memory.
# ==============================================================================
_mock_state = {
    "alias": "Smart Plug (mock)",
    "is_on": False,
    "host": "127.0.0.1",
}

# ==============================================================================
# SECTION 3: MCP SERVER SETUP
# ==============================================================================
mcp = FastMCP(
    name="MockKasaSmartHomeServer",
    instructions=(
        "You control a simulated smart plug (no real hardware required). "
        "Use list_smart_devices to see what is available. "
        "Use turn_device_on or turn_device_off to change its state. "
        "Use get_device_status to check current power state without changing it."
    ),
)

# ==============================================================================
# SECTION 4: TOOL DEFINITIONS
# Return shapes are identical to kasa_smart_home_server.py so the client
# works without modification.
# ==============================================================================

@mcp.tool()
def list_smart_devices() -> List[Dict]:
    """
    List the configured smart plug and its current power state.

    Returns:
        A list containing one dict with keys: alias, is_on (bool), host.
    """
    print(f"[MOCK] list_smart_devices called. State: {_mock_state}")
    return [dict(_mock_state)]


@mcp.tool()
def turn_device_on() -> Dict:
    """
    Turn the configured smart plug ON.

    Returns:
        A dict with keys: alias, is_on (bool), status.
    """
    _mock_state["is_on"] = True
    print(f"[MOCK] turn_device_on called. New state: {_mock_state}")
    return {"alias": _mock_state["alias"], "is_on": True, "status": "success"}


@mcp.tool()
def turn_device_off() -> Dict:
    """
    Turn the configured smart plug OFF.

    Returns:
        A dict with keys: alias, is_on (bool), status.
    """
    _mock_state["is_on"] = False
    print(f"[MOCK] turn_device_off called. New state: {_mock_state}")
    return {"alias": _mock_state["alias"], "is_on": False, "status": "success"}


@mcp.tool()
def get_device_status() -> Dict:
    """
    Return the current power state of the configured smart plug without changing it.

    Returns:
        A dict with keys: alias, is_on (bool), status.
    """
    print(f"[MOCK] get_device_status called. State: {_mock_state}")
    return {"alias": _mock_state["alias"], "is_on": _mock_state["is_on"], "status": "success"}


# ==============================================================================
# SECTION 5: SERVER ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    print("STATUS: Starting Mock Kasa Smart Home MCP Server...")
    print("STATUS: No physical device required — state is simulated in memory.")
    print("STATUS: Transport — streamable-http on http://localhost:8000/mcp")
    print("STATUS: Run client_kasa_workflow.py in a second terminal to test.")
    try:
        mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start mock server: {e}")
        sys.exit(1)

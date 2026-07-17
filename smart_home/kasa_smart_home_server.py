# kasa_smart_home_server.py
#
# Section 8.4 — Building an MCP server with a smart plug example
#
# This MCP server exposes four tools that allow a language model to control
# a single TP-Link Kasa smart plug over the local network.
#
# Key design decisions that enforce bounded execution (Section 8.2):
#   - The target device IP is read from the environment, not from the model
#   - The model can only interact with ONE pre-configured device
#   - All tool return values are typed dicts — FastMCP validates the schema
#   - Connection failures surface as structured error dicts, not exceptions
#
# Run with:  python smart_home/kasa_smart_home_server.py
# Default:   Listens on http://localhost:8000/mcp  (streamable-http transport)

# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
from mcp.server.fastmcp import FastMCP
from kasa import SmartPlug
import asyncio
import sys
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# SECTION 2: CONFIGURATION
# ==============================================================================
# The device alias is a human-readable label used in all tool responses.
KASA_DEVICE_ALIAS = os.getenv("KASA_DEVICE_ALIAS", "Smart Plug")

# The device IP is read exclusively from the environment.
# The model has no way to change or discover this value — bounded execution.
KASA_DEVICE_IP = os.getenv("KASA_DEVICE_IP")

if not KASA_DEVICE_IP:
    print("CRITICAL ERROR: KASA_DEVICE_IP is not set in the environment.")
    print("Add KASA_DEVICE_IP=<your_plug_ip> to your .env file and restart.")
    sys.exit(1)

# ==============================================================================
# SECTION 3: MCP SERVER SETUP
# ==============================================================================
mcp = FastMCP(
    name="KasaSmartHomeServer",
    instructions=(
        "You control a single smart plug. "
        "Use list_smart_devices to see what is available. "
        "Use turn_device_on or turn_device_off to change its state. "
        "Use get_device_status to check current power state without changing it."
    ),
)

# In-process cache for the SmartPlug object.
# Avoids recreating the connection on every tool call.
_plug_cache: Optional[SmartPlug] = None


async def _get_plug() -> Optional[SmartPlug]:
    """
    Return a connected SmartPlug instance, using the cache when possible.
    Invalidates the cache if the connection goes stale and retries once.
    """
    global _plug_cache

    if _plug_cache is not None:
        try:
            await _plug_cache.update()
            return _plug_cache
        except Exception:
            # Connection stale — fall through to re-create.
            _plug_cache = None

    try:
        plug = SmartPlug(KASA_DEVICE_IP)
        await plug.update()
        _plug_cache = plug
        return plug
    except Exception as e:
        print(f"ERROR: Could not connect to Kasa device at {KASA_DEVICE_IP}: {e}")
        return None


# ==============================================================================
# SECTION 4: TOOL DEFINITIONS
# ==============================================================================

@mcp.tool()
async def list_smart_devices() -> List[Dict]:
    """
    List the configured smart plug and its current power state.

    Returns:
        A list containing one dict per device with keys:
        alias, is_on (bool), host (IP address).
        Returns an empty list if the device is unreachable.
    """
    plug = await _get_plug()
    if plug:
        return [{"alias": plug.alias, "is_on": plug.is_on, "host": plug.host}]
    return []


@mcp.tool()
async def turn_device_on() -> Dict:
    """
    Turn the configured smart plug ON.

    Returns:
        A dict with keys: alias, is_on (bool), status ('success' or 'error').
        On failure, returns a dict with a single 'error' key.
    """
    plug = await _get_plug()
    if not plug:
        return {"error": f"Device '{KASA_DEVICE_ALIAS}' is not reachable."}
    try:
        await plug.turn_on()
        await plug.update()
        return {"alias": plug.alias, "is_on": plug.is_on, "status": "success"}
    except Exception as e:
        return {"error": f"Failed to turn on '{KASA_DEVICE_ALIAS}': {e}"}


@mcp.tool()
async def turn_device_off() -> Dict:
    """
    Turn the configured smart plug OFF.

    Returns:
        A dict with keys: alias, is_on (bool), status ('success' or 'error').
        On failure, returns a dict with a single 'error' key.
    """
    plug = await _get_plug()
    if not plug:
        return {"error": f"Device '{KASA_DEVICE_ALIAS}' is not reachable."}
    try:
        await plug.turn_off()
        await plug.update()
        return {"alias": plug.alias, "is_on": plug.is_on, "status": "success"}
    except Exception as e:
        return {"error": f"Failed to turn off '{KASA_DEVICE_ALIAS}': {e}"}


@mcp.tool()
async def get_device_status() -> Dict:
    """
    Return the current power state of the configured smart plug without changing it.

    Returns:
        A dict with keys: alias, is_on (bool), status ('success' or 'error').
        On failure, returns a dict with a single 'error' key.
    """
    plug = await _get_plug()
    if not plug:
        return {"error": f"Device '{KASA_DEVICE_ALIAS}' is not reachable."}
    try:
        await plug.update()
        return {"alias": plug.alias, "is_on": plug.is_on, "status": "success"}
    except Exception as e:
        return {"error": f"Failed to get status for '{KASA_DEVICE_ALIAS}': {e}"}


# ==============================================================================
# SECTION 5: SERVER ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    print("STATUS: Starting Kasa Smart Home MCP Server...")
    print(f"STATUS: Target device — '{KASA_DEVICE_ALIAS}' at {KASA_DEVICE_IP}")
    print("STATUS: Transport — streamable-http on http://localhost:8000/mcp")
    try:
        mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start server: {e}")
        sys.exit(1)

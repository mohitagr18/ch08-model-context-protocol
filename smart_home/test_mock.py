# test_mock.py
#
# Automated test runner for the mock Kasa server.
# Tests all four MCP tools directly (no LLM, no agent, no API key needed)
# so you can verify the server is wired correctly before adding the agent layer.
#
# REQUIRES: mock server must already be running in another terminal:
#   python smart_home/mock_kasa_server.py
#
# Run with:  python smart_home/test_mock.py

# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import sys

SERVER_URL = "http://localhost:8000/mcp"

# ==============================================================================
# SECTION 2: HELPERS
# ==============================================================================

def _pass(label: str, result) -> None:
    print(f"  \033[92m\u2713 PASS\033[0m  {label}")
    print(f"         result : {result}")

def _fail(label: str, reason: str) -> None:
    print(f"  \033[91m\u2717 FAIL\033[0m  {label}")
    print(f"         reason : {reason}")

async def _call(client, name: str, args: dict = {}):
    """Call a named MCP tool directly and return the result."""
    tools = await client.get_tools()
    tool_map = {t.name: t for t in tools}
    if name not in tool_map:
        raise ValueError(f"Tool '{name}' not found. Available: {list(tool_map.keys())}")
    return await tool_map[name].ainvoke(args)

# ==============================================================================
# SECTION 3: TEST SUITE
# ==============================================================================

async def run_tests():
    print(f"\n{'='*55}")
    print("  Chapter 8 — Mock Kasa Server Test Suite")
    print(f"{'='*55}")
    print(f"  Server : {SERVER_URL}")
    print(f"  Tests  : 7\n")

    passed = 0
    failed = 0

    async with MultiServerMCPClient(
        {"kasa_home": {"transport": "streamable_http", "url": SERVER_URL}}
    ) as client:

        # ------------------------------------------------------------------
        # TEST 1: Tool discovery — all 4 tools must be registered
        # ------------------------------------------------------------------
        print("[ TEST 1 ] Tool discovery")
        try:
            tools = await client.get_tools()
            names = {t.name for t in tools}
            expected = {"list_smart_devices", "turn_device_on", "turn_device_off", "get_device_status"}
            missing = expected - names
            if missing:
                _fail("All 4 tools registered", f"Missing: {missing}")
                failed += 1
            else:
                _pass("All 4 tools registered", sorted(names))
                passed += 1
        except Exception as e:
            _fail("Tool discovery", str(e))
            failed += 1

        # ------------------------------------------------------------------
        # TEST 2: list_smart_devices — returns a list with one device dict
        # ------------------------------------------------------------------
        print("\n[ TEST 2 ] list_smart_devices")
        try:
            result = await _call(client, "list_smart_devices")
            assert isinstance(result, list), "Expected list"
            assert len(result) == 1, f"Expected 1 device, got {len(result)}"
            assert "alias" in result[0], "Missing 'alias' key"
            assert "is_on" in result[0], "Missing 'is_on' key"
            _pass("Returns list with one device dict", result)
            passed += 1
        except (AssertionError, Exception) as e:
            _fail("list_smart_devices", str(e))
            failed += 1

        # ------------------------------------------------------------------
        # TEST 3: get_device_status — initial state must be OFF
        # ------------------------------------------------------------------
        print("\n[ TEST 3 ] get_device_status (initial state = OFF)")
        try:
            result = await _call(client, "get_device_status")
            assert result["is_on"] == False, f"Expected is_on=False, got {result['is_on']}"
            assert result["status"] == "success"
            _pass("Initial state is OFF", result)
            passed += 1
        except (AssertionError, Exception) as e:
            _fail("get_device_status (initial)", str(e))
            failed += 1

        # ------------------------------------------------------------------
        # TEST 4: turn_device_on — state must flip to ON
        # ------------------------------------------------------------------
        print("\n[ TEST 4 ] turn_device_on")
        try:
            result = await _call(client, "turn_device_on")
            assert result["is_on"] == True, f"Expected is_on=True, got {result['is_on']}"
            assert result["status"] == "success"
            _pass("Device turned ON, is_on=True", result)
            passed += 1
        except (AssertionError, Exception) as e:
            _fail("turn_device_on", str(e))
            failed += 1

        # ------------------------------------------------------------------
        # TEST 5: get_device_status — must confirm ON after turn_on
        # ------------------------------------------------------------------
        print("\n[ TEST 5 ] get_device_status (after turn_on)")
        try:
            result = await _call(client, "get_device_status")
            assert result["is_on"] == True, f"Expected is_on=True, got {result['is_on']}"
            _pass("Status confirmed ON (no state change)", result)
            passed += 1
        except (AssertionError, Exception) as e:
            _fail("get_device_status (after turn_on)", str(e))
            failed += 1

        # ------------------------------------------------------------------
        # TEST 6: turn_device_off — state must flip to OFF
        # ------------------------------------------------------------------
        print("\n[ TEST 6 ] turn_device_off")
        try:
            result = await _call(client, "turn_device_off")
            assert result["is_on"] == False, f"Expected is_on=False, got {result['is_on']}"
            assert result["status"] == "success"
            _pass("Device turned OFF, is_on=False", result)
            passed += 1
        except (AssertionError, Exception) as e:
            _fail("turn_device_off", str(e))
            failed += 1

        # ------------------------------------------------------------------
        # TEST 7: get_device_status — must confirm OFF after turn_off
        # ------------------------------------------------------------------
        print("\n[ TEST 7 ] get_device_status (after turn_off)")
        try:
            result = await _call(client, "get_device_status")
            assert result["is_on"] == False, f"Expected is_on=False, got {result['is_on']}"
            _pass("Status confirmed OFF (no state change)", result)
            passed += 1
        except (AssertionError, Exception) as e:
            _fail("get_device_status (after turn_off)", str(e))
            failed += 1

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------
    print(f"\n{'='*55}")
    status = "ALL TESTS PASSED" if failed == 0 else f"{failed} TEST(S) FAILED"
    color = "\033[92m" if failed == 0 else "\033[91m"
    print(f"  {color}{status}\033[0m  ({passed}/{passed + failed})")
    print(f"{'='*55}\n")

    if failed > 0:
        sys.exit(1)

# ==============================================================================
# SECTION 4: ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    asyncio.run(run_tests())

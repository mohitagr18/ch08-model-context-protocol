# external_tools_server.py
#
# Section 8.3 — Connecting agents to external systems safely
#
# Demonstrates how MCP enforces a safe boundary between the model
# and external APIs:
#   - API keys are loaded from the environment, never exposed to the model
#   - Tool arguments are type-validated by FastMCP before execution
#   - Response payloads are parsed and trimmed before being returned
#   - max_results is server-side bounded to prevent excessive API calls
#
# External APIs used (free tiers available):
#   - WeatherAPI.com  (WEATHER_API_KEY)
#   - NewsAPI.org     (NEWS_API_KEY)
#
# Run with:  mcp dev external_tools/external_tools_server.py

# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
from mcp.server.fastmcp import FastMCP
import httpx
import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# SECTION 2: CONFIGURATION
# ==============================================================================
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Hard cap on news results — the model cannot exceed this even if it tries.
MAX_RESULTS_CAP = 10

# ==============================================================================
# SECTION 3: MCP SERVER SETUP
# ==============================================================================
mcp = FastMCP(
    name="Chapter8ExternalToolsServer",
    instructions=(
        "You have access to two external data tools. "
        "Use fetch_weather to get current conditions for a city. "
        "Use fetch_top_headlines to search recent news on a topic."
    ),
)


# ==============================================================================
# SECTION 4: TOOL — WEATHER
# ==============================================================================

@mcp.tool()
async def fetch_weather(city: str) -> dict[str, Any]:
    """
    Fetch the current weather conditions for a given city.

    Args:
        city: The city name or 'City, Country' (e.g. 'London' or 'Paris, FR').

    Returns:
        A dict with keys: city, country, temp_c, temp_f, condition, humidity_pct, wind_kph.
        On error, returns a dict with a single 'error' key.
    """
    if not WEATHER_API_KEY:
        return {"error": "WEATHER_API_KEY is not configured on this server."}

    url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHER_API_KEY, "q": city, "aqi": "no"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Return only the fields the model needs — not the entire raw payload.
        return {
            "city": data["location"]["name"],
            "country": data["location"]["country"],
            "temp_c": data["current"]["temp_c"],
            "temp_f": data["current"]["temp_f"],
            "condition": data["current"]["condition"]["text"],
            "humidity_pct": data["current"]["humidity"],
            "wind_kph": data["current"]["wind_kph"],
        }
    except httpx.HTTPStatusError as e:
        return {"error": f"WeatherAPI returned HTTP {e.response.status_code} for city '{city}'."}
    except Exception as e:
        return {"error": f"Unexpected error fetching weather for '{city}': {e}"}


# ==============================================================================
# SECTION 5: TOOL — NEWS HEADLINES
# ==============================================================================

@mcp.tool()
async def fetch_top_headlines(topic: str, max_results: int = 5) -> dict[str, Any]:
    """
    Fetch recent top news headlines for a given topic.

    Args:
        topic:       The topic or keyword to search for (e.g. 'AI agents').
        max_results: How many headlines to return (1–10, default 5).
                     The server enforces a hard cap of 10.

    Returns:
        A dict with keys: topic, total_found, articles.
        Each article has: title, source, published_at, url.
        On error, returns a dict with a single 'error' key.
    """
    if not NEWS_API_KEY:
        return {"error": "NEWS_API_KEY is not configured on this server."}

    # Server-side cap — the model cannot trigger more than MAX_RESULTS_CAP calls.
    capped = min(max(1, max_results), MAX_RESULTS_CAP)

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "pageSize": capped,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        articles = [
            {
                "title": a["title"],
                "source": a["source"]["name"],
                "published_at": a["publishedAt"],
                "url": a["url"],
            }
            for a in data.get("articles", [])
        ]

        return {
            "topic": topic,
            "total_found": data.get("totalResults", 0),
            "articles": articles,
        }
    except httpx.HTTPStatusError as e:
        return {"error": f"NewsAPI returned HTTP {e.response.status_code} for topic '{topic}'."}
    except Exception as e:
        return {"error": f"Unexpected error fetching headlines for '{topic}': {e}"}


# ==============================================================================
# SECTION 6: SERVER ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    mcp.run()

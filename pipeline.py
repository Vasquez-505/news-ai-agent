"""
Morning pipeline: fetch all topics -> render HTML -> build voice script.
Called by the APScheduler at 5AM and by the /reload Telegram command.
"""

import logging
import asyncio
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import state
from dashboard.render import render
from llm.provider import get_llm
from utils.greetings import get_greeting

logger = logging.getLogger(__name__)

TOPIC_MODULES = [
    ("world_news",        "topics.world_news"),
    ("ai_productivity",   "topics.ai_productivity"),
    ("portugal_policy",   "topics.portugal_policy"),
    ("eu_policy",         "topics.eu_policy"),
    ("us_policy",         "topics.us_policy"),
    ("investment_markets","topics.markets_economy"),
    ("ai_tools_snapshot", "topics.ai_tools_snapshot"),
]

VOICE_SCRIPT_PROMPT = """You are Pedro's morning briefing voice assistant.
Today is {date}.

Based on the briefing data below, write a ~90-second spoken summary (about 200 words).

STRUCTURE:
1. Open with this exact greeting (use it word for word): "{greeting}"
2. Immediately follow with the 7-topic headline reel — one short sentence each, in this exact format:
   "World: [top global story in one sentence]"
   "Markets: [biggest market signal today]"
   "AI: [most important AI release or move]"
   "Portugal: [most relevant approved law or policy]"
   "Europe: [top EU decision]"
   "US: [top signed action or executive order]"
   "Tools: [notable AI tool change, or 'No significant changes today']"
3. Close with: "Your full dashboard is ready. What would you like to hear first?"

RULES:
- The 7 headline lines must follow the exact "Topic: sentence" format above
- Only cover what's in the briefing data — don't invent
- Tone: sharp, intelligent, slightly dry — Jarvis-style
- Total length: ~200 words

BRIEFING DATA:
{briefing_data}

Write the voice script now:"""


def _fetch_topic(module_name: str) -> dict:
    import importlib
    mod = importlib.import_module(module_name)
    return mod.fetch()


def _load_watchlist_file() -> list:
    """Load watchlist from data/watchlist.yaml at pipeline run time."""
    wl_path = Path("data/watchlist.yaml")
    if wl_path.exists():
        with open(wl_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("watchlist", [])
    return []


async def run_pipeline(output_dir: str = "output", watchlist: list = None) -> str:
    """
    Fetch all topics in parallel, render dashboard HTML, build voice script.
    Returns path to the rendered HTML file.
    """
    # Always read the latest watchlist from disk unless explicitly overridden
    if watchlist is None:
        watchlist = _load_watchlist_file()

    state.set_fetch_status("Fetching topics...")
    logger.info("Pipeline started at %s", datetime.now().strftime("%H:%M"))

    topics = {}
    errors = []

    # Fetch all topics concurrently using threads (topic fetchers are sync)
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(_fetch_topic, module): (topic_id, module)
            for topic_id, module in TOPIC_MODULES
        }
        for future in as_completed(futures):
            topic_id, module = futures[future]
            try:
                data = future.result()
                topics[data.get("id", topic_id)] = data
                logger.info("Fetched: %s", topic_id)
            except Exception as e:
                logger.error("Failed to fetch %s: %s", topic_id, e)
                errors.append(topic_id)
                topics[topic_id] = {
                    "id": topic_id,
                    "title": topic_id,
                    "content": f"[Data unavailable: {e}]",
                    "sources": [],
                }

    state.set_topics(topics)
    status_msg = f"Fetched {len(topics)} topics."
    if errors:
        status_msg += f" Errors: {', '.join(errors)}"
    state.set_fetch_status(status_msg)

    # Render HTML dashboard
    logger.info("Rendering dashboard...")
    try:
        html_path = render(topics, output_dir=output_dir, watchlist=watchlist)
        logger.info("Dashboard written to %s", html_path)
    except Exception as e:
        logger.error("Dashboard render failed: %s", e)
        html_path = ""

    # Build voice script with today's greeting and headline reel format
    logger.info("Generating voice script...")
    try:
        briefing_data = state.get_briefing_context()
        date_str = datetime.now().strftime("%B %d, %Y")
        greeting = get_greeting()
        prompt = VOICE_SCRIPT_PROMPT.format(
            date=date_str,
            greeting=greeting,
            briefing_data=briefing_data,
        )
        llm = get_llm()
        script = llm.generate(prompt)
        state.set_voice_script(script)
        logger.info("Voice script ready (%d chars)", len(script))
    except Exception as e:
        logger.error("Voice script generation failed: %s", e)
        state.set_voice_script(
            f"{get_greeting()} Today's briefing is ready but the spoken summary "
            f"couldn't be generated. Check the dashboard for the full briefing."
        )

    state.set_fetch_status(f"Ready. {status_msg}")
    return html_path

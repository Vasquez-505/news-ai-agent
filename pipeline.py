"""
Morning pipeline: fetch all topics -> render HTML -> build voice script.
Called by the APScheduler at 5AM and by the /reload Telegram command.
"""

import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import state
from dashboard.render import render
from llm.provider import get_llm

logger = logging.getLogger(__name__)

TOPIC_MODULES = [
    ("world_news",       "topics.world_news"),
    ("ai_productivity",  "topics.ai_productivity"),
    ("portugal_policy",  "topics.portugal_policy"),
    ("eu_policy",        "topics.eu_policy"),
    ("us_policy",        "topics.us_policy"),
    ("investment_markets","topics.markets_economy"),
    ("ai_tools_snapshot","topics.ai_tools_snapshot"),
]

VOICE_SCRIPT_PROMPT = """You are Pedro's morning briefing voice assistant.
Today is {date}.

Based on the briefing data below, write a ~90-second spoken summary (about 200 words).

RULES:
- Open with: "Good morning, sunshine. Here's your briefing for {date}."
- Cover only the 3-4 most important items across ALL topics
- One short sentence per item, flowing conversational prose (not bullet points)
- Mention the top market signal and one crypto move if notable
- Close with: "Your full dashboard is ready. Have a great day."
- Tone: warm, intelligent, slightly dry wit — like a well-read friend

BRIEFING DATA:
{briefing_data}

Write the voice script now:"""


def _fetch_topic(module_name: str) -> dict:
    import importlib
    mod = importlib.import_module(module_name)
    return mod.fetch()


async def run_pipeline(output_dir: str = "output", watchlist: list = None) -> str:
    """
    Fetch all topics in parallel, render dashboard HTML, build voice script.
    Returns path to the rendered HTML file.
    """
    state.set_fetch_status("Fetching topics...")
    logger.info("Pipeline started at %s", datetime.now().strftime("%H:%M"))

    topics = {}
    errors = []

    # Fetch all topics concurrently using threads (topic fetchers are sync)
    loop = asyncio.get_event_loop()
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
                # Store a placeholder so the template doesn't break
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

    # Build voice script
    logger.info("Generating voice script...")
    try:
        briefing_data = state.get_briefing_context()
        date_str = datetime.now().strftime("%B %d, %Y")
        prompt = VOICE_SCRIPT_PROMPT.format(
            date=date_str,
            briefing_data=briefing_data,
        )
        llm = get_llm()
        script = llm.generate(prompt)
        state.set_voice_script(script)
        logger.info("Voice script ready (%d chars)", len(script))
    except Exception as e:
        logger.error("Voice script generation failed: %s", e)
        state.set_voice_script(
            f"Good morning, sunshine. Today's briefing is ready. "
            f"There was an issue generating the spoken summary. "
            f"Check the dashboard for the full briefing."
        )

    state.set_fetch_status(f"Ready. {status_msg}")
    return html_path

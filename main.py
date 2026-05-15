"""
Entry point: starts the APScheduler (5AM pipeline) and the Telegram bot.
Designed to run as a single long-lived process on Render.
"""

import asyncio
import logging
import os

import yaml
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from bot import build_application
from pipeline import run_pipeline

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _briefing_json_url(dashboard_url: str) -> str:
    """Derive the briefing_data.json URL from DASHBOARD_URL."""
    from urllib.parse import urlparse
    parsed = urlparse(dashboard_url)
    path = parsed.path
    # Strip filename if present (e.g. /repo/briefing_2026-05-08.html → /repo/)
    if "." in path.split("/")[-1]:
        path = path.rsplit("/", 1)[0] + "/"
    elif not path.endswith("/"):
        path += "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}briefing_data.json"


async def _load_briefing_from_pages(dashboard_url: str) -> bool:
    """
    Download briefing_data.json from GitHub Pages and load into state.
    Returns True on success, False on any failure.
    """
    import aiohttp
    import json
    json_url = _briefing_json_url(dashboard_url)
    logger.info("Loading briefing data from %s", json_url)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(json_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    logger.error("briefing_data.json returned HTTP %d", resp.status)
                    return False
                data = await resp.json(content_type=None)

        topics = data.get("topics", {})
        voice_script = data.get("voice_script", "")
        if not topics:
            logger.error("briefing_data.json contained no topics")
            return False

        from state import set_topics, set_voice_script, set_fetch_status
        set_topics(topics)
        set_voice_script(voice_script)
        set_fetch_status(f"Loaded from GitHub Pages. Generated at {data.get('generated_at', '?')}")
        logger.info("Briefing loaded from GitHub Pages (%d topics)", len(topics))
        return True
    except Exception as e:
        logger.error("Failed to load briefing from GitHub Pages: %s", e)
        return False


async def _load_daily_briefing(dashboard_url: str, watchlist: list = None):
    """
    Load today's briefing into state so the GMS bot can answer questions.
    Called at startup and daily at the configured fetch time.
    The Telegram morning push is handled by GitHub Actions — not here.
    """
    logger.info("Loading daily briefing at %s", datetime.now().strftime("%H:%M"))

    loaded = False
    if dashboard_url:
        loaded = await _load_briefing_from_pages(dashboard_url)

    if not loaded:
        logger.warning("GitHub Pages load failed — running pipeline locally as fallback")
        try:
            await run_pipeline(output_dir="output", watchlist=watchlist or [])
            logger.info("Fallback pipeline complete")
        except Exception as e:
            logger.error("Fallback pipeline failed: %s", e)


async def main():
    config = _load_config()

    fetch_time = config.get("schedule", {}).get("fetch_time", "05:00")
    timezone   = config.get("schedule", {}).get("timezone", "Europe/Lisbon")
    hour, minute = map(int, fetch_time.split(":"))

    logger.info("Fetch scheduled for %s %s", fetch_time, timezone)

    watchlist = config.get("watchlist", [])
    dashboard_url = os.getenv("DASHBOARD_URL", "")

    # --- Telegram bot (non-blocking) ---
    app = build_application()

    # --- Scheduler: daily briefing refresh so GMS bot stays current ---
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(
        _load_daily_briefing,
        CronTrigger(hour=hour, minute=minute, timezone=timezone),
        args=[dashboard_url, watchlist or []],
        id="morning_fetch",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message", "callback_query"])
    logger.info("Telegram bot started")

    # Load today's briefing immediately so GMS works from the moment Render starts,
    # not just after the 5am scheduler fires.
    asyncio.create_task(_load_daily_briefing(dashboard_url, watchlist or []))

    # --- Health-check HTTP server (required by Render, used by UptimeRobot) ---
    async def health(request):
        return web.Response(text="OK")

    http_app = web.Application()
    http_app.router.add_get("/", health)
    http_app.router.add_get("/health", health)
    port = int(os.getenv("PORT", "10000"))
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health server listening on port %d", port)

    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown(wait=False)
        await runner.cleanup()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

"""
Entry point: starts the APScheduler (5AM pipeline) and the Telegram bot.
Designed to run as a single long-lived process on Render.
"""

import asyncio
import logging
import os
from datetime import datetime

import yaml
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


async def _scheduled_fetch(watchlist: list = None):
    """Called by APScheduler at the configured fetch time."""
    logger.info("Scheduled fetch triggered at %s", datetime.now().strftime("%H:%M"))
    try:
        html_path = await run_pipeline(output_dir="output", watchlist=watchlist or [])
        logger.info("Scheduled fetch complete. Dashboard: %s", html_path)
    except Exception as e:
        logger.error("Scheduled fetch failed: %s", e)


async def main():
    config = _load_config()

    fetch_time = config.get("schedule", {}).get("fetch_time", "05:00")
    timezone   = config.get("schedule", {}).get("timezone", "Europe/Lisbon")
    hour, minute = map(int, fetch_time.split(":"))

    logger.info("Fetch scheduled for %s %s", fetch_time, timezone)

    watchlist = config.get("watchlist", [])

    # --- Scheduler ---
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(
        lambda: asyncio.create_task(run_pipeline(output_dir="output", watchlist=watchlist)),
        CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="morning_fetch",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")

    # --- Telegram bot (non-blocking) ---
    app = build_application()
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message"])
    logger.info("Telegram bot started")

    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown(wait=False)
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

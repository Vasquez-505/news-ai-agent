"""
Entry point: starts the APScheduler (5AM pipeline) and the Telegram bot.
Designed to run as a single long-lived process on Render.
"""

import asyncio
import logging
import os
from datetime import datetime

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


async def _scheduled_fetch(bot, chat_id: int, dashboard_url: str, watchlist: list = None):
    """Called by APScheduler at the configured fetch time."""
    logger.info("Scheduled fetch triggered at %s", datetime.now().strftime("%H:%M"))
    try:
        await run_pipeline(output_dir="output", watchlist=watchlist or [])
        logger.info("Scheduled fetch complete")
    except Exception as e:
        logger.error("Scheduled fetch failed: %s", e)

    # Push morning newspaper link to Telegram regardless of pipeline errors
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    if dashboard_url:
        text = (
            f"📰 Your briefing for {date_str} is ready.\n\n"
            f"{dashboard_url}"
        )
    else:
        text = f"📰 Your briefing for {date_str} is ready."
    try:
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        inline_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🤖 Talk to TARS", callback_data="talk_to_tars"),
            InlineKeyboardButton("📰 Start Briefing", callback_data="start_briefing"),
        ]])
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=inline_kb)
        logger.info("Morning push sent to chat %d", chat_id)
    except Exception as e:
        logger.error("Failed to send morning push: %s", e)


async def main():
    config = _load_config()

    fetch_time = config.get("schedule", {}).get("fetch_time", "05:00")
    timezone   = config.get("schedule", {}).get("timezone", "Europe/Lisbon")
    hour, minute = map(int, fetch_time.split(":"))

    logger.info("Fetch scheduled for %s %s", fetch_time, timezone)

    watchlist = config.get("watchlist", [])
    dashboard_url = os.getenv("DASHBOARD_URL", "")
    chat_id = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

    # --- Telegram bot (non-blocking) ---
    app = build_application()

    # --- Scheduler ---
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(
        lambda: asyncio.create_task(
            _scheduled_fetch(app.bot, chat_id, dashboard_url, watchlist)
        ),
        CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="morning_fetch",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message"])
    logger.info("Telegram bot started")

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

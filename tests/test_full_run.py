"""
Full end-to-end pipeline test — fetches all 7 topics, renders the newspaper,
and sends the Telegram push exactly as the 5am scheduler does.
Uses real API calls (Gemini + yfinance + FRED + CoinGecko).
Run: python tests/test_full_run.py
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

from pipeline import run_pipeline

load_dotenv()


async def main():
    token         = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id       = os.getenv("TELEGRAM_CHAT_ID")
    dashboard_url = os.getenv("DASHBOARD_URL", "")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        return

    print("Running full pipeline (this takes ~2-3 minutes)...")
    html_path = await run_pipeline(output_dir="output")
    abs_path = Path(html_path).resolve()
    print(f"Pipeline done: {abs_path}")

    # Send the same push the 5am scheduler sends
    bot = Bot(token=token)
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    text = (
        f"📰 [FULL TEST] Your briefing for {date_str} is ready.\n\n"
        f"{dashboard_url}"
    )
    inline_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🤖 Talk to GMS", callback_data="talk_to_tars"),
        InlineKeyboardButton("📰 Start Briefing", callback_data="start_briefing"),
    ]])
    await bot.send_message(chat_id=int(chat_id), text=text, reply_markup=inline_kb)
    print(f"Telegram push sent to chat {chat_id}")


if __name__ == "__main__":
    asyncio.run(main())

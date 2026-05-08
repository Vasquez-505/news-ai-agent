"""
Test the Telegram morning push without running the full pipeline.
Sends the exact same message the 5am scheduler sends.
Run: python tests/test_telegram_push.py
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()


async def main():
    token      = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id    = os.getenv("TELEGRAM_CHAT_ID")
    dashboard_url = os.getenv("DASHBOARD_URL", "")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        return

    bot = Bot(token=token)
    date_str = datetime.now().strftime("%A, %B %d, %Y")

    text = (
        f"📰 [TEST PUSH] Your briefing for {date_str} is ready.\n\n"
        f"{dashboard_url}"
    )
    inline_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🤖 Talk to GMS", callback_data="talk_to_tars"),
        InlineKeyboardButton("📰 Start Briefing", callback_data="start_briefing"),
    ]])

    await bot.send_message(chat_id=int(chat_id), text=text, reply_markup=inline_kb)
    print(f"Push sent to chat {chat_id}")
    print(f"Dashboard URL: {dashboard_url or '(not set)'}")


if __name__ == "__main__":
    asyncio.run(main())

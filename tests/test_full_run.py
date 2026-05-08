"""
Full end-to-end pipeline test covering both stages of the new architecture:

  Stage 1 (GitHub Actions role):
    - Runs the full pipeline (all 7 topics via Tavily + Gemini 2.5 Flash,
      markets via yfinance/FRED/CoinGecko, voice script via Gemma)
    - Verifies briefing_2026-XX-XX.html is written
    - Verifies briefing_data.json is written alongside it

  Stage 2 (Render role):
    - Loads briefing_data.json from the local output/ directory
      (in production this comes from GitHub Pages, same file)
    - Populates state (topics + voice_script) exactly as Render does at 5am
    - Verifies GMS context is non-empty
    - Sends the Telegram push with inline buttons

Run: python -m tests.test_full_run
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

from pipeline import run_pipeline
import state

load_dotenv()


async def main():
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    dashboard_url = os.getenv("DASHBOARD_URL", "")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        return

    # ── Stage 1: Pipeline (GitHub Actions role) ────────────────────────────────
    print("=" * 60)
    print("STAGE 1: Running pipeline (all 7 topics + voice script)...")
    print("This takes ~2-3 minutes.")
    print("=" * 60)

    html_path = await run_pipeline(output_dir="output")
    abs_html  = Path(html_path).resolve()
    json_path = abs_html.parent / "briefing_data.json"

    print(f"\n[OK] HTML:  {abs_html}")
    if json_path.exists():
        size = json_path.stat().st_size
        print(f"[OK] JSON:  {json_path}  ({size:,} bytes)")
    else:
        print(f"[FAIL] JSON NOT FOUND at {json_path} — check pipeline logs above")
        return

    # ── Stage 2: Render-side load (simulated locally) ─────────────────────────
    print()
    print("=" * 60)
    print("STAGE 2: Loading briefing_data.json into state (Render role)...")
    print("=" * 60)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    topics       = data.get("topics", {})
    voice_script = data.get("voice_script", "")
    generated_at = data.get("generated_at", "?")

    state.set_topics(topics)
    state.set_voice_script(voice_script)
    state.set_fetch_status(f"Loaded from local JSON. Generated at {generated_at}")

    briefing_ctx = state.get_briefing_context()
    print(f"[OK] Topics loaded:       {len(topics)}")
    print(f"[OK] Voice script length: {len(voice_script)} chars")
    print(f"[OK] GMS context length:  {len(briefing_ctx)} chars")
    print(f"[OK] Generated at:        {generated_at}")

    if not briefing_ctx:
        print("[FAIL] GMS context is empty — something went wrong loading state")
        return

    print()
    print("GMS context preview (first 400 chars):")
    print("-" * 40)
    print(briefing_ctx[:400].encode("ascii", errors="replace").decode("ascii"))
    print("-" * 40)

    # ── Telegram push ──────────────────────────────────────────────────────────
    print()
    print("Sending Telegram push...")
    bot      = Bot(token=token)
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
    print(f"[OK] Telegram push sent to chat {chat_id}")
    print()
    print("All checks passed. New architecture end-to-end: OK")


if __name__ == "__main__":
    asyncio.run(main())

"""
Telegram bot: morning briefing delivery + open conversation.

Flow:
  1. Pedro taps /start or /briefing -> sends today's voice summary + HTML link
  2. Any follow-up message -> open AI conversation with briefing as context
  3. /status  -> show fetch status (was today's data ready?)
  4. /reload  -> force re-fetch of all topics right now
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from llm.provider import get_llm
from tts.voice import generate_audio
import state  # shared state module (topics cache, fetch status)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID    = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "")  # GitHub Pages URL

SYSTEM_PROMPT = """You are Pedro's personal morning intelligence assistant — sharp, concise, well-read.
You have already briefed Pedro on today's topics. Now hold an open conversation.

Guidelines:
- Respond in the same language Pedro writes in (Portuguese or English).
- Keep responses tight: 2-4 sentences unless Pedro asks for depth.
- Ground claims in today's briefing context when relevant.
- Never make up statistics or events. If unsure, say so.
- Tone: intelligent friend, not corporate assistant.
"""


def _auth(update: Update) -> bool:
    return update.effective_chat.id == CHAT_ID


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _auth(update):
        return
    await update.message.reply_text(
        "Good morning, sunshine. Use /briefing to get today's summary, "
        "or just type any question."
    )


async def cmd_briefing(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Send today's voice summary and dashboard link."""
    if not _auth(update):
        return

    await update.message.chat.send_action(constants.ChatAction.RECORD_VOICE)

    summary_text = state.get_voice_script()
    if not summary_text:
        await update.message.reply_text(
            "Today's briefing isn't ready yet — data is still being fetched. "
            "Try again in a minute or use /reload to fetch now."
        )
        return

    audio_path = Path("output") / "briefing_today.mp3"
    audio_path.parent.mkdir(exist_ok=True)

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, generate_audio, summary_text, str(audio_path))
        with open(audio_path, "rb") as f:
            await update.message.reply_voice(voice=f, caption="Good morning, sunshine.")
    except Exception as e:
        logger.error("TTS failed: %s", e)
        await update.message.reply_text(
            f"Voice generation failed. Here's the text summary:\n\n{summary_text[:1500]}"
        )

    if DASHBOARD_URL:
        await update.message.reply_text(
            f"Full dashboard: {DASHBOARD_URL}",
            disable_web_page_preview=False,
        )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _auth(update):
        return
    status = state.get_fetch_status()
    await update.message.reply_text(status)


async def cmd_reload(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Force an immediate re-fetch of all topics."""
    if not _auth(update):
        return
    await update.message.reply_text("Starting fetch... I'll let you know when it's done.")
    # Import here to avoid circular import with main.py
    from pipeline import run_pipeline
    try:
        await run_pipeline()
        await update.message.reply_text("Fetch complete. Use /briefing to get your summary.")
    except Exception as e:
        logger.error("Pipeline error: %s", e)
        await update.message.reply_text(f"Fetch failed: {e}")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any free-text message as an open conversation turn."""
    if not _auth(update):
        return

    user_text = update.message.text or ""
    if not user_text.strip():
        return

    await update.message.chat.send_action(constants.ChatAction.TYPING)

    # Build conversation history from context
    history = ctx.user_data.get("history", [])

    # Inject today's briefing as initial context on first message
    if not history:
        briefing_ctx = state.get_briefing_context()
        if briefing_ctx:
            history.append({"role": "user", "parts": [f"[Today's briefing]\n{briefing_ctx}"]})
            history.append({"role": "model", "parts": ["Understood. I have the full briefing context. What would you like to discuss?"]})

    history.append({"role": "user", "parts": [user_text]})

    llm = get_llm()
    try:
        # Build a single prompt from history for providers that don't support multi-turn
        prompt_parts = [SYSTEM_PROMPT, ""]
        for turn in history:
            role = "Pedro" if turn["role"] == "user" else "Assistant"
            prompt_parts.append(f"{role}: {' '.join(turn['parts'])}")
        prompt_parts.append("Assistant:")
        full_prompt = "\n".join(prompt_parts)

        reply = llm.generate(full_prompt)
    except Exception as e:
        logger.error("LLM error: %s", e)
        reply = "Sorry, I had trouble generating a response. Try again."

    history.append({"role": "model", "parts": [reply]})

    # Keep only last 20 turns to avoid unbounded growth
    ctx.user_data["history"] = history[-20:]

    await update.message.reply_text(reply)


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("briefing", cmd_briefing))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("reload",   cmd_reload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


if __name__ == "__main__":
    app = build_application()
    logger.info("Bot started (polling)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

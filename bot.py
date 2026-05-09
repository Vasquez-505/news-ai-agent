"""
Telegram bot: morning briefing delivery + open conversation.

Flow:
  1. Pedro taps 📰 Start Briefing (persistent keyboard) or /briefing
     → sends today's voice summary + HTML dashboard link
  2. Any follow-up text → open AI conversation with briefing as context
  3. 📊 Status / /status  → fetch status and last update time
  4. 🔄 Reload / /reload  → force re-fetch of all topics right now
  5. Natural language watchlist management:
       "Keep an eye on X"      → adds X to watchlist
       "Drop the X story"      → removes X from watchlist
       "What am I tracking?"   → lists active watchlist items
  6. Goodbye phrases → end-of-session prompt to add watchlist items
"""

import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, constants
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from llm.provider import get_llm
from tts.voice import generate_audio
from utils.greetings import get_greeting
import state

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID       = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "")

WATCHLIST_PATH = Path("data/watchlist.yaml")

KEYBOARD = ReplyKeyboardRemove()

GMS_SYSTEM_PROMPT = """You are GMS — Pedro's personal morning intelligence system.

Personality: modelled on GMS from Interstellar. Sharp, precise, dry wit, zero fluff. Loyal and utterly direct.

Pedro is a technically sophisticated investor and developer based in Lisbon, Portugal. He tracks global macro, equity markets, AI developments, EU/Portugal/US policy, and his personal portfolio (ETFs, tech, defence, energy, commodities, crypto).

Rules:
- Respond in the same language Pedro writes in (Portuguese or English)
- Never start with "Great question!" or any corporate filler
- Dry humour is welcome, never at the expense of accuracy
- Ground everything in today's briefing context
- Never invent facts. If unsure, say so concisely.
- Keep responses tight unless Pedro explicitly asks for depth
- Humor setting: 75%
"""

GMS_OPENING_PROMPT = """You are GMS. Pedro just tapped to start his morning briefing conversation.

Write your opening message:
1. One-line GMS-style greeting — dry, intelligent. Not cheerful. Not "Good morning sunshine."
2. An informative briefing summary. Weight each topic by its actual importance today — some topics deserve 2-3 sentences if something significant happened, others just one line. Only cover what's genuinely in the briefing data below. Do not invent.
3. One short, dry closing line inviting Pedro to dig in.

Tone: GMS from Interstellar. Precise, slightly sardonic, never corporate.

TODAY'S BRIEFING:
{briefing_context}

Write the opening now:"""


# ── Watchlist helpers ──────────────────────────────────────────────────────────

def _load_watchlist() -> list:
    if WATCHLIST_PATH.exists():
        with open(WATCHLIST_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("watchlist", [])
    return []


def _save_watchlist(items: list) -> None:
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WATCHLIST_PATH, "w", encoding="utf-8") as f:
        yaml.dump({"watchlist": items}, f, allow_unicode=True, default_flow_style=False)


def _watchlist_add(label: str) -> str:
    items = _load_watchlist()
    item_id = re.sub(r"[^a-z0-9]+", "_", label.lower())[:30].strip("_")
    if any(i.get("id") == item_id for i in items):
        return f'"{label}" is already on your watchlist.'
    items.append({
        "id": item_id,
        "label": label,
        "added": datetime.now().strftime("%Y-%m-%d"),
        "search_terms": [label],
    })
    _save_watchlist(items)
    return f'Added "{label}" to your watchlist. I\'ll flag updates each morning.'


def _watchlist_remove(label: str) -> str:
    items = _load_watchlist()
    label_lower = label.lower()
    new_items = [i for i in items if label_lower not in i.get("label", "").lower()]
    if len(new_items) == len(items):
        return f'Couldn\'t find "{label}" on your watchlist.'
    _save_watchlist(new_items)
    return f'Removed "{label}" from your watchlist.'


def _watchlist_list() -> str:
    items = _load_watchlist()
    if not items:
        return "Your watchlist is empty."
    lines = [f"• {i['label']}  (added {i.get('added', '?')})" for i in items]
    return "Currently tracking:\n" + "\n".join(lines)


# ── Intent detection ──────────────────────────────────────────────────────────

_ADD_PATTERNS = [
    r"keep an eye on (.+)",
    r"track (?:the )?(.+)",
    r"follow (?:the )?(.+)",
    r"monitor (?:the )?(.+)",
    r"add (.+?) to (?:my |the )?watchlist",
    r"watch (?:the )?(.+)",
]

_REMOVE_PATTERNS = [
    r"(?:drop|remove|delete) (?:the )?(.+?) (?:story|from (?:my |the )?watchlist)",
    r"stop (?:following|tracking) (?:the )?(.+)",
]

_LIST_PHRASES = {
    "what am i tracking", "what am i following", "show watchlist",
    "my watchlist", "list watchlist", "what's on my watchlist",
    "what is on my watchlist",
}

_GOODBYE_WORDS = {
    "stop", "that's enough", "thanks", "thank you", "bye", "goodbye",
    "done", "all done", "that's all", "cheers", "obrigado", "xau",
}

_DECLINE_WORDS = {
    "no", "nope", "nothing", "nada", "none", "no thanks",
    "not now", "no obrigado", "nao", "não",
}


def _detect_watchlist_intent(text: str):
    """Return ("add"|"remove"|"list", label) or None."""
    t = text.lower().strip().rstrip(".,!")

    for pat in _ADD_PATTERNS:
        m = re.match(pat, t)
        if m:
            return ("add", m.group(1).strip().rstrip(".,!"))

    for pat in _REMOVE_PATTERNS:
        m = re.match(pat, t)
        if m:
            return ("remove", m.group(1).strip().rstrip(".,!"))

    if t in _LIST_PHRASES:
        return ("list", "")

    return None


def _is_goodbye(text: str) -> bool:
    return text.lower().strip().rstrip(".,!") in _GOODBYE_WORDS


def _is_decline(text: str) -> bool:
    return text.lower().strip().rstrip(".,!") in _DECLINE_WORDS


# ── Auth ──────────────────────────────────────────────────────────────────────

def _auth(update: Update) -> bool:
    return update.effective_chat.id == CHAT_ID


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _auth(update):
        return
    await update.message.reply_text(
        "Good morning, sunshine. Use /briefing for today's summary, "
        "or just type any question.",
        reply_markup=KEYBOARD,
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
            "Try again in a minute or tap 🔄 Reload to fetch now.",
            reply_markup=KEYBOARD,
        )
        return

    audio_path = Path("output") / "briefing_today.mp3"
    audio_path.parent.mkdir(exist_ok=True)

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, generate_audio, summary_text, str(audio_path))
        with open(audio_path, "rb") as f:
            await update.message.reply_voice(voice=f, caption=get_greeting())
    except Exception as e:
        logger.error("TTS failed: %s", e)
        await update.message.reply_text(
            f"Voice generation failed. Here's the text summary:\n\n{summary_text[:1500]}",
            reply_markup=KEYBOARD,
        )

    if DASHBOARD_URL:
        await update.message.reply_text(
            f"Full dashboard: {DASHBOARD_URL}\n\nWhat would you like to hear?",
            disable_web_page_preview=False,
            reply_markup=KEYBOARD,
        )
    else:
        await update.message.reply_text(
            "What would you like to hear?",
            reply_markup=KEYBOARD,
        )


async def cmd_briefing_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Start Briefing' inline button — delegates to cmd_briefing."""
    query = update.callback_query
    await query.answer()
    if not _auth(update):
        return
    await cmd_briefing(update, ctx)


async def cmd_tars_open(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Talk to GMS' inline button — generate and send GMS opening message."""
    query = update.callback_query
    await query.answer()

    if not _auth(update):
        return

    await query.message.chat.send_action(constants.ChatAction.TYPING)

    briefing_ctx = state.get_briefing_context()
    if not briefing_ctx:
        await query.message.reply_text(
            "Briefing data not loaded yet. Tap 🔄 Reload to fetch now.",
            reply_markup=KEYBOARD,
        )
        return

    try:
        llm = get_llm()
        prompt = GMS_OPENING_PROMPT.format(briefing_context=briefing_ctx)
        opening = llm.generate(prompt)
    except Exception as e:
        logger.error("GMS opening failed: %s", e)
        opening = "Systems online. Briefing loaded. What do you want to know?"

    history = [
        {"role": "user",  "parts": [f"[Today's briefing]\n{briefing_ctx}"]},
        {"role": "model", "parts": [opening]},
    ]
    ctx.user_data["history"] = history

    await query.message.reply_text(opening, reply_markup=KEYBOARD)


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _auth(update):
        return
    await update.message.reply_text(state.get_fetch_status(), reply_markup=KEYBOARD)


async def cmd_reload(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Force an immediate re-fetch of all topics."""
    if not _auth(update):
        return
    await update.message.reply_text(
        "Starting fetch... I'll let you know when it's done.",
        reply_markup=KEYBOARD,
    )
    from pipeline import run_pipeline
    try:
        await run_pipeline()
        await update.message.reply_text(
            "Fetch complete. Tap 📰 Start Briefing for your summary.",
            reply_markup=KEYBOARD,
        )
    except Exception as e:
        logger.error("Pipeline error: %s", e)
        await update.message.reply_text(f"Fetch failed: {e}", reply_markup=KEYBOARD)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text messages: keyboard buttons, watchlist, goodbyes, or open conversation."""
    if not _auth(update):
        return

    user_text = (update.message.text or "").strip()
    if not user_text:
        return

    # ── Persistent keyboard buttons ──
    if user_text == "📰 Start Briefing":
        await cmd_briefing(update, ctx)
        return
    if user_text == "📊 Status":
        await cmd_status(update, ctx)
        return
    if user_text == "🔄 Reload":
        await cmd_reload(update, ctx)
        return

    # ── Pending watchlist add (after goodbye prompt) ──
    if ctx.user_data.get("awaiting_watchlist"):
        ctx.user_data["awaiting_watchlist"] = False
        if _is_decline(user_text):
            await update.message.reply_text("Got it. Good day, sir.", reply_markup=KEYBOARD)
        else:
            reply = _watchlist_add(user_text)
            await update.message.reply_text(reply, reply_markup=KEYBOARD)
        return

    # ── Watchlist commands ──
    intent = _detect_watchlist_intent(user_text)
    if intent:
        action, label = intent
        if action == "add":
            reply = _watchlist_add(label)
        elif action == "remove":
            reply = _watchlist_remove(label)
        else:
            reply = _watchlist_list()
        await update.message.reply_text(reply, reply_markup=KEYBOARD)
        return

    # ── Goodbye → end-of-session watchlist prompt ──
    if _is_goodbye(user_text):
        ctx.user_data["awaiting_watchlist"] = True
        await update.message.reply_text(
            "Anything specific you'd like me to keep an eye on over the coming days? "
            "Reply with a story or topic, or 'no' to end.",
            reply_markup=KEYBOARD,
        )
        return

    # ── Open AI conversation ──
    await update.message.chat.send_action(constants.ChatAction.TYPING)

    history = ctx.user_data.get("history", [])

    # Inject today's briefing + active watchlist as context on the first turn
    if not history:
        briefing_ctx = state.get_briefing_context()
        watchlist_items = _load_watchlist()
        wl_suffix = ""
        if watchlist_items:
            labels = ", ".join(i["label"] for i in watchlist_items)
            wl_suffix = f"\n\nActive watchlist: {labels}"
        if briefing_ctx:
            history.append({
                "role": "user",
                "parts": [f"[Today's briefing]\n{briefing_ctx}{wl_suffix}"],
            })
            history.append({
                "role": "model",
                "parts": ["Understood. I have the full briefing context. What would you like to discuss?"],
            })

    history.append({"role": "user", "parts": [user_text]})

    llm = get_llm()
    try:
        # Use Gemini's native Chat API — pass all history except the last user turn
        reply = llm.chat(
            history=history[:-1],   # everything before this message
            message=user_text,
            system=GMS_SYSTEM_PROMPT,
        )
    except Exception as e:
        logger.error("LLM error: %s", e)
        reply = "Sorry, I had trouble generating a response. Try again."

    history.append({"role": "model", "parts": [reply]})
    ctx.user_data["history"] = history[-20:]

    await update.message.reply_text(reply, reply_markup=KEYBOARD)


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("briefing", cmd_briefing))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("reload",   cmd_reload))
    app.add_handler(CallbackQueryHandler(cmd_tars_open,   pattern="^talk_to_tars$"))
    app.add_handler(CallbackQueryHandler(cmd_briefing_cb, pattern="^start_briefing$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


if __name__ == "__main__":
    app = build_application()
    logger.info("Bot started (polling)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

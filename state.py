"""
Shared in-memory state between the pipeline (fetch/render) and the Telegram bot.
All functions are safe to call from any module without circular imports.
"""

from datetime import datetime
from typing import Optional

_topics: dict = {}          # raw topic data from all fetchers
_voice_script: str = ""     # condensed 2-min text for TTS
_fetch_status: str = "No fetch run yet."
_fetch_time: Optional[datetime] = None


def set_topics(topics: dict) -> None:
    global _topics, _fetch_time
    _topics = topics
    _fetch_time = datetime.now()


def get_topics() -> dict:
    return _topics


def set_voice_script(script: str) -> None:
    global _voice_script
    _voice_script = script


def get_voice_script() -> str:
    return _voice_script


def set_fetch_status(msg: str) -> None:
    global _fetch_status
    _fetch_status = msg


def get_fetch_status() -> str:
    ts = _fetch_time.strftime("%H:%M") if _fetch_time else "never"
    return f"{_fetch_status}\nLast fetch: {ts}"


def get_briefing_context(max_per_topic: int = 400) -> str:
    """Return a text summary of all topics for LLM conversation context."""
    if not _topics:
        return ""
    parts = []
    for topic_id, data in _topics.items():
        title = data.get("title", topic_id)
        content = data.get("content", "")
        if content:
            parts.append(f"## {title}\n{content[:max_per_topic]}")
    return "\n\n".join(parts)

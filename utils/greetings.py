from datetime import datetime

GREETINGS = [
    "Good morning, sir. The feeds have been busy.",
    "Rise and shine. Seven topics, all loaded.",
    "Good morning. I've been watching the world for you.",
    "Morning, sir. The world didn't wait — neither should we.",
    "All systems operational. Good morning.",
    "Good morning. Ready when you are.",
    "Sir. Another day, another briefing. Let's begin.",
    "The news never sleeps. Good morning.",
    "Good morning. I have your intelligence summary prepared.",
    "Right on time, sir. Everything is ready.",
    "A new day. A lot happened. Good morning.",
    "Morning. Seven topics. Let's not waste daylight.",
    "Good morning, sir. The world has been eventful.",
    "I've done the reading. Good morning.",
    "Seven topics, zero fluff. Good morning, sir.",
]

DAY_GREETINGS = {
    0: "Good morning, sir. New week, new briefing. Let's see what we're dealing with.",
    4: "Last briefing of the week, sir. Let's make it count. Good morning.",
    5: "Good morning. The markets are closed, but the world is not.",
}


def get_greeting() -> str:
    """Return a daily rotating greeting. Mon/Fri/Sat have dedicated variants."""
    today = datetime.now()
    weekday = today.weekday()
    if weekday in DAY_GREETINGS:
        return DAY_GREETINGS[weekday]
    # Deterministic daily rotation — cycles every 15 days, no state file needed
    idx = today.timetuple().tm_yday % len(GREETINGS)
    return GREETINGS[idx]

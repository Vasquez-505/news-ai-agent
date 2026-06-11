# Good Morning Sunshine: Daily Intelligence Briefing Agent

> *"The world generates a lot of noise. This is the signal."*

A fully automated personal intelligence system that fetches, analyses, and delivers a daily morning briefing across 7 curated topics, deployed on a zero-cost stack, delivered via Telegram, and readable as a newspaper-style HTML dashboard.

---

## What it does

Every morning at 5:00 AM Lisbon time, before you wake up, the system:

1. Fetches and analyses 7 topics using Gemini 2.5 Flash with native Google Search grounding
2. Renders a newspaper dashboard deployed to GitHub Pages, readable anywhere
3. Pushes a Telegram notification with the dashboard link and a one-tap context button
4. Generates a voice briefing (~90 seconds) ready to play on demand via `/briefing`

---

## Morning flow

```
01:00 UTC ── GitHub Actions runs pipeline
             ├── 7 topics fetched with live Google Search grounding
             ├── HTML newspaper rendered and deployed to GitHub Pages
             └── briefing_data.json saved alongside HTML

05:00 Lisbon ── Render bot wakes up
                ├── Downloads briefing_data.json from GitHub Pages
                └── Pushes Telegram notification:

                    "📰 Your briefing for Monday, May 11 is ready."
                    https://vasquez-505.github.io/news-ai-agent/
                    [📋 Copy briefing context]

You wake up ── Options:
  A) Tap the link         → read the full newspaper in your browser
  B) Tap Copy context     → bot sends a ready-to-paste LLM prompt
                            (GMS persona + Pedro profile + full briefing)
                            long-press → copy → paste into any LLM
  C) Type anything to bot → open conversation with GMS
  D) /briefing            → 90-second voice note plays
```

---

## The 7 topics

| # | Topic | Coverage |
|---|-------|----------|
| 1 | World News | Top 3-5 global stories, what happened and why it matters |
| 2 | Markets & Economy | Live macro snapshot (S&P, Gold, BTC, EUR/USD, VIX) plus sector alerts |
| 3 | AI & Productivity | Shipped AI products only, no announcements, no speculation |
| 4 | Portugal Policy | Enacted laws, old rule vs new rule, exact thresholds, practical impact |
| 5 | EU Policy | Formally adopted regulations, compliance deadlines, Portugal impact flagged |
| 6 | US Policy | Signed executive orders and legislation, balanced, factual, before/after |
| 7 | AI Tools Snapshot | Daily table comparing Pedro's current tools vs best-in-class alternatives |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│             GITHUB ACTIONS (01:00 UTC daily)            │
│  morning_fetch.yml                                      │
│  ├── run_pipeline() → 7 topics via Gemini 2.5 Flash     │
│  ├── Renders HTML newspaper                             │
│  ├── Saves briefing_data.json                           │
│  └── peaceiris/actions-gh-pages → deploys to gh-pages  │
└────────────────────────┬────────────────────────────────┘
                         │ briefing_data.json available
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    RENDER (always-on)                   │
│  main.py                                                │
│  ├── APScheduler → 05:00 Lisbon                         │
│  │   ├── Downloads briefing_data.json from GitHub Pages │
│  │   └── Pushes Telegram notification                   │
│  ├── Telegram bot (polling) — GMS conversation          │
│  └── Health server → port 10000 (UptimeRobot ping)      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              GITHUB PAGES (static hosting)              │
│  gh-pages branch → newspaper + briefing_data.json       │
│  https://vasquez-505.github.io/news-ai-agent/           │
└─────────────────────────────────────────────────────────┘
```

**Single pipeline.** GitHub Actions generates the newspaper; Render loads it. No duplicate API calls, no divergence between what GMS knows and what the newspaper says.

---

## Tech stack

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM: Search & Grounding | Gemini 2.5 Flash (native Google Search) | Free (20 RPD, 500 grounding calls/day) |
| LLM: Generate & Chat | Gemma 4 31B IT | Free (higher quota, no grounding needed) |
| Bot framework | python-telegram-bot 21.x | Free |
| TTS | edge-tts (Microsoft Neural, en-US-GuyNeural) | Free |
| Scheduling | APScheduler (on Render) + GitHub Actions | Free |
| Bot hosting | Render free tier + UptimeRobot keepalive | Free |
| Dashboard hosting | GitHub Pages (gh-pages branch) | Free |
| Market data | yfinance + CoinGecko API + FRED API | Free |
| HTML templating | Jinja2 | Free |

**Total running cost: $0/month.**

---

## LLM architecture: two-model split

`generate_with_search()` uses **Gemini 2.5 Flash** with the `GoogleSearch` grounding tool. It searches Google's full index and synthesises content in one call, used by all 7 topic fetchers, falling back to Gemma on quota exhaustion.

`generate()` / `chat()` use **Gemma 4 31B IT**. Higher daily quota, used for the GMS conversation, voice script generation, and any plain generation that doesn't need live search.

```python
# provider.py — simplified
def generate_with_search(prompt):          # Gemini 2.5 Flash + GoogleSearch()
def generate(prompt):                      # Gemma 4 31B IT
def chat(history, message, system):        # Gemma 4 31B IT
```

---

## GMS: the briefing agent

Personality modelled on TARS from *Interstellar*: precise, dry wit, zero fluff. Humor setting: 75%.

The bot holds the full briefing context from the moment Render loads it at 5am. Any message you send triggers a GMS response grounded in today's briefing. The session ends with a watchlist prompt.

```
You:  [taps 📋 Copy briefing context]
Bot:  [sends full GMS persona + Pedro profile + today's briefing]
      → copy → paste into Claude.ai / ChatGPT → fully primed LLM

You:  "Tell me more about the Fed decision."
GMS:  [expands with context from today's briefing — no invention]

You:  "thanks"
GMS:  "Anything specific you'd like me to keep an eye on over the
       coming days? Reply with a topic, or 'no' to end."
```

---

## Copy briefing context

The morning push includes a single **📋 Copy briefing context** button. Tapping it makes the bot send a structured LLM prompt containing:

- System role: GMS/TARS persona definition
- User profile: Pedro's investor background, tools, location, language
- Behavioural rules: response style, language switching, no filler, portfolio flagging
- Today's briefing: all 7 topics
- Closing instruction: "Answer his questions. Proceed."

Long-press the message → Copy → paste into any frontier LLM for an instant briefed conversation.

---

## Watchlist

Track ongoing stories across sessions. GMS monitors them daily and surfaces updates automatically.

```
You:  "Keep an eye on the SpaceX IPO"
GMS:  "Added. I'll flag updates each morning."

You:  "What am I tracking?"
GMS:  "Currently tracking: SpaceX IPO (added May 07)"

You:  "Drop the SpaceX story"
GMS:  "Removed SpaceX IPO from your watchlist."
```

Stored in `data/watchlist.yaml`. Persists across sessions and pipeline runs.

---

## Prompt engineering

All 7 topic prompts use XML-structured format with explicit sections:

```xml
<role>     — who the model is and what Pedro expects         </role>
<task>     — what to research, date-aware                    </task>
<selection_criteria>
           — INCLUDE / EXCLUDE rules, source preference
</selection_criteria>
<output_format>
           — exact structure, bullet format, closing line
</output_format>
<quality_rules>
           — specificity requirements, before/after rule,
             no preamble, no internal citations
</quality_rules>
```

Key quality rules applied globally:
- Every bullet answers both *what happened* and *why it matters*
- Policy sections must state *"Previously: X. Now: Y."* with exact figures
- No opener lines ("Here is your morning briefing..."), `_OUTPUT_GUARD` appended to every prompt
- No internal citations (`[cite: X]`) in output
- Vague phrases ("experts say", "could potentially") explicitly prohibited

---

## File structure

```
News_AI_Agent/
├── main.py                     # Entry point — scheduler + bot + health server
├── bot.py                      # Telegram bot — GMS conversation, watchlist, copy context
├── pipeline.py                 # Pipeline — fetch all topics, render HTML, voice script
├── state.py                    # In-memory shared state (topics, voice script, status)
├── config.yaml                 # LLM, TTS, schedule, topics configuration
│
├── topics/
│   ├── world_news.py
│   ├── markets_economy.py      # Hybrid: live APIs (yfinance, CoinGecko, FRED) + grounding
│   ├── ai_productivity.py
│   ├── portugal_policy.py
│   ├── eu_policy.py
│   ├── us_policy.py
│   └── ai_tools_snapshot.py   # Pedro's tool comparison — PEDRO_TOOLS dict
│
├── llm/
│   └── provider.py             # Two-model Gemini provider — search, generate, chat
│
├── tts/
│   └── voice.py                # edge-tts — converts voice script to MP3
│
├── dashboard/
│   └── render.py               # Jinja2 → newspaper HTML
│
├── search/
│   └── searcher.py             # RSS helper (Tavily removed — native grounding used)
│
├── utils/
│   └── greetings.py            # Greeting pool (15 entries + day-aware variants)
│
├── data/
│   └── watchlist.yaml          # Persistent watchlist
│
├── output/                     # Generated HTML + briefing_data.json (deployed to gh-pages)
│
└── .github/workflows/
    └── morning_fetch.yml       # GitHub Actions — 01:00 UTC daily pipeline
```

---

## Configuration

```yaml
# config.yaml
schedule:
  fetch_time: "05:00"
  timezone: "Europe/Lisbon"

llm:
  provider: "gemini"
  model: "gemma-4-31b-it"       # generate() and chat() only

tts:
  provider: "edge-tts"
  voice: "en-US-GuyNeural"
  pitch: "-5st"
  rate: "-5%"

topics:
  enabled:
    - general_world_news
    - investment_markets
    - ai_productivity
    - portugal_policy
    - eu_policy
    - us_policy
    - ai_tools_snapshot
```

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | From BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram user ID |
| `GEMINI_API_KEY` | Google AI Studio (free) |
| `FRED_API_KEY` | FRED macroeconomic data (free) |
| `DASHBOARD_URL` | GitHub Pages URL for the newspaper |

---

## Deployment

Connect repo on Render, set env vars, deploy. Auto-deploys on every push to `main`.

GitHub Pages: Settings → Pages → Deploy from branch → `gh-pages` → `/`

GitHub Actions secrets: add `GEMINI_API_KEY` and `FRED_API_KEY` under repo Settings → Secrets → Actions.

UptimeRobot: create an HTTP monitor pointing at your Render URL, every 5 minutes. Keeps the free tier alive 24/7.

---

## Planned features

- GMS Voice Mode: one-click desktop workflow that opens a live voice conversation with a frontier LLM pre-loaded with today's full briefing context. No pasting, no setup. One double-click, start talking.

---

*Built by Pedro Vasquez · Lisbon, Portugal · 2026*

# Good Morning Sunshine — Daily Intelligence Briefing Agent

> *"The world generates a lot of noise. This is the signal."*

A fully automated personal intelligence system that fetches, analyses, and delivers a daily morning briefing across 7 curated topics — deployed on a zero-cost stack, delivered via Telegram, and readable as a newspaper-style HTML dashboard.

---

## What It Does

Every morning at 5:00 AM, before you wake up, the system:

1. **Fetches and analyses** 7 topics using Gemini 2.0 Flash with live Google Search grounding
2. **Renders a newspaper dashboard** deployed to GitHub Pages — readable anywhere, any time
3. **Pushes a Telegram notification** with the dashboard link and two action buttons
4. **Generates a voice briefing** (~90 seconds) ready to play on demand

When you tap **Talk to GMS**, your personal AI briefing agent — modelled on GMS from *Interstellar* — greets you with an intelligently weighted summary of the day and holds a free conversation about anything in the briefing.

---

## Morning Flow

```
5:00 AM  ─── Pipeline runs automatically (Render + GitHub Actions)
             ├── 7 topics fetched with live web search
             ├── HTML newspaper deployed to GitHub Pages
             └── Voice script generated

You wake up ─── Telegram push waiting:
                 "📰 Your briefing for Thursday, May 08 is ready."
                 [link to newspaper]
                 [🤖 Talk to GMS]  [📰 Start Briefing]

Option A ─── Tap the link → read the full newspaper in your browser
Option B ─── Tap Start Briefing → 90-second voice note plays
Option C ─── Tap Talk to GMS → GMS greets you with today's summary
                                  → free back-and-forth conversation
```

---

## The 7 Topics

| # | Topic | Coverage |
|---|-------|----------|
| 🌍 | **World News** | Top 3–5 global stories — what happened + why it matters |
| 📈 | **Markets & Economy** | Live macro snapshot (S&P, Gold, BTC, EUR/USD, Fed rate) + sector alerts |
| ⚡ | **AI & Productivity** | Shipped AI products only — no announcements, no speculation |
| 🇵🇹 | **Portugal Policy** | Enacted laws only — concrete provisions, practical impact |
| 🇪🇺 | **EU Policy** | Formally adopted regulations — Portugal impact flagged |
| 🇺🇸 | **US Policy** | Signed executive orders and legislation — balanced, factual |
| 🛠️ | **AI Tools Snapshot** | Daily table comparing current tools vs best-in-class alternatives |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    RENDER (always-on)                   │
│  main.py                                                │
│  ├── APScheduler → run_pipeline() at 05:00 Lisbon       │
│  ├── Telegram bot (polling)                             │
│  └── Health server → port 10000 (UptimeRobot ping)      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               GITHUB ACTIONS (scheduled)                │
│  morning_fetch.yml → cron 0 5 * * *                     │
│  ├── run_pipeline() → generates HTML                    │
│  └── peaceiris/actions-gh-pages → deploys to gh-pages  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              GITHUB PAGES (static hosting)              │
│  gh-pages branch → newspaper dashboard                  │
│  https://vasquez-505.github.io/news-ai-agent/           │
└─────────────────────────────────────────────────────────┘
```

**Two independent pipelines. Dashboard updates even if the bot is down.**

---

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM + Search | Gemini 2.0 Flash (Google Search Grounding) | Free — 1,500 req/day |
| Bot framework | python-telegram-bot 21.x | Free |
| TTS | edge-tts (Microsoft Neural — en-US-GuyNeural) | Free |
| Scheduling | APScheduler (on Render) + GitHub Actions | Free |
| Bot hosting | Render free tier + UptimeRobot keepalive | Free |
| Dashboard hosting | GitHub Pages (gh-pages branch) | Free |
| Market data | yfinance + CoinGecko API + FRED API | Free |
| HTML templating | Jinja2 | Free |

**Total running cost: $0/month.**

---

## GMS — The Briefing Agent

Personality modelled on GMS from *Interstellar*: precise, dry wit, zero fluff. Humor setting: 75%.

GMS holds the full briefing context from the moment you tap Talk to GMS. The conversation is completely open — ask about any story, go deeper on a topic, or ask something unrelated. Each session ends with a prompt to add items to your watchlist.

```
GMS:  "Morning. Markets are mixed, geopolitics are not.
        Here's what actually matters today:

        World: [weighted summary — 2-3 sentences if significant]
        Markets: [macro signal + one sector alert]
        AI: [what actually shipped]
        ...

        What do you want to dig into?"

You:   "Tell me more about the Fed decision."
GMS:  [expands with context from today's briefing]
```

---

## Watchlist

Track ongoing stories across sessions. GMS monitors them daily and surfaces updates automatically.

```
You:   "Keep an eye on the SpaceX IPO"
GMS:  "Added. I'll flag updates each morning."

You:   "What am I tracking?"
GMS:  "Currently tracking: SpaceX IPO (added May 07)"

You:   "Drop the SpaceX story"
GMS:  "Removed SpaceX IPO from your watchlist."
```

Stored in `data/watchlist.yaml`. Persists across sessions and pipeline runs.

---

## Prompt Engineering

All 7 topic prompts use XML-structured format with explicit sections:

```xml
<role>     — who the model is and what Pedro expects  </role>
<task>     — what to fetch, date-aware               </task>
<selection_criteria>
           — INCLUDE / EXCLUDE rules, source preference
</selection_criteria>
<output_format>
           — exact structure, bullet format, closing line
</output_format>
<quality_rules>
           — what not to do, specificity requirements
</quality_rules>
```

Every bullet is required to answer both **what happened** and **why it matters**. Vague phrases ("experts say", "could potentially") are explicitly prohibited. Markets topic is hybrid: live numeric data from APIs + grounding for sector news, keeping financial accuracy separate from editorial content.

---

## File Structure

```
News_AI_Agent/
├── main.py                     # Entry point — scheduler + bot + health server
├── bot.py                      # Telegram bot — GMS conversation, watchlist, briefing
├── pipeline.py                 # Pipeline — fetch all topics, render HTML, voice script
├── state.py                    # In-memory shared state (topics, voice script, status)
├── config.yaml                 # LLM, TTS, schedule, topics configuration
│
├── topics/
│   ├── world_news.py
│   ├── markets_economy.py      # Hybrid: live APIs + grounding
│   ├── ai_productivity.py
│   ├── portugal_policy.py
│   ├── eu_policy.py
│   ├── us_policy.py
│   └── ai_tools_snapshot.py
│
├── llm/
│   └── provider.py             # Gemini provider — generate, generate_with_search, chat
│
├── tts/
│   └── voice.py                # edge-tts — converts voice script to MP3
│
├── dashboard/
│   └── render.py               # Jinja2 → newspaper HTML
│
├── utils/
│   └── greetings.py            # Greeting pool (15 entries + day-aware variants)
│
├── data/
│   └── watchlist.yaml          # Persistent watchlist
│
├── output/                     # Generated HTML (deployed to gh-pages)
│
└── .github/workflows/
    └── morning_fetch.yml       # GitHub Actions — daily 05:00 UTC pipeline
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
  model: "gemini-2.0-flash"

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

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | From BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram user ID |
| `GEMINI_API_KEY` | Google AI Studio — free |
| `FRED_API_KEY` | FRED macroeconomic data — free |
| `DASHBOARD_URL` | GitHub Pages URL for the newspaper |

---

## Planned Features

See [PLANNED_FEATURES.md](PLANNED_FEATURES.md) for the full roadmap.

**Next:** `GMS_newt` — a one-click desktop workflow (Playwright) that opens a voice conversation with a top-tier LLM pre-loaded with today's full briefing context. No pasting, no setup — one double-click, start talking.

---

## Deployment

**Render:** Connect repo → set env vars → deploy. Auto-deploys on every push to `main`.

**GitHub Pages:** Settings → Pages → Deploy from branch → `gh-pages` → `/`

**GitHub Actions secrets:** Add `GEMINI_API_KEY` and `FRED_API_KEY` under repo Settings → Secrets → Actions.

**UptimeRobot:** Create HTTP monitor → your Render URL → every 5 minutes. Keeps the free tier warm 24/7.

---

*Built by Pedro Vasquez · Lisbon, Portugal · 2026*

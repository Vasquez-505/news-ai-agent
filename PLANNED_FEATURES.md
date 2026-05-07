# Planned Features — News AI Agent

---

## 1. GMS_newt — Voice Conversation Workflow

### What it is
A one-click workflow that opens a real voice conversation with a top-tier LLM (Claude.ai, Gemini, or ChatGPT), pre-loaded with today's full briefing context and Pedro's persona instructions. No pasting, no setup — click once, start talking.

This is the "Jarvis/TARS" experience: a proper back-and-forth voice conversation about the morning briefing, using the native voice mode of the chosen LLM app.

### Trigger
A desktop shortcut (`GMS_newt.bat` or `gms_newt.py`) on Pedro's PC. One double-click in the morning.

### What happens when triggered
1. Script reads `briefing_today.md` — generated automatically by the pipeline at 5am
2. Script reads `context/pedro_profile.md` — Pedro's permanent profile (investments, preferences, background)
3. Script reads `context/tars_prompt.md` — TARS persona instructions and behaviour rules
4. Playwright opens the chosen LLM app in the browser
5. Navigates to a new conversation (or designated project folder inside the app)
6. Pastes all three files as context
7. Sends the opening prompt
8. Browser is ready — Pedro starts the voice conversation

### Files needed (to be created)

#### `context/pedro_profile.md`
Permanent file. Contains:
- Pedro's background and location (Lisbon, Portugal)
- Investment portfolio composition (ETFs, tech, defence, energy, commodities, crypto)
- Tools he uses daily
- Topics he follows
- Languages (Portuguese / English)
- Risk appetite and investment style
- Any preferences TARS should know

#### `context/tars_prompt.md`
Permanent file. Contains:
- TARS persona and tone (Interstellar reference — dry, precise, 75% humor)
- Role: morning intelligence system
- How to handle the briefing (weight topics by importance, be specific)
- Conversation rules (no filler, no invented facts, tight unless asked for depth)
- Opening behaviour: greet + informative briefing summary + invite to dig in

#### `briefing_today.md`
Generated daily by the pipeline at 5am. Contains all 7 topics in plain text:
- World News
- Markets & Economy (including live macro data)
- AI & Productivity
- Portugal Policy
- EU Policy
- US Policy
- AI Tools Snapshot

**Pipeline change needed:** `pipeline.py` currently saves output as HTML only. It needs to also save `output/briefing_today.md` in plain text so the Playwright script can read it.

### Implementation steps
1. Write `context/pedro_profile.md` (Pedro reviews and adjusts)
2. Write `context/tars_prompt.md`
3. Add markdown export to `pipeline.py` (`output/briefing_today.md`)
4. Write `gms_newt.py` using Playwright
5. Create `GMS_newt.bat` desktop shortcut that runs `python gms_newt.py`
6. Test end-to-end

### Target LLM app
TBD — Claude.ai, Gemini, or ChatGPT. Pedro to confirm which voice mode he prefers.

---

## 2. TARS — Telegram Text Conversation (Implemented)

Already live. Morning push includes inline buttons:
- **🤖 Talk to TARS** — TARS sends an informative briefing summary and holds a free text conversation inside Telegram. Useful for quick questions on the go.
- **📰 Start Briefing** — sends the 90-second voice note summary

This is the mobile-friendly fallback. GMS_newt is the full desktop voice experience.

---

## 3. briefing_today.md Pipeline Export (Needed for GMS_newt)

Currently the pipeline outputs:
- `output/briefing_YYYY-MM-DD.html` — HTML newspaper dashboard (deployed to GitHub Pages)
- In-memory state for the Telegram bot

Needs to also output:
- `output/briefing_today.md` — plain text version of all 7 topics, readable by the Playwright script

Small change to `pipeline.py` and `dashboard/render.py`.

---

# Pedro's Daily Intelligence Briefing -- Project Spec

> **Status:** Planning phase -- no implementation yet
> **Last updated:** 2026-05-05
> **Owner:** Pedro (Portugal)

---

## 1. What This Is

A "Jarvis" morning briefing agent that:
- **Fetches all data silently at 5:00 AM** (before Pedro wakes up) -- no wait time when he starts
- **Pedro taps to start** -- no auto-play at a fixed hour; he opens Telegram, taps "Start Briefing", and the voice begins immediately
- Delivers the headline reel via voice, then holds a **fully open conversation** -- Pedro can interrupt at any moment, mid-sentence if needed
- Generates a **visual dashboard** (hosted HTML page with clickable source links) viewable on phone or PC anywhere

---

## 2. Interaction Flow

### Core principle
**All 7 topics are fetched and ready before Pedro ever touches his phone.** The conversation is Pedro navigating a briefing that is already fully prepared. No fetching on demand, no waiting.

### Step 1 -- Silent data fetch at 5:00 AM (automatic, no interaction)

GitHub Actions wakes up at 5:00 AM Lisbon time, runs all 7 topic searches, generates all summaries, generates TTS audio files, builds the HTML dashboard, and pushes everything to the bot backend. Content is ready and waiting.

### Step 2 -- Pedro taps "Start Briefing" (whenever he wakes up)

In Telegram, a persistent button "Start Briefing" is always available. Pedro taps it at whatever time he chooses -- 7 AM, 8 AM, whenever. The bot responds instantly with the greeting + headline reel voice message.

There is no scheduled audio. Pedro is always in control of when it starts.

### Step 3 -- Greeting + Headline Reel (~2 min)

The agent opens with a varied, original greeting (see greeting pool below), then flows immediately into the headline reel.

**Headline reel format:**

```
[greeting]

"World: [1-sentence global headline]"
"Markets: [1-sentence -- biggest market signal today]"
"AI: [1-sentence -- most important AI release or move]"
"Portugal: [1-sentence -- most relevant approved law or policy]"
"Europe: [1-sentence -- top EU decision]"
"US: [1-sentence -- top signed action]"
"Tools: [1-sentence -- any upgrade worth knowing about]"
```

**Greeting pool -- rotate randomly, never repeat within a week:**

```
"Good morning, sir. The feeds have been busy."
"Rise and shine. Seven topics, all loaded."
"Good morning. I've been watching the world for you."
"Morning, sir. The world didn't wait -- neither should we."
"All systems operational. Good morning."
"Good morning. Ready when you are."
"Sir. Another day, another briefing. Let's begin."
"The news never sleeps. Good morning."
"Good morning. I have your intelligence summary prepared."
"Right on time, sir. Everything is ready."
"A new day. A lot happened. Good morning."
"Morning. Seven topics. Let's not waste daylight."
"Good morning, sir. The world has been eventful."
"I've done the reading. Good morning."
"Seven topics, zero fluff. Good morning, sir."
```

**Day-aware variants:**

```
Monday:   "Good morning, sir. New week, new briefing. Let's see what we're dealing with."
Friday:   "Last briefing of the week, sir. Let's make it count. Good morning."
Saturday: "Good morning. The markets are closed, but the world is not."
```

### Step 4 -- Open prompt (always follows reel)

```
"What would you like to hear?"
```

Short. Open. No menu. Pedro decides.

### Step 5 -- Pedro leads, agent follows (fully open conversation)

This is a live conversation. Pedro can say anything natural. He can also **interrupt at any point -- mid-sentence, mid-topic -- to ask a question or change direction.** The agent stops, responds, and offers to continue.

| Pedro says (examples) | Agent does |
|----------------------|------------|
| "Markets" / "Tell me about markets" | Reads Topic 2 in full |
| "What happened in Portugal?" | Reads Topic 4 in full |
| "Give me everything" / "Full briefing" | Reads all topics in order, 1 through 7 |
| "Continue" / "Next" | Reads the next topic in the default order |
| "Skip that" / "Not interested" | Skips current topic, moves to next |
| "Tell me more about [X]" | Expands on that specific point from pre-loaded content |
| "Wait -- what does that mean for [Y]?" | Stops, explains the implication, then continues |
| "Stop" / "That's enough" / "Thanks" | Ends session cleanly |
| silence / no response | After ~15 seconds, defaults to Topic 1 and continues in order |

### Default behavior (no preference expressed)

Full briefing, Topics 1 through 7 in order. Pedro can interrupt at any point.

### After each topic

```
"[brief pause] -- want to continue?"
```

Just enough space for Pedro to redirect. Not a menu.

### Session End

When Pedro says stop, or after the last topic if he went through everything, the agent closes with two things:

**1. Watchlist check-in (always):**
```
"Anything specific you'd like me to keep an eye on over the coming days?"
```
Pedro can name a story, event, conflict, company, or situation. The agent adds it to the watchlist. If Pedro says "no" or "nothing", session ends cleanly.

**2. Bi-weekly spec health check (every two weeks, not every session):**
```
"Quick spec review -- a couple of suggestions when you have a moment."
```
Followed by a short list of flagged items (sources that changed, companies losing relevance, search terms that underperformed). Pedro reads, approves what he wants, ignores the rest. Agent only updates the spec for approved items.

---

## 3. Topic Order

| # | Topic | Emoji |
|---|-------|-------|
| 1 | General World News | 🌍 |
| 2 | Markets & Economy | 📈 |
| 3 | AI & Productivity | ⚡ |
| 4 | Portugal Policy & Law | 🇵🇹 |
| 5 | European Union Policy | 🇪🇺 |
| 6 | United States Policy | 🇺🇸 |
| 7 | AI Tools Snapshot | 🛠️ |

---

## 4. Voice & Audio Behavior

### Voice options (configurable in config.yaml)

| Option | Provider | Cost | Quality | Notes |
|--------|----------|------|---------|-------|
| edge-tts (default) | Microsoft neural (free) | Free | Very good | en-US-GuyNeural, deep and clear |
| elevenlabs | ElevenLabs API | Free tier: 10K chars/month | Excellent | Use a Jarvis-style community voice |
| openai-tts | OpenAI API | ~$0.015/1K chars | Very good | "onyx" voice -- deep, professional |

### TARS approximation
No official TARS voice exists. Closest available:
- edge-tts with en-US-GuyNeural at pitch -10% and rate -5% -- monotone, measured
- ElevenLabs community search: "TARS", "HAL 9000", "robotic narrator"

### Audio delivery via Telegram
- Bot sends each section as a voice message (.ogg, plays natively in Telegram)
- Text version always sent alongside audio (for silent reading)
- Pedro can interrupt by sending a text message at any point -- bot pauses and responds

---

## 5. Delivery & Dashboard

### Primary channel -- Telegram Bot

Telegram is the core interface. Works on mobile data and PC. Free. Handles voice messages, text, and buttons natively.

**Morning flow:**
1. 5:00 AM: content generated silently, bot is loaded and ready
2. Pedro wakes up, opens Telegram, taps **[Start Briefing]** button
3. Bot sends greeting + headline reel as voice message + text card
4. Bot sends link to HTML dashboard
5. Pedro responds naturally -- bot replies with the next section as voice + text
6. Conversation stays open -- Pedro can ask, interrupt, go deeper at any point

**Telegram UI:**
- Persistent reply keyboard with "Start Briefing" button (always visible at bottom of chat)
- After each topic: inline "Continue" / "Stop" buttons as quick options (but Pedro can also just type naturally)

### Secondary channel -- HTML Dashboard (always accessible)

A hosted web page Pedro can open anytime on phone or PC. Updated each morning by 5:30 AM.

- Journal / broadsheet newspaper aesthetic (see design spec below)
- Full briefing with all 7 topics
- Every news item has a **clickable source link** to the original article
- Macro signals table with live data (Markets topic)
- Same URL always -- today's briefing auto-loads
- Readable in ~5 minutes

### Dashboard Design Spec

**Aesthetic:** The Economist meets Financial Times. Serious, readable, dense with information but never cluttered. Classic broadsheet newspaper on screen. Light mode (cream/newsprint background -- easier to read than dark for long-form text).

**Masthead:**

```
---------------------------------------------------------
          GOOD MORNING SUNSHINE
---------------------------------------------------------
  THE DAILY BRIEFING  ·  LISBON  ·  [Day, Full Date]
---------------------------------------------------------
```

Warm, personal, slightly self-aware. Not taking itself too seriously.

**Typography (Google Fonts CDN -- free, no install):**

| Element | Font | Weight | Notes |
|---------|------|--------|-------|
| Masthead | Playfair Display | 900 | Classic newspaper serif |
| Topic section headers | Playfair Display | 700 | With thin/thick rule above |
| Body text | Source Serif 4 | 400 | Optimized for screen readability |
| Pull quotes / key stats | Libre Baskerville | 400 italic | For market numbers |
| Tickers / prices / numbers | IBM Plex Mono | 500 | Clean monospace for financial data |
| Meta / bylines / datelines / source links | Source Sans 3 | 400 | Small, uppercase |

**Color palette:**

| Element | Color | Hex |
|---------|-------|-----|
| Page background | Cream / newsprint | #F7F3E8 |
| Primary text | Near black | #1A1A1A |
| Section headers | Deep red (classic newspaper accent) | #8B1A1A |
| Column rules / dividers | Dark gray | #2A2A2A |
| Signal green | Muted green | #2D6A2D |
| Signal yellow | Warm amber | #A67C00 |
| Signal red | Deep red | #8B1A1A |
| Source links | Navy | #1B3A6B |
| Macro table background | Slightly darker cream | #EEE9D8 |

**Layout (CSS Grid -- pure CSS, no framework):**

- **Masthead:** Full width. "GOOD MORNING, PEDRO" in large Playfair Display. Date line below. Thick/thin rule separators.
- **Dateline:** "LISBON -- [Day], [Date], [Year]" in small uppercase Source Sans.
- **Topic grid:** 3 columns desktop, 2 tablet, 1 mobile. Each topic is a newspaper "section."
- **Markets topic:** Full-width section with macro snapshot table in newsprint colors.
- **Column rules:** Thin vertical lines between columns.
- **Drop cap:** First letter of each topic body in large drop cap (CSS ::first-letter, 3 lines tall).
- **Pull quotes:** "Why it matters" line displayed as indented pull quote with left border rule.
- **Source citations:** Each bullet ends with a small [Source Name] link in Source Sans, navy color, opens article in new tab.
- **No bullet points** -- bold lead word followed by em dash (newspaper paragraph style).

**No third-party UI framework.** Pure CSS + Google Fonts CDN. Self-contained, fast, no external dependencies that can break.

### Email (archive only -- optional)
Send the HTML dashboard to Pedro's email as a daily searchable archive. Not the primary channel.

---

## 6. Topics -- Full Specifications

**Global format rule (applies to ALL topics):**
Every bullet must do two things: (1) state the fact, (2) briefly explain what it means or why it matters. No raw facts without context. One sentence can do both if tight enough. The agent should always connect the news to its real-world implication, even for a 1-sentence headline.

---

### 🌍 Topic 1 -- General World News

**Focus:** The 5 most important global stories in the last 24 hours. Geopolitics, major events, science breakthroughs, conflicts, significant economic developments. No opinion, no spin -- state what happened and what it means.

**Format:** 5 bullets max. Bold the subject. State the fact + explain the implication. End with "Why it matters:" one-liner.

**What to avoid:** Soft news, celebrity stories, local/sports, anything without meaningful global relevance.

**Sources -- ranked by priority:**

| Source | Signal quality | Political lean | Notes |
|--------|---------------|---------------|-------|
| Reuters World | ⭐⭐⭐⭐⭐ | Center | Gold standard wire; fastest; zero editorial bias; free RSS |
| AP News | ⭐⭐⭐⭐⭐ | Center | Global cooperative, 100+ countries; free RSS |
| BBC News World | ⭐⭐⭐⭐ | Center-left | Strong editorial standards and depth; free RSS |
| Deutsche Welle (DW) | ⭐⭐⭐⭐ | Center | Germany's intl broadcaster; adds European/African angle; free RSS |
| Al Jazeera | ⭐⭐⭐⭐ | Center-left / non-Western | Best non-Western perspective; strong investigative work; free RSS |
| The Free Press | ⭐⭐⭐⭐ | Center-right / heterodox | Bari Weiss; covers stories mainstream media downplays; Substack RSS |
| Observador | ⭐⭐⭐⭐ | Center-right | High-quality Portuguese outlet with strong international desk; free RSS |
| The Daily Wire | ⭐⭐⭐ | Right | Right-leaning US conservative outlet; useful for stories framed differently; RSS available |
| France 24 | ⭐⭐⭐ | Center | Good Africa and Middle East gap coverage; free RSS |

**Source balance note:** Reuters + AP provide the factual baseline. The Free Press and Daily Wire ensure stories that left-leaning outlets underemphasise are captured. Al Jazeera adds the non-Western lens. Use all, cross-reference when perspectives diverge.

**Search queries:**
1. Top world news today [date]
2. Major geopolitical events this week
3. Breaking international news [date]

---

### 📈 Topic 2 -- Markets & Economy

**Focus:** Key market signals and economic developments. Pedro tracks these sectors for general market intelligence -- this is not portfolio management, it is market awareness. Cross-reference signal readings against the thresholds defined in `investment_framework.md`.

**Format:**

**Section A -- Macro Snapshot (always included)**

Pull live values and compare against thresholds. Emit signal: 🟢 bullish / 🟡 neutral / 🔴 caution.

| Indicator | Data source | Method |
|-----------|-------------|--------|
| S&P 500 level + daily % | Yahoo Finance | yfinance (free, no key) |
| Shiller CAPE ratio | Yale official data | econ.yale.edu/~shiller/data.htm or Multpl.com |
| Gold price (USD/oz) | Yahoo Finance (GC=F) | yfinance |
| Silver price (USD/oz) | Yahoo Finance (SI=F) | yfinance |
| Gold/Silver ratio | Calculated: Gold / Silver | -- |
| WTI Oil price | Yahoo Finance (CL=F) | yfinance |
| USD/EUR exchange rate | Yahoo Finance (EURUSD=X) | yfinance |
| BTC price | CoinGecko API | Free REST, no key |
| BTC dominance | CoinGecko API | Free REST, no key |
| 10Y US Treasury yield | Yahoo Finance (^TNX) | yfinance |
| Fed Funds Rate | FRED API (FEDFUNDS) | Free key from fred.stlouisfed.org |

**Section B -- Sector News**

Search for news across the tracked sectors. Only flag if materially relevant: earnings surprise, major contract, significant price move, regulatory action. Explain what it means, not just what happened.

| Sector | Search terms |
|--------|-------------|
| Equities / Indices | "S&P 500 performance", "MSCI World", "Nasdaq 100 today" |
| Tech / AI stocks | "Nvidia earnings", "Microsoft AI revenue", "Magnificent 7", "semiconductor cycle" |
| Gold & Silver | "gold price today", "silver price", "central bank gold buying" |
| Aerospace & Defense | "defense spending", "NATO budget", "defense sector earnings" |
| Clean Energy | "nuclear energy news", "uranium price", "IRA subsidies", "renewable energy" |
| Copper & Lithium | "copper LME price", "lithium price", "EV sales", "battery market" |
| Oil & Gas | "WTI oil price", "OPEC decision", "LNG Europe" |
| Quantum / Biotech | "quantum computing news", "CRISPR news", "biotech earnings" |
| Crypto | "Bitcoin price", "BTC dominance", "Ethereum news", "crypto regulation" |

**News sources -- Markets & Economy:**

| Source | Signal quality | Notes |
|--------|---------------|-------|
| Reuters Finance | ⭐⭐⭐⭐⭐ | Best financial wire; free RSS |
| MarketWatch | ⭐⭐⭐⭐ | Strong market coverage; free RSS |
| CNBC Markets | ⭐⭐⭐⭐ | Good real-time market news; free RSS |
| Yahoo Finance | ⭐⭐⭐ | Broad coverage; free RSS |
| JustETF | ⭐⭐⭐⭐ | Best UCITS ETF data for EU investors; use justetf-scraping Python library (GitHub, free) |
| Bloomberg | ⭐⭐⭐ | Headlines only (mostly paywalled) -- use via web search for specific stories |

**Format output:**

```
MACRO SNAPSHOT
[table: indicator | live value | signal]

SECTOR ALERTS (only sectors with material news today)
[bullets -- fact + implication, same format as other topics]

Why it matters: [one sentence -- most actionable signal today]
```

---

### ⚡ Topic 3 -- AI & Productivity

**Focus:** Latest AI model releases, product launches, and productivity tool updates. Prioritize shipped products over announcements. Explain practical impact -- what does this actually change for someone who works with these tools.

**Format:** 5 bullets max. Bold subject. State what launched + what it means in practice. "Why it matters:" one-liner.

**Search queries (run separately):**
1. New AI model releases this week -- OpenAI, Anthropic, Google DeepMind, xAI, Meta, Mistral, DeepSeek
2. New AI product launches this week -- Google Labs, Anthropic, OpenAI, Meta AI, Microsoft, xAI
3. AI productivity tools launched this week -- Cursor, Notion, Figma, Adobe, Perplexity, broader ecosystem
4. AI workplace automation news this week

**Sources -- tiered by signal quality:**

**Tier 1 -- High signal, curated (prioritize these)**

| Source | Signal quality | Notes |
|--------|---------------|-------|
| The Batch (DeepLearning.AI) | ⭐⭐⭐⭐⭐ | Andrew Ng's weekly; authoritative, high signal-to-noise; deeplearning.ai/the-batch |
| Import AI (Jack Clark) | ⭐⭐⭐⭐⭐ | Anthropic co-founder; 96K+ subscribers; deep technical + policy; Substack RSS |
| Hugging Face Blog | ⭐⭐⭐⭐⭐ | Direct source for open-source model releases; huggingface.co/blog/feed.xml |
| TLDR AI | ⭐⭐⭐⭐ | Daily digest; 1.25M+ subscribers; concise; tldr.tech/ai |

**Tier 2 -- Product launches and industry news**

| Source | Signal quality | Notes |
|--------|---------------|-------|
| TechCrunch AI | ⭐⭐⭐⭐ | Best for product launches and funding rounds; free RSS |
| VentureBeat AI | ⭐⭐⭐ | Good enterprise AI coverage; free RSS |
| Ars Technica | ⭐⭐⭐ | Good technical depth; free RSS |

**Tier 3 -- Official lab blogs (direct source, use for verification)**

| Lab | Blog URL |
|-----|---------|
| Anthropic | anthropic.com/news |
| OpenAI | openai.com/blog |
| Google DeepMind | deepmind.google/discover/blog |
| Meta AI | ai.meta.com/blog |
| Mistral | mistral.ai/news |
| xAI | x.ai/blog |
| Hugging Face | huggingface.co/blog |

---

### 🇵🇹 Topic 4 -- Portugal Policy & Law

**Focus:** Officially approved or enacted laws, tax changes, government regulations, and public policy. No proposals or debates -- only what has been signed, approved, or is coming into effect. For each measure: name it, describe its concrete provisions, and explain what it means for people or businesses.

**Format:** 5 bullets max. Name the law/measure, describe its key provisions (thresholds, who is affected, what changes), explain practical impact. "Why it matters:" one-liner.

**Search queries:**
1. Portugal nova lei aprovada [current month/year]
2. Assembleia da Republica aprovacao [current month/year]
3. Governo portugues medidas aprovadas
4. Portugal tax changes [current year]
5. Diario da Republica [current month] new laws

**Sources:**

| Source | Signal quality | Notes |
|--------|---------------|-------|
| Diario da Republica (dre.pt) | ⭐⭐⭐⭐⭐ | THE official source -- all laws published here first; /legislacao/ section |
| Assembleia da Republica (parlamento.pt) | ⭐⭐⭐⭐⭐ | Parliament votes and approved bills; official |
| Observador | ⭐⭐⭐⭐⭐ | Best digital-first Portuguese journalism; strong policy analysis; free RSS |
| Portugal.gov.pt | ⭐⭐⭐⭐ | Government press releases; ministerial decisions |
| Jornal de Negocios | ⭐⭐⭐⭐ | Best newspaper for tax law and business regulation impact; free RSS |
| Publico | ⭐⭐⭐⭐ | High-quality general Portuguese journalism; free RSS |

---

### 🇪🇺 Topic 5 -- European Union Policy

**Focus:** EU regulations and directives formally approved, entering into force, or with significant implementation deadlines. Real-world impact on citizens, businesses, or member states. For each measure: describe its concrete requirements, obligations, timelines, and enforcement. Flag anything directly relevant to Portugal.

**Format:** 5 bullets max. Name the regulation, explain its concrete requirements (not just the name), note Portugal-specific impact where relevant. "Why it matters:" one-liner.

**Search queries:**
1. EU regulation approved [current month/year]
2. European Commission directive [current month/year]
3. European Parliament vote [current month/year]
4. EU law entering into force [current month/year]
5. EU regulation Portugal impact

**Sources:**

| Source | Signal quality | Notes |
|--------|---------------|-------|
| EUR-Lex (eur-lex.europa.eu) | ⭐⭐⭐⭐⭐ | Official EU law journal; all regulations and directives; confirmed RSS |
| European Commission Press Corner | ⭐⭐⭐⭐⭐ | Official press releases; confirmed free RSS |
| European Parliament (europarl.europa.eu) | ⭐⭐⭐⭐ | Votes and news; confirmed RSS at /at-your-service/en/stay-informed/rss-feeds |
| Council of the EU (consilium.europa.eu) | ⭐⭐⭐⭐ | Council press releases and decisions; free RSS |
| Politico Europe | ⭐⭐⭐⭐ | Best EU policy journalism; insider coverage; free RSS |
| Euractiv | ⭐⭐⭐⭐ | Dedicated independent EU policy news; 13 languages; free RSS |

---

### 🇺🇸 Topic 6 -- United States Policy

**Focus:** Signed legislation, executive orders, and major regulatory changes. Balanced and factual. For each action: name it, describe its concrete directives (agencies involved, what is mandated, what changes), and explain what it means.

**Format:** 5 bullets max. Name the action, explain its concrete content, state the implication. "Why it matters:" one-liner.

**Search queries:**
1. Executive order signed [current month/year]
2. US law signed Congress [current month/year]
3. US regulation change [current month/year]
4. White House policy announcement [current month/year]
5. Federal Register new rule [current month/year]

**Sources:**

| Source | Signal quality | Notes |
|--------|---------------|-------|
| White House (whitehouse.gov/presidential-actions) | ⭐⭐⭐⭐⭐ | Official executive orders and presidential actions; free RSS |
| Federal Register (federalregister.gov) | ⭐⭐⭐⭐⭐ | All regulations in full detail; authoritative; confirmed free RSS |
| Congress.gov | ⭐⭐⭐⭐ | Legislation tracking; confirmed RSS and alert system |
| GovInfo (govinfo.gov/feeds) | ⭐⭐⭐⭐ | Government publications and Congressional Record; RSS |
| AP Politics | ⭐⭐⭐⭐ | Wire service quality; fast; free RSS |
| The Hill | ⭐⭐⭐⭐ | Capitol Hill specialist; multiple category feeds at thehill.com/resources/rss-feeds |
| Reuters US Politics | ⭐⭐⭐ | Good international wire perspective on US policy; free RSS |

---

### 🛠️ Topic 7 -- AI Tools Snapshot (Daily Table)

Cross-reference of Pedro's current tools vs best-in-class, updated daily based on Topic 3 news and market knowledge. Pedro's current tools defined in `AI_AGENTES_AUTONOMOS.txt`.

**Categories tracked:**

| Categoria | Pedro usa | Melhor atual | Alternativa | Custo/Plano | Esfoco migracao | Switch? | Motivo |
|-----------|-----------|--------------|-------------|-------------|-----------------|---------|--------|
| Codigo / Agentes | ... | ... | ... | ... | Baixo/Medio/Alto | ... | ... |
| Excel | ... | ... | ... | ... | ... | ... | ... |
| PowerPoint | ... | ... | ... | ... | ... | ... | ... |
| Word | ... | ... | ... | ... | ... | ... | ... |
| LaTeX / Overleaf | ... | ... | ... | ... | ... | ... | ... |
| Knowledge Management | ... | ... | ... | ... | ... | ... | ... |
| Geracao de imagens | ... | ... | ... | ... | ... | ... | ... |
| Pesquisa / Web search | ... | ... | ... | ... | ... | ... | ... |
| Transcricao / Audio | ... | ... | ... | ... | ... | ... | ... |
| Automacao de tarefas | ... | ... | ... | ... | ... | ... | ... |

**Switch? legend:** Optimal | Consider | Upgrade | Not using

Takeaway: 1 sentence -- most actionable change Pedro could make today.

---

## 7. AI Model Configuration

Swappable via config.yaml. No hardcoded model.

| Provider | Model | Cost | Web search built-in | Notes |
|----------|-------|------|---------------------|-------|
| Gemini Flash (default) | gemini-1.5-flash | Free (15 req/min) | Yes -- Google Grounding | Best free option for news tasks |
| Groq | llama-3.3-70b | Free | No -- needs Tavily | Very fast inference |
| OpenRouter | various free models | Free (limited) | No | Fallback |
| Claude API | claude-haiku-3-5 | ~$0.80/1M tokens | No | Best quality, small cost |
| OpenAI | gpt-4o-mini | Paid | Yes (with tool) | If Pedro gets API access |

**Default path (zero extra cost):**
- LLM: Gemini Flash (free) with Google Search Grounding
- Fallback search: Tavily free tier (1,000 calls/month)
- TTS: edge-tts (free)
- Price data: yfinance + CoinGecko (both free, no key)
- Macro data: FRED API (free key from fred.stlouisfed.org)

---

## 8. Cloud Infrastructure

### Where it runs

| Component | Service | Cost | Role |
|-----------|---------|------|------|
| 5:00 AM data fetch + generation | GitHub Actions | Free (2,000 min/month; briefing uses ~5-10 min/day) | Fetches all 7 topics, generates TTS audio, builds HTML dashboard |
| Telegram bot backend | Render free tier or Fly.io | Free | Always-on; handles Pedro's Start tap and all conversation replies |
| HTML dashboard hosting | GitHub Pages or Render static | Free | Serves today's briefing at a fixed URL |

### Why this split
- GitHub Actions handles the scheduled 5 AM generation reliably but cannot stay alive for interactive replies
- Render/Fly.io runs the bot webhook -- receives Pedro's Telegram messages and responds
- The morning job pushes all pre-generated content to the bot backend so it is ready when Pedro taps

### Hosting options (for bot backend)

| Option | Cost | Reliability | Notes |
|--------|------|-------------|-------|
| **Render + UptimeRobot (recommended)** | Free + Free | High | Render free web service (750h/month); UptimeRobot pings every 5 min to prevent spin-down; effectively always-on |
| Oracle Cloud Always Free | Truly free forever | Very high | 2 VMs, 1GB RAM each -- most reliable long-term but requires credit card (never charged) and Linux server knowledge |
| Fly.io | ~~Free~~ PAID -- removed Oct 2024 | -- | No longer viable; minimum ~$13-20/month |

**Why Render + UptimeRobot works:**
- Render free tier gives 750 instance hours/month. Running 24/7 uses 744h -- just within the limit.
- Render spins down after 15 min of inactivity. UptimeRobot (free tier) pings a health endpoint every 5 minutes -- keeps the service permanently warm.
- Combined cost: $0.

---

## 9. System Configuration (config.yaml -- to be defined)

```yaml
schedule:
  fetch_time: "05:00"
  timezone: "Europe/Lisbon"
  # No auto-play -- Pedro taps to start

llm:
  provider: "gemini"     # gemini | groq | openrouter | claude | openai
  model: "gemini-1.5-flash"

tts:
  provider: "edge-tts"   # edge-tts | elevenlabs | openai-tts
  voice: "en-US-GuyNeural"
  pitch: "-10%"
  rate: "-5%"

search:
  provider: "tavily"     # tavily | brave
  fallback: "rss"

delivery:
  telegram:
    enabled: true
    bot_token: ""        # from BotFather
    chat_id: ""          # Pedro's Telegram user ID
  email:
    enabled: false       # archive only
    to: "pepe.vasques10@gmail.com"

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

## 10. Open Questions (to resolve before implementation)

| # | Question | Options | Decision |
|---|----------|---------|----------|
| 1 | Voice interaction for Pedro's response | Type in Telegram vs speak (Whisper STT) | Type first, STT Phase 2 |
| 2 | Where does the agent run | Cloud -- GitHub Actions + Render/Fly.io/Oracle | Resolved -- cloud, available everywhere |
| 3 | Email | Archive only -- primary delivery is Telegram | Resolved |
| 4 | FRED API key | Register at fred.stlouisfed.org (free) | Pending |
| 5 | Market news: sector flagging threshold | All sectors daily vs only when materially relevant | TBD -- threshold-based |
| 6 | Audio on phone | Telegram voice messages -- plays natively | Resolved |
| 7 | Language | English for everything | Resolved |
| 8 | Fetch failure handling | If 5 AM fetch fails, retry at 6 AM? Notify Pedro? | TBD |

---

## 11. File Structure (planned)

```
News_AI_Agent/
├── config.yaml
├── main.py                        # Orchestrator -- runs the full 5 AM pipeline
├── bot.py                         # Telegram bot -- always-on, handles Pedro's Start tap and replies
├── topics/
│   ├── world_news.py
│   ├── markets_economy.py
│   ├── ai_productivity.py
│   ├── portugal_policy.py
│   ├── eu_policy.py
│   ├── us_policy.py
│   └── ai_tools_snapshot.py
├── llm/
│   ├── provider.py                # Abstraction layer -- swap LLM without touching topic files
│   └── prompts/                   # Prompt templates per topic
├── tts/
│   └── voice.py                   # Abstraction layer -- edge-tts / ElevenLabs / OpenAI TTS
├── search/
│   └── searcher.py                # Abstraction layer -- Tavily / Brave / RSS
├── dashboard/
│   └── render.py                  # Generates HTML briefing page
├── data/
│   ├── investment_framework.md    # Market signal thresholds (source of truth)
│   └── watchlist.yaml             # Pedro's active tracked stories (add/remove via conversation)
├── output/
│   └── briefing_YYYY-MM-DD.html
├── .github/
│   └── workflows/
│       └── morning_fetch.yml      # GitHub Actions cron at 05:00 Lisbon time
├── AI_News_Daily_Briefing_Agent.md
└── AI_AGENTES_AUTONOMOS.txt
```

---

## 12. Story Watchlist

Pedro can ask the agent to track any specific ongoing story across sessions -- a war, a negotiation, an IPO, a legislative process, a company situation. The agent monitors it and surfaces updates each morning without Pedro having to ask.

### How it works

- Stories are stored in `watchlist.yaml`
- Every morning during the 5 AM fetch, the agent runs a targeted search for each active watchlist item
- If there is a relevant update, it surfaces as a brief note inside the most relevant topic section (e.g. a geopolitical story appears in World News, a company story in Markets)
- If the update does not fit cleanly into any topic, it gets a short standalone "Watchlist Update" block at the end of the briefing
- If there is no new development, the agent says nothing -- no noise for quiet days

### Adding and removing stories

Pedro says it naturally in conversation:
- "Keep an eye on the SpaceX IPO" -- added to watchlist
- "Track the Gaza ceasefire talks" -- added
- "Drop the SpaceX story" / "Stop following [X]" -- removed
- "What am I currently tracking?" -- agent lists active watchlist items

### watchlist.yaml format

```yaml
watchlist:
  - id: spacex_ipo
    label: "SpaceX IPO"
    added: "2026-05-05"
    search_terms:
      - "SpaceX IPO timeline"
      - "SpaceX valuation listing"
    relevant_topics: ["markets_economy"]
    notes: "Targeting ~June 2026, valuation ~$1.5T"

  - id: gaza_ceasefire
    label: "Gaza ceasefire talks"
    added: "2026-05-05"
    search_terms:
      - "Gaza ceasefire negotiation"
      - "Hamas Israel talks"
    relevant_topics: ["general_world_news"]
    notes: ""
```

### End-of-session prompt (always)

At the end of every session:
```
"Anything specific you'd like me to keep an eye on over the coming days?"
```
Pedro can add a story, or say "no" / "nothing" to end cleanly.

---

## 13. Bi-weekly Spec Health Check

Every two weeks, at the end of a session, the agent performs a light review of the briefing spec and produces a short list of suggested updates. Pedro approves or ignores each one. The agent only edits the spec for items Pedro confirms.

### What it checks

| Check | Example flags |
|-------|--------------|
| Sources that changed or degraded | "The Free Press RSS URL appears broken for 5 days" |
| Companies or assets losing coverage relevance | "Vestas Wind Systems had zero relevant news for 3 weeks -- still worth tracking?" |
| Search terms underperforming | "BATT ETF search returns mostly unrelated results -- suggest refining" |
| New sources worth adding | "Ben's Bites newsletter now covers enterprise AI well -- worth adding to Topic 3 Tier 1?" |
| Topics with consistently thin results | "EU Policy section had fewer than 2 relevant items 8 out of 14 days -- adjust focus or search terms?" |

### Format of the health check output

```
Bi-weekly spec review -- [date]

Suggestions (approve or ignore each):

1. [Source] Daily Wire RSS feed returned zero results last 12 days.
   Suggest: remove from active sources, keep as web search fallback.
   Approve? [yes / no]

2. [Coverage] Vestas Wind Systems had no material news for 3 weeks.
   Suggest: move to "monitor quarterly" rather than daily search.
   Approve? [yes / no]

3. [Addition] The Free Press now has a dedicated international desk.
   Suggest: promote from Topic 1 Tier 2 to Tier 1.
   Approve? [yes / no]
```

### Cadence

- Every 14 days, at end of session
- Never interrupts the morning briefing itself -- always at session end
- If Pedro says "not now", skips to the next 14-day window

---

## 14. What Is NOT in Scope (yet)

- Speech-to-text for Pedro's voice responses (Phase 2)
- Mobile PWA -- Telegram + web dashboard is sufficient for Phase 1
- Persistent briefing history and archive search (Phase 2)
- Multi-language support (Phase 2)
- Push notifications beyond Telegram (Phase 2)

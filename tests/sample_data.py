"""
Realistic sample data for all 7 topics.
Used by test_render.py to test the HTML dashboard without any API calls.
"""

SAMPLE_TOPICS = {
    "investment_markets": {
        "id": "investment_markets",
        "title": "📈 Markets & Economy",
        "content": """SECTOR ALERTS

• **Magnificent 7 — Nvidia:** Nvidia reported Q1 datacenter revenue of $22.6B, up 427% year-on-year, beating consensus estimates by 18%. The company raised full-year guidance citing sustained hyperscaler demand for Blackwell chips — XLK (Tech/AI sector ETF) is up +2.3% vs SPY over the past month on this tailwind. [Reuters]

• **Gold & Silver:** Gold touched a fresh all-time high of $3,480/oz amid dollar weakness and central bank accumulation, with the People's Bank of China adding 8 tonnes for the 18th consecutive month. Silver followed, hitting $41.20/oz, bringing the Gold/Silver ratio to 84:1 — above the 80 threshold that historically signals silver undervaluation. [Reuters]

• **Oil & Gas (OPEC+):** OPEC+ agreed to extend production cuts of 2.2 million barrels/day through September, defying earlier speculation of a rollback. WTI held above $72 on the news. Cheniere Energy and Shell are direct beneficiaries of sustained LNG demand from Europe. [Financial Times]

• **Aerospace & Defense (ITA):** NATO member states confirmed aggregate defense spending reached 2.3% of collective GDP in 2025, the first time the alliance has exceeded the 2% threshold. ITA (Aerospace & Defense ETF) is the strongest performing sector this month at +3.4% vs SPY. [AP]

Why it matters: The Nvidia print confirms that AI capex is accelerating, not plateauing — the infrastructure build-out has years to run.""",
        "macro": {
            "sections": [
                {
                    "label": "BROAD INDICES",
                    "rows": [
                        {"name": "S&P 500", "price": "5,432.10", "change_pct": 0.54, "rsi": 62.3, "ma200_pct": 8.5, "pct_52w_high": -2.1, "key_indicator": "CAPE: ~39 — expensive (avg 17) | vs 200d MA: +8.5%", "signal": "caution"},
                        {"name": "Nasdaq 100", "price": "19,876.30", "change_pct": 0.91, "rsi": 65.1, "ma200_pct": 11.2, "pct_52w_high": -1.8, "key_indicator": "RSI: 65 — neutral | vs 200d MA: +11.2%", "signal": "neutral"},
                        {"name": "VWCE (All-World)", "price": "128.40", "change_pct": 0.48, "rsi": 58.7, "ma200_pct": 6.3, "pct_52w_high": -3.2, "key_indicator": "vs 200d MA: +6.3% — uptrend", "signal": "green"},
                    ]
                },
                {
                    "label": "MACRO",
                    "rows": [
                        {"name": "Gold", "price": "3,480.50", "change_pct": 1.20, "rsi": 71.2, "ma200_pct": 28.4, "pct_52w_high": -0.5, "key_indicator": "Real yield: -0.3% (bullish) | G/S ratio: 84", "signal": "green"},
                        {"name": "Silver", "price": "41.20", "change_pct": 2.10, "rsi": 68.5, "ma200_pct": 22.1, "pct_52w_high": -1.2, "key_indicator": "G/S ratio: 84 — BUY signal (>80 = silver cheap)", "signal": "green"},
                        {"name": "WTI Oil", "price": "72.40", "change_pct": 0.33, "rsi": 51.0, "ma200_pct": 2.1, "pct_52w_high": -18.3, "key_indicator": "Fair value — buy zone at $55-60", "signal": "neutral"},
                        {"name": "EUR/USD", "price": "1.0842", "change_pct": -0.21, "rsi": 44.2, "ma200_pct": -1.8, "pct_52w_high": -5.1, "key_indicator": "Rate differential driven", "signal": "neutral"},
                        {"name": "DXY (Dollar)", "price": "104.20", "change_pct": 0.18, "rsi": 53.1, "ma200_pct": 1.2, "pct_52w_high": -3.8, "key_indicator": "Strong $ = headwind for gold & EM", "signal": "neutral"},
                        {"name": "10Y Treasury", "price": "4.28", "change_pct": 0.03, "rsi": 55.0, "ma200_pct": None, "pct_52w_high": None, "key_indicator": "Real yield: +1.8% (bearish for gold) | Yield curve: +0.15% (normal)", "signal": "caution"},
                        {"name": "VIX (Fear)", "price": "18.40", "change_pct": -3.20, "rsi": 38.0, "ma200_pct": None, "pct_52w_high": None, "key_indicator": "18.4 — elevated (complacency <15, fear >25)", "signal": "neutral"},
                    ]
                },
                {
                    "label": "MAGNIFICENT 7",
                    "rows": [
                        {"name": "Apple",     "price": "210.40", "change_pct":  0.82, "rsi": 56.1, "ma200_pct":  8.2, "pct_52w_high":  -4.1, "key_indicator": "-4.1% below 52W high",      "signal": "green"},
                        {"name": "Microsoft", "price": "430.20", "change_pct":  0.62, "rsi": 58.2, "ma200_pct":  9.8, "pct_52w_high":  -5.4, "key_indicator": "-5.4% below 52W high",      "signal": "green"},
                        {"name": "Alphabet",  "price": "175.80", "change_pct":  1.10, "rsi": 60.3, "ma200_pct": 12.3, "pct_52w_high":  -3.2, "key_indicator": "-3.2% below 52W high",      "signal": "green"},
                        {"name": "Amazon",    "price": "195.60", "change_pct":  0.91, "rsi": 62.4, "ma200_pct": 14.1, "pct_52w_high":  -6.7, "key_indicator": "-6.7% below 52W high",      "signal": "green"},
                        {"name": "Nvidia",    "price": "880.30", "change_pct":  3.21, "rsi": 72.1, "ma200_pct": 42.3, "pct_52w_high":  -8.2, "key_indicator": "-8.2% below 52W high",      "signal": "caution"},
                        {"name": "Meta",      "price": "564.10", "change_pct":  0.91, "rsi": 61.4, "ma200_pct": 14.2, "pct_52w_high": -12.1, "key_indicator": "-12.1% below 52W high",     "signal": "green"},
                        {"name": "Tesla",     "price": "280.50", "change_pct": -1.20, "rsi": 45.2, "ma200_pct": -3.4, "pct_52w_high": -31.2, "key_indicator": "-31.2% below 52W high",     "signal": "caution"},
                    ]
                },
                {
                    "label": "SECTOR PULSE",
                    "rows": [
                        {"name": "Tech / AI (XLK)",           "price": "205.40", "change_pct":  1.20, "rsi": 62.1, "ma200_pct": 10.4, "pct_52w_high":  -3.8, "key_indicator": "+2.3% vs SPY (1M) — outperforming market",  "signal": "green"},
                        {"name": "Energy (XLE)",               "price":  "88.20", "change_pct": -0.40, "rsi": 47.8, "ma200_pct": -2.1, "pct_52w_high": -12.4, "key_indicator": "-3.1% vs SPY (1M) — underperforming market", "signal": "caution"},
                        {"name": "Oil & Gas (XOP)",            "price": "112.30", "change_pct": -0.80, "rsi": 44.2, "ma200_pct": -4.2, "pct_52w_high": -18.7, "key_indicator": "-4.8% vs SPY (1M) — underperforming market", "signal": "caution"},
                        {"name": "Aerospace & Defense (ITA)",  "price": "148.60", "change_pct":  1.80, "rsi": 65.3, "ma200_pct": 12.7, "pct_52w_high":  -2.1, "key_indicator": "+3.4% vs SPY (1M) — outperforming market",  "signal": "green"},
                        {"name": "FinTech (FINX)",             "price":  "45.20", "change_pct":  0.60, "rsi": 54.1, "ma200_pct":  3.2, "pct_52w_high":  -8.3, "key_indicator": "+0.3% vs SPY (1M) — in line with market",   "signal": "neutral"},
                        {"name": "Quantum Computing (QTUM)",   "price":  "38.40", "change_pct":  2.10, "rsi": 67.4, "ma200_pct": 18.4, "pct_52w_high":  -9.6, "key_indicator": "+5.2% vs SPY (1M) — outperforming market",  "signal": "green"},
                    ]
                },
                {
                    "label": "CRYPTO",
                    "rows": [
                        {"name": "Bitcoin (BTC)", "price": "$103,456", "change_pct": 2.10, "rsi": None, "ma200_pct": None, "pct_52w_high": None, "key_indicator": "Fear & Greed: 62 (Greed) | Day 383 post-halving", "signal": "green"},
                        {"name": "Ethereum (ETH)", "price": "$3,891", "change_pct": 1.40, "rsi": None, "ma200_pct": None, "pct_52w_high": None, "key_indicator": "ETH/BTC ratio trend — neutral", "signal": "neutral"},
                        {"name": "BTC Dominance", "price": "58.3%", "change_pct": None, "rsi": None, "ma200_pct": None, "pct_52w_high": None, "key_indicator": "58.3% — BTC dominant (>60% = altcoins depressed)", "signal": "neutral"},
                    ]
                },
            ],
            "extras": {
                "gs_ratio": 84.5,
                "real_yield": -0.30,
                "yield_curve": 0.15,
                "fear_greed": {"score": 62, "rating": "Greed"},
                "days_since_halving": 383,
                "btc_dominance": 58.3,
            }
        },
        "sources": [
            {"title": "Reuters Markets", "url": "https://www.reuters.com/markets"},
            {"title": "Financial Times", "url": "https://www.ft.com"},
            {"title": "AP Business", "url": "https://apnews.com/business"},
        ],
    },

    "general_world_news": {
        "id": "general_world_news",
        "title": "🌍 World News",
        "content": """• **Ukraine — Ceasefire Talks:** US and European mediators held a third round of indirect talks in Istanbul between Ukrainian and Russian delegations, with a proposed 90-day humanitarian corridor framework now on the table. Both sides have yet to confirm acceptance, but the framework represents the most concrete diplomatic progress since 2022. [Reuters]

• **India-Pakistan (Kashmir):** Following last week's cross-border skirmish in the Poonch district, both governments agreed to a UN-brokered communication channel to prevent further escalation. Markets in Mumbai recovered after an initial 2.1% intraday drop. [BBC World]

• **China (Economy):** The National Bureau of Statistics reported Q1 GDP growth of 4.7%, below the government's 5% target and consensus expectations of 5.1%. Beijing announced a $150B fiscal stimulus package focused on domestic consumption and infrastructure, effective immediately. [Financial Times]

• **EU-US Trade:** The European Commission and the US Trade Representative reached a preliminary agreement to suspend reciprocal tariffs on steel and aluminium for 12 months, pending a broader trade framework negotiation. The deal removes approximately €28B in annual bilateral trade friction. [Deutsche Welle]

• **Brazil (Amazon):** A landmark ruling by Brazil's Supreme Court upheld the government's authority to designate 14.6 million hectares of new protected Amazon territory, rejecting a congressional challenge backed by agribusiness interests. Scientists called it the most significant conservation ruling in 20 years. [Al Jazeera]

Why it matters: The China GDP miss and stimulus package are the most market-relevant signal today — a slower Chinese economy puts pressure on commodities and EM assets, but the stimulus response could reverse that within weeks.""",
        "sources": [
            {"title": "Reuters World", "url": "https://www.reuters.com/world"},
            {"title": "BBC World News", "url": "https://www.bbc.com/news/world"},
            {"title": "Financial Times", "url": "https://www.ft.com"},
            {"title": "Al Jazeera", "url": "https://www.aljazeera.com"},
            {"title": "Deutsche Welle", "url": "https://www.dw.com"},
        ],
    },

    "ai_productivity": {
        "id": "ai_productivity",
        "title": "⚡ AI & Productivity",
        "content": """• **Anthropic — Claude 4 Sonnet:** Anthropic released Claude 4 Sonnet to all Claude.ai and API users, featuring a 200K context window, improved instruction-following, and native PDF understanding. Claude Code users get access automatically via their existing subscription. Early benchmarks show 18% improvement over Claude 3.5 Sonnet on SWE-bench coding tasks. [anthropic.com]

• **Google DeepMind — Gemma 4 31B:** Google made Gemma 4 31B IT publicly available via Google AI Studio with Google Search grounding support. The model outperforms Llama 3 70B on MMLU while remaining free for API use. Available immediately under the Gemma license for commercial use. [ai.google.dev]

• **Cursor — v0.44 (Agent Mode):** Cursor shipped Agent Mode v0.44 with background task execution — the agent can now run tests, fix failures, and iterate without requiring your focus. Compatible with Claude 4 Sonnet and GPT-4o. Particularly useful for long refactoring sessions. [cursor.com/changelog]

• **Perplexity — Deep Research API:** Perplexity launched its Deep Research capability as a standalone API endpoint, allowing developers to trigger multi-step research tasks programmatically. Free tier includes 5 deep research queries/day. [perplexity.ai/blog]

Why it matters: Claude 4 Sonnet's release is the most significant shift today — it directly improves Pedro's primary coding tool (Claude Code) at no additional cost.""",
        "sources": [
            {"title": "Anthropic Blog", "url": "https://www.anthropic.com/news"},
            {"title": "Google AI Dev", "url": "https://ai.google.dev"},
            {"title": "Cursor Changelog", "url": "https://cursor.com/changelog"},
            {"title": "Perplexity Blog", "url": "https://www.perplexity.ai/blog"},
        ],
    },

    "portugal_policy": {
        "id": "portugal_policy",
        "title": "🇵🇹 Portugal Policy",
        "content": """• **IRS Jovem (Expanded):** The Assembleia da República approved an expansion of the IRS Jovem tax exemption scheme, raising the age limit from 35 to 40 and extending the full exemption period from 5 to 7 years. Workers under 40 in their first job now pay zero IRS for the first three years and 50% thereafter. Effective from the 2026 fiscal year. [Diário da República]

• **Golden Visa (Closure Confirmed):** The Government formally published the decree closing the real estate pathway of the Golden Visa programme to new applications, effective immediately. Existing applications submitted before the cutoff date will continue to be processed. The investment fund and capital transfer pathways remain open. [dre.pt]

• **Habitação — Arrendamento Acessível:** A new affordable rental framework was approved creating a state-backed guarantee for landlords who let properties at 30% below market rate to tenants earning up to €2,700/month. Landlords participating receive a 10-year IRS exemption on rental income. [portugal.gov.pt]

• **Energia — Autoconsumo Simplificado:** The DGEG published simplified rules for residential solar self-consumption up to 30kW, removing the requirement for prior grid operator approval for small installations. Registration is now handled via a single online portal within 10 business days. [Jornal de Negócios]

Why it matters: The IRS Jovem expansion is the most impactful measure for the professional class — it materially changes net income for workers under 40 across all sectors.""",
        "sources": [
            {"title": "Diário da República", "url": "https://dre.pt"},
            {"title": "Jornal de Negócios", "url": "https://www.jornaldenegocios.pt"},
            {"title": "Observador", "url": "https://observador.pt"},
            {"title": "portugal.gov.pt", "url": "https://www.portugal.gov.pt"},
        ],
    },

    "eu_policy": {
        "id": "eu_policy",
        "title": "🇪🇺 EU Policy",
        "content": """• **AI Act (Phase 2 — High-Risk Systems):** The European Commission confirmed that obligations for high-risk AI systems under the EU AI Act entered into force today for all systems deployed in critical infrastructure, education, employment, and law enforcement. Providers have 12 months to achieve compliance or face fines of up to 3% of global annual turnover. Portugal's CNPD will act as national supervisory authority. [EUR-Lex]

• **Capital Markets Union — Retail Investment Package:** The European Parliament approved the Retail Investment Strategy regulation, standardising cost disclosure for investment products across all 27 member states. From 2027, all retail investment products sold in the EU must display a standardised cost impact metric (€ per €10,000 invested). Relevant for Portuguese investors using Trading 212 and similar platforms. [europarl.europa.eu]

• **Energy — Gas Storage Obligation:** The Council of the EU formally extended the mandatory gas storage obligation at 90% capacity for all member states through winter 2026-27. Portugal is currently at 94% capacity, above the target. [consilium.europa.eu]

• **Digital Markets Act — Enforcement (Apple):** The European Commission issued a preliminary finding that Apple's App Store practices violate the Digital Markets Act, potentially triggering fines of up to 10% of global annual turnover (~$39B). Apple has 30 days to respond. [Politico Europe]

Why it matters: The AI Act's high-risk phase is the most consequential change today — any Portuguese company deploying AI in HR, credit scoring, or infrastructure must begin compliance processes now or face material liability.""",
        "sources": [
            {"title": "EUR-Lex", "url": "https://eur-lex.europa.eu"},
            {"title": "European Parliament", "url": "https://www.europarl.europa.eu"},
            {"title": "Politico Europe", "url": "https://www.politico.eu"},
            {"title": "Euractiv", "url": "https://www.euractiv.com"},
        ],
    },

    "us_policy": {
        "id": "us_policy",
        "title": "🇺🇸 US Policy",
        "content": """• **Executive Order — AI Infrastructure (National Security):** The President signed an executive order designating AI data centres as critical national infrastructure, directing the Departments of Energy and Defense to fast-track permitting for facilities exceeding 100MW. The order also establishes a $10B federal loan guarantee programme for qualifying projects. Direct beneficiaries include Constellation Energy, Vertiv, and major hyperscalers. [whitehouse.gov]

• **Reciprocal Tariffs — 90-Day Extension:** The administration extended the 90-day pause on reciprocal tariffs with 14 trading partners, including the EU, Japan, and South Korea, citing ongoing negotiations. The extension runs through August 2026. Markets interpreted the decision as a de-escalation signal. [Reuters]

• **Federal Reserve — Meeting Minutes:** Minutes from the May FOMC meeting revealed that a majority of members now view the current 4.25-4.50% rate range as "appropriately restrictive," with the first cut now expected no earlier than Q4 2026 absent a significant labour market deterioration. [federalreserve.gov]

• **CHIPS Act — Second Tranche:** The Department of Commerce disbursed the second $6.2B CHIPS Act tranche, with awards going to TSMC's Arizona facility ($2.1B), Samsung Austin ($1.4B), and Micron's Idaho plant ($2.7B). Production timelines were confirmed for 2026-2027. [AP Politics]

Why it matters: The AI infrastructure executive order is the most portfolio-relevant signal — it removes a key permitting bottleneck that has been constraining data centre build-out, directly benefiting Constellation Energy and Vertiv positions.""",
        "sources": [
            {"title": "White House", "url": "https://www.whitehouse.gov/presidential-actions"},
            {"title": "Federal Reserve", "url": "https://www.federalreserve.gov"},
            {"title": "Reuters Politics", "url": "https://www.reuters.com/world/us"},
            {"title": "AP Politics", "url": "https://apnews.com/politics"},
        ],
    },

    "ai_tools_snapshot": {
        "id": "ai_tools_snapshot",
        "title": "🛠️ AI Tools Snapshot",
        "content": """AI TOOLS SNAPSHOT
Categoria | Pedro usa | Melhor atual | Alternativa | Custo/Plano | Esforço migração | Switch? | Motivo
Código / Agentes | Claude Code | Claude Code | Cursor Agent | Incluído no Claude Pro | Nenhum | Optimal | Claude 4 Sonnet agora líder em SWE-bench; Claude Code é a escolha certa
Excel / Spreadsheets | Manual + ChatGPT | Claude.ai (artifacts) | Gemini Advanced | Incluído no Claude Pro | Baixo | Consider | Claude gera e edita spreadsheets diretamente em artifacts sem sair do chat
Presentations | Manual + ChatGPT | Gamma.app | Beautiful.ai | Free tier disponível | Médio | Consider | Gamma.app gera apresentações completas com design profissional em 60 segundos
Documents / Word | Manual + ChatGPT | Claude.ai | Notion AI | Incluído no Claude Pro | Baixo | Upgrade | Claude 4 Sonnet supera GPT-4o em escrita longa e estruturada segundo benchmarks recentes
LaTeX / Overleaf | Overleaf + ChatGPT | Overleaf + Claude | Overleaf nativo | Incluído no Claude Pro | Baixo | Consider | Claude compreende LaTeX melhor que GPT-4o; integração via API Overleaf possível
Knowledge Management | Notion | Notion AI | Obsidian + AI | Incluído no Notion Plus | Nenhum | Optimal | Notion AI agora integra modelos Claude diretamente; stack já é ótimo
Image Generation | Midjourney / DALL-E | Midjourney v7 | Ideogram 2.0 | $10/mês Midjourney Basic | Nenhum | Optimal | Midjourney v7 mantém liderança em qualidade fotorrealista e consistência de estilo
Research / Web Search | Perplexity | Perplexity Pro | Claude + Search | $20/mês Pro | Nenhum | Optimal | Perplexity Deep Research API agora disponível; stack atual é competitivo
Transcription / Audio | Whisper / Otter | Whisper v3 (local) | AssemblyAI | Free (local) | Baixo | Optimal | Whisper v3 local continua melhor custo-benefício para uso pessoal
Task Automation | Make / Zapier | Make | n8n (self-hosted) | Free tier Make | Nenhum | Optimal | Make free tier suficiente para maioria dos casos; n8n para controlo total

Takeaway: Migrar Documents/Word para Claude.ai é a mudança mais impactante disponível hoje — melhoria imediata de qualidade sem custo adicional dado o Claude Pro existente.""",
        "sources": [],
    },
}

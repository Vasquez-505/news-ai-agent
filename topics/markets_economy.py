import os
from datetime import datetime
import yfinance as yf
from pycoingecko import CoinGeckoAPI
from fredapi import Fred
from llm.provider import get_llm
from dotenv import load_dotenv

load_dotenv()

TICKERS = {
    "S&P 500":       "^GSPC",
    "Nasdaq 100":    "^NDX",
    "Gold (USD/oz)": "GC=F",
    "Silver (USD/oz)":"SI=F",
    "WTI Oil":       "CL=F",
    "EUR/USD":       "EURUSD=X",
    "10Y Treasury":  "^TNX",
}

PROMPT = """<role>
You are Pedro's morning intelligence briefing assistant. Pedro is a long-term investor with positions in ETFs, tech stocks, defense, energy, commodities, and crypto. He wants actionable market intelligence, not generic commentary.
</role>

<task>
Today is {date}. Using the live macro data below AND searching for today's financial news, write the MARKETS & ECONOMY section of this morning's briefing.
</task>

<live_macro_data>
{macro_data}

{btc_data}
</live_macro_data>

<output_structure>
Write two clearly labelled sections:

MACRO SNAPSHOT
For each indicator in the live data above, write one line:
[Indicator]: [Value] ([Change]) — [Signal: 🟢 BULLISH / 🟡 NEUTRAL / 🔴 CAUTION] — [One-line reason]

Signal thresholds:
- Equities/Crypto: 🟢 >+0.5% | 🟡 -0.5% to +0.5% | 🔴 <-0.5%
- 10Y Treasury: 🟢 falling yield | 🔴 rising yield above 4.5%
- Gold: 🟢 rising (safe haven demand) | 🟡 flat
- EUR/USD: context-dependent — note direction vs recent trend

SECTOR ALERTS
Search for today's material news across these sectors Pedro tracks:
- Equities & Indices (S&P 500, Nasdaq, Magnificent 7)
- Tech / AI stocks (Nvidia, Microsoft, Meta, Alphabet, Palantir, Vertiv, Micron)
- Gold & Silver (price drivers, central bank buying)
- Aerospace & Defense (NATO spending, earnings, contracts)
- Clean Energy & Nuclear (Cameco, Constellation Energy, uranium, IRA)
- Copper & Lithium (LME price, EV demand, BATT, 4COP)
- Oil & Gas (WTI, OPEC decisions, LNG exports)
- Crypto (BTC/ETH price action, regulation, dominance)

Only include sectors where something MATERIALLY relevant happened today.
For each sector alert:
• **[Sector — Company/Asset]:** [What happened — 1 sentence]. [Why it matters for Pedro's portfolio — 1 sentence]. [Source]

After both sections, write:
Why it matters: [One sentence — the single most actionable signal from today's markets]
</output_structure>

<quality_rules>
- Use the exact live numbers provided above for the macro snapshot — do not estimate or round
- Sector alerts: only include if there is a genuine material development (earnings beat/miss, major contract, significant price move >3%, regulatory action)
- Do not invent news — if a sector is quiet today, omit it
- Be specific about numbers: price levels, percentage moves, contract values
</quality_rules>"""


def _get_macro_data() -> str:
    lines = []
    for name, ticker in TICKERS.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2] if len(hist) > 1 else price
                change = ((price - prev) / prev) * 100
                lines.append(f"{name}: {price:.2f} ({change:+.2f}%)")
        except Exception as e:
            lines.append(f"{name}: unavailable ({e})")
    try:
        fred = Fred(api_key=os.getenv("FRED_API_KEY"))
        fed_rate = fred.get_series("FEDFUNDS").iloc[-1]
        lines.append(f"Fed Funds Rate: {fed_rate:.2f}%")
    except Exception:
        lines.append("Fed Funds Rate: unavailable")
    return "\n".join(lines)


def _get_btc_data() -> str:
    try:
        cg = CoinGeckoAPI()
        data = cg.get_price(
            ids="bitcoin,ethereum",
            vs_currencies="usd",
            include_24hr_change=True,
        )
        btc = data.get("bitcoin", {})
        eth = data.get("ethereum", {})
        global_data = cg.get_global()
        dominance = global_data.get("data", {}).get("market_cap_percentage", {}).get("btc", 0)
        return (
            f"BTC: ${btc.get('usd', 0):,.0f} ({btc.get('usd_24h_change', 0):+.1f}%)\n"
            f"ETH: ${eth.get('usd', 0):,.0f} ({eth.get('usd_24h_change', 0):+.1f}%)\n"
            f"BTC Dominance: {dominance:.1f}%"
        )
    except Exception as e:
        return f"Crypto data unavailable: {e}"


def fetch() -> dict:
    llm = get_llm()
    macro_data = _get_macro_data()
    btc_data = _get_btc_data()

    prompt = PROMPT.format(
        date=datetime.now().strftime("%A, %B %d, %Y"),
        macro_data=macro_data,
        btc_data=btc_data,
    )
    content, sources = llm.generate_with_search(prompt)

    return {
        "id": "investment_markets",
        "title": "📈 Markets & Economy",
        "content": content,
        "macro": {"raw": macro_data, "btc": btc_data},
        "sources": sources,
    }

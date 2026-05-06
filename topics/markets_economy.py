import os
import yfinance as yf
from pycoingecko import CoinGeckoAPI
from fredapi import Fred
from search.searcher import multi_search
from llm.provider import get_llm
from dotenv import load_dotenv

load_dotenv()

SECTOR_QUERIES = [
    "S&P 500 Nasdaq stock market performance today",
    "Nvidia Microsoft Magnificent 7 earnings news this week",
    "gold silver price today central bank",
    "defense spending NATO budget Lockheed RTX earnings",
    "nuclear energy uranium price IRA subsidies renewable",
    "copper LME price lithium EV sales battery",
    "WTI oil price OPEC decision LNG",
    "Bitcoin BTC crypto regulation news today",
]

TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Gold (USD/oz)": "GC=F",
    "Silver (USD/oz)": "SI=F",
    "WTI Oil": "CL=F",
    "EUR/USD": "EURUSD=X",
    "10Y Treasury": "^TNX",
}

PROMPT_TEMPLATE = """You are Pedro's morning intelligence briefing assistant.

Pedro tracks global markets for general market intelligence — not portfolio management.

Based on the MACRO DATA and SECTOR NEWS below, write the MARKETS & ECONOMY section.

FORMAT:
First write a compact macro snapshot table in this format (plain text, no markdown table):
MACRO SNAPSHOT
[Indicator] | [Value] | [Signal: BULLISH / NEUTRAL / CAUTION]

Then write sector alerts — only sectors with something materially relevant today:
SECTOR ALERTS
- **[Sector]:** [fact + what it means] [Source]

End with: "Why it matters: [one sentence — most actionable signal today]"

MACRO DATA:
{macro_data}

BTC DATA:
{btc_data}

SECTOR NEWS:
{sector_news}

Write the Markets & Economy section now:"""


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
            include_market_cap=True,
        )
        btc = data.get("bitcoin", {})
        eth = data.get("ethereum", {})
        global_data = cg.get_global()
        btc_dominance = global_data.get("data", {}).get("market_cap_percentage", {}).get("btc", 0)

        return (
            f"BTC: ${btc.get('usd', 0):,.0f} ({btc.get('usd_24h_change', 0):+.1f}%)\n"
            f"ETH: ${eth.get('usd', 0):,.0f} ({eth.get('usd_24h_change', 0):+.1f}%)\n"
            f"BTC Dominance: {btc_dominance:.1f}%"
        )
    except Exception as e:
        return f"Crypto data unavailable: {e}"


def fetch() -> dict:
    llm = get_llm()
    macro_data = _get_macro_data()
    btc_data = _get_btc_data()
    results = multi_search(SECTOR_QUERIES, max_per_query=2)

    sector_news = "\n\n".join(
        f"Source: {r['title']} ({r['url']})\n{r['content']}" for r in results
    )

    prompt = PROMPT_TEMPLATE.format(
        macro_data=macro_data,
        btc_data=btc_data,
        sector_news=sector_news,
    )
    summary = llm.generate(prompt)

    return {
        "id": "investment_markets",
        "title": "📈 Markets & Economy",
        "content": summary,
        "macro": {"raw": macro_data, "btc": btc_data},
        "sources": [{"title": r["title"], "url": r["url"]} for r in results],
    }

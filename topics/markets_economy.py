import os
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, datetime
from pycoingecko import CoinGeckoAPI
from fredapi import Fred
from llm.provider import get_llm
from dotenv import load_dotenv

load_dotenv()

# ── TICKER MAP ─────────────────────────────────────────────────────────────────
SECTIONS = {
    "BROAD INDICES": {
        "S&P 500":          "^GSPC",
        "Nasdaq 100":       "^NDX",
        "VWCE (All-World)": "VWCE.DE",
    },
    "MACRO": {
        "Gold":           "GC=F",
        "Silver":         "SI=F",
        "WTI Oil":        "CL=F",
        "EUR/USD":        "EURUSD=X",
        "DXY (Dollar)":   "DX-Y.NYB",
        "10Y Treasury":   "^TNX",
        "VIX (Fear)":     "^VIX",
    },
    "MAGNIFICENT 7": {
        "Apple":     "AAPL",
        "Microsoft": "MSFT",
        "Alphabet":  "GOOGL",
        "Amazon":    "AMZN",
        "Nvidia":    "NVDA",
        "Meta":      "META",
        "Tesla":     "TSLA",
    },
    "SECTOR PULSE": {
        "Tech / AI (XLK)":           "XLK",
        "Energy (XLE)":              "XLE",
        "Oil & Gas (XOP)":           "XOP",
        "Aerospace & Defense (ITA)": "ITA",
        "FinTech (FINX)":            "FINX",
        "Quantum Computing (QTUM)":  "QTUM",
    },
}

BTC_HALVING_4TH = date(2024, 4, 19)
BTC_HALVING_5TH = date(2028, 4, 20)  # estimated — ~210,000 blocks from block 840,000


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _calc_rsi(closes: pd.Series, period: int = 14) -> float | None:
    try:
        delta = closes.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        return round(float(val), 1) if not np.isnan(val) else None
    except Exception:
        return None


def _calc_ma200_pct(closes: pd.Series, current_price: float) -> float | None:
    try:
        ma200 = closes.rolling(200).mean().iloc[-1]
        if np.isnan(ma200) or ma200 == 0:
            return None
        return round(((current_price - ma200) / ma200) * 100, 1)
    except Exception:
        return None


def _calc_1w_return(closes: pd.Series) -> float | None:
    try:
        week = closes.tail(6)
        if len(week) < 2:
            return None
        return round(((float(week.iloc[-1]) - float(week.iloc[0])) / float(week.iloc[0])) * 100, 2)
    except Exception:
        return None


def _calc_1m_return(closes: pd.Series) -> float | None:
    try:
        month = closes.tail(22)
        if len(month) < 2:
            return None
        return round(((float(month.iloc[-1]) - float(month.iloc[0])) / float(month.iloc[0])) * 100, 2)
    except Exception:
        return None


_UNITLESS = {"^VIX", "DX-Y.NYB", "EURUSD=X"}  # indices / rates — no currency symbol
_EUR_TICKERS = {"VWCE.DE"}

def _fmt_price(price: float, ticker: str = "") -> str:
    try:
        if ticker == "^TNX":
            return f"{price:.2f}%"
        if ticker in _UNITLESS:
            return f"{price:.2f}"
        prefix = "€" if ticker in _EUR_TICKERS else "$"
        if price > 10000:
            return f"{prefix}{price:,.0f}"
        if price > 100:
            return f"{prefix}{price:,.2f}"
        return f"{prefix}{price:.4f}" if price < 5 else f"{prefix}{price:.2f}"
    except Exception:
        return "—"


# ── FRED DATA ──────────────────────────────────────────────────────────────────

def _get_fred_data() -> dict:
    result = {"real_yield": None, "yield_curve": None}
    try:
        fred = Fred(api_key=os.getenv("FRED_API_KEY"))
        try:
            result["real_yield"] = round(float(fred.get_series("DFII10").dropna().iloc[-1]), 2)
        except Exception:
            pass
        try:
            result["yield_curve"] = round(float(fred.get_series("T10Y2Y").dropna().iloc[-1]), 2)
        except Exception:
            pass
    except Exception:
        pass
    return result


# ── CNN FEAR & GREED ───────────────────────────────────────────────────────────

def _get_fear_greed() -> dict | None:
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        fg = resp.json().get("fear_and_greed", {})
        score = fg.get("score")
        if score is not None:
            return {"score": round(float(score), 1), "rating": fg.get("rating", "").title()}
    except Exception:
        pass
    return None


# ── CRYPTO (BTC + ETH + Dominance) ────────────────────────────────────────────

def _get_btc_dominance() -> float | None:
    """Fetch BTC dominance % — pycoingecko first, direct requests as fallback."""
    try:
        cg = CoinGeckoAPI()
        global_data = cg.get_global()
        # pycoingecko 3.x returns full response {"data": {...}}
        dom = global_data.get("data", {}).get("market_cap_percentage", {}).get("btc")
        # Some API versions strip the outer "data" wrapper
        if dom is None:
            dom = global_data.get("market_cap_percentage", {}).get("btc")
        if dom is not None:
            return round(float(dom), 1)
    except Exception:
        pass
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        dom = resp.json().get("data", {}).get("market_cap_percentage", {}).get("btc")
        if dom is not None:
            return round(float(dom), 1)
    except Exception:
        pass
    return None


def _get_crypto_rows(fear_greed: dict | None, days_since_halving: int) -> list:
    rows = []
    try:
        cg = CoinGeckoAPI()
        prices = cg.get_price(
            ids="bitcoin,ethereum",
            vs_currencies="usd",
            include_24hr_change=True,
            include_7d_change=True,
        )
        dominance = _get_btc_dominance()

        btc_price = prices.get("bitcoin", {}).get("usd")
        btc_chg   = prices.get("bitcoin", {}).get("usd_24h_change")
        eth_price = prices.get("ethereum", {}).get("usd")
        eth_chg   = prices.get("ethereum", {}).get("usd_24h_change")

        btc_chg_r = round(float(btc_chg), 2) if btc_chg is not None else None
        eth_chg_r = round(float(eth_chg), 2) if eth_chg is not None else None
        dom_r     = round(float(dominance), 1) if dominance is not None else None

        rows.append({
            "name": "Bitcoin (BTC)",
            "price": f"${btc_price:,.0f}" if btc_price else "—",
            "change_pct":   btc_chg_r,
            "week_return":  round(float(prices.get("bitcoin", {}).get("usd_7d_change", 0) or 0), 2),
            "month_return": None,
            "rsi": None, "ma200_pct": None,
        })
        rows.append({
            "name": "Ethereum (ETH)",
            "price": f"${eth_price:,.0f}" if eth_price else "—",
            "change_pct":   eth_chg_r,
            "week_return":  round(float(prices.get("ethereum", {}).get("usd_7d_change", 0) or 0), 2),
            "month_return": None,
            "rsi": None, "ma200_pct": None,
        })
        rows.append({
            "name": "BTC Dominance",
            "price": f"{dom_r:.1f}%" if dom_r is not None else "—",
            "change_pct": None, "week_return": None, "month_return": None,
            "rsi": None, "ma200_pct": None,
        })
    except Exception as e:
        rows.append({
            "name": "Bitcoin (BTC)", "price": "—",
            "change_pct": None, "week_return": None, "month_return": None,
            "rsi": None, "ma200_pct": None,
        })
    return rows


# ── MAIN SECTION FETCHER ───────────────────────────────────────────────────────

def _fetch_sections(fred_data: dict, gs_ratio: float | None, fear_greed: dict | None,
                    days_until_halving: int) -> list:
    sections_data = []

    for section_label, tickers in SECTIONS.items():
        rows = []

        for name, ticker in tickers.items():
            try:
                hist = yf.Ticker(ticker).history(period="1y")
                if hist.empty:
                    raise ValueError("No history returned")

                closes        = hist["Close"].dropna()
                current_price = float(closes.iloc[-1])
                prev_price    = float(closes.iloc[-2]) if len(closes) > 1 else current_price
                change_pct    = round(((current_price - prev_price) / prev_price) * 100, 2)

                rows.append({
                    "name":         name,
                    "price":        _fmt_price(current_price, ticker),
                    "change_pct":   change_pct,
                    "week_return":  _calc_1w_return(closes),
                    "month_return": _calc_1m_return(closes),
                    "rsi":          _calc_rsi(closes),
                    "ma200_pct":    _calc_ma200_pct(closes, current_price),
                })
            except Exception:
                rows.append({
                    "name": name, "price": "—",
                    "change_pct": None, "week_return": None, "month_return": None,
                    "rsi": None, "ma200_pct": None,
                })

        sections_data.append({"label": section_label, "rows": rows})

    return sections_data


# ── PROMPT HELPERS ─────────────────────────────────────────────────────────────

def _sections_to_prompt_text(sections_data: list, extras: dict) -> str:
    lines = []
    for sec in sections_data:
        lines.append(f"\n--- {sec['label']} ---")
        for r in sec["rows"]:
            chg  = f"({r['change_pct']:+.2f}%)" if r["change_pct"] is not None else ""
            w_s  = f"1W:{r['week_return']:+.2f}%"  if r.get("week_return")  is not None else ""
            m_s  = f"1M:{r['month_return']:+.2f}%" if r.get("month_return") is not None else ""
            rsi_s = f"RSI:{r['rsi']:.0f}" if r["rsi"] is not None else ""
            ma_s  = f"vs200MA:{r['ma200_pct']:+.1f}%" if r["ma200_pct"] is not None else ""
            parts = [p for p in [r["price"], chg, w_s, m_s, rsi_s, ma_s] if p]
            lines.append(f"  {r['name']}: {' | '.join(parts)}")

    lines.append("\n--- DERIVED METRICS ---")
    gs  = extras.get("gs_ratio")
    ry  = extras.get("real_yield")
    yc  = extras.get("yield_curve")
    fg  = extras.get("fear_greed")
    duh = extras.get("days_until_halving")
    if gs:  lines.append(f"  Gold/Silver Ratio: {gs:.1f}")
    if ry is not None: lines.append(f"  Real Yield (10Y TIPS): {ry:+.2f}%")
    if yc is not None: lines.append(f"  Yield Curve (10Y-2Y): {yc:+.2f}%")
    if fg:  lines.append(f"  CNN Fear & Greed: {fg['score']:.0f} ({fg['rating']})")
    if duh is not None: lines.append(f"  Days Until BTC Halving: {duh:,}")

    return "\n".join(lines)


PROMPT = """<role>
You are Pedro's morning intelligence briefing assistant. Pedro is a long-term investor with positions in ETFs, tech stocks, defense, energy, commodities, and crypto. He wants actionable market intelligence, not generic commentary.
</role>

<task>
Today is {date}. Using the live macro data below and the news search results already provided above, write the SECTOR ALERTS section of Pedro's morning briefing.
</task>

<live_macro_data>
{macro_data}
</live_macro_data>

<output_structure>
Write a SECTOR ALERTS section only (the macro snapshot table is rendered separately and already shows every price, % change, RSI, and signal):

SECTOR ALERTS
The table above already tells Pedro what moved. Your job is to tell him WHY — the news event, earnings result, geopolitical trigger, or regulatory action behind the move. Only write an alert when there is a specific news story driving a sector. Do not restate prices or % changes unless they are directly tied to explaining the news.

Sectors to monitor:
- Equities & Indices (S&P 500, Nasdaq, Magnificent 7: Apple, Microsoft, Alphabet, Amazon, Nvidia, Meta, Tesla)
- Gold & Silver (central bank buying, real yield shifts, safe-haven flows)
- Aerospace & Defense (ITA ETF — NATO spending commitments, contracts, earnings)
- FinTech & Digital Payments (FINX ETF — earnings, regulation, M&A)
- Quantum Computing (QTUM ETF — breakthroughs, funding rounds, partnerships)
- Clean Energy & Nuclear (uranium supply, IRA policy, datacenter power demand)
- Oil & Gas (OPEC decisions, supply disruptions, LNG export policy)
- Crypto (on-chain data, regulation, exchange news, ETF flows)

For each alert:
• **[Sector — Company/Asset]:** [The news event — what happened, who was involved, specific figures — 1–2 sentences]. [Why it matters for Pedro's portfolio or macro positioning — 1 sentence]. [Source]

After all alerts, write:
Why it matters: [One sentence — the single most actionable signal from today's markets]
</output_structure>

<quality_rules>
- The table already shows prices and % moves — do NOT open an alert with "X rose Y%" unless you are explaining the news cause of that move
- Only include a sector if there is a genuine news event: earnings beat/miss, contract award, regulatory ruling, geopolitical incident, major data release, analyst upgrade/downgrade with price target
- A price move alone — no matter how large — is not an alert. The alert is the story behind the move
- Do not invent news — if a sector is quiet today, omit it entirely
- If live price data shows errors or dashes, skip that sector silently — do not explain the errors
- Output only the final briefing text — no internal reasoning, no self-correction, no meta-commentary
- Be specific: company names, contract values, earnings figures vs estimates, regulator names, source names
</quality_rules>"""


# ── MAIN FETCH ─────────────────────────────────────────────────────────────────

def fetch() -> dict:
    llm = get_llm()

    fred_data          = _get_fred_data()
    fear_greed         = _get_fear_greed()
    days_until_halving = max(0, (BTC_HALVING_5TH - date.today()).days)

    # Gold/Silver ratio (pre-fetch for key indicators)
    gs_ratio = None
    try:
        gold_hist   = yf.Ticker("GC=F").history(period="2d")
        silver_hist = yf.Ticker("SI=F").history(period="2d")
        if not gold_hist.empty and not silver_hist.empty:
            gold_price   = float(gold_hist["Close"].iloc[-1])
            silver_price = float(silver_hist["Close"].iloc[-1])
            if silver_price > 0:
                gs_ratio = round(gold_price / silver_price, 1)
    except Exception:
        pass

    sections_data = _fetch_sections(fred_data, gs_ratio, fear_greed, days_until_halving)

    crypto_rows = _get_crypto_rows(fear_greed, days_until_halving)
    sections_data.append({"label": "CRYPTO", "rows": crypto_rows})

    btc_dominance = None
    for row in crypto_rows:
        if "dominance" in row["name"].lower():
            try:
                btc_dominance = float(row["price"].replace("%", ""))
            except Exception:
                pass

    extras = {
        "gs_ratio":           gs_ratio,
        "real_yield":         fred_data.get("real_yield"),
        "yield_curve":        fred_data.get("yield_curve"),
        "fear_greed":         fear_greed,
        "days_until_halving": days_until_halving,
        "btc_dominance":      btc_dominance,
    }

    macro_text = _sections_to_prompt_text(sections_data, extras)
    prompt = PROMPT.format(
        date=datetime.now().strftime("%A, %B %d, %Y"),
        macro_data=macro_text,
    )
    content, sources = llm.generate_with_search(prompt)

    return {
        "id":      "investment_markets",
        "title":   "Markets & Economy",
        "content": content,
        "macro": {
            "sections": sections_data,
            "extras":   extras,
        },
        "sources": sources,
    }

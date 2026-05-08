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


def _calc_52w_high_pct(closes: pd.Series, current_price: float) -> float | None:
    try:
        high_52w = closes.tail(252).max()
        if np.isnan(high_52w) or high_52w == 0:
            return None
        return round(((current_price - high_52w) / high_52w) * 100, 1)
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


# ── SIGNAL LOGIC ───────────────────────────────────────────────────────────────

def _signal(name: str, change_pct: float | None, rsi: float | None) -> str:
    n = name.lower()

    if "vix" in n:
        return "caution" if (change_pct is not None and change_pct > 10) else "neutral"

    if "treasury" in n or "10y" in n:
        if change_pct is not None:
            if change_pct > 0.05:
                return "caution"
            if change_pct < -0.05:
                return "green"
        return "neutral"

    if rsi is not None:
        if rsi > 70:
            return "caution"
        if rsi < 30:
            return "green"

    if change_pct is not None:
        if change_pct > 0.5:
            return "green"
        if change_pct < -0.5:
            return "caution"

    return "neutral"


# ── KEY INDICATOR TEXT ─────────────────────────────────────────────────────────

def _key_indicator(
    name: str,
    price: float | None,
    rsi: float | None,
    ma200_pct: float | None,
    pct_52w_high: float | None,
    real_yield: float | None,
    gs_ratio: float | None,
    fear_greed: dict | None,
    days_since_halving: int | None,
    btc_dominance: float | None,
    vs_spy_1m: float | None = None,
    section: str = "",
) -> str:
    n = name.lower()

    # ── MAGNIFICENT 7: key metric = % below 52-week high ──
    if section == "MAGNIFICENT 7":
        if pct_52w_high is not None:
            if pct_52w_high >= -1.0:
                return "Near 52W high"
            return f"{pct_52w_high:.1f}% below 52W high"
        return "—"

    # ── SECTOR PULSE: key metric = 1-month performance vs SPY ──
    if section == "SECTOR PULSE":
        if vs_spy_1m is not None:
            sign = "+" if vs_spy_1m >= 0 else ""
            label = "outperforming" if vs_spy_1m > 0.5 else ("underperforming" if vs_spy_1m < -0.5 else "in line with")
            return f"{sign}{vs_spy_1m:.1f}% vs SPY (1M) — {label} market"
        return "—"

    # ── BROAD INDICES ──
    if "s&p 500" in n:
        m = f"+{ma200_pct:.1f}% vs 200d MA" if ma200_pct is not None else ""
        return f"CAPE ~39 (avg 17 — expensive) | {m}" if m else "CAPE ~39 (avg 17 — expensive)"

    if "nasdaq" in n:
        r = f"RSI {rsi:.0f}" if rsi is not None else ""
        m = f"{ma200_pct:+.1f}% vs 200d MA" if ma200_pct is not None else ""
        return " | ".join(p for p in [r, m] if p) or "—"

    if "vwce" in n:
        m = f"{ma200_pct:+.1f}% vs 200d MA" if ma200_pct is not None else ""
        return m or "Global all-world ETF"

    # ── MACRO ──
    if "gold" in n and "silver" not in n:
        ry = (
            f"Real yield: {real_yield:+.2f}% ({'bullish' if real_yield < 0 else 'headwind'})"
            if real_yield is not None else ""
        )
        gs = f"G/S ratio: {gs_ratio:.0f}" if gs_ratio is not None else ""
        return " | ".join(p for p in [ry, gs] if p) or "—"

    if "silver" in n:
        if gs_ratio is not None:
            tag = "BUY zone (>80 = cheap)" if gs_ratio > 80 else "fair"
            return f"G/S ratio: {gs_ratio:.0f} — {tag}"
        return "—"

    if "wti" in n or "oil" in n:
        if price is not None:
            zone = (
                "in buy zone $55-60" if price < 60 else
                "fair value — buy zone $55-60" if price < 75 else
                "above buy zone"
            )
            return f"${price:.0f}/bbl — {zone}"
        return "—"

    if "vix" in n:
        if price is not None:
            label = (
                "PANIC — buy signal" if price > 30 else
                "fear — elevated" if price > 25 else
                "elevated" if price > 18 else
                "complacent — watch for reversal" if price < 15 else
                "normal"
            )
            return f"VIX {price:.1f} — {label}"
        return "—"

    if "treasury" in n or "10y" in n:
        return f"Real yield: {real_yield:+.2f}%" if real_yield is not None else "Yield watch"

    if "eur" in n:
        return "Rate differential driven"

    if "dxy" in n or "dollar" in n:
        return "Strong $ = headwind for gold & EM"

    # ── CRYPTO ──
    if "bitcoin" in n or ("btc" in n and "dominance" not in n):
        fg = (
            f"Fear & Greed: {fear_greed['score']:.0f} ({fear_greed['rating']})"
            if fear_greed else ""
        )
        dh = f"Day {days_since_halving} post-halving" if days_since_halving is not None else ""
        return " | ".join(p for p in [fg, dh] if p) or "—"

    if "ethereum" in n or "eth" in n:
        return "ETH/BTC ratio trend"

    if "dominance" in n:
        if btc_dominance is not None:
            label = (
                "altseason near (<45%)" if btc_dominance < 45 else
                "BTC dominant (>60%)" if btc_dominance > 60 else
                "neutral zone"
            )
            return f"{btc_dominance:.1f}% — {label}"
        return "—"

    # Fallback
    r = f"RSI {rsi:.0f}" if rsi is not None else ""
    m = f"{ma200_pct:+.1f}% vs 200d MA" if ma200_pct is not None else ""
    return " | ".join(p for p in [r, m] if p) or "—"


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

def _get_crypto_rows(fear_greed: dict | None, days_since_halving: int) -> list:
    rows = []
    try:
        cg = CoinGeckoAPI()
        prices = cg.get_price(
            ids="bitcoin,ethereum",
            vs_currencies="usd",
            include_24hr_change=True,
        )
        global_data = cg.get_global()
        dominance = global_data.get("data", {}).get("market_cap_percentage", {}).get("btc")

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
            "change_pct": btc_chg_r,
            "rsi": None, "ma200_pct": None, "pct_52w_high": None,
            "key_indicator": _key_indicator(
                "bitcoin", btc_price, None, None, None, None, None,
                fear_greed, days_since_halving, None
            ),
            "signal": _signal("bitcoin", btc_chg_r, None),
        })
        rows.append({
            "name": "Ethereum (ETH)",
            "price": f"${eth_price:,.0f}" if eth_price else "—",
            "change_pct": eth_chg_r,
            "rsi": None, "ma200_pct": None, "pct_52w_high": None,
            "key_indicator": _key_indicator("ethereum", eth_price, None, None, None, None, None, None, None, None),
            "signal": _signal("ethereum", eth_chg_r, None),
        })
        rows.append({
            "name": "BTC Dominance",
            "price": f"{dom_r:.1f}%" if dom_r is not None else "—",
            "change_pct": None,
            "rsi": None, "ma200_pct": None, "pct_52w_high": None,
            "key_indicator": _key_indicator("btc dominance", None, None, None, None, None, None, None, None, dom_r),
            "signal": "neutral",
        })
    except Exception as e:
        rows.append({
            "name": "Bitcoin (BTC)", "price": "—", "change_pct": None,
            "rsi": None, "ma200_pct": None, "pct_52w_high": None,
            "key_indicator": f"Fetch error: {e}", "signal": "neutral",
        })
    return rows


# ── MAIN SECTION FETCHER ───────────────────────────────────────────────────────

def _fetch_sections(fred_data: dict, gs_ratio: float | None, fear_greed: dict | None,
                    days_since_halving: int) -> list:
    # Pre-fetch SPY 1-month return for sector relative performance
    spy_1m_return = None
    try:
        spy_hist = yf.Ticker("SPY").history(period="1y")
        if not spy_hist.empty:
            spy_1m_return = _calc_1m_return(spy_hist["Close"].dropna())
    except Exception:
        pass

    sections_data = []

    for section_label, tickers in SECTIONS.items():
        rows = []
        is_sector_pulse = section_label == "SECTOR PULSE"

        for name, ticker in tickers.items():
            try:
                hist = yf.Ticker(ticker).history(period="1y")
                if hist.empty:
                    raise ValueError("No history returned")

                closes = hist["Close"].dropna()
                current_price = float(closes.iloc[-1])
                prev_price    = float(closes.iloc[-2]) if len(closes) > 1 else current_price
                change_pct    = round(((current_price - prev_price) / prev_price) * 100, 2)

                rsi          = _calc_rsi(closes)
                ma200_pct    = _calc_ma200_pct(closes, current_price)
                pct_52w_high = _calc_52w_high_pct(closes, current_price)

                # Sector vs SPY 1M
                vs_spy_1m = None
                if is_sector_pulse and spy_1m_return is not None:
                    etf_1m = _calc_1m_return(closes)
                    if etf_1m is not None:
                        vs_spy_1m = round(etf_1m - spy_1m_return, 2)

                key_ind = _key_indicator(
                    name, current_price, rsi, ma200_pct, pct_52w_high,
                    fred_data.get("real_yield"), gs_ratio, fear_greed,
                    days_since_halving, None,
                    vs_spy_1m=vs_spy_1m,
                    section=section_label,
                )
                sig = _signal(name, change_pct, rsi)

                rows.append({
                    "name":          name,
                    "price":         _fmt_price(current_price, ticker),
                    "change_pct":    change_pct,
                    "rsi":           rsi,
                    "ma200_pct":     ma200_pct,
                    "pct_52w_high":  pct_52w_high,
                    "key_indicator": key_ind,
                    "signal":        sig,
                })
            except Exception as e:
                rows.append({
                    "name": name, "price": "—", "change_pct": None,
                    "rsi": None, "ma200_pct": None, "pct_52w_high": None,
                    "key_indicator": f"Error: {e}", "signal": "neutral",
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
            rsi_s = f"RSI:{r['rsi']:.0f}" if r["rsi"] is not None else ""
            ma_s  = f"vs200MA:{r['ma200_pct']:+.1f}%" if r["ma200_pct"] is not None else ""
            parts = [p for p in [r["price"], chg, rsi_s, ma_s, r["key_indicator"]] if p]
            lines.append(f"  {r['name']}: {' | '.join(parts)}")

    lines.append("\n--- DERIVED METRICS ---")
    gs  = extras.get("gs_ratio")
    ry  = extras.get("real_yield")
    yc  = extras.get("yield_curve")
    fg  = extras.get("fear_greed")
    dsh = extras.get("days_since_halving")
    if gs:  lines.append(f"  Gold/Silver Ratio: {gs:.1f}")
    if ry is not None: lines.append(f"  Real Yield (10Y TIPS): {ry:+.2f}%")
    if yc is not None: lines.append(f"  Yield Curve (10Y-2Y): {yc:+.2f}%")
    if fg:  lines.append(f"  CNN Fear & Greed: {fg['score']:.0f} ({fg['rating']})")
    if dsh is not None: lines.append(f"  Days Since BTC Halving: {dsh}")

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
Write a SECTOR ALERTS section only (the macro snapshot table is rendered separately):

SECTOR ALERTS
Based on the search results and live data above, identify material developments across these sectors:
- Equities & Indices (S&P 500, Nasdaq, Magnificent 7: Apple, Microsoft, Alphabet, Amazon, Nvidia, Meta, Tesla)
- Gold & Silver (price drivers, central bank buying, real yield moves)
- Aerospace & Defense (ITA ETF — NATO spending, contracts, earnings)
- FinTech & Digital Payments (FINX ETF — earnings, regulation, M&A)
- Quantum Computing (QTUM ETF — breakthroughs, funding, partnerships)
- Clean Energy & Nuclear (uranium supply, IRA policy, datacenter power)
- Oil & Gas (WTI level, OPEC decisions, LNG exports)
- Crypto (BTC/ETH price action, on-chain data, regulation, dominance)

Only include sectors where something MATERIALLY relevant happened today.
For each sector alert:
• **[Sector — Company/Asset]:** [What happened — 1 sentence]. [Why it matters — 1 sentence]. [Source]

After all sector alerts, write:
Why it matters: [One sentence — the single most actionable signal from today's markets]
</output_structure>

<quality_rules>
- Use the exact live numbers from the macro data above — do not estimate or round
- Only include a sector if there is a genuine material development (earnings beat/miss, major contract, significant price move >3%, regulatory action)
- Do not invent news — if a sector is quiet today, omit it
- If live price data shows errors or dashes, skip that sector silently — do not explain the errors
- Output only the final briefing text — no internal reasoning, no self-correction, no meta-commentary
- Be specific: price levels, percentage moves, contract values, source names
</quality_rules>"""


# ── MAIN FETCH ─────────────────────────────────────────────────────────────────

def fetch() -> dict:
    llm = get_llm()

    fred_data        = _get_fred_data()
    fear_greed       = _get_fear_greed()
    days_since_halving = (date.today() - BTC_HALVING_4TH).days

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

    sections_data = _fetch_sections(fred_data, gs_ratio, fear_greed, days_since_halving)

    crypto_rows = _get_crypto_rows(fear_greed, days_since_halving)
    sections_data.append({"label": "CRYPTO", "rows": crypto_rows})

    btc_dominance = None
    for row in crypto_rows:
        if "dominance" in row["name"].lower():
            try:
                btc_dominance = float(row["price"].replace("%", ""))
            except Exception:
                pass

    extras = {
        "gs_ratio":          gs_ratio,
        "real_yield":        fred_data.get("real_yield"),
        "yield_curve":       fred_data.get("yield_curve"),
        "fear_greed":        fear_greed,
        "days_since_halving": days_since_halving,
        "btc_dominance":     btc_dominance,
    }

    macro_text = _sections_to_prompt_text(sections_data, extras)
    prompt = PROMPT.format(
        date=datetime.now().strftime("%A, %B %d, %Y"),
        macro_data=macro_text,
    )
    search_queries = [
        "stock market today S&P 500 Nasdaq performance",
        "macro economy Fed interest rates inflation today",
        "global markets bonds crypto news today",
    ]
    content, sources = llm.generate_with_search(prompt, search_queries=search_queries)

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

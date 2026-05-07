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
        "S&P 500":         "^GSPC",
        "Nasdaq 100":      "^NDX",
        "VWCE (All-World)":"VWCE.DE",
    },
    "MACRO": {
        "Gold":            "GC=F",
        "Silver":          "SI=F",
        "WTI Oil":         "CL=F",
        "EUR/USD":         "EURUSD=X",
        "DXY (Dollar)":    "DX-Y.NYB",
        "10Y Treasury":    "^TNX",
        "VIX (Fear)":      "^VIX",
    },
    "TECH / AI": {
        "Nvidia":          "NVDA",
        "Palantir":        "PLTR",
        "Vertiv":          "VRT",
        "Microsoft":       "MSFT",
        "Meta":            "META",
        "Micron":          "MU",
    },
    "ENERGY": {
        "Constellation Energy": "CEG",
        "Cameco":               "CCJ",
        "NextEra Energy":       "NEE",
        "Iberdrola":            "IBE.MC",
    },
}

BTC_HALVING_4TH = date(2024, 4, 19)

# ── HELPERS ────────────────────────────────────────────────────────────────────

def _calc_rsi(closes: pd.Series, period: int = 14) -> float | None:
    """Calculate RSI using Wilder's exponential smoothing."""
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
    """Return % above/below 200-day MA."""
    try:
        ma200 = closes.rolling(200).mean().iloc[-1]
        if np.isnan(ma200) or ma200 == 0:
            return None
        return round(((current_price - ma200) / ma200) * 100, 1)
    except Exception:
        return None


def _calc_52w_high_pct(closes: pd.Series, current_price: float) -> float | None:
    """Return % below 52-week high (negative value)."""
    try:
        high_52w = closes.tail(252).max()
        if np.isnan(high_52w) or high_52w == 0:
            return None
        return round(((current_price - high_52w) / high_52w) * 100, 1)
    except Exception:
        return None


def _fmt_price(price: float, ticker: str = "") -> str:
    """Format a price value sensibly."""
    try:
        if ticker in ("^TNX", "^VIX", "EURUSD=X", "DX-Y.NYB"):
            return f"{price:.2f}"
        if price > 10000:
            return f"{price:,.0f}"
        if price > 100:
            return f"{price:,.2f}"
        return f"{price:.4f}" if price < 5 else f"{price:.2f}"
    except Exception:
        return "—"


# ── SIGNAL LOGIC ───────────────────────────────────────────────────────────────

def _signal(name: str, change_pct: float | None, rsi: float | None) -> str:
    """Derive signal string from name, change % and RSI."""
    name_lower = name.lower()

    if "vix" in name_lower:
        if change_pct is not None and change_pct > 10:
            return "caution"
        return "neutral"

    if "treasury" in name_lower or "10y" in name_lower:
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
    real_yield: float | None,
    gs_ratio: float | None,
    fear_greed: dict | None,
    days_since_halving: int | None,
    btc_dominance: float | None,
) -> str:
    n = name.lower()

    def ma_str():
        if ma200_pct is not None:
            sign = "+" if ma200_pct >= 0 else ""
            return f"vs 200d MA: {sign}{ma200_pct:.1f}%"
        return ""

    def rsi_str():
        if rsi is not None:
            return f"RSI: {rsi:.0f}"
        return ""

    if "s&p 500" in n or "sp500" in n or "gspc" in n:
        ma = ma_str()
        return f"CAPE: ~39 — expensive (avg 17) | {ma}" if ma else "CAPE: ~39 — expensive (avg 17)"

    if "nasdaq" in n:
        ma = ma_str()
        r = rsi_str()
        parts = [p for p in [r, ma] if p]
        return " | ".join(parts) if parts else "—"

    if "vwce" in n:
        ma = ma_str()
        return f"{ma} — uptrend" if ma else "Global ETF"

    if "gold" in n and "silver" not in n:
        ry = f"Real yield: {real_yield:+.1f}% ({'bullish' if real_yield is not None and real_yield < 0 else 'bearish'})" if real_yield is not None else ""
        gs = f"G/S ratio: {gs_ratio:.0f}" if gs_ratio is not None else ""
        parts = [p for p in [ry, gs] if p]
        return " | ".join(parts) if parts else "—"

    if "silver" in n:
        if gs_ratio is not None:
            signal = "BUY signal (>80 = silver cheap)" if gs_ratio > 80 else "fair"
            return f"G/S ratio: {gs_ratio:.0f} — {signal}"
        return "—"

    if "wti" in n or "oil" in n:
        if price is not None:
            if price < 60:
                return f"In buy zone ($55-60)"
            if price < 75:
                return "Fair value — buy zone at $55-60"
            return "Above buy zone"
        return "—"

    if "vix" in n:
        if price is not None:
            if price > 30:
                label = "panic — buy signal"
            elif price > 25:
                label = "fear — elevated"
            elif price > 18:
                label = "elevated"
            elif price < 15:
                label = "complacent — watch for reversal"
            else:
                label = "normal"
            return f"{price:.1f} — {label}"
        return "—"

    if "treasury" in n or "10y" in n:
        ry = f"Real yield: {real_yield:+.1f}%" if real_yield is not None else ""
        return ry if ry else "Yield watch"

    if "eur" in n and "usd" in n:
        return "Rate differential driven"

    if "dxy" in n or "dollar" in n:
        return "Strong $ = headwind for gold & EM"

    if "nvidia" in n:
        r = rsi_str()
        ma = ma_str()
        parts = [p for p in [r, ma] if p]
        return " | ".join(parts) if parts else "—"

    if "palantir" in n:
        r = rsi_str()
        return f"{r} | Gov vs commercial growth key" if r else "Gov vs commercial growth key"

    if "vertiv" in n:
        r = rsi_str()
        return f"{r} | AI power infra backlog growing" if r else "AI power infra backlog growing"

    if "microsoft" in n:
        r = rsi_str()
        return f"{r} | Azure AI revenue growth key" if r else "Azure AI revenue growth key"

    if "meta" in n:
        r = rsi_str()
        return f"{r} | AI capex returns materialising" if r else "AI capex returns materialising"

    if "micron" in n:
        r = rsi_str()
        return f"{r} | HBM market share key" if r else "HBM market share key"

    if "constellation" in n:
        return "Nuclear + AI datacenter contracts"

    if "cameco" in n:
        return "Uranium demand from new reactors"

    if "nextera" in n:
        return "IRA subsidy dependency — policy risk"

    if "iberdrola" in n:
        return "Grid expansion pipeline solid"

    if "bitcoin" in n or "btc" in n and "dominance" not in n:
        fg = f"Fear & Greed: {fear_greed['score']:.0f} ({fear_greed['rating']})" if fear_greed else ""
        days = f"Day {days_since_halving} post-halving" if days_since_halving is not None else ""
        parts = [p for p in [fg, days] if p]
        return " | ".join(parts) if parts else "—"

    if "ethereum" in n or "eth" in n:
        return "ETH/BTC ratio trend — neutral"

    if "dominance" in n:
        if btc_dominance is not None:
            if btc_dominance < 45:
                label = "altseason near (<45%)"
            elif btc_dominance > 60:
                label = "BTC dominant (>60% = altcoins depressed)"
            else:
                label = "neutral zone"
            return f"{btc_dominance:.1f}% — {label}"
        return "—"

    # Generic fallback
    r = rsi_str()
    ma = ma_str()
    parts = [p for p in [r, ma] if p]
    return " | ".join(parts) if parts else "—"


# ── FRED DATA ──────────────────────────────────────────────────────────────────

def _get_fred_data() -> dict:
    result = {"real_yield": None, "yield_curve": None}
    try:
        fred = Fred(api_key=os.getenv("FRED_API_KEY"))
        try:
            series = fred.get_series("DFII10")
            result["real_yield"] = round(float(series.dropna().iloc[-1]), 2)
        except Exception:
            pass
        try:
            series = fred.get_series("T10Y2Y")
            result["yield_curve"] = round(float(series.dropna().iloc[-1]), 2)
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
        data = resp.json()
        fg = data.get("fear_and_greed", {})
        score = fg.get("score")
        rating = fg.get("rating", "").title()
        if score is not None:
            return {"score": round(float(score), 1), "rating": rating}
    except Exception:
        pass
    return None


# ── CRYPTO (BTC + ETH + Dominance) ────────────────────────────────────────────

def _get_crypto_rows(fear_greed: dict | None, days_since_halving: int) -> list:
    rows = []
    try:
        cg = CoinGeckoAPI()
        data = cg.get_price(
            ids="bitcoin,ethereum",
            vs_currencies="usd",
            include_24hr_change=True,
        )
        global_data = cg.get_global()
        dominance = global_data.get("data", {}).get("market_cap_percentage", {}).get("btc", None)

        btc_price = data.get("bitcoin", {}).get("usd")
        btc_chg = data.get("bitcoin", {}).get("usd_24h_change")
        eth_price = data.get("ethereum", {}).get("usd")
        eth_chg = data.get("ethereum", {}).get("usd_24h_change")

        btc_chg_r = round(float(btc_chg), 2) if btc_chg is not None else None
        eth_chg_r = round(float(eth_chg), 2) if eth_chg is not None else None

        btc_key = _key_indicator(
            "bitcoin", btc_price, None, None, None, None,
            fear_greed, days_since_halving, None
        )
        rows.append({
            "name": "Bitcoin (BTC)",
            "price": f"${btc_price:,.0f}" if btc_price else "—",
            "change_pct": btc_chg_r,
            "rsi": None,
            "ma200_pct": None,
            "pct_52w_high": None,
            "key_indicator": btc_key,
            "signal": _signal("bitcoin", btc_chg_r, None),
        })

        eth_key = _key_indicator(
            "ethereum", eth_price, None, None, None, None,
            None, None, None
        )
        rows.append({
            "name": "Ethereum (ETH)",
            "price": f"${eth_price:,.0f}" if eth_price else "—",
            "change_pct": eth_chg_r,
            "rsi": None,
            "ma200_pct": None,
            "pct_52w_high": None,
            "key_indicator": eth_key,
            "signal": _signal("ethereum", eth_chg_r, None),
        })

        dom_r = round(float(dominance), 1) if dominance is not None else None
        dom_key = _key_indicator(
            "btc dominance", None, None, None, None, None,
            None, None, dom_r
        )
        rows.append({
            "name": "BTC Dominance",
            "price": f"{dom_r:.1f}%" if dom_r is not None else "—",
            "change_pct": None,
            "rsi": None,
            "ma200_pct": None,
            "pct_52w_high": None,
            "key_indicator": dom_key,
            "signal": "neutral",
        })
    except Exception as e:
        rows.append({
            "name": "Bitcoin (BTC)",
            "price": "—", "change_pct": None, "rsi": None,
            "ma200_pct": None, "pct_52w_high": None,
            "key_indicator": f"Fetch error: {e}", "signal": "neutral",
        })
    return rows


# ── MAIN SECTION FETCHER ───────────────────────────────────────────────────────

def _fetch_sections(fred_data: dict, gs_ratio: float | None, fear_greed: dict | None,
                    days_since_halving: int) -> list:
    sections_data = []

    for section_label, tickers in SECTIONS.items():
        rows = []
        for name, ticker in tickers.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="1y")
                if hist.empty:
                    raise ValueError("No history returned")

                closes = hist["Close"].dropna()
                current_price = float(closes.iloc[-1])
                prev_price = float(closes.iloc[-2]) if len(closes) > 1 else current_price
                change_pct = round(((current_price - prev_price) / prev_price) * 100, 2)

                rsi = _calc_rsi(closes)
                ma200_pct = _calc_ma200_pct(closes, current_price)
                pct_52w_high = _calc_52w_high_pct(closes, current_price)

                key_ind = _key_indicator(
                    name, current_price, rsi, ma200_pct,
                    fred_data.get("real_yield"),
                    gs_ratio, fear_greed, days_since_halving, None
                )
                sig = _signal(name, change_pct, rsi)

                rows.append({
                    "name": name,
                    "price": _fmt_price(current_price, ticker),
                    "change_pct": change_pct,
                    "rsi": rsi,
                    "ma200_pct": ma200_pct,
                    "pct_52w_high": pct_52w_high,
                    "key_indicator": key_ind,
                    "signal": sig,
                })
            except Exception as e:
                rows.append({
                    "name": name,
                    "price": "—",
                    "change_pct": None,
                    "rsi": None,
                    "ma200_pct": None,
                    "pct_52w_high": None,
                    "key_indicator": f"Error: {e}",
                    "signal": "neutral",
                })

        sections_data.append({"label": section_label, "rows": rows})

    return sections_data


# ── PROMPT HELPERS ─────────────────────────────────────────────────────────────

def _sections_to_prompt_text(sections_data: list, extras: dict) -> str:
    lines = []
    for sec in sections_data:
        lines.append(f"\n--- {sec['label']} ---")
        for r in sec["rows"]:
            chg = f"({r['change_pct']:+.2f}%)" if r["change_pct"] is not None else ""
            rsi_s = f"RSI:{r['rsi']:.0f}" if r["rsi"] is not None else ""
            ma_s = (f"vs200MA:{r['ma200_pct']:+.1f}%" if r["ma200_pct"] is not None else "")
            parts = [p for p in [r["price"], chg, rsi_s, ma_s, r["key_indicator"]] if p]
            lines.append(f"  {r['name']}: {' | '.join(parts)}")

    lines.append("\n--- DERIVED METRICS ---")
    gs = extras.get("gs_ratio")
    ry = extras.get("real_yield")
    yc = extras.get("yield_curve")
    fg = extras.get("fear_greed")
    dsh = extras.get("days_since_halving")

    if gs:
        lines.append(f"  Gold/Silver Ratio: {gs:.1f}")
    if ry is not None:
        lines.append(f"  Real Yield (10Y TIPS): {ry:+.2f}%")
    if yc is not None:
        lines.append(f"  Yield Curve (10Y-2Y): {yc:+.2f}%")
    if fg:
        lines.append(f"  CNN Fear & Greed: {fg['score']:.0f} ({fg['rating']})")
    if dsh is not None:
        lines.append(f"  Days Since BTC Halving: {dsh}")

    return "\n".join(lines)


PROMPT = """<role>
You are Pedro's morning intelligence briefing assistant. Pedro is a long-term investor with positions in ETFs, tech stocks, defense, energy, commodities, and crypto. He wants actionable market intelligence, not generic commentary.
</role>

<task>
Today is {date}. Using the live macro data below AND searching for today's financial news, write the MARKETS & ECONOMY section of this morning's briefing.
</task>

<live_macro_data>
{macro_data}
</live_macro_data>

<output_structure>
Write a SECTOR ALERTS section only (the macro snapshot is rendered separately from live data):

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

After all sector alerts, write:
Why it matters: [One sentence — the single most actionable signal from today's markets]
</output_structure>

<quality_rules>
- Use the exact live numbers provided above for any references — do not estimate or round
- Sector alerts: only include if there is a genuine material development (earnings beat/miss, major contract, significant price move >3%, regulatory action)
- Do not invent news — if a sector is quiet today, omit it
- Be specific about numbers: price levels, percentage moves, contract values
</quality_rules>"""


# ── MAIN FETCH ─────────────────────────────────────────────────────────────────

def fetch() -> dict:
    llm = get_llm()

    # 1. FRED
    fred_data = _get_fred_data()

    # 2. Fear & Greed
    fear_greed = _get_fear_greed()

    # 3. Days since halving
    days_since_halving = (date.today() - BTC_HALVING_4TH).days

    # 4. Gold & Silver prices for G/S ratio (fetch early)
    gs_ratio = None
    try:
        gold_hist = yf.Ticker("GC=F").history(period="2d")
        silver_hist = yf.Ticker("SI=F").history(period="2d")
        if not gold_hist.empty and not silver_hist.empty:
            gold_price = float(gold_hist["Close"].iloc[-1])
            silver_price = float(silver_hist["Close"].iloc[-1])
            if silver_price > 0:
                gs_ratio = round(gold_price / silver_price, 1)
    except Exception:
        pass

    # 5. Fetch all yfinance sections
    sections_data = _fetch_sections(fred_data, gs_ratio, fear_greed, days_since_halving)

    # 6. Crypto rows
    crypto_rows = _get_crypto_rows(fear_greed, days_since_halving)
    sections_data.append({"label": "CRYPTO", "rows": crypto_rows})

    # 7. Extras dict
    btc_dominance = None
    for row in crypto_rows:
        if "dominance" in row["name"].lower():
            try:
                btc_dominance = float(row["price"].replace("%", ""))
            except Exception:
                pass

    extras = {
        "gs_ratio": gs_ratio,
        "real_yield": fred_data.get("real_yield"),
        "yield_curve": fred_data.get("yield_curve"),
        "fear_greed": fear_greed,
        "days_since_halving": days_since_halving,
        "btc_dominance": btc_dominance,
    }

    # 8. LLM prompt
    macro_text = _sections_to_prompt_text(sections_data, extras)
    prompt = PROMPT.format(
        date=datetime.now().strftime("%A, %B %d, %Y"),
        macro_data=macro_text,
    )
    content, sources = llm.generate_with_search(prompt)

    return {
        "id": "investment_markets",
        "title": "📈 Markets & Economy",
        "content": content,
        "macro": {
            "sections": sections_data,
            "extras": extras,
        },
        "sources": sources,
    }

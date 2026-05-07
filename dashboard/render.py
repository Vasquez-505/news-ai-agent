import re
import os
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


def _text_to_html(text: str) -> str:
    """Convert LLM plain text output to HTML paragraphs (newspaper style)."""
    if not text or not text.strip():
        return "<p>No content available.</p>"

    lines = text.strip().split("\n")
    html_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip section header lines that belong to the LLM's own structure
        if re.match(r'^(MACRO SNAPSHOT|SECTOR ALERTS|AI TOOLS SNAPSHOT|UNITED STATES POLICY|EU POLICY|PORTUGAL POLICY|WORLD NEWS|AI & PRODUCTIVITY)$', line, re.IGNORECASE):
            continue

        # "Why it matters:" becomes a pull-quote
        if line.lower().startswith("why it matters:"):
            rest = line[len("why it matters:"):].strip()
            rest = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', rest)
            html_parts.append(f'<div class="pull-quote">Why it matters: {rest}</div>')
            continue

        # Strip leading bullet chars
        if line.startswith(("- ", "• ", "* ")):
            line = line[2:]

        # Convert **bold** markdown
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)

        # Convert inline [Source Name] to styled cite spans
        line = re.sub(r'\[([^\]]+)\]', r'<span class="cite">[\1]</span>', line)

        html_parts.append(f"<p>{line}</p>")

    return "\n".join(html_parts) if html_parts else "<p>No content available.</p>"


def _signal_badge(change_pct: float, indicator: str = "") -> str:
    """Return an HTML signal badge based on % change and indicator type."""
    name_lower = indicator.lower()

    # 10Y Treasury: rising yield = caution
    if "treasury" in name_lower or "10y" in name_lower:
        if change_pct > 0.05:
            cls, label = "signal-red", "CAUTION"
        elif change_pct < -0.05:
            cls, label = "signal-green", "BULLISH"
        else:
            cls, label = "signal-neutral", "NEUTRAL"
    else:
        if change_pct > 0.5:
            cls, label = "signal-green", "BULLISH"
        elif change_pct < -0.5:
            cls, label = "signal-red", "CAUTION"
        else:
            cls, label = "signal-neutral", "NEUTRAL"

    return f'<span class="signal-badge {cls}">{label}</span>'


def _parse_macro_table_legacy(raw: str, btc: str) -> str:
    """Legacy: Build HTML <tr> rows for the old 4-column macro snapshot table."""
    rows = []

    def _row(name, value, change_str, badge):
        return (
            f"<tr>"
            f"<td>{name}</td>"
            f'<td style="font-family:var(--font-mono);">{value}</td>'
            f'<td style="font-family:var(--font-mono);">{change_str}</td>'
            f"<td>{badge}</td>"
            f"</tr>"
        )

    for line in (raw or "").strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Fed Funds Rate: 4.50%
        if "Fed Funds Rate:" in line:
            parts = line.split(":", 1)
            val = parts[1].strip() if len(parts) > 1 else "—"
            badge = f'<span class="signal-badge signal-neutral">INFO</span>'
            rows.append(_row("Fed Funds Rate", val, "—", badge))
            continue

        # Standard: "Name: 5432.12 (+0.54%)"
        m = re.match(r'^(.+?):\s*([\d,\.]+)\s*\(([+-][\d\.]+)%\)$', line)
        if m:
            name = m.group(1).strip()
            value = m.group(2)
            change_str = m.group(3) + "%"
            try:
                pct = float(m.group(3))
            except ValueError:
                pct = 0.0
            badge = _signal_badge(pct, name)
            rows.append(_row(name, value, change_str, badge))
            continue

        if "unavailable" in line.lower():
            name = line.split(":")[0].strip()
            badge = f'<span class="signal-badge signal-neutral">—</span>'
            rows.append(_row(name, "—", "—", badge))

    # BTC / ETH data
    for line in (btc or "").strip().split("\n"):
        line = line.strip()
        if not line or "unavailable" in line.lower():
            continue

        # "BTC: $103,456 (+2.1%)"
        m = re.match(r'^(BTC|ETH):\s*\$([\d,]+)\s*\(([+-][\d\.]+)%\)$', line)
        if m:
            name = m.group(1)
            value = f"${m.group(2)}"
            change_str = m.group(3) + "%"
            try:
                pct = float(m.group(3))
            except ValueError:
                pct = 0.0
            badge = _signal_badge(pct)
            rows.append(_row(name, value, change_str, badge))
            continue

        # "BTC Dominance: 58.3%"
        m2 = re.match(r'^BTC Dominance:\s*([\d\.]+)%$', line)
        if m2:
            badge = f'<span class="signal-badge signal-neutral">INFO</span>'
            rows.append(_row("BTC Dominance", m2.group(1) + "%", "—", badge))

    if not rows:
        return '<tr><td colspan="4">Market data unavailable</td></tr>'
    return "\n".join(rows)


# Keep the old name as an alias so any external callers still work
_parse_macro_table = _parse_macro_table_legacy


def _signal_badge_from_name(signal_str: str, indicator: str = "") -> str:
    """Map structured signal string to an HTML badge."""
    mapping = {
        "green":   ("signal-green",   "BULLISH"),
        "caution": ("signal-red",     "CAUTION"),
        "neutral": ("signal-neutral", "NEUTRAL"),
        "info":    ("signal-neutral", "INFO"),
    }
    cls, label = mapping.get(signal_str, ("signal-neutral", "NEUTRAL"))
    return f'<span class="signal-badge {cls}">{label}</span>'


def _build_macro_sections_html(sections_data: list, extras: dict) -> str:
    """
    Build HTML <tr> rows for the new 7-column macro table.
    Columns: Asset | Price | 24h Chg | RSI (14d) | vs 200d MA | Key Indicator | Signal
    """
    rows = []

    for section in sections_data:
        label = section.get("label", "")
        rows.append(
            f'<tr class="macro-section-header"><td colspan="7">{label}</td></tr>'
        )
        for r in section.get("rows", []):
            name = r.get("name", "—")
            price = r.get("price", "—")
            change_pct = r.get("change_pct")
            rsi = r.get("rsi")
            ma200_pct = r.get("ma200_pct")
            key_indicator = r.get("key_indicator", "—")
            signal_str = r.get("signal", "neutral")

            # 24h change cell
            if change_pct is not None:
                chg_val = f"{change_pct:+.2f}%"
                if change_pct > 0:
                    chg_html = f'<span class="chg-positive">{chg_val}</span>'
                elif change_pct < 0:
                    chg_html = f'<span class="chg-negative">{chg_val}</span>'
                else:
                    chg_html = f'<span class="chg-neutral">{chg_val}</span>'
            else:
                chg_html = '<span class="chg-neutral">—</span>'

            # RSI cell
            if rsi is not None:
                if rsi > 70:
                    rsi_html = f'<span class="rsi-overbought">{rsi:.1f} OVERBOUGHT</span>'
                elif rsi < 30:
                    rsi_html = f'<span class="rsi-oversold">{rsi:.1f} OVERSOLD</span>'
                else:
                    rsi_html = f"{rsi:.1f}"
            else:
                rsi_html = "—"

            # vs 200d MA cell
            if ma200_pct is not None:
                sign = "+" if ma200_pct >= 0 else ""
                ma_val = f"{sign}{ma200_pct:.1f}%"
                if ma200_pct > 0:
                    ma_html = f'<span class="chg-positive">{ma_val}</span>'
                elif ma200_pct < 0:
                    ma_html = f'<span class="chg-negative">{ma_val}</span>'
                else:
                    ma_html = ma_val
            else:
                ma_html = "—"

            badge = _signal_badge_from_name(signal_str, name)

            rows.append(
                f"<tr>"
                f'<td class="indicator-name">{name}</td>'
                f'<td style="font-family:var(--font-mono);">{price}</td>'
                f"<td>{chg_html}</td>"
                f"<td>{rsi_html}</td>"
                f"<td>{ma_html}</td>"
                f'<td class="key-ind-cell">{key_indicator}</td>'
                f"<td>{badge}</td>"
                f"</tr>"
            )

    if not rows:
        return '<tr><td colspan="7">Market data unavailable</td></tr>'
    return "\n".join(rows)


def _build_extras_bar_html(extras: dict) -> str:
    """Build the derived metrics bar HTML (chips) below the macro table."""
    if not extras:
        return ""

    chips = []

    gs = extras.get("gs_ratio")
    if gs is not None:
        chips.append(
            f'<div class="extras-chip">'
            f'<span class="extras-chip-label">Gold/Silver Ratio</span>'
            f'<span class="extras-chip-value">{gs:.1f}</span>'
            f'</div>'
        )

    ry = extras.get("real_yield")
    if ry is not None:
        sign = "+" if ry >= 0 else ""
        chips.append(
            f'<div class="extras-chip">'
            f'<span class="extras-chip-label">Real Yield (10Y)</span>'
            f'<span class="extras-chip-value">{sign}{ry:.2f}%</span>'
            f'</div>'
        )

    yc = extras.get("yield_curve")
    if yc is not None:
        sign = "+" if yc >= 0 else ""
        label = "normal" if yc >= 0 else "inverted"
        chips.append(
            f'<div class="extras-chip">'
            f'<span class="extras-chip-label">Yield Curve</span>'
            f'<span class="extras-chip-value">{sign}{yc:.2f}% ({label})</span>'
            f'</div>'
        )

    fg = extras.get("fear_greed")
    if fg:
        score = fg.get("score", "—")
        rating = fg.get("rating", "—")
        chips.append(
            f'<div class="extras-chip">'
            f'<span class="extras-chip-label">Fear &amp; Greed</span>'
            f'<span class="extras-chip-value">{score:.0f} — {rating}</span>'
            f'</div>'
        )

    dsh = extras.get("days_since_halving")
    if dsh is not None:
        chips.append(
            f'<div class="extras-chip">'
            f'<span class="extras-chip-label">Days Since BTC Halving</span>'
            f'<span class="extras-chip-value">{dsh}</span>'
            f'</div>'
        )

    return "\n".join(chips) if chips else ""


def _extract_sector_alerts(markets_text: str) -> str:
    """Extract SECTOR ALERTS portion from markets LLM output and return HTML."""
    if not markets_text:
        return "<p>No sector data available.</p>"

    lines = markets_text.strip().split("\n")
    in_alerts = False
    alert_lines = []

    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        if "SECTOR ALERTS" in upper:
            in_alerts = True
            continue
        # Stop if we somehow loop back into macro section
        if "MACRO SNAPSHOT" in upper and in_alerts:
            break
        if in_alerts and stripped:
            alert_lines.append(stripped)

    if not alert_lines:
        # No labeled section — convert entire content
        return _text_to_html(markets_text)

    return _text_to_html("\n".join(alert_lines))


def _parse_tools_table(content: str) -> tuple:
    """
    Parse LLM pipe-separated AI Tools table into (rows_html, takeaway_str).
    Expected format per row: Categoria | Pedro usa | Melhor atual | Alternativa | Custo | Esforco | Switch? | Motivo
    """
    SWITCH_MAP = {
        "optimal":    "switch-optimal",
        "consider":   "switch-consider",
        "upgrade":    "switch-upgrade",
        "not using":  "switch-notusing",
    }

    rows = []
    takeaway = ""
    header_seen = False

    for line in (content or "").strip().split("\n"):
        stripped = line.strip()

        if stripped.lower().startswith("takeaway:"):
            takeaway = stripped[len("takeaway:"):].strip()
            continue

        if "|" not in stripped:
            continue

        cells = [c.strip() for c in stripped.split("|")]

        # Detect and skip the header row
        if not header_seen:
            if cells[0].lower() in ("categoria", "category", "category"):
                header_seen = True
                continue
            header_seen = True  # first row is data even without explicit header

        if len(cells) < 7:
            continue

        cat      = cells[0]
        pedro    = cells[1]
        best     = cells[2]
        alt      = cells[3] if len(cells) > 3 else "—"
        custo    = cells[4] if len(cells) > 4 else "—"
        esforco  = cells[5] if len(cells) > 5 else "—"
        switch_v = cells[6] if len(cells) > 6 else "—"
        motivo   = cells[7] if len(cells) > 7 else "—"

        # Match switch value to CSS class
        switch_key = switch_v.lower()
        cls = next((v for k, v in SWITCH_MAP.items() if k in switch_key), "switch-notusing")
        switch_html = f'<span class="{cls}">{switch_v}</span>'

        rows.append(
            f"<tr>"
            f"<td><strong>{cat}</strong></td>"
            f"<td>{pedro}</td>"
            f"<td>{best}</td>"
            f"<td>{alt}</td>"
            f"<td>{custo}</td>"
            f"<td>{esforco}</td>"
            f"<td>{switch_html}</td>"
            f"<td>{motivo}</td>"
            f"</tr>"
        )

    rows_html = "\n".join(rows) if rows else '<tr><td colspan="8">Data unavailable</td></tr>'
    return rows_html, takeaway


def render(topics: dict, output_dir: str = "output", watchlist: list = None) -> str:
    """
    Render the newspaper HTML dashboard from fetched topic data.

    Args:
        topics: dict keyed by topic id, each value is the dict returned by topic.fetch()
        output_dir: directory where the HTML file will be written
        watchlist: optional list of {"label": str, "update": str} items

    Returns:
        Absolute path to the written HTML file.
    """
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    generated_at = now.strftime("%H:%M · %B %d, %Y")

    markets  = topics.get("investment_markets", {})
    world    = topics.get("general_world_news", {})
    ai       = topics.get("ai_productivity", {})
    portugal = topics.get("portugal_policy", {})
    eu       = topics.get("eu_policy", {})
    us       = topics.get("us_policy", {})
    tools    = topics.get("ai_tools_snapshot", {})

    macro_obj = markets.get("macro", {})
    tools_rows, tools_takeaway = _parse_tools_table(tools.get("content", ""))

    # New structured macro data (sections + extras)
    sections_data = macro_obj.get("sections")
    extras        = macro_obj.get("extras", {})

    if sections_data is not None:
        # New format: structured sections
        macro_table_rows_html = _build_macro_sections_html(sections_data, extras)
        macro_extras_html     = _build_extras_bar_html(extras)
    else:
        # Legacy fallback: parse old raw/btc strings
        macro_raw = macro_obj.get("raw", "")
        btc_raw   = macro_obj.get("btc", "")
        macro_table_rows_html = _parse_macro_table_legacy(macro_raw, btc_raw)
        macro_extras_html     = ""

    template_vars = {
        "date":           date_str,
        "generated_at":   generated_at,
        # Markets
        "macro_table_rows":  macro_table_rows_html,
        "macro_extras_html": macro_extras_html,
        "markets_content":   _extract_sector_alerts(markets.get("content", "")),
        "markets_sources":   markets.get("sources", []),
        # World News
        "world_news":         _text_to_html(world.get("content", "")),
        "world_news_sources": world.get("sources", []),
        # AI & Productivity
        "ai_content":  _text_to_html(ai.get("content", "")),
        "ai_sources":  ai.get("sources", []),
        # Portugal
        "portugal_content": _text_to_html(portugal.get("content", "")),
        "portugal_sources": portugal.get("sources", []),
        # EU Policy
        "eu_content": _text_to_html(eu.get("content", "")),
        "eu_sources": eu.get("sources", []),
        # US Policy
        "us_content": _text_to_html(us.get("content", "")),
        "us_sources": us.get("sources", []),
        # AI Tools
        "tools_table_rows": tools_rows,
        "tools_takeaway":   tools_takeaway,
        # Watchlist (optional)
        "watchlist": watchlist or [],
    }

    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=False)
    tmpl = env.get_template("template.html")
    html = tmpl.render(**template_vars)

    os.makedirs(output_dir, exist_ok=True)
    filename = f"briefing_{now.strftime('%Y-%m-%d')}.html"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path

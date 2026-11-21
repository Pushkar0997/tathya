"""SVG chart generators for Tathya (M1-CHT-01, M1-CHT-02, M1-CHT-03, plus magazine editorial visuals).

Standard library only. Emits deterministic, accessible inline SVG strings with no
JavaScript and no external assets. No geographic boundary maps are ever used (INV-8).
"""
from __future__ import annotations

import html
import json
import math
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TILE_CLASS_COLORS = {
    1: ("#FFFFFF", "#1B1346"),
    2: ("#B4A5EC", "#1B1346"),
    3: ("#6C58C8", "#FFFFFF"),
    4: ("#1B1346", "#FFFFFF"),
}

AREA_CHART_PALETTES = {
    "people": {
        "bg": "#2A0B1E",
        "fg": "#FFD3E0",
        "accent": "#FF6B9A",
        "highlight": "#FFB627",
        "grid": "#FFD3E0",
        "bar_muted": "#8A3356",
    },
    "planet": {
        "bg": "#0A3B2F",
        "fg": "#E3F5EA",
        "accent": "#C6E04B",
        "highlight": "#FFFFFF",
        "grid": "#E3F5EA",
        "bar_muted": "#2F755E",
    },
    "public-money": {
        "bg": "#0F1D3D",
        "fg": "#EAF0FF",
        "accent": "#F2B134",
        "highlight": "#FFFFFF",
        "grid": "#EAF0FF",
        "bar_muted": "#3B568F",
    },
    "industry": {
        "bg": "#1A2BD6",
        "fg": "#FFFFFF",
        "accent": "#FFE45E",
        "highlight": "#FF6A1F",
        "grid": "#FFFFFF",
        "bar_muted": "#5E6DF2",
    },
    "shared": {
        "bg": "#1B1346",
        "fg": "#E6E0FA",
        "accent": "#FFB627",
        "highlight": "#D81B60",
        "grid": "#FFFFFF",
        "bar_muted": "#4B3F8A",
    },
}


def format_number(value: int | float, unit: str = "") -> str:
    """Format a number keeping stored decimals; use Indian grouping for INR units (CONTRACT.md)."""
    text = format(Decimal(repr(value)), "f")
    if "." in text:
        int_part, dec_part = text.split(".", 1)
        dec_part = dec_part.rstrip("0")
    else:
        int_part, dec_part = text, ""

    sign = ""
    if int_part.startswith("-"):
        sign = "-"
        int_part = int_part[1:]

    is_inr = "inr" in unit.lower() or "rupee" in unit.lower()
    if len(int_part) > 3:
        if is_inr:
            last3 = int_part[-3:]
            rest = int_part[:-3]
            groups = []
            while len(rest) > 2:
                groups.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.append(rest)
            int_grouped = ",".join(reversed(groups)) + "," + last3
        else:
            groups = []
            rest = int_part
            while len(rest) > 3:
                groups.append(rest[-3:])
                rest = rest[:-3]
            if rest:
                groups.append(rest)
            int_grouped = ",".join(reversed(groups))
    else:
        int_grouped = int_part

    if dec_part:
        return f"{sign}{int_grouped}.{dec_part}"
    if isinstance(value, float) and value.is_integer() and not is_inr and len(int_part) <= 3:
        return f"{sign}{int_grouped}.0"
    return f"{sign}{int_grouped}"


def _nice_axis_max(max_val: float) -> float:
    """Compute a clean zero-based ceiling for editorial chart axes."""
    if max_val <= 0:
        return 1.0
    exp = math.floor(math.log10(max_val))
    base = 10.0 ** exp
    frac = max_val / base
    for mult in (1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0):
        if frac <= mult + 1e-9:
            return round(mult * base, max(0, -exp + 2))
    return round(10.0 * base, max(0, -exp + 2))


def _short_value(val: float, unit: str = "") -> str:
    """Compact axis/callout label preserving unit meaning."""
    u_low = unit.lower()
    if u_low.startswith("percent"):
        return f"{format_number(val, unit)}%"
    if u_low.startswith("billion"):
        return f"{format_number(val, unit)} bn"
    if u_low.startswith("million tonnes"):
        return f"{format_number(val, unit)} Mt"
    if u_low.startswith("tonnes per person"):
        return f"{format_number(val, unit)} t"
    if u_low.startswith("million usd"):
        if val >= 1000:
            return f"${val / 1000.0:.1f}B"
        return f"${format_number(val, unit)}M"
    if "crore inr" in u_low:
        return f"{format_number(val, unit)} Cr"
    return format_number(val, unit)


def _short_period(period: str) -> str:
    """Short readable period label for x-axis ticks (e.g. 2026-01-25 -> 2026)."""
    if len(period) == 10 and period[4] == "-" and period[7] == "-":
        return period[:4]
    return period


def line_chart(
    points: list[dict],
    *,
    unit: str = "",
    title: str = "Metric over time",
    preview: bool = False,
) -> str:
    """Return an inline SVG line chart for ordered points with y-axis starting at zero (M1-CHT-01)."""
    if not points:
        raise ValueError("line_chart requires at least one point")

    values = [float(p["value"]) for p in points]
    periods = [str(p["period"]) for p in points]
    has_sample = preview or any(p.get("status") == "sample" for p in points)

    max_val = max(values)
    y_max = max_val if max_val > 0 else 1.0

    x_left = 50.0
    x_right = 609.0
    y_top = 60.0
    y_bottom = 270.0
    plot_height = y_bottom - y_top
    plot_width = x_right - x_left

    n = len(points)
    coords: list[tuple[float, float]] = []
    for i, val in enumerate(values):
        if n == 1:
            x = (x_left + x_right) / 2.0
        else:
            x = x_left + (i / (n - 1)) * plot_width
        y = y_bottom - (max(val, 0.0) / y_max) * plot_height
        coords.append((round(x, 1), round(y, 1)))

    def fmt_coord(c: float) -> str:
        return str(int(c)) if c == int(c) else f"{c:.1f}"

    points_attr = " ".join(f"{fmt_coord(x)},{fmt_coord(y)}" for x, y in coords)
    last_x, last_y = coords[-1]

    first_period = html.escape(periods[0])
    last_period = html.escape(periods[-1])
    mid_period = html.escape(periods[n // 2]) if n >= 3 else ""

    aria_parts = [f"{title}: {periods[0]} to {periods[-1]}"]
    if unit:
        aria_parts.append(f"in {unit}")
    if has_sample:
        aria_parts.append("(SAMPLE data)")
    aria_label = html.escape(", ".join(aria_parts))

    max_label = html.escape(format_number(max_val, unit))

    lines = [
        f'<svg viewBox="0 0 640 320" class="chart-svg line-chart-svg" role="img" aria-label="{aria_label}">',
        '  <g stroke="#FFFFFF" opacity="0.15">',
        '    <line x1="50" y1="60" x2="610" y2="60"/>',
        '    <line x1="50" y1="140" x2="610" y2="140"/>',
        '    <line x1="50" y1="220" x2="610" y2="220"/>',
        '    <line x1="50" y1="270" x2="610" y2="270"/>',
        '  </g>',
        f'  <text x="42" y="64" text-anchor="end" font-size="12" fill="#E6E0FA">{max_label}</text>',
        '  <text x="42" y="274" text-anchor="end" font-size="12" fill="#E6E0FA">0</text>',
    ]
    if has_sample:
        lines.append(
            '  <text x="70" y="235" font-family="Playfair Display,Georgia,serif" '
            'font-weight="900" font-style="italic" font-size="96" fill="#FFB627" opacity="0.25">SAMPLE</text>'
        )
    lines.append(f'  <polyline fill="none" stroke="#FFB627" stroke-width="4" points="{points_attr}"/>')
    lines.append(f'  <circle cx="{fmt_coord(last_x)}" cy="{fmt_coord(last_y)}" r="8" fill="#D81B60"/>')
    lines.append(f'  <text x="50" y="304" font-size="14" fill="#E6E0FA">{first_period}</text>')
    if mid_period and n >= 3:
        lines.append(f'  <text x="316" y="304" font-size="14" fill="#E6E0FA">{mid_period}</text>')
    if n > 1:
        lines.append(f'  <text x="580" y="304" font-size="14" fill="#E6E0FA">{last_period}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def editorial_trend_chart(
    points: list[dict],
    *,
    unit: str = "",
    title: str = "Metric over time",
    area_id: str = "shared",
    preview: bool = False,
    grad_id: str = "trend-grad",
) -> str:
    """Rich editorial zero-based area-line SVG chart with gridlines, nodes, and direct callouts."""
    if not points:
        return ""
    if len(points) == 1:
        return editorial_bar_chart(points, unit=unit, title=title, area_id=area_id, preview=preview)

    pal = AREA_CHART_PALETTES.get(area_id, AREA_CHART_PALETTES["shared"])
    values = [float(p["value"]) for p in points]
    periods = [str(p["period"]) for p in points]
    has_sample = preview or any(p.get("status") == "sample" for p in points)

    max_val = max(values)
    y_max = _nice_axis_max(max_val * 1.08)

    x_left = 86.0
    x_right = 602.0
    y_top = 48.0
    y_bottom = 266.0
    plot_h = y_bottom - y_top
    plot_w = x_right - x_left

    n = len(points)
    coords: list[tuple[float, float]] = []
    for i, val in enumerate(values):
        x = x_left + (i / (n - 1)) * plot_w
        y = y_bottom - (max(val, 0.0) / y_max) * plot_h
        coords.append((round(x, 1), round(y, 1)))

    def fc(c: float) -> str:
        return str(int(c)) if c == int(c) else f"{c:.1f}"

    poly_pts = " ".join(f"{fc(x)},{fc(y)}" for x, y in coords)
    area_pts = f"{fc(coords[0][0])},{fc(y_bottom)} {poly_pts} {fc(coords[-1][0])},{fc(y_bottom)}"

    safe_grad = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in grad_id)
    aria = f"{title}: {periods[0]} to {periods[-1]}"
    if unit:
        aria += f" in {unit}"
    if has_sample:
        aria += " (SAMPLE data)"

    lines = [
        f'<svg viewBox="0 0 640 326" class="chart-svg line-chart-svg editorial-trend-svg" role="img" aria-label="{html.escape(aria)}">',
        "  <defs>",
        f'    <linearGradient id="{safe_grad}" x1="0" y1="0" x2="0" y2="1">',
        f'      <stop offset="0%" stop-color="{pal["accent"]}" stop-opacity="0.38"/>',
        f'      <stop offset="100%" stop-color="{pal["accent"]}" stop-opacity="0.02"/>',
        "    </linearGradient>",
        "  </defs>",
    ]

    for step_idx in range(4):
        frac = step_idx / 3.0
        gy = round(y_bottom - frac * plot_h, 1)
        tick_val = round(y_max * frac, 2)
        dash = "" if step_idx == 0 else ' stroke-dasharray="4 5"'
        op = "0.45" if step_idx == 0 else "0.18"
        lines.append(
            f'  <line x1="{fc(x_left)}" y1="{fc(gy)}" x2="{fc(x_right)}" y2="{fc(gy)}" '
            f'stroke="{pal["grid"]}" stroke-width="1" opacity="{op}"{dash}/>'
        )
        t_lbl = "0" if step_idx == 0 else _short_value(tick_val, unit)
        lines.append(
            f'  <text x="{fc(x_left - 10)}" y="{fc(gy + 4)}" text-anchor="end" '
            f'font-size="11.5" fill="{pal["fg"]}" opacity="0.82">{html.escape(t_lbl)}</text>'
        )

    if has_sample:
        lines.append(
            f'  <text x="90" y="232" font-family="Playfair Display,Georgia,serif" '
            f'font-weight="900" font-style="italic" font-size="92" fill="{pal["accent"]}" opacity="0.22">SAMPLE</text>'
        )

    lines.append(f'  <polygon points="{area_pts}" fill="url(#{safe_grad})"/>')
    lines.append(
        f'  <polyline fill="none" stroke="{pal["accent"]}" stroke-width="4" '
        f'stroke-linejoin="round" stroke-linecap="round" points="{poly_pts}"/>'
    )

    peak_idx = values.index(max_val)
    callout_indices = {0, n - 1}
    if n >= 4 and peak_idx not in callout_indices:
        callout_indices.add(peak_idx)

    for i, ((x, y), val, per) in enumerate(zip(coords, values, periods)):
        is_last = i == n - 1
        title_txt = html.escape(f"{per}: {format_number(val, unit)} {unit}".strip())
        if is_last:
            lines.append(f'  <circle cx="{fc(x)}" cy="{fc(y)}" r="13" fill="{pal["accent"]}" opacity="0.25"/>')
            lines.append(
                f'  <circle cx="{fc(x)}" cy="{fc(y)}" r="6.5" fill="{pal["highlight"]}" '
                f'stroke="{pal["bg"]}" stroke-width="2.5"><title>{title_txt}</title></circle>'
            )
        else:
            lines.append(
                f'  <circle cx="{fc(x)}" cy="{fc(y)}" r="4.5" fill="{pal["accent"]}" '
                f'stroke="{pal["bg"]}" stroke-width="2"><title>{title_txt}</title></circle>'
            )

        if i in callout_indices:
            lbl = html.escape(_short_value(val, unit))
            anchor = "start" if i == 0 else ("end" if is_last else "middle")
            lx = x + 4 if i == 0 else (x - 2 if is_last else x)
            ly = max(24.0, y - 16.0)
            weight = "800" if is_last else "700"
            fsize = "15" if is_last else "13"
            fill_c = "#FFFFFF" if is_last else pal["fg"]
            lines.append(
                f'  <text x="{fc(lx)}" y="{fc(ly)}" text-anchor="{anchor}" '
                f'font-size="{fsize}" font-weight="{weight}" fill="{fill_c}">{lbl}</text>'
            )

    if n <= 5:
        label_indices = list(range(n))
    else:
        label_indices = sorted({0, n // 3, (2 * n) // 3, n - 1})

    for idx in label_indices:
        x = coords[idx][0]
        anchor = "start" if idx == 0 else ("end" if idx == n - 1 else "middle")
        p_lbl = html.escape(_short_period(periods[idx]))
        lines.append(
            f'  <text x="{fc(x)}" y="302" text-anchor="{anchor}" font-size="13" '
            f'font-weight="600" fill="{pal["fg"]}" opacity="0.9">{p_lbl}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def editorial_bar_chart(
    points: list[dict],
    *,
    unit: str = "",
    title: str = "Comparison",
    area_id: str = "shared",
    preview: bool = False,
) -> str:
    """Editorial vertical column bar chart (2+ points) or calibrated single-value scale gauge (1 point)."""
    if not points:
        return ""

    pal = AREA_CHART_PALETTES.get(area_id, AREA_CHART_PALETTES["shared"])
    values = [float(p["value"]) for p in points]
    periods = [str(p["period"]) for p in points]
    has_sample = preview or any(p.get("status") == "sample" for p in points)

    def fc(c: float) -> str:
        return str(int(c)) if c == int(c) else f"{c:.1f}"

    if len(points) == 1:
        val = values[0]
        per = periods[0]
        scale_max = _nice_axis_max(val * 1.25)
        bar_x = 32.0
        bar_w_max = 576.0
        bar_y = 92.0
        bar_h = 56.0
        fill_w = max(12.0, round((max(val, 0.0) / scale_max) * bar_w_max, 1))
        val_lbl = html.escape(_short_value(val, unit))
        aria = f"{title}: {format_number(val, unit)} {unit} ({per}) on zero-based scale"

        lines = [
            f'<svg viewBox="0 0 640 210" class="chart-svg line-chart-svg editorial-scale-svg" role="img" aria-label="{html.escape(aria)}">',
            f'  <text x="{fc(bar_x)}" y="44" font-size="14" font-weight="700" fill="{pal["fg"]}" opacity="0.88">'
            f'{html.escape(per)} · {html.escape(unit)}</text>',
            f'  <text x="{fc(bar_x + bar_w_max)}" y="44" text-anchor="end" font-size="24" font-weight="800" fill="{pal["accent"]}">{val_lbl}</text>',
            f'  <rect x="{fc(bar_x)}" y="{fc(bar_y)}" width="{fc(bar_w_max)}" height="{fc(bar_h)}" rx="6" fill="{pal["grid"]}" opacity="0.14"/>',
            f'  <rect x="{fc(bar_x)}" y="{fc(bar_y)}" width="{fc(fill_w)}" height="{fc(bar_h)}" rx="6" fill="{pal["accent"]}"/>',
        ]
        for frac, anchor in ((0.0, "start"), (0.5, "middle"), (1.0, "end")):
            tx = round(bar_x + frac * bar_w_max, 1)
            tv = "0" if frac == 0.0 else _short_value(round(scale_max * frac, 2), unit)
            lines.append(
                f'  <line x1="{fc(tx)}" y1="{fc(bar_y + bar_h + 4)}" x2="{fc(tx)}" y2="{fc(bar_y + bar_h + 12)}" '
                f'stroke="{pal["fg"]}" opacity="0.45"/>'
            )
            lines.append(
                f'  <text x="{fc(tx)}" y="{fc(bar_y + bar_h + 30)}" text-anchor="{anchor}" font-size="12" fill="{pal["fg"]}" opacity="0.8">{html.escape(tv)}</text>'
            )
        lines.append("</svg>")
        return "\n".join(lines)

    max_val = max(values)
    y_max = _nice_axis_max(max_val * 1.12)
    x_left = 86.0
    x_right = 608.0
    y_top = 48.0
    y_bottom = 266.0
    plot_h = y_bottom - y_top
    plot_w = x_right - x_left
    n = len(points)

    slot_w = plot_w / n
    bar_w = min(84.0, max(24.0, slot_w * 0.56))

    aria = f"{title} bar comparison: {periods[0]} to {periods[-1]} in {unit}"
    if has_sample:
        aria += " (SAMPLE data)"

    lines = [
        f'<svg viewBox="0 0 640 326" class="chart-svg line-chart-svg editorial-bar-svg" role="img" aria-label="{html.escape(aria)}">',
    ]

    for step_idx in range(4):
        frac = step_idx / 3.0
        gy = round(y_bottom - frac * plot_h, 1)
        tick_val = round(y_max * frac, 2)
        dash = "" if step_idx == 0 else ' stroke-dasharray="4 5"'
        op = "0.45" if step_idx == 0 else "0.18"
        lines.append(
            f'  <line x1="{fc(x_left)}" y1="{fc(gy)}" x2="{fc(x_right)}" y2="{fc(gy)}" '
            f'stroke="{pal["grid"]}" stroke-width="1" opacity="{op}"{dash}/>'
        )
        t_lbl = "0" if step_idx == 0 else _short_value(tick_val, unit)
        lines.append(
            f'  <text x="{fc(x_left - 10)}" y="{fc(gy + 4)}" text-anchor="end" '
            f'font-size="11.5" fill="{pal["fg"]}" opacity="0.82">{html.escape(t_lbl)}</text>'
        )

    for i, (val, per) in enumerate(zip(values, periods)):
        is_last = i == n - 1
        cx = x_left + (i + 0.5) * slot_w
        bx = round(cx - bar_w / 2.0, 1)
        bh = max(4.0, round((max(val, 0.0) / y_max) * plot_h, 1))
        by = round(y_bottom - bh, 1)
        fill_c = pal["accent"] if is_last else pal["bar_muted"]
        stroke_attr = f' stroke="{pal["accent"]}" stroke-width="2"' if not is_last else ""
        title_txt = html.escape(f"{per}: {format_number(val, unit)} {unit}".strip())
        lines.append(
            f'  <rect x="{fc(bx)}" y="{fc(by)}" width="{fc(bar_w)}" height="{fc(bh)}" '
            f'rx="4" fill="{fill_c}"{stroke_attr}><title>{title_txt}</title></rect>'
        )
        v_lbl = html.escape(_short_value(val, unit))
        lines.append(
            f'  <text x="{fc(cx)}" y="{fc(max(24.0, by - 10.0))}" text-anchor="middle" '
            f'font-size="{15 if is_last else 13}" font-weight="{800 if is_last else 700}" '
            f'fill="{"#FFFFFF" if is_last else pal["fg"]}">{v_lbl}</text>'
        )
        p_lbl = html.escape(_short_period(per))
        lines.append(
            f'  <text x="{fc(cx)}" y="298" text-anchor="middle" font-size="13" '
            f'font-weight="600" fill="{pal["fg"]}" opacity="0.9">{p_lbl}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def editorial_ranked_bars(
    items: list[dict],
    *,
    unit: str = "",
    title: str = "Ranked comparison",
    area_id: str = "shared",
) -> str:
    """Horizontal zero-based ranked comparison bar chart for countries, states, or same-unit metrics.

    Each item dict requires: {"label": str, "value": float, "sub": str (optional)}.
    """
    if not items:
        return ""

    pal = AREA_CHART_PALETTES.get(area_id, AREA_CHART_PALETTES["shared"])
    sorted_items = sorted(items, key=lambda x: float(x["value"]), reverse=True)
    max_val = max(float(it["value"]) for it in sorted_items)
    scale_max = _nice_axis_max(max_val * 1.06)

    row_h = 54
    top_pad = 22
    bot_pad = 36
    svg_h = top_pad + len(sorted_items) * row_h + bot_pad
    bar_x = 185.0
    bar_max_w = 345.0

    def fc(c: float) -> str:
        return str(int(c)) if c == int(c) else f"{c:.1f}"

    aria = f"{title}: ranked comparison in {unit}"
    lines = [
        f'<svg viewBox="0 0 640 {svg_h}" class="chart-svg line-chart-svg editorial-ranked-svg" role="img" aria-label="{html.escape(aria)}">',
    ]

    axis_y = top_pad + len(sorted_items) * row_h
    for frac, anchor in ((0.0, "start"), (0.5, "middle"), (1.0, "end")):
        gx = round(bar_x + frac * bar_max_w, 1)
        dash_attr = "" if frac == 0.0 else ' stroke-dasharray="4 5"'
        op_val = "0.45" if frac == 0.0 else "0.16"
        lines.append(
            f'  <line x1="{fc(gx)}" y1="{top_pad - 6}" x2="{fc(gx)}" y2="{axis_y}" '
            f'stroke="{pal["grid"]}" opacity="{op_val}"{dash_attr}/>'
        )
        t_lbl = "0" if frac == 0.0 else _short_value(round(scale_max * frac, 2), unit)
        lines.append(
            f'  <text x="{fc(gx)}" y="{axis_y + 22}" text-anchor="{anchor}" '
            f'font-size="11.5" fill="{pal["fg"]}" opacity="0.8">{html.escape(t_lbl)}</text>'
        )

    for idx, it in enumerate(sorted_items):
        val = float(it["value"])
        lbl = str(it["label"])
        if len(lbl) > 24:
            lbl = lbl[:23] + "…"
        sub = str(it.get("sub", ""))
        y_row = top_pad + idx * row_h
        bar_y = y_row + 12
        bar_h = 26
        bw = max(6.0, round((max(val, 0.0) / scale_max) * bar_max_w, 1))
        is_top = idx == 0
        fill_c = pal["accent"] if is_top else pal["bar_muted"]
        stroke_attr = f' stroke="{pal["accent"]}" stroke-width="1.5"' if not is_top else ""
        title_txt = html.escape(f"{it['label']}: {format_number(val, unit)} {unit}".strip())

        lines.append(
            f'  <text x="{fc(bar_x - 12)}" y="{bar_y + 17}" text-anchor="end" '
            f'font-size="13.5" font-weight="{"800" if is_top else "600"}" fill="{"#FFFFFF" if is_top else pal["fg"]}">{html.escape(lbl)}</text>'
        )
        if sub:
            lines.append(
                f'  <text x="{fc(bar_x - 12)}" y="{bar_y + 32}" text-anchor="end" '
                f'font-size="10.5" fill="{pal["fg"]}" opacity="0.68">{html.escape(sub)}</text>'
            )
        lines.append(
            f'  <rect x="{fc(bar_x)}" y="{bar_y}" width="{fc(bar_max_w)}" height="{bar_h}" rx="4" fill="{pal["grid"]}" opacity="0.10"/>'
        )
        lines.append(
            f'  <rect x="{fc(bar_x)}" y="{bar_y}" width="{fc(bw)}" height="{bar_h}" rx="4" fill="{fill_c}"{stroke_attr}>'
            f"<title>{title_txt}</title></rect>"
        )
        val_txt = html.escape(_short_value(val, unit))
        lines.append(
            f'  <text x="{fc(bar_x + bar_max_w + 12)}" y="{bar_y + 18}" text-anchor="start" '
            f'font-size="14" font-weight="{"800" if is_top else "700"}" fill="{"#FFFFFF" if is_top else pal["fg"]}">{val_txt}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def editorial_waffle_grid(
    percent_value: float,
    *,
    label: str = "",
    area_id: str = "people",
) -> str:
    """10x10 editorial waffle proportion grid (100 cells) for percentage metrics."""
    pal = AREA_CHART_PALETTES.get(area_id, AREA_CHART_PALETTES["shared"])
    clamped = max(0.0, min(100.0, float(percent_value)))
    filled = int(round(clamped))

    cell = 20
    gap = 4
    step = cell + gap
    grid_w = 10 * step - gap
    aria = f"{label}: {format_number(clamped, 'percent')}% ({filled} out of 100 cells shaded)"

    lines = [
        f'<svg viewBox="0 0 {grid_w} {grid_w}" class="chart-svg waffle-grid-svg" role="img" aria-label="{html.escape(aria)}">',
    ]
    for idx in range(100):
        row = idx // 10
        col = idx % 10
        x = col * step
        y = row * step
        is_filled = idx < filled
        fill_c = pal["accent"] if is_filled else pal["grid"]
        op = "1" if is_filled else "0.16"
        lines.append(f'  <rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{fill_c}" opacity="{op}"/>')
    lines.append("</svg>")
    return "\n".join(lines)


def sparkline_svg(
    points: list[dict],
    *,
    area_id: str = "shared",
    width: int = 220,
    height: int = 52,
) -> str:
    """Compact decorative inline SVG sparkline for area tiles and measure rows."""
    if not points:
        return ""
    pal = AREA_CHART_PALETTES.get(area_id, AREA_CHART_PALETTES["shared"])
    values = [float(p["value"]) for p in points]

    if len(values) == 1:
        return (
            f'<svg viewBox="0 0 {width} {height}" class="sparkline-svg" aria-hidden="true">'
            f'<rect x="0" y="{height // 2 - 5}" width="{width}" height="10" rx="5" fill="{pal["grid"]}" opacity="0.18"/>'
            f'<rect x="0" y="{height // 2 - 5}" width="{int(width * 0.72)}" height="10" rx="5" fill="{pal["accent"]}"/>'
            f'<circle cx="{int(width * 0.72)}" cy="{height // 2}" r="6" fill="{pal["highlight"]}"/>'
            f"</svg>"
        )

    y_max = max(max(values), 1e-9)
    pad_x = 8.0
    pad_top = 8.0
    pad_bot = 6.0
    pw = width - 2 * pad_x
    ph = height - pad_top - pad_bot
    n = len(values)

    coords = []
    for i, v in enumerate(values):
        x = round(pad_x + (i / (n - 1)) * pw, 1)
        y = round(height - pad_bot - (max(v, 0.0) / y_max) * ph, 1)
        coords.append((x, y))

    pts_str = " ".join(f"{x},{y}" for x, y in coords)
    area_str = f"{coords[0][0]},{height - pad_bot} {pts_str} {coords[-1][0]},{height - pad_bot}"
    lx, ly = coords[-1]
    return (
        f'<svg viewBox="0 0 {width} {height}" class="sparkline-svg" aria-hidden="true">'
        f'<polygon points="{area_str}" fill="{pal["accent"]}" opacity="0.22"/>'
        f'<polyline fill="none" stroke="{pal["accent"]}" stroke-width="3" '
        f'stroke-linejoin="round" stroke-linecap="round" points="{pts_str}"/>'
        f'<circle cx="{lx}" cy="{ly}" r="5" fill="{pal["highlight"]}" stroke="{pal["bg"]}" stroke-width="1.5"/>'
        f"</svg>"
    )


def paired_scale_bars(
    first: dict | int | float,
    second: dict | int | float,
    *,
    unit: str = "",
    max_width: float = 560.0,
    preview: bool = False,
) -> str:
    """Return an inline SVG drawing two bars with widths proportional to their values on one shared scale (M1-CHT-02)."""
    if isinstance(first, dict):
        val_a = float(first["value"])
        label_a = str(first.get("label") or f"{first.get('geography', '')}, {first.get('period', '')}".strip(", "))
        unit_a = str(first.get("unit", unit))
        sample_a = first.get("status") == "sample"
    else:
        val_a = float(first)
        label_a = "First value"
        unit_a = unit
        sample_a = False

    if isinstance(second, dict):
        val_b = float(second["value"])
        label_b = str(second.get("label") or f"{second.get('geography', '')}, {second.get('period', '')}".strip(", "))
        unit_b = str(second.get("unit", unit))
        sample_b = second.get("status") == "sample"
    else:
        val_b = float(second)
        label_b = "Second value"
        unit_b = unit
        sample_b = False

    if unit_a and unit_b and unit_a != unit_b:
        raise ValueError(f"paired_scale_bars requires one shared unit, got '{unit_a}' and '{unit_b}'")

    shared_unit = unit_a or unit_b or unit
    if val_a < 0 or val_b < 0:
        raise ValueError("paired_scale_bars requires non-negative values")

    scale_max = max(val_a, val_b)
    if scale_max <= 0:
        width_a = 0.0
        width_b = 0.0
    else:
        width_a = round((val_a / scale_max) * max_width, 2)
        width_b = round((val_b / scale_max) * max_width, 2)

    def fmt_w(w: float) -> str:
        return str(int(w)) if w == int(w) else f"{w:.2f}".rstrip("0").rstrip(".")

    has_sample = preview or sample_a or sample_b
    aria = f"Paired scale comparison in {shared_unit or 'shared unit'}"
    if has_sample:
        aria += " (SAMPLE data)"

    text_a = html.escape(f"{label_a}: {format_number(val_a, shared_unit)} {shared_unit}".strip())
    text_b = html.escape(f"{label_b}: {format_number(val_b, shared_unit)} {shared_unit}".strip())

    lines = [
        f'<svg viewBox="0 0 640 140" class="chart-svg paired-scale-svg" role="img" aria-label="{html.escape(aria)}">',
        f'  <rect class="paired-bar paired-bar-1" x="20" y="20" width="{fmt_w(width_a)}" height="40" fill="#D81B60" data-value="{val_a}"/>',
        f'  <text x="20" y="14" font-size="13" fill="#1B1346">{text_a}</text>',
        f'  <rect class="paired-bar paired-bar-2" x="20" y="84" width="{fmt_w(width_b)}" height="40" fill="#FFB627" data-value="{val_b}"/>',
        f'  <text x="20" y="78" font-size="13" fill="#1B1346">{text_b}</text>',
        "</svg>",
    ]
    return "\n".join(lines)


def state_tile_grid(
    points: list[dict],
    *,
    unit: str = "",
    regions: list[dict] | None = None,
    preview: bool = False,
) -> str:
    """Return an inline SVG tile grid of Indian states and UTs (M1-CHT-03, INV-8).

    Contains ONLY rect, text, and title child elements inside the root svg element.
    """
    if regions is None:
        cfg = json.loads((ROOT / "config" / "in_states.json").read_text(encoding="utf-8"))
        regions = cfg["regions"]

    val_by_code: dict[str, float] = {}
    for p in points:
        geo = p.get("geography")
        if isinstance(geo, str) and geo.startswith("IN-") and isinstance(p.get("value"), (int, float)):
            val_by_code[geo] = float(p["value"])

    present_vals = list(val_by_code.values())
    if present_vals:
        min_v = min(present_vals)
        max_v = max(present_vals)
    else:
        min_v = 0.0
        max_v = 0.0
    span = max_v - min_v

    def shade_class(v: float | None) -> int:
        if v is None:
            return 0
        if span <= 0:
            return 1
        ratio = (v - min_v) / span
        if ratio < 0.25:
            return 1
        if ratio < 0.50:
            return 2
        if ratio < 0.75:
            return 3
        return 4

    states = [r for r in regions if r.get("kind") == "state" and r.get("tile")]
    uts = [r for r in regions if r.get("kind") == "union_territory"]

    tile_size = 52
    gap = 6
    step = tile_size + gap

    aria = "Tile grid of Indian states and union territories (not a map)"
    if preview or any(p.get("status") == "sample" for p in points):
        aria += ", SAMPLE data"

    lines = [
        f'<svg viewBox="0 0 520 430" class="chart-svg state-tile-grid-svg" role="img" aria-label="{html.escape(aria)}">',
    ]

    for st in states:
        row, col = st["tile"]
        code = st["code"]
        abbr = st["abbr"]
        name = st["name"]
        v = val_by_code.get(code)
        cls = shade_class(v)
        if cls in TILE_CLASS_COLORS:
            bg, fg = TILE_CLASS_COLORS[cls]
            cls_name = f"k{cls}"
        else:
            bg, fg = ("#F4F2FA", "#4B4570")
            cls_name = "k0"

        x = (col - 1) * step
        y = (row - 1) * step
        cx = x + tile_size // 2
        cy = y + tile_size // 2 + 5
        v_label = f"{format_number(v, unit)} {unit}".strip() if v is not None else "no data"
        title_text = html.escape(f"{name} ({abbr}): {v_label}")

        lines.append(
            f'  <rect class="tile state-tile {cls_name}" data-code="{html.escape(code)}" '
            f'data-abbr="{html.escape(abbr)}" data-row="{row}" data-col="{col}" data-class="{cls}" '
            f'x="{x}" y="{y}" width="{tile_size}" height="{tile_size}" fill="{bg}" stroke="#1B1346" stroke-width="1">'
            f"<title>{title_text}</title></rect>"
        )
        lines.append(
            f'  <text x="{cx}" y="{cy}" text-anchor="middle" font-size="13" font-weight="700" fill="{fg}">{html.escape(abbr)}</text>'
        )

    ut_y = 6 * step + 24
    for idx, ut in enumerate(uts):
        col = idx + 1
        code = ut["code"]
        abbr = ut["abbr"]
        name = ut["name"]
        v = val_by_code.get(code)
        cls = shade_class(v)
        if cls in TILE_CLASS_COLORS:
            bg, fg = TILE_CLASS_COLORS[cls]
            cls_name = f"k{cls}"
        else:
            bg, fg = ("#F4F2FA", "#4B4570")
            cls_name = "k0"

        x = idx * step
        cx = x + tile_size // 2
        cy = ut_y + tile_size // 2 + 5
        v_label = f"{format_number(v, unit)} {unit}".strip() if v is not None else "no data"
        title_text = html.escape(f"{name} ({abbr}, union territory): {v_label}")

        lines.append(
            f'  <rect class="tile ut-tile {cls_name}" data-code="{html.escape(code)}" '
            f'data-abbr="{html.escape(abbr)}" data-row="7" data-col="{col}" data-class="{cls}" '
            f'x="{x}" y="{ut_y}" width="{tile_size}" height="{tile_size}" fill="{bg}" stroke="#1B1346" stroke-width="1">'
            f"<title>{title_text}</title></rect>"
        )
        lines.append(
            f'  <text x="{cx}" y="{cy}" text-anchor="middle" font-size="13" font-weight="700" fill="{fg}">{html.escape(abbr)}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)

"""SVG chart generators for Tathya (M1-CHT-01, M1-CHT-02, M1-CHT-03).

Standard library only. Emits deterministic, accessible inline SVG strings with no
JavaScript and no external assets. No geographic boundary maps are ever used (INV-8).
"""
from __future__ import annotations

import html
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TILE_CLASS_COLORS = {
    1: ("#FFFFFF", "#1B1346"),
    2: ("#B4A5EC", "#1B1346"),
    3: ("#6C58C8", "#FFFFFF"),
    4: ("#1B1346", "#FFFFFF"),
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
    # If original value was a float with .0 (e.g. 8.0), preserve one decimal if unit is percent/billion/million
    if isinstance(value, float) and value.is_integer() and not is_inr and len(int_part) <= 3:
        return f"{sign}{int_grouped}.0"
    return f"{sign}{int_grouped}"


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
    y_bottom = 270.0  # y-axis zero baseline
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

    # Separate row beneath for Union Territories
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

"""Page view-model builders for Tathya (M1-PGE-01, M1-PGE-02, M1-STL-01, M2)."""
from __future__ import annotations

import json
import site as _stdlib_site
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_stdlib_site.__path__ = [str(ROOT / "site")]

from site import charts, staleness  # noqa: E402

AREA_ORDER = ["people", "planet", "public-money", "industry"]

AREA_META = {
    "people": {
        "id": "people",
        "label": "People",
        "tagline": "hunger, poverty and wealth",
        "tile_blurb": "Hunger, poverty and who holds the wealth.",
        "tile_count_class": "tile-count-people",
    },
    "planet": {
        "id": "planet",
        "label": "Planet",
        "tagline": "waste, farming and climate",
        "tile_blurb": "Textile and food waste, farming and climate.",
        "tile_count_class": "tile-count-planet",
    },
    "public-money": {
        "id": "public-money",
        "label": "Public money",
        "tagline": "budgets and outlays",
        "tile_blurb": "Budgets and outlays beside service indicators.",
        "tile_count_class": "tile-count-money",
    },
    "industry": {
        "id": "industry",
        "label": "Industry",
        "tagline": "AI and quantum, in the open",
        "tile_blurb": "Revenue, losses, hiring and layoffs in AI and quantum.",
        "tile_count_class": "tile-count-industry",
    },
}


def load_state_names() -> dict[str, dict]:
    cfg = json.loads((ROOT / "config" / "in_states.json").read_text(encoding="utf-8"))
    return {r["code"]: r for r in cfg["regions"]}


def format_geography(geo: str, state_map: dict[str, dict]) -> str:
    if geo == "WLD":
        return "World"
    if geo == "IND":
        return "India"
    if geo in state_map:
        return f"{state_map[geo]['name']} ({geo})"
    return geo


def format_period(period_kind: str, period: str) -> str:
    if period_kind == "financial_year":
        return f"FY {period}"
    return period


def format_period_long(period_kind: str, period: str) -> str:
    if period_kind == "financial_year":
        return f"FY {period}, financial year (April to March)"
    if period_kind == "calendar_year":
        return f"{period}, calendar year"
    return f"{period}, date"


def compact_figure_display(value: int | float, unit: str) -> str:
    formatted = charts.format_number(value, unit)
    u_low = unit.lower()
    if u_low.startswith("percent"):
        return f"{formatted}%"
    if u_low.startswith("million tonnes"):
        return f"{formatted} Mt"
    if u_low.startswith("billion"):
        return f"{formatted} bn"
    return formatted


def split_metric_title(title: str) -> tuple[str, str]:
    """Split a metric title into a bold first line and italic second line like design/reference/metric.html."""
    clean = title
    words = clean.split()
    if len(words) <= 1:
        return clean, ""
    if len(words) == 2:
        return words[0], words[1]
    mid = max(1, len(words) // 2)
    return " ".join(words[:mid]), " ".join(words[mid:])


def compute_series_delta(series_points: list[dict], unit: str) -> dict | None:
    """Compute a strictly factual arithmetic change summary between earliest and latest points."""
    if len(series_points) < 2:
        return None
    first = series_points[0]
    latest = series_points[-1]
    v0 = float(first["value"])
    v1 = float(latest["value"])
    diff = v1 - v0
    if abs(diff) < 1e-9:
        direction = "flat"
    elif diff > 0:
        direction = "up"
    else:
        direction = "down"

    sign = "+" if diff > 0 else ("-" if diff < 0 else "")
    u_low = unit.lower()
    if u_low.startswith("percent"):
        short_label = f"{sign}{abs(diff):.1f} pp"
    elif v0 > 0:
        pct = (diff / v0) * 100.0
        short_label = f"{sign}{abs(pct):.1f}%"
    else:
        short_label = f"{sign}{charts.format_number(abs(diff), unit)}"

    p0 = charts._short_period(str(first["period"]))
    p1 = charts._short_period(str(latest["period"]))
    ratio = round(v1 / v0, 1) if v0 > 0 and v1 > 0 else None
    ratio_str = f"{ratio:.1f}x" if ratio and ratio >= 1.5 else ""

    return {
        "first_period": p0,
        "latest_period": p1,
        "direction": direction,
        "short_label": short_label,
        "ratio_str": ratio_str,
        "full_label": f"{short_label} ({p0} to {p1})",
    }


def enrich_metric(doc: dict, build_date: date, state_map: dict[str, dict], preview: bool = False) -> dict:
    annotated = staleness.annotate_metric_staleness(doc, build_date)
    sources_by_id = {s["id"]: s for s in annotated.get("sources", [])}
    unit = annotated["unit"]
    area_id = annotated.get("area", "shared")
    months = annotated["stale_after_months"]

    enriched_points = []
    for idx, p in enumerate(annotated.get("points", [])):
        src = sources_by_id.get(p["source_id"], {})
        geo = p["geography"]
        p_kind = p["period_kind"]
        period = p["period"]
        val = p["value"]
        src_type = src.get("source_type", "primary")
        status = p["status"]
        is_state = isinstance(geo, str) and geo.startswith("IN-")

        pt_view = dict(p)
        pt_view.update({
            "index": idx,
            "formatted_value": charts.format_number(val, unit),
            "compact_value": compact_figure_display(val, unit),
            "unit": unit,
            "geography_label": format_geography(geo, state_map),
            "period_display": format_period(p_kind, period),
            "period_long": format_period_long(p_kind, period),
            "source": src,
            "source_type": src_type,
            "source_type_label": src_type.capitalize(),
            "source_badge": f"{src_type.capitalize()} source",
            "status_label": "SAMPLE" if status == "sample" else status.capitalize(),
            "is_sample": status == "sample",
            "is_state": is_state,
            "stale_after_months": months,
            "has_revision": bool(str(p.get("revision_note", "")).strip()),
            "revision_note": str(p.get("revision_note", "")).strip(),
        })
        enriched_points.append(pt_view)

    non_state_pts = [p for p in enriched_points if not p["is_state"]]
    state_pts = [p for p in enriched_points if p["is_state"]]

    # Choose headline point: latest WLD or IND or national non-state point; fallback to latest point
    if non_state_pts:
        wld_pts = [p for p in non_state_pts if p["geography"] == "WLD"]
        ind_pts = [p for p in non_state_pts if p["geography"] == "IND"]
        primary_series_pool = wld_pts or ind_pts or non_state_pts
        headline_geo = primary_series_pool[-1]["geography"]
        series_points = sorted(
            [p for p in non_state_pts if p["geography"] == headline_geo],
            key=lambda x: x["period"],
        )
        headline_point = series_points[-1]
    elif enriched_points:
        series_points = sorted(enriched_points, key=lambda x: (x["period"], x["geography"]))
        headline_point = series_points[-1]
    else:
        series_points = []
        headline_point = None

    line_svg = (
        charts.line_chart(series_points, unit=unit, title=annotated["title"], preview=preview)
        if series_points
        else ""
    )

    # Editorial charts: choose column bars for 2-4 point series, gradient trend for 5+ points, scale gauge for 1 point
    if len(series_points) >= 5:
        editorial_chart_svg = charts.editorial_trend_chart(
            series_points,
            unit=unit,
            title=annotated["title"],
            area_id=area_id,
            preview=preview,
            grad_id=f"grad-{annotated['id']}",
        )
        bar_chart_svg = charts.editorial_bar_chart(
            series_points,
            unit=unit,
            title=annotated["title"],
            area_id=area_id,
            preview=preview,
        )
        chart_kind_label = "Trajectory over time"
    elif 2 <= len(series_points) <= 4:
        editorial_chart_svg = charts.editorial_bar_chart(
            series_points,
            unit=unit,
            title=annotated["title"],
            area_id=area_id,
            preview=preview,
        )
        bar_chart_svg = charts.editorial_trend_chart(
            series_points,
            unit=unit,
            title=annotated["title"],
            area_id=area_id,
            preview=preview,
            grad_id=f"grad-{annotated['id']}",
        )
        chart_kind_label = "Period-by-period scale"
    elif len(series_points) == 1:
        editorial_chart_svg = charts.editorial_bar_chart(
            series_points,
            unit=unit,
            title=annotated["title"],
            area_id=area_id,
            preview=preview,
        )
        bar_chart_svg = ""
        chart_kind_label = "Verified benchmark"
    else:
        editorial_chart_svg = ""
        bar_chart_svg = ""
        chart_kind_label = ""

    spark_svg = charts.sparkline_svg(series_points, area_id=area_id) if series_points else ""
    series_delta = compute_series_delta(series_points, unit)

    if state_pts:
        latest_state_period = max(p["period"] for p in state_pts)
        latest_state_points = [p for p in state_pts if p["period"] == latest_state_period]
        tile_svg = charts.state_tile_grid(latest_state_points, unit=unit, preview=preview)
    else:
        latest_state_period = None
        latest_state_points = []
        tile_svg = ""

    # Points shown on the metric page: time-series points + latest state points (deduplicated preserving order)
    shown_points: list[dict] = []
    seen_indices: set[int] = set()
    if headline_point:
        shown_points.append(headline_point)
        seen_indices.add(headline_point["index"])
    for p in series_points:
        if p["index"] not in seen_indices:
            shown_points.append(p)
            seen_indices.add(p["index"])
    for p in latest_state_points:
        if p["index"] not in seen_indices:
            shown_points.append(p)
            seen_indices.add(p["index"])
    for p in enriched_points:
        if p["index"] not in seen_indices:
            shown_points.append(p)
            seen_indices.add(p["index"])

    title_line_1, title_line_2 = split_metric_title(annotated["title"])

    out = dict(annotated)
    out.update({
        "title_line_1": title_line_1,
        "title_line_2": title_line_2,
        "sources_by_id": sources_by_id,
        "points": enriched_points,
        "headline_point": headline_point,
        "series_points": series_points,
        "series_delta": series_delta,
        "state_points": latest_state_points,
        "latest_state_period": latest_state_period,
        "has_state_grid": bool(latest_state_points),
        "line_chart_svg": line_svg,
        "editorial_chart_svg": editorial_chart_svg,
        "bar_chart_svg": bar_chart_svg,
        "chart_kind_label": chart_kind_label,
        "sparkline_svg": spark_svg,
        "tile_grid_svg": tile_svg,
        "shown_points": shown_points,
        "any_stale": any(p["stale"] for p in enriched_points),
        "any_revision": any(p["has_revision"] for p in enriched_points),
    })
    return out


def select_paired_scale(metrics: list[dict], preview: bool = False) -> dict | None:
    """Select two comparable points in one shared unit for the home page paired scale (M1-CHT-02, M2-HOM-01).

    Priority:
    1. Two distinct points sharing both unit and period.
    2. Earliest vs. latest eligible points within the same metric (same unit, zero-based shared scale),
       preferring the series with the largest ratio so the visual contrast is clear.
    """
    allowed_statuses = {"verified", "sample"} if preview else {"verified"}

    # Group candidate points by (unit, period)
    by_unit_period: dict[tuple[str, str], list[tuple[dict, dict]]] = {}
    for m in metrics:
        unit = m["unit"]
        for p in m.get("points", []):
            if p["status"] in allowed_statuses:
                key = (unit, p["period"])
                by_unit_period.setdefault(key, []).append((m, p))

    chosen_pair: tuple[tuple[dict, dict], tuple[dict, dict]] | None = None
    for (unit, period), items in sorted(by_unit_period.items(), key=lambda kv: kv[0][1], reverse=True):
        if len(items) >= 2:
            sorted_items = sorted(items, key=lambda mp: float(mp[1]["value"]), reverse=True)
            first = sorted_items[0]
            second = next(
                (it for it in sorted_items[1:] if float(it[1]["value"]) != float(first[1]["value"]) and float(it[1]["value"]) > 0),
                sorted_items[1],
            )
            chosen_pair = (first, second)
            break

    # Fallback: compare earliest vs latest eligible point within the same metric (same unit, honest scale)
    if chosen_pair is None:
        best_ratio = 0.0
        for m in metrics:
            eligible = [p for p in m.get("series_points", []) if p["status"] in allowed_statuses and float(p["value"]) > 0]
            if len(eligible) >= 2:
                a, b = eligible[0], eligible[-1]
                va, vb = float(a["value"]), float(b["value"])
                hi, lo = (a, b) if va >= vb else (b, a)
                ratio = float(hi["value"]) / max(float(lo["value"]), 1e-9)
                if ratio > best_ratio:
                    best_ratio = ratio
                    chosen_pair = ((m, hi), (m, lo))

    if chosen_pair is None:
        return None

    (m1, p1), (m2, p2) = chosen_pair
    v1 = float(p1["value"])
    v2 = float(p2["value"])
    max_v = max(v1, v2, 1.0)
    flex_1 = round(max((v1 / max_v) * 5.0, 0.5), 2)
    flex_2 = round(max((v2 / max_v) * 5.0, 0.5), 2)
    ratio_val = round(v1 / v2, 1) if v2 > 0 else None
    ratio_label = f"{ratio_val:.1f}x" if ratio_val and ratio_val >= 1.1 else ""

    svg = charts.paired_scale_bars(
        {
            "value": v1,
            "label": f"{m1['title']} ({p1['geography_label']}, {p1['period_display']})",
            "unit": m1["unit"],
            "status": p1["status"],
        },
        {
            "value": v2,
            "label": f"{m2['title']} ({p2['geography_label']}, {p2['period_display']})",
            "unit": m2["unit"],
            "status": p2["status"],
        },
        unit=m1["unit"],
        preview=preview,
    )
    return {
        "unit": m1["unit"],
        "ratio_label": ratio_label,
        "first": {"metric": m1, "point": p1, "flex": flex_1},
        "second": {"metric": m2, "point": p2, "flex": flex_2},
        "svg": svg,
    }

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

COUNTRY_NAMES = {
    "WLD": "World",
    "IND": "India",
    "CHN": "China",
    "USA": "United States",
    "GBR": "United Kingdom",
    "BRA": "Brazil",
    "DEU": "Germany",
    "JPN": "Japan",
    "FRA": "France",
}

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
    if geo in COUNTRY_NAMES:
        return COUNTRY_NAMES[geo]
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
    if u_low.startswith("tonnes per person"):
        return f"{formatted} t"
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

    # Detect cross-geography comparison metrics (multiple countries in one latest period)
    geo_set = {p["geography"] for p in non_state_pts}
    comparison_points: list[dict] = []
    if len(geo_set) >= 2:
        latest_geo_period = max(p["period"] for p in non_state_pts)
        same_period_geos = [p for p in non_state_pts if p["period"] == latest_geo_period]
        if len({p["geography"] for p in same_period_geos}) >= 2:
            comparison_points = sorted(same_period_geos, key=lambda x: float(x["value"]), reverse=True)

    # Choose headline point: latest WLD or IND or highest comparison point
    if comparison_points and len(non_state_pts) == len(comparison_points):
        series_points = comparison_points
        headline_point = comparison_points[0]
    elif non_state_pts:
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

    is_geo_comparison = bool(comparison_points and len(non_state_pts) == len(comparison_points))

    # Choose the strongest editorial chart for the data shape
    if is_geo_comparison:
        ranked_items = [
            {"label": p["geography_label"], "value": float(p["value"]), "sub": p["period_display"]}
            for p in comparison_points
        ]
        editorial_chart_svg = charts.editorial_ranked_bars(
            ranked_items,
            unit=unit,
            title=annotated["title"],
            area_id=area_id,
        )
        bar_chart_svg = ""
        chart_kind_label = f"Country comparison · {comparison_points[0]['period_display']}"
        series_delta = None
        if len(comparison_points) >= 2 and float(comparison_points[-1]["value"]) > 0:
            ratio = float(comparison_points[0]["value"]) / float(comparison_points[-1]["value"])
            series_delta = {
                "first_period": comparison_points[-1]["geography_label"],
                "latest_period": comparison_points[0]["geography_label"],
                "direction": "up",
                "short_label": f"{ratio:.1f}x span",
                "ratio_str": f"{ratio:.1f}x",
                "full_label": f"{ratio:.1f}x highest to lowest ({comparison_points[0]['geography_label']} vs {comparison_points[-1]['geography_label']})",
            }
    elif len(series_points) >= 5:
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
        series_delta = compute_series_delta(series_points, unit)
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
        series_delta = compute_series_delta(series_points, unit)
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
        series_delta = None
    else:
        editorial_chart_svg = ""
        bar_chart_svg = ""
        chart_kind_label = ""
        series_delta = None

    # Editorial 10x10 waffle grid for percentage metrics
    waffle_svg = ""
    if headline_point and unit.lower().startswith("percent"):
        waffle_svg = charts.editorial_waffle_grid(
            float(headline_point["value"]),
            label=annotated["title"],
            area_id=area_id,
        )

    spark_svg = charts.sparkline_svg(series_points, area_id=area_id) if series_points else ""

    if state_pts:
        latest_state_period = max(p["period"] for p in state_pts)
        latest_state_points = [p for p in state_pts if p["period"] == latest_state_period]
        tile_svg = charts.state_tile_grid(latest_state_points, unit=unit, preview=preview)
        sorted_states = sorted(latest_state_points, key=lambda x: float(x["value"]), reverse=True)
        top_states = sorted_states[:5]
        bottom_states = list(reversed(sorted_states[-5:])) if len(sorted_states) >= 5 else []
    else:
        latest_state_period = None
        latest_state_points = []
        tile_svg = ""
        top_states = []
        bottom_states = []

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
        "is_geo_comparison": is_geo_comparison,
        "state_points": latest_state_points,
        "top_states": top_states,
        "bottom_states": bottom_states,
        "latest_state_period": latest_state_period,
        "has_state_grid": bool(latest_state_points),
        "line_chart_svg": line_svg,
        "editorial_chart_svg": editorial_chart_svg,
        "bar_chart_svg": bar_chart_svg,
        "waffle_svg": waffle_svg,
        "chart_kind_label": chart_kind_label,
        "sparkline_svg": spark_svg,
        "tile_grid_svg": tile_svg,
        "shown_points": shown_points,
        "any_stale": any(p["stale"] for p in enriched_points),
        "any_revision": any(p["has_revision"] for p in enriched_points),
    })
    return out


def build_area_comparison(area_id: str, area_metrics: list[dict]) -> dict | None:
    """Build an area-level multi-metric horizontal ranked bar visual when >=2 metrics share one unit."""
    by_unit: dict[str, list[dict]] = {}
    for m in area_metrics:
        if m.get("headline_point"):
            by_unit.setdefault(m["unit"], []).append(m)

    best_unit = None
    best_group: list[dict] = []
    for unit, group in by_unit.items():
        if len(group) >= 2 and len(group) > len(best_group):
            best_unit = unit
            best_group = group

    if not best_unit or len(best_group) < 2:
        return None

    items = [
        {
            "label": m["title"],
            "value": float(m["headline_point"]["value"]),
            "sub": f"{m['headline_point']['geography_label']} · {m['headline_point']['period_display']}",
        }
        for m in best_group
    ]
    svg = charts.editorial_ranked_bars(
        items,
        unit=best_unit,
        title=f"{AREA_META[area_id]['label']} metrics on one scale",
        area_id=area_id,
    )
    return {
        "unit": best_unit,
        "count": len(best_group),
        "svg": svg,
        "metrics": best_group,
    }


def select_paired_scale(metrics: list[dict], preview: bool = False) -> dict | None:
    """Select two comparable points in one shared unit for the home page paired scale (M1-CHT-02, M2-HOM-01).

    Priority:
    1. Two distinct metrics sharing both unit and period (preferring non-state national/world points).
    2. Two geographies in the same metric sharing unit and period.
    3. Earliest vs. latest eligible points within the same metric (same unit, zero-based shared scale).
    """
    allowed_statuses = {"verified", "sample"} if preview else {"verified"}

    by_unit_period: dict[tuple[str, str], list[tuple[dict, dict]]] = {}
    for m in metrics:
        unit = m["unit"]
        for p in m.get("points", []):
            if p["status"] in allowed_statuses and not p.get("is_state"):
                key = (unit, p["period"])
                by_unit_period.setdefault(key, []).append((m, p))

    chosen_pair: tuple[tuple[dict, dict], tuple[dict, dict]] | None = None

    # Priority 1: two DIFFERENT metrics sharing (unit, period)
    for (unit, period), items in sorted(by_unit_period.items(), key=lambda kv: kv[0][1], reverse=True):
        distinct_metrics: dict[str, tuple[dict, dict]] = {}
        for m, p in sorted(items, key=lambda mp: float(mp[1]["value"]), reverse=True):
            if m["id"] not in distinct_metrics and float(p["value"]) > 0:
                distinct_metrics[m["id"]] = (m, p)
        if len(distinct_metrics) >= 2:
            ranked = sorted(distinct_metrics.values(), key=lambda mp: float(mp[1]["value"]), reverse=True)
            chosen_pair = (ranked[0], ranked[1])
            break

    # Priority 2: two geographies in the same metric sharing (unit, period)
    if chosen_pair is None:
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

    # Priority 3: earliest vs latest eligible point in the same metric
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


def build_area_perspectives(area_id: str, area_metrics: list[dict]) -> list[dict]:
    """Build multi-perspective paired comparison boards derived strictly from verified metrics."""
    by_id = {m["id"]: m for m in area_metrics}
    boards: list[dict] = []

    if area_id == "public-money":
        sub_m = by_id.get("indian-state-subsidies")
        cap_m = by_id.get("indian-state-capital-outlay")
        if sub_m and cap_m:
            sub_states = {p["geography"]: p for p in sub_m.get("state_points", [])}
            cap_states = {p["geography"]: p for p in cap_m.get("state_points", [])}
            common = [g for g in sub_states if g in cap_states]
            common.sort(key=lambda g: float(sub_states[g]["value"]), reverse=True)
            top_states = common[:8]
            if len(top_states) >= 3:
                rows = []
                for g in top_states:
                    sp = sub_states[g]
                    cp = cap_states[g]
                    ratio = float(sp["value"]) / max(float(cp["value"]), 1e-9)
                    sub_lbl = f"Subsidies {ratio:.2f}x capex" if ratio >= 1.0 else f"Capex {1.0/ratio:.1f}x subsidies"
                    rows.append({
                        "label": sp["geography_label"],
                        "value_a": float(sp["value"]),
                        "value_b": float(cp["value"]),
                        "sub": sub_lbl,
                    })
                period_lbl = sub_m.get("latest_state_period") or "FY 2025-26"
                svg = charts.editorial_dual_bars(
                    rows,
                    series_a_label="Budgeted subsidies",
                    series_b_label="Capital outlay",
                    unit=sub_m["unit"],
                    title=f"State subsidies vs. capital outlay ({period_lbl})",
                    area_id=area_id,
                )
                boards.append({
                    "kicker": f"Fiscal lens · {period_lbl} · {sub_m['unit']}",
                    "title": "Subsidies vs. capital outlay by state",
                    "badge": f"Top {len(rows)} subsidy states",
                    "svg": svg,
                    "note": (
                        "Budgeted state subsidies alongside budgeted capital outlay on one zero-based crore-INR axis. "
                        "Source: Reserve Bank of India, State Finances: A Study of Budgets of 2025-26 (Statements 4 and 36)."
                    ),
                })

    elif area_id == "industry":
        # Perspective 1: Pure-play quantum revenue vs GAAP net loss
        quantum_pairs = [
            ("IonQ", "ionq-annual-revenue", "ionq-annual-net-loss"),
            ("D-Wave Quantum", "dwave-annual-revenue", "dwave-annual-net-loss"),
            ("Rigetti Computing", "rigetti-annual-revenue", "rigetti-annual-net-loss"),
        ]
        q_rows = []
        for label, rev_id, loss_id in quantum_pairs:
            rm = by_id.get(rev_id)
            lm = by_id.get(loss_id)
            if rm and lm and rm.get("headline_point") and lm.get("headline_point"):
                rv = float(rm["headline_point"]["value"])
                lv = float(lm["headline_point"]["value"])
                mult = lv / max(rv, 1e-9)
                q_rows.append({
                    "label": label,
                    "value_a": rv,
                    "value_b": lv,
                    "sub": f"{rm['headline_point']['period_display']} · loss {mult:.1f}x rev",
                })
        if len(q_rows) >= 2:
            svg = charts.editorial_dual_bars(
                q_rows,
                series_a_label="Annual revenue",
                series_b_label="GAAP net loss",
                unit="million USD",
                title="Pure-play quantum: revenue vs. GAAP net loss",
                area_id=area_id,
            )
            boards.append({
                "kicker": "Quantum lens · FY 2025 · million USD",
                "title": "Pure-play quantum: revenue vs. net loss",
                "badge": f"{len(q_rows)} listed companies",
                "svg": svg,
                "note": (
                    "Full-year GAAP revenue beside full-year GAAP net loss on a dedicated million-USD scale. "
                    "Source: SEC Form 10-K and Form 8-K filings (IonQ, D-Wave Quantum, Rigetti Computing)."
                ),
            })

        # Perspective 2: AI hyperscalers CapEx vs R&D
        ai_pairs = [
            ("Alphabet", "alphabet-ai-capex", "alphabet-rd-spending"),
            ("Meta Platforms", "meta-ai-capex", "meta-rd-spending"),
        ]
        ai_rows = []
        for label, cap_id, rd_id in ai_pairs:
            cm = by_id.get(cap_id)
            rm = by_id.get(rd_id)
            if cm and rm and cm.get("headline_point") and rm.get("headline_point"):
                cv = float(cm["headline_point"]["value"])
                rv = float(rm["headline_point"]["value"])
                ai_rows.append({
                    "label": label,
                    "value_a": cv,
                    "value_b": rv,
                    "sub": f"{cm['headline_point']['period_display']} · CapEx {cv / max(rv, 1e-9):.2f}x R&D",
                })
        if len(ai_rows) >= 2:
            svg = charts.editorial_dual_bars(
                ai_rows,
                series_a_label="Capital expenditure",
                series_b_label="Research & development",
                unit="million USD",
                title="AI infrastructure: CapEx vs. R&D",
                area_id=area_id,
            )
            boards.append({
                "kicker": "AI infrastructure lens · FY 2025 · million USD",
                "title": "Hyperscaler CapEx vs. R&D spending",
                "badge": "SEC FY 2025 filings",
                "svg": svg,
                "note": (
                    "Purchases of property and equipment (CapEx) alongside annual research and development expense. "
                    "Source: SEC Form 8-K FY 2025 earnings releases (Alphabet Inc., Meta Platforms, Inc.)."
                ),
            })

    return boards

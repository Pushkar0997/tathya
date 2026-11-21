"""Staleness calculation for Tathya metrics and points (M1-STL-01, INV-9).

Standard library only. Delegates date math to scripts/validate_data.py so the
validator and builder never diverge on staleness boundaries.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import validate_data as vd  # noqa: E402

DEFAULT_STALE_AFTER_MONTHS = vd.DEFAULT_STALE_AFTER_MONTHS
parse_date = vd.parse_date
add_months = vd.add_months
is_stale = vd.is_stale


def resolve_build_date(today_arg: str | date | None = None) -> date:
    """Return the build date in UTC, or parse an explicit YYYY-MM-DD override."""
    if isinstance(today_arg, date):
        return today_arg
    if isinstance(today_arg, str):
        parsed = parse_date(today_arg)
        if parsed is None:
            raise ValueError(f"Invalid --today date '{today_arg}', expected YYYY-MM-DD")
        return parsed
    return datetime.now(timezone.utc).date()


def annotate_metric_staleness(metric: dict, build_date: date) -> dict:
    """Return a shallow copy of metric with each point annotated with its computed `stale` boolean."""
    months = metric.get("stale_after_months", DEFAULT_STALE_AFTER_MONTHS)
    annotated_points = []
    for p in metric.get("points", []):
        pt = dict(p)
        verified_on = pt.get("verified_on")
        if verified_on:
            pt["stale"] = is_stale(verified_on, months, build_date)
            d = parse_date(verified_on)
            pt["stale_on"] = add_months(d, months).isoformat() if d else None
        else:
            pt["stale"] = False
            pt["stale_on"] = None
        annotated_points.append(pt)
    out = dict(metric)
    out["points"] = annotated_points
    out["stale_after_months"] = months
    return out

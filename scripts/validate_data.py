#!/usr/bin/env python3
"""validate_data: the correctness gate for Tathya data files. Standard library only.

Usage:
    python3 scripts/validate_data.py                     # validate data/ in production mode
    python3 scripts/validate_data.py --preview           # allow SAMPLE points (local preview only)
    python3 scripts/validate_data.py --data-dir fixtures/data --preview

Exit code 1 if any error is found. Error codes are listed in spec/evals.md.

What this checks is STRUCTURE and CONSISTENCY: every number has a source, a date, a
period, evidence that contains the figure as printed, and a verifier who is not the
person who entered it. What it cannot check is whether the figure matches the real
source. That needs a human or a separate verifier session (docs/prompts/verify.md).
"""
from __future__ import annotations

import argparse
import calendar
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

AREAS = {"people", "planet", "public-money", "industry"}
STATUSES = {"verified", "estimate", "derived", "sample"}
SOURCE_TYPES = {"primary", "secondary"}
PERIOD_KINDS = {"calendar_year", "financial_year", "date"}
MIN_EVIDENCE_CHARS = 20
DEFAULT_STALE_AFTER_MONTHS = 12

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FULL_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PARTIAL_DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
HANDLE_RE = re.compile(r"^(?:agent:)?[A-Za-z0-9][A-Za-z0-9._-]{0,38}$")
COUNTRY_RE = re.compile(r"^[A-Z]{3}$")

TOP_REQUIRED = ["id", "title", "area", "definition", "definition_source", "unit", "sources", "points"]
TOP_ALLOWED = set(TOP_REQUIRED) | {"stale_after_months", "sample"}
SOURCE_KEYS = ["id", "publisher", "title", "url", "source_type", "published", "retrieved"]
POINT_REQUIRED = ["geography", "period_kind", "period", "value", "status", "source_id", "evidence"]
POINT_ALLOWED = set(POINT_REQUIRED) | {
    "entered_by", "verified_by", "verified_on", "estimate_method", "formula", "inputs", "revision_note",
}


@dataclass(frozen=True)
class Finding:
    code: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.where}: {self.message}"


@dataclass
class Context:
    allowlist: dict
    states: set
    banned: list
    today: date
    production: bool = True


# ---------------------------------------------------------------- helpers

def parse_date(text) -> date | None:
    if not isinstance(text, str) or not FULL_DATE_RE.match(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def add_months(d: date, months: int) -> date:
    index = d.year * 12 + (d.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def is_stale(verified_on: str, stale_after_months: int, today: date) -> bool:
    """A point is stale once today is later than verified_on plus stale_after_months."""
    d = parse_date(verified_on)
    if d is None:
        return True
    return today > add_months(d, stale_after_months)


def value_text(value) -> str:
    """The number as a plain decimal string without trailing zeros: 12.30 -> '12.3'."""
    text = format(Decimal(repr(value)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def evidence_contains_value(evidence: str, value) -> bool:
    ev = evidence.replace(",", "").replace("\u2009", "").replace("\u00a0", "").replace("\u2212", "-")
    needle = value_text(value)
    return re.search(r"(?<![\d.])" + re.escape(needle) + r"(?!\d)", ev) is not None


def domain_tier(url: str, allowlist: dict) -> str | None:
    host = (urlparse(url).hostname or "").lower()
    best = None
    for domain, tier in allowlist.get("domains", {}).items():
        if host == domain or host.endswith("." + domain):
            if best is None or len(domain) > len(best[0]):
                best = (domain, tier)
    return best[1] if best else None


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def banned_hit(text: str, banned: list) -> str | None:
    for pattern in banned:
        if pattern.search(text):
            return pattern.pattern
    return None


def load_context(production: bool = True, today: date | None = None) -> Context:
    allowlist = json.loads((ROOT / "config" / "source_allowlist.json").read_text(encoding="utf-8"))
    states = {r["code"] for r in json.loads((ROOT / "config" / "in_states.json").read_text(encoding="utf-8"))["regions"]}
    banned = []
    for line in (ROOT / "config" / "banned_phrases.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            banned.append(re.compile(r"\b" + re.escape(line) + r"\b", re.I))
    return Context(allowlist, states, banned, today or datetime.now(timezone.utc).date(), production)


# ---------------------------------------------------------------- validation

def validate_metric(doc, stem: str, ctx: Context) -> list[Finding]:
    f: list[Finding] = []
    where = stem

    def err(code: str, loc: str, msg: str) -> None:
        f.append(Finding(code, loc, msg))

    if not isinstance(doc, dict):
        return [Finding("V-SCHEMA-01", where, "file must contain a JSON object")]
    for key in TOP_REQUIRED:
        if key not in doc:
            err("V-SCHEMA-01", where, f"missing required field '{key}'")
    for key in doc:
        if key not in TOP_ALLOWED:
            err("V-SCHEMA-01", where, f"unknown field '{key}'")
    if f:
        return f

    if not isinstance(doc["id"], str) or not ID_RE.match(doc["id"]) or doc["id"] != stem:
        err("V-ID-01", where, f"id must be kebab-case and equal the file name '{stem}'")
    if doc["area"] not in AREAS:
        err("V-AREA-01", where, f"area must be one of {sorted(AREAS)}")
    for key in ("title", "definition", "unit"):
        if not isinstance(doc[key], str) or not doc[key].strip():
            err("V-SCHEMA-01", where, f"'{key}' must be a non-empty string")
    months = doc.get("stale_after_months", DEFAULT_STALE_AFTER_MONTHS)
    if not isinstance(months, int) or isinstance(months, bool) or not 1 <= months <= 60:
        err("V-SCHEMA-01", where, "stale_after_months must be an integer from 1 to 60")
    if not isinstance(doc["sources"], list) or not doc["sources"]:
        err("V-SRC-01", where, "a metric needs at least one source")
        return f
    if not isinstance(doc["points"], list):
        err("V-SCHEMA-01", where, "points must be a list")
        return f

    for text_key in ("title", "definition"):
        hit = banned_hit(doc[text_key], ctx.banned) if isinstance(doc[text_key], str) else None
        if hit:
            err("V-LANG-01", where, f"banned phrase in {text_key}: {hit}")

    # sources
    sources: dict[str, dict] = {}
    for i, s in enumerate(doc["sources"]):
        loc = f"{stem}.sources[{i}]"
        if not isinstance(s, dict):
            err("V-SCHEMA-01", loc, "source must be an object")
            continue
        for key in SOURCE_KEYS:
            if not isinstance(s.get(key), str) or not s.get(key, "").strip():
                err("V-SCHEMA-01", loc, f"source missing '{key}'")
        if s.get("id") in sources:
            err("V-SRC-05", loc, f"duplicate source id '{s.get('id')}'")
        if isinstance(s.get("id"), str):
            sources[s["id"]] = s
        url = s.get("url", "")
        if urlparse(url).scheme != "https":
            err("V-SRC-03", loc, "source url must use https")
        if s.get("source_type") not in SOURCE_TYPES:
            err("V-SRC-03", loc, "source_type must be 'primary' or 'secondary'")
        tier = domain_tier(url, ctx.allowlist) if isinstance(url, str) else None
        if tier is None:
            err("V-SRC-02", loc, f"domain of {url} is not in config/source_allowlist.json")
        elif tier in SOURCE_TYPES and s.get("source_type") in SOURCE_TYPES and tier != s["source_type"]:
            err("V-SRC-04", loc, f"declared {s['source_type']} but the allowlist tier for this domain is {tier}")
        if not PARTIAL_DATE_RE.match(str(s.get("published", ""))):
            err("V-DATE-01", loc, "published must be YYYY, YYYY-MM or YYYY-MM-DD")
        retrieved = parse_date(s.get("retrieved"))
        if retrieved is None:
            err("V-DATE-01", loc, "retrieved must be a real date, YYYY-MM-DD")
        elif retrieved > ctx.today:
            err("V-DATE-01", loc, "retrieved is in the future")
    if doc["definition_source"] not in sources:
        err("V-SRC-01", where, "definition_source does not match any source id")

    # points
    seen: set = set()
    sample_points = 0
    for i, p in enumerate(doc["points"]):
        loc = f"{stem}.points[{i}]"
        if not isinstance(p, dict):
            err("V-SCHEMA-01", loc, "point must be an object")
            continue
        missing = [k for k in POINT_REQUIRED if k not in p]
        if missing:
            err("V-SCHEMA-01", loc, f"missing fields {missing}")
            continue
        for key in p:
            if key not in POINT_ALLOWED:
                err("V-SCHEMA-01", loc, f"unknown field '{key}'")
        status = p["status"]
        if status not in STATUSES:
            err("V-SCHEMA-01", loc, f"status must be one of {sorted(STATUSES)}")
            continue

        geo = p["geography"]
        if not (geo == "WLD" or (isinstance(geo, str) and COUNTRY_RE.match(geo)) or geo in ctx.states):
            err("V-GEO-01", loc, f"geography '{geo}' must be WLD, an ISO 3166-1 alpha-3 country code, or an ISO 3166-2:IN code")

        kind, period = p["period_kind"], p["period"]
        if kind not in PERIOD_KINDS:
            err("V-PER-01", loc, f"period_kind must be one of {sorted(PERIOD_KINDS)}")
        elif not isinstance(period, str):
            err("V-PER-01", loc, "period must be a string")
        elif kind == "calendar_year" and not re.fullmatch(r"(19|20)\d{2}", period):
            err("V-PER-01", loc, "calendar_year period must look like 2023")
        elif kind == "financial_year":
            m = re.fullmatch(r"((?:19|20)\d{2})-(\d{2})", period)
            if not m or (int(m.group(1)) + 1) % 100 != int(m.group(2)):
                err("V-PER-01", loc, "financial_year period must look like 2023-24")
        elif kind == "date" and parse_date(period) is None:
            err("V-PER-01", loc, "date period must be a real date, YYYY-MM-DD")

        key = (geo, kind, period)
        if key in seen:
            err("V-DUP-01", loc, f"duplicate point for {key}")
        seen.add(key)

        value = p["value"]
        if not is_number(value):
            err("V-VAL-01", loc, "value must be a finite JSON number, never a string")
        elif isinstance(doc["unit"], str) and doc["unit"].lower().startswith("percent") and not 0 <= value <= 100:
            err("V-VAL-02", loc, "a percent value must be between 0 and 100")

        src = sources.get(p["source_id"])
        if src is None:
            err("V-SRC-01", loc, f"source_id '{p['source_id']}' is not defined in sources")
        elif domain_tier(src.get("url", ""), ctx.allowlist) == "sample" and status != "sample":
            err("V-SRC-02", loc, "a sample-only source cannot back a real point")

        evidence = p["evidence"]
        if not isinstance(evidence, str) or len(evidence.strip()) < MIN_EVIDENCE_CHARS:
            err("V-EVID-01", loc, f"evidence must be a string of at least {MIN_EVIDENCE_CHARS} characters: locator plus the figure as printed")
        elif status != "derived" and is_number(value) and not evidence_contains_value(evidence, value):
            err("V-EVID-02", loc, f"evidence does not contain the figure {value_text(value)} as printed")

        if status == "sample":
            sample_points += 1
        else:
            for who in ("entered_by", "verified_by"):
                if not isinstance(p.get(who), str) or not HANDLE_RE.match(p.get(who, "")):
                    err("V-VER-01", loc, f"{who} must be a GitHub handle or 'agent:name'")
            if parse_date(p.get("verified_on")) is None:
                err("V-VER-01", loc, "verified_on must be a real date, YYYY-MM-DD")
            elif parse_date(p["verified_on"]) > ctx.today:
                err("V-DATE-01", loc, "verified_on is in the future")
            if isinstance(p.get("entered_by"), str) and isinstance(p.get("verified_by"), str) \
                    and p["entered_by"].lower() == p["verified_by"].lower():
                err("V-VER-02", loc, "the person who entered a point may not be the one who verified it")
        if status == "estimate" and not str(p.get("estimate_method", "")).strip():
            err("V-EST-01", loc, "an estimate needs estimate_method, the publisher's stated method")
        if status == "derived":
            if not str(p.get("formula", "")).strip() or not isinstance(p.get("inputs"), list) or not p.get("inputs"):
                err("V-DER-01", loc, "a derived point needs formula and a non-empty inputs list")
        for text_key in ("estimate_method", "formula", "revision_note"):
            if isinstance(p.get(text_key), str):
                hit = banned_hit(p[text_key], ctx.banned)
                if hit:
                    err("V-LANG-01", loc, f"banned phrase in {text_key}: {hit}")
    if sample_points and ctx.production:
        err("V-SAMPLE-01", where, f"{sample_points} SAMPLE point(s): SAMPLE data is not allowed in production")
    return f


def validate_tree(data_dirs, ctx: Context) -> tuple[list[Finding], int, dict]:
    findings: list[Finding] = []
    docs: dict[str, dict] = {}
    count = 0
    for base in data_dirs:
        base = Path(base)
        for path in sorted(base.rglob("*.json")):
            count += 1
            rel = str(path.relative_to(base))
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                findings.append(Finding("V-SCHEMA-01", rel, f"not valid JSON: {exc}"))
                continue
            if isinstance(doc, dict) and doc.get("sample") is True and ctx.production:
                findings.append(Finding("V-SAMPLE-01", rel, "file is flagged sample and cannot ship"))
            if isinstance(doc, dict) and doc.get("area") in AREAS and path.parent.name != doc["area"]:
                findings.append(Finding("V-AREA-01", rel, f"file must live in a folder named '{doc['area']}'"))
            findings += validate_metric(doc, path.stem, ctx)
            if isinstance(doc, dict) and isinstance(doc.get("id"), str):
                docs[doc["id"]] = doc
    # derived inputs must resolve: "metric-id|GEO|PERIOD"
    for mid, doc in docs.items():
        for i, p in enumerate(doc.get("points", []) if isinstance(doc.get("points"), list) else []):
            if isinstance(p, dict) and p.get("status") == "derived" and isinstance(p.get("inputs"), list):
                for ref in p["inputs"]:
                    parts = str(ref).split("|")
                    ok = len(parts) == 3 and parts[0] in docs and any(
                        isinstance(q, dict) and q.get("geography") == parts[1] and q.get("period") == parts[2]
                        for q in docs[parts[0]].get("points", []))
                    if not ok:
                        findings.append(Finding("V-DER-01", f"{mid}.points[{i}]", f"input '{ref}' does not resolve to an existing point"))
    return findings, count, docs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", action="append", default=None, help="folder of metric JSON files (default: data)")
    parser.add_argument("--preview", action="store_true", help="allow SAMPLE points; for local preview only, never for a deploy")
    parser.add_argument("--today", help="override today's date, YYYY-MM-DD (tests)")
    args = parser.parse_args(argv)
    today = parse_date(args.today) if args.today else None
    ctx = load_context(production=not args.preview, today=today)
    dirs = [ROOT / d for d in (args.data_dir or ["data"])]
    findings, count, docs = validate_tree(dirs, ctx)
    for item in findings:
        print(f"error: {item}", file=sys.stderr)
    stale = 0
    for doc in docs.values():
        months = doc.get("stale_after_months", DEFAULT_STALE_AFTER_MONTHS)
        for p in doc.get("points", []):
            if isinstance(p, dict) and p.get("verified_on") and is_stale(p["verified_on"], months, ctx.today):
                stale += 1
    mode = "production" if ctx.production else "preview"
    print(f"validate_data ({mode}): {count} file(s), {len(findings)} error(s), {stale} stale point(s) - {'FAIL' if findings else 'OK'}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

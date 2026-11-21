#!/usr/bin/env python3
"""check_revisions: enforce INV-10 (revisions are visible) on changed or removed points (M1-REV-01).

Usage:
    python3 scripts/check_revisions.py --base-ref origin/main
    python3 scripts/check_revisions.py --base-dir path/to/base/data --head-dir path/to/head/data

Exit code 1 when any published point's value changed or was removed relative to the base
without a non-empty `revision_note`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dir_docs(data_dir: Path) -> dict[str, dict]:
    docs: dict[str, dict] = {}
    if not data_dir.exists():
        return docs
    for path in sorted(data_dir.rglob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(doc, dict) and isinstance(doc.get("id"), str):
            docs[doc["id"]] = doc
    return docs


def load_git_docs(base_ref: str, data_rel: str = "data") -> dict[str, dict]:
    docs: dict[str, dict] = {}
    try:
        proc = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", base_ref, data_rel],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return docs
    if proc.returncode != 0:
        return docs

    for rel_path in proc.stdout.splitlines():
        rel_path = rel_path.strip()
        if not rel_path.endswith(".json"):
            continue
        show_proc = subprocess.run(
            ["git", "show", f"{base_ref}:{rel_path}"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if show_proc.returncode == 0:
            try:
                doc = json.loads(show_proc.stdout)
                if isinstance(doc, dict) and isinstance(doc.get("id"), str):
                    docs[doc["id"]] = doc
            except json.JSONDecodeError:
                pass
    return docs


def check_revisions(base_docs: dict[str, dict], head_docs: dict[str, dict]) -> list[str]:
    """Compare base_docs and head_docs; return error strings naming any changed or removed point lacking a revision_note."""
    errors: list[str] = []

    for mid, base_doc in sorted(base_docs.items()):
        base_points = {
            (p["geography"], p["period_kind"], p["period"]): p
            for p in base_doc.get("points", [])
            if isinstance(p, dict) and all(k in p for k in ("geography", "period_kind", "period", "value"))
        }
        if mid not in head_docs:
            for (geo, kind, period) in sorted(base_points.keys()):
                errors.append(
                    f"INV-10 {mid} ({geo}, {kind}, {period}): metric file removed without revision_note"
                )
            continue

        head_doc = head_docs[mid]
        head_points = {
            (p["geography"], p["period_kind"], p["period"]): p
            for p in head_doc.get("points", [])
            if isinstance(p, dict) and all(k in p for k in ("geography", "period_kind", "period", "value"))
        }

        for key, bp in sorted(base_points.items()):
            geo, kind, period = key
            point_label = f"{mid} ({geo}, {kind}, {period})"
            if key not in head_points:
                # Check whether another point for the same geography carries a revision_note naming the removed period
                noted = any(
                    hp.get("geography") == geo
                    and str(hp.get("revision_note", "")).strip()
                    and period in str(hp.get("revision_note", ""))
                    for hp in head_points.values()
                )
                if not noted:
                    errors.append(
                        f"INV-10 {point_label}: point removed without a revision_note"
                    )
            else:
                hp = head_points[key]
                if hp.get("value") != bp.get("value"):
                    note = str(hp.get("revision_note", "")).strip()
                    old_note = str(bp.get("revision_note", "")).strip()
                    if not note or (old_note and note == old_note):
                        errors.append(
                            f"INV-10 {point_label}: value changed from {bp.get('value')} to {hp.get('value')} without a revision_note"
                        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-ref", default="origin/main", help="git base reference to compare against")
    parser.add_argument("--base-dir", default=None, help="directory of base metric JSON files (overrides --base-ref)")
    parser.add_argument("--head-dir", default=None, help="directory of current metric JSON files (default: data)")
    args = parser.parse_args(argv)

    head_path = Path(args.head_dir) if args.head_dir else (ROOT / "data")
    if not head_path.is_absolute():
        head_path = ROOT / head_path
    head_docs = load_dir_docs(head_path)

    if args.base_dir is not None:
        base_path = Path(args.base_dir)
        if not base_path.is_absolute():
            base_path = ROOT / base_path
        base_docs = load_dir_docs(base_path)
    else:
        base_docs = load_git_docs(args.base_ref)

    errors = check_revisions(base_docs, head_docs)
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    print(f"check_revisions: {len(errors)} error(s) - {'FAIL' if errors else 'OK'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

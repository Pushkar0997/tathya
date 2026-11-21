#!/usr/bin/env python3
"""check_links: request every source URL in data/ and print a status table (M1-LNK-01).

Standard library only. Exits non-zero on any HTTP 404 or 410 response.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent


def collect_source_urls(data_dirs: list[Path]) -> list[tuple[str, list[str]]]:
    """Return sorted (url, [metric_ids]) pairs across all metric JSON files in data_dirs."""
    url_to_metrics: dict[str, set[str]] = {}
    for base in data_dirs:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(doc, dict):
                continue
            mid = str(doc.get("id") or path.stem)
            for s in doc.get("sources", []):
                if isinstance(s, dict) and isinstance(s.get("url"), str) and s["url"].strip():
                    url_to_metrics.setdefault(s["url"].strip(), set()).add(mid)
    return [(url, sorted(mids)) for url, mids in sorted(url_to_metrics.items())]


def default_requester(url: str, timeout: float = 15.0) -> int | str:
    """Perform an HTTP request (HEAD then GET fallback) and return integer status code or error label."""
    headers = {"User-Agent": "TathyaLinkChecker/1.0"}
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return int(resp.status)
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 501}:
                continue
            return int(exc.code)
        except urllib.error.URLError as exc:
            return f"ERR ({exc.reason})"
        except OSError as exc:
            return f"ERR ({exc})"
    return "ERR"


def check_links(
    data_dirs: list[Path],
    requester: Callable[[str], int | str] = default_requester,
) -> tuple[int, list[tuple[str, int | str, list[str]]]]:
    items = collect_source_urls(data_dirs)
    results: list[tuple[str, int | str, list[str]]] = []
    dead_count = 0

    print(f"{'STATUS':<10} | {'METRICS':<32} | URL")
    print("-" * 90)
    if not items:
        print(f"{'NONE':<10} | {'(no source URLs in data/)':<32} | -")
        return 0, results

    for url, mids in items:
        status = requester(url)
        results.append((url, status, mids))
        if status in {404, 410}:
            dead_count += 1
        print(f"{str(status):<10} | {', '.join(mids):<32} | {url}")

    return (1 if dead_count > 0 else 0), results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", action="append", default=None, help="folder of metric JSON files (default: data)")
    args = parser.parse_args(argv)

    dirs = [Path(d) if Path(d).is_absolute() else (ROOT / d) for d in (args.data_dir or ["data"])]
    rc, _ = check_links(dirs)
    return rc


if __name__ == "__main__":
    sys.exit(main())

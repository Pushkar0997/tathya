#!/usr/bin/env python3
"""check_contrast: verify WCAG 2.x contrast ratios for all colour pairs in design/tokens.json (M2-A11-01).

Standard library only. Exits non-zero if any pair falls below 4.5 (or 3.0 for pairs marked large).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        raise ValueError(f"Invalid hex colour '{hex_color}'")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    r, g, b = hex_to_rgb(hex_color)
    channels = []
    for c in (r, g, b):
        s = c / 255.0
        lin = s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
        channels.append(lin)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_tokens_contrast(tokens_path: Path | None = None) -> tuple[list[str], int]:
    path = tokens_path or (ROOT / "design" / "tokens.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = data.get("pairs", [])
    errors: list[str] = []

    for p in pairs:
        name = p.get("name", "unnamed")
        fg = p["fg"]
        bg = p["bg"]
        is_large = bool(p.get("large", False))
        required_min = 3.0 if is_large else 4.5
        ratio = contrast_ratio(fg, bg)
        if ratio < required_min:
            errors.append(
                f"{name} ({fg} on {bg}): computed contrast {ratio:.2f} is below required minimum {required_min:.1f}"
            )
    return errors, len(pairs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tokens", default=None, help="path to design/tokens.json")
    args = parser.parse_args(argv)

    t_path = Path(args.tokens) if args.tokens else None
    errors, count = check_tokens_contrast(t_path)
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    print(f"check_contrast: {count} pair(s), {len(errors)} failure(s) - {'FAIL' if errors else 'OK'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""build_site: static site generator for Tathya.

Usage:
    python3 scripts/build_site.py
    python3 scripts/build_site.py --preview
    python3 scripts/build_site.py --today 2026-11-08
    python3 scripts/build_site.py --data-dir data --out-dir dist
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import site as _stdlib_site
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
_stdlib_site.__path__ = [str(ROOT / "site")]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import make_tokens  # noqa: E402
import validate_data as vd  # noqa: E402
from site import pages, staleness  # noqa: E402

CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")\s]+)['\"]?\s*\)", re.I)
CSS_IMPORT_RE = re.compile(r"@import\s+(?:url\()?['\"]?([^'\");\s]+)['\"]?\)?", re.I)
FORBIDDEN_MAP_EXTS = {".geojson", ".topojson", ".map"}
MAX_PAGE_BYTES = 300 * 1024
MAX_AREA_FONT_BYTES = 250 * 1024


def is_external_ref(ref: str) -> bool:
    s = ref.strip()
    if not s or s.startswith("#") or s.startswith("data:"):
        return False
    if s.startswith("//"):
        return True
    parsed = urlparse(s)
    return bool(parsed.scheme in {"http", "https"} or parsed.netloc)


class DistHTMLScanner(HTMLParser):
    """Scans a built HTML file for external resource references and cookies (M1-NET-01, INV-7)."""

    def __init__(self, rel_path: str) -> None:
        super().__init__()
        self.rel_path = rel_path
        self.errors: list[str] = []
        self._in_style = False
        self._in_script = False

    def _check_css_text(self, css_text: str, where: str) -> None:
        for m in CSS_URL_RE.finditer(css_text):
            target = m.group(1)
            if is_external_ref(target):
                self.errors.append(f"INV-7 {self.rel_path} ({where}): external CSS url({target})")
        for m in CSS_IMPORT_RE.finditer(css_text):
            target = m.group(1)
            if is_external_ref(target):
                self.errors.append(f"INV-7 {self.rel_path} ({where}): external CSS @import {target}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()
        if t in {"script", "img", "iframe", "frame", "embed", "source"}:
            src = attr_dict.get("src", "")
            if is_external_ref(src):
                self.errors.append(f"INV-7 {self.rel_path}: <{t}> references external origin '{src}'")
            srcset = attr_dict.get("srcset", "")
            for part in srcset.split(","):
                candidate = part.strip().split(" ")[0] if part.strip() else ""
                if is_external_ref(candidate):
                    self.errors.append(f"INV-7 {self.rel_path}: <{t} srcset> references external origin '{candidate}'")
        elif t == "link":
            href = attr_dict.get("href", "")
            if is_external_ref(href):
                self.errors.append(f"INV-7 {self.rel_path}: <link> references external origin '{href}'")
        elif t == "object":
            data_url = attr_dict.get("data", "")
            if is_external_ref(data_url):
                self.errors.append(f"INV-7 {self.rel_path}: <object> references external origin '{data_url}'")
        elif t == "meta":
            http_equiv = attr_dict.get("http-equiv", "").lower()
            if http_equiv == "set-cookie":
                self.errors.append(f"INV-7 {self.rel_path}: <meta http-equiv='set-cookie'> is forbidden")

        if "style" in attr_dict:
            self._check_css_text(attr_dict["style"], f"<{t} style>")

        if t == "style":
            self._in_style = True
        elif t == "script":
            self._in_script = True

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "style":
            self._in_style = False
        elif t == "script":
            self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._check_css_text(data, "<style>")
        if self._in_script and "document.cookie" in data:
            self.errors.append(f"INV-7 {self.rel_path}: script accesses document.cookie")


def scan_templates_for_banned_phrases(template_dirs: list[Path], banned: list) -> list[str]:
    """Scan template files for banned phrases (M1-LNG-01, INV-5-B)."""
    errors: list[str] = []
    for tdir in template_dirs:
        if not tdir.exists():
            continue
        for path in sorted(tdir.rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            hit = vd.banned_hit(text, banned)
            if hit:
                try:
                    rel = str(path.relative_to(ROOT))
                except ValueError:
                    rel = str(path)
                errors.append(f"V-LANG-01 {rel}: banned phrase in template: {hit}")
    return errors


def scan_dist(out_dir: Path) -> list[str]:
    """Scan built dist/ folder for external requests, cookies, map files, and size budgets (M1-NET-01, M2)."""
    errors: list[str] = []
    if not out_dir.exists():
        return errors

    css_bytes = sum(p.stat().st_size for p in out_dir.rglob("*.css") if p.is_file())
    font_bytes = sum(p.stat().st_size for p in out_dir.rglob("*.woff2") if p.is_file())
    if font_bytes > MAX_AREA_FONT_BYTES * 4:
        errors.append(f"SIZE fonts: total woff2 size {font_bytes} exceeds budget")

    for path in sorted(out_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = str(path.relative_to(out_dir))
        except ValueError:
            rel = str(path)

        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_MAP_EXTS:
            errors.append(f"INV-8 {rel}: geographic map or boundary file '{path.name}' is forbidden")
            continue

        if suffix == ".html":
            total_page_bytes = path.stat().st_size + css_bytes
            if total_page_bytes > MAX_PAGE_BYTES:
                errors.append(
                    f"SIZE {rel}: page + CSS size {total_page_bytes} B exceeds 300 KB budget ({MAX_PAGE_BYTES} B)"
                )
            scanner = DistHTMLScanner(rel)
            scanner.feed(path.read_text(encoding="utf-8", errors="ignore"))
            errors.extend(scanner.errors)
        elif suffix == ".css":
            css_text = path.read_text(encoding="utf-8", errors="ignore")
            for m in CSS_URL_RE.finditer(css_text):
                target = m.group(1)
                if is_external_ref(target):
                    errors.append(f"INV-7 {rel}: external CSS url({target})")
            for m in CSS_IMPORT_RE.finditer(css_text):
                target = m.group(1)
                if is_external_ref(target):
                    errors.append(f"INV-7 {rel}: external CSS @import {target}")
    return errors


def render_markdown_to_html(md_text: str) -> str:
    """Convert simple Markdown from CONTRIBUTING.md / README.md into HTML without adding claims or h1."""
    lines = md_text.splitlines()
    out: list[str] = []
    in_code = False
    in_ul = False
    in_ol = False
    in_table = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol, in_table
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    def inline_fmt(s: str) -> str:
        escaped = html.escape(s)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        return escaped

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if stripped.startswith("```"):
            close_lists()
            if not in_code:
                out.append("<pre><code>")
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            i += 1
            continue
        if in_code:
            out.append(html.escape(raw))
            i += 1
            continue
        if not stripped:
            close_lists()
            i += 1
            continue
        if stripped.startswith("# "):
            close_lists()
            i += 1
            continue
        if stripped.startswith("## "):
            close_lists()
            out.append(f"<h2>{inline_fmt(stripped[3:].strip())}</h2>")
            i += 1
            continue
        if stripped.startswith("### "):
            close_lists()
            out.append(f"<h3>{inline_fmt(stripped[4:].strip())}</h3>")
            i += 1
            continue
        if stripped.startswith("> "):
            close_lists()
            out.append(f"<blockquote><p>{inline_fmt(stripped[2:].strip())}</p></blockquote>")
            i += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c) <= {"-", ":"} for c in cells):
                i += 1
                continue
            if not in_table:
                close_lists()
                out.append('<table class="data-table"><thead><tr>')
                for c in cells:
                    out.append(f"<th>{inline_fmt(c)}</th>")
                out.append("</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>")
                for c in cells:
                    out.append(f"<td>{inline_fmt(c)}</td>")
                out.append("</tr>")
            i += 1
            continue
        if stripped.startswith("- "):
            if in_ol or in_table:
                close_lists()
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_fmt(stripped[2:].strip())}</li>")
            i += 1
            continue
        m_ol = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m_ol:
            if in_ul or in_table:
                close_lists()
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline_fmt(m_ol.group(1).strip())}</li>")
            i += 1
            continue
        close_lists()
        out.append(f"<p>{inline_fmt(stripped)}</p>")
        i += 1

    close_lists()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def build(
    data_dirs: list[Path] | None = None,
    out_dir: Path | None = None,
    template_dir: Path | None = None,
    preview: bool = False,
    today: date | None = None,
) -> int:
    resolved_dirs = data_dirs if data_dirs is not None else [ROOT / ("fixtures/data" if preview else "data")]
    resolved_out = out_dir if out_dir is not None else (ROOT / "dist")
    resolved_tpl_dir = template_dir if template_dir is not None else (ROOT / "templates")

    build_date = staleness.resolve_build_date(today)
    ctx = vd.load_context(production=not preview, today=build_date)

    # 1. Scan templates for banned phrases (M1-LNG-01)
    tpl_errors = scan_templates_for_banned_phrases([resolved_tpl_dir], ctx.banned)
    if tpl_errors:
        for err in tpl_errors:
            print(f"error: {err}", file=sys.stderr)
        return 1

    # 2. Validate data files (M0-BLD-02, M1-LNG-01)
    findings, _, docs = vd.validate_tree(resolved_dirs, ctx)
    if findings:
        for item in findings:
            print(f"error: {item}", file=sys.stderr)
        return 1

    # 3. Generate static/css/tokens.css from design/tokens.json (M2-CSS-01)
    make_tokens.generate_tokens_css()

    if resolved_out.exists():
        shutil.rmtree(resolved_out)
    resolved_out.mkdir(parents=True, exist_ok=True)

    static_src = ROOT / "static"
    static_dst = resolved_out / "static"
    if static_src.exists():
        shutil.copytree(static_src, static_dst)

    state_map = pages.load_state_names()
    tokens_data = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
    area_tokens = tokens_data.get("areas", {})

    enriched_metrics = [
        pages.enrich_metric(docs[mid], build_date, state_map, preview=preview)
        for mid in sorted(docs.keys())
    ]
    total_points = sum(len(m.get("points", [])) for m in enriched_metrics)

    env = Environment(
        loader=FileSystemLoader(str(resolved_tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    has_tokens_css = (static_src / "css" / "tokens.css").exists()
    has_fonts_css = (static_src / "css" / "fonts.css").exists()

    area_tiles = []
    metrics_by_area: dict[str, list[dict]] = {a: [] for a in pages.AREA_ORDER}
    for m in enriched_metrics:
        if m["area"] in metrics_by_area:
            metrics_by_area[m["area"]].append(m)

    for area_id in pages.AREA_ORDER:
        meta = dict(pages.AREA_META[area_id])
        a_metrics = metrics_by_area[area_id]
        count = len(a_metrics)
        meta["count"] = count
        meta["count_str"] = f"{count:02d}"
        # Prefer a multi-point or country-comparison metric as the area hero when available
        ranked_hero = sorted(
            a_metrics,
            key=lambda m: (len(m.get("series_points", [])) > 1, len(m.get("points", []))),
            reverse=True,
        )
        meta["hero_metric"] = ranked_hero[0] if ranked_hero else None
        area_tiles.append(meta)

    # Home visual gallery: show up to 2 richest visual cards per area (up to 6 total) for editorial variety
    visual_cards = []
    for tile in area_tiles:
        a_metrics = metrics_by_area[tile["id"]]
        ordered = sorted(
            [m for m in a_metrics if m.get("headline_point") and m.get("editorial_chart_svg")],
            key=lambda m: (len(m.get("series_points", [])) >= 2, len(m.get("points", []))),
            reverse=True,
        )
        for m in ordered[:2]:
            visual_cards.append({"area": tile, "metric": m})

    # Featured Indian state tile-grid metric (for Home & Area magazine feature band)
    featured_state_metric = next(
        (m for m in enriched_metrics if m.get("has_state_grid") and len(m.get("state_points", [])) >= 10),
        next((m for m in enriched_metrics if m.get("has_state_grid")), None),
    )

    recent_metrics = sorted(
        [m for m in enriched_metrics if m.get("headline_point")],
        key=lambda m: (m["headline_point"].get("verified_on") or "", m["id"]),
        reverse=True,
    )
    paired_scale = pages.select_paired_scale(enriched_metrics, preview=preview)

    # 1. Home page
    home_tpl = env.get_template("home.html")
    home_html = home_tpl.render(
        page_title="Tathya — Facts, kept beside their sources",
        root_prefix="",
        preview=preview,
        has_tokens_css=has_tokens_css,
        has_fonts_css=has_fonts_css,
        body_class="area-shared page-home",
        current_area=None,
        current_page="home",
        metrics=enriched_metrics,
        total_points=total_points,
        area_tiles=area_tiles,
        visual_cards=visual_cards,
        featured_state_metric=featured_state_metric,
        recent_metrics=recent_metrics,
        paired_scale=paired_scale,
    )
    (resolved_out / "index.html").write_text(home_html, encoding="utf-8")

    # 2. Area pages
    area_tpl = env.get_template("area.html")
    for area_id in pages.AREA_ORDER:
        info = pages.AREA_META[area_id]
        a_metrics = metrics_by_area[area_id]
        tile_for_area = next(t for t in area_tiles if t["id"] == area_id)
        hero_metric = tile_for_area["hero_metric"]
        area_covers = area_tokens.get(area_id, {}).get("covers", info["tagline"])
        area_comparison = pages.build_area_comparison(area_id, a_metrics)
        area_perspectives = pages.build_area_perspectives(area_id, a_metrics)
        area_guide = pages.get_area_guide(area_id)
        area_state_metric = next((m for m in a_metrics if m.get("has_state_grid")), None)
        connected_areas = [
            tile for tile in area_tiles
            if tile["id"] != area_id and tile["hero_metric"] and tile["hero_metric"].get("headline_point")
        ]
        area_html = area_tpl.render(
            page_title=f"Tathya — {info['label']}",
            root_prefix="",
            preview=preview,
            has_tokens_css=has_tokens_css,
            has_fonts_css=has_fonts_css,
            body_class=f"area-{area_id} page-area",
            current_area=area_id,
            current_page=f"area-{area_id}",
            area_info=info,
            area_covers=area_covers,
            area_metrics=a_metrics,
            hero_metric=hero_metric,
            area_comparison=area_comparison,
            area_perspectives=area_perspectives,
            area_guide=area_guide,
            area_state_metric=area_state_metric,
            connected_areas=connected_areas,
        )
        (resolved_out / f"{area_id}.html").write_text(area_html, encoding="utf-8")

    # 3. Metric pages
    if enriched_metrics:
        metrics_dir = resolved_out / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        metric_tpl = env.get_template("metric.html")
        for m in enriched_metrics:
            area_id = m["area"]
            info = pages.AREA_META[area_id]
            same_area = [o for o in enriched_metrics if o["area"] == area_id and o["id"] != m["id"] and o.get("headline_point")]
            other_area = [o for o in enriched_metrics if o["area"] != area_id and o.get("headline_point")]
            related_metrics = (same_area + other_area)[:3]
            metric_html = metric_tpl.render(
                page_title=f"Tathya — {m['title']}",
                root_prefix="../",
                preview=preview,
                has_tokens_css=has_tokens_css,
                has_fonts_css=has_fonts_css,
                body_class=f"area-{area_id} page-metric",
                current_area=area_id,
                current_page="metric",
                area_info=info,
                metric=m,
                related_metrics=related_metrics,
                area_meta=pages.AREA_META,
            )
            (metrics_dir / f"{m['id']}.html").write_text(metric_html, encoding="utf-8")

    # 4. Contribute page
    contribute_tpl = env.get_template("contribute.html")
    contributing_md = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    contribute_html = contribute_tpl.render(
        page_title="Tathya — Contribute",
        root_prefix="",
        preview=preview,
        has_tokens_css=has_tokens_css,
        has_fonts_css=has_fonts_css,
        body_class="area-shared page-contribute",
        current_area=None,
        current_page="contribute",
        page_body=render_markdown_to_html(contributing_md),
    )
    (resolved_out / "contribute.html").write_text(contribute_html, encoding="utf-8")

    # 5. About page
    about_tpl = env.get_template("about.html")
    readme_md = (ROOT / "README.md").read_text(encoding="utf-8")
    about_html = about_tpl.render(
        page_title="Tathya — About",
        root_prefix="",
        preview=preview,
        has_tokens_css=has_tokens_css,
        has_fonts_css=has_fonts_css,
        body_class="area-shared page-about",
        current_area=None,
        current_page="about",
        page_body=render_markdown_to_html(readme_md),
    )
    (resolved_out / "about.html").write_text(about_html, encoding="utf-8")

    # 6. Scan built dist/ for external requests, cookies, map files, and size budgets (M1-NET-01, M2)
    net_errors = scan_dist(resolved_out)
    if net_errors:
        for err in net_errors:
            print(f"error: {err}", file=sys.stderr)
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Tathya static site into dist/.")
    parser.add_argument("--data-dir", action="append", default=None, help="folder of metric JSON files")
    parser.add_argument("--out-dir", default=None, help="output directory (default: dist)")
    parser.add_argument("--template-dir", default=None, help="templates directory (default: templates)")
    parser.add_argument("--preview", action="store_true", help="build preview using SAMPLE fixtures")
    parser.add_argument("--today", default=None, help="override build date in UTC, YYYY-MM-DD")
    args = parser.parse_args(argv)

    today = vd.parse_date(args.today) if args.today else None
    if args.today and today is None:
        print(f"error: invalid --today date '{args.today}', expected YYYY-MM-DD", file=sys.stderr)
        return 1

    data_dirs = [Path(d) if Path(d).is_absolute() else (ROOT / d) for d in args.data_dir] if args.data_dir else None
    out_dir = (Path(args.out_dir) if Path(args.out_dir).is_absolute() else (ROOT / args.out_dir)) if args.out_dir else None
    tpl_dir = (
        (Path(args.template_dir) if Path(args.template_dir).is_absolute() else (ROOT / args.template_dir))
        if args.template_dir
        else None
    )
    return build(data_dirs=data_dirs, out_dir=out_dir, template_dir=tpl_dir, preview=args.preview, today=today)


if __name__ == "__main__":
    sys.exit(main())

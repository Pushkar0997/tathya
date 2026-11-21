"""Tests for scripts/build_site.py, M0 and M1 build/page/scan evals."""
import contextlib
import copy
import io
import json
import shutil
import site as _stdlib_site
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_stdlib_site.__path__ = [str(ROOT / "site")]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_site as bs  # noqa: E402
import test_validate_data as tvd  # noqa: E402


class PageInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.has_doctype = False
        self.html_lang = None
        self.has_viewport = False
        self.in_title = False
        self.title_parts = []
        self.h1_count = 0
        self.has_skip_link = False
        self.has_main_target = False

    def handle_decl(self, decl):
        if decl.strip().lower() == "doctype html":
            self.has_doctype = True

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "html":
            self.html_lang = attr_dict.get("lang")
        elif tag == "meta" and attr_dict.get("name") == "viewport":
            if attr_dict.get("content"):
                self.has_viewport = True
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and attr_dict.get("href") == "#main-content":
            self.has_skip_link = True
        elif tag == "main" and attr_dict.get("id") == "main-content":
            self.has_main_target = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self):
        return "".join(self.title_parts).strip()


class BuildTests(unittest.TestCase):
    def test_G20_empty_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            empty_data = tmp_path / "data"
            empty_data.mkdir()
            out_dir = tmp_path / "dist"
            rc = bs.main(["--data-dir", str(empty_data), "--out-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            index_file = out_dir / "index.html"
            self.assertTrue(index_file.is_file())
            html = index_file.read_text(encoding="utf-8")
            self.assertIn("No verified numbers have been published yet", html)
            self.assertNotIn("Design preview. All values are SAMPLE.", html)
            self.assertTrue((out_dir / "static" / "css" / "base.css").is_file())

    def test_INV2_B_sample_fails_production_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bad_data = tmp_path / "data" / "people"
            bad_data.mkdir(parents=True)
            shutil.copy2(
                ROOT / "fixtures" / "data" / "people" / "undernourishment-prevalence.json",
                bad_data / "undernourishment-prevalence.json",
            )
            out_dir = tmp_path / "dist"
            stderr_buf = io.StringIO()
            with contextlib.redirect_stderr(stderr_buf):
                rc = bs.main(["--data-dir", str(tmp_path / "data"), "--out-dir", str(out_dir)])
            self.assertNotEqual(rc, 0)
            self.assertIn("V-SAMPLE-01", stderr_buf.getvalue())
            self.assertFalse(out_dir.exists())

            target_in_data = ROOT / "data" / "people" / "undernourishment-prevalence.json"
            out_dir_default = tmp_path / "dist_from_root_data"
            try:
                shutil.copy2(
                    ROOT / "fixtures" / "data" / "people" / "undernourishment-prevalence.json",
                    target_in_data,
                )
                stderr_root = io.StringIO()
                with contextlib.redirect_stderr(stderr_root):
                    rc_root = bs.main(["--out-dir", str(out_dir_default)])
                self.assertNotEqual(rc_root, 0)
                self.assertIn("V-SAMPLE-01", stderr_root.getvalue())
                self.assertFalse(out_dir_default.exists())
            finally:
                if target_in_data.exists():
                    target_in_data.unlink()

            rc_preview = bs.main(["--preview", "--out-dir", str(out_dir)])
            self.assertEqual(rc_preview, 0)
            for page in out_dir.rglob("*.html"):
                self.assertIn(
                    "Design preview. All values are SAMPLE.",
                    page.read_text(encoding="utf-8"),
                    f"Missing SAMPLE banner on {page.name}",
                )

    def test_G21_page_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "dist"
            rc = bs.main(["--out-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            expected_pages = {
                "index.html",
                "people.html",
                "planet.html",
                "public-money.html",
                "industry.html",
                "contribute.html",
                "about.html",
            }
            built_pages = {p.name for p in out_dir.glob("*.html")}
            self.assertEqual(built_pages, expected_pages)

            titles = set()
            for page_path in sorted(out_dir.rglob("*.html")):
                inspector = PageInspector()
                inspector.feed(page_path.read_text(encoding="utf-8"))
                self.assertTrue(inspector.has_doctype, f"{page_path.name} missing HTML5 doctype")
                self.assertEqual(inspector.html_lang, "en", f"{page_path.name} missing lang='en'")
                self.assertTrue(inspector.has_viewport, f"{page_path.name} missing viewport meta")
                self.assertTrue(inspector.has_skip_link, f"{page_path.name} missing skip link")
                self.assertTrue(inspector.has_main_target, f"{page_path.name} missing #main-content")
                self.assertEqual(inspector.h1_count, 1, f"{page_path.name} must have exactly one h1")
                self.assertTrue(inspector.title, f"{page_path.name} has empty title")
                self.assertNotIn(inspector.title, titles, f"Duplicate title '{inspector.title}'")
                titles.add(inspector.title)

    def test_M1_pages_area_and_metric_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = tmp_path / "data" / "people"
            data_dir.mkdir(parents=True)
            doc = tvd.good_doc()
            doc["points"][0]["revision_note"] = "Revised following updated FAO annex table."
            doc["points"].append({
                "geography": "IN-MH",
                "period_kind": "calendar_year",
                "period": "2023",
                "value": 14.5,
                "status": "verified",
                "source_id": "s1",
                "evidence": "Table 2, page 8: Maharashtra prevalence 14.5 percent in 2023",
                "entered_by": "agent:example",
                "verified_by": "reviewer-one",
                "verified_on": "2026-10-05",
            })
            (data_dir / f"{doc['id']}.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")

            out_dir = tmp_path / "dist"
            rc = bs.main(["--data-dir", str(tmp_path / "data"), "--out-dir", str(out_dir), "--today", "2026-11-08"])
            self.assertEqual(rc, 0)

            people_html = (out_dir / "people.html").read_text(encoding="utf-8")
            self.assertIn("Prevalence of undernourishment", people_html)
            self.assertIn("12.3%", people_html)
            self.assertIn("2023", people_html)
            self.assertIn("Primary source", people_html)

            planet_html = (out_dir / "planet.html").read_text(encoding="utf-8")
            self.assertIn("No verified numbers have been published yet in Planet.", planet_html)

            metric_html = (out_dir / "metrics" / "undernourishment-prevalence.html").read_text(encoding="utf-8")
            self.assertIn(doc["definition"], metric_html)
            self.assertIn("12.3%", metric_html)
            self.assertIn("line-chart-svg", metric_html)
            self.assertIn("state-tile-grid-svg", metric_html)
            self.assertIn("Example Agency", metric_html)
            self.assertIn("https://www.fao.org/example-report", metric_html)
            self.assertIn("Table 1, page 4: world prevalence 12.3 percent in 2023", metric_html)
            self.assertIn("reviewer-one", metric_html)
            self.assertIn("2026-10-05", metric_html)
            self.assertIn("Updated", metric_html)
            self.assertIn("Revised following updated FAO annex table.", metric_html)

    def test_INV9_T_stale_badge(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = tmp_path / "data" / "people"
            data_dir.mkdir(parents=True)
            doc = tvd.good_doc()
            doc["points"][0]["verified_on"] = "2025-11-07"
            doc["stale_after_months"] = 12
            (data_dir / f"{doc['id']}.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")

            # On 2026-11-08 (1 day past 12-month window), Stale badge appears
            out_stale = tmp_path / "dist_stale"
            rc = bs.main(["--data-dir", str(tmp_path / "data"), "--out-dir", str(out_stale), "--today", "2026-11-08"])
            self.assertEqual(rc, 0)
            metric_stale = (out_stale / "metrics" / "undernourishment-prevalence.html").read_text(encoding="utf-8")
            self.assertIn("badge-stale", metric_stale)
            self.assertIn(">Stale<", metric_stale)

            # On 2026-11-07 (within 12-month window), Stale badge does not appear
            out_fresh = tmp_path / "dist_fresh"
            rc2 = bs.main(["--data-dir", str(tmp_path / "data"), "--out-dir", str(out_fresh), "--today", "2026-11-07"])
            self.assertEqual(rc2, 0)
            metric_fresh = (out_fresh / "metrics" / "undernourishment-prevalence.html").read_text(encoding="utf-8")
            self.assertNotIn("badge-stale", metric_fresh)

    def test_INV5_B_banned_phrase_in_template_or_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bad_tpl_dir = tmp_path / "templates"
            shutil.copytree(ROOT / "templates", bad_tpl_dir)
            home_tpl = bad_tpl_dir / "home.html"
            home_tpl.write_text(
                home_tpl.read_text(encoding="utf-8") + "\n<!-- shocking commentary -->\n",
                encoding="utf-8",
            )
            out_dir = tmp_path / "dist"
            stderr_buf = io.StringIO()
            with contextlib.redirect_stderr(stderr_buf):
                rc = bs.main(["--template-dir", str(bad_tpl_dir), "--out-dir", str(out_dir)])
            self.assertNotEqual(rc, 0)
            self.assertIn("home.html", stderr_buf.getvalue())
            self.assertIn("V-LANG-01", stderr_buf.getvalue())
            self.assertFalse(out_dir.exists())

            # Also verify banned phrase in authored data text fails build naming the metric
            bad_data = tmp_path / "data" / "people"
            bad_data.mkdir(parents=True)
            doc = copy.deepcopy(tvd.good_doc())
            doc["definition"] = "This is an outrageous figure."
            (bad_data / f"{doc['id']}.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
            stderr_data = io.StringIO()
            with contextlib.redirect_stderr(stderr_data):
                rc_data = bs.main(["--data-dir", str(tmp_path / "data"), "--out-dir", str(out_dir)])
            self.assertNotEqual(rc_data, 0)
            self.assertIn("undernourishment-prevalence", stderr_data.getvalue())
            self.assertIn("V-LANG-01", stderr_data.getvalue())

    def test_INV7_T_no_external_requests_or_cookies(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out_dir = tmp_path / "dist"
            rc = bs.main(["--preview", "--out-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            self.assertEqual(bs.scan_dist(out_dir), [])

            # Inject an external font link and verify scan_dist fails
            bad_html = out_dir / "index.html"
            orig = bad_html.read_text(encoding="utf-8")
            bad_html.write_text(
                orig.replace("</head>", '<link rel="stylesheet" href="https://fonts.googleapis.com/css"></head>'),
                encoding="utf-8",
            )
            errs = bs.scan_dist(out_dir)
            self.assertTrue(any("INV-7" in e and "index.html" in e for e in errs))
            bad_html.write_text(orig, encoding="utf-8")

            # Inject a cookie meta tag and verify scan_dist fails
            bad_html.write_text(
                orig.replace("</head>", '<meta http-equiv="set-cookie" content="a=b"></head>'),
                encoding="utf-8",
            )
            errs_cookie = bs.scan_dist(out_dir)
            self.assertTrue(any("INV-7" in e and "set-cookie" in e for e in errs_cookie))
            bad_html.write_text(orig, encoding="utf-8")

            # Inject a .geojson file and verify scan_dist fails
            map_file = out_dir / "india.geojson"
            map_file.write_text("{}", encoding="utf-8")
            errs_map = bs.scan_dist(out_dir)
            self.assertTrue(any("INV-8" in e and "india.geojson" in e for e in errs_map))


if __name__ == "__main__":
    unittest.main()

"""Tests for Milestone M2 (G-25, contrast, accessibility, responsive CSS, area packs, empty states)."""
import json
import site as _stdlib_site
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_stdlib_site.__path__ = [str(ROOT / "site")]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_site as bs  # noqa: E402
import check_contrast as cc  # noqa: E402
import make_tokens as mt  # noqa: E402


class M2Tests(unittest.TestCase):
    def test_G25_tokens_css(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_css = Path(tmp) / "tokens.css"
            css = mt.generate_tokens_css(out_path=out_css)
            self.assertTrue(out_css.is_file())

            tokens = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))

            for ckey, cval in tokens["shared"]["colors"].items():
                prop = f"--shared-color-{ckey.replace('_', '-')}: {cval};"
                self.assertIn(prop, css)

            for fkey, fobj in tokens["shared"]["fonts"].items():
                prop = f"--font-{fkey.replace('_', '-')}: '{fobj['family']}'"
                self.assertIn(prop, css)

            for tkey, tval in tokens["shared"]["type_scale"].items():
                self.assertIn(f"--type-{tkey.replace('_', '-')}: {tval};", css)
            for lkey, lval in tokens["shared"]["layout"].items():
                self.assertIn(f"--layout-{lkey.replace('_', '-')}: {lval}px;", css)

            for area_id, aobj in tokens["areas"].items():
                self.assertIn(f"body.area-{area_id} {{", css)
                for ckey, cval in aobj["colors"].items():
                    self.assertIn(f"--color-{ckey.replace('_', '-')}: {cval};", css)
                self.assertIn(f"'{aobj['fonts']['display']['family']}'", css)
                self.assertIn(f"'{aobj['fonts']['script']['family']}'", css)

    def test_M2_A11_01_contrast(self):
        errors, count = cc.check_tokens_contrast()
        self.assertEqual(count, 38)
        self.assertEqual(errors, [])

        with tempfile.TemporaryDirectory() as tmp:
            bad_tokens = Path(tmp) / "bad_tokens.json"
            data = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
            data["pairs"][0]["fg"] = "#F0F0F5"
            data["pairs"][0]["bg"] = "#FBFAFF"
            bad_tokens.write_text(json.dumps(data), encoding="utf-8")
            bad_errs, _ = cc.check_tokens_contrast(bad_tokens)
            self.assertEqual(len(bad_errs), 1)

    def test_M2_A11_02_and_responsive_and_packs(self):
        base_css = (ROOT / "static" / "css" / "base.css").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", base_css)
        self.assertIn("prefers-reduced-motion: reduce", base_css)
        self.assertIn("@media (max-width: 640px)", base_css)
        self.assertIn("overflow-x: hidden", base_css)

        with tempfile.TemporaryDirectory() as tmp:
            out_prod = Path(tmp) / "dist_prod"
            rc = bs.main(["--out-dir", str(out_prod)])
            self.assertEqual(rc, 0)
            for area_id, label in [
                ("people", "People"),
                ("planet", "Planet"),
                ("public-money", "Public money"),
                ("industry", "Industry"),
            ]:
                area_html = (out_prod / f"{area_id}.html").read_text(encoding="utf-8")
                self.assertIn(f'class="area-{area_id} page-area"', area_html)
                self.assertIn(f"No verified numbers have been published yet in {label}.", area_html)

            out_prev = Path(tmp) / "dist_prev"
            rc_prev = bs.main(["--preview", "--out-dir", str(out_prev)])
            self.assertEqual(rc_prev, 0)
            home_html = (out_prev / "index.html").read_text(encoding="utf-8")
            self.assertIn("Two figures,", home_html)
            self.assertIn("paired-scale-svg", home_html)
            self.assertIn("Four places to start", home_html)
            self.assertIn("Recently", home_html)
            self.assertIn("No opinions.", home_html)


if __name__ == "__main__":
    unittest.main()

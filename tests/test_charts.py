"""Tests for site/charts.py (G-22, G-23, G-24, INV-8-T)."""
import json
import site as _stdlib_site
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_stdlib_site.__path__ = [str(ROOT / "site")]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from site import charts  # noqa: E402

GOLDEN_DIR = ROOT / "tests" / "goldens"


class ChartTests(unittest.TestCase):
    def test_G22_line_chart_golden(self):
        points = [
            {"period": "2020", "value": 10.0, "status": "verified"},
            {"period": "2021", "value": 15.0, "status": "verified"},
            {"period": "2022", "value": 20.0, "status": "verified"},
        ]
        svg = charts.line_chart(points, unit="percent of population", title="Test metric", preview=False)
        root = ET.fromstring(svg)
        self.assertEqual(root.attrib.get("role"), "img")
        self.assertTrue(root.attrib.get("aria-label"))

        texts = [el.text for el in root.iter("text") if el.text is not None]
        self.assertIn("0", texts)
        self.assertIn("2020", texts)
        self.assertIn("2022", texts)

        golden_path = GOLDEN_DIR / "line_chart.svg"
        self.assertTrue(golden_path.is_file())
        self.assertEqual(svg.strip(), golden_path.read_text(encoding="utf-8").strip())

    def test_G23_paired_scale_bars(self):
        svg = charts.paired_scale_bars(
            {"value": 80.0, "label": "Group A", "unit": "percent"},
            {"value": 20.0, "label": "Group B", "unit": "percent"},
        )
        root = ET.fromstring(svg)
        self.assertEqual(root.attrib.get("role"), "img")
        rects = list(root.iter("rect"))
        self.assertEqual(len(rects), 2)
        w1 = float(rects[0].attrib["width"])
        w2 = float(rects[1].attrib["width"])
        self.assertAlmostEqual(w1 / w2, 80.0 / 20.0, places=4)

        with self.assertRaises(ValueError):
            charts.paired_scale_bars(
                {"value": 80.0, "unit": "percent"},
                {"value": 20.0, "unit": "million tonnes"},
            )

    def test_G24_state_tile_grid(self):
        regions = json.loads((ROOT / "config" / "in_states.json").read_text(encoding="utf-8"))["regions"]
        points = []
        for idx, r in enumerate(regions):
            points.append({
                "geography": r["code"],
                "period_kind": "calendar_year",
                "period": "2023",
                "value": float(idx * 10),
                "status": "verified",
            })
        svg = charts.state_tile_grid(points, unit="percent")
        root = ET.fromstring(svg)

        rects = list(root.iter("rect"))
        self.assertEqual(len(rects), 36)

        state_rects = [r for r in rects if "state-tile" in r.attrib.get("class", "")]
        ut_rects = [r for r in rects if "ut-tile" in r.attrib.get("class", "")]
        self.assertEqual(len(state_rects), 28)
        self.assertEqual(len(ut_rects), 8)

        # Verify every state is placed on its exact configured [row, col]
        expected_tiles = {r["code"]: tuple(r["tile"]) for r in regions if r["kind"] == "state"}
        for sr in state_rects:
            code = sr.attrib["data-code"]
            row_col = (int(sr.attrib["data-row"]), int(sr.attrib["data-col"]))
            self.assertEqual(row_col, expected_tiles[code])

        # Verify all 4 equal-interval shade classes are used
        classes_seen = {int(r.attrib["data-class"]) for r in rects}
        self.assertEqual(classes_seen, {1, 2, 3, 4})

        # Verify every region's abbr is rendered as text
        texts = {el.text for el in root.iter("text") if el.text}
        for r in regions:
            self.assertIn(r["abbr"], texts)

    def test_INV8_T_tile_grid_no_maps(self):
        fixture = json.loads(
            (ROOT / "fixtures" / "data" / "people" / "undernourishment-prevalence.json").read_text(encoding="utf-8")
        )
        svg = charts.state_tile_grid(fixture["points"], unit=fixture["unit"], preview=True)
        root = ET.fromstring(svg)
        child_tags = {el.tag for el in root.iter() if el is not root}
        self.assertTrue(child_tags.issubset({"rect", "text", "title"}), f"Unexpected SVG tags: {child_tags}")
        self.assertEqual(child_tags, {"rect", "text", "title"})

        dist_dir = ROOT / "dist"
        if dist_dir.exists():
            bad_files = [
                p for p in dist_dir.rglob("*")
                if p.suffix.lower() in {".geojson", ".topojson", ".map", ".shp", ".kml"}
            ]
            self.assertEqual(bad_files, [])


if __name__ == "__main__":
    unittest.main()

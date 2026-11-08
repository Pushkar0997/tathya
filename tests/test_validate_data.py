"""Tests for scripts/validate_data.py. Each test carries its eval ID (see spec/evals.md)."""
import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_data as vd  # noqa: E402

TODAY = date(2026, 11, 8)


def ctx(production=True):
    c = vd.load_context(production=production, today=TODAY)
    return c


def good_doc():
    return {
        "id": "undernourishment-prevalence",
        "title": "Prevalence of undernourishment",
        "area": "people",
        "definition": "The share of a population whose usual food intake is too low to meet its energy needs.",
        "definition_source": "s1",
        "unit": "percent of population",
        "stale_after_months": 12,
        "sources": [{
            "id": "s1", "publisher": "Example Agency", "title": "Example report",
            "url": "https://www.fao.org/example-report", "source_type": "primary",
            "published": "2024-07-01", "retrieved": "2026-10-01",
        }],
        "points": [{
            "geography": "WLD", "period_kind": "calendar_year", "period": "2023", "value": 12.3,
            "status": "verified", "source_id": "s1",
            "evidence": "Table 1, page 4: world prevalence 12.3 percent in 2023",
            "entered_by": "agent:example", "verified_by": "reviewer-one", "verified_on": "2026-10-05",
        }],
    }


def codes(doc, production=True, stem=None):
    return [f.code for f in vd.validate_metric(doc, stem or doc.get("id", "x"), ctx(production))]


def with_point(**changes):
    d = good_doc()
    d["points"][0].update(changes)
    return d


class Golden(unittest.TestCase):
    def test_G01_valid_metric_passes(self):
        self.assertEqual(codes(good_doc()), [])

    def test_G02_financial_year_format(self):
        self.assertEqual(codes(with_point(period_kind="financial_year", period="2023-24")), [])
        self.assertEqual(codes(with_point(period_kind="financial_year", period="1999-00")), [])

    def test_G03_value_text_is_plain_decimal(self):
        self.assertEqual(vd.value_text(12.30), "12.3")
        self.assertEqual(vd.value_text(1200000), "1200000")
        self.assertEqual(vd.value_text(0.5), "0.5")
        self.assertTrue(vd.evidence_contains_value("Total 1,200,000 people", 1200000))

    def test_G04_staleness_boundary(self):
        self.assertFalse(vd.is_stale("2025-11-08", 12, TODAY))
        self.assertTrue(vd.is_stale("2025-11-07", 12, TODAY))

    def test_G05_add_months_clamps_day(self):
        self.assertEqual(vd.add_months(date(2024, 2, 29), 12), date(2025, 2, 28))
        self.assertEqual(vd.add_months(date(2026, 1, 31), 1), date(2026, 2, 28))

    def test_G06_states_config_is_complete(self):
        regions = json.loads((ROOT / "config" / "in_states.json").read_text())["regions"]
        self.assertEqual(len(regions), 36)
        self.assertEqual(len({r["code"] for r in regions}), 36)
        states = [r for r in regions if r["kind"] == "state"]
        self.assertEqual(len(states), 28)
        tiles = [tuple(r["tile"]) for r in states]
        self.assertEqual(len(set(tiles)), 28)
        self.assertIn("IN-CT", {r["code"] for r in regions})
        self.assertIn("IN-UT", {r["code"] for r in regions})

    def test_G07_fixtures_pass_in_preview(self):
        findings, count, _ = vd.validate_tree([ROOT / "fixtures" / "data"], ctx(production=False))
        self.assertEqual([str(x) for x in findings], [])
        self.assertEqual(count, 4)

    def test_G08_published_data_folder_passes(self):
        # Uses the real clock: future-dated points must fail, so no fixed date here.
        real = vd.load_context(production=True)
        findings, _, _ = vd.validate_tree([ROOT / "data"], real)
        self.assertEqual([str(x) for x in findings], [])


class Negative(unittest.TestCase):
    def test_N01_missing_evidence_is_rejected(self):
        d = good_doc(); d["points"][0]["evidence"] = "too short"
        self.assertIn("V-EVID-01", codes(d))

    def test_N02_value_missing_from_evidence_is_rejected(self):
        d = with_point(value=13.3)
        self.assertIn("V-EVID-02", codes(d))
        d = with_point(value=2.3, evidence="Table 1, page 4: world prevalence 12.3 percent in 2023")
        self.assertIn("V-EVID-02", codes(d))  # 2.3 must not match inside 12.3

    def test_N03_unknown_source_id_is_rejected(self):
        self.assertIn("V-SRC-01", codes(with_point(source_id="nope")))

    def test_N04_domain_not_on_allowlist_is_rejected(self):
        d = good_doc(); d["sources"][0]["url"] = "https://random-blog.example.net/post"
        self.assertIn("V-SRC-02", codes(d))

    def test_N05_http_url_is_rejected(self):
        d = good_doc(); d["sources"][0]["url"] = "http://www.fao.org/example-report"
        self.assertIn("V-SRC-03", codes(d))

    def test_N06_tier_mismatch_is_rejected(self):
        d = good_doc(); d["sources"][0]["url"] = "https://www.forbes.com/example"
        self.assertIn("V-SRC-04", codes(d))
        d["sources"][0]["source_type"] = "secondary"
        self.assertNotIn("V-SRC-04", codes(d))

    def test_N07_wrong_financial_year_is_rejected(self):
        for bad in ("2023-25", "2023-2024", "2023"):
            self.assertIn("V-PER-01", codes(with_point(period_kind="financial_year", period=bad)))

    def test_N08_bad_geography_is_rejected(self):
        for bad in ("India", "IN-XX", "ind", "IN"):
            self.assertIn("V-GEO-01", codes(with_point(geography=bad)))
        self.assertEqual(codes(with_point(geography="IN-MH")), [])

    def test_N09_value_must_be_number_and_percent_in_range(self):
        self.assertIn("V-VAL-01", codes(with_point(value="12.3")))
        self.assertIn("V-VAL-01", codes(with_point(value=True)))
        self.assertIn("V-VAL-02", codes(with_point(value=101.0, evidence="Table 1, page 4: prevalence 101.0 percent")))

    def test_N10_verifier_must_differ_from_enterer(self):
        self.assertIn("V-VER-02", codes(with_point(entered_by="Same-Person", verified_by="same-person")))

    def test_N11_estimate_needs_method(self):
        self.assertIn("V-EST-01", codes(with_point(status="estimate")))
        self.assertNotIn("V-EST-01", codes(with_point(status="estimate", estimate_method="Model described in annex 2")))

    def test_N12_banned_phrase_in_our_text_is_rejected(self):
        d = good_doc(); d["definition"] = "A shocking measure of hunger."
        self.assertIn("V-LANG-01", codes(d))
        d = good_doc(); d["points"][0]["evidence"] = "Quoted from the source, page 4: shocking 12.3 percent"
        self.assertNotIn("V-LANG-01", codes(d))  # evidence is a quotation, exempt

    def test_N13_duplicate_point_is_rejected(self):
        d = good_doc(); d["points"].append(copy.deepcopy(d["points"][0]))
        self.assertIn("V-DUP-01", codes(d))

    def test_N14_sample_is_blocked_in_production_only(self):
        d = with_point(status="sample")
        self.assertIn("V-SAMPLE-01", codes(d, production=True))
        self.assertNotIn("V-SAMPLE-01", codes(d, production=False))

    def test_N15_future_dates_are_rejected(self):
        self.assertIn("V-DATE-01", codes(with_point(verified_on="2027-01-01")))

    def test_N16_id_must_match_file_name(self):
        self.assertIn("V-ID-01", codes(good_doc(), stem="other-name"))

    def test_N17_derived_needs_formula_and_inputs(self):
        self.assertIn("V-DER-01", codes(with_point(status="derived")))

    def test_N18_missing_top_level_field_is_rejected(self):
        d = good_doc(); del d["unit"]
        self.assertIn("V-SCHEMA-01", codes(d))
        d = good_doc(); d["surprise"] = 1
        self.assertIn("V-SCHEMA-01", codes(d))

    def test_N19_sample_only_source_cannot_back_real_point(self):
        d = good_doc(); d["sources"][0]["url"] = "https://example.org/sample-report"
        self.assertIn("V-SRC-02", codes(d))


class Invariants(unittest.TestCase):
    def test_INV1_T_no_unsourced_number(self):
        d = good_doc(); d["sources"] = []
        self.assertIn("V-SRC-01", codes(d))
        self.assertIn("V-SRC-01", codes(with_point(source_id="missing")))

    def test_INV2_T_sample_never_ships(self):
        findings, _, _ = vd.validate_tree([ROOT / "fixtures" / "data"], ctx(production=True))
        self.assertTrue(findings)
        self.assertTrue(all(f.code == "V-SAMPLE-01" for f in findings))

    def test_INV3_T_evidence_must_contain_the_figure(self):
        self.assertIn("V-EVID-01", codes(with_point(evidence="")))
        self.assertIn("V-EVID-02", codes(with_point(value=99.9, evidence="Table 1, page 4: figure printed as 12.3")))

    def test_INV4_T_source_tier_must_match_allowlist(self):
        d = good_doc(); d["sources"][0]["url"] = "https://ourworldindata.org/example"
        self.assertIn("V-SRC-04", codes(d))

    def test_INV5_T_neutral_language_is_enforced(self):
        d = good_doc(); d["title"] = "The freebies tracker"
        self.assertIn("V-LANG-01", codes(d))

    def test_INV6_T_geography_period_and_units_are_pinned(self):
        self.assertIn("V-GEO-01", codes(with_point(geography="India")))
        self.assertIn("V-PER-01", codes(with_point(period="FY2023")))
        self.assertIn("V-VAL-01", codes(with_point(value="12.3")))


if __name__ == "__main__":
    unittest.main()

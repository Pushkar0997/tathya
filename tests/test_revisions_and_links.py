"""Tests for scripts/check_revisions.py (INV-10-T) and scripts/check_links.py (M1-LNK-01)."""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import check_links as cl  # noqa: E402
import check_revisions as cr  # noqa: E402
import test_validate_data as tvd  # noqa: E402


class RevisionAndLinkTests(unittest.TestCase):
    def test_INV10_T_check_revisions(self):
        base_doc = tvd.good_doc()
        # 1. Changed value without revision_note fails naming the point
        head_changed_no_note = copy.deepcopy(base_doc)
        head_changed_no_note["points"][0]["value"] = 13.0
        errs = cr.check_revisions({base_doc["id"]: base_doc}, {base_doc["id"]: head_changed_no_note})
        self.assertEqual(len(errs), 1)
        self.assertIn("undernourishment-prevalence", errs[0])
        self.assertIn("WLD", errs[0])
        self.assertIn("2023", errs[0])

        # 2. Changed value WITH revision_note passes
        head_changed_with_note = copy.deepcopy(head_changed_no_note)
        head_changed_with_note["points"][0]["revision_note"] = "Updated to 2024 FAO revision."
        self.assertEqual(
            cr.check_revisions({base_doc["id"]: base_doc}, {base_doc["id"]: head_changed_with_note}),
            [],
        )

        # 3. Removed point without revision_note fails naming the point
        head_removed = copy.deepcopy(base_doc)
        head_removed["points"] = []
        errs_removed = cr.check_revisions({base_doc["id"]: base_doc}, {base_doc["id"]: head_removed})
        self.assertEqual(len(errs_removed), 1)
        self.assertIn("undernourishment-prevalence", errs_removed[0])
        self.assertIn("2023", errs_removed[0])

        # 4. CLI exit code test with --base-dir and --head-dir
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base_dir = tmp_path / "base" / "people"
            head_dir = tmp_path / "head" / "people"
            base_dir.mkdir(parents=True)
            head_dir.mkdir(parents=True)
            (base_dir / "undernourishment-prevalence.json").write_text(json.dumps(base_doc), encoding="utf-8")
            (head_dir / "undernourishment-prevalence.json").write_text(
                json.dumps(head_changed_no_note), encoding="utf-8"
            )
            stderr_buf = io.StringIO()
            stdout_buf = io.StringIO()
            with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(stdout_buf):
                rc = cr.main(["--base-dir", str(tmp_path / "base"), "--head-dir", str(tmp_path / "head")])
            self.assertNotEqual(rc, 0)
            self.assertIn("undernourishment-prevalence", stderr_buf.getvalue())

    def test_M1_LNK_01_check_links_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = tmp_path / "data" / "people"
            data_dir.mkdir(parents=True)
            doc = tvd.good_doc()
            (data_dir / f"{doc['id']}.json").write_text(json.dumps(doc), encoding="utf-8")

            stdout_ok = io.StringIO()
            with contextlib.redirect_stdout(stdout_ok):
                rc_ok, _ = cl.check_links([tmp_path / "data"], requester=lambda u: 200)
            self.assertEqual(rc_ok, 0)
            self.assertIn("200", stdout_ok.getvalue())

            stdout_404 = io.StringIO()
            with contextlib.redirect_stdout(stdout_404):
                rc_404, _ = cl.check_links([tmp_path / "data"], requester=lambda u: 404)
            self.assertNotEqual(rc_404, 0)

            stdout_410 = io.StringIO()
            with contextlib.redirect_stdout(stdout_410):
                rc_410, _ = cl.check_links([tmp_path / "data"], requester=lambda u: 410)
            self.assertNotEqual(rc_410, 0)


if __name__ == "__main__":
    unittest.main()

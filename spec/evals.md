# evals.md — Evaluation

## 1. How to run

```
python3 -m unittest discover -s tests -v
python3 scripts/validate_data.py
python3 scripts/validate_data.py --data-dir fixtures/data --preview
python3 scripts/spec_lint.py --strict
```

All must exit 0 before any deploy. `bash scripts/spec-gate.sh ci` runs them together.

Tolerances: none. Every value is an exact string, date or code.

## 2. Golden values

Each ID appears in the name of the test that checks it.

| ID | Input | Expected |
|---|---|---|
| G-01 | A complete valid metric file | no findings |
| G-02 | Financial year periods `2023-24` and `1999-00` | accepted |
| G-03 | Values 12.30, 1200000, 0.5 | text `12.3`, `1200000`, `0.5`; "1,200,000" in evidence matches 1200000 |
| G-04 | Verified 2025-11-08 and 2025-11-07, 12 months, build date 2026-11-08 | not stale, stale |
| G-05 | 2024-02-29 plus 12 months; 2026-01-31 plus 1 month | 2025-02-28; 2026-02-28 |
| G-06 | `config/in_states.json` | 36 regions, 28 states with 28 distinct tiles, includes IN-CT and IN-UT |
| G-07 | `fixtures/data` in preview mode | 4 files, no findings |
| G-08 | The published `data/` folder, with the real clock | no findings |

Planned goldens, added to the table above with their tests in the milestone that implements them:

- G-20 — empty-data production build writes `dist/index.html` containing "No verified numbers have been published yet" (M0)
- G-21 — every page has `lang`, a unique title, a viewport tag, a skip link and one h1 (M0)
- G-22 — line chart SVG for a fixed input matches a reviewed golden file (M1)
- G-23 — paired-scale bar widths are proportional to the values (M1)
- G-24 — tile grid for fixed input places each state on its tile and shades four classes (M1)
- G-25 — generated tokens.css defines every token in design/tokens.json (M2)

## 3. Invariant tests

| ID | Invariant | Assertion |
|---|---|---|
| INV-1-T | No unsourced number | A metric with no sources, or a point whose source_id is undefined, yields V-SRC-01 |
| INV-2-T | No sample data in production | Validating `fixtures/data` in production mode yields only V-SAMPLE-01 findings, at least one |
| INV-3-T | Evidence contains the figure | Empty evidence yields V-EVID-01; evidence without the figure yields V-EVID-02 |
| INV-4-T | Tier matches allowlist | A source on `ourworldindata.org` declared primary yields V-SRC-04 |
| INV-5-T | Neutral language | The word "freebies" in a title yields V-LANG-01 |
| INV-6-T | Pinned conventions | Geography `India`, period `FY2023` and a text value yield V-GEO-01, V-PER-01, V-VAL-01 |

Planned invariant tests, moved into the table with their tests when implemented:

- INV-2-B — a production build fails when `data/` contains a SAMPLE point (M0)
- INV-5-B — a banned phrase in a template or authored data text fails the build (M1)
- INV-7-T — built pages reference no other origin and set no cookie (M1)
- INV-8-T — the tile grid output has only `rect`, `text` and `title` elements and no map files exist in `dist/` (M1)
- INV-9-T — a stale point shows the Stale badge on its page (M1)
- INV-10-T — a changed or removed value without a revision note fails `check_revisions.py` (M1)

## 4. Negative tests

**More important than positive tests.**

| ID | Assertion |
|---|---|
| N-01 | Evidence shorter than 20 characters is rejected (V-EVID-01) |
| N-02 | A value absent from the evidence is rejected, including 2.3 against "12.3" (V-EVID-02) |
| N-03 | An undefined source_id is rejected (V-SRC-01) |
| N-04 | A domain not on the allowlist is rejected (V-SRC-02) |
| N-05 | An http URL is rejected (V-SRC-03) |
| N-06 | A tier mismatch is rejected, and passes when declared correctly (V-SRC-04) |
| N-07 | Financial years `2023-25`, `2023-2024` and `2023` are rejected (V-PER-01) |
| N-08 | Geographies `India`, `IN-XX`, `ind` and `IN` are rejected (V-GEO-01) |
| N-09 | A text value, a boolean, and 101 percent are rejected (V-VAL-01, V-VAL-02) |
| N-10 | The same enterer and verifier is rejected, ignoring case (V-VER-02) |
| N-11 | An estimate without a method is rejected (V-EST-01) |
| N-12 | A banned phrase in a definition is rejected, but not inside quoted evidence (V-LANG-01) |
| N-13 | A duplicate geography, period kind and period is rejected (V-DUP-01) |
| N-14 | A SAMPLE point is rejected in production and accepted in preview (V-SAMPLE-01) |
| N-15 | A future verified_on date is rejected (V-DATE-01) |
| N-16 | An id that differs from the file name is rejected (V-ID-01) |
| N-17 | A derived point without formula and inputs is rejected (V-DER-01) |
| N-18 | A missing or unknown top-level field is rejected (V-SCHEMA-01) |
| N-19 | A sample-only source backing a real point is rejected (V-SRC-02) |

## 5. Telemetry
None. The site records nothing about visitors.

## 6. Pre-deploy gate
- [ ] All tests pass and `validate_data.py` passes in production mode
- [ ] Build clean
- [ ] `smoke.md` passes
- [ ] No SAMPLE or placeholder content is reachable in production

## 7. Recorded verdicts

*Written after a milestone, from a separate verifier's report. PASS only where a test or a recorded live result backs it. Never round up a PARTIAL.*

### 2026-11-08 — Scaffold verdict (correctness core only)

| Criterion | Verdict | Evidence |
|---|---|---|
| Validator rejects the failure modes in INV-1 to INV-6 | PASS | 33 tests in `tests/test_validate_data.py` pass |
| The tests would fail if a rule were removed | PASS | Five rules were removed one at a time and each removal made tests fail |
| Site builds | NOT STARTED | M0 |
| Deploys | NOT STARTED | M0 |

**Closes?** Not a milestone. This records the starting state only.

**Caveats carried forward:** the country check is a three-letter pattern only, and the source allowlist and ISO state codes were written from the author's knowledge and must be verified by opening each domain and the ISO listing before first use.

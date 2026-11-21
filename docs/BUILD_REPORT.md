# Build Report — Tathya (Milestones M0, M1, M2)

**Date:** 2026-11-09
**Scope:** Milestones M0, M1, and M2 from `spec/tasks.md`. Stopped at the end of M2; M3 was not started.
**Verification note:** Per `AGENTS.md` §1 and §4, the build agent does not tick task checkboxes in `spec/tasks.md` or grade its own work as verified. Every completed task is recorded as `done, unverified`, and tasks with environment-blocked parts (`M2-FNT-01` binary font download and `M2-HOM-01` / `M2-ARE-01` / `M2-MET-01` / `M2-PHN-01` headless browser visual comparison) are recorded as `partial`.

---

## 1. Task Status and Suggested Commit Messages (M0, M1, M2)

| Task ID | Milestone | Status | Suggested Commit Message | Supporting Evidence & Notes |
|---|---|---|---|---|
| **M0-BLD-01** | M0 | done, unverified | `feat(build): M0-BLD-01 add build_site.py, base.html and base.css` | `python3 scripts/build_site.py` writes `dist/index.html` containing `"No verified numbers have been published yet"`, copies `static/` to `dist/static/`, makes no network requests, and exits 0; tested by `test_G20_empty_build` (`G-20`). |
| **M0-BLD-02** | M0 | done, unverified | `feat(build): M0-BLD-02 run validate_data before build and add --preview mode` | Default production build runs `validate_data.validate_tree` first, prints errors to `stderr` and exits non-zero without writing `dist/` when SAMPLE or invalid data is present; `--preview` reads `fixtures/data` and renders `"Design preview. All values are SAMPLE."` on every page; tested by `test_INV2_B_sample_fails_production_build` (`INV-2-B`). |
| **M0-BLD-03** | M0 | done, unverified | `feat(pages): M0-BLD-03 generate home, area, contribute and about page set` | Generates `index.html`, `people.html`, `planet.html`, `public-money.html`, `industry.html`, `contribute.html`, and `about.html`, each with `<!doctype html>`, `lang="en"`, unique `<title>`, viewport meta tag, `#main-content` skip link, and exactly one `<h1>`; tested by `test_G21_page_structure` (`G-21`). |
| **M0-DEP-01** | M0 | done, unverified | `ci(pages): M0-DEP-01 add GitHub Pages workflow and record action versions in D-015` | `.github/workflows/pages.yml` triggers on push to `main`, Mondays `03:00 UTC` (`0 3 * * 1`), and `workflow_dispatch`, runs `bash scripts/spec-gate.sh ci` and `python3 scripts/build_site.py`, and deploys via `actions/configure-pages@v5`, `actions/upload-pages-artifact@v4`, and `actions/deploy-pages@v4`; recorded in `spec/decisions.md` (`D-015`). |
| **M0-DEP-02** | M0 | done, unverified | `docs(deploy): M0-DEP-02 document GitHub Actions Pages source, local preview and rollback` | `docs/DEPLOY.md` documents setting Pages source to GitHub Actions, local preview via `python3 -m http.server -d dist`, and rollback via `git revert`. |
| **M0-TST-01** | M0 | done, unverified | `test(build): M0-TST-01 add tests/test_build.py for G-20, G-21 and INV-2-B` | `tests/test_build.py` tests `G-20`, `G-21`, and `INV-2-B` (including placing a fixture copy into `data/people/` and verifying the production build exits non-zero without creating `dist/`). |
| **M1-CHT-01** | M1 | done, unverified | `feat(charts): M1-CHT-01 add SVG line chart generator and G-22 golden test` | `site/charts.py:line_chart` emits inline SVG with `role="img"`, `aria-label`, y-axis starting at `0`, and first/last period labels; matches `tests/goldens/line_chart.svg` in `test_G22_line_chart_golden` (`G-22`). |
| **M1-CHT-02** | M1 | done, unverified | `feat(charts): M1-CHT-02 add paired-scale bar chart generator and G-23 test` | `site/charts.py:paired_scale_bars` draws two bars with widths proportional to values on a shared scale and rejects mismatched units; tested by `test_G23_paired_scale_bars` (`G-23`). |
| **M1-CHT-03** | M1 | done, unverified | `feat(charts): M1-CHT-03 add Indian state tile grid SVG generator for G-24 and INV-8-T` | `site/charts.py:state_tile_grid` places all 28 states by `tile` `[row, col]`, places 8 union territories in a separate row beneath, shades 4 equal-interval classes, labels with `abbr`, and contains only `rect`, `text`, and `title` child elements; tested by `test_G24_state_tile_grid` (`G-24`) and `test_INV8_T_tile_grid_no_maps` (`INV-8-T`). |
| **M1-PGE-01** | M1 | done, unverified | `feat(pages): M1-PGE-01 implement area page template with metric rows and empty state` | `templates/area.html` and `site/pages.py` render each area's empty state when no metrics exist and list title, latest value, period, and source/status badges when metrics exist; tested by `test_M1_pages_area_and_metric_rendering`. |
| **M1-PGE-02** | M1 | done, unverified | `feat(pages): M1-PGE-02 implement metric page template with charts, source records and revisions` | `templates/metric.html` renders the definition, headline world/national value, line chart, full source record for every point shown (publisher, link, source type, published, retrieved, evidence, verified by, verified on), state tile grid when state points exist, and `"Updated"` badge/note when `revision_note` is present; tested by `test_M1_pages_area_and_metric_rendering`. |
| **M1-STL-01** | M1 | done, unverified | `feat(staleness): M1-STL-01 compute build-time staleness badges with --today override` | `site/staleness.py` computes staleness from `verified_on` + `stale_after_months` against UTC clock (or `--today YYYY-MM-DD`) and renders the `Stale` badge; tested by `test_INV9_T_stale_badge` (`INV-9-T`). |
| **M1-LNG-01** | M1 | done, unverified | `feat(lint): M1-LNG-01 scan templates and authored data text for banned phrases at build time` | `scripts/build_site.py:scan_templates_for_banned_phrases` and `validate_data.py` fail the build naming the offending file when any phrase from `config/banned_phrases.txt` appears; tested by `test_INV5_B_banned_phrase_in_template_or_data` (`INV-5-B`). |
| **M1-NET-01** | M1 | done, unverified | `feat(security): M1-NET-01 scan dist/ for external origins, cookies and map files` | `scripts/build_site.py:scan_dist` inspects all built HTML/CSS/files and fails on external `script`, `link`, `img`, `iframe`, CSS `url()`, `@import`, cookies, or `.geojson`/`.topojson`/`.map` files; tested by `test_INV7_T_no_external_requests_or_cookies` (`INV-7-T`). |
| **M1-REV-01** | M1 | done, unverified | `feat(ci): M1-REV-01 add check_revisions.py and run on pull requests` | `scripts/check_revisions.py` compares base and head metrics (via git ref or directories) and exits non-zero naming any point whose value changed or was removed without a `revision_note`; wired into `.github/workflows/pages.yml` on `pull_request`; tested by `test_INV10_T_check_revisions` (`INV-10-T`). |
| **M1-LNK-01** | M1 | done, unverified | `feat(ci): M1-LNK-01 add check_links.py and weekly link-check.yml workflow` | `scripts/check_links.py` (stdlib `urllib.request`) requests every source URL, prints a status table, and exits non-zero on 404 or 410; `.github/workflows/link-check.yml` runs weekly without blocking deploys; tested by `test_M1_LNK_01_check_links_statuses`. |
| **M2-CSS-01** | M2 | done, unverified | `feat(css): M2-CSS-01 add make_tokens.py generating static/css/tokens.css` | `scripts/make_tokens.py` writes `static/css/tokens.css` from `design/tokens.json`, defining all shared and per-area colour, font, type scale, layout, and sticker tokens scoped via `body.area-<area>`; tested by `test_G25_tokens_css` (`G-25`). |
| **M2-FNT-01** | M2 | **partial** | `chore(fonts): M2-FNT-01 add static/fonts/LICENSES.md and fallback font stacks (fonts pending)` | **Done:** `static/fonts/LICENSES.md` naming SIL OFL-1.1 licences for all 10 families, fallback font stacks configured per area in `tokens.css` and `base.css`, zero Google Fonts/remote requests (`INV-7`). **Missing:** Binary Latin/Devanagari-subset `.woff2` files in `static/fonts/`, because outbound internet access is disabled in the build sandbox (`fonts pending` logged in `AGENT_LOG.md`). |
| **M2-HOM-01** | M2 | **partial** | `feat(ui): M2-HOM-01 implement home page layout matching reference structure` | **Done:** Hero with Devanagari watermark, proportional paired scale (rendered when comparable points exist, omitted when empty), four area tiles in their respective packs, recently verified list, statement band, and footer; tested in `test_M2_A11_02_and_responsive_and_packs`. **Missing:** Side-by-side headless browser visual screenshot verification against `design/reference/home.html` (`visual match not checked`). |
| **M2-ARE-01** | M2 | **partial** | `feat(ui): M2-ARE-01 implement four area pages with area packs and SVG motifs` | **Done:** `people.html`, `planet.html`, `public-money.html`, and `industry.html` rendered in their own colour/font packs and hero SVG/CSS motifs (`concentric rings`, `wave lines`, `ledger rules + margin`, `tilted orbit ellipses`), with measures list and source record card. **Missing:** Side-by-side headless browser screenshot comparison (`visual match not checked`). |
| **M2-MET-01** | M2 | **partial** | `feat(ui): M2-MET-01 implement metric page layout matching reference structure` | **Done:** Marigold/indigo metric hero, breadcrumb, split display title, definition, giant figure with SAMPLE sticker in preview, indigo "Over time" chart panel, rani-topped Source record card, lilac "By Indian state" tile grid band, and full point source records ledger. **Missing:** Side-by-side headless browser screenshot comparison (`visual match not checked`). |
| **M2-PHN-01** | M2 | **partial** | `feat(ui): M2-PHN-01 add responsive phone layout rules and details menu` | **Done:** `@media (max-width: 640px)` rules in `static/css/base.css` collapsing desktop nav into a `<details>` Menu button (`min-height: 44px`), scaling titles/numbers to phone tokens (`104px`, `36px`, `16px`), stacking tiles and source card rows, and setting `overflow-x: hidden`. **Missing:** Live browser measurement at 360 px width and 390 px screenshot comparison (`visual match not checked`). |
| **M2-A11-01** | M2 | done, unverified | `feat(a11y): M2-A11-01 add scripts/check_contrast.py verifying WCAG ratios` | `scripts/check_contrast.py` computes WCAG 2.x luminance contrast for all 38 colour pairs in `design/tokens.json` and exits non-zero below 4.5 (3.0 for large); passes all 38 pairs and tested by `test_M2_A11_01_contrast`. |
| **M2-A11-02** | M2 | done, unverified | `feat(a11y): M2-A11-02 enforce focus ring, skip link, landmarks, reduced motion and text badges` | Visible `:focus-visible` outline, `.skip-link` to `#main-content`, `<header>`/`<nav>`/`<main>`/`<footer>` landmarks, `@media (prefers-reduced-motion: reduce)`, and text labels on every badge/tile/chart; tested in `test_G21_page_structure` and `test_M2_A11_02_and_responsive_and_packs`. |
| **M2-CTB-01** | M2 | done, unverified | `feat(pages): M2-CTB-01 render contribute and about pages from CONTRIBUTING.md and README.md` | `dist/contribute.html` and `dist/about.html` render directly from `CONTRIBUTING.md` and `README.md` with no added claims; tested in `test_G21_page_structure`. |
| **M2-EMP-01** | M2 | done, unverified | `feat(pages): M2-EMP-01 add per-area empty states styled in each area's pack` | When an area has zero published metrics, its page renders its empty state card inside `body.area-<area>` using that area's pack tokens; tested in `test_M2_A11_02_and_responsive_and_packs`. |
| **M2-DOC-01** | M2 | done, unverified | `docs(spec): M2-DOC-01 update README.md, BRIEF.md, AGENT_LOG.md and claims register` | Updated `README.md`, `BRIEF.md` (66 lines < 80 lines), `AGENT_LOG.md`, and `spec/architecture.md` §8 claims register; `python3 scripts/spec_lint.py --strict` passes with 0 errors and 0 warnings. |

---

## 2. Supporting Command Outputs

```text
$ python3 -m unittest discover -s tests -v
test_G20_empty_build (test_build.BuildTests.test_G20_empty_build) ... ok
test_G21_page_structure (test_build.BuildTests.test_G21_page_structure) ... ok
test_INV2_B_sample_fails_production_build (test_build.BuildTests.test_INV2_B_sample_fails_production_build) ... ok
test_INV5_B_banned_phrase_in_template_or_data (test_build.BuildTests.test_INV5_B_banned_phrase_in_template_or_data) ... ok
test_INV7_T_no_external_requests_or_cookies (test_build.BuildTests.test_INV7_T_no_external_requests_or_cookies) ... ok
test_INV9_T_stale_badge (test_build.BuildTests.test_INV9_T_stale_badge) ... ok
test_M1_pages_area_and_metric_rendering (test_build.BuildTests.test_M1_pages_area_and_metric_rendering) ... ok
test_G22_line_chart_golden (test_charts.ChartTests.test_G22_line_chart_golden) ... ok
test_G23_paired_scale_bars (test_charts.ChartTests.test_G23_paired_scale_bars) ... ok
test_G24_state_tile_grid (test_charts.ChartTests.test_G24_state_tile_grid) ... ok
test_INV8_T_tile_grid_no_maps (test_charts.ChartTests.test_INV8_T_tile_grid_no_maps) ... ok
test_G25_tokens_css (test_m2.M2Tests.test_G25_tokens_css) ... ok
test_M2_A11_01_contrast (test_m2.M2Tests.test_M2_A11_01_contrast) ... ok
test_M2_A11_02_and_responsive_and_packs (test_m2.M2Tests.test_M2_A11_02_and_responsive_and_packs) ... ok
test_INV10_T_check_revisions (test_revisions_and_links.RevisionAndLinkTests.test_INV10_T_check_revisions) ... ok
test_M1_LNK_01_check_links_statuses (test_revisions_and_links.RevisionAndLinkTests.test_M1_LNK_01_check_links_statuses) ... ok
test_G01_valid_metric_passes (test_validate_data.Golden.test_G01_valid_metric_passes) ... ok
test_G02_financial_year_format (test_validate_data.Golden.test_G02_financial_year_format) ... ok
test_G03_value_text_is_plain_decimal (test_validate_data.Golden.test_G03_value_text_is_plain_decimal) ... ok
test_G04_staleness_boundary (test_validate_data.Golden.test_G04_staleness_boundary) ... ok
test_G05_add_months_clamps_day (test_validate_data.Golden.test_G05_add_months_clamps_day) ... ok
test_G06_states_config_is_complete (test_validate_data.Golden.test_G06_states_config_is_complete) ... ok
test_G07_fixtures_pass_in_preview (test_validate_data.Golden.test_G07_fixtures_pass_in_preview) ... ok
test_G08_published_data_folder_passes (test_validate_data.Golden.test_G08_published_data_folder_passes) ... ok
test_INV1_T_no_unsourced_number (test_validate_data.Invariants.test_INV1_T_no_unsourced_number) ... ok
test_INV2_T_sample_never_ships (test_validate_data.Invariants.test_INV2_T_sample_never_ships) ... ok
test_INV3_T_evidence_must_contain_the_figure (test_validate_data.Invariants.test_INV3_T_evidence_must_contain_the_figure) ... ok
test_INV4_T_source_tier_must_match_allowlist (test_validate_data.Invariants.test_INV4_T_source_tier_must_match_allowlist) ... ok
test_INV5_T_neutral_language_is_enforced (test_validate_data.Invariants.test_INV5_T_neutral_language_is_enforced) ... ok
test_INV6_T_geography_period_and_units_are_pinned (test_validate_data.Invariants.test_INV6_T_geography_period_and_units_are_pinned) ... ok
test_N01_missing_evidence_is_rejected (test_validate_data.Negative.test_N01_missing_evidence_is_rejected) ... ok
test_N02_value_missing_from_evidence_is_rejected (test_validate_data.Negative.test_N02_value_missing_from_evidence_is_rejected) ... ok
test_N03_unknown_source_id_is_rejected (test_validate_data.Negative.test_N03_unknown_source_id_is_rejected) ... ok
test_N04_domain_not_on_allowlist_is_rejected (test_validate_data.Negative.test_N04_domain_not_on_allowlist_is_rejected) ... ok
test_N05_http_url_is_rejected (test_validate_data.Negative.test_N05_http_url_is_rejected) ... ok
test_N06_tier_mismatch_is_rejected (test_validate_data.Negative.test_N06_tier_mismatch_is_rejected) ... ok
test_N07_wrong_financial_year_is_rejected (test_validate_data.Negative.test_N07_wrong_financial_year_is_rejected) ... ok
test_N08_bad_geography_is_rejected (test_validate_data.Negative.test_N08_bad_geography_is_rejected) ... ok
test_N09_value_must_be_number_and_percent_in_range (test_validate_data.Negative.test_N09_value_must_be_number_and_percent_in_range) ... ok
test_N10_verifier_must_differ_from_enterer (test_validate_data.Negative.test_N10_verifier_must_differ_from_enterer) ... ok
test_N11_estimate_needs_method (test_validate_data.Negative.test_N11_estimate_needs_method) ... ok
test_N12_banned_phrase_in_our_text_is_rejected (test_validate_data.Negative.test_N12_banned_phrase_in_our_text_is_rejected) ... ok
test_N13_duplicate_point_is_rejected (test_validate_data.Negative.test_N13_duplicate_point_is_rejected) ... ok
test_N14_sample_is_blocked_in_production_only (test_validate_data.Negative.test_N14_sample_is_blocked_in_production_only) ... ok
test_N15_future_dates_are_rejected (test_validate_data.Negative.test_N15_future_dates_are_rejected) ... ok
test_N16_id_must_match_file_name (test_validate_data.Negative.test_N16_id_must_match_file_name) ... ok
test_N17_derived_needs_formula_and_inputs (test_validate_data.Negative.test_N17_derived_needs_formula_and_inputs) ... ok
test_N18_missing_top_level_field_is_rejected (test_validate_data.Negative.test_N18_missing_top_level_field_is_rejected) ... ok
test_N19_sample_only_source_cannot_back_real_point (test_validate_data.Negative.test_N19_sample_only_source_cannot_back_real_point) ... ok

----------------------------------------------------------------------
Ran 49 tests in 0.589s

OK

$ python3 scripts/validate_data.py
validate_data (production): 0 file(s), 0 error(s), 0 stale point(s) - OK

$ python3 scripts/validate_data.py --data-dir fixtures/data --preview
validate_data (preview): 4 file(s), 0 error(s), 0 stale point(s) - OK

$ python3 scripts/check_contrast.py
check_contrast: 38 pair(s), 0 failure(s) - OK

$ python3 scripts/spec_lint.py --strict

spec_lint: 0 error(s), 0 warning(s) — OK

$ bash scripts/spec-gate.sh ci

spec_lint: 0 error(s), 0 warning(s) — OK
```

---

## 3. Defaults Chosen for Ambiguities

1. **Output file paths in `dist/` (`M0-BLD-03`, `M1-PGE-01`, `M1-PGE-02`, `M2-ARE-01`):**
   - *Ambiguity:* `M0-BLD-01` specifies `dist/index.html` and `dist/static/`, while `M2-ARE-01` references the mockup names `area-people.html`, `area-planet.html`, `area-money.html`, `area-industry.html` and `CONTRACT.md` pins the area names `people`, `planet`, `public-money`, `industry`. Meanwhile, `G-21` requires every HTML page in `dist/` to have a unique `<title>`, preventing duplicate HTML alias files.
   - *Default chosen:* Write home to `dist/index.html`, area pages to `dist/people.html`, `dist/planet.html`, `dist/public-money.html`, `dist/industry.html`, contribute to `dist/contribute.html`, about to `dist/about.html`, and metric pages to `dist/metrics/<id>.html`, using relative links (`root_prefix`) so navigation works both on `http.server` locally and under a GitHub Pages repository subpath (`/tathya/`).
2. **Python `site/` package name vs. standard library `site` (`spec/architecture.md`, `M1-CHT-01`):**
   - *Ambiguity:* `spec/architecture.md` §2 places the project's Python modules (`charts.py`, `pages.py`, `staleness.py`) in `site/`, which collides with Python's built-in `site` module imported automatically at interpreter startup (`sys.modules['site']`).
   - *Default chosen:* Keep the `site/` folder and module names exactly as specified (`site/charts.py`, `site/pages.py`, `site/staleness.py`) and set `site.__path__ = [str(ROOT / "site")]` in scripts and tests so `from site import charts, pages, staleness` works seamlessly without breaking stdlib `site`.
3. **Paired-scale data selection on the Home page (`M1-CHT-02`, `M2-HOM-01`):**
   - *Ambiguity:* `M2-HOM-01` states that the home page paired scale uses "real data when two comparable verified points exist, otherwise omitted", whereas in `--preview` mode all fixture points have `status: "sample"`.
   - *Default chosen:* In production mode, render the paired scale only when at least two `verified` points share the same `unit` and `period` (so in an empty `data/` build it is omitted); in `--preview` mode, also allow `sample` points sharing a `unit` and `period` so the paired scale is rendered and previewable.
4. **Source records on Metric pages (`M1-PGE-02`, `M2-MET-01`):**
   - *Ambiguity:* `design/reference/metric.html` shows a single primary Source record card beside the "Over time" chart, whereas `M1-PGE-02` requires "the source record for every point shown (publisher, link, source type, published, retrieved, evidence, verified by, verified on)".
   - *Default chosen:* Render the primary Source record card beside the "Over time" chart (matching `design/reference/metric.html`) AND include an "All points and source records" ledger section below the chart/tile-grid displaying the complete source record, badges, staleness, and revision notes for every point shown on the page.

---

## 4. Noticed, Did Not Fix

1. **Starter config caveats (`config/source_allowlist.json`, `config/in_states.json`):** As noted in the spec session entry in `AGENT_LOG.md`, the allowlisted domains and ISO 3166-2:IN state codes were authored without live verification, and `validate_data.py` checks country codes using a 3-letter regex (`^[A-Z]{3}$`). Left untouched because both files and `scripts/validate_data.py` are protected files.
2. **Mockup tile abbreviations vs. ISO codes (`design/reference/metric.html`):** The reference mockups use `CG` and `UK` as display labels for `IN-CT` (Chhattisgarh) and `IN-UT` (Uttarakhand) and load Google Fonts. Left untouched because `design/reference/` is protected; production derives tile positions and `abbr` labels from `config/in_states.json` and makes zero external font requests.
3. **`scripts/spec_lint.py` `check_eval_traceability` regex:** Line 122 of `scripts/spec_lint.py` matches `r"\|\s*((?:G|N)-\d+|INV-\d+-T)\s*\|"`, which does not inspect `-B` invariant IDs (`INV-2-B`, `INV-5-B`). Left untouched because `scripts/spec_lint.py` is a protected file; both `test_INV2_B_sample_fails_production_build` and `test_INV5_B_banned_phrase_in_template_or_data` are implemented in `tests/test_build.py`.

---

## 5. Protected Files Checksum Verification (`sha256sum -c docs/PROTECTED_SHA256.txt`)

```text
$ sha256sum -c docs/PROTECTED_SHA256.txt
CONTRACT.md: OK
scripts/validate_data.py: OK
scripts/spec_lint.py: OK
tests/test_validate_data.py: OK
config/banned_phrases.txt: OK
config/in_states.json: OK
config/source_allowlist.json: OK
design/tokens.json: OK
design/reference/area-industry.html: OK
design/reference/area-money.html: OK
design/reference/area-people.html: OK
design/reference/area-planet.html: OK
design/reference/home.html: OK
design/reference/metric.html: OK
design/reference/phone-home.html: OK
design/reference/phone-metric.html: OK
design/reference/phone-people.html: OK
```

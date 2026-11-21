# AGENT_LOG

Append-only. **Newest entry at the top.** Never edit past entries — append corrections as new ones.

Every session writes an entry, including failed sessions. "Noticed, did not fix" may not be empty without a reason.

---

## 2026-11-09 — Build Agent — Milestones M0, M1 and M2 build session

**Milestone:** M0, M1 and M2 (stopped at the end of M2; M3 not started)
**Tasks attempted:**
- M0: `M0-BLD-01`, `M0-BLD-02`, `M0-BLD-03`, `M0-DEP-01`, `M0-DEP-02`, `M0-TST-01`
- M1: `M1-CHT-01`, `M1-CHT-02`, `M1-CHT-03`, `M1-PGE-01`, `M1-PGE-02`, `M1-STL-01`, `M1-LNG-01`, `M1-NET-01`, `M1-REV-01`, `M1-LNK-01`
- M2: `M2-CSS-01`, `M2-FNT-01`, `M2-HOM-01`, `M2-ARE-01`, `M2-MET-01`, `M2-PHN-01`, `M2-A11-01`, `M2-A11-02`, `M2-CTB-01`, `M2-EMP-01`, `M2-DOC-01`
**Landed:**
- `scripts/build_site.py`, `site/__init__.py`, `site/charts.py`, `site/pages.py`, `site/staleness.py`
- `templates/base.html`, `templates/home.html`, `templates/area.html`, `templates/metric.html`, `templates/contribute.html`, `templates/about.html`
- `scripts/make_tokens.py`, `static/css/tokens.css`, `static/css/base.css`, `static/fonts/LICENSES.md`
- `scripts/check_revisions.py`, `scripts/check_links.py`, `scripts/check_contrast.py`
- `.github/workflows/pages.yml`, `.github/workflows/link-check.yml`, `docs/DEPLOY.md`, `docs/BUILD_REPORT.md`
- `tests/test_build.py`, `tests/test_charts.py`, `tests/test_revisions_and_links.py`, `tests/test_m2.py`, `tests/goldens/line_chart.svg` (49 total tests, all passing)
- Updated `spec/evals.md`, `spec/decisions.md` (`D-015`), `spec/architecture.md`, `README.md`, `BRIEF.md`
**Did not land:**
- **fonts pending** (`M2-FNT-01` — partial): The build container has no outbound internet access to download binary `.woff2` files from Google Fonts. Fallback stacks from `design/tokens.json` and `static/fonts/LICENSES.md` are in place, with zero external font requests (`INV-7`).
- **visual match not checked** (`M2-HOM-01`, `M2-ARE-01`, `M2-MET-01`, `M2-PHN-01` — partial): Headless Chromium timed out inside the container sandbox (`RPC::DEADLINE_EXCEEDED`), so side-by-side 1360 px and 390 px screenshots against `design/reference/` could not be visually inspected in this session. HTML/CSS structure, tokens, motifs, and responsive rules (`@media (max-width: 640px)`) are implemented and tested structurally.
- Independent verification of M0–M2 tasks (`spec/tasks.md` checkboxes left unticked per `AGENTS.md` §4).
**Blockers:** Offline sandbox environment prevents downloading external `.woff2` font files; headless Chromium hangs in container without display/bus access.
**Noticed, did not fix:**
- Protected files (`config/source_allowlist.json`, `config/in_states.json`, `design/reference/*.html`, `scripts/validate_data.py`, `scripts/spec_lint.py`) are untouched and pass `sha256sum -c docs/PROTECTED_SHA256.txt`.
- In `scripts/spec_lint.py`, `check_eval_traceability` regex `r"\|\s*((?:G|N)-\d+|INV-\d+-T)\s*\|"` only checks `-T` invariant rows (not `INV-2-B` or `INV-5-B`), though both `test_INV2_B_sample_fails_production_build` and `test_INV5_B_banned_phrase_in_template_or_data` are implemented and executed by `unittest`.
- On GitHub, `actions/configure-pages` released `v6.0.0` (Node 24) in March 2026 while GitHub's official Pages custom-workflow documentation still specifies `actions/configure-pages@v5`, `actions/upload-pages-artifact@v4`, and `actions/deploy-pages@v4`; recorded in `D-015` in `spec/decisions.md`.
**Spec changes:**
- `spec/evals.md`: moved `G-20`, `G-21`, `G-22`, `G-23`, `G-24`, `G-25` and `INV-2-B`, `INV-5-B`, `INV-7-T`, `INV-8-T`, `INV-9-T`, `INV-10-T` into the active tables.
- `spec/decisions.md`: added `D-015` for GitHub Pages official action major versions.
- `spec/architecture.md`: updated §4 capability register and §8 architecture claims register with implementing scripts and test names.
- `README.md` and `BRIEF.md`: updated to reflect M0–M2 completion.
**Command outputs recorded after tasks:**
```
$ python3 -m unittest discover -s tests -q
----------------------------------------------------------------------
Ran 49 tests in 0.604s

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
**Next action:** Run a separate verifier session using `docs/prompts/verify.md` to verify M0–M2, supply self-hosted `.woff2` font subsets (`M2-FNT-01`), perform a human visual side-by-side review against `design/reference/`, and proceed to human-led M3 data entry.

---

## 2026-11-09 — Build Agent — Step 0 plan and baseline check

**Milestone:** M0 — Skeleton, CI and deploy (followed by M1 and M2; stopping at the end of M2)
**First task:** M0-BLD-01 — Create `scripts/build_site.py`, `templates/base.html` and `static/css/base.css`
**Baseline verification output:**
```
Ran 33 tests in 0.018s
OK
validate_data (production): 0 file(s), 0 error(s), 0 stale point(s) - OK
spec_lint: 0 error(s), 0 warning(s) — OK
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
**Ambiguities spotted and defaults chosen:**
1. **Output file paths in `dist/` (M0-BLD-03, M1-PGE-01, M1-PGE-02, M2-ARE-01):** `M0-BLD-01` specifies `dist/index.html` and `dist/static/`, while `M2-ARE-01` references `area-people.html`, `area-planet.html`, `area-money.html`, `area-industry.html` (the names in `design/reference/`) and `CONTRACT.md` uses area IDs `people`, `planet`, `public-money`, `industry`. `G-21` requires every HTML page in `dist/` to have a unique `<title>`, so duplicate HTML alias files cannot be emitted. Default chosen: output home at `dist/index.html`, area pages at `dist/people.html`, `dist/planet.html`, `dist/public-money.html`, `dist/industry.html`, metric pages at `dist/metrics/<id>.html`, contribute at `dist/contribute.html`, and about at `dist/about.html`, using relative links so the site works both at a root domain and under a GitHub Pages project subpath (`/tathya/`).
2. **Python `site/` package name collision (`spec/architecture.md`, M1-CHT-01):** `spec/architecture.md` §2 specifies `site/` for Python modules (`charts`, `pages`, `staleness`), which collides with Python's standard-library `site` module already loaded in `sys.modules['site']` at startup. Default chosen: create `site/__init__.py`, `site/charts.py`, `site/pages.py`, `site/staleness.py` as required by the spec, and set `site.__path__ = [str(ROOT / "site")]` in scripts and tests so `from site import charts, pages, staleness` works alongside stdlib `site`.
3. **Self-hosted fonts in an offline build container (M2-FNT-01):** The sandbox build environment has no outbound network access to download binary `.woff2` files from Google Fonts. Following `M2-FNT-01` ("IF fonts cannot be downloaded THE agent SHALL keep the fallback stacks and record 'fonts pending' in AGENT_LOG.md"), we keep the fallback font stacks active, create `static/fonts/LICENSES.md`, and record "fonts pending" in `AGENT_LOG.md`.
4. **Paired-scale selection on the home page (M1-CHT-02, M2-HOM-01):** `M2-HOM-01` states "real data when two comparable verified points exist, otherwise omitted", while in `--preview` mode all fixture points have status `sample`. Default chosen: in production mode, render the paired scale only when at least two `verified` points share the same `unit` and `period`; in `--preview` mode, also allow `sample` points sharing a `unit` and `period` so the paired scale is rendered and testable on the preview home page.
**Noticed, did not fix:** Protected files (`design/reference/*.html`, `config/*`) contain the caveats noted in the prior session; left untouched per protected-files rule.
**Next action:** Execute M0-BLD-01.

---

## 2026-11-08 — Claude Sonnet 5.5 / claude.ai — spec session

**Milestone:** pre-M0 — specification and correctness core
**Tasks attempted:** none from tasks.md; this session wrote the spec, design and validator
**Landed:** CONTRACT.md, AGENTS.md, BRIEF.md and spec/ files; design/ with four packs and nine reference pages; `scripts/validate_data.py` with 33 tests in `tests/test_validate_data.py`, all passing; five deliberate rule removals each made tests fail; `scripts/spec_lint.py --strict` passes; fixtures validate in preview and are refused in production
**Did not land:** the site builder, templates, deploy workflow and fonts (M0 to M2); no independent verification of this session's work has happened
**Blockers:** none for the build; the owner must later decide the data licence (D-011) and open each allowlisted domain
**Noticed, did not fix:** the source allowlist and the ISO 3166-2:IN state codes were written from the author's knowledge and are unverified against the live sites and the ISO listing; the country check is a three-letter pattern only; mockup tile labels CG and UK differ from ISO codes IN-CT and IN-UT; the mockups load Google Fonts, which production must not
**Spec changes:** all files created in this session
**Next action:** M0-BLD-01 — create `scripts/build_site.py` starting from the empty-state requirement in spec/tasks.md

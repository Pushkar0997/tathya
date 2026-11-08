# tasks.md — Backlog

One task = one change = one commit. Tick the box and add a one-line note only after the verifier's report.

Task ID format: `M<milestone>-<area>-<number>`. Acceptance criteria use the form WHEN trigger THE system SHALL response. Each task names the eval IDs it must satisfy; when you implement a planned eval, add its row to the table in spec/evals.md in the same commit.

---

## M0 — Skeleton, CI and deploy

### BLD
- [ ] **M0-BLD-01** Create `scripts/build_site.py`, `templates/base.html` and `static/css/base.css`. AC: WHEN run on a fresh clone with an empty `data/` THE build SHALL write `dist/index.html` containing the sentence "No verified numbers have been published yet", copy `static/` to `dist/static/`, make no network request, and exit 0. Evals: G-20.
- [ ] **M0-BLD-02** Make the default build run `validate_data.py` in production mode first. AC: WHEN any validation error exists THE build SHALL print the errors and exit non-zero without writing `dist/`. WHEN `--preview` is given THE build SHALL read `fixtures/data`, allow SAMPLE points, and put a visible banner "Design preview. All values are SAMPLE." on every page. Evals: INV-2-B.
- [ ] **M0-BLD-03** Generate the page set: home, one page per area, contribute, about. AC: WHEN built THE site SHALL contain valid HTML5 pages each with `lang="en"`, a unique `title`, a viewport meta tag, a skip link and one `h1`. Evals: G-21.

### DEP
- [ ] **M0-DEP-01** Write `.github/workflows/pages.yml`. AC: WHEN a push to main happens, or every Monday 03:00 UTC, THE workflow SHALL install requirements, run `bash scripts/spec-gate.sh ci`, build in production mode, and publish `dist/` using GitHub's official Pages actions with minimal permissions. Use the current major versions from GitHub's documentation and record them in spec/decisions.md.
- [ ] **M0-DEP-02** Write `docs/DEPLOY.md`. AC: THE file SHALL state that Pages source must be set to GitHub Actions, how to preview locally with `python3 -m http.server -d dist`, and that rollback is `git revert` of the bad commit.

### TST
- [ ] **M0-TST-01** Add `tests/test_build.py` for M0-BLD-01 to M0-BLD-03. AC: WHEN `data/` holds a copy of a fixture THE test SHALL assert the production build exits non-zero. Evals: G-20, G-21, INV-2-B.

---

## M1 — Pages and charts from fixtures

### CHT
- [ ] **M1-CHT-01** Write `site/charts.py` line chart. AC: WHEN given ordered points THE function SHALL return an inline SVG with `role="img"`, an `aria-label`, a y-axis starting at zero, and text of the first and last period. Evals: G-22.
- [ ] **M1-CHT-02** Add the paired-scale bars used on the home page. AC: WHEN given two values in one unit THE function SHALL draw two bars with widths proportional to the values on one shared scale. Evals: G-23.
- [ ] **M1-CHT-03** Add the state tile grid from `config/in_states.json`. AC: THE function SHALL place the 28 states by `tile`, show union territories in a separate row beneath, shade by four equal-interval classes of the data range, label every tile with `abbr`, and contain only `rect`, `text` and `title` elements. Evals: G-24, INV-8-T.

### PGE
- [ ] **M1-PGE-01** Area page template listing that area's metrics. AC: WHEN an area has no published metric THE page SHALL show its empty state. WHEN it has metrics THE page SHALL list title, latest value, period and source badge for each.
- [ ] **M1-PGE-02** Metric page template. AC: THE page SHALL show the definition, the latest world or national value, the line chart, the source record for every point shown (publisher, link, source type, published, retrieved, evidence, verified by, verified on), the tile grid when state-level points exist, and an "Updated" note when a point has a `revision_note`.
- [ ] **M1-STL-01** Staleness. AC: WHEN a point's `verified_on` plus the metric's `stale_after_months` is earlier than the build date THE page SHALL show a Stale badge beside it. THE build date SHALL come from the clock in UTC, overridable by `--today`. Evals: INV-9-T.

### CHK
- [ ] **M1-LNG-01** Scan templates and our text for banned phrases at build time. AC: WHEN any banned phrase appears in a template or in authored data text THE build SHALL fail naming the file. Evals: INV-5-B.
- [ ] **M1-NET-01** Add a build-time and test-time scan of `dist/`. AC: THE scan SHALL fail WHEN any `script`, `link`, `img`, `iframe` or CSS `url()` references another origin, and WHEN any file ends in `.geojson`, `.topojson` or `.map`. Evals: INV-7-T.
- [ ] **M1-REV-01** Write `scripts/check_revisions.py` and run it in CI on pull requests. AC: WHEN a published point's value changed or was removed relative to the base branch and no `revision_note` is present THE script SHALL exit non-zero naming the point. Evals: INV-10-T.
- [ ] **M1-LNK-01** Write `scripts/check_links.py` (standard library) and `.github/workflows/link-check.yml` running weekly. AC: THE script SHALL request every source URL, print a table of status codes, and exit non-zero on any 404 or 410; the workflow SHALL NOT block deploys.

---

## M2 — Design implementation and responsive

- [ ] **M2-CSS-01** `scripts/make_tokens.py` writes `static/css/tokens.css` from `design/tokens.json`. AC: THE CSS SHALL define every colour and font token as a custom property, scoped per area with a class on `body`. Evals: G-25.
- [ ] **M2-FNT-01** Self-host fonts. AC: THE build SHALL ship only the font files listed in `design/tokens.json`, as Latin-subset woff2 (and Devanagari for Rozha One), with `font-display: swap`, each area page loading only its own fonts plus the shared ones (the home page may also load glyph-subset copies of the other areas' display and script fonts, limited to the tile titles and the text "00 metrics"), and `static/fonts/LICENSES.md` naming each licence. IF fonts cannot be downloaded THE agent SHALL keep the fallback stacks and record "fonts pending" in AGENT_LOG.md.
- [ ] **M2-HOM-01** Home page as `design/reference/home.html`. AC: THE page SHALL contain the hero, the paired scale (real data when two comparable verified points exist, otherwise omitted), four area tiles in their own packs, a recently verified list from data, the statement band and the footer.
- [ ] **M2-ARE-01** Four area pages as `area-people.html`, `area-planet.html`, `area-money.html`, `area-industry.html`, each in its own pack.
- [ ] **M2-MET-01** Metric page as `design/reference/metric.html`.
- [ ] **M2-PHN-01** Phone layouts as `phone-home.html`, `phone-people.html`, `phone-metric.html`. AC: WHEN the viewport is 360 px wide THE page SHALL NOT scroll sideways.
- [ ] **M2-A11-01** `scripts/check_contrast.py`. AC: THE script SHALL compute WCAG contrast for every pair in `design/tokens.json` and exit non-zero below 4.5 (3.0 for pairs marked large).
- [ ] **M2-A11-02** Accessibility basics. AC: THE site SHALL show a visible focus ring, a skip link, landmark regions, `prefers-reduced-motion` support, and never carry meaning by colour alone.
- [ ] **M2-CTB-01** Contribute and about pages from CONTRIBUTING.md and README.md with no new claims.
- [ ] **M2-EMP-01** Empty states per area in that area's pack.
- [ ] **M2-DOC-01** Update README.md, BRIEF.md, AGENT_LOG.md and the claims register so each conceptual claim is honored with a test name or marked as not done.

---

## M3 — First verified data (human-led, do not start)

- [ ] **M3-DAT-01** Choose about ten starter metrics, one or two per area, each with a named primary source.
- [ ] **M3-DAT-02** Enter each using docs/prompts/data-entry.md after opening the source yourself.
- [ ] **M3-DAT-03** Verify each in a fresh session or by a second person with docs/prompts/verify.md.

---

## Backlog — unscheduled, do not start

- Canonical JSON formatter for contributors — deferred until contributions arrive.
- Full ISO 3166-1 country list in `config/` — the validator checks only the three-letter pattern today.
- A fifth area, for example Education or Energy, as a new design pack — deferred until the four are finished.
- Optional light JavaScript, such as sorting a table — deferred until M2 is accepted.
- Hindi or other languages — out of scope for v1.

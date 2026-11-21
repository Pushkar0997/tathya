# architecture.md — Tathya

## 1. Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Language | Python | 3.12 (CI), 3.9 or later locally | The owner's strongest language; the validator uses the standard library only |
| Templating | Jinja2 | pinned in requirements.txt | The one runtime dependency of the build; renders static pages |
| Output | Static HTML, CSS and inline SVG | HTML5, CSS3 | No JavaScript is needed to read any content |
| Charts | SVG generated at build time | none | No chart library; accessible, deterministic, testable |
| Hosting | GitHub Pages deployed by GitHub Actions | official actions, current majors | Free, static, no server |
| Data | One JSON file per metric | JSON | Stdlib parsing; avoids YAML type coercion |
| Fonts | Self-hosted woff2 files under the SIL Open Font License (fallback stacks active while binary files are pending) | see design/tokens.json | No third-party requests at runtime |

Do not add a dependency without a decision entry. The site must build offline from a fresh clone with `pip install -r requirements.txt`.

## 2. Structure

```
tathya/
├── data/<area>/<metric-id>.json   ← published metrics; only verified data; validated in production mode
├── fixtures/data/                 ← SAMPLE metrics for tests and local preview; never deployed
├── config/                        ← source_allowlist.json, banned_phrases.txt, in_states.json
├── scripts/                       ← validate_data.py, spec_lint.py, spec-gate.sh, build_site.py, make_tokens.py, check_contrast.py, check_revisions.py, check_links.py
├── site/                          ← Python modules: charts, pages, staleness
├── templates/                     ← Jinja2 templates, one base layout plus page templates
├── static/                        ← css, fonts, favicon; copied to dist/
├── design/                        ← DESIGN.md, tokens.json, reference/ mockups (read-only references)
├── tests/                         ← unittest; every test name carries its eval ID
├── docs/                          ← prompts, DEPLOY.md and BUILD_REPORT.md
├── spec/                          ← this specification
└── dist/                          ← build output, git-ignored, deployed by CI
```

Rules: data lives only in `data/`; presentation lives only in `templates/` and `static/`; no page contains a hard-coded statistic.

## 3. Data model

One file per metric at `data/<area>/<id>.json` (full rules in CONTRACT.md):

```json
{
  "id": "metric-id", "title": "...", "area": "people", "definition": "...",
  "definition_source": "s1", "unit": "percent of population", "stale_after_months": 12,
  "sources": [{"id": "s1", "publisher": "...", "title": "...", "url": "https://...",
               "source_type": "primary", "published": "2024-07-01", "retrieved": "2026-10-01"}],
  "points": [{"geography": "WLD", "period_kind": "calendar_year", "period": "2023", "value": 12.3,
              "status": "verified", "source_id": "s1", "evidence": "Table 1, page 4: ... 12.3 ...",
              "entered_by": "handle", "verified_by": "other-handle", "verified_on": "2026-10-05"}]
}
```

Expensive to reverse: the point schema and the geography and period conventions, because every contributed file depends on them. Changing them needs a change proposal.

## 4. Capability register

| Capability | Status | Needed for |
|---|---|---|
| Validate data files against CONTRACT rules | supported | every merge (scripts/validate_data.py) |
| Preview from SAMPLE fixtures | supported | design review and tests (`scripts/build_site.py --preview`) |
| Build static pages | supported | deploy (`scripts/build_site.py`) |
| SVG charts | supported | metric and home pages (`site/charts.py`) |
| Tile grid of Indian states | supported | state-level metrics (`site/charts.py`) |
| Geographic boundary maps | **not supported** | would need an approved boundary source; see INV-8 |
| JavaScript interactivity | **not supported** | not needed in v1; progressive enhancement only after M2 by decision |
| User accounts, comments, analytics | **not supported** | non-goals |
| Fetching data from the internet at build time | **not supported** | builds are offline and deterministic |
| Automatic data collection | **not supported** | data is entered and verified by people, with agents only as assistants |
| Currency conversion or inflation adjustment | **not supported** | only as an explicit derived point with a formula |
| Languages other than English | **not supported** | v1 |

## 5. Scale assumptions
- Building for: up to 200 metric files and 50,000 points.
- Revisit at: 500 metric files, or a build over 60 seconds.
- First thing to break: build time and review load, not hosting.
- Expensive to reverse: the data schema and the allowlist tier rules.

## 6. Performance budget
Each built page is at most 300 KB of HTML, CSS and inline SVG before compression, excluding fonts. Fonts for one area page total at most 250 KB. These are checked by a build-time size report in `scripts/build_site.py`.

## 7. Security and privacy
- Stored about visitors: nothing. No cookies, no analytics, no forms.
- Third-party requests from built pages: none (INV-7).
- Secrets: none exist and none may be added. Deploy uses GitHub's built-in permissions only.
- Contributions: pull requests only; CODEOWNERS or branch protection means only the owner merges.

## 8. Architecture claims register

| Claim | Status | Evidence |
|---|---|---|
| Every published point has a source, evidence containing its figure, and a verifier who is not its enterer | honored | scripts/validate_data.py; tests INV-1-T, INV-3-T, N-10 |
| SAMPLE data is refused by the validator in production mode | honored | tests INV-2-T, N-14 |
| The production build and deploy refuse SAMPLE data | honored | scripts/build_site.py; test_INV2_B_sample_fails_production_build (INV-2-B) |
| Built pages make no third-party requests and need no JavaScript | honored | scripts/build_site.py scan_dist; test_INV7_T_no_external_requests_or_cookies (INV-7-T) |
| States are drawn only as a tile grid, never as a boundary map | honored | site/charts.py state_tile_grid; tests test_G24_state_tile_grid, test_INV8_T_tile_grid_no_maps (G-24, INV-8-T) |
| Staleness badges are computed at build time and the site rebuilds weekly | honored | site/staleness.py, .github/workflows/pages.yml; test_INV9_T_stale_badge (INV-9-T) |
| A changed or removed published value must carry a revision note | honored | scripts/check_revisions.py; test_INV10_T_check_revisions (INV-10-T) |
| Our own text contains none of the banned phrases | honored | scripts/build_site.py, scripts/validate_data.py; tests test_INV5_T_neutral_language_is_enforced, test_INV5_B_banned_phrase_in_template_or_data (INV-5-T, INV-5-B) |

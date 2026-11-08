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
| Fonts | Self-hosted woff2 files under the SIL Open Font License | see design/tokens.json | No third-party requests at runtime |

Do not add a dependency without a decision entry. The site must build offline from a fresh clone with `pip install -r requirements.txt`.

## 2. Structure

```
tathya/
├── data/<area>/<metric-id>.json   ← published metrics; only verified data; validated in production mode
├── fixtures/data/                 ← SAMPLE metrics for tests and local preview; never deployed
├── config/                        ← source_allowlist.json, banned_phrases.txt, in_states.json
├── scripts/                       ← validate_data.py (done), spec_lint.py, spec-gate.sh, build_site.py (M0)
├── site/                          ← Python modules: charts, pages, staleness (M0 to M1)
├── templates/                     ← Jinja2 templates, one base layout plus page templates
├── static/                        ← css, fonts, favicon; copied to dist/
├── design/                        ← DESIGN.md, tokens.json, reference/ mockups (read-only references)
├── tests/                         ← unittest; every test name carries its eval ID
├── docs/                          ← prompts and deploy notes
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
| Preview from SAMPLE fixtures | in progress (M1) | design review and tests |
| Build static pages | in progress (M0) | deploy |
| SVG charts | in progress (M1) | metric and area pages |
| Tile grid of Indian states | in progress (M1) | state-level metrics |
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
Each built page is at most 300 KB of HTML, CSS and inline SVG before compression, excluding fonts. Fonts for one area page total at most 250 KB. These are checked by a build-time size report in M2.

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
| The production build and deploy refuse SAMPLE data | conceptual | M0-BLD-02 |
| Built pages make no third-party requests and need no JavaScript | conceptual | M1-NET-01 |
| States are drawn only as a tile grid, never as a boundary map | conceptual | M1-CHT-03 |
| Staleness badges are computed at build time and the site rebuilds weekly | conceptual | M0-DEP-01, M1-STL-01 |
| A changed or removed published value must carry a revision note | conceptual | M1-REV-01 |
| Our own text contains none of the banned phrases | conceptual | M1-LNG-01 |

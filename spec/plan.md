# plan.md — Milestones

Sequential. Do not start M(n+1) before M(n)'s exit criteria are met. A milestone closes only with a verdict table in spec/evals.md, written from a separate verifier's report.

**Currently active: M0.**

---

## M0 — Skeleton, CI and deploy ⏱ one session · cost ₹0

Everything else needs a site that builds and deploys. The correctness core (validator, tests, lint) already exists and must stay green.

**Deliverables**
- `scripts/build_site.py` producing `dist/` from templates, with an empty-state home page
- A production-mode build that refuses SAMPLE data and any validation error
- `.github/workflows/pages.yml` deploying on push to main and weekly
- `docs/DEPLOY.md`

**Exit criteria**
- [ ] `python3 scripts/build_site.py` on a fresh clone exits 0 and writes `dist/index.html` saying that no verified numbers have been published yet
- [ ] The same build exits non-zero when a SAMPLE metric is placed in `data/`
- [ ] `bash scripts/spec-gate.sh ci` exits 0
- [ ] A human has enabled Pages with source GitHub Actions and the live URL serves the build

**Risk:** the deploy actions' current major versions change. Check GitHub's own documentation, not memory.

---

## M1 — Pages and charts from fixtures ⏱ one to two sessions

**Deliverables**
- SVG generators for line chart, paired scale and state tile grid
- Area and metric page templates, badges, source record, staleness, revision notes
- Build-time scans: banned phrases, external requests, no map files
- `scripts/check_revisions.py` and `scripts/check_links.py` with a weekly link-check workflow

**Exit criteria**
- [ ] `python3 scripts/build_site.py --preview` renders all four areas from fixtures with a SAMPLE banner on every page
- [ ] INV-5, INV-7, INV-8, INV-9 and INV-10 each have a passing test in the INV table of evals.md
- [ ] Chart goldens G-22 to G-24 pass

---

## M2 — Design implementation and responsive ⏱ one to two sessions

**Deliverables**
- Tokens CSS from design/tokens.json, self-hosted fonts, the home, area, metric, contribute and about pages matching design/reference
- Phone layouts, accessibility checks, empty states per area

**Exit criteria**
- [ ] Every page matches its reference in design/reference by a human side-by-side review (recorded in the verdict)
- [ ] At 360 px width no page scrolls sideways
- [ ] `scripts/check_contrast.py` passes for every pair in design/tokens.json
- [ ] Each area page loads only its own fonts plus the shared ones; the home page loads only glyph-subset copies of the other areas' fonts

---

## M3 — First verified data (human-led, not for the build agent) ⏱ a few sittings

Choose about ten metrics across the four areas, open each source yourself, enter the data with docs/prompts/data-entry.md, and have a different person or fresh session verify it with docs/prompts/verify.md.

**Exit criteria**
- [ ] At least ten metrics are published, each point verified by someone other than its enterer
- [ ] No placeholder or SAMPLE content is reachable in production

---

## M4 — Launch ⏱ one sitting

**Exit criteria**
- [ ] spec/smoke.md passes in full on the live URL
- [ ] The data licence decision (D-011) is settled by the owner
- [ ] The README describes the real state of the project

---

## Sequencing rules
- M0 blocks everything.
- M3 must not start until M2's design is accepted, because data entry is wasted if the schema changes.
- Do not skip M3 verification: the validator checks structure, not truth.

## Anti-goals for the current stage

Things that will feel productive and are not, until M2 is complete:

- Adding metrics or entering real data from memory
- Adding JavaScript, animations or a chart library
- Adding a fifth area before the four existing ones are finished
- Polishing fonts before the pages work

If you find yourself doing one of these, check which milestone is active.

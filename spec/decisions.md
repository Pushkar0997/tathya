# decisions.md — Decision Log

Every non-obvious decision, why, and what was rejected. **This file exists to stop the next agent from re-opening a settled question or reverting a deliberate choice.**

---

## D-001 — Name: Tathya

**Status:** decided
**Decision:** The site and repository are named Tathya (Sanskrit for a fact, that which is so), repository slug `tathya`.
**Rationale:** Short, neutral, not tied to India or to one area, and it describes what the site does: show facts.
**Rejected:**
- *Numbers That Matter: India* — the country in the name limits the scope, and the phrase is common.
- *Pramāṇa* — means proof or evidence; the site shows numbers and does not argue or prove anything.
- *Asymmetry Atlas* — points at a conclusion, which conflicts with INV-5.

**Revisit if:** the owner finds a trademark or domain conflict.

---

## D-002 — Scope: global indicators with India in depth, four areas

**Status:** decided
**Decision:** Cover global and country figures from international bodies, plus Indian states from official Indian sources, in four areas: People, Planet, Public money, Industry.
**Rationale:** Hunger, textile waste, agriculture and climate are global systems and cannot be shown from India alone; the owner also wants state-level depth for India.
**Rejected:**
- *India only* — cannot show the global topics the owner cares about.
- *Global only* — loses the state-level view the owner wants.

**Revisit if:** the verification load exceeds what the owner can review; then narrow the areas, not the rules.

---

## D-003 — Static site, Python build, no JavaScript

**Status:** decided
**Decision:** Hand-written templates rendered by a Python script to static HTML and CSS, deployed to GitHub Pages. No JavaScript is needed to read anything.
**Rationale:** Simplest thing that works on Pages, easiest to verify, and the owner knows Python.
**Rejected:**
- *One big index.html* — every contribution would conflict, diffs would be unreviewable, and nothing could validate individual points.
- *A Node-based static site generator* — fine on Pages at build time, but adds a toolchain the owner does not want.
- *Client-side rendering with a chart library* — needs vendoring and pinning, and produces less accessible charts.

**Revisit if:** the site passes 200 metrics or a feature genuinely needs interactivity.

---

## D-004 — Data as JSON, not YAML or CSV

**Status:** decided
**Decision:** One JSON file per metric.
**Rationale:** Standard-library parsing, strict types, and room for per-point evidence.
**Rejected:**
- *YAML* — needs a parser dependency and silently coerces values: the country code NO becomes false and a period like 2023 becomes a number.
- *CSV* — cannot carry per-point evidence and source records cleanly.

**Revisit if:** contributors struggle with JSON syntax, in which case add a formatter or a form, not a looser format.

---

## D-005 — Charts are SVG generated at build time

**Status:** decided
**Decision:** Python functions emit inline SVG for line charts, paired bars and the tile grid.
**Rationale:** No library to pin, accessible by default, testable with golden files, no runtime code.
**Rejected:**
- *Chart.js or another vendored library* — a pinned dependency and canvas output that screen readers cannot read.
- *D3* — far more than needed.

**Revisit if:** the owner wants hover interaction; add it as optional enhancement by a new decision.

---

## D-006 — Tile grid for Indian states, no boundary map

**Status:** decided
**Decision:** States are squares placed roughly by position; union territories sit in a separate row.
**Rationale:** Avoids any depiction of India's borders, which carries legal and political risk, and the owner wants no legal exposure.
**Rejected:**
- *Choropleth from GeoJSON* — needs an authoritative boundary source and a legal check.
- *Third-party map tiles* — a third-party request, forbidden by INV-7.

**Revisit if:** the owner approves a specific official boundary source in a new decision entry.

---

## D-007 — Source allowlist with tiers

**Status:** decided
**Decision:** `config/source_allowlist.json` lists approved domains and whether each is primary or secondary. A source's declared type must match.
**Rationale:** Makes "verified source" a mechanical check instead of a judgement.
**Rejected:**
- *Free-form sources* — the validator could not tell an agency from a blog.
- *Primary sources only* — wealth-distribution lists exist only as commercial publications and should be shown, clearly labelled.

**Revisit if:** maintaining the list becomes a bottleneck for contributors.

---

## D-008 — Evidence field and separate verifier

**Status:** decided
**Decision:** Every point carries an evidence quote containing its figure, an enterer and a different verifier.
**Rationale:** Automated checks cannot prove a number is right; they can make checking it take seconds and stop anyone grading their own entry.
**Rejected:**
- *Trusting the source link alone* — nobody can see whether the figure matches.
- *Review only through pull request approval* — invisible to readers and not checkable by CI.

**Revisit if:** the process proves too heavy for contributors; simplify the form, never the check.

---

## D-009 — One design pack per area on a shared skeleton

**Status:** decided
**Decision:** People, Planet, Public money and Industry each have their own colours, fonts, accent script and motif; layout, source record, SAMPLE sticker and body font are shared.
**Rationale:** The owner found a single calm look dull; distinct packs give each topic its own character while the shared skeleton keeps the site coherent. New areas are added as new packs.
**Rejected:**
- *One look for the whole site* — the first mockup, rejected as boring.
- *Free design per page* — the site would stop looking like one publication.

**Revisit if:** a fifth area is added, or the number of font families becomes a performance problem.

---

## D-010 — Self-hosted fonts, loaded per area

**Status:** decided
**Decision:** Font files are stored in `static/fonts`, subset to Latin (and Devanagari for the wordmark), and each area page loads only its own fonts and the shared ones.
**Rationale:** The mockups use about ten families; loading them from Google would be a third-party request (INV-7) and slow.
**Rejected:**
- *Google Fonts link* — breaks INV-7.
- *System fonts only* — loses the character the owner chose.

**Revisit if:** per-area font weight exceeds the budget in spec/architecture.md.

---

## D-011 — Licence: code MIT, data licence pending

**Status:** proposed
**Decision:** The code is MIT-licensed. The owner must decide the data licence and contribution terms before M4, after checking each allowlisted source's reuse terms. This is not legal advice.
**Rationale:** Facts and figures from public documents are republished with attribution, but sources differ in their terms.
**Rejected:**
- *Leaving no licence* — contributors would not know their rights and reusers could not rely on anything.

**Revisit if:** before M4, or whenever a source's terms forbid republication.

---

## D-012 — Deploy through GitHub Actions with a weekly rebuild

**Status:** decided
**Decision:** Pages is deployed by a workflow that runs the full gate and the production build, on every push to main and every Monday.
**Rationale:** The weekly run makes Stale badges update without a commit and keeps the validation gate in front of every deploy.
**Rejected:**
- *Deploying a committed `docs/` folder* — build output in git and no gate before publishing.
- *A deploy only on push* — badges would go stale silently.

**Revisit if:** Actions minutes or terms change.

---

## D-013 — Company fiscal years use the `date` period kind

**Status:** decided
**Decision:** A company metric's period is its fiscal year end date, for example `2024-03-31`.
**Rationale:** Fiscal years end in different months; a date is unambiguous.
**Rejected:**
- *Labelling by calendar year* — ambiguous for years ending in March.
- *A separate fiscal_year kind* — needs each company's year end in the schema.

**Revisit if:** quarterly company data is needed.

---

## D-014 — The correctness core is written before the site, and is fixed for the build agent

**Status:** decided
**Decision:** `scripts/validate_data.py`, its tests and the config files were written and mutation-checked in the spec session. The build agent uses them and may extend them only by a task.
**Rationale:** The part that must be right should not be written by the party that is least verified.
**Rejected:**
- *Letting the build agent write the validator from the contract* — a plausible but subtly weaker validator is the most dangerous failure here.

**Revisit if:** the contract changes through a change proposal.

---

## Template

```
## D-0XX — short title

**Status:** proposed | decided | superseded by D-0YY
**Decision:** what
**Rationale:** why, including what breaks without it
**Rejected:** alternatives, each with why not
**Revisit if:** condition
```

Rules: add the entry the day the decision is made — backfilled logs are fiction. Supersede rather than delete. The rejected list is the part that does the work.

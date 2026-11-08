# CONTRACT — Tathya

**The correctness core. An agent that reads only this file must not be able to break the domain.**

Precedence: this file outranks every other document. If something here conflicts with a task, the task is wrong — stop and flag it.

---

## Invariants

### INV-1 — No unsourced number

**Rule:** Every published data point references a source defined in its own metric file, with publisher, title, an https URL on a domain in `config/source_allowlist.json`, a publication date and a retrieval date.
**Why:** The site's only promise is that every number can be traced. One untraceable number discredits all of them.
**Violated by:** Typing a statistic from memory, or copying it from an AI summary, a blog or a slide.
**Detected by:** `scripts/validate_data.py` codes V-SRC-01, V-SRC-02, V-SRC-03; test INV-1-T.

### INV-2 — No sample or invented data in production

**Rule:** Points with status `sample`, files flagged `"sample": true`, and everything under `fixtures/` never reach `data/`, a production build or a deploy. Production is the default mode of every script; preview is opt-in with `--preview`.
**Why:** A placeholder that looks like a statistic is a false claim.
**Violated by:** Copying a fixture into `data/` so a page looks full, or building the deploy with `--preview`.
**Detected by:** V-SAMPLE-01 in the validator; tests INV-2-T and (planned) INV-2-B for the build.

### INV-3 — Evidence contains the figure as printed

**Rule:** Every point has `evidence` of at least 20 characters naming where the figure sits in the source (table, page, section) and containing the figure exactly as printed. The `value` is stored in the unit the publisher used, so its digits appear in the evidence.
**Why:** It is the only mechanical link between our number and the source, and it lets a reviewer check a point in seconds.
**Violated by:** Paraphrased evidence, silent unit conversion, a transcription typo.
**Detected by:** V-EVID-01 and V-EVID-02; test INV-3-T. **Limit:** the check proves the digits match the quote, not that the quote is genuine. A human or fresh verifier session must open the source (docs/prompts/verify.md).

### INV-4 — Source tier and status are declared and shown

**Rule:** Each source is `primary` or `secondary`, and that must match its domain's tier in the allowlist. A point's status is `verified`, `estimate` or `derived`. An estimate carries the publisher's stated method. A derived point carries its formula and inputs that resolve to existing points. Every number on a page shows its tier and status as a badge.
**Why:** Readers must be able to tell a government figure from a magazine list and a measurement from an estimate.
**Violated by:** Declaring a commercial list as primary; presenting a model output as a measurement.
**Detected by:** V-SRC-04, V-EST-01, V-DER-01; test INV-4-T.

### INV-5 — Neutral language

**Rule:** Our own text states what is measured and nothing about why it is good or bad, who is to blame, or what to do. No phrase in `config/banned_phrases.txt` appears in our text. Two numbers may sit side by side, but never under a sentence that links them as cause and effect.
**Why:** Neutrality is the site's legal and editorial protection, and its credibility.
**Violated by:** Headlines, captions and definitions with adjectives, motive or advice.
**Detected by:** V-LANG-01 for data text; test INV-5-T; (planned) INV-5-B scans templates.

### INV-6 — Geography, period and unit are pinned

**Rule:** Geography, period and value follow the conventions table below, with no exceptions.
**Why:** Unpinned conventions are where contributors and agents silently diverge, and a mismatched period makes a comparison false.
**Violated by:** "India" instead of `IND`, `FY2023` instead of `2023-24`, a value stored as text, a fraction instead of a percent.
**Detected by:** V-GEO-01, V-PER-01, V-VAL-01, V-VAL-02; test INV-6-T.

### INV-7 — No third-party requests, no JavaScript required

**Rule:** Built pages load no script, stylesheet, font, image or frame from another origin, set no cookies and run no analytics. All content is readable without JavaScript. Source links are ordinary anchors.
**Why:** Visitor privacy, deterministic pages and no dependency on someone else's server staying up.
**Violated by:** A Google Fonts link, a CDN script, an embedded widget.
**Detected by:** (planned) build scan M1-NET-01, test INV-7-T.

### INV-8 — No geographic boundary maps

**Rule:** Indian states appear only as the tile grid from `config/in_states.json`. No GeoJSON, TopoJSON, map tiles or outline of any border.
**Why:** Depicting India's borders other than as officially published is a recognised legal and political risk in India, and the owner wants none.
**Violated by:** Adding a choropleth "just for the demo".
**Detected by:** (planned) build scan, test INV-8-T. Lifting this rule needs an approved boundary source recorded in `spec/decisions.md`.

### INV-9 — Staleness is computed, never typed

**Rule:** The Stale badge comes from `verified_on` plus `stale_after_months` compared with the build date in UTC. The site rebuilds weekly so badges update without a commit.
**Why:** An old number that looks current is the most likely way this site misleads.
**Violated by:** Hand-editing a badge, or letting the weekly rebuild lapse.
**Detected by:** tests G-04 and G-05 for the rule; (planned) INV-9-T for the badge on the page.

### INV-10 — Revisions are visible

**Rule:** Changing or removing a published value requires a `revision_note` on that point. The page shows "Updated" with the note. Earlier values remain in git history.
**Why:** Quietly replaced numbers destroy trust.
**Violated by:** Editing a number in a data fix without a note.
**Detected by:** (planned) `scripts/check_revisions.py` in CI, test INV-10-T.

---

## Pinned conventions

| Concern | Decision |
|---|---|
| Dates | ISO 8601 `YYYY-MM-DD`; the build date is the CI run date in UTC |
| Metric IDs | Lowercase kebab-case ASCII, for example `undernourishment-prevalence`; the file is `data/<area>/<id>.json` |
| Areas | `people`, `planet`, `public-money`, `industry`; the folder name equals the area |
| Geography | `WLD` for the world; ISO 3166-1 alpha-3 uppercase for countries, for example `IND`; ISO 3166-2:IN for Indian states and union territories, for example `IN-MH` |
| Periods | `calendar_year` as `2023`; `financial_year` as `2023-24` (India, April to March, second part equals first plus one); `date` as `2023-12-31` |
| Company fiscal years | Use kind `date` with the fiscal year end date; the metric definition states the fiscal year end |
| Values | JSON number, never text; in the unit the publisher printed; never converted; percent is 0 to 100, not 0 to 1 |
| Units | Explicit free text, for example `percent of population`, `crore INR`, `million tonnes`; amounts in lakh or crore stay as published |
| Currency | Never convert currencies or adjust for inflation except as a derived point with a formula and a published rate source |
| Number display | Show the stored decimals; INR-unit values use Indian digit grouping (12,34,567); all other values use 1,234,567 |
| Source IDs | `s1`, `s2` and so on, unique within a file |
| Handles | A GitHub handle, or `agent:name` for an assistant |
| Encoding | UTF-8, LF line endings, JSON with two-space indent and a trailing newline |
| Language | English. Devanagari appears only in the wordmark and the name explanation |

---

## Exact values

```
DEFAULT_STALE_AFTER_MONTHS = 12      (allowed range 1 to 60)
MIN_EVIDENCE_CHARS         = 20
STATUSES                   = verified, estimate, derived, sample
SOURCE_TYPES               = primary, secondary
PERIOD_KINDS               = calendar_year, financial_year, date
WEEKLY_REBUILD_CRON        = 0 3 * * 1      (Mondays 03:00 UTC)
```

---

## Reference examples

Known-correct outcomes of `validate_data.validate_metric` (all in `tests/test_validate_data.py`).

| Input | Expected output |
|---|---|
| Point with value 12.3 and evidence "Table 1, page 4: world prevalence 12.3 percent in 2023" | accepted |
| Same point with value 2.3 | V-EVID-02 (2.3 does not match inside 12.3) |
| `financial_year` period `2023-24` | accepted |
| `financial_year` period `2023-25` or `2023-2024` | V-PER-01 |
| Geography `India` or `IN-XX` | V-GEO-01 |
| Geography `IN-MH` | accepted |
| Value `"12.3"` as text | V-VAL-01 |
| Entered and verified by the same handle | V-VER-02 |
| Source on `forbes.com` declared `primary` | V-SRC-04 |
| Any `sample` point in production mode | V-SAMPLE-01 |
| Verified 2025-11-08, window 12 months, build date 2026-11-08 | not stale |
| Verified 2025-11-07, window 12 months, build date 2026-11-08 | stale |

---

## Never do this

- **Never write a statistic from memory** — it will sometimes be wrong and nothing can tell. Open the source, quote it, or write "unavailable".
- **Never convert units or currencies silently** — the evidence would no longer contain the value and the reader cannot reproduce it.
- **Never copy a fixture into `data/`** — SAMPLE numbers look real. Make a real file with real evidence instead.
- **Never add a CDN script, remote font or tracker** — it breaks INV-7. Self-host the file under `static/`.
- **Never add a map file or boundary outline** — it breaks INV-8. Use the tile grid.
- **Never add a domain to the allowlist without a decision entry** — the allowlist is the line between a source and a rumour.
- **Never round up a PARTIAL** — record it as PARTIAL in spec/evals.md.
- **Never tick your own task** — a separate verifier ticks it.
- **Never use persuasive or emotive wording** — see INV-5; describe the measure, not the moral.

---

## Changing this file

Requires explicit human approval. An agent proposing a change here stops and asks; it does not edit and report.

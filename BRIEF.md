# BRIEF — Tathya

*One page. Read in 3 minutes. Rewritten whenever state changes.*

**What this is:** a static site where anyone can see sourced public numbers on food, waste, public money and the AI and quantum industry, each with its source, period and last-checked date.

**Live at:** not deployed yet; expected `https://pushkar0997.github.io/tathya/` · **Repo:** expected `https://github.com/pushkar0997/tathya`

---

## Where things stand

**Milestone:** M2 — Design implementation and responsive (M0, M1, M2 built; awaiting independent verification and human M3 data entry)
**Exit criteria:** verifier reviews M0–M2 tasks (`docs/prompts/verify.md`), binary woff2 fonts are added (`M2-FNT-01`), visual side-by-side review is completed, and Pages is enabled on GitHub
**Progress:** 27 of 27 M0–M2 tasks attempted (22 done unverified, 5 partial: `M2-FNT-01` fonts pending, `M2-HOM-01`/`M2-ARE-01`/`M2-MET-01`/`M2-PHN-01` visual match not checked)

**Last done:** M0 (`build_site.py`, `pages.yml`, `DEPLOY.md`, `test_build.py`), M1 (`site/charts.py`, `site/pages.py`, `site/staleness.py`, templates, `check_revisions.py`, `check_links.py`, `link-check.yml`), and M2 (`make_tokens.py`, `tokens.css`, `check_contrast.py`, `LICENSES.md`, responsive CSS, 49 passing unit tests)
**Next:** Run `docs/prompts/verify.md` in a fresh verifier session to verify M0–M2, download woff2 fonts, and begin human-led M3 data entry.

---

## Prompt for the next session

Copy this into a fresh verifier session (`docs/prompts/verify.md`):

```
Read CONTRACT.md, spec/tasks.md, spec/evals.md, and docs/BUILD_REPORT.md.
Run python3 -m unittest discover -s tests -v, python3 scripts/validate_data.py,
python3 scripts/spec_lint.py --strict, and bash scripts/spec-gate.sh ci.
Verify M0, M1 and M2 tasks and report PASS, PARTIAL or FAIL for each criterion.
```

---

## Three things most likely to break

1. **Unverified starter lists.** `config/source_allowlist.json` and the ISO state codes in `config/in_states.json` were written from the author's knowledge. Open each domain and check the ISO 3166-2:IN list before the first real data goes in.
2. **Fonts and visual check.** Binary `.woff2` files could not be downloaded in the offline build sandbox ("fonts pending" logged; fallback stacks active), and headless browser screenshots timed out in the container ("visual match not checked").
3. **A build agent weakening the correctness core.** After any run, run `python3 -m unittest discover -s tests -v` and `sha256sum -c docs/PROTECTED_SHA256.txt` to confirm protected files are untouched.

---

## Where everything is

| Need | File |
|---|---|
| What must never break | `CONTRACT.md` |
| Rules for agents | `AGENTS.md` |
| What happened when | `AGENT_LOG.md`, `docs/BUILD_REPORT.md` |
| What we're building and why | `spec/product.md` |
| Stack and structure | `spec/architecture.md` |
| Milestones and backlog | `spec/plan.md`, `spec/tasks.md` |
| How correctness is proven | `spec/evals.md`, `spec/smoke.md` |
| Why things are the way they are | `spec/decisions.md` |
| The look | `design/DESIGN.md`, `design/tokens.json`, `design/reference/` |
| Prompts and deploy | `docs/prompts/`, `docs/DEPLOY.md` |

---

## Standing rules

- Cost ceiling: ₹0 per month — no servers, no paid APIs, no secrets
- Anti-metric (do not optimise): the number of metrics or charts
- Real metric: share of published points with evidence and an independent verifier (target 100 percent), and months since the oldest point was verified
- The build agent stops at the end of M2. M3 (real data) is human-led
- Every number comes from a source someone opened; nothing is typed from memory

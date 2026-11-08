# BRIEF — Tathya

*One page. Read in 3 minutes. Rewritten whenever state changes.*

**What this is:** a static site where anyone can see sourced public numbers on food, waste, public money and the AI and quantum industry, each with its source, period and last-checked date.

**Live at:** not deployed yet; expected `https://pushkar0997.github.io/tathya/` · **Repo:** expected `https://github.com/pushkar0997/tathya`

---

## Where things stand

**Milestone:** M0 — Skeleton, CI and deploy
**Exit criteria:** the site builds offline, refuses SAMPLE data, passes the CI gate, and a human has enabled Pages and seen it live
**Progress:** 0 of 6 tasks

**Last done:** spec, design (4 packs, 9 reference pages, tokens with computed contrast), and the correctness core: `scripts/validate_data.py` with 33 passing tests, mutation-checked
**Next:** M0-BLD-01 — create `scripts/build_site.py`, `templates/base.html`, `static/css/base.css`

---

## Prompt for the next session

Copy this into any coding agent:

```
Read AGENTS.md, then CONTRACT.md, then spec/plan.md and spec/tasks.md.
Then read the top 3 entries of AGENT_LOG.md.

Tell me which milestone is active and which task you propose next.
Do not write code yet.
```

---

## Three things most likely to break

1. **Unverified starter lists.** `config/source_allowlist.json` and the ISO state codes in `config/in_states.json` were written from the author's knowledge. Open each domain and check the ISO 3166-2:IN list before the first real data goes in.
2. **Fonts.** The design uses about ten families. Self-hosting, subsetting and per-area loading may not work in the build agent's environment; fallbacks are specified and "fonts pending" must be logged, not hidden.
3. **A build agent weakening the correctness core.** The validator and its tests are fixed. After any run, run `python3 -m unittest discover -s tests -v` and check that `CONTRACT.md` and `scripts/validate_data.py` are unchanged except by a task.

---

## Where everything is

| Need | File |
|---|---|
| What must never break | `CONTRACT.md` |
| Rules for agents | `AGENTS.md` |
| What happened when | `AGENT_LOG.md` |
| What we're building and why | `spec/product.md` |
| Stack and structure | `spec/architecture.md` |
| Milestones | `spec/plan.md` |
| The backlog | `spec/tasks.md` |
| How correctness is proven | `spec/evals.md` |
| Pre-ship checklist | `spec/smoke.md` |
| Why things are the way they are | `spec/decisions.md` |
| The look | `design/DESIGN.md`, `design/tokens.json`, `design/reference/` |
| Prompts | `docs/prompts/` |

---

## Standing rules

- Cost ceiling: ₹0 per month — no servers, no paid APIs, no secrets
- Anti-metric (do not optimise): the number of metrics or charts
- Real metric: share of published points with evidence and an independent verifier (target 100 percent), and months since the oldest point was verified
- The build agent stops at the end of M2. M3 (real data) is human-led
- Every number comes from a source someone opened; nothing is typed from memory

# AGENTS.md — Tathya

**Read this completely before touching any code.**

**Rigor level:** spec-lite core (CONTRACT.md, AGENTS.md, AGENT_LOG.md) plus BRIEF.md and a compact spec/, with `spec_lint` and the data validator enforced in pre-commit and CI. The extra files exist because the build is handed between tools — see the spec-driven-development skill, `references/enforcement.md` §1.

---

## 1. Read order

1. `AGENTS.md` — this file
2. `CONTRACT.md` — what must never break
3. `spec/architecture.md` — stack, structure, capabilities
4. `spec/plan.md` — which milestone is active
5. `spec/tasks.md` — the specific task
6. `AGENT_LOG.md` — top 3 entries, for current state
7. `design/DESIGN.md` and `design/tokens.json` — before any visual work

Read `spec/evals.md` before claiming anything works. Read `spec/smoke.md` before any deploy. Read `spec/decisions.md` before proposing an architectural change — it may already have been rejected. For any change bigger than one task, write a proposal in `spec/changes/` first (template: `spec/changes/_template/proposal.md`) and wait for approval.

**You do not verify your own work.** When you finish a task, report it; a separate verifier (`docs/prompts/verify.md`, in a fresh session) checks it against the spec before the checkbox is ticked. Until then, report tasks as "done, unverified".

**If a task conflicts with `CONTRACT.md`, the contract wins.** Stop and flag it. Do not silently resolve.

---

## 2. Hard invariants

Never break these without explicit human approval. Full rules, reasons and detection are in CONTRACT.md.

- **INV-1 No unsourced number.** Every point has a source on the allowlist.
- **INV-2 No sample or invented data in production.**
- **INV-3 Evidence contains the figure as printed.**
- **INV-4 Source tier and status are declared and shown.**
- **INV-5 Neutral language.** No opinions, motive, advice, or banned phrases.
- **INV-6 Geography, period and unit are pinned.**
- **INV-7 No third-party requests, no JavaScript required.**
- **INV-8 No geographic boundary maps.**
- **INV-9 Staleness is computed, never typed.**
- **INV-10 Revisions are visible.**

**The data rule that overrides everything:** you may never write, change or "fix" a statistic from memory or from your own knowledge. A value enters `data/` only from a source page that was opened in this session, with its figure quoted in `evidence`. If you cannot open the source, write "unavailable" in your report and stop. The build agent does not enter real data at all: that is milestone M3, done by a human.

---

## 3. Stack — pinned

| Layer | Choice | Version |
|---|---|---|
| Language | Python | 3.12 in CI; the code must also run on 3.9 or later |
| Templating | Jinja2 | exact version pinned in `requirements.txt` |
| Output | Static HTML, CSS, inline SVG | no JavaScript needed |
| Hosting | GitHub Pages via GitHub Actions | official actions, current majors |
| Data | JSON, one file per metric | see CONTRACT.md |
| Tests | `unittest` from the standard library | |

Do not add a dependency without checking: is it needed, is it maintained, does it work offline in CI, what does it cost on the critical path? Record additions in `spec/decisions.md`. Do not add a JavaScript library, a CSS framework, a chart library or a font CDN.

---

## 4. Working rules

**One task per change.** Do not batch. Do not refactor files you were not asked to touch.

**Report what you changed.** Files created, files modified, exported symbols changed, spec files needing updates, and anything noticed but not fixed.

**Update the spec when reality diverges** — in the same change, not later. When a planned eval gets a test, move its row into the table in `spec/evals.md` in that commit.

**Do not invent.** If you need a value, a convention or a capability and it is not in `CONTRACT.md` or `spec/architecture.md`, ask. Do not choose one and proceed.

**Prefer improving over adding.** When choosing between a new feature and making an existing one work properly, improve the existing one.

**Never claim what you did not run.** Every statement that something works must be backed by a command you ran in this session and its real output pasted into AGENT_LOG.md. "Should work" is not a result. Report PARTIAL honestly.

**Protected files.** `CONTRACT.md`, `scripts/validate_data.py`, `scripts/spec_lint.py`, `tests/test_validate_data.py`, everything in `config/`, `design/tokens.json` and `design/reference/` are fixed inputs. Do not edit them. `docs/PROTECTED_SHA256.txt` lists their checksums; `sha256sum -c docs/PROTECTED_SHA256.txt` must pass at the end of every run. If one of them is wrong, report it in AGENT_LOG.md and stop that task.

**Design files are references.** Never edit `design/reference/`. Treat it as a picture to match, not code to copy: reimplement it as templates and CSS tokens.

**Never write a real secret into a tracked file.** This project has no secrets and needs none: no API keys, no tokens. Deploy uses GitHub's built-in permissions only. If you think you need a credential, stop and ask.

**Commits:** one task, one commit, message `type(scope): TASK-ID summary`, for example `feat(build): M0-BLD-01 add build_site.py`. Types: feat, fix, test, docs, chore. In a one-shot build run whose history cannot be returned, do not commit: write the suggested commit message for each task in docs/BUILD_REPORT.md instead.

**Stop rules for a build run:** work through `spec/tasks.md` in order, M0 then M1 then M2. Stop at the end of M2. Never start M3. If a task is ambiguous, write the ambiguity and your proposed default in AGENT_LOG.md, then continue with the default.

---

## 5. Definition of done

- [ ] Build passes clean
- [ ] Acceptance criteria observably met, with command output recorded
- [ ] Relevant test in `spec/evals.md` passes
- [ ] `spec/smoke.md` passes for the affected area
- [ ] Spec updated if behaviour diverged
- [ ] `spec/tasks.md` checkbox ticked only after the verifier's report
- [ ] `AGENT_LOG.md` entry written
- [ ] Committed as `type(scope): TASK-ID summary`

"It builds" is not done.

---

## 6. Vocabulary

- **Metric** — one measure, one JSON file. **Point** — one value for one geography and period.
- **Source record** — source, link, dates, evidence and verifier shown for a point.
- **Evidence** — locator in the source plus the figure exactly as printed.
- **Area** — People, Planet, Public money or Industry. **Design pack** — that area's colours, fonts, script and motif.
- **Stale** — verified longer ago than the metric's refresh window.
- **SAMPLE** — placeholder data for fixtures and mockups only.

Words to avoid in site text, and what to use instead: "freebies" → "outlay"; "crisis", "shocking", "scandal" → state the number and the unit; "gap" used as a verdict → "difference" or just show both figures.

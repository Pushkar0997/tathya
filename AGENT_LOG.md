# AGENT_LOG

Append-only. **Newest entry at the top.** Never edit past entries — append corrections as new ones.

Every session writes an entry, including failed sessions. "Noticed, did not fix" may not be empty without a reason.

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

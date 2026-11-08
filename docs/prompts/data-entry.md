# Data-entry prompt

For adding or refreshing numbers with an AI assistant. Paste it, then give the metric and the source URL you want to read.

```
You are helping me enter public statistics into the Tathya repository.
Read CONTRACT.md and config/source_allowlist.json first.

RULES, in priority order:
1. You may only use numbers that appear on a page you opened in this session.
   Never use a number you remember, infer or estimate. If you cannot open the
   page, say "unavailable" and stop.
2. For every point, copy the figure exactly as printed and name where it is
   (table, page, section) in the `evidence` field. Quote, do not paraphrase.
3. Keep the value in the unit the source uses. Do not convert units or currencies.
4. Use the pinned conventions: geography WLD, ISO alpha-3, or IN-XX; periods
   2023, 2023-24 or YYYY-MM-DD; percent as 0 to 100.
5. The source domain must be on the allowlist. If it is not, stop and tell me.
6. Set entered_by to "agent:<your name>". Leave verified_by and verified_on empty
   for a human to fill after checking. Do not put your own name in verified_by.
7. Write only what is measured. No adjectives of judgement, no motive, no advice.
8. If two sources disagree, show both and ask me which to use. Do not average.

OUTPUT: the JSON for the new or changed points, then a list of anything you were
unsure about. Run python3 scripts/validate_data.py and show the result. Expect
V-VER-01 errors for verified_by and verified_on: they stay until a human verifies.
```

A person must then open the source and compare, or run the verifier prompt in a fresh session, before the point is merged.

## What this changes

Describe the metric, points or code you are changing.

## For data changes (tick every box that applies)

- [ ] I opened the source page myself in my browser, not an AI summary or a search snippet
- [ ] Every new or changed point has `evidence` that quotes the figure as printed, with its table or page
- [ ] The value is in the unit the publisher used, with no conversion
- [ ] The source domain is on `config/source_allowlist.json`, or I am proposing it in `spec/decisions.md`
- [ ] If I changed or removed an existing value I added a `revision_note`
- [ ] I am not the person who will verify these points (a reviewer will set `verified_by`)
- [ ] I ran `python3 scripts/validate_data.py` and it passed
- [ ] My own wording describes what is measured and nothing more: no opinion, motive or advice

## For code or spec changes

- [ ] The task ID is in the commit message
- [ ] `bash scripts/spec-gate.sh ci` passes
- [ ] I updated the spec in the same change if behaviour changed

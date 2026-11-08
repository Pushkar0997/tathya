# Contributing a number to Tathya

Anyone can propose a data point through a pull request. A number is accepted only with its source and its evidence.

## Steps

1. **Pick the metric.** Open its file in `data/<area>/<metric-id>.json`, or propose a new metric with its definition in a pull request description first.
2. **Open the source yourself.** Use the publisher's own page or document. Not an AI answer, a search snippet or a social post.
3. **Add the point.** Fill in geography, period, value, source, and evidence. Keep the value in the unit the publisher printed. Do not convert.
4. **Quote the evidence.** Write where the figure is (table, page, section) and copy the figure exactly as printed, for example `Table 1, page 4: world prevalence 12.3 percent in 2023`.
5. **Run the check.** `python3 scripts/validate_data.py` must print OK.
6. **Open a pull request** and tick the checklist. A different person will compare your number with the source and add their name as `verified_by`.

## Conventions you must follow

- Geography: `WLD`, an ISO country code such as `IND`, or an Indian state code such as `IN-MH`.
- Period: `2023`, `2023-24` (India's April to March year) or `2023-12-31`.
- The value is a number, never text. Percent is 0 to 100.
- Sources must be on `config/source_allowlist.json`. To propose a new domain, add a decision entry in `spec/decisions.md`.
- Describe what is measured. Leave out opinion, motive and advice.
- If you change or remove a published value, add a `revision_note` explaining why.

The full rules are in `CONTRACT.md`.

## Using an AI assistant

Fine, with one rule: it may only help you read a source you opened. Never accept a number it recalls. `docs/prompts/data-entry.md` is a prompt that enforces this.

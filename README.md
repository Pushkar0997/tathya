# Tathya

**Tathya** (तथ्य) is Sanskrit for a fact, that which is so.

A small, open, static website that shows public numbers on food, waste, public money and the AI and quantum industry, each beside the document it came from, the period it covers and the date a person last checked it. It offers no opinions and asks nothing of the reader.

> **Status: scaffold.** The rules, the data validator and the design are in place. The site itself is being built (see `BRIEF.md`). No real data is published yet, and the site refuses to publish any placeholder data.

## The four areas

| Area | Covers |
|---|---|
| People | Hunger, poverty, how wealth is distributed |
| Planet | Textile and food waste, agriculture, climate |
| Public money | Budgets and outlays beside service indicators, for countries and Indian states |
| Industry | Revenue, profit and loss, hiring and layoffs in AI and quantum companies |

## How a number gets on the site

Every number lives in a JSON file under `data/` with its source link, publication and retrieval dates, an evidence quote that contains the figure exactly as printed, who entered it, and a different person who verified it. A script (`scripts/validate_data.py`) rejects a file that breaks any rule, and a pull request cannot merge while it fails. The script checks structure and consistency. It cannot know whether a number is true, so a person must open the source and compare. See `CONTRACT.md` for the rules and `CONTRIBUTING.md` to add a number.

## Preview and test

```
pip install -r requirements.txt
python3 -m unittest discover -s tests -v          # correctness tests
python3 scripts/validate_data.py                  # validate data/ in production mode
python3 scripts/spec_lint.py --strict             # spec consistency
git config core.hooksPath .githooks               # run the checks before every commit
```

Once the builder exists: `python3 scripts/build_site.py --preview` renders the site from SAMPLE fixtures, and `python3 -m http.server -d dist` serves it locally.

## How this repository is organised

`BRIEF.md` is the one-page status. `CONTRACT.md` holds the rules that must never break. `AGENTS.md` tells any AI coding agent how to work here. `spec/` holds the plan and tasks. `design/` holds the visual design. `AGENT_LOG.md` records who did what.

## Licence

Code: MIT, see `LICENSE`. The data licence is not yet decided. Each point keeps the terms of its source. This is not legal advice.

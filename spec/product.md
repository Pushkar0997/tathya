# product.md — Tathya

## 1. One-line definition
Tathya lets anyone see sourced, comparable public numbers on food, waste, public money and the AI and quantum industry in one place, each with its source, period and last-checked date.

## 2. The problem
Good statistics exist, but they are scattered across agency reports, budget documents and company filings, in different formats and units. A curious reader cannot quickly see a figure beside the document it came from, and cannot tell how old it is. Existing sites cover one topic each (for example Our World in Data for global indicators) and none combines these four areas with a mandatory source record on every number and open contribution through pull requests.

## 3. Target user
**Primary:** a curious non-expert, such as a student or young professional, who wants a number and wants to know where it came from.
**Secondary:** journalists and researchers who need a citable source link and period.
**Explicitly not the target:** policy experts who need raw datasets, and campaigners looking for persuasive content. Tathya offers no opinions and no calls to action.

## 4. Core promise
> After using this, a visitor can read a statistic, see exactly which public document it comes from, and tell how recently a person checked it.

Everything is measured against that sentence.

## 5. Non-goals
- **Opinions, rankings of governments or companies, forecasts** — the site shows what sources say, never what it means or who is to blame.
- **Accounts, comments, a backend or a database** — it is static files on GitHub Pages; contributions happen only through pull requests.
- **Geographic maps** — India's states appear as a tile grid, never as a boundary map (see INV-8 in CONTRACT.md).
- **Scraped, private or rumoured data** — only public documents a person opened and quoted.
- **Real-time feeds** — figures are updated by people on a weekly or fortnightly rhythm at best.
- **Dramatic estimates** — an estimate is shown only when a recognised institution publishes it with a stated method.

## 6. Success metrics
1. Share of published data points that carry evidence and pass validation — target 100 percent, enforced by CI.
2. Months since the oldest published point was last verified — target under 12.

**Anti-metric — do not optimise:** the number of metrics or charts. It rises while quality falls.

## 7. Kill criteria
If no data point has been verified for 12 months, the README states that the project is archived and the deploy workflow stops running.

## 8. Glossary
- **Metric** — one named measure, such as prevalence of undernourishment, stored as one JSON file.
- **Point** — one value for one geography and one period within a metric.
- **Source record** — the source, link, dates, evidence quote and verifier shown for a point.
- **Evidence** — a locator in the source plus the figure exactly as printed.
- **Area** — one of People, Planet, Public money, Industry. Each has its own design pack.
- **Design pack** — the colours, fonts, accent script and motif of one area.
- **Stale** — a point whose last verification is older than the metric's refresh window.
- **SAMPLE** — placeholder data used only in fixtures and mockups, never published.

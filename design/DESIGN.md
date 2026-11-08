# DESIGN — Tathya

The approved look is in `design/reference/` (nine HTML pictures with SAMPLE values) and `design/tokens.json` (every colour, font and size). Match the pictures; take values only from the tokens. Never edit the references.

## Concept

A premium magazine for public facts. Large, confident type with strong contrast between weights, one colour world per area, and a calm structure underneath so the site still reads as one publication. The shared skeleton makes the pages feel connected; each area's pack gives its topic a character of its own.

## What is shared on every page

- **Masthead:** the wordmark "Tathya" in Rozha One, with the navigation to the four areas and Contribute. On phones the navigation collapses behind a Menu button; use a `details` element so no JavaScript is needed.
- **Hero:** a full-width coloured band holding the masthead, the huge area or page title, an accent script line, and a giant number.
- **SAMPLE sticker:** a rotated circle (12 degrees) in the pack's sticker colours. In production it is absent unless a point is a genuine placeholder, which can never ship; in preview it marks every number.
- **Measures list:** rows with a top rule, the metric title in the pack's display font, its coverage, and a status tag.
- **Source record card:** white card, two-pixel ink border, ten-pixel top bar in the pack's bar colour, rows of label and value. It shows source, type, link, evidence, period, published, retrieved, verified by, verified on, and any revision note.
- **Footer band:** the hero colour, the wordmark, and one line of text.
- **Body font:** DM Sans everywhere for running text.
- **Layout:** content maximum width 1200 px, gutters 32 px on desktop and 20 px on phones, tap targets at least 44 px.

## The four design packs

| Area | Hero colour | Accent | Display font | Script font | Motif |
|---|---|---|---|---|---|
| People | wine `#2A0B1E` | pink `#FF6B9A` | Playfair Display 900, roman and italic | Pinyon Script | concentric rings, like an empty plate |
| Planet | forest `#0A3B2F` | lime `#C6E04B` | Fraunces 900, roman and italic | Caveat 600 | flowing wave lines |
| Public money | navy `#0F1D3D` | gold `#F2B134` | Abril Fatface | Great Vibes | ledger-paper rules and a gold margin line |
| Industry | cobalt `#1A2BD6` | yellow `#FFE45E` | Syne 800 | Instrument Serif italic | tilted orbit ellipses, like an atom |

The home page and the contribute and about pages use the shared indigo, marigold and rani world: Playfair Display for headings, Pinyon Script for the tagline.

Giant numbers: People uses Playfair italic, Planet Fraunces italic, Public money Abril Fatface, Industry Syne 800.

## Adding a new area later

A new area is a new entry in `design/tokens.json` with the same keys as the existing four (colours, display font, script font, motif), a new motif SVG, and its contrast pairs. Nothing else in the layout changes. Until a pack exists, a new area uses the shared indigo, marigold and rani world.

## Responsive rules

- At phone width (390 px reference, 360 px minimum) the title scales to about 104 px, the giant number to about 104 px, headings to 36 px, tiles stack, and tables become stacked blocks.
- Nothing may scroll sideways at 360 px.
- The reference phone pages are `phone-home.html`, `phone-people.html` and `phone-metric.html`. The other areas follow People's structure.

## The state tile grid

One square per state placed by `tile` in `config/in_states.json` on a 6 by 9 grid, four shades by equal intervals of the data range (lightest `#FFFFFF`, then `#B4A5EC`, `#6C58C8`, `#1B1346`), labelled with `abbr`. Union territories sit in a separate row of tiles beneath. A note says "A tile grid, not a map. It makes no claim about boundaries." The mockup's shading and positions are SAMPLE; the grid itself is a standing rule (INV-8).

## Charts

Line charts: an indigo panel, a marigold line, a pink end dot, years along the bottom, the y-axis starting at zero. Every chart has `role="img"` and an `aria-label`. In preview the word SAMPLE is stamped large and faint behind the line.

## Accessibility

- All 38 colour pairs in `design/tokens.json` were computed and meet WCAG 2.x AA (4.5 for body text, 3.0 for large text). Keep it that way: `scripts/check_contrast.py` (task M2-A11-01) fails the build otherwise.
- Meaning is never carried by colour alone: every badge has text.
- Visible focus ring, skip link, landmark regions, `prefers-reduced-motion` respected, no animation required to read anything.

## Fonts

Self-host every font (INV-7). The families, weights and scripts are in `design/tokens.json`. Subset to Latin, plus Devanagari for the Rozha One wordmark. Each area page loads its own display and script fonts plus the shared ones; the home page loads glyph-subset copies of the other areas' fonts for its four tiles. If font files cannot be obtained, keep the fallback stacks and record "fonts pending" in AGENT_LOG.md.

## Known differences between the mockup and production

- Mockup tile abbreviations CG and UK differ from ISO codes IN-CT and IN-UT; production derives labels from `config/in_states.json`.
- Every value, shading and trend line in the references is SAMPLE.
- The mockup loads Google Fonts for convenience; production must not.
- The mockups are one picture per page type; the contribute and about pages follow the same skeleton with plain text content.

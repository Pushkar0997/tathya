# Font Licences — Tathya

Every font family specified in `design/tokens.json` is an open-licence typeface distributed under the **SIL Open Font License 1.1 (OFL-1.1)**.

| Family | Role | Weights / Styles | Subsets | Licence |
|---|---|---|---|---|
| DM Sans | Shared body font | 400, 500, 700 (normal) | Latin | SIL Open Font License 1.1 |
| Rozha One | Shared wordmark and Devanagari watermark | 400 (normal) | Latin, Devanagari | SIL Open Font License 1.1 |
| Playfair Display | Home & People display font | 400, 700, 900 (normal, italic) | Latin | SIL Open Font License 1.1 |
| Pinyon Script | Home & People script font | 400 (normal) | Latin | SIL Open Font License 1.1 |
| Fraunces | Planet display font | 900 (normal, italic) | Latin ( plus glyph subset on Home) | SIL Open Font License 1.1 |
| Caveat | Planet script font | 600 (normal) | Latin (plus glyph subset on Home) | SIL Open Font License 1.1 |
| Abril Fatface | Public money display font | 400 (normal) | Latin (plus glyph subset on Home) | SIL Open Font License 1.1 |
| Great Vibes | Public money script font | 400 (normal) | Latin (plus glyph subset on Home) | SIL Open Font License 1.1 |
| Syne | Industry display font | 800 (normal) | Latin (plus glyph subset on Home) | SIL Open Font License 1.1 |
| Instrument Serif | Industry script/accent font | 400 (italic) | Latin (plus glyph subset on Home) | SIL Open Font License 1.1 |

## Status in this build

- **Fonts pending:** The build agent ran in an offline container with no outbound network access to download binary `.woff2` files from Google Fonts. Per `M2-FNT-01` and `design/DESIGN.md`, the site ships with the configured system fallback font stacks (`Georgia, serif`, `system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif`, `cursive`) and per-area stylesheet scoping, with zero third-party font requests (honoring `INV-7`).
- When `.woff2` files are placed in `static/fonts/` in an online environment, `font-display: swap` and per-area loading apply automatically.

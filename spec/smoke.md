# smoke.md — Manual Smoke Checklist

Run before every deploy and again on the live URL after it. About 15 minutes. Catches what automated tests do not.

```
bash scripts/spec-gate.sh ci && python3 scripts/build_site.py
```

## 1. Build and content
- [ ] Build completes with zero errors
- [ ] `grep -ri "sample" dist` finds nothing in a production build
- [ ] `grep -rE "(src|href)=\"https?://" dist` shows only source links on `a` elements, never `script`, `link` or `img`
- [ ] No `.geojson`, `.topojson` or map files exist in `dist`

## 2. Cold start
Private window, no extensions.
- [ ] Home loads with no console errors and no requests to other origins (browser network panel)
- [ ] Each area page and the contribute and about pages load from the navigation
- [ ] Hard refresh on a metric page works

## 3. Core path
- [ ] Open a metric page, read the number, click its source link and find the same figure in the source
- [ ] The source record shows publisher, source type, published and retrieved dates, evidence, verified by and verified on
- [ ] Source type, status and Stale badges appear on every number
- [ ] A point past its window shows Stale

## 4. Cross-device
- [ ] Desktop Chrome
- [ ] One non-Chromium browser
- [ ] Phone, or a 360 px window: no sideways scrolling, controls reachable
- [ ] The menu works on a phone width

## 5. Accessibility
- [ ] Full keyboard traversal of home, an area page and a metric page
- [ ] Visible focus indicator on every control
- [ ] `prefers-reduced-motion` respected
- [ ] Meaning is never carried by colour alone
- [ ] Text contrast passes `scripts/check_contrast.py`

## 6. Language
- [ ] Read every page aloud once: no adjectives of judgement, no motive, no advice
- [ ] The tile grid carries the note that it is not a map

## 7. Post-deploy
- [ ] The live URL serves the new build (check a changed string)
- [ ] The weekly workflow has run at least once and the link-check workflow reports no dead links

---

## Failure protocol
1. **Roll back first:** `git revert` the bad commit and push; Pages redeploys the previous state
2. Reproduce locally
3. Add a test to `spec/evals.md` that would have caught it
4. Fix
5. Re-run this checklist in full, not just the failed section

Every production bug adds an item to this file.

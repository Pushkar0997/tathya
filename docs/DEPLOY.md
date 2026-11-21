# Deploying Tathya

Tathya is a static site deployed to GitHub Pages via `.github/workflows/pages.yml`. No secrets, tokens, or external credentials are used.

## 1. Repository configuration

1. Open the repository on GitHub and go to **Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Do not select "Deploy from a branch": the site is built and gated in CI from `main` before publishing `dist/`.

## 2. Automatic builds and weekly refresh

The workflow in `.github/workflows/pages.yml` runs:
- On every push to `main`.
- Every Monday at `03:00 UTC` (`0 3 * * 1`), so computed staleness badges refresh automatically without requiring a commit.
- Manually via `workflow_dispatch` in the **Actions** tab.

Every run executes `bash scripts/spec-gate.sh ci` and `python3 scripts/build_site.py` in production mode. Any validation error or `SAMPLE` data point fails the build before `dist/` can be uploaded.

## 3. Local preview

To build and inspect the site locally:

```bash
# Production build from data/ (empty states until verified metrics are added)
python3 scripts/build_site.py
python3 -m http.server -d dist

# Design preview from SAMPLE fixtures in fixtures/data/
python3 scripts/build_site.py --preview
python3 -m http.server -d dist
```

Then open `http://localhost:8000/` in a browser.

## 4. Rollback

If a bad change reaches `main`:

1. Revert the bad commit and push to `main`:
   ```bash
   git revert <bad-commit-sha>
   git push origin main
   ```
2. The `Deploy GitHub Pages` workflow will run on the revert commit and redeploy the previous working state.
3. Follow the failure protocol in `spec/smoke.md` before re-landing the change.

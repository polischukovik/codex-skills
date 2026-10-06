# Profiles

## Current profiles

- `auto`: Resolve `developer.genesys.cloud` to `genesys`; use `generic` for every other host.
- `generic`: Wait for `article`, `main`, or `[role="main"]`, then choose the best content container by text length.
- `genesys`: Fetch the underlying Yeti CMS Markdown asset first: `https://yeticms-api.genesys.cloud/assets/gc-dev-center<path>.md`. Fall back to browser rendering only if the asset path fails.

## Runtime notes

- Install optional Python packages with `python3 -m pip install --user ...` and Playwright browsers with `python3 -m playwright install chromium` so dependencies remain user-scoped instead of landing in a project checkout.
- For an isolated installation, `fetch_js_doc.py` also supports `python_deps/` and `playwright-browsers/` directories inside the skill folder.
- The output directory also maintains `index.json`, keyed by normalized source and final URLs, so repeated fetches for the same page can short-circuit to an existing snapshot.

## Extraction rules

- Remove scripts, styles, nav, footer, aside, breadcrumbs, toc blocks, cookie banners, and obvious UI chrome before Markdown conversion.
- Keep headings, paragraphs, lists, links, tables, and code blocks.
- Download image assets locally and rewrite Markdown image links to `<slug>_assets/...` when the fetch succeeds.
- Compact whitespace and drop boilerplate lines such as `On this page` after conversion.

## Adding a profile

1. Add the hostname rule to `resolve_profile`.
2. Add selector priorities to `PROFILE_SELECTORS`.
3. Add any site-specific noise selectors to `PROFILE_NOISE_SELECTORS`.
4. Add or update a fixture in `scripts/fixtures/`.
5. Extend `scripts/test_fetch_js_doc.py` to prove the new behavior without requiring a live fetch.

---
name: js-rendered-docs
description: Render JavaScript-driven documentation pages in a real browser and save compact Markdown snapshots plus metadata for later Codex use. Use when docs content is hidden behind client-side rendering, when `web.open` only returns an SPA shell or "enable JavaScript" placeholder, or when Codex needs a low-token local copy of pages such as developer.genesys.cloud.
---

# JS Rendered Docs

Use the script first. Keep the skill text short and let the script own rendering, waits, cleanup, extraction, and Markdown conversion. For `developer.genesys.cloud`, the script first tries the underlying Yeti CMS Markdown asset before launching a browser.

## Quick Start

For `developer.genesys.cloud`, try the script first. The Genesys profile fetches the underlying Markdown asset directly and may work with no extra packages.

Install the runtime once at user scope when you need the generic browser-rendered fallback. Do not place these dependencies in the current project:

```bash
python3 -m pip install --user playwright markdownify beautifulsoup4
python3 -m playwright install chromium
```

Fetch a page into a reusable local snapshot:

```bash
"$HOME/.agents/skills/js-rendered-docs/scripts/fetch_js_doc.py" \
  "https://developer.genesys.cloud/analyticsdatamanagement/analytics/aggregate/conversation-query" \
  --out-dir ./scraped-docs
```

## Workflow

1. Reuse an existing `./scraped-docs/*.md` snapshot when the user does not need a refresh.
2. Let the script consult `./scraped-docs/index.json`; it reuses an indexed snapshot for the same normalized URL unless `--overwrite` is passed.
3. Run `$HOME/.agents/skills/js-rendered-docs/scripts/fetch_js_doc.py <url> --out-dir ./scraped-docs` when the page is JS-rendered or the indexed snapshot is missing.
4. Read the generated Markdown file, not the raw HTML, unless debugging extraction problems.
5. Rerun with `--overwrite` only when the user wants a refresh.

## Outputs

- `<slug>.md`: primary Codex input with YAML frontmatter and compact Markdown
- `<slug>.meta.json`: fetch metadata, selector choice, and size stats
- `<slug>_assets/`: downloaded image assets referenced by the Markdown snapshot
- `index.json`: URL-to-snapshot cache used to avoid refetching the same page repeatedly
- `_debug/`: failure-only screenshot and rendered HTML for diagnosis

## Profiles

- Use `--profile auto` by default.
- `developer.genesys.cloud` resolves to the `genesys` profile.
- All other hosts resolve to `generic`.
- Read [references/profiles.md](references/profiles.md) before adding a new site profile.

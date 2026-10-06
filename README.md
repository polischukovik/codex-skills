# Codex Skills

Reusable skills for Codex and other Agent Skills-compatible hosts.

## Included skills

| Skill | Purpose | Runtime dependency |
| --- | --- | --- |
| `gc-cli` | Focused live validation against Genesys Cloud | Authenticated `gc` CLI; `jq` recommended |
| `genesys-live-proofing` | Design minimal live proofs and separate facts from inference | `gc-cli` for CLI execution |
| `genesys-platform-sdk-ref` | Inspect Genesys Cloud JavaScript SDK request and response shapes | `purecloud-platform-client-v2` in the npm cache or `GENESYS_PLATFORM_SDK_ROOT` |
| `genesys-flow-designer` | Design and operate Architect flows with Archy or the scripting SDK | `archy` on `PATH`; user-owned options files |
| `js-rendered-docs` | Save compact Markdown snapshots of JavaScript-rendered documentation | Python 3; optional Playwright, Beautiful Soup, and markdownify |
| `spreadsheet-export-audit` | Profile and compare large CSV/XLSX report exports | Standard shell tools; a spreadsheet/Python tool for advanced cases |
| `sql-contract-audit` | Check alignment among mapping CSVs, SQL projections, and playbooks | Python 3 and standard shell tools |

## Install one skill for Codex

Codex's user-global skill directory is `$HOME/.agents/skills`.

```bash
mkdir -p "$HOME/.agents/skills"
cp -R "skills/gc-cli" "$HOME/.agents/skills/gc-cli"
```

Copy only the skills you want. Codex detects skill changes automatically; restart it if a newly installed skill does not appear.

## Plugin package

The root `plugin.json` makes this collection a portable skills-only plugin. The individual folders under `skills/` remain usable as standalone Agent Skills.

## Configuration and secrets

- No credentials or tenant-specific configuration belong in this repository.
- Keep Archy options files under `$HOME/.config/genesys/archy/` or point to them with `ARCHY_QA_OPTIONS_FILE` and `ARCHY_PROD_OPTIONS_FILE`.
- Keep Genesys Cloud CLI authentication in the CLI's normal user configuration.
- Override the local Platform SDK location with `GENESYS_PLATFORM_SDK_ROOT` when npm-cache discovery is not appropriate.

## Validate

```bash
./scripts/audit-portability.sh
```

This checks skill structure, shell/Python syntax, accidental project-path coupling, and common secret-assignment patterns.

## License

No open-source license has been selected yet. Add one before publishing this repository publicly.

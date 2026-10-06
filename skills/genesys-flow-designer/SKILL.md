---
name: genesys-flow-designer
description: Use when a task involves designing, generating, refactoring, exporting, preprocessing, validating, or publishing Genesys Cloud Architect flows with Archy YAML and/or `purecloud-flow-scripting-api-sdk-javascript`, especially when the work should start from Archy documentation, use a configured Archy binary and options files correctly, and keep live org mutations explicit.
---

# Genesys Flow Designer

## Sources of Truth
- Primary Archy docs: `${ARCHY_DOCS_DIR:-$HOME/.local/share/genesys/archy/docs}` when that optional user-scoped bundle is installed
  - Start with `Welcome to Archy!.mhtml`, `Archy Installation.mhtml`, `Archy Example Flows.mhtml`, `Default Flows.mhtml`, and `Substitution.mhtml`.
- Primary SDK docs:
  - npm package: `purecloud-flow-scripting-api-sdk-javascript`
  - hosted docs: `https://mypurecloud.github.io/purecloud-flow-scripting-api-sdk-javascript/`
- Runtime checks:
  - Use the installed Archy binary's `--help` output to confirm command flags on this machine.
  - The reference snapshot in this skill was checked against Archy docs `2.39.2` and a `2.34.1` runtime; treat those versions as a baseline, not as the current installed version.
  - Use the docs bundle for concepts and examples, and the installed binary help for exact CLI behavior.

## Environment specifics
- Put the Archy executable on `PATH` as `archy`, or set `ARCHY_BIN`.
- User-scoped options files default to:
  - prod: `$HOME/.config/genesys/archy/env.prod.yaml`
  - qa: `$HOME/.config/genesys/archy/env.qa.yaml`
- Override them with `ARCHY_PROD_OPTIONS_FILE` and `ARCHY_QA_OPTIONS_FILE`.
- Those files contain `clientId` and `clientSecret`. Treat them as secrets and never print their contents.
- Do not infer `--location` from the options files. If a command needs a specific region override, require it explicitly.

## Default operating mode
1. Start read-only unless the user explicitly asks to mutate a Genesys Cloud org.
2. Prefer `export`, `preprocess`, `refresh`, `dump`, `version`, and `--help` when you are learning or inspecting.
3. Before `create`, `update`, or `publish`, confirm:
   - target environment: `qa` or `prod`
   - the concrete flow file or flow identifier
   - whether overwriting, unlocking, or recreating is acceptable
4. For existing flows, export first. Edit only after you have the current YAML or a scripted model of the current flow.

## Choosing Archy vs SDK
- Prefer Archy/YAML when:
  - the user wants a deployable flow artifact
  - the task is export, preprocess, create, update, or publish from YAML
  - you want to start from Archy default or example flow shapes
  - the change is easier to review as YAML
- Prefer Architect Scripting when:
  - you need code-driven generation or repeated structural edits
  - you need to create or refactor many similar flows
  - you want to validate, export, or transform flows in memory
  - you want machine-friendly export objects instead of immediately writing YAML files
- Combining them is normal:
  1. export or start from Archy YAML
  2. use the SDK for structured manipulation when helpful
  3. return to Archy for CLI-driven publish or update operations

## Archy workflow
1. Read `references/archy.md` for command behavior and local runtime specifics.
2. For new flows, read `references/examples.md` and start from the closest default or example flow in the downloaded docs.
3. Use substitutions for environment-specific values instead of hard-coding them into reusable YAML.
4. Run `preprocess` before mutating or publishing when substitutions or external refs are involved.
5. Prefer `--resultsFile` when you want machine-readable command output.

## Architect Scripting workflow
1. Read `references/architect-scripting.md` before writing SDK code.
2. Use the module namespaces instead of inventing constructors:
   - `environment.archSession`
   - `factories.archFactoryFlows`
   - `languages.archLanguages`
   - `enums.archEnums`
3. Start sessions with either:
   - `startWithClientIdAndSecret(...)` for client credentials
   - `startWithAuthToken(...)` for a supplied token
4. Prefer `validateAsync()` before `saveAsync()`, `checkInAsync()`, or `publishAsync()`.
5. Remember that `publishAsync()` is not atomic; it validates, saves, checks in, and then publishes.
6. Use `exportToObjectAsync()` when you want the export in memory. Use `exportToDirAsync()` only when file-system output is desired and the destination directory already exists.

## Safe command patterns
```bash
# Show installed Archy version
archy version

# Inspect command surface
archy --help
archy export --help
archy publish --help

# Preprocess a local YAML file with substitutions
"$HOME/.agents/skills/genesys-flow-designer/scripts/archy_run.sh" qa preprocess --file /abs/path/flow.yaml

# Export an existing flow as YAML
"$HOME/.agents/skills/genesys-flow-designer/scripts/archy_run.sh" prod export --flowName "My Flow" --flowType inboundemail --exportType yaml --outputDir /tmp/archy-export

# Publish a local flow YAML explicitly to prod
"$HOME/.agents/skills/genesys-flow-designer/scripts/archy_run.sh" prod publish --file /abs/path/flow.yaml
```

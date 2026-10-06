# Archy

## What the downloaded docs establish
- `Welcome to Archy!.mhtml`
  - Archy is a Genesys Cloud Architect YAML processor for creating, checking in, checking out, publishing, and updating flows.
  - Archy is intended for automated environments.
  - Archy is built on top of the Genesys Cloud Platform SDK and the Genesys Cloud Architect Scripting SDK.
- `Archy Installation.mhtml`
  - Archy can authenticate with an OAuth client or an auth token.
  - The docs recommend an OAuth client with:
    - token duration `86400`
    - grant type `Client Credentials`
    - `architect:ui:view` permission
- `Archy Example Flows.mhtml`
  - Basic flow examples are the best starting point for simple valid YAML shapes.
  - Default flow examples mimic what Architect creates in the UI.
- `Default Flows.mhtml`
  - Includes default YAML shapes for inbound call, inbound email, inbound message, in-queue call, outbound call, secure call, survey invite, workflow, and bot flow families.
- `Substitution.mhtml`
  - substitutions live at the YAML root under `substitutions`
  - keys cannot have leading or trailing whitespace
  - values must be string, number, or boolean
  - substitutions are applied at the end of preprocessing
  - quote strings that contain `{{ ... }}` substitutions

## Runtime specifics
- Put the Archy executable on `PATH` as `archy`, or set `ARCHY_BIN` for the bundled `scripts/archy_run.sh` wrapper.
- Reference runtime checked while authoring this skill: `2.34.1`.
- Reference docs version marker: `2.39.2`.
- Default user-scoped options files:
  - prod: `$HOME/.config/genesys/archy/env.prod.yaml`
  - qa: `$HOME/.config/genesys/archy/env.qa.yaml`
- Override those defaults with `ARCHY_PROD_OPTIONS_FILE` and `ARCHY_QA_OPTIONS_FILE`.
- Those options files contain `clientId` and `clientSecret` only. Do not print them, and do not assume they define `--location`.
- On this machine, many Archy subcommands print a Node version banner and an `ArchSessionId` before the main output.

## Command surface checked locally
- `archy --help`
  - commands exposed here include:
    - `changelog`
    - `checkin`
    - `checkout`
    - `checkVersion`
    - `configure`
    - `create`
    - `createImportFile`
    - `doesFlowExist`
    - `dump`
    - `export`
    - `isCheckedIn`
    - `isLocked`
    - `isPublished`
    - `preprocess`
    - `publish`
    - `refresh`
    - `setup`
    - `update`
    - `version`

### `export`
- `--flowName` plus `--flowType`, or `--flowId`
- `--flowVersion` defaults to `latest`
- accepted version strings include `latest`, `debug`, `published`, or a specific version like `2.0`
- `--exportType architect|yaml`
- `--outputDir` chooses the destination directory
- `--exportFileName` controls the output name
- `--force` overwrites an existing export file
- valid `--flowType` values include:
  - `bot`
  - `commonmodule`
  - `digitalbot`
  - `inboundcall`
  - `inboundchat`
  - `inboundemail`
  - `inboundshortmessage`
  - `inqueuecall`
  - `inqueueemail`
  - `inqueueshortmessage`
  - `outboundcall`
  - `securecall`
  - `surveyinvite`
  - `voice`
  - `voicemail`
  - `voicesurvey`
  - `workflow`
  - `workitem`

### `preprocess`
- `--file` or `--fileUri`
- writes `<flowYaml>_preprocess.yaml` next to the input YAML when using `--file`
- `--outputDir` overrides the output location
- `--full` adds `_orig` and `_resolved` properties to help inspect Archy's resolution behavior

### `refresh`
- refreshes Archy JSON schemas for the organization
- default output location is under Archy home in a `schemas` directory
- `--outputDir` overrides the schema output path

### `create`
- creates a flow from YAML
- does not publish it
- `--recreate` recreates the flow if it already exists
- `--forceUnlock` unlocks a flow held by another user first

### `update`
- updates an existing flow from YAML, creates it if missing
- checks the flow in
- does not publish it
- supports `--recreate` and `--forceUnlock`

### `publish`
- publishes a flow from YAML
- if the flow is checked out, Archy checks it in first
- supports `--recreate` and `--forceUnlock`

### `dump`
- writes current Archy configuration values
- only exposes `--resultsFile` and `--overwriteResultsFile`

### `checkVersion`
- checks for an Archy update
- only exposes `--debug`, `--resultsFile`, and `--overwriteResultsFile`

## Shared flags that matter in practice
- `--optionsFile`
  - supported on the networked commands checked here: `export`, `create`, `update`, `publish`, `refresh`, `preprocess`
  - use it to supply credentials and substitutions instead of inlining sensitive values on the command line
- `--resultsFile`
  - if you pass only a filename, Archy writes it under the `results` directory inside Archy home
  - if you pass a full path, Archy attempts to create missing parent directories
- `--overwriteResultsFile`
  - needed if the results file already exists
- auth override flags on networked commands:
  - `--authToken`
  - `--authTokenIsClientCredentials`
  - `--clientId`
  - `--clientSecret`
  - `--location`

## Recommended command patterns
```bash
# Installed binary help
archy --help

# Safe preprocess pass before a publish
"$HOME/.agents/skills/genesys-flow-designer/scripts/archy_run.sh" qa preprocess --file /abs/path/flow.yaml --resultsFile preprocess.json

# Export a flow as YAML
"$HOME/.agents/skills/genesys-flow-designer/scripts/archy_run.sh" prod export --flowName "Example Flow" --flowType inboundemail --exportType yaml --outputDir /tmp/archy-export

# Refresh local schemas
"$HOME/.agents/skills/genesys-flow-designer/scripts/archy_run.sh" qa refresh --resultsFile refresh.json
```

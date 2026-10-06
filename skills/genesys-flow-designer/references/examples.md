# Examples and starting points

## Start from the downloaded Archy docs
Use the downloaded docs bundle as the first place to look for flow structure and authoring patterns.

- `Welcome to Archy!.mhtml`
  - high-level orientation and links to the important Archy topics
- `Archy Installation.mhtml`
  - auth expectations and OAuth client setup guidance
- `Archy Example Flows.mhtml`
  - where to start for simple valid YAML shapes
- `Default Flows.mhtml`
  - the best source when you need a new flow that resembles Architect's default UI output
- `Default Inbound Email Flow.mhtml`
  - a minimal inbound email flow shape
- `Substitution.mhtml`
  - use this when environment-specific values should come from an options file instead of being hard-coded

## Practical doc-driven defaults
- New inbound email flow:
  - start from `Default Inbound Email Flow.mhtml`
  - then add variables, actions, settings, and error handling incrementally
- New common module or workflow:
  - start from `Default Flows.mhtml`
  - choose the closest default type before adding custom actions
- Reusable org-specific settings:
  - keep them in substitutions or options files
  - preprocess before publish so you can inspect the fully resolved YAML

## Publish shape
When the user explicitly requests a publish, use the configured Archy binary and options file:

```bash
archy publish \
  --file /abs/path/flow.yaml \
  --optionsFile "$HOME/.config/genesys/archy/env.prod.yaml"
```

Prefer the bundled helper script for new work:

```bash
"$HOME/.agents/skills/genesys-flow-designer/scripts/archy_run.sh" prod publish \
  --file /abs/path/flow.yaml
```

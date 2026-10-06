---
name: gc-cli
description: Use when a task needs focused live validation against Genesys Cloud through the local `gc` CLI, especially for spot testing API behavior, checking concrete entities, verifying payload assumptions, proving or disproving a mapping concept, or checking one live API scenario before changing code or documentation.
---

# GC CLI Skill

## Workflow
1. Use `gc` only for narrow live checks.
   - Prefer one user, one queue, one conversation, one day, or one small interval.
   - Do not turn the CLI into a bulk extractor when the task is only validation or concept proofing.
2. Start with help or shape discovery before guessing command syntax.
   - Examples:
     - `gc --help`
     - `gc analytics users details query create --help`
     - `gc conversations get --help`
3. For POST-style analytics queries, write a small JSON payload to `/tmp/gc-cli/` and call `gc ... create -f`.
   - Use `scripts/gc_json_query.sh` when a quick stdin-to-temp-file wrapper is faster than managing files manually.
4. Reduce output aggressively.
   - Prefer `jq` projections, counts, or a few representative rows over full raw dumps.
   - Summarize the evidence in the final response instead of pasting large payloads.
5. Clean up sensitive temporary payloads from `/tmp/gc-cli/` when the check is complete unless the user wants to keep them.

## Good Use Cases
- Verify whether a field exists in a live payload.
- Check whether a state transition really occurs in production data.
- Confirm whether two IDs refer to different resource types.
- Inspect one conversation, one user timeline, or one queue membership result.
- Prove whether a documented assumption matches actual API behavior.
- Spot-check a mapping rule before changing SQL or playbooks.

## Avoid
- Large historical pulls when a sampled proof is enough.
- Replacing repo documentation review with broad live exploration.
- Using the CLI as the default source when local code, samples, or docs already answer the question.

## Command Patterns
### Read one entity
```bash
gc conversations get <conversation-id>
gc users get <user-id>
gc users station get <user-id>
```

### List scoped resources
```bash
gc users list --pageSize 100 --pageNumber 1
gc routing queues members list <queue-id> --joined true --pageSize 100
gc telephony providers edges phones list --fields webRtcUser --pageSize 1000
```

### Run a focused analytics details query
Create a small request body in `/tmp/gc-cli/query.json`, then run:
```bash
gc analytics users details query create -f /tmp/gc-cli/query.json
gc analytics conversations details query create -f /tmp/gc-cli/query.json
```
Or pipe JSON directly through the helper script:
```bash
cat <<'JSON' | "$HOME/.agents/skills/gc-cli/scripts/gc_json_query.sh" analytics users details query create
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "userFilters": ["<user-id>"],
  "paging": {"pageSize": 25, "pageNumber": 1}
}
JSON
```

## Repo-Specific References
Read these only when needed:
- `references/recipes.md`
  - concrete command recipes for the Avaya-mapping repo workflows
  - use for conversation details, user details, queue members, phone/site/location, station, IVR, and synonym-related checks
- `references/payloads.md`
  - minimal JSON payload shapes for analytics queries used in this repo

## Output Discipline
- Prefer commands that already scope the result set.
- If the output is still large, post-process it immediately with `jq` or a short shell summary.
- Capture only the fields needed to support the conclusion.

## Practical Rules
- Treat live CLI checks as corroborating evidence, not as a substitute for stable repo contracts.
- If the environment blocks networked CLI access, request escalation rather than working around it.
- When the same proof requires several related commands, keep them on the same entity or interval so the evidence is coherent.
- When validating a bug or mapping claim, report the exact command and the exact fields that proved it.

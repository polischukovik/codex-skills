---
name: genesys-live-proofing
description: Use when a task needs a minimal live proof against Genesys Cloud rather than broad exploration, especially to verify one mapping claim, resolve an ambiguity in API behavior, confirm a state transition, or distinguish evidence from inference before changing code or documentation.
---

# Genesys Live Proofing Skill

## Workflow
1. State the exact claim to prove or disprove.
   - Example: "routingStatus can remain INTERACTING without a voice conversation leg."
2. Choose the smallest live proof.
   - Prefer one user, one conversation, one queue, one IVR, or one short interval.
3. Pick the narrowest endpoint set that can answer the claim.
   - Prefer direct entity GETs first.
   - Use analytics details only when timeline evidence is required.
4. Keep evidence coherent.
   - Use the same entity and interval across commands.
   - Correlate timestamps and IDs explicitly.
5. Separate facts from inference.
   - Facts: exact fields returned by the API.
   - Inference: what those fields imply for the mapping or design.
6. Conclude with one of three outcomes.
   - confirmed
   - disproven
   - inconclusive with the exact missing evidence

## Selection Rules
- Use `gc-cli` command patterns for execution.
- Read `references/decision-tree.md` when you need help choosing the smallest proof.
- Read `references/evidence-template.md` when you need a compact structure for reporting findings.

## Practical Rules
- Do not start with org-wide pulls.
- Do not mix multiple hypotheses in one proof run.
- Prefer one concrete counterexample over many weak examples.
- When proving a semantic mismatch, capture the field names and timestamps that show it.
- If live data disagrees with local docs, report both and say which one is authoritative for the decision.

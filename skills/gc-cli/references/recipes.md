# GC CLI Recipes For Avaya Mapping

Use these recipes for live spot checks in this repo. Keep requests small and summarize the result instead of pasting raw payloads.

## 1. Check one conversation in full
```bash
gc conversations get <conversation-id>
```
Use when you need participant purposes, segment types, queue names, call direction, or to confirm whether a suspicious `AG_ACTV` row is backed by a real conversation leg.

Useful projection:
```bash
gc conversations get <conversation-id> \
  | jq '.participants[] | {purpose, participantType, userId, queueId, queueName, segments: [.sessions[].segments[]? | {segmentType, startTime, endTime}]}'
```

## 2. Query one user's analytics details for one day
```bash
cat <<'JSON' >/tmp/gc-cli/user-details.json
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "userFilters": ["<user-id>"],
  "paging": {"pageSize": 25, "pageNumber": 1}
}
JSON

gc analytics users details query create -f /tmp/gc-cli/user-details.json
```
Use for presence/routing timelines, `HAGLOG` session proofs, and `AG_ACTV` workmode investigations.

Useful projection:
```bash
gc analytics users details query create -f /tmp/gc-cli/user-details.json \
  | jq '.userDetails[].primaryPresence[]?, .userDetails[].routingStatus[]?'
```

## 3. Query one conversation-details interval
```bash
cat <<'JSON' >/tmp/gc-cli/conversation-details.json
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "conversationFilters": [{"type": "or", "predicates": [{"dimension": "conversationId", "value": "<conversation-id>"}]}],
  "paging": {"pageSize": 25, "pageNumber": 1}
}
JSON

gc analytics conversations details query create -f /tmp/gc-cli/conversation-details.json
```
Use when the normal conversation GET is not enough and you need analytics-leg detail behavior.

## 4. Verify queue membership for one queue
```bash
gc routing queues members list <queue-id> --joined true --pageSize 100
```
Use for current-membership spot checks. Do not use this as a bulk extractor by default.

## 5. Verify queues for one user
```bash
gc users queues list <user-id> --joined true --pageSize 100
```
Use when you already have one user in scope and want the current joined queue set.

## 6. Check current station for one user
```bash
gc users station get <user-id>
```
Use when comparing station semantics to phone semantics.

## 7. Resolve phones tied to one user
```bash
gc telephony providers edges phones list --fields webRtcUser --webRtcUserId <user-id> --pageSize 1000
```
Use for `EXTN`/`LOC_ID` investigations based on phone assignment.

## 8. Resolve sites with locations
```bash
gc telephony providers edges sites list --expand location --pageSize 1000
```
Use when you need `site.location.id` for the phone-to-location chain.

## 9. Resolve one IVR or list IVRs
```bash
gc architect ivrs list --pageSize 100
gc architect ivrs get <ivr-id>
```
Use for `VDN` / call-routing entity checks.

## 10. Check one organization/user/entity directly
```bash
gc organizations me
gc users get <user-id>
gc routing queues get <queue-id>
```
Use when validating which stable Genesys id should back a synonym/export code.

## Notes
- Prefer one entity and one interval at a time.
- If the result is large, immediately summarize it with `jq`, `rg`, `head`, `wc`, or a focused transform.
- Keep `/tmp/gc-cli/` payloads disposable unless they are useful evidence for a follow-up step.

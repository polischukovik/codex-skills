# Decision Tree

## Choose the smallest proof
- Need to know whether one conversation leg exists: use `gc conversations get <conversation-id>`.
- Need analytics timeline behavior for one user/day: use `gc analytics users details query create` with one `userId` and one day.
- Need analytics conversation-leg behavior: use `gc analytics conversations details query create` scoped to one conversation or one short interval.
- Need current queue membership: use one queue or one user membership lookup, not both, unless the mismatch itself is the claim.
- Need phone/station/site semantics: resolve one user through `users station get`, `phones list --webRtcUserId`, and `sites list --expand location`.

## Stop conditions
- You already have one clear supporting payload.
- A second endpoint would only repeat the same evidence.
- The remaining uncertainty is policy, not API behavior.

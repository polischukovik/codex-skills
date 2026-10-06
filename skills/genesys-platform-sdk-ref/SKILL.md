---
name: genesys-platform-sdk-ref
description: Use when a task involves the Genesys Cloud Platform API and there is any doubt about request payload shape, query option names, API method names, auth/environment setup, or response types. This skill uses the locally predownloaded `purecloud-platform-client-v2` SDK as the first reference and provides a helper to inspect method signatures, `Models.*` shapes, `*Options` interfaces, and the generated API implementation locally before guessing.
---

# Genesys Platform SDK Reference

## Purpose
- Use this skill when the question is about Genesys Cloud Platform API usage rather than Architect flow design.
- Default stance: do not guess request shapes.
- When there is doubt about:
  - a body payload shape
  - query parameter names
  - which API class owns a method
  - auth or environment setup
  - request path or HTTP verb
  - whether a method is preview or has special caveats
  use the local Platform SDK files first.

## Local source of truth
- Primary local reference is the predownloaded JavaScript SDK package `purecloud-platform-client-v2`.
- On this machine, the helper script discovers the SDK root dynamically under the local npm cache.
- The checked local copy during skill creation was version `239.0.0`.

## What to inspect and why
- `README.md`
  - auth patterns
  - `ApiClient.instance` usage
  - `setEnvironment(...)`
  - high-level request examples
  - notes like preview API caveats and parameter filtering behavior
- `index.d.ts`
  - API method signatures
  - body model names like `Models.ConversationQuery`
  - `*Options` interfaces for query params
  - `ApiClient` methods and environment/auth helpers
- `src/purecloud-platform-client-v2/api/*.js`
  - concrete endpoint path
  - HTTP method
  - required parameter checks
  - query parameter serialization via `buildCollectionParam(...)`
  - content type / accept arrays
- `src/purecloud-platform-client-v2/index.js`
  - exported API constructors such as `new platformClient.UsersApi()`
- `src/purecloud-platform-client-v2/PureCloudRegionHosts.js`
  - region constants for `client.setEnvironment(...)`

## Workflow
1. Read `references/platform-sdk.md` for the local SDK layout and the most useful files.
2. Run the helper script before guessing:
   - `scripts/sdk_lookup.py root`
   - `scripts/sdk_lookup.py request <methodName>`
   - `scripts/sdk_lookup.py model <ModelName>`
   - `scripts/sdk_lookup.py symbol <text>`
3. For a request method:
   - inspect the TypeScript signature in `index.d.ts`
   - note any `Models.*` request body type
   - inspect any `*Options` interface for query params
   - inspect the generated API JS method for path, verb, and parameter handling
4. Only after the local SDK pass should you summarize the shape or propose code.

## Practical rules
- Prefer the local SDK over memory for shape questions.
- If `index.d.ts` and the generated API JS disagree, call that out explicitly.
- If a method is present in multiple API classes, report both and explain the difference if visible.
- For auth/environment setup, use the local README plus the `ApiClient` typings instead of guessing from other languages.
- Treat preview APIs as unstable if the README or generated comments mark them that way.

## Quick examples
```bash
# Find the SDK root and version
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" root

# Inspect a request method end to end
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" request postAnalyticsConversationsDetailsQuery

# Show a request body shape
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" model ConversationQuery

# Search for auth/environment helpers
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" symbol setEnvironment
```

## References
- `references/platform-sdk.md`
- `references/lookup-patterns.md`

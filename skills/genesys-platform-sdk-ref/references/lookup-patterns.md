# Lookup Patterns

## Use the helper first
```bash
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" root
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" request getUsersMe
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" model ConversationQuery
"$HOME/.agents/skills/genesys-platform-sdk-ref/scripts/sdk_lookup.py" symbol setUseLegacyParameterFilter
```

## Typical tasks

### I know the method name but not the payload
1. Run `request <methodName>`.
2. Read the method signature in `index.d.ts`.
3. If it references `Models.<Name>`, inspect that model block.
4. If it references `opts?: <Api>.<Name>Options`, inspect that options block too.

### I know the model name but not where it is used
1. Run `model <ModelName>`.
2. Run `symbol Models.<ModelName>` if you also want all method signatures that use it.

### I know the endpoint idea but not the SDK class
1. Run `symbol /api/v2/...` if you have the path fragment.
2. Or run `symbol <resourceName>` and inspect hits in:
   - `index.d.ts`
   - `src/.../api/*.js`
   - `README.md`

### I need to know whether `expand`, paging, or other query params exist
1. Run `request <methodName>`.
2. Inspect the `*Options` interface from `index.d.ts`.
3. Inspect the generated API JS method to see collection formatting like `multi`.

## What the helper output means
- `SDK root`
  - where the local package was found
- `TypeScript signatures`
  - authoritative method signature and model names
- `Options interfaces`
  - query parameter shape
- `Models`
  - body and response interfaces from `index.d.ts`
- `Generated API implementation`
  - path, verb, parameter checks, content types, and serialization details

## When not to stop at the SDK
- If the question is about live behavior, permissions, or current org data, use a live tool after the local SDK pass.
- If the method exists but the shape is still ambiguous, say exactly what the SDK proves and what it does not prove.

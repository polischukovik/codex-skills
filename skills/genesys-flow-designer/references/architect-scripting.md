# Architect Scripting SDK

## Primary docs
- npm package: `https://www.npmjs.com/package/purecloud-flow-scripting-api-sdk-javascript`
- hosted docs: `https://mypurecloud.github.io/purecloud-flow-scripting-api-sdk-javascript/`
- local package help page after install:
  - `<project>/node_modules/purecloud-flow-scripting-api-sdk-javascript/src/scripting/documentation/index.html`

## Package facts checked here
- package name: `purecloud-flow-scripting-api-sdk-javascript`
- current package version checked here: `0.66.1`
- README labels it as `Architect Scripting - Alpha`
- Node requirement from the package: `>=20.0.0`
- README summary: the SDK can programmatically create, check in, check out, modify, and publish Genesys Cloud Architect flows

## Namespaces and entry points
Use the exported SDK namespaces instead of inventing constructors that are not part of the public module surface.

```js
const scripting = require('purecloud-flow-scripting-api-sdk-javascript');

const session = scripting.environment.archSession;
const flows = scripting.factories.archFactoryFlows;
const languages = scripting.languages.archLanguages;
const enums = scripting.enums.archEnums;
```

## Session startup
The two real session entry points exposed by the typings are:
- `session.startWithClientIdAndSecret(orgLocation, callbackStart, clientId, clientSecret, callbackEnd?, isClientCredentialsOAuthClient?, options?)`
- `session.startWithAuthToken(orgLocation, callbackStart, authToken, callbackEnd?, isClientCredentialsOAuthClient?, options?)`

Important details from the typings:
- when using a Client Credentials OAuth client or its token, set `isClientCredentialsOAuthClient` to `true`
- optional `SessionStartOptions` supports:
  - `cacheEnabled`
  - `showCacheDiagnostics`
- `session.endTerminatesProcess` defaults to process-exit behavior; set it to `false` if the script should continue running after the Architect session ends

## Flow factory surface
The flow factory exposes dedicated creation methods for specific flow types, including:
- `createFlowInboundCallAsync`
- `createFlowInboundChatAsync`
- `createFlowInboundEmailAsync`
- `createFlowInQueueCallAsync`
- `createFlowInQueueEmailAsync`
- `createFlowCommonModuleAsync`
- `createFlowWorkflowAsync`
- `createFlowVoiceAsync`
- `createFlowWorkitemAsync`

The typings explicitly note that created flow objects are local in-memory objects until you save, check in, or publish them.

## Core flow methods to prefer
- `validateAsync()`
- `saveAsync()`
- `checkInAsync(ensureSearchable?)`
- `publishAsync(ensureSearchable?)`
- `checkoutAsync(forceUnlock?, callback?)`
- `loadAsync(flowVersion?, callback?)`
- `exportToObjectAsync(callback, flowFormat?)`
- `exportToDirAsync(destinationDir?, callback?, flowFormat?, fileName?)`
- `importFromContentAsync(exportContent, callback?)`
- `importFromFileAsync(exportFilePath, callback?)`

Important behavior from the typings:
- `publishAsync()` performs validate, save, check-in, and publish in sequence
- `publishAsync()` is not atomic
- `exportToDirAsync()` requires the destination directory to already exist
- `exportToObjectAsync()` is the safer default for machine-driven workflows because it does not need a pre-existing directory

## Minimal safe pattern
Use an export or validation-first sequence by default. Only swap in `saveAsync()`, `checkInAsync()`, or `publishAsync(true)` when the user explicitly asked to mutate an org.

```js
const scripting = require('purecloud-flow-scripting-api-sdk-javascript');

const session = scripting.environment.archSession;
session.endTerminatesProcess = false;

await session.startWithClientIdAndSecret(
  'mypurecloud.de',
  async () => {
    const flow = await scripting.factories.archFactoryFlows.createFlowInboundEmailAsync(
      'Example Inbound Email Flow',
      'Generated from Architect Scripting',
      scripting.languages.archLanguages.englishUnitedStates
    );

    const validation = await flow.validateAsync();
    if (validation.hasErrors) {
      console.error(validation.getSummaryStr(true));
      session.endExitCode = 1;
      return;
    }

    await flow.exportToObjectAsync((exportInfo) => {
      console.log(exportInfo.fileName);
      console.log(exportInfo.content);
    }, scripting.enums.archEnums.FLOW_FORMAT_TYPES.yaml);
  },
  process.env.GENESYS_CLIENT_ID,
  process.env.GENESYS_CLIENT_SECRET,
  undefined,
  true,
  { cacheEnabled: true }
);
```

## When to prefer the SDK
- generating a new flow from code
- applying the same structural change across many flows
- refactoring flows in memory before deciding whether to write YAML
- exporting or validating without committing to a CLI publish step

## When to prefer Archy instead
- the user wants a YAML artifact as the primary deliverable
- the task is driven by Archy example flows or substitutions
- the deliverable is an explicit `create`, `update`, `publish`, `export`, or `preprocess` CLI workflow

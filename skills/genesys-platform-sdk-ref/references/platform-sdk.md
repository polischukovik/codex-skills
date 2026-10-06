# Local Platform SDK Reference

## Package found locally
- Package: `purecloud-platform-client-v2`
- Version checked while creating this skill: `239.0.0`
- Repository from package metadata: `https://github.com/MyPureCloud/platform-client-sdk-javascript`
- Hosted docs from README: `https://mypurecloud.github.io/platform-client-sdk-javascript/`

## Local file roles
- `README.md`
  - main auth examples for:
    - client credentials
    - SAML2 bearer
    - authorization code
    - PKCE
    - implicit grant
  - `ApiClient.instance`
  - `client.setEnvironment(platformClient.PureCloudRegionHosts.eu_west_1)`
  - `client.setUseLegacyParameterFilter(false)` when false/zero query values must be preserved
  - request examples like `new platformClient.UsersApi().getUsersMe(...)`
- `index.d.ts`
  - best file for request shapes
  - contains:
    - API classes like `UsersApi`, `AnalyticsApi`, `RoutingApi`
    - API methods like `getUsersMe(opts?: UsersApi.getUsersMeOptions)`
    - model interfaces under `declare namespace Models`
    - option interfaces under `declare namespace <ApiName>`
    - `ApiClient` methods like `loginClientCredentialsGrant`, `setAccessToken`, `setEnvironment`
- `src/purecloud-platform-client-v2/api/*.js`
  - best file for concrete endpoint details
  - generated methods show:
    - path like `'/api/v2/users/me'`
    - HTTP verb
    - required parameter checks
    - query serialization and `buildCollectionParam`
    - body placement in `callApi(...)`
- `src/purecloud-platform-client-v2/index.js`
  - shows how API constructors are exported
- `src/purecloud-platform-client-v2/PureCloudRegionHosts.js`
  - region constant map, for example:
    - `eu_west_1 -> mypurecloud.ie`
    - `eu_central_1 -> mypurecloud.de`
    - `us_west_2 -> usw2.pure.cloud`

## Reliable lookup pattern
When a request shape is unclear:
1. Find the SDK method in `index.d.ts`.
2. Capture:
   - the API class
   - the request body type under `Models.*`
   - any `*Options` interface
   - the response model
3. Open the matching generated API JS method to confirm:
   - path
   - HTTP verb
   - required params
   - query/body placement
4. Open the model interface block in `index.d.ts`.

## Concrete example
For `postAnalyticsConversationsDetailsQuery`:
- `index.d.ts` shows:
  - method: `postAnalyticsConversationsDetailsQuery(body: Models.ConversationQuery)`
  - response: `Promise<Models.AnalyticsConversationQueryResponse>`
- `Models.ConversationQuery` in `index.d.ts` shows the request shape:
  - `interval`
  - `conversationFilters`
  - `segmentFilters`
  - `evaluationFilters`
  - `surveyFilters`
  - `resolutionFilters`
  - `order`
  - `orderBy`
  - `aggregations`
  - `paging`
- generated API JS shows:
  - path `/api/v2/analytics/conversations/details/query`
  - method `POST`
  - required `body`

## Auth and environment facts confirmed locally
- `client = platformClient.ApiClient.instance`
- client credentials method:
  - `client.loginClientCredentialsGrant(clientId, clientSecret)`
- environment method:
  - `client.setEnvironment(platformClient.PureCloudRegionHosts.eu_west_1)`
- important parameter-filtering behavior from README:
  - legacy filtering can drop `false` and `0` query parameters
  - `client.setUseLegacyParameterFilter(false)` switches to modern behavior

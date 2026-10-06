# Minimal Payloads

## User details by one user and one interval
```json
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "userFilters": ["<user-id>"],
  "paging": {"pageSize": 25, "pageNumber": 1}
}
```

## User details by a small user batch
```json
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "userFilters": ["<user-id-1>", "<user-id-2>"],
  "paging": {"pageSize": 100, "pageNumber": 1}
}
```

## Conversation details by one conversation id
```json
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "conversationFilters": [
    {
      "type": "or",
      "predicates": [
        {"dimension": "conversationId", "value": "<conversation-id>"}
      ]
    }
  ],
  "paging": {"pageSize": 25, "pageNumber": 1}
}
```

## Queue aggregate example with scoped grouped dimension
```json
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "groupBy": ["queueId"],
  "filter": {
    "type": "and",
    "clauses": [
      {
        "type": "or",
        "predicates": [
          {"dimension": "queueId", "value": "<queue-id>"}
        ]
      },
      {
        "type": "or",
        "predicates": [
          {"dimension": "mediaType", "value": "voice"}
        ]
      }
    ]
  },
  "metrics": ["nOffered", "tAnswered", "tAbandon"]
}
```

## DNIS aggregate example
```json
{
  "interval": "2026-03-16T00:00:00.000Z/2026-03-17T00:00:00.000Z",
  "groupBy": ["dnis"],
  "flattenMultivaluedDimensions": true,
  "filter": {
    "type": "and",
    "clauses": [
      {
        "type": "or",
        "predicates": [
          {"dimension": "dnis", "value": "<dnis>"}
        ]
      },
      {
        "type": "or",
        "predicates": [
          {"dimension": "mediaType", "value": "voice"}
        ]
      }
    ]
  },
  "metrics": ["nOffered", "tAnswered", "tAbandon"]
}
```

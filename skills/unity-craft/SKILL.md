# CRAFT — Unity Scene Manipulation Skill

## Trigger

Activate when the user mentions:
- "unity scene", "unity editor", "gameobject", "create object", "add component"
- "rollback", "undo", "revert scene"
- "scene query", "find object", "search scene"
- "scene doctor", "fix scene"

## Golden Rules

1. **Always use `Craft_Execute` for scene mutations** — never use raw Unity MCP tools (Unity_ManageGameObject etc.) for operations that need safety
2. **Name transactions descriptively** — e.g., "Add player spawn point with BoxCollider"
3. **Query before modify** — use `Craft_Query` to find targets before `Craft_Execute`
4. **validate=true is default** — trust the validation, don't skip it
5. **Always report transactionId** — the user needs it for rollback

## Tool Usage Patterns

### Create a GameObject

```json
Craft_Execute({
  "operations": [
    {
      "type": "CreateGameObject",
      "target": null,
      "parameters": {
        "name": "Player",
        "primitiveType": "Capsule",
        "position": [0, 1, 0],
        "components": ["Rigidbody", "CapsuleCollider"]
      }
    }
  ],
  "transactionName": "Create Player capsule with physics"
})
```

### Find and Modify

```json
// Step 1: Find the target
Craft_Query({
  "query": "Player",
  "filters": { "components": ["Rigidbody"] },
  "maxResults": 5
})

// Step 2: Modify using the path from query result
Craft_Execute({
  "operations": [
    {
      "type": "ModifyComponent",
      "target": "Player",
      "parameters": {
        "componentType": "Rigidbody",
        "values": {
          "mass": 2.0,
          "useGravity": true
        }
      }
    }
  ],
  "transactionName": "Set Player mass to 2"
})
```

### Batch Operations (Single Transaction)

```json
Craft_Execute({
  "operations": [
    {
      "type": "CreateGameObject",
      "parameters": { "name": "Environment" }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Ground",
        "primitiveType": "Plane",
        "parent": "Environment",
        "scale": [10, 1, 10]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "SpawnPoint",
        "position": [0, 1, 0],
        "parent": "Environment"
      }
    }
  ],
  "transactionName": "Create environment with ground and spawn point"
})
```

### Delete with Safety

```json
// Always query first to confirm the target
Craft_Query({ "query": "OldObject" })

// Then delete
Craft_Execute({
  "operations": [
    { "type": "DeleteGameObject", "target": "OldObject" }
  ],
  "transactionName": "Remove OldObject"
})
```

### Rollback

```json
// By transaction ID (from Craft_Execute result)
Craft_Rollback({ "transactionId": "abc-123-def" })

// Or by steps
Craft_Rollback({ "steps": 3 })
```

### Validate Before Risky Operations

```json
Craft_Validate({
  "operations": [
    {
      "type": "ModifyComponent",
      "target": "MainCamera",
      "parameters": {
        "componentType": "Camera",
        "values": { "fieldOfView": 90 }
      }
    }
  ]
})
```

### Check Engine Status

```json
Craft_Status({ "include": ["transactions", "lastTrace"] })
```

## Operation Types Reference

| Type | Target | Key Parameters |
|------|--------|----------------|
| `CreateGameObject` | — | name, primitiveType, position, rotation, scale, parent, components |
| `ModifyComponent` | GO path | componentType, values (field/prop → value map) |
| `DeleteGameObject` | GO path | — |

## Error Handling

- **Validation failure**: Report errors to user, suggest fixes
- **Execution failure**: Auto-rollback happens, report the error and trace
- **Transaction reported**: Always show the transactionId so user can rollback manually later

## Response Format

After successful execution, always tell the user:
1. What was done (summary)
2. The transactionId (for rollback)
3. Any warnings from validation or trace

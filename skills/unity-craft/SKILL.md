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
6. **Never output user-facing click instructions** — all actions execute via CRAFT or vision-driven dispatch. FORBIDDEN: "click X", "open Y menu", "go to Window > Z", "do setup step N". See `tools/screen-control.md` Forbidden Output Patterns.

## Extended Capabilities

Eleven tool families extend core CRAFT scene ops:

| Family | Tool file | Dispatch target | Purpose |
|--------|-----------|-----------------|---------|
| **Game Director** | [`tools/game-director.md`](tools/game-director.md) | A14 game-director | GDD → game pipeline — DAG, dispatch, critique loop, playtest |
| **Design Import** | [`tools/import-design-bundle.md`](tools/import-design-bundle.md) | D11 unity-ui-developer | Claude Design handoff bundle → UXML + USS + UIDocument |
| **Screen Control** | [`tools/screen-control.md`](tools/screen-control.md) | G13 vision-action-operator | Capture + analyze + act (autonomous, no user instructions) |
| **Cinematic** | [`tools/cinematic.md`](tools/cinematic.md) | E9 unity-cinematic-director | Cinemachine VCams + PostFX presets + shot capture |
| **Animation** | [`tools/animation.md`](tools/animation.md) | E9 unity-cinematic-director | Animator + Timeline + state machines + curve presets |
| **Level Design** | [`tools/level-design.md`](tools/level-design.md) | E11 unity-level-designer | Modular rooms, terrain, NavMesh, lighting presets |
| **Optimization** | [`tools/optimization.md`](tools/optimization.md) | B53 unity-performance-analyzer | Profile + batch + textures + LOD + quality + purge |
| **Audio** | [`tools/audio.md`](tools/audio.md) | B26 unity-audio-engineer | AudioMixer groups, snapshots, spatial setup, import presets |
| **Asset Store** | [`tools/asset-store.md`](tools/asset-store.md) | E16 asset-store-curator | Library inventory + UPM/OpenUPM/Git research + install |
| **Input System** | [`tools/input.md`](tools/input.md) | B36 unity-input-system | Action maps + bindings + UI Toolkit rebind UI |
| **Playtest** | [`tools/playtest.md`](tools/playtest.md) | A14 + G13 + B53 | Enter Play mode, scripted scenarios, sampled perf |
| **Critique** | [`tools/critique.md`](tools/critique.md) | G13 + specialist per scope | Self-scorecard UI/level/assets/hierarchy |

Read the relevant `tools/*.md` file before invoking a capability — each has signature, pipeline, dispatch protocol, and verification.

**Upstream dependency:** Screen control + texture/profile optimization need new ops in `com.skywalker.craft` (Craft_Inspect + Craft_ImportSettings). See [`tools/craft-unity-upstream-ops.md`](tools/craft-unity-upstream-ops.md) — implement that PR first, then these capabilities unlock.

**Presets:** `presets/cinema/*.json`, `presets/postfx/*.json`, `presets/animation/*.json`, `presets/input/*.json`, `presets/quality/*.json`, `presets/texture/*.json` — loaded by tool handlers, don't edit at runtime.

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

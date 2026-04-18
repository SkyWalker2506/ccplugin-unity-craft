# Level Design Tool Family

## Purpose

Structured level authoring for game production: modular room construction with ProBuilder, procedural prefab placement, terrain sculpting and painting, occlusion setup, and NavMesh carving. This tool complements core scene manipulation with dedicated patterns for building playable levels at scale. Dispatch target: **E11 unity-level-designer** (GPT-5.4).

The tool manages:
- **ProBuilder volumes** — room primitives with walls, ceilings, floors; parametric subdivision for doors/windows
- **Modular prefab placement** — grid, path, or cluster-based layout with collision detection and LOD setup
- **Terrain sculpting** — height-map based deformation from preset curves (flat, rolling, mountainous)
- **Terrain painting** — texture assignment with layer blending (grass, dirt, stone, sand, water)
- **NavMesh carving** — automatic surface bake for humanoid/small/large agent types; returns asset paths
- **Spawn points** — transform + tag markers for runtime player/enemy/item placement
- **Lighting presets** — directional, ambient, reflection probes with real-time or baked workflows
- **Preset system** — 6 curated level templates for rapid level prototyping (sandbox, dungeon, outdoor, platformer, racing, combat)

## Tool Signatures

### Level_CreateRoom

```
Level_CreateRoom(
  name: string,
  size: Vector3,
  wallThickness?: number = 0.3,
  floor?: boolean = true,
  ceiling?: boolean = true,
  doorPositions?: [Vector3]
) → {
  roomPath: string,
  transactionId: string,
  wallCount: number,
  geometry: object
}
```

Creates a ProBuilder room primitive with parametric walls and optional floor/ceiling. Uses ProBuilder cube as base, applies subtract operations to carve wall geometry. Wall thickness defines the shell; doorPositions array specifies [x, y, z] offsets for door apertures (default none).

**Behavior:**
- Base cube created at origin, size = [length, height, width]
- If `floor=true`: ground plane at y=0, same footprint as base
- If `ceiling=true`: top cap at y=height
- Walls are ProBuilder Face objects, optimized for lightmapping
- Each door position subtracts a 0.9×2.1m aperture from the nearest wall
- Returns roomPath (scene hierarchy), transactionId (rollback), and wallCount

### Level_PlaceModular

```
Level_PlaceModular(
  prefabRefs: string[],
  layout: "grid" | "path" | "cluster",
  count: number,
  spacing: number,
  seed?: number,
  avoidCollision?: boolean = true
) → {
  placedCount: number,
  positions: [Vector3],
  transactionId: string,
  collisionWarnings: string[]
}
```

Instantiate prefab clones in a procedural pattern. Layout determines placement:
- **grid**: Cartesian 2D grid, spacing in X/Z, Y=0 baseline
- **path**: Linear line (Z-axis), spacing controls density, optional spline interpolation
- **cluster**: Radial around origin, spacing = radius ring delta

Uses `PrefabUtility.InstantiatePrefab` to maintain prefab links. Seed enables deterministic replay. avoidCollision checks bounds against existing GameObjects and warns if overlaps detected.

**Behavior:**
- Prefabs selected by name regex or asset path from prefabRefs[]
- Each clone parented to a `_Modular_<layoutType>` container
- Rotation defaults to (0,0,0); can be randomized (opt-in via advanced params)
- Collision test uses physics `Bounds.Intersects()` — warns but does not abort
- Returns placedCount, array of placed positions, and warnings

### Level_CreateTerrain

```
Level_CreateTerrain(
  size: Vector3,
  heightmap: "flat" | "rolling" | "mountainous",
  texturePreset: string,
  treeDensity: number = 0.0
) → {
  terrainPath: string,
  terrainDataPath: string,
  transactionId: string,
  heightSamples: number
}
```

Create a TerrainData asset and apply height sculpting from a preset curve. Heightmap presets define height variation:
- **flat**: Minimal relief, y ∈ [0, 0.5]
- **rolling**: Gentle hills, y ∈ [0, 5] with 2-3 peaks
- **mountainous**: Jagged ridges, y ∈ [0, 15] with sharp peaks and valleys

TexturePreset selects a layer stack (e.g., "grass-dirt-stone", "desert-sand-rock"). TreeDensity ∈ [0, 1] controls tree prefab placement density (requires com.unity.terrain-tools).

**Behavior:**
- TerrainData created at size (width, height, length), resolution 513×513 heightmap
- Sculpt curve applied via Perlin noise seeded by preset name
- Texture layers composited from `Assets/Terrains/Materials/<preset>.terrainlayer` files
- Trees instantiated if treeDensity > 0 and Tree prefab found in scene
- Returns terrainPath (GameObject), terrainDataPath (asset), and heightSamples count

### Level_CarveNavMesh

```
Level_CarveNavMesh(
  scenePath: string,
  agentType: "humanoid" | "small" | "large"
) → {
  navMeshPath: string,
  bakeTime: number,
  transactionId: string,
  walkableArea: number,
  warnings: string[]
}
```

Trigger NavMesh surface bake for the scene. Requires NavMeshSurface component (from com.unity.ai.navigation package). AgentType selects pre-configured agent settings:
- **humanoid**: radius=0.5m, height=2.0m, step height=0.4m, max slope=45°
- **small**: radius=0.25m, height=1.0m, step height=0.2m, max slope=35°
- **large**: radius=1.0m, height=2.5m, step height=0.6m, max slope=30°

**Behavior:**
- Queries scene for NavMeshSurface component; if missing, creates one at root
- Applies agent settings from `presets/navmesh/<agentType>.json`
- Calls `NavMeshSurface.Bake()` synchronously (may block for large scenes)
- Saves NavMesh asset to `Assets/NavMesh/<sceneName>_<agentType>.asset`
- Returns navMeshPath, bake time in seconds, walkable area in m², and any warnings (obstacles, no surface, etc.)

### Level_AddSpawnPoint

```
Level_AddSpawnPoint(
  name: string,
  position: Vector3,
  rotation: Vector3,
  tags?: string[] = []
) → {
  spawnPointPath: string,
  transactionId: string,
  tags: string[]
}
```

Create a Transform marker for runtime spawn logic. No visual geometry; used by gameplay code to instantiate objects. Tags allow runtime filtering (e.g., "player_start", "enemy_melee", "chest_loot").

**Behavior:**
- Creates empty GameObject at position with Euler rotation
- Adds custom component `SpawnPointMarker` (if available) with tags[] data
- Parents to `_SpawnPoints` container
- Returns spawnPointPath (hierarchy), transactionId, and assigned tags

### Level_SetupLighting

```
Level_SetupLighting(
  preset: "realistic-day" | "realistic-night" | "stylized-day" | "dungeon" | "horror" | "cyberpunk",
  bake?: boolean = true
) → {
  directionalPath: string,
  ambientPath: string,
  probeCount: number,
  transactionId: string,
  bakingStatus: string
}
```

Install directional light, ambient settings, and reflection probes from a named preset. Bake option triggers lightmap generation asynchronously.

**Presets (intensity, color, ambient intensity, probe count):**
- **realistic-day**: directional 1.0 (white), ambient 0.5, 8 probes
- **realistic-night**: directional 0.3 (cool), ambient 0.1, 4 probes
- **stylized-day**: directional 0.8 (warm), ambient 0.6, 2 probes
- **dungeon**: directional 0.4 (warm-amber), ambient 0.05, 6 probes, no indirect
- **horror**: directional 0.2 (red-tint), ambient 0.02, 2 probes, spike filter
- **cyberpunk**: directional 0.9 (cyan), ambient 0.4, 12 probes, neon saturation

**Behavior:**
- Creates Directional Light with preset color/intensity
- Sets RenderSettings.ambientLight and ambientIntensity
- Instantiates ReflectionProbes in grid pattern (8×8 or sparser based on preset)
- If bake=true: Calls `Lightmapping.Bake()`, returns status "in progress" or "complete"
- Returns directionalPath, ambientPath (RenderSettings), probe count, and baking status

### Level_ApplyPreset

```
Level_ApplyPreset(
  name: string,
  origin: Vector3 = [0, 0, 0]
) → {
  operationsCount: number,
  transactionId: string,
  warnings: string[],
  sceneObjects: number
}
```

Macro tool: Apply one of 6 preset level templates to the scene, anchored at origin. Each preset is a CRAFT operation sequence loaded from `presets/level/<name>.json`. Wraps all operations into a single transaction for rollback safety.

**Available presets:** empty-sandbox, dungeon-room, outdoor-clearing, platformer-chunk, racing-track-straight, combat-arena

**Behavior:**
- Loads preset JSON from `Assets/Resources/CRAFT/Presets/Level/<name>.json` (or relative path)
- Deserializes operation array (CreateGameObject, ModifyComponent, etc.)
- Substitutes `{origin}` placeholder in position values
- Executes via Craft_Execute with transactionName = "Apply level preset: <name>"
- Returns operation count, transactionId, warnings (missing prefabs, etc.), and scene object count added

## Pipeline & E11 Dispatch Protocol

When Level Design tools are invoked, the request is dispatched to **E11 unity-level-designer** with the following contract:

**Request Format:**
```json
{
  "tool": "Level_CreateRoom" | "Level_PlaceModular" | "Level_CreateTerrain" | "Level_CarveNavMesh" | "Level_AddSpawnPoint" | "Level_SetupLighting" | "Level_ApplyPreset",
  "preset": "..." (if applicable),
  "parameters": { "..." },
  "origin": [0, 0, 0]
}
```

**Response Format:**
```json
{
  "success": true,
  "result": {
    "path": "..." | "paths": [...],
    "transactionId": "...",
    "metadata": {
      "geometry": {...} | "positions": [...] | "bakingStatus": "..."
    }
  },
  "warnings": [],
  "errors": []
}
```

E11 handles:
1. Preset JSON loading from `presets/level/` subdirectories
2. ProBuilder room construction (cube subdivision, wall carving)
3. Prefab instantiation and collision detection
4. TerrainData sculpting via height curves
5. NavMeshSurface setup and baking orchestration
6. Spawn point and lighting fixture assembly
7. Preset macro expansion into operation sequences
8. Package validation (ProBuilder, Navigation, Terrain Tools)

## Implementation Notes

### Level_CreateRoom

Uses `Craft_Execute` with the following operation sequence:

```json
[
  {
    "type": "CreateGameObject",
    "parameters": {
      "name": "<name>_Geometry",
      "primitiveType": "Cube",
      "position": [0, <height/2>, 0],
      "scale": [<length>, <height>, <width>]
    }
  },
  {
    "type": "ModifyComponent",
    "target": "<name>_Geometry",
    "parameters": {
      "componentType": "ProBuilderMesh",
      "values": {
        "convex": false,
        "smoothGroupsPerFace": true
      }
    }
  },
  { "type": "CreateGameObject", "parameters": { "name": "<name>", "position": [0, 0, 0] } },
  { "type": "ModifyComponent", "target": "<name>", "parameters": { "componentType": "MeshCollider", "values": { "convex": false } } }
]
```

Preset wall thickness and door positions are applied post-creation via ProBuilder API (not CRAFT ops — E11 handles).

### Level_PlaceModular

Uses `Craft_Execute` with a loop-generated CreateGameObject sequence:

```json
{
  "operations": [
    { "type": "CreateGameObject", "parameters": { "name": "_Modular_<layout>" } },
    ... (one CreateGameObject per placed prefab, parent = "_Modular_<layout>") ...
  ],
  "transactionName": "Place <count> modular instances (<layout> layout)"
}
```

Collision detection runs **before** Craft_Execute; if avoidCollision=true and overlaps detected, warnings populate but placement proceeds.

### Level_CarveNavMesh

Creates or finds NavMeshSurface, then invokes baking:

```json
[
  {
    "type": "CreateGameObject",
    "parameters": {
      "name": "NavMesh_Surface",
      "components": ["NavMeshSurface"]
    }
  },
  {
    "type": "ModifyComponent",
    "target": "NavMesh_Surface",
    "parameters": {
      "componentType": "NavMeshSurface",
      "values": {
        "agentTypeID": <agentType enum>,
        "collectObjects": "Children",
        "useGeometry": "PhysicsColliders"
      }
    }
  }
]
```

Baking happens **asynchronously after Craft_Execute** returns; E11 polls `Lightmapping.isRunning` and returns final bake time.

### Level_SetupLighting

Creates fixtures from preset values:

```json
[
  {
    "type": "CreateGameObject",
    "parameters": {
      "name": "Directional Light",
      "components": ["Light"]
    }
  },
  {
    "type": "ModifyComponent",
    "target": "Directional Light",
    "parameters": {
      "componentType": "Light",
      "values": {
        "type": "Directional",
        "intensity": <preset>,
        "color": <preset RGB>
      }
    }
  },
  ... (ReflectionProbe grid generation) ...
]
```

RenderSettings mutations (ambient color, intensity) are applied via E11's editor context, not CRAFT ops.

## Preset System

Six level presets in `presets/level/` directory, each ~40-60 lines JSON:

### empty-sandbox.json

**Purpose:** Fastest level start — flat ground, skybox, directional light, player spawn.

```json
{
  "preset_name": "empty-sandbox",
  "version": "1.0",
  "target": "Scene",
  "requires_packages": [],
  "origin_offset": [0, 0, 0],
  "operations": [
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Ground",
        "primitiveType": "Plane",
        "scale": [50, 1, 50]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Directional Light",
        "components": ["Light"],
        "position": [10, 10, 10],
        "rotation": [45, 45, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "PlayerSpawn",
        "position": [0, 1, 0],
        "tags": ["player_start"]
      }
    }
  ],
  "_note": "50×50m flat plane with overhead sun and player spawn at origin. Use for quick prototyping."
}
```

### dungeon-room.json

**Purpose:** Enclosed space with torches and baked lighting — ready for gameplay.

```json
{
  "preset_name": "dungeon-room",
  "version": "1.0",
  "target": "Scene",
  "requires_packages": ["com.unity.probuilder"],
  "origin_offset": [0, 0, 0],
  "operations": [
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "DungeonRoom",
        "position": [0, 0, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Floor",
        "primitiveType": "Plane",
        "parent": "DungeonRoom",
        "scale": [10, 1, 4],
        "position": [0, 0, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Ceiling",
        "primitiveType": "Plane",
        "parent": "DungeonRoom",
        "scale": [10, 1, 4],
        "position": [0, 10, 0],
        "rotation": [180, 0, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "WallNorth",
        "primitiveType": "Cube",
        "parent": "DungeonRoom",
        "scale": [10, 10, 0.3],
        "position": [0, 5, -2]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "WallSouth",
        "primitiveType": "Cube",
        "parent": "DungeonRoom",
        "scale": [10, 10, 0.3],
        "position": [0, 5, 2]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "WallEast",
        "primitiveType": "Cube",
        "parent": "DungeonRoom",
        "scale": [0.3, 10, 4],
        "position": [5, 5, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "WallWest",
        "primitiveType": "Cube",
        "parent": "DungeonRoom",
        "scale": [0.3, 10, 4],
        "position": [-5, 5, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "TorchSpawn1",
        "position": [4, 7, -1.8],
        "tags": ["torch_spawn"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "TorchSpawn2",
        "position": [-4, 7, -1.8],
        "tags": ["torch_spawn"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Directional Light",
        "components": ["Light"],
        "position": [2, 8, 0],
        "rotation": [45, 45, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "PlayerSpawn",
        "position": [0, 1, 0],
        "tags": ["player_start"]
      }
    }
  ],
  "_note": "10×4×10m dungeon room, 4 walls + ceiling + floor. Two torch spawn markers for torches. Baked lighting ready."
}
```

### outdoor-clearing.json

**Purpose:** Terrain sandbox with rolling hills, trees, river path.

```json
{
  "preset_name": "outdoor-clearing",
  "version": "1.0",
  "target": "Scene",
  "requires_packages": ["com.unity.terrain-tools"],
  "origin_offset": [0, 0, 0],
  "operations": [
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Terrain",
        "components": ["Terrain", "TerrainCollider"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "TreeContainer",
        "position": [0, 0, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "RiverPath",
        "position": [0, 0.5, 0],
        "tags": ["water_feature"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "PlayerSpawn",
        "position": [30, 3, 30],
        "tags": ["player_start"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Directional Light",
        "components": ["Light"],
        "position": [50, 20, 50],
        "rotation": [45, 120, 0]
      }
    }
  ],
  "_note": "100×100m terrain, rolling hills (Perlin noise), tree clusters, river spline center. Requires Tree prefab in scene."
}
```

### platformer-chunk.json

**Purpose:** Three stacked platforms for vertical gameplay — checkpoint, kill zone below.

```json
{
  "preset_name": "platformer-chunk",
  "version": "1.0",
  "target": "Scene",
  "requires_packages": [],
  "origin_offset": [0, 0, 0],
  "operations": [
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Platform0",
        "primitiveType": "Cube",
        "scale": [10, 0.5, 10],
        "position": [0, 0, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Platform1",
        "primitiveType": "Cube",
        "scale": [8, 0.5, 8],
        "position": [2, 2, 2]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Platform2",
        "primitiveType": "Cube",
        "scale": [6, 0.5, 6],
        "position": [4, 4, 4]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Checkpoint",
        "position": [4, 4.5, 4],
        "tags": ["checkpoint"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "KillZone",
        "primitiveType": "Cube",
        "scale": [50, 1, 50],
        "position": [0, -5, 0],
        "components": ["BoxCollider"],
        "tags": ["kill_zone"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Directional Light",
        "components": ["Light"],
        "position": [10, 10, 10],
        "rotation": [45, 45, 0]
      }
    }
  ],
  "_note": "3 platforms at y=0/2/4, scaled down, diagonal stagger. Checkpoint at top. Kill zone below."
}
```

### racing-track-straight.json

**Purpose:** 100m straight track with walls, start/finish markers, camera anchor.

```json
{
  "preset_name": "racing-track-straight",
  "version": "1.0",
  "target": "Scene",
  "requires_packages": [],
  "origin_offset": [0, 0, 0],
  "operations": [
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Track",
        "primitiveType": "Cube",
        "scale": [10, 0.2, 100],
        "position": [0, 0, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "WallLeft",
        "primitiveType": "Cube",
        "scale": [0.5, 2, 100],
        "position": [-5.5, 1, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "WallRight",
        "primitiveType": "Cube",
        "scale": [0.5, 2, 100],
        "position": [5.5, 1, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "StartLine",
        "position": [0, 0.3, -50],
        "tags": ["race_start"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "FinishLine",
        "position": [0, 0.3, 50],
        "tags": ["race_finish"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "CameraAnchor",
        "position": [0, 5, 0],
        "tags": ["camera_follow"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Directional Light",
        "components": ["Light"],
        "position": [20, 15, 0],
        "rotation": [45, 0, 0]
      }
    }
  ],
  "_note": "100m straight track (10m wide, 0.2m thick), left/right walls. Start/finish markers at ±50z."
}
```

### combat-arena.json

**Purpose:** 20×20m open fighting space — 4 cover blocks, 4 enemy spawns, center boss spawn.

```json
{
  "preset_name": "combat-arena",
  "version": "1.0",
  "target": "Scene",
  "requires_packages": [],
  "origin_offset": [0, 0, 0],
  "operations": [
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Floor",
        "primitiveType": "Plane",
        "scale": [10, 1, 10],
        "position": [0, 0, 0]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "CoverBlock1",
        "primitiveType": "Cube",
        "scale": [2, 2, 2],
        "position": [7, 1, 7]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "CoverBlock2",
        "primitiveType": "Cube",
        "scale": [2, 2, 2],
        "position": [-7, 1, 7]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "CoverBlock3",
        "primitiveType": "Cube",
        "scale": [2, 2, 2],
        "position": [7, 1, -7]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "CoverBlock4",
        "primitiveType": "Cube",
        "scale": [2, 2, 2],
        "position": [-7, 1, -7]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "EnemySpawn1",
        "position": [10, 1, 10],
        "tags": ["enemy_melee"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "EnemySpawn2",
        "position": [-10, 1, 10],
        "tags": ["enemy_ranged"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "EnemySpawn3",
        "position": [10, 1, -10],
        "tags": ["enemy_melee"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "EnemySpawn4",
        "position": [-10, 1, -10],
        "tags": ["enemy_ranged"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "BossSpawn",
        "position": [0, 1, 0],
        "tags": ["boss_spawn"]
      }
    },
    {
      "type": "CreateGameObject",
      "parameters": {
        "name": "Directional Light",
        "components": ["Light"],
        "position": [5, 10, 5],
        "rotation": [45, 45, 0]
      }
    }
  ],
  "_note": "20×20m arena, 4 cover blocks at corners, 4 enemy spawns (alternating melee/ranged), boss at center."
}
```

## Worked Examples

### Scenario 1: Quick Sandbox Setup

**User:** "Build a flat 50×50 sandbox for prototyping"

```
Level_ApplyPreset("empty-sandbox", origin=[0,0,0])
```

**Result:**
- 50×50m ground plane created
- Directional light positioned overhead
- Player spawn marker at origin
- Transaction ID returned for rollback
- Time to completion: <1s

### Scenario 2: Dungeon Room with Lighting

**User:** "Create a 10×4×10 dungeon room with torches and baked lighting"

```
Level_CreateRoom("MainChamber", [10, 10, 4], wallThickness=0.3, floor=true, ceiling=true)
Level_SetupLighting("dungeon", bake=true)
```

**Expected outcome:**
- MainChamber_Geometry created with ProBuilder cube, 4 walls + ceiling + floor
- Dungeon preset lighting: warm amber directional at 0.4 intensity, low ambient (0.05)
- 6 reflection probes placed in grid pattern
- Lightmap baking initiated asynchronously
- Torch spawn markers ready for runtime population

### Scenario 3: Combat Arena for Playtest

**User:** "Set up a combat arena with 4 cover blocks, enemy spawns, and boss center"

```
Level_ApplyPreset("combat-arena", origin=[0,0,0])
Level_CarveNavMesh("SampleScene", agentType="humanoid")
Level_AddSpawnPoint("Player_Start", [0, 1, 0], [0,0,0], tags=["player_start"])
```

**Expected outcome:**
- Combat arena geometry (floor, 4 cover blocks, 4 enemy + 1 boss spawn points) instantiated
- NavMesh baked for humanoid agents
- Additional player spawn point added at center
- Scene ready for enemy AI scripting + playtesting
- All operations in single transaction for safety rollback

## Integration Notes

### Package Dependencies

- **ProBuilder:** `Level_CreateRoom` requires `com.unity.probuilder` (UPM)
- **Navigation:** `Level_CarveNavMesh` requires `com.unity.ai.navigation` (UPM)
- **Terrain Tools:** `Level_CreateTerrain` with custom sculpting requires `com.unity.terrain-tools` (optional, defaults to Perlin if missing)

If a required package is missing, E11 detects via `Assets_InstallUPM("com.unity.probuilder")` CRAFT operation and suggests install.

### Material & Asset Paths

- **ProBuilder materials:** defaults to `Packages/com.unity.probuilder/Assets/Materials/Default*`
- **Terrain layers:** expects `.terrainlayer` files at `Assets/Terrains/Materials/<preset>.terrainlayer`
- **Tree prefabs:** looks for prefabs tagged `tree_prefab` or named `Tree_*` in scene/Assets
- **Spawn point markers:** uses simple Transform if `SpawnPointMarker` component unavailable (graceful fallback)

### Lighting & Baking

- Real-time lighting: directional + ambient only, fast, no shadow maps
- Baked lighting: adds reflection probes, triggers `Lightmapping.Bake()` asynchronously
- Baking status checked via `Lightmapping.isRunning` polling; returns final time

### Scene Organization

All generated GameObjects parented to containers:
- `_Rooms` — for Level_CreateRoom results
- `_Modular_<layout>` — for Level_PlaceModular prefab instances
- `_Terrain` — for terrain GameObject + TerrainCollider
- `_Lighting` — for lights + probes
- `_SpawnPoints` — for spawn point markers

## Limitations

1. **ProBuilder API requires editor context** — Level_CreateRoom cannot run in play mode; CRAFT validates and reports if attempted
2. **Preset paths are relative to project root** — `presets/level/<name>.json` must exist; missing files raise validation error
3. **NavMesh baking is slow for large scenes** — may block for >30s on complex geometry; E11 returns "baking in progress" status mid-transaction
4. **Terrain size limited to 4096×4096 heightmap** — sculpting beyond this resolution not supported
5. **Material fallback to default** — if custom preset materials not found, ProBuilder default material applied
6. **Tree placement requires Tree prefab** — if not present, treeDensity ignored with warning

## Verification Checklist

After executing Level Design operations, verify:

1. **Room Creation:**
   - Room GameObject exists at specified path with ProBuilder Mesh component
   - Wall count matches expected (4 + ceiling + floor if enabled)
   - Door apertures carved (if doorPositions provided)
   - Collider updated for game physics

2. **Modular Placement:**
   - All prefab instances parented to `_Modular_<layout>` container
   - Placed count matches request (or less if collision avoidance active)
   - Positions array populated with final [x,y,z] values
   - Warnings reported for any overlaps or missing prefabs

3. **Terrain:**
   - TerrainData asset created and saved to Assets/
   - Height variation matches preset curve (flat/rolling/mountainous)
   - Texture layers composited from preset
   - Trees visible if treeDensity > 0

4. **NavMesh:**
   - NavMesh asset saved to `Assets/NavMesh/<sceneName>_<agentType>.asset`
   - Bake time < 60s (warn if longer)
   - Walkable area reported in m²
   - Agent settings match requested type

5. **Spawn Points:**
   - Transform at correct position/rotation
   - Tags applied (visible in inspector Tags dropdown)
   - Parented to `_SpawnPoints` container

6. **Lighting:**
   - Directional light visible with correct color/intensity
   - Ambient settings applied (RenderSettings.ambientLight)
   - Reflection probes placed in grid pattern
   - Baking status reported (in progress or complete)

7. **Preset Application:**
   - All operations executed in single transaction
   - Scene object count increased by expected amount
   - Warnings for missing dependencies (packages, prefabs, materials)
   - transactionId valid for rollback

## Common Workflows

**Complete level from preset → lights → NavMesh:**
```
Level_ApplyPreset("dungeon-room", origin=[0,0,0])
Level_SetupLighting("dungeon", bake=true)
Level_CarveNavMesh("SampleScene", agentType="humanoid")
```

**Build a modular arena:**
```
Level_CreateRoom("Arena", [20, 4, 20], floor=true, ceiling=false)
Level_PlaceModular(["Assets/Prefabs/Cover_Block"], layout="cluster", count=4, spacing=5)
Level_AddSpawnPoint("Player_Start", [0, 1, 0], [0,0,0], tags=["player_start"])
Level_CarveNavMesh("SampleScene", agentType="humanoid")
```

**Outdoor level with terrain + trees:**
```
Level_CreateTerrain([100, 15, 100], heightmap="rolling", texturePreset="grass-dirt", treeDensity=0.3)
Level_SetupLighting("realistic-day", bake=true)
Level_CarveNavMesh("SampleScene", agentType="humanoid")
```

**Platformer challenge:**
```
Level_ApplyPreset("platformer-chunk", origin=[0,0,0])
Level_PlaceModular(["Assets/Prefabs/Spike_Trap"], layout="grid", count=5, spacing=3, seed=42)
Level_SetupLighting("stylized-day", bake=false)
```

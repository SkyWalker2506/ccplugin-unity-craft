# Combat System Tool Family

## Purpose

Automate combat mechanics setup in Unity via B19 agent dispatch + CRAFT MCP. This tool family handles melee, ranged, and skill-based combat components, health systems, and special abilities — generating production-ready C# scripts and wiring them to GameObjects through Craft_Execute operations.

The Combat System tool manages:
- **CombatComponent** — attack triggers, hitbox detection (Physics overlap calls), damage application, optional knockback, and cooldown timers
- **HealthSystem** — max HP tracking, damage intake, death events, and configurable death behaviours (disable, destroy, ragdoll)
- **SkillComponent** — special abilities (dash, projectile, AoE, and custom) with per-skill cooldowns and configurable parameters
- **VFX chaining** — automatic `Animation_Apply(onHitVFX)` integration when a hit preset is specified

All C# code generation is dispatched to **B19 unity-developer** (gpt-5.4). CRAFT operations handle scene mutation. Claude never outputs manual instructions to the user.

## Tool Overview

| Tool | Purpose | Dispatch |
|------|---------|----------|
| `Combat_Setup` | Configure a combat component (melee / ranged / skill) on any GameObject | B19 + Craft_Execute |
| `Combat_SetupHP` | Add a health system with configurable death behaviour and event | B19 + Craft_Execute |
| `Combat_SetupSkill` | Add a special skill component (dash / projectile / AoE / custom) | B19 + Craft_Execute |

## Tool Signatures

### Combat_Setup

```
Combat_Setup(
  gameObject: string,
  type: "melee" | "ranged" | "skill",
  damage: number,
  range: number,
  cooldown: number,
  hitboxShape: "capsule" | "sphere" | "box",
  targetLayer: string,
  pipeline: "2D" | "3D",
  knockback?: { x: number, y: number, z?: number },
  onHitVFX?: string
) → {
  gameObject: string,
  componentPath: string,
  hitboxChildPath: string,
  transactionId: string,
  vfxChained: boolean
}
```

Configure a complete combat component on a target GameObject. Generates `CombatComponent.cs` via B19 dispatch, then attaches it to the GO through Craft_Execute.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gameObject` | string | — | Target GameObject name in the scene hierarchy |
| `type` | "melee" \| "ranged" \| "skill" | — | Combat archetype — determines hitbox trigger logic and attack range semantics |
| `damage` | number | — | Damage value applied to target HealthSystem per hit |
| `range` | number | — | Hitbox detection radius/extent in Unity world units |
| `cooldown` | number | — | Seconds between attacks; enforced by CombatComponent timer |
| `hitboxShape` | "capsule" \| "sphere" \| "box" | — | Physics overlap method — Capsule for elongated volumes, Sphere for radial, Box for rectangular/directional |
| `targetLayer` | string | — | Unity layer name used in the LayerMask passed to the Physics overlap call |
| `pipeline` | "2D" \| "3D" | — | Physics pipeline — "2D" uses `Physics2D` overlap methods + `Rigidbody2D`; "3D" uses `Physics` + `Rigidbody` |
| `knockback?` | { x, y, z? } | none | Optional force vector applied via `AddForce` on successful hit. `z` is used only when `pipeline` is "3D". |
| `onHitVFX?` | string | none | Optional preset name from `presets/animation/`. If provided, `Animation_Apply` is chained automatically after each hit. |

**Physics API mapping by `pipeline` and `hitboxShape`:**

| pipeline | hitboxShape | API used |
|----------|------------|----------|
| 2D | sphere | `Physics2D.OverlapCircleAll` |
| 2D | capsule | `Physics2D.OverlapCapsuleAll` |
| 2D | box | `Physics2D.OverlapBoxAll` |
| 3D | sphere | `Physics.OverlapSphere` |
| 3D | capsule | `Physics.OverlapCapsule` |
| 3D | box | `Physics.OverlapBox` |

**Pipeline:**

1. **B19 dispatch** — B19 (unity-developer, gpt-5.4) generates `CombatComponent.cs`:
   - `Attack()` method: cooldown check, Physics overlap call using `hitboxShape` + `targetLayer`, damage application to `HealthSystem.TakeDamage()`, optional knockback `AddForce`, cooldown reset
   - Physics API selected based on `pipeline` parameter
   - Public serialized fields: `damage`, `range`, `cooldown`, `attackLayer`, `knockback` (optional)
2. **Craft_Execute** — CreateGameObject child named `{gameObject}_Hitbox` with Transform at attack origin; attach CombatComponent to parent GO via AddComponent
3. **VFX chain** (if `onHitVFX` is set) — `Animation_ApplyPreset(onHitVFX, targetCamera)` is called automatically; no user action required

**Example invocations:**

```
// 3D melee (e.g. third-person action, RPG)
Combat_Setup(
  gameObject: "PlayerCharacter",
  type: "melee",
  damage: 25,
  range: 1.5,
  cooldown: 0.6,
  hitboxShape: "capsule",
  targetLayer: "Enemy",
  pipeline: "3D",
  knockback: { x: 0, y: 1.0, z: 3.0 },
  onHitVFX: "camera-shake-hit"
)

// 2D ranged (e.g. platformer, top-down shooter)
Combat_Setup(
  gameObject: "Turret",
  type: "ranged",
  damage: 15,
  range: 8.0,
  cooldown: 1.0,
  hitboxShape: "sphere",
  targetLayer: "Player",
  pipeline: "2D"
)
```

---

### Combat_SetupHP

```
Combat_SetupHP(
  gameObject: string,
  maxHP: number,
  onDeath: "disable" | "destroy" | "ragdoll",
  deathEvent: string,
  pipeline?: "2D" | "3D"
) → {
  gameObject: string,
  componentPath: string,
  transactionId: string,
  maxHP: number,
  deathBehaviour: string
}
```

Add a health system to a GameObject. Generates `HealthSystem.cs` via B19 dispatch, then attaches it via Craft_Execute.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gameObject` | string | — | Target GameObject name |
| `maxHP` | number | — | Maximum hit points. Current HP initialised to `maxHP` on Awake. |
| `onDeath` | "disable" \| "destroy" \| "ragdoll" | — | Behaviour executed when HP reaches 0. `disable`: `gameObject.SetActive(false)`. `destroy`: `Destroy(gameObject)`. `ragdoll`: disables Animator + enables all Rigidbody components (expects pre-configured ragdoll hierarchy). |
| `deathEvent` | string | — | C# event name broadcast on death (e.g. `"OnActorDied"`). Other scripts subscribe via `HealthSystem.OnActorDied += handler`. |
| `pipeline?` | "2D" \| "3D" | "3D" | Determines Rigidbody type used in ragdoll handling (`Rigidbody2D` vs `Rigidbody`). Only relevant for `onDeath: "ragdoll"`. |

**Pipeline:**

1. **B19 dispatch** — B19 generates `HealthSystem.cs`:
   - `public float MaxHP`, `public float CurrentHP`
   - `public void TakeDamage(float amount)` — decrements CurrentHP, clamps to 0, calls `Die()` if zero
   - `private void Die()` — executes `onDeath` behaviour + broadcasts `deathEvent` C# event
   - `public event Action deathEvent` — subscribable by CombatComponent, game managers, UI, audio systems
2. **Craft_Execute** — `ModifyComponent` to attach `HealthSystem` to the target GO; sets `MaxHP` field

**Example invocations:**

```
// Generic enemy
Combat_SetupHP(
  gameObject: "EnemyUnit",
  maxHP: 80,
  onDeath: "destroy",
  deathEvent: "OnEnemyDied"
)

// Player with disable-on-death (respawn handled elsewhere)
Combat_SetupHP(
  gameObject: "PlayerCharacter",
  maxHP: 150,
  onDeath: "disable",
  deathEvent: "OnPlayerDied",
  pipeline: "3D"
)

// Boss with ragdoll death
Combat_SetupHP(
  gameObject: "BossUnit",
  maxHP: 500,
  onDeath: "ragdoll",
  deathEvent: "OnBossDied",
  pipeline: "3D"
)
```

---

### Combat_SetupSkill

```
Combat_SetupSkill(
  gameObject: string,
  skillType: "dash" | "projectile" | "aoe" | "custom",
  damage: number,
  cooldown: number,
  pipeline: "2D" | "3D",
  targetLayer?: string,
  dashForce?: number,
  dashDirection?: "facing" | "input",
  projectilePrefab?: string,
  projectileSpeed?: number,
  aoeRadius?: number,
  customScriptHint?: string
) → {
  gameObject: string,
  componentPath: string,
  transactionId: string,
  skillType: string,
  cooldown: number
}
```

Add a special skill component to a GameObject. Generates `SkillComponent.cs` via B19 dispatch, then attaches it via Craft_Execute.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gameObject` | string | — | Target GameObject name |
| `skillType` | "dash" \| "projectile" \| "aoe" \| "custom" | — | Skill archetype — determines generated logic |
| `damage` | number | — | Damage dealt by the skill on hit. Set to 0 for non-damaging skills (e.g. pure mobility dash). |
| `cooldown` | number | — | Seconds between skill uses |
| `pipeline` | "2D" \| "3D" | — | Physics pipeline; determines Rigidbody type and overlap API used |
| `targetLayer?` | string | none | Layer mask for overlap detection (required for `aoe`; optional for `projectile` if projectile prefab handles collision itself) |
| `dashForce?` | number | none | Required for `dash`: force magnitude applied to Rigidbody in the dash direction |
| `dashDirection?` | "facing" \| "input" | "facing" | For `dash`: "facing" uses the GO's forward/right vector; "input" uses the current movement input direction |
| `projectilePrefab?` | string | none | Required for `projectile`: prefab path used in `Instantiate()`. Prefab must have a Collider + Rigidbody. |
| `projectileSpeed?` | number | none | Optional: sets Rigidbody velocity on the spawned projectile. If omitted, the prefab's own script handles movement. |
| `aoeRadius?` | number | none | Required for `aoe`: radius in world units for the overlap blast |
| `customScriptHint?` | string | none | For `custom`: natural language description of the skill behaviour dispatched to B19 for code generation |

**Skill type rules:**

- `dash` — requires `dashForce`. Applies `AddForce(direction * dashForce, ForceMode.Impulse)` (3D) or `ForceMode2D.Impulse` (2D). Direction determined by `dashDirection`.
- `projectile` — requires `projectilePrefab`. Instantiates prefab at GO position facing movement direction. If `projectileSpeed` is provided, sets Rigidbody velocity on spawn.
- `aoe` — requires `aoeRadius` and `targetLayer`. Calls the appropriate `OverlapSphere`/`OverlapCircle` at GO position, applies `damage` to all `HealthSystem` components found.
- `custom` — requires `customScriptHint`. B19 generates a `UseSkill()` method based on the hint. Use for game-specific abilities (e.g. time slow, shield, tether).

**Pipeline:**

1. **B19 dispatch** — B19 generates `SkillComponent.cs`:
   - `public void UseSkill()` — cooldown gate, skill-type branch
   - `private IEnumerator CooldownRoutine()` — coroutine to reset `canUse` flag after `cooldown` seconds
   - Physics API, Rigidbody type, and ForceMode selected based on `pipeline`
   - Skill-specific parameters set as public serialized fields
2. **Craft_Execute** — AddComponent `SkillComponent` to target GO; sets all skill fields via ModifyComponent

**Example invocations:**

```
// Mobility dash (any genre — platformer, shooter, RPG)
Combat_SetupSkill(
  gameObject: "PlayerCharacter",
  skillType: "dash",
  damage: 0,
  cooldown: 2.0,
  pipeline: "3D",
  dashForce: 18.0,
  dashDirection: "input"
)

// Projectile attack (2D top-down, sidescroller, etc.)
Combat_SetupSkill(
  gameObject: "RangedUnit",
  skillType: "projectile",
  damage: 40,
  cooldown: 1.5,
  pipeline: "2D",
  projectilePrefab: "Assets/Prefabs/Projectile.prefab",
  projectileSpeed: 12.0
)

// AoE blast (any genre — boss, artillery, mage)
Combat_SetupSkill(
  gameObject: "HeavyUnit",
  skillType: "aoe",
  damage: 60,
  cooldown: 5.0,
  pipeline: "3D",
  aoeRadius: 4.0,
  targetLayer: "Enemy"
)

// Custom skill (game-specific logic)
Combat_SetupSkill(
  gameObject: "SupportUnit",
  skillType: "custom",
  damage: 0,
  cooldown: 10.0,
  pipeline: "3D",
  customScriptHint: "Emit a shield that absorbs the next 50 damage received, then expires after 5 seconds"
)
```

---

## B19 Dispatch Protocol

All C# code generation dispatches to **B19 unity-developer** (gpt-5.4).

**Request Format:**
```json
{
  "tool": "Combat_Setup" | "Combat_SetupHP" | "Combat_SetupSkill",
  "parameters": { "..." },
  "craft_context": {
    "targetGameObject": "...",
    "pipeline": "2D" | "3D"
  }
}
```

**Response Format:**
```json
{
  "success": true,
  "result": {
    "scriptPath": "Assets/Scripts/Combat/<ComponentName>.cs",
    "componentName": "...",
    "transactionId": "...",
    "craftOps": [ "..." ]
  },
  "warnings": [],
  "errors": []
}
```

B19 handles:
1. C# script generation for `CombatComponent`, `HealthSystem`, and `SkillComponent` following Unity MonoBehaviour conventions
2. Physics API selection (2D vs 3D) based on `pipeline` parameter in `craft_context`
3. Layer mask construction from string parameters (`LayerMask.GetMask(targetLayer)`)
4. Cooldown coroutine scaffolding and edge-case guards (null checks on HealthSystem, IsAlive flag)
5. C# event declaration and invocation for death and hit broadcast
6. Prefab path validation for projectile instantiation
7. Custom skill logic generation from `customScriptHint`

After B19 returns the script, CRAFT operations execute via `Craft_Execute`:
- `CreateAsset` — writes the `.cs` file to `Assets/Scripts/Combat/`
- `AddComponent` — attaches the component to the target GO
- `ModifyComponent` — sets serialized field values
- `CreateGameObject` — spawns hitbox child GO for `Combat_Setup`

## Integration with Animation Family

When `Combat_Setup` is called with `onHitVFX`, the pipeline automatically chains:

```
Animation_ApplyPreset(onHitVFX, targetCamera)
```

The `targetCamera` is resolved from the active Cinemachine Virtual Camera in the scene at the time of the call. The chain is injected by the orchestrator — no separate call is needed from the user.

Cross-family workflow example:
```
Combat_Setup(
  gameObject: "PlayerCharacter",
  type: "melee",
  damage: 25,
  range: 1.5,
  cooldown: 0.6,
  hitboxShape: "capsule",
  targetLayer: "Enemy",
  pipeline: "3D",
  onHitVFX: "camera-shake-hit"
)
// → CombatComponent.cs generated + hitbox child created
// → Animation_ApplyPreset("camera-shake-hit", <active VCam>) auto-chained
```

## Forbidden

- Never output "write this script" or "add this component manually" to the user
- Never output raw C# code blocks for the user to copy-paste
- Never ask the user to configure a Physics Layer in Project Settings manually — use `targetLayer` and instruct B19 to use `LayerMask.GetMask()`
- All operations must go through CRAFT (Craft_Execute) or B19 dispatch

## Limitations

1. **2D vs 3D physics:** The `pipeline` parameter is required for all tools that involve physics. There is no default pipeline — the caller must specify "2D" or "3D" based on the project.

2. **Ragdoll death:** `onDeath: "ragdoll"` requires a pre-existing ragdoll hierarchy on the GO (Rigidbody components on bones set to `isKinematic=true` at runtime). The generated `HealthSystem.cs` toggles kinematics but does not build the ragdoll rig. Set up the ragdoll hierarchy separately before calling `Combat_SetupHP`.

3. **Projectile prefab ownership:** `Combat_SetupSkill` with `skillType: "projectile"` requires the prefab to already exist at `projectilePrefab` path. The tool does not create the prefab. Use `Craft_Execute CreateGameObject` or a dedicated prefab-build workflow first.

4. **Network / multiplayer:** Generated scripts are single-player by default. For networked games (Netcode for GameObjects, Mirror, Photon), CombatComponent and HealthSystem need RPC wrappers. Dispatch to B19 with a `multiplayer: true` flag in `craft_context` to request network-compatible variants.

5. **Animation state coupling:** `CombatComponent.cs` triggers an attack animation via `animator.SetTrigger("AttackTrigger")` if an Animator is present on the GO. This requires an AnimatorController with an `AttackTrigger` parameter. If no Animator is found, the trigger call is skipped gracefully. Use `Animation_ApplyPreset` before `Combat_Setup` to ensure the state machine is configured.

6. **Custom skill complexity:** `customScriptHint` should describe a single, well-scoped ability. Highly complex or multi-phase abilities may need to be split into separate `SkillComponent` instances or require follow-up B19 dispatch with more specific instructions.

## Verification Checklist

After executing Combat System operations, verify:

1. **CombatComponent (Combat_Setup)**
   - `CombatComponent.cs` exists at `Assets/Scripts/Combat/CombatComponent.cs`
   - Target GO has CombatComponent in the Inspector
   - `{gameObject}_Hitbox` child GO is present in the hierarchy
   - `damage`, `range`, `cooldown`, `attackLayer` fields are set correctly in Inspector
   - Physics overlap gizmos visible in Scene view (if debug gizmos enabled)
   - If `onHitVFX` was set: animation preset is chained to the active camera

2. **HealthSystem (Combat_SetupHP)**
   - `HealthSystem.cs` exists at `Assets/Scripts/Combat/HealthSystem.cs`
   - Target GO has HealthSystem component; `MaxHP` matches specified value
   - In Play mode: `TakeDamage()` decrements `CurrentHP` correctly
   - At 0 HP: `onDeath` behaviour executes (GO disabled / destroyed / ragdolled)
   - `deathEvent` fires; subscriber scripts receive the callback

3. **SkillComponent (Combat_SetupSkill)**
   - `SkillComponent.cs` exists at `Assets/Scripts/Combat/SkillComponent.cs`
   - Target GO has SkillComponent; skill-type fields set correctly
   - In Play mode: `UseSkill()` executes correct branch (dash force / projectile spawn / AoE overlap / custom)
   - Cooldown prevents re-use within specified seconds
   - Projectile type: prefab spawns at GO position and travels in the expected direction
   - AoE type: all HealthSystems within `aoeRadius` on `targetLayer` receive `damage`

4. **No console errors** related to missing components, null Rigidbody references, or invalid layer names

## Common Workflows

### Generic Player Setup (any genre)

```
// 1. Health system
Combat_SetupHP(
  gameObject: "PlayerCharacter",
  maxHP: 100,
  onDeath: "disable",
  deathEvent: "OnPlayerDied",
  pipeline: "3D"
)

// 2. Primary attack
Combat_Setup(
  gameObject: "PlayerCharacter",
  type: "melee",
  damage: 20,
  range: 1.2,
  cooldown: 0.5,
  hitboxShape: "capsule",
  targetLayer: "Enemy",
  pipeline: "3D",
  knockback: { x: 0, y: 0.5, z: 2.5 },
  onHitVFX: "camera-shake-hit"
)

// 3. Mobility skill
Combat_SetupSkill(
  gameObject: "PlayerCharacter",
  skillType: "dash",
  damage: 0,
  cooldown: 2.0,
  pipeline: "3D",
  dashForce: 16.0,
  dashDirection: "input"
)
```

### Generic Enemy Unit

```
Combat_SetupHP(
  gameObject: "EnemyUnit",
  maxHP: 60,
  onDeath: "destroy",
  deathEvent: "OnEnemyDied"
)

Combat_Setup(
  gameObject: "EnemyUnit",
  type: "melee",
  damage: 10,
  range: 0.8,
  cooldown: 1.2,
  hitboxShape: "sphere",
  targetLayer: "Player",
  pipeline: "3D"
)
```

### Boss with AoE Skill

```
Combat_SetupHP(
  gameObject: "BossUnit",
  maxHP: 500,
  onDeath: "ragdoll",
  deathEvent: "OnBossDied",
  pipeline: "3D"
)

Combat_Setup(
  gameObject: "BossUnit",
  type: "melee",
  damage: 35,
  range: 2.0,
  cooldown: 1.0,
  hitboxShape: "box",
  targetLayer: "Player",
  pipeline: "3D",
  knockback: { x: 0, y: 1.5, z: 5.0 }
)

Combat_SetupSkill(
  gameObject: "BossUnit",
  skillType: "aoe",
  damage: 80,
  cooldown: 8.0,
  pipeline: "3D",
  aoeRadius: 5.0,
  targetLayer: "Player"
)
```

### 2D Ranged Shooter Setup

```
Combat_SetupHP(
  gameObject: "ShooterPlayer",
  maxHP: 80,
  onDeath: "disable",
  deathEvent: "OnPlayerDied",
  pipeline: "2D"
)

Combat_SetupSkill(
  gameObject: "ShooterPlayer",
  skillType: "projectile",
  damage: 30,
  cooldown: 0.3,
  pipeline: "2D",
  projectilePrefab: "Assets/Prefabs/Bullet.prefab",
  projectileSpeed: 20.0,
  targetLayer: "Enemy"
)
```

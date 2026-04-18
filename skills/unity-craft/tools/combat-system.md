# Combat System Tool Family

## Purpose

Automate combat mechanics setup in Unity via B19 agent dispatch + CRAFT MCP. This tool family handles melee, ranged, and skill-based combat components, health systems, and special abilities — generating production-ready C# scripts and wiring them to GameObjects through Craft_Execute operations.

The Combat System tool manages:
- **CombatComponent** — attack triggers, hitbox detection (Physics.OverlapSphere/Box/Capsule), damage application, knockback AddForce, and cooldown timers
- **HealthSystem** — max HP tracking, damage intake, death events, and configurable death behaviours (disable, destroy, ragdoll)
- **PlayerSkill** — dash, projectile, and AoE special abilities with per-skill cooldowns and force/radius configuration
- **VFX chaining** — automatic Animation_Apply(onHitVFX) integration when a hit preset is specified

All C# code generation is dispatched to **B19 unity-developer** (gpt-5.4). CRAFT operations handle scene mutation. Claude never outputs manual instructions to the user.

## Tool Overview

| Tool | Purpose | Dispatch |
|------|---------|----------|
| `Combat_Setup` | Configure complete combat component (melee/ranged/skill) | B19 + Craft_Execute |
| `Combat_SetupHP` | Add health system with death event | B19 + Craft_Execute |
| `Combat_SetupSkill` | Add special skill (dash / projectile / AoE) | B19 + Craft_Execute |

## Tool Signatures

### Combat_Setup

```
Combat_Setup(
  gameObject: string,
  type: "melee" | "ranged" | "skill",
  damage: number,
  range: number,
  knockbackForce: { x: number, y: number },
  cooldown: number,
  hitboxShape: "capsule" | "sphere" | "box",
  layer: string,
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

| Parameter | Type | Description |
|-----------|------|-------------|
| `gameObject` | string | Target GameObject name in the scene hierarchy |
| `type` | "melee" \| "ranged" \| "skill" | Combat archetype — determines hitbox trigger logic and attack range semantics |
| `damage` | number | Damage value applied to target HealthSystem per hit |
| `range` | number | Hitbox detection radius in Unity world units (used in Physics.OverlapSphere/Box/Capsule) |
| `knockbackForce` | { x, y } | Vector2 applied via `Rigidbody2D.AddForce` on successful hit |
| `cooldown` | number | Seconds between attacks; enforced by CombatComponent timer |
| `hitboxShape` | "capsule" \| "sphere" \| "box" | Physics overlap method — Capsule for character-shaped, Sphere for radial, Box for directional |
| `layer` | string | Unity layer name used in the LayerMask passed to the Physics overlap call |
| `onHitVFX?` | string | Optional preset name from `presets/animation/` (e.g. `"camera-shake-hit"`). If provided, Animation_Apply is chained automatically after each hit. |

**Pipeline:**

1. **B19 dispatch** — B19 (unity-developer, gpt-5.4) generates `CombatComponent.cs`:
   - `Attack()` method: cooldown check, Physics.Overlap call using `hitboxShape` + `layer`, damage application to `HealthSystem.TakeDamage()`, knockback `AddForce`, cooldown reset
   - `hitboxShape` maps to: `Physics2D.OverlapCapsuleAll` / `Physics2D.OverlapCircleAll` / `Physics2D.OverlapBoxAll`
   - Public fields: `damage`, `range`, `knockbackForce`, `cooldown`, `attackLayer`
2. **Craft_Execute** — CreateGameObject child named `{gameObject}_Hitbox` with Transform positioned at attack origin, attach CombatComponent to parent GO via AddComponent
3. **VFX chain** (if `onHitVFX` is set) — `Animation_ApplyPreset(onHitVFX, targetVCam)` is called automatically; no user action required

**Example invocation:**

```
Combat_Setup(
  gameObject: "Player",
  type: "melee",
  damage: 25,
  range: 1.5,
  knockbackForce: { x: 3.0, y: 1.5 },
  cooldown: 0.6,
  hitboxShape: "capsule",
  layer: "Enemy",
  onHitVFX: "camera-shake-hit"
)
```

Expected outcome: Player GameObject has CombatComponent attached. `Player_Hitbox` child exists. Calling `CombatComponent.Attack()` from gameplay scripts detects all colliders on the Enemy layer within 1.5 units, applies 25 damage, pushes targets with (3, 1.5) force, and triggers camera shake. 0.6s cooldown enforced.

---

### Combat_SetupHP

```
Combat_SetupHP(
  gameObject: string,
  maxHP: number,
  onDeath: "disable" | "destroy" | "ragdoll",
  deathEvent: string
) → {
  gameObject: string,
  componentPath: string,
  transactionId: string,
  maxHP: number,
  deathBehaviour: string
}
```

Add a health system to a GameObject. Generates `HealthSystem.cs` via B19 dispatch, then attaches it via Craft_Execute ModifyComponent.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `gameObject` | string | Target GameObject name |
| `maxHP` | number | Maximum hit points (default: 100). Current HP initialised to maxHP on Awake. |
| `onDeath` | "disable" \| "destroy" \| "ragdoll" | Behaviour executed when HP reaches 0. `disable`: `gameObject.SetActive(false)`. `destroy`: `Destroy(gameObject)`. `ragdoll`: disables Animator + enables all Rigidbody components (expects pre-configured ragdoll hierarchy). |
| `deathEvent` | string | C# event name broadcast on death (e.g. `"OnEnemyDied"`). Other scripts subscribe via `HealthSystem.OnEnemyDied += handler`. |

**Pipeline:**

1. **B19 dispatch** — B19 generates `HealthSystem.cs`:
   - `public int MaxHP`, `public int CurrentHP`
   - `public void TakeDamage(int amount)` — decrements CurrentHP, clamps to 0, calls `Die()` if zero
   - `private void Die()` — executes `onDeath` behaviour + broadcasts `deathEvent` C# event
   - `public event Action deathEvent` — subscribable by CombatComponent, GameDirector, UI, audio systems
2. **Craft_Execute** — `ModifyComponent` to attach `HealthSystem` to the target GO; sets `MaxHP` field to the specified value

**Example invocation:**

```
Combat_SetupHP(
  gameObject: "Enemy_Goblin",
  maxHP: 60,
  onDeath: "destroy",
  deathEvent: "OnGoblinDied"
)
```

Expected outcome: Enemy_Goblin has HealthSystem. CombatComponent.Attack() calls `HealthSystem.TakeDamage()`. At 0 HP, `Destroy(gameObject)` is called and `OnGoblinDied` event fires. Other systems (score, spawn manager) subscribe to that event.

---

### Combat_SetupSkill

```
Combat_SetupSkill(
  gameObject: string,
  skillType: "dash" | "projectile" | "aoe",
  damage: number,
  cooldown: number,
  dashForce?: number,
  projectilePrefab?: string,
  aoeRadius?: number
) → {
  gameObject: string,
  componentPath: string,
  transactionId: string,
  skillType: string,
  cooldown: number
}
```

Add a special skill to a GameObject. Generates `PlayerSkill.cs` via B19 dispatch, then attaches it via Craft_Execute.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `gameObject` | string | Target GameObject name |
| `skillType` | "dash" \| "projectile" \| "aoe" | Skill archetype — determines generated logic |
| `damage` | number | Damage dealt by the skill on hit |
| `cooldown` | number | Seconds between skill uses |
| `dashForce?` | number | Required for `dash`: force magnitude applied to Rigidbody2D in facing direction |
| `projectilePrefab?` | string | Required for `projectile`: prefab path used in `Instantiate()` call. Projectile must have a Collider2D + Rigidbody2D. |
| `aoeRadius?` | number | Required for `aoe`: radius in units for `Physics2D.OverlapCircleAll` blast |

Skill type rules:
- `dash` requires `dashForce`. Applies `Rigidbody2D.AddForce(facingDirection * dashForce, ForceMode2D.Impulse)`.
- `projectile` requires `projectilePrefab`. Instantiates prefab at GO position facing current direction; projectile script applies `damage` on collision.
- `aoe` requires `aoeRadius`. Calls `Physics2D.OverlapCircleAll` at GO position with `aoeRadius`, applies `damage` to all HealthSystems found.

**Pipeline:**

1. **B19 dispatch** — B19 generates `PlayerSkill.cs`:
   - `public void UseSkill()` — cooldown gate, skill-type branch (dash AddForce / Instantiate projectile / OverlapCircle AoE damage)
   - `private IEnumerator CooldownRoutine()` — coroutine to reset `canUse` flag after `cooldown` seconds
   - Skill-specific fields set as public serialized fields
2. **Craft_Execute** — AddComponent `PlayerSkill` to target GO; sets `damage`, `cooldown`, and type-specific fields via ModifyComponent

**Example invocations:**

```
// Dash skill
Combat_SetupSkill(
  gameObject: "Player",
  skillType: "dash",
  damage: 0,
  cooldown: 2.0,
  dashForce: 18.0
)

// Projectile skill
Combat_SetupSkill(
  gameObject: "Mage",
  skillType: "projectile",
  damage: 40,
  cooldown: 1.5,
  projectilePrefab: "Assets/Prefabs/Fireball.prefab"
)

// AoE skill
Combat_SetupSkill(
  gameObject: "Boss",
  skillType: "aoe",
  damage: 60,
  cooldown: 5.0,
  aoeRadius: 4.0
)
```

Expected outcomes:
- **Dash:** Player gets `PlayerSkill` with `UseSkill()` triggering an impulse dash. 2s cooldown. Zero damage (pure mobility).
- **Projectile:** Mage instantiates a Fireball prefab each skill use, deals 40 damage on collision. 1.5s cooldown.
- **AoE:** Boss detonates a 4-unit radius blast dealing 60 damage to all HealthSystems in range. 5s cooldown.

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
    "pipeline_hint": "2D" | "3D"
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
1. C# script generation for `CombatComponent`, `HealthSystem`, and `PlayerSkill` following Unity MonoBehaviour conventions
2. Physics API selection (2D vs 3D) based on `pipeline_hint`
3. Layer mask construction from the `layer` string parameter (`LayerMask.GetMask(layer)`)
4. Cooldown coroutine scaffolding and edge-case guards (null checks on HealthSystem, IsAlive flag)
5. C# event declaration and invocation for death broadcast
6. Prefab path validation for projectile instantiation

After B19 returns the script, CRAFT operations execute via `Craft_Execute`:
- `CreateAsset` — writes the `.cs` file to `Assets/Scripts/Combat/`
- `AddComponent` — attaches the component to the target GO
- `ModifyComponent` — sets serialized field values (damage, cooldown, layer, etc.)
- `CreateGameObject` — spawns hitbox child GO for `Combat_Setup`

## Integration with Animation Family

When `Combat_Setup` is called with `onHitVFX`, the pipeline automatically chains:

```
Animation_ApplyPreset(onHitVFX, "VCam_Combat")
```

This hooks the Cinemachine impulse (or other animation preset) to fire on each successful hit. The chain is injected by the orchestrator — no separate call is needed from the user.

Cross-family workflow example:
```
Combat_Setup("Player", "melee", 25, 1.5, {x:3, y:1.5}, 0.6, "capsule", "Enemy", "camera-shake-hit")
// → CombatComponent.cs generated + hitbox child created
// → Animation_ApplyPreset("camera-shake-hit", "VCam_Combat") auto-chained
```

## Forbidden

- Never output "write this script" or "add this component manually" to the user
- Never output raw C# code blocks for the user to copy-paste
- Never ask the user to configure a Physics Layer in Project Settings manually — use `layer` parameter and instruct B19 to use `LayerMask.GetMask()`
- All operations must go through CRAFT (Craft_Execute) or B19 dispatch

## Limitations

1. **2D vs 3D physics:** Default pipeline uses Physics2D (`OverlapCircleAll`, `AddForce` via `Rigidbody2D`). For 3D projects, pass `pipeline_hint: "3D"` in the dispatch context; B19 switches to `Physics.OverlapSphere`, `Rigidbody`, etc. The tool spec assumes 2D unless otherwise specified.

2. **Ragdoll death:** `onDeath: "ragdoll"` requires a pre-existing ragdoll hierarchy on the GO (Rigidbody components on bones set to `isKinematic=true` at runtime). The generated `HealthSystem.cs` toggles kinematics but does not build the ragdoll rig. Use a character rigging workflow to set it up beforehand.

3. **Projectile prefab ownership:** `Combat_SetupSkill` with `skillType: "projectile"` requires the prefab to already exist at `projectilePrefab` path. The tool does not create the prefab — use `Craft_Execute CreateGameObject` + `Assets_InstallUPM` or a separate prefab-build workflow first.

4. **Network / multiplayer:** Generated scripts are single-player only. For networked games (Netcode for GameObjects, Mirror), CombatComponent and HealthSystem need `[ServerRpc]` / `[ClientRpc]` wrappers. Dispatch to B19 with a `multiplayer: true` flag in `craft_context` to request Netcode-compatible variants.

5. **Animation state machine coupling:** `CombatComponent.cs` triggers the attack animation via `animator.SetTrigger("AttackTrigger")`. This requires an AnimatorController with an `AttackTrigger` parameter to exist on the GO. Use `Animation_ApplyPreset("combat-ground", gameObject)` before `Combat_Setup` to ensure the state machine is present.

## Verification Checklist

After executing Combat System operations, verify:

1. **CombatComponent (Combat_Setup)**
   - `CombatComponent.cs` exists at `Assets/Scripts/Combat/CombatComponent.cs`
   - Target GO has CombatComponent in the Inspector
   - `{gameObject}_Hitbox` child GO is present in the hierarchy
   - `damage`, `range`, `cooldown`, `attackLayer` fields are set correctly in Inspector
   - Physics overlap gizmos visible in Scene view (if debug gizmos enabled)
   - If `onHitVFX` was set: Cinemachine Impulse Source or animation preset is attached to the camera

2. **HealthSystem (Combat_SetupHP)**
   - `HealthSystem.cs` exists at `Assets/Scripts/Combat/HealthSystem.cs`
   - Target GO has HealthSystem component; `MaxHP` matches specified value
   - In Play mode: `TakeDamage()` decrements CurrentHP correctly
   - At 0 HP: `onDeath` behaviour executes (GO disabled/destroyed/ragdolled)
   - `deathEvent` fires; subscriber scripts receive the callback

3. **PlayerSkill (Combat_SetupSkill)**
   - `PlayerSkill.cs` exists at `Assets/Scripts/Combat/PlayerSkill.cs`
   - Target GO has PlayerSkill component; skill-type fields set correctly
   - In Play mode: `UseSkill()` executes correct branch (dash force / projectile spawn / AoE overlap)
   - Cooldown prevents re-use within specified seconds
   - Projectile type: prefab spawns at GO position and travels in facing direction
   - AoE type: all HealthSystems within `aoeRadius` receive `damage`

4. **No console errors** related to missing components, null Rigidbody references, or invalid layer names

## Common Workflows

### Full Player Combat Setup

```
// 1. Animation state machine first
Animation_ApplyPreset("combat-ground", "Player")

// 2. Health system
Combat_SetupHP(
  gameObject: "Player",
  maxHP: 100,
  onDeath: "disable",
  deathEvent: "OnPlayerDied"
)

// 3. Melee attack with camera shake
Combat_Setup(
  gameObject: "Player",
  type: "melee",
  damage: 20,
  range: 1.2,
  knockbackForce: { x: 2.5, y: 1.0 },
  cooldown: 0.5,
  hitboxShape: "capsule",
  layer: "Enemy",
  onHitVFX: "camera-shake-hit"
)

// 4. Dash skill
Combat_SetupSkill(
  gameObject: "Player",
  skillType: "dash",
  damage: 0,
  cooldown: 2.0,
  dashForce: 16.0
)
```

Result: Player has full combat loop — animated attack states, health with death event, melee hitbox with camera shake, and a dash ability.

### Enemy Setup

```
Combat_SetupHP(
  gameObject: "Enemy_Goblin",
  maxHP: 60,
  onDeath: "destroy",
  deathEvent: "OnGoblinDied"
)

Combat_Setup(
  gameObject: "Enemy_Goblin",
  type: "melee",
  damage: 10,
  range: 0.8,
  knockbackForce: { x: 1.0, y: 0.5 },
  cooldown: 1.2,
  hitboxShape: "sphere",
  layer: "Player"
)
```

Result: Goblin enemy with 60 HP, melee attacks the Player layer, is destroyed on death and fires `OnGoblinDied` for score/spawn systems to subscribe to.

### Boss with AoE Skill

```
Combat_SetupHP(
  gameObject: "Boss_Dragon",
  maxHP: 500,
  onDeath: "ragdoll",
  deathEvent: "OnBossDied"
)

Combat_Setup(
  gameObject: "Boss_Dragon",
  type: "melee",
  damage: 35,
  range: 2.0,
  knockbackForce: { x: 5.0, y: 2.0 },
  cooldown: 1.0,
  hitboxShape: "box",
  layer: "Player"
)

Combat_SetupSkill(
  gameObject: "Boss_Dragon",
  skillType: "aoe",
  damage: 80,
  cooldown: 8.0,
  aoeRadius: 5.0
)
```

Result: Dragon boss with 500 HP, heavy melee (box hitbox), ragdoll death, and a devastating 5-unit AoE blast on an 8s cooldown.

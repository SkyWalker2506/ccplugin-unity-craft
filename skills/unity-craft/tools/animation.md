# Animation / Timeline Tooling

## Purpose

Runtime animation authoring for character locomotion, combat systems, UI tweens, and cinematic sequences through Animator Controller state machines, parameters, transitions, AnimationCurves, and Timeline playable tracks. This tool complements the Cinemachine-focused `cinematic.md` capability by managing skeletal and property animations, state machine logic, and timeline composition for interactive cutscenes.

The tool manages:
- **Animator Controller** asset creation and state machine wiring
- **State machine design** with transitions, conditions (parameter-based), and blend trees
- **AnimationCurve authoring** for property animations (scale, position, UI tweens, camera shakes)
- **Timeline composition** with AnimationTrack, AudioTrack, ActivationTrack, and CinemachineTrack binding
- **Animation presets** — 6 curated state machines and timelines (locomotion, combat, UI, FX, doors, cinematics)
- **PlayableDirector integration** for synchronized multi-track playback

## Tool Signatures

### Animation_CreateController

```
Animation_CreateController(
  name: string,
  states: [
    {
      name: string,
      clipPath: string,
      speed?: number,
      isDefault?: boolean
    }
  ],
  transitions?: [
    {
      from: string,
      to: string,
      conditions?: [
        {
          parameter: string,
          mode: "Equals" | "Greater" | "Less",
          threshold: number | boolean
        }
      ],
      duration?: number,
      hasExitTime?: boolean
    }
  ]
) → {
  controllerPath: string,
  transactionId: string,
  stateCount: number,
  transitionCount: number
}
```

Creates an AnimatorController asset with wired states and transitions. Each state references an AnimationClip (asset path). Transitions are condition-based (parameter comparisons) with optional exit time blending. Returns the controller asset path for further modification.

### Animation_AddState

```
Animation_AddState(
  controllerPath: string,
  stateName: string,
  clipPath: string,
  speed?: number,
  isDefault?: boolean
) → {
  stateName: string,
  transactionId: string,
  speed: number,
  isDefault: boolean
}
```

Adds a new state to an existing AnimatorController. If `isDefault=true`, sets this state as the initial state for the state machine. Speed controls playback rate (1.0 = normal, 2.0 = double speed, 0.5 = half speed).

### Animation_AddTransition

```
Animation_AddTransition(
  controllerPath: string,
  from: string,
  to: string,
  conditions?: [
    {
      parameter: string,
      mode: "Equals" | "Greater" | "Less",
      threshold: number | boolean
    }
  ],
  duration?: number,
  hasExitTime?: boolean
) → {
  transitionId: string,
  transactionId: string,
  from: string,
  to: string,
  conditionCount: number
}
```

Adds a transition between two states. Conditions are AND-ed (all must be true for transition to trigger). `duration` is blend time in seconds (0.25 default). `hasExitTime=true` allows the state to exit after animation completes, independent of conditions.

### Animation_SetParameter

```
Animation_SetParameter(
  controllerPath: string,
  name: string,
  type: "float" | "int" | "bool" | "trigger",
  defaultValue?: number | boolean
) → {
  parameterName: string,
  parameterType: string,
  transactionId: string,
  defaultValue: any
}
```

Adds a parameter to the AnimatorController. Parameters drive state machine transitions. Types:
- `float` — continuous values (Speed, Blend, Intensity)
- `int` — discrete values (ComboIndex, AttackPhase)
- `bool` — on/off flags (IsMoving, IsJumping)
- `trigger` — one-shot events (Jump, Attack, Die)

### Animation_CreateTimeline

```
Animation_CreateTimeline(
  name: string,
  duration: number,
  tracks?: [
    {
      type: "AnimationTrack" | "AudioTrack" | "ActivationTrack" | "CinemachineTrack",
      targetPath?: string,
      clips: [
        {
          clipPath: string,
          startTime: number,
          duration: number
        }
      ]
    }
  ]
) → {
  timelineAssetPath: string,
  playableDirectorPath: string,
  transactionId: string,
  trackCount: number,
  duration: number
}
```

Creates a TimelineAsset and PlayableDirector GameObject. Tracks can bind AnimationClips, AudioClips, GameObject activation states, or Cinemachine virtual cameras. Each clip on a track has a start time and duration (in seconds).

### Animation_AddTrack

```
Animation_AddTrack(
  timelinePath: string,
  type: "AnimationTrack" | "AudioTrack" | "ActivationTrack" | "CinemachineTrack",
  targetPath: string,
  clips: [
    {
      clipPath: string,
      startTime: number,
      duration: number
    }
  ]
) → {
  trackName: string,
  trackType: string,
  transactionId: string,
  clipCount: number
}
```

Adds a new track to an existing Timeline. AnimationTrack targets a GameObject (animates its Animator). AudioTrack targets an AudioSource. ActivationTrack toggles GameObject.activeSelf. CinemachineTrack binds a VirtualCamera for cutscene camera work (integrates with `Cinema_RecordTrack`).

### Animation_CurveFromPoints

```
Animation_CurveFromPoints(
  points: [
    {
      time: number,
      value: number,
      inTangent?: number,
      outTangent?: number
    }
  ],
  interpolation?: "linear" | "smooth" | "step"
) → {
  curveJson: object,
  pointCount: number,
  duration: number,
  keyframeString: string
}
```

Helper function that produces an AnimationCurve from keyframe data. Supports linear (straight lines), smooth (Catmull-Rom splines), and step (holds value until next keyframe) interpolation. Returns a JSON representation suitable for use in ModifyComponent operations (e.g., animating scale, position, or shader properties).

### Animation_ApplyPreset

```
Animation_ApplyPreset(
  name: "locomotion-player" | "combat-ground" | "ui-button-press" | "camera-shake-hit" | "door-open" | "intro-cinematic",
  targetPath: string,
  options?: {
    speed?: number,
    duration?: number,
    customProperties?: object
  }
) → {
  presetName: string,
  targetPath: string,
  transactionId: string,
  assetsCreated: [string],
  setupComplete: boolean
}
```

Apply a named preset animation rig to a target GameObject. Presets bundle controller creation, state setup, parameter binding, and optional Timeline/PlayableDirector instantiation. See **Preset System** section below.

## Pipeline & E9 Dispatch Protocol

When Animation/Timeline tools are invoked, the request is dispatched to the E9 agent (`unity-cinematic-director`) with the following contract:

**Request Format:**
```json
{
  "tool": "Animation_CreateController" | "Animation_AddState" | "Animation_AddTransition" | "Animation_SetParameter" | "Animation_CreateTimeline" | "Animation_AddTrack" | "Animation_CurveFromPoints" | "Animation_ApplyPreset",
  "preset": "..." (if ApplyPreset),
  "parameters": { "..." },
  "pipeline_hint": "auto" | "URP" | "HDRP"
}
```

**Response Format:**
```json
{
  "success": true,
  "result": {
    "controllerPath": "..." | "timelineAssetPath": "..." | "curveJson": "...",
    "transactionId": "...",
    "metadata": {}
  },
  "warnings": [],
  "errors": []
}
```

E9 handles:
1. Preset JSON loading from `presets/animation/` subdirectories
2. AnimatorController asset creation and state/parameter/transition wiring
3. AnimationCurve serialization and keyframe setup
4. TimelineAsset + PlayableDirector instantiation and track binding
5. Component assembly using CRAFT operations (CreateAsset, ModifyComponent, AddComponent)
6. Integration with existing Cinemachine virtual cameras (CinemachineTrack binding)

## Preset System

Six animation presets in `presets/animation/`:

### 1. `locomotion-player.json`
Player movement state machine. States: Idle, Walk, Run. Parameters: `Speed` (float, 0–10), `IsMoving` (bool). Transitions: Idle ↔ Walk (Speed > 0.5), Walk ↔ Run (Speed > 5.0). Default: Idle.

**Applied to a GameObject with an Animator:**
```
Animation_ApplyPreset("locomotion-player", "Player")
```

Result: Player GameObject gets an AnimatorController with 3-state blend tree. Script can set `animator.SetFloat("Speed", moveSpeed)` to drive the state machine.

### 2. `combat-ground.json`
Combat state machine. States: Idle, Attack1, Attack2, Attack3, Hit, Block, Die. Parameters: `AttackTrigger` (trigger), `HitTrigger` (trigger), `BlockTrigger` (trigger), `IsDead` (bool). Transitions: Idle → any Attack (trigger), Attack → Idle (exit time 0.9s), Attack → Hit (HitTrigger), Hit → Idle (exit time 0.5s), Idle → Block (BlockTrigger), Block → Idle (BlockTrigger released), any → Die (IsDead=true).

**Applied to a combat character:**
```
Animation_ApplyPreset("combat-ground", "Enemy_Goblin")
```

Result: 3-hit combo system. Script calls `animator.SetTrigger("AttackTrigger")` to play Attack1/2/3 in sequence.

### 3. `ui-button-press.json`
Non-skeletal animation. Target: Button RectTransform. AnimationCurve for scale property. Keyframes: time 0 → value 1.0, time 0.1s → value 1.15, time 0.2s → value 1.0. Interpolation: smooth. Plays once on button click.

**Applied to a UI button:**
```
Animation_ApplyPreset("ui-button-press", "Canvas/StartButton")
```

Result: AnimationClip created. Button plays scale pop animation (1.0 → 1.15 → 1.0) over 0.2s on click.

### 4. `camera-shake-hit.json`
Cinemachine impulse curve for hit feedback. Target: CinemachineCamera. Noise amplitude curve. Keyframes: time 0 → amplitude 0, time 0.15s → amplitude 1.5, time 0.3s → amplitude 0. Duration: 0.3s. Used with Cinemachine Noise component.

**Applied to a camera during a combat hit:**
```
Animation_ApplyPreset("camera-shake-hit", "VCam_Combat")
```

Result: Screenshake impulse. Pairs with combat animations for visual impact.

### 5. `door-open.json`
Timeline-based door animation. 1-second PlayableDirector with two tracks:
- **AnimationTrack** — Door GameObject rotates from 0° to 90° (Y-axis) over 1s
- **AudioTrack** — Door creak SFX plays at 0.1s for 0.8s

**Applied to a door:**
```
Animation_ApplyPreset("door-open", "Level/Door_MainHall")
```

Result: PlayableDirector created. Script calls `playableDirector.Play()` to execute the 1-second door opening with sound.

### 6. `intro-cinematic.json`
5-second cinematic opening sequence. PlayableDirector with four tracks:
- **CinemachineTrack** — VirtualCamera cuts (framing character, 0–2s; wide shot, 2–5s)
- **AnimationTrack** — Character intro animation (0–4s)
- **AudioTrack** — Opening music (0–5s)
- **ActivationTrack** — UI fade-out overlay (4–5s)

**Applied during scene load:**
```
Animation_ApplyPreset("intro-cinematic", "Scene")
```

Result: PlayableDirector in scene root. `Craft_Execute` can bind it to scene load and auto-play for cinematic intro.

## Implementation Notes

### Animation_CreateController

Uses `Craft_Execute` with the following operation sequence:

```json
[
  {
    "type": "CreateAsset",
    "parameters": {
      "assetPath": "Assets/Animations/Controllers/<name>.controller",
      "assetType": "AnimatorController"
    }
  },
  {
    "type": "ModifyComponent",
    "target": "<target>",
    "parameters": {
      "componentType": "Animator",
      "values": {
        "controller": "Assets/Animations/Controllers/<name>.controller"
      }
    }
  }
]
```

States, transitions, and parameters are wired in E9's backend using the AnimatorController API.

### Animation_CreateTimeline

Uses `Craft_Execute` with:

```json
[
  {
    "type": "CreateAsset",
    "parameters": {
      "assetPath": "Assets/Timelines/<name>.playable",
      "assetType": "TimelineAsset"
    }
  },
  {
    "type": "CreateGameObject",
    "parameters": {
      "name": "PlayableDirector_<name>",
      "components": ["PlayableDirector"],
      "position": [0, 0, 0]
    }
  },
  {
    "type": "ModifyComponent",
    "target": "PlayableDirector_<name>",
    "parameters": {
      "componentType": "PlayableDirector",
      "values": {
        "playableAsset": "Assets/Timelines/<name>.playable"
      }
    }
  }
]
```

Tracks are added to the TimelineAsset after creation.

### Animation_CurveFromPoints

Converts array of `{time, value, inTangent?, outTangent?}` objects into Unity's Keyframe format and serializes as JSON. Interpolation mode is baked into the keyframe tangents (smooth = computed spline tangents, linear = zero tangents, step = infinite tangents).

## Example Scenarios

### Scenario 1: Player Locomotion State Machine

```
User: "Set up player locomotion with idle, walk, and run animations"

1. Animation_ApplyPreset("locomotion-player", "Player")
   → AnimatorController created with 3 states, Speed + IsMoving parameters
   
2. In gameplay script:
   animator.SetFloat("Speed", Vector3.Magnitude(moveDirection))
   → State machine drives Idle/Walk/Run blending automatically
```

**Expected outcome:**
- Player GameObject has Animator component pointing to locomotion-player controller
- Speed parameter controls state transitions smoothly
- Walk and Run animations play based on movement magnitude

### Scenario 2: Combat System from Scratch

```
User: "Create a combat animator for a ground-based enemy with attack combos"

1. Animation_CreateController("EnemyAttackController", [
     { name: "Idle", clipPath: "Assets/Animations/Enemy/Idle.anim", isDefault: true },
     { name: "Attack1", clipPath: "Assets/Animations/Enemy/Attack1.anim" },
     { name: "Attack2", clipPath: "Assets/Animations/Enemy/Attack2.anim" },
     { name: "Hit", clipPath: "Assets/Animations/Enemy/Hit.anim" }
   ])
   → EnemyAttackController created
   
2. Animation_SetParameter("Assets/Animations/EnemyAttackController.controller", "AttackTrigger", "trigger")
   Animation_SetParameter("Assets/Animations/EnemyAttackController.controller", "IsDead", "bool", false)
   → Parameters added
   
3. Animation_AddTransition(
     "Assets/Animations/EnemyAttackController.controller",
     "Idle", "Attack1",
     [{ parameter: "AttackTrigger", mode: "Equals", threshold: 1 }],
     0.1, false
   )
   Animation_AddTransition(
     "Assets/Animations/EnemyAttackController.controller",
     "Attack1", "Idle",
     [], 0.2, true  // exit time, no conditions
   )
   → Transitions wired
```

**Expected outcome:**
- Enemy Animator uses EnemyAttackController
- Script calls `animator.SetTrigger("AttackTrigger")` to trigger combo
- State machine cycles Attack1 → Attack2 → Attack3 → Idle automatically (via exit times)

### Scenario 3: Cinematic Intro Timeline

```
User: "Create a 5-second opening cutscene with character, camera, music, and UI fade"

1. Animation_ApplyPreset("intro-cinematic", "Scene")
   → PlayableDirector_intro-cinematic created with 4 tracks (VCam + animation + audio + UI activation)
   
2. Craft_Execute({
     "operations": [
       {
         "type": "ModifyComponent",
         "target": "PlayableDirector_intro-cinematic",
         "parameters": {
           "componentType": "PlayableDirector",
           "values": { "playOnAwake": true }
         }
       }
     ],
     "transactionName": "Auto-play intro on scene load"
   })
```

**Expected outcome:**
- PlayableDirector auto-plays when scene loads
- Character animation + VCam cuts + music + UI fade execute in sync over 5s
- Scene is fully loaded and interactive after director finishes

### Scenario 4: UI Button Pop Tween

```
User: "Add a scale pop animation to the start button"

1. Animation_ApplyPreset("ui-button-press", "Canvas/StartButton")
   → AnimationClip created with scale curve (1.0 → 1.15 → 1.0 over 0.2s)
   
2. Button's OnClick event can trigger the animation via Animator or Animation component
```

**Expected outcome:**
- StartButton RectTransform plays scale pop when clicked
- Animation completes in 0.2s, returns to original scale

## Integration with Cinematic Family

The Animation and Cinematic tool families work together:

1. **Cinemachine track in Timeline:** Use `Cinema_RecordTrack(vCamPath, timelinePath)` to bind a virtual camera created by `Cinema_CreateVCam` to a CinemachineTrack in a Timeline. The animation family can then add AnimationTracks + AudioTracks to the same Timeline for synchronized cutscenes.

2. **Camera shake on hit:** Use `Animation_ApplyPreset("camera-shake-hit", vCamPath)` to add Cinemachine impulse noise to a VCam, synced with combat animations.

3. **Cross-family workflow:**
   ```
   Cinema_CreateVCam("Cinematic", "CutsceneTarget", { name: "VCam_Intro" })
   Animation_CreateTimeline("OpeningSequence", 5.0, [...])
   Cinema_RecordTrack("VCam_Intro", "Assets/Timelines/OpeningSequence.playable")
   Animation_AddTrack("Assets/Timelines/OpeningSequence.playable", "AnimationTrack", "Character", [...])
   ```

## Limitations

1. **Curve editing at runtime:** AnimationCurve properties can only be fully authored in the Editor. At runtime (via CRAFT), curves can be created from keyframe points, but visual editing in the Inspector is unavailable. E9 handles preset JSON → curve serialization; custom curves require Editor time.

2. **AnimationEvent method binding:** AnimationEvents (callbacks triggered at specific animation frames) require a matching C# method on the target script. The animation tool can mark event frames in a clip, but the actual method must exist and match the signature — there is no automatic method generation.

3. **Blend Trees:** Complex blend tree topologies (2D, 3D directional) are supported via preset JSON, but runtime modification of blend tree structure is limited. The presets cover common cases (1D speed blending, directional blending); custom trees should be edited in the Editor.

4. **State machine validation:** The tool assumes clip assets exist at specified paths. Broken clip references will cause warnings at dispatch time; validation happens in E9.

## Verification Checklist

After executing Animation operations, verify:

1. **Animator Controller Creation:**
   - AnimatorController asset exists at the returned path
   - Target GameObject has Animator component linked to the controller
   - States appear in the Animator window (if opened in Editor)
   - Default state is set correctly

2. **State Machine Setup:**
   - States are wired with visible transitions in Animator
   - Transitions have correct conditions (parameter checks visible)
   - Exit time settings are applied as specified

3. **Parameters:**
   - Parameters appear in Animator's parameter panel
   - Default values are set correctly
   - Types are correct (float, int, bool, trigger)

4. **Timeline Execution:**
   - PlayableDirector GameObject exists in scene
   - TimelineAsset is linked to PlayableDirector
   - Tracks are visible in Timeline UI (if opened)
   - Clips are placed at specified start times with correct durations
   - PlayOnAwake is set if auto-play is desired

5. **Animation Curves:**
   - Curves applied to animated properties show correct keyframe positions
   - Interpolation mode matches specification (linear/smooth/step)
   - Animation plays correctly in Game view

6. **Scene Playback:**
   - Playing the scene executes state machine transitions as expected
   - PlayableDirector plays Timeline tracks in sync
   - No console errors related to missing assets or broken references

## Common Workflows

**Quick player setup:**
```
Animation_ApplyPreset("locomotion-player", "Player")
// Player now responds to Speed parameter from script
```

**Combat system with combo:**
```
Animation_ApplyPreset("combat-ground", "Enemy")
// Enemy animator has Attack1/2/3 states with trigger-based combo
```

**Cinematic intro with multiple tracks:**
```
Animation_ApplyPreset("intro-cinematic", "Scene")
// 5-second opening plays automatically on scene load
```

**Custom curve animation:**
```
Animation_CurveFromPoints([
  { time: 0, value: 1.0 },
  { time: 0.5, value: 2.0 },
  { time: 1.0, value: 1.0 }
], "smooth")
// Results in a bell-curve scale animation
```

**Door with SFX:**
```
Animation_ApplyPreset("door-open", "Level/Door_MainHall")
// Door rotates and plays creak sound in 1 second
```

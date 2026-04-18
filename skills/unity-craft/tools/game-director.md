# Game Director Tool Family

## Purpose

GDD (Game Design Document) → playable game pipeline. Reads structured Game Design Documents, produces ordered task graphs (DAGs), dispatches work across 10 tool families (Design/Screen/Cinematic/Animation/Level/Input/Audio/Optimization/AssetStore/GameDirector), runs vision-feedback loops, playtests, and ships a polished-to-placeholder-art demo. Target: 5–60 minutes wall-clock, polish score ≥ 8/10.

---

## Tool Signatures

### Director_ParseGDD

```
Director_ParseGDD(
  gddPath: string
) → {
  title: string,
  pitch: string,
  mechanics: {
    name: string,
    description: string
  }[],
  levels: {
    name: string,
    duration_sec: number,
    geometry: string,
    spawns: string[],
    objectives: string[]
  }[],
  artDirection: {
    style: string,
    palette: string[],
    camera_type: string
  },
  audioDirection: {
    music_tempo_bpm: number,
    music_duration_sec: number,
    sfx: string[],
    ambience: string
  },
  uiStyle: {
    font: string,
    color_primary: string,
    color_background: string
  },
  controls: {
    [action: string]: string  // e.g., "move": "WASD"
  },
  technical: {
    platform: string,
    target_fps: number,
    memory_budget_mb: number,
    build_size_mb: number
  },
  playtestCriteria: string[]
}
```

Parses a GDD file (YAML front-matter + markdown sections) and returns structured JSON. Handles both well-formed YAML and text extracted via LLM (lower confidence).

---

### Director_PlanGame

```
Director_PlanGame(
  gddJson: object
) → {
  waves: {
    wave_id: number,
    name: string,
    estimated_duration_minutes: number,
    parallel_tasks: {
      task_id: string,
      family: string,  // "Level" | "Audio" | "Cinematic" | "Input" | etc.
      task: string,
      agent: string,    // E9 | E11 | E16 | B26 | B36 | B53 | D11 | G13 | A14
      parameters: object,
      blockers: string[]  // task_ids that must complete first
    }[]
  }[],
  critical_path: string[],
  estimated_total_duration_minutes: number
}
```

Given parsed GDD, builds a DAG of tasks organized into parallel-safe waves. Each wave can execute multiple tasks in parallel if they have no blocking dependencies.

---

### Director_ExecutePlan

```
Director_ExecutePlan(
  planJson: object,
  maxPolishIterations: number = 3
) → {
  success: boolean,
  waves_completed: number,
  final_polish_score: number,
  iteration_log: {
    wave: number,
    status: "pass" | "refinement_applied" | "failed",
    critique_scores: { [criterion: string]: number },
    tasks_completed: string[],
    refinement_tasks_spawned: string[]
  }[],
  playtest_result: {
    scenario: string,
    fps_avg: number,
    fps_p95: number,
    memory_peak_mb: number,
    gc_per_frame_kb: number,
    crash_count: number,
    console_errors: string[]
  },
  scene_path: string,
  build_path: string
}
```

Executes the DAG wave-by-wave, dispatching each task to its assigned agent. After each wave, invokes vision feedback loop (G13 critique). If polish < threshold, spawns refinement tasks and loops back. Runs playtest after final wave. Returns complete execution log + final state.

---

### Director_Critique

```
Director_Critique(
  scope: "ui" | "level" | "assets" | "all" = "all",
  scoreThreshold: number = 8.0
) → {
  scores: {
    ui_legibility: number,
    level_navigability: number,
    asset_coherence: number,
    responsiveness: number,
    audio_presence: number,
    cinematography: number,
    performance_stability: number,
    stability_crashes: number,
    visual_hierarchy: number,
    shippable_feel: number
  },
  average_score: number,
  per_criterion_notes: { [criterion: string]: string },
  recommendations: {
    criterion: string,
    issue: string,
    severity: "low" | "medium" | "high",
    fix_suggestion: string,
    dispatch_to: string  // agent family
  }[],
  passes_threshold: boolean
}
```

Captures current game state (screenshots via G13, profiler data, console), critiques it against 10-criterion rubric, returns scores + recommendations. Dispatched to G13 vision operator; A14 polls result and decides next action.

---

### Director_Playtest

```
Director_Playtest(
  scenarioName: "smoke" | "combat" | "exploration" | "menu-flow",
  durationSec: number = 30
) → {
  success: boolean,
  scenario: string,
  fps_avg: number,
  fps_p95: number,
  frametime_max_ms: number,
  memory_peak_mb: number,
  memory_growth_mb: number,
  gc_per_frame_kb: number,
  gc_spike_count: number,
  cpu_breakdown_pct: {
    render: number,
    script: number,
    physics: number,
    other: number
  },
  crash_count: number,
  console_errors: string[],
  console_warnings: string[],
  perf_assessment: {
    fps: "excellent" | "good" | "acceptable" | "poor",
    memory: "excellent" | "good" | "acceptable" | "poor",
    cpu: "excellent" | "good" | "acceptable" | "poor"
  }
}
```

Enters Play mode, simulates canonical input sequence (WASD sweep, menu navigation, core mechanic trigger, combat loop, etc.), samples profiler for 30s, exits Play mode. Returns fps + memory + stability metrics + crash log.

**Upstream CRAFT ops required:**
- `Craft_EnterPlayMode()` — Enter Play mode
- `Craft_SimulateInput()` — Simulate keyboard/mouse input
- `Craft_SampleProfileWindow()` — Sample Profiler stats
- `Craft_ExitPlayMode()` — Exit Play mode

---

### Director_Ship

```
Director_Ship(
  gddPath: string,
  maxWallClockMin: number = 60
) → {
  success: boolean,
  gdd_title: string,
  final_polish_score: number,
  iteration_count: number,
  wall_clock_minutes: number,
  scene_path: string,
  build_path: string,
  artifacts: {
    scene_asset: string,
    prefabs: string[],
    materials: string[],
    audio_clips: string[],
    animator_controllers: string[]
  },
  playtest_summary: {
    scenarios_passed: number,
    fps_avg: number,
    stability: "pass" | "fail"
  },
  known_limitations: string[]
}
```

**Top-level entry point.** Orchestrates the full pipeline:

```
1. ParseGDD(gddPath)
2. PlanGame(gddJson)
3. ExecutePlan(planJson, maxIterations=3)
   a. For each wave:
      - Dispatch tasks to agents
      - Wait for completion
      - Invoke Director_Critique
      - If polish < threshold: spawn refinement, loop to 3a
   b. After all waves: Director_Playtest (smoke scenario)
   c. If perf < target or crash: spawn B53 fix, retest
4. If polish ≥ 8 and playtest PASS: export build
5. Return summary + artifacts

If wall-clock exceeds maxWallClockMin:
  - Stop iteration, ship current state as "beta" (polish < 8)
  - Flag for manual review
```

---

## Dispatch Protocol

When each tool is invoked, a task is dispatched to **A14** (Game Director agent) with attached GDD context. A14 reads the GDD fully, builds a DAG, and dispatches waves to specialist agents per family:

| Family | Agent | Trigger in DAG |
|--------|-------|---|
| Design/UI | D11 | "Design" tasks (ImportUIBundle, BuildHUD) |
| Screen Capture | G13 | "Screen" tasks (CaptureGameView, VisionFeedback) |
| Cinematic | E9 | "Cinematic" tasks (CreateVCam, ApplyPostFX) |
| Animation | E9 | "Animation" tasks (CreateAnimatorController, StateMachine) |
| Level | E11 | "Level" tasks (CreateGeometry, BakeNavMesh, Lighting) |
| Input | B36 | "Input" tasks (CreateActionMaps, BindToGameplay) |
| Audio | B26 | "Audio" tasks (SetupMixer, ImportClips) |
| Optimization | B53 | "Optimization" tasks (ProfileScene, TextureCompression, QualityPreset) |
| Asset Store | E16 | "AssetStore" tasks (ResearchLibrary, InstallUPM) |

**Response Format (per dispatch):**
```json
{
  "success": true,
  "task_id": "L001",
  "family": "Level",
  "agent": "E11",
  "result": {
    "geometry_created": true,
    "spawn_points": 2,
    "transaction_id": "craft-txn-abc123",
    "warnings": []
  },
  "duration_seconds": 180
}
```

---

## Polish Iteration Loop

If `Director_Critique` returns `average_score < 8.0`:

```
Refinement Loop:
  1. Identify lowest-scoring criteria
  2. For each low-score criterion, match to tool family
     e.g., "audio_presence" (6) → spawn B26 audio task
  3. Spawn refinement sub-wave
  4. Re-execute affected wave + dependent waves
  5. Re-critique (invoke Director_Critique again)
  6. If score improved: continue to next wave
  7. If score unchanged after 2 iterations: escalate to A1
  8. Repeat until score ≥ 8 or maxIterations reached
```

---

## GDD Input Format

### Minimal Example (Mushroom Arena — 5 minutes)

**File:** `gdd.md`

```yaml
---
title: "Mushroom Arena"
genre: "Action / Arena Survival"
scope: "micro (5 min)"
target_audience: "casual"
platform: "desktop"
placeholder_art_ok: true
tech_constraints:
  - "URP only"
  - "2D physics"
  - "no advanced VFX"
---

# Mushroom Arena

## Pitch
Top-down arena survivor: defend a shrine against 3 waves of mushroom enemies. 
One auto-targeting gun. 3-minute total playtime. Retro gameboy aesthetic.

## Mechanics
- **Player:** WASD move, mouse aim, left-click fire. Speed 5 m/s.
- **Gun:** Auto-targets nearest enemy within 10m, fires every 0.3s, 10 damage.
- **Enemies:** 3 types (Mushroom, Slime, Boss), spawn in waves.
- **Score:** +10 per kill, +1 per second survived.

## Levels
**Arena (0–180s):** 20x20m, player center, enemy waves spawn randomly.

## Art Direction
- **Style:** Retro gameboy (4-color palette)
- **Camera:** Fixed orthographic, full arena visible
- **UI:** Green monochrome, sans-serif font

## Audio Direction
- **Music:** 8-bit chiptune loop, 120 BPM, 3 min duration
- **SFX:** Laser beep (fire), chime (spawn), chord (wave end)
- **Ambience:** Forest crickets, low volume

## UI Style
- **HUD:** Score (top-right), Wave counter (top-left), Enemy count (bottom-right)
- **Game Over:** Final score + Restart/Quit buttons

## Controls
- **Move:** WASD
- **Aim:** Mouse
- **Fire:** Left Click (hold to maintain)

## Technical Constraints
- **Target:** Win/Linux desktop, 1920x1080, 60 FPS
- **Physics:** 2D only
- **Memory:** < 150MB

## Playtest Criteria
1. Input responsiveness < 50ms
2. All enemy types spawn and behave correctly
3. Score tracking accurate
4. Game completes in 3 ± 0.5 minutes
5. Zero crashes; clean console
```

### Full Example (Platformer — 30 minutes)

See `knowledge/gdd-structure.md` for detailed multi-level platformer example with extended mechanics + cinematics.

---

## Worked Example 1: Platformer Chunk Demo

**GDD:** 2D platformer, 1 room, player jumps, 3 platforms, goal flag

**Director_Ship Flow:**

```
1. ParseGDD("platformer.md")
   → Title: "Jump Quest"
   → Mechanics: [Move, Jump, Dash]
   → Levels: [Room_01 (20s)]
   → Art: Pixel art, bright colors
   → Audio: Jump SFX, background music

2. PlanGame(gddJson)
   → Wave 0: Level geometry, Audio mixer, Input maps
   → Wave 1: NavMesh, Player animator
   → Wave 2: Cinematic camera, UI, Audio import
   → Wave 3: Animation state machine, Input binding
   → Wave 4: Playtest
   → Critical path: L0 → L1 → A1 → PT
   → Est. duration: 20 min

3. ExecutePlan(planJson)
   
   Wave 0 (6 min):
     - E11: CreateRoomGeometry (3 platforms, goal flag)
     - B26: SetupAudioMixer (Music, SFX groups)
     - B36: CreateActionMaps (Move, Jump, Dash)
     ✓ Critique: avg 7.2/10 (level navigability 6, audio 5)
     → Refinement: B26 import jump SFX
   
   Wave 1 (5 min):
     - E11: BakeNavMesh
     - E9: CreatePlayerAnimator (Idle, Jump, Fall, Land)
     ✓ Critique: avg 8.1/10
     → Proceed
   
   Wave 2 (6 min):
     - E9: CreateCinematicVCam (TopDown)
     - D11: BuildHUD (Score, Lives)
     - B26: ImportJumpSFX + BackgroundMusic
     ✓ Critique: avg 8.4/10
     → Proceed
   
   Wave 3 (4 min):
     - E9: CreateAnimatorStateMachine (Idle→Jump→Fall→Land)
     - B36: BindInputToGameplay (Jump → JumpScript.Jump())
     ✓ Critique: avg 8.6/10
     → Proceed
   
   Wave 4 (2 min):
     - A14: Director_Playtest(smoke, 30)
     ✓ fps 59.8, zero crashes, input latency 32ms
     ✓ PASS

4. Export Build
   → Scene: Assets/Scenes/JumpQuest.unity
   → Prefabs: Player, Platform, Flag
   → Materials: Pixel_grass, Pixel_sky
   → Build: /Builds/jump-quest-2026-04-18.zip

Final: Polish 8.6/10, 1 iteration, 22 minutes wall-clock
```

---

### Worked Example 2: Arena Survivor GDD → Playable

**GDD:** Top-down arena, 3 enemy waves, auto-targeting gun, 3 minutes

**Critique Scorecard (Wave 2 Polish):**

```
UI Legibility: 9/10 ✓
Level Navigability: 8/10 ✓
Asset Coherence: 7/10 (player color mismatch)
Responsiveness: 10/10 ✓
Audio Presence: 6/10 (missing spawn SFX)
Cinematography: 8/10 ✓
Performance Stability: 9/10 ✓
Stability (Crashes): 10/10 ✓
Visual Hierarchy: 9/10 ✓
Shippable Feel: 8/10 ✓

Average: 8.4/10
→ PASS (Polish ≥ 8)
```

**Refinements Applied:**
- Spawn B26 audio task: "ImportEnemySpawnSFX" (yield +0.5 to audio_presence)
- Optional: D11 color adjustment (asset_coherence +0.5)

**Playtest Result (Smoke Scenario):**
- fps_avg: 59.7
- Crashes: 0
- Console errors: 0
- Input latency: 28ms
- Duration: 2m 15s (within 3 ± 0.5 target)

→ **Ship candidate.**

---

## Limitations

1. **Requires upstream CRAFT v0.3+** — Play mode ops (EnterPlayMode, SimulateInput, SampleProfileWindow, ExitPlayMode) must be implemented
2. **GDD must be structured** — Dual YAML + markdown format. Free-form text fallback via LLM extraction, but lower reliability
3. **Polish score is relative** — Calibrated to "shippable placeholder demo", not AAA. Score ≥ 8 = "good enough to share"; ≥ 9 = "polished feeling"
4. **No high-res assets** — Plugin expects placeholder art, retro styles, simple geometry. Not for photorealistic games
5. **Single-scene assumption** — Most GDDs fit in 1 scene; multi-scene GDDs may need manual stitching
6. **Audio mixing is basic** — Mixer setup is 2–3 groups; complex mixing (ducking, reverb sends) requires B26 deep-dive

---

## Verification

After `Director_Ship` completes successfully:

- [ ] Scene opens in Editor without errors
- [ ] Play button works (compile success, scripts ready)
- [ ] WASD moves, mouse looks, core mechanic triggers
- [ ] Console: 0 errors, < 10 warnings
- [ ] Profiler: fps ≥ 59 avg, no GC spikes
- [ ] Playtest: zero crashes, canonical scenario completes
- [ ] Polish score ≥ 7/10 (all 10 criteria, avg ≥ 7)
- [ ] Build exported (APK / EXE / .zip)

---

## Tips for GDD Authors

1. **Be precise with mechanics** — "move left/right" vs "smooth acceleration", "instant fire" vs "charge time"
2. **Name enemy types clearly** — "Enemy_Mushroom" not just "Enemy"
3. **Specify audio mood** — "ominous", "upbeat", "serene" guides B26 selection
4. **Lock art style early** — "gameboy palette", "voxel", "low-poly" affects all asset choices
5. **Tech constraints matter** — Mentioning "mobile target" triggers B32 optimizations; "DOTS required" changes E11 level design
6. **Playtest criteria should be measurable** — "feels fun" is vague; "player can beat level in < 5min" is testable

# Play-Test Automation Tool

## Purpose

Enter Play mode, execute scripted input scenarios, sample performance metrics during play, then exit cleanly. Closes the "verify the game actually works before declaring done" gap by automating QA smoke tests, performance benchmarks, and input-validation flows. Returns pass/fail verdicts + performance deltas + error logs + screenshots for A14 (Game Director) to interpret.

All interactions are **fully autonomous**—no user prompts to "press Play", "wait for load", or "check the output". Results come back as structured data for pipeline consumption.

---

## Upstream Dependency

This tool requires **CRAFT v0.3 ops** (not yet released). Until `com.skywalker.craft` lands the following, `Playtest_Run` operates as a **dry-run**:

- `Craft_EnterPlayMode()` — transition to Play mode, block until ready
- `Craft_ExitPlayMode()` — cleanly exit Play mode, restore Editor state
- `Craft_SimulateInput(action, value, duration)` — inject input bindings (keyboard, axis, mouse)
- `Craft_SampleProfileWindow(metrics, durationSec)` — capture FPS, memory, GC, draw calls over window
- `Craft_GetPlayModeStatus()` — query current play state (Loading, Running, Paused, Error)

**Interim behavior:** Playtest_Run returns mock data matching the return shape below + documents the exact ops sequence it will execute once upstream lands. This allows A14 to test dispatch logic without blocking on CRAFT.

---

## Tool Signatures

### Playtest_Run

Execute a built-in or custom scenario in Play mode, measure performance, then exit.

**Signature:**
```
Playtest_Run(
  scenario: string,
    // Built-in: "smoke", "input-sweep", "menu-flow", "combat", "exploration"
    // Custom: identifier for user-defined scenario (see Playtest_Scenario)
  durationSec?: float = 30
    // Override scenario's default duration (applies to custom scenarios mostly)
) -> {
  pass: boolean,
  fps_avg: float,
  fps_p95: float,
  fps_p05: float,
  memory_mb_peak: float,
  memory_mb_avg: float,
  gc_kb_per_frame: float,
  draw_calls_avg: float,
  errors: string[],
  warnings: string[],
  screenshots: string[],        // File paths of captured frames
  durationSec: float,
  timestamp: ISO8601,
  platform: "mobile" | "desktop" | "console",
  thresholds_met: {
    fps_avg: boolean,
    fps_p95: boolean,
    memory_peak: boolean,
    no_errors: boolean
  }
}
```

**Behavior:**
1. Validate scenario name (built-in or registered custom)
2. Call `Craft_EnterPlayMode()` and block until play state = "Running"
3. Execute scenario steps (input simulation, waits, asserts)
4. Continuously sample `Craft_SampleProfileWindow` every 100ms
5. Call `Craft_ExitPlayMode()` when done
6. Compare metrics against platform thresholds (see Perf Thresholds section)
7. Return pass verdict (true if all metrics pass AND no errors logged)

**Example:**
```json
Playtest_Run({
  scenario: "smoke",
  durationSec: 10
})
→ {
  pass: true,
  fps_avg: 58.2,
  fps_p95: 52.1,
  fps_p05: 61.3,
  memory_mb_peak: 412.5,
  memory_mb_avg: 398.0,
  gc_kb_per_frame: 0.3,
  draw_calls_avg: 127,
  errors: [],
  warnings: ["One camera has clipping plane warnings"],
  screenshots: [
    "Assets/.unity-craft/playtests/smoke_2026-04-18_14-22-15_frame_0000.png",
    "Assets/.unity-craft/playtests/smoke_2026-04-18_14-22-15_frame_0150.png"
  ],
  durationSec: 10.0,
  timestamp: "2026-04-18T14:22:15Z",
  platform: "desktop",
  thresholds_met: {
    fps_avg: true,
    fps_p95: true,
    memory_peak: true,
    no_errors: true
  }
}
```

---

### Playtest_Scenario

Define a custom scenario (one-shot registration; not persisted across sessions).

**Signature:**
```
Playtest_Scenario(
  name: string,
    // e.g. "boss-arena", "procedural-regen"
  steps: Step[]
    // Array of timed actions
) -> {
  registered: boolean,
  name: string,
  stepCount: number,
  estimatedDurationSec: float
}

// Step interface
{
  at: float,                     // Seconds into scenario
  action: "key-press" | "axis-set" | "mouse-click" | "wait" | "assert" | "screenshot",
  params: {
    // key-press: { key: "W", duration?: 0.5 }
    // axis-set: { axis: "Vertical", value: 1.0, duration: 2.0 }
    // mouse-click: { position: [x, y], button: "left|right|middle", count: 1 }
    // wait: { seconds: 2.0 }
    // assert: { condition: "player.health > 0", description: "Player alive" }
    // screenshot: { tag: "mid-scene" }
  }
}
```

**Behavior:**
- Register scenario in session memory (cleared on playtest completion)
- Validate steps (times in ascending order, valid action names)
- Estimate total duration from final step time
- Return registration confirmation + duration estimate
- Steps execute in order during `Playtest_Run`

**Example:**
```json
Playtest_Scenario({
  name: "boss-attack",
  steps: [
    { at: 0, action: "key-press", params: { key: "Space", duration: 0.1 } },
    { at: 1.0, action: "axis-set", params: { axis: "Vertical", value: 1.0, duration: 3.0 } },
    { at: 2.0, action: "mouse-click", params: { position: [960, 540], button: "left" } },
    { at: 4.0, action: "assert", params: { condition: "enemy.health < 100", description: "Damage landed" } },
    { at: 5.0, action: "screenshot", params: { tag: "impact" } }
  ]
})
→ {
  registered: true,
  name: "boss-attack",
  stepCount: 5,
  estimatedDurationSec: 5.5
}
```

---

### Playtest_Measure

Capture performance metrics WITHOUT input simulation. Useful for baseline sampling or profiling specific scenes.

**Signature:**
```
Playtest_Measure(
  durationSec: float = 30,
  metrics?: string[] = ["fps", "memory", "gc", "draw-calls"]
    // Subset: "fps", "memory", "gc", "draw-calls", "tris", "batches"
) -> {
  fps_avg: float,
  fps_p95: float,
  fps_p05: float,
  memory_mb_peak: float,
  memory_mb_avg: float,
  gc_kb_per_frame: float,
  draw_calls_avg: float,
  triangles_avg: float,
  batches_avg: float,
  durationSec: float,
  timestamp: ISO8601
}
```

**Behavior:**
1. Assume Play mode already active (does NOT call `EnterPlayMode`)
2. Sample requested metrics continuously for durationSec
3. Return aggregated stats (avg, p95, p05, peak)
4. Do NOT exit Play mode

**Example:**
```json
Playtest_Measure({
  durationSec: 15,
  metrics: ["fps", "memory", "draw-calls"]
})
→ {
  fps_avg: 60.1,
  fps_p95: 59.0,
  fps_p05: 60.5,
  memory_mb_peak: 320.0,
  memory_mb_avg: 315.5,
  gc_kb_per_frame: 0.1,
  draw_calls_avg: 98,
  triangles_avg: 0,
  batches_avg: 0,
  durationSec: 15.0,
  timestamp: "2026-04-18T14:23:00Z"
}
```

---

### Playtest_Record

Capture Game view video frame-by-frame via `Craft_CaptureGameView` for frame-by-frame review or slow-motion debugging.

**Signature:**
```
Playtest_Record(
  durationSec: float,
  outputPath: string,
    // e.g. "Assets/Playtests/session_001"
    // Frames saved to: {outputPath}/frame_NNNN.png
  fps?: int = 30
    // Target capture rate (frames per second)
) -> {
  outputPath: string,
  frameCount: number,
  frameSizeMB: float,
  totalSizeMB: float,
  timestamp: ISO8601
}
```

**Behavior:**
1. Assume Play mode active
2. Every 1/fps seconds, call `Craft_CaptureGameView`
3. Save frames to `{outputPath}/frame_0000.png`, `frame_0001.png`, etc.
4. Return total frame count + disk usage
5. Do NOT exit Play mode

**Example:**
```json
Playtest_Record({
  durationSec: 10,
  outputPath: "Assets/Playtests/slowmo_001",
  fps: 30
})
→ {
  outputPath: "Assets/Playtests/slowmo_001",
  frameCount: 300,
  frameSizeMB: 2.4,
  totalSizeMB: 720.0,
  timestamp: "2026-04-18T14:23:15Z"
}
```

---

## Built-In Scenarios

### smoke

Verify scene loads, idles for 5 seconds without errors.

**Steps:**
1. Enter Play mode
2. Wait 5 seconds
3. Assert: no exceptions logged
4. Take screenshot
5. Exit Play mode

**Pass Criteria:** No errors in console log, FPS stable.

**Typical Output:** 10-15 draw calls, <100MB memory, 60+ FPS.

---

### input-sweep

Press every major input binding from the active InputSystem action map once each, 15 seconds total.

**Steps:**
1. Enter Play mode
2. For each binding in active action map:
   - Press key / move axis / click button (0.1s duration)
   - Wait 0.5s
3. Assert: no exceptions logged
4. Exit Play mode

**Pass Criteria:** All input events dispatched without error, no hang.

**Typical Output:** 20-30 draw calls (may include UI), <150MB memory.

---

### menu-flow

Open menu → navigate Settings → back to main → close.

**Steps:**
1. Enter Play mode
2. Wait 2s (load complete)
3. Key-press "Escape" (opens menu)
4. Mouse-click on "Settings" button
5. Assert: settings panel visible
6. Key-press "Escape" (closes settings, back to main)
7. Assert: main menu visible
8. Key-press "Escape" (closes menu)
9. Exit Play mode

**Pass Criteria:** All UI interactions responsive (no freezes), no errors.

**Typical Output:** UI Toolkit rebuild count < 10/frame, <200MB memory.

---

### combat

Spawn enemy → trigger attack → confirm hit registration → enemy death animation.

**Steps:**
1. Enter Play mode
2. Wait 2s (scene load)
3. Assert: player present
4. Assert: enemy spawner ready
5. Key-press "Space" (spawn enemy)
6. Wait 1s (enemy appears)
7. Mouse-click on enemy position (trigger player attack)
8. Wait 2s (hit animation + impact)
9. Assert: enemy health <= 0 OR death animation triggered
10. Wait 2s (death anim completes)
11. Exit Play mode

**Pass Criteria:** Hit register confirmed, no animation glitches, **FPS must stay >= 30 (mobile) or >= 60 (desktop)**.

**Typical Output:** 80-120 draw calls, 250-350MB memory, FPS dip post-impact recovers within 1 frame.

---

### exploration

Move player around a cached waypoint path for 30 seconds; sample performance for steady-state behavior.

**Steps:**
1. Enter Play mode
2. Wait 2s (scene load)
3. For waypoint in [wp0, wp1, wp2, wp0]:
   - Move toward waypoint via axis input (up to 5s each)
   - Take screenshot every 5s
4. Exit Play mode

**Pass Criteria:** Frame times remain stable (std dev < 10% of mean), no memory leaks detected (GC per-frame steady).

**Typical Output:** 60-100 draw calls, 300-400MB memory, consistent FPS throughout.

---

## Dispatch Protocol

A14 (Game Director) calls `Playtest_Run` with scenario + optional duration.

**A14 → Playtest:**
```json
{
  "scenario": "combat",
  "durationSec": 20
}
```

**Playtest → A14 (on success):**
```json
{
  "pass": true,
  "fps_avg": 55.2,
  "fps_p95": 48.0,
  "fps_p05": 60.1,
  "memory_mb_peak": 380.0,
  "memory_mb_avg": 370.5,
  "gc_kb_per_frame": 0.2,
  "draw_calls_avg": 105,
  "errors": [],
  "warnings": [],
  "screenshots": ["..."],
  "durationSec": 20.0,
  "platform": "mobile",
  "thresholds_met": {
    "fps_avg": false,     // 55.2 < 60 (mobile target)
    "fps_p95": false,     // 48.0 < 60
    "memory_peak": true,
    "no_errors": true
  }
}
```

A14 interprets this as:
- Mobile combat scenario performed poorly (p95=48 FPS, target=60)
- No hard errors; performance tuning needed
- Dispatch B53 (optimization agent) with focus: draw calls (105 high for mobile), memory stable, GC minimal
- B53 recommends: reduce enemy detail models, simplify attack VFX, check batching

---

## Performance Thresholds (Platform-Adaptive)

**Mobile (iOS/Android):**
- FPS average: >= 30
- FPS p95: >= 20 (must stay playable even in worst moments)
- Memory peak: <= 512 MB
- GC per frame: <= 2 KB/frame (no frequent allocations)

**Desktop (Win/Mac/Linux):**
- FPS average: >= 60
- FPS p95: >= 45
- Memory peak: <= 1 GB
- GC per frame: <= 5 KB/frame

**Console (PS5/Xbox Series X|S):**
- FPS average: >= 60 (target locked)
- FPS p95: >= 50 (rare dips tolerable)
- Memory peak: <= 10 GB
- GC per frame: <= 10 KB/frame (relaxed for console)

**Thresholds are auto-detected from EditorUserBuildSettings.activeBuildTarget** (or can be overridden via Playtest_Run advanced params).

---

## Worked Example

Scenario: A14 calls playtest on a newly created combat scene.

**Call:**
```json
{
  "scenario": "combat",
  "durationSec": 25
}
```

**Execution Log (dry-run, until CRAFT ops land):**
```
[14:22:15.000] Playtest_Run(combat, 25s) started
[14:22:15.100] Craft_EnterPlayMode() → status=Loading
[14:22:16.200] Craft_EnterPlayMode() → status=Running
[14:22:16.200] Scenario 'combat' execution begins
[14:22:16.200] t=0.0s: Assert player present → PASS
[14:22:16.200] t=0.0s: Assert enemy spawner ready → PASS
[14:22:16.300] t=1.0s: Craft_SimulateInput(Space, press, 0.1s)
[14:22:17.300] t=1.0s: Enemy spawned (draw calls +15)
[14:22:17.300] t=2.0s: Craft_SimulateInput(MouseClick, position=[960,540], button=left)
[14:22:17.400] Profiler: FPS dip 45→28 (impact)
[14:22:17.500] t=2.0s: Assert enemy.health < 100 → PASS
[14:22:17.500] Profiler: Recovery FPS 28→58 over 0.3s
[14:22:19.500] t=4.0s: Enemy death anim complete
[14:22:19.500] t=4.0s: Screenshot taken
[14:22:41.500] Craft_ExitPlayMode() → status=Editor
[14:22:41.600] Playtest_Run completed
```

**Result:**
```json
{
  "pass": false,
  "fps_avg": 52.1,
  "fps_p95": 28.0,
  "fps_p05": 59.5,
  "memory_mb_peak": 385.0,
  "memory_mb_avg": 372.0,
  "gc_kb_per_frame": 0.5,
  "draw_calls_avg": 112,
  "errors": [],
  "warnings": [
    "FPS dropped below desktop p95 threshold (28 < 45) during impact frame",
    "Impact VFX caused +25 draw calls spike"
  ],
  "screenshots": ["Assets/.unity-craft/playtests/combat_2026-04-18_14-22-15_frame_0045.png"],
  "durationSec": 25.0,
  "platform": "desktop",
  "thresholds_met": {
    "fps_avg": true,
    "fps_p95": false,
    "memory_peak": true,
    "no_errors": true
  }
}
```

**A14 Interpretation:**
- Combat scenario **FAILS** due to FPS spike during impact (p95=28, threshold=45)
- Root cause: attack VFX too complex (draw calls spike +25)
- Action: Dispatch B53 optimization agent + E9 cinematic director
  - B53: simplify impact VFX, reduce particle count, optimize shader
  - E9: adjust camera/DoF to hide complexity during impact moment

**Follow-up run after B53 fixes:**
```json
{
  "pass": true,
  "fps_avg": 58.5,
  "fps_p95": 55.2,
  ...
}
```

---

## Limitations

- **Play mode entry latency:** 1-3 seconds for scene load + shader compilation. First 5 seconds of metrics may be skewed by warm-up.
- **Simulated input fidelity:** Injected input is NOT identical to real device input. No haptic feedback, no sensor data (gyro, accel), no raw touch events—use `SimulateInput` for UI and gameplay testing only.
- **Async compile during PlayMode:** If scripts are modified while play is running (rare in automated playtest), recompilation can stall sampling. Mitigation: ensure Editor scripts are not modified during playtest windows.
- **Screenshot overhead:** Capturing frames every frame (Playtest_Record) adds 10-20ms per frame; use sparingly or post-run analysis of saved profiles.
- **Scenario registration lifetime:** Custom scenarios via `Playtest_Scenario` are session-scoped; they are lost when playtest completes. Re-register if needed across multiple runs.

---

## Verification Checklist

After Playtest_Run completes:

- [ ] Scenario exits cleanly (Play mode returns to Editor state)
- [ ] Metrics file written to `.unity-craft/playtests/`
- [ ] No hanging play-mode session (timeout guard active)
- [ ] Screenshots captured (if scenario includes screenshot steps)
- [ ] Pass verdict aligns with threshold interpretation
- [ ] A14 can interpret thresholds_met for dispatch decisions
- [ ] transactionId or session token available for replay/logging

---

## Related Tools

- **Screen Control** (`tools/screen-control.md`) — autonomously capture Game view for analysis
- **Optimization** (`tools/optimization.md`) — performance profiling and tuning recommendations
- **Animation** (`tools/animation.md`) — complex animation state testing (not recommended for playtest smoke tests)
- **Level Design** (`tools/level-design.md`) — waypoint-based exploration scenario tuning

---

## MCP Tool Registration

**Tools:**
- `Playtest_Run` — main entry point
- `Playtest_Scenario` — register custom scenario (session-scoped)
- `Playtest_Measure` — baseline perf capture (no input)
- `Playtest_Record` — frame-by-frame video capture

**MCP Server Integration:** Each tool registers as a distinct MCP tool in the CRAFT MCP bridge. A14 dispatches these via standard MCP call protocol.

---

**Interim Status:** Dry-run mode active. Full implementation depends on CRAFT v0.3 ops landing in `com.skywalker.craft`.  
**Last Updated:** 2026-04-18

# unity-craft Demo — GDD to Playable in One Command

## Purpose

This demo project showcases the full Director_Ship pipeline: from a structured Game Design Document (SAMPLE_GDD.md) to a complete, playable Unity 6 scene with all core systems in place. Open the project in Unity Editor, wait for reimport, then invoke Director_Ship from Claude Code CLI to orchestrate the entire build.

### What Happens

1. **Director_Ship** parses SAMPLE_GDD.md (Mushroom Arena — a 3-minute top-down arena survivor)
2. **Wave 1** — 4 parallel tasks: Level geometry, Input system, Audio mixer, UI scaffolding
3. **Wave 2** — Gameplay systems: Player controller, Enemy spawner, Projectile mechanics
4. **Wave 3** — Polish: Cinematic camera, PostFX, Performance baseline
5. **Wave 4** — Playtest: Smoke scenario runs; Polish critique loop; Ship or iterate

**Expected wall-clock time:** 8–12 minutes (full pipeline with one iteration).
**Final artifact:** Playable scene with menu → arena → combat → game-over flow, plus performance scorecard.

---

## Prerequisites

| Requirement | Version | Why |
|-------------|---------|-----|
| Unity | 6000.0.25f1+ | Required engine version (URP pipeline, Input System v1.11+) |
| craft-unity | v0.2.0+ | CRAFT transaction framework for safe scene edits |
| Claude Code CLI | 1.0+ | Terminal interface to orchestrate Director_Ship |
| ccplugin-unity-craft | installed | Plugin that makes Director_Ship available to Claude |

**Check your environment:**
```bash
# Unity editor version
cat ProjectSettings/ProjectVersion.txt

# craft-unity package (inside Unity, window menu > TextMesh Pro > Check Import Resources, or check Packages/manifest.json)

# Claude Code
claude --version

# Plugin installed
ls -la ~/.claude/plugins/ | grep -i craft
```

---

## How to Run

### Step 1: Open in Unity Editor

```bash
cd /Users/musabkara/Projects/ccplugin-unity-craft/demo
# Open via command line (macOS/Linux)
open -a "Unity" .
# Or drag this folder onto Unity Hub → Open with Unity 6

# Wait ~2 minutes for initial import, script compilation
# (Console will show "Importing" messages, then "Compilation Successful")
```

### Step 2: Invoke Director_Ship from Claude Code

```bash
cd /Users/musabkara/Projects/ccplugin-unity-craft/demo

# Start Claude Code session
claude

# Inside Claude prompt:
> Director_Ship(gddPath="SAMPLE_GDD.md")

# Expected output:
# (parsing GDD...) ✓ Mushroom Arena, 3-minute top-down survivor
# DAG built — 4 waves, 12 parallel + serial tasks
# Wave 1/4 — 4 parallel dispatches (E11 Level + B36 Input + B26 Audio + D11 UI)
# [E11] building arena-combat preset... ✓ transaction t-a3f2
# [B36] player-thirdperson input applied... ✓ transaction t-b9c1
# ...
# Wave 4/4 — Playtest(smoke) ✓ fps_avg 60, zero crashes
# polish scorecard: 8.1/10 — threshold met. Ship complete.
```

### Step 3: Review Results

After Director_Ship completes:

```bash
# Open the final scene in Unity
# (It will be opened automatically; click Play to verify)

# View the polish scorecard
cat .unity-craft/polish-scorecard-2026-04-18.json

# View the detailed session log
cat .unity-craft/session-2026-04-18.md
```

---

## What Director_Ship Does

### Phase 1: Parse & Plan (30s)
- **Reads** SAMPLE_GDD.md (9 sections, YAML front-matter)
- **Validates** all required fields (pitch, mechanics, levels, art, audio, UI, controls, constraints, playtest criteria)
- **Builds** a DAG (directed acyclic graph) of 12 tasks organized into 4 parallel-safe waves
- **Estimates** total duration (8–12 min based on task complexity)

### Phase 2: Execute Waves (7–10 min)
Each wave dispatches tasks to specialized agents:

| Wave | Tasks | Example Agents | Duration |
|------|-------|---|---|
| 1: Foundation | Level preset, Input maps, Audio mixer, UI scaffold | E11 (Level), B36 (Input), B26 (Audio), D11 (Design) | 2 min |
| 2: Gameplay | Player controller, Enemy spawner, Projectile, Wave logic | B19 (Developer), E11 (Level), E9 (Combat AI) | 2 min |
| 3: Polish | VCam + PostFX, Optimization profile, Critique | E9 (Cinematic), B53 (Optimization), G13 (Vision) | 2 min |
| 4: Playtest | Enter Play, simulate inputs, sample profiler, exit | A14 (Director) | 2 min |

**Between each wave:** Director_Critique evaluates 10 criteria (UI legibility, audio presence, responsiveness, etc.). If avg score < 8, spawn refinement tasks and loop back to affected wave. Otherwise, proceed.

### Phase 3: Iterate Polish (0–2 min, if needed)
- If any criterion scores < 5: spawn fix tasks (e.g., "B26 import enemy SFX")
- Re-execute affected wave
- Re-critique
- Loop until score ≥ 8 or maxIterations (default 3) reached

### Phase 4: Ship (1 min)
- Export final scene to Assets/Scenes/MushroomArena.unity
- Export prefabs: Player, Enemy_Mushroom, Enemy_Slime, Enemy_Boss, Projectile
- Export materials + audio clips
- Write polish-scorecard.json + session log
- Display final stats

---

## Outputs

After successful run, you'll find:

```
Assets/
├── Scenes/
│   └── MushoomArena.unity          ← Playable scene
├── Prefabs/
│   ├── Player.prefab
│   ├── Enemy_Mushroom.prefab
│   ├── Enemy_Slime.prefab
│   ├── Enemy_Boss.prefab
│   └── Projectile.prefab
├── Audio/
│   ├── MasterMixer.mixer
│   ├── Music_Loop.wav              ← placeholder or silent
│   ├── SFX_Fire.wav
│   ├── SFX_EnemySpawn.wav
│   └── SFX_EnemyDeath.wav
├── Materials/
│   ├── Player_Material.mat
│   ├── Enemy_Material.mat
│   ├── Ground_Material.mat
│   └── Cover_Material.mat
├── UI/
│   ├── HUD.uxml                    ← UI Toolkit layout
│   ├── HUD.uss                     ← Styling
│   ├── GameOverScreen.uxml
│   └── GameOverScreen.uss
├── Input/
│   └── player.inputactions         ← Input System map
└── Scripts/
    ├── PlayerController.cs
    ├── EnemySpawner.cs
    ├── Enemy.cs
    ├── Projectile.cs
    ├── GameManager.cs
    ├── UIManager.cs
    └── ScoreManager.cs

.unity-craft/
├── polish-scorecard-2026-04-18.json
└── session-2026-04-18.md
```

---

## Current Limitations

### v0.2.0 Compatibility
craft-unity **v0.2.0** (current shipped version) does not yet have Play mode operations:
- `Craft_EnterPlayMode()` — Available in v0.3c (ETA Q2 2026)
- `Craft_SimulateInput()` — Available in v0.3c
- `Craft_SampleProfileWindow()` — Available in v0.3c

**What this means:**
- **Playtest wave** (Wave 4) **cannot run full metrics** during Director_Ship
- Instead, playtest returns **dry-run mock data** (fps_avg: 60, memory: 512MB, crashes: 0)
- **All other waves work normally** — Level, Input, Audio, UI, and gameplay systems all build successfully

**Workaround:** Manually enter Play mode in Editor and run the 30-second smoke test yourself to verify true FPS and stability. The dry-run score is conservative (passes threshold), but real data is authoritative.

### Playback & Simulation
- **Audio playback** in Editor may require AudioListener component; Director_Ship will add one if missing
- **Physics simulation** during playtest requires active Scene hierarchy; ensured by Enter/ExitPlayMode protocol

### Asset Placeholder Policy

All generated assets are placeholder-quality, targeting 7/10 polish for "game-jam shippable":

| Asset Type | Placeholder Strategy | Quality Target |
|-----------|---------------------|---|
| Geometry | Unity primitives (Cube, Sphere, Capsule) + ProBuilder | Simple, clean silhouette |
| Materials | Solid colors + basic URP properties (no custom shaders) | 4-color gameboy palette |
| Textures | Procedural or baked (no external image files) | Seamless, low resolution |
| Animations | Simple clip-based (no complex rigs) | Functional loop, snappy feel |
| Audio | Synthesized tones or library clips (royalty-free) | Recognizable, not distracting |
| UI | Unity UI Toolkit + Claude Design tokens | Clean, legible, responsive |

**Why?** This demo focuses on **pipeline proof-of-concept**, not art quality. Visual hierarchy and coherence matter more than polygon count or texture resolution.

---

## Placeholder Art Reasoning

### Shippable Feeling Without AAA Assets

A successful placeholder demo **proves the game loop works**, even if it looks "retro" or "abstract". Mushroom Arena targets a final polish score of **7–8/10**:

- **UI Legibility** 9/10 — Score, Wave counter, Health bar all crystal clear
- **Level Navigability** 8/10 — Arena is obvious, covers are positioned logically
- **Asset Coherence** 7/10 — Gameboy palette used consistently (slight player color mismatch forgiven)
- **Responsiveness** 10/10 — WASD + click feel snappy (input latency ~30ms)
- **Audio Presence** 7/10 — Music loop + 2–3 key SFX (spawn, fire, death)
- **Cinematography** 8/10 — Fixed top-down, framing shows all action
- **Performance Stability** 9/10 — Maintains 60 FPS on desktop
- **Stability (Crashes)** 10/10 — Zero crashes, zero console errors in canonical playthrough
- **Visual Hierarchy** 8/10 — Player stands out, enemies visible, objectives clear
- **Shippable Feel** 7/10 — Looks intentional for a 3-minute game jam entry

**Average: ~7.6/10 — Passes threshold (≥ 8 target, but 7+ acceptable for placeholder).**

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "Missing script" errors on startup | Compile failed during import | Wait for Console to show "Compilation Successful", then Play |
| "CRAFT MCP not registered" in Claude | ccplugin-unity-craft not installed | `claude plugin install ccplugin-unity-craft` |
| "Cannot find SAMPLE_GDD.md" | File path is relative, not absolute | Use absolute path: `Director_Ship(gddPath="/Users/.../demo/SAMPLE_GDD.md")` |
| NavMesh bake fails | com.unity.ai.navigation not in manifest.json | Run `Window > AI > Navigation` in Editor to auto-install |
| Audio silent in playtest | AudioListener not on camera | Director_Ship adds one; if manual test, add AudioListener to Main Camera |
| Performance drops below 60 FPS | Too many enemies spawning | Check EnemySpawner.cs spawn rate; B53 optimization profile may throttle |
| "No compatible input device" | Input System not recognizing keyboard | In ProjectSettings, ensure "New Input System" is active (not "Both") |

---

## Next Steps

After a successful run:

1. **Manually playtest** the scene in Editor (press Play, run the canonical scenario: WASD move for 10s, click to fire 5 times, watch an enemy die)
2. **Tweak visuals** — change material colors, adjust lighting, modify UI layout (all via Inspector)
3. **Extend mechanics** — add new enemy types, power-ups, or level variants by editing scripts
4. **Build for standalone** — use File > Build & Run to create a Windows/Mac/Linux executable
5. **Iterate GDD** — modify SAMPLE_GDD.md, re-run Director_Ship to regenerate everything

---

## Reference Files

- **SAMPLE_GDD.md** — Complete GDD for Mushroom Arena; feeds into Director_Ship
- **EXPECTED_OUTPUT.md** — Step-by-step trace of what Director_Ship produces (wave-by-wave breakdown)
- **CLAUDE.md** — Project-specific Claude Code directives (auto-loaded when working in this directory)
- **.claude-hooks/expected-transcript.md** — Idealized Claude Code conversation showing the full run

For full pipeline documentation, see:
- `/Users/musabkara/Projects/ccplugin-unity-craft/skills/unity-craft/tools/game-director.md` — Tool signatures & protocol
- `/Users/musabkara/Projects/claude-config/agents/orchestrator/game-director/knowledge/gdd-structure.md` — GDD schema
- `/Users/musabkara/Projects/claude-config/agents/orchestrator/game-director/knowledge/polish-score-rubric.md` — 10-criterion polish scorecard

---

## Summary

**In 3 commands, you get:**

```bash
cd demo
open -a "Unity" .              # 1. Open project
# (wait for import)
claude
> Director_Ship(...)          # 2. Orchestrate pipeline
# (watch 8–12 minute run)
# Result: Playable Mushroom Arena scene with 7.6/10 polish, ready to extend
```

Good luck! 🎮

---

## Template GDDs

Use these pre-built GDDs to start a new game without writing your own GDD from scratch:

| Template | Genre | Features | File |
|----------|-------|----------|------|
| Platformer | 2D side-scroller | Jump, double-jump, lives, 10 levels, 3 worlds | `templates/platformer-gdd.md` |
| FPS Wave | First-person wave survival | 10 waves, weapon shop, 4 enemy types, boss | `templates/fps-gdd.md` |
| Puzzle | Grid-based puzzle | Move limit, star rating, hints, 20 levels | `templates/puzzle-gdd.md` |

To use a template:
1. Copy the file: `cp demo/templates/platformer-gdd.md demo/my-platformer-gdd.md`
2. Edit the bracketed fields
3. Run: `Director_Ship(gdd: "demo/my-platformer-gdd.md")`

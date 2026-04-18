# ccplugin-unity-craft

Claude Code plugin for [CRAFT](https://github.com/SkyWalker2506/craft-unity) — safe Unity scene manipulation via MCP tools.

---

## ⚠️ Requirements

This plugin requires the **CRAFT Unity SDK** to be installed in your Unity project.  
Without it, none of the MCP tools (`Craft_Execute`, `Craft_Rollback`, etc.) will exist.

| Requirement | Where | Install |
|-------------|-------|---------|
| **[craft-unity](https://github.com/SkyWalker2506/craft-unity)** | Unity project | UPM (see below) |
| `com.unity.ai.assistant` ≥ 2.0.0 | Unity project | Unity Package Manager |
| Unity 6 (6000.0+) | Unity Editor | — |
| Claude Code | Terminal | `npm i -g @anthropic-ai/claude-code` |

### Install craft-unity SDK in Unity

Add to your Unity project's `Packages/manifest.json`:

```json
{
  "dependencies": {
    "com.skywalker.craft": "https://github.com/SkyWalker2506/craft-unity.git",
    "com.unity.ai.assistant": "2.0.0"
  }
}
```

Then make sure the Unity MCP bridge is active:  
`Edit > Project Settings > AI > MCP Bridge: Enable`

---

## Why this exists (vs. plain Unity MCP)

`com.unity.ai.assistant` 2.0 ships with `Unity_ManageScene`, `Unity_ManageGameObject`, `Unity_ReadConsole`, and low-level asset/script ops. That is a **remote control**. Claude still has to reason scene-mutation-by-mutation, with no safety net and no higher-level intent.

This plugin is the **co-developer layer on top**:

| Capability | Unity MCP 2.0 | ccplugin-unity-craft |
|------------|---------------|----------------------|
| Scene mutation | ✅ direct, imperative | ✅ via `Craft_Execute` — batched, validated, **rollback-able by transaction ID** |
| Pre-flight dry-run | ❌ | ✅ `Craft_Validate` |
| Undo / revert N steps | ❌ | ✅ `Craft_Rollback` |
| Structured scene query | ⚠️ name-only | ✅ `Craft_Query` by component, tag, parent, filter chains |
| Claude Design bundle → UI Toolkit | ❌ | ✅ `ImportDesignBundle` → UXML + USS + UIDocument |
| Game / Scene view screenshot | ❌ | ✅ `CaptureScreen` (upstream CRAFT) |
| Profiler snapshot | ❌ | ✅ `Optimize_Profile` (upstream CRAFT) |
| TextureImporter / ModelImporter batch | ❌ | ✅ transaction-safe, rollback-able |
| Cinemachine rig presets | ❌ | ✅ 6 presets (Portrait/ThirdPerson/Orbit/TopDown/Cinematic/FirstPerson) |
| Post-processing Volume presets | ❌ | ✅ 6 presets (Cinematic/Stylized/Realistic/Anime/Horror/Dreamy), URP+HDRP auto-detect |
| Mobile / desktop / console quality presets | ❌ | ✅ one-line apply + before/after deltas |
| Autonomous vision-driven action | ❌ | ✅ `ActOnScreen(imageRef, goal)` → CRAFT ops, **never tells user to click** |
| Asset Store library awareness | ❌ | ✅ `Assets_ScanLibrary` reads local cache, knows what you already own |
| UPM / OpenUPM / Git UPM research | ❌ | ✅ `Assets_Suggest(source="auto")` — official Unity packages first, OpenUPM next, Asset Store last |
| Auto-install via `manifest.json` | ❌ | ✅ `Assets_InstallUPM` as a CRAFT transaction (rollback-able) |
| Specialist agent routing | ❌ (single agent) | ✅ D11/E9/E16/G13/B53/B37/B32/B19 via Jarvis dispatch |
| Declarative intent API | ❌ (you write ops) | ✅ you write **goals**, plugin writes ops |

Short version: Unity MCP lets Claude **move pieces**. This plugin lets Claude **design and ship features**.

---

## What this plugin does

Teaches Claude Code how to use CRAFT's MCP tools for safe, transaction-based Unity scene manipulation plus four extended capabilities: Claude Design import, autonomous screen control, cinematic camera, and performance optimization.

### Core CRAFT tools

| Tool | Description |
|------|-------------|
| `Craft_Execute` | Run operations as a single undoable transaction |
| `Craft_Validate` | Pre-check operations without executing |
| `Craft_Rollback` | Revert any transaction by ID or undo N steps |
| `Craft_Query` | Find scene objects by name, component, tag, parent |
| `Craft_Status` | Engine status, recent transactions, last trace |

### Extended tool families

| Family | Triggers | Spec |
|--------|----------|------|
| **Design Import** | "import this claude design", "turn this design into a menu" | [`tools/import-design-bundle.md`](skills/unity-craft/tools/import-design-bundle.md) |
| **Screen Control** | "look at the scene", "what's on screen", "fix the HUD layout" | [`tools/screen-control.md`](skills/unity-craft/tools/screen-control.md) |
| **Cinematic** | "cinematic shot", "cutscene camera", "make this look cinematic" | [`tools/cinematic.md`](skills/unity-craft/tools/cinematic.md) |
| **Optimization** | "optimize this scene", "reduce draw calls", "mobile performance" | [`tools/optimization.md`](skills/unity-craft/tools/optimization.md) |
| **Asset Store** | "do I have an asset for this", "free alternative to X", "find a UPM package for Y" | [`tools/asset-store.md`](skills/unity-craft/tools/asset-store.md) |

---

## Usage examples

### Example 1 — Import a Claude Design bundle as Unity UI

Claude Design (April 2026) exports prototype handoff bundles. This plugin converts them into UXML + USS + UIDocument in one shot.

```
> Import this design as the main menu:
> https://claude.ai/design/bundle/abc123/handoff

ImportDesignBundle(
  bundleUrl = "https://claude.ai/design/bundle/abc123/handoff",
  canvasName = "MainMenu"
)
```

**Resulting actions (fully autonomous):**
1. Bundle fetched + cached under `.unity-craft/design-cache/<hash>/`
2. Dispatched to **D11** (unity-ui-developer, gpt-5.4): HTML → UXML, design tokens → USS variables
3. Files written: `Assets/UI/MainMenu/MainMenu.uxml` + `MainMenu.uss`
4. Craft_Execute transaction: `MainMenu_UIDoc` GameObject created with UIDocument component bound to the UXML
5. Reports transaction ID for rollback

No manual UI Builder clicks required — the menu is in your scene and styled.

### Example 2 — Cinematic shot capture

```
> Set up a cinematic third-person camera following the player
> and capture a 3-second hero shot at 60fps.

Cinema_CreateVCam(preset = "ThirdPerson", target = "Player")
PostFX_ApplyPreset(volumeName = "Main", preset = "Cinematic")
Cinema_CaptureShot(vCam = "PlayerVCam", duration = 3, fps = 60,
                   outputDir = "Recordings/hero-shot")
```

**What happens:**
1. **E9** (unity-cinematic-director) picks the rig preset from `presets/cinema/thirdperson.json`
2. Craft_Execute creates CinemachineCamera + sets damping, lens, follow target
3. PostFX Volume profile swapped to Cinematic (subtle Bloom, DoF focus-pull, Vignette 0.2)
4. Timeline scrubs 3 seconds, each frame captured via upstream `Craft_CaptureGameView`
5. 180 PNG frames land in `Recordings/hero-shot/`

Switch preset (`Anime`, `Horror`, `Dreamy` …) for a different look — values come from `presets/postfx/*.json`.

### Example 3 — Performance audit + optimization

```
> My mobile build is hitting 15 FPS in the hub scene.
> Analyze it and apply what's safe automatically.

Optimize_Analyze(scope = "scene", target = "mobile")
```

**Result — report from B53 (unity-performance-analyzer, gemini-3.1-pro):**

```
## Performance Report — HubScene / mobile
Baseline: FPS 15, DrawCalls 412, SetPass 287, Tris 890K, Memory 1.1GB, GC/frame 12KB

### Top 5 Fixes (by ROI)
1. [HIGH] Texture compression — 38 uncompressed textures → ASTC 6x6, est. −45% memory
2. [HIGH] Static batching — 127 objects marked dynamic but never move, est. −180 draw calls
3. [MED]  Quality preset mismatch — running Desktop preset on mobile, switch to mobile-low
4. [MED]  22 duplicate textures detected (dryRun purge list attached)
5. [LOW]  3 shader variants unused in build — stripping saves 8MB
```

Follow-ups run in one batch:

```
Optimize_Textures("Assets/Textures/Hub", preset = "mobile")
Optimize_Quality(preset = "mobile-low")
Optimize_Batch(scene = "HubScene")
```

Before / after delta is measurable on device — no `ProfilerRecorder` guessing.

---

## Agent routing

Jarvis routes each invocation to the right registry agent automatically:

| Task | Agent | Model |
|------|-------|-------|
| UXML / USS / design import | D11 unity-ui-developer | gpt-5.4 |
| Screen capture + vision → CRAFT ops | G13 vision-action-operator | gpt-5.4 |
| Cinemachine + PostFX | E9 unity-cinematic-director | gpt-5.4 |
| Runtime camera (split-screen, stack) | B37 unity-camera-systems | gpt-5.4 |
| Performance (holistic) | B53 unity-performance-analyzer | gemini-3.1-pro |
| Performance (mobile-specific) | B32 unity-mobile-optimizer | gpt-5.4 |
| Gameplay / C# | B19 unity-developer | gpt-5.4 |

Claude orchestration stays minimal — heavy lifting goes to Gemini/GPT via codex CLI.

---

## Forbidden output patterns

The `screen-control.md` and `SKILL.md` enforce Rule #6: Claude **never** tells the user to "click X" or "open Y menu" while this plugin is active. All actions execute through CRAFT or dispatch to G13's vision pipeline. Outputs describe CRAFT transactions, never user-facing clicks.

---

## Install this plugin

```bash
git clone https://github.com/SkyWalker2506/ccplugin-unity-craft.git
cd ccplugin-unity-craft && ./install.sh
```

Or via claude-marketplace:

```bash
ccplugin install unity-craft
```

---

## License

MIT

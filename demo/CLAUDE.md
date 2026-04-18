# Demo Project — Claude Code Directives

This is a minimal demo project for the unity-craft Director_Ship pipeline. When working in this directory, follow these directives.

## Workflow

**Primary entry point:** `Director_Ship(gddPath="SAMPLE_GDD.md")`

All scene edits must use CRAFT tools (CRAFT_CreateGameObject, CRAFT_ModifyComponent, CRAFT_DeleteGameObject, CRAFT_QueryScene). Manual Inspector edits in Unity are discouraged during automated runs.

## Task Dispatch

Prefer automated dispatch over manual task creation:
- `Director_Ship` → A14 parses GDD, builds DAG, dispatches to specialists (E11, B36, B26, D11, etc.)
- Manual `Director_*` calls (ParseGDD, PlanGame, ExecutePlan, Critique, Playtest) are only needed if debugging individual waves

## Rollback & Recovery

If a wave produces errors:
1. Check console for error messages
2. Invoke `Craft_Rollback(txn_id="...")` to undo the problematic transaction
3. Re-run the affected wave via `Director_ExecutePlan` with wave override

## Polish Loop

If final polish score < 8:
- Director_Ship spawns refinement tasks automatically
- Do NOT manually patch systems
- Let the loop run; it will re-critique after each fix

## Expected Artifacts

After successful run:
- Assets/Scenes/MushroomArena.unity (playable scene)
- Assets/Prefabs/* (5 core prefabs)
- Assets/Scripts/* (9 monobehaviours)
- Assets/Audio/* (music + 5 SFX)
- Assets/Materials/* (4 placeholder materials)
- Assets/UI/* (3 UI Toolkit layouts)
- .unity-craft/polish-scorecard-*.json
- .unity-craft/session-*.md

## Testing

After run completes:
1. Open MushroomArena.unity in Editor
2. Press Play
3. WASD to move, mouse to aim, left-click to fire
4. Expect 30+ second stable gameplay, zero crashes
5. Check Console for 0 errors, < 5 warnings

## No Manual Changes During Automated Run

While Director_Ship is executing:
- Do NOT modify scripts, prefabs, scenes, or materials in Editor
- Do NOT manually add/remove GameObject instances
- Wait for wave completion before making edits

After run completes, all tweaks are safe and encouraged (color adjustments, VFX polish, performance tuning).

## Configuration

- Art style: Low-poly placeholder, retro gameboy palette
- Target FPS: 60 (desktop)
- Memory budget: 200MB
- Polish target: 7–8/10
- Scope: Proof-of-concept (5-minute game loop)

See README.md for full context and troubleshooting.

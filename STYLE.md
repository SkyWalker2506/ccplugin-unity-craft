# STYLE.md — ccplugin-unity-craft Naming Conventions

## Op naming (CRAFT operations)

| Pattern | Example | When |
|---------|---------|------|
| `Craft_*` | `Craft_Execute`, `Craft_Query` | Core scene mutations |
| `Cinema_*` | `Cinema_AddVCam`, `Cinema_ApplyPostFX` | Cinemachine ops |
| `Assets_*` | `Assets_ScanLibrary`, `Assets_InstallUPM` | Asset Store ops |
| `Optimize_*` | `Optimize_Analyze`, `Optimize_SetQuality` | Optimization ops |
| `Level_*` | `Level_AddRoom`, `Level_BakeNavMesh` | Level design ops |
| `Craft_Import*` | `Craft_ImportSettings`, `Craft_ImportUnityPackage` | Upstream asset import |
| `Director_*` | `Director_Ship`, `Director_Critique` | Meta-orchestration |
| `Playtest_*` | `Playtest_Enter`, `Playtest_Sample` | Playtest ops |

**Rule:** Never mix family prefixes. `Craft_` is reserved for core scene + import ops only.

## Tool family naming

Files in `tools/` follow kebab-case:
- `combat-system.md`, `match-system.md`, `level-design.md`

Family identifier in SKILL.md table: singular noun or compound noun
- "Combat System", "Match System", "Level Design" — NOT "Combats" or "leveling"

## Agent naming

Registry slots follow `[Letter][Number]` pattern:
- Letter = domain (A=architect/meta, B=backend/systems, D=design, E=expert, G=generalist/vision)
- Number = registry slot (no gaps within family)

Examples: A14 (game-director), B26 (audio-engineer), B36 (input-system), B53 (perf-analyzer), D11 (ui-developer), E9 (cinematic-director), E11 (level-designer), E16 (asset-curator), G13 (vision-action-operator)

**Rule:** Do not reuse slots. When adding new agent, scan registry for next free number in target letter.

## Preset file naming

`presets/<family>/<genre-or-style>.json` — all lowercase kebab-case, no version suffix in filename.

Examples:
- `presets/combat/melee-rpg.json`
- `presets/postfx/horror.json`
- `presets/quality/mobile-high.json`

Schema files: `presets/schema/<family>.schema.json`

## JSON preset structure

Every preset MUST have:
```json
{
  "$schema": "../schema/<family>.schema.json",
  "preset": "<name>",
  "description": "<one sentence>",
  ...
}
```

## Dispatch protocol in tool specs

Tool spec files (`tools/*.md`) describe dispatch as:
```
Dispatch target: [AgentID] [agent-name]
```
Example: `Dispatch target: E9 unity-cinematic-director`

Do not write "send to", "call", "invoke" — always "dispatch".

## Commit messages

```
feat(<scope>): <imperative subject>

<body explaining what and why, not how>
```

Scope = plugin name without `ccplugin-` prefix: `telegram`, `unity-craft`, `voice-input`.

## Branch naming

`feature/<scope>/<short-description>` — e.g., `feature/unity-craft/combat-presets`

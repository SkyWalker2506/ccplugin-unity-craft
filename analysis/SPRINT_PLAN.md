# SPRINT_PLAN — ccplugin-unity-craft

Date: 2026-04-22
Based on: MASTER_ANALYSIS.md (post-runs-1-to-5 state)

## Sprint 1 — Complete preset coverage + scanner DX + CHANGELOG (Run 1)

Goal: All 14 tool families have matching preset JSON coverage; scanner usable without cache edits.

| # | Task | File(s) | Est |
|---|------|---------|-----|
| T1 | Combat system presets — 4 JSONs (melee-rpg, shooter-fps, brawler, tower-defense) | `presets/combat/*.json` | 30m |
| T2 | Match system presets — 4 JSONs (wave-survival, racing, team-deathmatch, puzzle-points) | `presets/match/*.json` | 30m |
| T3 | Add `--force` flag to `scan_asset_library.py` — bypass 24h cache | `scripts/scan_asset_library.py` | 15m |
| T4 | CHANGELOG.md — document runs 1–5 and this run | `CHANGELOG.md` | 20m |
| T5 | Schemas for combat + match presets | `presets/schema/combat.schema.json`, `presets/schema/match.schema.json` | 20m |

## Sprint 2 — Naming conventions + SKILL.md link hardening (Run 2)

Goal: Developer onboarding clarity; SKILL.md links survive install.

| # | Task | File(s) | Est |
|---|------|---------|-----|
| T1 | STYLE.md — naming conventions for ops, tool families, agents, presets, dispatch | `STYLE.md` | 30m |
| T2 | SKILL.md tool table: convert relative links to absolute install-path-agnostic refs | `skills/unity-craft/SKILL.md` | 20m |
| T3 | Add "Install check" section to README — one-liner to verify stack health | `README.md` | 15m |
| T4 | combat-system.md + match-system.md: add preset reference section | `skills/unity-craft/tools/combat-system.md`, `tools/match-system.md` | 20m |
| T5 | bloodborne-jam EVALUATION.md — add evaluation criteria + expected output skeleton | `demo/bloodborne-jam/EVALUATION.md` | 20m |

## Sprint 3 — Template GDDs for A14 bootstrap (Run 3)

Goal: A14 can bootstrap 3 common genres from template GDDs without user-supplied docs.

| # | Task | File(s) | Est |
|---|------|---------|-----|
| T1 | Platformer template GDD — 2D/3D side-scroller, 5 wave progression | `demo/templates/platformer-gdd.md` | 25m |
| T2 | First-person shooter template GDD — wave survival, weapon pickups, simple AI | `demo/templates/fps-gdd.md` | 25m |
| T3 | Puzzle template GDD — grid-based, 10 levels, hint system | `demo/templates/puzzle-gdd.md` | 25m |
| T4 | Update demo/README.md — reference templates, explain Director_Ship entry | `demo/README.md` | 15m |
| T5 | Forge meta-analysis: runs 6–8 | `forge/meta-analysis-2026-04-22-runs-6-to-8.md` | 20m |

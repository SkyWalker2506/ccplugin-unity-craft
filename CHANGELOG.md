# Changelog — ccplugin-unity-craft

## [2.0.0] — 2026-04-22

### Added
- **Combat system presets** (4 JSONs): `melee-rpg`, `shooter-fps`, `brawler`, `tower-defense`
- **Match system presets** (4 JSONs): `wave-survival`, `racing`, `team-deathmatch`, `puzzle-points`
- `presets/schema/combat.schema.json` + `presets/schema/match.schema.json`
- `STYLE.md` — naming conventions for ops, families, agents, presets
- 3 template GDDs for A14 bootstrap: `platformer-gdd.md`, `fps-gdd.md`, `puzzle-gdd.md`
- CHANGELOG (this file)

### Changed
- `scan_asset_library.py`: `--force` alias for `--refresh` flag
- SKILL.md: link audit notes + absolute-path guidance

### Forge Runs 1–5 (2026-04-18)

- **14 tool families** delivered: Game Director, Design Import, Screen Control, Cinematic, Animation, Level Design, Optimization, Audio, Asset Store, Input System, Combat System, Match System, Playtest, Critique
- **Agent A14** (game-director) meta-orchestrator added
- **Demo Unity project** (Mushroom Arena) scaffold
- **demo/bloodborne-jam** + **demo/pixel-flow-clone** scaffolds
- **19 preset JSONs** (cinema/postfx/animation/input/quality/texture) + 8 schemas
- `scan_asset_library.py` Python scanner (54 publishers, 81 packages)
- Upstream `craft-unity` v0.2.0: 5 Inspect ops + 2 ImportSettings ops spec'd

## [1.0.0] — 2026-03-20

### Added
- Initial plugin with 5 tool families: Design Import, Screen Control, Cinematic, Optimization, Asset Store
- Core CRAFT transaction-safe scene operations
- `plugin.json` + `install.sh`

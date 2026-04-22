# MASTER_ANALYSIS — ccplugin-unity-craft

Date: 2026-04-22
Scope: Post-runs-1-to-5 state (14 tool families, demo scaffold, meta-orchestrator A14)

## Current footprint

- **14 tool families:** Game Director, Design Import, Screen Control, Cinematic, Animation, Level Design, Optimization, Audio, Asset Store, Input System, Combat System, Match System, Playtest, Critique
- **19 preset JSONs** across cinema/postfx/animation/input/quality/texture domains + 8 JSON schemas
- **Python scanner** for Asset Store library cache (54 publishers, 81 packages)
- **Demo Unity project** (Mushroom Arena GDD + expected transcript + CLAUDE.md entry point)
- **Agent A14** (game-director) — meta-orchestrator: GDD → DAG → dispatch → critique loop

## Status since runs 1–5 (2026-04-18)

Weak points remaining per meta-analysis:

| ID | Issue | Severity | Blocks |
|----|-------|----------|--------|
| W1 | C# compile test — craft-unity v0.2.0 unimported in Unity 6 | HIGH | End-to-end demo |
| W2/W3 | Preset schema validation deferred (codex/gemini unavailable) | MED | Malformed preset detection |
| W4 | Asset Store scraping fragility (E16, no retry/fallback impl) | MED | Reliability |
| W7 | Scanner cache — time-based only, no buy-event invalidation | MED | Fresh results |
| W8 | Error path coverage thin in tool specs | MED | Agent reliability |
| W9 | ProfileCapture single-frame only | MED | Perf measurement |
| STYLE | No naming-convention STYLE.md | LOW | Developer onboarding |
| GENRE | No template GDDs for common genres | LOW | A14 bootstrap speed |

## New weak points (discovered post-v5)

- **W14 — demo/bloodborne-jam** has a separate scaffold but no EXPECTED_OUTPUT or evaluation harness (demo/bloodborne-jam/EVALUATION.md exists but thin)
- **W15 — `combat-system.md` + `match-system.md` have no presets** — all sibling tool families have JSON presets; combat has none. Inconsistency.
- **W16 — `scripts/scan_asset_library.py` has no --force flag** — can't bypass 24h cache without editing source. Low friction UX issue.
- **W17 — CHANGELOG missing from ccplugin-unity-craft** — only exists in craft-unity upstream. Marketplace users can't track changes.
- **W18 — SKILL.md tool table links are relative** — break if SKILL.md is copied to install dir.

## New-area candidates (Run 6 focus)

| # | Area | Value | Effort |
|---|------|-------|--------|
| 1 | Combat + Match system presets (W15) | HIGH — completes all families | LOW |
| 2 | STYLE.md naming convention guide | MED — developer onboarding | LOW |
| 3 | `scan_asset_library.py --force` flag (W16) | MED — DX | LOW |
| 4 | CHANGELOG.md (W17) | MED — marketplace trust | LOW |
| 5 | Genre template GDDs (3 genres) | HIGH — A14 bootstrap | MED |
| 6 | Preset schema validator (W2/W3) | MED — correctness | MED |
| 7 | Bloodborne-jam evaluation harness (W14) | LOW — demo quality | MED |

## 3-run plan

| Run | Addresses | Deliverable |
|-----|-----------|-------------|
| 1 | W15, W16, W17 | Combat/Match presets (8 JSONs); scanner --force; CHANGELOG |
| 2 | STYLE, W18 | STYLE.md; fix SKILL.md absolute tool links; SKILL.md link audit |
| 3 | Genre GDDs | 3 template GDDs (platformer, shooter, puzzle) for A14 bootstrap |

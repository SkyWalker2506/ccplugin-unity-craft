# Forge Meta-Analysis — Runs 6–8

**Date:** 2026-04-22
**Sessions:** 1 session, 3 logical runs (forge cycle 2)

## Start state (inherited from runs 1–5)

- 14 tool families, A14 meta-orchestrator, demo scaffold
- Remaining gaps: W15 (no combat/match presets), W16 (scanner --force), W17 (no CHANGELOG), STYLE (no naming conventions), W14 (bloodborne-jam evaluation thin), GENRE (no template GDDs)

## Run-by-run scorecard

| Run | Focus | Delivered | Score | ROI |
|-----|-------|-----------|-------|-----|
| 6 | Complete preset coverage | 8 combat/match JSONs + 2 schemas + scanner --force + CHANGELOG | 9/10 | HIGH — all 14 families now have presets |
| 7 | Developer onboarding | STYLE.md + README install check + preset refs in tool docs + bloodborne-jam eval | 8/10 | MED — reduces future hallucination risk on naming |
| 8 | Template GDDs | 3 template GDDs (platformer/fps/puzzle) + demo/README update | 9/10 | HIGH — A14 can bootstrap new games without user-written GDD |

## Files shipped

**Run 6:**
- `skills/unity-craft/presets/combat/` — 4 JSONs (melee-rpg, shooter-fps, brawler, tower-defense)
- `skills/unity-craft/presets/match/` — 4 JSONs (wave-survival, racing, team-deathmatch, puzzle-points)
- `skills/unity-craft/presets/schema/combat.schema.json`
- `skills/unity-craft/presets/schema/match.schema.json`
- `scripts/scan_asset_library.py` — `--force` alias
- `CHANGELOG.md`

**Run 7:**
- `STYLE.md` — naming conventions
- `README.md` — install check section
- `tools/combat-system.md` — presets section
- `tools/match-system.md` — presets section
- `demo/bloodborne-jam/EVALUATION.md` — evaluation criteria table + verdict

**Run 8:**
- `demo/templates/platformer-gdd.md`
- `demo/templates/fps-gdd.md`
- `demo/templates/puzzle-gdd.md`
- `demo/README.md` — template GDD table

## Remaining gaps (post-run-8)

- W1 — C# compile test (user-blocked, Unity Editor required)
- W2/W3 — Preset schema validator script (deferred again — low urgency, schemas exist)
- W4 — Asset Store scraping fragility in E16 (medium)
- W9 — ProfileCapture single-frame (blocked on craft-unity v0.3c)
- W10 — G13 vision pipeline untested (user-blocked, Unity Editor required)

## Lessons

1. **Preset coverage uniformity matters** — when 12/14 tool families have presets but 2 don't, users assume no presets exist. Complete coverage is a trust signal.
2. **Template GDDs are force multipliers** — A14 can now bootstrap a game in 3 genres without user-supplied docs. This moves the plugin from "powerful if you know how" to "powerful out of the box."
3. **STYLE.md is documentation investment** — took 30 min but prevents weeks of naming inconsistency in future agents. Especially critical since A14/B19/G13 all generate names autonomously.
4. **Evaluation harnesses close the loop** — bloodborne-jam had a scaffold but no success criteria. Adding the criteria table makes the demo verifiable, not just illustrative.

## Next iteration recommendations

1. **Preset schema validator script** — `python3 scripts/validate_presets.py` to lint all JSONs on PR
2. **4th template GDD** — metroidvania (connects to level design + progression)
3. **Multiplayer input template** — was identified in bloodborne-jam eval as gap
4. **craft-unity v0.3c implementation** — 5 PlayMode ops; unblocks real Playtest

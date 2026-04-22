# Lessons Learned — Run 1

## What worked

- **Parallel audit dispatches** — 2 Haiku agents doing specs-audit and knowledge-audit in parallel hit 45-84s total while producing 27+ structured findings. Cheap signal.
- **Pre-writing MASTER_ANALYSIS from Jarvis context** — I had fresh knowledge of the 3-repo 8-commit state, so generating the weak-point inventory myself was faster than delegating. Audit dispatches then stress-tested my self-assessment.
- **Audit-first ordering** — finding K7 (`com.xesmedia.fsm` hallucination) before ever trying to install it saved real debugging time downstream.

## What failed or underperformed

- **FilmGrain pipeline error in knowledge files went uncaught in original Haiku generation** — Haiku wrote postfx-volume-presets.md with FilmGrain listed generically. Audit caught it, but ideally we'd catch at generation time. Fix: when Haiku writes preset knowledge, have it cite the Unity package documentation URL for each VolumeComponent and include URP vs HDRP flag.
- **Codex `--full-auto` sandbox issue** (from previous session, not Run 1) — codex couldn't write outside its cwd. Pattern for Run 2: always `cd <target-dir> &&` before codex invocation.
- **Inconsistent naming convention** (`Cinema_*` vs `Assets_*` vs `Optimize_*`) — was not spotted during spec writing because no style guide existed. Run 5 deliverable should include a STYLE.md.

## Recommendations for next run (Run 2)

- **Invoke /dispatch for validate_presets.py implementation** — do NOT Haiku it. User explicit: "dispatch etmeyi unutma". Dispatch → GPT via codex from target cwd.
- **Before writing, write the JSON Schema files first** — `presets/schema/cinema.json`, `presets/schema/postfx.json`, etc. Then the validator is just "does this JSON match this schema?" — trivially correct.
- **Validate once as sanity check** — run the validator over all 19 preset JSONs; expected: zero errors. Any error = genuine bug.
- **After Run 2 commit, scan backward** — if validator finds e.g. that I wrote `maxTextureSize` vs `max_texture_size` inconsistently, note as audit finding Run 5 merges.

## Guardrails that held

- Forge-light mode avoided 5× Jira spam (would've been ~30 tickets + 30 PRs for 5 runs worth of feature scaffolding)
- Parallel dispatch didn't exceed token budget — each Haiku stayed under 140k tokens
- No Claude Opus invoked for implementation work (only Jarvis orchestration + sentence-level Jarvis-written MDs)

## Open questions for user (non-blocking)

- Should a STYLE.md be part of Run 5 output?
- Is the implicit agreement "W1 (Unity compile test) is manual, out-of-band" still valid for all future runs?

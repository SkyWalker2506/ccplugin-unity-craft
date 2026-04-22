# Forge Run 5 Summary — ccplugin-unity-craft

**Date:** 2026-04-18
**Focus:** Demo Unity project scaffold (GDD → playable pipeline proof)

## Stats

- Agent dispatches: 1 Haiku (scaffold builder)
- Files created: 10 in `demo/`
- Integration: `Director_Ship(SAMPLE_GDD.md)` entry point wired

## Deliverables

- `demo/README.md` — 320-line run instructions + prerequisites + troubleshooting
- `demo/SAMPLE_GDD.md` — "Mushroom Arena" top-down arena survivor GDD (YAML + 9 sections)
- `demo/EXPECTED_OUTPUT.md` — wave-by-wave Director_Ship trace + polish-scorecard example
- `demo/CLAUDE.md` — project-local directives (Director_Ship as top-level entry, CRAFT-only mutations)
- `demo/Packages/manifest.json` — UPM dependencies: craft-unity git#v0.2.0 + unity-ai-assistant 2.0 + cinemachine 3.1.1 + inputsystem 1.11 + probuilder 6.0.4 + ai.navigation 2.0.5 + URP 17.0.3 + localization + timeline + test-framework
- `demo/ProjectSettings/ProjectVersion.txt` — Unity 6000.0.25f1
- `demo/.gitignore` — canonical Unity ignore
- `demo/Assets/README.md` — "Director_Ship will populate"
- `demo/.claude-hooks/expected-transcript.md` — idealized 4-wave run transcript

## Polish target

Placeholder-art-but-shippable — **7.0** baseline, **≥ 8.0** after one refinement iteration.

## What can actually run today vs waits on v0.3c

Today (craft-unity 0.2.0):
- Scene generation (Core + ImportSettings)
- Cinemachine + PostFX application
- Audio mixer + input actions
- Vision critique via Craft_CaptureGameView
- Performance ProfileCapture (single-frame)

Blocked on craft-unity v0.3c upstream (spec'd, not yet implemented):
- Real Playtest execution (EnterPlayMode + SimulateInput + SampleProfileWindow)
- Live perf sampling during play
- Scripted input scenarios

Dry-run mode emits mock metrics until v0.3c lands.

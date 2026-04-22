# Template GDD — Grid Puzzle Game

> Copy + rename this file, then fill in the bracketed fields. Pass to `Director_Ship(gddPath)`.

---

## Game Identity

```yaml
title: "[Your Game Title]"
genre: Puzzle
subgenre: "[match-3 / sokoban / sliding / block-push / color-fill]"
art_style: "[minimal / cartoon / isometric]"
target_platform: "[mobile / PC]"
target_session: "5–10 min"
```

## Core Loop

1. **Present puzzle** — grid-based board with objects/tiles
2. **Player acts** — move/swap/rotate pieces within move limit
3. **Check win** — condition met → star rating + proceed
4. **Retry or advance** — out of moves → retry; win → unlock next

## Grid

```yaml
grid:
  columns: 8
  rows: 8
  cell_size: 64   # pixels, for 2D
  edge_padding: 16

objects:
  - type: tile
    variants: 5    # color / symbol variants
  - type: blocker
    breakable: false
  - type: special
    description: "[bomb / rainbow / locked]"
```

## Match Rules

```yaml
match_preset: puzzle-points    # presets/match/puzzle-points.json
win_condition: "[clear_N_tiles / reach_score / fill_all]"
move_limit: 30
time_limit_enabled: false
star_thresholds: [100, 80, 50]
```

## Levels

```yaml
total_levels: 20
save_progress: true
unlock_on_stars: 1
level_editor: false

level_themes:
  - "[spring / desert / ocean / space]"
```

## Hint System

```yaml
hints:
  count_per_level: 3
  show_best_move: true
  penalty_points: 20
  cooldown_seconds: 30
```

## Scoring

```yaml
base_score: 100
move_efficiency_bonus: true    # fewer moves = more points
combo_multiplier: true
combo_threshold: 3
```

## Audio

```yaml
bgm_preset: mobile-optimized    # presets/audio/mobile-optimized.json
sfx:
  - tile_match
  - tile_fail
  - combo_burst
  - level_complete
  - level_fail
  - hint_used
  - star_earned
```

## UI

```yaml
hud:
  - move_counter
  - score
  - star_preview
  - hint_button
screens:
  - main_menu
  - level_select
  - in_game
  - level_complete
  - settings
```

## Director_Ship Entry Point

```
Director_Ship(gdd: "demo/templates/puzzle-gdd.md")
```

Expected waves (A14):
1. Board generator (B19 dispatch — grid data structure + cell prefabs)
2. Tile system (B19 dispatch — match detection, swap animation)
3. Move + score manager (B19 dispatch)
4. Camera (orthographic, no Cinemachine needed — `Craft_Execute` ModifyComponent)
5. UI Toolkit (D11 dispatch — HUD + level select + star screen)
6. Audio (B26 dispatch)
7. Level data (B19 dispatch — JSON-driven level definitions)
8. Hint system (B19 dispatch)
9. Critique (G13 UI layout check + B53 mobile perf)

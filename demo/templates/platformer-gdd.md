# Template GDD — 2D Platformer

> Copy + rename this file, then fill in the bracketed fields. Pass to `Director_Ship(gddPath)`.

---

## Game Identity

```yaml
title: "[Your Game Title]"
genre: 2D Platformer
subgenre: "[action / puzzle-platformer / metroidvania]"
art_style: "[pixel-art / cartoon / hand-drawn]"
target_platform: "[PC / mobile / console]"
target_session: "[5 min / 15 min / open-ended]"
```

## Core Loop

1. **Explore** — player moves through side-scrolling level (left-right + jump)
2. **Overcome** — defeat enemies or solve jump puzzles
3. **Progress** — reach level end flag / unlock next area
4. **Reward** — coins / power-up / story beat

## Player

```yaml
movement:
  max_speed: 8.0
  jump_force: 12.0
  double_jump: true
  wall_jump: false
  coyote_time: 0.12
  jump_buffer: 0.1

combat:
  attack_type: melee   # melee | ranged | none
  attack_range: 1.0
  attack_damage: 10
  attack_cooldown: 0.4

health:
  max_hp: 100
  lives: 3
  invincibility_frames: 1.5
  death_behavior: respawn_at_checkpoint
```

## Levels

```yaml
level_count: 10
worlds: 3           # worlds group levels by theme
levels_per_world: 3 # + 1 boss per world
boss_level: true

layout_template: platformer-chunk  # presets/level/platformer-chunk.json
tile_theme: "[forest / dungeon / ice / industrial]"
```

## Enemies

| Enemy | Behavior | HP | Damage |
|-------|----------|-----|--------|
| Walker | Patrols platform edge-to-edge | 20 | 10 |
| Jumper | Hops toward player when in range | 30 | 15 |
| Boss | Pattern-based (3 phases) | 200 | 20 |

## Win / Lose Conditions

```yaml
win: reach_level_end_flag
lose: hp_zero_or_fall_into_pit
```

## Scoring

```yaml
coin_score: 5
enemy_kill_score: 10
time_bonus: true
perfect_run_bonus: 100   # no damage taken
```

## Audio

```yaml
bgm_preset: standard-game   # presets/audio/standard-game.json
sfx:
  - jump
  - land
  - attack
  - hit_received
  - coin_collect
  - level_complete
  - player_death
```

## UI

```yaml
hud:
  - hp_bar
  - lives_counter
  - coin_counter
  - level_timer
screens:
  - main_menu
  - pause
  - level_complete
  - game_over
```

## Director_Ship Entry Point

```
Director_Ship(gdd: "demo/templates/platformer-gdd.md")
```

Expected waves (A14 auto-generates):
1. Scene + level layout (`Level_Generate` with `platformer-chunk.json`)
2. Player rig (`Input_Apply` with `player-thirdperson.json` adapted for 2D + `Combat_Setup`)
3. Enemies (B19 dispatch per enemy type)
4. Camera (Cinemachine 2D confiner)
5. UI Toolkit (D11 dispatch)
6. Audio (B26 dispatch)
7. Playtest critique loop (G13 + B53)

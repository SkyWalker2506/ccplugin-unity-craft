# Template GDD — First-Person Shooter (Wave Survival)

> Copy + rename this file, then fill in the bracketed fields. Pass to `Director_Ship(gddPath)`.

---

## Game Identity

```yaml
title: "[Your Game Title]"
genre: First-Person Shooter
subgenre: "wave survival"
art_style: "[realistic / stylized / cel-shaded]"
target_platform: "[PC / console]"
target_session: "20–40 min"
```

## Core Loop

1. **Survive wave** — enemies spawn and rush player
2. **Kill** — eliminate all enemies in wave
3. **Shop** — spend earned coins on weapons / upgrades between waves
4. **Repeat** — next wave is harder
5. **Endgame** — survive all waves or die trying

## Player

```yaml
movement:
  speed: 5.0
  sprint_speed: 8.0
  crouch_speed: 2.5
  jump_force: 0
  gravity: 9.81

combat_preset: shooter-fps    # presets/combat/shooter-fps.json
health:
  max_hp: 100
  regeneration: false
  shield: 0

starting_weapon: "[pistol / assault_rifle / shotgun]"
weapon_slots: 2
```

## Weapons

| Weapon | Type | Magazine | Fire Rate | Damage | Unlock |
|--------|------|----------|-----------|--------|--------|
| Pistol | hitscan | 12 | 300 | 20 | start |
| Assault Rifle | hitscan | 30 | 600 | 15 | wave 3 |
| Shotgun | spread | 8 | 120 | 8×5 | wave 5 |
| Sniper | hitscan | 5 | 60 | 120 | wave 8 |

## Enemies

| Enemy | HP | Speed | Damage | Behavior |
|-------|-----|-------|--------|----------|
| Grunt | 50 | 3.0 | 10 | Direct rush |
| Flanker | 40 | 5.0 | 8 | Strafe + rush |
| Tank | 300 | 1.5 | 25 | Slow advance |
| Boss | 1000 | 2.0 | 40 | Phase pattern |

## Match

```yaml
match_preset: wave-survival   # presets/match/wave-survival.json
wave_count: 10
boss_wave_interval: 5
intermission: 15
endless_mode: false
```

## Level

```yaml
layout: combat-arena        # presets/level/combat-arena.json
cover_count: 12
spawn_points: 8
```

## Audio

```yaml
bgm_preset: stylized-arcade   # presets/audio/stylized-arcade.json
sfx:
  - gunshot
  - reload
  - empty_click
  - hit_received
  - enemy_death
  - wave_start
  - wave_complete
  - game_over
```

## UI

```yaml
hud:
  - crosshair
  - ammo_counter
  - hp_bar
  - wave_counter
  - kill_counter
  - score
screens:
  - main_menu
  - shop
  - pause
  - game_over
  - scoreboard
```

## Director_Ship Entry Point

```
Director_Ship(gdd: "demo/templates/fps-gdd.md")
```

Expected waves (A14):
1. Level (`Level_Generate` with `combat-arena.json`)
2. Player rig (`Input_Apply` with `player-fps.json` + `Combat_Setup(preset: "shooter-fps")`)
3. Weapon system (B19 dispatch)
4. Enemy AI (B19 dispatch per enemy type)
5. Wave manager + shop (B19 dispatch)
6. UI Toolkit — HUD + shop screen (D11 dispatch)
7. Audio (B26 dispatch)
8. PostFX (`PostFX_ApplyPreset("realistic")`)
9. Playtest + critique (G13 + B53)

---
title: "Mushroom Arena"
genre: "Action / Arena Survival"
scope: "micro (5 min)"
target_audience: "casual"
platform: "desktop"
placeholder_art_ok: true
tech_constraints:
  - "URP only"
  - "2D physics (optional; can use 3D with no physics)"
  - "no advanced VFX"
  - "single-threaded CPU target"
---

# Mushroom Arena — Game Design Document

## Pitch

Top-down arena survivor: defend a shrine against 3 waves of mushroom enemies. One auto-targeting gun. 3-minute total playtime. Retro gameboy aesthetic. Simple, satisfying combat loop — move, aim, fire, survive.

---

## Mechanics

- **Player Movement:** WASD keys, speed 5 m/s, can move during aim without acceleration ramp (instant responsiveness)
- **Player Gun:** Fixed auto-targeting weapon, auto-locks nearest enemy within 10m radius, fires every 0.3s (3.3 bullets/sec), 10 damage per hit, no ammo limit
- **Player Health:** 100 HP; enemies deal 10 damage on collision; game over at 0 HP
- **Enemy Types:**
  - **Mushroom (Wave 1):** 20 HP, 1 m/s walk speed, melee attack (collision damage), spawns 8 per wave
  - **Slime (Wave 2):** 10 HP, 1.5 m/s speed, splits into 2 smaller slimes on death, spawns 6 per wave
  - **Boss (Wave 3):** 100 HP, 0.5 m/s speed (slower), area attack every 10s (damages in 5m radius), 1 spawn per wave
- **Scoring:** +10 points per enemy kill, +1 point per second survived, multiplier x1.5 for boss kill
- **Wave System:** 3 timed waves (Wave 1: 0–60s, Wave 2: 60–120s, Wave 3: 120–180s); each wave spawns enemies at timed intervals
- **Win Condition:** Defeat the boss (Wave 3); health remaining when boss dies = final score bonus

---

## Levels

**Arena (0–180s, 3 minutes total):**
- **Geometry:** 20m × 20m flat ground plane, center shrine (visual landmark only)
- **Player Spawn:** Exact center (0, 0), facing up
- **Enemy Spawns:** 4 corners + randomized perimeter positions per wave
- **Cover:** 4 cylindrical covers (1.5m tall, 0.5m radius) positioned at midpoints between center and corners — visual and gameplay breaks
- **Boundaries:** Transparent walls at perimeter (player blocked, visual indication via shader or outline)
- **Lighting:** Ambient sunlight (key direction roughly NE); optional dramatic PostFX (desaturation during boss arrival)

---

## Art Direction

- **Style:** Retro gameboy (4-color palette: white #FFFBF0, light-green #A8E6CF, dark-green #56AB91, black #2D3436)
- **Aesthetic:** Minimalist, grid-aligned; all models built from primitives (Cube for mushroom, Capsule for player, Sphere for projectile) or simple ProBuilder geometry
- **Camera:** Fixed orthographic, framing 22m × 22m arena (player always center viewport)
- **UI Theme:** Green monochrome, sans-serif font (Roboto Mono), all text centered and readable at 1920×1080
- **Asset Placeholder Strategy:** Unity default materials (Standard/URP Lit) with solid color albedo; no custom shaders, no normal maps, no textures; ProBuilder for geometry only
- **Mood:** Calm, quirky, playful (not horror or gothic)

---

## Audio Direction

- **Music:** Single looping 8-bit chiptune track, 120 BPM, 3-minute duration (loops once); upbeat, arcade-style, matches wave pacing
- **SFX:**
  - Gun fire: short synthetic laser beep (50–100ms duration, 1kHz sine tone)
  - Enemy spawn: ascending chime (3 notes, 200–300ms)
  - Enemy death: impact thump (bass-heavy, 100ms)
  - Wave complete: ascending chord (happy, 500ms)
  - Boss spawn: ominous low tone (100ms)
- **Ambience:** Optional light forest crickets loop at −15dB background, or silence OK
- **Audio Mixer:** 2 groups (Music, SFX), Music auto-ducked −6dB when SFX plays
- **Spatial Audio:** No 3D audio; all sounds 2D stereo (no positional panning)

---

## UI Style

- **Main Menu:** Title "Mushroom Arena" centered, single "Play" button below, green text on black background
- **HUD (In-Game):**
  - **Top-Left:** Wave counter ("Wave 1 / 3") and timer remaining (MM:SS format)
  - **Top-Right:** Current score (lives) and combo multiplier ("Score: 1250x1.5")
  - **Bottom-Left:** Player health bar (green → yellow → red gradient, labeled "HP")
  - **Bottom-Right:** Enemy count remaining ("Enemies: 5 / 8")
- **Pause Menu:** Invoked via ESC key; "Resume", "Restart", "Quit" buttons; semi-transparent overlay
- **Game Over Screen:** Large text "Final Score: {score}", "Waves Survived: {wave}/3", two buttons: "Restart" and "Quit"
- **Font:** Roboto Mono; score labels 32px, wave counter 24px, HUD values 28px
- **Color Scheme:** Text #A8E6CF (light green), background overlay #2D3436 (black 80% alpha)
- **Responsiveness:** All UI updates instantly (no fade, no tween)

---

## Controls

### Keyboard (Primary)
- **W/A/S/D:** Move forward/left/backward/right (8-directional, no diagonal acceleration penalty)
- **Mouse X/Y:** Aim direction (gun swivels toward mouse, player model rotates to face aim direction)
- **Left Mouse Button:** Fire (hold to maintain aim and keep firing; releasing does not break aim)
- **ESC:** Pause / Unpause
- **R:** Restart (available on game-over screen)
- **Q:** Quit to menu (available on game-over screen)

### Gamepad (Secondary, Optional)
- **Left Stick:** Move
- **Right Stick:** Aim direction
- **Right Trigger / RB:** Fire
- **Menu Button (Start):** Pause

---

## Technical Constraints

- **Target Platform:** Windows/Mac/Linux desktop, 1920 × 1080 native resolution, 16:9 aspect ratio
- **Engine:** Unity 6.0.x LTS, URP rendering pipeline
- **Physics:** 3D physics OK (Rigidbody + Colliders); no 2D physics required but not excluded
- **Scripting:** C# only, no Bolt or visual scripting
- **Performance Budget:**
  - FPS: 60 FPS target (avg), min 50 FPS (p95), no frame drops > 16.67ms sustained
  - Memory: < 200MB peak RAM during 3-minute playthrough
  - Build size: < 300MB compressed
  - Draw calls: < 50 steady state (no explosion frames)
- **Known Limits:** No high-res assets; no advanced VFX (particle effects minimal); single-threaded main thread only; no Netcode; placeholder art only

---

## Playtest Criteria

1. **Input Responsiveness:** Player can move and fire within 50ms input-to-action latency; no perceivable input lag
2. **Mechanic Completeness:** All enemy types spawn correctly; melee collision damage works; player gun fires and hits enemies; scoring increments in real-time
3. **Wave Progression:** Each wave distinct; enemies spawn at correct times; wave timer visible and accurate; game-over triggers on loss or boss defeat
4. **Audio Cohesion:** Music loop syncs to wave timer (no drift); key SFX (fire, spawn, death) play at correct moments; no SFX clipping or overlap distortion
5. **Game Length:** Canonical playthrough (defend, defeat waves) completes in 3 ± 0.5 minutes
6. **Stability:** Zero crashes in 5-minute sustained playthrough; console shows 0 errors (< 5 warnings OK)
7. **Visual Clarity:** Player, enemies, and projectiles all clearly visible at 1920×1080; HUD text readable; no overlapping UI elements
8. **Scope Completion:** All mechanics from Mechanics section implemented and functional; no placeholder placeholders (i.e., scripts and behavior are real, not dummy stubs)

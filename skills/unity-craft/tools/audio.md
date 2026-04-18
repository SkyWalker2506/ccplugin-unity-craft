# Audio Tool Family

## Purpose

Establish professional audio mixing architecture in Unity scenes through AudioMixer asset creation, group hierarchy setup, spatial audio blending, snapshot transitions, and music/SFX routing. All operations execute as transaction-safe CRAFT operations, supporting runtime snapshot crossfades, AudioListener placement, and preset-driven AudioImporter settings for optimized audio compression and streaming per asset category (music, SFX, voice, 3D effects).

The tool manages:
- **AudioMixer asset creation** with group hierarchies (Master, Music, SFX, UI, Voice) and exposed volume parameters
- **Snapshot system** — runtime transitions between mix states (ambient→action, horror↔calm, etc.)
- **AudioSource routing** — add sources with group output, spatial blend, and loop/play settings
- **Spatial audio** — 3D panning via spatial blend (0=2D, 1=full 3D), distance rolloff curves
- **AudioListener** — ensures single listener on camera; removes duplicates
- **Import presets** — per-category AudioImporter overrides (sample rate, compression format, load type)

## Tool Signatures

### Audio_CreateMixer

```
Audio_CreateMixer(
  name: string,
  groups?: string[] = ["Master", "Music", "SFX", "UI", "Voice"]
) → {
  mixerPath: string,
  groupsCreated: string[],
  exposedParameters: string[],
  transactionId: string
}
```

Creates an AudioMixer asset with named group hierarchy and exposed volume parameters (one per group for dynamic control). All groups route to Master. Returns paths for use in subsequent operations.

**Presets via `Audio_ApplyMixerPreset`:**
- Uses JSON from `presets/audio/<preset-name>.json`
- Each preset auto-structures groups, applies compressor/EQ/reverb effects, and sets initial snapshot

### Audio_ApplyMixerPreset

```
Audio_ApplyMixerPreset(
  mixerPath: string,
  preset: "standard-game" | "horror" | "stylized-arcade" | "mobile-optimized"
) → {
  mixerPath: string,
  presetApplied: string,
  effectsAdded: string[],
  snapshotsCreated: string[],
  transactionId: string
}
```

Load a preset JSON from `presets/audio/<preset>.json` and apply mixer group layout, effects (compressor, EQ, reverb, saturation), and initial snapshots. Automatically routes groups, exposes volume parameters, and sets sidechain triggers (if applicable).

### Audio_AddSource

```
Audio_AddSource(
  gameObjectPath: string,
  clipPath: string,
  options?: {
    volume?: number = 1.0,
    spatialBlend?: number = 0,
    outputGroup?: string = "Master",
    loop?: boolean = false,
    playOnAwake?: boolean = false
  }
) → {
  audioSourcePath: string,
  clipAssigned: string,
  routedToGroup: string,
  spatialSettings: object,
  transactionId: string
}
```

Add an AudioSource component to a GameObject, assign an audio clip, route to a mixer group, and configure spatial properties. Spatial blend 0 = full 2D (no distance attenuation), 1 = full 3D with rolloff curve.

### Audio_SetupListener

```
Audio_SetupListener(
  cameraPath: string
) → {
  listenerPath: string,
  duplicatesRemoved: number,
  transactionId: string
}
```

Ensure a single AudioListener on the specified camera. Queries scene for duplicate listeners and removes all but the target, preventing audio routing conflicts.

### Audio_CreateSnapshot

```
Audio_CreateSnapshot(
  mixerPath: string,
  name: string,
  overrides: object
) → {
  mixerPath: string,
  snapshotPath: string,
  parametersOverridden: string[],
  transactionId: string
}
```

Add a named Snapshot to an AudioMixer. Overrides map exposed parameter names (e.g., "Master Volume", "Music Volume") to target values (0.0–1.0 or dB range for effects). Used for runtime crossfades.

**Typical usage:**
```
Audio_CreateSnapshot("Assets/Audio/GameMixer", "PlayerHit",
  { "Master Volume": -6, "Music Volume": -12 })

Audio_CreateSnapshot("Assets/Audio/GameMixer", "Ambient",
  { "Master Volume": -3, "Music Volume": 0, "SFX Volume": -9 })
```

### Audio_ApplyImportPreset

```
Audio_ApplyImportPreset(
  clipFolder: string,
  preset: "music" | "sfx-short" | "sfx-3d" | "voice"
) → {
  clipsProcessed: number,
  compressionApplied: string,
  sampleRate: number,
  loadType: string,
  transactionId: string
}
```

Batch-apply AudioImporter settings to clips in a folder using a category preset. Overrides sample rate, compression codec, and load type (streaming vs. in-memory). Uses upstream `Craft_SetAudioImporter` operation.

**Import presets:**
- **music** — Vorbis 128 kbps, streaming, 48 kHz sample rate
- **sfx-short** — ADPCM load-in-memory, 44.1 kHz, fast seek
- **sfx-3d** — ADPCM load-in-memory, mono (force), 44.1 kHz
- **voice** — Vorbis 80 kbps, streaming, 22.05 kHz

## Pipeline & Dispatch Protocol

When Audio tools are invoked, the request is dispatched to the **B26** agent (unity-audio-engineer) with the following contract:

**Request Format:**
```json
{
  "tool": "Audio_CreateMixer" | "Audio_ApplyMixerPreset" | "Audio_AddSource" | "Audio_SetupListener" | "Audio_CreateSnapshot" | "Audio_ApplyImportPreset",
  "parameters": { "..." },
  "preset": "..." | null
}
```

**Response Format:**
```json
{
  "success": true,
  "result": {
    "mixerPath": "..." | "audioSourcePath": "..." | "listenerPath": "...",
    "transactionId": "...",
    "metadata": {}
  },
  "warnings": [],
  "errors": []
}
```

B26 handles:
1. Mixer asset creation and group hierarchy setup
2. Preset JSON loading from `presets/audio/` subdirectories
3. Group routing, effect insertion, parameter exposure
4. Component assembly via CRAFT_Execute operations
5. Snapshot binding and sidechain configuration
6. AudioImporter batch updates via upstream `Craft_SetAudioImporter`

## Preset System

### Preset JSON Schema

File: `presets/audio/<preset-name>.json`

```json
{
  "preset_name": "string",
  "version": "1.0",
  "target": "AudioMixer",
  "groups": [
    {
      "name": "string",
      "parent": "string",
      "attenuation": number
    }
  ],
  "exposed_parameters": [
    {
      "name": "string",
      "controlGroup": "string",
      "controlProperty": "Volume"
    }
  ],
  "effects": [
    {
      "group": "string",
      "effectType": "AudioMixerEffectController",
      "effectName": "string",
      "enabled": boolean,
      "parameters": { "..." }
    }
  ],
  "snapshots": [
    {
      "name": "string",
      "overrides": { "parameter_name": value }
    }
  ],
  "_note": "..."
}
```

### Preset: standard-game.json

**Purpose:** General gameplay mix with music ducking under SFX intensity.

- **Groups:** Master → [Music, SFX, UI, Voice]
- **Effects:**
  - Master: Compressor (threshold −20dB, ratio 2:1) + subtle reverb
  - Music: Compressor (sidechain input from SFX)
  - SFX: Highpass EQ (20 Hz cutoff)
  - Voice: Normalizer (target −18dB)
- **Snapshots:**
  - `Gameplay` — Master 0dB, Music −3dB, SFX 0dB, Voice 0dB
  - `Dialogue` — Master −6dB, Music −12dB, SFX −9dB, Voice +3dB

### Preset: horror.json

**Purpose:** Atmospheric tension with heavy low-pass and reverb.

- **Groups:** Master → [Ambient, SFX, Voice]
  - Ambient includes music, drones, background loops
- **Effects:**
  - Master: Heavy reverb (room size 0.9, decay 4s, mix 0.4), Compressor
  - SFX: Lowpass EQ (peak at 100 Hz, resonance 3), Distortion (0.3 drive)
  - Voice: Compressor + Highpass (80 Hz)
- **Snapshots:**
  - `Ambient` — Master −3dB, Ambient 0dB, SFX −6dB
  - `PlayerHit` — Master −12dB, SFX +6dB (sidechain spike), reverb decay 6s
  - `AmbientTension` — Lowpass cutoff 800 Hz, reverb wet 0.5

### Preset: stylized-arcade.json

**Purpose:** Upbeat, saturated audio for arcade/retro games.

- **Groups:** Master → [Music, SFX, UI, Voice]
- **Effects:**
  - Master: Saturation (drive 0.4, tone 0.6)
  - Music: EQ (boost mid 1kHz +4dB, presence 4kHz +3dB), Compressor (ratio 4:1)
  - SFX: Saturation (drive 0.5) + Highpass (50 Hz)
  - UI: Compressor (fast attack)
- **Snapshots:**
  - `Gameplay` — All groups at 0dB
  - `MenuFocus` — Music −6dB, UI +3dB, SFX −3dB

### Preset: mobile-optimized.json

**Purpose:** Low CPU footprint, omits real-time convolution, voice channel limited.

- **Groups:** Master → [Music, SFX, UI, Voice]
  - Master has voiceCount limit: 32 max simultaneous voice count
- **Effects:**
  - Master: Compressor only (CPU-efficient, no reverb)
  - SFX: Highpass (20 Hz, minimal CPU)
  - Voice: Normalizer only
- **Snapshots:**
  - `GameDefault` — Master −1dB, Music −3dB
  - `MusicOnly` — Music 0dB, SFX −20dB, Voice −20dB (mute all but music)

## Audio Import Preset Details

Presets in `presets/audio/import-*.json` define per-category compression and streaming strategy:

| Category | Format | Bitrate | Load Type | Sample Rate | Notes |
|----------|--------|---------|-----------|-------------|-------|
| **music** | Vorbis | 128 kbps | Streaming | 48 kHz | Long loops, continuous playback, conserve memory |
| **sfx-short** | ADPCM | — | Load In Memory | 44.1 kHz | <2s clips, instant playback, high compression |
| **sfx-3d** | ADPCM | — | Load In Memory | 44.1 kHz | Mono-forced, positional effects |
| **voice** | Vorbis | 80 kbps | Streaming | 22.05 kHz | Dialogue, lower quality acceptable, save bandwidth |

## Implementation Notes

### Audio_CreateMixer

Uses `Craft_Execute` with:

```json
[
  {
    "type": "CreateAudioMixer",
    "parameters": {
      "name": "GameMixer",
      "assetPath": "Assets/Audio/GameMixer.mixer"
    }
  },
  {
    "type": "CreateAudioMixerGroup",
    "target": "Assets/Audio/GameMixer.mixer",
    "parameters": {
      "name": "Music",
      "parent": "Master"
    }
  },
  {
    "type": "CreateAudioMixerGroup",
    "target": "Assets/Audio/GameMixer.mixer",
    "parameters": {
      "name": "SFX",
      "parent": "Master"
    }
  },
  "..."
]
```

### Audio_ApplyMixerPreset

Merges preset JSON properties into the mixer asset, then calls upstream operations to:
1. Insert effect components (compressor, EQ, reverb, saturation)
2. Wire sidechain connections
3. Create and configure snapshots
4. Set initial parameter exposures

### Audio_ApplyImportPreset

Uses upstream `Craft_SetAudioImporter` to batch-update `AudioImporter` settings on all clips in the target folder. Returns count of clips processed and the applied compression format.

## Example Scenarios

### Scenario 1: Standard Game Setup

```
User: "Set up audio for a standard gameplay scene with music and SFX separation"

1. Audio_CreateMixer("GameMixer", ["Master", "Music", "SFX", "UI", "Voice"])
   → Mixer created, groups hierarchy established

2. Audio_ApplyMixerPreset("Assets/Audio/GameMixer.mixer", "standard-game")
   → Compressor + reverb added, music sidechain from SFX active, snapshots created

3. Audio_AddSource("MusicPlayer", "Assets/Audio/Music/MainTheme.ogg",
     { outputGroup: "Music", loop: true, playOnAwake: true })
   → AudioSource routed to Music group

4. Audio_AddSource("SFXEmitter", "Assets/Audio/SFX/footstep.wav",
     { outputGroup: "SFX", volume: 0.8, spatialBlend: 0.5 })
   → 3D positioned footstep effect routed to SFX
```

**Expected outcome:**
- GameMixer asset in Assets/Audio/
- Four groups visible in mixer hierarchy
- MusicPlayer and SFXEmitter components on respective GameObjects
- Master compressor attenuates music when SFX spike detected

### Scenario 2: Horror Ambient Mix

```
User: "Create a horror game audio setup with heavy reverb and tense snapshots"

1. Audio_CreateMixer("HorrorMixer")
2. Audio_ApplyMixerPreset("Assets/Audio/HorrorMixer.mixer", "horror")
   → Heavy reverb (decay 4s), lowpass on SFX, tension snapshots ready

3. Audio_CreateSnapshot("Assets/Audio/HorrorMixer.mixer", "Jumpscare",
     { "Master Volume": -18, "SFX Volume": +6 })
   → Mutes music, spikes SFX for jump event

4. Audio_AddSource("DoreBelly", "Assets/Audio/Horror/belly_drones.ogg",
     { outputGroup: "Ambient", loop: true, volume: 0.6, playOnAwake: true })
```

**Expected outcome:**
- Ambient layer drones at low volume
- Snapshot transitions available for scares and quiet moments
- Reverb tail audibly "spreads" sound, heightens dread

### Scenario 3: Mobile Performance

```
User: "Optimize audio for mobile with low CPU overhead"

1. Audio_CreateMixer("MobileMixer")
2. Audio_ApplyMixerPreset("Assets/Audio/MobileMixer.mixer", "mobile-optimized")
   → 32-voice limit enforced, no convolution reverb, minimal CPU

3. Audio_ApplyImportPreset("Assets/Audio/Music", "music")
   → Music clips set to Vorbis 128 kbps streaming

4. Audio_ApplyImportPreset("Assets/Audio/SFX", "sfx-short")
   → SFX clips compressed with ADPCM, loaded in-memory
```

**Expected outcome:**
- Mixer profiler shows <5% CPU on idle
- Music streams from disk, doesn't load entirely
- SFX play instantly without seek delay

### Scenario 4: Runtime Snapshot Transition (Dialogue)

```
User: "When dialogue plays, duck music and boost voice in the mix"

1. [Assume mixer already set up with standard-game preset]

2. Audio_CreateSnapshot("Assets/Audio/GameMixer.mixer", "DialogueMode",
     { "Music Volume": -12, "SFX Volume": -6, "Voice Volume": +3 })

3. // At runtime (pseudocode — in-game logic):
   mixer.FindSnapshot("DialogueMode").TransitionTo(2.0f); // Fade over 2s
```

**Expected outcome:**
- Music ducks instantly as snapshot activates
- Voice channel elevated for intelligibility
- Return to gameplay snapshot when dialogue ends

## Verification Checklist

After executing Audio operations, verify:

1. **Mixer Creation:**
   - AudioMixer asset exists at specified path (Assets/Audio/)
   - Group hierarchy is correct (Master parent, others children)
   - Exposed parameters appear in Inspector (volume sliders per group)

2. **Preset Application:**
   - Effects visibly attached to groups in mixer detail view
   - Snapshots appear in Snapshots list
   - Sidechain connections wired (if applicable)

3. **AudioSource Routing:**
   - AudioSource component present on target GameObject
   - Output Group dropdown shows correct group assignment
   - Spatial Blend slider set as specified (0 or >0)

4. **AudioListener:**
   - Single AudioListener exists on Main Camera
   - No duplicate listeners in scene (Console: no "listener" warnings)

5. **Import Presets:**
   - Target clips show updated compression format in Import Settings
   - Sample rate and load type reflect preset category
   - Project size reduced if switching from uncompressed to streaming

6. **Runtime Snapshot:**
   - Play scene, verify snapshot transitions are audible
   - Crossfade duration matches TransitionTo(duration) parameter
   - All exposed parameters animate smoothly between snapshots

## Common Workflows

**Minimal setup:**
```
Audio_CreateMixer("GameMixer")
Audio_ApplyMixerPreset("Assets/Audio/GameMixer.mixer", "standard-game")
Audio_AddSource("MusicPlayer", "Assets/Audio/Music.ogg", { outputGroup: "Music", loop: true })
```

**Mobile build:**
```
Audio_CreateMixer("MobileMixer")
Audio_ApplyMixerPreset("Assets/Audio/MobileMixer.mixer", "mobile-optimized")
Audio_ApplyImportPreset("Assets/Audio", "music")
Audio_ApplyImportPreset("Assets/Audio/SFX", "sfx-short")
```

**Horror game with transitions:**
```
Audio_CreateMixer("HorrorMixer")
Audio_ApplyMixerPreset("Assets/Audio/HorrorMixer.mixer", "horror")
Audio_CreateSnapshot("...", "Ambient", {...})
Audio_CreateSnapshot("...", "Jumpscare", {...})
// Bind to in-game events that call mixer.FindSnapshot().TransitionTo()
```

**3D spatial mix:**
```
Audio_AddSource("PlayerFootsteps", "Assets/SFX/footstep.wav",
  { outputGroup: "SFX", spatialBlend: 1.0, volume: 0.7 })
Audio_AddSource("AmbientWind", "Assets/Audio/wind.ogg",
  { outputGroup: "Ambient", spatialBlend: 0.3, loop: true })
```

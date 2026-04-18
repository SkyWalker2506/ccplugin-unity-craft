# Cinematic Camera Tool

## Purpose

Create high-quality cinematic visuals in Unity through Cinemachine virtual camera rigs and Post-Processing Volume effects. This tool integrates with CRAFT's transaction system to safely apply camera presets, blend between virtual cameras, and capture cinematic shots with Post-FX profiles (Cinematic, Stylized, Realistic, Anime, Horror, Dreamy).

The tool manages:
- **CinemachineCamera** component instantiation with preset rigging (Portrait, ThirdPerson, Orbit, TopDown, Cinematic, FirstPerson)
- **Blend transitions** between virtual cameras with easing curves
- **Shot capture** — render sequences at 24/30/60 fps for video playback
- **Timeline recording** — bind virtual cameras to Timeline tracks for cutscene authoring
- **PostFX Volume profiles** — apply preset color grading, bloom, depth-of-field, motion blur, vignette, chromatic aberration, and film grain

## Tool Signatures

### Cinema_CreateVCam

```
Cinema_CreateVCam(
  preset: "Portrait" | "ThirdPerson" | "Orbit" | "TopDown" | "Cinematic" | "FirstPerson",
  targetPath: string,
  options?: {
    name?: string,
    followTarget?: string,
    priority?: number,
    customProperties?: object
  }
) → {
  vCamPath: string,
  transactionId: string,
  preset: string,
  rigging: object
}
```

Creates a Cinemachine virtual camera GameObject with a named preset configuration. The virtual camera is linked to an optional follow target and assigned a priority for blending (higher priority takes precedence when multiple VCams exist).

**Presets:**
- **Portrait** — Centered framing, shallow depth-of-field candidate. FOV 35, Framing Transposer body, Composer aim, damping 0.5.
- **ThirdPerson** — Over-shoulder perspective. FOV 60, 3rd Person Follow body, Hard Look At aim, shoulder offset, damping 0.3.
- **Orbit** — Circular follow around target. FOV 50, Orbital Transposer body, Composer aim, radius 5, height 2, horizontal axis input.
- **TopDown** — Isometric or top-down view. FOV 70 (or ortho size 10), Framing Transposer, eulerAngles (90,0,0).
- **Cinematic** — Wide, immersive framing for cutscenes. FOV 28, Tracked Dolly body, Composer aim, Handheld noise 0.3, damping 0.8.
- **FirstPerson** — POV from character. FOV 75, 3rd Person Follow (radius=0, height=0), Same As Follow Target aim.

### Cinema_Blend

```
Cinema_Blend(
  fromVCamPath: string,
  toVCamPath: string,
  durationSec: number,
  curve?: "Linear" | "EaseInOut" | "Hard"
) → {
  blendIn: number,
  blendOut: number,
  transactionId: string,
  curve: string
}
```

Smoothly blend between two virtual cameras over a specified duration. Adjusts CinemachineBrain blend settings and applies an easing curve (Linear, EaseInOut, or Hard cut).

### Cinema_RecordTrack

```
Cinema_RecordTrack(
  vCamPath: string,
  timelineAssetPath: string
) → {
  trackName: string,
  clipName: string,
  transactionId: string,
  duration: number
}
```

Bind a virtual camera to a Timeline track for synchronized cutscene playback. Returns the Timeline track and clip references for further editing.

### Cinema_CaptureShot

```
Cinema_CaptureShot(
  vCamPath: string,
  durationSec: number,
  fps?: 24 | 30 | 60,
  outputDir?: string
) → {
  frameCount: number,
  outputPath: string,
  transactionId: string,
  fps: number
}
```

Render a sequence of frames from the virtual camera's perspective at the specified frame rate. Each frame is saved as an image file (PNG/EXR). Uses upstream `Craft_CaptureGameView` internally, looped for the duration.

Default fps: 24. Default outputDir: `Assets/Cinematics/Captures/`.

### PostFX_ApplyPreset

```
PostFX_ApplyPreset(
  volumeName: string,
  preset: "Cinematic" | "Stylized" | "Realistic" | "Anime" | "Horror" | "Dreamy"
) → {
  volumePath: string,
  presetName: string,
  transactionId: string,
  effectsApplied: string[]
}
```

Load a VolumeProfile preset and apply it to the named Volume GameObject. Automatically detects the render pipeline (URP/HDRP) and loads the appropriate preset JSON from `presets/postfx/<preset>.json`.

**Presets:**
- **Cinematic** — Subtle bloom (0.3), soft DoF, neutral color, motion blur, gentle vignette (0.2), light chromatic aberration (0.1).
- **Stylized** — Strong bloom (0.8), boosted saturation (+25), stylized LUT, no DoF, dynamic motion blur.
- **Realistic** — Minimal bloom (0.15), ACES tonemapping, neutral saturation, subtle vignette (0.1).
- **Anime** — Medium bloom (0.5), high saturation (+40), anime-style LUT, outline effect, flat colors.
- **Horror** — Desaturated (-40), red color tint, heavy vignette (0.5), film grain (0.3), strong chromatic aberration (0.4).
- **Dreamy** — Luminous bloom (0.6), wide-aperture DoF (f/1.4), lifted shadows, peach white balance, soft vignette (0.15).

### PostFX_Tune

```
PostFX_Tune(
  volumeName: string,
  effect: "Bloom" | "DepthOfField" | "ColorAdjustments" | "MotionBlur" | "Vignette" | "ChromaticAberration" | "FilmGrain",
  property: string,
  value: number | object
) → {
  volumePath: string,
  effectName: string,
  property: string,
  value: any,
  transactionId: string
}
```

Fine-tune a single post-processing effect property within a Volume. Examples: `PostFX_Tune("MainVolume", "Bloom", "intensity", 0.5)` or `PostFX_Tune("MainVolume", "DepthOfField", "aperture", 2.8)`.

## Pipeline & E9 Dispatch Protocol

When Cinema/PostFX tools are invoked, the request is dispatched to the E9 agent (`unity-cinematic-director`) with the following contract:

**Request Format:**
```json
{
  "tool": "Cinema_CreateVCam" | "Cinema_Blend" | "Cinema_RecordTrack" | "Cinema_CaptureShot" | "PostFX_ApplyPreset" | "PostFX_Tune",
  "preset": "...",
  "parameters": { "..." },
  "pipeline_hint": "auto" | "URP" | "HDRP"
}
```

**Response Format:**
```json
{
  "success": true,
  "result": {
    "vCamPath": "..." | "volumePath": "...",
    "transactionId": "...",
    "metadata": {}
  },
  "warnings": [],
  "errors": []
}
```

E9 handles:
1. Render pipeline detection (URP vs HDRP) via `knowledge/render-pipeline-auto-detect.md`
2. Preset JSON loading from `presets/` subdirectories
3. Component assembly and property binding using CRAFT operations
4. VolumeProfile and Volume setup
5. Timeline track binding (if applicable)
6. Frame capture loop orchestration

## Implementation Notes

### Cinema_CreateVCam

Uses `Craft_Execute` with the following operation sequence:

```json
[
  {
    "type": "CreateGameObject",
    "parameters": {
      "name": "VCam_<preset>",
      "position": [0, 1, 0],
      "components": ["CinemachineCamera"]
    }
  },
  {
    "type": "ModifyComponent",
    "target": "VCam_<preset>",
    "parameters": {
      "componentType": "CinemachineCamera",
      "values": {
        "m_Lens.FieldOfView": <preset FOV>,
        "m_Follow": <followTarget>,
        "m_Priority": <priority>,
        "...": "<preset-specific body/aim config>"
      }
    }
  }
]
```

Preset properties are merged from the preset JSON file (`presets/cinema/<preset>.json`).

### PostFX_ApplyPreset

Uses `Craft_Execute` with:

```json
[
  {
    "type": "ModifyComponent",
    "target": "<volumeName>",
    "parameters": {
      "componentType": "Volume",
      "values": {
        "profile": "<VolumeProfile asset path>"
      }
    }
  },
  {
    "type": "ModifyComponent",
    "target": "<volumeName>",
    "parameters": {
      "componentType": "Volume",
      "values": {
        "weight": 1.0
      }
    }
  }
]
```

The VolumeProfile asset is loaded from `Assets/Cinematics/Presets/PostFX/<preset>.asset` (compiled from `presets/postfx/<preset>.json` during import).

### Cinema_RecordTrack

Queries the Timeline asset, creates a new track, and binds the VCam via a CinemachineShot clip.

### Cinema_CaptureShot

Loops `Craft_CaptureGameView` with frame indexing:
- Frame filenames: `shot_<frame_index>.png` (or .exr)
- Increments index each frame
- Total frames = `durationSec * fps`

## Example Scenarios

### Scenario 1: Third-Person Camera Chasing Player

```
User: "Set up a third-person camera following the player"

1. Cinema_CreateVCam("ThirdPerson", "Player", { followTarget: "Player", name: "VCam_ThirdPerson" })
   → VCam created with shoulder offset
   
2. Cinema_Blend("MainCamera", "VCam_ThirdPerson", 0.5, "EaseInOut")
   → Smooth transition from static to follow camera
```

**Expected outcome:**
- VCam_ThirdPerson GameObject appears with CinemachineCamera component
- CinemachineBrain on MainCamera blends over 0.5s
- Player motion is followed smoothly with damping

### Scenario 2: Cinematic Cutscene with Stylized Lighting

```
User: "Create a cinematic cutscene with stylized post-processing"

1. Cinema_CreateVCam("Cinematic", "CutsceneTarget", { name: "VCam_Cutscene" })
   → Wide, immersive virtual camera
   
2. PostFX_ApplyPreset("MainVolume", "Stylized")
   → Bloom 0.8, saturated colors, stylized LUT applied
   
3. Cinema_RecordTrack("VCam_Cutscene", "Assets/Cinematics/MyScene_Timeline.asset")
   → VCam bound to Timeline for synchronized playback
```

**Expected outcome:**
- VCam_Cutscene appears with Tracked Dolly body, Composer aim
- MainVolume's VolumeProfile is replaced with Stylized preset
- Timeline has new Cinemachine track binding VCam_Cutscene

### Scenario 3: Capture a 5-Second Hero Shot

```
User: "Render a 5-second hero shot at 30 fps with cinematic post-FX"

1. Cinema_CreateVCam("Cinematic", "HeroTarget", { name: "VCam_Hero" })
2. PostFX_ApplyPreset("MainVolume", "Cinematic")
3. Cinema_CaptureShot("VCam_Hero", 5.0, 30, "Assets/Cinematics/HeroShot/")
   → 150 frames (5 * 30) rendered to PNG files
```

**Expected outcome:**
- 150 image files in `Assets/Cinematics/HeroShot/`
- Each frame composited with Cinematic post-FX (bloom 0.3, DoF, motion blur)
- Ready for video sequence import

### Scenario 4: Fine-Tune Depth of Field

```
User: "Adjust the depth of field aperture to f/2.8"

PostFX_Tune("MainVolume", "DepthOfField", "aperture", 2.8)
```

**Expected outcome:**
- DepthOfField component in MainVolume's VolumeProfile updated
- Focus distance adjusted for cinematic bokeh effect

## Preset JSON Schema

### Cinema Presets

File: `presets/cinema/<preset>.json`

```json
{
  "preset_name": "string",
  "version": "1.0",
  "target": "CinemachineCamera",
  "properties": {
    "m_Lens": {
      "FieldOfView": number,
      "NearClipPlane": number,
      "FarClipPlane": number,
      "dutch": number
    },
    "m_Body": {
      "type": "string (e.g., 'Framing Transposer')",
      "properties": { "..." }
    },
    "m_Aim": {
      "type": "string",
      "properties": { "..." }
    },
    "m_Noise": {
      "enabled": boolean,
      "Frequency": number,
      "Amplitude": number,
      "FilterSize": number
    },
    "m_Damping": number
  }
}
```

### PostFX Presets

File: `presets/postfx/<preset>.json`

```json
{
  "preset_name": "string",
  "version": "1.0",
  "pipeline": "URP" | "HDRP" | "both",
  "volume_components": [
    {
      "type": "Bloom",
      "enabled": boolean,
      "properties": {
        "intensity": { "value": number, "override": true },
        "threshold": { "value": number, "override": true }
      }
    },
    {
      "type": "DepthOfField",
      "enabled": boolean,
      "properties": {
        "focusDistance": { "value": number, "override": true },
        "aperture": { "value": number, "override": true }
      }
    },
    "..."
  ]
}
```

## Verification Checklist

After executing Cinema/PostFX operations, verify:

1. **VCam Creation:**
   - VirtualCamera GameObject exists at specified path
   - CinemachineCamera component is present and configured
   - Follow target is linked (if specified)
   - Priority is set correctly for blending

2. **Blend Transition:**
   - CinemachineBrain detects both VCams
   - Blend duration matches the requested value
   - Easing curve is applied (inspect blend settings in hierarchy)

3. **PostFX Application:**
   - Volume GameObject has Volume component with weight > 0
   - VolumeProfile asset is loaded and matches the preset
   - Effects are visible in Game view (bloom glow, color shift, DoF, etc.)

4. **Shot Capture:**
   - Frame files appear in the output directory
   - Frame count equals `durationSec * fps`
   - Image quality matches render pipeline settings

5. **Timeline Recording:**
   - Timeline asset has a new Cinemachine track
   - VCam clip is placed on the track
   - Duration in Timeline matches shot duration

## Common Workflows

**Quick cinematic blend:**
```
Cinema_CreateVCam("Cinematic", "Target1")
Cinema_Blend("MainCamera", "VCam_Cinematic", 1.0, "EaseInOut")
```

**Multi-camera cutscene:**
```
Cinema_CreateVCam("Portrait", "Actor1")
Cinema_CreateVCam("ThirdPerson", "Actor2")
Cinema_RecordTrack("VCam_Portrait", "Scene_Timeline")
Cinema_RecordTrack("VCam_ThirdPerson", "Scene_Timeline")
// Manually arrange clips in Timeline UI
```

**Hero shot with post-FX:**
```
Cinema_CreateVCam("Cinematic", "HeroTarget")
PostFX_ApplyPreset("MainVolume", "Cinematic")
PostFX_Tune("MainVolume", "Bloom", "intensity", 0.4)
PostFX_Tune("MainVolume", "DepthOfField", "aperture", 1.8)
Cinema_CaptureShot("VCam_Cinematic", 5.0, 30)
```

**Anime-style cutscene:**
```
Cinema_CreateVCam("Cinematic", "CharacterTarget")
PostFX_ApplyPreset("MainVolume", "Anime")
Cinema_RecordTrack("VCam_Cinematic", "AnimeScene_Timeline")
```

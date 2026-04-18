# Visual Critique Tool

## Purpose

Autonomous self-critique of scene visual coherence, UI layout, level navigation, asset palette, and composition. Delivers structured scorecards (1-10 per criterion) + prioritized refinement operations ready for execution. No user-facing prompts ("look at this", "check that")—critique returns **actionable data** for the Game Director pipeline.

Dispatches to **G13 (vision-action-operator)** for composition/layout analysis + specialist agents (D11 UI, E11 level design, E16 asset curator) per scope. Aggregates scorecard + cross-family refinement ops for A14 to queue.

---

## FORBIDDEN OUTPUT PATTERNS

### Critical: Never Tell User to Look at Something

The following phrases **MUST NOT** appear in Critique output. Violation indicates broken automation:

**FORBIDDEN (User-facing instructions):**
- "Look at the X in the scene"
- "Check the UI panel"
- "Open Inspector to see"
- "Notice the misalignment"
- "Observe the color mismatch"
- "You can see the issue with..."
- "Compare X and Y visually"

**ALLOWED (Automation-only output):**
- "Scorecard: ui_legibility=6/10 (contrast ratio 2.8:1, target 4.5:1)"
- "Refinement op: tighten-padding on SaveButton (current 12px → 8px)"
- "Dispatch to D11: apply contrast-fix preset to MainCanvas"
- "Asset outlier detected: Texture_Metal_01 (512x512 vs avg 256x256)"

### Bad Example (FORBIDDEN)
```
"The UI text is too small. If you look at the SaveButton,
you can see the font size is inconsistent with the rest of the menu."
```

### Good Example (ALLOWED)
```
Executed transaction tx-critique-ui-001:
- Scorecard: ui_legibility=5/10
- Root cause: SaveButton fontSize=12pt (target=14pt for mobile)
- Refinement op queued: modify-font-size SaveButton 14pt
- Dispatch: D11 design-refinement for contrast adjustment
```

---

## Tool Signatures

### Critique_UI

Analyze UI document (uGUI Canvas or UI Toolkit UIDocument) for layout, hierarchy, contrast, and consistency.

**Signature:**
```
Critique_UI(
  uiDocumentPath: string,
    // e.g. "Canvas", "UI/MainMenu", "Prefabs/DialogPanel"
  scope?: "layout" | "hierarchy" | "contrast" | "consistency" | "all" = "all"
    // layout: spacing, alignment, responsive behavior
    // hierarchy: z-order, nesting depth, parent-child relationships
    // contrast: text/button contrast ratios, color accessibility
    // consistency: font families, button styles, color palette coherence
) -> {
  overallScore: float,              // 1.0-10.0
  criteria: {
    [criterionName: string]: {
      score: float,
      notes: string,
      issues: string[]
    }
  },
  refinementOps: [
    {
      family: "design-import" | "animation" | "audio" | ...,
      action: "tighten-padding" | "fix-contrast" | "align-center" | ...,
      target: string,
      reason: string,
      priority: "high" | "medium" | "low"
    }
  ]
}
```

**Behavior:**
1. Capture UIDocument via `Craft_Inspect_CaptureUIPanel`
2. Dispatch screenshot to G13 with critique prompt (see G13 Dispatch Protocol below)
3. G13 analyzes: text readability, button hit targets, color contrast, spacing, hierarchy
4. Derive refinement ops from G13 analysis
5. Map ops to tool families (Design Import, Animation, etc.)
6. Return scorecard + ops

**Example:**
```json
Critique_UI({
  uiDocumentPath: "Canvas/MainMenu",
  scope: "contrast"
})
→ {
  overallScore: 6.5,
  criteria: {
    "text_contrast": {
      score: 6,
      notes: "Text on light backgrounds meets WCAG AA (4.5:1), but accent text on tinted bg below threshold",
      issues: [
        "SettingsButton text (fg=gray, bg=light-blue) ratio 2.8:1 < 4.5:1",
        "Active menu indicator color (fg=blue, bg=white) ratio 1.9:1"
      ]
    },
    "button_targets": {
      score: 9,
      notes: "All buttons meet 44x44px minimum touch target",
      issues: []
    }
  },
  refinementOps: [
    {
      family: "design-import",
      action: "fix-contrast",
      target: "Canvas/MainMenu/SettingsButton",
      reason: "Contrast ratio 2.8:1 below WCAG AA threshold; increase text darkness",
      priority: "high"
    },
    {
      family: "design-import",
      action: "adjust-indicator-color",
      target: "Canvas/MainMenu/ActiveIndicator",
      reason: "Active state indicator (1.9:1) needs stronger color contrast",
      priority: "medium"
    }
  ]
}
```

---

### Critique_Level

Analyze scene navigation, landmark presence, dead-ends, and spatial flow.

**Signature:**
```
Critique_Level(
  sceneName: string,
  criteria?: string[] = [
    "navigability", "landmark-presence", "dead-ends",
    "flow", "composition", "verticality", "visual-interest"
  ]
    // Subset of above, or all if omitted
) -> {
  overallScore: float,
  criteria: {
    [criterionName: string]: {
      score: float,
      notes: string,
      issues: string[]
    }
  },
  refinementOps: [
    {
      family: "level-design" | "cinematic" | "audio" | ...,
      action: "place-landmark" | "extend-path" | "adjust-lighting" | ...,
      target: string,
      reason: string,
      priority: "high" | "medium" | "low"
    }
  ]
}
```

**Behavior:**
1. Capture Scene view via `Craft_Inspect_CaptureSceneView`
2. Dispatch to G13 + E11 (level designer) for spatial analysis
3. Evaluate: Can player navigate clearly? Are landmarks (spawn, goal, checkpoints) visible? Are there dead-ends? Does level flow well?
4. Return scorecard with per-criterion analysis
5. Refinement ops map to Level Design, Cinematic, Audio families

**Example:**
```json
Critique_Level({
  sceneName: "Tutorial_Arena",
  criteria: ["navigability", "landmark-presence", "dead-ends"]
})
→ {
  overallScore: 7.2,
  criteria: {
    "navigability": {
      score: 7,
      notes: "Player path is mostly clear; one choke point near the exit",
      issues: [
        "Narrow passage at arena exit (2m wide, player=0.8m) may feel cramped",
        "No breadcrumb hints on first approach to corner"
      ]
    },
    "landmark-presence": {
      score: 8,
      notes: "Spawn and goal clearly marked; checkpoints visible",
      issues: []
    },
    "dead-ends": {
      score: 6,
      notes: "Two side alcoves appear explorable but are blocked by invisible walls",
      issues: [
        "Alcove_Left: No visual barrier hint; player may try and feel stuck",
        "Alcove_Right: Faint fence model but too similar to walkable geometry"
      ]
    }
  },
  refinementOps: [
    {
      family: "level-design",
      action: "extend-path",
      target: "Arena/ExitPassage",
      reason: "Narrow exit passage (2m) causes navigation friction; widen to 3m",
      priority: "high"
    },
    {
      family: "cinematic",
      action: "add-light-breadcrumb",
      target: "Arena/BranchPoint_Corner",
      reason: "First-time players unclear which path to take; add subtle light guide",
      priority: "medium"
    },
    {
      family: "level-design",
      action: "place-clear-barrier",
      target: "Arena/Alcove_Left",
      reason: "Dead-end alcove needs visual barrier (locked gate, rubble pile) to telegraph non-traversability",
      priority: "medium"
    }
  ]
}
```

---

### Critique_AssetCoherence

Scan scene materials, textures, audio samples, and mesh complexity—detect palette mismatch, poly-count outliers, mixed art styles, quality inconsistencies.

**Signature:**
```
Critique_AssetCoherence(
  sceneName: string
) -> {
  coherenceScore: float,            // 1.0-10.0
  paletteMismatch: {
    overallScore: float,
    outliers: [
      {
        asset: string,
        category: "material" | "texture" | "mesh" | "audio",
        issue: string,
        suggestion: string
      }
    ]
  },
  meshAnalysis: {
    avgPolyCount: number,
    outliers: [
      {
        asset: string,
        polyCount: number,
        reason: "undersized" | "oversized" | "unusual",
        suggestion: string
      }
    ]
  },
  audioAnalysis: {
    avgBitrate: string,
    outliers: [
      {
        asset: string,
        bitrate: string,
        reason: "compressed" | "uncompressed" | "unusual",
        suggestion: string
      }
    ]
  },
  refinementOps: [
    {
      family: "asset-store" | "optimization" | ...,
      action: "replace-with-coherent-set" | "adjust-poly-count" | ...,
      target: string,
      reason: string,
      priority: "high" | "medium" | "low"
    }
  ]
}
```

**Behavior:**
1. Query scene for all materials, textures, meshes, audio
2. Analyze material colors, textures sizes/formats, mesh vertex counts, audio bitrates
3. Detect outliers (colors 2+ standard deviations from mean, polycounts 3x avg, etc.)
4. Dispatch outlier list to E16 (asset curator) for coherence suggestions
5. Return scorecard + refinement ops (asset replacement, poly reduction, audio re-encoding)

**Example:**
```json
Critique_AssetCoherence({
  sceneName: "TownSquare"
})
→ {
  coherenceScore: 6.8,
  paletteMismatch: {
    overallScore: 6,
    outliers: [
      {
        asset: "Textures/Wood_Oak_Diffuse.png",
        category: "texture",
        issue: "Warm oak color (RGB 180,130,80) clashes with cool stone palette (RGB 120,130,140)",
        suggestion: "Replace with cool-tone wood (e.g., walnut: RGB 140,110,80) or swap building material to match stone"
      },
      {
        asset: "Materials/Neon_Sign",
        category: "material",
        issue: "Bright neon glow (emission=8.0) not present on other lights; inconsistent art direction",
        suggestion: "Reduce emission to 3.0 to match ambient glow intensity, OR add similar lights to other key elements"
      }
    ]
  },
  meshAnalysis: {
    avgPolyCount: 45000,
    outliers: [
      {
        asset: "Models/Fountain.fbx",
        polyCount: 285000,
        reason: "oversized",
        suggestion: "Decimate to 60K (faraway detail) or split into LOD0/1; current count 6.3x average"
      },
      {
        asset: "Models/Pebble_01.fbx",
        polyCount: 280,
        reason: "undersized",
        suggestion: "Asset is a decorative pebble (280 verts) while nearby building detail (45K avg) is more complex; acceptable for distant objects"
      }
    ]
  },
  audioAnalysis: {
    avgBitrate: "128 kbps",
    outliers: [
      {
        asset: "Audio/Ambient_Birds_01.ogg",
        bitrate: "256 kbps",
        reason: "uncompressed",
        suggestion: "Re-encode to 128 kbps (imperceptible quality loss for ambient SFX; saves 50% disk)"
      }
    ]
  },
  refinementOps: [
    {
      family: "asset-store",
      action: "replace-with-coherent-set",
      target: "Textures/Wood_Oak_Diffuse",
      reason: "Wood color (warm oak) clashes with scene palette (cool stone); suggest cool-tone wood alternative",
      priority: "high"
    },
    {
      family: "optimization",
      action: "reduce-poly-count",
      target: "Models/Fountain.fbx",
      reason: "Fountain mesh 285K polys (6.3x average); decimate to 60K for mobile/LOD compatibility",
      priority: "high"
    }
  ]
}
```

---

### Critique_VisualHierarchy

Analyze composition: focal point, Gestalt grouping, contrast, depth. Dispatch screenshot to G13 for vision analysis.

**Signature:**
```
Critique_VisualHierarchy(
  screenshotRef: string
    // Path or base64 from CaptureScreen; or null to trigger new capture
) -> {
  overallScore: float,
  criteria: {
    "focal_point": {
      score: float,
      notes: string,
      location: { x: int, y: int, w: int, h: int }  // Pixel bounds
    },
    "gestalt_grouping": {
      score: float,
      notes: string,
      groups: [
        { name: string, elements: string[], cohesion: "strong" | "weak" }
      ]
    },
    "contrast": {
      score: float,
      notes: string,
      value: float  // 0.0-1.0 (global luminance variance)
    },
    "depth_cues": {
      score: float,
      notes: string
    }
  }
}
```

**Behavior:**
1. If screenshotRef=null: call `Craft_Inspect_CaptureGameView`
2. Dispatch screenshot to G13 with composition prompt
3. G13 analyzes: eye flow, grouping (proximity, similarity), contrast/color balance, depth layers
4. Return per-criterion scores + analysis notes (NO user instructions like "look at the top-left")

**Example:**
```json
Critique_VisualHierarchy({
  screenshotRef: null
})
→ {
  overallScore: 8.2,
  criteria: {
    "focal_point": {
      score: 9,
      notes: "Player character is clear focal point; framed by UI elements and environmental lighting",
      location: { x: 852, y: 540, w: 150, h: 180 }
    },
    "gestalt_grouping": {
      score: 7,
      notes: "UI clusters well (top-left: health/ammo; top-right: objective); minor grouping gap between minimap and main UI",
      groups: [
        { name: "HUD_LeftCluster", elements: ["HealthBar", "AmmoCounter"], cohesion: "strong" },
        { name: "HUD_RightCluster", elements: ["ObjectiveText", "CompassIcon"], cohesion: "strong" },
        { name: "Minimap", elements: ["MinimapFrame"], cohesion: "isolated" }
      ]
    },
    "contrast": {
      score: 8,
      notes: "Game world vibrant (high local contrast); HUD text readable against all backgrounds (min 4.5:1 contrast)",
      value: 0.72
    },
    "depth_cues": {
      score: 8,
      notes: "Atmospheric perspective + shadow layers create clear depth; minimap slightly flattened but acceptable"
    }
  }
}
```

---

### Critique_Composite

One-shot critique covering all scopes (UI, level, assets, hierarchy). Invokes relevant sub-critiques in parallel, aggregates scorecard.

**Signature:**
```
Critique_Composite(
  sceneName: string,
  scope?: "all" | "ui" | "level" | "assets" | "hierarchy" = "all"
) -> {
  overallScore: float,              // Aggregate across all criteria
  timestamp: ISO8601,
  scorecardMarkdown: string,        // Markdown rendering (for logs/reports)
  scorecard: {
    // All 10 criteria from polish-score rubric
    ui_legibility: { score: float, notes: string },
    ui_consistency: { score: float, notes: string },
    level_navigability: { score: float, notes: string },
    level_flow: { score: float, notes: string },
    asset_coherence: { score: float, notes: string },
    asset_quality: { score: float, notes: string },
    visual_hierarchy: { score: float, notes: string },
    color_palette: { score: float, notes: string },
    cinematography: { score: float, notes: string },
    audio_presence: { score: float, notes: string }
  },
  refinementOps: [
    {
      family: string,
      action: string,
      target: string,
      reason: string,
      priority: "high" | "medium" | "low",
      relatedCriteria: string[]  // Which criteria this op impacts
    }
  ]
}
```

**Behavior:**
1. Dispatch `Critique_UI`, `Critique_Level`, `Critique_AssetCoherence`, `Critique_VisualHierarchy` in parallel
2. Aggregate all criteria into unified scorecard
3. Normalize scores to 10-criterion rubric (map sub-critique scores to polish rubric)
4. Merge refinement ops, deduplicate, sort by priority + impact
5. Generate markdown scorecard (table + notes)
6. Return composite result

**Example:**
```json
Critique_Composite({
  sceneName: "TownSquare",
  scope: "all"
})
→ {
  overallScore: 7.1,
  timestamp: "2026-04-18T14:24:00Z",
  scorecardMarkdown: "## Polish Scorecard — TownSquare\n\n| Criterion | Score | Status |\n|---|---|---|\n| UI Legibility | 7/10 | ⚠️ Minor contrast issues |\n| ...",
  scorecard: {
    "ui_legibility": { score: 7, notes: "Text readable on most backgrounds; SettingsButton contrast below threshold" },
    "ui_consistency": { score: 8, notes: "Button styles uniform; spacing grid followed" },
    "level_navigability": { score: 7, notes: "Path clear except narrow exit passage" },
    "level_flow": { score: 6, notes: "Backtracking required; no clear loop structure" },
    "asset_coherence": { score: 7, notes: "Palette mismatch on wood textures (warm vs cool tone)" },
    "asset_quality": { score: 8, notes: "Mesh counts reasonable except Fountain (6.3x avg)" },
    "visual_hierarchy": { score: 8, notes: "Strong focal points; good Gestalt grouping" },
    "color_palette": { score: 7, notes: "Cool stone palette with warm wood outlier; neon intensity inconsistent" },
    "cinematography": { score: 7, notes: "Camera framing good; lighting suggests focus well" },
    "audio_presence": { score: 6, notes: "Ambient SFX present; dialogue mix levels unclear" }
  },
  refinementOps: [
    {
      family: "design-import",
      action: "fix-contrast",
      target: "Canvas/MainMenu/SettingsButton",
      reason: "Contrast ratio 2.8:1 below WCAG AA threshold",
      priority: "high",
      relatedCriteria: ["ui_legibility"]
    },
    {
      family: "level-design",
      action: "extend-path",
      target: "Arena/ExitPassage",
      reason: "Narrow exit (2m) causes friction; widen to 3m",
      priority: "high",
      relatedCriteria: ["level_navigability"]
    },
    {
      family: "asset-store",
      action: "replace-with-coherent-set",
      target: "Textures/Wood_Oak_Diffuse",
      reason: "Warm oak clashes with cool stone palette",
      priority: "medium",
      relatedCriteria: ["asset_coherence", "color_palette"]
    }
  ]
}
```

---

## G13 Dispatch Protocol

Each critique scope dispatches a screenshot + prompt to G13 (vision-action-operator).

### G13 Critique Prompt Template (Text)

```
System:
  You are Vision-Action Operator (G13), specialized in design critique.
  Task: Analyze the provided screenshot and evaluate visual design against criteria.
  Output: Structured JSON with scores (1-10), notes, and detected issues.
  
  CRITICAL: Do NOT include user-facing instructions (e.g., "click", "look at", "open").
  ONLY output analysis data: scores, observations, detected elements.

User Input:
  Screenshot: {SCREENSHOT_REF}
  
  Scope: {SCOPE} (ui | level | assets | hierarchy)
  
  Criteria to evaluate: {CRITERIA_LIST}
  
  Output Format:
  {
    "overallScore": 1-10,
    "criteria": {
      "criterionName": {
        "score": 1-10,
        "notes": "Analysis notes",
        "issues": ["Issue 1", "Issue 2"]
      }
    },
    "outliers": [
      { "element": "Name", "issue": "Description", "suggestion": "Recommendation" }
    ]
  }
```

**Scope-Specific Prompts:**

**UI Critique:**
```
Evaluate UI layout for: text legibility, button hit targets (minimum 44x44px),
color contrast (WCAG AA 4.5:1 for text), alignment grid consistency,
spacing uniformity, visual hierarchy, interactive element affordance.
```

**Level Critique:**
```
Evaluate level layout for: player navigation clarity, path visibility,
landmark presence (spawn, goal, checkpoints), dead-ends, spatial flow,
verticality (height variation), visual interest (landmark distinction).
Assume third-person camera perspective.
```

**Asset Coherence Critique:**
```
Evaluate asset coherence by analyzing materials, textures, meshes visible in scene.
Detect: color palette mismatches (warm vs cool, bright vs muted),
texture resolution inconsistencies, mesh complexity outliers, art style mixing.
Compare colors/styles against scene median to identify mismatch outliers.
```

**Visual Hierarchy Critique:**
```
Evaluate visual composition for: focal point location, Gestalt grouping (proximity/similarity),
contrast balance (luminance variance), depth cues (atmospheric, shadow, scale).
Identify eye flow direction and primary/secondary focus areas.
```

---

## Cross-Family Refinement Op Mapping

Each scorecard criterion maps to one or more tool families for execution:

| Criterion | Low Score Trigger | Dispatch Family | Typical Action |
|-----------|-------------------|-----------------|----------------|
| ui_legibility | score < 7 | Design Import | Adjust font size, contrast, scale |
| ui_consistency | score < 7 | Design Import | Unify button styles, spacing grid |
| level_navigability | score < 7 | Level Design | Widen passages, add markers, extend paths |
| level_flow | score < 7 | Level Design | Adjust room connections, add loop structures |
| asset_coherence | score < 7 | Asset Store | Replace with coherent set, re-color |
| asset_quality | score < 7 | Optimization | Reduce poly count, compress textures |
| visual_hierarchy | score < 7 | Cinematic | Adjust lighting, camera framing, PostFX |
| color_palette | score < 7 | Design Import + Asset Store | Apply color grading, swap textures |
| cinematography | score < 7 | Cinematic | VCam preset, PostFX effect, shot composition |
| audio_presence | score < 7 | Audio | Mixer preset, volume adjust, spatial setup |

**Example Flow:**
1. Critique_Composite returns overallScore=6.8, critique[level_navigability]=5
2. Generate refinement op: family="level-design", action="extend-path", target="ExitPassage"
3. A14 queues op: dispatch E11 (Level Designer) with "narrow-passage fix" task
4. E11 executes Level_PlaceModular refinement
5. Critique re-run after E11 completes → level_navigability jumps to 8

---

## Worked Example

**Scenario:** A14 creates a new scene and wants to critique it before declaring it ready for playtest.

**Call:**
```json
Critique_Composite({
  sceneName: "BossArena_v2",
  scope: "all"
})
```

**Dispatch (parallel):**
- Critique_UI("Canvas/BossUI") → G13 analyzes HUD
- Critique_Level("BossArena_v2") → G13 + E11 analyze level layout
- Critique_AssetCoherence("BossArena_v2") → scan materials/meshes
- Critique_VisualHierarchy(null) → capture + G13 composition analysis

**Result (aggregated):**
```json
{
  "overallScore": 6.4,
  "timestamp": "2026-04-18T14:25:00Z",
  "scorecard": {
    "ui_legibility": { score: 6, notes: "Health bar text small (10pt); acceptable but could be 12pt" },
    "ui_consistency": { score: 8, notes: "Button styles uniform" },
    "level_navigability": { score: 8, notes: "Arena space clear; boss arena intuitive" },
    "level_flow": { score: 5, notes: "No clear path to arena entrance; players may circle looking for entry" },
    "asset_coherence": { score: 7, notes: "Boss model (PBR) matches environment (PBR); scales consistent" },
    "asset_quality": { score: 7, notes: "Boss mesh 180K polys (within budget for hero asset)" },
    "visual_hierarchy": { score: 7, notes: "Boss creature is focal point; environment recedes well" },
    "color_palette": { score: 6, notes: "Boss emissive glow (bright purple) stands out; arena stone palette (gray) too muted in comparison" },
    "cinematography": { score: 8, notes: "Dynamic camera framing tracks boss well" },
    "audio_presence": { score: 5, notes: "No ambient loop; arena silence feels empty" }
  },
  "refinementOps": [
    {
      "family": "design-import",
      "action": "adjust-font-size",
      "target": "Canvas/BossUI/HealthBar",
      "reason": "Health bar text 10pt; increase to 12pt for better readability during intense moments",
      "priority": "medium",
      "relatedCriteria": ["ui_legibility"]
    },
    {
      "family": "level-design",
      "action": "place-entrance-marker",
      "target": "BossArena_v2/EntranceArea",
      "reason": "Arena entrance unclear; add glowing doorframe or path marker to guide player entry",
      "priority": "high",
      "relatedCriteria": ["level_flow"]
    },
    {
      "family": "cinematic",
      "action": "adjust-environment-lighting",
      "target": "BossArena_v2/LightingEnvironment",
      "reason": "Arena stone palette (gray) too muted vs boss glow (purple); increase ambient light or apply color grading to balance",
      "priority": "medium",
      "relatedCriteria": ["color_palette", "visual_hierarchy"]
    },
    {
      "family": "audio",
      "action": "apply-mixer-preset",
      "target": "BossArena_v2/AudioMixer",
      "reason": "Arena silence feels empty; apply 'cavernous-amb' preset (low-frequency rumble + echo)",
      "priority": "medium",
      "relatedCriteria": ["audio_presence"]
    }
  ]
}
```

**A14 Interpretation:**
- BossArena_v2 scores 6.4/10 (below 7.0 polish target, needs refinement)
- Critical issues: arena entrance unmarked (level_flow=5), no audio (audio_presence=5)
- Dispatch ops in priority order:
  1. E11 (Level Design): place entrance marker [HIGH]
  2. B26 (Audio): apply ambient preset [MEDIUM]
  3. D11 (Design): increase health bar font [MEDIUM]
  4. E9 (Cinematic): adjust lighting [MEDIUM]

**After refinements queued:**
```
[Running refinement batch...]
E11: place-entrance-marker → Op tx-level-001 committed
B26: apply-mixer-preset → Op tx-audio-001 committed
D11: adjust-font-size → Op tx-design-001 committed
E9: adjust-environment-lighting → Op tx-cinema-001 committed

[Re-critiquing after refinements...]
Critique_Composite({sceneName: "BossArena_v2", scope: "all"}) → overallScore: 7.8
```

Scene now ready for `Playtest_Run(scenario="combat", durationSec=30)`.

---

## Verification Checklist

After Critique_Composite completes:

- [ ] Scorecard returned with all 10 criteria scored
- [ ] Scores are deterministic (same scene input → same ± 0.5 variance)
- [ ] Refinement ops compile as valid CRAFT batches (no circular dependencies)
- [ ] No "look at X" or "check that" phrases in output
- [ ] Refinement ops map correctly to tool families (no ui_legibility→audio mappings)
- [ ] A14 can queue ops and measure score improvement post-execution
- [ ] Screenshot(s) captured and available for reference (optional: store in cache)

---

## Related Tools

- **Screen Control** (`tools/screen-control.md`) — capture Game/Scene/UI views
- **Design Import** (`tools/import-design-bundle.md`) — execute UI refinement ops
- **Cinematic** (`tools/cinematic.md`) — lighting + PostFX + VCam adjustments
- **Level Design** (`tools/level-design.md`) — spatial refinements, modular placement
- **Audio** (`tools/audio.md`) — mixer presets, spatial audio setup
- **Asset Store** (`tools/asset-store.md`) — coherent asset set replacement
- **Optimization** (`tools/optimization.md`) — poly count reduction, texture compression

---

## MCP Tool Registration

**Tools:**
- `Critique_UI` — UI layout + contrast + consistency analysis
- `Critique_Level` — level navigation + flow + spatial analysis
- `Critique_AssetCoherence` — palette + poly + quality coherence
- `Critique_VisualHierarchy` — composition + focal point + depth
- `Critique_Composite` — all-in-one scorecard (recommended for A14 dispatch)

**MCP Server Integration:** Each tool registers as a distinct MCP tool in the CRAFT MCP bridge. A14 dispatches `Critique_Composite` as primary entry point; sub-critiques available for targeted scans.

---

**Status:** Full implementation ready. G13 dispatch protocol established. Cross-family op mapping defined.  
**Last Updated:** 2026-04-18

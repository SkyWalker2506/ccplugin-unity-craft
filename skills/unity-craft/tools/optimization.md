# Performance Optimization Tool

## Purpose

Holistic cross-platform Unity performance analysis and optimization. Dispatches to **B53 unity-performance-analyzer** agent for profiler interpretation, batching strategy, texture compression, LOD analysis, quality settings tuning, asset purging, and shader variant stripping. Integrates CRAFT-safe operations (ModifyComponent, TextureImporter overrides) with recommendations for Editor scripts when operations exceed CRAFT's scope.

## Tool Signatures

### Optimize_Analyze

**Purpose:** Comprehensive performance audit of a scene or entire project.

```
Optimize_Analyze(
  scope: "scene" | "project",
  target: "mobile" | "desktop" | "console"
)
```

**Returns:** Structured performance report with baseline metrics and prioritized fix list.

**Output Format:**
```
## Performance Report — {scope} / {target}

### Baseline Metrics
- FPS: {n}
- Draw Calls: {n}
- SetPass Calls: {n}
- Triangle Count: {M}M
- Memory: {MB}MB
- GC Alloc/frame: {KB}KB

### Top 5 Fixes (by ROI)
1. [HIGH] Texture compression — 38 textures at RGBA32 → ASTC 6x6 (mobile) — est. -45% memory
2. [HIGH] Static batching — 156 unbatched objects → 12 batches — est. -32% draw calls
3. [MEDIUM] LOD setup — 8 hero meshes missing LOD1/LOD2 — est. -18% tris at distance
4. [MEDIUM] Shader variants — 512 unused variants in build — est. -120MB build size
5. [LOW] Canvas UI — 2 canvases rebuild every frame → mark static — est. -8% CPU

### Dispatch to B53
Report and recommended priorities sent to B53 for deep-dive profiler analysis.
```

### Optimize_Batch

**Purpose:** Evaluate and configure static batching + SRP Batcher compatibility.

```
Optimize_Batch(
  scene: string
)
```

**Output:**
```
## Batching Analysis — {scene}

### Static Batching
- Current batches: 24
- Unbatched objects: 156 (flags: hasAnimator=12, hasDynamicScale=44, hasBoneWeights=100)
- Recommended batches: 12 (merge by material + shader variant)
- Est. draw call reduction: 68→24 (-65%)

### SRP Batcher Compatibility
- Compatible materials: 34/41 (83%)
- Incompatible: 7 (reasons: custom properties, GPU instancing disabled)
- Recommendation: Enable GPU instancing on 7 materials

### Implementation Steps
1. Run Assets/Editor/OptimizeBatch.cs → generates merged meshes
2. Verify static flags via script output log
3. Test scene FPS before/after (toggle batching flag)
```

**Note:** Some operations require Editor script execution (OptimizeBatch.cs) — not CRAFT-safe due to AssetDatabase access.

### Optimize_Textures

**Purpose:** Apply platform-specific texture compression presets.

```
Optimize_Textures(
  folder: string,        // Assets/Textures/Environment
  preset: "mobile" | "desktop" | "atlas"
)
```

**Uses:** CRAFT_SetTextureImporter to override TextureImporter settings per platform.

**Output:**
```
## Texture Optimization — {folder}

### Applied Preset: {preset}
- Mobile: ASTC 6x6, maxSize 1024, crunchCompression=true
- Desktop: BC7, maxSize 2048, anisotropicFiltering=ForceEnable
- Atlas: ASTC 4x4, maxSize 2048, packingTag="UI"

### Changes
- 38 textures updated
- Est. memory reduction: 156MB → 72MB (-54%)
- Est. VRAM reduction: 89MB → 34MB (-62%)

### Verification
- Monitor Profiler → Memory → Texture Category post-import
- Check Profiler window → GPU Memory before/after
```

### Optimize_LOD

**Purpose:** Generate LOD groups and simplify meshes for hero assets.

```
Optimize_LOD(
  meshAssetPath: string,           // Assets/Models/Character.fbx
  levels: [0.6, 0.3, 0.1]          // Distance thresholds
)
```

**Output:**
```
## LOD Group Setup — {meshAssetPath}

### Configuration
- LOD0: Full mesh (screenSize=1.0)
- LOD1: 60% of original vertices (screenSize=0.6)
- LOD2: 30% of original vertices (screenSize=0.3)
- LOD3: 10% of original vertices (screenSize=0.1)

### Process
1. CRAFT creates LODGroup component (via ModifyComponent)
2. External: User runs mesh simplification tool (e.g., Simplygon plugin)
3. CRAFT wires simplified mesh assets into LOD slots

### Est. Performance
- Mid-distance: -18% tris
- Far-distance: -75% tris
- FPS gain at 50m+: +8-12%
```

**Note:** Mesh simplification (step 2) is non-CRAFT and requires external tool or manual Artist work.

### Optimize_Quality

**Purpose:** Apply quality preset (mobile-low, mobile-high, desktop, console) to QualitySettings and render pipeline assets.

```
Optimize_Quality(
  preset: "mobile-low" | "mobile-high" | "desktop" | "console"
)
```

**Uses:** CRAFT_ModifyComponent to update QualitySettings and URP/HDRP asset references.

**Output:**
```
## Quality Settings Applied — {preset}

### QualitySettings
- pixelLightCount: {n}
- shadowResolution: {enum}
- shadowDistance: {float}m
- antiAliasing: {0|2|4|8}x
- vSyncCount: {0|1}
- masterTextureLimit: {0|1}
- anisotropicFiltering: {Disable|Enable|ForceEnable}
- lodBias: {float}

### URP Asset Overrides
- renderScale: {0.75|1.0}
- shadowDistance: {float}m
- msaaSampleCount: {1|2|4|8}
- cascadeCount: {1|2|4}
- supportsDynamicResolution: {bool}
- maxVisibleLights: {n}

### Runtime FPS Expectation
- Mobile-Low: 30fps (Mali/Adreno)
- Mobile-High: 60fps (Flagship)
- Desktop: 60+fps (Gaming PC)
- Console: 60fps (PS5/Xbox SX)
```

### Optimize_Purge

**Purpose:** Identify unused and duplicate assets for cleanup.

```
Optimize_Purge(
  dryRun: true | false
)
```

**Output:**
```
## Asset Purge Report (Dry Run)

### Unused Assets
- 23 textures never referenced in scenes or prefabs
- 8 materials unused by any renderer
- 12 shader variants not included in any LOD/quality preset
- Total: 156MB candidate for deletion

### Duplicate Textures
- Texture_Grass_v1.png and Texture_Grass_v2.png (identical pixel data)
- 2 copies of 512KB character diffuse texture
- Total: 2.1MB can be consolidated

### Oversized Meshes
- Character_HighPoly.fbx: 2.4M vertices → LOD0 only, LOD1/2 missing
- Environment_Cliffs.fbx: 890K vertices → consider mesh splitting

### Recommendation
Run with dryRun=false to delete candidates. CRAFT does NOT support recursive asset deletion — use Assets/Editor/PurgeUnused.cs script.
```

**Note:** Asset deletion requires Editor script — beyond CRAFT scope.

### Optimize_Profile

**Purpose:** Capture performance profile over duration and save to disk.

```
Optimize_Profile(
  durationSec: 30,
  outputPath: "Assets/Profiling/session_001.prof"
)
```

**Uses:** Upstream CRAFT_ProfileCapture or direct Profiler API.

**Output:**
```
## Profile Captured
- Duration: 30s
- Frame range: 1800 frames @ 60fps
- Output: Assets/Profiling/session_001.prof
- Profiler window opens automatically
```

### Optimize_Shaders

**Purpose:** Analyze shader variant complexity and recommend stripping.

```
Optimize_Shaders(
  target: "all" | "urp-lit" | "hdrp-lit"
)
```

**Output:**
```
## Shader Variant Report — {target}

### Variant Complexity
- Total variants in project: 2847
- Compiled (in current scene): 412
- Never used: 2435 (-86% bloat)

### Top 5 Variant Generators
1. Universal Lit: 1456 variants (keywords: MAIN_LIGHT, ADDITIONAL_LIGHTS, etc.)
2. Standard Surface: 840 variants
3. Particles/Lit: 512 variants

### Stripping Recommendations
1. Disable "Instancing" keyword for static geometry (-340 variants)
2. Remove "Fog" support for indoor-only scenes (-128 variants)
3. Limit "AdditionalLights" to mobile/desktop only (-45 variants)

### Est. Build Size Reduction
- Current: 450MB
- Post-strip: 280MB (-38%)

### Implementation
Run Assets/Editor/VariantStripper.cs → generates ShaderVariantCollection
```

## Pipeline

### B53 Dispatch Protocol

1. **User calls Optimize_Analyze** → generates baseline report
2. **Report sent to B53** → agent interprets Profiler data, prioritizes fixes
3. **B53 returns action list:**
   - Priority 1-2 (HIGH): Auto-apply via CRAFT (ModifyComponent, SetTextureImporter)
   - Priority 3-4 (MEDIUM): Surface as Editor scripts (OptimizeBatch.cs, VariantStripper.cs)
   - Priority 5+ (LOW): User decision required
4. **User approves → CRAFT executes** or **Editor script runs**

### Example Workflow

```
[User] "Analyze my mobile scene for performance"
  ↓
[Optimize_Analyze] scene / mobile
  ↓
[B53] Interprets profiler → prioritizes: 
  1. Texture RGBA32 → ASTC
  2. Unbatched objects
  3. LOD setup
  4. Shader variants
  ↓
[CRAFT] Applies texture presets (safe) + ModifyComponent for QualitySettings
  ↓
[Editor Script] User runs OptimizeBatch.cs + VariantStripper.cs (requires consent)
  ↓
[Verify] Re-profile → measure FPS/draw call delta
```

## Response Format — Optimize_Analyze Output

All performance reports follow this structure:

```markdown
## Performance Report — {scope} / {target}

Baseline: FPS {n}, DrawCalls {n}, SetPass {n}, Tris {M}M, Memory {MB}MB, GC/frame {KB}KB

### Top 5 Fixes (by ROI)
1. [HIGH] Category — description — est. impact
2. [HIGH] ...
...

### Dispatch to B53
Detailed metrics and logs sent to agent for prioritization.
```

## Example Scenarios

### Scenario 1: Audit Mobile Build Performance

```
User: "My iOS build is dropping to 25fps in crowded scenes."

1. Optimize_Analyze(scope="scene", target="mobile")
   → Finds: 45 RGBA32 textures, 180 draw calls, 2.1M tris
   
2. B53 feedback:
   - Texture compression: -45% memory, -28% VRAM bandwidth
   - Static batching: -45 draw calls (-25%)
   
3. CRAFT applies: Optimize_Textures(preset="mobile")
   → Sets ASTC 6x6 for all textures
   
4. User runs: OptimizeBatch.cs
   → Merges meshes → 24 batches
   
5. Re-profile: FPS now stable at 55fps
```

### Scenario 2: Reduce Draw Calls on Hero Scene

```
User: "Main character scene has 127 draw calls. Target: <60."

1. Optimize_Batch(scene="HeroScene")
   → Identifies 156 unbatched objects
   
2. CRAFT recommendation:
   - Merge by material group
   - Enable GPU instancing
   
3. User runs: OptimizeBatch.cs
   → Result: 24 batches, 68 draw calls
```

### Scenario 3: Strip Unused Shader Variants for Build

```
User: "Build size 680MB is too large. Focus on shaders."

1. Optimize_Shaders(target="all")
   → Finds 2435 unused variants (-86%)
   
2. B53 priorities:
   - Instancing: -340 variants
   - Fog: -128 variants
   - Additional Lights: -45 variants
   
3. User runs: VariantStripper.cs
   → Generates ShaderVariantCollection
   
4. Build size: 680MB → 410MB (-40%)
```

## Verification Checklist

After applying presets and fixes:

- [ ] FPS before/after measured (frame timing stable, 30+ samples)
- [ ] Draw call count reduced by target % (profiler verified)
- [ ] Memory reduction meets estimate (Profiler → Memory)
- [ ] Texture visual quality acceptable (PSNR > 30dB for compressed assets)
- [ ] No shader compilation errors (Console log clean)
- [ ] Editor scripts ran without errors (check Assets/Editor output log)
- [ ] Scene loads/runs without crashes
- [ ] Rollback plan documented (transaction IDs from CRAFT ops)

## Related Tools

- **CRAFT_Execute** — safe GameObject/Component operations
- **CRAFT_Query** — find targets before modification
- **CRAFT_ModifyComponent** — update QualitySettings, URP assets
- **CRAFT_SetTextureImporter** — texture compression presets
- **CRAFT_ProfileCapture** — capture performance data
- **B53 Agent** — profiler interpretation, fix prioritization

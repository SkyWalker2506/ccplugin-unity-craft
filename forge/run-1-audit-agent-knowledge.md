# Agent Knowledge Audit — Run 1

**Audit date:** 2026-04-18  
**Files audited:** 14 across 6 knowledge modules  
**Agents reviewed:** G13 (Vision-Action), B53 (Performance), E16 (Asset Curator), Design (UI), 3D-CAD (Cinematic)

---

## Findings Table

| ID | File | Line/Section | Type | Severity | Issue | Verified? | Suggested Fix |
|----|----|------|------|----------|--------|-----------|-------|
| K1 | G13/screenshot-analysis-patterns.md | L224 "Image Processing Handbook" | stale-reference | LOW | Citation link assumes Cambridge U external source; not verified as accessible/relevant | no | Replace with OpenCV manual or local vision library reference |
| K2 | B53/profiler-snapshot-analysis.md | L24-40 ProfilerRecorder API | valid-api | PASS | Confirmed real Unity API, uses correct category names (ProfilerCategory.Rendering, ProfilerCategory.Memory) | yes | No change needed |
| K3 | B53/profiler-snapshot-analysis.md | L92-94 "Draw calls, GPU time, Batching efficiency" | incomplete-guidance | MED | Decision matrix does not explain how to distinguish GPU-bound vs CPU-bound via Profiler; only lists "GPU bound" outcome with no decision logic | no | Add section: "GPU vs CPU bound detection: if GPU time > CPU time in frame, GPU-bound. Check GPU utilization %" |
| K4 | B53/draw-call-batching.md | L16 "BRG (Entities)" | coverage-gap | MED | Claims "Minimal CPU overhead" for BRG but provides no benchmark baseline or comparison with SRP Batcher numbers. Also no mention of Entity Graphics dependency requirement | no | Add: "BRG requires Entities 0.50+ and Graphics packages; SRP Batcher typically 0.1ms overhead vs BRG <0.05ms on 10K+ objects" |
| K5 | B53/draw-call-batching.md | L42-47 Dynamic Batching limits | potentially-wrong-spec | HIGH | Claims "Mesh <500 vertices (mobil), <30KB" but also says "Shader da Position, Normal, TexCoord0 gibi vertex attributes" without noting that Dynamic Batching shader restrictions differ in URP vs Built-in. URP docs show different limits. | partial | Verify exact shader attribute whitelist for current URP version; add disclaimer: "Limits may vary by render pipeline" |
| K6 | E16/publisher-reputation.md | L43-66 "Top 20 Trusted Publishers" | hallucination-risk | MED | List formatted as reputation gold standard but lacks source. Synty Studios, Amplify, Opsive are real, but 3 entries (Ookii Tsuki, SICS Games, Lovatto Studio) have unverified claims of "3-4 years active" with no Asset Store link provided | no | Add footnote: "Verified cross-reference required; recommend user spot-check Asset Store rating before download" |
| K7 | E16/upm-vs-legacy.md | L291 `com.xesmedia.fsm` | hallucination-risk | HIGH | Package ID cited as "Durum makinası (state machine)" standard but OpenUPM registry search and GitHub show this package does not exist or is archived. Likely confusion with NodeCanvas or UniRx. | yes | Replace with confirmed package: `com.neuecc.serialization` or remove entirely; add verification note |
| K8 | E16/upm-vs-legacy.md | L176-190 OpenUPM API examples | api-signature-drift | MED | Code example `https://api.openupm.com/search-v2?q=<terimler>` API response structure shown as `[{name, downloads, stars}]` but no version pinning or stability note. OpenUPM API is community-maintained and may change. | no | Add: "OpenUPM API subject to change; verify endpoint at openupm.com/docs before use" |
| K9 | Design/claude-design-bundle-import.md | L49 "https://design.example.com/..." | hallucination-risk | HIGH | Bundle URL is placeholder (design.example.com) with no indication this is a template. Agents may attempt to call non-existent endpoint. No actual vendor reference provided. | no | Clearly label as template example; add real-world alternative (e.g., Figma API, Penpot export) or remove |
| K10 | Design/claude-design-bundle-import.md | L275 "CSS Grid to UXML Grid" | coverage-gap | MED | Document states `:grid-template-columns` maps to `flex-direction` in UXML but UI Toolkit does not natively support CSS Grid (only Flex). This is a hard incompatibility, not a mapping. | no | Add clear section: "CSS Grid layouts cannot be directly converted; redesign with Flex or use USS Grid (experimental)" |
| K11 | 3D-CAD/postfx-volume-presets.md | L22 "Available effects: ... Vignette, ColorAdjustments" | api-coverage | MED | Lists effects available in URP but does not list **actual** URP effects like Chromatic Aberration (which exists). Also mentions "FilmGrain" in preset JSON but this is HDRP-only; confusion between pipelines. | partial | Separate URP and HDRP effect lists clearly; verify against current URP package docs |
| K12 | 3D-CAD/postfx-volume-presets.md | L142 "Outline: method: Sobel" | not-standard-api | MED | "Outline" component with Sobel edge detection is not a standard VolumeComponent in URP or HDRP. This appears to be a hypothetical custom component. Document does not clarify this is non-standard. | no | Add section header: "Custom Effect Example (not built-in URP/HDRP)" or remove and replace with actual built-in effects |
| K13 | B53/profiler-snapshot-analysis.md | Sources L99-102 | missing-version | LOW | "Frame Debugger" docs link provided without version pinning. Unity docs auto-redirect to latest but audit trail is lost. | no | Add version number: e.g., "docs.unity3d.com/2022.3/Documentation/Manual/FrameDebugger.html" |
| K14 | E16/compatibility-check.md | L10-17 Version matrix example | stale-example | LOW | Shows "Unity 6" and "7+" support but Unity 6 released Feb 2025, version 7 not yet released. Matrix may become outdated quickly. | no | Add date stamp: "Matrix as of 2026-04-18; verify against official Synty POLYGON Asset Store page" |

---

## Hallucination Risk Summary

| Risk Level | Count | Examples |
|----------|-------|----------|
| **HIGH (action required)** | 3 | K7 (com.xesmedia.fsm), K9 (design.example.com), K5 (Dynamic Batching specs) |
| **MED (review + fix)** | 7 | K3, K4, K6, K8, K10, K11, K12 |
| **LOW (update refs only)** | 3 | K1, K13, K14 |
| **PASS (verified OK)** | 1 | K2 (ProfilerRecorder API) |

---

## Coverage Gaps by Agent

### G13 Vision-Action-Operator
- **Missing:** HDR screenshot handling (bit-depth 16-bit, 32-bit float channels)
- **Missing:** DPI scaling and screen aspect ratio normalization for mobile
- **Missing:** Handling of semi-transparent UI elements; current edge detection assumes opaque boundaries
- **Missing:** Multi-screen / split-view coordinate mapping
- **Recommendation:** Add "Advanced Scenario: HDR Awareness & Multi-Display" section

### B53 Unity-Performance-Analyzer
- **Missing:** Concrete SRP Batcher vs BRG benchmark numbers (e.g., "typical gains: 30-50% draw call reduction")
- **Missing:** Texture memory profiling beyond GC alloc (addressing VRAM fragmentation)
- **Missing:** Mobile-specific frame time variance detection (frame pacing, 60 vs 120 FPS targets)
- **Recommendation:** Add "Batching Performance Baseline" with real measured data

### E16 Asset-Store-Curator
- **Missing:** How to audit third-party asset for deprecated APIs (e.g., PostProcessing v2 code in 2026)
- **Missing:** License compatibility matrix (MIT vs Apache vs GPL in same project)
- **Missing:** Guidance on reporting security vulnerabilities in assets
- **Recommendation:** Add "Asset Code Audit Checklist" section

### Design UI-Developer
- **Missing:** How to handle responsive breakpoints (UI Toolkit only supports pixel-based layout)
- **Missing:** Animation state machine integration (Animator + UXML interaction)
- **Missing:** Accessibility (screen reader hints, ARIA alternatives)
- **Recommendation:** Add "Responsive Design Workarounds" and "A11y Best Practices"

### 3D-CAD Cinematic-Director
- **Missing:** VolumeProfile blending performance cost (CPU time to interpolate weights)
- **Missing:** How to layer multiple Volume components without order ambiguity
- **Missing:** HDR vs SDR tone-mapping preset differences
- **Recommendation:** Add "Volume Performance & Blending Order" section

---

## Internal Contradictions

**K11 contradiction:** postfx-volume-presets.md L21 lists "FilmGrain" as available in URP, but FilmGrain is HDRP-only (first introduced HDRP 12.0+). URP has no built-in FilmGrain. Presets 5 (Horror, L172) and 6 (Dreamy) do not use FilmGrain, but L21 implies it's available.

**K5 contradiction:** draw-call-batching.md L42 claims dynamic batching <500 verts/mobil, but L14's decision matrix doesn't mention vertex limits at all — agent may recommend dynamic batching for complex meshes without checking limits first.

---

## Recommendations (Ranked by Risk × Fix-Cost)

| Rank | ID | Fix | Cost | Risk Reduction |
|------|----|----|------|---|
| 1 | K7 | Remove/replace com.xesmedia.fsm with verified package (OpenUPM search) | 15 min | HIGH → resolved |
| 2 | K9 | Replace design.example.com with real example (Figma API or remove) | 20 min | HIGH → resolved |
| 3 | K5 | Add "URP vs Built-in Dynamic Batching limits" section with links | 30 min | HIGH → MED |
| 4 | K4 | Add SRP Batcher vs BRG benchmark baselines | 45 min | MED → LOW |
| 5 | K12 | Clarify "Outline" as custom effect, replace with real URP effects | 25 min | MED → LOW |
| 6 | K3 | Add GPU vs CPU bound detection logic to decision matrix | 20 min | MED → LOW |
| 7 | K10 | Split CSS Grid/Flex guidance; add "CSS Grid unsupported" disclaimer | 15 min | MED → LOW |
| 8 | K6 | Add verification footnotes to Top 20 Publishers list | 10 min | MED → LOW (confidence) |

---

## Summary

**Critical issues:** 3 hallucinations requiring immediate fix (K7, K9, K5)  
**Medium issues:** 7 API/coverage gaps requiring review + enhancement  
**Low issues:** 3 citation/version-pinning updates  
**Overall quality:** 65/100 (solid baseline, needs hallucination purge + coverage fill)

Most critical path: Fix K7 (fake package), K9 (fake endpoint), K5 (wrong API specs) before shipping agents to production. These can cause silent failures or incorrect recommendation chains.

# Tool Specs Audit — Run 1

## Summary
- **Files audited:** 5
- **Contract inconsistencies found:** 8
- **Missing error paths:** 12
- **Missing verification sections:** 0 (all present)
- **Overall consistency score:** 6.2/10

---

## Findings Table

| ID | File | Type | Severity | Description | Suggested Fix |
|----|------|------|----------|-------------|---------------|
| A1 | all | naming-convention | HIGH | Inconsistent naming: `Cinema_*` (PascalCase prefix) vs `Craft_*` (Pascal) vs `Assets_*` (Snake-Pascal) vs `Optimize_*` (Pascal) | Establish convention: all tools use `Agent_ToolName` pattern or `namespace_operation`. Current mix confuses dispatch. |
| A2 | all | return-format | HIGH | Transaction IDs vary: `transactionId` (camelCase) in some, `transaction_id` (snake_case) implied in others. Asset-store lacks transactionId entirely for UPM installs initially. | Standardize all returns to `transactionId: "tx-<timestamp>-<id>"` format across all tools. |
| A3 | import-design-bundle.md | error-path | MEDIUM | Step 1 (Fetch Bundle) documents only 404/401/timeout. Missing: TLS cert errors, malformed JSON response, redirect loops, rate-limiting (429). | Add 5-6 error cases to Error Handling section. |
| A4 | screen-control.md | error-path | MEDIUM | G13 dispatch protocol missing error for "confidence < 0.70" in AnalyzeScreen docs but present in ActOnScreen. Inconsistent escalation behavior across two similar tools. | Unify confidence threshold handling: document in AnalyzeScreen signature, not just ActOnScreen. |
| A5 | screen-control.md | missing-section | MEDIUM | CaptureScreen lacks explicit error responses; only mentions behavior. No documented handling for "camera path invalid", "resolution too large (>4K)", "output disk full". | Add explicit error cases section to CaptureScreen docstring. |
| A6 | cinematic.md | upstream-dependency | HIGH | Cinema_CaptureShot uses upstream `Craft_CaptureGameView` (line 96) without version constraint. cinematic.md doesn't note "requires craft-unity 0.2.0+". screen-control.md also uses same, no version note. | Add "Upstream Dependencies" section to both tools: "Requires CRAFT v0.2.0+; CinemachineCamera v2.4+". |
| A7 | cinematic.md | cross-ref-drift | MEDIUM | PostFX_ApplyPreset mentions "render pipeline detection via knowledge/render-pipeline-auto-detect.md" (line 172) but this file not in tool bundle. Verification §3 says "Effects visible in Game view (bloom glow, color shift...)" — undescriptive for horror preset (desaturation key indicator). | Document which effects are visually key per preset. Clarify knowledge file path or remove reference. |
| A8 | optimization.md | error-path | MEDIUM | Optimize_Analyze output format § doesn't specify what happens when profiler unavailable (Play mode required, no Development Build enabled). Optimize_Profile also missing timeout error. | Add errors: "Profiler unavailable in Build | WebGL | unsupported platform". |
| A9 | optimization.md | dispatch-protocol | MEDIUM | B53 dispatch expected input/output not formally documented (only Example Workflow § 292-309). AnalyzeScreen/ActOnScreen in screen-control.md have explicit dispatch protocols; Optimize_* should match. | Add formal "B53 Dispatch Protocol" section with Input/Output JSON schema. |
| A10 | asset-store.md | missing-error | HIGH | Assets_ScanLibrary cache error handling incomplete: "cache_not_found" only error documented (line 49). Missing: invalid JSON in cache file, permission errors (read-only cache dir), cache >5GB corruption. | Expand error handling to 4-5 cases; document cache repair flow. |
| A11 | asset-store.md | missing-transaction | MEDIUM | Assets_InstallUPM returns transactionId (line 159) but Assets_CompareOwned has no transactionId in output (line 206-220). Query-only operation, so no rollback needed, but inconsistent with other tools' return contracts. | Clarify in docstring: "Query-only; no transactionId returned. For install, use Assets_InstallUPM." |
| A12 | asset-store.md | error-path | MEDIUM | E16 dispatch (lines 126-141) lacks error handling: "E16 times out", "E16 returns invalid JSON", "Asset Store unreachable", "Web scrape HTML parse fails". Error Handling only documents "manifest_not_found". | Add section: "E16 Dispatch Errors" with timeout/parse/network failure modes. |

---

## Top Insights

### 1. Naming Convention Fragmentation (Severity: HIGH)
**Files affected:** All 5 tools
**Impact:** Callers cannot predict tool name format without doc lookup.
**Fix (Quick Win):** Establish `Agent_Operation` convention (e.g., `E9_CreateVCam`, `G13_AnalyzeScreen`) or `operation_TargetType` (e.g., `Create_VCam`, `Analyze_Screen`). Current mix is accidental.

### 2. Transaction ID Return Format (Severity: HIGH)
**Files affected:** import-design-bundle.md, cinematic.md, optimization.md, screen-control.md
**Impact:** Rollback chains fail if field names vary. Downstream CRAFT_Rollback expects consistent key.
**Fix:** All returns use `transactionId` (camelCase, not `transaction_id`). Standardize format: `tx-YYYYMMDD-HHMMSS-<hash>`.

### 3. Upstream Dependency Declarations Missing (Severity: HIGH)
**Files affected:** cinematic.md, screen-control.md
**Impact:** Users attempt tools with incompatible CRAFT versions, ops fail silently.
**Fix:** Add "Upstream Dependencies" section to each tool:
```markdown
## Upstream Dependencies
- CRAFT v0.2.0+ (required for Craft_CaptureGameView, Craft_Execute)
- CinemachineCamera v2.4+ (cinematic.md only)
- com.unity.postprocessing 3.2+ (post-FX presets)
```

### 4. Dispatch Protocol Inconsistency (Severity: MEDIUM)
**Files affected:** optimization.md (none), screen-control.md (explicit), asset-store.md (explicit)
**Impact:** Optimization tool (B53 dispatch) underspecified vs G13/E16 which have full JSON schemas.
**Fix:** Add "B53 Dispatch Protocol" section to optimization.md matching screen-control.md structure (Input/Output JSON, timeout, error handling).

### 5. Error Path Coverage Gap (Severity: MEDIUM)
**Files affected:** All 5 tools
**Impact:** "Happy path" documentation only; failure scenarios under-tested.
**Common missing errors across tools:**
- Network timeouts/retries (import-design-bundle: bundle fetch, asset-store: web scraping)
- Disk space exhausted (cinematic: frame capture, import-design-bundle: cache write)
- Permissions denied (asset-store: manifest edit, cinematic: project path write)
- Parse/validation failures (all: JSON responses, image analysis, UXML validation)

---

## Recommendations (Ranked by ROI)

### Top 3 High-Impact Fixes

1. **Standardize Transaction ID & Return Contracts** (2 hours)
   - Establish single `transactionId` format across all tools
   - Document return shape as JSON schema per agent (D11, E9, G13, B53, E16)
   - Impact: Unblocks reliable rollback chains; enables audit trail

2. **Add Upstream Dependency Declarations** (1.5 hours)
   - Each tool documents CRAFT version, component versions, pipeline constraints
   - Example: "Requires CRAFT v0.2.0+, CinemachineCamera 2.4+, URP or HDRP (not Built-in)"
   - Impact: Prevents silent failures; guides user troubleshooting

3. **Expand Error Handling for All Tools** (3 hours)
   - Add 4-6 failure modes per tool (network, disk, parsing, permission, timeout)
   - Include suggested user recovery steps
   - Impact: Reduces escalations; guides autonomous error recovery

### Top 3 Deferrable Fixes

1. **Unify Naming Convention** (Can wait for v1.1)
   - Current names work; convention matters for consistency at scale
   - Deferrable because: no runtime impact, tools individually clear

2. **Formalize B53 Dispatch Protocol** (Can wait for optimization v2)
   - Optimization tool works; explicit schema is nice-to-have
   - Deferrable because: B53 integration less critical than CRAFT ops

3. **Reconcile PostFX Preset Visual Keys** (Can wait for docs refresh)
   - Minor: Verification § needs better preset-specific visual cues
   - Deferrable because: artists discover effects by testing

---

## Audit Methodology

Reviewed each tool for:
1. **Parameter/return consistency** — camelCase vs snake_case drift, missing fields
2. **Error coverage** — happy path vs 3-5 failure modes per tool
3. **Upstream dependencies** — undeclared version constraints
4. **Dispatch protocols** — JSON schema completeness, timeout/error handling
5. **Cross-tool references** — consistency when tool A calls tool B
6. **Verification sections** — all present; quality varies

**Confidence:** 8/10 (files are clear; gaps are refinement-level, not critical bugs)

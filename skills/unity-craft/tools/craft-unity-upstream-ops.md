# CRAFT-Unity Upstream Operations Specification

## Introduction

The `com.skywalker.craft` UPM package (craft-unity) currently provides mutation operations via CRAFT transaction framework. This document specifies **5 new read-only `Craft_Inspect` operations** and **2 new mutating `Craft_ImportSettings` operations** to unlock advanced screen automation and asset optimization workflows.

**Target Repo:** `/Users/musabkara/Projects/craft-unity` (UPM package)  
**Related Plugin:** `/Users/musabkara/Projects/ccplugin-unity-craft` (MCP bridge)  
**Vision Pipeline:** Screen capture → G13 analysis → CRAFT ops derivation

### Why These Ops?

- **Inspect Ops** (read-only): Enable vision pipeline to capture and analyze Game/Scene views, extract console logs, profile performance—*inputs* to ops derivation
- **ImportSettings Ops** (mutating): Enable automation of asset import configurations—textures, models, audio—via transaction-safe patching

The transaction framework already handles mutation safety; ImportSettings ops integrate cleanly into it.

---

## New Craft_Inspect Category (Read-Only)

Read-only operations bypass the transaction framework—no state mutation, no rollback needed, immediate return.

### 1. CaptureGameView

Capture the Game view rendering at specified resolution.

**MCP Tool Name:** `Craft_Inspect_CaptureGameView`

**Parameters:**
```
resolution: Vector2Int (default: editor Game view size, min: 256x144, max: 4096x4096)
format: "png" | "jpg" (default: "png")
```

**Returns:**
```json
{
  "filePath": "/Assets/.unity-craft/captures/game_2026-04-18_14-22-15.png",
  "width": 1920,
  "height": 1080,
  "format": "png",
  "sizeBytes": 245600,
  "timestamp": "2026-04-18T14:22:15Z"
}
```

**Rationale:**
- Requires Game view to be active and rendered (Play mode or preview)
- Returns file path + metadata for immediate G13 dispatch
- No state change; purely observational

**Implementation Notes:**
- Use `Texture2D.ReadPixels()` + `EncodeToPNG()`
- Save to `.unity-craft/captures/` (git-ignored)
- Timestamp filename for cache invalidation

---

### 2. CaptureSceneView

Capture the Scene view using a specific camera or default editor camera.

**MCP Tool Name:** `Craft_Inspect_CaptureSceneView`

**Parameters:**
```
cameraGameObjectPath: string (optional, e.g. "Main", "TopDown")
                      if omitted, use editor's default scene camera
```

**Returns:**
```json
{
  "filePath": "/Assets/.unity-craft/captures/scene_main_2026-04-18_14-22-15.png",
  "width": 1920,
  "height": 1080,
  "format": "png",
  "sizeBytes": 312400,
  "cameraPath": "Main",
  "timestamp": "2026-04-18T14:22:15Z"
}
```

**Rationale:**
- Complements `CaptureGameView` for editor-based workflows
- Allows targeting specific cameras for multi-camera setups
- Editor scene camera fallback when path omitted

**Implementation Notes:**
- If path provided: find GameObject, get Camera component, render to texture
- If path omitted: use `SceneHierarchyHooks.GetSceneViewCamera()`
- Save rendered texture to disk
- Return camera path for reference in analysis

---

### 3. CaptureUIPanel

Capture isolated UIDocument rendering (uGUI or UI Toolkit).

**MCP Tool Name:** `Craft_Inspect_CaptureUIPanel`

**Parameters:**
```
uiDocumentPath: string (e.g. "Canvas/SettingsPanel", "UI/MainMenu")
```

**Returns:**
```json
{
  "filePath": "/Assets/.unity-craft/captures/ui_SettingsPanel_2026-04-18_14-22-15.png",
  "width": 800,
  "height": 600,
  "format": "png",
  "sizeBytes": 156200,
  "documentPath": "Canvas/SettingsPanel",
  "timestamp": "2026-04-18T14:22:15Z"
}
```

**Rationale:**
- Isolates UI panel rendering without game world
- Useful for UI automation (button detection, form filling)
- Works with both Canvas (uGUI) and UIDocument (UI Toolkit)

**Implementation Notes:**
- Find GameObject by path, validate Canvas/UIDocument component
- Render via temporary RenderTexture (off-screen)
- Return document path for target mapping

---

### 4. ReadConsoleLog

Read Editor or Player console log entries since a Unix timestamp.

**MCP Tool Name:** `Craft_Inspect_ReadConsoleLog`

**Parameters:**
```
sinceUnixTs: long (e.g. 1713441735; omit for last 1 hour)
level: "all" | "warning" | "error" (default: "all")
```

**Returns:**
```json
{
  "entries": [
    {
      "timestamp": "2026-04-18T14:22:15Z",
      "level": "error",
      "message": "NullReferenceException in Player.Update()",
      "stackTrace": "..."
    },
    {
      "timestamp": "2026-04-18T14:21:02Z",
      "level": "warning",
      "message": "Material not found: Materials/Blue"
    }
  ],
  "entriesReturned": 2,
  "totalAvailable": 5
}
```

**Rationale:**
- Introspect runtime logs for debugging and verification
- Filter by level (error-only, all, etc.)
- Time-scoped queries for post-execution validation

**Implementation Notes:**
- Hook into `Debug.LogHandler` callback
- Store in-memory circular buffer (last 10MB of logs)
- Unix timestamp filtering with UTC conversion
- Return last 100 entries (cap to avoid overflow)

---

### 5. ProfileCapture

Capture performance profiling snapshot (frame stats, draw calls, triangle count, memory).

**MCP Tool Name:** `Craft_Inspect_ProfileCapture`

**Parameters:**
```
durationSeconds: float (default: 1.0, range: 0.1 - 10.0)
```

**Returns:**
```json
{
  "snapshotPath": "/Assets/.unity-craft/profiles/profile_2026-04-18_14-22-15.pprof",
  "frameStats": {
    "avgFrameTime_ms": 16.7,
    "minFrameTime_ms": 14.2,
    "maxFrameTime_ms": 22.1,
    "frameCount": 30
  },
  "drawCalls": 150,
  "trianglesRendered": 125000,
  "memoryBytes": {
    "heap": 256000000,
    "gfx": 128000000,
    "audio": 8000000
  },
  "timestamp": "2026-04-18T14:22:15Z"
}
```

**Rationale:**
- Validate scene performance before/after ops
- Detect regressions (too many draw calls, memory spike)
- Inform optimization decisions

**Implementation Notes:**
- Requires Editor or Development build with profiler enabled
- Sample frame time via `Time.deltaTime` during capture window
- Use `UnityEngine.Profiling.Recorder` for per-subsystem data
- Return in pprof binary format (compatible with external tools)

---

## New Craft_ImportSettings Category (Mutating)

Mutating operations integrate with the transaction framework: `AssetDatabase.StartAssetEditing()` / `StopAssetEditing()`, rollback via cached importer settings.

### 1. SetTextureImporter

Configure TextureImporter settings (compression, max size, mipmaps, crunch, etc.).

**MCP Tool Name:** `Craft_Mutate_SetTextureImporter`

**Parameters:**
```
assetPath: string (e.g. "Assets/Textures/Player.png")
overrides: {
  compressionFormat: "DXT1" | "DXT5" | "ASTC" | "ETC2" | "PVRTC" | "Uncompressed",
  maxSize: 1024 | 2048 | 4096 | ... (power of 2),
  crunch: boolean,
  mipmaps: boolean,
  sRGB: boolean,
  filterMode: "Point" | "Bilinear" | "Trilinear",
  wrapMode: "Repeat" | "Clamp" | "Mirror",
  aniso: 1 | 2 | 4 | 8 | 16
}
```

**Returns:**
```json
{
  "assetPath": "Assets/Textures/Player.png",
  "appliedOverrides": {
    "compressionFormat": "DXT5",
    "maxSize": 2048,
    "crunch": true
  },
  "previousSettings": {
    "compressionFormat": "DXT1",
    "maxSize": 4096,
    "crunch": false
  },
  "cachedRollbackId": "rollback-tx-abc123-texture-001"
}
```

**Rationale:**
- Automate texture import optimization (size, compression)
- Batch configure multiple assets via repeated calls in transaction
- Rollback via cached original importer state

**Transaction Integration:**
- Wraps `AssetDatabase.StartAssetEditing()` / `StopAssetEditing()`
- Caches original `TextureImporter` state in transaction log
- On rollback: restore original settings via cached importer object
- Validates asset path and TextureImporter presence before mutation

---

### 2. SetModelImporter

Configure ModelImporter settings (materials, animations, rig, LOD, etc.).

**MCP Tool Name:** `Craft_Mutate_SetModelImporter`

**Parameters:**
```
assetPath: string (e.g. "Assets/Models/Player.fbx")
overrides: {
  importMaterials: boolean,
  materialLocation: "Embedded" | "External",
  importAnimations: boolean,
  animationType: "Legacy" | "Generic" | "Humanoid",
  rigImportErrors: boolean,
  animationCompression: "Off" | "Keyframe" | "Optimal",
  optimizeGameObjects: boolean,
  meshCompression: "Off" | "Low" | "Medium" | "High",
  meshOptimizationFlags: ["CombineMeshes", "OptimizePolygonOrder"],
  importBlendShapes: boolean,
  normalImportMode: "Import" | "Calculate" | "None"
}
```

**Returns:**
```json
{
  "assetPath": "Assets/Models/Player.fbx",
  "appliedOverrides": {
    "importMaterials": false,
    "animationType": "Humanoid",
    "meshCompression": "High"
  },
  "previousSettings": {
    "importMaterials": true,
    "animationType": "Generic",
    "meshCompression": "Low"
  },
  "cachedRollbackId": "rollback-tx-abc123-model-001"
}
```

**Rationale:**
- Automate model optimization (LOD, compression, materials)
- Enable/disable animations, rigs, blend shapes per-asset
- Rollback via cached ModelImporter state

**Transaction Integration:**
- Same pattern as `SetTextureImporter`
- `AssetDatabase.StartAssetEditing()` / `StopAssetEditing()` wrapping
- Cached original ModelImporter in transaction log
- Rollback restores original importer settings

---

## File Layout (C# Code Structure)

**Source Directory:** `Packages/com.skywalker.craft/` (UPM package root)

```
src/
├── Operations/
│   ├── Inspect/
│   │   ├── CaptureGameViewOp.cs        (implements ICraftInspectOp)
│   │   ├── CaptureSceneViewOp.cs
│   │   ├── CaptureUIPanelOp.cs
│   │   ├── ReadConsoleLogOp.cs
│   │   └── ProfileCaptureOp.cs
│   │
│   └── ImportSettings/
│       ├── SetTextureImporterOp.cs     (implements ICraftMutateOp)
│       └── SetModelImporterOp.cs
│
├── McpTools/
│   ├── InspectTools.cs                 (MCP tool registration for Inspect)
│   └── ImportSettingsTools.cs          (MCP tool registration for ImportSettings)
│
├── Interfaces/
│   ├── ICraftInspectOp.cs              (read-only, no transaction needed)
│   └── ICraftMutateOp.cs               (existing, extended for ImportSettings)
│
└── TransactionLog/
    └── RollbackCache.cs                (caches importer settings for ImportSettings rollback)
```

---

## Transaction Safety

### Inspect Operations (Read-Only)

**No transaction needed.** Read-only operations return immediately without modifying scene or asset database state.

- No locking required
- No rollback state cached
- Safe to call concurrently
- No undo/redo entry

---

### ImportSettings Operations (Mutating)

**Full transaction safety via existing framework.**

**Execution:**
1. `AssetDatabase.StartAssetEditing()` — batch mode (prevents multiple reimports)
2. Apply importer overrides
3. Cache original importer settings in transaction log (for rollback)
4. `AssetDatabase.StopAssetEditing()` — trigger reimport
5. Return `cachedRollbackId` to transaction manager

**Rollback:**
1. Retrieve cached importer state from transaction log
2. `AssetDatabase.StartAssetEditing()`
3. Restore original importer via cached object
4. `AssetDatabase.StopAssetEditing()`

**Example Rollback Code Flow** (pseudocode):
```csharp
// On rollback request
var rollbackId = "rollback-tx-abc123-texture-001";
var cachedState = transactionLog.GetCachedState(rollbackId);

AssetDatabase.StartAssetEditing();
cachedState.importer.SaveAndReimport();  // Restore from cache
AssetDatabase.StopAssetEditing();
```

---

## MCP Tool Registration

### Inspect Tools Registration

Each Inspect op registers as a distinct MCP tool in the CRAFT MCP server.

**MCP Server Side (mcp-tools.json or equivalent):**
```json
{
  "tools": [
    {
      "name": "Craft_Inspect_CaptureGameView",
      "description": "Capture Game view to PNG/JPG at specified resolution",
      "inputSchema": {
        "type": "object",
        "properties": {
          "resolution": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
          "format": {"type": "string", "enum": ["png", "jpg"]}
        }
      }
    },
    {
      "name": "Craft_Inspect_CaptureSceneView",
      "description": "Capture Scene view using editor camera or specified camera",
      "inputSchema": {...}
    },
    {
      "name": "Craft_Inspect_CaptureUIPanel",
      "description": "Capture isolated UIDocument/Canvas panel",
      "inputSchema": {...}
    },
    {
      "name": "Craft_Inspect_ReadConsoleLog",
      "description": "Read console log entries since Unix timestamp",
      "inputSchema": {...}
    },
    {
      "name": "Craft_Inspect_ProfileCapture",
      "description": "Capture performance profiling snapshot",
      "inputSchema": {...}
    }
  ]
}
```

### ImportSettings Tools Registration

```json
{
  "tools": [
    {
      "name": "Craft_Mutate_SetTextureImporter",
      "description": "Configure TextureImporter settings (compression, size, mipmaps, etc.)",
      "inputSchema": {
        "type": "object",
        "properties": {
          "assetPath": {"type": "string"},
          "overrides": {"type": "object"}
        },
        "required": ["assetPath"]
      }
    },
    {
      "name": "Craft_Mutate_SetModelImporter",
      "description": "Configure ModelImporter settings (animations, rig, compression, etc.)",
      "inputSchema": {...}
    }
  ]
}
```

---

## Testing Notes

### Inspect Operations

**No Play mode required** (except `CaptureGameView` which needs Game view rendering).

```csharp
[UnityTest]
public IEnumerator CaptureSceneView_ReturnsValidPNG()
{
    var op = new CaptureSceneViewOp(cameraPath: "Main");
    var result = op.Execute();
    
    Assert.That(File.Exists(result.filePath));
    Assert.That(result.width, Is.GreaterThan(0));
    Assert.That(result.format, Is.EqualTo("png"));
    
    yield return null;
}

[UnityTest]
public IEnumerator ReadConsoleLog_FiltersLevel()
{
    Debug.LogWarning("test warning");
    Debug.LogError("test error");
    
    var op = new ReadConsoleLogOp(level: "error");
    var result = op.Execute();
    
    Assert.That(result.entries.Count, Is.EqualTo(1));
    Assert.That(result.entries[0].level, Is.EqualTo("error"));
    
    yield return null;
}
```

### ImportSettings Operations

**Requires real assets and AssetDatabase access** (Editor only, not runtime).

```csharp
[Test]
public void SetTextureImporter_AppliesOverrides()
{
    var assetPath = "Assets/Test/TestTexture.png";
    // Ensure asset exists in test setup
    
    var op = new SetTextureImporterOp(
        assetPath,
        overrides: new() { compressionFormat = "DXT5", maxSize = 2048 }
    );
    var result = op.Execute();
    
    Assert.That(result.appliedOverrides["compressionFormat"], Is.EqualTo("DXT5"));
    Assert.That(result.previousSettings, Is.Not.Null);  // Cached for rollback
}

[Test]
public void SetModelImporter_Rollback()
{
    var assetPath = "Assets/Test/TestModel.fbx";
    
    var op = new SetModelImporterOp(
        assetPath,
        overrides: new() { animationType = "Humanoid" }
    );
    var result = op.Execute();
    var rollbackId = result.cachedRollbackId;
    
    // Verify cached state can be rolled back
    var rollbackOp = new SetModelImporterOp(assetPath, overrides: result.previousSettings);
    var rollbackResult = rollbackOp.Execute();
    
    Assert.That(rollbackResult.appliedOverrides["animationType"], 
                Is.EqualTo(result.previousSettings["animationType"]));
}
```

---

## Implementation Priority

### Phase 1: Inspect Ops (Unlocks Screen Automation)

**Timeline:** 2-3 weeks (no transaction complexity)

1. `CaptureSceneView` → `CaptureGameView` → `CaptureUIPanel` (screenshot pipeline)
2. `ReadConsoleLog` (debugging, post-execution validation)
3. `ProfileCapture` (optional, for optimization workflows)

**Enables:** screen-control.md pipeline, G13 vision analysis, pattern caching

**Integration:** MCP tool registration in CRAFT MCP server

---

### Phase 2: ImportSettings Ops (Optimization Tools)

**Timeline:** 1-2 weeks (leverages existing transaction framework)

1. `SetTextureImporter` (asset optimization, memory reduction)
2. `SetModelImporter` (LOD, animation, rig configuration)

**Enables:** Batch asset optimization, automation of import workflows

**Integration:** Transaction framework, rollback caching, MCP tool registration

---

---

## v0.3 Roadmap — Craft_ImportUnityPackage

Closes weak-point **W5** (legacy `.unitypackage` auto-import missing). Enables `Assets_InstallUPM` to handle 90% of Asset Store library (legacy `.unitypackage` format alongside modern UPM).

### Purpose

Legacy `.unitypackage` files dominate the Asset Store (pre-2022). Current workflow requires manual import dialog in Unity Editor. `Craft_ImportUnityPackage` automates this with:
- Path, URL, or embedded package support
- Silent (no prompt) or interactive import modes
- Transaction-safe rollback: enumeration of imported assets + undo on failure
- Post-import validation via `Craft_ReadConsoleLog` for compile errors

### Operation Class

**Namespace:** `SkyWalker.Craft.Editor.Operations.ImportPackage`  
**Class:** `ImportUnityPackageOp : ICraftOperation`  
**Location:** `Editor/Operations/ImportPackage/ImportUnityPackageOp.cs`

### MCP Tool

**Tool Name:** `Craft_ImportUnityPackage`  
**Tool Class:** `CraftImportUnityPackageTool` in `Editor/McpTools/`

### Parameters

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `packagePath` | string | yes | — | Absolute path to `.unitypackage` file, OR relative to `Assets/`, OR HTTP(S) URL. URL is fetched to temp dir, imported, temp file deleted. |
| `importMode` | enum | no | "silent" | "interactive" (shows Unity's import dialog), "silent" (imports all without prompt), "replace-without-asking" (overwrites existing without dialog). |
| `deleteSourceAfterImport` | bool | no | false | If true, delete package file after successful import. Only meaningful when source is outside `Assets/`. |

### Return Shape

```json
{
  "success": true,
  "transactionId": "import-pkg-2026-04-18-143022-abc123",
  "packagePath": "Assets/Downloaded/MyPackage.unitypackage",
  "importedAssetPaths": [
    "Assets/MyPackage/Models/Character.fbx",
    "Assets/MyPackage/Scripts/PlayerController.cs",
    "Assets/MyPackage/Materials/Skin.mat"
  ],
  "skippedAssets": [
    {
      "path": "Assets/Existing/Duplicate.mat",
      "reason": "already exists"
    }
  ],
  "durationMs": 2340,
  "compilationErrors": 0,
  "warnings": 0
}
```

### Unity API

**Primary:** `AssetDatabase.ImportPackage(packagePath, interactive)`

**Fallback for silent import in Unity 6+:** `AssetDatabase.ImportPackageImmediately(packagePath)` (verify availability in implementation phase)

**Content enumeration:** `AssetDatabase.GetPackageContents(packagePath)` (if available; else reflection fallback to extract tar.gz metadata)

### Rollback Strategy

**Pre-import enumeration:**
1. Call `AssetDatabase.GetPackageContents(packagePath)` to list all assets the package would import
2. Store list in transaction log with transaction ID
3. Filter out assets already present in project (to avoid false-positive "created by CRAFT" detection)

**On Undo/Rollback:**
1. Retrieve stored asset list from transaction log
2. Iterate each asset and call `AssetDatabase.DeleteAsset(assetPath)`
3. Emit trace entry per deleted file (verbose logging)
4. Return success

**Best-effort caveat:** Unity triggers async C# compilation after import. If rollback is requested during compilation, metadata may be stale. Document as "best-effort rollback; verify clean state via `Craft_Status` post-rollback".

### Transaction Safety

**Execution flow:**

```
1. Fetch package (if URL)
2. Enumerate package contents → cache in transaction log
3. AssetDatabase.StartAssetEditing()
4. Call AssetDatabase.ImportPackage(packagePath, interactive)
5. AssetDatabase.StopAssetEditing()  ← triggers reimport
6. Poll Craft_ReadConsoleLog for compile errors (1-3 sec delay)
7. If errors detected: return partial success + error list
8. Register transaction with TransactionManager
9. Return transactionId + importedAssetPaths
```

**Rollback:**
```
1. Retrieve cached asset list from transaction log
2. AssetDatabase.StartAssetEditing()
3. For each asset: AssetDatabase.DeleteAsset(assetPath)
4. AssetDatabase.StopAssetEditing()
5. Emit trace entries per file
```

### Error Modes

| Error | Detection | Response |
|-------|-----------|----------|
| File not found | `!File.Exists(packagePath)` | `success: false, error: "Package file not found at {path}"` |
| Invalid package | `AssetDatabase.ImportPackage()` exception | `success: false, error: "Invalid .unitypackage format: {exception}"` |
| URL fetch failure | Network timeout, 404, SSL error | `success: false, error: "Failed to fetch {url}: {statusCode}"` |
| Dependency missing | Post-import console: unresolved reference | `success: true (partial), warnings: "Missing dependencies detected"` |
| Compile error cascade | `Craft_ReadConsoleLog` post-import errors | `success: true (partial), compilationErrors: N, error: "Asset import succeeded but {N} compile errors detected"` |
| Rollback during compilation | Async compile in progress | `success: false, error: "Rollback requested during asset compilation; best-effort deletion attempted. Verify state via Craft_Status."` |

### Integration with Assets_InstallUPM

When plugin inspection detects legacy package signature:
- File ends in `.unitypackage`
- OR manifest file not present (fallback check)
- OR URL resolves to `.unitypackage` MIME type

Route to `Craft_ImportUnityPackage` instead of UPM manifest edit path. Example logic in plugin dispatcher:

```csharp
if (packagePath.EndsWith(".unitypackage", StringComparison.OrdinalIgnoreCase) ||
    (isUrl && await GetUrlMimeType(packagePath) == "application/x-unitypackage"))
{
    return await MCP.CallTool("Craft_ImportUnityPackage", new { packagePath, importMode = "silent" });
}
else
{
    // Existing UPM path (Assets_InstallUPM)
}
```

### Known Limitations

1. **Async Compilation:** Unity fires async C# compilation after `StopAssetEditing()`. The operation returns once import is initiated but before compilation completes. Agents should call `Craft_Status` afterward to verify clean state (0 errors).
   
2. **Rollback Window:** Cached asset list is only valid during the transaction TTL (default: 24 hours). If rollback is requested after TTL expiry, transaction manager logs a warning and returns partial success.

3. **URL Fetch Size:** Downloaded packages are stored in temp. No size limit enforced; very large packages (>2GB) may exhaust disk. Document as "use with caution for packages >500MB".

4. **Import Mode Interaction:** `interactive` mode requires editor in foreground (user sees dialog). In headless/CI scenarios, use `silent` or `replace-without-asking`.

### Return Metadata

**`transactionId`:** Unique token for this import session. Use for:
- Rollback requests: `Craft_Rollback(transactionId)`
- Status queries: `Craft_Status(transactionId)`
- Trace retrieval: `Craft_CommandLog(transactionId)`

**`importedAssetPaths`:** List of assets CRAFT imported. Pre-existing assets NOT included (caller can compare with `.Before` snapshot if needed).

**`skippedAssets`:** Array of skipped imports (conflicts, permission errors). Reason explains why (e.g., "already exists", "read-only", "invalid format").

**`compilationErrors` / `warnings`:** Counts from `Craft_ReadConsoleLog` polling post-import. If > 0, recommend agent run `Craft_ReadConsoleLog(sinceTs: importStartTime)` for detailed error list.

### File Layout

```
Editor/
├── Operations/
│   ├── ImportPackage/
│   │   ├── ImportUnityPackageOp.cs        (ICraftOperation implementation)
│   │   └── PackageContentsCache.cs        (helper: enumerate & track assets)
│   │
├── McpTools/
│   └── ImportPackageTools.cs              (MCP tool registration)
│
├── Models/
│   └── PackageImportResult.cs             (strongly-typed result shape)
```

### Testing Strategy

**Unit Tests:**
- Path validation (absolute, relative, invalid)
- URL fetch simulation (mock HttpClient)
- Empty package (no assets)
- Duplicate asset handling (replace vs. skip)

**Integration Tests:**
- Create real `.unitypackage` (tar.gz) with test assets
- Import into test project
- Verify asset list matches enumeration
- Trigger rollback; verify deletion
- Compile error detection post-import

### Security Considerations

- **URL validation:** Only allow HTTP(S). Reject file://, ftp://, UNC paths.
- **Temp file cleanup:** Always delete fetched packages from temp, even on error. Use `try-finally`.
- **Package inspection:** Scan for suspicious file paths in enumeration (e.g., `../../../System32`). Reject with "traversal attack detected".

---

## v0.3 Roadmap — Play Mode Automation

Unity Editor's PlayMode lifecycle can be controlled via `UnityEditor.EditorApplication.isPlaying` and `EnterPlayMode()`/`ExitPlayMode()` APIs. Combined with InputSystem's `InputTestRuntime` or direct `Keyboard.current`/`Mouse.current` manipulation, we can automate smoke/scenario testing and profiling workflows. These new ops make the plugin's Playtest tool family functional, enabling game-director playback simulation and sustained performance sampling during test execution.

### New Operations

#### 1. Craft_EnterPlayMode

Transition the Unity Editor into Play Mode with optional synchronization on completion.

**MCP Tool Name:** `Craft_EnterPlayMode`

**Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `waitForReady` | bool | no | true | If true, block until `isPlaying` is true AND `scriptsCompiled` is true AND scene is loaded. |
| `maxWaitSec` | float | no | 10.0 | Timeout for ready-wait (0.5–60.0). |

**Returns:**

```json
{
  "success": true,
  "playModeActive": true,
  "scriptsCompiled": true,
  "enterDurationMs": 1250,
  "activeSceneName": "GameScene",
  "errors": []
}
```

**Class:** `EnterPlayModeOp` in `Editor/Operations/PlayMode/`

**Unity API:** 
- `EditorApplication.EnterPlaymode()` to initiate
- Poll `EditorApplication.isPlaying` and `EditorApplication.isCompiling` to wait for readiness
- Poll `SceneManager.GetActiveScene().name` for active scene

**Transaction & Safety:**
- **No transaction log entry:** PlayMode state is ephemeral and paired with `ExitPlayMode`. Document this as explicit: cannot rollback to pre-play state via transaction framework (editor state, not scene mutation).
- If already in play mode, return idempotent success (no re-entry cost).
- Compilation errors block entry; return `success: false` with error list from console.

**Error Modes:**

| Error | Detection | Response |
|-------|-----------|----------|
| Compilation error | `EditorApplication.isCompiling` || console has errors | `success: false, errors: [error details from ReadConsoleLog]` |
| asmdef loop | Circular dependency in Assembly definitions | `success: false, error: "Circular asmdef dependency detected"` |
| Scene not saved | Scene dirty + import mode mismatch | `success: false, error: "Scene has unsaved changes; save before entering play mode"` |
| Timeout exceeded | `waitForReady && elapsed > maxWaitSec` | `success: false, error: "Play mode entry timeout after {maxWaitSec}s"` |

---

#### 2. Craft_ExitPlayMode

Exit Play Mode and return to Edit Mode.

**MCP Tool Name:** `Craft_ExitPlayMode`

**Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `force` | bool | no | false | If true, exit immediately. If false, allow scripts to finalize (e.g., OnApplicationQuit). |

**Returns:**

```json
{
  "success": true,
  "exitDurationMs": 340,
  "finalLogEntries": [
    {
      "timestamp": "2026-04-18T14:25:30Z",
      "level": "warning",
      "message": "Game object destroyed during shutdown"
    }
  ]
}
```

**Class:** `ExitPlayModeOp` in `Editor/Operations/PlayMode/`

**Unity API:**
- `EditorApplication.ExitPlaymode()`
- Poll `EditorApplication.isPlaying` to confirm transition

**Transaction & Safety:** No rollback. Exit is idempotent (if already in edit mode, return success immediately).

**Error Modes:**

| Error | Detection | Response |
|-------|-----------|----------|
| Exit timeout | Play mode won't exit after 5s | `success: false, error: "Play mode exit timeout; force=true may be needed"` |
| Already in Edit Mode | Not in play mode | `success: true` (idempotent) |

---

#### 3. Craft_GetPlayModeStatus

Query the current Play Mode state without mutation.

**MCP Tool Name:** `Craft_GetPlayModeStatus`

**Parameters:** None

**Returns:**

```json
{
  "isPlaying": true,
  "timeSincePlayStart": 12.5,
  "currentFps": 59.8,
  "memoryMB": 512,
  "errorCount": 0,
  "warningCount": 2,
  "activeSceneName": "GameScene",
  "timestamp": "2026-04-18T14:25:30Z"
}
```

**Class:** `GetPlayModeStatusOp` in `Editor/Operations/PlayMode/`

**Unity API:**
- `EditorApplication.isPlaying`
- `Time.realtimeSinceStartup` (elapsed time in play mode)
- `Application.targetFrameRate` and last frame time for FPS calculation
- `Profiler.GetTotalMemoryUsage()` (requires Development/Profiling build)
- Console log introspection for error/warning counts
- `SceneManager.GetActiveScene().name`

**Transaction & Safety:** Read-only; no state change.

---

#### 4. Craft_SimulateInput

Queue input events while in Play Mode (keyboard, mouse, gamepad).

**MCP Tool Name:** `Craft_SimulateInput`

**Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `device` | enum | yes | — | "keyboard" \| "mouse" \| "gamepad" |
| `action` | enum | yes | — | "press" \| "release" \| "hold" \| "axis" \| "click" |
| `control` | string | yes | — | Device control name: "w", "space", "leftButton", "rightStick", etc. |
| `value` | float | no | 1.0 | For axis actions: analog value (0.0–1.0). For press/release: ignored. |
| `durationMs` | int | no | 0 | For hold action: duration in milliseconds. |
| `coords` | [float, float] | no | [0, 0] | For mouse: screen coordinates [x, y]. |

**Returns:**

```json
{
  "success": true,
  "queued": true,
  "simulatedAt": "2026-04-18T14:25:30Z",
  "device": "keyboard",
  "control": "w",
  "action": "press",
  "errors": []
}
```

**Class:** `SimulateInputOp` in `Editor/Operations/PlayMode/`

**Unity API:**
- **Preferred:** `InputSystem.QueueStateEvent()` with `InputEventPtr` (modern InputSystem package)
- **Fallback:** Direct property manipulation: `Keyboard.current.wKey.Press()` + `Keyboard.current.wKey.Release()` (if InputSystem supports this; verify)
- **Legacy fallback:** `Event.KeyboardEvent()` for projects without InputSystem

**Validation:**
- Must be in Play Mode (call `Craft_GetPlayModeStatus()` internally or accept `inPlayModeOnly: true` param)
- Control name must match device (e.g., "w" not valid for gamepad)

**Transaction & Safety:** No rollback. Input events are fire-and-forget and cannot be undone in-engine.

**Error Modes:**

| Error | Detection | Response |
|-------|-----------|----------|
| Not in play mode | `!EditorApplication.isPlaying` | `success: false, error: "Play mode not active; enter play mode first"` |
| Invalid control name | Control not found on device | `success: false, error: "Unknown control '{control}' for device '{device}'"` |
| InputSystem missing | Package not imported | `success: false, error: "InputSystem package not found; install via UPM or use legacy Event API"` |
| Coordinate out of bounds | Mouse coords beyond screen | `success: true` (clamp to valid range) |

---

#### 5. Craft_SampleProfileWindow

Continuously sample performance metrics during Play Mode over a specified duration.

**MCP Tool Name:** `Craft_SampleProfileWindow`

**Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `durationSec` | float | yes | — | Total sampling window (1.0–600.0). |
| `sampleRateHz` | float | no | 10.0 | Samples per second (0.5–100). |
| `metrics` | string[] | no | ["fps", "cpu-ms", "gpu-ms", "memory-mb"] | Metrics to capture. Valid: "fps", "cpu-ms", "gpu-ms", "draw-calls", "triangles", "memory-mb", "gc-kb-per-frame". |

**Returns:**

```json
{
  "success": true,
  "durationSec": 5.0,
  "sampleCount": 50,
  "samples": [
    {
      "ts": 0.0,
      "fps": 60.0,
      "cpuMs": 16.67,
      "gpuMs": 8.5,
      "drawCalls": 120,
      "triangles": 85000,
      "memoryMb": 512,
      "gcKbPerFrame": 0.0
    },
    {
      "ts": 0.1,
      "fps": 59.8,
      "cpuMs": 16.92,
      ...
    }
  ],
  "aggregates": {
    "fps_avg": 59.5,
    "fps_p95": 60.0,
    "fps_min": 58.2,
    "fps_max": 60.0,
    "cpuMs_avg": 16.8,
    "memoryMb_peak": 528,
    "gcKbTotal": 45.2,
    "crashCount": 0
  },
  "errors": []
}
```

**Class:** `SampleProfileWindowOp` in `Editor/Operations/PlayMode/`

**Unity API:**
- `ProfilerRecorder` for frame time, draw calls, triangle count
- `Profiler.GetTotalMemoryUsage()` for heap + GFX memory
- `GC.GetTotalMemory()` for garbage collection tracking
- Sample loop: `await Task.Delay((int)(1000.0 / sampleRateHz))` between samples
- Console log polling for crash detection (exit code != 0 or "Fatal Error")

**Validation:**
- Must be in Play Mode (return error if not)
- `durationSec` clamped to [1.0, 600.0]
- `sampleRateHz` clamped to [0.5, 100.0]

**Transaction & Safety:** Read-only; sampling does not mutate state. If Play Mode exits mid-sample, return partial data with warning.

**Error Modes:**

| Error | Detection | Response |
|-------|-----------|----------|
| Not in play mode | `!EditorApplication.isPlaying` at start | `success: false, error: "Play mode not active"` |
| Play mode exits during sample | `!isPlaying` during loop | `success: true (partial), warnings: ["Play mode exited after {elapsed}s; returning partial data"]` |
| Profiler unavailable | Development build not enabled | `success: false, error: "Profiler data unavailable; enable Development build or Editor profiler"` |
| Invalid metric name | Metric not in predefined list | `success: false, error: "Unknown metric '{metric}'; valid: [fps, cpu-ms, ...]"` |

**Aggregation Logic:**
- `fps_avg`: Simple mean of FPS samples
- `fps_p95`: 95th percentile (sorted samples, index = 0.95 * count)
- `fps_min/max`: Min and max values
- `memoryMb_peak`: Largest memory reading
- `gcKbTotal`: Sum of all GC-per-frame values
- `crashCount`: Count of error-level console entries during window

---

## v0.3 Roadmap — Asset Importer Specific Ops (Deferred, Lower Priority)

Beyond `SetTextureImporter` and `SetModelImporter` (already specced), the logical next-phase asset family op is `Craft_SetAudioImporter`, enabling batch audio import automation for optimization workflows (compression, loading strategy, preload allocation).

**Brief Spec:**

**MCP Tool Name:** `Craft_SetAudioImporter`

**Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `assetPath` | string | yes | — | Path to `.mp3`, `.wav`, `.ogg`, etc. |
| `overrides` | object | no | {} | Importer settings to apply. |

**Overrides Schema:**

```
{
  "loadType": "DecompressOnLoad" | "CompressedInMemory" | "Streaming",
  "compressionFormat": "PCM" | "Vorbis" | "ADPCM" | "MP3" | "VAG" | "HEVAG" | "XMA" | "GCADPCM" | "AT9",
  "quality": 0.1 - 1.0 (float, compression ratio),
  "forceToMono": boolean,
  "loadInBackground": boolean,
  "preloadAudioData": boolean,
  "ambisonic": boolean,
  "defaultSampleSettings": { /* platform-specific overrides */ }
}
```

**Returns:** Same pattern as `SetTextureImporter` — `{appliedOverrides, previousSettings, cachedRollbackId}`.

**Integration:** Transaction-safe with rollback via cached AudioImporter state (same pattern as texture/model ops).

**Rationale:** Completes asset family, enables audio-specific CI/CD optimization (memory reduction via streaming, compression tuning).

**Timeline:** Phase 3d (1 week, **deferred** — lower priority than PlayMode ops).

---

## Implementation Priority (Updated)

### Phase 3a: Inspect Ops (Unblocks Screen Control + Cinematic Capture)

**Timeline:** 2–3 weeks (no transaction complexity)

**Operations:**
1. `CaptureSceneView` → `CaptureGameView` → `CaptureUIPanel` (screenshot pipeline)
2. `ReadConsoleLog` (debugging, post-execution validation)
3. `ProfileCapture` (optional, for optimization workflows)

**Enables:** screen-control.md pipeline, G13 vision analysis, pattern caching

**Status:** Already specced in earlier sections

---

### Phase 3b: ImportSettings Ops (Unblocks Optimization Importer Batch)

**Timeline:** 2 weeks (leverages existing transaction framework)

**Operations:**
1. `SetTextureImporter` (asset optimization, memory reduction)
2. `SetModelImporter` (LOD, animation, rig configuration)

**Enables:** Batch asset optimization, automation of import workflows

**Status:** Already specced in earlier sections

---

### Phase 3c: PlayMode + Input Simulation + Sustained Profiling (NEW)

**Timeline:** 3 weeks (new, enables playtest loop)

**Operations:**
1. `EnterPlayMode` (lifecycle control)
2. `ExitPlayMode` (cleanup + state transition)
3. `GetPlayModeStatus` (inspect-category readiness check)
4. `SimulateInput` (keyboard/mouse/gamepad events, play-mode only)
5. `SampleProfileWindow` (sustained performance sampling, aggregation)

**Enables:**
- Game-director playback automation (smoke tests, scenario replay)
- Input-driven testing workflows (UI automation, gameplay flows)
- Sustained performance profiling during test execution (detect FPS drops, memory leaks, GC spikes)
- Integration with CI/CD playtest pipelines (automated QA, regression detection)

**Dependencies:** PlayMode automation prerequisites (no external package dependencies beyond core InputSystem, which is standard in Unity 2022+)

**Status:** Newly specced in this section

---

### Phase 3d: SetAudioImporter + Audio Family Completion (Deferred)

**Timeline:** 1 week (lower priority, same pattern as texture/model ops)

**Operation:**
1. `SetAudioImporter` (compression, load strategy, preload settings)

**Enables:** Complete asset importer family for CI/CD automation

**Rationale:** Nice-to-have; audio optimization is less critical than playtest automation. Defer until phase 3c is tested in production.

**Status:** Briefly specced above

---

## Related Documents

- [screen-control.md](screen-control.md) — Vision pipeline using Inspect ops
- [SKILL.md](../../SKILL.md) — CRAFT operation semantics and validation
- [craft-ops-derivation.md](../../../claude-config/agents/ai-ops/vision-action-operator/knowledge/craft-ops-derivation.md) — G13 ops derivation logic

---

## Open Questions & Decisions

1. **Inspect Concurrency:** Can multiple Inspect ops run in parallel, or must they serialize? (Proposed: parallel-safe, no locking)
2. **Console Log Circular Buffer:** Size limit (proposed: 10MB)? Format (proposed: JSON array)?
3. **Profile Format:** pprof binary or custom JSON? (Proposed: pprof for tooling compatibility)
4. **ImportSettings Rollback Window:** How long to keep cached importer states? (Proposed: transaction TTL, max 24 hours)
5. **ImportUnityPackage Poll Interval:** How often to poll `ReadConsoleLog` post-import for compile errors? (Proposed: 500ms, max 3 retries, 1.5s total)

---

## Rationale Summary

| Op | Problem Solved | Impact | Phase |
|---|---|---|---|
| CaptureGameView | No way to grab Game view for vision analysis | Enables automated UI testing | 1 |
| CaptureSceneView | Editor screenshot in code-only workflows | Scene validation, architecture checks | 1 |
| CaptureUIPanel | Isolated UI testing without game world | UI automation, form validation | 1 |
| ReadConsoleLog | No structured console access for verification | Post-ops error detection, debugging | 1 |
| ProfileCapture | No built-in perf snapshot tool | Regression detection, optimization | 1 |
| SetTextureImporter | Manual texture optimization tedious to automate | Batch memory optimization, CI/CD | 2 |
| SetModelImporter | Model import config hard to version control | Consistent imports, LOD automation | 2 |
| ImportUnityPackage | 90% of Asset Store is legacy format; manual import blocks automation | Unlocks automated asset library, closes W5 | 3 |

---

**Document Status:** Specification + roadmap (v0.3 planned, C# stub provided)  
**Last Updated:** 2026-04-18  
**Target:** craft-unity UPM package, com.skywalker.craft  
**Related Plugin:** ccplugin-unity-craft v1.0

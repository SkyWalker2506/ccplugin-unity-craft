# Asset Store Integration Tools

## Purpose

Asset Store awareness layer bridges local inventory (Assets_ScanLibrary) with curated recommendation (E16 Asset Store Curator agent) and installation (Assets_InstallUPM, Assets_CompareOwned). Enables Claude to answer "what asset should I use for this task?" by combining user's existing library, budget constraints, compatibility requirements, and publisher reputation into ranked recommendations.

Pipeline: User intent → scan local cache → E16 web research + owned inventory check → ranked candidates → install or user consent.

## Tool Signatures

### Assets_ScanLibrary(refresh = false)

Scans local Unity Asset Store cache (macOS: `~/Library/Unity/Asset Store-5.x`, Windows: `%APPDATA%\Unity\Asset Store-5.x`) and returns JSON inventory.

**Arguments:**
| Arg | Type | Default | Example |
|-----|------|---------|---------|
| `refresh` | bool | false | true (force full rescan, ignore 24h cache) |

**Output:**
```json
{
  "scanned_at": "2026-04-18T14:30:22Z",
  "cache_root": "/Users/username/Library/Unity/Asset Store-5.x",
  "publisher_count": 62,
  "package_count": 1847,
  "publishers": [
    {
      "name": "AlexisDevArt",
      "packageCount": 3,
      "packages": [
        {
          "publisher": "AlexisDevArt",
          "category": "3D Models",
          "subcategory": "Characters",
          "name": "Orc Pack",
          "path": "/Users/.../Asset Store-5.x/AlexisDevArt/3D ModelsCharacters/Orc Pack.unitypackage",
          "sizeBytes": 45678901,
          "lastModified": "2024-11-15T10:22:00Z"
        }
      ]
    }
  ]
}
```

**Caching:** First call scans filesystem (1-5 seconds). Result cached in `.unity-craft/asset-cache.json`. Subsequent calls <24h return cache unchanged. `--refresh` bypasses cache.

**Error Handling:**
```json
{
  "error": "cache_not_found",
  "message": "Asset Store-5.x cache not found. Check ~/Library/Unity/Asset Store-5.x (macOS) or %APPDATA%\\Unity\\Asset Store-5.x (Windows)"
}
```

---

### Assets_Suggest(task, source = "auto", budget = "both", maxResults = 10, pipelineFilter = null)

Dispatch to E16 (Asset Store Curator) with local inventory + task, returns ranked recommendations.

**Arguments:**
| Arg | Type | Default | Example | Notes |
|-----|------|---------|---------|-------|
| `task` | string | — | "I need a low-poly fantasy environment" | User's asset need |
| `source` | string | "auto" | "auto" \| "upm" \| "asset-store" \| "all" | Registry source: `"auto"` tries UPM official first, then OpenUPM, then Asset Store; `"upm"` queries only Unity Registry + OpenUPM + Git UPM; `"asset-store"` skips UPM; `"all"` queries every source and interleaves results |
| `budget` | string | "both" | "free" \| "paid" \| "both" | Price filter |
| `maxResults` | int | 10 | 5, 15 | Top-N results |
| `pipelineFilter` | string | null | "URP" \| "HDRP" \| "Built-in" | Optional: render pipeline |

**Output:**
```json
{
  "task": "low-poly fantasy environment",
  "ownedAssets": [
    {"name": "ScansFactory - Modular Environments", "publisher": "Scans Factory", "category": "3D Models/Environments"}
  ],
  "recommendations": [
    {
      "packageName": "Synty POLYGON - Fantasy Kingdom",
      "publisher": "POLYGON by Synty",
      "price": "$35",
      "rating": "4.7/5 (892 reviews)",
      "category": "3D Models/Environments",
      "unityVersionSupport": "2020.3 LTS, 2021 LTS, 2022 LTS, 6",
      "url": "https://assetstore.unity.com/packages/3d/environments/fantasy/polygon-fantasy-kingdom-170842",
      "reasoning": "Highest-rated stylized fantasy environment; actively maintained; perfect art style match; comparable to your Scans Factory",
      "competesWith": ["ScansFactory"],
      "upmOrLegacy": ".unitypackage",
      "estimatedValue": "Excellent for mid-budget indie projects"
    },
    {
      "packageName": "Kenney Assets — Fantasy",
      "publisher": "Kenney",
      "price": "Free",
      "rating": "4.5/5 (245 reviews)",
      "category": "3D Models/Characters",
      "unityVersionSupport": "All LTS versions",
      "url": "https://assetstore.unity.com/packages/3d/characters/creatures/kenney-fantasy-creatures-free-206940",
      "reasoning": "Free alternative; good variety; slightly lower fidelity than Synty; excellent for quick prototyping",
      "competesWith": ["None"],
      "upmOrLegacy": ".unitypackage",
      "estimatedValue": "Best free option for learning"
    }
  ],
  "summary": "2 paid options (Synty, Fimpossible FX) + 3 free alternatives. You already own Scans Factory — consider supplementing with Synty POLYGON for production quality or Kenney Assets for learning."
}
```

**E16 Dispatch Protocol (Internal):**

Input to E16:
```json
{
  "task": "low-poly fantasy environment",
  "owned_inventory": [
    {"name": "ScansFactory", "publisher": "Scans Factory", "category": "Environments"}
  ],
  "budget": "both",
  "maxResults": 10,
  "pipelineFilter": null
}
```

E16 workflow:
1. Parse task intent (keywords: "fantasy", "environment", "low-poly")
2. Load owned inventory to avoid duplicate recommendations
3. Query Asset Store (free + paid variants)
4. Filter by budget + pipeline + compatibility
5. Rank by: rating, reviews, maintenance status, value vs owned assets
6. Return top N with reasoning + conflict analysis (competesWith)

**Web Research Approach:**
E16 uses `fetch` MCP to query Asset Store listing pages:
```
https://assetstore.unity.com/packages/search?q=fantasy+environment&price=0-0  (free)
https://assetstore.unity.com/packages/search?q=fantasy+environment&price=1-  (paid)
```
Parses HTML for product cards: name, rating, price, publisher, url.
Rate limit: ~10 requests/minute (respectful crawling).

---

### Assets_InstallUPM(packageId, version = null)

Install UPM package into target project's `Packages/manifest.json` via CRAFT transaction (rollback-able).

**Arguments:**
| Arg | Type | Default | Example | Notes |
|-----|------|---------|---------|-------|
| `packageId` | string | — | "com.synty.polygon" | UPM package ID from Asset Store |
| `version` | string | null | "2.0.0" | Optional: specific version; default = latest |

**Output (Success):**
```json
{
  "status": "success",
  "transactionId": "craft-install-upm-synty-polygon-2026-04-18",
  "packageId": "com.synty.polygon",
  "version": "2.0.0",
  "manifestPath": "Packages/manifest.json",
  "installedAt": "2026-04-18T14:35:22Z",
  "note": "UPM packages auto-download on next Editor restart. Package ready in Unity 2022 LTS+"
}
```

**Implementation:**
1. Query target project's `Packages/manifest.json`
2. CRAFT transaction: modify manifest, add dependency entry
3. Unity Editor auto-downloads package on next load
4. Return transactionId for rollback

**Error Handling:**
```json
{
  "error": "manifest_not_found",
  "message": "Packages/manifest.json not found. Ensure this is a valid Unity project."
}
```

**Rollback:** `Craft_Rollback({ "transactionId": "craft-install-upm-synty-polygon-..." })`

---

### Assets_InstallLegacy(packagePath, targetPath = "Assets/Imported/")

Legacy .unitypackage import requires upstream op `Craft_ImportUnityPackage` (v0.3+, not shipped in v0.2).

**Future Note:** v0.2 cannot import .unitypackage files. Coordinate with CRAFT v0.3 roadmap for this capability.

**Workaround (v0.2):**
Manual: User downloads `.unitypackage` from Asset Store, double-clicks to import (Editor handles).

---

### Assets_CompareOwned(need)

Query owned inventory (Assets_ScanLibrary result) to answer "do I already have something for this?"

**Arguments:**
| Arg | Type | Example | Notes |
|-----|------|---------|-------|
| `need` | string | "character animation system" | User's stated need |

**Output:**
```json
{
  "need": "character animation system",
  "matches": [
    {
      "owned": true,
      "name": "Mixamo Animations",
      "publisher": "Mixamo",
      "category": "Animation",
      "reason": "Exact match: character animations in library"
    }
  ],
  "summary": "You already own Mixamo Animations — covers most character animation needs. Consider E16 Assets_Suggest for advanced systems (procedural animation, behavior trees)."
}
```

---

## Pipeline Diagram

```
User: "I need a low-poly fantasy environment"
  ↓
Assets_ScanLibrary(refresh=false)
  ↓ (local cache scan, ~100ms)
{
  publisher_count: 62,
  packages: [...]
}
  ↓
E16 dispatch with:
  - Task: "low-poly fantasy environment"
  - Owned inventory: [ScansFactory, ...]
  - Budget: "both"
  ↓ (web research)
E16: Query Asset Store (free + paid)
  ↓
E16: Rank by rating, reviews, maintenance
  ↓
E16: Filter owned assets (avoid duplicates)
  ↓
Return ranked list:
[
  {packageName, publisher, price, rating, url, reasoning, competesWith, ...}
]
  ↓
User selects candidate
  ↓
Assets_InstallUPM(packageId, version) OR manual .unitypackage import
  ↓
✓ Installed
```

---

## E16 Dispatch Protocol

**When Assets_Suggest is called:**

1. Extract task, budget, pipeline from arguments
2. Call Assets_ScanLibrary to get owned inventory
3. Invoke E16 with structured input:
   ```json
   {
     "dispatch": "asset_recommendation",
     "task": "user's need",
     "owned_inventory": [{...}],
     "constraints": {
       "budget": "both|free|paid",
       "maxResults": 10,
       "renderPipeline": "URP|HDRP|Built-in|null"
     }
   }
   ```
4. E16 returns JSON recommendations
5. Return to user with format as above

---

## Web Research Approach

E16 researches Asset Store via `fetch` MCP:

```
Fetch: https://assetstore.unity.com/packages/search?q=fantasy+environment&price=0-0&sort=rating
Parse HTML for product cards
Extract: name, rating (X.Y/5), review count, price, publisher, url
Return top 5-10 ranked by rating ↓ review count
```

**Rate Limiting:** Respectful crawling, ~10 reqs/min. Cache results <24h.
**Fragility:** Web scraping fragile to UI redesigns; fallback to cached knowledge if scrape fails.

---

## UPM Registry Search Pipeline

When `source="auto"` or `source="upm"`, E16 searches three UPM sources in order:

**Search Order (source="auto"):**

1. **Fetch Unity's official package list** (cached 7 days)
   - Source: `https://docs.unity3d.com/Manual/PackagesList.html`
   - Method: Parse HTML for `com.unity.*` packages matching search terms
   - Example: User asks "I need async support" → scan docs for `com.unity.inputsystem`, `com.unity.*`
   - Fallback: Direct package docs URL `https://docs.unity3d.com/Packages/com.unity.<name>@latest/manual/index.html`

2. **Query OpenUPM API**
   - Source: `https://api.openupm.com/search-v2?q=<terms>`
   - Method: JSON response with `name`, `downloads`, `stars`, `version`, `repo`
   - Take top 5 results ranked by download count
   - Example: User asks "I need async support" → API returns `com.cysharp.unitask` (15k downloads, MIT)

3. **Query Asset Store** (only if UPM sources returned < maxResults/2 matches)
   - Source: Asset Store web pages (HTML scraping)
   - Method: Fetch and parse free packages, then paid if budget allows
   - Stop early if enough results accumulated

**openupm CLI (optional):**
Agent can invoke `openupm add <package>` or edit `manifest.json` directly. Both paths supported:
- CLI: `openupm add com.cysharp.unitask` → auto-edits manifest
- Manual: Add `scopedRegistry` entry to `Packages/manifest.json` + add dependency

**Assets_InstallUPM behavior per source:**

| Package type | Installation method | Example |
|---|---|---|
| `com.unity.*` | Add simple dependency to manifest | `"com.unity.addressables": "1.21.0"` |
| OpenUPM package | Add scopedRegistry for `package.openupm.com` + dependency | `scopedRegistries` entry + `"com.cysharp.unitask": "2.5.1"` |
| Git UPM URL | dependency value is the full git URL with optional tag | `"com.cysharp.unitask": "https://github.com/Cysharp/UniTask.git#v2.5.1"` |

---

## Privacy & Data

- **Inventory JSON stays local** — `.unity-craft/asset-cache.json` never uploaded
- **Cached inventory** — only shared with E16 for recommendation matching
- **No telemetry** — plugin does not report user inventory to external services
- **Asset URLs** — returned from Asset Store public pages (no auth required)

---

## Worked Examples

### Example 1: Free Alternative Check
```
User: "I need a flexible damage number system"
Assets_ScanLibrary() → Library has: [TextMesh Pro, Playmaker, old tweening]
Assets_Suggest("damage numbers", budget="free") →
E16: Searches for "damage number" free assets
Returns:
  1. "Floating Damage Text System" (free, simple, 100+ reviews)
  2. "Easy Floating Text" (free, lightweight)
  3. "TextMesh Pro + coroutines" (no purchase needed, use owned asset)
Summary: "No owned damage system. 3 excellent free options. 
          TextMesh Pro + simple C# coroutines sufficient for indie games."
```

### Example 2: Owned Asset Conflict
```
User: "I want cinematic sequences with advanced camera"
Assets_ScanLibrary() → Library has: [Cinemachine 2.4, Timeline, PostProcessing]
Assets_Suggest("cinematic camera", budget="free") →
E16: Recognizes owned Cinemachine + Timeline
Returns:
  1. "E9 Cinematic Director" (internal tool, free, native integration)
  2. "Advanced Cutscene Manager" (free, build on Timeline)
  3. "Cinemachine Pro" (paid, $50, redundant with owned v2.4)
Summary: "You already own Cinemachine 2.4 + Timeline — sufficient for cinematics.
          Upgrade to Pro ($50) only if you need advanced rig types (not yet available in free)."
```

### Example 3: Render Pipeline Compat Check
```
User: "I need an advanced tonemapping system for URP"
Project: URP (not Built-in or HDRP)
Assets_Suggest("tonemapping URP", pipelineFilter="URP") →
E16: Filters for URP-compatible only
Returns:
  1. "Amplify Color for URP" (paid, $35, actively maintained, 4.8/5)
  2. "Custom Post Processing" (free, but limited tonemapping)
Summary: "Amplify Color is industry-standard for URP color grading + tonemapping.
          Custom Post Processing free alternative if budget limited, but fewer controls."
```

### Example 4: UPM Registry Priority Beats Asset Store
```
User: "I need async/await support without coroutines"
Assets_Suggest("async/await", source="auto") →
E16 search order:
  1. Unity Registry: No first-party async package
  2. OpenUPM: Finds com.cysharp.unitask (15k+ downloads, MIT license, actively maintained)
  3. Asset Store: Skipped (UPM source already sufficient)
Returns:
  1. Cysharp UniTask (OpenUPM, free, MIT, industry-standard, 4.9/5 from community)
  2. Async Helpers (Asset Store, free, simpler but lower quality)
Summary: "source='auto' discovered Cysharp UniTask via OpenUPM — battle-tested async 
          library, MIT licensed, zero cost. This is why UPM registries often beat Asset 
          Store: better quality, free, active community maintenance. 
          Assets_InstallUPM('com.cysharp.unitask') adds scopedRegistry + dependency."
```

---

## Limitations

1. **No auto-login:** Plugin cannot authenticate to Unity Hub. User downloads manually or via Asset Store client.

2. **Legacy .unitypackage import:** Not available in CRAFT v0.2. Requires upstream `Craft_ImportUnityPackage` op (planned v0.3).

3. **Dynamic list binding:** Assets_Suggest returns static list. ListViews and real-time updates require C# wiring.

4. **Web scraping fragility:** Asset Store page redesigns may break E16 scraper. Fallback: cached knowledge base.

5. **No price history:** Cannot predict sales or discounts. All prices as-of query time.

6. **Rating lag:** Published ratings may lag by hours. Cache respects this with caution flag if >4h old.

7. **OpenUPM API reliability:** OpenUPM search API has no published SLA. On 500-level errors, agent must gracefully fall back to docs.unity3d.com scraping or cached knowledge.

8. **Git UPM discovery requires GitHub token:** GitHub API used to discover and verify Git UPM packages. `GITHUB_TOKEN` env var must be provided in workspace; already available in this workspace.

---

## Verification Checklist

After implementation, verify:

- [ ] Assets_ScanLibrary returns ≥50 publishers on reference machine
- [ ] Assets_ScanLibrary cache persists and is <24h old
- [ ] Assets_Suggest("chess piece 3d model", budget="free") returns ≥3 results with valid urls
- [ ] Assets_Suggest filters correctly by budget (free vs paid)
- [ ] E16 dispatch receives owned inventory correctly
- [ ] Recommendations ranked by rating + review count + maintenance
- [ ] E16 identifies conflicts (competesWith field populated)
- [ ] Assets_InstallUPM edits manifest.json and returns transactionId
- [ ] Rollback works: Craft_Rollback restores previous manifest

---

## Related Tools & Agents

- **E16 (Asset Store Curator)** — agent; web research + ranking
- **B53 (Performance Analyzer)** — validate texture/shader/pipeline compat
- **D11 (UI Developer)** — UI asset adaptation
- **K3 (Research Agent)** — fallback for deep publisher reputation research
- **CRAFT_Execute** — UPM package installation via manifest edit
- **CRAFT_Rollback** — undo failed installations

---

## References

- [Unity Asset Store](https://assetstore.unity.com)
- [E16 Agent: Asset Store Curator](../../../agents/3d-cad/asset-store-curator/AGENT.md)
- [E16 Knowledge: Asset Store Taxonomy](../../../agents/3d-cad/asset-store-curator/knowledge/asset-store-taxonomy.md)
- [UPM Package Manager](https://docs.unity3d.com/Manual/upm-ui.html)
- [CRAFT Transaction Safety](../SKILL.md)

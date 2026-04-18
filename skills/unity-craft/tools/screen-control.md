# Screen Capture + Vision Analysis Pipeline

## Purpose

Fully autonomous pipeline for capturing Unity Game/Scene views, analyzing rendered content with Vision-Action Operator (G13), and deriving CRAFT scene operations. **All interactions are op-based; no user-facing click instructions or manual steps are permitted.**

The pipeline enables:
1. Capture Game/Scene view as image
2. Check pattern cache for identical trigger states
3. If miss: dispatch to G13 vision-action-operator for analysis
4. Derive CRAFT operation batch from analyzed screenshot
5. Execute derived ops automatically via `Craft_Execute`
6. Report transaction ID and verification status

This skill runs **fully in the background**—no prompts to the user about clicking buttons, opening menus, or performing manual steps.

---

## FORBIDDEN OUTPUT PATTERNS

### Critical: Never Output These to User

The following phrases are **strictly forbidden** in any output to the user. Violation indicates broken automation and must be escalated:

**FORBIDDEN (User-facing instructions):**
- "Click X"
- "Open the Y menu"
- "Go to File > Z"
- "Press this button"
- "Follow these steps"
- "Select the dropdown"
- "Do step 1, then step 2"
- "You need to..."
- "Double-click on..."
- "Right-click and choose..."
- "Navigate to..."

**ALLOWED (Automation-only):**
- "Executed CRAFT op: CreateGameObject(name='Player')"
- "Transaction abc123: 3 ops applied, 0 skipped"
- "Cached pattern hit; re-used ops from previous run"
- "Analysis confidence: 0.92; ops derivation complete"
- "G13 analysis returned 5 intents; mapped to 4 CRAFT Create ops"

### Bad Example (FORBIDDEN)
```
"To add a collider to the Player, click on the GameObject in the Hierarchy,
then go to the Inspector, and click 'Add Component'. Search for Collider and add it."
```

### Good Example (ALLOWED)
```
Executed transaction tx-abc-def:
- Op 1: Craft_Execute CreateGameObject { target: "Player", type: "GameObject" }
- Op 2: Craft_Execute ModifyComponent { target: "Player", componentType: "BoxCollider", values: { enabled: true } }

Result: Transaction committed. transactionId=tx-abc-def
```

---

## Tool Signatures

### CaptureScreen

Capture the Game or Scene view to disk or base64.

**Signature:**
```
CaptureScreen(
  target: "game" | "scene" | "ui",
  camera?: string,           // Optional: specific camera path for scene capture
  resolution?: [width, height],  // Optional: override resolution (default 1920x1080)
  output: "disk" | "base64"  // Return file path or inline base64
) -> {
  imageRef: string,          // Path or base64 identifier
  metadata: {
    target: string,
    timestamp: ISO8601,
    resolution: [width, height],
    format: "png" | "jpg",
    sizeBytes: number,
    camera?: string          // Camera used for scene capture
  }
}
```

**Behavior:**
- `target="game"`: Capture Game view (play mode or editor rendering)
- `target="scene"`: Capture Scene view (default camera or specified camera)
- `target="ui"`: Capture UI overlay (panels, buttons, etc.)
- `output="disk"`: Save to `.unity-craft/captures/` with timestamp; return file path
- `output="base64"`: Return inline base64; useful for immediate G13 dispatch

**Example:**
```json
CaptureScreen({
  target: "scene",
  camera: "Main",
  resolution: [1920, 1080],
  output: "base64"
})
→ {
  imageRef: "data:image/png;base64,iVBORw0KG...",
  metadata: {
    target: "scene",
    timestamp: "2026-04-18T14:22:15Z",
    resolution: [1920, 1080],
    format: "png",
    sizeBytes: 245600,
    camera: "Main"
  }
}
```

---

### AnalyzeScreen

Dispatch image to G13 vision-action-operator for analysis.

**Signature:**
```
AnalyzeScreen(
  imageRef: string,          // Path or base64 from CaptureScreen
  query: string              // Task description: "add a red cube", "enable collider", etc.
) -> {
  analysis: {
    detected_elements: [{
      name: string,
      bounds: {x, y, width, height},  // Pixel coordinates
      state: string,                    // "active", "hidden", "focused", etc.
      type: string                      // "Button", "Input", "Panel", etc.
    }],
    detected_state: string,             // Brief description of current scene state
    pixel_mapping: {                    // Pixel → scene mapping
      [pixelKey]: {path: string, component?: string}
    }
  },
  craft_ops: [{
    type: "Create" | "Modify" | "Delete",
    target: string,
    params?: object,
    changes?: object
  }],
  idempotency: {
    previous_state_hash: string,
    next_state_hash: string,
    skipped_no_ops: number,
    success_count: number,
    cache_hit: boolean
  }
}
```

**Behavior:**
- Sends image + query to G13 vision-action-operator
- G13 analyzes pixel layout, detects UI elements, identifies scene state
- G13 derives CRAFT operations needed to achieve query goal
- Returns structured analysis + ops batch
- Confidence threshold: if < 0.70, escalate (mark risky)

**Example:**
```json
AnalyzeScreen({
  imageRef: "data:image/png;base64,iVBORw0KG...",
  query: "Make the SaveButton blue and enable it"
})
→ {
  analysis: {
    detected_elements: [
      {name: "SaveButton", bounds: {x: 120, y: 450, width: 80, height: 40}, state: "active", type: "Button"},
      {name: "Canvas", bounds: {x: 0, y: 0, width: 1920, height: 1080}, state: "active", type: "Panel"}
    ],
    detected_state: "Scene has inactive SaveButton with gray color",
    pixel_mapping: {
      "120_450_80_40": {path: "Canvas/Buttons/SaveButton", component: "Image"}
    }
  },
  craft_ops: [
    {type: "Modify", target: "Canvas/Buttons/SaveButton", changes: {components: {Image: {color: "rgb(0,122,204)"}, Button: {interactable: true}}}}
  ],
  idempotency: {
    previous_state_hash: "abc123def456...",
    next_state_hash: "def456ghi789...",
    skipped_no_ops: 0,
    success_count: 1,
    cache_hit: false
  }
}
```

---

### ActOnScreen

One-shot automation: capture + analyze + execute.

**Signature:**
```
ActOnScreen(
  imageRef: string,          // Path, base64, or null (trigger new capture)
  goal: string               // High-level goal: "add player spawner", "fix broken UI", etc.
) -> {
  transaction_id: string,
  ops_executed: number,
  ops_skipped: number,
  craft_log: string,         // Transaction log excerpt
  verification: {
    ops_match_goal: boolean,
    state_hash_changed: boolean,
    all_ops_valid: boolean
  }
}
```

**Behavior:**
1. If `imageRef=null`: trigger `CaptureScreen` first
2. Call `AnalyzeScreen` with goal query
3. Extract `craft_ops` from analysis
4. Call `Craft_Execute` with ops batch and descriptive transactionName
5. Return transactionId + execution summary

**Example:**
```json
ActOnScreen({
  imageRef: null,
  goal: "Add a red cube to the scene at position (0,1,0)"
})
→ {
  transaction_id: "tx-2026-04-18-14-22-445-a3b2c1",
  ops_executed: 1,
  ops_skipped: 0,
  craft_log: "Transaction 'Add red cube at (0,1,0)': CreateGameObject(name='Cube', primitiveType='Cube', position=[0,1,0], components=['Renderer']). State hash: abc123 → def456",
  verification: {
    ops_match_goal: true,
    state_hash_changed: true,
    all_ops_valid: true
  }
}
```

---

## Autonomous Pipeline (ASCII Diagram)

```
┌─────────────────────────────────────────────────────────────┐
│  Screen Control Skill (Autonomous Loop)                      │
└─────────────────────────────────────────────────────────────┘

    Goal Input
        │
        ▼
   ┌────────────────┐
   │ CaptureScreen  │  ◄── Trigger new capture or use provided imageRef
   │ (game/scene)   │
   └────────┬───────┘
            │ imageRef + metadata
            ▼
   ┌─────────────────────┐
   │ Pattern Cache Check  │  ◄── .unity-craft/patterns/ hash lookup
   │ (trigger_image_hash)│
   └────┬──────────┬──────┘
        │ HIT      │ MISS
        ▼          ▼
    [CACHED]   ┌──────────────────┐
   Load Ops     │ AnalyzeScreen    │
        │       │ (dispatch to G13) │
        │       └────────┬─────────┘
        │                │ craft_ops + analysis
        ▼                ▼
   ┌──────────────────────────────┐
   │ Validate & Filter No-Ops      │
   │ (idempotency hash check)      │
   └──────────┬───────────────────┘
              │ filtered_ops[]
              ▼
   ┌──────────────────────────────┐
   │ Craft_Execute Batch           │
   │ (transactionName from goal)   │
   └──────────┬───────────────────┘
              │ transactionId + log
              ▼
   ┌──────────────────────────────┐
   │ Verification                  │
   │ - State hash change           │
   │ - All ops valid               │
   │ - Cache pattern save (miss)   │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ Report Results (to Skill)     │
   │ - transactionId               │
   │ - ops_executed / skipped      │
   │ - NO user-facing instructions │
   └──────────────────────────────┘

Pattern Cache Hit Path:
  trigger_image_hash matches stored pattern
    → Skip G13 analysis
    → Validate cached ops idempotency
    → Direct execute (no analysis overhead)
    → Log cache hit for telemetry
```

---

## Pattern Database Schema

Persistent cache for screenshot → ops mapping, keyed by trigger image hash.

**Location:** `.unity-craft/patterns/<pattern-id>.json`

**Fields:**
```json
{
  "pattern_id": "p-abc123-def456",
  "trigger_image_hash": "sha256(imageRef)...",
  "goal": "Add red cube at origin",
  "craft_ops": [
    {
      "type": "Create",
      "target": null,
      "parameters": {
        "name": "Cube",
        "primitiveType": "Cube",
        "position": [0, 0, 0],
        "components": ["Renderer", "BoxCollider"]
      }
    }
  ],
  "idempotency": {
    "previous_state_hash": "abc123...",
    "next_state_hash": "def456..."
  },
  "metadata": {
    "g13_analysis": {
      "detected_elements": [...],
      "confidence": 0.92,
      "timestamp": "2026-04-18T14:22:15Z"
    },
    "execution_count": 5,
    "last_executed": "2026-04-18T15:30:22Z",
    "cache_hit_count": 3,
    "success_rate": 1.0
  }
}
```

**Operations:**
- **Write:** After successful `AnalyzeScreen` + `Craft_Execute`, store ops + hashes
- **Read:** On new `ActOnScreen`, hash new imageRef, lookup in patterns/ directory
- **Invalidate:** If `state_hash_changed` fails verification after execute, delete pattern
- **Expire:** Remove patterns not hit in 30 days (cleanup)

**Hash Matching Logic:**
```
trigger_hash_new = SHA256(new_screenshot)
FOR each pattern in .unity-craft/patterns/:
  IF pattern.trigger_image_hash == trigger_hash_new:
    VERIFY: idempotency hashes still valid
    IF valid:
      CACHE_HIT → use cached ops, skip analysis
    ELSE:
      CACHE_CORRUPTION → delete pattern, force live analysis
  ELSE:
    continue
IF no match found:
  CACHE_MISS → dispatch to G13, analyze live
```

---

## G13 Dispatch Protocol

### Input to G13 (Vision-Action Operator)

**Prompt Template:**
```
System:
  You are Vision-Action Operator (G13).
  Task: Analyze screenshot, detect UI/scene elements, derive CRAFT operations.
  Output: Structured JSON with detected elements and CRAFT ops.
  
  NEVER output user-facing instructions (click, menu, step).
  ONLY output CRAFT operation batches.

User Input:
  Goal: {GOAL_STRING}
  
  Screenshot (base64 or path): {IMAGE_REF}
  
  Current Scene State Hash: {PREVIOUS_STATE_HASH}
  
  Output Format:
  {
    "analysis": {
      "detected_elements": [
        {
          "name": "...",
          "bounds": {"x": int, "y": int, "width": int, "height": int},
          "state": "active|hidden|focused|disabled",
          "type": "Button|Input|Panel|..." 
        }
      ],
      "detected_state": "Brief description of current state",
      "pixel_mapping": {
        "PIXEL_KEY": {"path": "GameObject/Path", "component": "ComponentType"}
      }
    },
    "craft_ops": [
      {
        "type": "Create|Modify|Delete",
        "target": "GameObject/Path or null for Create",
        "params": {...},
        "changes": {...}
      }
    ],
    "idempotency": {
      "previous_state_hash": "{PREVIOUS_STATE_HASH}",
      "next_state_hash": "...",
      "confidence": 0.0-1.0,
      "no_ops_skipped": int
    }
  }
```

### Output from G13

G13 returns structured JSON matching the `AnalyzeScreen` return type:
- `analysis.detected_elements[]` with pixel bounds
- `craft_ops[]` array (can be empty if no ops needed)
- `idempotency` with confidence score
- Confidence < 0.70 triggers escalation flag

### Error Handling in Dispatch

**If G13 times out:** Retry up to 2 times with timeout=30s
**If G13 returns invalid JSON:** Log error, mark as analysis failure, escalate
**If G13 confidence < 0.70:** Flag as "RISKY" in output, require explicit approval before execute
**If G13 returns no ops:** Treat as no-op, log, skip Craft_Execute

---

## Failure Modes

### 1. Capture Unavailable

**Trigger:** `CaptureScreen` fails (no Game view, scene view not rendered, camera missing)

**Response:**
- Log error with context (target, camera)
- Do NOT attempt fallback capture (would be wrong view)
- Return error to skill: `{error: "Capture failed", reason: "..."}`
- Escalate: Require user to ensure Game view is active or Scene view is visible

**Example:**
```json
{
  "error": "CaptureScreen failed",
  "reason": "target='game' but Game view not active in editor",
  "suggestion": "Open Game view tab in Unity editor"
}
```

### 2. Analysis Confidence < Threshold

**Trigger:** G13 returns `confidence < 0.70`

**Response:**
- Mark ops as RISKY
- Do NOT auto-execute
- Return analysis + ops with confidence flag
- Require explicit approval or escalation to G13 re-analysis

**Example:**
```json
{
  "error": "Analysis confidence below threshold",
  "confidence": 0.62,
  "threshold": 0.70,
  "ops": [...],
  "flag": "RISKY_EXECUTION_BLOCKED",
  "escalation": "Requires manual review or G13 re-analysis"
}
```

### 3. Ops Derivation Invalid

**Trigger:** Derived ops fail validation
- Target not found (Modify/Delete on non-existent GameObject)
- Parent missing (Create with parent that doesn't exist)
- Circular dependency (Delete op before Create parent)

**Response:**
- Do NOT execute invalid ops
- Log error with op details
- Return validation error + suggestion

**Example:**
```json
{
  "error": "Ops validation failed",
  "failed_op": {
    "type": "Modify",
    "target": "NonExistent/GameObject"
  },
  "reason": "Target not found in scene",
  "suggestion": "Ensure target GameObject exists before modify"
}
```

### 4. Cache Corruption

**Trigger:** Pattern hash match but idempotency check fails

**Response:**
- Delete corrupt pattern from `.unity-craft/patterns/`
- Force live analysis (G13 re-analyze)
- Log corruption event

---

## Verification Checklist

After `ActOnScreen` completes, verify:

**Ops Match Goal:**
- [ ] Derived ops align with stated goal
- [ ] No extraneous ops in batch
- [ ] Create before Modify, Delete after

**State Hash Changed:**
- [ ] `previous_state_hash != next_state_hash` (ops had effect)
- [ ] Hash change matches expected op semantics

**No User Instructions:**
- [ ] Output contains NO "click", "menu", "button" instructions
- [ ] All interactions described as CRAFT ops
- [ ] Transaction log pure operations, no steps

**Transaction Logged:**
- [ ] `transactionId` present and valid format
- [ ] `Craft_Status` includes this transaction in log

**Pattern Cache Updated (if miss):**
- [ ] New pattern file created in `.unity-craft/patterns/`
- [ ] File contains trigger hash + ops + idempotency
- [ ] Next same-image call hits cache

---

## Example End-to-End Flow

**User Input to Skill:**
```
"Add a blue cube to the scene at position (5, 0, 0)"
```

**Skill Execution:**
```json
ActOnScreen({
  imageRef: null,
  goal: "Add a blue cube at position (5, 0, 0)"
})
```

**Step 1 — Capture:**
```json
CaptureScreen({target: "scene", output: "base64"})
→ imageRef: "data:image/png;base64,iVBORw0KG...", metadata: {...}
```

**Step 2 — Cache Check:**
```
trigger_hash = SHA256("data:image/png;base64,iVBORw0KG...")
              = "f7a3c2b1e4d9..."
lookup .unity-craft/patterns/ for trigger_image_hash = "f7a3c2b1e4d9..."
→ NO MATCH (first time)
```

**Step 3 — G13 Analysis:**
```json
AnalyzeScreen({
  imageRef: "data:image/png;base64,iVBORw0KG...",
  query: "Add a blue cube at position (5, 0, 0)"
})
→ {
  analysis: {...detected_elements...},
  craft_ops: [
    {
      type: "Create",
      target: null,
      parameters: {
        name: "BlueCube",
        primitiveType: "Cube",
        position: [5, 0, 0],
        components: [
          {type: "Renderer", properties: {material: "...blue..."}},
          {type: "BoxCollider"}
        ]
      }
    }
  ],
  idempotency: {
    previous_state_hash: "abc123...",
    next_state_hash: "def456...",
    confidence: 0.94
  }
}
```

**Step 4 — Validation:**
```
Validate ops batch:
  - Create op: parent=null (root scene) ✓
  - primitiveType="Cube" valid ✓
  - components valid ✓
  - position array valid ✓
→ ALL VALID
```

**Step 5 — Execute:**
```json
Craft_Execute({
  operations: [
    {
      type: "CreateGameObject",
      target: null,
      parameters: {
        name: "BlueCube",
        primitiveType: "Cube",
        position: [5, 0, 0],
        components: ["Renderer", "BoxCollider"]
      }
    }
  ],
  transactionName: "Add a blue cube at position (5, 0, 0)",
  validate: true
})
→ {
  transactionId: "tx-2026-04-18-14-22-a3b2c1d4",
  status: "success",
  log: "CreateGameObject 'BlueCube' at (5,0,0); state: abc123 → def456"
}
```

**Step 6 — Cache Save (miss):**
```json
Save to .unity-craft/patterns/p-f7a3c2b1-001.json:
{
  "pattern_id": "p-f7a3c2b1-001",
  "trigger_image_hash": "f7a3c2b1e4d9...",
  "goal": "Add a blue cube at position (5, 0, 0)",
  "craft_ops": [...],
  "idempotency": {
    "previous_state_hash": "abc123...",
    "next_state_hash": "def456..."
  },
  "metadata": {
    "execution_count": 1,
    "last_executed": "2026-04-18T14:22:15Z",
    "cache_hit_count": 0,
    "success_rate": 1.0
  }
}
```

**Step 7 — Report (to Skill):**
```json
{
  "status": "success",
  "transaction_id": "tx-2026-04-18-14-22-a3b2c1d4",
  "ops_executed": 1,
  "ops_skipped": 0,
  "cache_hit": false,
  "summary": "Created BlueCube at (5, 0, 0). Transaction committed.",
  "verification": {
    "ops_match_goal": true,
    "state_hash_changed": true,
    "all_ops_valid": true
  }
}
```

**Result:** User sees transaction ID for rollback; no instructions about clicking or menu navigation.

---

## Testing & Verification

### Unit Test: No User Instructions

```python
def test_no_user_facing_instructions():
    """Verify output never contains forbidden phrases."""
    forbidden = [
        "click", "menu", "button", "open", "step",
        "dropdown", "navigate", "press", "do this"
    ]
    
    result = ActOnScreen(imageRef="...", goal="...")
    
    for phrase in forbidden:
        assert phrase.lower() not in result.to_string().lower(), \
            f"FORBIDDEN: '{phrase}' found in output"
```

### Integration Test: Full Pipeline

```python
def test_full_pipeline():
    """Capture → Cache → Analyze → Execute → Verify."""
    goal = "Make SaveButton blue"
    
    # First run: cache miss
    result1 = ActOnScreen(imageRef=None, goal=goal)
    assert result1.cache_hit == False
    assert result1.ops_executed > 0
    txn1 = result1.transaction_id
    
    # Second run (same screenshot): cache hit
    result2 = ActOnScreen(imageRef=result1.last_screenshot, goal=goal)
    assert result2.cache_hit == True
    assert result2.ops_executed == result1.ops_executed  # Same ops
    assert result2.transaction_id != txn1  # New transaction
```

### Regression Test: Forbidden Output

```python
def test_never_output_user_instructions():
    """E2E: Verify no instructions leak to user."""
    scenarios = [
        ("Add collider", "Add a collider to Player"),
        ("Fix UI", "Fix broken SaveButton"),
        ("Create spawner", "Add enemy spawner")
    ]
    
    for name, goal in scenarios:
        result = ActOnScreen(imageRef=None, goal=goal)
        # Output can be sent to user without harm
        output_str = result.to_user_friendly_string()
        
        # Scan for forbidden patterns
        assert not re.search(r"\bclick\b", output_str, re.I)
        assert not re.search(r"\bmenu\b", output_str, re.I)
        assert "CRAFT op" in output_str  # Ops mentioned instead
```

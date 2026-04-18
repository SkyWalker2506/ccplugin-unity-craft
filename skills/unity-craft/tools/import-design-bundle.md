# ImportDesignBundle Tool Specification

## Purpose

ImportDesignBundle enables Claude to import Claude Design handoff bundles (UI component hierarchies, design tokens, HTML/CSS) directly into Unity UI Toolkit scenes. Released April 2026, Claude Design bundles provide designers with a standardized handoff format; this tool bridges that to UXML/USS, making UI Toolkit the natural composition target. The tool handles bundle fetch, caching, design-to-code transpilation (via D11 agent dispatch), and scene integration via CRAFT operations.

## Signature

```
ImportDesignBundle(
  bundleUrl,           // string: URL to Claude Design bundle API endpoint
  targetScenePath,     // string: Unity scene path (e.g., "Assets/Scenes/MainMenu.unity")
  canvasName = "MainMenu"  // string: UIDocument GameObject name + UXML/USS namespace
)
```

### Arguments

| Argument | Type | Default | Example | Notes |
|----------|------|---------|---------|-------|
| `bundleUrl` | string | — | `https://design.example.com/api/bundles/abc123` | Must return 200 + valid JSON (see Bundle Structure below) |
| `targetScenePath` | string | — | `Assets/Scenes/MainMenu.unity` | Scene must exist; UIDocument GameObject created if absent |
| `canvasName` | string | `MainMenu` | `LoginDialog`, `CharacterSelect` | Used for GameObject name + UXML/USS filenames; alphanumeric + underscore only |

## Bundle Structure

Claude Design API returns JSON conforming to this shape:

```json
{
  "components": [
    {
      "name": "MainMenu",
      "html": "<div class=\"menu-container\">...</div>",
      "css": ".menu-container { ... }",
      "interactions": [
        { "event": "click", "target": "#start-btn", "action": "navigate", "to": "/game" }
      ]
    }
  ],
  "designTokens": {
    "colors": { "primary": "#007AFF", "text": "#333333", "error": "#FF3B30" },
    "spacing": { "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px" },
    "radii": { "small": "4px", "default": "8px", "large": "12px" },
    "typography": {
      "body": "14px/1.5 -apple-system",
      "heading": "24px/1.2 -apple-system bold",
      "caption": "12px/1.4 -apple-system"
    }
  },
  "readme": "Menu system with login and main navigation...",
  "version": "1.0.0"
}
```

## Pipeline

### Step 1: Fetch Bundle

Claude issues HTTP GET to `bundleUrl` (with Bearer token if required):

```bash
curl -H "Authorization: Bearer $DESIGN_API_TOKEN" "$bundleUrl" \
  -o bundle.json
```

On failure (404, 401, timeout), report error with recovery suggestions (check token, verify URL).

### Step 2: Check Cache

Compute SHA256 hash of bundle JSON:

```
hash = SHA256(bundleJson)
cachePath = <project>/.unity-craft/design-cache/<hash>/
```

If `cachePath/bundle.json` exists and `version` field matches bundle, **skip to Step 4** (use cached UXML/USS).

Cache metadata stored in `<project>/.unity-craft/design-cache/metadata.json`:

```json
{
  "bundles": {
    "https://design.example.com/api/bundles/abc123": {
      "hash": "sha256-abc...",
      "cached_at": "2026-04-18T10:30:00Z",
      "version": "1.0.0"
    }
  }
}
```

### Step 3: Dispatch to D11 (unity-ui-developer)

Send bundle to D11 agent with this prompt template:

```
You are the Unity UI Developer (D11).

Task: Convert Claude Design bundle to UXML + USS.

Input (Claude Design bundle JSON):
{bundleJson}

Output format (return JSON):
{
  "components": [
    {
      "name": "MainMenu",
      "uxml": "<ui:UXML xmlns:ui=\"UnityEngine.UIElements\">...</ui:UXML>",
      "uss": ".container { flex-direction: column; ... }"
    }
  ],
  "tokens.uss": ":root { --color-primary: #007AFF; ... }",
  "metadata": {
    "componentCount": 1,
    "tokenCount": 15,
    "warnings": ["Hover states not wired to C# handlers"]
  }
}

Rules:
- HTML → UXML mapping (see reference table below)
- Design tokens → USS :root variables
- Preserve CSS structure; convert to USS syntax
- Do NOT generate C# event handlers (interactions wired by gameplay code)
- Return valid, unity-formatted XML/USS
```

D11 returns UXML + USS for each component. **Store results in cache:**

```
cachePath/
  ├── bundle.json
  ├── components/
  │   ├── MainMenu.uxml
  │   └── MainMenu.uss
  └── tokens.uss
```

### Step 4: Write to Assets

Copy cached UXML/USS to project:

```
Assets/UI/<canvasName>/
  ├── <canvasName>.uxml
  └── <canvasName>.uss
```

If directory absent, create it.

### Step 5: CRAFT Batch — Create UIDocument

Execute single CRAFT transaction to add UIDocument GameObject + configure:

```json
Craft_Execute({
  "operations": [
    {
      "type": "CreateGameObject",
      "target": null,
      "parameters": {
        "name": "<canvasName>",
        "components": ["UIDocument"],
        "tag": "UIRoot"
      }
    },
    {
      "type": "ModifyComponent",
      "target": "<canvasName>",
      "parameters": {
        "componentType": "UIDocument",
        "values": {
          "sourceAsset": "Assets/UI/<canvasName>/<canvasName>.uxml"
        }
      }
    },
    {
      "type": "ModifyComponent",
      "target": "<canvasName>",
      "parameters": {
        "componentType": "PanelSettings",
        "values": {
          "targetTexture": null,
          "scaleMode": "ConstantPixelSize",
          "referenceDpi": 96
        }
      }
    }
  ],
  "transactionName": "Import Claude Design bundle: <canvasName>"
})
```

### Step 6: Report

Return to user:

```
✓ Design bundle imported
  - Transaction ID: {transactionId}
  - Canvas: <canvasName> (UIDocument)
  - UXML: Assets/UI/<canvasName>/<canvasName>.uxml
  - USS: Assets/UI/<canvasName>/<canvasName>.uss
  - Tokens: Assets/UI/<canvasName>/tokens.uss
  - Components: {componentCount}
  - Interactions: NOT wired (configure C# handlers in your gameplay code)
```

## Example Invocation

User: "Import the LoginDialog design from our Claude Design handoff bundle."

```
Invocation:
ImportDesignBundle(
  bundleUrl="https://design.acme.com/api/bundles/login-dialog-v1.0",
  targetScenePath="Assets/Scenes/Auth.unity",
  canvasName="LoginDialog"
)

Expected output (D11 agent):
{
  "components": [
    {
      "name": "LoginDialog",
      "uxml": "<ui:UXML xmlns:ui=\"UnityEngine.UIElements\" xmlns:uie=\"UnityEditor.UIElements\">\n  <VisualElement class=\"dialog-container\">\n    <Label text=\"Welcome Back\" class=\"title\" />\n    <TextField label=\"Email\" class=\"input-email\" />\n    <TextField label=\"Password\" class=\"input-password\" is-password-field=\"true\" />\n    <Button text=\"Sign In\" class=\"btn-primary\" />\n    <Button text=\"Create Account\" class=\"btn-secondary\" />\n  </VisualElement>\n</ui:UXML>",
      "uss": ".dialog-container {\n  flex-direction: column;\n  padding: var(--spacing-lg);\n  background-color: #ffffff;\n  border-radius: var(--radius-default);\n  min-width: 300px;\n}\n\n.title {\n  font-size: var(--font-heading);\n  color: var(--color-primary);\n  margin-bottom: var(--spacing-md);\n}\n\n.input-email,\n.input-password {\n  margin-bottom: var(--spacing-md);\n  font-size: var(--font-body);\n}\n\n.btn-primary {\n  background-color: var(--color-primary);\n  color: white;\n  padding: var(--spacing-sm) var(--spacing-md);\n  border-radius: var(--radius-default);\n  margin-bottom: var(--spacing-sm);\n}\n\n.btn-primary:hover {\n  opacity: 0.85;\n}\n\n.btn-secondary {\n  background-color: transparent;\n  color: var(--color-primary);\n  padding: var(--spacing-sm) var(--spacing-md);\n}"
    }
  ],
  "tokens.uss": ":root {\n  --color-primary: #007AFF;\n  --color-secondary: #34C759;\n  --color-text: #333333;\n  --color-error: #FF3B30;\n  --color-bg-light: #F2F2F7;\n  --spacing-xs: 4px;\n  --spacing-sm: 8px;\n  --spacing-md: 16px;\n  --spacing-lg: 24px;\n  --spacing-xl: 32px;\n  --radius-small: 4px;\n  --radius-default: 8px;\n  --radius-large: 12px;\n  --font-body: 14px;\n  --font-heading: 24px;\n}",
  "metadata": {
    "componentCount": 1,
    "tokenCount": 15,
    "warnings": []
  }
}

CRAFT result:
✓ Design bundle imported
  - Transaction ID: txn-7f3a-2026-04-18-login-dialog
  - Canvas: LoginDialog (UIDocument)
  - UXML: Assets/UI/LoginDialog/LoginDialog.uxml
  - USS: Assets/UI/LoginDialog/LoginDialog.uss
  - Tokens: Assets/UI/LoginDialog/tokens.uss
  - Components: 1
  - Interactions: NOT wired

Next steps:
1. Open Assets/UI/LoginDialog/LoginDialog.uxml in UI Builder to preview
2. To wire interactions (Sign In button → login handler), attach a script to LoginDialog GameObject:
   - GetComponent<UIDocument>().rootVisualElement.Q<Button>("btn-primary").clicked += OnSignInClicked;
```

## HTML → UXML Mapping Reference

D11 agent uses this mapping during transpilation:

| HTML | UXML | Notes |
|------|------|-------|
| `<div class="...">` | `<VisualElement class="...">` | Generic container |
| `<button>` | `<Button>` | Clickable button |
| `<input type="text">` | `<TextField>` | Single-line text input |
| `<input type="password">` | `<TextField is-password-field="true">` | Masked password field |
| `<textarea>` | `<TextField multiline="true">` | Multi-line text input |
| `<label>` | `<Label>` | Static text label |
| `<h1>...<h6>` | `<Label class="heading">` | Heading (use CSS for size) |
| `<p>` | `<Label class="body">` | Paragraph text |
| `<img src="...">` | `<VisualElement style="background-image: url(...)">` | Image via background |
| `<ul><li>` | `<ListView>` | Scrollable list (dynamic binding via C#) |
| `<select>` | `<DropdownField>` | Dropdown selector |
| `<section>` | `<VisualElement class="section">` | Semantic grouping |
| `<header>`, `<nav>` | `<VisualElement class="header">` | Navigation container |
| `<footer>` | `<VisualElement class="footer">` | Footer container |

## Design Tokens → USS Variables

D11 converts design tokens to USS `:root` variables:

| Token Category | USS Variable | Example Value |
|---|---|---|
| `colors.primary` | `--color-primary` | `#007AFF` |
| `colors.text` | `--color-text` | `#333333` |
| `spacing.md` | `--spacing-md` | `16px` |
| `radii.default` | `--radius-default` | `8px` |
| `typography.body` | `--font-body` | `14px` |

All tokens referenced via `var(--token-name)` in component USS.

## Cache Strategy

**Cache key:** SHA256 hash of bundle JSON

**Cache directory structure:**

```
<project>/.unity-craft/design-cache/
  ├── sha256-abc123def456/
  │   ├── bundle.json                     # Original bundle
  │   ├── components/
  │   │   ├── MainMenu.uxml               # Generated by D11
  │   │   ├── MainMenu.uss
  │   │   ├── LoginDialog.uxml
  │   │   └── LoginDialog.uss
  │   ├── tokens.uss                      # Shared token definitions
  │   └── metadata.json
  └── metadata.json                       # Index of all cached bundles
```

**Cache invalidation:**

- Manual override: User can pass `skipCache=true` parameter (future extension)
- No automatic expiration (unless user deletes `.unity-craft/` directory)
- Metadata updated when new bundle cached

**Metadata example:**

```json
{
  "bundles": {
    "https://design.acme.com/api/bundles/login-v1.0": {
      "hash": "sha256-abc123...",
      "cached_at": "2026-04-18T14:22:35Z",
      "version": "1.0.0",
      "componentCount": 3
    }
  }
}
```

## D11 Dispatch Protocol

When sending bundle to D11 agent, provide:

**Input:**
- Bundle JSON (full structure)
- Task: Convert HTML/CSS → UXML/USS
- Constraints: No C# event handlers; preserve design tokens as variables

**Expected return:**
- JSON with keys: `components`, `tokens.uss`, `metadata`
- Each component: `{name, uxml, uss}`
- `uxml` is valid, complete UXML document (with xmlns declarations)
- `uss` is valid USS syntax (no validation errors)
- `metadata.warnings` lists known issues (e.g., "Hover states not wired")

**Timeout:** 30 seconds (D11 agent transpilation usually < 10s)

**Failure handling:**
- D11 returns parse error: Report to user, suggest bundle check
- D11 returns malformed UXML: Report error, suggest manual fix in UI Builder
- D11 timeout: Offer to use cached version or retry

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| **Invalid bundle URL** | 404, DNS fail, timeout | Check URL spelling; verify authentication token; test `curl` manually |
| **Missing designTokens** | Bundle missing `designTokens` field | Use D11 defaults or user-supplied token file |
| **UXML validation fail** | D11 produced malformed XML | Report XML error line; ask user to fix in UI Builder and re-export |
| **File write fail** | `Assets/UI/<canvasName>/` not writable | Check project permissions; ensure `Assets/` directory exists |
| **PanelSettings missing** | Scene lacks PanelSettings GameObject | CRAFT auto-creates; if fails, manually add PanelSettings to scene |
| **UIDocument not added** | CRAFT_Execute failed | Check CRAFT status; attempt manual creation in Editor; rollback via transactionId |
| **Cache corruption** | `.unity-craft/` partially written | Delete cache directory; re-run import |

## Verification Checklist

After successful import, verify in Editor:

1. **Hierarchy check**: Scene contains `<canvasName>` GameObject with UIDocument component
2. **Asset check**: Files exist at `Assets/UI/<canvasName>/{<canvasName>.uxml, <canvasName>.uss, tokens.uss}`
3. **UXML validation**: Open UXML file in UI Builder → no red squiggles
4. **USS validation**: Open USS file in text editor → syntax highlight works; no parse errors in Editor console
5. **Visual preview**: In UI Builder, select UIDocument root → preview pane shows layout (may be blank until runtime)
6. **PanelSettings**: Scene has exactly one PanelSettings GameObject; set as "Match Game View" or fixed resolution

**Manual test in Play mode:**
- Run scene
- UIDocument renders at canvas position
- Layout matches design (spacing, colors, fonts)
- Interactions respond to mouse (not wired to gameplay yet)

## Limitations

1. **No interaction wiring**: Bundle includes interaction metadata (e.g., "click Sign In → navigate to /game"), but ImportDesignBundle does not generate C# event handlers. User must wire these manually in gameplay code:
   ```csharp
   var signInBtn = GetComponent<UIDocument>().rootVisualElement.Q<Button>("btn-primary");
   signInBtn.clicked += OnSignInClicked;
   ```

2. **No dynamic list binding**: ListViews are created empty; populating list items requires C# code (not design-driven).

3. **No media queries**: Bundle static breakpoints only; runtime viewport changes (resize window) not auto-handled. User can listen to `Panel.onSizeChange` event to adapt layout at runtime.

4. **Design token updates**: If designer updates tokens in Claude Design and re-exports bundle, old cache remains. User must manually delete cache or pass future `skipCache=true` flag.

5. **Complex CSS features**: Some CSS features (backdrop-filter, CSS Grid gaps, advanced pseudo-selectors) may not map to USS. D11 agent flags these in `metadata.warnings`.

6. **No image assets**: Bundle includes `<img>` tags as background references; actual image files must exist in project. USS references relative paths; ensure images in `Assets/` match bundle expectations.

## Related Tools

- **Craft_Execute**: Used for UIDocument creation + PanelSettings configuration
- **Craft_Query**: Pre-check if UIDocument already exists (avoid duplicates)
- **Craft_Rollback**: Undo failed imports via transactionId
- **D11 (unity-ui-developer) agent**: Transpiles HTML/CSS → UXML/USS

## References

- [Claude Design Bundle API](https://design.example.com/docs/bundle-export) — authentication, endpoint
- [Unity UI Toolkit UXML Manual](https://docs.unity3d.com/Manual/UIE-UXML.html) — element reference
- [Unity UI Toolkit USS Reference](https://docs.unity3d.com/Manual/UIE-USS.html) — selectors, properties
- [CRAFT Tool Specification](../SKILL.md) — transaction safety, validation

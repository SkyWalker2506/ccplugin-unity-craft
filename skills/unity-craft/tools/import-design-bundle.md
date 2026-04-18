# ImportDesignBundle Tool Specification

## Purpose

ImportDesignBundle enables Claude to import Claude Design handoff bundles (UI component hierarchies, design tokens, HTML/CSS) directly into Unity UI Toolkit scenes. Released April 2026, Claude Design exports a web-first format (`styles.css` + `index.html`); this tool bridges that to UXML/USS, making UI Toolkit the natural composition target. The tool handles bundle fetch, caching, design-to-code transpilation (via D11 agent dispatch), and scene integration via CRAFT operations.

## Signature

```
ImportDesignBundle(
  bundleUrl,           // string: Claude Design project URL (claude.ai/design/p/xxx)
  targetScenePath,     // string: Unity scene path (e.g., "Assets/Scenes/MainMenu.unity")
  canvasName = "MainMenu"  // string: UIDocument GameObject name + UXML/USS namespace
)
```

### Arguments

| Argument | Type | Default | Example | Notes |
|----------|------|---------|---------|-------|
| `bundleUrl` | string | — | `https://claude.ai/design/p/abc123` | Claude Design project URL; bundle assets fetched from this URL |
| `targetScenePath` | string | — | `Assets/Scenes/MainMenu.unity` | Scene must exist; UIDocument GameObject created if absent |
| `canvasName` | string | `MainMenu` | `LoginDialog`, `CharacterSelect` | Used for GameObject name + UXML/USS filenames; alphanumeric + underscore only |

## Real Bundle Format (Claude Design, April 2026)

Claude Design is **web-first**. There is no native UXML/Unity export. "Handoff to Claude Code" produces a structured bundle containing:

- **`styles.css`** — CSS custom properties (design tokens) and component class rules
- **`index.html`** — React/HTML component tree with class references
- **Interaction notes** — described inline in HTML comments or a companion `interactions.md`
- **Asset references** — Google Fonts `@import` URLs, image `src` paths

### Example `styles.css`

```css
@import url('https://fonts.googleapis.com/css2?family=Cinzel&display=swap');

:root {
  --color-blood: #8b0000;
  --color-bone: #f5f5dc;
  --color-shadow: #1a1a1a;
  --font-display: 'Cinzel', serif;
  --font-body: 'Inter', sans-serif;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --radius-sm: 4px;
  --radius-md: 8px;
}

.menu-container {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
  background-color: var(--color-shadow);
}

.btn-primary {
  background-color: var(--color-blood);
  color: var(--color-bone);
  font-family: var(--font-display);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
}

.btn-primary:hover {
  opacity: 0.85;
}
```

### Example `index.html`

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="menu-container">
    <h1 class="menu-title">Dark Realm</h1>
    <p class="menu-subtitle">A gothic adventure</p>
    <button class="btn-primary" id="start-btn">Start Game</button>
    <button class="btn-secondary" id="settings-btn">Settings</button>
  </div>
</body>
</html>
```

## Pipeline

### Step 1: Fetch Bundle Assets

Fetch `styles.css` and `index.html` from the Claude Design project URL:

```bash
# styles.css
curl "https://claude.ai/design/p/abc123/styles.css" -o styles.css

# index.html
curl "https://claude.ai/design/p/abc123/index.html" -o index.html
```

If the URL is a project share link (not direct file URLs), parse the HTML response to locate asset references. On failure (404, 401, timeout), report error with recovery suggestions (verify URL, check project sharing settings).

### Step 2: Check Cache

Compute SHA256 hash of `styles.css` + `index.html` content concatenated:

```
hash = SHA256(stylesCss + indexHtml)
cachePath = <project>/.unity-craft/design-cache/<hash>/
```

If `cachePath/bundle/` exists and is complete, **skip to Step 4** (use cached UXML/USS).

Cache metadata stored in `<project>/.unity-craft/design-cache/metadata.json`.

### Step 3: Dispatch to D11 (unity-ui-developer)

Send both files to D11 agent with this prompt template:

```
You are the Unity UI Developer (D11).

Task: Convert Claude Design web export to UXML + USS.

Input:
--- styles.css ---
{stylesCss}

--- index.html ---
{indexHtml}

Output format (return JSON):
{
  "components": [
    {
      "name": "MainMenu",
      "uxml": "<ui:UXML xmlns:ui=\"UnityEngine.UIElements\">...</ui:UXML>",
      "uss": ".container { flex-direction: column; ... }"
    }
  ],
  "tokens.uss": ":root { --color-blood: #8b0000; ... }",
  "metadata": {
    "componentCount": 1,
    "tokenCount": 8,
    "fontWarnings": ["Cinzel → assign Unity font asset manually"],
    "warnings": []
  }
}

Rules:
- Parse CSS custom properties from :root in styles.css → USS :root variables
  - Rename --color-* → keep as-is (Claude Design color convention maps directly)
  - Rename --font-* → same name (font values become Unity font asset references, flag in fontWarnings)
- Parse HTML component structure → convert to UXML elements (see mapping table)
- CSS class rules → USS selectors (same class names)
- :hover / :focus → USS :hover/:focus pseudo-classes
- Google Fonts @import → remove; add fontWarnings entry for each font family
- Do NOT generate C# event handlers
- Return valid, Unity-formatted XML/USS
```

D11 returns UXML + USS for each component. **Store results in cache:**

```
cachePath/
  ├── bundle/
  │   ├── styles.css          # Original
  │   ├── index.html          # Original
  │   ├── components/
  │   │   └── MainMenu.uxml
  │   │   └── MainMenu.uss
  │   └── tokens.uss
  └── metadata.json
```

### Step 4: Write to Assets

Copy cached UXML/USS to project:

```
Assets/UI/<canvasName>/
  ├── <canvasName>.uxml
  ├── <canvasName>.uss
  └── tokens.uss
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

```
Design bundle imported
  - Transaction ID: {transactionId}
  - Canvas: <canvasName> (UIDocument)
  - UXML: Assets/UI/<canvasName>/<canvasName>.uxml
  - USS: Assets/UI/<canvasName>/<canvasName>.uss
  - Tokens: Assets/UI/<canvasName>/tokens.uss
  - Components: {componentCount}
  - Font warnings: {fontWarnings} — assign Unity font assets manually
  - Interactions: NOT wired (configure C# handlers in your gameplay code)
```

## HTML → UXML Mapping Reference

D11 agent uses this mapping during transpilation:

| HTML | UXML | Notes |
|------|------|-------|
| `<div class="...">` | `<VisualElement class="...">` | Generic container |
| `<span class="...">` | `<VisualElement class="...">` | Inline container; use Label if text-only |
| `<button>` | `<Button>` | Clickable button |
| `<input type="text">` | `<TextField>` | Single-line text input |
| `<input type="password">` | `<TextField is-password-field="true">` | Masked password field |
| `<input type="checkbox">` | `<Toggle>` | Checkbox toggle |
| `<input type="range">` | `<Slider>` | Range slider |
| `<textarea>` | `<TextField multiline="true">` | Multi-line text input |
| `<label>` | `<Label>` | Static text label |
| `<h1>`...`<h6>` | `<Label class="heading-N">` | Heading (use USS for size) |
| `<p>` | `<Label class="body">` | Paragraph text |
| `<span>` (text-only) | `<Label>` | Inline text |
| `<img src="...">` | `<Image>` or `<VisualElement style="background-image: url(...)">` | Prefer `<Image>` for explicit assets |
| `<ul><li>` | `<ListView>` | Scrollable list (dynamic binding via C#) |
| `<ol><li>` | `<ListView>` | Ordered list; numbering via C# |
| `<select>` | `<DropdownField>` | Dropdown selector |
| `<form>` | `<VisualElement class="form">` | Form wrapper |
| `<section>` | `<VisualElement class="section">` | Semantic grouping |
| `<article>` | `<VisualElement class="article">` | Article block |
| `<header>`, `<nav>` | `<VisualElement class="header">` | Navigation container |
| `<footer>` | `<VisualElement class="footer">` | Footer container |
| `<main>` | `<VisualElement class="main">` | Main content area |

## CSS → USS Property Mapping

### Supported (direct map)

| CSS | USS | Notes |
|-----|-----|-------|
| `display: flex` | (default in USS) | USS is flex-only; no `display` property needed |
| `flex-direction: row/column` | `flex-direction: row/column` | Direct map |
| `flex-wrap: wrap` | `flex-wrap: wrap` | Direct map |
| `flex: 1` | `flex-grow: 1` | USS uses longhand |
| `align-items: center` | `align-items: center` | Direct map |
| `justify-content: center` | `justify-content: center` | Direct map |
| `padding: 16px` | `padding: 16px` | Direct map |
| `margin: 8px` | `margin: 8px` | Direct map |
| `width: 100%` | `width: 100%` | Direct map |
| `min-width / max-width` | `min-width / max-width` | Direct map |
| `background-color: #fff` | `background-color: #fff` | Direct map |
| `color: #333` | `color: #333` | Text color |
| `font-size: 14px` | `font-size: 14px` | px only; no rem/em |
| `font-style: italic` | `font-style: italic` | Direct map |
| `font-weight: bold` | `-unity-font-style: bold` | USS uses `-unity-font-style` |
| `border-radius: 8px` | `border-radius: 8px` | Direct map |
| `border: 1px solid #ccc` | `border-width: 1px; border-color: #ccc` | USS longhand only |
| `opacity: 0.85` | `opacity: 0.85` | Direct map |
| `overflow: hidden` | `overflow: hidden` | Direct map |
| `position: absolute` | `position: absolute` | Supported |
| `top/left/right/bottom` | `top/left/right/bottom` | With `position: absolute` |
| `var(--token)` | `var(--token)` | CSS custom properties work in USS |
| `:hover` | `:hover` | USS pseudo-class |
| `:focus` | `:focus` | USS pseudo-class |
| `:active` | `:active` | USS pseudo-class |
| `:checked` | `:checked` | USS pseudo-class (Toggle) |
| `:disabled` | `:disabled` | USS pseudo-class |

### Not Supported in USS (flag in warnings)

| CSS | USS Alternative | Note |
|-----|----------------|-------|
| `display: grid` | Flex nesting | USS has no CSS Grid |
| `display: inline-flex` | `flex-direction: row` | No inline layout |
| `display: block/inline` | (default) | USS has no block/inline |
| `z-index` | Element order in hierarchy | Last child renders on top |
| `backdrop-filter` | Not supported | No blur effects via USS |
| `box-shadow` | Not supported natively | Use custom meshes or workaround |
| `text-shadow` | Not supported | |
| `@media` queries | `Panel.onSizeChange` C# | No runtime media queries |
| `transform: rotate/scale` | `rotate`, `scale` USS (Unity 2022.1+) | Check Unity version |
| `transition` | Not supported | Use C# animation or Tweens |
| `animation / @keyframes` | Not supported | Use C# or DoTween |
| `calc()` | Not supported | Use fixed px values |
| `rem / em` units | Convert to `px` | USS px only |
| `vh / vw` units | `%` relative to parent | No viewport units |
| `font-family` | `-unity-font` / `-unity-font-definition` | Requires Unity Font Asset |

## Design Tokens: CSS Custom Properties → USS Variables

Claude Design uses `--color-*`, `--font-*`, `--spacing-*` pattern. D11 maps these directly:

| Claude Design CSS var | USS var | Notes |
|-----------------------|---------|-------|
| `--color-blood: #8b0000` | `--color-blood: #8b0000` | Direct map; no rename needed |
| `--color-bone: #f5f5dc` | `--color-bone: #f5f5dc` | Direct map |
| `--font-display: 'Cinzel'` | `--font-display: 'Cinzel'` | Value becomes font asset ref; flag warning |
| `--font-body: 'Inter'` | `--font-body: 'Inter'` | Flag warning |
| `--spacing-md: 16px` | `--spacing-md: 16px` | Direct map |
| `--radius-md: 8px` | `--radius-md: 8px` | Direct map |

All tokens go into `tokens.uss` `:root` block. Components reference via `var(--token-name)`.

**Font handling:** Google Fonts `@import` URLs in `styles.css` are removed. Each referenced font family is flagged in `metadata.fontWarnings`. The developer must:
1. Download the font file (`.ttf` / `.otf`)
2. Create a Unity Font Asset (TextMeshPro or UI Toolkit font asset)
3. Replace `var(--font-display)` references with the asset path in USS

## Cache Strategy

**Cache key:** SHA256 hash of `styles.css` + `index.html` content

```
<project>/.unity-craft/design-cache/
  ├── sha256-abc123def456/
  │   ├── bundle/
  │   │   ├── styles.css
  │   │   ├── index.html
  │   │   ├── components/
  │   │   │   ├── MainMenu.uxml
  │   │   │   └── MainMenu.uss
  │   │   └── tokens.uss
  │   └── metadata.json
  └── metadata.json
```

Cache invalidation: manual (`skipCache=true` future flag) or delete `.unity-craft/` directory.

## D11 Dispatch Protocol

**Input:**
- `styles.css` full content
- `index.html` full content
- Task: Parse CSS custom properties + HTML → UXML/USS
- Constraints: No C# event handlers; preserve design tokens as USS variables; flag unsupported CSS

**Expected return:**
- JSON with keys: `components`, `tokens.uss`, `metadata`
- Each component: `{name, uxml, uss}`
- `uxml` is valid, complete UXML document (with xmlns declarations)
- `uss` is valid USS syntax
- `metadata.fontWarnings` lists font families requiring manual asset assignment
- `metadata.warnings` lists unsupported CSS features

**Timeout:** 30 seconds

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| **Bundle URL 404** | Claude Design project not shared or URL wrong | Verify project is shared; copy URL from Share dialog |
| **styles.css missing** | Project has no styles | Proceed with defaults; warn user |
| **index.html missing** | Bundle incomplete | Abort; ask user to re-export from Claude Design |
| **UXML validation fail** | D11 produced malformed XML | Report XML error line; open in UI Builder for manual fix |
| **Font not found** | Google Font not imported | See font handling section; assign font asset manually |
| **File write fail** | `Assets/UI/<canvasName>/` not writable | Check project permissions |
| **Cache corruption** | Partial write | Delete `.unity-craft/design-cache/`; re-run import |

## Limitations

1. **No interaction wiring**: Interaction notes are preserved in `metadata` but ImportDesignBundle does not generate C# event handlers. Wire manually:
   ```csharp
   var startBtn = GetComponent<UIDocument>().rootVisualElement.Q<Button>("start-btn");
   startBtn.clicked += OnStartClicked;
   ```

2. **Font assets required**: All Google Fonts must be manually downloaded and converted to Unity Font Assets.

3. **No CSS Grid**: Claude Design may use `display: grid`; D11 converts to flex nesting with warnings.

4. **No dynamic list binding**: ListViews created empty; C# populates items at runtime.

5. **No media queries**: Use `Panel.onSizeChange` C# event for responsive layouts.

6. **No image assets**: Bundle references image paths; actual files must exist in `Assets/`.

7. **Unsupported CSS**: `box-shadow`, `backdrop-filter`, `transition`, `@keyframes` flagged in `metadata.warnings`.

## Related Tools

- **Craft_Execute**: UIDocument creation + PanelSettings configuration
- **Craft_Query**: Pre-check if UIDocument already exists (avoid duplicates)
- **Craft_Rollback**: Undo failed imports via transactionId
- **D11 (unity-ui-developer) agent**: Transpiles CSS/HTML → UXML/USS

## References

- [Unity UI Toolkit UXML Manual](https://docs.unity3d.com/Manual/UIE-UXML.html) — element reference
- [Unity UI Toolkit USS Reference](https://docs.unity3d.com/Manual/UIE-USS.html) — selectors, properties
- [CRAFT Tool Specification](../SKILL.md) — transaction safety, validation

# ccplugin-unity-craft

Claude Code plugin for [CRAFT](https://github.com/SkyWalker2506/craft-unity) — safe Unity scene manipulation via MCP tools.

---

## ⚠️ Requirements

This plugin requires the **CRAFT Unity SDK** to be installed in your Unity project.  
Without it, none of the MCP tools (`Craft_Execute`, `Craft_Rollback`, etc.) will exist.

| Requirement | Where | Install |
|-------------|-------|---------|
| **[craft-unity](https://github.com/SkyWalker2506/craft-unity)** | Unity project | UPM (see below) |
| `com.unity.ai.assistant` ≥ 2.0.0 | Unity project | Unity Package Manager |
| Unity 6 (6000.0+) | Unity Editor | — |
| Claude Code | Terminal | `npm i -g @anthropic-ai/claude-code` |

### Install craft-unity SDK in Unity

Add to your Unity project's `Packages/manifest.json`:

```json
{
  "dependencies": {
    "com.skywalker.craft": "https://github.com/SkyWalker2506/craft-unity.git",
    "com.unity.ai.assistant": "2.0.0"
  }
}
```

Then make sure the Unity MCP bridge is active:  
`Edit > Project Settings > AI > MCP Bridge: Enable`

---

## What this plugin does

Teaches Claude Code how to use CRAFT's MCP tools for safe, transaction-based Unity scene manipulation:

| Tool | Description |
|------|-------------|
| `Craft_Execute` | Run operations as a single undoable transaction |
| `Craft_Validate` | Pre-check operations without executing |
| `Craft_Rollback` | Revert any transaction by ID or undo N steps |
| `Craft_Query` | Find scene objects by name, component, tag, parent |
| `Craft_Status` | Engine status, recent transactions, last trace |

---

## Install this plugin

```bash
git clone https://github.com/SkyWalker2506/ccplugin-unity-craft.git
cd ccplugin-unity-craft && ./install.sh
```

Or via claude-marketplace:

```bash
ccplugin install unity-craft
```

---

## License

MIT

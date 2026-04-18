# Input System Tool Family

## Purpose

Automate player input setup using Unity's New Input System (`com.unity.inputsystem`). This tool family manages action map creation, binding configuration, rebinding UI scaffolding with UI Toolkit, and preset action map application.

The Input System tool enables:
- **Action map generation** — structured action definitions with multiple control schemes (Keyboard&Mouse, Gamepad)
- **Binding setup** — attach keyboard, mouse, gamepad, and composite bindings to actions
- **C# class generation** — automatic strongly-typed wrapper classes via AssetDatabase
- **Rebinding UI** — UI Toolkit UXML + USS + backing script for in-game control remapping
- **Preset application** — apply one of four curated action maps (FPS, Third-Person, UI Standard, Vehicle)

All tools dispatch through the **B36 unity-input-system** agent, which handles action map validation, JSON schema enforcement, and bind-time checking against installed control schemes.

## Tool Signatures

### Input_CreateActionMap

```
Input_CreateActionMap(
  name: string,
  actions: [
    {
      name: string,
      type: "Button" | "Value" | "PassThrough",
      expectedControlType?: string,
      bindings: []
    }
  ]
) → {
  assetPath: string,
  actionCount: number,
  transactionId: string,
  actionNames: string[]
}
```

Create a new `.inputactions` asset with the specified action map name and action list. Each action is a record with:
- **name** — unique identifier within the map (e.g., "Move", "Jump", "Interact")
- **type** — "Button" (discrete press/release), "Value" (analog axis -1 to 1 or 0 to 1), or "PassThrough" (raw device input)
- **expectedControlType** — optional hint for binding validation (e.g., "Button", "Axis", "Vector2"). Defaults based on type.
- **bindings** — initially empty; populate via `Input_AddBinding` after creation

The action map is created at `Assets/Input/<name>.inputactions` and is immediately usable in Unity Editor. Returns the asset path, transaction ID for rollback, and action name list.

### Input_AddBinding

```
Input_AddBinding(
  actionPath: string,
  bindingPath: string,
  interactions?: string[],
  processors?: string[]
) → {
  actionPath: string,
  bindingPath: string,
  controlScheme: string,
  transactionId: string
}
```

Attach a single binding (keyboard key, mouse button, gamepad control) to an existing action. Binding paths follow Unity Input System format:
- **Keyboard bindings:** `<Keyboard>/w`, `<Keyboard>/space`, `<Keyboard>/leftCtrl`
- **Mouse bindings:** `<Mouse>/leftButton`, `<Mouse>/rightButton`, `<Mouse>/delta`, `<Mouse>/scroll`
- **Gamepad bindings:** `<Gamepad>/leftStick`, `<Gamepad>/rightStick`, `<Gamepad>/buttonSouth`, `<Gamepad>/buttonEast`
- **Composite bindings:** `2DVector(up=<Keyboard>/w,down=<Keyboard>/s,left=<Keyboard>/a,right=<Keyboard>/d)` for structured axes

**Interactions** (optional) — e.g., `["Press"]`, `["Hold(duration=0.5)"]`, `["Tap"]`. Modify action response behavior.

**Processors** (optional) — e.g., `["Normalize"]`, `["Invert"]`, `["Clamp(max=1)"]`. Modify input values before action fires.

Returns the binding path, detected control scheme, and transaction ID. Automatically assigns to the appropriate control scheme based on device type (Keyboard&Mouse vs. Gamepad).

### Input_GenerateCSharpClass

```
Input_GenerateCSharpClass(
  assetPath: string,
  className?: string
) → {
  classPath: string,
  className: string,
  methods: string[],
  transactionId: string
}
```

Invoke Unity's InputActionCodeGenerator via `AssetDatabase.LoadAssetAtPath` to generate a strongly-typed C# wrapper class from the `.inputactions` asset. The generated class appears under `Assets/Input/Generated/<ClassName>.cs` and exposes:
- **Properties** — one per action (e.g., `public InputAction Move { get; }`)
- **Control property getter** — e.g., `Move.controls`
- **Value and callback accessors** — for both Button and Value action types

The generated class is ready to instantiate and bind to input handlers. Returns the class file path, class name, public method names, and transaction ID.

### Input_ApplyPreset

```
Input_ApplyPreset(
  name: "player-fps" | "player-thirdperson" | "ui-standard" | "vehicle"
) → {
  assetPath: string,
  presetName: string,
  actionCount: number,
  controlSchemes: string[],
  transactionId: string
}
```

Apply one of four curated action map presets. Presets include all actions, bindings, and control schemes pre-configured for the named input scheme:
- **player-fps** — Move (WASD + stick), Look (mouse delta + right stick), Jump, Attack, Reload, Aim, Crouch, Interact, Menu
- **player-thirdperson** — Move, Camera (stick), Jump, Attack, Dodge, Target, Interact, Menu
- **ui-standard** — Navigate (arrow keys + stick), Submit, Cancel, Point (mouse), Click, RightClick, MiddleClick, ScrollWheel
- **vehicle** — Accelerate, Brake, Steer, Handbrake, LookBack, Horn, Camera

Each preset is generated from `presets/input/<preset>.json` and includes both Keyboard&Mouse and Gamepad control schemes. Returns the asset path, action count, control scheme list, and transaction ID.

### Input_CreateRebindingUI

```
Input_CreateRebindingUI(
  actions: string[],
  targetCanvasName: string,
  outputDir?: string
) → {
  uxmlPath: string,
  ussPath: string,
  csPath: string,
  transactionId: string
}
```

Generate a UI Toolkit rebinding interface (UXML + USS + C# backing) for the specified action list. The UI includes:
- **Action ListView** — displays all action names with current binding label per row
- **Rebind button** — per-action button to enter rebind mode
- **Modal overlay** — "Press any key…" prompt that captures the next input and assigns it as a binding
- **Save/Load buttons** — persist rebindings via `InputActionRebindingExtensions.SaveBindingOverridesAsJson` and restore from JSON
- **Control scheme selector** — dropdown to switch between Keyboard&Mouse and Gamepad schemes (optional, shown if multiple schemes exist)

Generated files:
- `Assets/Input/UI/RebindMenu.uxml` — UI element layout
- `Assets/Input/UI/RebindMenu.uss` — styling (light/dark theme-aware)
- `Assets/Input/UI/RebindMenuController.cs` — event bindings and rebind loop

The backing script (`RebindMenuController`) is fully functional: it hooks into `InputAction.started` callbacks, manages modal state, and invokes the save extension on user confirmation. Returns file paths and transaction ID. **UI Toolkit only** — does not generate legacy OnGUI menus.

### Input_CreateDualScheme

Setup two independent keyboard input schemes on the same machine for local multiplayer.

```
Input_CreateDualScheme(
  player1Keys: { move: "wasd"|"arrows", jump: string, attack: string, skill: string },
  player2Keys: { move: "wasd"|"arrows", jump: string, attack: string, skill: string },
  playerCount?: 2 | 3 | 4,
  inputMode?: "simultaneous" | "split-screen",
  conflictResolution?: "allow" | "block-shared"
) → {
  p1AssetPath: string,
  p2AssetPath: string,
  handlerPath: string,
  conflicts: string[],
  transactionId: string
}
```

Setup two independent keyboard input schemes on the same machine for local multiplayer. Parameters:
- **player1Keys** — P1 binding map: `move` preset (`"wasd"` or `"arrows"`), plus individual key strings for jump/attack/skill
- **player2Keys** — P2 binding map, same structure
- **playerCount** — 2 / 3 / 4 (default 2; 3–4 players require additional key maps passed as extended parameters)
- **inputMode** — `"simultaneous"` (both PlayerInput components read same frame, default) or `"split-screen"` (inputs routed by camera region)
- **conflictResolution** — `"allow"` (shared keys permitted) or `"block-shared"` (validate no key overlap between players)

**Pipeline:**

1. **B36** (unity-input-system, gpt-5.4) generates:
   - `Assets/Input/PlayerInput_P1.inputactions` — P1 bindings only
   - `Assets/Input/PlayerInput_P2.inputactions` — P2 bindings only
   - `Assets/Input/DualInputHandler.cs` — instantiates 2 separate `InputActionAsset` instances at runtime, routes callbacks to the correct `PlayerInput` component per player GO
2. **Craft_Execute** — attaches `PlayerInput` component to each player GameObject, assigns respective `.inputactions` asset
3. **Conflict check** — if `conflictResolution == "block-shared"`, B36 validates no key path overlap between P1 and P2 binding sets before generating assets; returns `conflicts[]` list if violations found

**Key insight:** Unity InputSystem requires 2 separate `InputActionAsset` instances (not a shared asset reference) for same-keyboard local multiplayer. A shared asset causes P2 bindings to override P1 at runtime. `DualInputHandler` manages independent enable/disable lifecycle for each asset.

**Example invocation:**

```
Input_CreateDualScheme(
  player1Keys: { move: "wasd", jump: "w", attack: "f", skill: "g" },
  player2Keys: { move: "arrows", jump: "up", attack: "k", skill: "l" },
  conflictResolution: "block-shared"
)
```

---

## Pipeline & B36 Dispatch Protocol

Input System tool invocations dispatch to **B36 unity-input-system** agent with the following contract:

**Request Format:**
```json
{
  "tool": "Input_CreateActionMap" | "Input_AddBinding" | "Input_GenerateCSharpClass" | "Input_ApplyPreset" | "Input_CreateRebindingUI",
  "parameters": { "..." },
  "validation": {
    "ensurePackageInstalled": true,
    "ensureProjectSettingNewInputSystem": true
  }
}
```

**Response Format:**
```json
{
  "success": true,
  "result": {
    "assetPath": "Assets/Input/...",
    "transactionId": "...",
    "metadata": { "..." }
  },
  "warnings": [],
  "errors": []
}
```

B36 handles:
1. **Pre-flight checks** — verify `com.unity.inputsystem` is installed in project (`Packages/manifest.json`)
2. **Project Settings validation** — ensure Edit > Project Settings > Input System > Backend is set to "New Input System" (not "Input Manager")
3. **Asset serialization** — write `.inputactions` JSON following Unity's InputActionMap schema
4. **Binding resolution** — validate binding paths against available devices (keyboard, mouse, gamepad) and control schemes
5. **Code generation** — invoke `AssetDatabase` and `InputActionCodeGenerator` from within the Unity Editor context
6. **Rebinding UI scaffold** — generate UXML, USS, and C# with proper event wiring for runtime rebinding

## Preset System

Four preset action map definitions live in `presets/input/`:

### 1. player-fps.json (~120 lines)

Standard FPS/shooter input scheme. Actions: Move (2D axis, WASD + left stick), Look (2D delta, mouse + right stick), Jump (button), Attack (button), Reload (button), Aim (button, toggled), Crouch (button), Interact (button), Menu (button, Escape). Control schemes: Keyboard&Mouse (mouse+keyboard), Gamepad (dual-stick + buttons).

### 2. player-thirdperson.json (~100 lines)

Third-person action RPG scheme. Actions: Move, Camera (2D axis), Jump, Attack (button, light), Attack Heavy (button, held), Dodge, Target (toggle), Interact, Menu. Uses WASD + mouse look or stick dual-axis. Control schemes: Keyboard&Mouse, Gamepad.

### 3. ui-standard.json (~80 lines)

Universal UI navigation. Actions: Navigate (2D axis, arrows + stick), Submit, Cancel, Point (mouse position), Click (left button), RightClick, MiddleClick, ScrollWheel (axis). No gamepad/stick alternative for Point/Click — uses mouse only. Scrollbar interaction compatible.

### 4. vehicle.json (~110 lines)

Driving / piloting scheme. Actions: Accelerate (axis 0–1, W + trigger), Brake (axis 0–1, S + opposite trigger), Steer (2D axis, A/D + left stick), Handbrake (button, Space), LookBack (button, toggle), Horn (button), Camera (axis for zoom or view switch). Control schemes: Keyboard&Mouse, Gamepad (with trigger sensitivity curves).

Each JSON file matches Unity's `.inputactions` schema: one action map entry with multiple action objects, each with binding arrays specifying device paths, interactions, and control scheme membership.

## UI Toolkit Rebinding Pattern

The `Input_CreateRebindingUI` tool generates three files that work together:

### UXML Layout (RebindMenu.uxml)

```xml
<ui:UXML xmlns:ui="UnityEngine.UIElements" xmlns:uie="UnityEditor.UIElements">
  <Style src="RebindMenu.uss" />
  
  <ui:VisualElement class="rebind-menu">
    <ui:Label text="Control Rebinding" class="title" />
    
    <ui:DropdownField label="Control Scheme" name="SchemeSelector" />
    
    <ui:ListView name="ActionsList" 
                 virtualization-method="DynamicHeight"
                 class="actions-list" />
    
    <!-- Rebind Modal Overlay -->
    <ui:VisualElement name="RebindOverlay" class="rebind-overlay hidden">
      <ui:Label text="Press any key…" class="rebind-prompt" />
      <ui:Button text="Cancel" class="rebind-cancel" />
    </ui:VisualElement>
    
    <ui:VisualElement class="button-row">
      <ui:Button text="Save" name="SaveButton" />
      <ui:Button text="Reset to Defaults" name="ResetButton" />
      <ui:Button text="Close" name="CloseButton" />
    </ui:VisualElement>
  </ui:VisualElement>
</ui:UXML>
```

### USS Styling (RebindMenu.uss)

```css
.rebind-menu {
  width: 400px;
  padding: 16px;
  background-color: #2a2a2a;
  border-radius: 8px;
}

.title {
  font-size: 24px;
  color: #ffffff;
  margin-bottom: 16px;
}

.actions-list {
  flex-grow: 1;
  margin: 12px 0;
  border: 1px solid #444;
  padding: 8px;
}

.action-row {
  flex-direction: row;
  align-items: center;
  padding: 8px;
  margin: 4px 0;
  background-color: #333;
  border-radius: 4px;
}

.action-name {
  flex-grow: 1;
  min-width: 120px;
  color: #ffffff;
}

.binding-label {
  min-width: 100px;
  color: #aaaaaa;
  font-size: 12px;
}

.rebind-button {
  width: 80px;
  background-color: #0066cc;
  color: #ffffff;
  border-radius: 4px;
  padding: 4px 8px;
}

.rebind-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  justify-content: center;
  align-items: center;
  display: flex;
}

.rebind-overlay.hidden {
  display: none;
}

.rebind-prompt {
  font-size: 18px;
  color: #ffffff;
  margin-bottom: 16px;
}

.button-row {
  flex-direction: row;
  gap: 8px;
  margin-top: 16px;
}

.button-row > ui:Button {
  flex-grow: 1;
  padding: 8px;
  background-color: #0066cc;
  color: #ffffff;
  border-radius: 4px;
}
```

### C# Backing Script (RebindMenuController.cs)

```csharp
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

public class RebindMenuController : MonoBehaviour
{
    private InputActionAsset m_InputAsset;
    private ListView m_ActionsList;
    private VisualElement m_RebindOverlay;
    private InputAction m_RebindingAction;

    public void Setup(InputActionAsset inputAsset, UIDocument uiDocument)
    {
        m_InputAsset = inputAsset;
        var root = uiDocument.rootVisualElement;
        m_ActionsList = root.Q<ListView>("ActionsList");
        m_RebindOverlay = root.Q<VisualElement>("RebindOverlay");

        // Populate action list
        m_ActionsList.itemsSource = m_InputAsset.actionMaps[0].actions;
        m_ActionsList.makeItem = () =>
        {
            var row = new VisualElement { name = "action-row" };
            row.style.flexDirection = FlexDirection.Row;
            row.style.alignItems = Align.Center;
            row.style.paddingLeft = 8;
            row.style.paddingRight = 8;
            row.style.paddingTop = 4;
            row.style.paddingBottom = 4;

            var label = new Label { name = "action-name" };
            var bindingLabel = new Label { name = "binding-label" };
            var rebindBtn = new Button { text = "Rebind" };

            row.Add(label);
            row.Add(bindingLabel);
            row.Add(rebindBtn);

            return row;
        };

        m_ActionsList.bindItem = (element, index) =>
        {
            var action = (InputAction)m_ActionsList.itemsSource[index];
            element.Q<Label>("action-name").text = action.name;
            element.Q<Label>("binding-label").text = 
                action.bindings.Count > 0 ? action.bindings[0].path : "[not bound]";
            element.Q<Button>().clicked += () => StartRebind(action);
        };

        root.Q<Button>("SaveButton").clicked += SaveBindings;
        root.Q<Button>("ResetButton").clicked += ResetBindings;
        root.Q<Button>("CloseButton").clicked += () => gameObject.SetActive(false);
    }

    private void StartRebind(InputAction action)
    {
        m_RebindingAction = action;
        m_RebindOverlay.RemoveFromClassList("hidden");

        var rebind = m_RebindingAction.GetBindingIndexForControl(null);
        var operation = m_RebindingAction.PerformInteractiveRebinding(rebind)
            .OnComplete(op => CompleteRebind(op))
            .OnCancel(op => CancelRebind(op));
    }

    private void CompleteRebind(InputActionRebindingExtensions.RebindingOperation op)
    {
        m_RebindOverlay.AddToClassList("hidden");
        m_ActionsList.RefreshItems();
        op.Dispose();
    }

    private void CancelRebind(InputActionRebindingExtensions.RebindingOperation op)
    {
        m_RebindOverlay.AddToClassList("hidden");
        op.Dispose();
    }

    private void SaveBindings()
    {
        var overrides = m_InputAsset.SaveBindingOverridesAsJson();
        PlayerPrefs.SetString("input-overrides", overrides);
        PlayerPrefs.Save();
    }

    private void ResetBindings()
    {
        m_InputAsset.RemoveAllBindingOverrides();
        m_ActionsList.RefreshItems();
    }
}
```

The backing script uses `InputAction.PerformInteractiveRebinding()` to capture the next input device press, validates it against the action's expected control type, and updates the action map in memory. The modal overlay prevents accidental inputs during rebinding. On save, `SaveBindingOverridesAsJson` serializes all overrides to a JSON string stored in `PlayerPrefs`, allowing persistence across play sessions and game restarts.

## Limitations

1. **Package dependency** — `com.unity.inputsystem` must be installed in the Unity project. If missing, the tool fails at pre-flight validation. To install, add to `Packages/manifest.json`:
   ```json
   "com.unity.inputsystem": "1.7.0"
   ```
   or use `Assets_InstallUPM("com.unity.inputsystem", "1.7.0")` from the Asset Store tool family.

2. **Project Settings** — Edit > Project Settings > Input System > Backend must be set to **"New Input System"** (not legacy Input Manager). This is a one-time project setting. B36 can validate but cannot programmatically set it; manual toggle or `Craft_SetProjectSetting` (Unity 6+) required.

3. **Control scheme coverage** — Preset action maps include Keyboard&Mouse and Gamepad schemes only. Mobile touch input requires custom binding paths (`<Touchscreen>/touch0`) and additional action setup; not included in presets.

4. **UI Toolkit only** — `Input_CreateRebindingUI` generates UI Toolkit UXML/USS, not legacy OnGUI. For legacy UI or IMGUI workflows, manually build rebinding UI using `InputActionRebindingExtensions` C# API.

5. **Runtime rebinding** — Rebindings persist in `PlayerPrefs` by default. For cloud save or per-device profile switching, customize `RebindMenuController.cs` to use a different persistence layer (e.g., JSON file, Playfab, Netcode).

## Verification

After executing Input System operations, verify:

1. **Action Map Asset**
   - `.inputactions` file exists at `Assets/Input/<name>.inputactions`
   - Opened in Editor shows all actions and bindings in the InputActionAsset inspector
   - Each action has at least one binding for at least one control scheme

2. **Binding Resolution**
   - All binding paths resolve to actual devices (no "unknown device" warnings)
   - Keyboard/Mouse scheme includes keyboard keys and mouse bindings
   - Gamepad scheme includes only gamepad/joystick paths

3. **C# Generated Class**
   - `.cs` file exists at `Assets/Input/Generated/<ClassName>.cs`
   - File compiles without errors (`Assets > Reimport All` to force compile)
   - Class exposes properties for each action (e.g., `public InputAction Move { get; }`)

4. **Rebinding UI**
   - UXML, USS, and C# files exist in `Assets/Input/UI/`
   - UIDocument component references the `.uxml` file
   - Play mode: rebind overlay appears and captures input
   - Save button serializes overrides to `PlayerPrefs`
   - Load/reset buttons restore default or saved bindings

5. **Play Mode Test**
   - Spawn the action map via `inputAsset.Enable()`
   - Input from bound controls triggers action callbacks (`action.started` fires)
   - Multiple schemes: verify that swapping control scheme changes which device is active
   - Rebinding: verify that reassigning a binding updates the action immediately

## Common Workflows

### Quick FPS Setup

```
Input_ApplyPreset("player-fps")
Input_GenerateCSharpClass("Assets/Input/player-fps.inputactions", "FPSInput")
Input_CreateRebindingUI(["Move", "Look", "Jump", "Attack"], "MainCanvas")
```

**Result:** FPS action map with all bindings pre-configured, typed C# wrapper, and rebinding menu ready to wire to a Canvas.

### Custom Multi-Device Action Map

```
Input_CreateActionMap("MyGame", [
  { name: "Move", type: "Value", expectedControlType: "Vector2", bindings: [] },
  { name: "Jump", type: "Button", bindings: [] },
  { name: "Crouch", type: "Button", bindings: [] }
])
Input_AddBinding("MyGame/Move", "2DVector(up=<Keyboard>/w,down=<Keyboard>/s,left=<Keyboard>/a,right=<Keyboard>/d)")
Input_AddBinding("MyGame/Move", "<Gamepad>/leftStick")
Input_AddBinding("MyGame/Jump", "<Keyboard>/space")
Input_AddBinding("MyGame/Jump", "<Gamepad>/buttonSouth")
Input_GenerateCSharpClass("Assets/Input/MyGame.inputactions")
```

**Result:** Action map with keyboard WASD + gamepad stick move, keyboard space + gamepad A button jump. Strongly-typed C# class `MyGame` ready to use in MonoBehaviour.

### UI Navigation with Rebinding

```
Input_ApplyPreset("ui-standard")
Input_GenerateCSharpClass("Assets/Input/ui-standard.inputactions", "UIInput")
Input_CreateRebindingUI(["Navigate", "Submit", "Cancel"], "SettingsCanvas")
```

**Result:** Standard UI action map (arrows, stick, buttons). Rebinding UI scaffolded for settings menu.

### Vehicle Presets with Fine-Tuning

```
Input_ApplyPreset("vehicle")
Input_AddBinding("vehicle/Accelerate", "<Gamepad>/rightTrigger", [], ["Clamp(min=0,max=1)"])
Input_AddBinding("vehicle/Brake", "<Gamepad>/leftTrigger", [], ["Clamp(min=0,max=1)"])
Input_GenerateCSharpClass("Assets/Input/vehicle.inputactions", "VehicleInput")
```

**Result:** Vehicle action map with trigger clamping to ensure 0–1 normalized brake/accelerate axes.

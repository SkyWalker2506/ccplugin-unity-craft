# Match System Tool Family

## Purpose

Establish a complete match/game-loop architecture in Unity scenes through win condition configuration, score tracking, victory UI generation, and live scoreboard HUD assembly. All operations execute as transaction-safe CRAFT operations, with game logic dispatched to B19 (unity-developer) and all UI components dispatched to D11 (unity-ui-developer).

The tool manages:
- **MatchManager singleton** — win condition loop, match state enum (Playing/Victory/Draw), score tracking, restart logic
- **Victory/game-over screen** — UIDocument panel auto-shown/hidden by MatchManager on match end
- **Live scoreboard HUD** — real-time HP bars, score counters, and countdown timer mounted as UIDocument
- **Event wiring** — MatchManager auto-listens to HealthSystem.OnDeath events from all player GameObjects

## Tool Signatures

### Match_Configure

```
Match_Configure(
  winCondition: "last-standing" | "score-limit" | "time-limit" | "objective",
  playerCount: number,             // 1–4
  restartKey: string,              // e.g. "r", "space"
  resetMode: "scene-reload" | "soft-reset",
  onMatchEnd: string,              // C# event name, e.g. "OnMatchEnd"
  scoreLimit?: number,             // required when winCondition = "score-limit"
  timeLimitSeconds?: number        // required when winCondition = "time-limit"
) → {
  managerPath: string,
  scriptPath: string,
  winCondition: string,
  playersLinked: number,
  transactionId: string
}
```

Generates MatchManager.cs via B19 dispatch, then mounts it as a singleton GameObject in the active scene. The script implements a win check loop, a `MatchState` enum (Playing/Victory/Draw), a score dictionary keyed by player index, and a restart handler bound to `restartKey`. Auto-wires `HealthSystem.OnDeath` listeners for all player GameObjects found in the scene at startup.

**Win condition behavior:**
- **last-standing** — triggers victory for the sole surviving player when all others have `OnDeath` fired
- **score-limit** — triggers victory for the first player reaching `scoreLimit`
- **time-limit** — triggers Draw or current leader victory when `timeLimitSeconds` elapses
- **objective** — fires `onMatchEnd` event; caller is responsible for raising it from custom objective logic

**Reset modes:**
- **scene-reload** — calls `SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex)`
- **soft-reset** — calls `MatchManager.SoftReset()`, which respawns players and resets state without reloading

### Match_SetupVictoryUI

```
Match_SetupVictoryUI(
  winnerLabel: string,             // e.g. "OYUNCU {n} KAZANDI"
  restartPrompt: string,           // e.g. "Yeniden başlatmak için R'ye bas"
  showScore: boolean,
  style: "gothic" | "minimal" | "arcade"
) → {
  uxmlPath: string,
  ussPath: string,
  gameObjectPath: string,
  transactionId: string
}
```

Dispatches to D11 (unity-ui-developer, gpt-5.4) to generate `VictoryScreen.uxml` and `VictoryScreen.uss` for the selected style, then mounts a `UIDoc_Victory` GameObject with a UIDocument component pointing to the generated asset. MatchManager.cs auto-shows this panel on match end and hides it on restart.

`{n}` in `winnerLabel` is replaced at runtime with the winning player index (1-based).

**Style variants:**
- **gothic** — dark overlay, serif font, desaturated palette, heavy drop shadow
- **minimal** — centered white text on semi-transparent black panel, no decorations
- **arcade** — bright color flash border, bold pixel font, animated blink on prompt text

### Match_SetupScoreboard

```
Match_SetupScoreboard(
  players: Array<{ name: string, color: string }>,
  showHP: boolean,
  showScore: boolean,
  showTimer: boolean,
  position: "top" | "bottom" | "sides"
) → {
  uxmlPath: string,
  ussPath: string,
  gameObjectPath: string,
  transactionId: string
}
```

Dispatches to D11 to generate `Scoreboard.uxml` + `Scoreboard.uss`, then mounts a `UIDoc_Scoreboard` GameObject via `Craft_Execute`. The scoreboard binds live to MatchManager's public score/HP/timer properties each frame via `INotifyValueChanged` or manual `Update` binding depending on the Unity version detected.

**Position variants:**
- **top** — full-width strip anchored to top of screen, players laid out horizontally
- **bottom** — full-width strip anchored to bottom of screen
- **sides** — player panels docked left/right; supports 2-player split only (falls back to `top` for 3–4 players)

**Column visibility** is controlled by `showHP`, `showScore`, `showTimer` flags. Columns are omitted from the UXML entirely when disabled, not merely hidden, to avoid layout ghost space.

## Pipeline & Dispatch Protocol

When Match tools are invoked, requests are dispatched to the appropriate agent per component type:

**Match_Configure — B19 (unity-developer, gpt-5.4):**
```json
{
  "tool": "Match_Configure",
  "parameters": {
    "winCondition": "...",
    "playerCount": 2,
    "restartKey": "r",
    "resetMode": "scene-reload",
    "onMatchEnd": "OnMatchEnd",
    "scoreLimit": null,
    "timeLimitSeconds": null
  }
}
```

B19 generates `MatchManager.cs` and returns the script asset path. The orchestrator then calls `Craft_Execute` to create the singleton GameObject and attach the script.

**Match_SetupVictoryUI / Match_SetupScoreboard — D11 (unity-ui-developer, gpt-5.4):**
```json
{
  "tool": "Match_SetupVictoryUI" | "Match_SetupScoreboard",
  "parameters": { "..." }
}
```

D11 returns `uxml` + `uss` asset paths. The orchestrator calls `Craft_Execute: CreateGameObject` + component attachment.

**Unified Response Format:**
```json
{
  "success": true,
  "result": {
    "gameObjectPath": "...",
    "scriptPath": "..." | "uxmlPath": "...",
    "transactionId": "...",
    "metadata": {}
  },
  "warnings": [],
  "errors": []
}
```

**CRAFT operations used:**
- `Craft_Execute: CreateGameObject` — creates MatchManager, UIDoc_Victory, UIDoc_Scoreboard
- `Craft_Execute: AttachScript` — attaches MatchManager.cs to the manager GameObject
- `Craft_Execute: AttachComponent` — adds UIDocument component and assigns UXML asset
- `Craft_Execute: QueryGameObjects` — finds all player GameObjects for HealthSystem wiring

## Implementation Notes

### Match_Configure

B19 generates `MatchManager.cs` with the following structure:

```csharp
public class MatchManager : MonoBehaviour
{
    public static MatchManager Instance { get; private set; }

    public enum MatchState { Playing, Victory, Draw }
    public MatchState CurrentState { get; private set; } = MatchState.Playing;

    public event Action<int> OnMatchEnd;   // winner index; -1 = Draw

    // Populated at runtime from winCondition parameters
    private WinCondition _winCondition;
    private Dictionary<int, int> _scores = new();
    private float _elapsed;
}
```

CRAFT sequence:
```json
[
  {
    "type": "CreateGameObject",
    "parameters": { "name": "MatchManager", "singleton": true }
  },
  {
    "type": "AttachScript",
    "target": "MatchManager",
    "parameters": { "scriptPath": "Assets/Scripts/MatchManager.cs" }
  }
]
```

### Match_SetupVictoryUI

D11 generates `VictoryScreen.uxml` with a root `VisualElement` containing:
- `#winner-label` — `Label` updated at runtime with resolved winner string
- `#score-display` — `Label` block, visible only when `showScore = true`
- `#restart-prompt` — `Label` with animated blink USS class

CRAFT sequence:
```json
[
  {
    "type": "CreateGameObject",
    "parameters": { "name": "UIDoc_Victory" }
  },
  {
    "type": "AttachComponent",
    "target": "UIDoc_Victory",
    "parameters": {
      "component": "UIDocument",
      "sourceAsset": "Assets/UI/VictoryScreen.uxml",
      "panelSettings": "Assets/UI/PanelSettings.asset"
    }
  }
]
```

### Match_SetupScoreboard

D11 generates `Scoreboard.uxml` with a `#scoreboard-root` containing one `#player-row-{n}` per player entry. Each row optionally includes `#hp-bar` (ProgressBar), `#score-value` (Label), and `#timer-display` (Label). Player `color` values are applied as inline USS custom properties (`--player-color: <hex>`).

CRAFT sequence mirrors `Match_SetupVictoryUI` with target name `UIDoc_Scoreboard`.

## Example Scenarios

### Scenario 1: Simple Last-Standing Deathmatch

```
User: "Set up a 2-player last-standing match with R to restart"

1. Match_Configure(
     winCondition: "last-standing",
     playerCount: 2,
     restartKey: "r",
     resetMode: "scene-reload",
     onMatchEnd: "OnMatchEnd"
   )
   → MatchManager singleton created, HealthSystem.OnDeath wired for both players

2. Match_SetupVictoryUI(
     winnerLabel: "OYUNCU {n} KAZANDI",
     restartPrompt: "Yeniden başlatmak için R'ye bas",
     showScore: false,
     style: "minimal"
   )
   → VictoryScreen.uxml mounted as UIDoc_Victory, hidden until match ends

3. Match_SetupScoreboard(
     players: [{ name: "P1", color: "#3399FF" }, { name: "P2", color: "#FF4444" }],
     showHP: true,
     showScore: false,
     showTimer: false,
     position: "top"
   )
   → Live HP bars anchored to top of screen
```

**Expected outcome:**
- MatchManager singleton in scene Hierarchy
- Victory panel hidden at start, shown when a player dies
- HP bars updating in real time from HealthSystem values

### Scenario 2: Score-Limit Mode with Full HUD

```
User: "3-player score race to 10 kills, arcade style UI, bottom scoreboard"

1. Match_Configure(
     winCondition: "score-limit",
     playerCount: 3,
     scoreLimit: 10,
     restartKey: "space",
     resetMode: "soft-reset",
     onMatchEnd: "OnMatchEnd"
   )

2. Match_SetupVictoryUI(
     winnerLabel: "PLAYER {n} WINS",
     restartPrompt: "Press SPACE to play again",
     showScore: true,
     style: "arcade"
   )
   → Blink animation on prompt, bright border flash

3. Match_SetupScoreboard(
     players: [
       { name: "P1", color: "#FF0000" },
       { name: "P2", color: "#00FF00" },
       { name: "P3", color: "#0000FF" }
     ],
     showHP: false,
     showScore: true,
     showTimer: false,
     position: "bottom"
   )
```

**Expected outcome:**
- First player to reach score 10 triggers victory panel
- Scoreboard shows kill counts per player at bottom
- Soft reset respawns players without scene reload

### Scenario 3: Timed Match with Countdown Timer

```
User: "90-second timed match, gothic victory screen, show timer and HP"

1. Match_Configure(
     winCondition: "time-limit",
     playerCount: 2,
     timeLimitSeconds: 90,
     restartKey: "r",
     resetMode: "scene-reload",
     onMatchEnd: "OnMatchEnd"
   )

2. Match_SetupVictoryUI(
     winnerLabel: "ZAFER — OYUNCU {n}",
     restartPrompt: "Yeniden başlatmak için R'ye bas",
     showScore: true,
     style: "gothic"
   )

3. Match_SetupScoreboard(
     players: [{ name: "Oyuncu 1", color: "#CCCCCC" }, { name: "Oyuncu 2", color: "#880000" }],
     showHP: true,
     showScore: true,
     showTimer: true,
     position: "top"
   )
```

**Expected outcome:**
- Countdown timer ticks from 90s to 0 in scoreboard HUD
- On timeout, leader wins; tie triggers Draw state
- Gothic panel overlays with desaturated palette on match end

### Scenario 4: Custom Objective Match

```
User: "Objective-based match — I'll raise OnMatchEnd from my own capture logic"

1. Match_Configure(
     winCondition: "objective",
     playerCount: 2,
     restartKey: "r",
     resetMode: "soft-reset",
     onMatchEnd: "OnMatchEnd"
   )
   → MatchManager listens for external OnMatchEnd invocation; no internal win loop

2. Match_SetupVictoryUI(
     winnerLabel: "NOKTA ALINDI — TAKIM {n}",
     restartPrompt: "R ile tekrar oyna",
     showScore: false,
     style: "minimal"
   )

// In custom capture script:
// MatchManager.Instance.OnMatchEnd?.Invoke(winnerIndex);
```

**Expected outcome:**
- MatchManager defers win evaluation entirely to capture script
- Victory panel shown immediately when OnMatchEnd fires

## Verification Checklist

After executing Match operations, verify:

1. **Match_Configure:**
   - `MatchManager` GameObject present in scene Hierarchy, tagged as singleton
   - `MatchManager.cs` script attached and visible in Inspector
   - `HealthSystem.OnDeath` subscriptions confirmed in Console (no null-ref on startup)
   - `restartKey` input triggers correct reset mode in Play mode

2. **Match_SetupVictoryUI:**
   - `UIDoc_Victory` GameObject present in Hierarchy
   - UIDocument component references correct `.uxml` asset
   - Panel invisible at scene start; appears on match end event
   - `{n}` placeholder resolves to correct player index at runtime

3. **Match_SetupScoreboard:**
   - `UIDoc_Scoreboard` GameObject present in Hierarchy
   - Player rows count matches `players` array length
   - Disabled columns (`showHP: false`, etc.) absent from UXML, not just hidden
   - Live values update correctly in Play mode without GC allocation per frame

4. **Event wiring:**
   - `OnMatchEnd` C# event fires correctly under each win condition
   - No duplicate MatchManager instances across scene reloads (singleton guard active)
   - Soft reset correctly resets `_scores` dictionary and `_elapsed` timer

## Common Workflows

**Minimal deathmatch:**
```
Match_Configure(winCondition: "last-standing", playerCount: 2, restartKey: "r",
  resetMode: "scene-reload", onMatchEnd: "OnMatchEnd")
Match_SetupVictoryUI(winnerLabel: "PLAYER {n} WINS", restartPrompt: "Press R",
  showScore: false, style: "minimal")
```

**Full-featured arcade match:**
```
Match_Configure(winCondition: "score-limit", playerCount: 4, scoreLimit: 5,
  restartKey: "space", resetMode: "soft-reset", onMatchEnd: "OnMatchEnd")
Match_SetupVictoryUI(winnerLabel: "PLAYER {n} WINS", restartPrompt: "SPACE to replay",
  showScore: true, style: "arcade")
Match_SetupScoreboard(players: [...], showHP: false, showScore: true,
  showTimer: false, position: "top")
```

**Timed gothic match:**
```
Match_Configure(winCondition: "time-limit", playerCount: 2, timeLimitSeconds: 120,
  restartKey: "r", resetMode: "scene-reload", onMatchEnd: "OnMatchEnd")
Match_SetupVictoryUI(winnerLabel: "ZAFER {n}", restartPrompt: "R ile yeniden",
  showScore: true, style: "gothic")
Match_SetupScoreboard(players: [...], showHP: true, showScore: true,
  showTimer: true, position: "top")
```

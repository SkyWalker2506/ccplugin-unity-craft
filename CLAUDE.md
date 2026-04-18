# ccplugin-unity-craft

Claude Code plugin for CRAFT — safe Unity scene manipulation + design import + screen control + cinematic + perf optimization via MCP tools.

## Bu plugin ne yapar

Unity MCP + CRAFT uzerinden:
- **Core:** Transaction-safe scene mutasyonu (Create/Modify/Delete GameObject, Query, Rollback)
- **Design Import:** Claude Design handoff bundle → UI Toolkit (UXML + USS + UIDocument)
- **Screen Control:** Game/Scene view capture → vision analizi → autonomous CRAFT ops (kullanıcıya "click X" yasak)
- **Cinematic:** Cinemachine VCam + PostFX preset'leri + shot capture
- **Optimization:** Profiler analizi + batching + texture/LOD/shader optimizasyonu + quality preset'leri
- **Asset Store:** Lokal cache envanteri + UPM registry (`com.unity.*`) + OpenUPM + Git UPM + Asset Store araştırması ve auto-install

Detay: `skills/unity-craft/SKILL.md` + `skills/unity-craft/tools/*.md`

## Agent Routing (Jarvis dispatch matrisi)

| Görev | Hedef Agent | Model |
|-------|-------------|-------|
| UI Toolkit / UXML / USS / design bundle | D11 unity-ui-developer | gpt-5.4 |
| Screenshot → CRAFT ops | G13 vision-action-operator | gpt-5.4 |
| Cinemachine + PostFX | E9 unity-cinematic-director | gpt-5.4 |
| Runtime camera (split-screen, stack) | B37 unity-camera-systems | gpt-5.4 |
| Performance (holistic cross-platform) | B53 unity-performance-analyzer | gemini-3.1-pro |
| Performance (mobile-specific) | B32 unity-mobile-optimizer | gpt-5.4 |
| Asset inventory + UPM/OpenUPM/Asset Store araştırma | E16 asset-store-curator | gemini-3.1-pro |
| Gameplay kodu | B19 unity-developer | gpt-5.4 |

Claude orchestration minimum — implementation Gemini/GPT agent'larına yönlendirilir.

## Dependency

- Unity projede `com.skywalker.craft` package'i kurulu olmali
- Unity MCP bridge aktif olmali (`com.unity.ai.assistant`)
- Screen Control + Optimization (tam fonksiyonel) için: `craft-unity` upstream'e Craft_Inspect + Craft_ImportSettings ops'ları eklenmeli — bkz. `skills/unity-craft/tools/craft-unity-upstream-ops.md`

## Install

```bash
./install.sh
```

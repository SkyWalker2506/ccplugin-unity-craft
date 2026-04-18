# Pixel Rush — Director_Ship Beklenen Çıktı

## Wave 1 — Core Scene Setup

```
Director_ParseGDD → board: 5×8 grid, 3 renk
Craft_Execute: CreateGameObject "Board" (GridLayoutGroup)
Craft_Execute: Spawn 40 CubePrefab → ColorType assigned
Craft_Execute: CreateGameObject "Conveyor" (5 capacity queue)
Craft_Execute: CreateGameObject "SlotManager" (5 slots)
Craft_Execute: PostFX_ApplyPreset "Stylized"
→ Scene görünür, küpler yerleşik
```

## Wave 2 — Character System

```
B19 → GameManager.cs, ConveyorSystem.cs, SlotManager.cs, CubeController.cs
Craft_Execute: Import character prefabs (Pig_Red, Pig_Blue, Pig_Green)
Craft_Execute: Assign Animator controllers
→ Tap → karakter konveyöre biniyor, renk eşleşiyor, küp patlıyor
```

## Wave 3 — UI Toolkit

```
D11 → MainMenu.uxml/uss, GamePlay.uxml/uss, LevelComplete.uxml/uss, GameOver.uxml/uss
Craft_Execute: CreateGameObject "UIDocument_MainMenu"
Craft_Execute: CreateGameObject "UIDocument_GamePlay"
→ HUD görünür: level, coin, slot gösterge, powerup butonları
```

## Wave 4 — Level Data

```
B19 → LevelData ScriptableObject (level 1–5)
Craft_Execute: Addressables group "Levels" → assign level 1
→ Level 1 load → board deterministik spawn → oynanabilir
```

## Wave 5 — Audio + Juice

```
B26 → AudioMixer + gameplay.json preset
DOTween integre → konveyör slide, küp pop particle
→ Full juice: ses + haptic + animasyon
```

## Polish Score Hedefi: ≥ 8.0

| Kriter | Hedef |
|--------|-------|
| Core loop çalışıyor | ✅ |
| Görsel netlik | ≥ 8 |
| Kontrol responsiveness | ≥ 9 |
| UI okunabilirlik | ≥ 8 |
| Audio feel | ≥ 7 |

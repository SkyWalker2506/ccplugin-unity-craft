# Pixel Rush — Unity Clone Project

Pixel Flow (Loom Games) klonu. Top-down sorting shooter / color queue puzzle.

## Entry Point

```
Director_Ship("SAMPLE_GDD.md")
```

## Kurallar

- Tüm UI: UIDocument + UXML + USS — UGUI Canvas yasak
- Tüm sahne mutasyonu: CRAFT ops (Craft_Execute) — doğrudan GameObject.Instantiate çağrısı yasak
- Level data: Addressable ScriptableObject — Resources.Load yasak
- Agent routing: B19 (gameplay kodu), D11 (UI Toolkit), B26 (audio), A14 (orchestration)

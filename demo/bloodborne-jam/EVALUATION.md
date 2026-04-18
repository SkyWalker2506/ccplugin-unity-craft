# Değerlendirme: Bloodborne Jam GDD vs. Mevcut unity-craft Altyapısı

**Tarih:** 2026-04-18  
**Sonuç:** ✅ Büyük ölçüde destekleniyor — 2 gap var, her ikisi de çalışılabilir

---

## Kapsam Analizi

### ✅ Desteklenen (Doğrudan Mevcut Tool'larla)

| GDD Gereksinimi | Tool | Nasıl |
|-----------------|------|-------|
| Arena sahne (platform + duvarlar) | `Level_Generate` | `combat-arena.json` preset → Craft_Execute |
| Gothic atmosfer (sis, karanlık BG) | `PostFX_ApplyPreset` | `horror.json` → Vignette + Color Grading |
| Point Light karakterlerde | `Craft_Execute` → ModifyComponent | Light2D component, intensity/radius |
| Screen shake (vuruş anı) | `Animation_Apply` | `camera-shake-hit.json` preset — CinemachineImpulse |
| HP bar + skill cooldown UI | `ImportDesignBundle` / D11 | UIDocument + UXML/USS → HP bar bileşeni |
| Victory screen UI | D11 → UIDocument | VictoryScreen.uxml, overlay panel |
| Dark gothic BGM + SFX | `Audio_SetMixer` | `horror.json` AudioMixer preset |
| Kan partikülü (vuruş VFX) | `Animation_Apply` | ParticleSystem prefab, Craft_Execute spawn |
| Cinemachine Impulse | `Cinema_CreateVCam` + preset | `camera-shake-hit.json` zaten var |

---

### ⚠️ Kısmi Destek — B19 Agent Gerekli

| GDD Gereksinimi | Durum | Çözüm |
|-----------------|-------|-------|
| CharacterController2D + Rigidbody2D physics | Araç yok — saf gameplay kodu | B19 (unity-developer, gpt-5.4) → `PlayerController.cs` |
| Dual input (2 keyboard scheme aynı anda) | Input presetleri tek oyuncu | B19 → `DualInputHandler.cs`, 2 ayrı InputActionAsset instance |
| HP sistemi + damage collision trigger | Gameplay logic | B19 → `HealthSystem.cs` + `PlayerCombat.cs` |
| Skill cooldown timer | Gameplay logic | B19 → `PlayerSkill.cs` |
| Match win/restart logic | Gameplay logic | B19 → `MatchManager.cs` |
| Warrior Dash skill | Gameplay logic | B19 → Rigidbody2D velocity burst |
| Knockback (AddForce) | Gameplay logic | B19 → `PlayerCombat.cs` içinde |

**Not:** B19 bunları yazabilir. Süresi yaklaşık 5–10 dakika (codex dispatch). Kod kalitesi production-ready değil, jam-grade.

---

### ❌ Eksik — Altyapıda Yok

| GDD Gereksinimi | Neden Eksik | Çözüm |
|-----------------|-------------|-------|
| **Local Multiplayer Input Routing** | Input tool'u single-player varsayıyor; 2 InputActionAsset'i aynı anda yönetecek tool/agent yok | B19'a "dual input" bağlamı açıkça verilmeli; gelecekte `Input_CreateDualScheme` tool'u eklenebilir |
| **Gerçek Playtest (v0.3c)** | `Playtest_Run` dry-run mode — gerçek play mode girişi craft-unity v0.3c'yi bekliyor | Jam için manuel test yeterli; v0.3c specs yazılı, uygulanmadı |

---

## Uygulanabilirlik Özeti

```
Süre Tahmini (Director_Ship ile):

Wave 1 (sahne + arena)        → ~3 dk   ✅ Tam otomatik
Wave 2 (PostFX + atmosphere)  → ~2 dk   ✅ Tam otomatik  
Wave 3 (Input presets)        → ~2 dk   ✅ Tam otomatik
Wave 4 (Gameplay scripts)     → ~8 dk   ⚠️ B19 dispatch (codex)
Wave 5 (UI Toolkit)           → ~5 dk   ✅ D11 dispatch
Wave 6 (Audio)                → ~2 dk   ✅ Tam otomatik
Wave 7 (Animation/VFX)        → ~2 dk   ✅ Tam otomatik

TOPLAM TAHMİN: ~25 dakika (vs. 3 saatlik jam)
```

**Sonuç:** Bizim altyapı bu jam'in %80'ini otomatikleştirir. Geliştirici 3 saatini gameplay kodu debug'ına ve level polish'e harcayabilir — sıfırdan setup'a değil.

---

## Önerilen Gelecek Tool Eklemeleri

Bu projeden çıkan gap'ler için:

1. **`Input_CreateDualScheme(player1Keys, player2Keys)`** — local multiplayer için 2 ayrı InputActionAsset yaratır, PlayerInput component'lerine atar
2. **`Combat_Setup(type, damage, range, knockback, cooldown)`** — temel dövüş component'i konfigürasyonu (hitbox, damage, knockback tek çağrıyla)
3. **`Match_Configure(winCondition, resetKey, victoryUI)`** — match loop (win check + reset) standart konfigürasyonu

Bu 3 tool gelecek forge run'da eklenebilir.

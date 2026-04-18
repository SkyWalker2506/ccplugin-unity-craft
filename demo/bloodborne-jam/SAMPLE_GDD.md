# Game Jam GDD: Bloodborne Online — 3 Saatlik Prototip
# "Yarnham Duel" — Local 1v1 PvP Fighter

**Version:** 1.0  
**Engine:** Unity 6 (URP, 2D)  
**Platform:** PC (Local Multiplayer, Same Machine)  
**Süre:** 3 Saat  
**Ekip:** 2 Kişi  

---

## 1. Hedef ve Kapsam

Bloodborne atmosferinde 1v1 yerel dövüş prototipi. 3 saat sonunda iki oyuncu aynı bilgisayarda karşılıklı dövüşebilmeli.

**MVP Kapsam:** Core combat loop — hareket, saldırı, HP, kazanma/kaybetme, yeniden başlatma.

---

## 2. Oynanış Mekanikleri

### 2.1 Karakter Kontrolleri

| Aksiyon | Oyuncu 1 | Oyuncu 2 |
|---------|----------|----------|
| Hareket (sol/sağ) | A / D | Sol Ok / Sağ Ok |
| Zıplama | W | Yukarı Ok |
| Temel Saldırı | F | K |
| Özel Skill (Dash+Hasar) | G | L |
| Yeniden Başlat (Game Over) | R | R |

### 2.2 Savaş Sistemi

- **HP:** Her oyuncu 100 HP ile başlar
- **Temel Saldırı:** Yakın menzil, 15 hasar, 0.5s cooldown, Knockback force: 8
- **Özel Skill (Warrior Dash):** 30 hasar, 800ms dash, 5s cooldown
- **Knockback:** `Rigidbody2D.AddForce` ile horizontal + slight vertical
- **Ölüm:** HP ≤ 0 → ragdoll disable → "VICTORY" ekran overlay
- **Reset:** R tuşu → SceneManager.LoadScene(current)

### 2.3 Win/Loss

```
HP 0 → PlayerDeath()
  → Disable CharacterController
  → Aktivate VictoryScreen UIDocument
  → "OYUNCU X KAZANDI" + press R to restart
```

---

## 3. 3 Saatlik Geliştirme Planı

### Saat 1 (00:00–01:00): Temeller
- **A (Kod):** CharacterController2D, jump + gravity, dual input scheme
- **B (Sahne):** Arena — platform zemini, 2 kule/sınır, gothic BG + fog particle

### Saat 2 (01:00–02:00): Savaş + UI
- **A (Kod):** HP sistemi, damage collision trigger, skill cooldown timer
- **B (UI+VFX):** HP bar (UI Toolkit), skill cooldown icon, kan partikül efekti

### Saat 3 (02:00–03:00): Döngü + Cila
- **A (Kod):** Victory screen, restart, screen shake (Cinemachine Impulse)
- **B (Audio+FX):** Vuruş SFX, dark gothic BGM, point light karakterlerde

### Bonus (Vakit Kalırsa)
- Kazanana "Anvil" butonu → %50 şans: silah parlar / karakter patlar

---

## 4. Görsel Stil

- **Renk Paleti:** Siyah `#1A1A1A`, Koyu Gri `#333333`, Kan Kırmızısı `#8B0000`
- **Işıklandırma:** Point Light 2D, karakter başında meşale efekti (sarı-turuncu, intensity: 1.5, radius: 3)
- **Fog:** Particle System, white color, low alpha, looping, emisyon rate 20/s
- **PostFX:** Vignette (intensity 0.5) + Color Grading (saturation -30, contrast +20)
- **Karakterler:** Placeholder — 2 renkli capsule (beyaz vs kırmızı), sonra Dark Fantasy sprite

---

## 5. Audio

- **BGM:** Dark, gothic, slow tempo ambient loop (`Audio_SetMixer` → horror preset)
- **SFX:** Sword hit (metallic impact), dash whoosh, death grunt, victory sting
- **Mixer:** horror.json preset (reverb heavy, atmospheric)

---

## 6. Teknik Mimari

### Paketler

```json
{
  "com.skywalker.craft": "git+https://github.com/skywalker/craft-unity.git#v0.2.0",
  "com.unity.ai.assistant": "2.0.0",
  "com.unity.inputsystem": "1.11.0",
  "com.unity.cinemachine": "3.1.1",
  "com.unity.render-pipelines.universal": "17.0.3"
}
```

### Core Scriptler (B19 üretir)

| Script | Sorumluluk |
|--------|------------|
| `PlayerController.cs` | Hareket, jump, Rigidbody2D |
| `PlayerCombat.cs` | Saldırı trigger, hasar, knockback |
| `PlayerSkill.cs` | Dash + cooldown timer |
| `HealthSystem.cs` | HP track, death event |
| `DualInputHandler.cs` | 2 ayrı InputActionAsset instance |
| `MatchManager.cs` | Win check, restart |
| `ScreenShakeController.cs` | Cinemachine Impulse Source |

---

## 7. Director_Ship Entry Point

```
Director_Ship("SAMPLE_GDD.md")
  → Wave 1: Arena sahne (platform + duvarlar + gothic BG + fog)
  → Wave 2: PostFX (vignette + color grading + point lights)
  → Wave 3: Input presets (dual keyboard scheme)
  → Wave 4: B19 → core scripts (PlayerController, Combat, Health, Match)
  → Wave 5: UI Toolkit (HP bars + skill cooldown + VictoryScreen)
  → Wave 6: Audio (horror mixer preset + SFX)
  → Wave 7: Animation (camera-shake-hit preset, combat-ground preset)
  → Critique → polish ≥ 7.0 (jam standard)
```

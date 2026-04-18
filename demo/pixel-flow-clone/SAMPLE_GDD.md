# Game Design Document — Pixel Flow Clone
# "Pixel Rush" — Sorting Shooter / Color Queue Puzzle

**Version:** 1.0  
**Engine:** Unity 6 (URP)  
**Platform:** iOS + Android  
**Reference:** Pixel Flow by Loom Games (Türkiye)  
**Monetization Model:** IAA + IAP Hybrid  

---

## 1. Elevator Pitch

Renk kodlu karakterleri doğru sırayla konveyöre gönder, karakterler eşleşen küpleri temizlesin. Timer yok — ama bekleme slotun dolunca oyun biter. Basit kontrol, derin queue yönetimi.

---

## 2. Core Mechanic

### 2.1 Oyun Alanı Bileşenleri

```
┌─────────────────────────────────────────┐
│         KÜPLER (2D Grid, 5×8)           │
│  🟥🟥🟦🟦🟩  ← üst satır               │
│  🟥🟦🟦🟩🟩                             │
│  🟥🟥🟩🟦🟥                             │
│  ...                                    │
├─────────────────────────────────────────┤
│         KONVEYÖR BANT (5 kapasite)      │
│  [🐷R]→[🐷B]→[🐷G]→[  ]→[  ]          │
├─────────────────────────────────────────┤
│         BEKLEME SLOTLARI (5 adet)       │
│  [🐷R][🐷G][🐷B][  ][  ]               │
└─────────────────────────────────────────┘
```

### 2.2 Oynanış Akışı

1. Bekleme slotunda renkli karakterler (pig/cat/robot) sıralanmış gelir
2. Oyuncu bir karaktere **tap** yapar → konveyöre biner
3. Konveyördeki karakter, kendi rengiyle eşleşen küplere otomatik top atar
4. Tüm eşleşen küpler temizlenince karakter sahneden çıkar
5. Slotlar boşalınca yeni karakterler gelir
6. **Kaybetme koşulu:** Konveyör + slot toplam kapasitesi (10) dolunca yeni karakter giremez → GAME OVER

### 2.3 Kontrol Şeması

- **Tap:** Slottaki karakteri konveyöre gönder
- **Tek elle oynanabilir** — kompleks gesture yok
- Konveyör kapasitesi doluysa tap engellenir (visual feedback)

### 2.4 Özel Mekanikler (Progressive Unlock)

| Level Aralığı | Yeni Mekanik |
|---------------|-------------|
| 1–10 | Temel: 3 renk, 4×6 grid |
| 11–25 | Double Block: 2 tap gerektiren küpler |
| 26–50 | Chain Bonus: 5+ aynı renkli ard arda = 2x coin |
| 51–100 | Mixed Block: 2 renk taşıyan küpler (2 ayrı karakter gerekir) |
| 101+ | Speed Burst: konveyör hızlanma bölgeleri |

---

## 3. Level Yapısı

### 3.1 Level Formatı (ScriptableObject)

```
LevelData {
  levelId: int
  gridWidth: int          // 5–8
  gridHeight: int         // 5–12
  colorCount: int         // 3–6
  cubes: CubeData[]       // position + color + hitsRequired
  initialSlotQueue: CharacterColor[]  // deterministik sıra
  targetScore: int        // tamamlanma için min coin
  parMoves: int           // 3-star için max tap sayısı
}
```

### 3.2 Difficulty Eğrisi

```
Level 1–5:   Eğitim — 3 renk, geniş grid, açık sıra
Level 6–15:  Temel — 4 renk, daha dolu grid
Level 16–35: Orta — double blocks giriyor, tight queue
Level 36:    ★ TRAP LEVEL — neredeyse imkansız, FOMO + streak trigger
Level 37–100: Standart orta-zor, ödül mekanikleri devreye giriyor
Level 100+:  Expert — 6 renk, mixed blocks, full board
```

---

## 4. Progression Sistemi

### 4.1 Currency

- **Coin:** Her tamamlanan level = 40 coin (sabit, zorluktan bağımsız)
- **Gem:** Premium; reklamdan kazanılır veya IAP ile alınır

### 4.2 Powerup'lar (Coin ile satın alınır)

| Powerup | Maliyet | Etki |
|---------|---------|------|
| Shuffle | 100 coin | Slottaki karakterleri yeniden sırala |
| +1 Slot | 150 coin | Geçici 6. slot aç |
| Color Bomb | 200 coin | Tüm aynı renk küpleri patlat |
| Skip Level | 500 coin | Seviyeyi geç, coin kazanma yok |

---

## 5. UI / UX Tasarımı

**Not: Tüm UI Unity UI Toolkit (UXML + USS) ile yapılır. UGUI Canvas kullanılmaz.**

### 5.1 Ekranlar

| Ekran | Açıklama |
|-------|---------|
| `MainMenu.uxml` | Logo, Play butonu, coin/gem gösterge, settings |
| `GamePlay.uxml` | Küp grid overlay, konveyör HUD, slot gösterge, powerup butonları |
| `LevelComplete.uxml` | 3 yıldız animasyon, coin kazanım, next level |
| `GameOver.uxml` | "Devam et" (rewarded ad) veya restart |
| `Shop.uxml` | IAP + rewarded ad seçenekleri |

### 5.2 HUD Elemanları (GamePlay)

- Her karakterin başı üstünde ammo counter (kaç küp kalıyor)
- Konveyör kapasite bar (5/5 dolunca kırmızılaşır)
- Slot'lar: dolu/boş durum renk kodu
- Üst bar: level no + coin + gem
- Sağ köşe: pause + powerup butonları

### 5.3 Feel / Juice

- Küp patlama: particle burst + haptic (light impact)
- Konveyöre binme: DOTween slide + bounce ease
- Renk eşleşme: kısa flaş + satisfying pop SFX
- Slotlar doluyken tap: kısa shake + "full!" tooltip
- Chain bonus: ekran geneli glow + ses yükselişi

---

## 6. Art Style

- **Stil:** 3D low-poly cartoon (pixel art değil — pixel kelimesi brand ismi)
- **Karakterler:** Sevimli hayvanlar (domuz, kedi, ayı) — renk tonu karakter rengiyle uyumlu
- **Küpler:** Yuvarlak köşeli, parlak doygun renkler
- **Background:** Sade gradient, grid net görünsün diye kontrast düşük
- **Renk Paleti:**
  - Kırmızı: `#FF4444`
  - Mavi: `#4488FF`
  - Yeşil: `#44CC66`
  - Sarı: `#FFCC00`
  - Mor: `#9944FF`
  - Turuncu: `#FF8833`

---

## 7. Audio

- **BGM:** Upbeat, döngüsel, dikkat dağıtmayan
- **SFX:** Küp pop, konveyör kayma, slot dolma, game over, level complete
- **Mixer Presets:** `gameplay.json` (balanced), `tense.json` (slot dolunca aktif)

---

## 8. Monetizasyon (Unity LevelPlay / ironSource)

### 8.1 Reklam Akışı

| Tetikleyici | Ad Tipi |
|-------------|---------|
| Her 2 level tamamlanınca | Interstitial (level 20'den itibaren) |
| Game Over ekranı | Rewarded → 2 can + devam et |
| Level complete (opsiyonel) | Rewarded → 2x coin |
| Günlük bonus | Rewarded → 100 coin |

### 8.2 IAP

| Ürün | Fiyat | İçerik |
|------|-------|--------|
| Remove Ads | ₺49.99 | Tüm interstitial'lar kaldırılır |
| Coin Pack S | ₺19.99 | 1000 coin |
| Coin Pack M | ₺49.99 | 3000 coin + 50 gem |
| Coin Pack L | ₺99.99 | 8000 coin + 150 gem |
| Starter Bundle | ₺29.99 | Remove Ads + 500 coin (first-time only) |

---

## 9. Teknik Mimari (Unity 6)

### 9.1 Paketler

```json
{
  "com.skywalker.craft": "git+https://github.com/skywalker/craft-unity.git#v0.2.0",
  "com.unity.ai.assistant": "2.0.0",
  "com.unity.inputsystem": "1.11.0",
  "com.unity.textmeshpro": "3.0.6",
  "com.unity.addressables": "2.3.1",
  "com.unity.monetization": "4.4.2",
  "com.ironsource.mediation": "7.9.0",
  "com.unity.render-pipelines.universal": "17.0.3",
  "com.kybernetik.animancer": "8.0.0"
}
```

### 9.2 Core Sistemler

| Sistem | Implementation |
|--------|----------------|
| Konveyör | `Queue<CharacterController>` + DOTween path |
| Slot Manager | `List<SlotView>` (5 eleman) + event bus |
| Grid/Board | 2D array `CubeData[,]` + prefab pool |
| Renk eşleşme | `ColorType enum` karşılaştırma + Physics2D |
| Level Loading | Addressables → ScriptableObject stream |
| Save/Load | PlayerPrefs (level no, coin) + Cloud Save |
| Analytics | Unity Analytics → funnel per level |

### 9.3 Klasör Yapısı

```
Assets/
  Characters/       ← prefab + animator controller per color
  Cubes/            ← cube prefab variants (single/double/mixed)
  Levels/           ← LevelData ScriptableObjects (Addressable groups)
  UI/               ← UXML + USS dosyaları
  Scripts/
    Core/           ← GameManager, ConveyorSystem, SlotManager
    Grid/           ← BoardBuilder, CubeController
    UI/             ← ScreenController, HUDPresenter
    Monetization/   ← AdManager, IAPManager
    Data/           ← LevelData, SaveData
  Audio/            ← AudioMixer + clips
```

---

## 10. Director_Ship Entry Point

```
Director_Ship("pixel-flow-clone/SAMPLE_GDD.md")
  → ParseGDD → PlanGame (wave DAG)
  → Wave 1: Core scene setup (Board + Conveyor + Slots)
  → Wave 2: Character system + color matching
  → Wave 3: UI Toolkit screens (MainMenu + GamePlay + LevelComplete)
  → Wave 4: Level 1–5 data + progression
  → Wave 5: Audio + haptics + juice
  → Wave 6: Ad integration (dry-run)
  → Critique → polish score ≥ 8.0
```

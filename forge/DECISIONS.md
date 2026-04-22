# Decisions Log — ccplugin-unity-craft forge

Append-only. Each decision captures: what, why, alternatives considered, downstream effects.

## Run 1 — 2026-04-18

### D001: Forge-light mode — skip Jira/PR ceremony, keep structure
- **Karar:** /forge 5 invocation-ında tam Jira ticket + PR + Opus review cycle uygulanmadı. Forge'un iskeleti (Phase 1 analysis, Phase 4 dispatch, Phase 5 lessons, Phase 7 meta-analysis, DECISIONS.md) korundu; ticket-per-task + branch-per-task atlandı.
- **Neden:** (a) ccplugin-unity-craft için dedicated Jira project yok; mevcut FECRFT (Frontend Craft Plugin) semantik yanlış olur. (b) Tek-developer projesi için 5 run × N task × 2 PR (coder + reviewer) spam üretir. (c) Kullanıcı önceki session'da "forge bypass" kararımı onayladı.
- **Alternatifler:** Full forge (rejected — noise), pure direct dispatch (rejected — lessons/decisions kaybı), bu hibrit (kabul)
- **Etkisi:** run-N-summary.md + run-N-lessons.md + DECISIONS.md tutulur, Jira ticket + PR tutulmaz. Değişiklikler tek feat commit'i ile gider.

### D002: Agent dispatch > Jarvis direct implementation
- **Karar:** Kod yazma (.py, .cs, büyük .md) Haiku sub-agent veya /dispatch → GPT'ye gider. Jarvis orchestration + sentez + küçük edit yapar.
- **Neden:** Kullanıcının "Claude minimum, Gemini/GPT ağırlıklı" kuralı + memory feedback_dispatch_implementation.md.
- **Etkisi:** Her run'da 2-4 paralel Haiku/GPT dispatch; Jarvis yerine implement edenler onlar. Token/kalite dengesi Jarvis lehine, hız sub-agent lehine.

### D003: K7 hallucination fix — `com.xesmedia.fsm` kaldırıldı
- **Karar:** E16 knowledge'deki sahte UPM paket adı (`com.xesmedia.fsm`) gerçek bir alternatifle değiştirildi veya kaldırıldı.
- **Neden:** Audit verify etti — OpenUPM'de o paket yok. Agent bunu önerirse kullanıcı manifest'e ekleyip Unity'de hata alır.
- **Etkisi:** E16'nın state-machine önerisi artık doğrulanmış paketleri işaret ediyor.

### D004: FilmGrain HDRP-only etiketleme
- **Karar:** PostFX knowledge + 2 preset JSON (horror, dreamy) FilmGrain için `hdrp_only: true` veya inline not içerecek.
- **Neden:** Unity 6'da URP Volume stack'inde FilmGrain Component'i yok; URP'de çalışıyormuş gibi preset uygulanırsa sessizce görmezden gelinir (debug zor).
- **Etkisi:** E9 dispatch protokolü pipeline-auto-detect kullanıyor; artık pipeline mismatch erken yakalanır.

### D005: Weak-points openly scored — polish değil gerçek iş
- **Karar:** MASTER_ANALYSIS'te her W-item severity + fix-ROI ile kaydedildi. Run 2-5 bu listeye göre ilerler; rastgele feature değil.
- **Neden:** Kullanıcının 9/10 hedefi + "mantıklı şekilde" dayatması → ROI-driven plan.
- **Etkisi:** Run 2 = W2/W3 (preset schema + validator), Run 3 = W5 (legacy .unitypackage import), Run 4 = yeni alan (animation), Run 5 = W6/W10/W11/W12 (integration demo + CHANGELOG).

### D006: Run 2 deferred — codex + gemini unavailable
- **Karar:** Preset JSON schema + validate_presets.py Run 2'de yazılmadı. Codex CLI kotası bitti, Gemini CLI 404 auth error verdi.
- **Neden:** User directive "Claude minimum"; her iki external model da başarısız; Claude'a fallback etmemek doğru. Öte yandan 19 preset zaten commit'li ve çalışıyor — drift-catcher yokluğu bugünkü kullanıma engel değil.
- **Etkisi:** W2 + W3 weak-point'leri açık kalır. Run 5 meta-analysis'te "open items" olarak raporlanır. Kullanıcı quota reset edince dispatch yeniden denenebilir.
- **Alternatif denenen:** Groq (user'ın key'i var ama /dispatch skill'i Groq route etmiyor — dev cost yüksek)

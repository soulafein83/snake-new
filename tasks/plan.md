# Implementation Plan: SnakeNew — dalszy rozwój gry

## Overview
Plan rozwija grę po zakończeniu iteracji 1–5 (testy, tryby trudności, zapis, top‑scores, przeszkody, gamepad). Nowe prace grupują się wokół trzech osi: (1) ustawienia i motywy jako fundament konfiguracji, (2) nowa mechanika power‑upów, (3) polerka wizualna i progresja. Każda faza pozostawia grę działającą i zweryfikowaną.

## Architecture Decisions
- `snake/core` pozostaje wolne od pygame; power‑upy i statystyki są czystymi modelami.
- Nowe moduły: `snake/settings.py`, `snake/core/powerup.py`, `snake/stats.py`.
- Ustawienia i statystyki zapisywane w `persistence.py` z wersjonowaniem i fallbackiem.
- Motyw to słownik palet w `config.py`; renderer czyta kolory przez `settings`, nie przez stałe.
- Power‑upy są danymi w `Game`; `Renderer` tylko je rysuje, `Application` obsługuje HUD.

## Dependency Graph
```
settings persistence (T11)
    ├── settings screen (T12)
    └── theme palette (T13) ──► renderer / backgrounds (T17–T19)

powerup model (T14) ──► effects in Game (T15) ──► HUD + render (T16)

stats persistence (T20) ──► achievements (T21) ──► stats screen (T22)
```

## Task List

### Phases 1–5 — ukończone
Zob. `tasks/todo.md`: fundament, jakość, top‑N, trudności, zapis gry, optymalizacje, przeszkody, TOP SCORES, gamepad.

### Checkpoint: Historyczny
- [x] pytest, ruff, pyright, smoke headless

---

### Phase 6: Ustawienia i motywy (foundation)

#### Task 11: Model ustawień i persistence
**Description:** Dodać `snake/settings.py` z `Settings` (audio, reduced_motion, theme, wrap_around) oraz zapis/odczyt w `persistence.py` (nowy plik `settings.json`, wersja 1, walidacja i fallback do domyślnych wartości).

**Acceptance criteria:**
- [ ] Brak pliku → wartości domyślne.
- [ ] Nieprawidłowe typy/wartości → fallback bez wyjątku.
- [ ] Zapis jest atomowy i odczytywany z `SNAKE_DATA_DIR`.

**Verification:** `pytest tests/test_settings.py`, `ruff`, `pyright`.
**Dependencies:** None.
**Files:** `snake/settings.py`, `snake/persistence.py`, `snake/config.py`, `tests/test_settings.py`.
**Scope:** S.

#### Task 12: Ekran ustawień w menu
**Description:** Dodać `MenuScreen.SETTINGS` z przełącznikami (Audio, Reduced motion, Wrap around, Theme) i połączyć z `Settings` w `Application`.

**Acceptance criteria:**
- [ ] Wybór opcji zmienia wartość i zapisuje ją.
- [ ] `Esc` wraca do menu głównego.
- [ ] Ustawienia audio i reduced motion wpływają na app/renderer.

**Verification:** `pytest tests/test_app.py`, `ruff`, `pyright`.
**Dependencies:** T11.
**Files:** `snake/menu.py`, `snake/app.py`, `snake/render.py`, `tests/test_app.py`.
**Scope:** M.

#### Task 13: Motywy kolorystyczne
**Description:** Dodać 3 palety (`classic`, `neon`, `retro`) w `config.py` i sprawić, by renderer pobierał kolory z aktywnego motywu zamiast stałych.

**Acceptance criteria:**
- [ ] Zmiana motywu w ustawieniach zmienia planszę, węża i menu bez restartu.
- [ ] Istniejący wygląd `classic` pozostaje domyślny.

**Verification:** `pytest`, smoke headless, `ruff`, `pyright`.
**Dependencies:** T11, T12.
**Files:** `snake/config.py`, `snake/render.py`, `snake/app.py`.
**Scope:** M.

### Checkpoint: Po T11–T13
- [ ] Ustawienia działają end‑to‑end, motywy nie psują renderu.

---

### Phase 7: Mechanika — power‑upy

#### Task 14: Model power‑upów i spawn
**Description:** `snake/core/powerup.py` z typami `SLOW`, `SHIELD`, `BONUS`; `Game` spawnuje je co N zjedzeń na wolnej komórce (nie koliduje z jedzeniem, przeszkodami ani wężem).

**Acceptance criteria:**
- [ ] Power‑up znika po N tickach.
- [ ] Spawn respektuje RNG i nie narusza sekwencji przy braku power‑upów.
- [ ] Testy pokrywają spawn, timeout i kolizję.

**Verification:** `pytest tests/test_core.py`, `ruff`, `pyright`.
**Dependencies:** None (może równolegle z T11–T13).
**Files:** `snake/core/powerup.py`, `snake/core/game.py`, `tests/test_core.py`.
**Scope:** M.

#### Task 15: Efekty power‑upów w rozgrywce
**Description:** `SLOW` tymczasowo zwiększa `step_interval`, `SHIELD` pochłania jedną śmierć, `BONUS` dodaje punkty. Dodać liczniki czasu trwania do `Game`.

**Acceptance criteria:**
- [ ] Efekty mają określony czas i kończą się same.
- [ ] Shield nie zapobiega wygranej/anulowaniu runu po zakończeniu.
- [ ] Save/restore zachowuje aktywne efekty.

**Verification:** `pytest`, `ruff`, `pyright`.
**Dependencies:** T14.
**Files:** `snake/core/game.py`, `snake/app.py`, `tests/test_core.py`.
**Scope:** M.

#### Task 16: Render i HUD power‑upów
**Description:** Rysowanie power‑upów na planszy oraz pasek aktywnych efektów w HUD.

**Acceptance criteria:**
- [ ] Ikony/efekty są czytelne we wszystkich motywach.
- [ ] HUD pokazuje pozostały czas efektu.

**Verification:** `pytest`, smoke headless, `ruff`, `pyright`.
**Dependencies:** T13, T15.
**Files:** `snake/render.py`, `snake/config.py`.
**Scope:** S.

### Checkpoint: Po T14–T16
- [ ] Power‑upy działają end‑to‑end, brak regresji w core.

---

### Phase 8: Polerka wizualna

#### Task 17: Cząsteczki i screen shake
**Description:** Prosty system cząstek przy zjedzeniu/śmierci oraz krótki shake ekranu.

**Acceptance criteria:**
- [ ] Efekty respektują `REDUCED_MOTION`.
- [ ] Brak alokacji w hot path (pula cząstek).

**Verification:** smoke headless, `pytest`, `ruff`, `pyright`.
**Dependencies:** T13.
**Files:** `snake/render.py`, `snake/config.py`, `snake/app.py`.
**Scope:** M.

#### Task 18: Animacje zakończenia rundy
**Description:** Wąż „rozpuszcza się” przy game over, krótkie zwolnienie przy win zamiast natychmiastowego panelu.

**Acceptance criteria:**
- [ ] Animacja nie blokuje inputu dłużej niż obecny transition.
- [ ] Można ją wyłączyć w ustawieniach reduced motion.

**Verification:** `pytest tests/test_app.py`, smoke, `ruff`, `pyright`.
**Dependencies:** T12, T13.
**Files:** `snake/app.py`, `snake/render.py`, `snake/ui.py`.
**Scope:** M.

#### Task 19: Tła i siatka per motyw
**Description:** Różne wzory siatki i tła dla motywów (np. neonowe linie, retro ASCII).

**Acceptance criteria:**
- [ ] Motyw zmienia tło menu i planszy.
- [ ] Cache grafik nie rośnie bez ograniczenia.

**Verification:** smoke, `pytest`, `ruff`, `pyright`.
**Dependencies:** T13.
**Files:** `snake/render.py`, `snake/config.py`.
**Scope:** S.

### Checkpoint: Po T17–T19
- [ ] Gra wygląda spójnie we wszystkich motywach, brak regresji wydajności.

---

### Phase 9: Progresja i meta

#### Task 20: Poziomy / etapy
**Description:** Co N zjedzeń przejście do kolejnego poziomu: więcej przeszkód, szybsza prędkość, nowy motyw tła.

**Acceptance criteria:**
- [ ] Poziom rośnie zgodnie z progiem i jest zapisywany.
- [ ] HUD pokazuje aktualny poziom.

**Verification:** `pytest`, `ruff`, `pyright`.
**Dependencies:** T13, T14.
**Files:** `snake/core/game.py`, `snake/config.py`, `snake/render.py`, `tests/test_core.py`.
**Scope:** M.

#### Task 21: Statystyki i osiągnięcia
**Description:** `snake/stats.py` + persistence: liczba gier, całkowity wynik, najdłuższy wąż, odblokowane osiągnięcia.

**Acceptance criteria:**
- [ ] Statystyki aktualizują się po każdej rundzie.
- [ ] Osiągnięcia mają progi i są trwałe.

**Verification:** `pytest tests/test_stats.py`, `ruff`, `pyright`.
**Dependencies:** T11.
**Files:** `snake/stats.py`, `snake/persistence.py`, `snake/app.py`, `tests/test_stats.py`.
**Scope:** M.

#### Task 22: Ekran statystyk w menu
**Description:** Nowy ekran „Statistics” z liczbami i odblokowanymi osiągnięciami.

**Acceptance criteria:**
- [ ] Dane z T21 są widoczne i czytelne.
- [ ] Nawigacja zgodna z innymi ekranami.

**Verification:** `pytest tests/test_app.py`, smoke, `ruff`, `pyright`.
**Dependencies:** T21.
**Files:** `snake/menu.py`, `snake/render.py`, `snake/app.py`.
**Scope:** S.

### Checkpoint: Końcowy
- [ ] Wszystkie testy przechodzą.
- [ ] Każda nowa funkcja ma test lub jasną weryfikację manualną.
- [ ] Gotowe do review.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Zmiana palet rozjedzie layout | Średni | Zachować `classic` jako domyślny, test smoke |
| Power‑upy zmienią RNG i zepsują testy seedowane | Średni | Spawn tylko przy włączonych power‑upach, osobny RNG |
| Nowe pliki settings/stats zwiększą złożoność persistence | Niski | Wersjonowanie + fallback + testy |
| Animacje pogorszą FPS | Niski | Pule obiektów, `REDUCED_MOTION`, profil smoke |

## Open Questions
- Czy power‑upy mają być domyślnie włączone we wszystkich trudnościach?
- Czy motywy mają zmieniać tylko kolory, czy też siatkę i tło (T19)?
- Czy statystyki powinny być per trudność, czy globalne?
- Czy wrap‑around (T12) zmienia zasady gry na tyle, by wymagał osobnego trybu?

## Parallelization Opportunities
- T11–T13 (ustawienia/motywy) oraz T14 (model power‑upów) są niezależne i mogą iść równolegle.
- T17–T19 (wizualia) po T13, ale przed T20–T22.
- T20 i T21 wymagają ustaleń co do progu poziomu i statystyk — najpierw krótka decyzja projektowa.

# Potential bugs — SnakeNew

Review of `main.py` and the `snake/` package. All 18 reported findings were
addressed: fixes verified headless (dummy SDL driver) and re-run through the
full regression suite.

---

## Not bugs (verified OK, listed to close the loop)

- `snake.py` `advance` — tail removed before head inserted; moving into the vacated tail cell is correctly legal.
- `snake.py` `request_turn` — reversal and duplicate rejection uses the last queued direction as reference; correct for `TURN_QUEUE_MAX = 2`.
- `game.py` `tick` — wall check before self-collision check; self-collision exempts the vacating tail only when not growing. Correct.
- `game.py` win condition — `food.position is None` after a full-board spawn triggers `State.WON`. Correct.
- `persistence.py` — atomic write via `os.replace`; `bool`/negative guards on both read and write. Correct.
- `render.py` `_blit` — `set_alpha` on an SRCALPHA surface multiplies per-pixel alpha in SDL2/pygame 2.x; the reset to 255 is correct.
- `app.py` accumulator/alpha for smooth motion — `prev_body` is set *before* `advance` in `tick`, so `prev_body[i]` and `body[i]` correspond to the correct logical segments for lerp.
- `menu.py` `move` — modulo wrap is correct; `selected` is reset to 0 on every `set_screen`.
- `render.py` `_draw_ghost_snake` — ghost path starts at board row 2, which lands at window y ≈ 140, safely below the HUD; no overlap.
- `persistence.py` `load_high_score` — `OSError` already covers `NotADirectoryError` (it's a subclass); the `try` block is correct as written.

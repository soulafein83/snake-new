"""Food spawning on free grid cells."""

from __future__ import annotations

import random
from functools import cache

from snake.config import COLS, ROWS
from snake.core.snake import Cell


@cache
def _all_cells(cols: int, rows: int) -> tuple[Cell, ...]:
    return tuple((x, y) for y in range(rows) for x in range(cols))


class Food:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng if rng is not None else random.Random()
        self.position: Cell | None = None

    def spawn(
        self,
        occupied: set[Cell],
        cols: int = COLS,
        rows: int = ROWS,
    ) -> Cell | None:
        """Place food on a random free cell, or clear it when the board is full."""
        # Keep the exact row-major order (and therefore the RNG sequence)
        # of the original implementation; only the cell enumeration is cached.
        free = [cell for cell in _all_cells(cols, rows) if cell not in occupied]
        self.position = self.rng.choice(free) if free else None
        return self.position

    def clear(self) -> None:
        self.position = None

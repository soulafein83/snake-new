"""The snake body: a deque of cells plus an occupancy set."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from snake.config import START_LENGTH, TURN_QUEUE_MAX
from snake.core.direction import Direction

Cell = tuple[int, int]


class Snake:
    """Grid snake.

    Invariants:
      * ``body[0]`` is the head, ``body[-1]`` the tail.
      * Cells are unique and each consecutive pair is orthogonally adjacent.
      * ``occupied == set(body)`` after every mutation.
    """

    def __init__(
        self,
        start: Cell = (12, 10),
        direction: Direction = Direction.RIGHT,
        length: int = START_LENGTH,
    ) -> None:
        if length < 1:
            raise ValueError("snake length must be at least 1")
        dx, dy = direction.opposite.vector
        cells = [(start[0] + dx * i, start[1] + dy * i) for i in range(length)]
        self.body: deque[Cell] = deque(cells)
        self.occupied: set[Cell] = set(cells)
        self.direction: Direction = direction
        self.pending: deque[Direction] = deque(maxlen=TURN_QUEUE_MAX)

    @classmethod
    def from_cells(cls, cells: Iterable[Cell], direction: Direction) -> Snake:
        """Build a snake from explicit cells (first cell is the head)."""
        seq = list(cells)
        if not seq:
            raise ValueError("snake needs at least one cell")
        if len(set(seq)) != len(seq):
            raise ValueError("snake cells must be unique")
        obj = cls.__new__(cls)
        obj.body = deque(seq)
        obj.occupied = set(seq)
        obj.direction = direction
        obj.pending = deque(maxlen=TURN_QUEUE_MAX)
        return obj

    # --- Queries -----------------------------------------------------------
    @property
    def head(self) -> Cell:
        return self.body[0]

    @property
    def tail(self) -> Cell:
        return self.body[-1]

    def next_head(self) -> Cell:
        hx, hy = self.head
        return (hx + self.direction.dx, hy + self.direction.dy)

    def __len__(self) -> int:
        return len(self.body)

    # --- Turns -------------------------------------------------------------
    def request_turn(self, direction: Direction) -> bool:
        """Queue a turn, rejecting reversals, duplicates and a full queue.

        The reference is the last *queued* direction (or the applied one when
        the queue is empty), so a double tap cannot fold the snake back onto
        itself across ticks.
        """
        reference = self.pending[-1] if self.pending else self.direction
        if direction is reference or direction is reference.opposite:
            return False
        if len(self.pending) >= TURN_QUEUE_MAX:
            return False
        self.pending.append(direction)
        return True

    def consume_turn(self) -> Direction | None:
        return self.pending.popleft() if self.pending else None

    # --- Movement ----------------------------------------------------------
    def advance(self, grow: bool = False, target: Cell | None = None) -> Cell:
        """Move one cell forward. Returns the new head cell."""
        new_head = target if target is not None else self.next_head()
        if not grow:
            # Remove the tail *before* inserting the head: moving into the
            # cell the tail is vacating is legal, and the cell must not be
            # removed from ``occupied`` after being added again.
            old_tail = self.body.pop()
            self.occupied.discard(old_tail)
        self.body.appendleft(new_head)
        self.occupied.add(new_head)
        return new_head

    # --- Diagnostics -------------------------------------------------------
    def is_consistent(self) -> bool:
        if not self.body:
            return False
        if len(set(self.body)) != len(self.body):
            return False
        if self.occupied != set(self.body):
            return False
        return all(
            abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
            for a, b in zip(self.body, list(self.body)[1:], strict=False)
        )

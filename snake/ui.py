"""Small rendering helpers: easing, colours and the fade transition."""

from __future__ import annotations

from collections.abc import Callable

from snake.config import MAX_DT, TRANSITION_S

Color = tuple[int, int, int]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(a: Color, b: Color, t: float) -> Color:
    t = clamp(t)
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def ease_out_cubic(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


class Transition:
    """Short black fade; the queued callback runs at the darkest point."""

    def __init__(self, duration: float = TRANSITION_S) -> None:
        self.duration = duration
        self.t = 0.0
        self.active = False
        self._callback: Callable[[], None] | None = None
        self._fired = False

    def start(self, on_midpoint: Callable[[], None] | None = None) -> None:
        if self.active:
            # A fade is already in flight: keep its pending callback and
            # ignore this request so nothing is silently lost. Callers must
            # check `active` before calling `start`.
            return
        self.t = 0.0
        self.active = True
        self._callback = on_midpoint
        self._fired = False

    @property
    def blocks_input(self) -> bool:
        return self.active

    @property
    def alpha(self) -> int:
        if not self.active:
            return 0
        half = self.duration / 2.0
        if self.t <= half:
            return int(255 * clamp(self.t / half))
        return int(255 * clamp(1.0 - (self.t - half) / half))

    def update(self, dt: float) -> None:
        if not self.active:
            return
        # Cap dt (as the app does) so an oversized frame from a test or a
        # future caller cannot skip past the midpoint at a wrong time.
        self.t += min(max(0.0, dt), MAX_DT)
        half = self.duration / 2.0
        if not self._fired and self.t >= half:
            self._fired = True
            if self._callback is not None:
                callback, self._callback = self._callback, None
                callback()
        if self.t >= self.duration:
            self.active = False
            self.t = 0.0
            self._callback = None

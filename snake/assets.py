"""Fonts and optional synthesized sound effects with silent fallbacks."""

from __future__ import annotations

import contextlib
import math
from array import array

import pygame

_FONT_NAMES = ("dejavusansmono", "consolas", "liberationmono", "monospace")


def _load_font(size: int, bold: bool) -> pygame.font.Font:
    """Load the first available font in ``_FONT_NAMES``.

    ``SysFont`` with a comma list silently falls back to the built-in
    default when none of the names exists, so the monospace intent is
    not guaranteed. Resolve the names explicitly; if truly none is
    available, use the built-in default as the documented fallback.
    """
    for name in _FONT_NAMES:
        path = pygame.font.match_font(name)
        if path:
            font = pygame.font.Font(path, size)
            font.set_bold(bold)
            return font
    return pygame.font.Font(None, size)


# ``pygame.mixer.get_init`` reports the bit depth as signed (negative) or
# unsigned (positive); map each to its array typecode and sample ceiling so
# the sound buffer always matches the live mixer format.
_SAMPLE_FORMATS: dict[int, tuple[str, bool, int]] = {
    -16: ("h", True, 32767),
    16: ("H", False, 65535),
    -8: ("b", True, 127),
    8: ("B", False, 255),
}


def _mixer_init() -> tuple[int, int, int] | None:
    """Return the active mixer format, or None if audio is unavailable.

    ``pygame.mixer.get_init`` may be missing (or raise) when the mixer
    subsystem was never successfully initialised, so probe defensively.
    """
    try:
        return getattr(pygame.mixer, "get_init", lambda: None)()
    except (Exception, SystemExit):  # noqa: BLE001 - audio is strictly optional
        return None


class Assets:
    def __init__(self) -> None:
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    def font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._fonts:
            try:
                self._fonts[key] = _load_font(size, bold)
            except Exception:  # noqa: BLE001 - font availability is best-effort
                self._fonts[key] = pygame.font.Font(None, size)
        return self._fonts[key]


class Audio:
    """Tiny procedural blips. Any failure leaves the game silent."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        if not enabled:
            return
        try:
            if _mixer_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.sounds = {
                "hover": self._tone(660.0, 0.035, 0.10),
                "confirm": self._tone(880.0, 0.075, 0.16),
                "eat": self._tone(1046.0, 0.060, 0.18),
                "over": self._tone(196.0, 0.220, 0.20),
                "win": self._tone(1318.0, 0.260, 0.18),
            }
            self.enabled = True
        except (Exception, SystemExit):  # noqa: BLE001 - audio is strictly optional
            self.enabled = False
            self.sounds = {}

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        with contextlib.suppress(pygame.error):
            sound.play()

    @staticmethod
    def _tone(frequency: float, seconds: float, volume: float) -> pygame.mixer.Sound:
        init = _mixer_init()
        if init is None:
            raise pygame.error("mixer not initialised")
        sample_rate, size, channels = init
        code, signed, max_sample = _SAMPLE_FORMATS.get(size, ("h", True, 32767))
        count = max(1, int(sample_rate * seconds))
        attack = max(1, int(sample_rate * 0.008))
        release = max(1, int(sample_rate * 0.030))
        samples = array(code)
        for index in range(count):
            if index < attack:
                env = index / attack
            elif index > count - release:
                env = max(0.0, (count - index) / release)
            else:
                env = 1.0
            wave = math.sin(2.0 * math.pi * frequency * index / sample_rate)
            if signed:
                value = int(max_sample * volume * env * wave)
            else:
                value = max_sample // 2 + int((max_sample // 2) * volume * env * wave)
            samples.extend((value,) * channels)
        return pygame.mixer.Sound(buffer=samples.tobytes())

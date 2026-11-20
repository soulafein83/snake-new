"""User preferences, independent of pygame and the game core."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Settings:
    audio: bool = True
    reduced_motion: bool = False
    theme: str = "classic"
    wrap_around: bool = False

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "audio": self.audio,
            "reduced_motion": self.reduced_motion,
            "theme": self.theme,
            "wrap_around": self.wrap_around,
        }

    @classmethod
    def from_dict(cls, data: object) -> Settings:
        if not isinstance(data, dict):
            return cls()
        values = {
            "audio": _as_bool(data.get("audio"), True),
            "reduced_motion": _as_bool(data.get("reduced_motion"), False),
            "theme": _as_theme(data.get("theme")),
            "wrap_around": _as_bool(data.get("wrap_around"), False),
        }
        return cls(**values)

    def updated(self, **changes: object) -> Settings:
        return replace(self, **changes)  # type: ignore[arg-type]


def _as_bool(value: object, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _as_theme(value: object) -> str:
    if isinstance(value, str) and value in _VALID_THEMES:
        return value
    return "classic"


_VALID_THEMES = frozenset({"classic", "neon", "retro"})

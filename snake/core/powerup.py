"""Power-up data model for the game core (no pygame)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from snake.core.snake import Cell


class PowerUpType(Enum):
    SLOW = "slow"
    SHIELD = "shield"
    BONUS = "bonus"


@dataclass(frozen=True)
class PowerUp:
    kind: PowerUpType
    position: Cell
    ttl: int

    def to_dict(self) -> dict:
        return {"kind": self.kind.value, "position": list(self.position), "ttl": self.ttl}

    @classmethod
    def from_dict(cls, data: object) -> PowerUp | None:
        if not isinstance(data, dict):
            return None
        try:
            kind = PowerUpType(data["kind"])
            pos = data["position"]
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                return None
            return cls(kind, (int(pos[0]), int(pos[1])), int(data["ttl"]))
        except (KeyError, ValueError, TypeError):
            return None

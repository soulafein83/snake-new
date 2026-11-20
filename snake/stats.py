"""Persistent career statistics and achievements."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Stats:
    games_played: int = 0
    total_score: int = 0
    best_level: int = 1
    longest_snake: int = 0
    achievements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "games_played": self.games_played,
            "total_score": self.total_score,
            "best_level": self.best_level,
            "longest_snake": self.longest_snake,
            "achievements": list(self.achievements),
        }

    @classmethod
    def from_dict(cls, data: object) -> Stats:
        if not isinstance(data, dict):
            return cls()

        def as_int(key: str, default: int) -> int:
            value = data.get(key, default)
            return (
                value
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0
                else default
            )

        achievements = data.get("achievements", [])
        if not isinstance(achievements, list):
            achievements = []
        return cls(
            games_played=as_int("games_played", 0),
            total_score=as_int("total_score", 0),
            best_level=as_int("best_level", 1),
            longest_snake=as_int("longest_snake", 0),
            achievements=[a for a in achievements if isinstance(a, str)],
        )

    def record_run(self, game) -> None:  # type: ignore[no-untyped-def]
        self.games_played += 1
        self.total_score += game.score
        self.best_level = max(self.best_level, game.level)
        self.longest_snake = max(self.longest_snake, len(game.snake))
        if game.score >= 100 and "CENTURY" not in self.achievements:
            self.achievements.append("CENTURY")
        if game.level >= 3 and "LEVEL_3" not in self.achievements:
            self.achievements.append("LEVEL_3")
        if game.state.name == "WON" and "FULL_BOARD" not in self.achievements:
            self.achievements.append("FULL_BOARD")

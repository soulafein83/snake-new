"""Tests for career statistics persistence."""

from __future__ import annotations

from pathlib import Path

from snake.core.game import Game, State
from snake.persistence import load_stats, save_stats
from snake.stats import Stats


def test_stats_roundtrip_and_fallback(tmp_path: Path) -> None:
    path = tmp_path / "stats.json"
    assert load_stats(path) == Stats()
    stats = Stats(games_played=3, total_score=250, best_level=4, longest_snake=12)
    assert save_stats(stats, path) is True
    assert load_stats(path) == stats

    path.write_text('{"games_played": -1, "achievements": "bad"}')
    assert load_stats(path) == Stats()


def test_stats_record_run() -> None:
    stats = Stats()
    game = Game(high_scores=[10])
    game.start()
    game.score = 120
    game.foods_eaten = 18
    game.state = State.GAME_OVER
    stats.record_run(game)
    assert stats.games_played == 1
    assert stats.total_score == 120
    assert stats.best_level == 3
    assert "CENTURY" in stats.achievements
    assert "LEVEL_3" in stats.achievements

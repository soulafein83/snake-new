"""Tests for settings persistence."""

from __future__ import annotations

from pathlib import Path

from snake.persistence import load_settings, save_settings
from snake.settings import Settings


def test_settings_defaults() -> None:
    assert Settings() == Settings(
        audio=True,
        reduced_motion=False,
        theme="classic",
        wrap_around=False,
    )


def test_settings_roundtrip_and_fallback(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    assert load_settings(path) == Settings()
    custom = Settings(audio=False, reduced_motion=True, theme="neon", wrap_around=True)
    assert save_settings(custom, path) is True
    assert load_settings(path) == custom

    path.write_text('{"audio": "yes", "theme": "unknown", "wrap_around": 1}')
    assert load_settings(path) == Settings()

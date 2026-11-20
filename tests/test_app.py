"""Integration tests for the application loop with a headless SDL driver."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from snake.app import Application  # noqa: E402
from snake.core.game import State  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_data(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("SNAKE_DATA_DIR", str(tmp_path))


def _post_key(key: int, mod: int = 0) -> None:
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod))


def _frames(app: Application, count: int, dt: float = 0.016) -> None:
    for _ in range(count):
        app.step(dt)


def test_app_starts_and_enters_playing() -> None:
    app = Application()
    assert app.running is True
    assert app.game.state is State.MENU

    _post_key(pygame.K_RETURN)
    _frames(app, 20)
    assert app.game.state is State.PLAYING


def test_app_pause_and_resume() -> None:
    app = Application()
    _post_key(pygame.K_RETURN)
    _frames(app, 20)
    assert app.game.state is State.PLAYING

    _post_key(pygame.K_p)
    _frames(app, 2)
    assert app.game.state is State.PAUSED

    _post_key(pygame.K_p)
    _frames(app, 2)
    assert app.game.state is State.PLAYING


def test_app_quit_via_key() -> None:
    app = Application()
    _post_key(pygame.K_q)
    _frames(app, 20)
    assert app.running is False

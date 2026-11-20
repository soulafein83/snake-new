"""Tests for persistence, transitions, input mapping and menu model."""

from __future__ import annotations

import json
from pathlib import Path

import pygame

from snake.core.game import State
from snake.input import Intent, map_event
from snake.menu import MenuAction, MenuModel, MenuScreen
from snake.persistence import load_high_score, save_high_score
from snake.ui import Transition


def test_persistence_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "hs.json"
    assert load_high_score(path) == 0
    assert save_high_score(42, path) is True
    assert load_high_score(path) == 42
    data = json.loads(path.read_text())
    assert data["high_score"] == 42


def test_persistence_guards() -> None:
    import tempfile

    d = Path(tempfile.mkdtemp())
    path = d / "hs.json"
    path.write_text("{bad json")
    assert load_high_score(path) == 0
    path.write_text(json.dumps({"high_score": True}))
    assert load_high_score(path) == 0
    path.write_text(json.dumps({"high_score": -5}))
    assert load_high_score(path) == 0
    assert save_high_score(True, path) is False  # type: ignore[arg-type]
    assert save_high_score(-1, path) is False


def test_transition_midpoint_callback() -> None:
    t = Transition(duration=0.16)
    called = {"n": 0}

    def cb() -> None:
        called["n"] += 1

    t.start(cb)
    assert t.blocks_input is True
    t.update(0.08)  # half
    assert called["n"] == 1
    t.update(0.08)
    assert t.active is False
    assert t.alpha == 0
    # second start while active ignored
    t2 = Transition(duration=0.16)
    t2.start()
    t2.start(lambda: None)
    assert t2.active is True


def test_input_mapping_playing() -> None:
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, mod=0)
    assert map_event(ev, State.PLAYING) is Intent.TURN_UP
    ev2 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p, mod=pygame.KMOD_SHIFT)
    assert map_event(ev2, State.PLAYING) is None


def test_top_scores_roundtrip(tmp_path: Path) -> None:
    from snake.persistence import load_high_scores, save_high_scores

    path = tmp_path / "hs.json"
    assert load_high_scores(path) == []
    assert save_high_scores([10, 30, 20, 30], path) is True
    assert load_high_scores(path) == [30, 30, 20, 10]
    # legacy single-score file migrates
    path2 = tmp_path / "legacy.json"
    path2.write_text(__import__("json").dumps({"version": 1, "high_score": 7}))
    assert load_high_scores(path2) == [7]


def test_gamepad_mapping() -> None:
    b0 = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    assert map_event(b0, State.MENU) is Intent.CONFIRM
    hat = pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    assert map_event(hat, State.PLAYING) is Intent.TURN_DOWN
    axis = pygame.event.Event(pygame.JOYAXISMOTION, axis=0, value=-0.8)
    assert map_event(axis, State.PLAYING) is Intent.TURN_LEFT


def test_menu_model_navigation() -> None:
    m = MenuModel()
    assert m.screen is MenuScreen.MAIN
    m.move(1)
    assert m.selected == 1
    m.move(10)
    assert 0 <= m.selected < len(m.items)
    assert m.activate() in {
        MenuAction.PLAY,
        MenuAction.RESUME_GAME,
        MenuAction.OPEN_HELP,
        MenuAction.QUIT,
    }

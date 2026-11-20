"""Map raw pygame events to high-level intents, depending on game state."""

from __future__ import annotations

from enum import Enum

import pygame

from snake.core.direction import Direction
from snake.core.game import State


class Intent(Enum):
    TURN_UP = "turn_up"
    TURN_DOWN = "turn_down"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    MENU_UP = "menu_up"
    MENU_DOWN = "menu_down"
    CONFIRM = "confirm"
    BACK = "back"
    TOGGLE_PAUSE = "toggle_pause"
    RESTART = "restart"
    MENU = "menu"
    QUIT = "quit"


_UP_KEYS = {pygame.K_UP, pygame.K_w}
_DOWN_KEYS = {pygame.K_DOWN, pygame.K_s}
_LEFT_KEYS = {pygame.K_LEFT, pygame.K_a}
_RIGHT_KEYS = {pygame.K_RIGHT, pygame.K_d}
_CONFIRM_KEYS = {pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_KP_5, pygame.K_SPACE}
_PAUSE_KEYS = {pygame.K_ESCAPE, pygame.K_p}
_RESTART_KEYS = {pygame.K_r}
_MENU_KEYS = {pygame.K_m}
_QUIT_KEYS = {pygame.K_q}


def _map_joy_direction(x: int, y: int, state: State) -> Intent | None:
    if state is State.PLAYING:
        if y < 0:
            return Intent.TURN_UP
        if y > 0:
            return Intent.TURN_DOWN
        if x < 0:
            return Intent.TURN_LEFT
        if x > 0:
            return Intent.TURN_RIGHT
        return None
    if y < 0:
        return Intent.MENU_UP
    if y > 0:
        return Intent.MENU_DOWN
    return None


def _map_joy_button(button: int, state: State) -> Intent | None:
    if button == 0:
        return Intent.CONFIRM
    if button == 1:
        if state is State.PLAYING:
            return Intent.TOGGLE_PAUSE
        return Intent.BACK
    if button == 2 and state in (State.PAUSED, State.GAME_OVER, State.WON):
        return Intent.RESTART
    if button == 3:
        return Intent.QUIT
    return None


def map_event(event: pygame.event.Event, state: State) -> Intent | None:
    # ``pygame.QUIT`` window events are handled directly by
    # ``Application._process_events`` before any event reaches ``map_event``;
    # only ``K_q`` produces ``Intent.QUIT`` here.
    if event.type == pygame.JOYBUTTONDOWN:
        return _map_joy_button(event.button, state)

    if event.type == pygame.JOYHATMOTION:
        x, y = event.value
        return _map_joy_direction(x, y, state)

    if event.type == pygame.JOYAXISMOTION:
        if abs(event.value) < 0.5:
            return None
        direction = 1 if event.value > 0 else -1
        if event.axis % 2 == 0:
            return _map_joy_direction(direction, 0, state)
        return _map_joy_direction(0, direction, state)
    if event.type != pygame.KEYDOWN:
        return None
    key = event.key

    # Modifier policy (enforced in this one place): only bare keys are
    # mapped, so OS shortcuts like Shift+Q / Ctrl+P never trigger actions.
    # CapsLock/NumLock are intentionally not blocked: they do not form OS
    # shortcuts, and gameplay keys must keep working with CapsLock on.
    if event.mod & (pygame.KMOD_SHIFT | pygame.KMOD_CTRL | pygame.KMOD_ALT):
        return None

    if state is State.PLAYING:
        if key in _UP_KEYS:
            return Intent.TURN_UP
        if key in _DOWN_KEYS:
            return Intent.TURN_DOWN
        if key in _LEFT_KEYS:
            return Intent.TURN_LEFT
        if key in _RIGHT_KEYS:
            return Intent.TURN_RIGHT
        if key in _PAUSE_KEYS:
            return Intent.TOGGLE_PAUSE
        return None

    if state is State.PAUSED:
        if key in _UP_KEYS:
            return Intent.MENU_UP
        if key in _DOWN_KEYS:
            return Intent.MENU_DOWN
        if key in _CONFIRM_KEYS:
            return Intent.CONFIRM
        if key in _PAUSE_KEYS:
            return Intent.TOGGLE_PAUSE
        if key in _RESTART_KEYS:
            return Intent.RESTART
        if key in _MENU_KEYS:
            return Intent.MENU
        if key in _QUIT_KEYS:
            return Intent.QUIT
        return None

    if state is State.MENU:
        if key in _UP_KEYS:
            return Intent.MENU_UP
        if key in _DOWN_KEYS:
            return Intent.MENU_DOWN
        if key in _CONFIRM_KEYS:
            return Intent.CONFIRM
        if key == pygame.K_ESCAPE:
            return Intent.BACK
        if key in _QUIT_KEYS:
            return Intent.QUIT
        return None

    if state in (State.GAME_OVER, State.WON):
        if key in _UP_KEYS:
            return Intent.MENU_UP
        if key in _DOWN_KEYS:
            return Intent.MENU_DOWN
        if key in _CONFIRM_KEYS:
            return Intent.CONFIRM
        if key in _RESTART_KEYS:
            return Intent.RESTART
        if key in _MENU_KEYS or key == pygame.K_ESCAPE:
            return Intent.MENU
        if key in _QUIT_KEYS:
            return Intent.QUIT
        return None

    return None


def direction_for(intent: Intent) -> Direction | None:
    return {
        Intent.TURN_UP: Direction.UP,
        Intent.TURN_DOWN: Direction.DOWN,
        Intent.TURN_LEFT: Direction.LEFT,
        Intent.TURN_RIGHT: Direction.RIGHT,
    }.get(intent)

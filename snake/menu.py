"""Menu model: pure UI state, independent of pygame and of the game core."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from snake.config import FOCUS_EASE, PANEL_ANIM_S


class MenuScreen(Enum):
    MAIN = "main"
    HELP = "help"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    WON = "won"
    DIFFICULTY = "difficulty"
    SCORES = "scores"


class MenuAction(Enum):
    NONE = "none"
    PLAY = "play"
    RESUME_GAME = "resume_game"
    RESUME = "resume"
    RESTART = "restart"
    MAIN_MENU = "main_menu"
    QUIT = "quit"
    OPEN_HELP = "open_help"
    CLOSE_HELP = "close_help"
    OPEN_DIFFICULTY = "open_difficulty"
    CLOSE_DIFFICULTY = "close_difficulty"
    SELECT_DIFFICULTY = "select_difficulty"
    OPEN_SCORES = "open_scores"
    CLOSE_SCORES = "close_scores"


@dataclass(frozen=True, slots=True)
class MenuItem:
    label: str
    action: MenuAction
    hint: str | None = None


# Single source of truth for the menu buttons. Both MenuModel and the
# renderer derive per-screen item counts from this mapping, so adding or
# removing an item here cannot desync rendering or mouse hit-testing.
ITEMS: dict[MenuScreen, tuple[MenuItem, ...]] = {
    MenuScreen.MAIN: (
        MenuItem("Play", MenuAction.PLAY, "Enter"),
        MenuItem("Resume", MenuAction.RESUME_GAME, "Enter"),
        MenuItem("Scores", MenuAction.OPEN_SCORES, "Enter"),
        MenuItem("Difficulty", MenuAction.OPEN_DIFFICULTY, "Enter"),
        MenuItem("How to Play", MenuAction.OPEN_HELP, "Enter"),
        MenuItem("Quit", MenuAction.QUIT, "Esc"),
    ),
    MenuScreen.HELP: (MenuItem("Back", MenuAction.CLOSE_HELP, "Esc"),),
    MenuScreen.DIFFICULTY: (
        MenuItem("Easy", MenuAction.SELECT_DIFFICULTY, "Enter"),
        MenuItem("Normal", MenuAction.SELECT_DIFFICULTY, "Enter"),
        MenuItem("Hard", MenuAction.SELECT_DIFFICULTY, "Enter"),
        MenuItem("Back", MenuAction.CLOSE_DIFFICULTY, "Esc"),
    ),
    MenuScreen.SCORES: (MenuItem("Back", MenuAction.CLOSE_SCORES, "Esc"),),
    MenuScreen.PAUSE: (
        MenuItem("Resume", MenuAction.RESUME, "Esc"),
        MenuItem("Restart", MenuAction.RESTART, "R"),
        MenuItem("Main Menu", MenuAction.MAIN_MENU, "M"),
        MenuItem("Quit", MenuAction.QUIT, "Q"),
    ),
    MenuScreen.GAME_OVER: (
        MenuItem("Play Again", MenuAction.PLAY, "R"),
        MenuItem("Main Menu", MenuAction.MAIN_MENU, "M"),
        MenuItem("Quit", MenuAction.QUIT, "Q"),
    ),
    MenuScreen.WON: (
        MenuItem("Play Again", MenuAction.PLAY, "R"),
        MenuItem("Main Menu", MenuAction.MAIN_MENU, "M"),
        MenuItem("Quit", MenuAction.QUIT, "Q"),
    ),
}


class MenuModel:
    def __init__(self) -> None:
        self.time = 0.0
        self.screen = MenuScreen.MAIN
        self.items: list[MenuItem] = []
        self.selected = 0
        self.focus_t: list[float] = []
        self.open_t = 0.0
        self.set_screen(MenuScreen.MAIN)

    # --- Screens -----------------------------------------------------------
    def set_screen(self, screen: MenuScreen) -> None:
        self.screen = screen
        self.items = list(ITEMS[screen])
        self.selected = 0
        self.focus_t = [0.0 for _ in self.items]
        self.open_t = 0.0

    @property
    def current(self) -> MenuItem:
        return self.items[self.selected]

    # --- Navigation --------------------------------------------------------
    def move(self, delta: int) -> None:
        if not self.items:
            return
        self.selected = (self.selected + delta) % len(self.items)

    def activate(self) -> MenuAction:
        # ``move`` already guards an empty item list; ``activate`` must too,
        # or a screen with zero items would raise IndexError on confirm.
        if not self.items:
            return MenuAction.NONE
        return self.items[self.selected].action

    def back(self) -> MenuAction:
        if self.screen is MenuScreen.HELP:
            return MenuAction.CLOSE_HELP
        if self.screen is MenuScreen.DIFFICULTY:
            return MenuAction.CLOSE_DIFFICULTY
        if self.screen is MenuScreen.SCORES:
            return MenuAction.CLOSE_SCORES
        if self.screen is MenuScreen.PAUSE:
            return MenuAction.RESUME
        if self.screen in (MenuScreen.GAME_OVER, MenuScreen.WON):
            return MenuAction.MAIN_MENU
        return MenuAction.QUIT

    # --- Animation ---------------------------------------------------------
    def update(self, dt: float) -> None:
        dt = max(0.0, min(dt, 0.25))
        self.time += dt
        self.open_t = min(1.0, self.open_t + dt / PANEL_ANIM_S)
        step = min(1.0, dt * FOCUS_EASE)
        for index, value in enumerate(self.focus_t):
            target = 1.0 if index == self.selected else 0.0
            self.focus_t[index] = value + (target - value) * step

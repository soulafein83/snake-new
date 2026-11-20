"""Application shell: pygame lifecycle, fixed-timestep loop and menu wiring."""

from __future__ import annotations

import contextlib

import pygame

from snake.assets import Assets, Audio
from snake.config import (
    AUDIO_ENABLED,
    COLOR_BG,
    COLOR_SNAKE,
    DIFFICULTIES,
    DIFFICULTY_BASE_STEP,
    DIFFICULTY_OBSTACLES,
    FPS,
    MAX_CATCHUP_STEPS,
    MAX_DT,
    MOUSE_MENUS,
    WINDOW_H,
    WINDOW_W,
)
from snake.core.game import Game, State
from snake.input import Intent, direction_for, map_event
from snake.menu import MenuAction, MenuModel, MenuScreen
from snake.persistence import (
    delete_save,
    load_game,
    load_high_scores,
    load_settings,
    save_game,
    save_high_scores,
    save_settings,
)
from snake.render import Renderer
from snake.ui import Transition

# Max keyboard intents kept while a fade is running (oldest dropped on
# overflow); replayed in order once the fade ends.
PENDING_INTENT_LIMIT = 8
POWERUP_DIFFICULTIES = frozenset({"Normal", "Hard"})


class Application:
    def __init__(self) -> None:
        # Headless / no-audio environments: pygame.init may raise SystemExit
        # (or any error) when the mixer fails; swallow it and let the later
        # display setup surface a graceful pygame.error if that fails too.
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
            pygame.init()
            pygame.joystick.init()
        except (Exception, SystemExit):  # noqa: BLE001, S110 - audio is strictly optional
            pass
        pygame.display.set_caption("Snake — Classic")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self._set_icon()
        self.settings = load_settings()
        self.assets = Assets()
        self.renderer = Renderer(self.screen, self.assets, self.settings)
        self.audio = Audio(enabled=AUDIO_ENABLED and self.settings.audio)
        self.clock = pygame.time.Clock()

        self.difficulty = "Normal"
        self.game = Game(
            high_scores=load_high_scores(),
            base_step=DIFFICULTY_BASE_STEP[self.difficulty],
            difficulty=self.difficulty,
            obstacles=DIFFICULTY_OBSTACLES[self.difficulty],
            wrap_around=self.settings.wrap_around,
            powerups_enabled=self.difficulty in POWERUP_DIFFICULTIES,
        )
        saved = load_game()
        if saved is not None:
            restored = Game.from_save(saved)
            if restored is not None:
                self.game = restored
                self.difficulty = self.game.difficulty

        self.menu = MenuModel(self.settings)
        self.transition = Transition()
        self.accumulator = 0.0
        self._pending_intents: list[Intent] = []
        self.running = True
        self._hand_cursor = False

    @staticmethod
    def _set_icon() -> None:
        icon = pygame.Surface((32, 32))
        icon.fill(COLOR_BG)
        pygame.draw.rect(icon, COLOR_SNAKE, (5, 5, 22, 22), border_radius=7)
        pygame.draw.circle(icon, (18, 34, 26), (12, 12), 2)
        pygame.draw.circle(icon, (18, 34, 26), (20, 12), 2)
        pygame.display.set_icon(icon)

    # ------------------------------------------------------------------ loop
    def run(self) -> int:
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_DT)
            self.step(dt)
            if self.running:
                pygame.display.flip()

        save_high_scores(self.game.high_scores)
        pygame.quit()
        return 0

    def step(self, dt: float) -> None:
        """One frame: events, animation, simulation, render. Used by tests too."""
        dt = min(dt, MAX_DT)
        self._process_events()
        if not self.running:
            return

        self.transition.update(dt)
        if not self.transition.active and self._pending_intents:
            # Fade just ended: replay the intents buffered while it ran.
            pending, self._pending_intents = self._pending_intents, []
            for intent in pending:
                self._handle_intent(intent)
        if not self.running:
            return

        if self.game.state is State.PLAYING and not self.transition.blocks_input:
            self._advance(dt)

        self.menu.update(dt)
        if self.game.state is State.PLAYING:
            alpha = self.accumulator / self.game.step_interval
        else:
            alpha = 1.0

        self.renderer.draw(self.game, self.menu, alpha, self.transition)

    def _advance(self, dt: float) -> None:
        self.accumulator += dt
        steps = 0
        while self.accumulator >= self.game.step_interval and steps < MAX_CATCHUP_STEPS:
            self.accumulator -= self.game.step_interval
            before = self.game.score
            self.game.tick()
            steps += 1

            if self.game.score != before:
                self.audio.play("eat")
                self.renderer.burst(self.game.snake.head, self.renderer.c("COLOR_FOOD"))

            if self.game.state is not State.PLAYING:
                self.accumulator = 0.0
                self._on_run_finished()
                break

        if steps >= MAX_CATCHUP_STEPS:
            # Drop only the overflow past the catch-up budget so the leftover
            # time is simulated on later frames instead of being discarded
            # (which would make the snake jump ahead after a lag spike).
            self.accumulator = min(self.accumulator, MAX_CATCHUP_STEPS * self.game.step_interval)

    def _on_run_finished(self) -> None:
        self.renderer.end_burst(self.game)
        if self.game.state is State.WON:
            self.menu.set_screen(MenuScreen.WON)
            self.audio.play("win")
        else:
            self.menu.set_screen(MenuScreen.GAME_OVER)
            self.audio.play("over")
        save_high_scores(self.game.high_scores)
        delete_save()
        self._update_cursor(False)

    # ---------------------------------------------------------------- events
    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit_now()
                return

            if self.transition.blocks_input:
                # Mouse feedback mid-fade is irrelevant: drop it. Keyboard
                # intents are buffered and replayed once the fade ends, so
                # rapid key presses (e.g. mashing R on game-over) are kept.
                if event.type == pygame.KEYDOWN:
                    intent = map_event(event, self.game.state)
                    if intent is not None:
                        if len(self._pending_intents) >= PENDING_INTENT_LIMIT:
                            self._pending_intents.pop(0)
                        self._pending_intents.append(intent)
                continue

            if MOUSE_MENUS and self._menu_visible() and event.type == pygame.MOUSEMOTION:
                self._on_mouse_motion(event.pos)
                continue

            if (
                MOUSE_MENUS
                and self._menu_visible()
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                self._on_mouse_click(event.pos)
                continue

            intent = map_event(event, self.game.state)
            if intent is not None:
                self._handle_intent(intent)

    def _handle_intent(self, intent: Intent) -> None:
        direction = direction_for(intent)
        if direction is not None:
            # No cursor handling here: every transition into PLAYING already
            # resets the cursor, so the old on-accepted-turn reset was dead.
            self.game.turn(direction)
            return

        if intent is Intent.MENU_UP:
            self.menu.move(-1)
            self.audio.play("hover")
        elif intent is Intent.MENU_DOWN:
            self.menu.move(1)
            self.audio.play("hover")
        elif intent is Intent.CONFIRM:
            self._activate_menu()
        elif intent is Intent.BACK:
            self._handle_action(self.menu.back())
        elif intent is Intent.TOGGLE_PAUSE:
            self._toggle_pause()
        elif intent is Intent.RESTART:
            self._begin_restart()
        elif intent is Intent.MENU:
            self._begin_main_menu()
        elif intent is Intent.QUIT:
            self._begin_quit()

    def _activate_menu(self) -> None:
        self.audio.play("confirm")
        self._handle_action(self.menu.activate())

    def _handle_action(self, action: MenuAction) -> None:
        if action is MenuAction.PLAY:
            self._update_cursor(False)
            delete_save()
            self.transition.start(self.game.start)
        elif action is MenuAction.RESUME_GAME:
            saved = load_game()
            if saved is not None:
                restored = Game.from_save(saved)
                if restored is not None:
                    self.game = restored
                    self.difficulty = self.game.difficulty
                    self.accumulator = 0.0
                    self.menu.set_screen(MenuScreen.MAIN)
                    self._update_cursor(False)
        elif action is MenuAction.RESUME:
            self._resume()
        elif action is MenuAction.RESTART:
            self._begin_restart()
        elif action is MenuAction.MAIN_MENU:
            self._begin_main_menu()
        elif action is MenuAction.QUIT:
            self._begin_quit()
        elif action is MenuAction.OPEN_HELP:
            self.menu.set_screen(MenuScreen.HELP)
        elif action is MenuAction.CLOSE_HELP:
            self.menu.set_screen(MenuScreen.MAIN)
        elif action is MenuAction.OPEN_DIFFICULTY:
            self.menu.set_screen(MenuScreen.DIFFICULTY)
        elif action is MenuAction.CLOSE_DIFFICULTY:
            self.menu.set_screen(MenuScreen.MAIN)
        elif action is MenuAction.OPEN_SCORES:
            self.menu.set_screen(MenuScreen.SCORES)
        elif action is MenuAction.CLOSE_SCORES:
            self.menu.set_screen(MenuScreen.MAIN)
        elif action is MenuAction.OPEN_SETTINGS:
            self.menu.set_screen(MenuScreen.SETTINGS)
        elif action is MenuAction.CLOSE_SETTINGS:
            self.menu.set_screen(MenuScreen.MAIN)
        elif action is MenuAction.SETTING_AUDIO:
            self._toggle_setting("audio")
        elif action is MenuAction.SETTING_REDUCED_MOTION:
            self._toggle_setting("reduced_motion")
        elif action is MenuAction.SETTING_WRAP_AROUND:
            self._toggle_setting("wrap_around")
        elif action is MenuAction.SETTING_THEME:
            self.settings = self.settings.updated(
                theme={
                    "classic": "neon",
                    "neon": "retro",
                    "retro": "classic",
                }.get(self.settings.theme, "classic")
            )
            self._commit_settings()
        elif action is MenuAction.SELECT_DIFFICULTY:
            index = self.menu.selected
            if 0 <= index < len(DIFFICULTIES):
                self.difficulty = DIFFICULTIES[index]
                self.game = Game(
                    high_scores=self.game.high_scores,
                    base_step=DIFFICULTY_BASE_STEP[self.difficulty],
                    difficulty=self.difficulty,
                    obstacles=DIFFICULTY_OBSTACLES[self.difficulty],
                    wrap_around=self.settings.wrap_around,
                    powerups_enabled=self.difficulty in POWERUP_DIFFICULTIES,
                )
            self.menu.set_screen(MenuScreen.MAIN)

    def _toggle_setting(self, name: str) -> None:
        self.settings = self.settings.updated(**{name: not getattr(self.settings, name)})
        self._commit_settings()

    def _commit_settings(self) -> None:
        save_settings(self.settings)
        self.menu.settings = self.settings
        self.renderer.settings = self.settings
        self.renderer.apply_theme(self.settings.theme)
        self.renderer.refresh_theme_surfaces()
        self.audio.enabled = AUDIO_ENABLED and self.settings.audio
        self.game.wrap_around = self.settings.wrap_around
        self.menu.set_screen(MenuScreen.SETTINGS)

    def _toggle_pause(self) -> None:
        if self.game.state is State.PLAYING:
            self.game.pause()
            self.accumulator = 0.0
            save_game(self.game.to_save_dict())
            self.menu.set_screen(MenuScreen.PAUSE)
            self.audio.play("confirm")
            self._update_cursor(False)
        elif self.game.state is State.PAUSED:
            self._resume()

    def _resume(self) -> None:
        if self.game.state is not State.PAUSED:
            return
        self.game.resume()
        self.game.snap_interpolation()
        self.accumulator = 0.0
        self._update_cursor(False)

    def _begin_restart(self) -> None:
        if self.transition.active:
            return
        delete_save()
        self.transition.start(self.game.restart)
        self.accumulator = 0.0
        self._update_cursor(False)

    def _begin_main_menu(self) -> None:
        if self.transition.active:
            return
        if self.game.state in (State.PLAYING, State.PAUSED):
            if self.game.state is State.PLAYING:
                self.game.pause()
            save_game(self.game.to_save_dict())

        def go_to_menu() -> None:
            self.game.to_menu()
            self.menu.set_screen(MenuScreen.MAIN)

        self.transition.start(go_to_menu)
        self.accumulator = 0.0
        self._update_cursor(False)

    def _begin_quit(self) -> None:
        if self.transition.active:
            return
        if self.game.state in (State.PLAYING, State.PAUSED):
            if self.game.state is State.PLAYING:
                self.game.pause()
            save_game(self.game.to_save_dict())
        self.transition.start(self._quit_now)

    def _quit_now(self) -> None:
        if self.game.state in (State.PLAYING, State.PAUSED):
            if self.game.state is State.PLAYING:
                self.game.pause()
            save_game(self.game.to_save_dict())
        save_high_scores(self.game.high_scores)
        self.running = False

    # ----------------------------------------------------------------- mouse
    def _menu_visible(self) -> bool:
        return self.game.state in (
            State.MENU,
            State.PAUSED,
            State.GAME_OVER,
            State.WON,
        )

    def _button_at(self, pos: tuple[int, int]) -> int | None:
        for index, rect in enumerate(self.renderer.menu_button_rects(self.menu.screen, self.menu)):
            if rect.collidepoint(pos):
                return index
        return None

    def _on_mouse_motion(self, pos: tuple[int, int]) -> None:
        index = self._button_at(pos)
        self._update_cursor(index is not None)
        if index is not None and index != self.menu.selected:
            self.menu.selected = index
            self.audio.play("hover")

    def _on_mouse_click(self, pos: tuple[int, int]) -> None:
        index = self._button_at(pos)
        if index is None:
            return
        self.menu.selected = index
        self._activate_menu()

    def _update_cursor(self, hand: bool) -> None:
        if hand == self._hand_cursor:
            return
        self._hand_cursor = hand
        with contextlib.suppress(pygame.error):
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW
            )


def main() -> int:
    try:
        app = Application()
    except pygame.error as exc:
        print(f"Could not start Snake: {exc}")
        return 1
    return app.run()

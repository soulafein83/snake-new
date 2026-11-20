"""Core game state machine, scoring and speed curve."""

from __future__ import annotations

import random
from collections import deque
from enum import Enum

from snake.config import (
    BASE_STEP,
    COLS,
    MIN_STEP,
    ROWS,
    SCORE_PER_FOOD,
    SPEED_STEP,
    TURN_QUEUE_MAX,
)
from snake.core.direction import Direction
from snake.core.food import Food
from snake.core.powerup import PowerUp, PowerUpType
from snake.core.snake import Cell, Snake


class State(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    WON = "won"
    QUIT = "quit"


class Game:
    """Owns all mutable gameplay state.

    ``tick()`` is the only method that mutates the board during a run.
    """

    def __init__(
        self,
        high_score: int = 0,
        rng: random.Random | None = None,
        seed: int | None = None,
        high_scores: list[int] | None = None,
        base_step: float | None = None,
        difficulty: str = "Normal",
        obstacles: int = 0,
        wrap_around: bool = False,
        powerups_enabled: bool = False,
    ) -> None:
        if high_scores is None:
            high_scores = [high_score] if high_score and high_score > 0 else []
        valid = [
            s for s in high_scores if isinstance(s, int) and not isinstance(s, bool) and s >= 0
        ]
        valid.sort(reverse=True)
        self._high_scores: list[int] = valid[:5]
        self.base_step = base_step if base_step is not None else BASE_STEP
        self.difficulty = difficulty
        self.obstacle_count = max(0, int(obstacles))
        self.wrap_around = bool(wrap_around)
        self.powerups_enabled = bool(powerups_enabled)
        self.powerup: PowerUp | None = None
        self.active_effects: dict[str, int] = {"slow": 0, "shield": 0}
        self._power_rng = random.Random()
        self._rng = rng if rng is not None else random.Random(seed)
        self.obstacles: set[Cell] = set()
        self.state = State.MENU
        self._reset_run()

    @property
    def level(self) -> int:
        return 1 + self.foods_eaten // 8

    @property
    def high_score(self) -> int:
        return self._high_scores[0] if self._high_scores else 0

    @high_score.setter
    def high_score(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return
        self._high_scores = sorted(self._high_scores + [value], reverse=True)[:5]
        # keep only if new best? Actually high_score setter used by _finish; handle there.

    @property
    def high_scores(self) -> list[int]:
        return list(self._high_scores)

    @high_scores.setter
    def high_scores(self, value: list[int]) -> None:
        valid = [s for s in value if isinstance(s, int) and not isinstance(s, bool) and s >= 0]
        valid.sort(reverse=True)
        self._high_scores = valid[:5]

    def to_save_dict(self) -> dict:
        return {
            "version": 1,
            "difficulty": self.difficulty,
            "base_step": self.base_step,
            "obstacle_count": self.obstacle_count,
            "wrap_around": self.wrap_around,
            "powerups_enabled": self.powerups_enabled,
            "powerup": self.powerup.to_dict() if self.powerup else None,
            "active_effects": dict(self.active_effects),
            "score": self.score,
            "foods_eaten": self.foods_eaten,
            "step_interval": self.step_interval,
            "state": self.state.value,
            "snake_cells": list(self.snake.body),
            "snake_direction": self.snake.direction.name,
            "pending": [d.name for d in self.snake.pending],
            "food": self.food.position,
            "high_scores": self.high_scores,
            "obstacles": [list(c) for c in self.obstacles],
        }

    @classmethod
    def from_save(cls, data: dict) -> Game | None:
        if not isinstance(data, dict):
            return None
        try:
            difficulty = str(data.get("difficulty", "Normal"))
            base_step = float(data.get("base_step", BASE_STEP))
            high_scores = data.get("high_scores", [])
            if not isinstance(high_scores, list):
                high_scores = []
            game = cls(
                high_scores=high_scores,
                base_step=base_step,
                difficulty=difficulty,
                obstacles=int(data.get("obstacle_count", 0)),
                wrap_around=bool(data.get("wrap_around", False)),
                powerups_enabled=bool(data.get("powerups_enabled", False)),
            )
            game.score = int(data.get("score", 0))
            game.foods_eaten = int(data.get("foods_eaten", 0))
            game.step_interval = float(data.get("step_interval", game.base_step))
            cells = data.get("snake_cells")
            if not isinstance(cells, list) or not cells:
                return None
            cells = [tuple(c) for c in cells if isinstance(c, (list, tuple)) and len(c) == 2]
            if not cells:
                return None
            direction_name = data.get("snake_direction", "RIGHT")
            direction = Direction[direction_name]
            game.snake = Snake.from_cells(cells, direction)
            obstacle_cells = data.get("obstacles", [])
            if isinstance(obstacle_cells, list):
                game.obstacles = {
                    tuple(c) for c in obstacle_cells if isinstance(c, (list, tuple)) and len(c) == 2
                }
            pending_names = data.get("pending", [])
            if isinstance(pending_names, list):
                game.snake.pending = deque(
                    (Direction[n] for n in pending_names if n in Direction.__members__),
                    maxlen=TURN_QUEUE_MAX,
                )
            food = data.get("food")
            game.food.position = (
                tuple(food) if isinstance(food, (list, tuple)) and len(food) == 2 else None
            )
            effects = data.get("active_effects", {})
            if isinstance(effects, dict):
                game.active_effects = {
                    "slow": max(0, int(effects.get("slow", 0))),
                    "shield": max(0, int(effects.get("shield", 0))),
                }
            game.powerup = PowerUp.from_dict(data.get("powerup"))
            state_value = data.get("state", State.PAUSED.value)
            try:
                game.state = State(state_value)
            except ValueError:
                game.state = State.PAUSED
            if game.state is State.PLAYING:
                game.state = State.PAUSED
            game.prev_body = list(game.snake.body)
            return game
        except (KeyError, ValueError, TypeError):
            return None

    # --- Setup / transitions ----------------------------------------------
    def _generate_obstacles(self, count: int) -> set[Cell]:
        if count <= 0:
            return set()
        free = [
            (x, y) for y in range(ROWS) for x in range(COLS) if (x, y) not in self.snake.occupied
        ]
        return set(self._rng.sample(free, min(count, len(free))))

    def _reset_run(self) -> None:
        self.powerup = None
        self.active_effects = {"slow": 0, "shield": 0}
        self.snake = Snake()
        self.obstacles = self._generate_obstacles(self.obstacle_count)
        self.food = Food(self._rng)
        self.food.spawn(self.snake.occupied | self.obstacles)
        self.score = 0
        self.foods_eaten = 0
        self.step_interval = self.base_step
        self.new_best = False
        self.prev_body = list(self.snake.body)

    def start(self) -> None:
        self._reset_run()
        self.state = State.PLAYING

    def restart(self) -> None:
        self.start()

    def pause(self) -> None:
        if self.state is State.PLAYING:
            self.state = State.PAUSED

    def resume(self) -> None:
        if self.state is State.PAUSED:
            self.state = State.PLAYING

    def toggle_pause(self) -> None:
        if self.state is State.PLAYING:
            self.pause()
        elif self.state is State.PAUSED:
            self.resume()

    def snap_interpolation(self) -> None:
        """Reset the render baseline so resuming never snaps a cell backwards."""
        self.prev_body = list(self.snake.body)

    def to_menu(self) -> None:
        self._reset_run()
        self.state = State.MENU

    def quit(self) -> None:
        self.state = State.QUIT

    # --- Input -------------------------------------------------------------
    def turn(self, direction: Direction) -> bool:
        if self.state is not State.PLAYING:
            return False
        return self.snake.request_turn(direction)

    # --- Simulation --------------------------------------------------------
    def _die_or_shield(self) -> State:
        if self.active_effects["shield"] > 0:
            self.active_effects["shield"] -= 1
            return self.state
        return self._finish(State.GAME_OVER)

    def _recalculate_step_interval(self) -> None:
        interval = max(MIN_STEP, round(self.base_step - SPEED_STEP * self.foods_eaten, 4))
        if self.active_effects["slow"] > 0:
            interval += 0.06
        self.step_interval = interval

    def _spawn_powerup(self) -> None:
        if not self.powerups_enabled or self.foods_eaten % 4 != 0:
            return
        if self.powerup is not None:
            return
        occupied = self.snake.occupied | self.obstacles
        if self.food.position is not None:
            occupied = occupied | {self.food.position}
        free = [(x, y) for y in range(ROWS) for x in range(COLS) if (x, y) not in occupied]
        if not free:
            return
        kind = self._power_rng.choice(list(PowerUpType))
        self.powerup = PowerUp(kind, self._power_rng.choice(free), 80)

    def _collect_powerup(self) -> None:
        if self.powerup is None:
            return
        kind = self.powerup.kind
        if kind is PowerUpType.SLOW:
            self.active_effects["slow"] = 60
            self._recalculate_step_interval()
        elif kind is PowerUpType.SHIELD:
            self.active_effects["shield"] += 1
        elif kind is PowerUpType.BONUS:
            self.score += 50
        self.powerup = None

    def tick(self) -> State:
        if self.state is not State.PLAYING:
            return self.state

        turn = self.snake.consume_turn()
        if turn is not None:
            self.snake.direction = turn

        if self.active_effects["slow"] > 0:
            self.active_effects["slow"] -= 1
            if self.active_effects["slow"] == 0:
                self._recalculate_step_interval()
        if self.powerup is not None:
            self.powerup = PowerUp(
                self.powerup.kind,
                self.powerup.position,
                self.powerup.ttl - 1,
            )
            if self.powerup.ttl <= 0:
                self.powerup = None

        self.prev_body = list(self.snake.body)
        new_head = self.snake.next_head()

        if self.powerup is not None and new_head == self.powerup.position:
            self._collect_powerup()

        if self.wrap_around:
            new_head = (new_head[0] % COLS, new_head[1] % ROWS)
        elif not self._inside(new_head):
            return self._die_or_shield()
        growing = new_head == self.food.position
        if new_head in self.obstacles:
            return self._die_or_shield()
        tail = self.snake.tail
        if new_head in self.snake.occupied and not (new_head == tail and not growing):
            return self._die_or_shield()
        self.snake.advance(grow=growing, target=new_head)

        if growing:
            previous_level = self.level
            self.score += SCORE_PER_FOOD
            self.foods_eaten += 1
            self._recalculate_step_interval()
            if self.level > previous_level and self.obstacle_count > 0:
                free = [
                    (x, y)
                    for y in range(ROWS)
                    for x in range(COLS)
                    if (x, y) not in self.snake.occupied | self.obstacles | {self.food.position}
                ]
                if free:
                    self.obstacles.add(self._power_rng.choice(free))
            self.food.spawn(self.snake.occupied | self.obstacles)
            if self.food.position is None:
                return self._finish(State.WON)
            self._spawn_powerup()

        return self.state

    def _finish(self, state: State) -> State:
        self.new_best = self.score > self.high_score
        if self.new_best:
            self.high_score = self.score
        self.state = state
        return state

    @staticmethod
    def _inside(cell: Cell) -> bool:
        return 0 <= cell[0] < COLS and 0 <= cell[1] < ROWS

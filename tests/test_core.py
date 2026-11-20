"""Tests for the pure game core (no pygame)."""

from __future__ import annotations

import random

from snake.config import COLS, ROWS
from snake.core.direction import Direction
from snake.core.food import Food
from snake.core.game import Game, State
from snake.core.snake import Snake


def test_snake_initial_invariants() -> None:
    snake = Snake()
    assert len(snake.body) == 3
    assert snake.occupied == set(snake.body)
    assert snake.is_consistent()


def test_snake_request_turn_rejects_reversal_and_duplicates() -> None:
    snake = Snake()
    assert snake.request_turn(Direction.RIGHT) is False  # duplicate of current
    assert snake.request_turn(Direction.LEFT) is False  # reversal
    assert snake.request_turn(Direction.UP) is True
    assert snake.request_turn(Direction.UP) is False  # duplicate queued
    assert (
        snake.request_turn(Direction.DOWN) is False
    )  # reversal of queued up? reference up, opposite down
    assert snake.request_turn(Direction.RIGHT) is True
    # queue full (max 2)
    assert snake.request_turn(Direction.UP) is False


def test_snake_advance_grow_and_shrink() -> None:
    snake = Snake(start=(5, 5), direction=Direction.RIGHT, length=2)
    tail_before = snake.tail
    new_head = snake.advance(grow=False)
    assert new_head == (6, 5)
    assert tail_before not in snake.occupied
    assert new_head in snake.occupied
    assert len(snake.body) == 2
    assert snake.is_consistent()

    snake2 = Snake(start=(5, 5), direction=Direction.RIGHT, length=2)
    snake2.advance(grow=True)
    assert len(snake2.body) == 3
    assert snake2.is_consistent()


def test_snake_from_cells() -> None:
    cells = [(0, 0), (1, 0), (2, 0)]
    snake = Snake.from_cells(cells, Direction.RIGHT)
    assert list(snake.body) == cells
    assert snake.is_consistent()


def test_direction_opposite() -> None:
    assert Direction.UP.opposite is Direction.DOWN
    assert Direction.LEFT.opposite is Direction.RIGHT


def test_food_spawn_full_board() -> None:
    food = Food(rng=random.Random(0))
    food.spawn(set((x, y) for y in range(ROWS) for x in range(COLS)))
    assert food.position is None


def test_food_spawn_free() -> None:
    food = Food(rng=random.Random(1))
    pos = food.spawn({(0, 0)})
    assert pos is not None
    assert pos != (0, 0)


def test_game_start_and_pause() -> None:
    game = Game()
    assert game.state is State.MENU
    game.start()
    assert game.state is State.PLAYING
    game.pause()
    assert game.state is State.PAUSED
    game.resume()
    assert game.state is State.PLAYING
    game.toggle_pause()
    assert game.state is State.PAUSED


def test_game_to_menu_resets() -> None:
    game = Game()
    game.start()
    game.turn(Direction.RIGHT)
    game.tick()
    game.to_menu()
    assert game.state is State.MENU
    assert game.score == 0


def test_game_wall_collision() -> None:
    game = Game()
    game.start()
    # force snake to left edge by setting direction left repeatedly until wall
    for _ in range(COLS + 5):
        game.turn(Direction.LEFT)
        game.tick()
        if game.state is not State.PLAYING:
            break
    assert game.state is State.GAME_OVER


def test_powerup_collection_and_shield() -> None:
    from snake.core.powerup import PowerUp, PowerUpType

    game = Game(powerups_enabled=True)
    game.start()
    game.snake = Snake.from_cells([(5, 5)], Direction.RIGHT)
    game.food.position = None
    game.powerup = PowerUp(PowerUpType.SLOW, (6, 5), 20)
    game.state = State.PLAYING
    game.tick()
    assert game.powerup is None
    assert game.active_effects["slow"] > 0

    game.snake = Snake.from_cells([(COLS - 1, 5)], Direction.RIGHT)
    game.active_effects["shield"] = 1
    game.tick()
    assert game.state is State.PLAYING
    assert game.active_effects["shield"] == 0


def test_wrap_around() -> None:
    game = Game(wrap_around=True)
    game.start()
    game.snake = Snake.from_cells([(0, 5)], Direction.LEFT)
    game.food.position = None
    game.state = State.PLAYING
    game.tick()
    assert game.state is State.PLAYING
    assert game.snake.head == (COLS - 1, 5)


def test_obstacles_block_movement() -> None:
    game = Game(obstacles=2, rng=random.Random(3))
    game.start()
    assert len(game.obstacles) == 2
    game.snake = Snake.from_cells([(0, 0)], Direction.RIGHT)
    game.obstacles = {(1, 0)}
    game.food.position = None
    game.state = State.PLAYING
    game.tick()
    assert game.state is State.GAME_OVER


def test_game_save_roundtrip() -> None:
    game = Game(high_scores=[5], base_step=0.12, difficulty="Hard")
    game.start()
    game.turn(Direction.RIGHT)
    game.tick()
    data = game.to_save_dict()
    restored = Game.from_save(data)
    assert restored is not None
    assert restored.score == game.score
    assert restored.difficulty == "Hard"
    assert list(restored.snake.body) == list(game.snake.body)
    assert restored.state in (State.PAUSED, State.PLAYING)


def test_game_win_on_full_board() -> None:
    game = Game(rng=random.Random(7))
    game.start()
    # Occupy every cell except (0, 0), which becomes the food.
    cells = [(x, y) for y in range(ROWS) for x in range(COLS) if (x, y) != (0, 0)]
    game.snake = Snake.from_cells(cells, Direction.RIGHT)
    # Make the head adjacent to the food so the next step eats it.
    # Move head cell to (COLS-1? no) - instead set body order: head at (1,0)?
    # We'll rebuild with head at (1,0) and keep uniqueness by removing (1,0) from tail list.
    cells = [(x, y) for y in range(ROWS) for x in range(COLS) if (x, y) not in ((0, 0), (1, 0))]
    cells = [(1, 0)] + cells
    game.snake = Snake.from_cells(cells, Direction.LEFT)
    game.food.position = (0, 0)
    game.state = State.PLAYING
    game.prev_body = list(game.snake.body)
    game.tick()
    assert game.state is State.WON

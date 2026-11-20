"""Single source of truth for tunable constants and the visual palette."""

from __future__ import annotations

from typing import Final

# --- Grid & window ---------------------------------------------------------
COLS: Final = 24
ROWS: Final = 20
CELL: Final = 30
HUD_H: Final = 80
WINDOW_W: Final = COLS * CELL  # 720
WINDOW_H: Final = HUD_H + ROWS * CELL  # 680
BOARD_TOP: Final = HUD_H

# --- Timing ----------------------------------------------------------------
FPS: Final = 60
BASE_STEP: Final = 0.140  # seconds per grid step at score 0
SPEED_STEP: Final = 0.004  # faster per food eaten
MIN_STEP: Final = 0.060  # speed cap
MAX_CATCHUP_STEPS: Final = 4
MAX_DT: Final = 0.25

# --- Rules -----------------------------------------------------------------
SCORE_PER_FOOD: Final = 10
START_LENGTH: Final = 3
TURN_QUEUE_MAX: Final = 2

# --- Difficulty ------------------------------------------------------------
DIFFICULTIES: Final = ("Easy", "Normal", "Hard")
DIFFICULTY_BASE_STEP: Final = {
    "Easy": 0.18,
    "Normal": BASE_STEP,
    "Hard": 0.10,
}
DIFFICULTY_OBSTACLES: Final = {
    "Easy": 0,
    "Normal": 0,
    "Hard": 8,
}
# --- Presentation ----------------------------------------------------------
SMOOTH_MOTION: Final = True
REDUCED_MOTION: Final = False
MOUSE_MENUS: Final = True
AUDIO_ENABLED: Final = True
TRANSITION_S: Final = 0.16
PANEL_ANIM_S: Final = 0.18
FOCUS_EASE: Final = 18.0
GHOST_SPEED: Final = 3.0  # cells per second in the main-menu backdrop

# --- Palette (RGB) ---------------------------------------------------------
COLOR_BG: Final = (15, 20, 25)
COLOR_GRID: Final = (38, 52, 64)
COLOR_GRID_FAINT: Final = (32, 44, 55)
COLOR_SNAKE: Final = (61, 220, 132)
COLOR_SNAKE_HEAD: Final = (124, 240, 172)
COLOR_SNAKE_TAIL: Final = (34, 150, 90)
COLOR_FOOD: Final = (255, 92, 92)
COLOR_FOOD_GLOW: Final = (255, 70, 70)
COLOR_ACCENT: Final = (85, 230, 193)
COLOR_PANEL: Final = (11, 16, 21)
COLOR_TEXT: Final = (230, 237, 243)
COLOR_MUTED: Final = (139, 148, 158)
COLOR_DANGER: Final = (255, 110, 110)
COLOR_OBSTACLE: Final = (110, 130, 150)
COLOR_BLACK: Final = (0, 0, 0)
COLOR_WHITE: Final = (255, 255, 255)

# --- Persistence -----------------------------------------------------------
APP_DIR_NAME: Final = "snake-new"
HIGHSCORE_FILENAME: Final = "highscore.json"
GAME_SAVE_FILENAME: Final = "savegame.json"
DATA_DIR_ENV: Final = "SNAKE_DATA_DIR"

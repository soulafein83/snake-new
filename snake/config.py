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
COLOR_POWERUP_SLOW: Final = (120, 190, 255)
COLOR_POWERUP_SHIELD: Final = (255, 215, 120)
COLOR_POWERUP_BONUS: Final = (220, 120, 255)
COLOR_BLACK: Final = (0, 0, 0)
COLOR_WHITE: Final = (255, 255, 255)

# --- Themes (overrides of the classic palette) -----------------------------
THEMES: Final = {
    "classic": {},
    "neon": {
        "COLOR_BG": (8, 6, 18),
        "COLOR_GRID": (80, 40, 140),
        "COLOR_GRID_FAINT": (40, 24, 72),
        "COLOR_SNAKE": (255, 80, 200),
        "COLOR_SNAKE_HEAD": (255, 180, 240),
        "COLOR_SNAKE_TAIL": (130, 40, 160),
        "COLOR_FOOD": (80, 255, 220),
        "COLOR_FOOD_GLOW": (60, 240, 200),
        "COLOR_ACCENT": (180, 120, 255),
        "COLOR_PANEL": (14, 8, 28),
        "COLOR_TEXT": (245, 235, 255),
        "COLOR_MUTED": (150, 120, 190),
        "COLOR_OBSTACLE": (110, 70, 160),
    },
    "retro": {
        "COLOR_BG": (18, 18, 12),
        "COLOR_GRID": (70, 70, 40),
        "COLOR_GRID_FAINT": (45, 45, 25),
        "COLOR_SNAKE": (180, 220, 60),
        "COLOR_SNAKE_HEAD": (230, 255, 120),
        "COLOR_SNAKE_TAIL": (90, 130, 30),
        "COLOR_FOOD": (230, 140, 50),
        "COLOR_FOOD_GLOW": (200, 110, 40),
        "COLOR_ACCENT": (220, 200, 80),
        "COLOR_PANEL": (20, 20, 12),
        "COLOR_TEXT": (235, 230, 180),
        "COLOR_MUTED": (150, 145, 100),
        "COLOR_OBSTACLE": (120, 110, 60),
    },
}
# --- Persistence -----------------------------------------------------------
APP_DIR_NAME: Final = "snake-new"
HIGHSCORE_FILENAME: Final = "highscore.json"
GAME_SAVE_FILENAME: Final = "savegame.json"
SETTINGS_FILENAME: Final = "settings.json"
DATA_DIR_ENV: Final = "SNAKE_DATA_DIR"

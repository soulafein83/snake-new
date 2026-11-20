"""High-score persistence with atomic writes and defensive reads."""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path

from snake.config import (
    APP_DIR_NAME,
    DATA_DIR_ENV,
    GAME_SAVE_FILENAME,
    HIGHSCORE_FILENAME,
)

SCHEMA_VERSION = 2
MAX_HIGH_SCORES = 5


def default_data_dir() -> Path:
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / APP_DIR_NAME


def highscore_path() -> Path:
    return default_data_dir() / HIGHSCORE_FILENAME


def _valid_score(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def load_high_scores(path: Path | str | None = None) -> list[int]:
    """Return a sorted (desc) list of up to MAX_HIGH_SCORES valid scores."""
    target = Path(path) if path is not None else highscore_path()
    try:
        raw = target.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError, TypeError):
        return []

    if not isinstance(data, dict):
        return []

    scores: list[int] = []
    if isinstance(data.get("high_scores"), list):
        for value in data["high_scores"]:
            if _valid_score(value):
                scores.append(value)
    elif _valid_score(data.get("high_score")):
        scores.append(data["high_score"])

    scores.sort(reverse=True)
    return scores[:MAX_HIGH_SCORES]


def load_high_score(path: Path | str | None = None) -> int:
    """Backwards-compatible single best score."""
    scores = load_high_scores(path)
    return scores[0] if scores else 0


def save_high_scores(scores: list[int], path: Path | str | None = None) -> bool:
    """Atomically persist the top scores. Returns False on failure."""
    valid = [s for s in scores if _valid_score(s)]
    valid.sort(reverse=True)
    valid = valid[:MAX_HIGH_SCORES]

    target = Path(path) if path is not None else highscore_path()
    tmp = target.with_name(target.name + ".tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(
            json.dumps(
                {
                    "version": SCHEMA_VERSION,
                    "high_score": valid[0] if valid else 0,
                    "high_scores": valid,
                }
            ),
            encoding="utf-8",
        )
        os.replace(tmp, target)
        return True
    except OSError:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        return False


def save_high_score(score: int, path: Path | str | None = None) -> bool:
    """Backwards-compatible single-score persist."""
    if not _valid_score(score):
        return False
    return save_high_scores([score], path)


def game_save_path() -> Path:
    return default_data_dir() / GAME_SAVE_FILENAME


def save_game(data: dict, path: Path | str | None = None) -> bool:
    target = Path(path) if path is not None else game_save_path()
    tmp = target.with_name(target.name + ".tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, target)
        return True
    except OSError:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        return False


def load_game(path: Path | str | None = None) -> dict | None:
    target = Path(path) if path is not None else game_save_path()
    try:
        raw = target.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def delete_save(path: Path | str | None = None) -> None:
    target = Path(path) if path is not None else game_save_path()
    with contextlib.suppress(OSError):
        target.unlink(missing_ok=True)
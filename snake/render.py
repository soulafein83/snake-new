"""All pygame drawing: playfield, HUD, animated menus and transitions."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from snake.assets import Assets
from snake.config import (
    BOARD_TOP,
    CELL,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_BLACK,
    COLOR_DANGER,
    COLOR_FOOD,
    COLOR_FOOD_GLOW,
    COLOR_GRID,
    COLOR_GRID_FAINT,
    COLOR_MUTED,
    COLOR_OBSTACLE,
    COLOR_PANEL,
    COLOR_SNAKE,
    COLOR_SNAKE_HEAD,
    COLOR_SNAKE_TAIL,
    COLOR_TEXT,
    COLOR_WHITE,
    COLS,
    GHOST_SPEED,
    HUD_H,
    REDUCED_MOTION,
    ROWS,
    SMOOTH_MOTION,
    WINDOW_H,
    WINDOW_W,
)
from snake.core.game import Game, State
from snake.menu import ITEMS, MenuModel, MenuScreen
from snake.ui import Transition, clamp, ease_out_cubic, lerp, lerp_color

BUTTON_W = 320
BUTTON_H = 54
BUTTON_GAP = 14
PANEL_W = 420
HELP_PANEL_W = 440
PANEL_RADIUS = 22
HEADER_H = 46
STATS_H = 74
HELP_H = 226
SCORES_H = 190
FOOTER_H = 30
PAD_TOP = 28
PAD_BOTTOM = 20
TITLE_Y = 84
# Bottom of the title block on MAIN (big title + the subtitle drawn at
# TITLE_Y + 96).
TITLE_BLOCK_BOTTOM = TITLE_Y + 124
# Anchor for the MAIN panel: below the title block.
MAIN_PANEL_Y = 300

_HEADERS = {
    MenuScreen.HELP: "HOW TO PLAY",
    MenuScreen.PAUSE: "PAUSED",
    MenuScreen.GAME_OVER: "GAME OVER",
    MenuScreen.WON: "YOU WIN",
    MenuScreen.DIFFICULTY: "DIFFICULTY",
    MenuScreen.SCORES: "TOP SCORES",
}


@dataclass(frozen=True)
class MenuLayout:
    panel: pygame.Rect
    buttons: tuple[pygame.Rect, ...]
    header_y: int
    stats_y: int
    help_y: int
    footer_y: int


class Renderer:
    def __init__(self, screen: pygame.Surface, assets: Assets) -> None:
        self.screen = screen
        self.assets = assets
        self.now = 0.0
        self.title_y = TITLE_Y

        self.font_title = assets.font(74, bold=True)
        self.font_header = assets.font(32, bold=True)
        self.font_button = assets.font(22, bold=True)
        self.font_body = assets.font(18, bold=True)
        self.font_small = assets.font(14, bold=True)
        self.font_tiny = assets.font(12)
        self.font_hud_label = assets.font(12, bold=True)
        self.font_hud_value = assets.font(28, bold=True)
        self.font_hud_hint = assets.font(14)

        self.board_bg = self._build_board_bg()
        self.hud_bg = self._build_hud_bg()
        self.menu_bg = self._build_menu_bg()
        self.vignette = self._build_vignette()
        self.food_glow = self._build_glow(48, COLOR_FOOD_GLOW)
        self.glow_green = self._build_glow(240, (30, 180, 120), 48)
        self.glow_teal = self._build_glow(280, (30, 120, 150), 34)
        self.fade_surface = pygame.Surface((WINDOW_W, WINDOW_H))
        self.fade_surface.fill(COLOR_BLACK)
        self.dim_surface = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        self.ghost_layer = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        self.ghost_path = self._build_ghost_path()

        self.title_letters = self._build_title()
        self.button_idle = self._build_button(False)
        self.button_focus = self._build_button(True)
        self.badge = self._build_badge()

        self.text_cache: dict[
            tuple[str, str, int, bool, bool, tuple[int, int, int]], pygame.Surface
        ] = {}
        self.menu_layouts = {
            screen_name: self._compute_layout(screen_name) for screen_name in MenuScreen
        }
        self.panel_surfaces = {
            screen_name: self._build_panel(
                layout.panel.width,
                layout.panel.height,
            )
            for screen_name, layout in self.menu_layouts.items()
        }

    # ------------------------------------------------------------------ draw
    def draw(
        self,
        game: Game,
        menu: MenuModel,
        alpha: float = 1.0,
        fade: Transition | None = None,
    ) -> None:
        self.now = pygame.time.get_ticks() / 1000.0

        if game.state is State.MENU:
            self._draw_menu_scene(game, menu)
        else:
            self._draw_board(game, alpha)
            self._draw_hud(game)

            if game.state is State.PAUSED:
                self._draw_dim(95)
                self._draw_overlay_panel(game, menu, paused=True)
            elif game.state in (State.GAME_OVER, State.WON):
                self._draw_dim(115)
                self._draw_overlay_panel(game, menu)

        if fade is not None and fade.alpha > 0:
            self.fade_surface.set_alpha(fade.alpha)
            self.screen.blit(self.fade_surface, (0, 0))
            self.fade_surface.set_alpha(255)

    def menu_button_rects(
        self, screen_name: MenuScreen, menu: MenuModel | None = None
    ) -> tuple[pygame.Rect, ...]:
        layout = self.menu_layouts[screen_name]
        if menu is None:
            return layout.buttons
        t = ease_out_cubic(menu.open_t)
        dy = int((1.0 - t) * 14)
        dx = int((1.0 - t) * 24) if screen_name is MenuScreen.PAUSE else 0
        return tuple(rect.move(dx, dy) for rect in layout.buttons)

    # ------------------------------------------------------------- background
    def _build_board_bg(self) -> pygame.Surface:
        surface = pygame.Surface((WINDOW_W, ROWS * CELL))
        surface.fill((17, 24, 31))
        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                if (x + y) % 2 == 0:
                    surface.fill((20, 28, 36), rect)
                pygame.draw.rect(surface, COLOR_GRID_FAINT, rect, width=1)
        pygame.draw.line(surface, COLOR_GRID, (0, 0), (WINDOW_W, 0))
        pygame.draw.line(surface, COLOR_GRID, (0, ROWS * CELL - 1), (WINDOW_W, ROWS * CELL - 1))
        return surface

    def _build_hud_bg(self) -> pygame.Surface:
        surface = pygame.Surface((WINDOW_W, HUD_H))
        surface.fill(COLOR_BG)
        pygame.draw.line(surface, COLOR_GRID, (0, HUD_H - 1), (WINDOW_W, HUD_H - 1))
        return surface

    def _build_menu_bg(self) -> pygame.Surface:
        surface = pygame.Surface((WINDOW_W, WINDOW_H))
        top = (12, 19, 27)
        bottom = (19, 35, 45)
        for y in range(WINDOW_H):
            t = y / max(1, WINDOW_H - 1)
            pygame.draw.line(surface, lerp_color(top, bottom, t), (0, y), (WINDOW_W, y))
        return surface

    def _build_vignette(self) -> pygame.Surface:
        surface = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        depth = 64
        for i in range(depth):
            alpha = int(115 * (1.0 - i / depth) ** 2)
            if alpha <= 0:
                continue
            rect = pygame.Rect(i * 2, i * 2, WINDOW_W - i * 4, WINDOW_H - i * 4)
            pygame.draw.rect(surface, (0, 0, 0, alpha), rect, width=2)
        return surface

    @staticmethod
    def _build_glow(
        radius: int, color: tuple[int, int, int], max_alpha: int = 26
    ) -> pygame.Surface:
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            alpha = int(max_alpha * (1.0 - r / radius) ** 2.2)
            if alpha <= 0:
                continue
            pygame.draw.circle(surface, (*color, alpha), (radius, radius), r)
        return surface

    @staticmethod
    def _build_ghost_path() -> list[tuple[int, int]]:
        inset = 2
        top, bottom = inset, ROWS - inset - 1
        left, right = inset, COLS - inset - 1
        path: list[tuple[int, int]] = []
        path.extend((x, top) for x in range(left, right + 1))
        path.extend((right, y) for y in range(top + 1, bottom + 1))
        path.extend((x, bottom) for x in range(right - 1, left - 1, -1))
        path.extend((left, y) for y in range(bottom - 1, top, -1))
        return path

    # --------------------------------------------------------------- menu art
    def _build_title(self) -> list[tuple[pygame.Surface, pygame.Surface, int]]:
        text = "SNAKE"
        spacing = 2
        widths = [self.font_title.size(char)[0] for char in text]
        total = sum(widths) + spacing * (len(text) - 1)
        x = (WINDOW_W - total) // 2
        result: list[tuple[pygame.Surface, pygame.Surface, int]] = []
        for index, char in enumerate(text):
            t = index / max(1, len(text) - 1)
            color = lerp_color(COLOR_SNAKE, COLOR_ACCENT, t)
            glyph = self.font_title.render(char, True, color)
            small = pygame.transform.smoothscale(
                glyph, (max(1, glyph.get_width() // 3), max(1, glyph.get_height() // 3))
            )
            glow = pygame.transform.smoothscale(small, glyph.get_size())
            glow.set_alpha(95)
            result.append((glyph, glow, x))
            x += widths[index] + spacing
        return result

    @staticmethod
    def _build_button(focused: bool) -> pygame.Surface:
        surface = pygame.Surface((BUTTON_W, BUTTON_H), pygame.SRCALPHA)
        fill = (61, 220, 132, 38) if focused else (255, 255, 255, 8)
        border = (61, 220, 132, 220) if focused else (255, 255, 255, 32)
        pygame.draw.rect(surface, fill, (0, 0, BUTTON_W, BUTTON_H), border_radius=14)
        pygame.draw.rect(surface, border, (0, 0, BUTTON_W, BUTTON_H), width=1, border_radius=14)
        return surface

    @staticmethod
    def _build_badge() -> pygame.Surface:
        surface = pygame.Surface((124, 26), pygame.SRCALPHA)
        pygame.draw.rect(surface, (85, 230, 193, 38), (0, 0, 124, 26), border_radius=13)
        pygame.draw.rect(surface, (85, 230, 193, 160), (0, 0, 124, 26), width=1, border_radius=13)
        return surface

    def _build_panel(self, width: int, height: int) -> tuple[pygame.Surface, pygame.Surface]:
        shadow = pygame.Surface((width + 24, height + 28), pygame.SRCALPHA)
        for offset, alpha in ((6, 60), (10, 45), (14, 30)):
            pygame.draw.rect(
                shadow,
                (0, 0, 0, alpha),
                (12, offset, width, height),
                border_radius=PANEL_RADIUS,
            )
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (*COLOR_PANEL, 238),
            (0, 0, width, height),
            border_radius=PANEL_RADIUS,
        )
        pygame.draw.rect(
            panel,
            (255, 255, 255, 42),
            (0, 0, width, height),
            width=1,
            border_radius=PANEL_RADIUS,
        )
        return panel, shadow

    # ----------------------------------------------------------- menu layout
    def _compute_layout(self, screen_name: MenuScreen) -> MenuLayout:
        # Derived from the single source of truth in snake.menu, so the
        # layout always matches the actual menu items.
        count = len(ITEMS[screen_name])

        has_header = screen_name in _HEADERS
        has_stats = screen_name in (MenuScreen.GAME_OVER, MenuScreen.WON)
        has_help = screen_name is MenuScreen.HELP
        has_scores = screen_name is MenuScreen.SCORES

        header_h = HEADER_H if has_header else 0
        stats_h = STATS_H if has_stats else 0
        help_h = HELP_H if has_help else (SCORES_H if has_scores else 0)
        gap_after = 18 if has_header else 0
        body_h = count * BUTTON_H + (count - 1) * BUTTON_GAP
        height = PAD_TOP + header_h + stats_h + help_h + gap_after + body_h + FOOTER_H + PAD_BOTTOM
        width = HELP_PANEL_W if has_help else PANEL_W
        x = (WINDOW_W - width) // 2
        if screen_name is MenuScreen.MAIN:
            # Anchored below the title block; clamped so the panel always
            # fits inside the window even if WINDOW_H shrinks or the
            # menu gains items.
            y = max(TITLE_BLOCK_BOTTOM, min(MAIN_PANEL_Y, WINDOW_H - height))
        else:
            y = (WINDOW_H - height) // 2
        panel = pygame.Rect(x, y, width, height)

        first_y = panel.y + PAD_TOP + header_h + stats_h + help_h + gap_after
        buttons = tuple(
            pygame.Rect(
                panel.centerx - BUTTON_W // 2,
                first_y + index * (BUTTON_H + BUTTON_GAP),
                BUTTON_W,
                BUTTON_H,
            )
            for index in range(count)
        )
        return MenuLayout(
            panel=panel,
            buttons=buttons,
            header_y=panel.y + 24,
            stats_y=panel.y + PAD_TOP + header_h,
            help_y=panel.y + PAD_TOP + header_h,
            footer_y=panel.bottom - 42,
        )

    # --------------------------------------------------------------- scenes
    def _draw_menu_scene(self, game: Game, menu: MenuModel) -> None:
        self._draw_backdrop(menu)

        if menu.screen is MenuScreen.MAIN:
            self._draw_title(menu)
            self._draw_text(
                "EAT  ·  GROW  ·  SURVIVE",
                self.font_tiny,
                COLOR_MUTED,
                (WINDOW_W // 2, TITLE_Y + 96),
                anchor="midtop",
            )
            self._draw_text(
                f"BEST  {game.high_score}",
                self.font_small,
                COLOR_MUTED,
                (WINDOW_W - 26, 24),
                anchor="topright",
            )
            self._draw_text(
                f"DIFFICULTY  {getattr(game, 'difficulty', 'Normal').upper()}",
                self.font_small,
                COLOR_MUTED,
                (26, 24),
                anchor="topleft",
            )
        else:
            self._draw_text(
                "SNAKE",
                self.font_button,
                COLOR_ACCENT,
                (28, 22),
                anchor="topleft",
            )

        self._draw_overlay_panel(game, menu)
        if menu.screen is MenuScreen.MAIN:
            self._draw_text(
                "A CLASSIC SNAKE  ·  PYGAME-CE",
                self.font_tiny,
                (78, 92, 104),
                (WINDOW_W // 2, WINDOW_H - 26),
                anchor="midtop",
            )

    def _draw_title(self, menu: MenuModel) -> None:
        for index, (glyph, glow, x) in enumerate(self.title_letters):
            bob = 0
            if not REDUCED_MOTION:
                bob = round(math.sin(menu.time * 1.8 + index * 0.4) * 3)
            y = self.title_y + bob
            self.screen.blit(glow, (x - 3, y - 3))
            self.screen.blit(glow, (x + 3, y + 2))
            self.screen.blit(glyph, (x, y))

    def _draw_backdrop(self, menu: MenuModel) -> None:
        self.screen.blit(self.menu_bg, (0, 0))

        if not REDUCED_MOTION:
            gx = int(-80 + math.sin(menu.time * 0.24) * 40)
            gy = int(-40 + math.cos(menu.time * 0.19) * 30)
            tx = int(WINDOW_W - 380 + math.cos(menu.time * 0.17) * 50)
            ty = int(WINDOW_H - 420 + math.sin(menu.time * 0.21) * 40)
        else:
            gx, gy, tx, ty = -80, -40, WINDOW_W - 380, WINDOW_H - 420

        self.screen.blit(self.glow_green, (gx, gy))
        self.screen.blit(self.glow_teal, (tx, ty))

        offset_x = int((menu.time * 7) % CELL) if not REDUCED_MOTION else 0
        offset_y = int((menu.time * 5) % CELL) if not REDUCED_MOTION else 0
        for x in range(-CELL + offset_x, WINDOW_W, CELL):
            pygame.draw.line(self.screen, (31, 45, 56), (x, 0), (x, WINDOW_H))
        for y in range(-CELL + offset_y, WINDOW_H, CELL):
            pygame.draw.line(self.screen, (28, 40, 50), (0, y), (WINDOW_W, y))

        self._draw_ghost_snake(menu)
        self.screen.blit(self.vignette, (0, 0))

    def _draw_ghost_snake(self, menu: MenuModel) -> None:
        if not self.ghost_path:
            return
        advance = 0 if REDUCED_MOTION else int(menu.time * GHOST_SPEED)
        head = advance % len(self.ghost_path)
        self.ghost_layer.fill((0, 0, 0, 0))
        trail = 15
        for step in range(trail, -1, -1):
            cell = self.ghost_path[(head - step) % len(self.ghost_path)]
            alpha = int(42 * (1.0 - step / (trail + 1)) ** 1.4)
            if alpha <= 1:
                continue
            rect = pygame.Rect(
                cell[0] * CELL + 2,
                BOARD_TOP + cell[1] * CELL + 2,
                CELL - 4,
                CELL - 4,
            )
            pygame.draw.rect(self.ghost_layer, (*COLOR_ACCENT, alpha), rect, border_radius=8)
        self.screen.blit(self.ghost_layer, (0, 0))

    def _draw_overlay_panel(self, game: Game, menu: MenuModel, paused: bool = False) -> None:
        layout = self.menu_layouts[menu.screen]
        panel_surface, shadow_surface = self.panel_surfaces[menu.screen]

        t = ease_out_cubic(menu.open_t)
        content_alpha = int(255 * t)
        dy = int((1.0 - t) * 14)
        dx = int((1.0 - t) * 24) if paused else 0
        panel_rect = layout.panel.move(dx, dy)
        offset_y = panel_rect.y - layout.panel.y
        offset_x = panel_rect.x - layout.panel.x

        self._blit(shadow_surface, (panel_rect.x - 12, panel_rect.y - 4), content_alpha)
        self._blit(panel_surface, panel_rect.topleft, content_alpha)

        header = _HEADERS.get(menu.screen)
        if header:
            color = COLOR_DANGER if menu.screen is MenuScreen.GAME_OVER else COLOR_ACCENT
            self._draw_text(
                header,
                self.font_header,
                color,
                (panel_rect.centerx, layout.header_y + offset_y),
                anchor="midtop",
                alpha=content_alpha,
            )
            if paused:
                self._draw_text(
                    "The board is frozen.",
                    self.font_small,
                    COLOR_MUTED,
                    (panel_rect.centerx, layout.header_y + offset_y + 40),
                    anchor="midtop",
                    alpha=content_alpha,
                )

        if menu.screen in (MenuScreen.GAME_OVER, MenuScreen.WON):
            self._draw_stats(game, layout, panel_rect, content_alpha)

        if menu.screen is MenuScreen.HELP:
            self._draw_help_content(layout, panel_rect, content_alpha)
        if menu.screen is MenuScreen.SCORES:
            self._draw_scores_content(game, layout, panel_rect, content_alpha)
        for index, (item, rect) in enumerate(zip(menu.items, layout.buttons, strict=False)):
            button_rect = rect.move(offset_x, offset_y)
            focus = menu.focus_t[index] if index < len(menu.focus_t) else 0.0
            self._draw_button(
                item.label,
                button_rect,
                focus,
                content_alpha,
                menu.screen,
            )

        self._draw_text(
            self._footer_hint(menu.screen),
            self.font_tiny,
            COLOR_MUTED,
            (panel_rect.centerx, layout.footer_y + offset_y),
            anchor="midtop",
            alpha=content_alpha,
        )

    def _draw_stats(
        self, game: Game, layout: MenuLayout, panel_rect: pygame.Rect, alpha: int
    ) -> None:
        y = layout.stats_y + (panel_rect.y - layout.panel.y)
        self._draw_text(
            f"SCORE   {game.score}",
            self.font_body,
            COLOR_TEXT,
            (panel_rect.centerx, y + 2),
            anchor="midtop",
            alpha=alpha,
        )
        self._draw_text(
            f"BEST    {game.high_score}",
            self.font_small,
            COLOR_MUTED,
            (panel_rect.centerx, y + 30),
            anchor="midtop",
            alpha=alpha,
        )
        if game.new_best:
            pulse = 255
            if not REDUCED_MOTION:
                pulse = int(200 + 55 * (0.5 + 0.5 * math.sin(self.now * 5.0)))
            badge_rect = self.badge.get_rect(center=(panel_rect.centerx, y + 57))
            self._blit(self.badge, badge_rect.topleft, min(alpha, pulse))
            self._draw_text(
                "NEW BEST",
                self.font_tiny,
                COLOR_ACCENT,
                badge_rect.center,
                anchor="center",
                alpha=min(alpha, pulse),
            )

        if len(game.high_scores) > 1:
            top = "  ".join(str(s) for s in game.high_scores[:3])
            self._draw_text(
                f"TOP  {top}",
                self.font_tiny,
                COLOR_MUTED,
                (panel_rect.centerx, y + 80),
                anchor="midtop",
                alpha=alpha,
            )

    def _draw_scores_content(
        self, game: Game, layout: MenuLayout, panel_rect: pygame.Rect, alpha: int
    ) -> None:
        y = layout.help_y + (panel_rect.y - layout.panel.y) + 12
        scores = game.high_scores[:5]
        if not scores:
            self._draw_text(
                "No scores yet - play a game!",
                self.font_small,
                COLOR_MUTED,
                (panel_rect.centerx, y + 30),
                anchor="midtop",
                alpha=alpha,
            )
            return
        for rank, score in enumerate(scores, start=1):
            color = COLOR_ACCENT if rank == 1 else COLOR_TEXT
            font = self.font_body if rank <= 3 else self.font_small
            self._draw_text(
                f"{rank}.",
                font,
                color,
                (panel_rect.x + 60, y),
                anchor="midtop",
                alpha=alpha,
            )
            self._draw_text(
                str(score),
                font,
                color,
                (panel_rect.centerx + 40, y),
                anchor="midtop",
                alpha=alpha,
            )
            y += 32

    def _draw_help_content(self, layout: MenuLayout, panel_rect: pygame.Rect, alpha: int) -> None:
        y = layout.help_y + (panel_rect.y - layout.panel.y) + 6
        rows = (
            ("↑ ↓ ← →  /  WASD", "Steer the snake"),
            ("P  /  Esc", "Pause"),
            ("Enter  /  Space", "Confirm"),
            ("R", "Restart after a run"),
            ("M", "Return to main menu"),
            ("Mouse", "Hover / click menus"),
        )
        left = panel_rect.x + 34
        right = panel_rect.x + panel_rect.width - 34
        for key, description in rows:
            self._draw_text(key, self.font_small, COLOR_ACCENT, (left, y), alpha=alpha)
            self._draw_text(
                description,
                self.font_small,
                COLOR_MUTED,
                (right, y),
                anchor="topright",
                alpha=alpha,
            )
            y += 24

        y += 8
        for line in (
            "Eat the red food to grow.",
            "Avoid walls and your own tail.",
            "Fill every cell to win.",
        ):
            self._draw_text(
                line,
                self.font_tiny,
                COLOR_MUTED,
                (panel_rect.centerx, y),
                anchor="midtop",
                alpha=alpha,
            )
            y += 19

    def _draw_button(
        self,
        label: str,
        rect: pygame.Rect,
        focus: float,
        alpha: int,
        screen_name: MenuScreen,
    ) -> None:
        focus = clamp(focus)
        self._blit(self.button_idle, rect.topleft, alpha)
        if focus > 0.01:
            self._blit(self.button_focus, rect.topleft, int(alpha * focus))

        if focus > 0.02 and alpha > 4:
            width = max(1, round(4 * focus))
            bar = pygame.Surface((width, BUTTON_H - 30), pygame.SRCALPHA)
            bar.fill((*COLOR_ACCENT, 255))
            self._blit(
                bar,
                (rect.x + 9, rect.y + 15),
                int(alpha * min(1.0, focus * 2.0)),
            )

        shift = round(7 * focus)
        label_pos = (rect.centerx + shift, rect.centery)
        idle_label = self._text_surface(label, self.font_button, COLOR_TEXT)
        focused_label = self._text_surface(label, self.font_button, COLOR_ACCENT)

        idle_rect = idle_label.get_rect(center=label_pos)
        focus_rect = focused_label.get_rect(center=label_pos)
        self._blit(idle_label, idle_rect.topleft, int(alpha * (1.0 - focus)))
        if focus > 0.01:
            self._blit(focused_label, focus_rect.topleft, int(alpha * focus))

        if focus > 0.02:
            bob = round(math.sin(self.now * 6.0) * 2) if not REDUCED_MOTION else 0
            chevron = self._text_surface("›", self.font_header, COLOR_ACCENT)
            chevron_rect = chevron.get_rect(midright=(rect.right - 22, rect.centery + bob))
            self._blit(chevron, chevron_rect.topleft, int(alpha * min(1.0, focus * 1.8)))

    # ----------------------------------------------------------------- board
    def _draw_board(self, game: Game, alpha: float) -> None:
        self.screen.blit(self.board_bg, (0, BOARD_TOP))
        self._draw_obstacles(game)
        self._draw_food(game)
        self._draw_snake(game, clamp(alpha))

    def _draw_obstacles(self, game: Game) -> None:
        for x, y in game.obstacles:
            rect = pygame.Rect(x * CELL + 3, BOARD_TOP + y * CELL + 3, CELL - 6, CELL - 6)
            pygame.draw.rect(self.screen, COLOR_OBSTACLE, rect, border_radius=6)
            pygame.draw.rect(self.screen, (70, 90, 105), rect, width=1, border_radius=6)

    def _draw_food(self, game: Game) -> None:
        if game.food.position is None:
            return
        x, y = game.food.position
        center = (x * CELL + CELL // 2, BOARD_TOP + y * CELL + CELL // 2)

        pulse = 0.5 + 0.5 * math.sin(self.now * 6.0) if not REDUCED_MOTION else 0.5
        glow = self.food_glow
        glow.set_alpha(int(150 + 80 * pulse))
        self.screen.blit(glow, glow.get_rect(center=center))
        glow.set_alpha(255)

        radius = 9 + (1.5 * pulse if not REDUCED_MOTION else 0.0)
        pygame.draw.circle(self.screen, COLOR_FOOD, center, round(radius))
        pygame.draw.circle(
            self.screen,
            (255, 156, 150),
            (center[0] - 2, center[1] - 2),
            max(1, int(radius) // 3),
        )

    def _draw_snake(self, game: Game, alpha: float) -> None:
        body = list(game.snake.body)
        length = len(body)
        previous = game.prev_body

        for index in range(length - 1, -1, -1):
            cell = body[index]
            if SMOOTH_MOTION and previous:
                prev = previous[index] if index < len(previous) else cell
                gx = lerp(prev[0], cell[0], alpha)
                gy = lerp(prev[1], cell[1], alpha)
            else:
                gx, gy = float(cell[0]), float(cell[1])

            x = round(gx * CELL) + 1
            y = round(gy * CELL) + BOARD_TOP + 1
            rect = pygame.Rect(x, y, CELL - 2, CELL - 2)

            if index == 0:
                color = COLOR_SNAKE_HEAD
            else:
                t = index / max(1, length - 1)
                color = lerp_color(COLOR_SNAKE, COLOR_SNAKE_TAIL, t * 0.75)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)

            if index == 0:
                self._draw_eyes(rect, game)

    def _draw_eyes(self, head_rect: pygame.Rect, game: Game) -> None:
        dx, dy = game.snake.direction.vector
        px, py = -dy, dx
        cx, cy = head_rect.center
        for side in (-1, 1):
            ex = cx + dx * 5 + px * 5 * side
            ey = cy + dy * 5 + py * 5 * side
            pygame.draw.circle(self.screen, COLOR_WHITE, (int(ex), int(ey)), 3)
            pygame.draw.circle(
                self.screen,
                (18, 34, 26),
                (int(ex + dx * 1.2), int(ey + dy * 1.2)),
                1,
            )

    # ------------------------------------------------------------------- HUD
    def _draw_hud(self, game: Game) -> None:
        self.screen.blit(self.hud_bg, (0, 0))

        self._draw_text("SCORE", self.font_hud_label, COLOR_MUTED, (24, 14), alpha=230)
        self._draw_text(str(game.score), self.font_hud_value, COLOR_TEXT, (24, 28))

        self._draw_text("BEST", self.font_hud_label, COLOR_MUTED, (174, 14), alpha=230)
        self._draw_text(str(game.high_score), self.font_hud_value, COLOR_TEXT, (174, 28))

        hint = "P / Esc   Pause" if game.state is State.PLAYING else ""
        if hint:
            self._draw_text(
                hint,
                self.font_hud_hint,
                COLOR_MUTED,
                (WINDOW_W - 24, 42),
                anchor="midright",
            )

    # --------------------------------------------------------------- helpers
    def _draw_dim(self, alpha: int) -> None:
        self.dim_surface.fill((0, 0, 0, alpha))
        self.screen.blit(self.dim_surface, (0, 0))

    def _text_surface(
        self, text: str, font: pygame.font.Font, color: tuple[int, int, int]
    ) -> pygame.Surface:
        # Key by the font's identifying attributes instead of ``id(font)``:
        # a memory address can be reused by a *different* Font after garbage
        # collection, and the old key would then serve a stale surface.
        key = (text, font.name, font.get_height(), font.bold, font.italic, color)
        cached = self.text_cache.get(key)
        if cached is None:
            cached = font.render(text, True, color)
            self.text_cache[key] = cached
        return cached

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
        anchor: str = "topleft",
        alpha: int = 255,
    ) -> None:
        surface = self._text_surface(text, font, color)
        rect = surface.get_rect(**{anchor: position})
        self._blit(surface, rect.topleft, alpha)

    def _blit(self, surface: pygame.Surface, position: tuple[int, int], alpha: int = 255) -> None:
        alpha = int(clamp(alpha, 0, 255))
        if alpha >= 255:
            self.screen.blit(surface, position)
        else:
            surface.set_alpha(alpha)
            self.screen.blit(surface, position)
            surface.set_alpha(255)

    @staticmethod
    def _footer_hint(screen_name: MenuScreen) -> str:
        if screen_name is MenuScreen.MAIN:
            return "↑/↓  Move      Enter  Select      Esc  Quit"
        if screen_name is MenuScreen.HELP:
            return "Esc  Back"
        if screen_name is MenuScreen.DIFFICULTY:
            return "Enter  Select      Esc  Back"
        if screen_name is MenuScreen.SCORES:
            return "Esc  Back"
        if screen_name is MenuScreen.PAUSE:
            return "Esc  Resume      Enter  Select"
        return "R  Restart      M  Menu      Esc  Menu"

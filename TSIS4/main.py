"""
TSIS4 — Snake Game with PostgreSQL leaderboard.
Screens: Main Menu → Game → Game Over → Leaderboard → Settings
"""

import pygame
import sys
import json
import os

from config  import WIN_W, WIN_H, FPS
from db      import ensure_tables, save_session, get_top10, get_personal_best
from game    import SnakeGame

SETTINGS_FILE = "settings.json"

# ── Colours ────────────────────────────────────────────────────
C_BG     = (15,  20,  15)
C_PANEL  = (22,  30,  22)
C_BORDER = (60, 100,  60)
C_BTN    = (35,  55,  35)
C_BHOV   = (50,  80,  50)
C_BACT   = (60, 160,  80)
C_TEXT   = (200, 230, 200)
C_ACCENT = (80,  220, 100)
C_WARN   = (220, 100,  50)
C_WHITE  = (255, 255, 255)

COLOR_OPTIONS = {
    "Green":  [60,  200, 100],
    "Blue":   [60,  160, 255],
    "Orange": [255, 140,  40],
    "Pink":   [255, 100, 180],
    "White":  [220, 220, 220],
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"snake_color": [60, 200, 100], "grid": True, "sound": False}
    with open(SETTINGS_FILE) as f:
        return json.load(f)


def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)


def draw_btn(surf, rect, label, font, active=False, hover=False):
    bg = C_BACT if active else (C_BHOV if hover else C_BTN)
    pygame.draw.rect(surf, bg,       rect, border_radius=8)
    pygame.draw.rect(surf, C_BORDER, rect, 2, border_radius=8)
    t = font.render(label, True, C_WHITE)
    surf.blit(t, (rect.centerx - t.get_width()//2,
                  rect.centery - t.get_height()//2))


def draw_txt(surf, text, font, color, x, y, center=False):
    t = font.render(text, True, color)
    if center:
        x -= t.get_width() // 2
    surf.blit(t, (x, y))


class App:
    def __init__(self):
        pygame.init()
        self.screen   = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Snake — TSIS4")
        self.clock    = pygame.time.Clock()
        self.settings = load_settings()
        ensure_tables()

        self.fonts = {
            "sm":  pygame.font.SysFont("segoeui", 16),
            "md":  pygame.font.SysFont("segoeui", 22, bold=True),
            "lg":  pygame.font.SysFont("segoeui", 38, bold=True),
            "xl":  pygame.font.SysFont("segoeui", 56, bold=True),
            "inp": pygame.font.SysFont("monospace", 24),
        }

        self.state         = "menu"
        self.username      = ""
        self.game          = None
        self.personal_best = 0
        self.final_score   = 0
        self.final_level   = 1

    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            if   self.state == "menu":        self._menu(events, mx, my)
            elif self.state == "input":       self._input(events, mx, my)
            elif self.state == "game":        self._play(events)
            elif self.state == "gameover":    self._gameover(events, mx, my)
            elif self.state == "leaderboard": self._leaderboard(events, mx, my)
            elif self.state == "settings":    self._settings_screen(events, mx, my)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ── MAIN MENU ──────────────────────────────────────────────

    def _menu(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W
        draw_txt(self.screen, "SNAKE", self.fonts["xl"],
                 C_ACCENT, W//2, 65, center=True)
        draw_txt(self.screen, "TSIS 4  —  PostgreSQL Edition",
                 self.fonts["sm"], C_TEXT, W//2, 138, center=True)

        btns = {
            "play":        pygame.Rect(W//2-130, 190, 260, 54),
            "leaderboard": pygame.Rect(W//2-130, 262, 260, 54),
            "settings":    pygame.Rect(W//2-130, 334, 260, 54),
            "quit":        pygame.Rect(W//2-130, 406, 260, 54),
        }
        lbls = {"play": "▶  Play", "leaderboard": "🏆  Leaderboard",
                "settings": "⚙  Settings", "quit": "✕  Quit"}

        for k, r in btns.items():
            draw_btn(self.screen, r, lbls[k], self.fonts["md"],
                     hover=r.collidepoint(mx, my))

        draw_txt(self.screen, "● +1pt   ★ +3pts   ♦ +5pts   ☠ Poison (-2 seg)",
                 self.fonts["sm"], (100,130,100), W//2, 488, center=True)
        draw_txt(self.screen, "⚡ Speed Boost   🐢 Slow Motion   🛡 Shield",
                 self.fonts["sm"], (100,130,100), W//2, 512, center=True)
        draw_txt(self.screen, "Obstacles appear from Level 3",
                 self.fonts["sm"], (100,130,100), W//2, 536, center=True)

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btns["play"].collidepoint(mx, my):
                    self.state = "input"
                elif btns["leaderboard"].collidepoint(mx, my):
                    self.state = "leaderboard"
                elif btns["settings"].collidepoint(mx, my):
                    self.state = "settings"
                elif btns["quit"].collidepoint(mx, my):
                    pygame.quit(); sys.exit()

    # ── USERNAME INPUT ─────────────────────────────────────────

    def _input(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W
        draw_txt(self.screen, "Enter your name", self.fonts["lg"],
                 C_ACCENT, W//2, 175, center=True)

        box = pygame.Rect(W//2-170, 262, 340, 54)
        pygame.draw.rect(self.screen, C_PANEL,  box, border_radius=8)
        pygame.draw.rect(self.screen, C_BORDER, box, 2, border_radius=8)
        t = self.fonts["inp"].render(self.username + "|", True, C_WHITE)
        self.screen.blit(t, (box.x+14, box.y+13))

        btn = pygame.Rect(W//2-110, 344, 220, 50)
        draw_btn(self.screen, btn, "Start Game", self.fonts["md"],
                 hover=btn.collidepoint(mx, my))
        draw_txt(self.screen, "Press Enter to start",
                 self.fonts["sm"], C_TEXT, W//2, 410, center=True)

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and self.username.strip():
                    self._start_game()
                elif e.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif e.unicode.isprintable() and len(self.username) < 16:
                    self.username += e.unicode
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn.collidepoint(mx, my) and self.username.strip():
                    self._start_game()

    def _start_game(self):
        name = self.username.strip()
        self.personal_best = get_personal_best(name)
        self.game  = SnakeGame(name, self.settings, self.personal_best)
        self.state = "game"

    # ── GAMEPLAY ───────────────────────────────────────────────

    def _play(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if   e.key in (pygame.K_UP,    pygame.K_w):
                    self.game.set_direction((0, -1))
                elif e.key in (pygame.K_DOWN,  pygame.K_s):
                    self.game.set_direction((0,  1))
                elif e.key in (pygame.K_LEFT,  pygame.K_a):
                    self.game.set_direction((-1, 0))
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.game.set_direction((1,  0))
                elif e.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    return

        self.game.update()
        self.screen.fill(C_BG)
        self.game.draw(self.screen, self.settings.get("grid", True))
        self._draw_hud()

        if not self.game.alive:
            self.final_score = self.game.score
            self.final_level = self.game.level
            save_session(self.username.strip(),
                         self.final_score, self.final_level)
            self.state = "gameover"

    def _draw_hud(self):
        g  = self.game
        fs = self.fonts["sm"]
        fm = self.fonts["md"]

        pygame.draw.rect(self.screen, (12, 20, 12), (0, 0, WIN_W, 95))
        pygame.draw.line(self.screen, C_BORDER, (0, 95), (WIN_W, 95), 2)

        draw_txt(self.screen, f"Player: {self.username}", fs, C_TEXT, 10, 8)
        draw_txt(self.screen, f"Score:  {g.score}",  fm, C_ACCENT, 10, 28)
        draw_txt(self.screen, f"Best:   {self.personal_best}", fs,
                 (140, 190, 140), 10, 60)

        draw_txt(self.screen, f"Level:  {g.level}", fm, C_TEXT, 230, 28)
        draw_txt(self.screen, f"Length: {len(g.body)}", fs, C_TEXT, 230, 60)

        if g.pu_effect:
            now       = pygame.time.get_ticks()
            remaining = max(0, (g.pu_effect_end - now) // 1000)
            lbl = {"speed_boost": "⚡ SPEED BOOST",
                   "slow_motion": "🐢 SLOW MOTION"}[g.pu_effect]
            draw_txt(self.screen, f"{lbl}  {remaining}s",
                     fm, (255, 180, 40), 420, 35)
        if g.shield_active:
            draw_txt(self.screen, "🛡 SHIELD ACTIVE",
                     fm, (80, 180, 255), 420, 60)

        draw_txt(self.screen, "WASD / Arrows  |  ESC = menu",
                 fs, (70, 100, 70), WIN_W - 260, 75)

    # ── GAME OVER ──────────────────────────────────────────────

    def _gameover(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W
        draw_txt(self.screen, "GAME OVER", self.fonts["xl"],
                 C_WARN, W//2, 75, center=True)
        draw_txt(self.screen, f"Player: {self.username}",
                 self.fonts["md"], C_TEXT,   W//2, 168, center=True)
        draw_txt(self.screen, f"Score:  {self.final_score}",
                 self.fonts["md"], C_ACCENT, W//2, 210, center=True)
        draw_txt(self.screen, f"Level:  {self.final_level}",
                 self.fonts["md"], C_TEXT,   W//2, 252, center=True)

        new_best = self.final_score > self.personal_best
        best_val = max(self.final_score, self.personal_best)
        clr  = (255, 215, 0) if new_best else (140, 180, 140)
        lbl  = f"🏆 NEW BEST: {best_val}!" if new_best else f"Personal best: {best_val}"
        draw_txt(self.screen, lbl, self.fonts["md"], clr, W//2, 300, center=True)

        b_retry = pygame.Rect(W//2-230, 370, 200, 50)
        b_board = pygame.Rect(W//2-10,  370, 200, 50)
        b_menu  = pygame.Rect(W//2-110, 440, 220, 50)
        draw_btn(self.screen, b_retry, "↺  Retry",        self.fonts["md"],
                 hover=b_retry.collidepoint(mx, my))
        draw_btn(self.screen, b_board, "🏆  Leaderboard",  self.fonts["md"],
                 hover=b_board.collidepoint(mx, my))
        draw_btn(self.screen, b_menu,  "⌂  Main Menu",    self.fonts["md"],
                 hover=b_menu.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if b_retry.collidepoint(mx, my): self._start_game()
                elif b_board.collidepoint(mx, my): self.state = "leaderboard"
                elif b_menu.collidepoint(mx, my):  self.state = "menu"

    # ── LEADERBOARD ────────────────────────────────────────────

    def _leaderboard(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W
        draw_txt(self.screen, "🏆 TOP 10  ALL-TIME",
                 self.fonts["lg"], C_ACCENT, W//2, 22, center=True)

        rows = get_top10()
        hdrs = ["#", "Username", "Score", "Level", "Date"]
        xs   = [45, 105, 305, 415, 505]
        y0   = 88

        for i, h in enumerate(hdrs):
            draw_txt(self.screen, h, self.fonts["sm"],
                     (120, 160, 120), xs[i], y0)
        pygame.draw.line(self.screen, C_BORDER,
                         (35, y0+22), (W-35, y0+22), 1)

        for rank, row in enumerate(rows, 1):
            y   = y0 + 30 + (rank-1) * 40
            col = (255, 215, 0) if row[0] == self.username else C_TEXT
            for i, v in enumerate([str(rank), row[0],
                                    str(row[1]), str(row[2]), str(row[3])]):
                draw_txt(self.screen, v, self.fonts["sm"], col, xs[i], y)

        btn = pygame.Rect(W//2-110, WIN_H-68, 220, 48)
        draw_btn(self.screen, btn, "← Back", self.fonts["md"],
                 hover=btn.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn.collidepoint(mx, my): self.state = "menu"
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = "menu"

    # ── SETTINGS ───────────────────────────────────────────────

    def _settings_screen(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W
        draw_txt(self.screen, "⚙ Settings", self.fonts["lg"],
                 C_ACCENT, W//2, 32, center=True)

        grid_rect = pygame.Rect(W//2-130, 118, 260, 48)
        draw_btn(self.screen, grid_rect,
                 f"Grid: {'ON' if self.settings['grid'] else 'OFF'}",
                 self.fonts["md"], active=self.settings["grid"],
                 hover=grid_rect.collidepoint(mx, my))

        snd_rect = pygame.Rect(W//2-130, 184, 260, 48)
        draw_btn(self.screen, snd_rect,
                 f"Sound: {'ON' if self.settings['sound'] else 'OFF'}",
                 self.fonts["md"], active=self.settings["sound"],
                 hover=snd_rect.collidepoint(mx, my))

        draw_txt(self.screen, "Snake Color:", self.fonts["md"],
                 C_TEXT, W//2, 258, center=True)
        color_rects = {}
        cx0 = W//2 - (len(COLOR_OPTIONS)*58)//2
        for i, (name, col) in enumerate(COLOR_OPTIONS.items()):
            r   = pygame.Rect(cx0 + i*58, 293, 50, 50)
            sel = self.settings["snake_color"] == col
            color_rects[name] = (r, col)
            pygame.draw.rect(self.screen, tuple(col), r, border_radius=8)
            pygame.draw.rect(self.screen,
                             C_ACCENT if sel else C_BORDER, r, 3, border_radius=8)
            draw_txt(self.screen, name, self.fonts["sm"],
                     C_TEXT, r.centerx, r.bottom+4, center=True)

        btn_save = pygame.Rect(W//2-130, WIN_H-85, 260, 50)
        draw_btn(self.screen, btn_save, "💾 Save & Back", self.fonts["md"],
                 hover=btn_save.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if grid_rect.collidepoint(mx, my):
                    self.settings["grid"] = not self.settings["grid"]
                if snd_rect.collidepoint(mx, my):
                    self.settings["sound"] = not self.settings["sound"]
                for name, (r, col) in color_rects.items():
                    if r.collidepoint(mx, my):
                        self.settings["snake_color"] = col
                if btn_save.collidepoint(mx, my):
                    save_settings(self.settings)
                    self.state = "menu"
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = "menu"


if __name__ == "__main__":
    App().run()

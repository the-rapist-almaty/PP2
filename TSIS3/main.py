"""
TSIS3 — Racer Game
Screens: Main Menu → Game → Game Over → Leaderboard → Settings
Features:
   Weighted coins, enemies, obstacles, power-ups (Nitro/Shield/Repair)
   Difficulty scaling (speed + spawn rate)
   Score = coins × value + distance bonus
   Persistent leaderboard (leaderboard.json)
   Settings: sound toggle, car color, difficulty (settings.json)
"""

import pygame
import random
import sys

from racer      import (Road, Player, Enemy, Coin, Obstacle, PowerUp,
                        WIN_W, WIN_H, HUD_H, LANE_COUNT, lane_center)
from ui         import (draw_button, draw_text, draw_panel,
                        C_BG, C_PANEL, C_BORDER, C_BTN, C_BTN_HOV,
                        C_BTN_ACT, C_TEXT, C_ACCENT, C_WARN, C_WHITE, C_BLACK)
from persistence import load_leaderboard, save_score, load_settings, save_settings

FPS = 60

#  Difficulty presets 
DIFFICULTY = {
    "easy":   {"base_speed": 3, "enemy_interval": 2200, "obs_interval": 3500},
    "normal": {"base_speed": 5, "enemy_interval": 1600, "obs_interval": 2500},
    "hard":   {"base_speed": 7, "enemy_interval": 1000, "obs_interval": 1800},
}

COLOR_OPTIONS = {
    "Blue":   (50,  180, 255),
    "Red":    (220,  60,  60),
    "Green":  (60,  200,  80),
    "Yellow": (230, 190,  40),
    "Purple": (160,  80, 220),
}


#  GAME

class Game:
    def __init__(self, screen, fonts, username, settings):
        self.screen   = screen
        self.fonts    = fonts
        self.username = username
        self.settings = settings

        diff          = DIFFICULTY[settings["difficulty"]]
        self.base_speed     = diff["base_speed"]
        self.enemy_interval = diff["enemy_interval"]
        self.obs_interval   = diff["obs_interval"]
        self.scroll_speed   = self.base_speed

        self.road     = Road()
        self.player   = Player(settings["car_color"])

        self.enemies  : list[Enemy]   = []
        self.coins    : list[Coin]    = []
        self.obstacles: list[Obstacle]= []
        self.powerups : list[PowerUp] = []

        self.score    = 0
        self.coins_collected = 0
        self.distance = 0
        self.alive    = True

        # Active power-up state
        self.nitro_end   = 0
        self.active_pu   = None   # label string

        # Spawn timers (ms)
        now = pygame.time.get_ticks()
        self.next_enemy   = now + self.enemy_interval
        self.next_coin    = now + 800
        self.next_obs     = now + self.obs_interval
        self.next_powerup = now + 5000

        # Key repeat
        self.last_left  = 0
        self.last_right = 0
        self.key_delay  = 180

    # ── Spawn helpers ──────────────────────────────────────────

    def _occupied_lanes(self):
        lanes = set()
        for e in self.enemies:
            if e.y < WIN_H * 0.4:
                lanes.add(e.lane)
        return lanes

    def _spawn_enemy(self):
        occupied = self._occupied_lanes()
        free = [l for l in range(LANE_COUNT) if l not in occupied]
        if not free:
            return
        speed = self.scroll_speed * random.uniform(0.7, 1.1)
        e = Enemy(speed)
        e.lane = random.choice(free)
        e.x    = float(lane_center(e.lane))
        self.enemies.append(e)

    def _spawn_coin(self):
        c = Coin(self.scroll_speed * 0.9)
        self.coins.append(c)

    def _spawn_obstacle(self):
        o = Obstacle(self.scroll_speed * 0.85)
        self.obstacles.append(o)

    def _spawn_powerup(self):
        if not self.powerups:
            p = PowerUp(self.scroll_speed * 0.8)
            self.powerups.append(p)

    # ── Power-up application ───────────────────────────────────

    def _apply_powerup(self, kind):
        if kind == "nitro":
            self.scroll_speed = self.base_speed * 2
            self.nitro_end    = pygame.time.get_ticks() + 4000
            self.active_pu    = "NITRO"
        elif kind == "shield":
            self.player.shield = True
            self.active_pu     = "SHIELD"
        elif kind == "repair":
            self.active_pu = "REPAIR ✓"

    # ── Update ─────────────────────────────────────────────────

    def update(self):
        now = pygame.time.get_ticks()

        # Nitro timeout
        if self.nitro_end and now > self.nitro_end:
            self.scroll_speed = self.base_speed
            self.nitro_end    = 0
            self.active_pu    = None

        # Distance & score scaling
        self.distance     += self.scroll_speed
        display_distance   = self.distance // 60
        self.score         = self.coins_collected * 10 + display_distance

        # Gradually increase speed
        self.base_speed = DIFFICULTY[self.settings["difficulty"]]["base_speed"] + display_distance // 200
        if not self.nitro_end:
            self.scroll_speed = self.base_speed

        # Spawns
        if now >= self.next_enemy:
            self._spawn_enemy()
            interval = max(600, self.enemy_interval - display_distance * 2)
            self.next_enemy = now + interval

        if now >= self.next_coin:
            self._spawn_coin()
            self.next_coin = now + random.randint(600, 1200)

        if now >= self.next_obs:
            self._spawn_obstacle()
            interval = max(800, self.obs_interval - display_distance * 3)
            self.next_obs = now + interval

        if now >= self.next_powerup:
            self._spawn_powerup()
            self.next_powerup = now + random.randint(7000, 12000)

        # Road
        self.road.update(self.scroll_speed)

        # Player
        self.player.update()

        # Enemies
        pr = self.player.rect
        for e in self.enemies[:]:
            e.update()
            if e.is_off_screen():
                self.enemies.remove(e)
                continue
            if pr.colliderect(e.rect):
                if self.player.shield:
                    self.player.shield = False
                    self.active_pu     = None
                    self.enemies.remove(e)
                else:
                    self.alive = False

        # Coins
        for c in self.coins[:]:
            c.update()
            if c.is_off_screen():
                self.coins.remove(c)
                continue
            if pr.colliderect(c.rect):
                self.coins_collected += c.value
                self.coins.remove(c)

        # Obstacles
        for o in self.obstacles[:]:
            o.update()
            if o.is_off_screen():
                self.obstacles.remove(o)
                continue
            if pr.colliderect(o.rect):
                if self.player.shield:
                    self.player.shield = False
                    self.active_pu     = None
                    self.obstacles.remove(o)
                else:
                    self.alive = False

        # Power-ups
        for p in self.powerups[:]:
            p.update()
            if p.is_off_screen() or p.is_expired():
                self.powerups.remove(p)
                continue
            if pr.colliderect(p.rect):
                self._apply_powerup(p.kind)
                self.powerups.remove(p)

    # ── Draw ───────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(C_BG)
        self.road.draw(self.screen)

        for e in self.enemies:   e.draw(self.screen)
        for c in self.coins:     c.draw(self.screen)
        for o in self.obstacles: o.draw(self.screen)
        for p in self.powerups:  p.draw(self.screen)
        self.player.draw(self.screen)

        self._draw_hud()

    def _draw_hud(self):
        f  = self.fonts["sm"]
        fb = self.fonts["md"]
        dist_m = self.distance // 60

        pygame.draw.rect(self.screen, (20, 20, 35),
                         (0, 0, WIN_W, HUD_H))
        pygame.draw.line(self.screen, C_BORDER,
                         (0, HUD_H), (WIN_W, HUD_H), 2)

        draw_text(self.screen, f"👤 {self.username}", f, C_TEXT, 10, 8)
        draw_text(self.screen, f"Score: {self.score}", fb, C_ACCENT, 10, 30)
        draw_text(self.screen, f"🪙 {self.coins_collected}", f, (255,215,0), 200, 8)
        draw_text(self.screen, f"📏 {dist_m}m", f, C_TEXT, 200, 30)
        draw_text(self.screen, f"Speed: {self.base_speed}", f, C_TEXT, 340, 8)

        if self.active_pu:
            draw_text(self.screen, f"⚡ {self.active_pu}", fb, (255,140,0), 480, 15)

        # Controls hint
        draw_text(self.screen, "← → move   ESC pause", f, (100,100,130), 560, 38)

    # ── Handle input ───────────────────────────────────────────

    def handle_event(self, event):
        now = pygame.time.get_ticks()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and now - self.last_left > self.key_delay:
                self.player.move_left()
                self.last_left = now
            elif event.key == pygame.K_RIGHT and now - self.last_right > self.key_delay:
                self.player.move_right()
                self.last_right = now


#  SCREENS

class App:
    def __init__(self):
        pygame.init()
        self.screen   = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Racer — TSIS3")
        self.clock    = pygame.time.Clock()
        self.settings = load_settings()

        self.fonts = {
            "sm":  pygame.font.SysFont("segoeui", 16),
            "md":  pygame.font.SysFont("segoeui", 22, bold=True),
            "lg":  pygame.font.SysFont("segoeui", 36, bold=True),
            "xl":  pygame.font.SysFont("segoeui", 52, bold=True),
            "inp": pygame.font.SysFont("monospace", 24),
        }

        self.username = ""
        self.state    = "menu"   # menu | input | game | gameover | leaderboard | settings
        self.game     = None
        self.final_score    = 0
        self.final_distance = 0
        self.final_coins    = 0

    # ── Main loop ──────────────────────────────────────────────

    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            if   self.state == "menu":        self._menu(events, mx, my)
            elif self.state == "input":       self._input_screen(events, mx, my)
            elif self.state == "game":        self._game_loop(events)
            elif self.state == "gameover":    self._gameover(events, mx, my)
            elif self.state == "leaderboard": self._leaderboard(events, mx, my)
            elif self.state == "settings":    self._settings(events, mx, my)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ── MENU ───────────────────────────────────────────────────

    def _menu(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W

        draw_text(self.screen, "RACER", self.fonts["xl"], C_ACCENT,
                  W//2, 80, center=True)
        draw_text(self.screen, "TSIS 3", self.fonts["sm"], C_TEXT,
                  W//2, 148, center=True)

        btns = {
            "play":        pygame.Rect(W//2-120, 210, 240, 52),
            "leaderboard": pygame.Rect(W//2-120, 280, 240, 52),
            "settings":    pygame.Rect(W//2-120, 350, 240, 52),
            "quit":        pygame.Rect(W//2-120, 420, 240, 52),
        }
        labels = {"play": "▶  Play", "leaderboard": "🏆  Leaderboard",
                  "settings": "⚙  Settings", "quit": "✕  Quit"}

        for key, rect in btns.items():
            draw_button(self.screen, rect, labels[key], self.fonts["md"],
                        hover=rect.collidepoint(mx, my))

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

    def _input_screen(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W

        draw_text(self.screen, "Enter your name", self.fonts["lg"],
                  C_ACCENT, W//2, 180, center=True)

        box = pygame.Rect(W//2 - 160, 260, 320, 52)
        pygame.draw.rect(self.screen, C_PANEL, box, border_radius=8)
        pygame.draw.rect(self.screen, C_BORDER, box, 2, border_radius=8)
        txt = self.fonts["inp"].render(self.username + "|", True, C_WHITE)
        self.screen.blit(txt, (box.x + 12, box.y + 12))

        btn_start = pygame.Rect(W//2 - 100, 340, 200, 50)
        draw_button(self.screen, btn_start, "Start Game", self.fonts["md"],
                    hover=btn_start.collidepoint(mx, my))
        draw_text(self.screen, "Press Enter or click Start", self.fonts["sm"],
                  C_TEXT, W//2, 408, center=True)

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and self.username.strip():
                    self._start_game()
                elif e.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif e.unicode.isprintable() and len(self.username) < 16:
                    self.username += e.unicode
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_start.collidepoint(mx, my) and self.username.strip():
                    self._start_game()

    def _start_game(self):
        self.game  = Game(self.screen, self.fonts,
                          self.username.strip(), self.settings)
        self.state = "game"

    # ── GAME LOOP ──────────────────────────────────────────────

    def _game_loop(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = "menu"
                return
            self.game.handle_event(e)

        self.game.update()
        self.game.draw()

        if not self.game.alive:
            self.final_score    = self.game.score
            self.final_distance = self.game.distance // 60
            self.final_coins    = self.game.coins_collected
            save_score(self.username, self.final_score,
                       self.final_distance, self.final_coins)
            self.state = "gameover"

    # ── GAME OVER ──────────────────────────────────────────────

    def _gameover(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W

        draw_text(self.screen, "GAME OVER", self.fonts["xl"],
                  C_WARN, W//2, 90, center=True)
        draw_text(self.screen, f"Player: {self.username}", self.fonts["md"],
                  C_TEXT, W//2, 175, center=True)
        draw_text(self.screen, f"Score:    {self.final_score}", self.fonts["md"],
                  C_ACCENT, W//2, 220, center=True)
        draw_text(self.screen, f"Distance: {self.final_distance} m", self.fonts["md"],
                  C_TEXT, W//2, 260, center=True)
        draw_text(self.screen, f"Coins:    {self.final_coins}", self.fonts["md"],
                  (255,215,0), W//2, 300, center=True)

        # Personal best from leaderboard
        board = load_leaderboard()
        personal = [e for e in board if e["username"] == self.username]
        if personal:
            best = max(personal, key=lambda x: x["score"])["score"]
            draw_text(self.screen, f"Personal best: {best}", self.fonts["sm"],
                      C_ACCENT, W//2, 345, center=True)

        btn_retry = pygame.Rect(W//2 - 220, 400, 200, 50)
        btn_menu  = pygame.Rect(W//2 + 20,  400, 200, 50)
        draw_button(self.screen, btn_retry, "↺  Retry",     self.fonts["md"],
                    hover=btn_retry.collidepoint(mx, my))
        draw_button(self.screen, btn_menu,  "⌂  Main Menu", self.fonts["md"],
                    hover=btn_menu.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_retry.collidepoint(mx, my):
                    self._start_game()
                elif btn_menu.collidepoint(mx, my):
                    self.state = "menu"

    # ── LEADERBOARD ────────────────────────────────────────────

    def _leaderboard(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W

        draw_text(self.screen, "🏆 TOP 10", self.fonts["lg"],
                  C_ACCENT, W//2, 30, center=True)

        board = load_leaderboard()
        headers = ["#", "Name", "Score", "Distance", "Coins", "Date"]
        col_x   = [60, 120, 300, 400, 490, 570]
        y0      = 100

        # Header
        for i, h in enumerate(headers):
            draw_text(self.screen, h, self.fonts["sm"],
                      (150,150,200), col_x[i], y0)

        pygame.draw.line(self.screen, C_BORDER, (50, y0+22), (W-50, y0+22), 1)

        for rank, entry in enumerate(board, 1):
            y    = y0 + 30 + (rank-1) * 36
            color = C_ACCENT if entry.get("username") == self.username else C_TEXT
            row  = [str(rank), entry["username"], str(entry["score"]),
                    f"{entry['distance']}m", str(entry["coins"]), entry["date"][:10]]
            for i, val in enumerate(row):
                draw_text(self.screen, val, self.fonts["sm"], color, col_x[i], y)

        btn_back = pygame.Rect(W//2 - 100, WIN_H - 70, 200, 46)
        draw_button(self.screen, btn_back, "← Back", self.fonts["md"],
                    hover=btn_back.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.collidepoint(mx, my):
                    self.state = "menu"
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = "menu"

    # ── SETTINGS ───────────────────────────────────────────────

    def _settings(self, events, mx, my):
        self.screen.fill(C_BG)
        W = WIN_W

        draw_text(self.screen, "⚙ Settings", self.fonts["lg"],
                  C_ACCENT, W//2, 40, center=True)

        # Sound toggle
        sound_rect = pygame.Rect(W//2 - 120, 130, 240, 46)
        sound_lbl  = f"Sound: {'ON' if self.settings['sound'] else 'OFF'}"
        draw_button(self.screen, sound_rect, sound_lbl, self.fonts["md"],
                    active=self.settings["sound"],
                    hover=sound_rect.collidepoint(mx, my))

        # Car colour
        draw_text(self.screen, "Car Color:", self.fonts["md"],
                  C_TEXT, W//2, 210, center=True)
        color_rects = {}
        cx0 = W//2 - (len(COLOR_OPTIONS) * 56) // 2
        for i, (name, col) in enumerate(COLOR_OPTIONS.items()):
            r = pygame.Rect(cx0 + i*56, 248, 48, 48)
            color_rects[name] = (r, col)
            sel = list(self.settings["car_color"]) == list(col)
            pygame.draw.rect(self.screen, col, r, border_radius=8)
            pygame.draw.rect(self.screen,
                             C_ACCENT if sel else C_BORDER, r, 3, border_radius=8)

        # Difficulty
        draw_text(self.screen, "Difficulty:", self.fonts["md"],
                  C_TEXT, W//2, 330, center=True)
        diff_rects = {}
        diffs = ["easy", "normal", "hard"]
        for i, d in enumerate(diffs):
            r = pygame.Rect(W//2 - 180 + i*130, 365, 110, 42)
            diff_rects[d] = r
            draw_button(self.screen, r, d.capitalize(), self.fonts["sm"],
                        active=(self.settings["difficulty"] == d),
                        hover=r.collidepoint(mx, my))

        # Save & Back
        btn_save = pygame.Rect(W//2 - 120, WIN_H - 80, 240, 48)
        draw_button(self.screen, btn_save, "💾 Save & Back", self.fonts["md"],
                    hover=btn_save.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if sound_rect.collidepoint(mx, my):
                    self.settings["sound"] = not self.settings["sound"]
                for name, (r, col) in color_rects.items():
                    if r.collidepoint(mx, my):
                        self.settings["car_color"] = list(col)
                for d, r in diff_rects.items():
                    if r.collidepoint(mx, my):
                        self.settings["difficulty"] = d
                if btn_save.collidepoint(mx, my):
                    save_settings(self.settings)
                    self.state = "menu"
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = "menu"



if __name__ == "__main__":
    App().run()

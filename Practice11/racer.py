"""
Practice 11 — Racer
Extends Practice 10 with:
  1. Weighted coins (gold=1, silver=3, blue=5)
  2. Enemy speed increases every N coins collected
  3. Comments throughout
"""

import pygame
import random
import sys

# ── Window and road layout ─────────────────────────────────────
WIN_W      = 600          # window width  in pixels
WIN_H      = 700          # window height in pixels
ROAD_X     = 100          # left edge of the road
ROAD_W     = 400          # road width in pixels
LANE_COUNT = 4            # number of lanes
LANE_W     = ROAD_W // LANE_COUNT  # width of one lane

FPS        = 60           # frames per second

# How many coins the player must collect before enemies speed up
SPEED_UP_EVERY = 5

# ── Colours ────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GRAY       = (80,  80,  80)
DARK_GRAY  = (50,  50,  50)
YELLOW     = (240, 200,  40)
RED        = (220,  50,  50)
BLUE_CAR   = (50,  130, 220)
ROAD_COL   = (60,  60,  65)
LINE_COL   = (200, 200, 200)
HUD_COL    = (20,  20,  30)

# Coin type definitions: (point value, display colour, label)
COIN_TYPES = [
    (1, (255, 215,   0), "1"),   # gold   — common
    (3, (200, 200, 200), "3"),   # silver — uncommon
    (5, ( 80, 180, 255), "5"),   # blue   — rare
]


def lane_center(lane: int) -> int:
    """Return the screen-x centre of the given lane (0-indexed)."""
    return ROAD_X + lane * LANE_W + LANE_W // 2


# ══════════════════════════════════════════════════════════════
#  ROAD — scrolling lane dividers
# ══════════════════════════════════════════════════════════════

class Road:
    STRIPE_H   = 50   # height of a white stripe
    STRIPE_GAP = 40   # gap between stripes

    def __init__(self):
        self.offset = 0   # current scroll offset in pixels

    def update(self, speed: float):
        """Advance the scroll offset by `speed` pixels."""
        self.offset = (self.offset + speed) % (self.STRIPE_H + self.STRIPE_GAP)

    def draw(self, surface):
        # Asphalt rectangle
        pygame.draw.rect(surface, ROAD_COL, (ROAD_X, 0, ROAD_W, WIN_H))

        # Yellow road edges
        pygame.draw.rect(surface, YELLOW, (ROAD_X,            0, 6, WIN_H))
        pygame.draw.rect(surface, YELLOW, (ROAD_X + ROAD_W - 6, 0, 6, WIN_H))

        # Dashed lane dividers
        for lane in range(1, LANE_COUNT):
            lx = ROAD_X + lane * LANE_W
            y  = -self.offset          # start slightly above screen
            while y < WIN_H:
                pygame.draw.rect(surface, LINE_COL,
                                 (lx - 2, y, 4, self.STRIPE_H))
                y += self.STRIPE_H + self.STRIPE_GAP


# ══════════════════════════════════════════════════════════════
#  PLAYER CAR
# ══════════════════════════════════════════════════════════════

class Player:
    W, H = 44, 70   # car width and height in pixels

    def __init__(self):
        self.lane     = 1                       # start in lane 1
        self.x        = float(lane_center(1))   # smooth x position
        self.y        = WIN_H - 120             # fixed y near bottom
        self.target_x = self.x                  # destination x for smooth slide
        self.slide_speed = 6                    # pixels per frame for lane switch

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - self.W // 2,
                           int(self.y) - self.H // 2,
                           self.W, self.H)

    def move_left(self):
        """Switch one lane to the left if possible."""
        if self.lane > 0:
            self.lane    -= 1
            self.target_x = lane_center(self.lane)

    def move_right(self):
        """Switch one lane to the right if possible."""
        if self.lane < LANE_COUNT - 1:
            self.lane    += 1
            self.target_x = lane_center(self.lane)

    def update(self):
        """Smoothly slide the car toward the target lane centre."""
        diff = self.target_x - self.x
        if abs(diff) < self.slide_speed:
            self.x = self.target_x          # snap when close enough
        else:
            self.x += self.slide_speed * (1 if diff > 0 else -1)

    def draw(self, surface):
        r = self.rect
        # Car body
        pygame.draw.rect(surface, BLUE_CAR, r, border_radius=8)
        # Windshield
        pygame.draw.rect(surface, (180, 230, 255),
                         (r.x + 6, r.y + 8, r.w - 12, 18), border_radius=4)
        # Four wheels (small black rectangles on the sides)
        wheel_col = (20, 20, 20)
        for wx, wy in [(r.x - 7, r.y + 10), (r.right - 3, r.y + 10),
                       (r.x - 7, r.bottom - 26), (r.right - 3, r.bottom - 26)]:
            pygame.draw.rect(surface, wheel_col, (wx, wy, 10, 16), border_radius=3)


# ══════════════════════════════════════════════════════════════
#  ENEMY CAR
# ══════════════════════════════════════════════════════════════

ENEMY_COLORS = [
    (220,  60,  60),
    (60,  200,  60),
    (220, 160,  40),
    (180,  60, 180),
]

class Enemy:
    W, H = 44, 68

    def __init__(self, speed: float):
        self.lane  = random.randint(0, LANE_COUNT - 1)
        self.x     = float(lane_center(self.lane))
        self.y     = float(-self.H)              # start just above screen
        self.speed = speed                        # downward speed (px/frame)
        self.color = random.choice(ENEMY_COLORS)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - self.W // 2,
                           int(self.y) - self.H // 2,
                           self.W, self.H)

    def update(self):
        """Move downward each frame."""
        self.y += self.speed

    def is_off_screen(self) -> bool:
        return self.y > WIN_H + self.H

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, self.color, r, border_radius=8)
        pygame.draw.rect(surface, (180, 230, 255),
                         (r.x + 6, r.y + 8, r.w - 12, 18), border_radius=4)
        wheel_col = (20, 20, 20)
        for wx, wy in [(r.x - 7, r.y + 10), (r.right - 3, r.y + 10),
                       (r.x - 7, r.bottom - 26), (r.right - 3, r.bottom - 26)]:
            pygame.draw.rect(surface, wheel_col, (wx, wy, 10, 16), border_radius=3)


# ══════════════════════════════════════════════════════════════
#  COIN  — weighted: gold(1pt), silver(3pt), blue(5pt)
# ══════════════════════════════════════════════════════════════

class Coin:
    R = 14   # coin radius in pixels

    def __init__(self, speed: float):
        # Choose coin type by weighted probability:
        # gold=60%, silver=30%, blue=10%
        idx = random.choices([0, 1, 2], weights=[60, 30, 10])[0]
        self.value  = COIN_TYPES[idx][0]   # point value
        self.color  = COIN_TYPES[idx][1]   # display colour
        self.label  = COIN_TYPES[idx][2]   # text shown on coin

        self.lane  = random.randint(0, LANE_COUNT - 1)
        self.x     = float(lane_center(self.lane))
        self.y     = float(-self.R)        # start above screen
        self.speed = speed

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - self.R, int(self.y) - self.R,
                           self.R * 2, self.R * 2)

    def update(self):
        self.y += self.speed

    def is_off_screen(self) -> bool:
        return self.y > WIN_H + self.R

    def draw(self, surface, font):
        cx, cy = int(self.x), int(self.y)
        # Filled circle
        pygame.draw.circle(surface, self.color, (cx, cy), self.R)
        # White border
        pygame.draw.circle(surface, WHITE, (cx, cy), self.R, 2)
        # Point value label in the centre
        txt = font.render(self.label, True, BLACK)
        surface.blit(txt, (cx - txt.get_width() // 2,
                           cy - txt.get_height() // 2))


# ══════════════════════════════════════════════════════════════
#  MAIN GAME
# ══════════════════════════════════════════════════════════════

class RacerGame:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Racer — Practice 11")
        self.clock  = pygame.time.Clock()

        # Fonts
        self.font_sm = pygame.font.SysFont("segoeui", 16)
        self.font_md = pygame.font.SysFont("segoeui", 22, bold=True)
        self.font_lg = pygame.font.SysFont("segoeui", 40, bold=True)

        self._init_game()

    def _init_game(self):
        """Reset all game state for a new game or restart."""
        self.road         = Road()
        self.player       = Player()
        self.enemies      : list[Enemy] = []
        self.coins        : list[Coin]  = []

        self.scroll_speed = 4.0    # base road scroll speed (px/frame)
        self.enemy_speed  = 4.5    # current enemy movement speed

        self.score        = 0      # total points from coins
        self.coins_total  = 0      # total coins collected (used for speed trigger)
        self.alive        = True

        # Spawn timers (milliseconds)
        now = pygame.time.get_ticks()
        self.next_enemy = now + 1500   # first enemy after 1.5 s
        self.next_coin  = now + 800    # first coin  after 0.8 s

        # Key-repeat guard: timestamp of last lane switch
        self.last_key_time = 0
        self.key_delay     = 180       # ms between accepted key presses

    # ── Spawning ───────────────────────────────────────────────

    def _spawn_enemy(self):
        """Spawn an enemy car that doesn't share a lane with a recent enemy."""
        occupied = {e.lane for e in self.enemies if e.y < WIN_H * 0.3}
        free     = [l for l in range(LANE_COUNT) if l not in occupied]
        if not free:
            return
        e      = Enemy(self.enemy_speed)
        e.lane = random.choice(free)
        e.x    = float(lane_center(e.lane))
        self.enemies.append(e)

    def _spawn_coin(self):
        """Spawn a weighted coin on the road."""
        self.coins.append(Coin(self.scroll_speed * 0.9))

    # ── Speed scaling ──────────────────────────────────────────

    def _check_speed_up(self):
        """Increase enemy speed every SPEED_UP_EVERY coins collected."""
        # Integer-divide tells us how many thresholds have been crossed
        thresholds_crossed = self.coins_total // SPEED_UP_EVERY
        # Base speed + 0.4 per threshold
        new_enemy_speed = 4.5 + thresholds_crossed * 0.4
        if new_enemy_speed != self.enemy_speed:
            self.enemy_speed = new_enemy_speed
            # Apply new speed to already-spawned enemies too
            for e in self.enemies:
                e.speed = self.enemy_speed

    # ── Update ─────────────────────────────────────────────────

    def update(self):
        now = pygame.time.get_ticks()

        # Spawn enemies on a timer
        if now >= self.next_enemy:
            self._spawn_enemy()
            self.next_enemy = now + random.randint(1000, 1800)

        # Spawn coins on a timer
        if now >= self.next_coin:
            self._spawn_coin()
            self.next_coin = now + random.randint(600, 1200)

        # Scroll the road
        self.road.update(self.scroll_speed)

        # Update player (smooth lane slide)
        self.player.update()

        pr = self.player.rect   # player rectangle for collision checks

        # Update enemies, check collision
        for e in self.enemies[:]:
            e.update()
            if e.is_off_screen():
                self.enemies.remove(e)
                continue
            if pr.colliderect(e.rect):
                self.alive = False   # collision → game over

        # Update coins, check collection
        for c in self.coins[:]:
            c.update()
            if c.is_off_screen():
                self.coins.remove(c)
                continue
            if pr.colliderect(c.rect):
                self.score       += c.value    # add weighted points
                self.coins_total += c.value    # track total for speed trigger
                self.coins.remove(c)
                self._check_speed_up()         # maybe increase enemy speed

    # ── Draw ───────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(DARK_GRAY)         # background outside road
        self.road.draw(self.screen)

        for e in self.enemies:
            e.draw(self.screen)
        for c in self.coins:
            c.draw(self.screen, self.font_sm)
        self.player.draw(self.screen)

        self._draw_hud()

    def _draw_hud(self):
        """Draw score, coin count, enemy speed info at the top."""
        pygame.draw.rect(self.screen, HUD_COL, (0, 0, WIN_W, 50))

        self.screen.blit(
            self.font_md.render(f"Score: {self.score}", True, WHITE), (10, 12))
        self.screen.blit(
            self.font_sm.render(f"Coins: {self.coins_total}", True, YELLOW), (200, 15))
        self.screen.blit(
            self.font_sm.render(f"Enemy speed: {self.enemy_speed:.1f}", True, (200,200,200)),
            (340, 15))
        self.screen.blit(
            self.font_sm.render("← → to move", True, (120,120,150)),
            (WIN_W - 140, 15))

    def _draw_gameover(self):
        """Overlay a game-over message."""
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        self.screen.blit(
            self.font_lg.render("GAME OVER", True, RED),
            (WIN_W//2 - 120, WIN_H//2 - 60))
        self.screen.blit(
            self.font_md.render(f"Score: {self.score}", True, WHITE),
            (WIN_W//2 - 60, WIN_H//2))
        self.screen.blit(
            self.font_sm.render("Press R to restart  or  ESC to quit", True, WHITE),
            (WIN_W//2 - 160, WIN_H//2 + 50))

    # ── Input ──────────────────────────────────────────────────

    def handle_keys(self):
        """Handle lane-switch key presses with a small delay to avoid
        switching multiple lanes per key tap."""
        now  = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        if now - self.last_key_time > self.key_delay:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.move_left()
                self.last_key_time = now
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.move_right()
                self.last_key_time = now

    # ── Main loop ──────────────────────────────────────────────

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    # Restart after game over
                    if not self.alive and event.key == pygame.K_r:
                        self._init_game()

            if self.alive:
                self.handle_keys()
                self.update()

            self.draw()

            if not self.alive:
                self._draw_gameover()

            pygame.display.flip()
            self.clock.tick(FPS)


# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    RacerGame().run()

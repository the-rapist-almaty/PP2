"""
racer.py — Game objects: Player, Enemy, Coin, Obstacle, PowerUp, Road.
"""

import pygame
import random

# Lane layout 
WIN_W, WIN_H = 800, 650
HUD_H        = 60
ROAD_X       = 150
ROAD_W       = 500
LANE_COUNT   = 4
LANE_W       = ROAD_W // LANE_COUNT

def lane_center(lane: int) -> int:
    """Return screen-x center of a lane (0-indexed)."""
    return ROAD_X + lane * LANE_W + LANE_W // 2


#  ROAD (scrolling stripes)

class Road:
    STRIPE_H  = 60
    STRIPE_GAP= 40

    def __init__(self):
        self.offset = 0

    def update(self, speed):
        self.offset = (self.offset + speed) % (self.STRIPE_H + self.STRIPE_GAP)

    def draw(self, surface):
        # Asphalt
        pygame.draw.rect(surface, (50, 50, 55),
                         (ROAD_X, HUD_H, ROAD_W, WIN_H - HUD_H))
        # Road edges
        pygame.draw.rect(surface, (200, 200, 50),
                         (ROAD_X, HUD_H, 6, WIN_H - HUD_H))
        pygame.draw.rect(surface, (200, 200, 50),
                         (ROAD_X + ROAD_W - 6, HUD_H, 6, WIN_H - HUD_H))

        # Lane dividers
        for lane in range(1, LANE_COUNT):
            lx = ROAD_X + lane * LANE_W
            y  = HUD_H - self.offset
            while y < WIN_H:
                pygame.draw.rect(surface, (180, 180, 180),
                                 (lx - 2, y, 4, self.STRIPE_H))
                y += self.STRIPE_H + self.STRIPE_GAP


#  PLAYER CAR

class Player:
    W, H = 44, 70

    def __init__(self, color):
        self.lane    = 1
        self.color   = tuple(color)
        self.x       = float(lane_center(self.lane))
        self.y       = float(WIN_H - 110)
        self.target_x= self.x
        self.speed   = 6      # lane-switch animation speed
        self.shield  = False
        self.nitro   = False
        self.alive   = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - self.W//2,
                           int(self.y) - self.H//2, self.W, self.H)

    def move_left(self):
        if self.lane > 0:
            self.lane    -= 1
            self.target_x = lane_center(self.lane)

    def move_right(self):
        if self.lane < LANE_COUNT - 1:
            self.lane    += 1
            self.target_x = lane_center(self.lane)

    def update(self):
        # Smooth lane transition
        dx = self.target_x - self.x
        if abs(dx) < self.speed:
            self.x = self.target_x
        else:
            self.x += self.speed * (1 if dx > 0 else -1)

    def draw(self, surface):
        r = self.rect
        # Body
        pygame.draw.rect(surface, self.color, r, border_radius=8)
        # Windshield
        pygame.draw.rect(surface, (150, 220, 255),
                         (r.x+6, r.y+8, r.w-12, 18), border_radius=4)
        # Wheels
        wc = (30, 30, 30)
        for wx, wy in [(r.x-6, r.y+10), (r.right, r.y+10),
                       (r.x-6, r.bottom-22), (r.right, r.bottom-22)]:
            pygame.draw.rect(surface, wc, (wx, wy, 10, 16), border_radius=3)
        # Shield glow
        if self.shield:
            pygame.draw.ellipse(surface, (100, 200, 255),
                                r.inflate(16, 16), 3)


#  ENEMY CAR

ENEMY_COLORS = [
    (220, 60,  60),  (60,  180, 60),  (220, 160, 40),
    (180, 60, 180),  (40,  180, 220), (200, 100, 40),
]

class Enemy:
    W, H = 44, 68

    def __init__(self, speed):
        self.lane  = random.randint(0, LANE_COUNT - 1)
        self.x     = float(lane_center(self.lane))
        self.y     = float(HUD_H - self.H)
        self.speed = speed
        self.color = random.choice(ENEMY_COLORS)

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - self.W//2,
                           int(self.y) - self.H//2, self.W, self.H)

    def update(self):
        self.y += self.speed

    def is_off_screen(self):
        return self.y > WIN_H + self.H

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, self.color, r, border_radius=8)
        pygame.draw.rect(surface, (150, 220, 255),
                         (r.x+6, r.y+8, r.w-12, 18), border_radius=4)
        wc = (30, 30, 30)
        for wx, wy in [(r.x-6, r.y+10), (r.right, r.y+10),
                       (r.x-6, r.bottom-22), (r.right, r.bottom-22)]:
            pygame.draw.rect(surface, wc, (wx, wy, 10, 16), border_radius=3)


#  COIN

COIN_WEIGHTS = [(1, (255, 215, 0)),   # gold  — 1 pt
                (3, (200, 200, 200)), # silver — 3 pts
                (5, (100, 220, 255))] # blue   — 5 pts

class Coin:
    R = 12

    def __init__(self, speed):
        weight_idx = random.choices([0, 1, 2], weights=[60, 30, 10])[0]
        self.value, self.color = COIN_WEIGHTS[weight_idx]
        self.lane  = random.randint(0, LANE_COUNT - 1)
        self.x     = float(lane_center(self.lane))
        self.y     = float(HUD_H - self.R)
        self.speed = speed

    @property
    def rect(self):
        return pygame.Rect(int(self.x)-self.R, int(self.y)-self.R,
                           self.R*2, self.R*2)

    def update(self):
        self.y += self.speed

    def is_off_screen(self):
        return self.y > WIN_H + self.R

    def draw(self, surface):
        pygame.draw.circle(surface, self.color,
                           (int(self.x), int(self.y)), self.R)
        pygame.draw.circle(surface, (255, 255, 255),
                           (int(self.x), int(self.y)), self.R, 2)
        # Value label
        font = pygame.font.SysFont("segoeui", 11, bold=True)
        txt  = font.render(str(self.value), True, (0, 0, 0))
        surface.blit(txt, (int(self.x) - txt.get_width()//2,
                           int(self.y) - txt.get_height()//2))


#  OBSTACLE  (oil spill / barrier)

class Obstacle:
    W, H = 50, 28

    def __init__(self, speed):
        self.lane  = random.randint(0, LANE_COUNT - 1)
        self.x     = float(lane_center(self.lane))
        self.y     = float(HUD_H - self.H)
        self.speed = speed
        self.kind  = random.choice(["oil", "barrier"])

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - self.W//2,
                           int(self.y) - self.H//2, self.W, self.H)

    def update(self):
        self.y += self.speed

    def is_off_screen(self):
        return self.y > WIN_H + self.H

    def draw(self, surface):
        r = self.rect
        if self.kind == "oil":
            pygame.draw.ellipse(surface, (20, 20, 80), r)
            pygame.draw.ellipse(surface, (60, 60, 160), r, 2)
        else:
            pygame.draw.rect(surface, (220, 60, 60), r, border_radius=4)
            pygame.draw.rect(surface, (255, 200, 50), r, 3, border_radius=4)


#  POWER-UP

POWERUP_TYPES = {
    "nitro":  {"color": (255, 140, 0),   "label": "N", "duration": 4000},
    "shield": {"color": (100, 200, 255), "label": "S", "duration": 0},     # until hit
    "repair": {"color": (80,  220, 80),  "label": "R", "duration": 0},     # instant
}

class PowerUp:
    W, H    = 32, 32
    TIMEOUT = 8000   # ms before disappearing if not collected

    def __init__(self, speed):
        self.kind   = random.choice(list(POWERUP_TYPES.keys()))
        self.info   = POWERUP_TYPES[self.kind]
        self.lane   = random.randint(0, LANE_COUNT - 1)
        self.x      = float(lane_center(self.lane))
        self.y      = float(HUD_H - self.H)
        self.speed  = speed
        self.born   = pygame.time.get_ticks()

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - self.W//2,
                           int(self.y) - self.H//2, self.W, self.H)

    def update(self):
        self.y += self.speed

    def is_expired(self):
        return pygame.time.get_ticks() - self.born > self.TIMEOUT

    def is_off_screen(self):
        return self.y > WIN_H + self.H

    def draw(self, surface):
        r    = self.rect
        col  = self.info["color"]
        lbl  = self.info["label"]
        pygame.draw.rect(surface, col, r, border_radius=6)
        pygame.draw.rect(surface, (255,255,255), r, 2, border_radius=6)
        font = pygame.font.SysFont("segoeui", 18, bold=True)
        txt  = font.render(lbl, True, (0, 0, 0))
        surface.blit(txt, (r.centerx - txt.get_width()//2,
                           r.centery - txt.get_height()//2))
        # Timeout bar
        elapsed  = pygame.time.get_ticks() - self.born
        frac     = max(0, 1 - elapsed / self.TIMEOUT)
        bar_w    = int(self.W * frac)
        pygame.draw.rect(surface, (255, 255, 100),
                         (r.x, r.bottom + 2, bar_w, 4))

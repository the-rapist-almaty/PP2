"""
game.py — Snake game logic.
Handles: snake movement, food (weighted + disappearing),
         poison food, power-ups, obstacles (level 3+).
"""

import pygame
import random
from config import COLS, ROWS, CELL, GRID_X, GRID_Y, FPS

# ── Directions ───────────────────────────
UP    = (0, -1)
DOWN  = (0,  1)
LEFT  = (-1, 0)
RIGHT = (1,  0)

# ── Food types: (points, color, label)────
FOOD_TYPES = [
    (1,  (255, 80,  80),  "●"),   # red    — common
    (3,  (255, 200, 40),  "★"),   # yellow — uncommon
    (5,  (100, 220, 255), "♦"),   # cyan   — rare
]
FOOD_WEIGHTS     = [60, 30, 10]
FOOD_LIFETIME_MS = 7000   # disappearing food timer

# ── Power-up types ───────────────────────
PU_TYPES = ["speed_boost", "slow_motion", "shield"]
PU_COLORS = {
    "speed_boost": (255, 140,  0),
    "slow_motion": (140,  80, 220),
    "shield":      (80,  180, 255),
}
PU_LABELS = {
    "speed_boost": "⚡",
    "slow_motion": "🐢",
    "shield":      "🛡",
}
PU_DURATION_MS  = 5000
PU_LIFETIME_MS  = 8000


def cell_to_pixel(cx, cy):
    """Convert grid cell (col, row) to top-left pixel on screen."""
    return (GRID_X + cx * CELL, GRID_Y + cy * CELL)


class Food:
    def __init__(self, pos, disappearing=False):
        idx              = random.choices([0, 1, 2], weights=FOOD_WEIGHTS)[0]
        self.points, self.color, self.label = FOOD_TYPES[idx]
        self.pos         = pos
        self.disappearing= disappearing
        self.born        = pygame.time.get_ticks()

    def is_expired(self):
        if not self.disappearing:
            return False
        return pygame.time.get_ticks() - self.born > FOOD_LIFETIME_MS

    def time_left_frac(self):
        if not self.disappearing:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.born
        return max(0.0, 1.0 - elapsed / FOOD_LIFETIME_MS)

    def draw(self, surface, font):
        px, py = cell_to_pixel(*self.pos)
        pygame.draw.rect(surface, self.color,
                         (px+2, py+2, CELL-4, CELL-4), border_radius=5)
        # Timer bar for disappearing food
        if self.disappearing:
            frac = self.time_left_frac()
            pygame.draw.rect(surface, (255, 255, 100),
                             (px, py + CELL - 3, int(CELL * frac), 3))


class PoisonFood:
    COLOR = (140, 20, 20)

    def __init__(self, pos):
        self.pos  = pos
        self.born = pygame.time.get_ticks()

    def draw(self, surface, font):
        px, py = cell_to_pixel(*self.pos)
        pygame.draw.rect(surface, self.COLOR,
                         (px+2, py+2, CELL-4, CELL-4), border_radius=5)
        txt = font.render("☠", True, (200, 60, 60))
        surface.blit(txt, (px + CELL//2 - txt.get_width()//2,
                           py + CELL//2 - txt.get_height()//2))


class PowerUp:
    def __init__(self, pos, kind):
        self.pos   = pos
        self.kind  = kind
        self.color = PU_COLORS[kind]
        self.label = PU_LABELS[kind]
        self.born  = pygame.time.get_ticks()

    def is_expired(self):
        return pygame.time.get_ticks() - self.born > PU_LIFETIME_MS

    def draw(self, surface, font):
        px, py = cell_to_pixel(*self.pos)
        pygame.draw.rect(surface, self.color,
                         (px+1, py+1, CELL-2, CELL-2), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255),
                         (px+1, py+1, CELL-2, CELL-2), 2, border_radius=6)
        # Timeout bar
        elapsed = pygame.time.get_ticks() - self.born
        frac    = max(0, 1 - elapsed / PU_LIFETIME_MS)
        pygame.draw.rect(surface, (255, 255, 100),
                         (px, py + CELL - 3, int(CELL * frac), 3))


class SnakeGame:
    # Base move interval in ms per level
    BASE_INTERVAL = 180
    SPEED_STEP    = 18    # ms faster per level
    MIN_INTERVAL  = 60

    def __init__(self, username, settings, personal_best):
        self.username     = username
        self.settings     = settings
        self.personal_best= personal_best

        # Snake starts in the middle
        sx, sy = COLS // 2, ROWS // 2
        self.body      = [(sx, sy), (sx-1, sy), (sx-2, sy)]
        self.direction = RIGHT
        self.next_dir  = RIGHT
        self.alive     = True

        # Scoring / progression
        self.score     = 0
        self.level     = 1
        self.food_eaten= 0
        self.food_per_level = 4

        # Timing
        self.last_move = pygame.time.get_ticks()
        self.interval  = self.BASE_INTERVAL

        # Objects
        self.foods    : list[Food]     = []
        self.poison   : list[PoisonFood] = []
        self.powerups : list[PowerUp]  = []
        self.obstacles: list[tuple]    = []   # list of (col, row)

        # Active power-up effect
        self.shield_active   = False
        self.pu_effect       = None   # "speed_boost" | "slow_motion"
        self.pu_effect_end   = 0
        self.pu_spawn_next   = pygame.time.get_ticks() + 10000

        # Spawn initial food
        self._spawn_food(disappearing=False)
        self._spawn_food(disappearing=True)

        # Font for food icons
        self.icon_font = pygame.font.SysFont("segoeuiemoji", CELL - 4)

    # ── Occupied cells ───────────────────

    def _occupied(self):
        s = set(self.body)
        s.update(self.obstacles)
        s.update(f.pos for f in self.foods)
        s.update(p.pos for p in self.poison)
        s.update(p.pos for p in self.powerups)
        return s

    def _random_free_cell(self):
        occ = self._occupied()
        free = [(c, r) for c in range(COLS) for r in range(ROWS)
                if (c, r) not in occ]
        return random.choice(free) if free else None

    # ── Spawning ─────────────────────────

    def _spawn_food(self, disappearing=False):
        pos = self._random_free_cell()
        if pos:
            self.foods.append(Food(pos, disappearing))

    def _spawn_poison(self):
        pos = self._random_free_cell()
        if pos:
            self.poison.append(PoisonFood(pos))

    def _spawn_powerup(self):
        if not self.powerups:
            pos  = self._random_free_cell()
            kind = random.choice(PU_TYPES)
            if pos:
                self.powerups.append(PowerUp(pos, kind))

    def _spawn_obstacles(self):
        """Randomly place obstacles; guarantee they don't trap the snake head."""
        head        = self.body[0]
        safe_radius = 4
        count       = 3 + self.level
        occ         = self._occupied()
        candidates  = [
            (c, r) for c in range(COLS) for r in range(ROWS)
            if (c, r) not in occ
            and abs(c - head[0]) + abs(r - head[1]) > safe_radius
        ]
        random.shuffle(candidates)
        for pos in candidates[:count]:
            self.obstacles.append(pos)

    # ── Level up ─────────────────────────

    def _level_up(self):
        self.level     += 1
        self.food_eaten = 0
        self.interval   = max(self.MIN_INTERVAL,
                              self.BASE_INTERVAL - (self.level-1) * self.SPEED_STEP)
        if self.level >= 3:
            self.obstacles.clear()
            self._spawn_obstacles()

    # ── Power-up application ─────────────

    def _apply_powerup(self, kind):
        now = pygame.time.get_ticks()
        if kind == "speed_boost":
            self.pu_effect     = "speed_boost"
            self.pu_effect_end = now + PU_DURATION_MS
            self.interval      = max(self.MIN_INTERVAL, self.interval // 2)
        elif kind == "slow_motion":
            self.pu_effect     = "slow_motion"
            self.pu_effect_end = now + PU_DURATION_MS
            self.interval      = min(300, self.interval * 2)
        elif kind == "shield":
            self.shield_active = True

    def _check_pu_expiry(self):
        now = pygame.time.get_ticks()
        if self.pu_effect and now > self.pu_effect_end:
            # Restore base interval for level
            self.interval  = max(self.MIN_INTERVAL,
                                 self.BASE_INTERVAL - (self.level-1) * self.SPEED_STEP)
            self.pu_effect = None

    # ── Direction ────────────────────────

    def set_direction(self, new_dir):
        # Prevent reversing
        if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
            self.next_dir = new_dir

    # ── Main update ──────────────────────

    def update(self):
        now = pygame.time.get_ticks()

        self._check_pu_expiry()

        # Remove expired disappearing foods
        for f in self.foods[:]:
            if f.is_expired():
                self.foods.remove(f)
                self._spawn_food(disappearing=True)

        # Remove expired power-ups on field
        for p in self.powerups[:]:
            if p.is_expired():
                self.powerups.remove(p)

        # Spawn power-up periodically
        if now >= self.pu_spawn_next:
            self._spawn_powerup()
            self._spawn_poison()
            self.pu_spawn_next = now + random.randint(10000, 16000)

        # Move snake at interval
        if now - self.last_move < self.interval:
            return
        self.last_move = now
        self.direction = self.next_dir

        head     = self.body[0]
        new_head = (head[0] + self.direction[0],
                    head[1] + self.direction[1])

        # Border collision
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            if self.shield_active:
                self.shield_active = False
            else:
                self.alive = False
                return

        # Self collision
        if new_head in self.body[1:]:
            if self.shield_active:
                self.shield_active = False
            else:
                self.alive = False
                return

        # Obstacle collision
        if new_head in self.obstacles:
            if self.shield_active:
                self.shield_active = False
            else:
                self.alive = False
                return

        self.body.insert(0, new_head)
        grew = False

        # Eat normal food
        for f in self.foods[:]:
            if new_head == f.pos:
                self.score     += f.points
                self.food_eaten+= 1
                self.foods.remove(f)
                grew = True
                # Ensure there are always 2 foods
                self._spawn_food(disappearing=False)
                if len([x for x in self.foods if x.disappearing]) < 1:
                    self._spawn_food(disappearing=True)
                if self.food_eaten >= self.food_per_level:
                    self._level_up()
                break

        # Eat poison food
        for p in self.poison[:]:
            if new_head == p.pos:
                self.poison.remove(p)
                grew = True   # head already added, but we remove 3 from tail
                # Shorten by 2 extra segments
                for _ in range(2):
                    if len(self.body) > 1:
                        self.body.pop()
                if len(self.body) <= 1:
                    self.alive = False
                    return
                break

        # Collect power-up
        for pu in self.powerups[:]:
            if new_head == pu.pos:
                self._apply_powerup(pu.kind)
                self.powerups.remove(pu)
                grew = True
                break

        if not grew:
            self.body.pop()

    # ── Draw ─────────────────────────────

    def draw(self, surface, show_grid):
        # Grid overlay
        if show_grid:
            for c in range(COLS + 1):
                x = GRID_X + c * CELL
                pygame.draw.line(surface, (40, 50, 40),
                                 (x, GRID_Y), (x, GRID_Y + ROWS * CELL))
            for r in range(ROWS + 1):
                y = GRID_Y + r * CELL
                pygame.draw.line(surface, (40, 50, 40),
                                 (GRID_X, y), (GRID_X + COLS * CELL, y))

        # Arena border
        pygame.draw.rect(surface, (80, 160, 80),
                         (GRID_X - 2, GRID_Y - 2,
                          COLS * CELL + 4, ROWS * CELL + 4), 3)

        # Obstacles
        for (c, r) in self.obstacles:
            px, py = cell_to_pixel(c, r)
            pygame.draw.rect(surface, (90, 70, 50),
                             (px, py, CELL, CELL))
            pygame.draw.rect(surface, (60, 40, 20),
                             (px, py, CELL, CELL), 2)

        # Food
        for f in self.foods:
            f.draw(surface, self.icon_font)

        # Poison
        for p in self.poison:
            p.draw(surface, self.icon_font)

        # Power-ups
        for pu in self.powerups:
            pu.draw(surface, self.icon_font)

        # Snake body
        snake_color = tuple(self.settings.get("snake_color", [60, 200, 100]))
        for i, (c, r) in enumerate(self.body):
            px, py = cell_to_pixel(c, r)
            col = snake_color if i > 0 else (
                (80, 220, 255) if self.shield_active else
                tuple(min(255, v + 60) for v in snake_color)
            )
            pygame.draw.rect(surface, col,
                             (px+1, py+1, CELL-2, CELL-2),
                             border_radius=4)
            if i == 0:
                # Eyes
                pygame.draw.circle(surface, (0, 0, 0),
                                   (px + CELL//3, py + CELL//3), 3)
                pygame.draw.circle(surface, (0, 0, 0),
                                   (px + 2*CELL//3, py + CELL//3), 3)

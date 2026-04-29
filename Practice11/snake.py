"""
Practice 11 — Snake
Extends Practice 10 with:
  1. Food with different weights (normal=1, bonus=3, rare=5)
  2. Higher-value food disappears after a timer
  3. Comments throughout
"""

import pygame
import random
import sys

# ── Grid settings ──────────────────────────────────────────────
CELL   = 24        # size of one grid cell in pixels
COLS   = 25        # number of columns
ROWS   = 20        # number of rows
HUD_H  = 55        # height of the top HUD bar in pixels

WIN_W  = COLS * CELL          # total window width
WIN_H  = ROWS * CELL + HUD_H  # total window height

FPS    = 10   # frames per second = snake moves per second at level 1

# ── Colours ────────────────────────────────────────────────────
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_BG     = (18,  18,  28)
ARENA_BG    = (24,  26,  38)
GRID_COL    = (32,  35,  52)
SNAKE_HEAD  = (60,  210, 110)
SNAKE_BODY  = (40,  160,  80)
HUD_COL     = (14,  14,  22)
BORDER_COL  = (60,  80, 130)
RED         = (220,  50,  50)
YELLOW      = (255, 215,   0)

# Food type definitions: (point value, colour, lifetime_ms)
# lifetime_ms = 0 means the food never expires
FOOD_TYPES = [
    (1, (255,  80,  80),     0),     # normal  — red,    permanent
    (3, (255, 200,  50),  6000),     # bonus   — yellow, 6 seconds
    (5, ( 80, 180, 255),  4000),     # rare    — blue,   4 seconds
]

# How many foods the snake must eat to advance to the next level
FOOD_PER_LEVEL = 4

# Directions as (dx, dy) vectors
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


def rand_cell(exclude: set) -> tuple:
    """Return a random (col, row) cell that is not in `exclude`."""
    while True:
        c = random.randint(0, COLS - 1)
        r = random.randint(0, ROWS - 1)
        if (c, r) not in exclude:
            return (c, r)


def cell_rect(col: int, row: int) -> pygame.Rect:
    """Convert grid coordinates to a pixel Rect."""
    return pygame.Rect(col * CELL, HUD_H + row * CELL, CELL, CELL)


# ══════════════════════════════════════════════════════════════
#  FOOD  — weighted value + optional expiry timer
# ══════════════════════════════════════════════════════════════

class Food:
    def __init__(self, pos: tuple, type_idx: int):
        self.pos      = pos
        self.points   = FOOD_TYPES[type_idx][0]   # point value
        self.color    = FOOD_TYPES[type_idx][1]   # display colour
        self.lifetime = FOOD_TYPES[type_idx][2]   # ms until expiry (0=never)
        self.born     = pygame.time.get_ticks()   # timestamp of creation

    def is_expired(self) -> bool:
        """Return True if this food has timed out and should be removed."""
        if self.lifetime == 0:
            return False                           # permanent food never expires
        return pygame.time.get_ticks() - self.born > self.lifetime

    def time_fraction(self) -> float:
        """Return remaining lifetime as a fraction 0.0–1.0 (1.0 = fresh)."""
        if self.lifetime == 0:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.born
        return max(0.0, 1.0 - elapsed / self.lifetime)

    def draw(self, surface: pygame.Surface, font):
        r    = cell_rect(*self.pos).inflate(-4, -4)   # slightly smaller than cell
        frac = self.time_fraction()

        # Fade the colour toward dark as the timer runs out
        col = tuple(int(c * frac + 15 * (1 - frac)) for c in self.color)
        pygame.draw.rect(surface, col,   r, border_radius=6)
        pygame.draw.rect(surface, WHITE, r, 1, border_radius=6)

        # Show point value as a label
        txt = font.render(str(self.points), True, BLACK)
        surface.blit(txt, (r.centerx - txt.get_width()  // 2,
                           r.centery - txt.get_height() // 2))

        # Draw a shrinking timer bar at the bottom of the cell for expiring food
        if self.lifetime > 0:
            bar_w = int((r.w) * frac)
            pygame.draw.rect(surface, YELLOW,
                             (r.x, r.bottom - 4, bar_w, 4))


# ══════════════════════════════════════════════════════════════
#  SNAKE GAME
# ══════════════════════════════════════════════════════════════

class SnakeGame:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Snake — Practice 11")
        self.clock  = pygame.time.Clock()

        # Small font for food labels and HUD
        self.font_sm = pygame.font.SysFont("segoeui", 14, bold=True)
        self.font_md = pygame.font.SysFont("segoeui", 20, bold=True)
        self.font_lg = pygame.font.SysFont("segoeui", 40, bold=True)

        self._init_game()

    def _init_game(self):
        """Reset all state for a new game."""
        # Snake body: list of (col, row), head at index 0
        mid = (COLS // 2, ROWS // 2)
        self.body      = [mid, (mid[0]-1, mid[1]), (mid[0]-2, mid[1])]
        self.direction = RIGHT
        self.next_dir  = RIGHT    # buffered next direction

        self.score      = 0
        self.level      = 1
        self.food_eaten = 0       # foods eaten this level
        self.alive      = True

        self.foods: list[Food] = []
        self._spawn_food()        # place first food item

        # Movement speed: controlled by FPS * level multiplier
        self.current_fps = FPS

    # ── Food management ────────────────────────────────────────

    def _occupied_cells(self) -> set:
        """All cells that should not receive new food."""
        return set(self.body) | {f.pos for f in self.foods}

    def _spawn_food(self):
        """Keep 2 food items on the board at all times."""
        while len(self.foods) < 2:
            pos = rand_cell(self._occupied_cells())
            # Weighted choice: 65% normal, 25% bonus, 10% rare
            idx = random.choices([0, 1, 2], weights=[65, 25, 10])[0]
            self.foods.append(Food(pos, idx))

    # ── Level progression ──────────────────────────────────────

    def _level_up(self):
        """Advance one level: reset food counter and increase speed."""
        self.level      += 1
        self.food_eaten  = 0
        # Each level adds 1.5 to FPS (movement speed)
        self.current_fps = FPS + int((self.level - 1) * 1.5)

    # ── Border collision ───────────────────────────────────────

    def _hits_border(self, pos: tuple) -> bool:
        """Return True if `pos` is outside the arena."""
        c, r = pos
        return not (0 <= c < COLS and 0 <= r < ROWS)

    # ── Update (called once per frame) ────────────────────────

    def update(self):
        if not self.alive:
            return

        # Remove expired timed foods and replenish
        self.foods = [f for f in self.foods if not f.is_expired()]
        self._spawn_food()

        # Apply buffered direction (ignore reversal)
        if self.next_dir != OPPOSITE.get(self.direction):
            self.direction = self.next_dir

        # Calculate new head position
        hx, hy   = self.body[0]
        dx, dy   = self.direction
        new_head = (hx + dx, hy + dy)

        # Check border collision
        if self._hits_border(new_head):
            self.alive = False
            return

        # Check self collision
        if new_head in self.body[:-1]:
            self.alive = False
            return

        # Move: insert new head
        self.body.insert(0, new_head)
        grew = False

        # Check food collection
        for food in self.foods[:]:
            if new_head == food.pos:
                self.score      += food.points * self.level   # level bonus
                self.food_eaten += 1
                grew = True
                self.foods.remove(food)

                # Level up after eating FOOD_PER_LEVEL foods
                if self.food_eaten >= FOOD_PER_LEVEL:
                    self._level_up()

                self._spawn_food()
                break

        # Remove tail only if snake did not eat (no growth)
        if not grew:
            self.body.pop()

    # ── Input ──────────────────────────────────────────────────

    def handle_key(self, key):
        """Buffer a direction change from keyboard input."""
        mapping = {
            pygame.K_UP:    UP,
            pygame.K_w:     UP,
            pygame.K_DOWN:  DOWN,
            pygame.K_s:     DOWN,
            pygame.K_LEFT:  LEFT,
            pygame.K_a:     LEFT,
            pygame.K_RIGHT: RIGHT,
            pygame.K_d:     RIGHT,
        }
        if key in mapping:
            nd = mapping[key]
            # Only accept if not reversing direction
            if nd != OPPOSITE.get(self.direction):
                self.next_dir = nd

    # ── Draw ───────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(DARK_BG)
        self._draw_arena()
        self._draw_food()
        self._draw_snake()
        self._draw_hud()

    def _draw_arena(self):
        """Draw the arena background and grid lines."""
        arena = pygame.Rect(0, HUD_H, WIN_W, WIN_H - HUD_H)
        pygame.draw.rect(self.screen, ARENA_BG, arena)
        pygame.draw.rect(self.screen, BORDER_COL, arena, 3)

        # Vertical grid lines
        for c in range(COLS + 1):
            x = c * CELL
            pygame.draw.line(self.screen, GRID_COL,
                             (x, HUD_H), (x, WIN_H))
        # Horizontal grid lines
        for r in range(ROWS + 1):
            y = HUD_H + r * CELL
            pygame.draw.line(self.screen, GRID_COL, (0, y), (WIN_W, y))

    def _draw_food(self):
        """Draw all food items."""
        for food in self.foods:
            food.draw(self.screen, self.font_sm)

    def _draw_snake(self):
        """Draw the snake body, with the head slightly brighter."""
        for i, (c, r) in enumerate(self.body):
            rect = cell_rect(c, r).inflate(-2, -2)
            col  = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(self.screen, col, rect, border_radius=5)

            # Draw eyes on the head
            if i == 0:
                pygame.draw.circle(self.screen, WHITE,
                                   (rect.x + 6,  rect.y + 6), 3)
                pygame.draw.circle(self.screen, WHITE,
                                   (rect.right - 6, rect.y + 6), 3)
                pygame.draw.circle(self.screen, BLACK,
                                   (rect.x + 6,  rect.y + 6), 1)
                pygame.draw.circle(self.screen, BLACK,
                                   (rect.right - 6, rect.y + 6), 1)

    def _draw_hud(self):
        """Draw score, level, and length in the top bar."""
        pygame.draw.rect(self.screen, HUD_COL, (0, 0, WIN_W, HUD_H))
        pygame.draw.line(self.screen, BORDER_COL,
                         (0, HUD_H), (WIN_W, HUD_H), 2)

        self.screen.blit(
            self.font_md.render(f"Score: {self.score}", True, WHITE), (10, 14))
        self.screen.blit(
            self.font_md.render(f"Level: {self.level}", True, (100,200,255)), (200, 14))
        self.screen.blit(
            self.font_sm.render(f"Length: {len(self.body)}", True, (180,180,180)),
            (360, 18))
        self.screen.blit(
            self.font_sm.render("WASD / Arrows", True, (100,100,130)),
            (WIN_W - 150, 18))

    def _draw_gameover(self):
        """Darken the screen and show the game-over message."""
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        self.screen.blit(
            self.font_lg.render("GAME OVER", True, RED),
            (WIN_W // 2 - 120, WIN_H // 2 - 60))
        self.screen.blit(
            self.font_md.render(f"Score: {self.score}  Level: {self.level}",
                                True, WHITE),
            (WIN_W // 2 - 110, WIN_H // 2))
        self.screen.blit(
            self.font_sm.render("Press R to restart  or  ESC to quit",
                                True, WHITE),
            (WIN_W // 2 - 140, WIN_H // 2 + 50))

    # ── Main loop ──────────────────────────────────────────────

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if not self.alive and event.key == pygame.K_r:
                        self._init_game()      # restart
                    self.handle_key(event.key)

            if self.alive:
                self.update()

            self.draw()

            if not self.alive:
                self._draw_gameover()

            pygame.display.flip()
            # Speed increases with level via FPS
            self.clock.tick(self.current_fps)


# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    SnakeGame().run()

"""
Practice 11 — Paint
Extends Practice 10 with:
  1. Draw square   (forced equal sides)
  2. Draw right triangle
  3. Draw equilateral triangle
  4. Draw rhombus
  5. Comments throughout
"""

import pygame
import sys
import math

# ── Window layout ──────────────────────────────────────────────
WIN_W      = 1000   # total window width
WIN_H      = 680    # total window height
TOOLBAR_W  = 170    # width of the left toolbar
CANVAS_X   = TOOLBAR_W
CANVAS_W   = WIN_W - TOOLBAR_W
CANVAS_H   = WIN_H

FPS = 60

# ── Colours ────────────────────────────────────────────────────
WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)
BG_DARK     = (28,  28,  38)
PANEL_BG    = (20,  20,  30)
BORDER_COL  = (55,  55,  80)
BTN_NORMAL  = (42,  42,  60)
BTN_HOVER   = (62,  62,  90)
BTN_ACTIVE  = (70, 120, 210)
TEXT_COL    = (210, 210, 230)

# Colour palette for the toolbar
PALETTE = [
    BLACK,           WHITE,           (220,  50,  50),
    (50,  180,  50), (50,  100, 220), (220, 180,  40),
    (180,  60, 180), (40,  200, 200), (230, 130,  40),
    (100,  60,  20), (160, 160, 160), (70,   70,  70),
]


# ══════════════════════════════════════════════════════════════
#  GEOMETRY HELPERS
# ══════════════════════════════════════════════════════════════

def make_rect(p1: tuple, p2: tuple) -> pygame.Rect:
    """Build a Rect from two corner points (any order)."""
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = abs(p2[0] - p1[0])
    h = abs(p2[1] - p1[1])
    return pygame.Rect(x, y, w, h)


def square_rect(p1: tuple, p2: tuple) -> pygame.Rect:
    """Build a square Rect: uses the smaller of dx/dy as the side length."""
    dx   = p2[0] - p1[0]
    dy   = p2[1] - p1[1]
    side = min(abs(dx), abs(dy))             # force equal sides
    sx   = p1[0] + (side if dx >= 0 else -side)
    sy   = p1[1] + (side if dy >= 0 else -side)
    return make_rect(p1, (sx, sy))


def right_triangle_pts(p1: tuple, p2: tuple) -> list:
    """
    Right-angle triangle with the 90° corner at p1.
    Points: top-left corner, bottom-left corner, bottom-right corner.
    """
    return [p1, (p1[0], p2[1]), p2]


def equilateral_pts(p1: tuple, p2: tuple) -> list:
    """
    Equilateral triangle with base from p1 to p2.
    The apex is placed perpendicular to the base at height = base * sqrt(3)/2.
    """
    base_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    height   = base_len * math.sqrt(3) / 2

    # Mid-point of the base
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2

    # Unit vector perpendicular to the base (rotated 90°)
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy) or 1
    nx = -dy / length   # perpendicular direction
    ny =  dx / length

    apex = (int(mx + nx * height), int(my + ny * height))
    return [p1, p2, apex]


def rhombus_pts(p1: tuple, p2: tuple) -> list:
    """
    Rhombus (diamond) defined by bounding box p1–p2.
    Four points: top, right, bottom, left.
    """
    cx = (p1[0] + p2[0]) // 2
    cy = (p1[1] + p2[1]) // 2
    return [
        (cx,    p1[1]),   # top centre
        (p2[0], cy),      # right centre
        (cx,    p2[1]),   # bottom centre
        (p1[0], cy),      # left centre
    ]


# ══════════════════════════════════════════════════════════════
#  PAINT APPLICATION
# ══════════════════════════════════════════════════════════════

class PaintApp:

    # Available tools in the toolbar (display label, internal key)
    TOOLS = [
        ("Pencil",   "pencil"),
        ("Rect",     "rect"),
        ("Square",   "square"),
        ("Circle",   "circle"),
        ("R.Tri",    "rtri"),
        ("Eq.Tri",   "etri"),
        ("Rhombus",  "rhombus"),
        ("Eraser",   "eraser"),
    ]

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Paint — Practice 11")
        self.clock  = pygame.time.Clock()

        self.font_sm = pygame.font.SysFont("segoeui", 13)
        self.font_md = pygame.font.SysFont("segoeui", 15, bold=True)

        # The drawing canvas (white surface)
        self.canvas = pygame.Surface((CANVAS_W, CANVAS_H))
        self.canvas.fill(WHITE)

        # Current state
        self.tool       = "pencil"
        self.color      = BLACK
        self.thickness  = 3
        self.drawing    = False
        self.start_pos  = None    # used for shape tools (mouse-down position)
        self.last_pos   = None    # used for pencil/eraser (previous position)

        # Build toolbar rects once
        self._build_toolbar()

    # ── Toolbar layout ─────────────────────────────────────────

    def _build_toolbar(self):
        """Pre-compute Rect for every toolbar element."""
        pad = 6
        x0  = 8
        bw  = TOOLBAR_W - 16    # button width
        bh  = 28                 # button height

        # Tool buttons
        self.tool_rects = {}
        y = 32
        for label, key in self.TOOLS:
            self.tool_rects[key] = pygame.Rect(x0, y, bw, bh)
            y += bh + pad

        # Thickness buttons
        y += 8
        self.thick_label_y = y
        y += 20
        sw = (bw - 8) // 3
        self.thick_rects = {}
        for i, val in enumerate([1, 3, 6]):
            self.thick_rects[val] = pygame.Rect(x0 + i * (sw + 4), y, sw, bh)
        y += bh + pad + 10

        # Colour palette swatches
        self.palette_label_y = y
        y += 20
        cols = 3
        sw2  = (bw - (cols - 1) * 4) // cols
        self.palette_rects = []
        for idx, col in enumerate(PALETTE):
            row = idx // cols
            c   = idx  % cols
            self.palette_rects.append(
                (pygame.Rect(x0 + c * (sw2 + 4), y + row * 24, sw2, 20), col)
            )
        y += (len(PALETTE) // cols + 1) * 24 + 8

        # Clear button
        self.clear_rect = pygame.Rect(x0, y, bw, bh)

    # ── Toolbar drawing ────────────────────────────────────────

    def _draw_toolbar(self, mx: int, my: int):
        pygame.draw.rect(self.screen, PANEL_BG,
                         pygame.Rect(0, 0, TOOLBAR_W, WIN_H))
        pygame.draw.line(self.screen, BORDER_COL,
                         (TOOLBAR_W, 0), (TOOLBAR_W, WIN_H), 2)

        # Title
        title = self.font_md.render("🎨 Paint", True, BTN_ACTIVE)
        self.screen.blit(title, (8, 8))

        # Tool buttons
        for label, key in self.TOOLS:
            r      = self.tool_rects[key]
            active = (self.tool == key)
            hover  = r.collidepoint(mx, my)
            bg     = BTN_ACTIVE if active else (BTN_HOVER if hover else BTN_NORMAL)
            pygame.draw.rect(self.screen, bg, r, border_radius=5)
            pygame.draw.rect(self.screen, BORDER_COL, r, 1, border_radius=5)
            t = self.font_sm.render(label, True, TEXT_COL)
            self.screen.blit(t, (r.x + (r.w - t.get_width()) // 2,
                                 r.y + (r.h - t.get_height()) // 2))

        # Thickness label + buttons
        self.screen.blit(
            self.font_sm.render("Thickness:", True, TEXT_COL),
            (8, self.thick_label_y))
        size_labels = {1: "S", 3: "M", 6: "L"}
        for val, r in self.thick_rects.items():
            active = (self.thickness == val)
            hover  = r.collidepoint(mx, my)
            bg     = BTN_ACTIVE if active else (BTN_HOVER if hover else BTN_NORMAL)
            pygame.draw.rect(self.screen, bg, r, border_radius=5)
            pygame.draw.rect(self.screen, BORDER_COL, r, 1, border_radius=5)
            t = self.font_sm.render(size_labels[val], True, TEXT_COL)
            self.screen.blit(t, (r.centerx - t.get_width() // 2,
                                 r.centery - t.get_height() // 2))

        # Colour swatches
        self.screen.blit(
            self.font_sm.render("Colour:", True, TEXT_COL),
            (8, self.palette_label_y))
        for r, col in self.palette_rects:
            pygame.draw.rect(self.screen, col, r, border_radius=3)
            border = BTN_ACTIVE if self.color == col else BORDER_COL
            pygame.draw.rect(self.screen, border, r, 2, border_radius=3)

        # Clear button
        hover_c = self.clear_rect.collidepoint(mx, my)
        bg = BTN_HOVER if hover_c else BTN_NORMAL
        pygame.draw.rect(self.screen, bg, self.clear_rect, border_radius=5)
        pygame.draw.rect(self.screen, BORDER_COL, self.clear_rect, 1, border_radius=5)
        t = self.font_sm.render("Clear", True, TEXT_COL)
        self.screen.blit(t, (self.clear_rect.centerx - t.get_width() // 2,
                             self.clear_rect.centery - t.get_height() // 2))

        # Active colour preview at the bottom
        preview = pygame.Rect(8, WIN_H - 44, TOOLBAR_W - 16, 32)
        pygame.draw.rect(self.screen, self.color, preview, border_radius=5)
        pygame.draw.rect(self.screen, BORDER_COL, preview, 2, border_radius=5)

    # ── Canvas helpers ─────────────────────────────────────────

    def _canvas_pos(self, screen_pos: tuple) -> tuple:
        """Convert a screen position to canvas-local coordinates."""
        return (screen_pos[0] - CANVAS_X, screen_pos[1])

    def _on_canvas(self, screen_pos: tuple) -> bool:
        return screen_pos[0] >= CANVAS_X

    # ── Shape drawing ──────────────────────────────────────────

    def _draw_shape(self, surface, p1: tuple, p2: tuple, preview=False):
        """
        Draw the active shape between p1 and p2 onto `surface`.
        If `preview` is True, draw at reduced opacity (for live preview).
        """
        col  = self.color
        t    = self.thickness

        if self.tool == "rect":
            pygame.draw.rect(surface, col, make_rect(p1, p2), t)

        elif self.tool == "square":
            pygame.draw.rect(surface, col, square_rect(p1, p2), t)

        elif self.tool == "circle":
            # Circle whose diameter spans the diagonal of p1–p2 bounding box
            cx = (p1[0] + p2[0]) // 2
            cy = (p1[1] + p2[1]) // 2
            r  = int(math.hypot(p2[0]-p1[0], p2[1]-p1[1]) // 2)
            if r > 0:
                pygame.draw.circle(surface, col, (cx, cy), r, t)

        elif self.tool == "rtri":
            pts = right_triangle_pts(p1, p2)
            pygame.draw.polygon(surface, col, pts, t)

        elif self.tool == "etri":
            pts = equilateral_pts(p1, p2)
            pygame.draw.polygon(surface, col, pts, t)

        elif self.tool == "rhombus":
            pts = rhombus_pts(p1, p2)
            pygame.draw.polygon(surface, col, pts, t)

    # ── Toolbar click handling ─────────────────────────────────

    def _handle_toolbar_click(self, pos: tuple):
        """Process a click inside the toolbar area."""
        # Tool buttons
        for label, key in self.TOOLS:
            if self.tool_rects[key].collidepoint(pos):
                self.tool = key
                return

        # Thickness buttons
        for val, r in self.thick_rects.items():
            if r.collidepoint(pos):
                self.thickness = val
                return

        # Colour swatches
        for r, col in self.palette_rects:
            if r.collidepoint(pos):
                self.color = col
                return

        # Clear button
        if self.clear_rect.collidepoint(pos):
            self.canvas.fill(WHITE)

    # ── Main loop ──────────────────────────────────────────────

    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                # ── Mouse button DOWN ──
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._on_canvas(event.pos):
                        cp = self._canvas_pos(event.pos)
                        self.drawing   = True
                        self.start_pos = cp
                        self.last_pos  = cp

                        # For point-click tools start immediately
                        if self.tool == "pencil":
                            pygame.draw.circle(self.canvas, self.color,
                                               cp, self.thickness // 2 + 1)
                        elif self.tool == "eraser":
                            pygame.draw.circle(self.canvas, WHITE,
                                               cp, self.thickness * 3)
                    else:
                        self._handle_toolbar_click(event.pos)

                # ── Mouse MOVE ──
                elif event.type == pygame.MOUSEMOTION:
                    if self.drawing and self._on_canvas(event.pos):
                        cp = self._canvas_pos(event.pos)

                        if self.tool == "pencil":
                            # Connect previous and current positions
                            pygame.draw.line(self.canvas, self.color,
                                             self.last_pos, cp, self.thickness)
                            self.last_pos = cp

                        elif self.tool == "eraser":
                            pygame.draw.line(self.canvas, WHITE,
                                             self.last_pos, cp, self.thickness * 6)
                            self.last_pos = cp

                # ── Mouse button UP ──
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.drawing and self._on_canvas(event.pos):
                        cp = self._canvas_pos(event.pos)
                        # Commit shape to canvas on release
                        if self.tool not in ("pencil", "eraser"):
                            self._draw_shape(self.canvas, self.start_pos, cp)
                    self.drawing   = False
                    self.start_pos = None
                    self.last_pos  = None

            # ── Render ────────────────────────────────────────
            self.screen.fill(BG_DARK)

            # Draw the permanent canvas
            self.screen.blit(self.canvas, (CANVAS_X, 0))

            # Draw live preview for shape tools while dragging
            if self.drawing and self.start_pos and \
               self.tool not in ("pencil", "eraser"):
                mx_c, my_c = pygame.mouse.get_pos()
                if self._on_canvas((mx_c, my_c)):
                    # Draw preview directly on screen (not on canvas)
                    preview_surface = self.screen.copy()
                    cp = self._canvas_pos((mx_c, my_c))
                    # Offset start_pos back to screen space for drawing
                    sp_screen = (self.start_pos[0] + CANVAS_X, self.start_pos[1])
                    cp_screen = (cp[0] + CANVAS_X, cp[1])
                    self._draw_shape_screen(sp_screen, cp_screen)

            self._draw_toolbar(mx, my)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _draw_shape_screen(self, p1: tuple, p2: tuple):
        """
        Draw a preview of the current shape directly on self.screen
        (not on the canvas) so it disappears next frame.
        """
        col = self.color
        t   = self.thickness

        if self.tool == "rect":
            pygame.draw.rect(self.screen, col, make_rect(p1, p2), t)
        elif self.tool == "square":
            pygame.draw.rect(self.screen, col, square_rect(p1, p2), t)
        elif self.tool == "circle":
            cx = (p1[0] + p2[0]) // 2
            cy = (p1[1] + p2[1]) // 2
            r  = int(math.hypot(p2[0]-p1[0], p2[1]-p1[1]) // 2)
            if r > 0:
                pygame.draw.circle(self.screen, col, (cx, cy), r, t)
        elif self.tool == "rtri":
            pts = right_triangle_pts(p1, p2)
            pygame.draw.polygon(self.screen, col, pts, t)
        elif self.tool == "etri":
            pts = equilateral_pts(p1, p2)
            pygame.draw.polygon(self.screen, col, pts, t)
        elif self.tool == "rhombus":
            pts = rhombus_pts(p1, p2)
            pygame.draw.polygon(self.screen, col, pts, t)


# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    PaintApp().run()

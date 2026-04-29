"""
tools.py — Drawing tool implementations for the Paint app.
Each tool class handles its own mouse events and drawing logic.
"""

import pygame
from collections import deque


# ── Brush sizes ────────────────────────────────────────────────
BRUSH_SIZES = {1: 2, 2: 5, 3: 10}   # key = level, value = px


class PencilTool:
    """Freehand drawing: connects consecutive mouse positions."""

    def __init__(self):
        self.drawing  = False
        self.last_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing  = True
        self.last_pos = pos
        pygame.draw.circle(canvas, color, pos, size // 2)

    def on_mouse_move(self, pos, canvas, color, size):
        if self.drawing and self.last_pos:
            pygame.draw.line(canvas, color, self.last_pos, pos, size)
            self.last_pos = pos

    def on_mouse_up(self, pos, canvas, color, size):
        self.drawing  = False
        self.last_pos = None

    def draw_preview(self, surface, pos, color, size):
        pygame.draw.circle(surface, color, pos, size // 2, 1)


class LineTool:
    """Straight line with live preview while dragging."""

    def __init__(self):
        self.drawing   = False
        self.start_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing   = True
        self.start_pos = pos

    def on_mouse_move(self, pos, canvas, color, size):
        pass   # preview handled externally

    def on_mouse_up(self, pos, canvas, color, size):
        if self.drawing and self.start_pos:
            pygame.draw.line(canvas, color, self.start_pos, pos, size)
        self.drawing   = False
        self.start_pos = None

    def draw_preview(self, surface, pos, color, size):
        if self.drawing and self.start_pos:
            pygame.draw.line(surface, color, self.start_pos, pos, size)


class RectTool:
    """Rectangle outline."""

    def __init__(self):
        self.drawing   = False
        self.start_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing   = True
        self.start_pos = pos

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        if self.drawing and self.start_pos:
            rect = _make_rect(self.start_pos, pos)
            pygame.draw.rect(canvas, color, rect, size)
        self.drawing   = False
        self.start_pos = None

    def draw_preview(self, surface, pos, color, size):
        if self.drawing and self.start_pos:
            rect = _make_rect(self.start_pos, pos)
            pygame.draw.rect(surface, color, rect, size)


class SquareTool:
    """Perfect square — forces equal width/height."""

    def __init__(self):
        self.drawing   = False
        self.start_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing   = True
        self.start_pos = pos

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        if self.drawing and self.start_pos:
            rect = _square_rect(self.start_pos, pos)
            pygame.draw.rect(canvas, color, rect, size)
        self.drawing   = False
        self.start_pos = None

    def draw_preview(self, surface, pos, color, size):
        if self.drawing and self.start_pos:
            rect = _square_rect(self.start_pos, pos)
            pygame.draw.rect(surface, color, rect, size)


class CircleTool:
    """Circle outline."""

    def __init__(self):
        self.drawing   = False
        self.start_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing   = True
        self.start_pos = pos

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        if self.drawing and self.start_pos:
            cx, cy, r = _circle_params(self.start_pos, pos)
            if r > 0:
                pygame.draw.circle(canvas, color, (cx, cy), r, size)
        self.drawing   = False
        self.start_pos = None

    def draw_preview(self, surface, pos, color, size):
        if self.drawing and self.start_pos:
            cx, cy, r = _circle_params(self.start_pos, pos)
            if r > 0:
                pygame.draw.circle(surface, color, (cx, cy), r, size)


class RightTriangleTool:
    """Right triangle: right angle at the start point."""

    def __init__(self):
        self.drawing   = False
        self.start_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing   = True
        self.start_pos = pos

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        if self.drawing and self.start_pos:
            pts = _right_triangle_pts(self.start_pos, pos)
            pygame.draw.polygon(canvas, color, pts, size)
        self.drawing   = False
        self.start_pos = None

    def draw_preview(self, surface, pos, color, size):
        if self.drawing and self.start_pos:
            pts = _right_triangle_pts(self.start_pos, pos)
            pygame.draw.polygon(surface, color, pts, size)


class EquilateralTriangleTool:
    """Equilateral triangle centred between start and end."""

    def __init__(self):
        self.drawing   = False
        self.start_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing   = True
        self.start_pos = pos

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        if self.drawing and self.start_pos:
            pts = _equilateral_pts(self.start_pos, pos)
            pygame.draw.polygon(canvas, color, pts, size)
        self.drawing   = False
        self.start_pos = None

    def draw_preview(self, surface, pos, color, size):
        if self.drawing and self.start_pos:
            pts = _equilateral_pts(self.start_pos, pos)
            pygame.draw.polygon(surface, color, pts, size)


class RhombusTool:
    """Rhombus (diamond) shape."""

    def __init__(self):
        self.drawing   = False
        self.start_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing   = True
        self.start_pos = pos

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        if self.drawing and self.start_pos:
            pts = _rhombus_pts(self.start_pos, pos)
            pygame.draw.polygon(canvas, color, pts, size)
        self.drawing   = False
        self.start_pos = None

    def draw_preview(self, surface, pos, color, size):
        if self.drawing and self.start_pos:
            pts = _rhombus_pts(self.start_pos, pos)
            pygame.draw.polygon(surface, color, pts, size)


class EraserTool:
    """Eraser — draws with white color."""

    def __init__(self):
        self.drawing  = False
        self.last_pos = None

    def on_mouse_down(self, pos, canvas, color, size):
        self.drawing  = True
        self.last_pos = pos
        pygame.draw.circle(canvas, (255, 255, 255), pos, size * 2)

    def on_mouse_move(self, pos, canvas, color, size):
        if self.drawing and self.last_pos:
            pygame.draw.line(canvas, (255, 255, 255), self.last_pos, pos, size * 4)
            self.last_pos = pos

    def on_mouse_up(self, pos, canvas, color, size):
        self.drawing  = False
        self.last_pos = None

    def draw_preview(self, surface, pos, color, size):
        pygame.draw.circle(surface, (200, 200, 200), pos, size * 2, 1)


class FillTool:
    """Flood-fill using BFS — fills a closed region with the active color."""

    def on_mouse_down(self, pos, canvas, color, size):
        flood_fill(canvas, pos, color)

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        pass

    def draw_preview(self, surface, pos, color, size):
        # Show a small bucket cursor hint
        pygame.draw.circle(surface, color, pos, 6)
        pygame.draw.circle(surface, (0, 0, 0), pos, 6, 1)


class TextTool:
    """Click to place text cursor; type characters; Enter confirms."""

    def __init__(self):
        self.active   = False
        self.pos      = None
        self.text     = ""
        self.font     = pygame.font.SysFont("monospace", 20)

    def on_mouse_down(self, pos, canvas, color, size):
        self.active = True
        self.pos    = pos
        self.text   = ""

    def on_mouse_move(self, pos, canvas, color, size):
        pass

    def on_mouse_up(self, pos, canvas, color, size):
        pass

    def handle_key(self, event, canvas, color):
        """Returns True when text has been committed to canvas."""
        if not self.active:
            return False
        if event.key == pygame.K_RETURN:
            # Render text permanently onto canvas
            surf = self.font.render(self.text, True, color)
            canvas.blit(surf, self.pos)
            self.active = False
            self.text   = ""
            return True
        elif event.key == pygame.K_ESCAPE:
            self.active = False
            self.text   = ""
            return True
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        else:
            ch = event.unicode
            if ch and ch.isprintable():
                self.text += ch
        return False

    def draw_preview(self, surface, pos, color, size):
        if self.active and self.pos:
            surf = self.font.render(self.text + "|", True, color)
            surface.blit(surf, self.pos)

    def draw_cursor(self, surface, color):
        if self.active and self.pos:
            surf = self.font.render(self.text + "|", True, color)
            surface.blit(surf, self.pos)


# ── Flood fill ─────────────────────────────────────────────────

def flood_fill(canvas: pygame.Surface, start: tuple, fill_color: tuple):
    """BFS flood fill on a pygame Surface."""
    sx, sy     = int(start[0]), int(start[1])
    w, h       = canvas.get_size()

    if not (0 <= sx < w and 0 <= sy < h):
        return

    target = canvas.get_at((sx, sy))[:3]   # ignore alpha
    fill   = fill_color[:3]

    if target == fill:
        return

    visited = set()
    queue   = deque([(sx, sy)])

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        if not (0 <= x < w and 0 <= y < h):
            continue
        if canvas.get_at((x, y))[:3] != target:
            continue

        canvas.set_at((x, y), fill_color)
        visited.add((x, y))

        queue.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])


# ── Geometry helpers ───────────────────────────────────────────

def _make_rect(p1, p2):
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = abs(p2[0] - p1[0])
    h = abs(p2[1] - p1[1])
    return pygame.Rect(x, y, w, h)


def _square_rect(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    side = min(abs(dx), abs(dy))
    sx = p1[0] + (side if dx >= 0 else -side)
    sy = p1[1] + (side if dy >= 0 else -side)
    return _make_rect(p1, (sx, sy))


def _circle_params(p1, p2):
    cx = (p1[0] + p2[0]) // 2
    cy = (p1[1] + p2[1]) // 2
    r  = int(((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2) ** 0.5 // 2)
    return cx, cy, r


def _right_triangle_pts(p1, p2):
    # Right angle at p1
    return [p1, (p1[0], p2[1]), p2]


def _equilateral_pts(p1, p2):
    import math
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2
    base = ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2) ** 0.5
    h    = base * (3**0.5) / 2
    # perpendicular direction
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = (dx*dx + dy*dy) ** 0.5 or 1
    nx = -dy / length
    ny =  dx / length
    apex = (int(mx + nx * h), int(my + ny * h))
    return [p1, p2, apex]


def _rhombus_pts(p1, p2):
    cx = (p1[0] + p2[0]) // 2
    cy = (p1[1] + p2[1]) // 2
    return [
        (cx,    p1[1]),   # top
        (p2[0], cy),      # right
        (cx,    p2[1]),   # bottom
        (p1[0], cy),      # left
    ]

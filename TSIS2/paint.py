"""
TSIS2 — Paint Application
Extends Practice 10 & 11 with:
  • Pencil (freehand)          • Straight line (live preview)
  • Rectangle, Square          • Circle
  • Right triangle             • Equilateral triangle
  • Rhombus                    • Eraser
  • Flood fill                 • Text tool (click → type → Enter)
  • 3 brush sizes  (1/2/3)     • Ctrl+S  saves timestamped PNG
"""

import pygame
import sys
from datetime import datetime
from tools import (
    PencilTool, LineTool, RectTool, SquareTool, CircleTool,
    RightTriangleTool, EquilateralTriangleTool, RhombusTool,
    EraserTool, FillTool, TextTool, BRUSH_SIZES
)

# ── Window / layout constants ──────────────────────────────────
WIN_W, WIN_H   = 1100, 720
TOOLBAR_W      = 160
CANVAS_X       = TOOLBAR_W
CANVAS_W       = WIN_W - TOOLBAR_W
CANVAS_H       = WIN_H

# ── Colours ────────────────────────────────────────────────────
BG_DARK        = (30,  30,  38)
PANEL_BG       = (22,  22,  28)
PANEL_BORDER   = (60,  60,  80)
BTN_NORMAL     = (45,  45,  58)
BTN_HOVER      = (65,  65,  85)
BTN_ACTIVE     = (80, 120, 200)
TEXT_COLOR     = (220, 220, 235)
WHITE          = (255, 255, 255)
BLACK          = (0,   0,   0)

PALETTE = [
    (0,   0,   0),   (255, 255, 255), (200,  50,  50),
    (50,  180,  50), (50,  100, 220), (220, 180,  40),
    (180,  60, 180), (40,  200, 200), (230, 130,  40),
    (100,  60,  20), (150, 150, 150), (80,   80,  80),
]

FPS = 60


#  UI helpers

def draw_button(surface, rect, label, active=False, hover=False, font=None):
    color = BTN_ACTIVE if active else (BTN_HOVER if hover else BTN_NORMAL)
    pygame.draw.rect(surface, color, rect, border_radius=6)
    pygame.draw.rect(surface, PANEL_BORDER, rect, 1, border_radius=6)
    if font and label:
        txt = font.render(label, True, TEXT_COLOR)
        tx  = rect.x + (rect.w - txt.get_width())  // 2
        ty  = rect.y + (rect.h - txt.get_height()) // 2
        surface.blit(txt, (tx, ty))


def draw_color_swatch(surface, rect, color, selected=False):
    pygame.draw.rect(surface, color, rect, border_radius=4)
    border = BTN_ACTIVE if selected else PANEL_BORDER
    pygame.draw.rect(surface, border, rect, 2, border_radius=4)


#  Main App

class PaintApp:

    TOOLS = [
        ("Pencil",    "pencil"),
        ("Line",      "line"),
        ("Rect",      "rect"),
        ("Square",    "square"),
        ("Circle",    "circle"),
        ("R.Tri",     "rtri"),
        ("Eq.Tri",    "etri"),
        ("Rhombus",   "rhombus"),
        ("Eraser",    "eraser"),
        ("Fill",      "fill"),
        ("Text",      "text"),
    ]

    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Paint — TSIS2")
        self.clock   = pygame.time.Clock()

        # Fonts
        self.font_sm = pygame.font.SysFont("segoeui", 13)
        self.font_md = pygame.font.SysFont("segoeui", 15, bold=True)
        self.font_lg = pygame.font.SysFont("segoeui", 17, bold=True)

        # Canvas (white)
        self.canvas  = pygame.Surface((CANVAS_W, CANVAS_H))
        self.canvas.fill(WHITE)

        # State
        self.active_tool  = "pencil"
        self.brush_level  = 1                      # 1=small 2=med 3=large
        self.color        = (0, 0, 0)
        self.custom_color = None

        # Tool instances
        self._tools = {
            "pencil":  PencilTool(),
            "line":    LineTool(),
            "rect":    RectTool(),
            "square":  SquareTool(),
            "circle":  CircleTool(),
            "rtri":    RightTriangleTool(),
            "etri":    EquilateralTriangleTool(),
            "rhombus": RhombusTool(),
            "eraser":  EraserTool(),
            "fill":    FillTool(),
            "text":    TextTool(),
        }

        # UI rects (built once)
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────

    def _build_ui(self):
        """Pre-compute all toolbar button rectangles."""
        x0, pad, bw, bh = 8, 6, TOOLBAR_W - 16, 30

        # Tool buttons
        self.tool_rects = {}
        y = 36
        for label, key in self.TOOLS:
            self.tool_rects[key] = pygame.Rect(x0, y, bw, bh)
            y += bh + pad

        # Brush size buttons
        y += 10
        self.size_label_y  = y
        y += 22
        sw = (bw - 8) // 3
        self.size_rects = {}
        for i, level in enumerate([1, 2, 3]):
            self.size_rects[level] = pygame.Rect(x0 + i*(sw+4), y, sw, bh)
        y += bh + pad + 10

        # Colour palette
        self.palette_label_y = y
        y += 22
        cols = 3
        sw2  = (bw - (cols-1)*4) // cols
        self.palette_rects = []
        for idx, col in enumerate(PALETTE):
            row = idx // cols
            c   = idx  % cols
            self.palette_rects.append(
                (pygame.Rect(x0 + c*(sw2+4), y + row*26, sw2, 22), col)
            )
        y += (len(PALETTE) // cols + 1) * 26 + 10

        # Clear button
        self.clear_rect = pygame.Rect(x0, y, bw, bh)
        y += bh + pad

        # Save button
        self.save_rect  = pygame.Rect(x0, y, bw, bh)

    # ── Properties ────────────────────────────────────────────

    @property
    def brush_size(self):
        return BRUSH_SIZES[self.brush_level]

    @property
    def tool(self):
        return self._tools[self.active_tool]

    # ── Draw toolbar ──────────────────────────────────────────

    def _draw_toolbar(self, mx, my):
        pygame.draw.rect(self.screen, PANEL_BG,
                         pygame.Rect(0, 0, TOOLBAR_W, WIN_H))
        pygame.draw.line(self.screen, PANEL_BORDER,
                         (TOOLBAR_W, 0), (TOOLBAR_W, WIN_H), 2)

        # Title
        title = self.font_lg.render("🎨 Paint", True, BTN_ACTIVE)
        self.screen.blit(title, (8, 8))

        # Tool buttons
        for label, key in self.TOOLS:
            rect   = self.tool_rects[key]
            active = (self.active_tool == key)
            hover  = rect.collidepoint(mx, my)
            draw_button(self.screen, rect, label, active, hover, self.font_sm)

        # Brush size label
        lbl = self.font_sm.render("Brush size (1/2/3):", True, TEXT_COLOR)
        self.screen.blit(lbl, (8, self.size_label_y))

        # Brush buttons
        size_labels = {1: "S", 2: "M", 3: "L"}
        for level, rect in self.size_rects.items():
            active = (self.brush_level == level)
            hover  = rect.collidepoint(mx, my)
            draw_button(self.screen, rect, size_labels[level], active, hover, self.font_md)

        # Palette label
        lbl2 = self.font_sm.render("Colour:", True, TEXT_COLOR)
        self.screen.blit(lbl2, (8, self.palette_label_y))

        # Swatches
        for rect, col in self.palette_rects:
            draw_color_swatch(self.screen, rect, col, self.color == col)

        # Clear / Save
        hover_c = self.clear_rect.collidepoint(mx, my)
        hover_s = self.save_rect.collidepoint(mx, my)
        draw_button(self.screen, self.clear_rect, "Clear Canvas",
                    False, hover_c, self.font_sm)
        draw_button(self.screen, self.save_rect,  "Save (Ctrl+S)",
                    False, hover_s, self.font_sm)

        # Active colour preview
        preview_rect = pygame.Rect(8, WIN_H - 50, TOOLBAR_W - 16, 36)
        pygame.draw.rect(self.screen, self.color, preview_rect, border_radius=6)
        pygame.draw.rect(self.screen, PANEL_BORDER, preview_rect, 2, border_radius=6)

    # ── Draw canvas area ──────────────────────────────────────

    def _draw_canvas(self, mx, my):
        self.screen.blit(self.canvas, (CANVAS_X, 0))

        # Tool preview overlay
        preview = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)
        cx = mx - CANVAS_X

        if self.active_tool == "text":
            text_tool = self._tools["text"]
            text_tool.draw_preview(preview, (cx, my), self.color, self.brush_size)
        else:
            self.tool.draw_preview(preview, (cx, my), self.color, self.brush_size)

        self.screen.blit(preview, (CANVAS_X, 0))

    # ── Save ──────────────────────────────────────────────────

    def save_canvas(self):
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"canvas_{ts}.png"
        pygame.image.save(self.canvas, filename)
        print(f"Canvas saved as '{filename}'")

    # ── Event handling ────────────────────────────────────────

    def _handle_toolbar_click(self, pos):
        mx, my = pos

        # Tool selection
        for label, key in self.TOOLS:
            if self.tool_rects[key].collidepoint(mx, my):
                self.active_tool = key
                return

        # Brush size
        for level, rect in self.size_rects.items():
            if rect.collidepoint(mx, my):
                self.brush_level = level
                return

        # Palette
        for rect, col in self.palette_rects:
            if rect.collidepoint(mx, my):
                self.color = col
                return

        # Clear
        if self.clear_rect.collidepoint(mx, my):
            self.canvas.fill(WHITE)
            return

        # Save
        if self.save_rect.collidepoint(mx, my):
            self.save_canvas()

    def _canvas_pos(self, pos):
        """Convert screen position to canvas-local position."""
        return (pos[0] - CANVAS_X, pos[1])

    def _on_canvas(self, pos):
        return pos[0] >= CANVAS_X

    # ── Main loop ─────────────────────────────────────────────

    def run(self):
        running = True

        while running:
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():

                # ── Quit ──
                if event.type == pygame.QUIT:
                    running = False

                # ── Key down ──
                elif event.type == pygame.KEYDOWN:

                    # Ctrl+S
                    if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.save_canvas()

                    # Brush size shortcuts
                    elif event.key == pygame.K_1:
                        self.brush_level = 1
                    elif event.key == pygame.K_2:
                        self.brush_level = 2
                    elif event.key == pygame.K_3:
                        self.brush_level = 3

                    # Text tool keyboard input
                    elif self.active_tool == "text":
                        self._tools["text"].handle_key(
                            event, self.canvas, self.color
                        )

                # ── Mouse button down ──
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._on_canvas(event.pos):
                        cp = self._canvas_pos(event.pos)
                        self.tool.on_mouse_down(cp, self.canvas,
                                                self.color, self.brush_size)
                    else:
                        self._handle_toolbar_click(event.pos)

                # ── Mouse move ──
                elif event.type == pygame.MOUSEMOTION:
                    if self._on_canvas(event.pos) and pygame.mouse.get_pressed()[0]:
                        cp = self._canvas_pos(event.pos)
                        self.tool.on_mouse_move(cp, self.canvas,
                                                self.color, self.brush_size)

                # ── Mouse button up ──
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self._on_canvas(event.pos):
                        cp = self._canvas_pos(event.pos)
                        self.tool.on_mouse_up(cp, self.canvas,
                                              self.color, self.brush_size)

            # ── Render ──
            self.screen.fill(BG_DARK)
            self._draw_canvas(mx, my)
            self._draw_toolbar(mx, my)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()



if __name__ == "__main__":
    PaintApp().run()

"""
ui.py — Reusable Pygame UI helpers.
"""

import pygame

#  Palette 
C_BG        = (15,  15,  25)
C_PANEL     = (25,  25,  40)
C_BORDER    = (60,  60,  100)
C_BTN       = (40,  40,  65)
C_BTN_HOV   = (60,  60,  95)
C_BTN_ACT   = (70,  130, 220)
C_TEXT      = (220, 220, 240)
C_ACCENT    = (70,  200, 120)
C_WARN      = (220, 100,  50)
C_WHITE     = (255, 255, 255)
C_BLACK     = (0,   0,   0)


def draw_button(surface, rect, label, font,
                active=False, hover=False, color=None):
    bg = color if color else (C_BTN_ACT if active else (C_BTN_HOV if hover else C_BTN))
    pygame.draw.rect(surface, bg,       rect, border_radius=8)
    pygame.draw.rect(surface, C_BORDER, rect, 2, border_radius=8)
    txt = font.render(label, True, C_WHITE)
    surface.blit(txt, (rect.centerx - txt.get_width()  // 2,
                       rect.centery - txt.get_height() // 2))


def draw_text(surface, text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    if center:
        x -= surf.get_width() // 2
    surface.blit(surf, (x, y))


def draw_panel(surface, rect, alpha=200):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    s.fill((*C_PANEL, alpha))
    surface.blit(s, rect.topleft)
    pygame.draw.rect(surface, C_BORDER, rect, 2, border_radius=10)


def is_hover(rect, mx, my):
    return rect.collidepoint(mx, my)

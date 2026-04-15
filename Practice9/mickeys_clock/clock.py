from datetime import datetime
from pathlib import Path

import pygame


WINDOW_SIZE = (900, 700)
FPS = 30
BACKGROUND = (245, 245, 245)
MINUTE_COLOR = (32, 32, 32)
SECOND_COLOR = (220, 40, 40)
CENTER_DOT_COLOR = (25, 25, 25)


def load_clock_face():
    image_path = Path(__file__).resolve().parent / "images" / "mickeyclock.jpeg"
    original = pygame.image.load(str(image_path)).convert()
    face = pygame.transform.smoothscale(original, (620, 465))
    face_rect = face.get_rect(center=(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2 - 20))
    center = face_rect.center
    return face, face_rect, center


def draw_hand(screen, center, angle, length, color, width):
    # Draw the hand on a separate surface first, then rotate the whole rectangle.
    hand_surface = pygame.Surface((width, length), pygame.SRCALPHA)
    pygame.draw.rect(hand_surface, color, (0, 0, width, length), border_radius=2)
    rotated_hand = pygame.transform.rotate(hand_surface, -angle)

    # Move the rotated hand so its base stays in the middle of the clock.
    offset = pygame.math.Vector2(0, -length / 2).rotate(angle)
    hand_rect = rotated_hand.get_rect(center=(center[0] + offset.x, center[1] + offset.y))
    screen.blit(rotated_hand, hand_rect)


def draw_scene(screen, face, face_rect, center, font, small_font):
    now = datetime.now()

    # 360 / 60 = 6 degrees for each minute or second step.
    minute_angle = now.minute * 6 + now.second * 0.1
    second_angle = now.second * 6

    screen.fill(BACKGROUND)
    screen.blit(face, face_rect)

    # Keep the minute hand a bit shorter so both hands stay inside the dial.
    draw_hand(screen, center, minute_angle, 110, MINUTE_COLOR, 12)
    draw_hand(screen, center, second_angle, 155, SECOND_COLOR, 10)
    pygame.draw.circle(screen, CENTER_DOT_COLOR, center, 10)

    time_text = font.render(now.strftime("%H:%M:%S"), True, (30, 30, 30))
    info_text = small_font.render(
        "Right-style hand = minutes, left-style hand = seconds", True, (60, 60, 60)
    )

    screen.blit(time_text, time_text.get_rect(center=(WINDOW_SIZE[0] // 2, 40)))
    screen.blit(info_text, info_text.get_rect(center=(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] - 35)))


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Mickey's Clock")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28)
    small_font = pygame.font.SysFont("arial", 22)
    face, face_rect, center = load_clock_face()

    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        draw_scene(screen, face, face_rect, center, font, small_font)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

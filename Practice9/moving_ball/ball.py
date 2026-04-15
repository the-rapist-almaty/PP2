import pygame


WINDOW_SIZE = (600, 600)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
STEP = 20
RADIUS = 25
FPS = 60


def keep_inside(x, y):
    x = max(RADIUS, min(WINDOW_SIZE[0] - RADIUS, x))
    y = max(RADIUS, min(WINDOW_SIZE[1] - RADIUS, y))
    return x, y


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Moving Ball")
    clock = pygame.time.Clock()

    x = WINDOW_SIZE[0] // 2
    y = WINDOW_SIZE[1] // 2
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_UP]:
            y -= STEP
        if pressed[pygame.K_DOWN]:
            y += STEP
        if pressed[pygame.K_LEFT]:
            x -= STEP
        if pressed[pygame.K_RIGHT]:
            x += STEP

        # Keep the ball inside the screen after every movement update.
        x, y = keep_inside(x, y)

        screen.fill(WHITE)
        pygame.draw.circle(screen, RED, (x, y), RADIUS)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

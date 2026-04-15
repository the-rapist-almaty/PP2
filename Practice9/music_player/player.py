from pathlib import Path

import pygame


WINDOW_SIZE = (800, 300)
BACKGROUND = (18, 22, 33)
PANEL = (28, 34, 48)
ACCENT = (88, 166, 255)
TEXT = (238, 242, 247)
MUTED = (150, 160, 175)
FPS = 30


def load_playlist():
    music_dir = Path(__file__).resolve().parent / "music"
    return sorted(music_dir.glob("*.wav"))


def load_current_track(playlist, current_index):
    current_track = playlist[current_index]
    pygame.mixer.music.load(str(current_track))

    # Sound is only used here to get the track duration for the progress bar.
    return int(pygame.mixer.Sound(str(current_track)).get_length() * 1000)


def play_track(is_playing):
    if is_playing:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.play()
    return True


def stop_track():
    pygame.mixer.music.stop()
    return False


def next_track(playlist, current_index):
    current_index = (current_index + 1) % len(playlist)
    track_length_ms = load_current_track(playlist, current_index)
    pygame.mixer.music.play()
    return current_index, track_length_ms


def previous_track(playlist, current_index):
    current_index = (current_index - 1) % len(playlist)
    track_length_ms = load_current_track(playlist, current_index)
    pygame.mixer.music.play()
    return current_index, track_length_ms


def get_progress_ms():
    position = pygame.mixer.music.get_pos()
    return max(position, 0)


def draw_scene(screen, title_font, text_font, small_font, playlist, current_index, track_length_ms, is_playing):
    screen.fill(BACKGROUND)
    pygame.draw.rect(screen, PANEL, (35, 35, 730, 230), border_radius=16)

    current_name = playlist[current_index].name
    title = title_font.render("Keyboard Music Player", True, TEXT)
    track = text_font.render(f"Track: {current_name}", True, TEXT)
    controls = small_font.render("P Play  S Stop  N Next  B Back  Q Quit", True, MUTED)

    position = min(get_progress_ms(), track_length_ms)
    progress_ratio = 0 if track_length_ms == 0 else position / track_length_ms
    bar_width = 620
    progress_width = int(bar_width * progress_ratio)

    # Draw the full bar first, then overlay the active progress.
    pygame.draw.rect(screen, (60, 67, 82), (90, 175, bar_width, 18), border_radius=9)
    pygame.draw.rect(screen, ACCENT, (90, 175, progress_width, 18), border_radius=9)

    status_text = "Playing" if is_playing and pygame.mixer.music.get_busy() else "Stopped"
    status = small_font.render(f"Status: {status_text}", True, ACCENT)
    timer = small_font.render(
        f"Position: {position / 1000:.1f}s / {track_length_ms / 1000:.1f}s", True, TEXT
    )

    screen.blit(title, (75, 60))
    screen.blit(track, (75, 110))
    screen.blit(status, (75, 145))
    screen.blit(timer, (90, 205))
    screen.blit(controls, (75, 240))


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Music Player")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 32, bold=True)
    text_font = pygame.font.SysFont("arial", 24)
    small_font = pygame.font.SysFont("arial", 18)

    # Read all wav files from the local music folder and use them as a playlist.
    playlist = load_playlist()
    current_index = 0
    track_length_ms = load_current_track(playlist, current_index)
    is_playing = False

    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    done = True
                elif event.key == pygame.K_p:
                    is_playing = play_track(is_playing)
                elif event.key == pygame.K_s:
                    is_playing = stop_track()
                elif event.key == pygame.K_n:
                    current_index, track_length_ms = next_track(playlist, current_index)
                    is_playing = True
                elif event.key == pygame.K_b:
                    current_index, track_length_ms = previous_track(playlist, current_index)
                    is_playing = True

        # If the current song ends, switch to the next one automatically.
        if is_playing and not pygame.mixer.music.get_busy() and get_progress_ms() == 0:
            current_index, track_length_ms = next_track(playlist, current_index)

        draw_scene(screen, title_font, text_font, small_font, playlist, current_index, track_length_ms, is_playing)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.mixer.music.stop()
    pygame.quit()

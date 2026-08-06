# library imports
import os
from pathlib import Path

import pygame
import sys

from player import Player
from world import Floor
from camera import Camera

PROJECT_ROOT = Path(__file__).resolve().parent

# initialisation
pygame.init()

# window
screen = pygame.display.set_mode((800,600))
pygame.display.set_caption("Gone Rogue - Character Movement")

clock = pygame.time.Clock()

# helpers functions

# pick frames out of an animation folder by index
def resolve_asset_folder(folder):
    path = Path(folder)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def load_folder_frames(folder, indices_1_based):
    folder_path = resolve_asset_folder(folder)
    png_paths = sorted(folder_path.glob("*.png"), key=lambda p: p.name.lower())
    selected = []
    for idx in indices_1_based:
        if 1 <= idx <= len(png_paths):
            selected.append(png_paths[idx - 1])

    frames = []
    for path in selected:
        frame = pygame.image.load(str(path)).convert_alpha()
        frames.append(frame)

    if not frames:
        fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
        fallback.fill((255, 0, 255))
        return [fallback]

    return frames

# 0-based variant for 01/02/03 etc.
def load_folder_frames_0based(folder, indices_0_based):
    folder_path = resolve_asset_folder(folder)
    png_paths = sorted(folder_path.glob("*.png"), key=lambda p: p.name.lower())
    selected = []
    for idx in indices_0_based:
        if 0 <= idx < len(png_paths):
            selected.append(png_paths[idx])

    frames = []
    for path in selected:
        frame = pygame.image.load(str(path)).convert_alpha()
        frames.append(frame)

    if not frames:
        fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
        fallback.fill((255, 0, 255))
        return [fallback]

    return frames

# scale a list of frames to a uniform size
def scale_frames(frames, size=(64, 64)):
    return [pygame.transform.scale(f, size) for f in frames]

# flip a frame list horizontally to produce the opposite-facing variant
def mirror(frames):
    return [pygame.transform.flip(f, True, False) for f in frames]

# animation lists
# front run: 01, 02, 03
front_run = scale_frames(
    load_folder_frames(
        "assets/images/main character/front-animations",
        [1, 2, 3],
    )
)

# back run: 01, 02, 03
back_run = scale_frames(
    load_folder_frames(
        "assets/images/main character/back-animations",
        [1, 2, 3],
    )
)

# side run: 01, 02, 03, 04, 05
side_run = scale_frames(
    load_folder_frames(
        "assets/images/main character/side-animations",
        [1, 2, 3],
    )
)
# mirror the right-facing side run to get a left-facing side run
left_run = mirror(side_run)

# backside run: 03, 04, 05 (0-based: sprite_03, sprite_04, sprite_05)
backside_run = scale_frames(
    load_folder_frames_0based(
        "assets/images/main character/backside-animations",
        [3, 4, 5],
    )
)
backleft_run = mirror(backside_run)

# frontside run: 03, 04, 05 (0-based: sprite_03, sprite_04, sprite_05)
frontside_run = scale_frames(
    load_folder_frames_0based(
        "assets/images/main character/frontside-animations",
        [3, 4, 5],
    )
)
frontleft_run = mirror(frontside_run)

animations = {
    "front":        front_run,
    "back":         back_run,
    "side":         side_run,
    "side_left":    left_run,
    "backside":     backside_run,
    "backside_left":backleft_run,
    "frontside":    frontside_run,
    "frontside_left": frontleft_run,
}

# character position
floor = Floor()
camera = Camera(800, 600, 64, 128, 64)
player = Player(*floor.find_spawn_point(), animations)
floor_number = 1
font = pygame.font.SysFont(None, 26)

# player loop
playing = True
while playing:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            playing = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                floor.try_unlock_elevator(player.rect)
            elif event.key == pygame.K_ESCAPE:
                playing = False

    keys = pygame.key.get_pressed()
    dx, dy = player.handle_input(keys)
    player.move(dx, dy, floor.get_solid_rects())
    player.update_animation()

    if floor.check_elevator(player.rect):
        floor_number += 1
        floor.build()
        player.teleport_to(*floor.find_spawn_point())

    camera.update(player.wx, player.wy)

    # drawing — split the iso floor around the player's tile so the player
    # renders on top of their standing tile and everything farther away
    # (north-west), but is occluded by tiles closer to the camera (south-east).
    screen.fill((15, 15, 20))
    player_depth = floor.draw_behind_player(screen, camera, player.feet_wx, player.feet_wy)
    player.draw(screen, camera)
    floor.draw_in_front_of_player(screen, camera, player_depth)

    elevator_state = "LOCKED" if floor.elevator_locked else "OPEN"
    label = font.render(
        f"Floor {floor_number}  |  Elevator: {elevator_state}  |  "
        f"WASD/arrows move, E opens the elevator, Esc quits",
        True, (255, 255, 255))
    screen.blit(label, (10, 10))

    pygame.display.flip()

print("play again bro or are you too scareeeeeed...")
pygame.quit()
sys.exit()
# library imports
import pygame
import math
import sys
import os

from player import Player

# initialisation
pygame.init()

# colours
black = (0,0,0)
red = (255,0,0)
orange = (255, 128, 0)
yellow = (255, 255, 0)
lime = (149, 255, 0)
green = (0,255,0)

blue = (0,0,255)
purple = (171, 0, 255)
pink = (255, 0, 186)
white = (255,255,255)

# window
screen = pygame.display.set_mode((800,600))
pygame.display.set_caption("Gone Rogue - Chracter Movement")

clock = pygame.time.Clock()

# helpers functions

# pick frames out of an animation folder by index
def load_folder_frames(folder, indices_1_based):
    files = sorted(os.listdir(folder))
    pngs = [f for f in files if f.lower().endswith(".png")]
    selected = []
    for idx in indices_1_based:
        if 1 <= idx <= len(pngs):
            selected.append(pngs[idx - 1])
    frames = []
    for fname in selected:
        path = os.path.join(folder, fname)
        frames.append(pygame.image.load(path))
    return frames

# 0-based variant for 01/02/03 etc.
def load_folder_frames_0based(folder, indices_0_based):
    files = sorted(os.listdir(folder))
    pngs = [f for f in files if f.lower().endswith(".png")]
    selected = []
    for idx in indices_0_based:
        if 0 <= idx < len(pngs):
            selected.append(pngs[idx])
    frames = []
    for fname in selected:
        path = os.path.join(folder, fname)
        frames.append(pygame.image.load(path))
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
    "frontside":    front_run
}

# character position
player = Player(*floor.find_spawn_point(), animations)
floor_number = 1

# last direction the player pressed - used to pick the right sprite set
facing = "front"
facing_left = False

# walk / idle frame bookkeeping
current_frame = 0
frame_delay = 150
last_frame_time = pygame.time.get_ticks()

# movement speed
speed = 3

# player loop
playing = True
while playing:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            playing = False

    keys = pygame.key.get_pressed()
    dx, dy = player.handle_input(keys)
    player.move(dx, dy, floor.get_solid_rects()) # for adding floors later
    player.update_animation()

    # drawing (utilising a camera/floor template I will actually code later)
    screen.fill((15, 15, 20))
    floor.draw(screen, camera)
    player.draw(screen, camera)
    pygame.display.flip()

print("play again bro or are you too scareeeeeed...")
pygame.quit()
sys.exit()
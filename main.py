# library imports
import pygame
import math
import sys
import os

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


# character position
x = 400
y = 300

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

    # track which directions are held this frame
    up    = keys[pygame.K_w] or keys[pygame.K_UP]
    down  = keys[pygame.K_s] or keys[pygame.K_DOWN]
    left  = keys[pygame.K_a] or keys[pygame.K_LEFT]
    right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
    escape = keys[pygame.K_ESCAPE]

    moving = False
    dx = 0
    dy = 0

    if escape:
        playing = False

    # cardinal movement
    if left:
        dx -= speed
        moving = True
    if right:
        dx += speed
        moving = True
    if up:
        dy -= speed
        moving = True
    if down:
        dy += speed
        moving = True

    if dx != 0 and dy != 0:
        inv = 1 / math.sqrt(2)
        dx *= inv
        dy *= inv

    x += dx
    y += dy

    if moving:
        if up and not down and not left and not right:
            facing = "back"
        elif down and not up and not left and not right:
            facing = "front"
        elif left and not right and not up and not down:
            facing = "side"
            facing_left = True
        elif right and not left and not up and not down:
            facing = "side"
            facing_left = False
        elif up and right:
            facing = "backside"
            facing_left = False
        elif up and left:
            facing = "backside"
            facing_left = True
        elif down and right:
            facing = "frontside"
            facing_left = False
        elif down and left:
            facing = "frontside"
            facing_left = True

    # pick the right run frame list for the current facing
    if facing == "back":
        run_frames = back_run
    elif facing == "front":
        run_frames = front_run
    elif facing == "side":
        run_frames = left_run if facing_left else side_run
    elif facing == "backside":
        run_frames = backleft_run if facing_left else backside_run
    elif facing == "frontside":
        run_frames = frontleft_run if facing_left else frontside_run
    else:
        run_frames = front_run

    # advance the animation
    if moving:
        frames_to_use = run_frames
    else:
        frames_to_use = run_frames
        current_frame = 0

    if frames_to_use:
        current_frame %= len(frames_to_use)
    else:
        current_frame = 0

    now = pygame.time.get_ticks()
    if moving and now - last_frame_time > frame_delay:
        current_frame = (current_frame + 1) % len(frames_to_use)
        last_frame_time = now

    # draw
    screen.fill((40, 40, 40))
    screen.blit(frames_to_use[current_frame], (x, y))
    pygame.display.flip()

print("play again bro or are you too scareeeeeed...")
pygame.quit()
sys.exit()
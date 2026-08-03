# library imports
import pygame
import random
import math
import sys


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
pygame.display.set_caption("charaacter does not move well bruh")

clock = pygame.time.Clock()

# animation lists
front_frames = []

back_frames = []

right_frames = [
    pygame.image.load("assets/images/main character/side-animations/sprite_00.png"),
    pygame.image.load("assets/images/main character/side-animations/sprite_01.png"),
    pygame.image.load("assets/images/main character/side-animations/sprite_02.png")
]

frontright_frames = []

backright_frames = []

# scale the pixel art up to size
front_frames = [pygame.transform.scale(frame, (64, 64)) for frame in front_frames]
back_frames = [pygame.transform.scale(frame, (64, 64)) for frame in back_frames]
right_frames = [pygame.transform.scale(frame, (64, 64)) for frame in right_frames]
left_frames = [pygame.transform.flip(frame, True, False) for frame in right_frames]
frontright_frames = [pygame.transform.scale(frame, (64, 64)) for frame in frontright_frames]
frontleft_frames = [pygame.transform.flip(frame, True, False) for frame in frontright_frames]
backright_frames = [pygame.transform.scale(frame, (64, 64)) for frame in backright_frames]
backleft_frames = [pygame.transform.flip(frame, True, False) for frame in backright_frames]


current_frame = 0
frame_delay = 150
last_frame_time =pygame.time.get_ticks()

# character position
x = 400
y = 300
facing_left = False


playing = True
while playing:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            playing = False

    keys = pygame.key.get_pressed()

    moving = False

    # RIGHT (D or →)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        x += 3
        facing_left = False
        moving = True

    # LEFT (A or ←)
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        x -= 3
        facing_left = True
        moving = True

    # animation update
    if moving:
        now = pygame.time.get_ticks()
        if now - last_frame_time > frame_delay:
            # cycle only frames 1 and 2 (walking)
            current_frame = 1 + ((current_frame - 1 + 1) % 2)
            last_frame_time = now
    else:
        current_frame = 0  # idle frame

    # draw
    screen.fill(yellow)

    if facing_left:
        screen.blit(left_frames[current_frame], (x, y))
    else:
        screen.blit(right_frames[current_frame], (x, y))

    pygame.display.flip()


pygame.quit()
sys.exit()
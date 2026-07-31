# library imports
import pygame
import random
import math
import sys


# initialisation
pygame.init()


# window
screen = pygame.display.set_mode((800,600))
pygame.display.set_caption("character movement")

clock = pygame.time.Clock()

# animation lists
side_frames = [
    pygame.image.load("assets/images/main character/side-animations/sprite_00.png"),
    pygame.image.load("assets/images/main character/side-animations/sprite_01.png"),
    pygame.image.load("assets/images/main character/side-animations/sprite_02.png")
]


# scale the pixel art up to size
side_frames = [pygame.transform.scale(frame, (128, 128)) for frame in side_frames]

left_frames = [pygame.transform.flip(frame, True, False) for frame in side_frames]


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

    if keys[pygame.K_d]:
        x += 3
        facing_left = False

        now = pygame.time.get_ticks()
        if now - last_frame_time > frame_delay:
            current_frame = (current_frame + 1) % len(side_frames)
            last_frame_time = now

    elif keys[pygame.K_a]:
        x -= 3
        facing_left = True

        now = pygame.time.get_ticks()
        if now - last_frame_time > frame_delay:
            current_frame = (current_frame + 1) % len(side_frames)
            last_frame_time = now

    else:
        # idle frame
        current_frame = 0


    screen.fill((0, 0, 0))
    screen.blit(side_frames[current_frame], (x, y))
    pygame.display.flip()

pygame.quit()
sys.exit()
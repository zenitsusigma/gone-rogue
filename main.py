# library imports
import os
from pathlib import Path

import pygame
import sys

from player import Player
from world import Floor, init_tile_images
from camera import Camera

PROJECT_ROOT = Path(__file__).resolve().parent

# initialisation
pygame.init()

# window
screen = pygame.display.set_mode((800,600))
init_tile_images()
pygame.display.set_caption("Gone Rogue tile renderer")

clock = pygame.time.Clock()

# a bunch of helper functions

# pick grames out of an animation folder by index
def resolve_asset_folder(folder):
    path = Path(folder)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path

# singular loader now because indices are always 0-based, matching filenames.
def load_indices(folder, indices_0_based):
    folder_path = resolve_asset_folder(folder)
    png_paths = sorted(folder_path.glob("*.png"), key = lambda p: p.name.lower())
    frames = []
    for idx in indices_0_based:
        if 0 <= idx < len(png_paths):
            frame = pygame.image.load(str(png_paths[idx])).convert_alpha()
            frames.append(frame)

    if not frames:
        fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
        fallback.fill((255, 0, 255))
        return [fallback]

    return frames

def scale_frames(frames, size=(64,64)):
    return [pygame.transform.scale(f, size) for f in frames]

def mirror(frames):
    return [pygame.transform.flip(f, True, False) for f in frames]

def mirror_states(state_dict):
    return {state: mirror(frames) for state, frames in state_dict.items()}

frame_map = {
    "front": {
        "idle":[0], 
        "run":[1,2,3], 
        "pistol":[4,5,6], 
        "rifle":[7,8], 
        "dying":[9,10],
    },
    "back": {
        "idle":[0], 
        "run":[1,2,3], 
        "pistol":[4,5,6], 
        "rifle":[7,8], 
        "dying":[9,10],
    },
    "side": {
        "idle":[0], 
        "run":[1, 2, 3], 
        "pistol":[4, 5, 6], 
        "rifle":[7, 8], 
        "dying":[9, 10, 11],
    },
    "backside": {
        "idle":[0], 
        "sitting":[1], 
        "crouching":[2], 
        "run":[3, 4, 5], 
        "pistol":[6, 7, 8], 
        "rifle":[9, 10, 11], 
        "dying":[12, 13, 14],
    },
    "frontside": {
        "idle":[0], 
        "sitting":[1], 
        "crouching":[2], 
        "run":[3, 4, 5], 
        "pistol":[6, 7, 8], 
        "rifle":[9, 10, 11], 
        "dying":[12, 13, 14],
    }
}

folder_for_direction = {
    "front":        "assets/images/main character/front-animations",
    "back":         "assets/images/main character/back-animations",
    "side":         "assets/images/main character/side-animations",
    "backside":     "assets/images/main character/backside-animations",
    "frontside":    "assets/images/main character/frontside-animations",
}

def build_direction_animations(direction):
    folder = folder_for_direction[direction]
    return {
        state: scale_frames(load_indices(folder, indices))
        for state, indices in frame_map[direction].items()
    }

front_anim = build_direction_animations("front")
back_anim = build_direction_animations("back")
side_anim = build_direction_animations("side")
backside_anim = build_direction_animations("backside")
frontside_anim = build_direction_animations("frontside")

animations = {
    "front":            front_anim,
    "back":             back_anim,
    "side":             side_anim,
    "side_left":        mirror_states(side_anim),
    "backside":         backside_anim,
    "backside_left":    mirror_states(backside_anim),
    "frontside":        frontside_anim,
    "frontside_left":   mirror_states(frontside_anim),
}

# character position
floor = Floor()
camera = Camera(800, 600, 64, 128, 64)
# temporary demo props – delete later
floor.add_prop(2, 2, "table_mug_blue")
floor.add_prop(3, 2, "chair")
floor.add_prop(4, 4, "crate")
floor.add_prop(5, 2, "drawers")
floor.add_wall_decor(0, 3, "left", "sign")
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
            elif event.key == pygame.K_1:
                player.set_action(None)
            elif event.key == pygame.K_2:
                player.set_action("pistol")
            elif event.key == pygame.K_3:
                player.set_action("rifle")
            elif event.key == pygame.K_k:
                player.play_death()
            elif event.key == pygame.K_1 and player.dying:
                player.reset_death()

    keys = pygame.key.get_pressed()
    if player.dying:
        player.moving = False
    else:
        dx, dy = player.handle_input(keys)
        player.move(dx, dy, floor.get_solid_rects())
    player.update_animation()

    if floor.check_elevator(player.rect):
        floor_number += 1
        floor.build()
        player.teleport_to(*floor.find_spawn_point())

    camera.update(player.wx, player.wy)

    screen.fill((15, 15, 20))
    player_depth = floor.draw_behind_player(screen, camera, player.feet_wx, player.feet_wy, player.wx, player.wy)
    player.draw(screen, camera)
    floor.draw_in_front_of_player(screen, camera, player_depth)
    floor.draw_props(screen, camera)

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
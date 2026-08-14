# library imports
import os
from pathlib import Path

import pygame
import sys

from player import Player
from enemy import Enemy
from world import Floor, init_tile_images, OffsetTuner, tile_size, floor as FLOOR_TILE
from camera import Camera
import random

PROJECT_ROOT = Path(__file__).resolve().parent
GAME_FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "Jersey10-Regular.ttf"
MENU_BACKGROUND_PATH = PROJECT_ROOT / "assets" / "images" / "pixel_art_large (1).png"

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

WORKER_VARIANTS = ["red", "green", "blue"]
WORKER_SPRITE_SIZE = (56, 56)
WORKER_COUNT_PER_FLOOR = 5


def build_worker_animations(variant):
    folder = f"assets/images/enemy/worker/{variant}"
    idle = scale_frames(load_indices(folder, [0]), size=WORKER_SPRITE_SIZE)
    walk = scale_frames(load_indices(folder, [1, 2, 3, 4, 5, 6, 7, 8]), size=WORKER_SPRITE_SIZE)
    return {
        "idle": idle,
        "walk": walk,
        "idle_left": mirror(idle),
        "walk_left": mirror(walk),
    }


worker_animations = {variant: build_worker_animations(variant) for variant in WORKER_VARIANTS}

BULLET_FRAME_SIZE = (40, 40)
bullet_frames = scale_frames(
    load_indices("assets/images/items/weapons", list(range(9))),
    size=BULLET_FRAME_SIZE,
)


def spawn_workers(floor_obj, avoid_point, count=WORKER_COUNT_PER_FLOOR, min_distance=1.5):
    """Place `count` workers on random floor tiles, skipping any tile too
    close to `avoid_point` (the player's spawn) and any tile that already
    has a solid prop on it."""
    ax, ay = avoid_point
    min_px = min_distance * tile_size
    occupied = {(row, col) for row, col, _ in floor_obj.props}
    candidates = []
    for row in range(floor_obj.rows):
        for col in range(floor_obj.cols):
            if floor_obj.grid[row][col] != FLOOR_TILE:
                continue
            if (row, col) in occupied:
                continue
            wx = (col + 0.5) * tile_size
            wy = (row + 0.5) * tile_size
            if ((wx - ax) ** 2 + (wy - ay) ** 2) ** 0.5 < min_px:
                continue
            candidates.append((wx, wy))

    random.shuffle(candidates)
    spawned = []
    for wx, wy in candidates[:count]:
        variant = random.choice(WORKER_VARIANTS)
        spawned.append(Enemy(wx, wy, worker_animations[variant], variant))
    return spawned

# character position
floor = Floor()
camera = Camera(800, 600, 64, 128, 64)
# temporary demo props – delete later
floor.add_prop(2, 2, "table_mug_blue")
floor.add_prop(3, 2, "chair")
floor.add_prop(4, 4, "crate")
floor.add_prop(5, 2, "drawers")
floor.add_wall_decor(0, 3, "left", "sign")
spawn_point = floor.find_spawn_point()
player = Player(*spawn_point, animations, bullet_frames)
enemies = spawn_workers(floor, spawn_point)
bullets = []
floor_number = 1
font = pygame.font.Font(str(GAME_FONT_PATH), 28)
tuner = OffsetTuner()
tuner_font = pygame.font.Font(str(GAME_FONT_PATH), 18)


def load_menu_background(size):
    """Scale the square artwork to cover the menu without stretching it."""
    image = pygame.image.load(str(MENU_BACKGROUND_PATH)).convert()
    scale = max(size[0] / image.get_width(), size[1] / image.get_height())
    scaled_size = (round(image.get_width() * scale), round(image.get_height() * scale))
    image = pygame.transform.scale(image, scaled_size)
    crop = pygame.Rect(
        (image.get_width() - size[0]) // 2,
        (image.get_height() - size[1]) // 2,
        *size,
    )
    return image.subsurface(crop).copy()


def draw_menu_button(surface, rect, text, font, selected):
    fill = (50, 120, 132) if selected else (18, 28, 35)
    border = (180, 255, 250) if selected else (120, 170, 175)
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, 3)
    label = font.render(text, True, (255, 255, 255))
    surface.blit(label, label.get_rect(center=rect.center))


def show_main_menu(surface, menu_clock):
    background = load_menu_background(surface.get_size())
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((0, 8, 15, 145))
    title_font = pygame.font.Font(str(GAME_FONT_PATH), 88)
    button_font = pygame.font.Font(str(GAME_FONT_PATH), 38)
    start_button = pygame.Rect(65, 330, 270, 64)
    exit_button = pygame.Rect(65, 410, 270, 64)
    buttons = [start_button, exit_button]
    selected = 0

    while True:
        menu_clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        for index, button in enumerate(buttons):
            if button.collidepoint(mouse_pos):
                selected = index

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.collidepoint(event.pos):
                    return True
                if exit_button.collidepoint(event.pos):
                    return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(buttons)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(buttons)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return selected == 0
                elif event.key == pygame.K_ESCAPE:
                    return False

        surface.blit(background, (0, 0))
        surface.blit(shade, (0, 0))
        title = title_font.render("GONE ROGUE", True, (220, 255, 250))
        surface.blit(title, (60, 155))
        draw_menu_button(surface, start_button, "START GAME", button_font, selected == 0)
        draw_menu_button(surface, exit_button, "EXIT", button_font, selected == 1)
        pygame.display.flip()


# player loop
playing = show_main_menu(screen, clock)
while playing:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            playing = False
        elif event.type == pygame.KEYDOWN:
            tuner.handle_key(event.key, event.mod)
            if event.key == pygame.K_e:
                floor.try_unlock_elevator(player.rect)
            elif event.key == pygame.K_ESCAPE:
                playing = False
            elif event.key == pygame.K_1:
                if player.dying:
                    player.reset_death()
                else:
                    player.set_action(None)
            elif event.key == pygame.K_2:
                player.set_action("pistol")
            elif event.key == pygame.K_3:
                player.set_action("rifle")
            elif event.key == pygame.K_k:
                player.play_death()

    keys = pygame.key.get_pressed()
    solid_rects = floor.get_solid_rects()
    if player.dying or tuner.active:
        player.moving = False
    else:
        dx, dy = player.handle_input(keys)
        player.move(dx, dy, solid_rects)
    player.update_animation()

    if not tuner.active:
        fire_pressed = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]
        if fire_pressed:
            player.fire(bullets)

        for worker in enemies:
            worker.update(solid_rects)

        alive_bullets = []
        for bullet in bullets:
            if bullet.update(camera):
                for worker in enemies:
                    if bullet.check_hit(worker):
                        bullet.dead = True
                        worker.hp -= 1
                        break
                if not bullet.dead:
                    alive_bullets.append(bullet)
        bullets = alive_bullets
        enemies = [w for w in enemies if w.hp > 0]

    tuner.update()

    if floor.check_elevator(player.rect):
        floor_number += 1
        floor.build()
        spawn_point = floor.find_spawn_point()
        player.teleport_to(*spawn_point)
        enemies = spawn_workers(floor, spawn_point)
        bullets = []

    camera.update(player.wx, player.wy)

    screen.fill((15, 15, 20))
    floor.draw_scene(screen, camera, [player] + enemies + bullets)

    elevator_state = "LOCKED" if floor.elevator_locked else "OPEN"
    label = font.render(
        f"Floor {floor_number}  |  Elevator: {elevator_state}  |  "
        f"WASD/arrows move, 2/3 switch to pistol/rifle, Space fires, E opens the elevator, Esc quits",
        True, (255, 255, 255))
    screen.blit(label, (10, 10))
    tuner.draw(screen, tuner_font)

    pygame.display.flip()

print("play again bro or are you too scareeeeeed...")
pygame.quit()
sys.exit()

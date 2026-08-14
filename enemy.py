"""
Tier 1 enemy: the Faceless Worker. Wanders the floor and bounces off
anything solid. No combat yet -- damage/incapacitation gets wired in once
the weapon system exists.
"""

import math
import random

import pygame


class Enemy:
    speed = 1.4
    frame_delay = 130
    size = 56  # must match the size passed into scale_frames() in main.py

    def __init__(self, wx, wy, animations, variant):
        self.wx = float(wx)
        self.wy = float(wy)
        self.variant = variant           # "red" / "green" / "blue"
        self.animations = animations     # {"idle","walk","idle_left","walk_left"}

        # collision box a bit smaller than the sprite so it doesn't feel unfair
        hitbox = int(self.size * 0.5)
        self.rect = pygame.Rect(0, 0, hitbox, hitbox)
        self.rect.center = (int(self.wx), int(self.wy))

        self.facing_left = False
        self.moving = False
        self.vx = 0.0
        self.vy = 0.0

        self.current_frame = 0
        self.last_frame_time = pygame.time.get_ticks()

        self.wander_timer = 0
        self._pick_new_direction()
        self.hp = 2

    def _pick_new_direction(self):
        """Roll either a short idle pause or a new wander direction."""
        if random.random() < 0.3:
            self.vx = self.vy = 0.0
            self.moving = False
            self.wander_timer = random.randint(40, 100)
        else:
            angle = random.uniform(0, math.tau)
            self.vx = math.cos(angle) * self.speed
            self.vy = math.sin(angle) * self.speed
            self.moving = True
            if abs(self.vx) > 0.01:
                self.facing_left = self.vx < 0
            self.wander_timer = random.randint(90, 220)

    def update(self, solid_rects):
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            self._pick_new_direction()

        if self.moving:
            bumped = False

            self.wx += self.vx
            self.rect.centerx = int(self.wx)
            if any(self.rect.colliderect(tile) for tile in solid_rects):
                self.wx -= self.vx
                self.rect.centerx = int(self.wx)
                bumped = True

            self.wy += self.vy
            self.rect.centery = int(self.wy)
            if any(self.rect.colliderect(tile) for tile in solid_rects):
                self.wy -= self.vy
                self.rect.centery = int(self.wy)
                bumped = True

            if bumped:
                self._pick_new_direction()

        self._update_animation()

    def _frames(self):
        state = "walk" if self.moving else "idle"
        if self.facing_left:
            state += "_left"
        return self.animations.get(state) or self.animations["idle"]

    def _update_animation(self):
        frames = self._frames()
        now = pygame.time.get_ticks()
        self.current_frame %= len(frames)
        if not self.moving:
            self.current_frame = 0
        elif now - self.last_frame_time > self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(frames)
            self.last_frame_time = now

    def draw(self, surface, camera):
        frames = self._frames()
        sprite = frames[min(self.current_frame, len(frames) - 1)]
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        rect = sprite.get_rect(midbottom=(sx, sy))
        surface.blit(sprite, rect)
"""
My player class!!!
"""

import pygame

class Player:
    speed = 3
    frame_delay = 150

    def __init__(self, wx, wy, animations):
        self.wx = float(wx)
        self.wy = float(wy)

        self.rect = pygame.Rect(0, 0, 30, 30)
        self.rect.center = (int(self.wx), int(self.wy))

        self.animations = animations
        self.facing = "front"
        self.facing_left = False
        self.moving = False

        self.current_frame = 0
        self.last_frame_time = pygame.time.get_ticks()

        # stubs for inventory and health
        self.health = 100
        self.max_health = 100
        self.inventory = []

    def handle_input(self):
        up = keys[pygame.K_w] or keys[pygame.K_UP]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

        dx = dy = 0
        self.moving = False
        if left:
            dx -= self.speed
            self.moving = True
        if right:
            dx += self.speed
            self.moving = True
        if up:
            dy -= self.speed
            self.moving = True 
        if down:
            dy += self.speed
            self.moving = True

        if dx != 0 and dy != 0:
            dx * 0.7071
            dy * 0.7071

        if self.moving:
            if up and not down and not left and not right:
                self.facing = "back"
            elif down and not up and not left and not right =:
                self.facing = "front"
            elif left and not right and not up and not down:
                self.facing = "side"
                self.facing_left = True
            elif right and not left and not up and not down:
                self.facing = "side"
                self.facing_left = False
            elif up and right:
                self.facing = "backside"
                self.facing_left = False
            elif up and left:
                self.facing = "backside"
                self.facing_left = True
            elif down and right:
                self.facing = "frontside"
                self.facing_left = False
            elif down and left:
                self.facing = "frontside"
                self.facing_left = True

        return dx,dy

    def move(self, dx, dy, solid_rects):
        self.rect.x += int(dx)
        for tile in solid_rects:
            if self.rect.colliderect(tile):
                if dx > 0:
                    self.rect.right = tile.left
                elif dx < 0:
                    self.rect.left = tile.right

        self.rect.y += int(dy)
        for tile in solid_rects:
            if self.rect.colliderect(tile):
                if dy > 0:
                    self.rect.bottom = tile.top
                elif dy < 0:
                    self.rect.top = tile.bottom

        self.wx, self.wy = self.rect.centerx, self.rect.centery

    def teleport_to(self, wx, wy):
        self.wx, self.wy = float(wx), float(wy)
        self.rect.center = (int(self.wx), int(self.wy))

    def current_frames(self):
        key = self.facing
        if self.facing in ("side", "backside", "frontside") and self.facing_left:
            key = key + "_left"
        return self.animations.get(key, self.animation["front"])

    def update_animation(self):
        frames = self.current_frames
        if not frames:
            return
        self.current_frame %= len(frames)
        now = pygame.time.get_ticks()
        if self.moving and now - self.last_frame_time > self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(frames)
            self.last_frame_time = now
        elif not self.moving:
            self.current_frame = 0

    def draw(self, surface, camera):
        frames = self.current_frames()
        sprite = frames[self.current_frame]
        sx, sy =  camera.world_to_screen(self.wx, self.wy)
        rect = sprite.get_rect(midbottom=(sx, sy + 20)) # change adjustment later
        surface.blit(sprite, rect)
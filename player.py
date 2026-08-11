"""
My player class!!!
"""

import pygame

class Player:
    speed = 3
    frame_delay = 150
    # how far below the tile centre the sprite's feet sit on screen. kept as a
    # named constant so it's easy to tune; 0 means the feet sit exactly on the
    # tile centre, which keeps the tall sprite from overlapping the tiles
    # south-east of the player (so side walls no longer cover the character).
    feet_offset = 0

    def __init__(self, wx, wy, animations):
        self.wx = float(wx)
        self.wy = float(wy)
        self.fx = self.wx
        self.fy = self.wy

        self.rect = pygame.Rect(0, 0, 30, 30)
        self.rect.center = (int(self.wx), int(self.wy))

        self.animations = animations
        self.facing = "front"
        self.facing_left = False
        self.moving = False

        self.action = None
        self.dying = False
        self.death_done = False

        self.current_frame = 0
        self.last_frame_time = pygame.time.get_ticks()

        # stubs for inventory and health
        self.health = 100
        self.max_health = 100
        self.inventory = []

    def handle_input(self, keys):
        up = keys[pygame.K_w] or keys[pygame.K_UP]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

        # map the keys onto the iso grid so W/A/S/D move the player straight
        # up/left/down/right on screen instead of along the diagonal grid axes
        dx = dy = 0
        self.moving = False
        if up:
            dx -= 1
            dy -= 1
            self.moving = True
        if down:
            dx += 1
            dy += 1
            self.moving = True
        if left:
            dx -= 1
            dy += 1
            self.moving = True
        if right:
            dx += 1
            dy -= 1
            self.moving = True

        if dx != 0 or dy != 0:
            length = (dx * dx + dy * dy) ** 0.5
            dx = dx / length * self.speed
            dy = dy / length * self.speed

        if self.moving:
            if up and not down and not left and not right:
                self.facing = "back"
                self.facing_left = False
            elif down and not up and not left and not right:
                self.facing = "front"
                self.facing_left = False
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
        self.fx += dx
        self.rect.centerx = int(self.fx)
        hit = False
        for tile in solid_rects:
            if self.rect.colliderect(tile):
                hit = True
                if dx > 0:
                    self.rect.right = tile.left
                elif dx < 0:
                    self.rect.left = tile.right
        if hit:
            self.fx = float(self.rect.centerx)

        self.fy += dy
        self.rect.centery = int(self.fy)
        hit = False
        for tile in solid_rects:
            if self.rect.colliderect(tile):
                hit = True
                if dy > 0:
                    self.rect.bottom = tile.top
                elif dy < 0:
                    self.rect.top = tile.bottom
        if hit:
            self.fy = float(self.rect.centery)

        self.wx, self.wy = self.rect.centerx, self.rect.centery

    def teleport_to(self, wx, wy):
        self.wx, self.wy = float(wx), float(wy)
        self.fx, self.fy = self.wx, self.wy
        self.rect.center = (int(self.wx), int(self.wy))

    @property
    def feet_wx(self):
        return self.wx + self.feet_offset

    @property
    def feet_wy(self):
        return self.wy + self.feet_offset

    def set_action(self, action):
        if not self.dying:
            self.action = action

    def play_death(self):
        self.dying = True
        self.death_done = False
        self.current_frame = 0
        self.last_frame_time = pygame.time.get_ticks()

    def reset_death(self):
        self.dying = False
        self.death_done = False
        self.current_frame = 0

    def _current_state(self):
        if self.dying:
            return "dying"
        if self.action in ("pistol", "rifle"):
            return self.action
        if self.moving:
            return "run"
        return "idle"

    def current_frames(self):
        key = self.facing
        if self.facing in ("side", "backside", "frontside") and self.facing_left:
            key = key + "_left"
        direction_set = self.animations.get(key, self.animations["front"])

        state = self._current_state()
        frames = direction_set.get(state)
        if not frames:
            frames = direction_set.get("idle") or next(iter(direction_set.values()))
            state = "idle"
        return frames, state

    def update_animation(self):
        frames, state = self.current_frames()
        if not frames:
            return
        now = pygame.time.get_ticks()

        if state == "dying":
            if self.current_frame < len(frames) - 1:
                if now - self.last_frame_time > self.frame_delay:
                    self.current_frame += 1
                    self.last_frame_time = now
            else:
                self.death_done = True
            return

        self.current_frame %= len(frames)
        if state == "idle":
            self.current_frame = 0
        else:
            if now - self.last_frame_time > self.frame_delay:
                self.current_frame = (self.current_frame + 1) % len(frames)
                self.last_frame_time = now

    def draw(self, surface, camera):
        frames, _ = self.current_frames()
        sprite = frames[min(self.current_frame, len(frames) - 1)]
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        rect = sprite.get_rect(midbottom=(sx, sy + self.feet_offset))
        surface.blit(sprite, rect)
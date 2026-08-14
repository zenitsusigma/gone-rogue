"""
My player class!!!
"""

import pygame

from bullet import Bullet, WEAPON_STATS, FIRE_DIRECTIONS, flash_tint

class Player:
    speed = 3
    frame_delay = 150
    # how far below the tile centre the sprite's feet sit on screen. kept as a
    # named constant so it's easy to tune; 0 means the feet sit exactly on the
    # tile centre, which keeps the tall sprite from overlapping the tiles
    # south-east of the player (so side walls no longer cover the character).
    feet_offset = 0

    # combat feedback timing (ms)
    HURT_FLASH_MS = 150
    INVINCIBLE_MS = 500

    def __init__(self, wx, wy, animations, bullet_frames=None):
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

        # shooting state -- bullet_frames are loaded in main.py (the asset
        # loading helpers live there) and passed in on construction.
        self.bullet_frames = bullet_frames
        self.last_fire_time = 0
        self.firing = False

        self.current_frame = 0
        self.last_frame_time = pygame.time.get_ticks()
        self._last_state = None# combat feedback state
        self.hurt_until = 0
        self.invincible_until = 0

        # stubs for inventory and health
        self.health = 100
        self.max_health = 100
        self.inventory = []

    def handle_input(self, keys):
        up = keys[pygame.K_w] or keys[pygame.K_UP]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

        dx = dy = 0
        if up:    dx -= 1; dy -= 1
        if down:  dx += 1; dy += 1
        if left:  dx -= 1; dy += 1
        if right: dx += 1; dy -= 1

        self.moving = dx != 0 or dy != 0

        if self.moving:
            length = (dx * dx + dy * dy) ** 0.5
            dx = dx / length * self.speed
            dy = dy / length * self.speed

            # facing logic stays exactly as you already have it
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

        return dx, dy

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

    def take_damage(self, amount):
        """Apply damage unless dying or still within the post-hit
        invincibility window. Returns True if the hit actually landed."""
        now = pygame.time.get_ticks()
        if self.dying or now < self.invincible_until:
            return False
        self.health = max(0, self.health - amount)
        self.hurt_until = now + self.HURT_FLASH_MS
        self.invincible_until = now + self.INVINCIBLE_MS
        if self.health <= 0:
            self.play_death()
        return True

    def set_firing(self, firing):
        self.firing = firing and not self.dying

    def fire(self, bullets):
        """Spawn a bullet in the direction the player is facing, if they are
        holding a gun, the fire-rate cooldown has passed, and the current
        weapon's active-bullet cap isn't full. Returns the bullet or None."""
        if (self.dying or self.action not in WEAPON_STATS
                or self.bullet_frames is None):
            return None

        stats = WEAPON_STATS[self.action]
        now = pygame.time.get_ticks()
        if now - self.last_fire_time < stats["fire_rate"]:
            return None
        if len(bullets) >= stats["max_bullets"]:
            return None

        self.last_fire_time = now
        vx, vy = FIRE_DIRECTIONS.get((self.facing, self.facing_left), (0.7071, 0.7071))
        bullet = Bullet(
            self.wx + vx * 20,
            self.wy + vy * 20,
            vx, vy,
            self.bullet_frames,
            stats["bullet_speed"],
            stats["bullet_lifetime"],
        )
        bullets.append(bullet)
        return bullet

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
        if self.firing and self.action in ("pistol", "rifle"):
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

        if state != self._last_state:
            self._last_state = state
            self.current_frame = len(frames) - 1 if state in ("pistol", "rifle") else 0
            self.last_frame_time = now

        if state == "dying":
            if self.current_frame < len(frames) - 1:
                if now - self.last_frame_time > self.frame_delay:
                    self.current_frame += 1
                    self.last_frame_time = now
            else:
                self.death_done = True
            return

        if state in ("pistol", "rifle"):
            # Snap straight to the ready pose and hold there -- no more
            # replaying the "pull the gun out" frames every time you fire.
            self.current_frame = len(frames) - 1
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
        if pygame.time.get_ticks() < self.hurt_until:
            sprite = flash_tint(sprite)
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        rect = sprite.get_rect(midbottom=(sx, sy + self.feet_offset))
        surface.blit(sprite, rect)

    def draw_hitbox(self, surface, camera):
        """Draw the actual Cartesian collision rectangle in isometric view."""
        points = [
            camera.world_to_screen(self.rect.left, self.rect.top),
            camera.world_to_screen(self.rect.right, self.rect.top),
            camera.world_to_screen(self.rect.right, self.rect.bottom),
            camera.world_to_screen(self.rect.left, self.rect.bottom),
        ]
        pygame.draw.polygon(surface, (255, 60, 60), points, 2)
"""
Tier 1-3 enemies.
"""

import math
import random
import pygame
from bullet import Bullet, aim_at, flash_tint


class Enemy:
    speed = 1.4
    frame_delay = 130
    size = 56
    max_hp = 2

    # combat feedback timing (ms)
    HURT_FLASH_MS = 150
    DEATH_FALL_MS = 250     # "lean back" phase
    DEATH_FADE_MS = 500     # fade-out phase, after the lean
    DEATH_LEAN_DEGREES = 65

    def __init__(self, wx, wy, animations, variant):
        self.wx = float(wx)
        self.wy = float(wy)
        self.variant = variant
        self.animations = animations

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
        self.hp = self.max_hp

        # combat feedback state
        self.hurt_until = 0
        self.dying = False
        self.death_start = None

    def _pick_new_direction(self):
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

    def take_damage(self, amount):
        """Apply damage. Triggers the death sequence at 0 HP instead of an
        instant removal -- the caller keeps the enemy in its list until
        is_removable() says the fall+fade animation has finished."""
        if self.dying:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.start_death()
        else:
            self.hurt_until = pygame.time.get_ticks() + self.HURT_FLASH_MS

    def start_death(self):
        self.dying = True
        self.death_start = pygame.time.get_ticks()
        self.moving = False
        self.vx = self.vy = 0.0

    def is_removable(self):
        """True once the fall + fade sequence has fully played out -- only
        then should the caller actually drop this enemy from its list."""
        if not self.dying:
            return False
        now = pygame.time.get_ticks()
        return now >= self.death_start + self.DEATH_FALL_MS + self.DEATH_FADE_MS

    def _death_progress(self):
        """Returns (lean_fraction 0-1, alpha 0-255) for the current moment
        in the death sequence."""
        now = pygame.time.get_ticks()
        t = now - self.death_start
        lean_t = max(0.0, min(1.0, t / self.DEATH_FALL_MS))
        fade_t = max(0.0, min(1.0, (t - self.DEATH_FALL_MS) / self.DEATH_FADE_MS))
        return lean_t, int(255 * (1.0 - fade_t))

    def update(self, solid_rects, player=None, bullets_out=None):
        if self.dying:
            return

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
        now = pygame.time.get_ticks()
        if self.dying:
            lean_t, alpha = self._death_progress()
            sprite = pygame.transform.rotate(sprite, -self.DEATH_LEAN_DEGREES * lean_t)
            sprite = sprite.copy()
            sprite.set_alpha(alpha)
        elif now < self.hurt_until:
            sprite = flash_tint(sprite)
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        rect = sprite.get_rect(midbottom=(sx, sy))
        surface.blit(sprite, rect)


class MiddleManager(Enemy):
    speed = 1.0
    strafe_speed = 0.8
    min_engage_range = 90
    max_hp = 3
    detection_range = 260
    fire_cooldown_ms = 1700
    flash_ms = 180
    clipboard_speed = 7.0
    clipboard_lifetime = 1300
    clipboard_damage = 8

    def __init__(self, wx, wy, animations, variant, clipboard_frames):
        super().__init__(wx, wy, animations, variant)
        self.clipboard_frames = clipboard_frames
        self.last_shot_time = 0
        self.flash_until = 0
        self.engaged = False
        self._strafe_dir = random.choice((-1, 1))

    def update(self, solid_rects, player=None, bullets_out=None):
        if self.dying:
            return

        in_range = False
        if player is not None:
            dist = math.hypot(player.wx - self.wx, player.wy - self.wy)
            in_range = dist <= self.detection_range

        self.engaged = in_range
        if in_range:
            self._engage(player, solid_rects)
            self._try_fire(player, bullets_out)
        else:
            super().update(solid_rects)

    def _engage(self, player, solid_rects):
        """Strafe side-to-side while facing the player so the walk animation keeps playing."""
        dx = player.wx - self.wx
        dy = player.wy - self.wy
        dist = math.hypot(dx, dy) or 1.0
        dir_x, dir_y = dx / dist, dy / dist
        self.facing_left = dx < 0

        if dist < self.min_engage_range:
            # back away
            self.vx = -dir_x * self.strafe_speed
            self.vy = -dir_y * self.strafe_speed
        else:
            # strafe perpendicular
            perp_x, perp_y = -dir_y, dir_x
            self.vx = perp_x * self.strafe_speed * self._strafe_dir
            self.vy = perp_y * self.strafe_speed * self._strafe_dir

        self.moving = True

        # simple collision response
        self.wx += self.vx
        self.rect.centerx = int(self.wx)
        if any(self.rect.colliderect(tile) for tile in solid_rects):
            self.wx -= self.vx
            self.rect.centerx = int(self.wx)
            self._strafe_dir *= -1

        self.wy += self.vy
        self.rect.centery = int(self.wy)
        if any(self.rect.colliderect(tile) for tile in solid_rects):
            self.wy -= self.vy
            self.rect.centery = int(self.wy)
            self._strafe_dir *= -1

        self._update_animation()

    def _try_fire(self, player, bullets_out):
        if bullets_out is None:
            return
        now = pygame.time.get_ticks()
        if now - self.last_shot_time < self.fire_cooldown_ms:
            return
        self.last_shot_time = now
        self.flash_until = now + self.flash_ms

        vx, vy = aim_at(self.wx, self.wy, player.wx, player.wy)
        bullets_out.append(Bullet(
            self.wx, self.wy, vx, vy,
            self.clipboard_frames,
            self.clipboard_speed,
            self.clipboard_lifetime,
            damage=self.clipboard_damage,
            frame_delay=180,
        ))

    def draw(self, surface, camera):
        frames = self._frames()
        sprite = frames[min(self.current_frame, len(frames) - 1)]
        now = pygame.time.get_ticks()
        if self.dying:
            lean_t, alpha = self._death_progress()
            sprite = pygame.transform.rotate(sprite, -self.DEATH_LEAN_DEGREES * lean_t)
            sprite = sprite.copy()
            sprite.set_alpha(alpha)
        elif now < self.hurt_until:
            sprite = flash_tint(sprite)
        elif now < self.flash_until:
            w, h = sprite.get_size()
            sprite = pygame.transform.smoothscale(sprite, (int(w * 1.15), int(h * 1.15)))
            bright = sprite.copy()
            bright.fill((40, 40, 40, 0), special_flags=pygame.BLEND_RGBA_ADD)
            sprite = bright
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        rect = sprite.get_rect(midbottom=(sx, sy))
        surface.blit(sprite, rect)


class ExecutiveSummoner(Enemy):
    max_hp = 5
    speed = 0
    detection_range = 320
    summon_cooldown_ms = 4000
    summon_windup_ms = 1000
    max_lifetime_summons = 4
    spawn_offset = 34

    def __init__(self, wx, wy, animations, variant="executive"):
        super().__init__(wx, wy, animations, variant)
        self.engaged = False
        self.last_summon_time = 0
        self.summon_started_at = None
        self.summons_left = self.max_lifetime_summons
        self.pending_summons = []

    def update(self, solid_rects, player=None, bullets_out=None):
        if self.dying:
            return

        self.moving = False
        self.vx = self.vy = 0.0

        if player is not None:
            dist = math.hypot(player.wx - self.wx, player.wy - self.wy)
            self.engaged = self.engaged or dist <= self.detection_range
            if self.engaged:
                self.facing_left = player.wx < self.wx

        self._update_animation()
        self._update_summon()

    def _update_summon(self):
        now = pygame.time.get_ticks()

        if self.summon_started_at is not None:
            if now - self.summon_started_at >= self.summon_windup_ms:
                offset = -self.spawn_offset if self.facing_left else self.spawn_offset
                self.pending_summons.append((self.wx + offset, self.wy))
                self.summon_started_at = None
                self.last_summon_time = now
            return

        if not self.engaged or self.summons_left <= 0:
            return
        if now - self.last_summon_time < self.summon_cooldown_ms:
            return

        self.summons_left -= 1
        self.summon_started_at = now

    def take_pending_summons(self):
        summons, self.pending_summons = self.pending_summons, []
        return summons

    def _windup_progress(self):
        if self.summon_started_at is None:
            return None
        elapsed = pygame.time.get_ticks() - self.summon_started_at
        return max(0.0, min(1.0, elapsed / self.summon_windup_ms))

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        now = pygame.time.get_ticks()

        progress = self._windup_progress()
        if progress is not None:
            about_to_spawn = progress > 0.85
            radius = int(10 + progress * 30)
            alpha = int(90 + progress * 130)
            if about_to_spawn:
                radius, alpha = int(radius * 1.25), 235
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (200, 60, 220, alpha), (radius, radius), radius)
            pygame.draw.circle(glow, (240, 190, 250, min(255, alpha + 20)), (radius, radius), radius, width=3)
            surface.blit(glow, glow.get_rect(center=(sx, sy - 6)))

        frames = self._frames()
        sprite = frames[min(self.current_frame, len(frames) - 1)]
        if self.dying:
            lean_t, alpha = self._death_progress()
            sprite = pygame.transform.rotate(sprite, -self.DEATH_LEAN_DEGREES * lean_t)
            sprite = sprite.copy()
            sprite.set_alpha(alpha)
        elif now < self.hurt_until:
            sprite = flash_tint(sprite)
        rect = sprite.get_rect(midbottom=(sx, sy))
        surface.blit(sprite, rect)
"""
Bullet / projectile system. Bullets live in world space (wx, wy), move in a
straight line along their velocity vector, and depth-sort with the rest of the
scene because they expose the same wx/wy + draw(surface, camera) interface the
Floor.draw_scene() depth pass expects.
"""

import pygame

# Per-weapon tuning. fire_rate is the minimum ms between shots, bullet_speed is
# world px moved per frame (the game runs at a fixed 60fps), bullet_lifetime is
# the ms a bullet stays alive, max_bullets caps how many of this weapon's
# bullets can be active at once.
WEAPON_STATS = {
    "pistol": {"fire_rate": 300, "bullet_speed": 9.0, "bullet_lifetime": 900, "max_bullets": 6},
    "rifle":  {"fire_rate": 130, "bullet_speed": 12.0, "bullet_lifetime": 650, "max_bullets": 15},
}

# World-space unit direction vectors per facing, matching the isometric
# movement mapping in Player.handle_input (up = (-1,-1), down = (+1,+1),
# left = (-1,+1), right = (+1,-1), and the diagonals are just those summed
# and normalised).
FIRE_DIRECTIONS = {
    ("front", False):      (0.7071, 0.7071),
    ("back", False):       (-0.7071, -0.7071),
    ("side", False):       (0.7071, -0.7071),
    ("side", True):        (-0.7071, 0.7071),
    ("backside", False):   (0.0, -1.0),
    ("backside", True):    (-1.0, 0.0),
    ("frontside", False):  (1.0, 0.0),
    ("frontside", True):   (0.0, 1.0),
}

OFFSCREEN_MARGIN = 64


class Bullet:
    frame_delay = 45  # ms between projectile frames

    def __init__(self, wx, wy, vx, vy, frames, speed, lifetime, damage=10):
        self.wx = float(wx)
        self.wy = float(wy)
        self.vx = float(vx)
        self.vy = float(vy)
        self.speed = float(speed)
        self.damage = damage
        self.frames = frames
        self.current_frame = 0
        self.last_frame_time = pygame.time.get_ticks()
        self.expire_at = self.last_frame_time + lifetime
        self.dead = False

    def _advance_frame(self):
        now = pygame.time.get_ticks()
        if now - self.last_frame_time > self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_frame_time = now

    def update(self, camera):
        if self.dead:
            return False

        self.wx += self.vx * self.speed
        self.wy += self.vy * self.speed
        self._advance_frame()

        if pygame.time.get_ticks() >= self.expire_at:
            self.dead = True
            return False

        sx, sy = camera.world_to_screen(self.wx, self.wy)
        if (sx < -OFFSCREEN_MARGIN or sx > camera.sw + OFFSCREEN_MARGIN
                or sy < -OFFSCREEN_MARGIN or sy > camera.sh + OFFSCREEN_MARGIN):
            self.dead = True
            return False

        return True

    def check_hit(self, entity, radius=16):
        """Collision stub: rough distance check against an entity's centre.
        Swap for rect / mask collision once real combat is wired up."""
        ex, ey = entity.rect.center
        return (self.wx - ex) ** 2 + (self.wy - ey) ** 2 < radius * radius

    def draw(self, surface, camera):
        frames = self.frames
        sprite = frames[min(self.current_frame, len(frames) - 1)]
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        surface.blit(sprite, sprite.get_rect(center=(sx, sy)))

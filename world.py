import random
import copy
import pygame

tile_size = 64

tile_w = 128
tile_h = 64
wall_height = 48

empty = 0
floor = 1
wall = 2
elevator = 3

template_rect_arena = [
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
]

template_pillars = [
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 2],
    [2, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 2],
    [2, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 2],
    [2, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
]
 
template_l_shape = [
    [0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2],
    [0, 0, 0, 0, 0, 0, 2, 1, 1, 1, 1, 2],
    [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

room_template = [template_rect_arena, template_pillars, template_l_shape]

floor_colour = (70, 70, 90)
floor_line_colour = (50, 50, 65)
wall_top_colour = (110, 110, 130)
wall_left_colour  = (75, 75, 92)
wall_right_colour = (60, 60, 75)
elevator_locked_colour = (150, 60, 60)
elevator_open_colour = (210, 180, 60)
elevator_door_frame_colour = (35, 35, 42)
elevator_indicator_locked = (220, 70, 70)
elevator_indicator_open = (90, 220, 90)

def draw_iso_floor_tile(surface, cx, cy, colour):
    points = [
        (cx, cy - tile_h // 2),
        (cx + tile_w // 2, cy),
        (cx, cy + tile_h // 2),
        (cx - tile_w // 2, cy),
    ]
    pygame.draw.polygon(surface, colour, points)
    pygame.draw.polygon(surface, floor_line_colour, points, 1)

def draw_iso_wall_tile(surface, cx, cy, height=wall_height):
    top = [
        (cx, cy - tile_h // 2 - height),
        (cx + tile_w // 2, cy - height),
        (cx, cy + tile_h // 2 - height),
        (cx - tile_w // 2, cy - height),
    ]
    left_face = [
        (cx - tile_w // 2, cy - height), (cx, cy + tile_h // 2 - height),
        (cx, cy + tile_h // 2), (cx - tile_w // 2, cy),
    ]
    right_face = [
        (cx, cy + tile_h // 2 - height), (cx + tile_w // 2, cy - height),
        (cx + tile_w // 2, cy), (cx, cy + tile_h // 2),
    ]
    pygame.draw.polygon(surface, wall_left_colour, left_face)
    pygame.draw.polygon(surface, wall_right_colour, right_face)
    pygame.draw.polygon(surface, wall_top_colour, top)
    pygame.draw.polygon(surface, (20, 20, 25), top, 1)

def _shade_colour(colour, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in colour)

def draw_elevator_door(surface, cx, cy, side, locked):
    # draw an elevator door on one vertical face of a wall tile centred at
    # (cx, cy). `side` is the compass direction of the elevator relative to
    # the wall, so the door is drawn on the face that faces the elevator.
    h = wall_height
    half = tile_h // 2
    tw = tile_w // 2

    if side == "east":
        p0t, p1t = (cx + tw, cy - h), (cx, cy + half - h)
        p0b, p1b = (cx + tw, cy), (cx, cy + half)
    elif side == "north":
        p0t, p1t = (cx, cy - half - h), (cx + tw, cy - h)
        p0b, p1b = (cx, cy - half), (cx + tw, cy)
    elif side == "south":
        p0t, p1t = (cx, cy + half - h), (cx - tw, cy - h)
        p0b, p1b = (cx, cy + half), (cx - tw, cy)
    else:  # west
        p0t, p1t = (cx, cy - half - h), (cx - tw, cy - h)
        p0b, p1b = (cx, cy - half), (cx - tw, cy)

    def top(u):
        return (p0t[0] + (p1t[0] - p0t[0]) * u, p0t[1] + (p1t[1] - p0t[1]) * u)

    def bottom(u):
        return (p0b[0] + (p1b[0] - p0b[0]) * u, p0b[1] + (p1b[1] - p0b[1]) * u)

    u0, u1 = 0.28, 0.72
    mid = (u0 + u1) / 2
    inset = 3

    recess = [top(u0), top(u1), bottom(u1), bottom(u0)]
    pygame.draw.polygon(surface, elevator_door_frame_colour, recess)

    def shift(point, dy):
        return (point[0], point[1] + dy)

    panel_a = [shift(top(u0), inset), shift(top(mid), inset),
               shift(bottom(mid), -inset), shift(bottom(u0), -inset)]
    panel_b = [shift(top(mid), inset), shift(top(u1), inset),
               shift(bottom(u1), -inset), shift(bottom(mid), -inset)]

    colour = elevator_locked_colour if locked else elevator_open_colour
    pygame.draw.polygon(surface, _shade_colour(colour, 0.85), panel_a)
    pygame.draw.polygon(surface, colour, panel_b)
    pygame.draw.polygon(surface, elevator_door_frame_colour, recess, 2)

    seam_a = shift(top(mid), inset)
    seam_b = shift(bottom(mid), -inset)
    pygame.draw.line(surface, elevator_door_frame_colour, seam_a, seam_b, 1)

    light = shift(top(mid), inset + 5)
    light_colour = elevator_indicator_locked if locked else elevator_indicator_open
    pygame.draw.circle(surface, light_colour,
                       (int(light[0]), int(light[1])), 3)

class Floor:
    def __init__(self):
        self.grid = []
        self.cols = 0
        self.rows = 0
        self.elevator_locked = True
        self.build()

    def build(self):
        self.grid = copy.deepcopy(random.choice(room_template))
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.elevator_locked = True

    def find_spawn_point(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == floor:
                    return (col + 0.5) * tile_size, (row + 0.5) * tile_size
        return tile_size * 2, tile_size * 2 # fallback

    def tile_at(self, wx, wy):
        col = int(wx // tile_size)
        row = int(wy // tile_size)
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return row, col
        return None

    def get_solid_rects(self):
        rects = []
        for row in range(self.rows):
            for col in range(self.cols):
                tile = self.grid[row][col]
                if tile == wall or tile == empty:
                    rects.append(pygame.Rect(col * tile_size, row * tile_size,
                                              tile_size, tile_size))
        return rects

    def check_elevator(self, player_rect):
        if self.elevator_locked:
            return False
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == elevator:
                    tile_rect = pygame.Rect(col * tile_size, row * tile_size,
                                             tile_size, tile_size)
                    if player_rect.colliderect(tile_rect):
                        return True
        return False

    def try_unlock_elevator(self, player_rect):
        # unlock the elevator when the player stands on or next to it. the
        # elevator pad is always walkable; the closed door beside it is what
        # blocks the player until they press the button.
        if not self.elevator_locked:
            return False
        px, py = player_rect.center
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != elevator:
                    continue
                tx = col * tile_size + tile_size // 2
                ty = row * tile_size + tile_size // 2
                if abs(px - tx) <= tile_size and abs(py - ty) <= tile_size:
                    self.elevator_locked = False
                    return True
        return False

    def draw(self, surface, camera, player_depth=None):
        # player_depth = the row+col of the tile the player is standing on.
        # Everything the player renders on top of is drawn first: all
        # floor/elevator tiles (the player always stands on the ground, so
        # ground never covers them) plus walls at or behind the player's
        # depth. The caller draws the player here. Then walls closer to the
        # camera (south-east) are drawn so they occlude the player.
        for row, col in self._tiles_in_order():
            if player_depth is not None and row + col > player_depth and self.grid[row][col] == wall:
                continue
            self._draw_tile(surface, camera, row, col)

        # caller draws the player here

        if player_depth is not None:
            for row, col in self._tiles_in_order():
                if row + col <= player_depth:
                    continue
                if self.grid[row][col] == wall:
                    self._draw_tile(surface, camera, row, col)

    def draw_behind_player(self, surface, camera, wx, wy, cx, cy):
        # everything the player renders on top of: all floor/elevator tiles
        # (the player always stands on the ground, so ground never covers
        # them) plus walls at or behind the player's depth. drawn before the
        # player so their feet sit on their own tile and far walls render
        # underneath them.
        #
        # (wx, wy) is the sprite's visual feet point, a fraction of a tile
        # south-east of the player's centre (cx, cy). Normally both land in the
        # same tile, but when the player presses against a wall the feet point
        # can cross into the wall tile; anchoring the depth there would make
        # that wall render *behind* the player. Fall back to the tile under the
        # player's centre so walls in front still occlude them. Ground tiles
        # (floor/elevator) keep the feet tile so the player draws on top of
        # them.
        player_depth = self._anchor_depth(wx, wy, cx, cy)
        for row, col in self._tiles_in_order():
            if player_depth is not None and row + col > player_depth and self.grid[row][col] == wall:
                continue
            self._draw_tile(surface, camera, row, col)
        return player_depth

    def _anchor_depth(self, feet_wx, feet_wy, center_wx, center_wy):
        tile = self.tile_at(feet_wx, feet_wy)
        if tile is not None and self.grid[tile[0]][tile[1]] in (wall, empty):
            tile = self.tile_at(center_wx, center_wy)
        return tile[0] + tile[1] if tile else None

    def draw_in_front_of_player(self, surface, camera, player_depth):
        # walls closer to the camera than the player (south-east) are drawn
        # after the player so they occlude them. nothing else is drawn in
        # front, so ground tiles (floor/elevator) never cover the player.
        # when player_depth is None (player is off the map) draw nothing so the
        # player stays visible.
        if player_depth is None:
            return
        for row, col in self._tiles_in_order():
            if row + col <= player_depth:
                continue
            if self.grid[row][col] == wall:
                self._draw_tile(surface, camera, row, col)

    def _tiles_in_order(self):
        return sorted(
            ((row, col) for row in range(self.rows) for col in range(self.cols)),
            key=lambda rc: rc[0] + rc[1]
        )

    def _draw_tile(self, surface, camera, row, col):
        tile = self.grid[row][col]
        if tile == empty:
            return
        wx = (col + 0.5) * tile_size
        wy = (row + 0.5) * tile_size
        cx, cy = camera.world_to_screen(wx, wy)
        if tile == floor:
            draw_iso_floor_tile(surface, cx, cy, floor_colour)
        elif tile == elevator:
            draw_iso_floor_tile(surface, cx, cy, floor_colour)
            self._draw_elevator_pad(surface, cx, cy)
            if not self._has_adjacent_wall(row, col):
                self._draw_free_standing_door(surface, cx, cy)
        elif tile == wall:
            draw_iso_floor_tile(surface, cx, cy, floor_colour)
            draw_iso_wall_tile(surface, cx, cy)
            self._draw_wall_elevator_doors(surface, camera, row, col)

    def _draw_elevator_pad(self, surface, cx, cy):
        colour = elevator_locked_colour if self.elevator_locked else elevator_open_colour
        scale = 0.55
        half_w = tile_w // 2 * scale
        half_h = tile_h // 2 * scale
        points = [
            (cx, cy - half_h),
            (cx + half_w, cy),
            (cx, cy + half_h),
            (cx - half_w, cy),
        ]
        pygame.draw.polygon(surface, (55, 55, 72), points)
        pygame.draw.polygon(surface, colour, points, 2)

    def _draw_wall_elevator_doors(self, surface, camera, row, col):
        for drow, dcol, side in (
            (row, col - 1, "west"),
            (row, col + 1, "east"),
            (row - 1, col, "north"),
            (row + 1, col, "south"),
        ):
            if 0 <= drow < self.rows and 0 <= dcol < self.cols and self.grid[drow][dcol] == elevator:
                wx = (col + 0.5) * tile_size
                wy = (row + 0.5) * tile_size
                cx, cy = camera.world_to_screen(wx, wy)
                draw_elevator_door(surface, cx, cy, side, self.elevator_locked)

    def _has_adjacent_wall(self, row, col):
        for drow, dcol in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= drow < self.rows and 0 <= dcol < self.cols and self.grid[drow][dcol] == wall:
                return True
        return False

    def _draw_free_standing_door(self, surface, cx, cy):
        draw_elevator_door(surface, cx, cy, "north", self.elevator_locked)

if __name__ == "__main__":
    from camera import Camera
 
    pygame.init()
    sw, sh = 800, 600
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Gone Rogue - Map Generation Test")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 26)

    floor = Floor()
    player_wx, player_wy = floor.find_spawn_point()
    player_rect = pygame.Rect(0, 0, 30, 30)
    player_rect.center = (int(player_wx), int(player_wy))
    camera = Camera(sw, sh, tile_size, tile_w, tile_h)
    floor_number = 1
    speed = 4

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_u:
                    floor.elevator_locked = not floor.elevator_locked

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += speed
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        solid_rects = floor.get_solid_rects()
        player_rect.x += int(dx)
        for tile in solid_rects:
            if player_rect.colliderect(tile):
                if dx > 0: player_rect.right = tile.left
                elif dx < 0: player_rect.left = tile.right
        player_rect.y += int(dy)
        for tile in solid_rects:
            if player_rect.colliderect(tile):
                if dy > 0: player_rect.bottom = tile.top
                elif dy < 0: player_rect.top = tile.bottom
        player_wx, player_wy = player_rect.centerx, player_rect.centery
 
        if floor.check_elevator(player_rect):
            floor_number += 1
            floor.build()
            player_wx, player_wy = floor.find_spawn_point()
            player_rect.center = (int(player_wx), int(player_wy))

        camera.update(player_wx, player_wy)
 
        screen.fill((15, 15, 20))
        floor.draw(screen, camera)
 
        psx, psy = camera.world_to_screen(player_wx, player_wy)
        pygame.draw.circle(screen, (0, 220, 220), (psx, psy - 10), 12)
        pygame.draw.circle(screen, (255, 255, 255), (psx, psy - 10), 12, 2)
 
        lock_state = "LOCKED" if floor.elevator_locked else "OPEN"
        label = font.render(
            f"Floor {floor_number}  |  Elevator: {lock_state}  |  "
            f"WASD move, U toggles elevator (debug), Esc quit",
            True, (255, 255, 255))
        screen.blit(label, (10, 10))
 
        pygame.display.flip()

    pygame.quit()
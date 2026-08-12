from pathlib import Path
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

elevator_locked_colour = (150, 60, 60)
elevator_open_colour = (210, 180, 60)
elevator_indicator_locked = (220, 70, 70)
elevator_indicator_open = (90, 220, 90)

TILE_ASSET_DIR = Path(__file__).resolve().parent / "assets" / "images" / "tiles"

FLOOR_TILE_INDICES = [31, 32, 33]
WALL_FACE_INDEX = 21

ELEVATOR_ANIM_DURATION = 500
ELEVATOR_DOOR_STAGE_INDICES = [
    (13, 14),   # closed / idle
    (15, 16),   # opening, stage 1
    (17, 18),   # opening, stage 2
    (19, 20),   # fully open
]

PROP_CRATE, PROP_TABLE, PROP_DRAWERS = 2, 7, 8
PROP_CHAIR_BOTTOM, PROP_CHAIR_TOP = 9, 10
PROP_CABINET_BOTTOM, PROP_CABINET_TOP = 12, 11

DESK_MUG = {"blue": 39, "yellow": 40, "red": 41, "green": 42}
DESK_PAPER = {"note1": 44, "note2": 45, "note3": 46, "blank": 47}
DESK_CHEESE = 43
DESK_PLANT = {"sunflower": 35, "small": 36, "tulip": 37, "leafy": 38}
DESK_KEYBOARD = 48

WALL_DECOR_RIGHT = {"portrait_a": 23, "portrait_b": 25, "sign": 27, "poster": 29}
WALL_DECOR_LEFT = {"portrait_a": 24, "portrait_b": 26, "sign": 28, "poster": 30}

_tile_cache = {}

def _load_tile(index):
    path = TILE_ASSET_DIR / f"sprite_{index:02d}.png"
    return pygame.image.load(str(path)).convert_alpha()

def compose_layers(*indices):
    """Stack tile layers drawn in the same 32x32 coordinate space directly on
    top of each other, no offset -- this is the chair/cabinet/desk-decor
    technique: each layer is the same drawing with some parts erased to
    transparent, so overlaying at (0,0) reassembles the original."""
    combo = pygame.Surface((32, 32), pygame.SRCALPHA)
    for idx in indices:
        combo.blit(_load_tile(idx), (0, 0))
    return combo

def _scale_prop(raw_surface):
    scale = tile_w / 32
    size = (int(32 * scale), int(32 * scale))
    return pygame.transform.scale(raw_surface, size)

def _face_crop(index, left_half):
    region = pygame.Rect(0, 8, 16, 24) if left_half else pygame.Rect(16, 8, 16, 24)
    return _load_tile(index).subsurface(region)

def init_tile_images():
    """Load and pre-scale every tile image. MUST be called once, AFTER
    pygame.display.set_mode() -- convert_alpha() needs a display to exist."""
    if _tile_cache:
        return

    floor_surfaces = []
    for idx in FLOOR_TILE_INDICES:
        cropped = _load_tile(idx).subsurface(pygame.Rect(0, 0, 32, 16))
        floor_surfaces.append(pygame.transform.scale(cropped, (tile_w, tile_h)))
    _tile_cache["floor"] = floor_surfaces

    size = (tile_w // 2, wall_height + tile_h // 2)
    left_img = pygame.transform.scale(_face_crop(WALL_FACE_INDEX, True), size)
    _tile_cache["wall_left"] = left_img
    _tile_cache["wall_right"] = pygame.transform.flip(left_img, True, False)

    def door_stage(bottom_idx, top_idx):
        b = _load_tile(bottom_idx).subsurface(pygame.Rect(0, 8, 16, 24))
        t = _load_tile(top_idx).subsurface(pygame.Rect(0, 8, 16, 24))
        combined = pygame.Surface((16, 32), pygame.SRCALPHA)
        combined.blit(t, (0, 0))
        combined.blit(b, (0, 8))
        return pygame.transform.scale(combined, size)

    _tile_cache["door_stages"] = [door_stage(b, t) for b, t in ELEVATOR_DOOR_STAGE_INDICES]

    wall_decor = {}
    for name, idx in WALL_DECOR_RIGHT.items():
        wall_decor[("right", name)] = pygame.transform.scale(_face_crop(idx, True), size)
    for name, idx in WALL_DECOR_LEFT.items():
        wall_decor[("left", name)] = pygame.transform.scale(_face_crop(idx, False), size)
    _tile_cache["wall_decor"] = wall_decor

    props = {
        "crate": _scale_prop(_load_tile(PROP_CRATE)),
        "table": _scale_prop(_load_tile(PROP_TABLE)),
        "drawers": _scale_prop(_load_tile(PROP_DRAWERS)),
        "chair": _scale_prop(compose_layers(PROP_CHAIR_BOTTOM, PROP_CHAIR_TOP)),
        "cabinet": _scale_prop(compose_layers(PROP_CABINET_BOTTOM, PROP_CABINET_TOP)),
    }
    for mug_name, idx in DESK_MUG.items():
        props[f"table_mug_{mug_name}"] = _scale_prop(compose_layers(PROP_TABLE, idx))
    for paper_name, idx in DESK_PAPER.items():
        props[f"table_paper_{paper_name}"] = _scale_prop(compose_layers(PROP_TABLE, idx))
    props["table_cheese"] = _scale_prop(compose_layers(PROP_TABLE, DESK_CHEESE))
    _tile_cache["props"] = props


def draw_iso_floor_tile(surface, cx, cy, variant):
    img = _tile_cache["floor"][variant]
    surface.blit(img, img.get_rect(center=(cx, cy)))

def draw_iso_wall_tile(surface, cx, cy, height=wall_height):
    top = [
        (cx, cy - tile_h // 2 - height), (cx + tile_w // 2, cy - height),
        (cx, cy + tile_h // 2 - height), (cx - tile_w // 2, cy - height),
    ]
    pygame.draw.polygon(surface, (110, 110, 130), top)
    pygame.draw.polygon(surface, (20, 20, 25), top, 1)
    surface.blit(_tile_cache["wall_left"], (cx - tile_w // 2, cy - height))
    surface.blit(_tile_cache["wall_right"], (cx, cy - height))

def draw_elevator_door(surface, cx, cy, side, stage, locked):
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

    xs = [p0t[0], p1t[0], p0b[0], p1b[0]]
    ys = [p0t[1], p1t[1], p0b[1], p1b[1]]
    x0, y0 = min(xs), min(ys)
    w = max(1, int(max(xs) - x0))
    hgt = max(1, int(max(ys) - y0))

    img = _tile_cache["door_stages"][stage]
    surface.blit(pygame.transform.scale(img, (w, hgt)), (int(x0), int(y0)))

    light_x = p0t[0] + (p1t[0] - p0t[0]) * 0.5
    light_y = p0t[1] + (p1t[1] - p0t[1]) * 0.5 + 10
    light_colour = elevator_indicator_locked if locked else elevator_indicator_open
    pygame.draw.circle(surface, light_colour, (int(light_x), int(light_y)), 3)


class Floor:
    def __init__(self):
        self.grid = []
        self.cols = 0
        self.rows = 0
        self.elevator_locked = True
        self.elevator_open_start = None
        self.build()

    def build(self):
        self.grid = copy.deepcopy(random.choice(room_template))
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.elevator_locked = True
        self.elevator_open_start = None
        self.floor_variant = [[random.randrange(len(FLOOR_TILE_INDICES))
                                for _ in range(self.cols)] for _ in range(self.rows)]
        self.props = []
        self.wall_decor = []

    def find_spawn_point(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == floor:
                    return (col + 0.5) * tile_size, (row + 0.5) * tile_size
        return tile_size * 2, tile_size * 2

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
                    self.elevator_open_start = pygame.time.get_ticks()
                    return True
        return False

    def _elevator_anim_progress(self):
        if self.elevator_locked or self.elevator_open_start is None:
            return 0.0
        elapsed = pygame.time.get_ticks() - self.elevator_open_start
        return min(1.0, elapsed / ELEVATOR_ANIM_DURATION)

    def _elevator_stage(self):
        if self.elevator_locked:
            return 0
        return min(3, int(self._elevator_anim_progress() * 4))

    def draw(self, surface, camera, player_depth=None):
        for row, col in self._tiles_in_order():
            if player_depth is not None and row + col > player_depth and self.grid[row][col] == wall:
                continue
            self._draw_tile(surface, camera, row, col)

        if player_depth is not None:
            for row, col in self._tiles_in_order():
                if row + col <= player_depth:
                    continue
                if self.grid[row][col] == wall:
                    self._draw_tile(surface, camera, row, col)

    def draw_behind_player(self, surface, camera, wx, wy, cx, cy):
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
        variant = self.floor_variant[row][col]
        if tile == floor:
            draw_iso_floor_tile(surface, cx, cy, variant)
        elif tile == elevator:
            draw_iso_floor_tile(surface, cx, cy, variant)
            self._draw_elevator_pad(surface, cx, cy)
            if not self._has_adjacent_wall(row, col):
                self._draw_free_standing_door(surface, cx, cy)
        elif tile == wall:
            draw_iso_floor_tile(surface, cx, cy, variant)
            draw_iso_wall_tile(surface, cx, cy)
            self._draw_wall_elevator_doors(surface, camera, row, col)
            self._draw_wall_decor(surface, cx, cy, row, col)

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
                draw_elevator_door(surface, cx, cy, side, self._elevator_stage(), self.elevator_locked)

    def _has_adjacent_wall(self, row, col):
        for drow, dcol in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= drow < self.rows and 0 <= dcol < self.cols and self.grid[drow][dcol] == wall:
                return True
        return False

    def _draw_free_standing_door(self, surface, cx, cy):
        draw_elevator_door(surface, cx, cy, "north", self._elevator_stage(), self.elevator_locked)

    def add_prop(self, row, col, name):
        if 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == floor:
            self.props.append((row, col, name))

    def draw_props(self, surface, camera):
        for row, col, name in self.props:
            wx, wy = (col + 0.5) * tile_size, (row + 0.5) * tile_size
            cx, cy = camera.world_to_screen(wx, wy)
            img = _tile_cache["props"][name]
            surface.blit(img, img.get_rect(midbottom=(cx, cy + tile_h // 2)))

    def add_wall_decor(self, row, col, side, name):
        if 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == wall:
            self.wall_decor.append((row, col, side, name))

    def _draw_wall_decor(self, surface, cx, cy, row, col):
        for drow, dcol, side, name in self.wall_decor:
            if (drow, dcol) != (row, col):
                continue
            img = _tile_cache["wall_decor"][(side, name)]
            if side == "left":
                surface.blit(img, (cx - tile_w // 2, cy - wall_height))
            else:
                surface.blit(img, (cx, cy - wall_height))
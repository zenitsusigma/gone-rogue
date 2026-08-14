from pathlib import Path
import random
import copy
import json
import pygame

tile_size = 64

tile_w = 128
tile_h = 64
wall_height = 48

# how many px in the 128px-wide SCALED art corresponds to one native (32px
# source canvas) pixel -- every OFFSETS value below is expressed in NATIVE
# pixels (matching how you described them), and gets multiplied by this
# wherever it's actually used against screen coordinates.
TILE_SCALE = tile_w / 32  # = 4

empty = 0
floor = 1
wall = 2
elevator = 3

template_rect_arena = [
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

# interior pillars are now plain floor tiles with a crate PROP standing on
# them instead of "wall" grid tiles -- a floating wall block read as a weird
# stray box in the middle of the room, a crate reads as an actual object.
# The crates are added in Floor.build() at PILLAR_POSITIONS for this template.
template_pillars = [
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
PILLAR_POSITIONS = [(2, 3), (2, 8), (3, 3), (3, 8), (5, 3), (5, 8), (6, 3), (6, 8)]

template_l_shape = [
    [0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0],
    [0, 0, 0, 0, 0, 0, 2, 1, 1, 1, 3, 0],
    [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

room_template = [
    (template_rect_arena, []),
    (template_pillars, PILLAR_POSITIONS),
    (template_l_shape, []),
]

elevator_locked_colour = (150, 60, 60)
elevator_open_colour = (210, 180, 60)
elevator_indicator_locked = (220, 70, 70)
elevator_indicator_open = (90, 220, 90)

TILE_ASSET_DIR = Path(__file__).resolve().parent / "assets" / "images" / "tiles"
OFFSETS_FILE = Path(__file__).resolve().parent / "offsets.json"

# Sprite 33 is an opaque black diamond. Against the game's black background it
# reads as a hole rather than a floor tile, so reserve it for a future special
# surface with a contrasting outline instead of mixing it into normal rooms.
FLOOR_TILE_INDICES = [31, 32]
WALL_FACE_INDEX = 21
BORDER_WALL_HEIGHT = wall_height * 2

ELEVATOR_ANIM_DURATION = 500
ELEVATOR_DOOR_STAGE_INDICES = [
    (14, 13),   # closed / idle
    (16, 15),   # opening, stage 1
    (18, 17),   # opening, stage 2
    (20, 19),   # fully open
]

PROP_CRATE, PROP_TABLE, PROP_DRAWERS = 2, 7, 8
PROP_CHAIR_BOTTOM, PROP_CHAIR_TOP = 9, 10
PROP_CABINET_BOTTOM, PROP_CABINET_TOP = 12, 11

DESK_MUG = {"blue": 39, "yellow": 40, "red": 41, "green": 42}
DESK_PAPER = {"note1": 44, "note2": 45, "note3": 46, "blank": 47}
DESK_CHEESE = 43
DESK_PLANT = {"sunflower": 35, "small": 36, "tulip": 37, "leafy": 38}
DESK_PLANT_SCALE = 0.65
DESK_KEYBOARD = 48

WALL_DECOR_RIGHT = {"portrait_a": 23, "portrait_b": 25, "sign": 27, "poster": 29}
WALL_DECOR_LEFT = {"portrait_a": 24, "portrait_b": 26, "sign": 28, "poster": 30}

# props that block movement, matched against floor.props' `name` field by
# prefix (so "table_mug_blue" etc all count as "table")
SOLID_PROP_PREFIXES = ("crate", "table", "drawers", "chair", "cabinet")

# ---------------------------------------------------------------------------
# OFFSETS -- every tunable pixel value lives here, in NATIVE (32x32 source
# canvas) pixel units. Nothing else in this file should have a bare magic
# number for placement; add a key here instead so it shows up in the live
# tuning overlay (F1 in-game) and survives to offsets.json.
# ---------------------------------------------------------------------------
DEFAULT_OFFSETS = {
    "wall_place_dx": 0,
    "wall_place_dy": 0,
    "door_top_lift": 7,   # native px – tune live with F1
}

OFFSETS = dict(DEFAULT_OFFSETS)


def load_offsets():
    global OFFSETS
    if OFFSETS_FILE.exists():
        try:
            saved = json.loads(OFFSETS_FILE.read_text())
            OFFSETS.update({k: v for k, v in saved.items() if k in DEFAULT_OFFSETS})
        except (json.JSONDecodeError, OSError):
            pass


def save_offsets():
    OFFSETS_FILE.write_text(json.dumps(OFFSETS, indent=2))


_tile_cache = {}


def _load_tile(index):
    path = TILE_ASSET_DIR / f"sprite_{index:02d}.png"
    return pygame.image.load(str(path)).convert_alpha()


def _face_crop(index, left_half):
    """Crop out just the single visible face from a 32x32 source tile.
    Verified identical bbox (x=[0,15], y=[8,30]) across wall/elevator/panel
    art, so this one crop rect is shared by all of them."""
    region = pygame.Rect(0, 8, 16, 24) if left_half else pygame.Rect(16, 8, 16, 24)
    return _load_tile(index).subsurface(region)


def _scale_prop(raw_surface):
    scale = tile_w / 32
    size = (max(1, int(raw_surface.get_width() * scale)), max(1, int(raw_surface.get_height() * scale)))
    return pygame.transform.scale(raw_surface, size)


def compose_layers(*indices):
    """Stack tile layers drawn in the same 32x32 coordinate space directly on
    top of each other with no offset -- verified by direct pixel comparison
    for chair (9+10), cabinet (12+11), and every desk-decor item: each layer
    was drawn pre-aligned to the same canvas position, so overlaying at
    (0,0) reassembles the original with no gap and no offset needed."""
    combo = pygame.Surface((32, 32), pygame.SRCALPHA)
    for idx in indices:
        combo.blit(_load_tile(idx), (0, 0))
    return combo


def compose_layer_scaled(base_idx, decor_idx, decor_scale):
    """Like compose_layers, but shrinks one decor layer first, anchored on
    its own bottom-centre so it stays "planted" in roughly the same spot
    instead of shrinking toward the canvas centre. Used for the plant art,
    which was drawn at a noticeably larger scale than the rest of the desk
    decor."""
    base = _load_tile(base_idx)
    decor = _load_tile(decor_idx)
    bbox = decor.get_bounding_rect()
    anchor_x, anchor_y = bbox.centerx, bbox.bottom
    new_w = max(1, int(decor.get_width() * decor_scale))
    new_h = max(1, int(decor.get_height() * decor_scale))
    decor_small = pygame.transform.scale(decor, (new_w, new_h))
    paste_x = int(anchor_x - anchor_x * decor_scale)
    paste_y = int(anchor_y - anchor_y * decor_scale)
    combo = pygame.Surface((32, 32), pygame.SRCALPHA)
    combo.blit(base, (0, 0))
    combo.blit(decor_small, (paste_x, paste_y))
    return combo


def init_tile_images():
    """Load and pre-scale every tile image. MUST be called once, AFTER
    pygame.display.set_mode() -- convert_alpha() needs a display to exist."""
    load_offsets()
    if _tile_cache:
        return

    # The floor sprites are solid-colour diamonds on 32px canvases. Sampling
    # their actual colours then drawing full-size diamonds avoids the uneven
    # transparent edge left by scaling the tiny source shape.
    floor_colours = [_load_tile(idx).get_at((16, 8)) for idx in FLOOR_TILE_INDICES]
    average = tuple(sum(colour[channel] for colour in floor_colours) // len(floor_colours)
                    for channel in range(3))
    seam_colour = tuple(component * 82 // 100 for component in average)
    floor_surfaces = []
    for colour in floor_colours:
        diamond = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
        points = [
            (tile_w // 2, 0),
            (tile_w - 1, tile_h // 2),
            (tile_w // 2, tile_h - 1),
            (0, tile_h // 2),
        ]
        pygame.draw.polygon(diamond, colour, points)
        pygame.draw.lines(diamond, seam_colour, True, points, 1)
        floor_surfaces.append(diamond)
    _tile_cache["floor"] = floor_surfaces

    size = (tile_w // 2, wall_height + tile_h // 2)
    left_img = pygame.transform.scale(_face_crop(WALL_FACE_INDEX, True), size)
    _tile_cache["wall_left"] = left_img
    _tile_cache["wall_right"] = pygame.transform.flip(left_img, True, False)
    _tile_cache["wall_colour"] = _load_tile(WALL_FACE_INDEX).get_at((0, 8))
    _tile_cache["wall_shadow_colour"] = tuple(
        component * 72 // 100 for component in _tile_cache["wall_colour"][:3]
    )
    _tile_cache["wall_cap_colour"] = tuple(
        component * 88 // 100 for component in _tile_cache["wall_colour"][:3]
    )
    _tile_cache["wall_corner_colour"] = tuple(
        component * 55 // 100 for component in _tile_cache["wall_colour"][:3]
    )

    # elevator doors -- each stage is a (bottom_face, top_face) PAIR of
    # single-face crops, stacked at draw time with the same technique as
    # the wall (NOT pre-spliced into one small composite -- that was the
    # bug). Store the scaled left-half face per stage; the east/west/etc
    # mirroring for each compass side happens in draw_elevator_door.
    door_stage_faces = []
    for bottom_idx, top_idx in ELEVATOR_DOOR_STAGE_INDICES:
        bottom_face = pygame.transform.scale(_face_crop(bottom_idx, True), size)
        top_face = pygame.transform.scale(_face_crop(top_idx, True), size)
        door_stage_faces.append((bottom_face, top_face))
    _tile_cache["door_stage_faces"] = door_stage_faces
    _tile_cache["door_closed_colour"] = _load_tile(13).get_at((0, 8))
    _tile_cache["door_open_colour"] = _load_tile(19).get_at((0, 8))

    wall_decor = {}
    for name, idx in WALL_DECOR_RIGHT.items():
        wall_decor[("right", name)] = pygame.transform.scale(_face_crop(idx, False), size)
    for name, idx in WALL_DECOR_LEFT.items():
        wall_decor[("left", name)] = pygame.transform.scale(_face_crop(idx, True), size)
    _tile_cache["wall_decor"] = wall_decor

    props = {
        "crate": _scale_prop(_load_tile(PROP_CRATE)),
        "table": _scale_prop(_load_tile(PROP_TABLE)),
        "drawers": _scale_prop(_load_tile(PROP_DRAWERS)),
        # verified by direct pixel-diff against the source art: these two
        # pieces are drawn in the SAME 32x32 coordinate space with no built-in
        # separation -- compose_layers (zero offset) is correct, not a guess.
        "chair": _scale_prop(compose_layers(PROP_CHAIR_BOTTOM, PROP_CHAIR_TOP)),
        "cabinet": _scale_prop(compose_layers(PROP_CABINET_BOTTOM, PROP_CABINET_TOP)),
    }
    for mug_name, idx in DESK_MUG.items():
        props[f"table_mug_{mug_name}"] = _scale_prop(compose_layers(PROP_TABLE, idx))
    for paper_name, idx in DESK_PAPER.items():
        props[f"table_paper_{paper_name}"] = _scale_prop(compose_layers(PROP_TABLE, idx))
    props["table_cheese"] = _scale_prop(compose_layers(PROP_TABLE, DESK_CHEESE))
    for plant_name, idx in DESK_PLANT.items():
        props[f"table_plant_{plant_name}"] = _scale_prop(
            compose_layer_scaled(PROP_TABLE, idx, DESK_PLANT_SCALE))
    props["table_keyboard"] = _scale_prop(compose_layers(PROP_TABLE, DESK_KEYBOARD))
    _tile_cache["props"] = props

def _floor_vertices(cx, cy):
    """True on-screen vertices of the floor diamond (matches the actual polygon
    drawn by draw_iso_floor_tile, which trims 1 px from right/bottom edges)."""
    return {
        "top":    (cx, cy - tile_h // 2),
        "right":  (cx + tile_w // 2 - 1, cy),
        "bottom": (cx, cy + tile_h // 2 - 1),
        "left":   (cx - tile_w // 2, cy),
    }

def draw_iso_floor_tile(surface, cx, cy, variant):
    img = _tile_cache["floor"][variant]
    surface.blit(img, img.get_rect(center=(cx, cy)))


def draw_iso_wall_tile(surface, cx, cy, faces=("left", "right"), tall=False, outer_corner=False):
    """Draw wall faces from their exact shared floor edges, plus a top cap
    whenever both faces are present (a genuine corner post). Without the
    cap, the two sloped face-tops meet in a V-notch instead of a flat top
    -- that notch is the "spike". outer_corner gets a bolder, darker line
    so the room's true boundary reads clearly against interior corners."""
    height = BORDER_WALL_HEIGHT if tall else wall_height
    place_x = OFFSETS["wall_place_dx"] * TILE_SCALE
    place_y = OFFSETS["wall_place_dy"] * TILE_SCALE
    lit_colour = _tile_cache["wall_colour"]
    shadow_colour = _tile_cache["wall_shadow_colour"]
    cx += place_x
    cy += place_y

    v = _floor_vertices(cx, cy)

    if "left" in faces:
        base_left, base_right = v["left"], v["bottom"]
        pygame.draw.polygon(surface, lit_colour, [
            (base_left[0], base_left[1] - height),
            (base_right[0], base_right[1] - height),
            base_right, base_left,
        ])
    if "right" in faces:
        base_left, base_right = v["bottom"], v["right"]
        pygame.draw.polygon(surface, shadow_colour, [
            (base_left[0], base_left[1] - height),
            (base_right[0], base_right[1] - height),
            base_right, base_left,
        ])
    if "left" in faces and "right" in faces:
        # Top cap: same diamond shape as a floor tile, translated up by
        # `height`. This is what was missing -- closes the V-notch.
        cap = [
            (v["top"][0], v["top"][1] - height),
            (v["right"][0], v["right"][1] - height),
            (v["bottom"][0], v["bottom"][1] - height),
            (v["left"][0], v["left"][1] - height),
        ]
        pygame.draw.polygon(surface, _tile_cache["wall_cap_colour"], cap)

        line_colour = _tile_cache["wall_corner_colour"]
        line_width = 3 if outer_corner else 2
        pygame.draw.line(
            surface, line_colour,
            (v["bottom"][0], v["bottom"][1] - height), v["bottom"], line_width)
        if outer_corner:
            pygame.draw.lines(surface, line_colour, False, cap, 2)


def draw_elevator_door(surface, cx, cy, face, stage, locked):
    """Draw the real two-piece door art (bottom + top face) stacked like a
    two-high wall. stage selects which of the 4 cached pairs to use."""
    cx += OFFSETS["wall_place_dx"] * TILE_SCALE
    cy += OFFSETS["wall_place_dy"] * TILE_SCALE

    v = _floor_vertices(cx, cy)
    if face == "left":
        base_left, base_right = v["left"], v["bottom"]
    else:
        base_left, base_right = v["bottom"], v["right"]

    bottom_face, top_face = _tile_cache["door_stage_faces"][stage]
    if face == "right":
        bottom_face = pygame.transform.flip(bottom_face, True, False)
        top_face = pygame.transform.flip(top_face, True, False)

    anchor_x = (base_left[0] + base_right[0]) // 2
    floor_y = (base_left[1] + base_right[1]) / 2  # true midpoint of the diagonal floor edge

    bottom_rect = bottom_face.get_rect(midbottom=(anchor_x, floor_y))
    surface.blit(bottom_face, bottom_rect)

    lift = OFFSETS.get("door_top_lift", 16) * TILE_SCALE
    top_rect = top_face.get_rect(midbottom=(anchor_x, bottom_rect.top + lift))
    surface.blit(top_face, top_rect)

    light_colour = elevator_indicator_locked if locked else elevator_indicator_open
    pygame.draw.circle(surface, light_colour, (anchor_x, top_rect.top + 10), 3)


class OffsetTuner:
    """Live in-game tool for nudging OFFSETS by eye instead of guessing pixel
    numbers over chat. F1 toggles it on/off; while active:
      Tab / Shift+Tab  -- cycle which offset is selected
      Up / Down arrow  -- nudge the selected value by 1 (native px)
      Shift+Up/Down    -- nudge by 5
      S                -- save current values to offsets.json
      R                -- reset ALL values back to the coded defaults
    Changes apply immediately (chair/cabinet get re-composited on the spot),
    so you see the result before deciding to save it."""

    def __init__(self):
        self.active = False
        self.keys = list(OFFSETS.keys())
        self.index = 0
        self.message = ""
        self.message_timer = 0

    def _flash(self, text):
        self.message = text
        self.message_timer = 90

    def handle_key(self, key, mods):
        if key == pygame.K_F1:
            self.active = not self.active
            return
        if not self.active:
            return

        shift = mods & pygame.KMOD_SHIFT
        name = self.keys[self.index]

        if key == pygame.K_TAB:
            step = -1 if shift else 1
            self.index = (self.index + step) % len(self.keys)
        elif key in (pygame.K_UP, pygame.K_DOWN):
            step = (5 if shift else 1) * (1 if key == pygame.K_UP else -1)
            OFFSETS[name] += step
        elif key == pygame.K_s:
            save_offsets()
            self._flash("saved to offsets.json")
        elif key == pygame.K_r:
            OFFSETS.update(DEFAULT_OFFSETS)
            self._flash("reset to defaults")

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1

    def draw(self, surface, font):
        if not self.active:
            return
        lines = ["OFFSET TUNER (F1 to close)  Tab=select  Up/Down=nudge  Shift=x5  S=save  R=reset"]
        for i, key in enumerate(self.keys):
            marker = ">" if i == self.index else " "
            lines.append(f"{marker} {key:18s} {OFFSETS[key]:+d}")
        if self.message:
            lines.append(self.message)
        rendered = [font.render(line, True, (255, 255, 255)) for line in lines]
        panel_w = max(r.get_width() for r in rendered) + 16
        panel_h = 20 * len(lines) + 10
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 10, 15, 210))
        for i, line in enumerate(lines):
            colour = (255, 230, 120) if (0 < i <= len(self.keys) and i - 1 == self.index) else (230, 230, 230)
            panel.blit(font.render(line, True, colour), (8, 6 + i * 20))
        panel_x = max(10, surface.get_width() - panel_w - 10)
        surface.blit(panel, (panel_x, 40))


class Floor:
    def __init__(self):
        self.grid = []
        self.cols = 0
        self.rows = 0
        self.elevator_locked = True
        self.elevator_open_start = None
        self.build()

    def build(self):
        grid_template, pillar_positions = random.choice(room_template)
        self.grid = copy.deepcopy(grid_template)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.elevator_locked = True
        self.elevator_open_start = None
        self.floor_variant = [[(row + col) % len(FLOOR_TILE_INDICES)
                                for col in range(self.cols)] for row in range(self.rows)]
        self.props = []
        self.wall_decor = []
        for row, col in pillar_positions:
            self.add_prop(row, col, "crate")

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
        for row, col, name in self.props:
            if name.startswith(SOLID_PROP_PREFIXES):
                # a little smaller than the full tile so it feels fair to
                # walk past rather than blocking the whole grid cell
                pad = tile_size * 0.2
                rects.append(pygame.Rect(
                    col * tile_size + pad, row * tile_size + pad,
                    tile_size - 2 * pad, tile_size - 2 * pad))
        return rects

    def check_elevator(self, player_rect):
        # The player may already be standing on the pad when it is unlocked.
        # Do not rebuild the floor until the door animation has finished, or
        # the visual feedback is skipped entirely.
        if self.elevator_locked or self._elevator_anim_progress() < 1.0:
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
            deferred = player_depth is not None and row + col > player_depth
            if not (deferred and self.grid[row][col] == wall):
                self._draw_tile(surface, camera, row, col)
            if not deferred:
                self._draw_props_at(surface, camera, row, col)

        if player_depth is not None:
            for row, col in self._tiles_in_order():
                if row + col <= player_depth:
                    continue
                if self.grid[row][col] == wall:
                    self._draw_tile(surface, camera, row, col)
                self._draw_props_at(surface, camera, row, col)
        self._draw_all_elevator_doors(surface, camera)

    def draw_behind_player(self, surface, camera, wx, wy, cx, cy):
        player_depth = self._anchor_depth(wx, wy, cx, cy)
        for row, col in self._tiles_in_order():
            deferred = player_depth is not None and row + col > player_depth
            # the tile itself (floor/elevator always draw now -- they're
            # flat ground and never occlude anyone; a wall waits if it's
            # further from the camera than the player)
            if not (deferred and self.grid[row][col] == wall):
                self._draw_tile(surface, camera, row, col)
            # props standing on this tile get the SAME depth treatment as
            # walls -- a crate/table closer to the camera than the player
            # should be drawn after them (occluding), not always on top
            if not deferred:
                self._draw_props_at(surface, camera, row, col)
        return player_depth

    def _anchor_depth(self, feet_wx, feet_wy, center_wx, center_wy):
        tile = self.tile_at(feet_wx, feet_wy)
        if tile is not None and self.grid[tile[0]][tile[1]] in (wall, empty):
            tile = self.tile_at(center_wx, center_wy)
        if tile is None:
            return 0
        return tile[0] + tile[1]

    def draw_in_front_of_player(self, surface, camera, player_depth):
        if player_depth is None:
            return
        for row, col in self._tiles_in_order():
            if row + col <= player_depth:
                continue
            if self.grid[row][col] == wall:
                self._draw_tile(surface, camera, row, col)
            self._draw_props_at(surface, camera, row, col)
        # Doors are a fixed part of the room boundary, not an object that
        # changes draw order as the player crosses a nearby tile.
        self._draw_all_elevator_doors(surface, camera)

    def _tiles_in_order(self):
        return sorted(
            ((row, col) for row in range(self.rows) for col in range(self.cols)),
            key=lambda rc: rc[0] + rc[1]
        )

    def _wall_faces(self, row, col):
        def is_walkable(r, c):
            return (
                0 <= r < self.rows and 0 <= c < self.cols
                and self.grid[r][c] in (floor, elevator)
            )

        faces = []
        if is_walkable(row + 1, col):
            faces.append("left")
        if is_walkable(row, col + 1):
            faces.append("right")
        # True 90° outer corner has neither neighbour walkable → faces stays empty.
        # Treat it as an isolated corner block and show both faces.
        if not faces and self._is_outer_wall(row, col):
            faces = ["left", "right"]
        return tuple(faces)

    def _is_void(self, row, col):
        return (
            row < 0 or col < 0 or row >= self.rows or col >= self.cols
            or self.grid[row][col] == empty
        )

    def _is_outer_wall(self, row, col):
        """Return whether this wall borders the void on the back or left side.

        In the isometric projection those are the two sides that form the
        tall, room-enclosing backdrop.  Looking at neighbours rather than the
        grid's row/column zero also handles stepped rooms such as the L-shaped
        template correctly.
        """
        return self._is_void(row - 1, col) or self._is_void(row, col - 1)

    def _is_outer_corner(self, row, col):
        """An outer corner is already covered by its two adjoining wall runs."""
        return self._is_void(row - 1, col) and self._is_void(row, col - 1)

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
            is_outer_wall = self._is_outer_wall(row, col)
            faces = self._wall_faces(row, col)
            # A concave room corner joins two tall exterior runs.  It needs
            # the same height and must not reveal its floor tile through the
            # joint, otherwise the corner looks split open.
            is_tall_wall = is_outer_wall or len(faces) == 2
            # The floor diamond on a tall exterior wall is hidden behind its
            # two wall sections.  Drawing it creates a bright strip that looks
            # like a floor tile floating behind the outside wall.
            if not is_tall_wall:
                draw_iso_floor_tile(surface, cx, cy, variant)
            if faces:
                draw_iso_wall_tile(
                    surface, cx, cy, faces=faces, tall=is_tall_wall,
                    outer_corner=self._is_outer_corner(row, col))
            self._draw_wall_decor(surface, cx, cy, row, col, is_tall_wall)

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

    def _draw_all_elevator_doors(self, surface, camera):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != wall:
                    continue
                wx = (col + 0.5) * tile_size
                wy = (row + 0.5) * tile_size
                cx, cy = camera.world_to_screen(wx, wy)
                if row + 1 < self.rows and self.grid[row + 1][col] == elevator:
                    draw_elevator_door(
                        surface, cx, cy, "left", self._elevator_stage(), self.elevator_locked)
                if col + 1 < self.cols and self.grid[row][col + 1] == elevator:
                    draw_elevator_door(
                        surface, cx, cy, "right", self._elevator_stage(), self.elevator_locked)

    def _has_adjacent_wall(self, row, col):
        for drow, dcol in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= drow < self.rows and 0 <= dcol < self.cols and self.grid[drow][dcol] == wall:
                return True
        return False

    def _draw_free_standing_door(self, surface, cx, cy):
        draw_elevator_door(surface, cx, cy, "left", self._elevator_stage(), self.elevator_locked)

    def add_prop(self, row, col, name):
        if 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == floor:
            self.props.append((row, col, name))

    def _draw_props_at(self, surface, camera, row, col):
        """Draw any props anchored at this cell. Called from within the
        depth-sorted draw passes (not on its own) so a prop's row+col is
        compared against the player the same way a wall's is -- a prop
        closer to the camera occludes the player, one further away doesn't,
        instead of always rendering on top of everything."""
        for prow, pcol, name in self.props:
            if (prow, pcol) != (row, col):
                continue
            wx, wy = (pcol + 0.5) * tile_size, (prow + 0.5) * tile_size
            cx, cy = camera.world_to_screen(wx, wy)
            img = _tile_cache["props"][name]
            surface.blit(img, img.get_rect(midbottom=(cx, cy + tile_h // 2)))

    def add_wall_decor(self, row, col, side, name):
        if 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == wall:
            self.wall_decor.append((row, col, side, name))

    def _draw_wall_decor(self, surface, cx, cy, row, col, tall=False):
        height = BORDER_WALL_HEIGHT if tall else wall_height
        for drow, dcol, side, name in self.wall_decor:
            if (drow, dcol) != (row, col):
                continue
            img = _tile_cache["wall_decor"][(side, name)]
            if side == "left":
                surface.blit(img, (cx - tile_w // 2, cy - height))
            else:
                surface.blit(img, (cx, cy - height))

    def _depth_for(self, wx, wy):
        tile = self.tile_at(wx, wy)
        if tile is None:
            return 0
        return tile[0] + tile[1]

    def _door_jobs(self):
        """(depth, face, row, col) for every door, so draw_scene can
        depth-sort them against entities instead of always drawing on top."""
        jobs = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != wall:
                    continue
                depth = row + col
                if row + 1 < self.rows and self.grid[row + 1][col] == elevator:
                    jobs.append((depth, "left", row, col))
                if col + 1 < self.cols and self.grid[row][col + 1] == elevator:
                    jobs.append((depth, "right", row, col))
        return jobs

    def _draw_door_job(self, surface, camera, face, row, col):
        wx = (col + 0.5) * tile_size
        wy = (row + 0.5) * tile_size
        cx, cy = camera.world_to_screen(wx, wy)
        draw_elevator_door(
            surface, cx, cy, face,
            self._elevator_stage(), self.elevator_locked
        )

    def draw_scene(self, surface, camera, entities):
        """Depth-sorted draw of the whole room + any number of moving entities
        and elevator doors."""
        tiles = self._tiles_in_order()

        jobs = sorted(
            [(self._depth_for(e.wx, e.wy), "entity", e) for e in entities]
            + [(d, "door", (face, r, c)) for d, face, r, c in self._door_jobs()],
            key=lambda j: j[0],
        )

        def flush(job):
            _, kind, payload = job
            if kind == "entity":
                payload.draw(surface, camera)
            else:
                face, r, c = payload
                self._draw_door_job(surface, camera, face, r, c)

        job_index = 0
        tile_index = 0
        total_tiles = len(tiles)

        while tile_index < total_tiles:
            row, col = tiles[tile_index]
            depth = row + col

            # draw every tile + prop at this depth
            while tile_index < total_tiles and (tiles[tile_index][0] + tiles[tile_index][1]) == depth:
                r, c = tiles[tile_index]
                self._draw_tile(surface, camera, r, c)
                self._draw_props_at(surface, camera, r, c)
                tile_index += 1

            # draw every entity / door that belongs at or behind this depth
            while job_index < len(jobs) and jobs[job_index][0] <= depth:
                flush(jobs[job_index])
                job_index += 1

        # anything still left (entities/doors further forward than the last tile)
        while job_index < len(jobs):
            flush(jobs[job_index])
            job_index += 1
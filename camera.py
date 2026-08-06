"""
My camera class to like move the camera around my dude
"""

class Camera:
    def __init__(self, screen_width, screen_height, tile_size, tile_w, tile_h):
        self.sw = screen_width
        self.sh = screen_height
        self.tile_size = tile_size
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.cam_x = 0
        self.cam_y = 0

    def update(self, target_wx, target_wy):
        gx = target_wx / self.tile_size
        gy = target_wy / self.tile_size
        px = (gx - gy) * (self.tile_w / 2)
        py = (gx + gy) * (self.tile_h / 2)
        self.cam_x = px - self.sw // 2
        self.cam_y = py - self.sh // 2

    def world_to_screen(self, wx, wy):
        gx = wx / self.tile_size
        gy = wy / self.tile_size
        sx = (gx - gy) * (self.tile_w / 2) - self.cam_x
        sy = (gx + gy) * (self.tile_h / 2) - self.cam_y
        return int(sx), int(sy)
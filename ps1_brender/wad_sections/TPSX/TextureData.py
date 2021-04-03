import math
from io import BufferedIOBase

from ps1_brender.configuration import Configuration, G


class TextureData:
    def __init__(self, raw_data: BufferedIOBase, conf: Configuration):
        coords_1 = (raw_data.read(1)[0], raw_data.read(1)[0])
        palette_info = int.from_bytes(raw_data.read(2), 'little')
        coords_2 = (raw_data.read(1)[0], raw_data.read(1)[0])
        flags = int.from_bytes(raw_data.read(2), 'little')  # Use a IntFlag class
        coords_3 = (raw_data.read(1)[0], raw_data.read(1)[0])
        coords_4 = (raw_data.read(1)[0], raw_data.read(1)[0])
        coords = [coords_1, coords_2, coords_3, coords_4]

        # Coordinates Mapping
        if coords[0][0] > coords[1][0]:
            if coords[0][1] > coords[2][1]:
                cm = (3, 2, 1, 0)
            else:
                cm = (1, 0, 3, 2)
        else:
            if coords[0][1] > coords[2][1]:
                cm = (2, 3, 0, 1)
            else:
                cm = (0, 1, 2, 3)

        self.n_row = ((flags & 4) >> 1) + ((flags & 16) >> 4)
        self.n_column = flags & 3
        self.idk = flags & 0xFE00

        self.paletted: bool = (flags & 256) == 0
        if self.paletted:
            self.palette_256_colors = (flags & 128) != 0
            self.palette_start = ((palette_info & 65472) << 3) + ((palette_info & 15) << 5)

        # Correction Ratio, needed for non-4bit/pixel textures to be correctly positioned
        cr = 4 if not self.paletted else 2 if self.palette_256_colors else 1
        # The top-left x coordinate of the 256-colors or true color textures needs to be corrected
        x_correction = coords[cm[0]][0] * cr - coords[cm[0]][0]
        for i in range(4):
            coords[i] = \
                (coords[i][0] + x_correction + self.n_column * 256, coords[i][1] + self.n_row * 256)

        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            for i in range(4):
                coords[i] = (2 * math.ceil(coords[i][0] / 2), 2 * math.ceil(coords[i][1] / 2))
        else:
            pass  # FIXME Croc 2 Demo Dummy textures are sometimes 1 pixel too small
        self.coords = tuple(coords)

        self.box = (self.coords[cm[0]][0], self.coords[cm[0]][1], self.coords[cm[3]][0], self.coords[cm[3]][1])
        self.width = self.box[2] - self.box[0]
        self.height = self.box[3] - self.box[1]
        assert self.width > 0
        assert self.height > 0

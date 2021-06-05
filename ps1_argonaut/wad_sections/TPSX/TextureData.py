import math
from io import BufferedIOBase
from struct import Struct
from typing import Tuple, Iterable, List, Optional

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.configuration import Configuration
from ps1_argonaut.utils import XY
from ps1_argonaut.wad_sections.TPSX.TextureFlags import TextureFlags

Box = Tuple[int, int, int, int]
Coords = List[XY]


class TextureData(BaseDataClass):
    struct = Struct('2BH2BH4B')

    def __init__(self, flags: TextureFlags, raw_coords: Coords, cm: Box, palette_start: Optional[int]):
        self.flags = flags
        assert self.flags.value & 0xFE00 == 0
        self.raw_coords = raw_coords
        self.cm = cm
        self.palette_start = palette_start

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        c1x, c1y, palette_info, c2x, c2y, flags, c3x, c3y, c4x, c4y = cls.struct.unpack(data_in.read(12))
        flags: TextureFlags = TextureFlags(flags)
        # Raw coordinates are contained in a 1024x1024, 512x1024 or 256x1024 space
        # (16-colors paletted, 256-colors paletted and non-paletted high color respectively)
        raw_coords = [(c1x, c1y), (c2x, c2y), (c3x, c3y), (c4x, c4y)]

        # Coordinates Mapping, needed to put the coordinates in the right order
        # (top-left, top-right, bottom-left then bottom-right)
        if raw_coords[0][0] > raw_coords[1][0]:
            if raw_coords[0][1] > raw_coords[2][1]:
                cm = 3, 2, 1, 0
            else:
                cm = 1, 0, 3, 2
        else:
            if raw_coords[0][1] > raw_coords[2][1]:
                cm = 2, 3, 0, 1
            else:
                cm = 0, 1, 2, 3

        palette_start = None
        if TextureFlags.IS_NOT_PALETTED not in flags:
            palette_start = ((palette_info & 0xFFC0) << 3) + ((palette_info & 0xF) << 5)

        # The top-left x coordinate of the 256-colors or high color textures needs to be corrected
        # 1024x1024 space -> 512x1024 or 256x1024 space respectively
        return cls(flags, raw_coords, cm, palette_start)

    @staticmethod
    def round_coords(coords: Iterable[XY]):
        """Textures tend to be better delimited when rounded to the nearest multiple of 2"""
        return [(2 * math.ceil(coord[0] / 2), 2 * math.ceil(coord[1] / 2)) for coord in coords]

    @property
    def input_coords(self):
        """Unordered coordinates of this texture (256x1024, 512x1024 or 1024x1024 space)"""
        return self.round_coords(
            (self.raw_coords[i][0] + (256 // self.flags.correction_ratio) * self.flags.n_column,
             self.raw_coords[i][1] + 256 * self.flags.n_row) for i in range(4))

    @property
    def output_coords(self):
        """Unordered coordinates of this texture (1024x1024 space)"""
        x_correction = self.raw_coords[self.cm[0]][0] * self.flags.correction_ratio - self.raw_coords[self.cm[0]][0]
        return self.round_coords(
            (self.raw_coords[i][0] + x_correction + 256 * self.flags.n_column,
             self.raw_coords[i][1] + 256 * self.flags.n_row) for i in range(4))

    @property
    def input_box(self):
        """Left, top, right, bottom coordinates of this texture (256x1024, 512x1024 or 1024x1024 space)"""
        ic = self.input_coords
        return ic[self.cm[0]][0], ic[self.cm[0]][1], ic[self.cm[3]][0], ic[self.cm[3]][1]

    @property
    def output_top_left_corner(self):
        """x, y coordinates of this texture's top left corner (1024x1024 space)"""
        return self.output_coords[self.cm[0]]

from enum import Enum
from itertools import accumulate
from typing import Iterable, List, Optional

import numpy as np
from PIL import Image

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.configuration import Configuration
from ps1_argonaut.files.DATFile import DATFile
from ps1_argonaut.utils import parse_palette, XY, parse_4bits_paletted, parse_high_color


class ImageType(Enum):
    def __init__(self, bytes_size: int, dimensions: XY, n_palette_colors: int, has_alpha=True):
        self.bytes_size = bytes_size
        self.dimensions = dimensions
        self.n_palette_colors = n_palette_colors
        self.has_alpha = has_alpha

        if n_palette_colors == 0:
            assert 2 * dimensions[0] * dimensions[1] == bytes_size
        elif n_palette_colors == 16:
            assert dimensions[0] * dimensions[1] == 2 * (bytes_size - 32)
        elif n_palette_colors == 256:
            assert dimensions[0] * dimensions[1] == (bytes_size - 512 - (256 * (self._name_ == 'SKY')))
        else:
            raise ValueError("Unsupported color palette size")

    @classmethod
    def guess_from_bytes_size(cls, bytes_size: int):
        for member in cls._member_map_.values():  # type: ImageType
            if member.bytes_size == bytes_size:
                return member

    LOAD = (262144, (512, 256), 0, False)
    STORY = (123392, (512, 240), 256)
    TEXT = (72192, (448, 160), 256)
    BADGES1 = (229376, (448, 256), 0)
    BADGES2 = (215040, (448, 240), 0)
    FLAG1 = (49664, (128, 384), 256)
    FLAG2 = (25088, (128, 192), 256)
    FORKLIGT = (42804, (218, 194), 256)
    PAGE = (1536, (32, 32), 256)
    PLAY = (20992, (256, 80), 256)
    SKY = (131840, (512, 256), 256)
    SKY2 = (131584, (512, 256), 256)
    CARD = (6656, (96, 64), 256)
    DADA = (608, (48, 24), 16)
    REFL = (4128, (64, 128), 16)
    LBAR = (336, (12, 14), 0)
    SAVE = (9728, (96, 96), 256)
    AM = (31232, (320, 96), 256)
    GLOW = (832, (40, 40), 16)
    GRADE = (288, (32, 16), 16)
    WIZ = (2080, (64, 64), 16)
    WIZPAGE = (2080, (128, 32), 16)


class IMGFile(List[Image.Image], DATFile, BaseDataClass):
    suffix = 'IMG'

    def __init__(self, stem: str, images: Iterable[Image.Image] = None, data: bytes = None):
        list.__init__(self, images if images is not None else ())
        DATFile.__init__(self, stem, data=data)

    def __str__(self):
        dimensions = ', '.join(f'({x.size[0]}x{x.size[1]} px)' for x in self)
        res = 'Menu image'
        if dimensions:
            res += f'\n{dimensions}'
        return res

    def parse(self, conf: Configuration, *args, **kwargs):
        if self.stem == 'REPORT':  # Patch for REPORT.IMG that contains multiple images
            offsets = list(accumulate((608, 288, 288, 288, 608, 608, 608, 608, 608, 608, 608, 608)))
            images_data = [self._data[offsets[i - 1]:offsets[i]] for i in range(1, len(offsets))]
        else:
            images_data = (self._data,)

        self.clear()
        for image_data in images_data:
            if len(image_data) in [image_type.bytes_size for image_type in ImageType]:
                # Fix for WIZPAGE.IMG that has the same bytes length than other WIZ files but not the same dimensions
                if 'stem' in kwargs and kwargs['stem'] == 'WIZPAGE':
                    image_type = ImageType.WIZPAGE
                else:
                    image_type: ImageType = ImageType.guess_from_bytes_size(len(image_data))
                if image_type.n_palette_colors != 0:
                    palette = parse_palette(image_data, image_type.n_palette_colors, image_type.has_alpha)
                else:
                    palette = None
                self.append(IMGFile.to_full_colorized(image_data, image_type.dimensions, palette,
                                                      image_type.n_palette_colors, image_type.has_alpha))
            else:
                raise ValueError("Unknown image size")
        self.end_parse()

    @staticmethod
    def to_full_colorized(data: bytes, dimensions: XY, palette: Optional[List[int]], n_palette_colors: int,
                          has_alpha: bool):
        mode = 'RGBA' if has_alpha else 'RGB'
        pixels_data = data[2 * n_palette_colors:]
        if n_palette_colors != 0:
            if n_palette_colors == 16:
                pixels = np.reshape(np.array(parse_4bits_paletted(pixels_data), dtype=np.uint8),
                                    (dimensions[1], dimensions[0]))
                image = Image.fromarray(pixels, 'P')
            else:
                image = Image.frombytes('P', dimensions, pixels_data)
            image.putpalette(palette, mode)
            return image
        else:
            pixels = np.reshape(np.array(parse_high_color(pixels_data, has_alpha), dtype=np.uint8),
                                (dimensions[1], dimensions[0], 4 if has_alpha else 3))
            return Image.fromarray(pixels, mode)

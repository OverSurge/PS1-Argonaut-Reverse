import warnings
from io import BufferedIOBase, SEEK_CUR, BytesIO
from typing import List, Iterable

import numpy as np
from PIL import Image

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.errors_warnings import TexturesWarning, ZeroRunLengthError
from ps1_argonaut.utils import parse_4bits_paletted, parse_high_color, parse_palette
from ps1_argonaut.wad_sections.TPSX.TextureData import TextureData
from ps1_argonaut.wad_sections.TPSX.TextureFlags import TextureFlags


class TextureFile(List[TextureData], BaseDataClass):
    image_header_size = 4
    rle_size = 2
    image_dimensions = (1024, 1024)
    image_bytes_size = image_dimensions[0] * image_dimensions[1] // 2

    def __init__(self, n_rows: int, textures_data: bytes, legacy_alpha: bool, textures: Iterable[TextureData] = None):
        super().__init__(textures)
        self.n_rows = n_rows
        self.textures_data = textures_data
        self.legacy_alpha = legacy_alpha  # TODO Legacy alpha (Croc 2)
        self.has_alpha = not legacy_alpha  # TODO Remove. Patch that disables bugged Croc 2 textures transparency export
        self.textures = list(textures) if textures is not None else []

    @property
    def n_textures(self):
        return len(self)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        super().parse(data_in, conf)
        has_legacy_textures: bool = kwargs['has_legacy_textures']
        end: int = kwargs['end']
        rle = conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)

        textures: List[TextureData] = []
        n_textures: int = int.from_bytes(data_in.read(4), 'little')
        n_rows: int = int.from_bytes(data_in.read(4), 'little')

        if n_textures > 4000 or 0 > n_rows > 4:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much textures ({n_textures}, or incorrect row count {n_rows}."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the textures format.")
            else:
                raise TexturesWarning(data_in.tell(), n_textures, n_rows)

        # In Harry Potter, the last 16 textures are empty (full of 00 bytes)
        n_stored_textures = n_textures - 16 if conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1) else n_textures
        for texture_id in range(n_stored_textures):
            textures.append(TextureData.parse(data_in, conf))
        if conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1):
            data_in.seek(192, SEEK_CUR)  # 16 textures x 12 bytes
        n_idk_yet_1 = int.from_bytes(data_in.read(4), 'little')
        n_idk_yet_2 = int.from_bytes(data_in.read(4), 'little')
        data_in.seek(n_idk_yet_1 * cls.image_header_size, SEEK_CUR)

        if has_legacy_textures:  # Patch for legacy textures, see Textures documentation
            data_in.seek(15360, SEEK_CUR)
        if rle:
            raw_textures = BytesIO(cls.image_bytes_size * b'\x00')
            while data_in.tell() < end:
                run = int.from_bytes(data_in.read(cls.rle_size), 'little', signed=True)
                if run < 0:
                    raw_textures.write(abs(run) * data_in.read(cls.rle_size))
                elif run > 0:
                    raw_textures.write(data_in.read(cls.rle_size * run))
                else:
                    raise ZeroRunLengthError(data_in.tell())
            raw_textures.seek(0)
            textures_data = raw_textures.read()
            if conf.game == G.CROC_2_DEMO_PS1:  # Patch for Croc 2 Demo (non-dummy) last end offset error
                data_in.seek(-2, SEEK_CUR)
        else:
            image_size = n_rows * (cls.image_bytes_size // 4)
            padding_size = cls.image_bytes_size - image_size
            textures_data = data_in.read(image_size) + padding_size * b'\x00'
        legacy_alpha = conf.game in (G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY)
        return cls(n_rows, textures_data, legacy_alpha, textures)

    def to_colorized_texture(self):
        """Draws a complete colored texture image (composed of multiple single textures)."""
        rgba = 'RGBA'
        rgb = 'RGB'

        res = Image.new(rgba, self.image_dimensions, None)

        im_4bits_paletted = Image.fromarray(np.array(parse_4bits_paletted(self.textures_data), dtype=np.uint8)
                                            .reshape(self.image_dimensions[1], self.image_dimensions[0]), 'P')
        im_8bits_paletted = Image.fromarray(np.array(list(self.textures_data), dtype=np.uint8)
                                            .reshape((self.image_dimensions[1], self.image_dimensions[0] // 2)), 'P')
        im_high_color = Image.fromarray(np.array(parse_high_color(self.textures_data, True), dtype=np.uint8)
                                        .reshape((self.image_dimensions[1], self.image_dimensions[0] // 4, 4)), rgba)

        texture_mode = rgba if self.has_alpha else rgb
        for texture in self.textures:
            box = texture.input_box
            if TextureFlags.IS_NOT_PALETTED not in texture.flags:
                if TextureFlags.HAS_256_COLORS_PALETTE in texture.flags:  # 256-colors paletted
                    texture_image = im_8bits_paletted.crop(box)
                    texture_image.putpalette(parse_palette(self.textures_data, 256, self.has_alpha, self.legacy_alpha,
                                                           texture.palette_start), texture_mode)
                else:  # 16-colors paletted
                    texture_image = im_4bits_paletted.crop(box)
                    texture_image.putpalette(parse_palette(self.textures_data, 16, self.has_alpha, self.legacy_alpha,
                                                           texture.palette_start), texture_mode)
            else:  # True color (no palette)
                texture_image = im_high_color.crop(box)
            res.paste(texture_image, texture.output_top_left_corner)
        return res

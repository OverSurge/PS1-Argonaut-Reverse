import warnings
from io import BufferedIOBase, SEEK_CUR
from typing import List, Tuple, Union

from PIL import Image

from ps1_brender.configuration import Configuration, G
from ps1_brender.errors_warnings import TexturesWarning, ZeroRunLengthError
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.TPSX.TextureData import TextureData


class TextureFile(BaseBRenderClass):
    image_header_size = 4
    rle_size = 2
    image_size = 1024

    def __init__(self, has_legacy_textures: bool, textures: List[TextureData], n_textures: int,
                 n_rows: int, raw_texture: bytes):
        self.has_legacy_textures = has_legacy_textures
        self.textures = textures
        self.n_textures = n_textures
        self.n_rows = n_rows
        self.raw_texture = raw_texture

    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration, end: int, has_legacy_textures: bool):
        super().parse(raw_data, conf)
        rle = conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)

        textures: List[TextureData] = []
        n_textures: int = int.from_bytes(raw_data.read(4), 'little')
        n_rows: int = int.from_bytes(raw_data.read(4), 'little')

        if n_textures > 4000 or 0 > n_rows > 4:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much textures ({n_textures}, or incorrect row count {n_rows}."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the textures format.")
            else:
                raise TexturesWarning(raw_data.tell(), n_textures, n_rows)

        # In Harry Potter, the last 16 textures are empty (full of 00 bytes)
        n_stored_textures = n_textures - 16 if conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1) else n_textures
        for texture_id in range(n_stored_textures):
            textures.append(TextureData(raw_data, conf))
        if conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1):
            raw_data.seek(192, SEEK_CUR)  # 16 textures x 12 bytes
        n_idk_yet_1 = int.from_bytes(raw_data.read(4), 'little')
        n_idk_yet_2 = int.from_bytes(raw_data.read(4), 'little')
        raw_data.seek(n_idk_yet_1 * cls.image_header_size, SEEK_CUR)

        if has_legacy_textures:  # Patch for legacy textures, see Textures documentation
            raw_data.seek(15360, SEEK_CUR)
        if rle:
            raw = bytearray()
            while raw_data.tell() < end:
                run = int.from_bytes(raw_data.read(cls.rle_size), 'little', signed=True)
                if run < 0:
                    raw += raw_data.read(cls.rle_size) * abs(run)
                elif run > 0:
                    raw += raw_data.read(cls.rle_size * run)
                else:
                    raise ZeroRunLengthError(raw_data.tell())
            raw_texture = bytes(raw)
            if conf.game == G.CROC_2_DEMO_PS1:  # Patch for Croc 2 Demo (non-dummy) last end offset error
                raw_data.seek(-2, SEEK_CUR)
        else:
            raw_texture: bytes = raw_data.read(n_rows * 131072)

        return cls(has_legacy_textures, textures, n_textures, n_rows, raw_texture)

    def generate_texture(self, texture: Union[int, TextureData], debug=False):
        """Draws a single colored texture."""
        if isinstance(texture, int):
            texture = self.textures[texture]
        elif not isinstance(texture, TextureData):
            raise TypeError

        palette = None
        res: Image.Image = Image.new('RGBA', (texture.width, texture.height), 'green' if debug else None)
        if texture.paletted:
            palette = self.get_palette(texture)

        start = (self.image_size * texture.box[1] + texture.box[0]) // 2
        for row_id in range(texture.height):
            if texture.paletted:
                if texture.palette_256_colors:  # 256-colors paletted
                    for column_id in range(texture.width):
                        pos = start + (column_id + self.image_size // 2 * row_id)
                        res.putpixel((column_id, row_id), palette[self.raw_texture[pos]])
                else:  # 16-colors paletted
                    for column_id in range(0, texture.width, 2):
                        pos = start + (column_id + self.image_size * row_id) // 2
                        pixel1 = self.raw_texture[pos] & 15
                        pixel2 = (self.raw_texture[pos] & 240) >> 4
                        res.putpixel((column_id, row_id), palette[pixel1])
                        if column_id + 1 < texture.width:
                            res.putpixel((column_id + 1, row_id), palette[pixel2])
            else:  # True color (no palette)
                pos = start + (self.image_size // 2 * row_id)
                pixels = TextureFile.raw_as_true_color(self.raw_texture, pos, pos + texture.width * 2)
                for i in range(len(pixels)):
                    res.putpixel((i, row_id), pixels[i])
        return res

    # TODO: Remove textures parameter (used for debug)
    def generate_colorized_texture(self, debug=False, textures=None):
        """Draws a complete colored texture image (composed of multiple single textures)."""
        if textures is None:
            textures = self.textures
        res: Image.Image = Image.new('RGBA', (self.image_size, self.image_size), 'green' if debug else None)
        for texture in textures:
            texture_image = self.generate_texture(texture, debug)
            if texture_image:
                res.paste(texture_image, texture.box)
        return res

    def get_palette(self, texture: TextureData) -> Tuple[Tuple[int, int, int, int], ...]:
        """Returns palettes colors in tuples of 3 RGB colors given the palette start and type (16 or 256 colors)."""
        if texture.palette_256_colors:  # 256-colors palettes ignore the transparency bit (always unset)
            return TextureFile.raw_as_true_color(self.raw_texture, texture.palette_start, texture.palette_start + 512,
                                                 True)
        else:
            return TextureFile.raw_as_true_color(self.raw_texture, texture.palette_start, texture.palette_start + 32)

    def __getitem__(self, item):
        return self.textures[item]

    @staticmethod
    def raw_as_true_color(data: bytes, start: int, end: int, ignore_transparency_bit=False) -> \
            Tuple[Tuple[int, int, int, int], ...]:
        """Converts 15-bit high color raw bytes (see doc @Textures.md#15-bit-high-color)
        into tuples containing separate RGB components."""
        res = []
        for i in range(start, end, 2):
            color_bytes = int.from_bytes(data[i:i + 2], 'little')
            res.append((((color_bytes & 31) * 527 + 23) >> 6,
                        (((color_bytes & 992) >> 5) * 527 + 23) >> 6,
                        (((color_bytes & 31744) >> 10) * 527 + 23) >> 6,
                        0 if color_bytes == 0 else 255))
        return tuple(res)

    # Debug functions

    def generate_greyscale_texture(self):
        """Debug use, do not use for textures extraction ! Draws the complete texture image in greyscale."""
        res: Image.Image = Image.new('L', (self.image_size, self.image_size))
        for i in range(len(self.raw_texture)):
            pixel1 = self.raw_texture[i] & 15
            pixel2 = (self.raw_texture[i] & 240) >> 4
            i2 = 2 * i
            xy1 = (i2 % self.image_size, i2 // self.image_size)
            xy2 = ((i2 + 1) % self.image_size, (i2 + 1) // self.image_size)
            res.putpixel(xy1, pixel1 * 16)
            res.putpixel(xy2, pixel2 * 16)
        return res

    def generate_true_color_texture(self):
        """Debug use, do not use for textures extraction ! Draws the complete texture image in greyscale."""
        res: Image.Image = Image.new('RGBA', (self.image_size // 4, self.image_size))
        res.putdata(TextureFile.raw_as_true_color(self.raw_texture, 0, len(self.raw_texture)))
        return res

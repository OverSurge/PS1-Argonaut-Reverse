import warnings
from typing import List, Tuple, Union

from ps1_brender import *
from ps1_brender.data_models import AnimationData, ModelData, TextureData


class TextureFile:
    def __init__(self, data: bytes, start: int, end: int, conf: Configuration, has_legacy_textures=False):
        self.game = conf.game
        texture_size = 12
        image_header_size = 4

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            rle = True
        elif conf.game == CROC_2_DEMO_PS1_DUMMY:
            rle = False
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)

        self.textures: List[TextureData] = []
        self.n_textures: int = int.from_bytes(data[start:start + 4], 'little')
        self.n_rows: int = int.from_bytes(data[start + 4:start + 8], 'little')
        self.size = end - start
        start += 8

        if self.n_textures > 4000 or 0 > self.n_rows > 4:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much textures ({self.n_textures}, or incorrect row count {self.n_rows}."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the textures format.")
            else:
                raise TexturesWarning(start, self.n_textures, self.n_rows)

        for texture_id in range(self.n_textures):
            tex_start = start + texture_id * texture_size
            self.textures.append(TextureData(data, tex_start, conf))
        start += self.n_textures * texture_size
        n_idk_yet_1 = int.from_bytes(data[start:start + 4], 'little')
        n_idk_yet_2 = int.from_bytes(data[start + 4:start + 8], 'little')
        start += 8 + n_idk_yet_1 * image_header_size

        if has_legacy_textures:  # Patch for legacy textures, see Textures documentation
            start += 15360
        if rle:
            rle_bytes = 2
            raw = bytearray()
            while start < end:
                run = int.from_bytes(data[start:start + rle_bytes], 'little', signed=True)
                start += rle_bytes
                if run < 0:
                    raw += data[start:start + rle_bytes] * abs(run)
                    start += rle_bytes
                elif run > 0:
                    raw += data[start:start + rle_bytes * run]
                    start += rle_bytes * run
                else:
                    raise ZeroRunLengthError(start)
            self.raw_texture: bytes = bytes(raw)
        else:
            self.raw_texture: bytes = data[start:start + self.n_rows * 131072]
        self.image_size = 1024

    def generate_texture(self, texture: Union[int, TextureData], debug=False):
        from PIL import Image

        if isinstance(texture, int):
            texture = self.textures[texture]
        elif not isinstance(texture, TextureData):
            raise TypeError

        if debug:
            debug_print = f"w:{texture.width}|h:{texture.height}|box:{texture.box}|row:{texture.n_row}|" \
                          f"col:{texture.n_column}|coords:{texture.coordinates}|"
            if texture.paletted:
                if texture.palette_256_colors:
                    debug_print += f"palette256:{texture.palette_start}"
                else:
                    debug_print += f"palette16:{texture.palette_start}"
            else:
                debug_print += "nopalette"
            print(debug_print)

        if texture.width < 0 or texture.height < 0:
            # TODO: Mirrored (reversed) textures
            return

        palette = None
        res: Image.Image = Image.new('RGBA', (texture.width, texture.height), 'green' if debug else None)
        if texture.paletted:
            palette = self.get_palette(texture)

        start = (self.image_size * texture.box[1] + texture.box[0]) // 2
        # TODO: Non-rectangular textures
        for row_id in range(texture.height):
            if texture.paletted:
                if texture.palette_256_colors:
                    for column_id in range(texture.width):
                        pos = start + (column_id + self.image_size // 2 * row_id)
                        res.putpixel((column_id, row_id), palette[self.raw_texture[pos]])
                else:
                    for column_id in range(0, texture.width, 2):
                        pos = start + (column_id + self.image_size * row_id) // 2
                        pixel1 = self.raw_texture[pos] & 15
                        pixel2 = (self.raw_texture[pos] & 240) >> 4
                        res.putpixel((column_id, row_id), palette[pixel1])
                        if column_id + 1 < texture.width:
                            res.putpixel((column_id + 1, row_id), palette[pixel2])
            else:
                pos = start + (self.image_size // 2 * row_id)
                pixels = TextureFile.raw_as_true_color(self.raw_texture, pos, pos + texture.width * 2)
                for i in range(len(pixels)):
                    res.putpixel((i, row_id), pixels[i])
        return res

    # TODO: Remove textures parameter (used for debug)
    def generate_colorized_texture(self, debug=False, textures=None):
        from PIL import Image
        if textures is None:
            textures = self.textures
        """Draws a complete colored texture image. Meant for visual indication, not reliable.
        (multiple textures (with multiple palettes) may overlap)"""
        if debug:
            res: Image.Image = Image.new('RGBA', (self.image_size, self.image_size), 'green')
        else:
            res: Image.Image = Image.new('RGBA', (self.image_size, self.n_rows * 256), None)
        if self.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            textures = textures[:-16]
        elif self.game in (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY):
            pass
        else:
            raise NotImplementedError
        for texture in textures:
            texture_image = self.generate_texture(texture, debug)
            if texture_image:
                res.paste(texture_image, texture.box)
        return res

    def generate_greyscale_texture(self):
        """Draws the complete texture image in greyscale (Palette indexes are converted into a color value).
        Meant for visual indication, not reliable."""
        from PIL import Image
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
        """"""
        from PIL import Image
        res: Image.Image = Image.new('RGBA', (self.image_size // 4, self.image_size))
        res.putdata(TextureFile.raw_as_true_color(self.raw_texture, 0, len(self.raw_texture)))
        return res

    def get_palette(self, texture: TextureData) -> List[Tuple[int, int, int, int]]:
        if texture.palette_256_colors:
            return TextureFile.raw_as_true_color(self.raw_texture, texture.palette_start, texture.palette_start + 512,
                                                 True)
        else:
            return TextureFile.raw_as_true_color(self.raw_texture, texture.palette_start, texture.palette_start + 32)

    def __getitem__(self, item):
        return self.textures[item]

    @staticmethod
    def raw_as_true_color(data: bytes, start: int, end: int, ignore_transparency_bit=False) -> \
            List[Tuple[int, int, int, int]]:
        """Converts 15-bit high color (|GGGRRRRR|TBBBBBGG|, see doc @Textures.md#15-bit-high-color)
        into a list of tuples containing separate RGB components"""
        res = []
        for i in range(start, end, 2):
            color_bytes = int.from_bytes(data[i:i + 2], 'little')
            color = (((color_bytes & 31) * 527 + 23) >> 6,
                     (((color_bytes & 992) >> 5) * 527 + 23) >> 6,
                     (((color_bytes & 31744) >> 10) * 527 + 23) >> 6)
            if color_bytes == 0 and ignore_transparency_bit is False:
                transparency = 0
            else:
                transparency = 255
            res.append(color + (transparency,))
        return res


class ModelFile:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.models: List[ModelData] = []
        self.n_models: int = int.from_bytes(data[start:start + 4], 'little')
        self.size = start
        start += 4
        for model_id in range(self.n_models):
            model = ModelData(data, start, conf)
            self.models.append(model)
            start += model.size
        self.size = start - self.size

    def __getitem__(self, item):
        return self.models[item]


class AnimationFile:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.animations: List[AnimationData] = []
        self.n_animations: int = int.from_bytes(data[start: start + 4], 'little')
        self.size = start
        start += 4
        for anim_id in range(self.n_animations):
            animation = AnimationData(data, start, conf)
            start += animation.size
            self.animations.append(animation)
        self.size = start - self.size

    def __getitem__(self, item):
        return self.animations[item]

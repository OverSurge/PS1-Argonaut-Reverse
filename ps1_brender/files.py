import warnings
from typing import List, Union

from ps1_brender import *
from ps1_brender.data_models import AnimationData, ModelData, TextureData, VAGSoundData


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

        # In Harry Potter, the last 16 textures are empty (full of 00 bytes)
        for texture_id in range(
                self.n_textures - 16 if conf.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1) else self.n_textures):
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
        """Draws a single colored texture."""
        from PIL import Image

        if isinstance(texture, int):
            texture = self.textures[texture]
        elif not isinstance(texture, TextureData):
            raise TypeError

        debug_print = f"w:{texture.width}|h:{texture.height}|box:{texture.box}|row:{texture.n_row}|" \
                      f"col:{texture.n_column}|coords:{texture.coords}|"
        if texture.paletted:
            if texture.palette_256_colors:
                debug_print += f"palette256:{texture.palette_start}"
            else:
                debug_print += f"palette16:{texture.palette_start}"
        else:
            debug_print += "nopalette"
        logging.debug(debug_print)

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
        from PIL import Image
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
            color = (((color_bytes & 31) * 527 + 23) >> 6,
                     (((color_bytes & 992) >> 5) * 527 + 23) >> 6,
                     (((color_bytes & 31744) >> 10) * 527 + 23) >> 6)
            if color_bytes == 0 and ignore_transparency_bit is False:
                transparency = 0
            else:
                transparency = 255
            res.append(color + (transparency,))
        return tuple(res)

    # Debug functions

    def generate_greyscale_texture(self):
        """Debug use, do not use for textures extraction ! Draws the complete texture image in greyscale."""
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
        """Debug use, do not use for textures extraction ! Draws the complete texture image in greyscale."""
        from PIL import Image
        res: Image.Image = Image.new('RGBA', (self.image_size // 4, self.image_size))
        res.putdata(TextureFile.raw_as_true_color(self.raw_texture, 0, len(self.raw_texture)))
        return res


class SoundFile:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.size = start

        flags = data[start]
        self.has_ambient_tracks = bool(flags & 1)
        assert flags & 2 == 0  # Bit 1 is always unset
        self.has_common_sound_effects = bool(flags & 4)
        self.has_level_sound_effects = bool(flags & 8)
        assert self.has_ambient_tracks == bool(flags & 16)  # Bit 0 and 4 are identical

        logging.debug(f"Flags: {flags}|Level sound effects: {self.has_level_sound_effects}|"
                      f"Common sound effects: {self.has_common_sound_effects}|"
                      f"Ambient tracks: {self.has_ambient_tracks}")

        self.common_sound_effects = []  # Common sound effects can be found in the majority of the levels
        self.common_sound_effects_vags: List[VAGSoundData] = []
        self.ambient_tracks = []
        self.ambient_vags: List[VAGSoundData] = []

        self.level_sound_effect_groups = []
        self.level_sound_effects = []  # Level sound effects are specific to one or some level(s)
        self.dialogues_bgms = []  # BGM = BackGround Music

        sound_effects_count = int.from_bytes(data[start + 4:start + 8], 'little')
        logging.debug(f"sound effects count: {sound_effects_count}")
        start += 8

        # Common sound effects
        if self.has_common_sound_effects:
            self.common_sound_effects = [data[start + i * 20:start + (i + 1) * 20] for i in range(sound_effects_count)]
            logging.debug(
                "sound effect tracks:\n" + '\n'.join([track.hex(' ', 4) for track in self.common_sound_effects]))
            for track in self.common_sound_effects:
                assert track[8] < 2
                assert int.from_bytes(track[9:9], 'little') in (0x0101, 0)
                assert track[13:14] == b'\x00'
                assert track[14:16] == b'\x42\x00'
            start += sound_effects_count * 20

        # Ambient tracks
        if self.has_ambient_tracks:
            ambient_tracks_headers_size = int.from_bytes(data[start:start + 4], 'little')
            start += 4
            assert ambient_tracks_headers_size % 20 == 0
            ambient_tracks_count = ambient_tracks_headers_size // 20
            self.ambient_tracks = [data[start + i * 20:start + (i + 1) * 20] for i in range(ambient_tracks_count)]
            logging.debug(f"ambient_tracks_count:{ambient_tracks_count}\nambient tracks:\n" +
                          '\n'.join([track.hex(' ', 4) for track in self.ambient_tracks]))
            start += ambient_tracks_headers_size

        # Level sound effects groups
        self.idk1 = None
        self.idk2 = None
        if self.has_level_sound_effects:
            level_sound_effect_groups_count = int.from_bytes(data[start:start + 4], 'little')
            self.idk1 = data[start + 4:start + 8]
            self.idk2 = data[start + 8:start + 12]
            logging.debug(f"Level effects groups count: {level_sound_effect_groups_count}\n"
                          f"Unknown level effects values: {self.idk1.hex()}({int.from_bytes(self.idk1, 'little')})/"
                          f"{self.idk2.hex()}({int.from_bytes(self.idk2, 'little')})")
            ff_groups_count = int.from_bytes(data[start + 12:start + 16], 'little')
            start += 16

            self.level_sound_effect_groups = \
                [data[start + i * 16:start + (i + 1) * 16] for i in range(level_sound_effect_groups_count)]
            level_sound_effect_groups_counts = []
            logging.debug("Level effects groups headers:\n" +
                          '\n'.join([track.hex(' ', 4) for track in self.level_sound_effect_groups]))
            for track in self.level_sound_effect_groups:
                level_sound_effect_groups_counts.append(int.from_bytes(track[4:8], 'little'))

            level_sound_effect_groups_sum = \
                sum([int.from_bytes(x[12:16], 'little') for x in self.level_sound_effect_groups])
            level_sound_effects_count = sum(level_sound_effect_groups_counts)
            logging.debug(f"Level effects groups sizes sum: {level_sound_effect_groups_sum}\n"
                          f"Level effects count: {level_sound_effects_count}\nLevel effects headers (20d):")
            start += level_sound_effect_groups_count * 16

            # Level sound effects
            self.level_sound_effects: List[List[bytes]] = []
            level_sound_effects_sum = 0
            for count in level_sound_effect_groups_counts:
                group = []
                for i in range(count):
                    track = data[start:start + 20]
                    assert track[14:16] == b'\x42\x00'
                    group.append(track)
                    level_sound_effects_sum += int.from_bytes(track[16:20], 'little')
                    start += 20
                logging.debug('\n' + '\n'.join([track.hex(' ', 4) for track in group]))
                self.level_sound_effects.append(group)

            logging.debug(f"Level effects sizes sum: {level_sound_effects_sum}")
            assert level_sound_effect_groups_sum == level_sound_effects_sum
            start += ff_groups_count * 16

        # Dialogues & BGMs
        dialogues_count = int.from_bytes(data[start:start + 4], 'little')
        logging.debug(f"dialogues count: {dialogues_count}")
        start += 4
        if self.has_common_sound_effects:
            # Gap between level sound effects and dialogues/BGMs
            dne_gap = int.from_bytes(data[start:start + 4], 'little')
            assert (dne_gap != 0) == self.has_level_sound_effects
            start += 4

            self.dialogues_bgms = [data[start + i * 16:start + (i + 1) * 16] for i in range(dialogues_count)]
            logging.debug(f"DNE gap: {dne_gap} / {data[start:start + 4].hex()}\ndialogues headers:\n" + '\n'.join(
                [f"{i:>3}:{self.dialogues_bgms[i].hex(' ', 4)}" for i in range(len(self.dialogues_bgms))]))

            # TODO: Not always null
            # for track in self.dialogues_bgms:
            #     assert track[8:12] == b"\x00\x00\x00\x00"

            self.dialogues_tracks_sizes_sum = sum([int.from_bytes(x[12:16], 'little') for x in self.dialogues_bgms])
            logging.debug(f"dialogues tracks sum: {self.dialogues_tracks_sizes_sum}")
            start += 16 * dialogues_count

        effect_tracks_sizes_sum = sum(
            [int.from_bytes(x[16:20], 'little') for x in self.common_sound_effects]) if self.common_sound_effects else 0
        ambient_tracks_sizes_sum = sum(
            [int.from_bytes(x[16:20], 'little') for x in self.ambient_tracks]) if self.ambient_tracks else 0

        # Common sound effects audio data
        if self.has_common_sound_effects:
            declared_size = int.from_bytes(data[start:start + 4], 'little')
            assert declared_size == effect_tracks_sizes_sum
            start += 4
            for track in self.common_sound_effects:
                size = int.from_bytes(track[16:20], 'little')
                self.common_sound_effects_vags.append(VAGSoundData(
                    size, data[start:start + size], 1, int.from_bytes(track[0:4], 'little'), conf))
                start += size

        # Ambient tracks audio data
        if self.has_ambient_tracks:
            declared_size = int.from_bytes(data[start:start + 4], 'little')
            assert declared_size == ambient_tracks_sizes_sum
            start += 4
            for track in self.ambient_tracks:
                size = int.from_bytes(track[16:20], 'little')
                self.ambient_vags.append(VAGSoundData(
                    size, data[start:start + size], 1, int.from_bytes(track[0:4], 'little'), conf))
                start += size

        self.size = start - self.size


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

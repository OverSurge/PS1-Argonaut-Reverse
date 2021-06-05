from io import BufferedIOBase
from typing import Union, BinaryIO, Tuple

padding_size = 2048

XY = Tuple[int, int]

# Padding


def round_up_padding(n: int):
    return (n + padding_size - 1) & (-padding_size)


def pad_out_2048_bytes(bio: Union[BufferedIOBase, BinaryIO]):
    bio.write((round_up_padding(bio.tell()) - bio.tell()) * b'\x00')


def pad_in_2048_bytes(bio: Union[BufferedIOBase, BinaryIO]):
    bio.seek(round_up_padding(bio.tell()))


# Images

def parse_high_color(data_in: bytes, has_alpha: bool, legacy_alpha=False):  # TODO Legacy alpha (Croc 2)
    """Converts 15-bit high color raw bytes (see doc @Textures.md#15-bit-high-color)
    into a flattened list of RGB colors."""
    res = []
    for i in range(0, len(data_in), 2):
        color_bytes = int.from_bytes(data_in[i: i + 2], 'little')
        res.extend((((color_bytes & 0x1F) * 527 + 23) >> 6,
                    (((color_bytes & 0x3E0) >> 5) * 527 + 23) >> 6,
                    (((color_bytes & 0x7C00) >> 10) * 527 + 23) >> 6))
        if has_alpha:
            res.append(255 * (color_bytes != 0))
    return res


def parse_4bits_paletted(data: bytes):
    res = []
    for byte in data:
        pixel1 = byte & 15
        pixel2 = (byte & 240) >> 4
        res.extend((pixel1, pixel2))
    return res


def parse_palette(data: bytes, n_palette_colors: int, has_alpha: bool, legacy_alpha=False, start=0):
    return parse_high_color(data[start:start + 2 * n_palette_colors], has_alpha, legacy_alpha)

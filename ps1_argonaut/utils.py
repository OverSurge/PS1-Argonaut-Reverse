from io import BufferedIOBase
from typing import Union, BinaryIO

padding_size = 2048


def round_up_padding(n: int):
    return (n + padding_size - 1) & (-padding_size)


def pad_out_2048_bytes(bio: Union[BufferedIOBase, BinaryIO]):
    bio.write((round_up_padding(bio.tell()) - bio.tell()) * b'\x00')


def pad_in_2048_bytes(bio: Union[BufferedIOBase, BinaryIO]):
    bio.seek(round_up_padding(bio.tell()))

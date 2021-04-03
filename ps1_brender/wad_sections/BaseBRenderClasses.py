from io import BufferedIOBase
from typing import Tuple

from ps1_brender.configuration import Configuration, G
from ps1_brender.errors_warnings import SectionNameError, SectionSizeMismatch, UnsupportedReverse


class BaseBRenderClass:
    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        pass

    @classmethod
    def serialize(cls):
        pass


class BaseWADSection(BaseBRenderClass):
    supported_games: Tuple[G]
    section_content_description: str
    codename_str: str
    codename_bytes: bytes

    def __init__(self, size: int):
        self.size = size

    @classmethod
    def check_codename(cls, raw_data: BufferedIOBase):
        found_codename = raw_data.read(4)
        if found_codename != cls.codename_bytes:
            raise SectionNameError(raw_data.tell(), cls.codename_str, found_codename.decode('latin_1'))

    @classmethod
    def check_size(cls, expected_size: int, section_start: int, current_position: int):
        calculated_size = current_position - section_start
        if expected_size != calculated_size:
            raise SectionSizeMismatch(current_position, cls.codename_str, expected_size, calculated_size)

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        if conf.game not in cls.supported_games:
            raise UnsupportedReverse(cls.section_content_description)
        cls.check_codename(raw_data)
        return int.from_bytes(raw_data.read(4), 'little'), raw_data.tell()

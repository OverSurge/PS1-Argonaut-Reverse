from io import BufferedIOBase
from typing import Tuple

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.errors_warnings import SectionNameError, SectionSizeMismatch, UnsupportedParsing, \
    UnsupportedSerialization


class BaseDataClass:
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        pass

    def serialize(self, data_in: BufferedIOBase, conf: Configuration):
        pass


class BaseWADSection(BaseDataClass):
    supported_games: Tuple[G]
    section_content_description: str
    codename_str: str
    codename_bytes: bytes

    @classmethod
    def check_codename(cls, data_in: BufferedIOBase):
        found_codename = data_in.read(4)
        if found_codename != cls.codename_bytes:
            raise SectionNameError(data_in.tell(), cls.codename_str, found_codename.decode('latin_1'))

    @classmethod
    def check_size(cls, expected_size: int, section_start: int, current_position: int):
        calculated_size = current_position - section_start
        if expected_size != calculated_size:
            raise SectionSizeMismatch(current_position, cls.codename_str, expected_size, calculated_size)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        if conf.game not in cls.supported_games:
            raise UnsupportedParsing(cls.section_content_description)
        cls.check_codename(data_in)
        return int.from_bytes(data_in.read(4), 'little'), data_in.tell()

    def serialize(self, data_in: BufferedIOBase, conf: Configuration):
        if conf.game not in self.supported_games:
            raise UnsupportedSerialization(self.section_content_description)
        data_in.write(b'\x00\x00\x00\x00')  # Section's size
        return data_in.tell() - 4

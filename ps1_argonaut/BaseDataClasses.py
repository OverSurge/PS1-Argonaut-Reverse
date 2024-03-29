from io import BufferedIOBase

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.errors_warnings import (
    SectionNameError,
    SectionSizeMismatch,
    UnsupportedParsing,
    UnsupportedSerialization,
)


class BaseDataClass:
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        pass

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        pass


class BaseWADSection(BaseDataClass):
    supported_games: tuple[G, ...]
    section_content_description: str
    codename_str: str
    codename_bytes: bytes

    def __init__(self, data: bytes = None):
        if data is not None:
            self._data = data

    @classmethod
    def check_codename(cls, data_in: BufferedIOBase):
        found_codename = data_in.read(4)
        if found_codename != cls.codename_bytes:
            raise SectionNameError(
                data_in.tell(), cls.codename_str, found_codename.decode("latin_1")
            )

    @classmethod
    def check_size(cls, expected_size: int, section_start: int, current_position: int):
        calculated_size = current_position - section_start
        if expected_size != calculated_size:
            raise SectionSizeMismatch(
                current_position, cls.codename_str, expected_size, calculated_size
            )

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        if conf.game not in cls.supported_games:
            raise UnsupportedParsing(cls.section_content_description)
        cls.check_codename(data_in)
        return int.from_bytes(data_in.read(4), "little"), data_in.tell()

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        if conf.game not in self.supported_games:
            raise UnsupportedSerialization(self.section_content_description)
        data_out.write(self.codename_bytes)
        data_out.write(b"\x00\x00\x00\x00")  # Section's size
        return data_out.tell()

    @staticmethod
    def serialize_section_size(data_out: BufferedIOBase, start: int):
        end = data_out.tell()
        size = end - start
        data_out.seek(start - 4)
        data_out.write(size.to_bytes(4, "little"))
        data_out.seek(end)

    @classmethod
    def fallback_parse_data(cls, data_in: BufferedIOBase):
        start = data_in.tell()
        codename = data_in.read(4)
        size = data_in.read(4)
        data = codename + size + data_in.read(int.from_bytes(size, "little"))
        data_in.seek(start)
        return data

    @classmethod
    def fallback_parse(cls, data_in: BufferedIOBase):
        return cls(cls.fallback_parse_data(data_in))

    def fallback_serialize(self, data_out: BufferedIOBase):
        data_out.write(self._data)

from io import BufferedIOBase

from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.BaseDataClasses import BaseDataClass


class StrategyData(BaseDataClass):
    def __init__(self, data: bytes):
        self.data = data

    @property
    def size(self):
        return len(self.data)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        super().parse(data_in, conf)
        size = 4 * int.from_bytes(data_in.read(4), 'little')
        return cls(data_in.read(size))

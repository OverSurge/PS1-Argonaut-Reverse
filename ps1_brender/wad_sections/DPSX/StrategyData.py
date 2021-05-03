from io import BufferedIOBase

from ps1_brender.configuration import Configuration
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass


class StrategyData(BaseBRenderClass):
    def __init__(self, data: bytes):
        self.data = data

    @property
    def size(self):
        return len(self.data)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        super().parse(data_in, conf)
        size = 4 * int.from_bytes(data_in.read(4), 'little')
        return cls(data_in.read(size))

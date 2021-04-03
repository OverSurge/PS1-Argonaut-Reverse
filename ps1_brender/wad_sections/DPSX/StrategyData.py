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
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        super().parse(raw_data, conf)
        size = 4 * int.from_bytes(raw_data.read(4), 'little')
        return cls(raw_data.read(size))

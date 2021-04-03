from io import BufferedIOBase, SEEK_CUR
from typing import List

from ps1_brender.configuration import Configuration, G
from ps1_brender.wad_sections.BaseBRenderClasses import BaseWADSection


class PORTSection(BaseWADSection):
    codename_str = 'TROP'
    codename_bytes = b'TROP'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "chunk zone ids"

    def __init__(self, size: int, idk1: List[bytes], chunks_zones: List[List[int]]):
        super().__init__(size)
        self.idk1 = idk1
        self.chunks_zones = chunks_zones

    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        size, start = super().parse(raw_data, conf)
        n_zones = int.from_bytes(raw_data.read(4), 'little')
        n_idk1 = int.from_bytes(raw_data.read(4), 'little')
        idk1 = [raw_data.read(32) for _ in range(n_idk1)]
        n_chunks_per_zone = []
        for _ in range(n_zones):
            raw_data.seek(2, SEEK_CUR)
            n_chunks_per_zone.append(raw_data.read(1)[0])
            raw_data.seek(9, SEEK_CUR)
        chunks_zones = []
        for n_chunks in n_chunks_per_zone:
            chunks_zones.append([int.from_bytes(raw_data.read(2), 'little') for _ in range(n_chunks)])

        cls.check_size(size, start, raw_data.tell())
        return cls(size, idk1, chunks_zones)

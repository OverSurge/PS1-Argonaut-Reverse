from io import BufferedIOBase, SEEK_CUR
from typing import List

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.wad_sections.BaseDataClasses import BaseWADSection


class PORTSection(BaseWADSection):
    codename_str = 'TROP'
    codename_bytes = b'TROP'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "chunk zone ids"

    def __init__(self, idk1: List[bytes], chunks_zones: List[List[int]], fallback_data: bytes = None):
        super().__init__(fallback_data)
        self.idk1 = idk1
        self.chunks_zones = chunks_zones

    @property
    def size(self) -> int:
        return 8 + 32 * len(self.idk1) + 12 * self.n_chunks_zones + 2 * self.n_chunks

    @property
    def n_chunks_zones(self):
        return len(self.chunks_zones)

    @property
    def n_chunks(self):
        return sum(len(zone) for zone in self.chunks_zones)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        fallback_data = cls.fallback_parse_data(data_in)
        size, start = super().parse(data_in, conf)
        n_zones = int.from_bytes(data_in.read(4), 'little')
        n_idk1 = int.from_bytes(data_in.read(4), 'little')
        idk1 = [data_in.read(32) for _ in range(n_idk1)]
        n_chunks_per_zone = []
        for _ in range(n_zones):
            data_in.seek(2, SEEK_CUR)
            n_chunks_per_zone.append(data_in.read(1)[0])
            data_in.seek(9, SEEK_CUR)
        chunks_zones = []
        for n_chunks in n_chunks_per_zone:
            chunks_zones.append([int.from_bytes(data_in.read(2), 'little') for _ in range(n_chunks)])

        cls.check_size(size, start, data_in.tell())
        return cls(idk1, chunks_zones, fallback_data)

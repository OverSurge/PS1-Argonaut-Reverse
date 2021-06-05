from enum import IntEnum
from io import StringIO
from typing import List, Iterable

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.wad_sections.DPSX.Model3DData import LevelGeom3DData


class ChunkRotation(IntEnum):
    TOP = 0
    RIGHT = 4
    BOTTOM = 8
    LEFT = 12


class SubChunk(BaseDataClass):
    def __init__(self, model_3d_data: LevelGeom3DData, height: int, rotation: ChunkRotation):
        self.model_3d_data = model_3d_data
        self.height = height
        self.rotation = rotation


class ChunkHolder(List[SubChunk], BaseDataClass):
    def __init__(self, sub_chunks: List[SubChunk] = None, zone_id: int = None, fvw_data: bytes = None):
        super().__init__(sub_chunks if sub_chunks is not None else [])
        self.zone_id = zone_id
        self.fvw_data = fvw_data


class ChunksMatrix(List[ChunkHolder]):
    def __init__(self, chunks_holders: Iterable[ChunkHolder], chunks_models: Iterable[LevelGeom3DData], n_rows: int,
                 n_columns: int, has_zone_ids: bool):
        super().__init__(chunks_holders)
        self.n_rows = n_rows
        self.n_columns = n_columns
        self.chunks_models = list(chunks_models)
        self.max_zone_id = max(
            chunk_holder.zone_id for chunk_holder in chunks_holders) if chunks_holders and has_zone_ids else None

    @property
    def n_filled_chunks(self):
        return sum(len(chunk) != 0 for chunk in self)

    def __str__(self):
        return self.chunks_visual_map()

    def chunks_visual_map(self):
        return '\n'.join([' '.join(['█' if self[x * self.n_columns + y] else '░'
                                    for y in range(self.n_columns)]) for x in range(self.n_rows)])

    def chunks_visual_ids(self):
        return '\n'.join([' '.join(
            [str(x * self.n_columns + y).ljust(4) if self[x * self.n_columns + y] else '░░░░'
             for y in range(self.n_columns)]) for x in range(self.n_rows)])

    def subchunks_visual_ids(self):
        subchunk_id = 0
        res = StringIO()
        for x in range(self.n_rows):
            for y in range(self.n_columns):
                if y != 0:
                    res.write(' ')
                subchunks = self[x * self.n_columns + y]
                if subchunks:
                    res.write(str(subchunk_id).ljust(4))
                    subchunk_id += len(subchunks)
                else:
                    res.write('░░░░')
            res.write('\n')
        return res.getvalue()

    def chunks_visual_zone_ids(self):
        if self.max_zone_id is None:
            return "There are no zone ids in this level."
        res = StringIO()
        for x in range(self.n_rows):
            for y in range(self.n_columns):
                if y != 0:
                    res.write(' ')
                zone_id = self[x * self.n_columns + y].zone_id
                if zone_id is not None and zone_id != self.max_zone_id:
                    res.write(str(zone_id).ljust(3))
                else:
                    res.write('░░░')
            res.write('\n')
        return res.getvalue()

    def x_z_coords(self, chunk_id):
        # Chunks are 4096-large, so +2048 is needed to point to the chunk's center
        return 4096 * (chunk_id % self.n_columns) + 2048, 4096 * (chunk_id // self.n_columns) + 2048

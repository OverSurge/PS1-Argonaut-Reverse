from enum import IntEnum
from io import StringIO
from typing import List

from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.DPSX.Model3DData import LevelGeom3DData


class ChunkRotation(IntEnum):
    TOP = 0
    RIGHT = 4
    BOTTOM = 8
    LEFT = 12


class SubChunk(BaseBRenderClass):
    def __init__(self, model_3d_data: LevelGeom3DData, height: int, rotation: ChunkRotation):
        self.model_3d_data = model_3d_data
        self.height = height
        self.rotation = rotation


class ChunkHolder(BaseBRenderClass):
    def __init__(self, sub_chunks: List[SubChunk] = None, zone_id: int = None, fvw_data: bytes = None):
        self.sub_chunks = sub_chunks if sub_chunks is not None else []
        self.zone_id = zone_id
        self.fvw_data = fvw_data


class ChunksMatrix:
    def __init__(self, n_rows: int, n_columns: int, chunks_models: List[LevelGeom3DData],
                 chunks_holders: List[ChunkHolder], has_zone_ids: bool):
        self.n_rows = n_rows
        self.n_columns = n_columns
        self.chunks_models = chunks_models
        self.chunks_holders = chunks_holders
        self.max_zone_id = max(chunk_holder.zone_id for chunk_holder in chunks_holders) if has_zone_ids else None

    @property
    def n_filled_chunks(self):
        return sum(len(x.sub_chunks) != 0 for x in self.chunks_holders)

    def __str__(self):
        return self.chunks_visual_map()

    def chunks_visual_map(self):
        return '\n'.join([' '.join(['█' if self.chunks_holders[x * self.n_columns + y].sub_chunks else '░'
                                    for y in range(self.n_columns)]) for x in range(self.n_rows)])

    def chunks_visual_zone_ids(self):
        if self.max_zone_id is None:
            return "There are no zone ids in this level."
        res = StringIO()
        for x in range(self.n_rows):
            for y in range(self.n_columns):
                if y != 0:
                    res.write(' ')
                zone_id = self.chunks_holders[x * self.n_columns + y].zone_id
                if zone_id is not None and zone_id != self.max_zone_id:
                    res.write(str(zone_id).ljust(3))
                else:
                    res.write('░░░')
            res.write('\n')
        return res.getvalue()

    def x_z_coords(self, chunk_id):
        # Chunks are 4096-large, so +2048 is needed to point to the chunk's center
        return 4096 * (chunk_id % self.n_columns) + 2048, 4096 * (chunk_id // self.n_columns) + 2048

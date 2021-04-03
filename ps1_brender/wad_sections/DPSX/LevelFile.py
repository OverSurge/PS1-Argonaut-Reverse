from io import BufferedIOBase, SEEK_CUR
from typing import List, Optional, Union

from ps1_brender.configuration import Configuration, G
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.DPSX.ChunkClasses import ChunkHolder, ChunkRotation, ChunksMatrix, SubChunk
from ps1_brender.wad_sections.DPSX.Model3DData import LevelGeom3DData
from ps1_brender.wad_sections.DPSX.Model3DHeader import Model3DHeader


class LevelFile(BaseBRenderClass):
    def __init__(self, chunks_matrix: ChunksMatrix):
        self.chunks_matrix = chunks_matrix

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        super().parse(raw_data, conf)
        n_chunk_models = int.from_bytes(raw_data.read(4), 'little')
        _chunk_model_headers = [Model3DHeader.parse(raw_data, conf) for _ in range(n_chunk_models)]
        chunk_models = [LevelGeom3DData.parse(raw_data, conf, _chunk_model_headers[i]) for i in range(n_chunk_models)]
        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            raw_data.seek(8, SEEK_CUR)
        n_sub_chunks = int.from_bytes(raw_data.read(4), 'little')

        n_idk1 = int.from_bytes(raw_data.read(4), 'little')
        raw_data.seek(4 * n_idk1, SEEK_CUR)
        assert n_sub_chunks == int.from_bytes(raw_data.read(4), 'little')
        n_actors_instances = int.from_bytes(raw_data.read(2), 'little')
        raw_data.seek(6 if conf.game != G.CROC_2_DEMO_PS1_DUMMY else 2, SEEK_CUR)
        n_total_chunks = int.from_bytes(raw_data.read(4), 'little')
        n_chunk_columns = int.from_bytes(raw_data.read(4), 'little')
        n_chunk_rows = int.from_bytes(raw_data.read(4), 'little')
        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            n_lighting_headers = int.from_bytes(raw_data.read(2), 'little')
            n_add_sub_chunks_lighting = int.from_bytes(raw_data.read(2), 'little')
            idk3 = int.from_bytes(raw_data.read(4), 'little')
        else:
            n_lighting_headers, n_add_sub_chunks_lighting = None, None
        n_idk4 = int.from_bytes(raw_data.read(4), 'little')
        raw_data.seek(116 if conf.game != G.CROC_2_DEMO_PS1_DUMMY else 80, SEEK_CUR)

        _chunks_matrix: List[Union[List[int], Optional[int]]] = \
            [int.from_bytes(raw_data.read(4), 'little') for _ in range(n_total_chunks)]
        _sub_chunks_height = {}
        chunks_info_start_offset = raw_data.tell()

        def parse_chunks_info(offset: int, chunks_ids_list: List[int]):
            raw_data.seek(chunks_info_start_offset + offset)
            chunks_ids_list.append(int.from_bytes(raw_data.read(4), 'little'))
            linked_chunk_offset = int.from_bytes(raw_data.read(4), 'little')
            if linked_chunk_offset != 0xFFFFFFFF:
                return parse_chunks_info(linked_chunk_offset, chunks_ids_list)
            else:
                return chunks_ids_list

        for i in range(n_chunk_rows):
            for j in range(n_chunk_columns):
                index = i * n_chunk_columns + j
                chunk_info_offset = _chunks_matrix[index]
                if chunk_info_offset != 0xFFFFFFFF:
                    sub_chunk_ids = parse_chunks_info(chunk_info_offset, [])
                    _chunks_matrix[index] = sub_chunk_ids
                    for sub_chunk_id in sub_chunk_ids:
                        _sub_chunks_height[sub_chunk_id] = (i, j)
                else:
                    _chunks_matrix[index] = None

        raw_data.seek(chunks_info_start_offset + 8 * n_sub_chunks)
        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            header256bytes = raw_data.read(256)
            n_zone_ids = int.from_bytes(raw_data.read(4), 'little')
            zone_ids = [int.from_bytes(raw_data.read(4), 'little') for _ in range(n_zone_ids)]
            assert n_zone_ids == n_total_chunks

            if raw_data.read(4) == b'fvw\x00':
                fvw_data = [raw_data.read(2) for _ in range(n_total_chunks)]
            else:
                fvw_data = None
                raw_data.seek(-4, SEEK_CUR)
        else:
            zone_ids = None
            fvw_data = None

        _sub_chunks_rotation = {}
        for i in range(n_sub_chunks):
            rotation = int.from_bytes(raw_data.read(4), 'big')
            assert rotation in (0, 4, 8, 12)
            _sub_chunks_rotation[i] = ChunkRotation(rotation)
            assert raw_data.read(4) == b'\x00\x00\x00\x00'
            x = int.from_bytes(raw_data.read(4), 'little')
            y = int.from_bytes(raw_data.read(4), 'little')
            z = int.from_bytes(raw_data.read(4), 'little')
            assert raw_data.read(4) == b'\x00\x00\x00\x00'
            assert x == 2048 + 4096 * _sub_chunks_height[i][1]  # Chunks are 4096-large, so +2048 for the chunk's center
            assert z == 2048 + 4096 * _sub_chunks_height[i][0]
            _sub_chunks_height[i] = y
        chunks_models_mapping = [int.from_bytes(raw_data.read(4), 'little') for _ in range(n_sub_chunks)]

        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            lighting_headers = [raw_data.read(84) for _ in range(n_lighting_headers)]

        idk_4 = [raw_data.read(36) for _ in range(n_idk4)]

        for i in range(n_actors_instances):
            raw_data.seek(24, SEEK_CUR)
            actor_offset = int.from_bytes(raw_data.read(4), 'little')
            raw_data.seek(32, SEEK_CUR)
            actor_sound_level = int.from_bytes(raw_data.read(4), 'little')

        if conf.game not in (G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY):
            add_models_mapping = []
            for i in range(n_add_sub_chunks_lighting):
                raw_data.seek(16, SEEK_CUR)
                add_models_mapping.append(int.from_bytes(raw_data.read(4), 'little'))
                raw_data.seek(4, SEEK_CUR)

            n_idk2 = int.from_bytes(raw_data.read(4), 'little')
            raw_data.seek(32 * n_idk2, SEEK_CUR)  # TODO Reverse this
        else:
            add_models_mapping = None
            raw_data.seek(32 * n_sub_chunks, SEEK_CUR)  # Two different 32-bytes long structures
            raw_data.seek(32 * n_sub_chunks, SEEK_CUR)
            raw_data.seek(32 if conf.game == G.CROC_2_DEMO_PS1 else 92, SEEK_CUR)

        if conf.game == G.CROC_2_PS1:
            raw_data.seek(30732, SEEK_CUR)
        elif conf.game != G.CROC_2_DEMO_PS1_DUMMY and n_sub_chunks != 0:
            sub_chunks_n_lighting = [int.from_bytes(raw_data.read(4), 'little') for _ in range(n_sub_chunks)]
            sub_chunks_n_add_lighting = [int.from_bytes(raw_data.read(4), 'little') for _ in
                                         range(n_add_sub_chunks_lighting)]
            for model_id in range(n_sub_chunks):
                for i in range(sub_chunks_n_lighting[model_id]):
                    size = 4 * chunk_models[chunks_models_mapping[model_id]].n_vertices
                    raw_data.seek(size, SEEK_CUR)
            for model_id in range(n_add_sub_chunks_lighting):
                for i in range(sub_chunks_n_add_lighting[model_id]):
                    size = 4 * chunk_models[add_models_mapping[model_id]].n_vertices
                    raw_data.seek(size, SEEK_CUR)
            if conf.game != G.CROC_2_DEMO_PS1:  # Not present in Croc 2 Demo Dummy
                idk_size = int.from_bytes(raw_data.read(4), 'little')
                if idk_size != 0:
                    raw_data.seek(4 + idk_size, SEEK_CUR)
                else:
                    raw_data.seek(-4, SEEK_CUR)
                n_idk3 = int.from_bytes(raw_data.read(4), 'little')
                if n_idk3 == 0:
                    raw_data.seek(-4, SEEK_CUR)
                idk3 = [int.from_bytes(raw_data.read(40), 'little') for _ in range(n_idk3)]
            raw_data.seek(12, SEEK_CUR)

        chunks_holders = []
        for i in range(n_total_chunks):
            if _chunks_matrix[i] is not None:
                sub_chunks = [
                    SubChunk(chunk_models[chunks_models_mapping[sub_chunk_id]], _sub_chunks_height[sub_chunk_id],
                             _sub_chunks_rotation[sub_chunk_id]) for sub_chunk_id in _chunks_matrix[i]]
                if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
                    chunks_holders.append(
                        ChunkHolder(sub_chunks, zone_ids[i], fvw_data[i] if fvw_data else None))
                else:
                    chunks_holders.append(ChunkHolder(sub_chunks))
            else:
                chunks_holders.append(
                    ChunkHolder(zone_id=zone_ids[i], fvw_data=fvw_data[i] if fvw_data else None)
                    if conf.game != G.CROC_2_DEMO_PS1_DUMMY else ChunkHolder())

        return cls(ChunksMatrix(n_chunk_rows, n_chunk_columns, chunk_models, chunks_holders, zone_ids is not None))

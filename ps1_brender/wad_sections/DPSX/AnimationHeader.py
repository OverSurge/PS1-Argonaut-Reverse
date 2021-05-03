import warnings
from io import BufferedIOBase, SEEK_CUR
from typing import List

from ps1_brender.configuration import Configuration, G
from ps1_brender.errors_warnings import AnimationsWarning
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass


class AnimationHeader(BaseBRenderClass):
    base_frame_data_size = 4
    inter_frames_header_size = 8

    def __init__(self, n_total_frames: int, n_stored_frames: int, n_vertex_groups: int, n_flags: int,
                 has_additional_data: bool, flags: List[bytes], old_animation_format: bool, n_inter_frames=0):
        self.n_total_frames = n_total_frames
        self.n_stored_frames = n_stored_frames
        self.n_vertices_groups = n_vertex_groups
        self.n_flags = n_flags
        self.has_additional_data = has_additional_data
        self.flags = flags
        self.old_animation_format = old_animation_format
        self.n_inter_frames = n_inter_frames
        self.sub_frame_size = 24 if old_animation_format else 16

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        super().parse(data_in, conf)
        n_flags: int = int.from_bytes(data_in.read(4), 'little')
        data_in.seek(4, SEEK_CUR)
        n_total_frames: int = int.from_bytes(data_in.read(4), 'little')
        has_additional_frame_data_value = int.from_bytes(data_in.read(4), 'little')
        has_additional_data: bool = has_additional_frame_data_value == 0
        n_stored_frames = 0
        if conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY):
            n_inter_frames = int.from_bytes(data_in.read(4), 'little')
            if n_inter_frames != 0:
                n_stored_frames = n_total_frames
            data_in.seek(4, SEEK_CUR)
        else:  # Harry Potter 1 & 2
            data_in.seek(8, SEEK_CUR)
            n_inter_frames = 0
        n_vertex_groups: int = int.from_bytes(data_in.read(4), 'little')
        data_in.seek(4, SEEK_CUR)

        if conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1):
            n_stored_frames = int.from_bytes(data_in.read(4), 'little')
            data_in.seek(12, SEEK_CUR)

        flags = [data_in.read(4) for _ in range(n_flags)]
        if has_additional_data:
            data_in.seek(8 * n_total_frames, SEEK_CUR)
        data_in.seek(4 * n_total_frames, SEEK_CUR)  # Total frames info
        data_in.seek(n_inter_frames * cls.inter_frames_header_size, SEEK_CUR)  # Inter-frames header
        if conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1) or n_inter_frames != 0:
            data_in.seek(4 * n_stored_frames, SEEK_CUR)  # Stored frames info

        if n_stored_frames == 0 or n_inter_frames != 0:  # Rotation matrices
            old_animation_format = True
            n_stored_frames = n_total_frames
        else:  # Unit quaternions
            old_animation_format = False

        if n_total_frames > 500 or n_total_frames == 0:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much frames in animation (or no frame): {n_total_frames} frames."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the textures format.")
            else:
                raise AnimationsWarning(data_in.tell(), n_total_frames)
        return cls(n_total_frames, n_stored_frames, n_vertex_groups, n_flags, has_additional_data, flags,
                   old_animation_format, n_inter_frames)

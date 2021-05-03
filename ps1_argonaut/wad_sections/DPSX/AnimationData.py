import math
from io import BufferedIOBase, SEEK_CUR
from typing import List

import numpy as np
from pyquaternion import Quaternion

from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.BaseDataClasses import BaseDataClass
from ps1_argonaut.wad_sections.DPSX.AnimationHeader import AnimationHeader


class AnimationData(BaseDataClass):
    def __init__(self, header: AnimationHeader, frames: List[List[np.ndarray]]):
        self.frames = frames
        self.header = header

    def __getitem__(self, item):
        return self.frames[item]

    @property
    def n_vertices_groups(self):
        return self.header.n_vertices_groups

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        super().parse(data_in, conf)
        header = AnimationHeader.parse(data_in, conf)

        if header.n_total_frames == header.n_stored_frames:
            frame_indexes = list(range(header.n_total_frames))
        else:
            frame_indexes = []

        inter_frames_size = 4 * math.ceil((header.n_inter_frames * 2) / 4)
        frames = []

        for frame_id in range(header.n_stored_frames):
            last: List[np.ndarray] = []
            for group_id in range(header.n_vertices_groups):
                sub_frame = [int.from_bytes(data_in.read(2), 'little', signed=True) for _ in
                             range(header.sub_frame_size // 2)]
                if header.old_animation_format:
                    matrix = np.divide((sub_frame[:3], sub_frame[3:6], sub_frame[6:9]), 4096).T  # Need to be reversed
                    translation = (sub_frame[9:10], sub_frame[10:11], sub_frame[11:12])
                else:
                    matrix = Quaternion(sub_frame[0], sub_frame[1], sub_frame[2], sub_frame[3]).rotation_matrix
                    translation = (sub_frame[4:5], sub_frame[5:6], sub_frame[6:7])
                    if header.n_total_frames != header.n_stored_frames:
                        frame_indexes.append(sub_frame[7])
                last.append(np.append(matrix, translation, axis=1))
            if header.n_inter_frames != 0 and frame_id != header.n_stored_frames - 1:
                data_in.seek(inter_frames_size, SEEK_CUR)
            frames.append(last)
        return cls(header, frames)

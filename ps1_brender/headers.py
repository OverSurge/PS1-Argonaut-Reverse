import warnings

from ps1_brender import *


class ModelHeader:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.n_vertices: int = int.from_bytes(data[start + 72: start + 76], 'little')
        self.n_faces: int = int.from_bytes(data[start + 84:start + 88], 'little')

        if self.n_vertices > 1000 or self.n_faces > 1000:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much vertices or faces ({self.n_vertices} vertices, {self.n_faces} faces)."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the models format.")
            else:
                raise Models3DWarning(start, self.n_vertices, self.n_faces)

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY):
            self.total_header_size: int = 100
        elif conf.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            self.total_header_size: int = 104
        else:
            raise NotImplementedError
        self.n_extended_data_frames = int.from_bytes(data[start + 92:start + 94], 'little') + int.from_bytes(
            data[start + 94:start + 96], 'little') + int.from_bytes(data[start + 96:start + 98], 'little')


class AnimationHeader:
    base_frame_data_size = 4
    interframe_header_size = 8

    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.n_total_frames: int = int.from_bytes(data[start + 8: start + 12], 'little')
        self.n_stored_frames: int = 0
        self.n_vertex_groups: int = int.from_bytes(data[start + 24:start + 28], 'little')
        self.flags_count: int = int.from_bytes(data[start: start + 4], 'little')
        has_additional_frame_data_value = int.from_bytes(data[start + 12: start + 16], 'little')
        self.has_additional_data: bool = has_additional_frame_data_value == 0
        self.n_interframe = 0

        if conf.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            self.n_stored_frames = int.from_bytes(data[start + 32: start + 36], 'little')
            base_header_size = 48
            flags_size = 4
            additional_frame_data_size = 8
        elif conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY,):
            base_header_size = 32
            flags_size = 4
            additional_frame_data_size = 8
            self.n_interframe = int.from_bytes(data[start + 16: start + 20], 'little')
            if self.n_interframe != 0:
                self.n_stored_frames = self.n_total_frames
        else:
            raise NotImplementedError

        self.flags: bytes = data[start + base_header_size:start + base_header_size + 4 * self.flags_count]

        self.total_header_size: int = \
            base_header_size + self.flags_count * flags_size + \
            self.has_additional_data * additional_frame_data_size * self.n_total_frames + \
            AnimationHeader.base_frame_data_size * self.n_total_frames + \
            AnimationHeader.base_frame_data_size * self.n_stored_frames + \
            self.n_interframe * AnimationHeader.interframe_header_size

        if self.n_stored_frames == 0 or self.n_interframe != 0:  # Rotation matrices
            self.old_animation_format = True
            self.n_stored_frames = self.n_total_frames
        else:  # Unit quaternions
            self.old_animation_format = False

        if self.n_total_frames > 500 or self.n_total_frames == 0:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much frames in animation (or no frame): {self.n_total_frames} frames."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the textures format.")
            else:
                raise AnimationsWarning(start, self.n_total_frames)

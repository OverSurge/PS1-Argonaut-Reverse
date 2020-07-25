from ctypes import c_int32
from typing import List

import numpy as np
from pyquaternion import Quaternion

from ps1_brender import *
from ps1_brender.headers import AnimationHeader, ModelHeader


class TextureData:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            coords = [(int.from_bytes(data[start: start + 1], 'little'),
                       int.from_bytes(data[start + 1: start + 2], 'little')),
                      (int.from_bytes(data[start + 4: start + 5], 'little'),
                       int.from_bytes(data[start + 5: start + 6], 'little')),
                      (int.from_bytes(data[start + 8: start + 9], 'little'),
                       int.from_bytes(data[start + 9: start + 10], 'little')),
                      (int.from_bytes(data[start + 10: start + 11], 'little'),
                       int.from_bytes(data[start + 11: start + 12], 'little'))]

            # TODO: On Croc 2 Demo dummy WADs, the UV order is 1 0 3 2 instead of 0 1 2 3 (normal) or 2 3 0 1 (reversed)
            if coords[3][0] > coords[2][0]:
                flipped = True
            else:
                flipped = False

            flags = int.from_bytes(data[start + 6:start + 8], 'little')
            self.n_row = ((flags & 4) >> 1) + ((flags & 16) >> 4)
            self.n_column = flags & 3

            self.paletted: bool = (flags & 256) == 0
            if self.paletted:
                self.palette_256_colors = (flags & 128) != 0
                palette_info = int.from_bytes(data[start + 2:start + 4], 'little')
                self.palette_start = ((palette_info & 65472) << 3) + ((palette_info & 15) << 5)

            # Correction Ratio, needed for non-4bit/pixel textures to be correctly positioned
            cr = 4 if not self.paletted else 2 if self.palette_256_colors else 1
            # The top-left x coordinate of the 256-colors or true color textures needs to be corrected
            x_correction = coords[3][0] * cr - coords[3][0] if not flipped else coords[2][0] * cr - coords[2][0]
            for i in range(4):
                coords[i] = \
                    (coords[i][0] + x_correction + self.n_column * 256, coords[i][1] + self.n_row * 256)

            for i in range(4):
                coords[i] = (2 * np.math.ceil(coords[i][0] / 2), 2 * np.math.ceil(coords[i][1] / 2))
            self.coords = tuple(coords)

            self.box = (self.coords[3][0], self.coords[3][1], self.coords[0][0], self.coords[0][1]) if not flipped \
                else (self.coords[2][0], self.coords[2][1], self.coords[1][0], self.coords[1][1])
            self.width = self.box[2] - self.box[0]
            self.height = self.box[3] - self.box[1]
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)


class VAGSoundData:
    constants = ((0.0, 0.0),
                 (60.0 / 64.0, 0.0),
                 (115.0 / 64.0, -52.0 / 64.0),
                 (98.0 / 64.0, -55.0 / 64.0),
                 (122.0 / 64.0, -60.0 / 64.0))

    def __init__(self, size: int, data: bytes, channels: int, sampling_rate: int, conf: Configuration):
        if channels != 1 and channels != 2:
            raise ValueError
        self.size: int = size
        self.data: bytes = data
        self.channels_count: int = channels
        self.sampling_rate: int = sampling_rate
        self.conf = conf

    def to_vag(self, with_headers: bool = True):
        header_size = 0 if with_headers else 48
        header = b"VAGp\x00\x00\x00\x00\x00\x00\x00\x00" + \
                 (self.size // self.channels_count).to_bytes(4, 'big') + self.sampling_rate.to_bytes(4, 'big') + \
                 b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00OverSurgeBRender" if with_headers else None
        if self.channels_count == 1:
            return (header + self.data,) if with_headers else (self.data,)
        else:
            res = bytearray(header_size + self.size // 2)
            if with_headers:
                res[:48] = header
            res2 = res.copy()
            for i in range(0, self.size, 2048):
                i2 = header_size + i // 2
                res[i2:i2 + 1024] = self.data[i:i + 1024]
                res2[i2:i2 + 1024] = self.data[i + 1024:i + 2048]
            return res, res2

    def to_wav(self, filename: str):
        """supports stereo export in a single file, unlike to_vag()."""
        vag = self.to_vag(False)

        byte_rate = self.sampling_rate * self.channels_count * 2
        block_align = self.channels_count * 2
        audio_data_size = (self.size * 7) // 2  # VAG -> WAV has a 3.5 size ratio

        id3_tags = b"TALB" + (len(self.conf.game.title) + 5).to_bytes(4, 'big') + b"\x00\x00\x00" + \
                   (self.conf.game.title + ' OST').encode('ASCII') + \
                   b"TIT2" + (len(filename) + 1).to_bytes(4, 'big') + b"\x00\x00\x00" + \
                   filename.encode('ASCII') + b"COMM\x00\x00\x00\x55\x00\x00\x00XXX\x00" + wav_header + \
                   b"TCON\x00\x00\x00\x05\x00\x00\x00GameTDRC\x00\x00\x00\x05\x00\x00\x00" + \
                   str(self.conf.game.release_year).encode('ASCII')
        # The ID3 header size uses 7 bits/byte, see https://id3.org/id3v2.3.0#ID3v2_header for more
        id3_tags_size = (len(id3_tags) & 127) + ((len(id3_tags) & 16256) << 1)
        id3 = b"ID3\x03\x00\x00" + id3_tags_size.to_bytes(4, 'big') + id3_tags
        footer = b"ID3 " + len(id3).to_bytes(4, 'little') + id3

        total_wav_size = 44 + audio_data_size + len(footer)
        header = b"RIFF" + (total_wav_size - 8).to_bytes(4, 'little') + b"WAVEfmt \x10\x00\x00\x00\x01\x00" + \
                 self.channels_count.to_bytes(2, 'little') + self.sampling_rate.to_bytes(4, 'little') + \
                 byte_rate.to_bytes(4, 'little') + block_align.to_bytes(2, 'little') + b"\x10\x00data" + \
                 audio_data_size.to_bytes(4, 'little')

        res = bytearray(total_wav_size)
        res[:44] = header
        res[-len(footer):] = footer
        if self.channels_count == 1:
            channels = None
        else:
            channels = (bytearray(audio_data_size // 2), bytearray(audio_data_size // 2))

        # Based on VAG-Depack 0.1 by bITmASTER
        for c in range(self.channels_count):
            s_1 = 0.0
            s_2 = 0.0
            samples = [0.0] * 28
            for i in range(16, self.size // self.channels_count, 16):
                predict_nr = vag[c][i]
                shift_factor = predict_nr & 0xF
                predict_nr >>= 4
                flags = vag[c][i + 1]
                if flags == 7:
                    break
                for j in range(0, 28, 2):
                    d = vag[c][i + 2 + j // 2]
                    s = (d & 0xF) << 12
                    if s & 0x8000:
                        s = c_int32(s | 0xFFFF0000).value
                    samples[j] = s >> shift_factor
                    s = (d & 0xF0) << 8
                    if s & 0x8000:
                        s = c_int32(s | 0xFFFF0000).value
                    samples[j + 1] = float(s >> shift_factor)
                for j in range(28):
                    samples[j] += s_1 * VAGSoundData.constants[predict_nr][0] + s_2 * \
                                  VAGSoundData.constants[predict_nr][1]
                    s_2 = s_1
                    s_1 = samples[j]
                    d = int(samples[j] + 0.5)
                    wav_pos = (i * 7) // 2 + j * 2
                    if self.channels_count == 1:
                        res[44 + wav_pos] = d & 0xFF
                        res[45 + wav_pos] = (d >> 8) & 0xFF
                    else:
                        channels[c][wav_pos] = d & 0xFF
                        channels[c][wav_pos + 1] = (d >> 8) & 0xFF
                if flags == 1:
                    break
        if self.channels_count == 2:
            for i in range(0, audio_data_size // 2, 2):
                res[44 + 2 * i:46 + 2 * i] = channels[0][i:i + 2]
                res[46 + 2 * i:48 + 2 * i] = channels[1][i:i + 2]
        return res


class AnimationData:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.header = AnimationHeader(data, start, conf)
        self.n_vertex_groups = self.header.n_vertex_groups

        first_bytes = data[start:start + self.header.total_header_size].hex(' ', 4)
        logging.debug(f"start:{start}|frames:{self.header.n_stored_frames}/{self.header.n_total_frames}|"
                      f"{self.header.old_animation_format}|vg:{self.n_vertex_groups}|"
                      f"hasdata:{self.header.has_additional_data}|header_size:{self.header.total_header_size}\n"
                      f"{first_bytes[:107]}|{first_bytes[108:]}")

        if conf.game not in (
                CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            raise NotImplementedError(UNSUPPORTED_GAME)

        if self.header.old_animation_format:
            subframe_size = 24
        else:
            subframe_size = 16
        if self.header.n_total_frames == self.header.n_stored_frames:
            frame_indexes = range(self.header.n_total_frames)
        else:
            frame_indexes = []

        frame_size = self.n_vertex_groups * subframe_size
        interframe_size = 4 * np.math.ceil((self.header.n_interframe * 2) / 4)
        frames: List[np.ndarray] = []

        for frame_id in range(self.header.n_stored_frames):
            if self.header.n_total_frames != self.header.n_stored_frames:
                frame_index_data_start = start + self.header.total_header_size + frame_id * frame_size + 14
                frame_indexes.append(int.from_bytes(data[frame_index_data_start:frame_index_data_start + 2], 'little'))
            last: List[np.ndarray] = []
            for group_id in range(self.n_vertex_groups):
                sub_start = start + self.header.total_header_size + interframe_size * frame_id + \
                            frame_id * frame_size + group_id * subframe_size
                subframe = [int.from_bytes(data[sub_start + i: sub_start + i + 2], 'little', signed=True)
                            for i in range(0, subframe_size, 2)]
                if self.header.old_animation_format:
                    matrix: np.ndarray = np.divide(np.array((np.array(subframe[:3]), np.array(subframe[3:6]),
                                                             np.array(subframe[6:9]))), 4096)
                    translation = \
                        np.array((np.array(subframe[9:10]), np.array(subframe[10:11]), np.array(subframe[11:12])))
                else:
                    matrix = Quaternion(subframe[0], subframe[1], subframe[2], subframe[3]).rotation_matrix
                    translation = np.array(
                        (np.array(subframe[4:5]), np.array(subframe[5:6]), np.array(subframe[6:7])))
                last.append(np.append(matrix, translation, axis=1))
            frames.append(np.array(last))
        self.frames: np.ndarray = np.array(frames)
        self.frame_indexes = tuple(frame_indexes)
        self.size = self.header.total_header_size + self.header.n_stored_frames * frame_size

        # TODO: True interframe parsing
        if self.header.n_interframe != 0:
            self.size += (self.header.n_total_frames - 1) * interframe_size

    def __getitem__(self, item):
        return self.frames[item]


class ModelData:
    vertex_size = 8
    face_size = 20

    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.header = ModelHeader(data, start, conf)
        self.game = conf.game

        self.n_vertices = self.header.n_vertices
        self.n_faces = self.header.n_faces

        self.animations: List[AnimationData] = []

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            grouped_vertices: List[np.ndarray] = []
            ungrouped_vertices: List[np.ndarray] = []
            grouped_vertices_normals: List[np.ndarray] = []
            ungrouped_vertices_normals: List[np.ndarray] = []
            last_vertices_group: List[np.ndarray] = []
            last_normals_group: List[np.ndarray] = []
            for vertex_id in range(self.n_vertices):
                # Vertices
                vertex_start = start + self.header.total_header_size + vertex_id * ModelData.vertex_size
                raw_vertex_data = (int.from_bytes(data[vertex_start: vertex_start + 2], 'little', signed=True),
                                   int.from_bytes(data[vertex_start + 2: vertex_start + 4], 'little', signed=True),
                                   int.from_bytes(data[vertex_start + 4: vertex_start + 6], 'little', signed=True),
                                   int.from_bytes(data[vertex_start + 6: vertex_start + 8], 'little'))
                vertex_array = np.array(raw_vertex_data[:3])
                last_vertices_group.append(vertex_array)
                ungrouped_vertices.append(vertex_array)

                if raw_vertex_data[3] < 1:
                    raise NegativeIndexError(start, NegativeIndexError.CAUSE_VERTEX, raw_vertex_data[3],
                                             raw_vertex_data)
                elif raw_vertex_data[3] == 1:
                    grouped_vertices.append(np.array(last_vertices_group))
                    last_vertices_group = []

                # Vertices normals
                normal_start = \
                    start + self.header.total_header_size + self.n_vertices * ModelData.vertex_size + \
                    vertex_id * ModelData.vertex_size
                raw_normal_data = (int.from_bytes(data[normal_start: normal_start + 2], 'little', signed=True),
                                   int.from_bytes(data[normal_start + 2: normal_start + 4], 'little', signed=True),
                                   int.from_bytes(data[normal_start + 4: normal_start + 6], 'little', signed=True),
                                   int.from_bytes(data[normal_start + 6: normal_start + 8], 'little'))
                normal_array = np.array(raw_normal_data[:3])
                last_normals_group.append(normal_array)
                ungrouped_vertices_normals.append(normal_array)
                if raw_normal_data[3] < 1:
                    raise NegativeIndexError(start, NegativeIndexError.CAUSE_VERTEX_NORMAL, raw_normal_data[3],
                                             raw_normal_data)
                if raw_normal_data[3] == 1:
                    grouped_vertices_normals.append(np.array(last_normals_group))
                    last_normals_group = []

            self.grouped_vertices: np.ndarray = np.array(grouped_vertices)
            self.ungrouped_vertices: np.ndarray = np.array(ungrouped_vertices)
            self.n_vertex_groups = len(self.grouped_vertices)

            self.grouped_vertices_normals: np.ndarray = np.array(grouped_vertices_normals)
            self.ungrouped_vertices_normals: np.ndarray = np.array(ungrouped_vertices_normals)

            # Faces
            faces: List[np.ndarray] = []
            faces_normals: List[np.ndarray] = []
            faces_texture_id: List[int] = []
            quad = True
            for face_id in range(self.n_faces):
                face_start = \
                    start + self.header.total_header_size + self.n_vertices * ModelData.vertex_size * 2 + \
                    face_id * ModelData.face_size
                # The last 2 bytes (16-18) are not reversed yet
                raw_face_data = (int.from_bytes(data[face_start: face_start + 2], 'little', signed=True),
                                 int.from_bytes(data[face_start + 2: face_start + 4], 'little', signed=True),
                                 int.from_bytes(data[face_start + 4: face_start + 6], 'little', signed=True),
                                 int.from_bytes(data[face_start + 6: face_start + 8], 'little'),
                                 int.from_bytes(data[face_start + 8: face_start + 10], 'little'),
                                 int.from_bytes(data[face_start + 10: face_start + 12], 'little'),
                                 int.from_bytes(data[face_start + 12: face_start + 14], 'little'),
                                 int.from_bytes(data[face_start + 14: face_start + 16], 'little'),
                                 int.from_bytes(data[face_start + 16: face_start + 18], 'little'))
                if quad:  # 1st vertex, then 2nd, 4th and 3rd
                    faces.append(np.array((raw_face_data[4], raw_face_data[5], raw_face_data[7], raw_face_data[6])))
                else:  # 1st vertex, then 2nd and 3rd
                    faces.append(np.array((raw_face_data[4], raw_face_data[5], raw_face_data[6])))
                faces_normals.append(np.array(raw_face_data[:3]))
                faces_texture_id.append(raw_face_data[8])
                if raw_face_data[3] < 1:
                    raise NegativeIndexError(start, NegativeIndexError.CAUSE_FACE, raw_face_data[3], raw_face_data)
                elif raw_face_data[3] == 1:
                    quad = False
            self.faces: np.ndarray = np.array(faces)
            self.faces_normals: np.ndarray = np.array(faces_normals)
            self.faces_texture_id: np.ndarray = np.array(faces_texture_id)
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY):
            extended_data_size = 44
        elif conf.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            extended_data_size = 32
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)
        self.size = \
            self.header.total_header_size + self.n_vertices * ModelData.vertex_size * 2 + \
            self.n_faces * ModelData.face_size + self.header.n_extended_data_frames * extended_data_size

    def animate(self, animation: AnimationData, frame_id: int = 0):
        """Returns vertices and vertices vertices_normals of this model after application of an animation frame's
        rotation & translation information. The model is **not** modified."""
        if self.n_vertex_groups != animation.n_vertex_groups:
            raise IncompatibleAnimationError(self.n_vertex_groups, animation.n_vertex_groups)
        vertices: List[np.ndarray] = []
        vertices_normals: List[np.ndarray] = []
        for i in range(self.n_vertex_groups):
            for j in range(len(self.grouped_vertices[i])):
                matrix: np.ndarray = animation[frame_id][i]
                # Dot operation order needs to be reversed for Croc 2 rotation matrices
                if self.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
                    vertex = np.add(self.grouped_vertices[i][j].dot(matrix[:, 0:3]), matrix[:, 3])
                    vertex_normal = np.add(self.grouped_vertices_normals[i][j].dot(matrix[:, 0:3]), matrix[:, 3])
                elif self.game in (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY):
                    vertex = np.add(matrix[:, 0:3].dot(self.grouped_vertices[i][j]), matrix[:, 3])
                    vertex_normal = np.add(matrix[:, 0:3].dot(self.grouped_vertices_normals[i][j]), matrix[:, 3])
                else:
                    raise NotImplementedError(UNSUPPORTED_GAME)
                vertices.append(vertex)
                vertices_normals.append(vertex_normal)
        return np.array(vertices), np.array(vertices_normals)

    @staticmethod
    def to_obj(vertices: np.ndarray, vertices_normals: np.ndarray, faces: np.ndarray, faces_tex_ids: np.ndarray,
               texture_file, obj_filename, mtl_filename):
        """Creates a Wavefront OBJ model from 3D model information and a texture file."""
        res = ""
        res += wavefront_header + f"mtllib {mtl_filename}.MTL\no {obj_filename}\n"
        # / 1024: Best value I found to correctly rescale the mesh
        res += "".join([f"v {v[0] / 1024} {v[1] / 1024} {v[2] / 1024}\n" for v in vertices])
        res += "".join([f"vn {n[0]} {n[1]} {n[2]}\n" for n in vertices_normals])
        for texture in texture_file.textures:
            for i in range(4):
                res += f"vt {texture.coords[i][0] / 1024} {(1024 - texture.coords[i][1]) / 1024}\n"
        res += "usemtl mtl1\ns off\n"
        for i in range(len(faces)):
            if len(faces[i]) == 4:  # Quadrilateral
                res += "f {v1}/{t1}/{v1} {v2}/{t2}/{v2} {v4}/{t3}/{v4} {v3}/{t4}/{v3}\n".format(
                    v1=faces[i][1] + 1, v2=faces[i][0] + 1, v3=faces[i][2] + 1, v4=faces[i][3] + 1,
                    t1=4 * faces_tex_ids[i] + 2, t2=4 * faces_tex_ids[i] + 1, t3=4 * faces_tex_ids[i] + 3,
                    t4=4 * faces_tex_ids[i] + 4)
            else:  # Triangle
                res += "f {v1}/{t1}/{v1} {v2}/{t2}/{v2} {v3}/{t3}/{v3}\n".format(
                    v1=faces[i][1] + 1, v2=faces[i][0] + 1, v3=faces[i][2] + 1,
                    t1=4 * faces_tex_ids[i] + 2, t2=4 * faces_tex_ids[i] + 1, t3=4 * faces_tex_ids[i] + 3)
        return res

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


class AnimationData:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.header = AnimationHeader(data, start, conf)
        self.n_vertex_groups = self.header.n_vertex_groups

        if conf.debug:
            debug_print = f"{start}|{self.header.old_animation_format}\n"
            f"start:{start}|frames:{self.header.n_stored_frames}/{self.header.n_total_frames}|"
            f"vg:{self.n_vertex_groups}|hasdata:{self.header.has_additional_data}|"
            f"header_size:{self.header.total_header_size}\n"
            f"{data[start:start + 48].hex(' ', 4)}"
            # f"fc:{self.header.idk_count}|flags:{self.header.idk.hex(' ', 2)}\nindexes:{self.frame_indexes}"
            print(debug_print)

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

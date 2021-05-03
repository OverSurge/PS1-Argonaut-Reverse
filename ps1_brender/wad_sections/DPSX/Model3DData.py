from io import BufferedIOBase, SEEK_CUR, StringIO
from typing import List, TextIO, Union

import numpy as np

from ps1_brender.configuration import Configuration, G, wavefront_header
from ps1_brender.errors_warnings import IncompatibleAnimationError, NegativeIndexError, VerticesNormalsGroupsMismatch
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.DPSX import ChunkClasses
from ps1_brender.wad_sections.DPSX.AnimationData import AnimationData
from ps1_brender.wad_sections.DPSX.Model3DHeader import Model3DHeader
from ps1_brender.wad_sections.TPSX.TextureData import TextureData


class BaseModel3DData(BaseBRenderClass):
    vertex_size = 8
    face_size = 20
    chunk_face_size = 12
    mtl_header = wavefront_header + "mtllib {mtl_filename}.MTL\nusemtl mtl1\ns off\n"

    def __init__(self, header: Model3DHeader, is_world_model_3d: bool, vertices: List[np.ndarray],
                 normals: List[np.ndarray], quads: np.ndarray, tris: np.ndarray, faces_normals: np.ndarray,
                 faces_texture_ids: List[int], n_vertices_groups: int):
        """header parameter is needed for chunks 3D models, where the headers are separated from the 3D model data."""
        self.header = header
        self.is_world_model_3d = is_world_model_3d
        self.vertices = vertices
        self.normals = normals
        self.quads = quads
        self.tris = tris
        self.faces_normals = faces_normals
        self.faces_texture_ids = faces_texture_ids
        self.n_vertices_groups = n_vertices_groups

    @property
    def n_vertices(self):
        return self.header.n_vertices

    @property
    def n_faces(self):
        return self.header.n_faces

    @property
    def n_bounding_box_info(self):
        return self.header.n_bounding_box_info

    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, header: Model3DHeader, is_world_model_3d: bool):
        super().parse(data_in, conf)

        def parse_vertices_normals(mode: int):
            res = []
            group = []
            for i in range(header.n_vertices):
                # Vertices
                xyzi = (int.from_bytes(data_in.read(2), 'little', signed=True),
                        int.from_bytes(data_in.read(2), 'little', signed=True),
                        int.from_bytes(data_in.read(2), 'little', signed=True),
                        int.from_bytes(data_in.read(2), 'little'))
                group.append(xyzi[:3])
                if xyzi[3] < 1:
                    error_cause = \
                        NegativeIndexError.CAUSE_VERTEX if mode == 0 else NegativeIndexError.CAUSE_VERTEX_NORMAL
                    raise NegativeIndexError(data_in.tell(), error_cause, xyzi[3], xyzi)
                elif xyzi[3] == 1:
                    res.append(np.array(group, dtype=np.int16))
                    group = []
            if group:
                res.append(np.array(group, dtype=np.int16))
            return res, len(res)

        vertices, n_vertices_groups = parse_vertices_normals(0)
        normals: List[np.ndarray] = []

        if not (is_world_model_3d and conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)):
            normals, n_normals_groups = parse_vertices_normals(1)
            if n_vertices_groups != n_normals_groups:
                raise VerticesNormalsGroupsMismatch(n_vertices_groups, n_normals_groups, data_in.tell())

        # Faces
        quads = []
        tris = []
        faces_normals = []
        faces_texture_ids: List[int] = []
        if conf.game == G.CROC_2_DEMO_PS1_DUMMY or not is_world_model_3d:  # Large face headers (Actors' models)
            for face_id in range(header.n_faces):
                raw_face_data = (int.from_bytes(data_in.read(2), 'little', signed=True),
                                 int.from_bytes(data_in.read(2), 'little', signed=True),
                                 int.from_bytes(data_in.read(2), 'little', signed=True),
                                 int.from_bytes(data_in.read(2), 'little'), int.from_bytes(data_in.read(2), 'little'),
                                 int.from_bytes(data_in.read(2), 'little'), int.from_bytes(data_in.read(2), 'little'),
                                 int.from_bytes(data_in.read(2), 'little'), int.from_bytes(data_in.read(2), 'little'),
                                 int.from_bytes(data_in.read(2), 'little'))
                if raw_face_data[9] & 0x0800:  # 1st vertex, then 2nd, 4th and 3rd, except in Croc 2 Demo Dummy WADs
                    if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
                        # FIXME
                        #  quads.append((raw_face_data[4], raw_face_data[5], raw_face_data[7], raw_face_data[6]))
                        quads.append((raw_face_data[4], raw_face_data[5], raw_face_data[6], raw_face_data[7]))
                    else:
                        quads.append((raw_face_data[4], raw_face_data[5], raw_face_data[6], raw_face_data[7]))
                else:  # 1st vertex, then 2nd and 3rd
                    tris.append((raw_face_data[4], raw_face_data[5], raw_face_data[6]))
                faces_normals.append(raw_face_data[:3])
                faces_texture_ids.append(raw_face_data[8])
                if raw_face_data[3] < 1:
                    raise NegativeIndexError(data_in.tell(), NegativeIndexError.CAUSE_FACE, raw_face_data[3],
                                             raw_face_data)
        else:  # Small face headers (Subchunks' models)
            for face_id in range(header.n_faces):
                raw_face_data = (int.from_bytes(data_in.read(2), 'little'), int.from_bytes(data_in.read(2), 'little'),
                                 int.from_bytes(data_in.read(2), 'little'), int.from_bytes(data_in.read(2), 'little'),
                                 int.from_bytes(data_in.read(2), 'little'), int.from_bytes(data_in.read(2), 'little'))
                if raw_face_data[5] & 0x0800:
                    quads.append((raw_face_data[0], raw_face_data[1], raw_face_data[2], raw_face_data[3]))
                else:
                    tris.append((raw_face_data[0], raw_face_data[1], raw_face_data[2]))
                faces_texture_ids.append(raw_face_data[4])
        quads = np.array(quads, dtype=np.uint16)
        tris = np.array(tris, dtype=np.uint16)
        faces_normals = np.array(faces_normals, dtype=np.int16)

        if conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY):
            bounding_box_info_size = 44
        else:  # Harry Potter 1 & 2
            bounding_box_info_size = 32
        data_in.seek(header.n_bounding_box_info * bounding_box_info_size, SEEK_CUR)
        return cls(header, is_world_model_3d, vertices, normals, quads, tris, faces_normals, faces_texture_ids,
                   n_vertices_groups)

    def animate(self, animation: AnimationData, frame_id: int = 0):
        """Returns vertices and vertices normals of this model after application of an animation frame's
        rotation & translation information. The model is **not** modified."""
        if self.n_vertices_groups != animation.n_vertices_groups:
            raise IncompatibleAnimationError(self.n_vertices_groups, animation.n_vertices_groups)
        vertices: List[np.ndarray] = []
        normals: List[np.ndarray] = []
        for i in range(self.n_vertices_groups):
            rotation = animation[frame_id][i][:, 0:3]
            translation = animation[frame_id][i][:, 3]
            vertices.append(np.add(self.vertices[i].dot(rotation), translation))
            normals.append(np.add(self.normals[i].dot(rotation), translation))
        return Model3DData(self.header, self.is_world_model_3d, vertices, normals, self.quads, self.tris,
                           self.faces_normals, self.faces_texture_ids, self.n_vertices_groups)

    def _to_obj(self, obj: Union[StringIO, TextIO], filename: str, textures: List[TextureData] = None, x: int = None,
                y: int = None, z: int = None, rotation=None, vertex_index_offset: int = None):
        """Creates a Wavefront OBJ 3D model from 3D model information and a texture file."""
        if textures is None and x is not None and y is not None and z is not None and rotation is not None and \
                vertex_index_offset is not None:
            standalone_export = False
        else:
            standalone_export = True
            vertex_index_offset = 0

        if not standalone_export:
            obj.write(f"o {filename}\n")

        # / 1024: Best value I found to correctly rescale the mesh
        vs = self.vertices

        if rotation is None:
            [[obj.write(f"v {v[0] / 1024} {v[1] / 1024} {v[2] / 1024}\n") for v in vg] for vg in vs]
        elif rotation == ChunkClasses.ChunkRotation.TOP:
            [[obj.write(f"v {(v[0] + x) / 1024} {(v[1] + y) / 1024} {(v[2] + z) / 1024}\n") for v in vg] for vg in vs]
        elif rotation == ChunkClasses.ChunkRotation.RIGHT:
            [[obj.write(f"v {(v[2] + x) / 1024} {(v[1] + y) / 1024} {(-v[0] + z) / 1024}\n") for v in vg] for vg in vs]
        elif rotation == ChunkClasses.ChunkRotation.BOTTOM:
            [[obj.write(f"v {(-v[0] + x) / 1024} {(v[1] + y) / 1024} {(-v[2] + z) / 1024}\n") for v in vg] for vg in vs]
        else:
            [[obj.write(f"v {(-v[2] + x) / 1024} {(v[1] + y) / 1024} {(v[0] + z) / 1024}\n") for v in vg] for vg in vs]

        [[obj.write(f"vn {n[0]} {n[1]} {n[2]}\n") for n in ng] for ng in self.normals]

        if standalone_export:
            [[obj.write(f"vt {texture.coords[j][0] / 1024} {(1024 - texture.coords[j][1]) / 1024}\n")
              for j in range(4)] for texture in textures]

        vio = vertex_index_offset
        [obj.write("f {v1}/{t1}/{v1} {v2}/{t2}/{v2} {v3}/{t3}/{v3} {v4}/{t4}/{v4}\n".format(
            v1=vio + self.quads[i][1] + 1, v2=vio + self.quads[i][0] + 1, v3=vio + self.quads[i][2] + 1,
            v4=vio + self.quads[i][3] + 1,
            t1=4 * self.faces_texture_ids[i] + 2, t2=4 * self.faces_texture_ids[i] + 1,
            t3=4 * self.faces_texture_ids[i] + 3, t4=4 * self.faces_texture_ids[i] + 4))
            for i in range(len(self.quads))]
        n_q = len(self.quads)
        [obj.write("f {v1}/{t1}/{v1} {v2}/{t2}/{v2} {v3}/{t3}/{v3}\n".format(
            v1=vio + self.tris[i][1] + 1, v2=vio + self.tris[i][0] + 1, v3=vio + self.tris[i][2] + 1,
            t1=4 * self.faces_texture_ids[n_q + i] + 2, t2=4 * self.faces_texture_ids[n_q + i] + 1,
            t3=4 * self.faces_texture_ids[n_q + i] + 3)) for i in range(len(self.tris))]

    def to_single_obj(self, obj: Union[StringIO, TextIO], obj_filename: str, textures: List[TextureData],
                      mtl_filename: str = None):
        """Creates a standalone Wavefront OBJ 3D model."""
        obj.write(self.mtl_header.format(mtl_filename=mtl_filename if mtl_filename else obj_filename))
        self._to_obj(obj, obj_filename, textures)

    def to_batch_obj(self, obj: Union[StringIO, TextIO], filename: str, x: int, y: int, z: int, rotation,
                     vertex_index_offset: int):
        """Creates a Wavefront OBJ 3D model and appends it to an existing StringIO (used to export entire levels)."""
        self._to_obj(obj, filename, None, x, y, z, rotation, vertex_index_offset)


class Model3DData(BaseModel3DData):
    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        header = Model3DHeader.parse(data_in, conf)
        return super().parse(data_in, conf, header, False)


class LevelGeom3DData(BaseModel3DData):
    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, header: Model3DHeader):
        return super().parse(data_in, conf, header, True)

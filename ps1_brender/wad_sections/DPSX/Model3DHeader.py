import warnings
from io import BufferedIOBase, SEEK_CUR

from ps1_brender.configuration import Configuration, G
from ps1_brender.errors_warnings import Models3DWarning
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass


class Model3DHeader(BaseBRenderClass):
    def __init__(self, n_vertices: int, n_faces: int, n_bounding_box_info: int):
        self.n_vertices = n_vertices
        self.n_faces = n_faces
        self.n_bounding_box_info = n_bounding_box_info

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        super().parse(raw_data, conf)
        raw_data.seek(72, SEEK_CUR)
        n_vertices = int.from_bytes(raw_data.read(4), 'little')
        raw_data.seek(8, SEEK_CUR)
        n_faces = int.from_bytes(raw_data.read(4), 'little')

        if n_vertices > 1000 or n_faces > 1000:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much vertices or faces ({n_vertices} vertices, {n_faces} faces)."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the models format.")
            else:
                raise Models3DWarning(raw_data.tell(), n_vertices, n_faces)

        raw_data.seek(4, SEEK_CUR)
        n_bounding_box_info = int.from_bytes(raw_data.read(2), 'little') + int.from_bytes(
            raw_data.read(2), 'little') + int.from_bytes(raw_data.read(2), 'little')

        if conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY):
            raw_data.seek(2, SEEK_CUR)
        elif conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1):
            raw_data.seek(6, SEEK_CUR)

        return cls(n_vertices, n_faces, n_bounding_box_info)

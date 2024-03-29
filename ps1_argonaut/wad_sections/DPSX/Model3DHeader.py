import warnings
from io import BufferedIOBase, SEEK_CUR

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.errors_warnings import Models3DWarning


class Model3DHeader(BaseDataClass):
    def __init__(self, n_vertices: int, n_faces: int, n_bounding_box_info: int):
        self.n_vertices = n_vertices
        self.n_faces = n_faces
        self.n_bounding_box_info = n_bounding_box_info

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        super().parse(data_in, conf)
        data_in.seek(72, SEEK_CUR)
        n_vertices = int.from_bytes(data_in.read(4), "little")
        data_in.seek(8, SEEK_CUR)
        n_faces = int.from_bytes(data_in.read(4), "little")

        if n_vertices > 1000 or n_faces > 1000:
            if conf.ignore_warnings:
                warnings.warn(
                    f"Too much vertices or faces ({n_vertices} vertices, {n_faces} faces)."
                    f"It is most probably caused by an inaccuracy in my reverse engineering of the models format."
                )
            else:
                raise Models3DWarning(data_in.tell(), n_vertices, n_faces)

        data_in.seek(4, SEEK_CUR)
        n_bounding_box_info = (
            int.from_bytes(data_in.read(2), "little")
            + int.from_bytes(data_in.read(2), "little")
            + int.from_bytes(data_in.read(2), "little")
        )

        if conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY):
            data_in.seek(2, SEEK_CUR)
        elif conf.game in (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1):
            data_in.seek(6, SEEK_CUR)

        return cls(n_vertices, n_faces, n_bounding_box_info)

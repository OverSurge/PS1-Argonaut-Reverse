from io import BufferedIOBase
from typing import List

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.DPSX.Model3DData import Model3DData


class Models3DFile(BaseDataClass):
    def __init__(self, n_models: int, models: List[Model3DData]):
        self.models = models
        self.n_models: int = n_models

    def __getitem__(self, item):
        return self.models[item]

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        super().parse(data_in, conf)
        n_models = int.from_bytes(data_in.read(4), 'little')
        models: List[Model3DData] = []
        for model_id in range(n_models):
            models.append(Model3DData.parse(data_in, conf))
        return cls(n_models, models)

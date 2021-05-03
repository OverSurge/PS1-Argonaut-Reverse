from io import BufferedIOBase
from typing import List

from ps1_brender.configuration import Configuration
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.DPSX.AnimationData import AnimationData


class AnimationsFile(BaseBRenderClass):
    def __init__(self, animations: List[AnimationData]):
        self.animations = animations

    @property
    def n_animations(self):
        return len(self.animations)

    def __getitem__(self, item):
        return self.animations[item]

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        super().parse(data_in, conf)
        n_animations: int = int.from_bytes(data_in.read(4), 'little')
        animations = [AnimationData.parse(data_in, conf) for _ in range(n_animations)]
        return cls(animations)

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
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        super().parse(raw_data, conf)
        n_animations: int = int.from_bytes(raw_data.read(4), 'little')
        animations = [AnimationData.parse(raw_data, conf) for _ in range(n_animations)]
        return cls(animations)

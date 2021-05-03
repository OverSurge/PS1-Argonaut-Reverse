from io import BufferedIOBase
from typing import List

from ps1_brender.configuration import Configuration
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.DPSX.StrategyData import StrategyData


class StrategiesFile(BaseBRenderClass):
    def __init__(self, strategies: List[StrategyData]):
        self.strategies = strategies

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        super().parse(data_in, conf)
        n_strategies = int.from_bytes(data_in.read(4), 'little')
        strategies = [StrategyData.parse(data_in, conf) for _ in range(n_strategies)]
        return cls(strategies)

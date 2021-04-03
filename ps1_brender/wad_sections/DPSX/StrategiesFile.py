from io import BufferedIOBase
from typing import List

from ps1_brender.configuration import Configuration
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.DPSX.StrategyData import StrategyData


class StrategiesFile(BaseBRenderClass):
    def __init__(self, strategies: List[StrategyData]):
        self.strategies = strategies

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        super().parse(raw_data, conf)
        n_strategies = int.from_bytes(raw_data.read(4), 'little')
        strategies = [StrategyData.parse(raw_data, conf) for _ in range(n_strategies)]
        return cls(strategies)

from io import BufferedIOBase
from typing import List

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.DPSX.StrategyData import StrategyData


class StrategiesFile(BaseDataClass):
    def __init__(self, strategies: List[StrategyData]):
        self.strategies = strategies

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        super().parse(data_in, conf)
        n_strategies = int.from_bytes(data_in.read(4), 'little')
        strategies = [StrategyData.parse(data_in, conf) for _ in range(n_strategies)]
        return cls(strategies)

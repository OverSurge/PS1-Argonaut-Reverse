from io import BufferedIOBase
from typing import Dict, Iterable, List, Optional

import numpy as np

from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.BaseDataClasses import BaseDataClass
from ps1_argonaut.wad_sections.SPSX.SoundContainers import LevelSFXContainer, LevelSFXGroupContainer
from ps1_argonaut.wad_sections.SPSX.Sounds import EffectSound


class LevelSFXMapping(BaseDataClass):
    def __init__(self, channel_group_mapping: Dict[int, int] = None, sounds_hashes: Iterable[int] = None,
                 mapping: np.ndarray = None):
        self.channel_group_mapping = channel_group_mapping if channel_group_mapping is not None else {}
        self.sounds_hashes = list(sounds_hashes) if sounds_hashes is not None else []
        if mapping is not None:
            self._mapping = mapping

    @property
    def n_unique_level_sfx(self):
        return self._mapping.shape[0] if hasattr(self, '_mapping') else len(self.sounds_hashes)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        n_unique_level_sfx: int = kwargs['n_unique_level_sfx']

        mapping = np.array([[ord(data_in.read(1)) for _ in range(16)] for _ in range(n_unique_level_sfx)],
                           np.uint8)
        return cls(mapping=mapping)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        level_sfx_groups: LevelSFXContainer = kwargs['level_sfx_groups']
        mapping = np.full((self.n_unique_level_sfx, 16), 255, np.uint8)
        for group_id, group in enumerate(level_sfx_groups):  # type: int, LevelSFXGroupContainer
            channel_id = self.channel_group_mapping[group_id]
            for sound_id, sound in enumerate(group):  # type: int, EffectSound
                sound_hash = hash(sound.vag.data)
                if sound_hash in self.sounds_hashes:
                    unique_sound_id = self.sounds_hashes.index(sound_hash)
                    mapping[unique_sound_id][channel_id] = sound_id
        data_out.write(bytes(mapping.flatten()))

    def parse_mapping(self, level_sfx_groups: LevelSFXContainer):
        channel_group_mapping = {}
        sounds_hashes: List[Optional[int]] = self.n_unique_level_sfx * [None]
        group_id = 0

        for channel_id in range(1, 16):
            empty_channel = True
            for unique_sound_id, sound_id in enumerate(self._mapping[:, channel_id]):  # type: int, int
                if sound_id != 255:
                    empty_channel = False
                    sounds_hashes[unique_sound_id] = hash(level_sfx_groups[group_id][sound_id].vag.data)
            if not empty_channel:
                channel_group_mapping[group_id] = channel_id
                group_id += 1
        del self._mapping
        self.channel_group_mapping = channel_group_mapping
        self.sounds_hashes = sounds_hashes

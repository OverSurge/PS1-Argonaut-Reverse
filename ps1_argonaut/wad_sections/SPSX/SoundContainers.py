import itertools
import math
from io import BufferedIOBase, SEEK_CUR
from typing import Iterable

from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.BaseDataClasses import BaseDataClass
from ps1_argonaut.wad_sections.SPSX.Sounds import Sound


class SoundsContainer(list[Sound]):
    def __init__(self, sounds: Iterable[Sound] = None):
        super().__init__(sounds if sounds else [])

    @property
    def size(self):
        return sum(sound.size for sound in self)

    @property
    def vags(self):
        return (sound.vag for sound in self)

    def parse_vags(self, data_in: BufferedIOBase, conf: Configuration):
        for sound in self:
            sound.parse_vag(data_in, conf)


class CommonSoundEffectsContainer(SoundsContainer):
    pass


class AmbientContainer(SoundsContainer):
    pass


class LevelSoundEffectsGroupContainer(SoundsContainer, BaseDataClass):
    def __init__(self, sound_effect_descriptor_offset: int, n_sound_effects: int, end_offset: int,
                 sounds: Iterable[Sound] = None):
        super().__init__(sounds if sounds else [])
        self.sound_effect_descriptor_offset = sound_effect_descriptor_offset
        self.n_sound_effects = n_sound_effects  # TODO Remove
        self.end_offset = end_offset

    @property
    def size(self):
        return sum(sound.vag.size for sound in self)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        sound_effect_descriptor_offset = int.from_bytes(data_in.read(4), 'little')
        n_sound_effects = int.from_bytes(data_in.read(4), 'little')
        end_offset = int.from_bytes(data_in.read(4), 'little')
        data_in.seek(4, SEEK_CUR)  # Sum of group VAGs' sizes
        return cls(sound_effect_descriptor_offset, n_sound_effects, end_offset)


class LevelSoundEffectsContainer(list[LevelSoundEffectsGroupContainer]):
    def __init__(self, groups: Iterable[LevelSoundEffectsGroupContainer]):
        super().__init__(groups if groups else [])

    @property
    def n_sound_effects(self):
        return sum(len(group) for group in self)

    @property
    def size(self):
        return sum(group.size for group in self)

    @property
    def sounds(self):
        return itertools.chain(*self)

    @property
    def vags(self):
        return [sound.vag for group in self for sound in group]

    def parse_vags(self, data_in: BufferedIOBase, conf: Configuration):
        for group in self:
            data_in.seek(2048 * math.ceil(data_in.tell() / 2048))
            group.parse_vags(data_in, conf)


class DialoguesBGMsContainer(SoundsContainer):
    def parse_vags(self, data_in: BufferedIOBase, conf: Configuration):
        for sound in self:
            data_in.seek(2048 * math.ceil(data_in.tell() / 2048))
            sound.parse_vag(data_in, conf)

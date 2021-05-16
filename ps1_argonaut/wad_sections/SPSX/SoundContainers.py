import itertools
import math
from io import BufferedIOBase, SEEK_CUR
from struct import Struct
from typing import Iterable, List

from ps1_argonaut.configuration import Configuration
from ps1_argonaut.utils import round_up_padding
from ps1_argonaut.wad_sections.BaseDataClasses import BaseDataClass
from ps1_argonaut.wad_sections.SPSX.Sounds import Sound, EffectSound


class SoundsContainer(List[Sound]):
    def __init__(self, sounds: Iterable[Sound] = None):
        super().__init__(sounds if sounds else [])

    @property
    def size(self):
        return sum(sound.size for sound in self)

    @property
    def vags(self):
        return (sound.vag for sound in self)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration):
        for sound in self:
            sound.serialize(data_out, conf)

    def parse_vags(self, data_in: BufferedIOBase, conf: Configuration):
        for sound in self:
            sound.parse_vag(data_in, conf)

    def serialize_vags(self, data_in: BufferedIOBase, conf: Configuration):
        for sound in self:
            sound.serialize_vag(data_in, conf)


class CommonSFXContainer(SoundsContainer):
    pass


class AmbientContainer(SoundsContainer):
    pass


class LevelSFXGroupContainer(SoundsContainer, BaseDataClass):
    struct = Struct('<4I')

    def __init__(self, sounds: Iterable[Sound] = None, n_sound_effects: int = None):
        super().__init__(sounds if sounds else [])
        if n_sound_effects is not None:
            self._n_sound_effects = n_sound_effects

    @property
    def size(self):
        return sum(sound.size for sound in self)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        data_in.seek(4, SEEK_CUR)  # Group header offset
        n_sound_effects = int.from_bytes(data_in.read(4), 'little')
        data_in.seek(8, SEEK_CUR)  # End offset (4 bytes) | Sum of group VAGs' sizes (4 bytes)
        return cls(n_sound_effects=n_sound_effects)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        data_out.write(self.struct.pack(kwargs['group_header_offset'], len(self), kwargs['end_offset'], self.size))

    def parse_children(self, data_in: BufferedIOBase, conf: Configuration):
        self.extend(EffectSound.parse(data_in, conf) for _ in range(self._n_sound_effects))
        del self._n_sound_effects

    def serialize_children(self, data_out: BufferedIOBase, conf: Configuration):
        for sound in self:
            sound.serialize(data_out, conf)


class LevelSFXContainer(List[LevelSFXGroupContainer], BaseDataClass):
    def __init__(self, groups: Iterable[LevelSFXGroupContainer] = None):
        super().__init__(groups if groups is not None else [])

    @property
    def n_sounds(self):
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

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        group_header_offset = 0
        end_offset = 0
        for group in self:
            group.serialize(data_out, conf, group_header_offset=group_header_offset, end_offset=end_offset)
            group_header_offset += 20 * len(group)
            end_offset += round_up_padding(group.size)

    def parse_groups(self, data_in: BufferedIOBase, conf: Configuration):
        for group in self:
            group.parse_children(data_in, conf)

    def parse_vags(self, data_in: BufferedIOBase, conf: Configuration):
        for group in self:
            data_in.seek(2048 * math.ceil(data_in.tell() / 2048))
            group.parse_vags(data_in, conf)

    def serialize_vags(self, data_out: BufferedIOBase, conf: Configuration):
        for group in self:
            data_out.seek(2048 * math.ceil(data_out.tell() / 2048))
            group.serialize_vags(data_out, conf)


class DialoguesBGMsContainer(SoundsContainer):
    def parse_vags(self, data_in: BufferedIOBase, conf: Configuration):
        for sound in self:
            data_in.seek(2048 * math.ceil(data_in.tell() / 2048))
            sound.parse_vag(data_in, conf)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration):
        end_section_offset = 0
        for sound in self:
            sound.serialize(data_out, conf, end_section_offset=end_section_offset)
            end_section_offset += sound.size

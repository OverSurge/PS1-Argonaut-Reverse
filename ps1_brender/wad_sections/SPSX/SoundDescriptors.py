import math
from enum import IntFlag
from io import BufferedIOBase, SEEK_CUR
from typing import List, Union

from ps1_brender.configuration import Configuration
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.SPSX.VAGSoundData import MONO, VAGSoundData, STEREO


class SoundEffectsAmbientFlags(IntFlag):
    pass


class DialoguesBGMsSoundFlags(IntFlag):
    HAS_INTERLEAVED_STEREO = 0x1
    IS_BACKGROUND_MUSIC = 0x4


class SoundDescriptor:
    def __init__(self, sampling_rate: int, flags: Union[SoundEffectsAmbientFlags, DialoguesBGMsSoundFlags], size: int):
        self.sampling_rate = sampling_rate
        self.flags = flags
        self.size = size

    def parse_vag(self, raw_data: BufferedIOBase, conf: Configuration):
        pass


class SoundEffectsAmbientDescriptor(SoundDescriptor, BaseBRenderClass):
    known_values_1st_flags_byte = (0x00000000, 0x00000001)
    known_values_2nd_2rd_flags_bytes = (0x00000000, 0x00010100)

    def __init__(self, sampling_rate: int, volume_level: int, flags: SoundEffectsAmbientFlags, uk1: bytes, size: int):
        super().__init__(sampling_rate, flags, size)
        self.volume_level = volume_level
        self.uk1 = uk1

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        sampling_rate = int.from_bytes(raw_data.read(4), 'little')
        raw_data.seek(2, SEEK_CUR)  # "Compressed" sampling rate, see SPSX's documentation
        volume_level = int.from_bytes(raw_data.read(2), 'little')
        flags = SoundEffectsAmbientFlags(int.from_bytes(raw_data.read(4), 'little'))
        raw_data.seek(2, SEEK_CUR)
        uk1 = raw_data.read(2)
        size = int.from_bytes(raw_data.read(4), 'little')
        return cls(sampling_rate, volume_level, flags, uk1, size)

    def parse_vag(self, raw_data: BufferedIOBase, conf: Configuration):
        return VAGSoundData(self.size, raw_data.read(self.size), MONO, self.sampling_rate, conf)


class SoundEffectsDescriptor(SoundEffectsAmbientDescriptor):
    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        res = super().parse(raw_data, conf)
        assert (res.flags & 0x000000FF).value in cls.known_values_1st_flags_byte
        assert (res.flags & 0x00FFFF00).value in cls.known_values_2nd_2rd_flags_bytes
        assert res.uk1 == b'\x42\x00'
        return res


class DialoguesBGMsDescriptor(SoundDescriptor, BaseBRenderClass):
    def __init__(self, end_section_offset: int, sampling_rate: int, flags: DialoguesBGMsSoundFlags, uk1: bytes,
                 size: int):
        super().__init__(sampling_rate, flags, size)
        self.end_section_offset = end_section_offset
        self.uk1 = uk1

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        end_section_offset = int.from_bytes(raw_data.read(4), 'little')
        sampling_rate = (int.from_bytes(raw_data.read(2), 'little') * 44100) // 4096
        flags = DialoguesBGMsSoundFlags(int.from_bytes(raw_data.read(2), 'little'))
        uk1 = raw_data.read(4)
        size = int.from_bytes(raw_data.read(4), 'little')
        return cls(end_section_offset, sampling_rate, flags, uk1, size)

    def parse_vag(self, raw_data: BufferedIOBase, conf: Configuration):
        return VAGSoundData(self.size, raw_data.read(self.size),
                            STEREO if DialoguesBGMsSoundFlags.HAS_INTERLEAVED_STEREO in self.flags else MONO,
                            self.sampling_rate, conf)


class SoundsHolder:
    def __init__(self, descriptors: List[SoundDescriptor] = None, vags: List[VAGSoundData] = None):
        self._descriptors = descriptors if descriptors is not None else []
        self._vags = vags if vags is not None else []

    @property
    def descriptors(self):
        return self._descriptors

    @property
    def vags(self):
        return self._vags

    def __len__(self):
        return len(self.descriptors)

    def parse_vags(self, raw_data: BufferedIOBase, conf: Configuration):
        self._vags = [x.parse_vag(raw_data, conf) for x in self.descriptors]


class LevelSoundEffectsGroupDescriptor(BaseBRenderClass):
    def __init__(self, sound_effect_descriptor_offset: int, n_sound_effects: int, end_offset: int, size: int,
                 sounds_holder: SoundsHolder = None):
        self.sound_effect_descriptor_offset = sound_effect_descriptor_offset
        self.n_sound_effects = n_sound_effects
        self.end_offset = end_offset
        self.size = size
        self.sounds_holder = sounds_holder if sounds_holder is not None else SoundsHolder()

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        sound_effect_descriptor_offset = int.from_bytes(raw_data.read(4), 'little')
        n_sound_effects = int.from_bytes(raw_data.read(4), 'little')
        end_offset = int.from_bytes(raw_data.read(4), 'little')
        size = int.from_bytes(raw_data.read(4), 'little')
        return cls(sound_effect_descriptor_offset, n_sound_effects, end_offset, size)


class LevelSoundEffectsGroupsHolder(SoundsHolder):
    # noinspection PyMissingConstructor
    def __init__(self, groups: List[LevelSoundEffectsGroupDescriptor]):
        self.groups = groups

    @property
    def descriptors(self):
        return [descriptor for group in self.groups for descriptor in group.sounds_holder.descriptors]

    @property
    def vags(self):
        return [vag for group in self.groups for vag in group.sounds_holder.vags]

    def parse_vags(self, raw_data: BufferedIOBase, conf: Configuration):
        for group in self.groups:
            raw_data.seek(2048 * math.ceil(raw_data.tell() / 2048))
            group.sounds_holder.parse_vags(raw_data, conf)


class DialoguesBGMsHolder(SoundsHolder):
    def parse_vags(self, raw_data: BufferedIOBase, conf: Configuration):
        vags = []
        for descriptor in self.descriptors:
            raw_data.seek(2048 * math.ceil(raw_data.tell() / 2048))
            vags.append(descriptor.parse_vag(raw_data, conf))
        self._vags = vags

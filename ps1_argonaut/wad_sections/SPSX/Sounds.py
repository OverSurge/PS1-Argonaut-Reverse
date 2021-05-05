from enum import IntFlag
from io import BufferedIOBase, SEEK_CUR
from typing import Union

from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.BaseDataClasses import BaseDataClass
from ps1_argonaut.wad_sections.SPSX.VAGSoundData import MONO, VAGSoundData, STEREO


class SoundEffectsAmbientFlags(IntFlag):
    pass


class DialoguesBGMsSoundFlags(IntFlag):
    HAS_INTERLEAVED_STEREO = 0x1
    IS_BACKGROUND_MUSIC = 0x4


class Sound:
    def __init__(self, sampling_rate: int, flags: Union[SoundEffectsAmbientFlags, DialoguesBGMsSoundFlags], size: int,
                 vag: VAGSoundData = None):
        self.sampling_rate = sampling_rate
        self.flags = flags
        self.size = size  # TODO Remove
        self.vag = vag

    def parse_vag(self, data_in: BufferedIOBase, conf: Configuration):
        pass


class _AmbientOrEffectSound(Sound, BaseDataClass):
    known_values_1st_flags_byte = (0x00000000, 0x00000001)
    known_values_2nd_2rd_flags_bytes = (0x00000000, 0x00010100)

    def __init__(self, sampling_rate: int, volume_level: int, flags: SoundEffectsAmbientFlags, uk1: bytes, size: int,
                 vag: VAGSoundData = None):
        super().__init__(sampling_rate, flags, size, vag)
        self.volume_level = volume_level
        self.uk1 = uk1

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        sampling_rate = int.from_bytes(data_in.read(4), 'little')
        data_in.seek(2, SEEK_CUR)  # "Compressed" sampling rate, see SPSX's documentation
        volume_level = int.from_bytes(data_in.read(2), 'little')
        flags = SoundEffectsAmbientFlags(int.from_bytes(data_in.read(4), 'little'))
        data_in.seek(2, SEEK_CUR)
        uk1 = data_in.read(2)
        size = int.from_bytes(data_in.read(4), 'little')
        return cls(sampling_rate, volume_level, flags, uk1, size)

    def parse_vag(self, data_in: BufferedIOBase, conf: Configuration):
        self.vag = VAGSoundData(self.size, data_in.read(self.size), MONO, self.sampling_rate, conf)


class AmbientSound(_AmbientOrEffectSound):
    pass


class EffectSound(_AmbientOrEffectSound):
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        res = super().parse(data_in, conf)
        assert (res.flags & 0x000000FF).value in cls.known_values_1st_flags_byte
        assert (res.flags & 0x00FFFF00).value in cls.known_values_2nd_2rd_flags_bytes
        assert res.uk1 == b'\x42\x00'
        return res


class DialogueBGMSound(Sound, BaseDataClass):
    def __init__(self, end_section_offset: int, sampling_rate: int, flags: DialoguesBGMsSoundFlags, uk1: bytes,
                 size: int, vag: VAGSoundData = None):
        super().__init__(sampling_rate, flags, size, vag)
        self.end_section_offset = end_section_offset
        self.uk1 = uk1

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        end_section_offset = int.from_bytes(data_in.read(4), 'little')
        sampling_rate = (int.from_bytes(data_in.read(2), 'little') * 44100) // 4096
        flags = DialoguesBGMsSoundFlags(int.from_bytes(data_in.read(2), 'little'))
        uk1 = data_in.read(4)
        size = int.from_bytes(data_in.read(4), 'little')
        return cls(end_section_offset, sampling_rate, flags, uk1, size)

    def parse_vag(self, data_in: BufferedIOBase, conf: Configuration):
        self.vag = VAGSoundData(self.size, data_in.read(self.size),
                                STEREO if DialoguesBGMsSoundFlags.HAS_INTERLEAVED_STEREO in self.flags else MONO,
                                self.sampling_rate, conf)

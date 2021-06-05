from enum import IntFlag
from io import BufferedIOBase, SEEK_CUR
from struct import Struct
from typing import Union

from ps1_argonaut.BaseDataClasses import BaseDataClass
from ps1_argonaut.configuration import Configuration
from ps1_argonaut.wad_sections.SPSX.VAGSoundData import MONO, VAGSoundData, STEREO


class SoundEffectsAmbientFlags(IntFlag):
    pass


class DialoguesBGMsSoundFlags(IntFlag):
    IS_STEREO = 0x1
    IS_MONO = 0x2
    IS_BACKGROUND_MUSIC = 0x4


class Sound(BaseDataClass):
    def __init__(self, sampling_rate: int, flags: Union[SoundEffectsAmbientFlags, DialoguesBGMsSoundFlags],
                 vag: VAGSoundData = None, size: int = None):
        self.sampling_rate = sampling_rate
        self.flags = flags
        if size is not None:
            self._size = size
        self.vag = vag

    @property
    def size(self):
        return self.vag.size if self.vag is not None else self._size if hasattr(self, '_size') else 0

    def parse_vag(self, data_in: BufferedIOBase, conf: Configuration):
        del self._size

    def serialize_vag(self, data_out: BufferedIOBase, conf: Configuration):
        self.vag.serialize(data_out, conf)


class _AmbientOrEffectSound(Sound):
    struct = Struct('<IHHI2s2sI')
    known_values_1st_flags_byte = (0x00000000, 0x00000001)
    known_values_2nd_2rd_flags_bytes = (0x00000000, 0x00010100)

    def __init__(self, sampling_rate: int, volume_level: int, flags: SoundEffectsAmbientFlags, uk1: bytes, uk2: bytes,
                 size: int, vag: VAGSoundData = None):
        super().__init__(sampling_rate, flags, vag, size)
        self.volume_level = volume_level
        self.uk1 = uk1
        self.uk2 = uk2

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        sampling_rate = int.from_bytes(data_in.read(4), 'little')
        data_in.seek(2, SEEK_CUR)  # "Compressed" sampling rate, see SPSX's documentation
        volume_level = int.from_bytes(data_in.read(2), 'little')
        flags = SoundEffectsAmbientFlags(int.from_bytes(data_in.read(4), 'little'))
        uk1 = data_in.read(2)
        uk2 = data_in.read(2)
        size = int.from_bytes(data_in.read(4), 'little')
        return cls(sampling_rate, volume_level, flags, uk1, uk2, size)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        rounded_sampling_rate = int(round((self.sampling_rate * 4096) / 44100))
        data_out.write(self.struct.pack(self.sampling_rate, rounded_sampling_rate, self.volume_level,
                                        self.flags.value, self.uk1, self.uk2, self.size))

    def parse_vag(self, data_in: BufferedIOBase, conf: Configuration):
        self.vag = VAGSoundData.parse(data_in, conf, size=self._size, n_channels=MONO, sampling_rate=self.sampling_rate)
        super().parse_vag(data_in, conf)


class AmbientSound(_AmbientOrEffectSound):
    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        rounded_sampling_rate = int(round((self.sampling_rate * 4096) / 48000))
        data_out.write(self.struct.pack(self.sampling_rate, rounded_sampling_rate, self.volume_level, self.flags.value,
                                        self.uk1, self.uk2, self.size))


class EffectSound(_AmbientOrEffectSound):
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        res = super().parse(data_in, conf)
        assert (res.flags & 0x000000FF).value in cls.known_values_1st_flags_byte
        assert (res.flags & 0x00FFFF00).value in cls.known_values_2nd_2rd_flags_bytes
        assert res.uk2 == b'\x42\x00'
        return res


class DialogueBGMSound(Sound):
    struct = Struct('<IHH4sI')

    def __init__(self, sampling_rate: int, flags: DialoguesBGMsSoundFlags, uk1: bytes, size: int,
                 vag: VAGSoundData = None):
        super().__init__(sampling_rate, flags, vag, size)
        self.uk1 = uk1

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        data_in.seek(4, SEEK_CUR)  # END section offset
        sampling_rate = int(round(((int.from_bytes(data_in.read(2), 'little') * 44100) / 4096)))
        flags = DialoguesBGMsSoundFlags(int.from_bytes(data_in.read(2), 'little'))
        uk1 = data_in.read(4)
        size = int.from_bytes(data_in.read(4), 'little')
        return cls(sampling_rate, flags, uk1, size)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        rounded_sampling_rate = int(round((self.sampling_rate * 4096) / 44100))
        data_out.write(self.struct.pack(kwargs['end_section_offset'], rounded_sampling_rate, self.flags.value, self.uk1,
                                        self.size))

    def parse_vag(self, data_in: BufferedIOBase, conf: Configuration):
        self.vag = VAGSoundData.parse(data_in, conf, size=self._size, sampling_rate=self.sampling_rate,
                                      n_channels=STEREO if DialoguesBGMsSoundFlags.IS_STEREO in self.flags else MONO)
        super().parse_vag(data_in, conf)

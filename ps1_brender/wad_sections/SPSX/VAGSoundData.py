from ctypes import c_int32
from io import BufferedIOBase

from ps1_brender.configuration import Configuration, wav_header
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass


class VAGSoundData(BaseBRenderClass):
    constants = ((0.0, 0.0),
                 (60.0 / 64.0, 0.0),
                 (115.0 / 64.0, -52.0 / 64.0),
                 (98.0 / 64.0, -55.0 / 64.0),
                 (122.0 / 64.0, -60.0 / 64.0))

    def __init__(self, size: int, data: bytes, channels: int, sampling_rate: int, conf: Configuration):
        if channels != 1 and channels != 2:
            raise ValueError
        self.size: int = size
        self.data: bytes = data
        self.n_channels: int = channels
        self.sampling_rate: int = sampling_rate
        self.conf = conf

    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration, size: int, channels: int, sampling_rate: int):
        return cls(size, raw_data.read(size), channels, sampling_rate, conf)

    def to_vag(self, with_headers: bool = True):
        header_size = 0 if with_headers else 48
        header = b"VAGp\x00\x00\x00\x00\x00\x00\x00\x00" + (self.size // self.n_channels).to_bytes(4, 'big') + \
                 self.sampling_rate.to_bytes(4, 'big') + \
                 b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00OverSurgeBRender" if with_headers else None
        if self.n_channels == 1:
            return (header + self.data,) if with_headers else (self.data,)
        else:
            res = bytearray(header_size + self.size // 2)
            if with_headers:
                res[:48] = header
            res2 = res.copy()
            for i in range(0, self.size, 2048):
                i2 = header_size + i // 2
                res[i2:i2 + 1024] = self.data[i:i + 1024]
                res2[i2:i2 + 1024] = self.data[i + 1024:i + 2048]
            return res, res2

    def to_wav(self, filename: str):  # TODO Poor performance
        """supports stereo export in a single file, unlike to_vag()."""
        vag = self.to_vag(False)

        byte_rate = self.sampling_rate * self.n_channels * 2
        block_align = self.n_channels * 2
        audio_data_size = (self.size * 7) // 2  # VAG -> WAV has a 3.5 size ratio

        id3_tags = b"TALB" + (len(self.conf.game.title) + 5).to_bytes(4, 'big') + b"\x00\x00\x00" + \
                   (self.conf.game.title + ' OST').encode('ASCII') + \
                   b"TIT2" + (len(filename) + 1).to_bytes(4, 'big') + b"\x00\x00\x00" + \
                   filename.encode('ASCII') + b"COMM\x00\x00\x00\x55\x00\x00\x00XXX\x00" + wav_header + \
                   b"TCON\x00\x00\x00\x05\x00\x00\x00GameTDRC\x00\x00\x00\x05\x00\x00\x00" + \
                   str(self.conf.game.release_year).encode('ASCII')
        # The ID3 header size uses 7 bits/byte, see https://id3.org/id3v2.3.0#ID3v2_header for more
        id3_tags_size = (len(id3_tags) & 127) + ((len(id3_tags) & 16256) << 1)
        id3 = b"ID3\x03\x00\x00" + id3_tags_size.to_bytes(4, 'big') + id3_tags
        footer = b"ID3 " + len(id3).to_bytes(4, 'little') + id3

        total_wav_size = 44 + audio_data_size + len(footer)
        header = b"RIFF" + (total_wav_size - 8).to_bytes(4, 'little') + b"WAVEfmt \x10\x00\x00\x00\x01\x00" + \
                 self.n_channels.to_bytes(2, 'little') + self.sampling_rate.to_bytes(4, 'little') + \
                 byte_rate.to_bytes(4, 'little') + block_align.to_bytes(2, 'little') + b"\x10\x00data" + \
                 audio_data_size.to_bytes(4, 'little')

        res = bytearray(total_wav_size)
        res[:44] = header
        res[-len(footer):] = footer
        if self.n_channels == 1:
            channels = None
        else:
            channels = (bytearray(audio_data_size // 2), bytearray(audio_data_size // 2))

        # Based on VAG-Depack 0.1 by bITmASTER
        for c in range(self.n_channels):
            s_1 = 0.0
            s_2 = 0.0
            samples = [0.0] * 28
            for i in range(16, self.size // self.n_channels, 16):
                predict_nr = vag[c][i]
                shift_factor = predict_nr & 0xF
                predict_nr >>= 4
                flags = vag[c][i + 1]
                if flags == 7:
                    break
                for j in range(0, 28, 2):
                    d = vag[c][i + 2 + j // 2]
                    s = (d & 0xF) << 12
                    if s & 0x8000:
                        s = c_int32(s | 0xFFFF0000).value
                    samples[j] = s >> shift_factor
                    s = (d & 0xF0) << 8
                    if s & 0x8000:
                        s = c_int32(s | 0xFFFF0000).value
                    samples[j + 1] = float(s >> shift_factor)
                for j in range(28):
                    samples[j] += s_1 * VAGSoundData.constants[predict_nr][0] + s_2 * \
                                  VAGSoundData.constants[predict_nr][1]
                    s_2 = s_1
                    s_1 = samples[j]
                    d = int(samples[j] + 0.5)
                    wav_pos = (i * 7) // 2 + j * 2
                    if self.n_channels == 1:
                        res[44 + wav_pos] = d & 0xFF
                        res[45 + wav_pos] = (d >> 8) & 0xFF
                    else:
                        channels[c][wav_pos] = d & 0xFF
                        channels[c][wav_pos + 1] = (d >> 8) & 0xFF
                if flags == 1:
                    break
        if self.n_channels == 2:
            for i in range(0, audio_data_size // 2, 2):
                res[44 + 2 * i:46 + 2 * i] = channels[0][i:i + 2]
                res[46 + 2 * i:48 + 2 * i] = channels[1][i:i + 2]
        return res
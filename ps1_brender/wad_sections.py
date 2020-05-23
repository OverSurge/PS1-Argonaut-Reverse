from typing import List

from ps1_brender import *
from ps1_brender.files import AnimationFile, ModelFile, TextureFile


class WADFile:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        codenames: List[str] = []
        offsets: List[int] = []
        offset = start + 4
        while True:
            codename = data[offset: offset + 4]

            # Detects incorrect WADs like FESOUND or FETHUND
            if len(codenames) == 0 and codename != XSPTSection.codename_bytes:
                raise SectionNameError(offset, XSPTSection.codename, codename.decode('latin1'))

            codenames.append(codename.decode('latin1'))
            offsets.append(offset)
            if codename == b'\x20\x44\x4E\x45':  # ' DNE'
                break
            offset += 8 + int.from_bytes(data[offset + 4: offset + 8], 'little')
        xspt_index = codenames.index('XSPT')
        self.xspt = XSPTSection(data, offsets[xspt_index], offsets[xspt_index + 1], conf)
        if conf.process_all_sections:
            xspd_index = codenames.index('XSPD')
            self.xspd = XSPDSection(data, offsets[xspd_index], offsets[xspd_index + 1], conf)


class XSPTSection:
    codename = 'XSPT'
    codename_bytes = b'\x58\x53\x50\x54'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration):
        codename_bytes = data[start:start + 4]
        if codename_bytes != XSPTSection.codename_bytes:
            raise SectionNameError(start, XSPTSection.codename, codename_bytes.decode('latin_1'))

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            xspt_flags = data[start + 8]
            has_translated_titles = xspt_flags & 16 != 0
            has_legacy_textures = xspt_flags & 8 != 0
            has_title_and_demo_mode_data = xspt_flags & 4 != 0
            if has_title_and_demo_mode_data:
                if has_translated_titles:
                    n_titles = int.from_bytes(data[start + 12:start + 16], 'little')
                    xspt_header_size = 16 + n_titles * 48 + 2052
                else:
                    xspt_header_size = 2096  # 44 + 2052
            else:
                xspt_header_size = 12
        elif conf.game == CROC_2_DEMO_PS1_DUMMY:  # The dummy WADs don't have any sort of flag or XSPT header
            xspt_header_size = 8
            has_legacy_textures = False
        else:
            raise NotImplementedError

        self.texture_file = TextureFile(data, start + xspt_header_size, end, conf, has_legacy_textures)

        expected_size = end - start
        calculated_size = xspt_header_size + self.texture_file.size
        if expected_size != calculated_size:
            raise SectionSizeMismatch(end, XSPTSection.codename, expected_size, calculated_size)


class XSPDSection:
    codename = 'XSPD'
    codename_bytes = b'\x58\x53\x50\x44'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration):
        codename_bytes = data[start:start + 4]
        if codename_bytes != XSPDSection.codename_bytes:
            raise SectionNameError(start, XSPDSection.codename, codename_bytes.decode('latin_1'))

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            xspd_header_size = 2064
        elif conf.game == CROC_2_DEMO_PS1_DUMMY:
            xspd_header_size = 2068
        else:
            raise NotImplementedError
        self.model_file = ModelFile(data, start + xspd_header_size, conf)
        self.animation_file = AnimationFile(data, start + xspd_header_size + self.model_file.size, conf)

        # TODO: XSPD isn't entirely reversed yet
        # expected_size = end - start
        # calculated_size = xspd_header_size + self.model_file.size + self.animation_file.size
        # if expected_size != calculated_size:
        #     raise SectionSizeMismatch(end, XSPDSection.codename, expected_size, calculated_size)

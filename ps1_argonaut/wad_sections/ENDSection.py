import math
from io import BufferedIOBase

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.utils import pad_out_2048_bytes
from ps1_argonaut.wad_sections.BaseDataClasses import BaseWADSection
from ps1_argonaut.wad_sections.SPSX.SPSXFlags import SPSXFlags
from ps1_argonaut.wad_sections.SPSX.SPSXSection import SPSXSection


class ENDSection(BaseWADSection):
    codename_str = ' DNE'
    codename_bytes = b' DNE'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "sound effects, background music & dialogues"

    def __init__(self, spsx_section: SPSXSection):
        super().__init__()
        self.spsx_section = spsx_section

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        size, start = super().parse(data_in, conf)
        spsx_section: SPSXSection = kwargs['spsx_section']

        if size != 0:
            if SPSXFlags.HAS_LEVEL_SFX in spsx_section.spsx_flags:
                spsx_section.level_sfx_groups.parse_vags(data_in, conf)

            data_in.seek(2048 * math.ceil(data_in.tell() / 2048))
            spsx_section.dialogues_bgms.parse_vags(data_in, conf)

            if conf.game == G.HARRY_POTTER_2_PS1:
                data_in.seek(2048 * math.ceil(data_in.tell() / 2048))

            cls.check_size(size, start, data_in.tell())
        return cls(spsx_section)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        start = super().serialize(data_out, conf)
        if SPSXFlags.HAS_LEVEL_SFX in self.spsx_section.spsx_flags:
            self.spsx_section.level_sfx_groups.serialize_vags(data_out, conf)

        pad_out_2048_bytes(data_out)
        self.spsx_section.dialogues_bgms.serialize_vags(data_out, conf)

        if conf.game == G.HARRY_POTTER_2_PS1:
            pad_out_2048_bytes(data_out)

        size = data_out.tell() - start
        data_out.seek(start - 4)
        data_out.write(size.to_bytes(4, 'little'))

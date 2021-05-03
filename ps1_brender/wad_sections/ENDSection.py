import math
from io import BufferedIOBase

from ps1_brender.configuration import Configuration, G
from ps1_brender.wad_sections.BaseBRenderClasses import BaseWADSection
from ps1_brender.wad_sections.SPSX.SPSXFlags import SPSXFlags
from ps1_brender.wad_sections.SPSX.SPSXSection import SPSXSection


class ENDSection(BaseWADSection):
    codename_str = ' DNE'
    codename_bytes = b' DNE'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "sound effects, background music & dialogues"

    def __init__(self, spsx_section: SPSXSection):
        self.spsx_section = spsx_section

    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, spsx_section: SPSXSection):
        size, start = super().parse(data_in, conf)
        if size != 0:
            if SPSXFlags.HAS_LEVEL_SOUND_EFFECTS in spsx_section.spsx_flags:
                spsx_section.level_sound_effects_groups.parse_vags(data_in, conf)

            data_in.seek(2048 * math.ceil(data_in.tell() / 2048))
            spsx_section.dialogues_bgms.parse_vags(data_in, conf)

            if conf.game == G.HARRY_POTTER_2_PS1:
                data_in.seek(2048 * math.ceil(data_in.tell() / 2048))

            cls.check_size(size, start, data_in.tell())
        return cls(spsx_section)

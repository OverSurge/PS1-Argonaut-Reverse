from io import BufferedIOBase

from ps1_brender.configuration import Configuration, G
from ps1_brender.wad_sections.BaseBRenderClasses import BaseWADSection
from ps1_brender.wad_sections.SPSX.SoundFile import SoundFile


class SPSXSection(BaseWADSection):
    codename_str = 'XSPS'
    codename_bytes = b'XSPS'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "sound effects, background music & dialogues"

    def __init__(self, size: int, sound_file: SoundFile):
        super().__init__(size)
        self.sound_file = sound_file

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        size, start = super().parse(raw_data, conf)

        sound_file = SoundFile.parse(raw_data, conf)

        cls.check_size(size, start, raw_data.tell())
        return cls(size, sound_file)

from io import BufferedIOBase, SEEK_CUR
from typing import Tuple

from ps1_brender.configuration import Configuration, G, PARSABLE_GAMES
from ps1_brender.wad_sections.BaseBRenderClasses import BaseWADSection
from ps1_brender.wad_sections.TPSX.TextureFile import TextureFile


class TPSXSection(BaseWADSection):
    codename_str = 'XSPT'
    codename_bytes = b'XSPT'
    supported_games = PARSABLE_GAMES
    section_content_description = "textures"

    def __init__(self, titles: Tuple[str], texture_file: TextureFile):
        self.titles = titles
        self.texture_file = texture_file

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        size, start = super().parse(raw_data, conf)
        if conf.game == G.CROC_2_DEMO_PS1_DUMMY:
            has_legacy_textures = False
            titles = ()
        else:
            tpsx_flags = int.from_bytes(raw_data.read(4), 'little')
            has_translated_titles = tpsx_flags & 16 != 0
            has_legacy_textures = tpsx_flags & 8 != 0
            has_title_and_demo_mode_data = tpsx_flags & 4 != 0
            if has_title_and_demo_mode_data:
                if has_translated_titles:
                    n_titles = int.from_bytes(raw_data.read(4), 'little')
                    titles = tuple([raw_data.read(48).decode('latin1') for _ in range(n_titles)])
                else:
                    titles = raw_data.read(32).decode('latin1'),
                raw_data.seek(2052, SEEK_CUR)
            else:
                titles = ()
        texture_file = TextureFile.parse(raw_data, conf, start + size, has_legacy_textures)

        cls.check_size(size, start, raw_data.tell())
        return cls(titles, texture_file)

from collections.abc import Iterable
from io import BufferedIOBase, SEEK_CUR

from ps1_argonaut.BaseDataClasses import BaseWADSection
from ps1_argonaut.configuration import Configuration, G, PARSABLE_GAMES
from ps1_argonaut.wad_sections.TPSX.TextureFile import TextureFile


class TPSXSection(BaseWADSection):
    codename_str = "XSPT"
    codename_bytes = b"XSPT"
    supported_games = PARSABLE_GAMES
    section_content_description = "textures"

    def __init__(
        self,
        texture_file: TextureFile,
        titles: Iterable[str] = None,
        fallback_data: bytes = None,
    ):
        super().__init__(fallback_data)
        self.texture_file = texture_file
        self.titles = list(titles) if titles is not None else []

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        fallback_data = cls.fallback_parse_data(data_in)
        size, start = super().parse(data_in, conf)
        if conf.game == G.CROC_2_DEMO_PS1_DUMMY:
            has_legacy_textures = False
            titles = None
        else:
            tpsx_flags = int.from_bytes(data_in.read(4), "little")
            has_translated_titles = tpsx_flags & 16 != 0
            has_legacy_textures = tpsx_flags & 8 != 0
            has_title_and_demo_mode_data = tpsx_flags & 4 != 0
            if has_title_and_demo_mode_data:
                if has_translated_titles:
                    n_titles = int.from_bytes(data_in.read(4), "little")
                    titles = [
                        data_in.read(48).strip(b"\0").decode("latin1")
                        for _ in range(n_titles)
                    ]
                else:
                    titles = [data_in.read(32).strip(b"\0").decode("latin1")]
                data_in.seek(2052, SEEK_CUR)
            else:
                titles = None
        texture_file = TextureFile.parse(
            data_in, conf, has_legacy_textures=has_legacy_textures, end=start + size
        )

        cls.check_size(size, start, data_in.tell())
        return cls(texture_file, titles, fallback_data)

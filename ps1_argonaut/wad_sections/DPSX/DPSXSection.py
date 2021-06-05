from io import BufferedIOBase, SEEK_CUR

from ps1_argonaut.BaseDataClasses import BaseWADSection
from ps1_argonaut.configuration import Configuration, G, PARSABLE_GAMES
from ps1_argonaut.wad_sections.DPSX.AnimationsFile import AnimationsFile
from ps1_argonaut.wad_sections.DPSX.LevelFile import LevelFile
from ps1_argonaut.wad_sections.DPSX.Models3DFile import Models3DFile
from ps1_argonaut.wad_sections.DPSX.StrategiesFile import StrategiesFile


class DPSXSection(BaseWADSection):
    codename_str = 'XSPD'
    codename_bytes = b'XSPD'
    supported_games = PARSABLE_GAMES
    section_content_description = "3D models, animations & level geometry"

    def __init__(self, models_3d_file: Models3DFile, animations_file: AnimationsFile, strategies_file: StrategiesFile,
                 level_file: LevelFile, fallback_data: bytes = None):
        super().__init__(fallback_data)
        self.models_3d_file = models_3d_file
        self.animations_file = animations_file
        self.strategies_file = strategies_file
        self.level_file = level_file

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        fallback_data = super().fallback_parse_data(data_in)
        size, start = super().parse(data_in, conf)
        idk1 = data_in.read(4)
        n_idk_unique_textures = int.from_bytes(data_in.read(4), 'little')

        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            data_in.seek(2048, SEEK_CUR)
        else:
            data_in.seek(2052, SEEK_CUR)

        models_3d_file = Models3DFile.parse(data_in, conf)
        animations_file = AnimationsFile.parse(data_in, conf)

        if conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1):
            n_dpsx_legacy_textures = int.from_bytes(data_in.read(4), 'little')
            data_in.seek(n_dpsx_legacy_textures * 3072, SEEK_CUR)

        strategies_file = StrategiesFile.parse(data_in, conf)
        level_file = LevelFile.parse(data_in, conf)

        # FIXME End of Croc 2 & Croc 2 Demo Dummies' level files aren't reversed yet
        if conf.game not in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1_DUMMY):
            cls.check_size(size, start, data_in.tell())
        return cls(models_3d_file, animations_file, strategies_file, level_file, fallback_data)
from io import BufferedIOBase, SEEK_CUR

from ps1_brender.configuration import Configuration, G, PARSABLE_GAMES
from ps1_brender.wad_sections.BaseBRenderClasses import BaseWADSection
from ps1_brender.wad_sections.DPSX.AnimationsFile import AnimationsFile
from ps1_brender.wad_sections.DPSX.LevelFile import LevelFile
from ps1_brender.wad_sections.DPSX.Models3DFile import Models3DFile
from ps1_brender.wad_sections.DPSX.StrategiesFile import StrategiesFile


class DPSXSection(BaseWADSection):
    codename_str = 'XSPD'
    codename_bytes = b'XSPD'
    supported_games = PARSABLE_GAMES
    section_content_description = "3D models, animations & level geometry"

    def __init__(self, models_3d_file: Models3DFile, animations_file: AnimationsFile,
                 strategies_file: StrategiesFile, level_file: LevelFile):
        self.models_3d_file = models_3d_file
        self.animations_file = animations_file
        self.strategies_file = strategies_file
        self.level_file = level_file

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        size, start = super().parse(raw_data, conf)
        idk1 = raw_data.read(4)
        n_idk_unique_textures = int.from_bytes(raw_data.read(4), 'little')

        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            raw_data.seek(2048, SEEK_CUR)
        else:
            raw_data.seek(2052, SEEK_CUR)

        models_3d_file = Models3DFile.parse(raw_data, conf)
        animations_file = AnimationsFile.parse(raw_data, conf)

        if conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1):
            n_dpsx_legacy_textures = int.from_bytes(raw_data.read(4), 'little')
            raw_data.seek(n_dpsx_legacy_textures * 3072, SEEK_CUR)

        strategies_file = StrategiesFile.parse(raw_data, conf)
        level_file = LevelFile.parse(raw_data, conf)

        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:  # FIXME End of Croc 2 Demo Dummies' level files aren't reversed yet
            cls.check_size(size, start, raw_data.tell())
        return cls(models_3d_file, animations_file, strategies_file, level_file)

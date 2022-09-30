from io import BufferedIOBase, SEEK_CUR

from ps1_argonaut.BaseDataClasses import BaseWADSection
from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.wad_sections.DPSX.AnimationData import AnimationData
from ps1_argonaut.wad_sections.DPSX.LevelFile import LevelFile
from ps1_argonaut.wad_sections.DPSX.Model3DData import Model3DData
from ps1_argonaut.wad_sections.DPSX.ScriptData import ScriptData


class DPSXSection(BaseWADSection):
    codename_str = "XSPD"
    codename_bytes = b"XSPD"
    # FIXME DEBUG
    supported_games = (
        G.CROC_2_PS1,
        G.CROC_2_DEMO_PS1_DUMMY,
        G.HARRY_POTTER_1_PS1,
        G.HARRY_POTTER_2_PS1,
    )
    section_content_description = "3D models, animations & level geometry"

    def __init__(
        self,
        models_3d: list[Model3DData],
        animations: list[AnimationData],
        scripts: list[ScriptData],
        level_file: LevelFile,
        fallback_data: bytes = None,
    ):
        super().__init__(fallback_data)
        self.models_3d = models_3d
        self.animations = animations
        self.scripts = scripts
        self.level_file = level_file

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        fallback_data = super().fallback_parse_data(data_in)
        size, start = super().parse(data_in, conf)
        idk1 = data_in.read(4)
        n_idk_unique_textures = int.from_bytes(data_in.read(4), "little")

        if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
            data_in.seek(2048, SEEK_CUR)
        else:
            data_in.seek(2052, SEEK_CUR)

        n_models_3d = int.from_bytes(data_in.read(4), "little")
        models_3d = [Model3DData.parse(data_in, conf) for _ in range(n_models_3d)]

        n_animations = int.from_bytes(data_in.read(4), "little")
        animations = [AnimationData.parse(data_in, conf) for _ in range(n_animations)]

        if conf.game in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1):
            n_dpsx_legacy_textures = int.from_bytes(data_in.read(4), "little")
            data_in.seek(n_dpsx_legacy_textures * 3072, SEEK_CUR)

        n_scripts = int.from_bytes(data_in.read(4), "little")
        scripts = [ScriptData.parse(data_in, conf) for _ in range(n_scripts)]

        level_file = LevelFile.parse(data_in, conf)

        # FIXME End of Croc 2 & Croc 2 Demo Dummies' level files aren't reversed yet
        if conf.game not in (G.CROC_2_PS1, G.CROC_2_DEMO_PS1_DUMMY):
            cls.check_size(size, start, data_in.tell())
        return cls(models_3d, animations, scripts, level_file, fallback_data)

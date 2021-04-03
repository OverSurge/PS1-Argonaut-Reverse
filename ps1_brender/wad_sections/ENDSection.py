import math
from io import BufferedIOBase
from typing import List

from ps1_brender.configuration import Configuration, G
from ps1_brender.wad_sections.BaseBRenderClasses import BaseWADSection
from ps1_brender.wad_sections.SPSX.SoundFile import SoundFile
from ps1_brender.wad_sections.SPSX.VAGSoundData import VAGSoundData


class ENDSection(BaseWADSection):
    codename_str = ' DNE'
    codename_bytes = b' DNE'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "sound effects, background music & dialogues"

    def __init__(self, size: int, level_sound_effects_vags: List[VAGSoundData], dialogues_bgms_vags: List[VAGSoundData],
                 bgm_only_vags: List[VAGSoundData]):
        super().__init__(size)
        self.level_sound_effects_vags = level_sound_effects_vags
        self.dialogues_bgms_vags = dialogues_bgms_vags
        self.bgm_only_vags = bgm_only_vags

    # noinspection PyMethodOverriding
    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration, sound_file: SoundFile):
        size, start = super().parse(raw_data, conf)
        level_sound_effects_vags = []
        dialogues_bgms_vags = []
        bgm_only_vags = []
        if size != 0:
            if sound_file.has_level_sound_effects:
                for i in range(len(sound_file.level_sound_effect_groups)):
                    raw_data.seek(2048 * math.ceil(raw_data.tell() / 2048))
                    for track in sound_file.level_sound_effects[i]:
                        level_sound_effects_vags.append(
                            VAGSoundData.parse(raw_data, conf, int.from_bytes(track[16:20], 'little'), 1,
                                               int.from_bytes(track[0:4], 'little')))
            raw_data.seek(2048 * math.ceil(raw_data.tell() / 2048))
            for track in sound_file.dialogues_bgms:
                track_flags = track[6]
                assert track_flags & 3 != 3
                channels = 2 if track_flags & 1 else 1
                # See SPSX' Dialogues & BGM descriptors documentation for the 44100 / 4096 ratio explanation
                vag = VAGSoundData.parse(raw_data, conf, int.from_bytes(track[12:16], 'little'), channels,
                                         math.ceil(int.from_bytes(track[4:6], 'little') * (44100 / 4096)))
                dialogues_bgms_vags.append(vag)
                if track_flags & 4:
                    bgm_only_vags.append(vag)

            if conf.game == G.HARRY_POTTER_2_PS1:
                raw_data.seek(2048 * math.ceil(raw_data.tell() / 2048))

            cls.check_size(size, start, raw_data.tell())
        return cls(size, level_sound_effects_vags, dialogues_bgms_vags, bgm_only_vags)

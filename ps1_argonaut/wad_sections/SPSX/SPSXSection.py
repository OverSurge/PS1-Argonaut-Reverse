import logging
from collections import defaultdict
from io import BufferedIOBase, SEEK_CUR
from struct import pack
from typing import Optional

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.utils import round_up_padding
from ps1_argonaut.wad_sections.BaseDataClasses import BaseWADSection
from ps1_argonaut.wad_sections.SPSX.SPSXFlags import SPSXFlags
from ps1_argonaut.wad_sections.SPSX.SoundContainers import CommonSFXContainer, AmbientContainer, LevelSFXContainer, \
    LevelSFXGroupContainer, DialoguesBGMsContainer
from ps1_argonaut.wad_sections.SPSX.Sounds import EffectSound, AmbientSound, DialogueBGMSound


class SPSXSection(BaseWADSection):
    codename_str = 'XSPS'
    codename_bytes = b'XSPS'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "sound effects, background music & dialogues"

    def __init__(self, spsx_flags: SPSXFlags, common_sfx: CommonSFXContainer,
                 ambient_tracks: AmbientContainer, level_sfx_groups: LevelSFXContainer, idk1: int,
                 idk2: int, dialogues_bgms: DialoguesBGMsContainer):
        super().__init__()
        self.spsx_flags = spsx_flags
        self.common_sfx = common_sfx if common_sfx is not None else CommonSFXContainer()
        self.ambient_tracks = ambient_tracks if ambient_tracks is not None else AmbientContainer()
        self.level_sfx_groups = level_sfx_groups if level_sfx_groups is not None else LevelSFXContainer()
        self.idk1 = idk1
        self.idk2 = idk2
        self.dialogues_bgms = dialogues_bgms if dialogues_bgms is not None else DialoguesBGMsContainer()

    @property
    def n_sounds(self):
        return self.n_common_sfx + self.n_ambient_tracks + self.n_level_sfx + self.n_dialogues_bgms

    @property
    def n_common_sfx(self):
        return len(self.common_sfx)

    @property
    def common_sfx_size(self):
        return self.common_sfx.size

    @property
    def n_ambient_tracks(self):
        return len(self.ambient_tracks)

    @property
    def ambient_tracks_size(self):
        return self.ambient_tracks.size

    @property
    def n_level_sfx_groups(self):
        return len(self.level_sfx_groups)

    @property
    def n_level_sfx(self):
        return self.level_sfx_groups.n_sounds

    @property
    def n_dialogues_bgms(self):
        return len(self.dialogues_bgms)

    @property
    def end_gap(self):
        return sum(round_up_padding(group.size) for group in self.level_sfx_groups)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration, *args, **kwargs):
        size, start = super().parse(data_in, conf)

        spsx_flags: SPSXFlags = SPSXFlags(int.from_bytes(data_in.read(4), 'little'))
        assert spsx_flags & 0x2 == 0  # Bit 1 is always unset
        # Bit 0 and 4 are identical
        assert (SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags) == (SPSXFlags.HAS_AMBIENT_TRACKS_ in spsx_flags)

        logging.debug(f"Flags: {str(spsx_flags)}")

        n_sfx = int.from_bytes(data_in.read(4), 'little')
        logging.debug(f"sound effects count: {n_sfx}")

        common_sfx: Optional[CommonSFXContainer] = None
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in spsx_flags:
            common_sfx = CommonSFXContainer(EffectSound.parse(data_in, conf) for _ in range(n_sfx))

        ambient_tracks: Optional[AmbientContainer] = None
        if SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags:
            ambient_tracks_headers_size = int.from_bytes(data_in.read(4), 'little')
            assert ambient_tracks_headers_size % 20 == 0
            n_ambient_tracks = ambient_tracks_headers_size // 20
            ambient_tracks = AmbientContainer(AmbientSound.parse(data_in, conf) for _ in range(n_ambient_tracks))

        # Level sound effects groups
        idk1 = None
        idk2 = None
        level_sfx_groups: Optional[LevelSFXContainer] = None
        if SPSXFlags.HAS_LEVEL_SFX in spsx_flags:
            n_level_sfx_groups = int.from_bytes(data_in.read(4), 'little')
            assert n_level_sfx_groups < 16  #
            idk1 = int.from_bytes(data_in.read(4), 'little')
            idk2 = int.from_bytes(data_in.read(4), 'little')
            n_unique_level_sfx = int.from_bytes(data_in.read(4), 'little')
            level_sfx_groups = LevelSFXContainer(
                LevelSFXGroupContainer.parse(data_in, conf) for _ in range(n_level_sfx_groups))
            level_sfx_groups.parse_groups(data_in, conf)
            assert n_unique_level_sfx <= level_sfx_groups.n_sounds
            data_in.seek(n_unique_level_sfx * 16, SEEK_CUR)  # Duplicated level sound effects mapping, see doc

        # Dialogues & BGMs
        dialogues_bgms: Optional[DialoguesBGMsContainer] = None
        n_dialogues_bgms = int.from_bytes(data_in.read(4), 'little')
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in spsx_flags:
            # Gap between level sound effects and dialogues/BGMs
            end_gap = int.from_bytes(data_in.read(4), 'little')
            assert (end_gap != 0) == (SPSXFlags.HAS_LEVEL_SFX in spsx_flags)
            logging.debug(f"END (DNE) gap: {end_gap}")

            dialogues_bgms = DialoguesBGMsContainer(
                DialogueBGMSound.parse(data_in, conf) for _ in range(n_dialogues_bgms))

            # Common sound effects audio data
            common_sfx_total_size = int.from_bytes(data_in.read(4), 'little')
            assert common_sfx_total_size == common_sfx.size
            common_sfx.parse_vags(data_in, conf)

        # Ambient tracks audio data
        if SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags:
            ambient_tracks_total_size = int.from_bytes(data_in.read(4), 'little')
            assert ambient_tracks_total_size == ambient_tracks.size
            ambient_tracks.parse_vags(data_in, conf)

        cls.check_size(size, start, data_in.tell())
        return cls(spsx_flags, common_sfx, ambient_tracks, level_sfx_groups, idk1, idk2, dialogues_bgms)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration, *args, **kwargs):
        start = super().serialize(data_out, conf)

        data_out.write(pack('<II', self.spsx_flags, self.n_common_sfx))
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in self.spsx_flags:
            self.common_sfx.serialize(data_out, conf)
        if SPSXFlags.HAS_AMBIENT_TRACKS in self.spsx_flags:
            data_out.write((20 * self.n_ambient_tracks).to_bytes(4, 'little'))
            self.ambient_tracks.serialize(data_out, conf)
        if SPSXFlags.HAS_LEVEL_SFX in self.spsx_flags:
            duplicated_level_sfx_mapping = defaultdict(lambda: [255] * 16)
            for group_id, group in enumerate(self.level_sfx_groups):
                for sound_id, sound in enumerate(group):
                    duplicated_level_sfx_mapping[sound.vag.data][group_id + 1] = sound_id
            n_unique_level_sfx = len(duplicated_level_sfx_mapping)
            data_out.write(pack('<4I', self.n_level_sfx_groups, self.idk1, self.idk2, n_unique_level_sfx))
            self.level_sfx_groups.serialize(data_out, conf)
            for group in self.level_sfx_groups:
                group.serialize_children(data_out, conf)
            for mapping in duplicated_level_sfx_mapping.values():
                data_out.write(bytes(mapping))

        data_out.write(self.n_dialogues_bgms.to_bytes(4, 'little'))
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in self.spsx_flags:
            data_out.write(self.end_gap.to_bytes(4, 'little'))
            self.dialogues_bgms.serialize(data_out, conf)
            data_out.write(self.common_sfx_size.to_bytes(4, 'little'))
            for vag in self.common_sfx.vags:
                data_out.write(vag.data)
        if SPSXFlags.HAS_AMBIENT_TRACKS in self.spsx_flags:
            data_out.write(self.ambient_tracks_size.to_bytes(4, 'little'))
            for vag in self.ambient_tracks.vags:
                data_out.write(vag.data)

        end = data_out.tell()
        size = end - start
        data_out.seek(start - 4)
        data_out.write(size.to_bytes(4, 'little'))
        data_out.seek(end)

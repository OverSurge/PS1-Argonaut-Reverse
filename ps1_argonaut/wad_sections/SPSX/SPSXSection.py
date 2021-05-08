import logging
from io import BufferedIOBase, SEEK_CUR
from struct import pack
from typing import Optional

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.wad_sections.BaseDataClasses import BaseWADSection
from ps1_argonaut.wad_sections.SPSX.SPSXFlags import SPSXFlags
from ps1_argonaut.wad_sections.SPSX.SoundContainers import CommonSoundEffectsContainer, AmbientContainer, \
    LevelSoundEffectsContainer, LevelSoundEffectsGroupContainer, DialoguesBGMsContainer
from ps1_argonaut.wad_sections.SPSX.Sounds import EffectSound, AmbientSound, DialogueBGMSound


class SPSXSection(BaseWADSection):
    codename_str = 'XSPS'
    codename_bytes = b'XSPS'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "sound effects, background music & dialogues"

    def __init__(self, spsx_flags: SPSXFlags, common_sound_effects: CommonSoundEffectsContainer,
                 ambient_tracks: AmbientContainer, level_sound_effects_groups: LevelSoundEffectsContainer, idk1: int,
                 idk2: int, n_ff_groups: int, dialogues_bgms: DialoguesBGMsContainer):
        super().__init__()
        self.spsx_flags = spsx_flags
        self.common_sound_effects = common_sound_effects
        self.ambient_tracks = ambient_tracks
        self.level_sound_effects_groups = level_sound_effects_groups
        self.idk1 = idk1
        self.idk2 = idk2
        self.n_ff_groups = n_ff_groups
        self.dialogues_bgms = dialogues_bgms

    @property
    def size(self):
        return 8 + 20 * self.n_common_sound_effects + 4 * (SPSXFlags.HAS_AMBIENT_TRACKS in self.spsx_flags) + \
               20 * self.n_ambient_tracks + 16 * (SPSXFlags.HAS_LEVEL_SFX in self.spsx_flags) + \
               16 * self.n_level_sound_effects_groups + 20 * self.n_level_sound_effects + 16 * self.n_ff_groups + 4 + \
               8 * (SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in self.spsx_flags) + 16 * self.n_dialogues_bgms + \
               self.common_sound_effects_size + 4 * (SPSXFlags.HAS_AMBIENT_TRACKS in self.spsx_flags) + \
               self.ambient_tracks_size

    @property
    def n_common_sound_effects(self):
        return len(self.common_sound_effects)

    @property
    def common_sound_effects_size(self):
        return self.common_sound_effects.size

    @property
    def n_ambient_tracks(self):
        return len(self.ambient_tracks)

    @property
    def ambient_tracks_size(self):
        return self.ambient_tracks.size

    @property
    def n_level_sound_effects_groups(self):
        return len(self.level_sound_effects_groups)

    @property
    def n_level_sound_effects(self):
        return self.level_sound_effects_groups.n_sound_effects

    @property
    def n_dialogues_bgms(self):
        return len(self.dialogues_bgms)

    @property
    def end_gap(self):
        return 0  # FIXME Needs to be re-calculated

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        size, start = super().parse(data_in, conf)

        spsx_flags: SPSXFlags = SPSXFlags(int.from_bytes(data_in.read(4), 'little'))
        assert spsx_flags & 0x2 == 0  # Bit 1 is always unset
        # Bit 0 and 4 are identical
        assert (SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags) == (SPSXFlags.HAS_AMBIENT_TRACKS_ in spsx_flags)

        logging.debug(f"Flags: {spsx_flags}|Level sound effects: {spsx_flags.HAS_LEVEL_SFX}|"
                      f"Common sound effects: {spsx_flags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS}|"
                      f"Ambient tracks: {spsx_flags.HAS_AMBIENT_TRACKS}")

        n_sound_effects = int.from_bytes(data_in.read(4), 'little')
        logging.debug(f"sound effects count: {n_sound_effects}")

        common_sound_effects: Optional[CommonSoundEffectsContainer] = None
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in spsx_flags:
            common_sound_effects = CommonSoundEffectsContainer(
                EffectSound.parse(data_in, conf) for _ in range(n_sound_effects))

        ambient_tracks: Optional[AmbientContainer] = None
        if SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags:
            ambient_tracks_headers_size = int.from_bytes(data_in.read(4), 'little')
            assert ambient_tracks_headers_size % 20 == 0
            n_ambient_tracks = ambient_tracks_headers_size // 20
            ambient_tracks = AmbientContainer(AmbientSound.parse(data_in, conf) for _ in range(n_ambient_tracks))

        # Level sound effects groups
        idk1 = None
        idk2 = None
        n_ff_groups = 0
        level_sound_effects_groups: Optional[LevelSoundEffectsContainer] = None
        if SPSXFlags.HAS_LEVEL_SFX in spsx_flags:
            n_level_sound_effects_groups = int.from_bytes(data_in.read(4), 'little')
            idk1 = int.from_bytes(data_in.read(4), 'little')
            idk2 = int.from_bytes(data_in.read(4), 'little')
            n_ff_groups = int.from_bytes(data_in.read(4), 'little')
            level_sound_effects_groups = LevelSoundEffectsContainer(
                LevelSoundEffectsGroupContainer.parse(data_in, conf) for _ in range(n_level_sound_effects_groups))
            for group in level_sound_effects_groups:
                group.parse_children(data_in, conf)
            data_in.seek(n_ff_groups * 16, SEEK_CUR)  # TODO FF groups reverse

        # Dialogues & BGMs
        dialogues_bgms: Optional[DialoguesBGMsContainer] = None
        n_dialogues_bgms = int.from_bytes(data_in.read(4), 'little')
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in spsx_flags:
            # Gap between level sound effects and dialogues/BGMs
            end_gap = int.from_bytes(data_in.read(4), 'little')
            assert (end_gap != 0) == (SPSXFlags.HAS_LEVEL_SFX in spsx_flags)
            logging.debug(f"DNE (END) gap: {end_gap}")

            dialogues_bgms = DialoguesBGMsContainer(
                DialogueBGMSound.parse(data_in, conf) for _ in range(n_dialogues_bgms))

            # Common sound effects audio data
            common_sound_effects_total_size = int.from_bytes(data_in.read(4), 'little')
            assert common_sound_effects_total_size == common_sound_effects.size
            common_sound_effects.parse_vags(data_in, conf)

        # Ambient tracks audio data
        if SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags:
            ambient_tracks_total_size = int.from_bytes(data_in.read(4), 'little')
            assert ambient_tracks_total_size == ambient_tracks.size
            ambient_tracks.parse_vags(data_in, conf)

        cls.check_size(size, start, data_in.tell())
        return cls(spsx_flags, common_sound_effects, ambient_tracks, level_sound_effects_groups, idk1, idk2,
                   n_ff_groups, dialogues_bgms)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration):
        start = super().serialize(data_out, conf)

        data_out.write(pack('<II', self.spsx_flags, self.n_common_sound_effects))
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in self.spsx_flags:
            self.common_sound_effects.serialize(data_out, conf)
        if SPSXFlags.HAS_AMBIENT_TRACKS in self.spsx_flags:
            data_out.write((20 * self.n_ambient_tracks).to_bytes(4, 'little'))
            self.ambient_tracks.serialize(data_out, conf)
        if SPSXFlags.HAS_LEVEL_SFX in self.spsx_flags:
            data_out.write(pack('<4I', self.n_level_sound_effects_groups, self.idk1, self.idk2, self.n_ff_groups))
            self.level_sound_effects_groups.serialize(data_out, conf)
            for group in self.level_sound_effects_groups:
                group.serialize_children(data_out, conf)
            data_out.write(16 * self.n_ff_groups * b'\xFF')  # TODO FF groups reverse
        data_out.write(self.n_dialogues_bgms.to_bytes(4, 'little'))
        if SPSXFlags.HAS_COMMON_SFX_AND_DIALOGUES_BGMS in self.spsx_flags:
            data_out.write(self.end_gap.to_bytes(4, 'little'))
            self.dialogues_bgms.serialize(data_out, conf)
            data_out.write(self.common_sound_effects_size.to_bytes(4, 'little'))
            for vag in self.common_sound_effects.vags:
                data_out.write(vag.data)
        if SPSXFlags.HAS_AMBIENT_TRACKS in self.spsx_flags:
            data_out.write(self.ambient_tracks_size.to_bytes(4, 'little'))
            for vag in self.ambient_tracks.vags:
                data_out.write(vag.data)

        size = data_out.tell() - start
        data_out.seek(start - 4)
        data_out.write(size.to_bytes(4, 'little'))

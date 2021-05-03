import logging
from io import BufferedIOBase, SEEK_CUR
from typing import Optional

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.wad_sections.BaseDataClasses import BaseWADSection
from ps1_argonaut.wad_sections.SPSX.SPSXFlags import SPSXFlags
from ps1_argonaut.wad_sections.SPSX.SoundDescriptors import SoundsHolder, LevelSoundEffectsGroupsHolder, \
    SoundEffectsDescriptor, SoundEffectsAmbientDescriptor, LevelSoundEffectsGroupDescriptor, DialoguesBGMsDescriptor, \
    DialoguesBGMsHolder


class SPSXSection(BaseWADSection):
    codename_str = 'XSPS'
    codename_bytes = b'XSPS'
    supported_games = (G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
    section_content_description = "sound effects, background music & dialogues"

    def __init__(self, spsx_flags: SPSXFlags, common_sound_effects: SoundsHolder,
                 ambient_tracks: SoundsHolder, level_sound_effects_groups: LevelSoundEffectsGroupsHolder,
                 idk1: int, idk2: int, n_ff_groups: int, dialogues_bgms: DialoguesBGMsHolder):
        self.spsx_flags = spsx_flags
        self.common_sound_effects = common_sound_effects
        self.ambient_tracks = ambient_tracks
        self.level_sound_effects_groups = level_sound_effects_groups
        self.n_ff_groups = n_ff_groups
        self.dialogues_bgms = dialogues_bgms

    @property
    def size(self):
        return 8 + 20 * self.n_common_sound_effects + 4 * (SPSXFlags.HAS_AMBIENT_TRACKS in self.spsx_flags) + \
               20 * self.n_ambient_tracks + 16 * (SPSXFlags.HAS_LEVEL_SOUND_EFFECTS in self.spsx_flags) + \
               16 * self.n_level_sound_effects_groups + 20 * self.n_level_sound_effects + 16 * self.n_ff_groups + 4 + \
               8 * (SPSXFlags.HAS_COMMON_SOUND_EFFECTS in self.spsx_flags) + 16 * self.n_dialogues_bgms + \
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
        return len(self.level_sound_effects_groups.groups)

    @property
    def n_level_sound_effects(self):
        return len(self.level_sound_effects_groups)

    @property
    def n_dialogues_bgms(self):
        return len(self.dialogues_bgms)

    @property
    def dialogues_bgms_total_size(self):
        return sum(dialogue_bgm.size for dialogue_bgm in self.dialogues_bgms.descriptors)

    @classmethod
    def parse(cls, data_in: BufferedIOBase, conf: Configuration):
        size, start = super().parse(data_in, conf)

        spsx_flags: SPSXFlags = SPSXFlags(int.from_bytes(data_in.read(4), 'little'))
        assert spsx_flags & 0x2 == 0  # Bit 1 is always unset
        # Bit 0 and 4 are identical
        assert (SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags) == (SPSXFlags.HAS_AMBIENT_TRACKS_ in spsx_flags)

        logging.debug(f"Flags: {spsx_flags}|Level sound effects: {spsx_flags.HAS_LEVEL_SOUND_EFFECTS}|"
                      f"Common sound effects: {spsx_flags.HAS_COMMON_SOUND_EFFECTS}|"
                      f"Ambient tracks: {spsx_flags.HAS_AMBIENT_TRACKS}")

        n_sound_effects = int.from_bytes(data_in.read(4), 'little')
        logging.debug(f"sound effects count: {n_sound_effects}")

        common_sound_effects: Optional[SoundsHolder] = None
        if SPSXFlags.HAS_COMMON_SOUND_EFFECTS in spsx_flags:
            common_sound_effects = SoundsHolder(
                [SoundEffectsDescriptor.parse(data_in, conf) for _ in range(n_sound_effects)])

        ambient_tracks: Optional[SoundsHolder] = None
        if SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags:
            ambient_tracks_headers_size = int.from_bytes(data_in.read(4), 'little')
            assert ambient_tracks_headers_size % 20 == 0
            n_ambient_tracks = ambient_tracks_headers_size // 20
            ambient_tracks = SoundsHolder(
                [SoundEffectsAmbientDescriptor.parse(data_in, conf) for _ in range(n_ambient_tracks)])

        # Level sound effects groups
        idk1 = None
        idk2 = None
        n_ff_groups = 0
        level_sound_effects_groups: Optional[LevelSoundEffectsGroupsHolder] = None
        if SPSXFlags.HAS_LEVEL_SOUND_EFFECTS in spsx_flags:
            n_level_sound_effects_groups = int.from_bytes(data_in.read(4), 'little')
            idk1 = int.from_bytes(data_in.read(4), 'little')
            idk2 = int.from_bytes(data_in.read(4), 'little')
            n_ff_groups = int.from_bytes(data_in.read(4), 'little')
            level_sound_effects_groups = LevelSoundEffectsGroupsHolder(
                [LevelSoundEffectsGroupDescriptor.parse(data_in, conf) for _ in range(n_level_sound_effects_groups)])

            for group in level_sound_effects_groups.groups:
                group.sounds_holder = SoundsHolder(
                    [SoundEffectsAmbientDescriptor.parse(data_in, conf) for _ in range(group.n_sound_effects)])

            assert sum([group.size for group in level_sound_effects_groups.groups]) == \
                   sum([sum([sound_effect.size for sound_effect in group.sounds_holder.descriptors]) for group in
                        level_sound_effects_groups.groups])
            data_in.seek(n_ff_groups * 16, SEEK_CUR)  # FF groups

        # Dialogues & BGMs
        dialogues_bgms: Optional[DialoguesBGMsHolder] = None
        n_dialogues_bgms = int.from_bytes(data_in.read(4), 'little')
        if SPSXFlags.HAS_COMMON_SOUND_EFFECTS in spsx_flags:
            # Gap between level sound effects and dialogues/BGMs
            end_gap = int.from_bytes(data_in.read(4), 'little')
            assert (end_gap != 0) == (SPSXFlags.HAS_LEVEL_SOUND_EFFECTS in spsx_flags)
            logging.debug(f"DNE (END) gap: {end_gap}")

            dialogues_bgms = \
                DialoguesBGMsHolder([DialoguesBGMsDescriptor.parse(data_in, conf) for _ in range(n_dialogues_bgms)])

            # Common sound effects audio data
            common_sound_effects_total_size = int.from_bytes(data_in.read(4), 'little')
            assert common_sound_effects_total_size == \
                   sum([sound_effect.size for sound_effect in common_sound_effects.descriptors])
            common_sound_effects.parse_vags(data_in, conf)

        # Ambient tracks audio data
        if SPSXFlags.HAS_AMBIENT_TRACKS in spsx_flags:
            ambient_tracks_total_size = int.from_bytes(data_in.read(4), 'little')
            assert ambient_tracks_total_size == \
                   sum([sound_effect.size for sound_effect in ambient_tracks.descriptors])
            ambient_tracks.parse_vags(data_in, conf)

        cls.check_size(size, start, data_in.tell())
        return cls(spsx_flags, common_sound_effects, ambient_tracks, level_sound_effects_groups, idk1, idk2,
                   n_ff_groups, dialogues_bgms)

    def serialize(self, data_out: BufferedIOBase, conf: Configuration):
        size_offset = super().serialize(data_out, conf)

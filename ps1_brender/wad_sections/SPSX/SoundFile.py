import logging
from io import BufferedIOBase, SEEK_CUR
from typing import List

from ps1_brender.configuration import Configuration
from ps1_brender.wad_sections.BaseBRenderClasses import BaseBRenderClass
from ps1_brender.wad_sections.SPSX.VAGSoundData import VAGSoundData


class SoundFile(BaseBRenderClass):
    # TODO Use a custom class for audio headers, with flags in a IntFlag class
    def __init__(self, has_ambient_tracks: bool, has_common_sound_effects: bool, has_level_sound_effects: bool,
                 common_sound_effects: List[bytes], common_sound_effects_vags: List[VAGSoundData],
                 ambient_tracks: List[bytes], ambient_vags: List[VAGSoundData], level_sound_effect_groups: List[bytes],
                 level_sound_effects: List[List[bytes]], dialogues_bgms: List[bytes]):
        self.has_ambient_tracks = has_ambient_tracks
        self.has_common_sound_effects = has_common_sound_effects
        self.has_level_sound_effects = has_level_sound_effects
        self.common_sound_effects = common_sound_effects
        self.common_sound_effects_vags = common_sound_effects_vags
        self.ambient_tracks = ambient_tracks
        self.ambient_vags = ambient_vags
        self.level_sound_effect_groups = level_sound_effect_groups
        self.level_sound_effects = level_sound_effects
        self.dialogues_bgms = dialogues_bgms

        self.dialogues_tracks_sizes_sum = sum([int.from_bytes(x[12:16], 'little') for x in self.dialogues_bgms])
        logging.debug(f"dialogues tracks sum: {self.dialogues_tracks_sizes_sum}")

    @classmethod
    def parse(cls, raw_data: BufferedIOBase, conf: Configuration):
        super().parse(raw_data, conf)
        flags = int.from_bytes(raw_data.read(4), 'little')  # TODO Use a IntFlag class
        has_ambient_tracks = bool(flags & 1)
        assert flags & 2 == 0  # Bit 1 is always unset
        has_common_sound_effects = bool(flags & 4)
        has_level_sound_effects = bool(flags & 8)
        assert has_ambient_tracks == bool(flags & 16)  # Bit 0 and 4 are identical

        logging.debug(f"Flags: {flags}|Level sound effects: {has_level_sound_effects}|"
                      f"Common sound effects: {has_common_sound_effects}|"
                      f"Ambient tracks: {has_ambient_tracks}")

        common_sound_effects = []  # Common sound effects can be found in the majority of the levels
        common_sound_effects_vags: List[VAGSoundData] = []
        ambient_tracks = []
        ambient_vags: List[VAGSoundData] = []

        level_sound_effect_groups = []
        level_sound_effects = []  # Level sound effects are specific to one or some level(s)
        dialogues_bgms = []  # BGM = BackGround Music

        n_sound_effects = int.from_bytes(raw_data.read(4), 'little')
        logging.debug(f"sound effects count: {n_sound_effects}")

        # Common sound effects
        if has_common_sound_effects:
            common_sound_effects = [raw_data.read(20) for _ in range(n_sound_effects)]
            for track in common_sound_effects:
                assert track[8] < 2
                assert track[9:12] in (b'\x01\x01\x00', b'\x00\x00\x00')
                assert track[14:16] == b'\x42\x00'

        # Ambient tracks
        if has_ambient_tracks:
            ambient_tracks_headers_size = int.from_bytes(raw_data.read(4), 'little')
            assert ambient_tracks_headers_size % 20 == 0
            n_ambient_tracks = ambient_tracks_headers_size // 20
            ambient_tracks = [raw_data.read(20) for _ in range(n_ambient_tracks)]

        # Level sound effects groups
        idk1 = None
        idk2 = None
        if has_level_sound_effects:
            level_sound_effects_groups_counts = int.from_bytes(raw_data.read(4), 'little')
            idk1 = raw_data.read(4)
            idk2 = raw_data.read(4)
            logging.debug(f"Level effects groups count: {level_sound_effects_groups_counts}\n"
                          f"Unknown level effects values: {idk1.hex()}({int.from_bytes(idk1, 'little')})/"
                          f"{idk2.hex()}({int.from_bytes(idk2, 'little')})")
            n_ff_groups = int.from_bytes(raw_data.read(4), 'little')

            level_sound_effect_groups = [raw_data.read(16) for _ in range(level_sound_effects_groups_counts)]
            level_sound_effects_groups_counts = []
            for track in level_sound_effect_groups:
                level_sound_effects_groups_counts.append(int.from_bytes(track[4:8], 'little'))

            level_sound_effect_groups_sum = \
                sum([int.from_bytes(x[12:16], 'little') for x in level_sound_effect_groups])
            n_level_sound_effects = sum(level_sound_effects_groups_counts)
            logging.debug(f"Level effects groups sizes sum: {level_sound_effect_groups_sum}\n"
                          f"Level effects count: {n_level_sound_effects}\n")

            # Level sound effects
            level_sound_effects: List[List[bytes]] = []
            level_sound_effects_sum = 0
            for n_sound_effects in level_sound_effects_groups_counts:
                group = []
                for i in range(n_sound_effects):
                    track = raw_data.read(20)
                    assert track[14:16] == b'\x42\x00'
                    group.append(track)
                    level_sound_effects_sum += int.from_bytes(track[16:20], 'little')
                level_sound_effects.append(group)

            logging.debug(f"Level effects sizes sum: {level_sound_effects_sum}")
            assert level_sound_effect_groups_sum == level_sound_effects_sum
            raw_data.seek(n_ff_groups * 16, SEEK_CUR)

        # Dialogues & BGMs
        n_dialogues_bgms = int.from_bytes(raw_data.read(4), 'little')
        logging.debug(f"dialogues count: {n_dialogues_bgms}")
        if has_common_sound_effects:
            # Gap between level sound effects and dialogues/BGMs
            end_gap = int.from_bytes(raw_data.read(4), 'little')
            assert (end_gap != 0) == has_level_sound_effects

            dialogues_bgms = [raw_data.read(16) for _ in range(n_dialogues_bgms)]
            logging.debug(f"DNE (END) gap: {end_gap}")

            # Common sound effects audio data
            declared_size = int.from_bytes(raw_data.read(4), 'little')
            assert declared_size == sum([int.from_bytes(x[16:20], 'little') for x in common_sound_effects])
            for track in common_sound_effects:
                common_sound_effects_vags.append(
                    VAGSoundData.parse(raw_data, conf, int.from_bytes(track[16:20], 'little'), 1,
                                       int.from_bytes(track[0:4], 'little')))

        # Ambient tracks audio data
        if has_ambient_tracks:
            declared_size = int.from_bytes(raw_data.read(4), 'little')
            assert declared_size == sum([int.from_bytes(x[16:20], 'little') for x in ambient_tracks])
            for track in ambient_tracks:
                ambient_vags.append(
                    VAGSoundData.parse(raw_data, conf, int.from_bytes(track[16:20], 'little'), 1,
                                       int.from_bytes(track[0:4], 'little')))

        return cls(has_ambient_tracks, has_common_sound_effects, has_level_sound_effects, common_sound_effects,
                   common_sound_effects_vags, ambient_tracks, ambient_vags, level_sound_effect_groups,
                   level_sound_effects, dialogues_bgms)

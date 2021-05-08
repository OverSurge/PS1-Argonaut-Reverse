from enum import IntFlag


class SPSXFlags(IntFlag):
    HAS_AMBIENT_TRACKS = 0x1
    HAS_COMMON_SFX_AND_DIALOGUES_BGMS = 0x4  # Stored in SPSX, generally found in several levels
    HAS_LEVEL_SFX = 0x8  # Stored in END, generally level-specific
    HAS_AMBIENT_TRACKS_ = 0x10

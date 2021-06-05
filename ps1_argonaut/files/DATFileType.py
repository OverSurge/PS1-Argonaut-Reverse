from enum import Enum
from typing import Tuple

from ps1_argonaut.files.BINFile import BINFile
from ps1_argonaut.files.DEMFile import DEMFile
from ps1_argonaut.files.IMGFile import IMGFile
from ps1_argonaut.files.WADFile import WADFile


def guess_dat_file_type(stem: str, suffix: str):
    for dat_file_type_suffix, dat_file_type in DATFileType.__members__.items():  # type: DATFileType
        if suffix == dat_file_type_suffix and stem not in dat_file_type.excluded_stems:
            return dat_file_type
    return DATFileType.NON_PARSABLE


class DATFileType(Enum):
    BIN = (BINFile,)
    DEM = (DEMFile,)
    IMG = (IMGFile, ('SECURITY', 'KEEP'))
    WAD = (WADFile, ('FESOUND', 'FETHUND'))
    NON_PARSABLE = ()

    def __init__(self, file_class=None, excluded_stems: Tuple[str, ...] = None):
        self.file_class = file_class
        self.excluded_stems = excluded_stems if excluded_stems is not None else []

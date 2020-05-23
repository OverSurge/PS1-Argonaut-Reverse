from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from ps1_brender import *


def parse_dir_dat_paths(input_path: Path, game: str):
    if input_path.is_dir():
        if game != CROC_2_DEMO_PS1_DUMMY:
            dir_path = input_path / dir_dat[game][1]
            dat_path = input_path / dir_dat[game][2]
        else:
            dir_path = None
            dat_path = input_path / dir_dat[game][2]
    elif input_path.is_file():
        if game != CROC_2_DEMO_PS1_DUMMY:
            if input_path.suffix == '.DIR':
                dir_path = input_path
                dat_path = input_path.parent / (input_path.stem + '.DAT')
            else:
                dir_path = input_path.parent / (input_path.stem + '.DIR')
                dat_path = input_path
        else:
            dir_path = None
            dat_path = input_path
    else:
        raise FileNotFoundError
    if (dir_path is not None and not dir_path.is_file()) or not dat_path.is_file():
        raise FileNotFoundError
    return dir_path, dat_path


def slice_dat(dir_path: Optional[Path], dat_path: Path, game: str):
    files_data: List[bytes] = []
    files_names: List[str] = []
    files: List[Tuple[str, int, int]] = []
    if game == CROC_2_DEMO_PS1_DUMMY:
        start = 0
        dat_data = dat_path.read_bytes()
        while True:
            offset = int.from_bytes(dat_data[start:start + 4], 'little')
            suffix = \
                '.WAD' if dat_data[start + 4:start + 8] == b'\x58\x53\x50\x54' else '.DEM'  # WADs start with 'XSPT'
            end = 2048 * np.math.ceil((start + offset) / 2048)
            files_data.append(dat_data[start:end])
            files_names.append(hex(start)[2:].rjust(7, '0') + suffix)
            start = end
            if end >= len(dat_data):
                break
    else:
        dir_len = dir_dat[game][0]
        dir_data = dir_path.read_bytes()
        for i in range(4 + dir_len, len(dir_data) + 4, dir_len):
            name = dir_data[i - dir_len:i - dir_len + 12].decode('ASCII').replace('\x00', '')
            size = int.from_bytes(dir_data[i - dir_len + 12:i - dir_len + 16], 'little')
            start = int.from_bytes(dir_data[i - dir_len + 16:i - dir_len + 20], 'little')
            files.append((name, size, start))

        n_files = int.from_bytes(dir_data[:4], 'little')
        if len(files) != n_files:
            raise ReverseError(f"File count mismatch : {len(files)} found instead of {n_files} expected.")

        dat_data = dat_path.read_bytes()
        for file in files:
            files_data.append(dat_data[file[2]:file[2] + file[1]])
            files_names.append(file[0])

    return files_data, files_names


def parse_and_slice(input_path: Path, game: str):
    dir_path, dat_path = parse_dir_dat_paths(input_path, game)
    return slice_dat(dir_path, dat_path, game)

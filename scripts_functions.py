import math
from pathlib import Path
from typing import List, Optional, Tuple

from ps1_argonaut.configuration import G
from ps1_argonaut.errors_warnings import ReverseError


def parse_dir_dat_paths(input_path: Path, game: G):
    if input_path.is_dir():
        if game != G.CROC_2_DEMO_PS1_DUMMY:
            dir_path = input_path / game.dir_filename
            dat_path = input_path / game.dat_filename
        else:  # CROC 2 DEMO DUMMY file has no .DIR file
            dir_path = None
            dat_path = input_path / game.dat_filename
    elif input_path.is_file():
        if game != G.CROC_2_DEMO_PS1_DUMMY:
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


def slice_dat(dir_path: Optional[Path], dat_path: Path, game: G):
    files_data: List[bytes] = []
    files_names: List[str] = []
    files: List[Tuple[str, int, int]] = []
    if game == G.CROC_2_DEMO_PS1_DUMMY:
        start = 0
        dat_data = dat_path.read_bytes()
        while True:
            offset = int.from_bytes(dat_data[start:start + 4], 'little')
            # WADs start with the 'XSPT' codename
            suffix = '.WAD' if dat_data[start + 4:start + 8] == b'XSPT' else '.DEM'
            end = 2048 * math.ceil((start + offset) / 2048)
            files_data.append(dat_data[start:end])
            files_names.append(hex(start)[2:].rjust(7, '0') + suffix)
            start = end
            if end >= len(dat_data):
                break
    else:
        dir_len = game.dir_descriptor_size
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


def parse_and_slice(input_path: Path, game: G):
    dir_path, dat_path = parse_dir_dat_paths(input_path, game)
    return slice_dat(dir_path, dat_path, game)

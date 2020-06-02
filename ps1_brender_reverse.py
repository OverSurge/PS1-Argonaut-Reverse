import argparse
from pathlib import Path
from typing import List, Tuple, Union

from ps1_brender import *
from ps1_brender.wad_sections import WADFile
from scripts_functions import parse_and_slice

parser = argparse.ArgumentParser(
    description="Utility to extract data and display information about BRender games like Croc 1 & 2. By OverSurge.")
parser.add_argument("game", type=str, choices=EXTRACTABLE_GAMES,
                    help="The game the file(s) are from. If it is not listed, choose one close to it.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-dirdat", action='append', type=str,
                   help="Where the DIR/DAT files are located", metavar="DIR_DAT_PATH")
group.add_argument("-wad", action='append', type=str,
                   help="The file path to a WAD file / a folder containing WAD files", metavar="WAD_PATH")
parser.add_argument("-tex", "--extract-textures", type=str, help="Extracts textures to the given folder",
                    metavar="FOLDER_PATH")
parser.add_argument("-all", "--process-all-sections", action='store_true',
                    help="By default, this script only reads textures information to greatly reduce the processing "
                         "duration. This option forces the processing of 3D models & animations.")
parser.add_argument("--ignore-warnings", action='store_true',
                    help="Allows the program to continue its execution after triggering a warning.")
args = parser.parse_args()


def parse_files(paths: Union[List[Path], Tuple[Path]], separated_wads: bool):
    if args.game not in PARSABLE_GAMES:
        raise NotImplementedError("Files from this game can be extracted, but not reversed (yet). "
                                  "If you just want to extract them, use the dat_slicing.py script.")
    wads_data: List[bytes] = []
    wads_names: List[str] = []
    if separated_wads:
        for wad_path in paths:
            wads_data.append(wad_path.read_bytes())
            wads_names.append(wad_path.name)
    else:
        for dir_dat_path in paths:
            files_data, files_names = parse_and_slice(dir_dat_path, args.game)
            for i in range(len(files_names)):
                if files_names[i][-4:] == '.WAD':
                    wads_data.append(files_data[i])
                    wads_names.append(files_names[i])
    for i in range(len(wads_names)):
        try:
            print(f"Processing {wads_names[i]}..")
            # The processing is sped up by ignoring other sections than XSPT (animations calculations are long)
            wad_file = WADFile(wads_data[i], 0,
                               Configuration(args.game, args.ignore_warnings, args.process_all_sections))
            wad_print = f"{wad_file.xspt.texture_file.n_textures:>4} textures"
            if args.extract_textures:
                wad_file.xspt.texture_file.generate_colorized_texture().save(tex_path / f"{wads_names[i][:-4]}.PNG")
            if args.process_all_sections:
                wad_print += f", {wad_file.xspd.model_file.n_models:>4} models, " \
                             f"{wad_file.xspd.animation_file.n_animations:>4} animations"
            print(wad_print)
        except SectionNameError:
            print("Not a correct WAD file (generally FESOUND or FETHUND)")


if args.extract_textures:
    tex_path = Path(args.extract_textures)
    if tex_path.is_file():
        raise FileExistsError
    elif not tex_path.exists():
        tex_path.mkdir()

if args.dirdat:
    for dat in args.dirdat:  # type: str
        path = Path(dat)
        parse_files((path,), False)

if args.wad:
    for wad in args.wad:  # type: str
        path = Path(wad)
        if path.is_dir():
            parse_files([wad_path for wad_path in path.glob('*.wad')], True)
        elif path.is_file():
            parse_files((path,), True)
        else:
            raise FileNotFoundError

print("No error encountered (Textures, 3D models and animations processed)." if args.process_all_sections else
      "No error encountered (Note that only textures were processed, see this script's help for more).")

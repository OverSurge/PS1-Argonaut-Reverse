import argparse
from pathlib import Path
from typing import List, Tuple, Union

from ps1_brender.configuration import Configuration, PARSABLE_GAMES, PARSABLE_SECTIONS, SLICEABLE_GAMES, SUPPORTED_GAMES
from ps1_brender.errors_warnings import SectionNameError
from ps1_brender.wad_sections.WAD import WAD
from scripts_functions import parse_and_slice

parser = argparse.ArgumentParser(
    description="Utility to extract data and display information about BRender games like Croc 1 & 2. By OverSurge.")
parser.add_argument("game", type=str, choices=[game.title for game in SLICEABLE_GAMES],
                    help="The game the file(s) are from. If it is not listed, choose one close to it.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-dirdat", action='append', type=str,
                   help="Where the DIR/DAT files are located.", metavar="DIR_DAT_PATH")
group.add_argument("-wad", action='append', type=str,
                   help="The file path to a WAD file / a folder containing WAD files", metavar="WAD_PATH")
parser.add_argument("-tex", "--extract-textures", type=str, help="Extracts textures to the given folder.",
                    metavar="FOLDER_PATH")
parser.add_argument("-mod", "--extract-models", type=str, help="Extracts 3D models to the given folder.",
                    metavar="FOLDER_PATH")
parser.add_argument("-aud", "--extract-audio", type=str, help="Extracts audio tracks to the given folder.",
                    metavar="FOLDER_PATH")
parser.add_argument("-lvl", "--extract-levels", type=str, help="Extracts levels as 3D models to the given folder.",
                    metavar="FOLDER_PATH")
parser.add_argument("-all", "--process-all-sections", action='store_true',
                    help="DEBUG | By default, this script only reads textures information to greatly reduce the "
                         "processing duration. This option forces the processing of 3D models & animations.")
parser.add_argument("-v", "--verbose", action='store_true', help="Enables debug prints")
parser.add_argument("--ignore-warnings", action='store_true',
                    help="Allows the program to continue its execution after triggering a warning.")
args = parser.parse_args()
args.game = next((game for game in SUPPORTED_GAMES if game.title == args.game), None)


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
    parse_sections = PARSABLE_SECTIONS if args.process_all_sections else ['XSPT', 'XSPD']
    if args.extract_audio:
        parse_sections.extend(('XSPS', ' DNE'))
    if args.extract_models:
        input("Models extraction is VERY EXPERIMENTAL, some models will be completely broken or even missing. "
              "Press <Enter> to continue.\n")
    for i in range(len(wads_names)):
        try:
            print(f"Processing {wads_names[i]:>12}.. ", end='')
            wad_file = WAD.parse(
                wads_data[i], Configuration(args.game, args.ignore_warnings, parse_sections, args.verbose))
            titles = ', '.join([x.strip(' \0') for x in wad_file.titles])
            print(f"({titles})\n  ", end='')

            if 'XSPT' in parse_sections:
                print(f" {wad_file.tpsx.texture_file.n_textures:>4} texture(s)", end=' ')
            if args.extract_textures:
                wad_file.tpsx.texture_file.generate_colorized_texture().save(tex_path / f"{wads_names[i][:-4]}.PNG")

            if 'XSPS' in parse_sections:
                if wad_file.spsx:
                    total_tracks = len(wad_file.common_sound_effects) + len(wad_file.level_sound_effects) + \
                                   len(wad_file.dialogues_bgms) + len(wad_file.ambient_tracks)
                    print(f" {total_tracks:>3} audio file(s)", end=' ')
            if args.extract_audio:
                wad_audio_folder_path = Path(args.extract_audio) / wads_names[i][:-4]
                if not wad_audio_folder_path.exists():
                    wad_audio_folder_path.mkdir()
                elif wad_audio_folder_path.is_file():
                    raise FileExistsError
                wad_file.extract_audio(wad_audio_folder_path, wads_names[i][:-4])

            if 'XSPD' in parse_sections:
                print(f" {wad_file.dpsx.models_3d_file.n_models:>4} model(s)"
                      f" {wad_file.dpsx.animations_file.n_animations:>4} animation(s)"
                      f" {wad_file.dpsx.level_file.chunks_matrix.n_filled_chunks:>4} chunk(s)", end=' ')
            if args.extract_models:
                wad_file.extract_experimental_models(Path(args.extract_models) / wads_names[i][:-4],
                                                     wads_names[i][:-4])
            if args.extract_levels:
                wad_level_folder_path = Path(args.extract_levels) / "No actors - No lighting" / wads_names[i][:-4]
                wad_file.extract_level(wad_level_folder_path, wads_names[i][:-4])

            print('\n')
        except SectionNameError:
            print("\n  /!\\ Not a correct WAD file (generally FESOUND or FETHUND)")
    if len(wads_names) == 0:
        print("/!\\ There are no WADs in this folder.")
    else:
        print("No error encountered.")


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

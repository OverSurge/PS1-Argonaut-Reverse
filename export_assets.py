import argparse
import sys
from pathlib import Path

from ps1_argonaut.DIR_DAT import DIR_DAT, DATFile
from ps1_argonaut.configuration import Configuration, PARSABLE_GAMES, SLICEABLE_GAMES, SUPPORTED_GAMES
from ps1_argonaut.errors_warnings import SectionNameError
from ps1_argonaut.wad_sections.DPSX.DPSXSection import DPSXSection
from ps1_argonaut.wad_sections.SPSX.SPSXSection import SPSXSection
from ps1_argonaut.wad_sections.TPSX.TPSXSection import TPSXSection


def parse_args(_args):
    parser = argparse.ArgumentParser(
        description="Utility to extract data and display information about PS1 Argonaut games like Croc 2 or "
                    "Harry Potter. By OverSurge.")
    parser.add_argument("game", type=str, choices=[g.title for g in SLICEABLE_GAMES],
                        help="The game the file(s) are from. If it is not listed, choose one close to it.")

    data_source = parser.add_mutually_exclusive_group(required=True)
    data_source.add_argument("-dirdat", type=str, help="Where the DIR/DAT files are located.", metavar="DIR_DAT_PATH")
    data_source.add_argument("-wad", action='append', type=str,
                             help="Path(s) to WAD file(s) / folder(s) containing WAD files", metavar="WAD_PATH")

    parser.add_argument("-tex", "--export-textures", type=str, help="Extracts textures to the given folder.",
                        metavar="FOLDER_PATH")
    parser.add_argument("-mod", "--export-models", type=str, help="Extracts 3D models to the given folder.",
                        metavar="FOLDER_PATH")
    parser.add_argument("-aud", "--export-audio", type=str, help="Extracts audio tracks to the given folder.",
                        metavar="FOLDER_PATH")
    parser.add_argument("-lvl", "--export-levels", type=str, help="Extracts levels as 3D models to the given folder.",
                        metavar="FOLDER_PATH")
    parser.add_argument("-all", "--process-all-sections", action='store_true',
                        help="DEBUG | By default, this script only reads textures information to greatly reduce the "
                             "processing duration. This option forces the processing of 3D models & animations.")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enables debug prints")
    parser.add_argument("--ignore-warnings", action='store_true',
                        help="Allows the program to continue its execution after triggering a warning.")
    parser.add_argument("--no-confirm", action='store_true', help="Automatically answers questions.")
    return parser.parse_args(_args)


def create_export_directory(path: Path):
    if path.is_file():
        raise FileExistsError
    elif not path.exists():
        path.mkdir(parents=True)


def export_assets_from_wad(wad: DATFile, args, conf: Configuration):
    wad_file = wad.file
    titles = ', '.join([title.strip(' \0') for title in wad_file.titles])
    print(f": Game level ({titles})\n ", end='')

    if conf.game in TPSXSection.supported_games:
        print(f" {wad_file.tpsx.texture_file.n_textures:>4} texture(s)", end=' ')
        if args.export_textures:
            wad_file.tpsx.texture_file.generate_colorized_texture().save(Path(args.export_textures) / f"{wad.stem}.PNG")

    if conf.game in SPSXSection.supported_games:
        print(f" {wad_file.spsx.n_sounds:>3} audio file(s)", end=' ')
        if args.export_audio:
            wad_audio_folder_path = Path(args.export_audio) / wad.stem
            create_export_directory(wad_audio_folder_path)
            wad_file.export_audio(wad_audio_folder_path, wad.stem)

    if conf.game in DPSXSection.supported_games:
        print(f" {wad_file.dpsx.models_3d_file.n_models:>4} model(s)"
              f" {wad_file.dpsx.animations_file.n_animations:>4} animation(s)"
              f" {wad_file.dpsx.level_file.chunks_matrix.n_filled_chunks:>4} chunk(s)", end=' ')
        if args.export_models:
            wad_models_3d_folder_path = Path(args.export_models) / wad.stem
            create_export_directory(wad_models_3d_folder_path)
            wad_file.export_experimental_models(wad_models_3d_folder_path, wad.stem)
        if args.export_levels:
            wad_level_folder_path = Path(args.export_levels) / "No actors - No lighting" / wad.stem
            create_export_directory(wad_level_folder_path)
            wad_file.export_level(wad_level_folder_path, wad.stem)


def export_assets(args):
    def parse_files():
        n_files = len(dir_dat)
        n_digits = len(str(n_files))
        for i, dat_file in enumerate(dir_dat):  # type: int, DATFile
            print(f"[{i + 1:>{n_digits}}/{n_files}] {dat_file.name:>12}", end='')
            try:
                dat_file.parse(conf)
                if dat_file.suffix == 'WAD':
                    export_assets_from_wad(dat_file, args, conf)
            except SectionNameError:
                print("\n  /!\\ Not a correct WAD file (generally FESOUND or FETHUND)")
            print('\n')

    exports = (args.export_textures, args.export_models, args.export_audio, args.export_levels)
    game = next((game for game in SUPPORTED_GAMES if game.title == args.game), None)
    if game not in PARSABLE_GAMES:
        raise NotImplementedError("Files from this game can be extracted, but not reversed (yet). "
                                  "If you just want to extract them, use the extract_files_from_dat.py script.")

    conf = Configuration(game, args.ignore_warnings)

    if args.dirdat:
        dir_dat = DIR_DAT.from_dir_dat(Path(args.dirdat), conf)
    else:  # args.wad
        dir_dat = DIR_DAT.from_files(Path(file) for file in args.wad)

    for export in exports:
        if export:
            create_export_directory(Path(export))

    parse_files()


if __name__ == '__main__':
    _args = parse_args(sys.argv[1:])
    if _args.export_models and not _args.no_confirm:
        input("Models export is VERY EXPERIMENTAL, some models will be completely broken or even missing. "
              "Press <Enter> to continue.\n")

    export_assets(_args)

    print("No error encountered.")

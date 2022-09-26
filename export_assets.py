import argparse
import sys
from pathlib import Path

from ps1_argonaut.configuration import Configuration, PARSABLE_GAMES, SLICEABLE_GAMES, SUPPORTED_GAMES
from ps1_argonaut.DIR_DAT import DIR_DAT
from ps1_argonaut.files.DATFile import DATFile
from ps1_argonaut.files.IMGFile import IMGFile
from ps1_argonaut.files.WADFile import WADFile
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
    data_source.add_argument("-files", action='append', type=str, metavar="FILES_PATH",
                             help="Path(s) to WAD/IMG/etc. file(s) / folder(s) containing some of them. "
                                  "DON'T use this for DIR/DAT files, use -dirdat instead.")

    parser.add_argument("-tex", "--export-textures", type=str, help="Extracts WAD textures to the given folder.",
                        metavar="FOLDER_PATH")
    parser.add_argument("-mod", "--export-models", type=str, help="Extracts WAD 3D models to the given folder.",
                        metavar="FOLDER_PATH")
    parser.add_argument("-aud", "--export-audio", type=str,
                        help="Extracts WAD audio tracks to the given folder (WAV format).",
                        metavar="FOLDER_PATH")
    parser.add_argument("--unpack-audio", type=str,
                        help="Unpack WAD audio tracks to the given folder (PS1 VAG format).",
                        metavar="FOLDER_PATH")
    parser.add_argument("-lvl", "--export-levels", type=str,
                        help="Extracts WAD levels as 3D models to the given folder.",
                        metavar="FOLDER_PATH")
    parser.add_argument('-img', "--export-images", type=str, help="Extracts .IMG files to the given folder.")
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


def export_images_from_img(img_file: IMGFile, output_dir: Path):
    if len(img_file) == 1:
        img_file[0].save(output_dir / f"{img_file.stem}.PNG")
    else:
        for i, image in enumerate(img_file):
            image.save(output_dir / f"{img_file.stem}_{i}.PNG")


def export_assets_from_wad(wad_file: WADFile, args, conf: Configuration):
    if conf.game in TPSXSection.supported_games:
        if args.export_textures:
            wad_file.tpsx.texture_file.to_colorized_texture().save(Path(args.export_textures) / f"{wad_file.stem}.PNG")

    if conf.game in SPSXSection.supported_games:
        if args.export_audio:
            wad_audio_export_folder_path = Path(args.export_audio) / wad_file.stem
            create_export_directory(wad_audio_export_folder_path)
            wad_file.export_audio_to_wav(wad_audio_export_folder_path, wad_file.stem)

        if args.unpack_audio:
            wad_audio_unpack_folder_path = Path(args.unpack_audio) / wad_file.stem
            create_export_directory(wad_audio_unpack_folder_path)
            wad_file.export_audio_to_vag(wad_audio_unpack_folder_path, wad_file.stem)

    if conf.game in DPSXSection.supported_games:
        if args.export_models:
            wad_models_3d_folder_path = Path(args.export_models) / wad_file.stem
            create_export_directory(wad_models_3d_folder_path)
            wad_file.export_experimental_models(wad_models_3d_folder_path, wad_file.stem)
        if args.export_levels:
            wad_level_folder_path = Path(args.export_levels) / "No actors - No lighting" / wad_file.stem
            create_export_directory(wad_level_folder_path)
            wad_file.export_level(wad_level_folder_path, wad_file.stem)


def export_assets(args):
    def parse_files():
        n_files = len(dir_dat)
        n_digits = len(str(n_files))
        for i, dat_file in enumerate(dir_dat):  # type: int, DATFile
            print(f"[{i + 1:>{n_digits}}/{n_files}] {dat_file.name:>12}: ", end='')
            if isinstance(dat_file, IMGFile) and args.export_images:
                dat_file.parse(conf)
                export_images_from_img(dat_file, Path(args.export_images))
            elif isinstance(dat_file, WADFile) and wads_parsing_needed:
                dat_file.parse(conf)
                export_assets_from_wad(dat_file, args, conf)
            print(dat_file, end='\n\n')

    game = next((game for game in SUPPORTED_GAMES if game.title == args.game), None)
    if game not in PARSABLE_GAMES:
        raise NotImplementedError("Files from this game can be extracted, but not reversed (yet). "
                                  "If you just want to extract them, use the extract_files_from_dat.py script.")

    conf = Configuration(game, args.ignore_warnings)

    if args.dirdat:
        dir_dat = DIR_DAT.from_dir_dat(Path(args.dirdat), conf)
    else:  # args.files
        dir_dat = DIR_DAT.from_files(*(Path(file) for file in args.files))

    export_paths = (args.export_images, args.export_textures, args.export_models, args.export_audio, args.unpack_audio,
                    args.export_levels)
    wads_parsing_needed = any(
        (args.export_textures, args.export_models, args.export_audio, args.unpack_audio, args.export_levels))
    [create_export_directory(Path(export_path)) for export_path in export_paths if export_path]
    parse_files()


if __name__ == '__main__':
    _args = parse_args(sys.argv[1:])
    if _args.export_models and not _args.no_confirm:
        input("Models export is VERY EXPERIMENTAL, some models will be completely broken or even missing. "
              "Press <Enter> to continue.\n")

    export_assets(_args)

    print("No error encountered.")

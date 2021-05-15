import argparse
from pathlib import Path

from ps1_argonaut.DIR_DAT import DIR_DAT
from ps1_argonaut.configuration import SLICEABLE_GAMES, SUPPORTED_GAMES, Configuration

parser = argparse.ArgumentParser(
    description="Utility to extract WAD files from PS1 Argonaut games like Croc 2 or Harry Potter. By OverSurge.")
parser.add_argument("game", type=str, choices=[game.title for game in SLICEABLE_GAMES],
                    help="The game the files are from. If it is not listed, choose one you think is the closest.")
parser.add_argument("dirdat", type=str,
                    help="Where the DIR/DAT files are located.")
parser.add_argument("output_dir", type=str, help="Where to extract the WADs.")
args = parser.parse_args()
args.game = next((game for game in SUPPORTED_GAMES if game.title == args.game), None)
conf = Configuration(args.game, True, False)

input_path = Path(args.dirdat)
output_path = Path(args.output_dir)

if output_path.is_file():
    raise FileExistsError

dir_dat = DIR_DAT.from_dir_dat(input_path, conf)

if not output_path.is_dir():
    output_path.mkdir()

for dat_file in dir_dat:
    dat_file.serialize(output_path / dat_file.name, conf)

print(f"{len(dir_dat)} files successfully extracted to {output_path}")

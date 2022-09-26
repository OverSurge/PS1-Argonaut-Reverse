from io import BytesIO, SEEK_CUR
from pathlib import Path
from typing import Iterable, List, Type

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.files.DATFile import DATFile
from ps1_argonaut.files.DATFileType import guess_dat_file_type
from ps1_argonaut.utils import pad_in_2048_bytes, pad_out_2048_bytes
from ps1_argonaut.wad_sections.TPSX.TPSXSection import TPSXSection


def parse_dat_file(name: str, data: bytes):
    stem, suffix = name.rsplit('.', 1)
    dat_class: Type[DATFile] = guess_dat_file_type(stem, suffix).file_class
    if dat_class is None:
        dat_file = DATFile(stem, suffix, data)
    else:
        dat_file = dat_class(stem, data=data)
    return dat_file


# noinspection PyPep8Naming
class DIR_DAT(List[DATFile]):
    def __init__(self, files: Iterable[DATFile] = None):
        super().__init__(files if files else [])

    @staticmethod
    def find_dir_dat_files(input_path: Path, conf: Configuration):
        if input_path.is_dir():
            # CROC 2 DEMO DUMMY file has no .DIR file
            dir_path = input_path / conf.game.dir_filename if conf.game != G.CROC_2_DEMO_PS1_DUMMY else None
            dat_path = input_path / conf.game.dat_filename
        elif input_path.is_file():
            if conf.game != G.CROC_2_DEMO_PS1_DUMMY:
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
        return dir_path, dat_path

    @classmethod
    def from_dir_dat(cls, input_path: Path, conf: Configuration):
        dir_path, dat_path = cls.find_dir_dat_files(input_path, conf)
        files = []

        with open(dat_path, 'rb') as dat_data:
            if dir_path is not None:
                with open(dir_path, 'rb') as dir_data:
                    n_files = int.from_bytes(dir_data.read(4), 'little')
                    for i in range(n_files):
                        name, size, start = conf.game.dir_struct.unpack(dir_data.read(conf.game.dir_struct.size))
                        dat_data.seek(start)
                        files.append(parse_dat_file(name.strip(b'\x00').decode('ASCII'), dat_data.read(size)))
            else:  # Croc 2 Demo DUMMY
                while True:
                    name = hex(dat_data.tell())[2:].rjust(7, '0')
                    size_bytes = dat_data.read(4)
                    size = int.from_bytes(size_bytes, 'little')
                    if size == 0:
                        break
                    # WADs start with the 'XSPT' codename
                    suffix = '.WAD' if dat_data.read(4) == TPSXSection.codename_bytes else '.DEM'
                    dat_data.seek(-4, SEEK_CUR)
                    data = dat_data.read(size - 4)
                    pad_in_2048_bytes(dat_data)
                    files.append(parse_dat_file(name + suffix, size_bytes + data))
        return cls(files)

    @classmethod
    def from_files(cls, *files: Path):
        all_files = []
        for file in files:
            if file.is_dir():
                all_files.extend(file for file in file.rglob('*') if file.is_file())
            elif file.is_file():
                all_files.append(file)
        return cls(parse_dat_file(file.name, file.read_bytes()) for file in all_files)

    def serialize(self, output_folder: Path, conf: Configuration):
        dir_output = BytesIO()
        dat_output = BytesIO()

        if output_folder.is_file():
            raise FileExistsError()
        elif not output_folder.exists():
            output_folder.mkdir(parents=True)

        if conf.game != G.CROC_1_PS1:
            dir_output.write(len(self).to_bytes(4, 'little'))

        for file in self:
            start = dat_output.tell()
            file.serialize(dat_output, conf)
            size = dat_output.tell() - start
            pad_out_2048_bytes(dat_output)
            dir_output.write(conf.game.dir_struct.pack(file.name.encode('ASCII'), size, start))

        with open(output_folder / conf.game.dir_filename, 'wb') as dir_file:
            dir_output.seek(0)
            dir_file.write(dir_output.read())

        with open(output_folder / conf.game.dat_filename, 'wb') as dat_file:
            dat_output.seek(0)
            dat_file.write(dat_output.read())

        dir_output.close()
        dat_output.close()

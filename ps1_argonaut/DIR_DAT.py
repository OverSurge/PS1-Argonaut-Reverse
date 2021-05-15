from io import BytesIO, BufferedIOBase, SEEK_CUR
from pathlib import Path
from typing import List, Union, Optional, Iterable

from ps1_argonaut.configuration import Configuration, G
from ps1_argonaut.utils import pad_out_2048_bytes, pad_in_2048_bytes
from ps1_argonaut.wad_sections.TPSX.TPSXSection import TPSXSection
from ps1_argonaut.wad_sections.WAD import WAD


class DATFile:
    def __init__(self, name: str, data: bytes = None):
        if len(name) > 12 or '.' not in name:
            raise ValueError('The engine uses "8.3 filenames" (8-characters stem, dot then 3-characters extension), '
                             'please use a compatible filename.')
        self.stem, self.suffix = name.rsplit('.', 1)
        self.data = data
        self.file: Optional[WAD] = None

    @property
    def name(self):
        return f"{self.stem}.{self.suffix}"

    def parse(self, conf: Configuration):
        if self.suffix == 'WAD':
            self.file = WAD.parse(self.data, conf)
            self.data = None

    def serialize(self, data_out: Union[Path, BufferedIOBase], conf: Configuration):
        if self.file is not None:
            self.file.serialize(data_out, conf)
        elif self.data is not None:
            if isinstance(data_out, Path):
                data_out.write_bytes(self.data)
            elif isinstance(data_out, BufferedIOBase):
                data_out.write(self.data)
            else:
                raise TypeError


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
                    for _ in range(n_files):
                        name, size, start = conf.game.dir_struct.unpack(dir_data.read(conf.game.dir_struct.size))
                        dat_data.seek(start)
                        files.append(DATFile(name.decode('ASCII'), dat_data.read(size)))
            else:  # Croc 2 Demo DUMMY
                while True:
                    name = hex(dat_data.tell())[2:].rjust(7, '0')
                    size_bytes = dat_data.read(4)
                    size = int.from_bytes(size_bytes, 'little')
                    if size == 0:
                        break
                    print("size", size)
                    # WADs start with the 'XSPT' codename
                    suffix = '.WAD' if dat_data.read(4) == TPSXSection.codename_bytes else '.DEM'
                    dat_data.seek(-4, SEEK_CUR)
                    data = dat_data.read(size - 4)
                    pad_in_2048_bytes(dat_data)
                    print(dat_data.tell())
                    files.append(DATFile(name + suffix, size_bytes + data))
        return cls(files)

    @classmethod
    def from_files(cls, files: Iterable[Path]):
        all_files = []
        for file in files:
            if file.is_dir():
                all_files.extend(file for file in file.rglob('*') if file.is_file())
            elif file.is_file():
                all_files.append(file)
        return cls(DATFile(file.name, file.read_bytes()) for file in all_files)

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

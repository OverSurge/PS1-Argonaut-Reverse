from io import BufferedIOBase
from pathlib import Path
from typing import Union

from ps1_argonaut.configuration import Configuration


class DATFile:
    suffix: str

    def __init__(self, stem: str, suffix: str = None, data: bytes = None, *args, **kwargs):
        if data is not None:
            self._data = data

        self.suffix = suffix if suffix is not None else self.__class__.suffix

        if len(stem) > 8 or len(self.suffix) > 3:
            raise ValueError('The engine uses "8.3 filenames" (8-characters stem, dot then 3-characters extension), '
                             'please use a compatible filename.')
        self.stem = stem

    @property
    def name(self):
        return f"{self.stem}.{self.suffix}"

    def __str__(self):
        return "(?) Unknown file"

    def parse(self, conf: Configuration, *args, **kwargs):
        pass

    def end_parse(self):
        if hasattr(self, '_data'):
            del self._data

    def serialize(self, data_out: Union[Path, BufferedIOBase], conf: Configuration):
        if isinstance(data_out, Path):
            data_out.write_bytes(self._data)
        elif isinstance(data_out, BufferedIOBase):
            data_out.write(self._data)
        else:
            raise TypeError

import logging
from enum import Enum
from typing import Tuple


class G(Enum):
    def __init__(self, title: str, release_year: int, dat_filename: str = None, dir_filename: str = None,
                 dir_descriptor_size: int = None):
        self.title = title
        self.release_year = release_year
        self.dir_filename = dir_filename
        self.dat_filename = dat_filename
        self.dir_descriptor_size = dir_descriptor_size

    CROC_1_PS1 = ("Croc 1 PS1", 1997, 'CROCFILE.1', 'CROCFILE.DIR', 24)
    CROC_2_PS1 = ("Croc 2 PS1", 1999, 'CROCII.DAT', 'CROCII.DIR', 20)
    CROC_2_DEMO_PS1 = ("Croc 2 Demo PS1", 1999, 'CROCII.DAT', 'CROCII.DIR', 20)
    CROC_2_DEMO_PS1_DUMMY = ("Croc 2 Demo PS1 (Dummy)", 1999, 'DUMMY.DAT', None, None)
    HARRY_POTTER_1_PS1 = ("Harry Potter 1 PS1", 2001, 'POTTER.DAT', 'POTTER.DIR', 20)
    HARRY_POTTER_2_PS1 = ("Harry Potter 2 PS1", 2002, 'POTTER.DAT', 'POTTER.DIR', 20)


class Configuration:
    def __init__(self, game: G, ignore_warnings: bool, parse_sections: Tuple[str, ...] = None, debug=False):
        self.game = game
        self.ignore_warnings = ignore_warnings  # If False, warnings stop program execution
        self.parse_sections = () if parse_sections is None else parse_sections
        logging.basicConfig(format='%(message)s', level=logging.DEBUG if debug else logging.WARNING)
        self.debug = debug


SUPPORTED_GAMES = \
    (G.CROC_1_PS1, G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY, G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
# Croc 1 parsing is not supported, but it can be sliced
PARSABLE_GAMES = (G.CROC_2_PS1, G.CROC_2_DEMO_PS1, G.CROC_2_DEMO_PS1_DUMMY, G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1)
SLICEABLE_GAMES = SUPPORTED_GAMES

PARSABLE_SECTIONS = ('XSPT', 'XSPS', 'XSPD', 'PORT', ' DNE')

wavefront_header = "# Generated by ps1_brender tools: https://github.com/OverSurge/PS1-BRender-Reverse\n"
wav_header = b"Generated by ps1_brender tools: https://github.com/OverSurge/PS1-BRender-Reverse"

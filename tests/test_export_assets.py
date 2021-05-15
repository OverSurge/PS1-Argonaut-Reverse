import os

import pytest

from export_assets import *


class TestExportAssets:
    @pytest.fixture
    def limited_exports_args(self, tmp_path):
        return ['--export-textures', str(tmp_path / 'Textures'),
                '--export-models', str(tmp_path / '3D models'),
                '--export-levels', str(tmp_path / 'Levels/No actors - No lighting')]

    @pytest.fixture
    def full_exports_args(self, tmp_path, limited_exports_args):
        return limited_exports_args + ['--export-audio', str(tmp_path / 'Audio')]

    def test_croc_2_exports(self, limited_exports_args):
        wads_path = Path(os.environ['CROC_2_WADS_PATH'])
        args = parse_args(["-wad", str(wads_path / 'T2L2M001.WAD'), "Croc 2 PS1"] + limited_exports_args)
        export_assets(args)

    # def test_croc_2_demo_exports(self, limited_exports_args):
    #     wads_path = Path(os.environ['CROC_2_DEMO_WADS_PATH'])
    #     args = parse_args(["-wad", str(wads_path / 'T1L2M001.WAD'), "Croc 2 Demo PS1"] + limited_exports_args)
    #     export_assets(args)

    def test_croc_2_demo_dummy_exports(self, limited_exports_args):
        wads_path = Path(os.environ['CROC_2_DEMO_DUMMY_WADS_PATH'])
        args = parse_args(["-wad", str(wads_path / '11A6000.WAD'), "Croc 2 Demo PS1 (Dummy)"] + limited_exports_args)
        export_assets(args)

    def test_hp1_exports(self, full_exports_args):
        wads_path = Path(os.environ['HP1_WADS_PATH'])
        args = parse_args(["-wad", str(wads_path / 'T1L2M002.WAD'), "Harry Potter 1 PS1"] + full_exports_args)
        export_assets(args)

    def test_hp2_exports(self, full_exports_args):
        wads_path = Path(os.environ['HP2_WADS_PATH'])
        args = parse_args(["-wad", str(wads_path / 'T1L4M005.WAD'), "Harry Potter 2 PS1"] + full_exports_args)
        export_assets(args)

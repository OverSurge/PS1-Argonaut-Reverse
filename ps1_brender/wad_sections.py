from pathlib import Path
from typing import List

from ps1_brender import *
from ps1_brender.data_models import ModelData
from ps1_brender.files import AnimationFile, ModelFile, TextureFile


class WADFile:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        codenames: List[str] = []
        offsets: List[int] = []
        offset = start + 4
        while True:
            codename = data[offset: offset + 4]

            # Detects incorrect WADs like FESOUND or FETHUND
            if len(codenames) == 0 and codename != XSPTSection.codename_bytes:
                raise SectionNameError(offset, XSPTSection.codename, codename.decode('latin1'))

            codenames.append(codename.decode('latin1'))
            offsets.append(offset)
            if codename == b'\x20\x44\x4E\x45':  # ' DNE' (END)
                break
            offset += 8 + int.from_bytes(data[offset + 4: offset + 8], 'little')
        xspt_index = codenames.index('XSPT')
        self.xspt = XSPTSection(data, offsets[xspt_index], offsets[xspt_index + 1], conf)
        self.textures = self.xspt.texture_file.textures
        if conf.process_all_sections:
            xspd_index = codenames.index('XSPD')
            self.xspd = XSPDSection(data, offsets[xspd_index], offsets[xspd_index + 1], conf)
            self.models = self.xspd.model_file.models
            self.animations = self.xspd.animation_file.animations

    # FIXME: EXPERIMENTAL: 3D model + animation linking is only guessed
    def extract_experimental_models(self, folder_path: str, filename: str):
        """Tries to find one compatible animation for each model in the WAD, animate it to make it clean
        (see doc about 3D models) and extract them into Wavefront OBJ files at the given location."""
        folder_path = Path(folder_path)
        if not folder_path.exists():
            folder_path.mkdir()
        elif folder_path.is_file():
            raise FileExistsError

        animation_id = 0
        with (folder_path / (filename + '.MTL')).open('w') as mtl:
            mtl.write(wavefront_header + f"newmtl mtl1\nmap_Kd {filename}.PNG")
        self.xspt.texture_file.generate_colorized_texture().save(folder_path / (filename + '.PNG'))

        for i in range(self.xspd.model_file.n_models):
            while self.models[i].n_vertex_groups != self.animations[animation_id].n_vertex_groups:
                animation_id += 1
                if animation_id == self.xspd.animation_file.n_animations:
                    break
            if animation_id == self.xspd.animation_file.n_animations:
                break

            obj_filename = f"{filename}_{i}"
            if self.models[i].n_vertex_groups == 1:
                vertices = self.models[i].ungrouped_vertices
                vertices_normals = self.models[i].ungrouped_vertices_normals
            else:
                vertices, vertices_normals = self.models[i].animate(self.animations[animation_id])
            obj = ModelData.to_obj(vertices, vertices_normals, self.models[i].faces, self.models[i].faces_texture_id,
                                   self.xspt.texture_file, obj_filename, filename)
            with (folder_path / (obj_filename + '.OBJ')).open('w', encoding='ASCII') as obj_file:
                obj_file.write(obj)


class XSPTSection:
    codename = 'XSPT'
    codename_bytes = b'\x58\x53\x50\x54'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration):
        codename_bytes = data[start:start + 4]
        if codename_bytes != XSPTSection.codename_bytes:
            raise SectionNameError(start, XSPTSection.codename, codename_bytes.decode('latin_1'))

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            xspt_flags = data[start + 8]
            has_translated_titles = xspt_flags & 16 != 0
            has_legacy_textures = xspt_flags & 8 != 0
            has_title_and_demo_mode_data = xspt_flags & 4 != 0
            if has_title_and_demo_mode_data:
                if has_translated_titles:
                    n_titles = int.from_bytes(data[start + 12:start + 16], 'little')
                    xspt_header_size = 16 + n_titles * 48 + 2052
                else:
                    xspt_header_size = 2096  # 44 + 2052
            else:
                xspt_header_size = 12
        elif conf.game == CROC_2_DEMO_PS1_DUMMY:  # The dummy WADs don't have any sort of flag or XSPT header
            xspt_header_size = 8
            has_legacy_textures = False
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)

        self.texture_file = TextureFile(data, start + xspt_header_size, end, conf, has_legacy_textures)

        expected_size = end - start
        calculated_size = xspt_header_size + self.texture_file.size
        if expected_size != calculated_size:
            raise SectionSizeMismatch(end, XSPTSection.codename, expected_size, calculated_size)


class XSPDSection:
    codename = 'XSPD'
    codename_bytes = b'\x58\x53\x50\x44'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration):
        codename_bytes = data[start:start + 4]
        if codename_bytes != XSPDSection.codename_bytes:
            raise SectionNameError(start, XSPDSection.codename, codename_bytes.decode('latin_1'))

        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            xspd_header_size = 2064
        elif conf.game == CROC_2_DEMO_PS1_DUMMY:
            xspd_header_size = 2068
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)
        self.model_file = ModelFile(data, start + xspd_header_size, conf)
        self.animation_file = AnimationFile(data, start + xspd_header_size + self.model_file.size, conf)

        # TODO: XSPD isn't entirely reversed yet
        # expected_size = end - start
        # calculated_size = xspd_header_size + self.model_file.size + self.animation_file.size
        # if expected_size != calculated_size:
        #     raise SectionSizeMismatch(end, XSPDSection.codename, expected_size, calculated_size)

import math
from io import BytesIO, SEEK_CUR, StringIO
from pathlib import Path
from typing import Dict, Union, List

from ps1_brender.configuration import Configuration, wavefront_header
from ps1_brender.errors_warnings import SectionNameError
from ps1_brender.wad_sections.DPSX.DPSXSection import DPSXSection
from ps1_brender.wad_sections.DPSX.Model3DData import Model3DData
from ps1_brender.wad_sections.ENDSection import ENDSection
from ps1_brender.wad_sections.PORTSection import PORTSection
from ps1_brender.wad_sections.SPSX.SPSXSection import SPSXSection
from ps1_brender.wad_sections.SPSX.SoundDescriptors import SoundsHolder, DialoguesBGMsSoundFlags
from ps1_brender.wad_sections.TPSX.TPSXSection import TPSXSection


class WAD:
    def __init__(self, tpsx: TPSXSection = None, spsx: SPSXSection = None, dpsx: DPSXSection = None,
                 port: PORTSection = None, end: ENDSection = None):
        self.tpsx = tpsx
        self.spsx = spsx
        self.dpsx = dpsx
        self.port = port
        self.end = end

    @property
    def titles(self):
        return None if (self.tpsx is None) else self.tpsx.titles

    @property
    def textures(self):
        return None if (self.tpsx is None) else self.tpsx.texture_file.textures

    @property
    def common_sound_effects(self):
        return None if (self.spsx is None) else self.spsx.common_sound_effects

    @property
    def ambient_tracks(self):
        return None if (self.spsx is None) else self.spsx.ambient_tracks

    @property
    def models(self):
        return None if (self.dpsx is None) else self.dpsx.models_3d_file.models

    @property
    def animations(self):
        return None if (self.dpsx is None) else self.dpsx.animations_file.animations

    @property
    def chunks_matrix(self):
        return None if (self.dpsx is None) else self.dpsx.level_file.chunks_matrix

    @property
    def level_sound_effects(self):
        return None if (self.end is None) else self.spsx.level_sound_effects_groups

    @property
    def dialogues_bgms(self):
        return None if (self.end is None) else self.spsx.dialogues_bgms

    def _prepare_obj_export(self, folder_path: Path, wad_filename: str):
        """Exports the material (MTL) and texture (PNG) files that are needed by the OBJ Wavefront file."""
        with (folder_path / (wad_filename + '.MTL')).open('w', encoding='ASCII') as mtl_file:
            mtl_file.write(wavefront_header + f"newmtl mtl1\nmap_Kd {wad_filename}.PNG")
        self.tpsx.texture_file.generate_colorized_texture().save(folder_path / (wad_filename + '.PNG'))

    def export_experimental_models(self, folder_path: Path, wad_filename: str):
        """Tries to find one compatible animation for each model in the WAD, animates it to make it clean
        (see doc about 3D models) and exports them into Wavefront OBJ files at the given location."""
        n_models = self.dpsx.models_3d_file.n_models
        n_animations = self.dpsx.animations_file.n_animations

        def guess_compatible_animation(position: int, n_vertices_groups: int):
            """EXPERIMENTAL: Band-aid, will be removed when animations' model id is found & reversed."""
            position = int((position / n_models) * n_animations)
            a = int(position)
            b = int(math.ceil(position))
            while a > -1 or b < n_animations:
                if a > -1:
                    if self.animations[a].n_vertices_groups == n_vertices_groups:
                        return a
                    a -= 1
                if b < self.dpsx.animations_file.n_animations:
                    if self.animations[b].n_vertices_groups == n_vertices_groups:
                        return b
                    b += 1
            return None

        if not folder_path.exists():
            folder_path.mkdir()
        elif folder_path.is_file():
            raise FileExistsError

        self._prepare_obj_export(folder_path, wad_filename)
        for i, model_3d in enumerate(self.dpsx.models_3d_file.models):
            obj_filename = f"{wad_filename}_{i}"
            with (folder_path / (obj_filename + '.OBJ')).open('w', encoding='ASCII') as obj_file:
                if model_3d.n_vertices_groups == 1:
                    model_3d.to_single_obj(obj_file, obj_filename, self.textures, wad_filename)
                else:
                    animation_id = guess_compatible_animation(i, self.models[i].n_vertices_groups)
                    if animation_id is None:
                        model_3d.to_single_obj(obj_file, obj_filename, self.textures, wad_filename)
                    else:
                        model_3d.animate(self.animations[animation_id]).to_single_obj(obj_file, obj_filename,
                                                                                      self.textures, wad_filename)

    def export_model_3d(self, model_id: int, folder_path: Path, filename: str):
        """Exports a 3D model into a Wavefront OBJ file along with a MTL file and a texture file.
        Avoid calling this function on a lot of 3D models at once, WAD batch export functions are made for that.
        If you do it anyway, the export will take a long time as a new texture file will be generated for each model."""
        self._prepare_obj_export(folder_path, filename)
        with (folder_path / (filename + '.OBJ')).open('w', encoding='ASCII') as obj_file:
            obj = StringIO()
            self.models[model_id].to_single_obj(obj, filename, self.textures, filename)
            obj_file.write(obj.getvalue())

    def export_audio(self, folder_path: Path, wad_filename: str):
        if self.spsx:
            tracks_lists: List[SoundsHolder] = [self.spsx.common_sound_effects, self.spsx.ambient_tracks,
                                                self.spsx.level_sound_effects_groups, self.spsx.dialogues_bgms]
            tracks_prefixes = ('effect', 'ambient', 'level_effect', 'dialogue_bgm')
            for i in range(len(tracks_lists)):
                for j in range(len(tracks_lists[i])):
                    filename = f"{wad_filename}_{tracks_prefixes[i]}_{j}"
                    if i == 3 and DialoguesBGMsSoundFlags.IS_BACKGROUND_MUSIC in tracks_lists[i].descriptors[j].flags:
                        filename += '_(BGM)'
                    print(i, j)
                    (folder_path / f"{filename}.WAV").write_bytes(tracks_lists[i].vags[j].to_wav(filename))

    def export_level(self, folder_path: Path, wad_filename: str):
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
        elif folder_path.is_file():
            raise FileExistsError

        self._prepare_obj_export(folder_path, wad_filename)
        with (folder_path / (wad_filename + '.OBJ')).open('w', encoding='ASCII') as obj_file:
            obj = StringIO()
            obj.write(Model3DData.mtl_header.format(mtl_filename=wad_filename))
            vio = 0
            sub_chunk_id = 0
            for texture in self.textures:
                for j in range(4):
                    obj.write(f"vt {texture.coords[j][0] / 1024} {(1024 - texture.coords[j][1]) / 1024}\n")
            for i, chunk_holder in enumerate(self.dpsx.level_file.chunks_matrix.chunks_holders):
                if chunk_holder.sub_chunks:
                    x, z = self.dpsx.level_file.chunks_matrix.x_z_coords(i)
                    for chunk in chunk_holder.sub_chunks:
                        cm = chunk.model_3d_data
                        cm.to_batch_obj(obj, f"{wad_filename}_{sub_chunk_id}", x, chunk.height, z, chunk.rotation, vio)
                        vio += cm.n_vertices
                        sub_chunk_id += 1
            obj_file.write(obj.getvalue())

    @classmethod
    def parse(cls, file_path_or_data: Union[Path, bytes], conf: Configuration):
        def parse_sections():
            raw_data.seek(4)
            while True:
                codename = raw_data.read(4)

                # Detects incorrect WADs like FESOUND or FETHUND
                if len(sections) == 0 and codename != TPSXSection.codename_bytes:
                    raise SectionNameError(raw_data.tell(), TPSXSection.codename_str, codename.decode('latin1'))

                sections[codename.decode('latin1')] = raw_data.tell() - 4
                raw_data.seek(int.from_bytes(raw_data.read(4), 'little'), SEEK_CUR)
                if codename == ENDSection.codename_bytes:  # ' DNE' (END)
                    break

        if isinstance(file_path_or_data, Path):
            with open(file_path_or_data, 'rb') as file:
                raw_data = BytesIO(file.read())
        elif isinstance(file_path_or_data, bytes):
            raw_data = BytesIO(file_path_or_data)
        else:
            raise TypeError("file_path_or_data should be of type Path or bytes")
        sections: Dict[str, int] = {}
        parse_sections()

        if TPSXSection.codename_str in conf.parse_sections:
            raw_data.seek(sections[TPSXSection.codename_str])
            tpsx = TPSXSection.parse(raw_data, conf)
        else:
            tpsx = None
        if SPSXSection.codename_str in sections.keys() and SPSXSection.codename_str in conf.parse_sections:
            raw_data.seek(sections[SPSXSection.codename_str])
            spsx = SPSXSection.parse(raw_data, conf)
            end = True
        else:
            spsx = None

        if DPSXSection.codename_str in conf.parse_sections:
            raw_data.seek(sections[DPSXSection.codename_str])
            dpsx = DPSXSection.parse(raw_data, conf)
        else:
            dpsx = None

        if PORTSection.codename_str in sections.keys() and PORTSection.codename_str in conf.parse_sections:
            raw_data.seek(sections[PORTSection.codename_str])
            port = PORTSection.parse(raw_data, conf)
        else:
            port = None

        if spsx:
            raw_data.seek(sections[ENDSection.codename_str])
            end = ENDSection.parse(raw_data, conf, spsx)
        else:
            end = None

        raw_data.close()
        return cls(tpsx, spsx, dpsx, port, end)

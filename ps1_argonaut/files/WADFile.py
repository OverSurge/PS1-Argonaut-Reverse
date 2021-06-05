import math
from io import BytesIO, SEEK_CUR, StringIO, BufferedIOBase
from pathlib import Path
from typing import Dict, Union, Optional, List

from ps1_argonaut.BaseDataClasses import BaseWADSection
from ps1_argonaut.configuration import Configuration, wavefront_header, G
from ps1_argonaut.errors_warnings import SectionNameError
from ps1_argonaut.files.DATFile import DATFile
from ps1_argonaut.wad_sections.DPSX.ChunkClasses import ChunkHolder
from ps1_argonaut.wad_sections.DPSX.DPSXSection import DPSXSection
from ps1_argonaut.wad_sections.DPSX.Model3DData import Model3DData
from ps1_argonaut.wad_sections.ENDSection import ENDSection
from ps1_argonaut.wad_sections.PORTSection import PORTSection
from ps1_argonaut.wad_sections.SPSX.SPSXSection import SPSXSection
from ps1_argonaut.wad_sections.SPSX.Sounds import DialoguesBGMsSoundFlags
from ps1_argonaut.wad_sections.TPSX.TPSXSection import TPSXSection


class WADFile(Dict[bytes, BaseWADSection], DATFile):
    suffix = 'WAD'

    sections_conf: Dict[bytes, BaseWADSection] = {
        TPSXSection.codename_bytes: TPSXSection, SPSXSection.codename_bytes: SPSXSection,
        DPSXSection.codename_bytes: DPSXSection, PORTSection.codename_bytes: PORTSection,
        ENDSection.codename_bytes: ENDSection}

    def __init__(self, stem: str, sections: Dict[bytes, BaseWADSection] = None, data: bytes = None):
        dict.__init__(self, sections if sections is not None else {})
        DATFile.__init__(self, stem, data=data)

    def __str__(self):
        titles = ' ({})'.format(', '.join(title.strip(' ') for title in self.titles)) if self.titles else ''
        res = f"Game level{titles}"
        if self:
            res += '\n'
            if self.tpsx:
                res += f" {self.n_textures:>4} texture(s)"
            if isinstance(self.spsx, SPSXSection):
                res += f" {self.n_sounds:>4} audio file(s)"
            if self.dpsx:
                res += f" {self.n_models:>4} model(s) {self.n_animations:>4} animation(s)" \
                       f" {self.n_filled_chunks:>4} chunk(s)"
        return res

    # WAD sections

    @property
    def tpsx(self) -> Optional[TPSXSection]:
        return self[TPSXSection.codename_bytes] if TPSXSection.codename_bytes in self else None

    @property
    def spsx(self) -> Optional[SPSXSection]:
        return self[SPSXSection.codename_bytes] if SPSXSection.codename_bytes in self else None

    @property
    def dpsx(self) -> Optional[DPSXSection]:
        return self[DPSXSection.codename_bytes] if DPSXSection.codename_bytes in self else None

    @property
    def port(self) -> Optional[PORTSection]:
        return self[PORTSection.codename_bytes] if PORTSection.codename_bytes in self else None

    @property
    def end(self) -> Optional[ENDSection]:
        return self[ENDSection.codename_bytes] if ENDSection.codename_bytes in self else None

    # TPSX

    @property
    def titles(self) -> List[str]:
        return () if self.tpsx is None else self.tpsx.titles

    @property
    def textures(self):
        return None if (self.tpsx is None) else self.tpsx.texture_file.textures

    @property
    def n_textures(self):
        return 0 if self.tpsx is None else len(self.tpsx.texture_file.textures)

    # SPSX

    @property
    def common_sound_effects(self):
        return None if (self.spsx is None) else self.spsx.common_sfx

    @property
    def ambient_tracks(self):
        return None if (self.spsx is None) else self.spsx.ambient_tracks

    @property
    def flattened_level_sfx(self):
        return None if (self.end is None) else self.spsx.level_sfx_groups.sounds

    @property
    def level_sfx(self):
        return None if (self.end is None) else self.spsx.level_sfx_groups

    @property
    def dialogues_bgms(self):
        return None if (self.end is None) else self.spsx.dialogues_bgms

    @property
    def n_sounds(self):
        return 0 if (self.spsx is None or not isinstance(self.spsx, SPSXSection)) else self.spsx.n_sounds

    # DPSX

    @property
    def models_3d(self):
        return None if self.dpsx is None else self.dpsx.models_3d

    @property
    def n_models(self):
        return 0 if self.dpsx is None else len(self.dpsx.models_3d)

    @property
    def animations(self):
        return None if self.dpsx is None else self.dpsx.animations

    @property
    def n_animations(self):
        return 0 if self.dpsx is None else len(self.dpsx.animations)

    @property
    def scripts(self):
        return None if self.dpsx is None else self.dpsx.scripts

    @property
    def n_scripts(self):
        return 0 if self.dpsx is None else len(self.dpsx.scripts)

    @property
    def chunks_matrix(self):
        return None if (self.dpsx is None) else self.dpsx.level_file.chunks_matrix

    @property
    def n_filled_chunks(self):
        return 0 if self.dpsx is None else self.dpsx.level_file.chunks_matrix.n_filled_chunks

    def _prepare_obj_export(self, folder_path: Path, wad_filename: str):
        """Exports the material (MTL) and texture (PNG) files that are needed by the OBJ Wavefront file."""
        with (folder_path / (wad_filename + '.MTL')).open('w', encoding='ASCII') as mtl_file:
            mtl_file.write(wavefront_header + f"newmtl mtl1\nmap_Kd {wad_filename}.PNG")
        self.tpsx.texture_file.to_colorized_texture().save(folder_path / (wad_filename + '.PNG'))

    def export_experimental_models(self, folder_path: Path, wad_filename: str):
        """Tries to find one compatible animation for each model in the WAD, animates it to make it clean
        (see doc about 3D models) and exports them into Wavefront OBJ files at the given location."""
        n_models = self.n_models
        n_animations = self.n_animations

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
                if b < n_animations:
                    if self.animations[b].n_vertices_groups == n_vertices_groups:
                        return b
                    b += 1
            return None

        if not folder_path.exists():
            folder_path.mkdir()
        elif folder_path.is_file():
            raise FileExistsError

        self._prepare_obj_export(folder_path, wad_filename)
        for i, model_3d in enumerate(self.dpsx.models_3d):
            obj_filename = f"{wad_filename}_{i}"
            with (folder_path / (obj_filename + '.OBJ')).open('w', encoding='ASCII') as obj_file:
                if model_3d.n_vertices_groups == 1:
                    model_3d.to_single_obj(obj_file, obj_filename, self.textures, wad_filename)
                else:
                    animation_id = guess_compatible_animation(i, self.models_3d[i].n_vertices_groups)
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
            self.models_3d[model_id].to_single_obj(obj, filename, self.textures, filename)
            obj_file.write(obj.getvalue())

    def export_audio(self, folder_path: Path, wad_filename: str):
        if self.spsx:
            mono_sounds = {'effect': self.spsx.common_sfx, 'ambient': self.spsx.ambient_tracks,
                           'level_effect': self.spsx.level_sfx_groups}
            for prefix, sounds in mono_sounds.items():
                for i, vag in enumerate(sounds.vags):
                    filename = f"{wad_filename}_{prefix}_{i}"
                    (folder_path / f"{filename}.WAV").write_bytes(vag.to_wav(filename))

            dialogue_index = 0
            bgm_index = 0
            for sound in self.spsx.dialogues_bgms:
                if DialoguesBGMsSoundFlags.IS_BACKGROUND_MUSIC in sound.flags:
                    filename = f"{wad_filename}_background_music_{bgm_index}"
                    bgm_index += 1
                else:
                    filename = f"{wad_filename}_dialogue_{dialogue_index}"
                    dialogue_index += 1
                (folder_path / f"{filename}.WAV").write_bytes(sound.vag.to_wav(filename))

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
            [[obj.write(f"vt {coord[0] / 1024} {(1024 - coord[1]) / 1024}\n")
              for coord in texture.output_coords] for texture in self.textures]
            for i, chunk_holder in enumerate(self.dpsx.level_file.chunks_matrix):  # type: int, ChunkHolder
                if chunk_holder:
                    x, z = self.dpsx.level_file.chunks_matrix.x_z_coords(i)
                    for chunk in chunk_holder:
                        cm = chunk.model_3d_data
                        cm.to_batch_obj(obj, f"{wad_filename}_{sub_chunk_id}", x, chunk.height, z, chunk.rotation, vio)
                        vio += cm.n_vertices
                        sub_chunk_id += 1
            obj_file.write(obj.getvalue())

    def parse(self, conf: Configuration, *args, **kwargs):
        def parse_sections():
            data_in.seek(4)
            while True:
                codename = data_in.read(4)

                # Detects incorrect WADs like FESOUND or FETHUND
                if len(sections_offsets) == 0 and codename != TPSXSection.codename_bytes:
                    raise SectionNameError(data_in.tell(), TPSXSection.codename_str, codename.decode('latin1'))

                sections_offsets[codename] = data_in.tell() - 4
                data_in.seek(int.from_bytes(data_in.read(4), 'little'), SEEK_CUR)
                if codename == ENDSection.codename_bytes:  # ' DNE' (END)
                    break

        data_in = BytesIO(self._data)
        sections_offsets: Dict[bytes, int] = {}
        self.clear()
        parse_sections()

        for codename_bytes, offset in sections_offsets.items():
            data_in.seek(offset)
            if codename_bytes in WADFile.sections_conf:
                section = WADFile.sections_conf[codename_bytes]
                if conf.game in section.supported_games:
                    if codename_bytes != ENDSection.codename_bytes:
                        self[codename_bytes] = section.parse(data_in, conf)
                    else:
                        self[codename_bytes] = section.parse(data_in, conf,
                                                             spsx_section=self[SPSXSection.codename_bytes])
                else:
                    self[codename_bytes] = BaseWADSection.fallback_parse(data_in)
            else:
                self[codename_bytes] = BaseWADSection.fallback_parse(data_in)

        data_in.close()
        self.end_parse()

    def serialize(self, file_path_or_data_out: Union[Path, BufferedIOBase], conf: Configuration):
        data_out = file_path_or_data_out if isinstance(file_path_or_data_out, BufferedIOBase) else BytesIO()
        wad_size_offset = data_out.tell()
        data_out.write(b'\x00\x00\x00\x00')
        for section in self.values():
            if section.serialize.__func__ is BaseWADSection.serialize:
                section.fallback_serialize(data_out)
            else:
                section.serialize(data_out, conf)
        end_offset = data_out.tell()
        wad_size = end_offset - wad_size_offset
        if conf.game in (G.CROC_2_PS1, G.HARRY_POTTER_1_PS1, G.HARRY_POTTER_2_PS1):
            wad_size += 2048
        data_out.seek(wad_size_offset)
        data_out.write(wad_size.to_bytes(4, 'little'))
        data_out.seek(end_offset)

        if isinstance(file_path_or_data_out, Path):
            with open(file_path_or_data_out, 'wb') as output_file:
                data_out.seek(0)
                output_file.write(data_out.read())
                data_out.close()

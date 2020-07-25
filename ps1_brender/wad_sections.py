import math
from pathlib import Path
from typing import List

from ps1_brender import *
from ps1_brender.data_models import ModelData, VAGSoundData
from ps1_brender.files import AnimationFile, ModelFile, SoundFile, TextureFile


class WADFile:
    def __init__(self, data: bytes, start: int, conf: Configuration):
        self.conf = conf
        codenames: List[str] = []
        offsets: List[int] = []
        offset = start + 4
        while True:
            codename = data[offset: offset + 4]

            # Detects incorrect WADs like FESOUND or FETHUND
            if len(codenames) == 0 and codename != XSPTSection.codename_bytes:
                raise SectionNameError(offset, XSPTSection.codename_str, codename.decode('latin1'))

            codenames.append(codename.decode('latin1'))
            offsets.append(offset)
            offset += 8 + int.from_bytes(data[offset + 4: offset + 8], 'little')
            if codename == DNESection.codename_bytes:  # ' DNE' (END)
                codenames.append('EOF')  # End Of File, doesn't actually exist in WAD
                offsets.append(offset)
                break

        xspt_index = codenames.index(XSPTSection.codename_str)
        self.xspt = XSPTSection(data, offsets[xspt_index], offsets[xspt_index + 1], conf)
        self.titles = self.xspt.titles
        if XSPTSection.codename_str in conf.parse_sections:
            self.textures = self.xspt.texture_file.textures
        if XSPSSection.codename_str in conf.parse_sections or DNESection.codename_str in conf.parse_sections:
            if XSPSSection.codename_str in codenames:
                xsps_index = codenames.index(XSPSSection.codename_str)
                self.xsps = XSPSSection(data, offsets[xsps_index], offsets[xsps_index + 1], conf)
                self.dne = DNESection(data, offsets[-2], offsets[-1], conf, self.xsps.sound_file)
                self.common_sound_effects = self.xsps.sound_file.common_sound_effects_vags
                self.ambient_tracks = self.xsps.sound_file.ambient_vags
                self.level_sound_effects = self.dne.level_sound_effects_vags
                self.dialogues_bgms = self.dne.dialogues_bgms_vags
            else:
                self.xsps = None
                self.dne = None

        if XSPDSection.codename_str in conf.parse_sections:
            xspd_index = codenames.index(XSPDSection.codename_str)
            self.xspd = XSPDSection(data, offsets[xspd_index], offsets[xspd_index + 1], conf)
            self.models = self.xspd.model_file.models
            self.animations = self.xspd.animation_file.animations

    # FIXME: EXPERIMENTAL: 3D model + animation linking is only guessed
    def extract_experimental_models(self, folder_path: Path, wad_filename: str):
        """Tries to find one compatible animation for each model in the WAD, animate it to make it clean
        (see doc about 3D models) and extract them into Wavefront OBJ files at the given location."""

        def guess_compatible_animation(position: int, n_vertex_groups: int):
            """EXPERIMENTAL: Band-aid, will be removed when animations' model id is found & reversed."""
            position = int((position / self.xspd.model_file.n_models) * self.xspd.animation_file.n_animations)
            a = int(position)
            b = int(math.ceil(position))
            while a > -1 or b < self.xspd.animation_file.n_animations:
                if a > -1:
                    if self.animations[a].n_vertex_groups == n_vertex_groups:
                        return a
                    a -= 1
                if b < self.xspd.animation_file.n_animations:
                    if self.animations[b].n_vertex_groups == n_vertex_groups:
                        return b
                    b += 1
            return None

        if not folder_path.exists():
            folder_path.mkdir()
        elif folder_path.is_file():
            raise FileExistsError

        logging.debug(f"anims :{[x.n_vertex_groups for x in self.animations]}")
        logging.debug(f"models:{[x.n_vertex_groups for x in self.models]}")

        with (folder_path / (wad_filename + '.MTL')).open('w') as mtl:
            mtl.write(wavefront_header + f"newmtl mtl1\nmap_Kd {wad_filename}.PNG")
        self.xspt.texture_file.generate_colorized_texture().save(folder_path / (wad_filename + '.PNG'))

        for i in range(self.xspd.model_file.n_models):
            if self.models[i].n_vertex_groups == 1:
                vertices = self.models[i].ungrouped_vertices
                vertices_normals = self.models[i].ungrouped_vertices_normals
            else:
                animation_id = guess_compatible_animation(i, self.models[i].n_vertex_groups)
                if animation_id is None:
                    vertices = self.models[i].ungrouped_vertices
                    vertices_normals = self.models[i].ungrouped_vertices_normals
                else:
                    vertices, vertices_normals = self.models[i].animate(self.animations[animation_id])

            obj_filename = f"{wad_filename}_{i}"
            obj = ModelData.to_obj(vertices, vertices_normals, self.models[i].faces, self.models[i].faces_texture_id,
                                   self.xspt.texture_file, obj_filename, wad_filename)
            with (folder_path / (obj_filename + '.OBJ')).open('w', encoding='ASCII') as obj_file:
                obj_file.write(obj)

    def extract_audio(self, folder_path: Path, wad_filename: str):
        if self.conf.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            if self.xsps:
                tracks_lists = [self.xsps.sound_file.common_sound_effects_vags, self.xsps.sound_file.ambient_vags,
                                self.dne.level_sound_effects_vags, self.dne.dialogues_bgms_vags]
                tracks_prefixes = ('effect', 'ambient', 'level_effect', 'dialogue_bgm')
                for i in range(len(tracks_lists)):
                    for j in range(len(tracks_lists[i])):
                        filename = f"{wad_filename}_{tracks_prefixes[i]}_{j}"
                        if tracks_lists[i][j] in self.dne.bgm_only_vags:
                            filename += '_(BGM)'
                        (folder_path / f"{filename}.WAV").write_bytes(tracks_lists[i][j].to_wav(filename))
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)


def check_codename(start: int, expected_codename_str: str, expected_codename_bytes: bytes, codename_bytes: bytes):
    if codename_bytes != expected_codename_bytes:
        raise SectionNameError(start, expected_codename_str, codename_bytes.decode('latin_1'))


class XSPTSection:
    codename_str = 'XSPT'
    codename_bytes = b'XSPT'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration):
        check_codename(start, XSPTSection.codename_str, XSPTSection.codename_bytes, data[start:start + 4])
        if conf.game in (CROC_2_PS1, CROC_2_DEMO_PS1, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            xspt_flags = data[start + 8]
            has_translated_titles = xspt_flags & 16 != 0
            has_legacy_textures = xspt_flags & 8 != 0
            has_title_and_demo_mode_data = xspt_flags & 4 != 0
            if has_title_and_demo_mode_data:
                if has_translated_titles:
                    n_titles = int.from_bytes(data[start + 12:start + 16], 'little')
                    self.titles = tuple(
                        [data[start + 16 + i * 48:start + 16 + (i + 1) * 48].decode('latin1') for i in range(n_titles)])
                    xspt_header_size = 16 + n_titles * 48 + 2052
                else:
                    xspt_header_size = 2096  # 44 + 2052
                    self.titles = data[start + 12:start + 44].decode('latin1'),
            else:
                xspt_header_size = 12
                self.titles = ()
        elif conf.game == CROC_2_DEMO_PS1_DUMMY:  # The dummy WADs don't have any sort of flag or XSPT header
            xspt_header_size = 8
            has_legacy_textures = False
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)

        if XSPTSection.codename_str in conf.parse_sections:
            self.texture_file = TextureFile(data, start + xspt_header_size, end, conf, has_legacy_textures)

            expected_size = end - start
            calculated_size = xspt_header_size + self.texture_file.size
            if expected_size != calculated_size:
                raise SectionSizeMismatch(end, XSPTSection.codename_str, expected_size, calculated_size)


class XSPSSection:
    codename_str = 'XSPS'
    codename_bytes = b'XSPS'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration):
        check_codename(start, XSPSSection.codename_str, XSPSSection.codename_bytes, data[start:start + 4])

        if conf.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            self.sound_file = SoundFile(data, start + 8, conf)

            expected_size = end - start
            calculated_size = 8 + self.sound_file.size
            if expected_size != calculated_size:
                raise SectionSizeMismatch(end, XSPSSection.codename_str, expected_size, calculated_size)
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)


class XSPDSection:
    codename_str = 'XSPD'
    codename_bytes = b'XSPD'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration):
        check_codename(start, XSPDSection.codename_str, XSPDSection.codename_bytes, data[start:start + 4])

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


class DNESection:
    codename_str = ' DNE'
    codename_bytes = b' DNE'

    def __init__(self, data: bytes, start: int, end: int, conf: Configuration, sound_file: SoundFile):
        check_codename(start, DNESection.codename_str, DNESection.codename_bytes, data[start:start + 4])

        if conf.game in (HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1):
            expected_size = end - start
            self.level_sound_effects_vags = []
            self.dialogues_bgms_vags = []
            self.bgm_only_vags = []
            if expected_size != 8:
                dne_start = start
                start += 8
                if sound_file.has_level_sound_effects:
                    for i in range(len(sound_file.level_sound_effect_groups)):
                        start = 2048 * math.ceil(start / 2048)
                        for track in sound_file.level_sound_effects[i]:
                            size = int.from_bytes(track[16:20], 'little')
                            self.level_sound_effects_vags.append(VAGSoundData(
                                size, data[start:start + size], 1, int.from_bytes(track[0:4], 'little'), conf))
                            start += size
                start = 2048 * math.ceil(start / 2048)
                for track in sound_file.dialogues_bgms:
                    size = int.from_bytes(track[12:16], 'little')
                    vag_start = start + int.from_bytes(track[0:4], 'little')
                    track_flags = track[6]
                    assert track_flags & 3 != 3
                    channels = 2 if track_flags & 1 else 1
                    # See XSPS' Dialogues & BGM descriptors documentation for the 44100 / 4096 ratio explanation
                    vag = VAGSoundData(size, data[vag_start:vag_start + size], channels,
                                       math.ceil(int.from_bytes(track[4:6], 'little') * (44100 / 4096)), conf)
                    self.dialogues_bgms_vags.append(vag)
                    if track_flags & 4:
                        self.bgm_only_vags.append(vag)
                start += sound_file.dialogues_tracks_sizes_sum

                if conf.game != HARRY_POTTER_2_PS1:
                    calculated_size = start - dne_start
                else:
                    calculated_size = 2048 * math.ceil(start / 2048) - dne_start
                if expected_size != calculated_size:
                    raise SectionSizeMismatch(end, DNESection.codename_str, expected_size, calculated_size)
        else:
            raise NotImplementedError(UNSUPPORTED_GAME)

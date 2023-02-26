# PS1 Argonaut Games Reverse Engineering

Unofficial documentation of PS1 Argonaut games' file formats & game assets extraction scripts

[![Discord](https://img.shields.io/discord/1013732315186335764?label=Join%20our%20Discord%20%21&logo=discord)](https://discord.gg/feMkSQeFms)

## Documentation

If you want to learn more about PS1 Argonaut games' file formats, check [this piece of documentation](Documentation/General%20information.md) (WIP).

## Game assets extraction

PS1 Argonaut games mostly use custom file formats for animations, 3D models, textures, maps and audio.

This toolkit can extract some of these file formats, in some games only.

### Supported games

- Aladdin in Nasira's Revenge ❌
- Alien Resurrection ❌
- Croc 1 ❌
- Croc 2 PS1 ✅
- Croc 2 Demo PS1 (including DUMMY WADs) ✅
- Harry Potter 1 PS1 ✅
- Harry Potter 2 PS1 ✅
- The Emperor's New Groove ❌

### Extraction scripts

All supported game assets should already be uploaded here:

[![Extracted assets repository](https://img.shields.io/badge/-Extracted%20assets%20repository-black?style=for-the-badge&logo=github)](https://github.com/OverSurge/PS1-Argonaut-Assets)

If you cannot find the assets you're looking for, they are probably not yet extractable by this toolkit.

If you still want to use the extraction scripts, please follow these steps:

1. [![](https://img.shields.io/badge/-Install%20Python%20%3E%3D%203.10-ffde57?logo=python)](https://www.python.org/downloads/)
2. (Optional) Create a virtual environment (`venv`) and activate it.
3. Install the required Python packages: `pip install -r requirements.txt`.
4. Run one of the 2 scripts :

- `python extract_files_from_dat.py`: Extracts files (.WAD for example) from raw game files (.DIR/.DAT).
- `python export_assets.py`: Extracts assets (textures, music, levels, etc.) from raw game files or .WAD files.

Add `--help` at the end of the command if needed.

---

#### Huge thanks to my friends Dobbyatemysock and supluk for supporting me and sharing their ideas

#### Thanks to MasterLeoBlue for advising me to use my scripts on Croc 2: it was a good idea

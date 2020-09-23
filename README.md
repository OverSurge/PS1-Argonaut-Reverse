# PS1 BRender Games Reverse Engineering

### Unofficial documentation of PS1 BRender games formats & Python extraction scripts.

> Extracted assets: [PS1-BRender-Assets](https://github.com/OverSurge/PS1-BRender-Assets).

#### Currently supported games (Animations, 3D models, textures, maps & audio (HP only))
- Croc 2 PS1
- Croc 2 Demo PS1 (including DUMMY WADs)
- Harry Potter 1 PS1
- Harry Potter 2 PS1

[Argonaut's BRender](https://en.wikipedia.org/wiki/Argonaut_Games#BRender) is a game engine mainly used by Argonaut Games.  
If I'm not mistaken, Argonaut games released around 2000 use BRender.  
However, the engine seems to have evolved a lot over time, causing the file formats to change.  
Therefore, this documentation and these tools cannot work with all BRender games, especially non-PS1 ones.  

## How to use the Python scripts

> Check that the assets you seek are not already extracted on [PS1-BRender-Assets](https://github.com/OverSurge/PS1-BRender-Assets) before using ps1_brender_reverse.py.  
> If they are not, it most probably means that they are not extractable or too experimental for now.

1. (Optional) Create a virtual environment (venv) and activate it.
2. Install the required Python packages: `pip install -r requirements.txt`.
3. You can now launch the scripts, there are 2 at the moment:
 - dat_slicing.py: Extracts all files (like WADs) from raw game files (.DIR/.DAT).
 - ps1_brender_reverse.py: Processes raw game files or WADs and extract assets from them.

## Disclaimers
- Please read [this piece of documentation](Documentation/General%20information.md) before the other pages.
- This project is **in progress**, so anything in this repo **may change anytime**.
- This is my first reverse, please be indulgent. Also, any help or advice is appreciated !
- I don't plan on reversing the code at the moment.
- I didn't manage to understand some values & concepts (yet).
Don't hesitate to contact me / open an issue / submit a pull request if you have any valuable information.
- The scripts can't create modified/forged assets yet, but I plan on making this possible.
- Some documentation files can be hard to understand, sorry about that.

## Contact
You can currently contact me on several Discord guilds (XeNTaX, TCRF, HP Modding, HP Console Speedruns, hpgames.net, Croc & Stuff, PSXDEV Network & more).

#### Huge thanks to my friends Dobbyatemysock and supluk for supporting me and sharing their ideas.
#### Thanks to MasterLeoBlue for advising me to use my scripts on Croc 2: it was a good idea !
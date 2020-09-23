# WAD files documentation

> Most probably means "Where's All the Data"

The WAD files are divided into several sections.
Each section starts by a codename, followed by an offset that leads to the next section.

- All versions of Croc 2 PS1 contain these sections (in order): TPSX, SPSX (Optional), DPSX and 'END ' (with a space).  
  (Includes release, demo and demo dummy WADs)  
- Harry Potter 1 & 2 PS1 contain these sections (in order): TPSX, SPSX, UNIF, LPSX, DPSX, PORT and ' END'.  

These codenames are stored backwards : XSPT, XSPS, FINU, XSPL, XSPD, TROP and ' DNE'.
Some sections codenames contain 'PSX' in their name (The PS1's codename).
In my opinion, these sections were specifically coded in BRender for the PS1 platform.
Therefore, it could mean that the other sections (or some) are platform-independent.

## Demo mode

Some levels support demo mode: they can appear on the title screen if you don't use your controller for a minute or so.
The WAD files of those levels go along with a [.DEM file](DEM.md) (having the same filename).

This is not the only change that occurs: some areas at the beginning of TPSX and DPSX and that are usually filled with 0x800 (2048) empty bytes are filled with data.  
Those data areas aren't reversed yet.

## File structure

| Offset (h) | Size (h) | Usage                        | Notes                                                        | Example                                               |
| :--------- | :------- | :--------------------------- | :----------------------------------------------------------- | :---------------------------------------------------- |
| 0x0        | 0x4      | Offset to the end of the WAD | In newer games, you need to add 0x800<sup>1</sup> to this value | T1I0M000.WAD is 0x5B8804 long, value is then 0x5B9000 |

<sup>1</sup> : Starting with Croc 2 release, they began adding 0x800 to this value (The only idea I have about this is that it might be linked to [Demo mode data](#Demo-mode) as it is 0x800 bytes long)

## Sections documentations

- [TPSX](WAD%20sections/TPSX.md): Textures
- [SPSX](WAD%20sections/SPSX.md): Sound effects and ambient tracks
- UNIF: Fonts & text management (TODO)
- LPSX: Localization, translated strings (TODO)
- [DPSX](WAD%20sections/DPSX.md): 3D models, animations, actors and level.
- PORT: Rendering groups / zones & more (TODO)
- ['END '](WAD%20sections/END.md): Delimits the end of the file. In Harry Potter, contains background music and level-specific sound effects


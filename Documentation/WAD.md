# WAD files documentation
> Probably means "Where's All the Data"

The WAD files are divided into several sections.
Each section starts by a codename, followed by an offset that leads to the next section.

- All versions of Croc 2 PS1 contain these sections (in order): XSPT, XSPS (Optional), XSPD and ' DNE' (with a space at the beginning).  
(Includes release, demo and demo dummy WADs)  
- Harry Potter 1 & 2 PS1 contain these sections (in order): XSPT, XSPS, FINU, XSPL, XSPD, TROP and ' DNE'.  

These codenames need to be read backwards in order to be understood: TPSX, SPSX, UNIF, LPSX, DPSX, PORT and 'END '.
Some sections codenames contain 'PSX' in their name (The PS1's codename).
In my opinion, these sections were specifically coded in BRender for the PS1 platform.
Therefore, it could mean that the other sections (or some) are platform-independent.

## Demo mode

Some levels support demo mode: they can appear on the title screen if you don't use your controller for a minute or so.
The WAD files of those levels go along with a [.DEM file](DEM.md) (having the same filename).

This is not the only change that occurs: some areas at the beginning of XSPT and XSPD and that are usually filled with 0x800 (2048) empty bytes are filled with data.  
Those data areas aren't reversed yet.

## File structure

|Offset (h)|Size (h)|Usage|Notes|Example|
|:---|:---|:---|:---|:---|
|0x0|0x4|Offset to the end of the WAD|In newer games, you need to add 0x800<sup>1</sup> to this value|T1I0M000.WAD is 0x5B8804 long, value is then 0x5B9000|

<sup>1</sup> : Starting with Croc 2 release, they began adding 0x800 to this value (The only idea I have about this is that it might be linked to [Demo mode data](#Demo-mode) as it is 0x800 bytes long)

## Sections documentations

- [XSPT](WAD%20sections/XSPT.md): Textures
- [XSPS](WAD%20sections/XSPS.md): Sound (TODO)
- FINU: Fonts & text management (TODO)
- XSPL: Localization, translated strings (TODO)
- [XSPD](WAD%20sections/XSPD.md): 3D models, animations, objects, 3D world & more (TODO)
- TROP: **Unknown** (TODO)
- [' DNE'](WAD%20sections/DNE.md): In older BRender games, it shows the end of the file, but in Harry Potter, it contains the background music (TODO)
# XSPT section documentation
> "T" stands for "Textures"

The XSPT section holds texture data. As it is the first section of every WAD, it also contains the level's title.

## Section structure

|Offset (h)|Size (h)|Usage|Notes|
|:---|:---|:---|:---|
|0x0|0x4|Section name|Value: `58 53 50 54` ("XSPT")|
|0x4|0x4|Offset to the next section|
|0x8|**DEPENDS**|[XSPT header](#XSPT-header-structure)|In the dummy WADs of Croc 2 Demo, there is no XSPT header|
|+0x0|**DEPENDS**|[Textures file](../Data%20formats/Textures.md)|

> The majority of the textures documentation is in [Textures](../Data%20formats/Textures.md).

### XSPT header structure

|Offset (h)|Size (h)|Usage|Notes|
|:---|:---|:---|:---|
|0x0|0x4|[XSPT flags](#XSPT-flags-structure)||

- **If the 1st flags bit is set:**
    - **If the 4th flags bit is not set:**

        |Offset (h)|Size (h)|Usage|
        |:---|:---|:---|
        |0x4|0x20|Level title in ASCII|
    
    - **If the 4th flags bit is set:**
    
        |Offset (h)|Size (h)|Usage|
        |:---|:---|:---|
        |0x4|0x4|Titles count. Abbreviated to 'tc'|
        |0x8|0x30 × *tc*|Level titles in ASCII (0x30 bytes per title)|

    |Offset (h)|Size (h)|Usage|Notes|
    |:---|:---|:---|:---|
    |+0x0|0x4|Maybe a "unique textures" count|Can be calculated: *tc* - 0x2C (44). Copied in [XSPD](XSPD.md) @0x12|
    |+0x4|0x800|Demo mode data|See [Demo mode](../WAD.md#Demo-mode)|


#### XSPT flags structure

On your hex editor, the bits are in this order:  
`| 07 06 05 04 03 02 01 00 | 15 14 13 12 11 10 09 08 | 23 22 21 20 19 18 17 16 | etc.`

|Bit|Usage|Notes|
|:---|:---|:---|
|0|**UNKNOWN**|||
|1|Title & demo mode data|If not set, there is no XSPT header, the data starts immediately after these flags. If set, there can be title(s) and 800 bytes are added after the title(s) to make room for [Demo mode data](../WAD.md#Demo-mode)|
|2|**UNKNOWN**|Set on all levels I reversed|
|3|Presence of legacy textures|If set, 5 textures (0xC00 long each, 0x3C00 in total) appear between the texture descriptors and the raw texture data|
|4|Multiple titles|If set, multiple titles are defined (usually one per language). The first unsigned long is then the number of titles, followed by 0x30-long titles.|
|5-31|**UNKNOWN** / ∅ Empty|||
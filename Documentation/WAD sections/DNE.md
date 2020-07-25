# ' DNE' section documentation
> 'END ' backwards

In older games, DNE delimits the WAD's end.  
In Harry Potter PS1, the DNE section holds some sound effects and background music tracks in Playstation VAG format.  
Even if VAG only supports mono officially, some tracks are stereo (1024-bytes interleaved).

## Section structure

|Offset (h)|Size (h)|Usage|Notes|
|:---|:---|:---|:---|
|0x0|0x4|Section name|Value: `20 44 4E 45` (" DNE")|
|0x4|0x4|Section's size|Technically the offset to the next section, but there is none after DNE|

- **If XSPS' 3rd flags bit is set:**

> A 2048-bytes alignment is present before each group, see [XSPS](XSPS.md)

|Offset (h)|Size (h)|Usage|Notes|
|:---|:---|:---|:---|
|+0x0|**DEPENDS**|2048-bytes alignment||
|++0x0|**DEPENDS**|Level sound effects audio data|This is where the [Group's beginning offsets](XSPS.md#Level-sound-effects-groups-descriptors) start from (Previous alignment not included, alignment between each group INCLUDED)|

- **If XSPS' 2nd flags bit is set:**

|Offset (h)|Size (h)|Usage|Notes|
|:---|:---|:---|:---|
|+0x0|**DEPENDS**|2048-bytes alignment||
|++0x0|**DEPENDS**|Dialogues & BGM audio data|This is where the [Dialogues & BGM beginning offsets](XSPS.md#Dialogues--BGMs-descriptors) start from (Alignment not included)|

> In Harry Potter 2 PS1, this section is 2048-bytes aligned at the end. 

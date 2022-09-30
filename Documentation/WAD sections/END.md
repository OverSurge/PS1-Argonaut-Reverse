# 'END ' (' DNE') section documentation

In older games, END delimits the WAD's end.  
In Harry Potter PS1, the END section holds some sound effects and background music tracks in Playstation VAG format.  
Even if VAG only supports mono officially, some tracks are stereo (1024-bytes interleaved).

## Section structure

| Offset (h) | Size (h) | Usage          | Notes                                                        |
| :--------- | :------- | :------------- | :----------------------------------------------------------- |
| 0x0        | 0x4      | Section's name | Value: `20 44 4E 45` (" DNE")                                |
| 0x4        | 0x4      | Section's size | Technically the offset to the next section, but there is none after END |

- **If SPSX' 3rd flags bit is set:**

> A 2048-bytes alignment is present before each group, see [SPSX](SPSX.md)

| Offset (h) | Size (h)    | Usage                          | Notes                                                        |
| :--------- | :---------- | :----------------------------- | :----------------------------------------------------------- |
| +0x0       | **DEPENDS** | 2048-bytes alignment           |                                                              |
| ++0x0      | **DEPENDS** | Level sound effects audio data | This is where the [Group's beginning offsets](SPSX.md#Level-sound-effects-groups-descriptors) start from (Previous alignment not included, alignment between each group INCLUDED) |

- **If SPSX' 2nd flags bit is set:**

| Offset (h) | Size (h)    | Usage                      | Notes                                                        |
| :--------- | :---------- | :------------------------- | :----------------------------------------------------------- |
| +0x0       | **DEPENDS** | 2048-bytes alignment       |                                                              |
| ++0x0      | **DEPENDS** | Dialogues & BGM audio data | This is where the [Dialogues & BGM beginning offsets](SPSX.md#Dialogues--BGMs-descriptors) start from (Alignment not included) |

> In Harry Potter 2 PS1, this section is 2048-bytes aligned at the end.

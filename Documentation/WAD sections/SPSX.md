# SPSX (XSPS) section documentation

> "S" most probably stands for "Sound"

This section contains background music and sound effects, stored in Playstation VAG format.  
Stereo audio is stored with a 1024 bytes interleave.

Starting with Harry Potter PS1, audio is stored in SPSX **and** END sections.

## Audio sections representation (in Harry Potter and after)

This is what SPSX and END look like with all possible tracks. Depending on the SPSX flags of the level you work on, they can be present or not.

> BGM stands for "BackGround Music"

````
             SPSX                                   END
 ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐         ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
 │ SPSX header               │         │ Level sound effects VAGs  │
 │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │         │ (2048-bytes aligned *)    │
 │ Common sound effects VAGs │         │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
 │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │         │ Dialogues & BGMs VAGs     │
 │ Ambient tracks VAGs       │         │ (2048-bytes aligned)      │
 └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘         └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
````

> \* Level sound effects alignment only occurs before the first group and between groups, not between sounds inside the same group, see [Level sound effects headers](#Level-sound-effects-headers-structure).

## Section structure (in Harry Potter and after)

> The 'common sound effects count' and 'Dialogues & BGMs count' values are always present, even if the 2nd flags bit is unset.

| Offset (h) | Size (h) | Usage                                       | Notes                                    |
| :--------- | :------- | :------------------------------------------ | :--------------------------------------- |
| 0x0        | 0x4      | Section's name                              | Value: `58 53 50 53` ("XSPS")            |
| 0x4        | 0x4      | Section's size / Offset to the next section |                                          |
| 0x8        | 0x4      | [SPSX flags](#SPSX-flags-structure)         |                                          |
| 0xC        | 0x4      | Common sound effects count                  | Always present. Abbreviated to '**sec**' |

- **If the 2nd flags bit is set:**

  | Offset (h) | Size (h)       | Usage                                                        | Notes |
  | :--------- | :------------- | :----------------------------------------------------------- | :---- |
  | +0x0       | 0x14 × **sec** | [Common sound effects descriptors](#Common-sound-effects-descriptors) |       |

- **If the 0th flags bit is set:**

  | Offset (h) | Size (h)       | Usage                                                     | Notes                    |
  | :--------- | :------------- | :-------------------------------------------------------- | :----------------------- |
  | +0x0       | 0x4            | Ambient tracks count                                      | Abbreviated to '**atc**' |
  | +0x4       | 0x14 × **atc** | [Ambient tracks descriptors](#Ambient-tracks-descriptors) |                          |

- **If the 3rd flags bit is set:**

  | Offset (h) | Size (h)    | Usage                                                        | Notes |
  | :--------- | :---------- | :----------------------------------------------------------- | :---- |
  | +0x0       | **DEPENDS** | [Level sound effects headers](#Level-sound-effects-headers-structure) |       |

| Offset (h) | Size (h) | Usage                  | Notes                                    |
| :--------- | :------- | :--------------------- | :--------------------------------------- |
| +0x0       | 0x4      | Dialogues & BGMs count | Always present. Abbreviated to '**dbc**' |

- **If the 2nd flags bit is set:**

  | Offset (h) | Size (h)       | Usage                                                        | Notes                                                        |
  | :--------- | :------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
  | +0x0       | 0x4            | END offset                                                   | If there are level sound effects (bit 3 set), they come before the dialogues & BGMs. This value is the offset to add at the start of END to get the beginning of the dialogues & BGMs. |
  | +0x4       | 0x10 × **dbc** | [Dialogues & BGMs descriptors](#Dialogues--BGMs-descriptors) |                                                              |
  | ++0x0      | 0x4            | Common sound effects audio data size                         | Abbreviated to '**ses**'                                     |
  | ++0x4      | **ses**        | Common sound effects audio data                              |                                                              |

- **If the 0th flags bit is set:**

  | Offset (h) | Size (h) | Usage                          | Notes                    |
  | :--------- | :------- | :----------------------------- | :----------------------- |
  | +0x0       | 0x4      | Ambient tracks audio data size | Abbreviated to '**ats**' |
  | +0x4       | **ats**  | Ambient tracks audio data      |                          |

### SPSX flags structure

On your hex editor, the bits are in this order:  
`| 07 06 05 04 03 02 01 00 | 15 14 13 12 11 10 09 08 | etc.`

| Bit  | Usage                      | Notes                                                        |
| :--- | :------------------------- | :----------------------------------------------------------- |
| 0    | Presence of ambient tracks | Identical to the 4th bit. Presence of ambient tracks in SPSX |
| 1    | ∅ Empty                    |                                                              |
| 2    | Presence of sound effects  | Presence of common sound effects in SPSX and dialogues & background music in END |
| 3    | Presence of sound effects  | Presence of level sound effects in END                       |
| 4    | Presence of ambient tracks | Identical to the 0th bit. Presence of ambient tracks in SPSX |
| 5-31 | ∅ Empty                    |                                                              |

### Common sound effects descriptors

> Mono only.

| Offset (h) | Size (h) | Usage               | Notes                                                        |
| :--------- | :------- | :------------------ | :----------------------------------------------------------- |
| 0x0        | 0x4      | Sampling rate       | **Seems unused by the engine !**                             |
| 0x4        | 0x2      | Sampling rate       | Multiply by 10.7666015625 (44100 / 4096) to get the sampling rate <sup>1</sup> |
| 0x6        | 0x2      | Volume level        | Values between -32768 and 32767, the sign seems to be ignored though |
| 0x8        | 0x1      | **UNKNOWN**         | Unknown flag, always 0 or 1                                  |
| 0x9        | 0x2      | Flags               | Two possible values: `00 00` and `01 01`. Imo, the 2nd one means that the sound is looped |
| 0xB        | 0x1      | ∅ Empty             |                                                              |
| 0xC        | 0x2      | **UNKNOWN**         |                                                              |
| 0xE        | 0x2      | **UNKNOWN**         | Always `42 00`                                               |
| 0x10       | 0x4      | Sound effect's size |                                                              |

### Ambient tracks descriptors

> Mono only.

| Offset (h) | Size (h) | Usage                | Notes                                                        |
| :--------- | :------- | :------------------- | :----------------------------------------------------------- |
| 0x0        | 0x4      | Sampling rate        | Values are close to common sampling rates, but not totally (15996 instead of 16000 for example) |
| 0x4        | 0x2      | Sampling rate        | Multiply by 11.71875 (48000 / 4096) to get the sampling rate <sup>2</sup> |
| 0x6        | 0x2      | **UNKNOWN**          |                                                              |
| 0x8        | 0x4      | **UNKNOWN**          |                                                              |
| 0xC        | 0x2      | **UNKNOWN**          |                                                              |
| 0xE        | 0x2      | **UNKNOWN**          |                                                              |
| 0x10       | 0x4      | Ambient track's size |                                                              |

### Level sound effects headers structure

> Level sound effects are separated into groups. Based on my observations, these groups seem to represent one object that can emit sound (like an enemy).  
> The headers are located in SPSX and the audio data in END. A 2048-bytes alignment is present before each group's audio data.

> '**lec**' = sum of all groups' sound effects count, see [Level sound effects groups descriptors](#Level-sound-effects-groups-descriptors)

| Offset (h) | Size (h)         | Usage                                                        | Notes                      |
| :--------- | :--------------- | :----------------------------------------------------------- | :------------------------- |
| 0x0        | 0x4              | Level sound effects groups count                             | Abbreviated to '**legc**'  |
| 0x4        | 0x4              | **UNKNOWN**                                                  |                            |
| 0x8        | 0x4              | **UNKNOWN**                                                  |                            |
| 0xC        | 0x4              | Unique level sound effects count                             | Abbreviated to '**ulsec**' |
| 0x10       | 0x10 × **legc**  | [Level sound effects groups descriptors](#Level-sound-effects-groups-descriptors) |                            |
| +0x0       | 0x14 × **lec**   | [Level sound effects descriptors](#Level-sound-effects-descriptors) |                            |
| ++0x0      | 0x10 × **ulsec** | [Level sound effects channels](#Level-sound-effects-channels-structure) |                            |

#### Level sound effects groups descriptors

| Offset (h) | Size (h) | Usage                                             | Notes                                                        |
| :--------- | :------- | :------------------------------------------------ | :----------------------------------------------------------- |
| 0x0        | 0x4      | Offset to the 1st group's sound effect descriptor | Starts from the beginning of the [Level sound effects descriptors](#Level-sound-effects-descriptors) |
| 0x4        | 0x4      | Group's sound effects count                       | The sum of these values among all groups (abbreviated to 'lec') gives us the total amount of level sound effects |
| 0x8        | 0x4      | Group's beginning offset                          | Starts at the beginning of the level sound effects audio data. See [END](END.md) |
| 0xC        | 0x4      | Group's size                                      | Does not include the 2048-bytes alignment                    |

#### Level sound effects descriptors

> Mono only.

If I'm not mistaken, identical to [Common sound effects descriptors](#Common-sound-effects-descriptors).

#### Dialogues & BGMs descriptors

> Mono or stereo, depending on the Dialogues & BGMs flags.

| Offset (h) | Size (h) | Usage                                            | Notes                                                        |
| :--------- | :------- | :----------------------------------------------- | :----------------------------------------------------------- |
| 0x0        | 0x4      | Beginning offset                                 | Starts at the beginning of the Dialogues & BGMs audio data. See [END](END.md) |
| 0x4        | 0x2      | Sampling rate                                    | Multiply by 10.7666015625 (44100 / 4096) to get the sampling rate <sup>1</sup> |
| 0x6        | 0x2      | [Dialogues & BGMs flags](#Dialogues--BGMs-flags) |                                                              |
| 0x8        | 0x4      | **UNKNOWN**                                      | Empty, or `35 00 00 00` for the bosses BGMs : gargoyle (T1L2M003) & ice potion knight (T1L4M009) |
| 0xC        | 0x4      | Sound's size                                     |                                                              |

#### Dialogues & BGMs flags

On your hex editor, the bits are in this order:  
`| 07 06 05 04 03 02 01 00 | 15 14 13 12 11 10 09 08 |`

| Bit  | Usage              | Notes                                                        |
| :--- | :----------------- | :----------------------------------------------------------- |
| 0    | Interleaved stereo | If set, the audio is 1024-bytes interleaved stereo, otherwise mono |
| 1    | **UNSURE**         | Never set when 0th bit is set (on stereo tracks that is)     |
| 2    | Background music   | If set, the track is intended for background music use       |
| 3-15 | ∅ Empty            |                                                              |

#### Level sound effects channels structure

This structure seems to list duplicated level sound effects amongst groups.

Each row represents an unique level sound effect. Each column seems to represent an audio channel which is bound to a level sound effect group.

Not every column needs to be filled, but groups seem to always be in order.

Values are either FF when empty or a level sound effect index (inside its group, not a global index).

There are always 16 columns, the first one being empty. We can then assume that there can be at most 15 level sound effect groups in one level.

##### Example:

| Empty | 0th channel | ...  | ...  | ...  | ...  | ...  | ...  | ...  | ...  | ...  | ...  | ...  | ...  | ...  | 14th channel |
| :---- | ----------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ------------ |
| FF    | FF          | FF   | FF   | 00   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF           |
| FF    | 00          | FF   | 01   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF           |
| FF    | FF          | FF   | 00   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF   | FF           |

This level has 4 level sound effects, 3 groups and 3 unique level sound effects.

The 0th column is empty, the 1st contains the 1st group, the 2nd is empty, the 3rd contains the 2nd group, the 4th contains the 3rd group, and the others are empty.

The 0th level sound effect of the 2nd group is unique to this level.

The 0th level sound effect of the 0th group and the 1st level sound effect of the 1st group are identical.

The 0th level sound effect of the 1st group is unique to this level.

## Footnotes

<sup>1</sup> : Here's my hypothesis : as 44100 Hz is the base CD sampling rate, they probably wanted to store it as 0x1000 (4096), a symbolic value.  
<sup>2</sup> : Same as before, but 0x1000 (4096) equals 48000 Hz.


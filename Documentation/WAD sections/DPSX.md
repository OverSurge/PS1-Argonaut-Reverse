# DPSX (XSPD) section documentation

> Not sure about what "D" stands for, maybe "Data"

The DPSX section contains a lot of different data (kind of like a WAD in a WAD, unfortunately).

In order, without gaps between them:

1. [3D models](../Data%20formats/3D%20models.md)
2. [Animations](../Data%20formats/Animations.md): Animations are stored in the same order as the actors.
3. [Actors](../Data%20formats/Actors.md): Actors are interactive objects instantiated in the 3D world in the level file (4.). They appear to contain Argonaut Strategy Language (ASL) code.
4. [Level](../Data%20formats/Level.md): Contains the level geometry, actors instances and lighting. The level geometry is divided into chunks.

## Section structure

| Offset (h) | Size (h)                 | Usage                                       | Notes                                                       |
| :--------- | :----------------------- | :------------------------------------------ | :---------------------------------------------------------- |
| 0x0        | 0x4                      | Section's name                              | Value: `58 53 50 44` ("XSPD")                               |
| 0x4        | 0x4                      | Section's size / Offset to the next section |                                                             |
| 0x8        | 0x4                      | [DPSX flags](#DPSX-flags-structure)         |                                                             |
| 0xC        | 0x4                      | Maybe "unique textures" count               | Same value as in [TPSX](TPSX.md) @0x2C                      |
| 0x10       | 0x800                    | Demo mode data                              | See [Demo mode](../WAD.md#Demo-mode)                        |
| 0x810      | **DEPENDS**              | **UNKNOWN**                                 | 0x4 long in Croc 2 Demo dummy WADs, nonexistent otherwise   |
| +0x0       | Sum of models' sizes     | 3D models file                              | See [3D models](../Data%20formats/3D%20models.md)           |
| ++0x0      | Sum of animations' sizes | Animations file                             | See [Animations](../Data%20formats/Animations.md)           |

- **If the 8th flags bit is set:**
  | Offset (h) | Size (h)    | Usage | Notes |
  | :--------- | :---------- | :------------------- | :----------------------------------------------------------- |
  | +++0x0 | **COMPLEX** | Additional 3D models | See [Additional 3D models](../Data%20formats/Additional%203D%20models.md) |

- **If the 18th flags bit is set:**
  | Offset (h) | Size (h)                 | Usage | Notes |
  | :--------- | :----------------------- | :------------------------------------------ | :---------------------------------------------------------- |
  | +++0x0 | 0x4 | Mid legacy textures count | Abbreviated to '**mltc**'                                   | | +++0x4 | 0xC00 × **mltc**         | Mid legacy textures | |

| Offset (h) | Size (h)             | Usage       | Notes                                                       |
| :--------- | :------------------- | :---------- | :---------------------------------------------------------- |
| ++++0x0    | Sum of actors' sizes | Actors file | See [Actors](../Data%20formats/Actors.md). Not reversed yet |
| +++++0x0   | **COMPLEX**          | Level file  | See [Level](../Data%20formats/Level.md)                     |

### DPSX flags structure

On your hex editor, the bits are in this order:  
`| 07 06 05 04 03 02 01 00 | 15 14 13 12 11 10 09 08 | etc.`

| Bit  | Usage                            | Notes |
| :--- | :------------------------------- | :---- |
| 0-7  | **UNKNOWN**                      |       |
| 8    | Presence of additional 3D models |       |
| 9-17 | **UNKNOWN**                      |       |
| 18   | Presence of mid legacy textures  |       |
| 19   | **UNKNOWN**                      |       |
| 20   | Presence of end legacy textures  |       |

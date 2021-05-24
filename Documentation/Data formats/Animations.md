# Animations format documentation

Animations are separated into frames.
Each frame stores a rotation and a translation per vertex group.  
Rotations can be stored as unit quaternions or in a 3x3 rotation matrix.  
Translations are stored as a 3D vector.

> What I call 'subframes' are the smallest indivisible piece of data (1 rotation & 1 translation for a single vertex group & a single animation frame).

As far as I know, there are two big versions of the animations format:

- The "new" one:  
  All frames don't need to be stored (they are probably interpolated).  
  As a result, a frame index is stored to keep an eye on which frame the data refers to.  
  Rotations are stored as an unit quaternion.  
  Subframes are 0x10 (16) bytes long.
- The "old" one:  
  All frames needed to be stored, so there was no need to store a frame index.  
  Rotations are stored in a 3×3 rotation matrix.  
  Subframes are 0x18 (24) bytes long.

In Croc 2 PS1, only the old format is used. In Harry Potter PS1, a majority of the animations use the new format, but some use the old one.

## File structure

Starting with Harry Potter 1 PS1, the base header size increased (from 0x20 to 0x30) in order to store the stored frames count and maybe other information.

### Animations file header

| Offset (h) | Size (h)                 | Use                                |
| :--------- | :----------------------- | :--------------------------------- |
| 0x0        | 0x4                      | Animations count                   |
| 0x4        | Sum of animations' sizes | [Animations](#Animation-structure) |

### Animation structure

#### In Harry Potter

| Offset (h) | Size (h)                             | Use                 | Notes                                                        |
| :--------- | :----------------------------------- | :------------------ | :----------------------------------------------------------- |
| 0x0        | 0x4                                  | **UNKNOWN**         | Unknown count, linked to some sort of flags at 0x30. Abbreviated to '**uc**' |
| 0x4        | 0x4                                  | ∅ Empty             |                                                              |
| 0x8        | 0x4                                  | Total frames count  | As opposed to stored frames count, this value even includes non-stored frames. Abbreviated to '**tf**' |
| 0xC        | 0x4                                  | **UNKNOWN**         | I've only seen 2 values: 0 & 1. If == 0, some sort of data appears later. Abbreviated to '**uk**' |
| 0x10       | 0x8                                  | ∅ Empty             |                                                              |
| 0x18       | 0x4                                  | Vertex groups count | Abbreviated to '**vg**'                                      |
| 0x1C       | 0x4                                  | ∅ Empty             |                                                              |
| 0x20       | 0x4                                  | Stored frames count | Amount of effectively stored frames. **IMPORTANT**: If this value is null, the animation format is the old one (as all frames must be stored), else it is the new one. Abbreviated to '**sf**' |
| 0x24       | 0xC                                  | ∅ Empty             |                                                              |
| 0x30       | 0x4 × **uc**                         | **UNKNOWN**         | Can be nonexistent if **uc** == 0. Looks like some sort of flags, probably divided into 2-byte values that seems linked to a frame index (including non-stored ones) given the values I encountered |
| +0x0       | 0x0 if **uk** == 1 else 0x8 × **tf** | **UNKNOWN**         | If **uk** == 0, what looks like frame data appear here       |
| ++0x0      | 0x4 × **tf** + 0x4 × **sf**          | **UNKNOWN**         | Often zeros, but not always. Some sort of flags              |
| +++0x0     | Subframe size × **vg** × **sf**      | Animation frames    | Subframe size: 0x18 for the [old format](#Old-animation-format), 0x10 for the [new one](#New-animation-format) |

#### In Croc 2

> What I call 'interframe' is a feature I discovered on pre-Harry Potter games that inserts data between frames (and at the end of the header). It is enabled if the interframe count is not null.  
> It is structured like that (H: Header, IH: Interframe Header, F: Frame, ID: Interframe Data):
> `H IH F ID F ID F ID F`

| Offset (h) | Size (h)                             | Use                 | Notes                                                        |
| :--------- | :----------------------------------- | :------------------ | :----------------------------------------------------------- |
| 0x0        | 0x4                                  | **UNKNOWN**         | Unknown count, linked to some sort of flags at 0x20. Abbreviated to '**uc**' |
| 0x4        | 0x4                                  | ∅ Empty             |                                                              |
| 0x8        | 0x4                                  | Total frames count  | As opposed to stored frames count, this value even includes non-stored frames. Abbreviated to '**tf**' |
| 0xC        | 0x4                                  | **UNKNOWN**         | I've only seen 2 values: 0 & 1. If == 0, some sort of data appears later. Abbreviated to '**uk**' |
| 0x10       | 0x4                                  | Interframe count    | I don't know how this value is calculated. Abbreviated to '**ic**' |
| 0x14       | 0x4                                  | ∅ Empty             |                                                              |
| 0x18       | 0x4                                  | Vertex groups count | Abbreviated to '**vg**'                                      |
| 0x1C       | 0x4                                  | ∅ Empty             |                                                              |
| 0x20       | 0x4 × **uc**                         | **UNKNOWN**         | Can be nonexistent if **uc** == 0. Looks like some sort of flags, probably divided into 2-byte values that seems linked to a frame index (including non-stored ones) given the values I encountered |
| +0x0       | 0x0 if **uk** == 1 else 0x8 × **tf** | **UNKNOWN**         | If **uk** == 0, what looks like frame data appear here       |
| ++0x0      | 0x4 × **tf**                         | **UNKNOWN**         | Often zeros, but not always                                  |
| +++0x0     | 0x0 or 0x4 × **sf**                  | **UNKNOWN**         | Can be nonexistent if there are no interframes (interframe count == 0) |
| ++++0x0    | 0x8 × **ic**                         | **UNKNOWN**         | Interframe header data, unknown purpose                      |
| +++++0x0   | 0x18 × **vg** × **tf**               | Animation frames    | See [Old animation format](#Old-animation-format) (it was the only one used back then) |


### Old animation format

#### Old format's frame structure

| Offset (h) | Size (h)      | Use                                          |
| :--------- | :------------ | :------------------------------------------- |
| 0x0        | 0x18 × **vg** | [Subframes](#Old-formats-subframe-structure) |

If **ic** != 0, interframe data appears **between** (not after the last one) each frame (2 × **ic** long (Rounded up to a multiple of 4)). Not reversed yet.

#### Old format's subframe structure

Rxy indicates matrix positions:

```
R      y
  ┌──┬──┬──┐
  │11│12│13│
  ├──┼──┼──┤
x │21│22│23│
  ├──┼──┼──┤
  │31│32│33│
  └──┴──┴──┘
```

| Offset (h) | Size (h) | Use                    | Notes                                                        |
| :--------- | :------- | :--------------------- | :----------------------------------------------------------- |
| 0x0        | 0x2      | R11 ┐                  |                                                              |
| 0x2        | 0x2      | R12 ┤                  |                                                              |
| 0x4        | 0x2      | R13 ┤                  |                                                              |
| 0x6        | 0x2      | R21 ┤                  |                                                              |
| 0x8        | 0x2      | R22 ┼ Matrix           | Stores transformation information. Values between -32768 and 32767 |
| 0xA        | 0x2      | R23 ┤                  |                                                              |
| 0xC        | 0x2      | R31 ┤                  |                                                              |
| 0xE        | 0x2      | R32 ┤                  |                                                              |
| 0x10       | 0x2      | R33 ┘                  |                                                              |
| 0x12       | 0x2      | x ┐                    |                                                              |
| 0x14       | 0x2      | y ┼ Translation vector |                                                              |
| 0x16       | 0x2      | z ┘                    |                                                              |

### New animation format

### New format's frame structure

| Offset (h) | Size (h)      | Use                                          |
| :--------- | :------------ | :------------------------------------------- |
| 0x0        | 0x10 × **vg** | [Subframes](#New-formats-subframe-structure) |

#### New format's subframe structure

| Offset (h) | Size (h) | Use                    | Notes                                                        |
| :--------- | :------- | :--------------------- | :----------------------------------------------------------- |
| 0x0        | 0x2      | w ┐                    |                                                              |
| 0x2        | 0x2      | x ┼ Unit quaternion    | Stores rotation information. Values between -4096 and 4096, Euclidean distance of the 4 values is 4096 |
| 0x4        | 0x2      | y ┤                    |                                                              |
| 0x6        | 0x2      | z ┘                    |                                                              |
| 0x8        | 0x2      | x ┐                    |                                                              |
| 0xA        | 0x2      | y ┼ Translation vector |                                                              |
| 0xC        | 0x2      | z ┘                    |                                                              |
| 0xE        | 0x2      | Frame index            | Starts at 0 and goes up                                      |


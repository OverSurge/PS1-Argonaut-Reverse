# Level format documentation

The level format can be separated in 5 parts :

- The level geometry, which contains reusable 3D models of walls, ground, ceiling, furniture, etc.
- The level header, which contains various information about the other data in the level file.
- The 3D world, which contains all information about where each piece of geometry is placed.
- The actors and lighting information, which contains the position of the actors (characters, doors, etc) and how the level is lit.
- The level footer, its use is not yet known.

## Levels format's concepts


### General concept

The 3D world is divided into chunks (like in Minecraft for example). Most of them are empty. Each filled chunk can
contain one or multiple subchunks, each one of them having a 3D model.  
Each chunk and subchunk is unique, but chunk 3D models are reusable, in order to reduce the file size.  
Chunk 3D models' structure is very similar to regular 3D models, except these ones don't contain vertex normals (except
in Croc 2 Demo dummy WADs).

### Axes

The 3D world's axes are arranged that way (Y up). The chunks matrix follow that logic.

````
Y
 ┌ ─ ► X
 │
 ▼
 Z
````

### Chunks matrix

The chunks matrix is made of 4 bytes offsets that refer to subchunks information.  
A 0xFFFFFFFF offset denotes that the chunk is empty.  
These offsets start just after the end of the matrix.

Example :

> A primary subchunk is declared in the chunk matrix, contrary to a secondary subchunk, that is linked to a primary subchunk by another subchunk.

````
Chunks matrix ┬► Primary subchunk → Secondary subchunk
              ├► Primary subchunk → Secondary subchunk → Secondary subchunk → Secondary subchunk
              ├► Empty
              └► Primary subchunk
````

### Lighting

This level format **doesn't** seem to use light sources (with a position, a color and an intensity for example).  
Instead, levels' lighting is pre-rendered and stored as one color per vertex, for each vertex in the level.  
Usually, there is one lighting data structure for each subchunk (+ one for each additional lighting header), but there
can be more in case of "dynamic" lighting (for example, near the fireplace in the common room).

## File structure

> I cannot document the Croc level format yet, as I haven't managed to reverse it entirely. There are sound effects, textures and strings inside it (+ usual stuff there is in the newer format).  
>
> For the sake of readability, given the large amount of values, start offsets are omitted from this section, there is no gap between values (unless I made a mistake on the documentation).

### Level geometry

Unlike regular 3D models, chunk 3D models headers and data are separated: all headers and data are stored contiguously.

| Size (h)                      | Use                     | Notes                            |
| :---------------------------- | :---------------------- | :------------------------------- |
| 0x4                           | Chunk 3D models count   | Abbreviated to '**cmc**'         |
| 0x68 × **cmc**                | Chunk 3D models headers | All headers are stored in one go |
| Sum of chunk 3D models' sizes | Chunk 3D models data    | Same as before, stored in one go |

### Level header

| Size (h)      | Use                                   | Notes                                   |
| :------------ | :------------------------------------ | :-------------------------------------- |
| 0x8           | **UNKNOWN**                           |                                         |
| 0x4           | Subchunks count                       | Abbreviated to '**scc**'                |
| 0x4           | Unknown count                         | Abbreviated to '**uk1**'                |
| 0x4 × **uk1** | **UNKNOWN**                           |                                         |
| 0x4           | Subchunks count                       | Identical to the previous one           |
| 0x2           | Actor instances count                 | Abbreviated to '**aic**'                |
| 0x2 or 0x6    | **UNKNOWN**                           | 0x2 in Croc 2 Demo dummy WADs, else 0x6 |
| 0x4           | Total chunks count (X × Z counts)     | Abbreviated to '**tcc**'                |
| 0x4           | X axis chunks count ("chunk columns") |                                         |
| 0x4           | Z axis chunks count ("chunk rows")    |                                         |

- **If the game isn't Croc 2 Demo dummy WADs:**

  | Size (h) | Use                               | Notes                                                        |
  | :------- | :-------------------------------- | :----------------------------------------------------------- |
  | 0x2      | Lighting headers count            | Abbreviated to '**lc1**'. See [Lighting information](#Lighting-information-structure) |
  | 0x2      | Additional lighting headers count | Abbreviated to '**lc2**'. See [Lighting information](#Lighting-information-structure) |
  | 0x4      | **UNKNOWN**                       |                                                              |

| Size (h)     | Use           | Notes                                                        |
| :----------- | :------------ | :----------------------------------------------------------- |
| 0x4          | Unknown count | Abbreviated to '**uk2**'                                     |
| 0x50 or 0x74 | **UNKNOWN**   | Rest of the level header. 0x50 in Croc 2 Demo dummy WADs, else 0x74 |

### 3D world

| Size (h)      | Use                                             | Notes |
| :------------ | :---------------------------------------------- | :---- |
| 0x4 × **tcc** | Chunks matrix                                   |       |
| 0x8 × **scc** | [Subchunks headers](#Subchunk-header-structure) |       |

- **If the game isn't Croc 2 Demo dummy WADs:**
  
  | Size (h)                    | Use                       | Notes                                                        |
  | :-------------------------- | :------------------------ | :----------------------------------------------------------- |
  | 0x100                       | **UNKNOWN**               | Doesn't change a lot between levels                          |
  | 0x4                         | Zone ids count            | AFAIK, equal to **tcc**                                      |
  | 0x4 × **tcc**               | Zone ids                  | The same system exists in the [PORT section](../WAD%20sections/PORT.md), but reversed (which chunks belong to a zone) |
  | 0x0, or 0x4 + 0x2 × **tcc** | [fvw matrix](#fvw-matrix) | Optional, the engine checks for the presence of `66 76 77 00` (fvw ) at that position and skips it if it doesn't match |

| Size (h)       | Use                                                          | Notes                                               |
| :------------- | :----------------------------------------------------------- | :-------------------------------------------------- |
| 0x18 × **scc** | [Subchunks position information](#Subchunk-position-information-structure) |                                                     |
| 0x4 × **scc**  | Subchunks 3D models mapping                                  | For each subchunk, stores the 3D models' id it uses |

### Actors & lighting information

- **If the game isn't Croc 2 Demo dummy WADs:**
  
  | Size (h)       | Use              | Notes |
  | :------------- | :--------------- | :---- |
  | 0x54 × **lc1** | Lighting headers |       |

> The rest of this documentation file only applies to Harry Potter, I'm still working on Croc 2.

| Size (h)                                | Use                                                          | Notes                                                        |
| :-------------------------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| 0x24 × **uk2**                          | **UNKNOWN**                                                  | TODO Has an impact on camera position, ability to cast spells, game rules, etc |
| 0x40 × **aic**                          | [Actor instances headers](#Actor-instances-headers-structure) |                                                              |
| 0x18 × **lc2**                          | Additional lighting headers                                  |                                                              |
| 0x4                                     | Unknown count                                                | Abbreviated to '**uk3**'                                     |
| 0x20 × **uk3**                          | **UNKNOWN**                                                  |                                                              |
| 0x4 × **scc**                           | Subchunk lighting count                                      | When > 1, means that the subchunk can be lit dynamically and therefore has multiple lighting info data. See [Lighting information](#Lighting-information-structure) |
| 0x4 × **lc2**                           | Additional lighting count                                    | Same as before, but I don't know on which subchunk they are applied and why. |
| Sum of subchunk lighting info's sizes   | Subchunk lighting information                                | See [Lighting information](#Lighting-information-structure)  |
| Sum of additional lighting info's sizes | Additional lighting info                                     | See [Lighting information](#Lighting-information-structure)  |

### Footer (unknown use)

| Size (h)              | Use           | Notes                                                        |
| :-------------------- | :------------ | :----------------------------------------------------------- |
| 0x0, or 0x8 + **uk4** | Unknown size  | Optional, if these 4 bytes are null, then nonexistent. Abbreviated to '**uk4**' |
| 0x0, or 0x4           | Unknown count | Optional, if these 4 bytes are null, then nonexistent. Abbreviated to '**uk5**' |
| 0x28 × **uk5**        | **UNKNOWN**   |                                                              |
| 0xC                   | **UNKNOWN**   |                                                              |

#### Subchunk header structure

| Offset (h) | Size (h) | Use                          | Notes                                        |
| :--------- | :------- | :--------------------------- | :------------------------------------------- |
| 0x0        | 0x4      | Subchunk id                  |                                              |
| 0x4        | 0x4      | Offset to secondary subchunk | If 0xFFFFFFFF, doesn't link another subchunk |

#### fvw matrix

| Offset (h) | Size (h)      | Use                   | Notes                                                    |
| :--------- | :------------ | :-------------------- | :------------------------------------------------------- |
| 0x0        | 0x4           | fvw codename          | `66 76 77 00` (fvw )                                     |
| 0x4        | 0x2 × **scc** | Unknown subchunk flag | 'vw' reminds me of 'view', could be linked to the camera |

#### Subchunk position information structure

| Offset (h) | Size (h) | Use                      | Notes                                                        |
| :--------- | :------- | :----------------------- | :----------------------------------------------------------- |
| 0x0        | 0x4      | Subchunk Y rotation      | `00000000`: 0°, `00000004`: 90°, `00000008`: 180°, `0000000C`: 270° |
| 0x4        | 0x4      | ∅ Empty                  |                                                              |
| 0x8        | 0x4      | Subchunk's X translation | Same scale as in 3D models                                   |
| 0xC        | 0x4      | Subchunk's Y translation | Same scale as in 3D models                                   |
| 0x10       | 0x4      | Subchunk's Z translation | Same scale as in 3D models                                   |
| 0x14       | 0x4      | ∅ Empty                  |                                                              |

#### Actor instances headers structure

| Offset (h) | Size (h) | Use                         | Notes                                                        |
| :--------- | :------- | :-------------------------- | :----------------------------------------------------------- |
| 0x0        | 0x18     | **UNKNOWN**                 |                                                              |
| 0x18       | 0x4      | Actor offset                | Starts at the beginning of [DPSX](../WAD%20sections/DPSX.md) |
| 0x1C       | 0x20     | **UNKNOWN**                 |                                                              |
| 0x3C       | 0x4      | Sound effects' volume level | Should work like other volume level values in [SPSX](../WAD%20sections/SPSX.md) |

#### Lighting information structure

> '**lc**' is the subchunk's lighting count (usually 1 unless there are multiple lighting cases for this subchunk).  
> '**vc**' is the vertices count of the 3D model the subchunk uses.

| Offset (h) | Size (h)              | Use                             |
| :--------- | :-------------------- | :------------------------------ |
| 0x0        | 0x4 × **vc** × **lc** | Subchunk's lighting information |

| Offset (h) | Size (h)     | Use                         |
| :--------- | :----------- | :-------------------------- |
| 0x0        | 0x4 × **vc** | Vertex lighting information |

| Offset (h) | Size (h) | Use             |
| :--------- | :------- | :-------------- |
| 0x0        | 0x1      | Red component   |
| 0x1        | 0x1      | Green component |
| 0x2        | 0x1      | Blue component  |
| 0x3        | 0x1      | **UNKNOWN**     |


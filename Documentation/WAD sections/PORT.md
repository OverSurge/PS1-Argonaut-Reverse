# PORT (TROP) section documentation

Seems to contain information related to rendering groups / zones.

Linked to [Level's zone ids](../Data%20formats/Level.md), which are the contrary of the zone chunks ids (PORT's one lists each chunk id of a zone, level's one gives the zone id of each chunk).

## Section structure

| Offset (h) | Size (h)                  | Usage                                         | Notes                         |
| :--------- | :------------------------ | :-------------------------------------------- | :---------------------------- |
| 0x0        | 0x4                       | Section's name                                | Value: `54 52 4F 50` ("TROP") |
| 0x4        | 0x4                       | Section's size / Offset to the next section   |                               |
| 0x8        | 0x4                       | Zones count                                   | Abbreviated to '**zc**'       |
| 0xC        | 0x4                       | Unknown count                                 | Abbreviated to '**uk2**'      |
| 0x10       | 0x20 × **uk2**            | **UNKNOWN**                                   |                               |
| +0x0       | 0xC × **zc**              | [Zone headers](#Zone-headers-structure)       | One header per zone           |
| ++0x0      | 0x2 × (Sum of all **cc**) | [Zone chunks ids](#Zone-chunks-ids-structure) | Abbreviated to '**zci**'      |

### Zone headers structure

| Offset (h) | Size (h) | Usage                               | Notes                                                       |
| :--------- | :------- | :---------------------------------- | :---------------------------------------------------------- |
| 0x0        | 0x2      | **UNKNOWN**                         |                                                             |
| 0x2        | 0x1      | Chunks count                        | How many chunks this zone contains. Abbreviated to '**cc**' |
| 0x3        | 0x1      | **UNKNOWN**                         |                                                             |
| 0x4        | 0x2      | Start offset of the data in **zci** | Needs to be multiplied by 2                                 |

### Zone chunks ids structure

| Offset (h) | Size (h)                    | Usage     | Notes                                      |
| :--------- | :-------------------------- | :-------- | :----------------------------------------- |
| 0x0        | 0x2 × (**cc** of this zone) | Chunk ids | One id per chunk that belongs to this zone |


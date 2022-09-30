# Additional 3D models format documentation

Additional 3D models appear in old versions of the level file format. They work similarly to
regular [3D models](3D%20models.md).

## File structure

| Offset (h) | Size (h)                 | Use                                                          |
| :--------- | :----------------------- | :----------------------------------------------------------- |
| 0x0        | 0x8                      | Value: `01 00 00 00 41 30 30 00`                             |
| 0x8        | 0x4                      | Additional 3D models count. Abbreviated to '**amc**'         |
| 0xC        | 0x8                      | **UNKNOWN**                                                  |
| 0x14       | 0x8 × **amc**            | [Vertices groups counts](#Vertices-groups-count-structure)   |
| +0x0       | (0x64 or 0x68) × **amc** | Additional 3D models headers. See [3D models headers](3D%20models.md#3D-model-header) |
| ++0x0      | Sum of models' sizes     | Additional 3D models data. See [3D models data](3D%20models.md#3D-model-data) |

### Vertices groups count structure

> See [Vertex groups](3D%20models.md#Vertex-groups) for more information.

| Offset (h) | Size (h)             | Use                                                          |
| :--------- | :------------------- | :----------------------------------------------------------- |
| 0x0        | 0x4                  | **UNKNOWN**                                                  |
| 0x4        | 0x4                  | Vertex groups count                                          |

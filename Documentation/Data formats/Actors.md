# Actors format documentation

## File structure

| Offset (h) | Size (h)             | Use                         |
| :--------- | :------------------- | :-------------------------- |
| 0x0        | 0x4                  | Actors count                |
| +0x0       | Sum of actors' sizes | [Actors](#Actors-structure) |

### Actors structure

| Offset (h) | Size (h) | Use        | Notes                                                        |
| :--------- | :------- | :--------- | :----------------------------------------------------------- |
| 0x0        | 0x4      | Actor size | Abbreviated to '**as**'. Multiply by 4 to get the size in bytes. |
| 0x4        | **as**   | Actor data | Not reversed yet                                             |

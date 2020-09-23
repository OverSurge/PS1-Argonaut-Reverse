# DEM files documentation

> DEM is probably for "Demo"

A DEM file is bound to a WAD file, they share the same filename (but not the same extension obviously).  
DEM files are only present on levels that support [Demo mode](WAD.md#Demo-mode)
(triggered when you don't use your controller for a minute or so on the title screen), hence their name.

It *could* be linked to Argonaut Strategy Language (ASL).

| Offset (h) | Size (h)      | Usage             | Notes                                                        |
| :--------- | :------------ | :---------------- | :----------------------------------------------------------- |
| 0x0        | 0x4           | Demo frames count | I don't what those frames mean yet. Abbreviated to '**dfc**' |
| 0x4        | 0x8 × **dfc** | Demo frames       | Not reversed yet                                             |


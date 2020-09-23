# General information

This document lists BRender formats' key concepts.

#### Little endian

BRender uses little endian. Consider all values as stored in little endian, unless otherwise specified.

#### Offsets

Offsets are relative and must be added **after** the value's **end address**. An example:  

```
00 00 00 00 | 00 00 00 0C | 01 02 03 04 | 05 06 07 08 | 09 0A 0B 0C | 00 00 00 00
              ↑↑ ↑↑ ↑↑ ↑↑                             ↑             ↑
           Offset (0x4 long)                      not here         HERE
```

#### "Chained" data structures

A lot of BRender's data structures don't store the size of their children.  
Consequently, if a value is misinterpreted during extraction and leads the script to misjudge the child's length, the script will, for example, try to interpret raw data as an amount value, and will crash.  
It also means that, in order to retrieve a precise child, you must have correctly extracted (at least correctly calculated the sizes of) all previous children.

#### WAD "self-sufficiency" and redundancy

The engine generally only loads one WAD at a time (at least, one level WAD (TxLxM00x)) (I have no proof of that).  
That causes multiple WAD files to store the same assets (like Harry's 3D model, GUI icons, etc) multiple times, because they can't be loaded from another WAD.

### Thank you for reading this ! Have a look at the [WAD documentation](WAD.md) if you want to go any further.


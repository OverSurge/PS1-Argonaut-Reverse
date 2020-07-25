# XSPD section documentation
> Not sure about what "D" stands for, maybe "Data"

The XSPD section contains a lot of different data (kind of like a WAD in a WAD, unfortunately).

In order, without gaps between them:
1. [3D models](../Data%20formats/3D%20models.md)
2. [Animations](../Data%20formats/Animations.md): Animations are stored in the same order as the objects.
3. "Objects": These objects seem to link 3D models, animations, textures, etc together
into objects that can then be instantiated in the world (4.).
I didn't manage to reverse this part yet. It could contain Argonaut Strategy Language (ASL) code.
4. [3D world](../Data%20formats/3D%20world.md): Describes objects instances inside the 3D world. Very early reverse.

## Section structure

|Offset (h)|Size (h)|Usage|Notes|
|:---|:---|:---|:---|
|0x0|0x4|Section name|Value: `58 53 50 44` ("XSPD")|
|0x4|0x4|Offset to the next section|
|0x8|0x4|**UNKNOWN**|*Might* be 2 separate values of 2 bytes each
|0xC|0x4|Maybe "unique textures" count|Same value as in [XSPT](XSPT.md) @0x2C
|0x10|0x800|Demo mode data|See [Demo mode](../WAD.md#Demo-mode)
|0x810|**DEPENDS**|**UNKOWN**|0x4 long in Croc 2 Demo dummy WADs, nonexistent otherwise|
|+0x0|Sum of models' sizes|3D models file|See [3D models](../Data%20formats/3D%20models.md)|
|++0x0|Sum of animations' sizes|Animations file|See [Animations](../Data%20formats/Animations.md)|
|+++0x0|?|Objects file|Not reversed yet|
|?|?|3D world and other non-reversed data structures|Not reversed yet, see [3D world](../Data%20formats/3D%20world.md) for a very early reverse of the 3D world format.|
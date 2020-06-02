# 3D models format documentation

3D models are stored one after the other, there is no way I'm aware of of knowing by advance their size.
They seem to contain vertices, vertices normals (same amount & order), faces, and sometimes, other data after that.  
Vertices are divided into vertex groups, for more info, see [Groups](#Groups-explanation).  
An [animation](Animations.md) only stores one translation & rotation by vertex group.  
Vertices inside the same vertex group cannot be animated separately.

**Animatable** models are **not** stored in T-pose or star pose, if you preview/convert them without any modification, they will look messy/glitched.
In order to preview it, you must apply an animation frame to it (from an [animation](Animations.md) made for this model).

> I didn't manage to reverse [objects](../WAD%20sections/XSPD.md) yet, as a consequence, models and animations can't be linked automatically. As animations seems to be stored in the same order as 3D models, and, as vertex groups count is stored in animation headers, it is possible to guess which model an animation refers to.

## File structure

### 3D models file header
|Offset (h)|Size (h)|Use|
|:---|:---|:---|
|0x0|0x4|Models count|
|0x4|Sum of models' sizes|[3D models](#3D-model-structure)|

### 3D model structure

> Extended data size, abbreviated to 'eds', is 0x2C long in Croc 2 Demo PS1, and 0x20 long in Harry Potter 1 PS1.

|Offset (h)|Size (h)|Use|Notes|
|:---|:---|:---|:---|
|0x0|0x48|**UNKNOWN**|The values around 0x30-0x43 may contain bounding box info<sup>**1**</sup>. Tinkering with them makes the models disappear before they hit the border of the screen and reappear when they are already entirely on screen|
|0x48|0x4|Vertices count|Abbreviated to 'vc'|
|0x4C|0x8|∅ Empty||
|0x54|0x4|Faces count|Abbreviated to 'fc'|
|0x58|0x4|∅ Empty||
|0x5C|0x2|1st amount of extended data|These 3 amounts are 0 most of the time, but in some models, this isn't the case, and data appear at the end of the model. Abbreviated to 'ed1'|
|0x5E|0x2|2nd amount of extended data|Abbreviated to 'ed2'|
|0x60|0x2|3rd amount of extended data|Abbreviated to 'ed3'|
|0x62|**DEPENDS**|∅ Empty|Size: Croc 2 Demo: 0x2, Harry Potter 1 PS1: 0x6|
|+0x0|0x8 × *vc*|[Vertices coordinates](#Vertex-coordinates-structure)||
|++0x0|0x8 × *vc*|[Vertices normals](#Vertex-normal-structure)|(Seems like vertices normals, but I could be wrong)|
|+++0x0|0x14 × *fc*|[Faces](#Face-structure)||
|++++0x0|*eds* × (*ed1* + *ed2* + *ed3*)|**UNKNOWN**|Can be nonexistent if sum is 0. Extended data, unknown use for now. Could be related to faces, as the sum is often equal to face count|

<sup>**1**</sup> : Similarities with [Croc 1's Format/Content Revision](https://web.archive.org/web/20140708201323/http://www.epiczen.net/crocfileformats.html) by Rexhunter, Andre, Zane, Paul

### Vertex coordinates structure
|Offset (h)|Size (h)|Use|Notes|
|:---|:---|:---|:---|
|0x0|0x2|x ┐|
|0x2|0x2|y ┼ 3D position of vertex| Signed shorts
|0x4|0x2|z ┘|
|0x6|0x2|Vertex index in group|Used to deduce vertex group, see [Vertex groups](#Vertex-groups)

### Vertex normal structure
|Offset (h)|Size (h)|Use|Notes|
|:---|:---|:---|:---|
|0x0|0x2|x ┐|
|0x2|0x2|y ┼ Normal vector?|Values between -4096 and 4096, euclidean distance of the 3 values is 4096
|0x4|0x2|z ┘|
|0x6|0x2|Vertex index in group|Same as before, see [Vertex groups](#Vertex-groups)

### Face structure
|Offset (h)|Size (h)|Use|Notes|
|:---|:---|:---|:---|
|0x0|0x2|x ┐|
|0x2|0x2|y ┼ Face normal (vector)?|Values between -4096 and 4096, euclidean distance of the 3 values is 4096
|0x4|0x2|z ┘|
|0x6|0x2|Face index in group|See [Face groups](#Face-groups)
|0x8|0x2|1st vertex index|
|0xA|0x2|2nd vertex index|
|0xC|0x2|3rd vertex index|
|0xE|0x2|4th vertex index|If the face is a triangle (belongs to the 2nd [face group](#Face-groups)), this field is 0
|0x10|0x2|Texture index|See [Textures](Textures.md)
|0x12|0x2|**UNKNOWN**|Most probably flags, not reversed yet

#### Quadrilaterals vertices order

I'm not 100% sure of the order in which the vertices should be linked, but they are declared like that (In a Z-shape):
````
4       3
 ┌ ─ ─ ┐
 └ ─ ─ ┘
2       1
````
So you can link them in this order for example: `1, 2, 4, 3`.

## Groups explanation

#### Vertex groups

Each vertex and vertex normal contains an index.
Those indexes decrease until they reach 1, which shows the end of the present group.
As we know this, we can separate them into vertex groups.  
An example:

|Vertex "in group" index (h)|Group id (not stored, deduced from indexes)
|:---|:---|
|0x3|0|
|0x2|0|
|0x1|0|
|0x1|1|
|0x2|2|
|0x1|2|
|0x1|3|
|...|4|

#### Face groups

Faces use the same system as vertices groups, but can only have 1 or 2 groups in total.  
The first group contains quadrilateral faces, the second triangle faces.
If there are only 1 face group, all faces are quadrilaterals (as far as I know).
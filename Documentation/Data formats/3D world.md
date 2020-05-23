# 3D world format documentation

TODO: The 3D world format is very vaguely reversed.

> On this page, I talk about owls: these are the ones you can see on the title screen (T1I0M000.WAD).
> I worked a lot on them, because they allow me to see the result of animations, 3D models, etc. tinkering without having to wait for the game to load a game save and a complex level.

In order:
- Other non-reversed data \[...\]
- 'fvw.' (0x66767700) followed by 00s, FFs and other values
- 1st headers (0x18 long each)
- 2nd headers (0x24 bytes long each)
  - 0-3: Header id ? (On T1L1M000, the 5th is null instead of 05000000)
- Objects descriptors (0x40 (64) bytes long each):
  - First bytes: Could be related to x,y,z coordinates or rotation information
  - \[...\]
  - 18-1C: **This is the most important value**: It links an object instance to the source object. Seems to be the offset starting at the beginning of XSPD's section to some data inside an object (It doesn't point at the beginning of the object, weird).
  - \[...\]
  - 24-26: If set to 0, owl trajectories aren't refreshed, they go straight on.
  - \[...\]
  - 34-38: Could be rotation information
  - \[...\]
  - 3C-3F (last bytes): Related to the object's sound effects. When I set those bytes to 0 on the owls' descriptors, I couldn't ear their hoots anymore.
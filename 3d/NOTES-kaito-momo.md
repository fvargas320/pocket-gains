# Kaito & Momo: Tripo H3.1 multiview (fal tripo3d/h3.1/multiview-to-3d)

Inputs: mockups-v7/<char>/apose_{front,side_left,back,side_right}.png, detailed geometry + texture, PBR.
**Slot order that works: [front, side_left (faces image-left), back, side_right (faces image-right)].**
The first try had the side views swapped, which gave two-faced (Janus) meshes: Momo had a second face on the back of her
head. Those meshes are kept as *_v1_janus.glb for reference only. Don't use them.

| file | tris | verts | islands | textures |
|---|---|---|---|---|
| kaito/kaito_tripoh31.glb (64 MB) | 2.00 M | 1.03 M | 392 | 4K color / normal / ORM |
| momo/momo_tripoh31.glb (65 MB) | 1.94 M | 1.00 M | 198 | 4K color / normal / ORM |

Previews: <char>/previews/<char>_{front,three_quarter,side,back}.png
(`blender -b -P tools/preview.py -- in.glb out prefix yaw=-90`: Tripo meshes face -X, so yaw=-90 is needed).

Honest quality: silhouettes, outfits and colours read well from every angle and the backs are clean. These are still
single-mesh, triangle-soup scans: there are no separate clothes, eyes or mouth, 2 M tris, and the faces are baked into
the texture. Kaito's headband tails are fused to the back of the neck. Momo's 3/4 face slightly stretches the eyes. To use
them in the game, they need the same pipeline as Zeek v2/v3: retopo to roughly 8–15k tris, rig to the shared joint list
(v2work/joints.json; Kaito needs longer limb bones), sculpt the 11 shape keys, and add a face texture/decals for
expressions. Good as sculpt and texture references and for quick previews; not production-ready as-is.

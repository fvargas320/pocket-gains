import bpy, sys, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--')+1:]; src, dst, yaw = a[0], a[1], float(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
R = Matrix.Rotation(math.radians(yaw), 4, 'Z')
for o in ms:
    o.data.transform(R @ o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
co = [v.co for o in ms for v in o.data.vertices]
mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
off = Vector((-(mn.x+mx.x)/2, -(mn.y+mx.y)/2, -mn.z))
for o in ms: o.data.transform(Matrix.Translation(off)); o.name = 'Zeek'
for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']: bpy.data.objects.remove(o)
print('DIMS', [round(x,3) for x in (mx-mn)])
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_image_format='AUTO')

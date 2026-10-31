import bpy, bmesh, math, glob
from mathutils import Matrix, Vector
SRC='/workspace/gym-app/3d/alternates/zeek_base_tripoh31_raw.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ms=[o for o in bpy.context.scene.objects if o.type=='MESH']; body=ms[0]
me=body.data; me.transform(Matrix.Rotation(math.radians(-90),4,'Z') @ body.matrix_world)
for o in list(bpy.context.scene.objects):
    if o!=body: bpy.data.objects.remove(o)
body.parent=None; body.matrix_world=Matrix.Identity(4)
bm=bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
co=[v.co for v in bm.verts]
mn=Vector([min(c[i] for c in co) for i in range(3)]); mx=Vector([max(c[i] for c in co) for i in range(3)])
s=1.0/(mx.z-mn.z)
bmesh.ops.translate(bm,verts=bm.verts,vec=Vector((-(mn.x+mx.x)/2,-(mn.y+mx.y)/2,-mn.z)))
bmesh.ops.scale(bm,verts=bm.verts,vec=(s,s,s))
bm.to_mesh(me); bm.free()
body.name='Zeek_Body'; me.name='Zeek_Body'
bpy.context.view_layer.objects.active=body; body.select_set(True)
n0=sum(len(p.vertices)-2 for p in me.polygons)
d=body.modifiers.new('dec','DECIMATE'); d.ratio=28500/n0; d.use_collapse_triangulate=True
bpy.ops.object.modifier_apply(modifier='dec')
bm=bmesh.new(); bm.from_mesh(me)
print('PREP tris',len(bm.faces),'boundary',sum(e.is_boundary for e in bm.edges),'nonman',sum((not e.is_manifold) for e in bm.edges))
bm.free()
bpy.ops.object.shade_smooth()
img=[i for i in bpy.data.images][0]; img.name='Zeek_Body_BaseColor'; img.filepath=glob.glob('/workspace/gym-app/3d/tex/zeek_body_basecolor.*')[0]; img.source='FILE'; img.reload(); img.pack()
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v2work/01_body.blend')

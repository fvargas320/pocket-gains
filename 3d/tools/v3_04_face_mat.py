import bpy, bmesh, numpy as np, sys
sys.path.insert(0,'/workspace/gym-app/3d/tools')
from v3_common import *
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v3work/03_face.blend')
body=bpy.data.objects['Zeek_Body']; rig=bpy.data.objects['Zeek_Rig']; me=body.data
old=me.materials[0]
build_body_material_v3(body)
if old.users==0: bpy.data.materials.remove(old)
for i in list(bpy.data.images):
    if i.users==0: bpy.data.images.remove(i)
# ---- face decal mesh
n=len(me.vertices)
co=np.zeros(n*3); me.vertices.foreach_get('co',co); co=co.reshape(n,3)
nr=np.zeros(n*3); me.vertices.foreach_get('normal',nr); nr=nr.reshape(n,3)
hi=body.vertex_groups[P+'Head'].index
hw=np.zeros(n)
for v in me.vertices:
    for g in v.groups:
        if g.group==hi: hw[v.index]=g.weight
u=co[:,0]/0.24+0.5; vv=(co[:,2]-0.77)/0.24+0.5
HC=np.array([0.001,0.0066,0.7641]); dh=np.linalg.norm(co-HC,axis=1)
keep=(dh<0.13)&(co[:,2]>0.67)&(nr[:,1]<-0.15)&(u>0.03)&(u<0.97)&(vv>0.03)&(vv<0.97)&(co[:,1]<0)
oa=me.attributes.new('orig','INT','POINT'); oa.data.foreach_set('value',np.arange(n))
bm=bmesh.new(); bm.from_mesh(me)
me.attributes.remove(me.attributes['orig'])
for k in list(bm.verts.layers.shape.keys()): pass
bm.verts.ensure_lookup_table()
kill=[f for f in bm.faces if not all(keep[v.index] for v in f.verts)]
bmesh.ops.delete(bm,geom=kill,context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
for v in bm.verts: v.co=v.co+v.normal*0.0045
dm=bpy.data.meshes.new('Zeek_FaceDecal'); bm.to_mesh(dm); bm.free()
if dm.shape_keys: pass
dm.materials.clear()
uvl=dm.uv_layers[0] if dm.uv_layers else dm.uv_layers.new()
while len(dm.uv_layers)>1: dm.uv_layers.remove(dm.uv_layers[1])
for p in dm.polygons:
    p.use_smooth=True
    for li in p.loop_indices:
        c=dm.vertices[dm.loops[li].vertex_index].co
        uvl.data[li].uv=(c.x/0.24+0.5,(c.z-0.77)/0.24+0.5)
for a in [a.name for a in dm.color_attributes]:
    try: dm.color_attributes.remove(dm.color_attributes[a])
    except Exception as e: print('keep attr',a)
print('decal verts',len(dm.vertices))
for k,label in (('smirk','Smirk'),('grin','Grin'),('grit','Grit'),('tired','Tired')):
    m2=dm.copy(); m2.name=f'Zeek_Face_{label}'
    o=bpy.data.objects.new(f'Zeek_Face_{label}',m2); bpy.context.scene.collection.objects.link(o)
    if m2.shape_keys:
        o.shape_key_clear()
    m2.materials.append(decal_material(f'Zeek_Face_{label}',f'zeek_v3_face_{k}.png'))
    oi=np.zeros(len(m2.vertices),dtype=int); m2.attributes['orig'].data.foreach_get('value',oi)
    for vi,bi in enumerate(oi):
        for g in me.vertices[bi].groups:
            nm=body.vertex_groups[g.group].name
            vg=o.vertex_groups.get(nm) or o.vertex_groups.new(name=nm)
            vg.add([vi],g.weight,'REPLACE')
    m2.attributes.remove(m2.attributes['orig'])
    o.parent=rig; o.matrix_parent_inverse=rig.matrix_world.inverted()
    md=o.modifiers.new('Armature','ARMATURE'); md.object=rig
    o.hide_render=o.hide_viewport=(label!='Smirk')
    o['expression']=k
bpy.data.meshes.remove(dm)
add_outline(body,0.0035)
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v3work/04_facemat.blend')
print('saved')

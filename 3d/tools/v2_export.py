import bpy
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/06_final.blend')
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/zeek_v2.blend', copy=True)
O=bpy.data.objects
def find_img(mat):
    for n in mat.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image and 'Leg' not in n.name and 'leg' not in n.image.name.lower(): return n.image
for o in list(O):
    if o.type!='MESH': continue
    for m in list(o.modifiers):
        if m.type=='SOLIDIFY': o.modifiers.remove(m)
    newmats=[]
    for ms in o.material_slots:
        m=ms.material
        if m is None or m.name.startswith('Outline'): continue
        img=find_img(m)
        pm=bpy.data.materials.new(m.name+'_PBR'); pm.use_nodes=True; nt=pm.node_tree; bsdf=nt.nodes['Principled BSDF']
        bsdf.inputs['Roughness'].default_value=0.75
        if img:
            t=nt.nodes.new('ShaderNodeTexImage'); t.image=img; nt.links.new(t.outputs['Color'],bsdf.inputs['Base Color'])
        else:
            bsdf.inputs['Base Color'].default_value=(1,0.72,0.12,1); bsdf.inputs['Metallic'].default_value=1.0; bsdf.inputs['Roughness'].default_value=0.3
        newmats.append(pm)
    o.data.materials.clear()
    for pm in newmats: o.data.materials.append(pm)
    for p in o.data.polygons: p.material_index=0
    if o.data.color_attributes.get('leg_def_mask'): pass
O['Zeek_Rig'].hide_render=False; O['Zeek_Rig'].hide_set(False)
for ob in O: ob.hide_set(False); ob.hide_viewport=False
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath='/workspace/gym-app/3d/zeek_v2_rigged.glb', export_format='GLB', export_apply=False, export_skins=True, export_morph=True, export_morph_normal=False, export_animations=False, use_selection=False, export_extras=True, export_attributes=True)
print('EXPORTED')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/workspace/gym-app/3d/zeek_v2_rigged.glb')
for o in bpy.data.objects:
    if o.type=='MESH':
        sk=[k.name for k in o.data.shape_keys.key_blocks][1:] if o.data.shape_keys else []
        arm=[m.object.name for m in o.modifiers if m.type=='ARMATURE']
        print('VERIFY',o.name,'tris',sum(len(p.vertices)-2 for p in o.data.polygons),'mats',[m.name for m in o.data.materials],'arm',arm,'keys',sk)
    elif o.type=='ARMATURE': print('VERIFY ARM',o.name,len(o.data.bones))

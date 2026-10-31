import bpy
D3='/workspace/gym-app/3d'
bpy.ops.wm.open_mainfile(filepath=f'{D3}/v3work/08_render.blend')
bpy.ops.wm.save_as_mainfile(filepath=f'{D3}/zeek_v3.blend', copy=True)
O=bpy.data.objects
for n in ('Floor','ShotCam','CamPivot','chk','C','Cam'):
    if n in O: O.remove(O[n],do_unlink=True)
for o in list(O):
    if o.type in ('CAMERA','LIGHT'): O.remove(o,do_unlink=True)
def pick_img(m):
    imgs=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    for i in imgs:
        if 'basecolor' in i.name.lower(): return i
    imgs=[i for i in imgs if not any(k in i.name.lower() for k in ('detail','normal','leg'))]
    return imgs[0] if imgs else None
def rgb_of(m):
    for n in m.node_tree.nodes:
        if n.type=='RGB': return tuple(n.outputs[0].default_value)
    return None
cache={}
def pbr(m):
    if m.name in cache: return cache[m.name]
    pm=bpy.data.materials.new(m.name+'_PBR'); pm.use_nodes=True; nt=pm.node_tree; b=nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value=0.75; n=m.name
    img=pick_img(m)
    if n.startswith('Aura_Shell') or n.startswith('Aura_Flame'):
        b.inputs['Base Color'].default_value=(0.15,1,0.85,1); b.inputs['Emission Color'].default_value=(0.15,1,0.85,1); b.inputs['Emission Strength'].default_value=1.5
        b.inputs['Alpha'].default_value=0.35; pm.surface_render_method='BLENDED'
    elif 'Gold' in n:
        b.inputs['Base Color'].default_value=(1,0.72,0.12,1); b.inputs['Metallic'].default_value=1; b.inputs['Roughness'].default_value=0.3
    elif 'Lens' in n:
        b.inputs['Base Color'].default_value=(0.12,0.30,0.45,1); b.inputs['Metallic'].default_value=0.4; b.inputs['Roughness'].default_value=0.1
    elif img:
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=img; nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
        if n.startswith('Zeek_Face') or 'Decal' in n or 'Face' in n:
            nt.links.new(t.outputs['Alpha'],b.inputs['Alpha']); pm.surface_render_method='BLENDED'
    else:
        c=rgb_of(m) or (0.5,0.5,0.5,1); b.inputs['Base Color'].default_value=c
        if 'Steel' in n: b.inputs['Metallic'].default_value=0.9; b.inputs['Roughness'].default_value=0.35
        if 'Frame' in n and 'Shades' in n: b.inputs['Roughness'].default_value=0.3
    cache[m.name]=pm; return pm
for o in list(O):
    if o.type!='MESH': continue
    for md in list(o.modifiers):
        if md.type=='SOLIDIFY': o.modifiers.remove(md)
    if o.animation_data: o.animation_data_clear()
    slots=[ms.material for ms in o.material_slots]
    keep=[]; remap={}
    for i,m in enumerate(slots):
        if m is None or m.name.startswith('Outline'): continue
        remap[i]=len(keep); keep.append(pbr(m))
    idx=[remap.get(p.material_index,0) for p in o.data.polygons]
    o.data.materials.clear()
    for pm in keep: o.data.materials.append(pm)
    for p,i in zip(o.data.polygons,idx): p.material_index=i
    o['visible_default']=not o.hide_render
for o in O: o.hide_set(False); o.hide_viewport=False; o.hide_render=False
rig=O['Zeek_Rig']; rig.animation_data_create(); rig.animation_data.action=None
for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0)
# barbell: keep static (baked bar actions remain in .blend); export rig actions only
bar=O.get('Prop_Barbell')
if bar and bar.animation_data: bar.animation_data_clear()
for a in list(bpy.data.actions):
    if not a.name.startswith('Zeek_'): bpy.data.actions.remove(a)
# push every rig action to NLA so exporter sees them
for a in bpy.data.actions:
    tr=rig.animation_data.nla_tracks.new(); tr.name=a.name; st=tr.strips.new(a.name,1,a); tr.mute=True
bpy.ops.export_scene.gltf(filepath=f'{D3}/zeek_v3_rigged.glb', export_format='GLB', export_apply=False, export_skins=True, export_morph=True,
    export_morph_normal=False, export_animations=True, export_animation_mode='NLA_TRACKS', export_extras=True, use_selection=False,
    export_force_sampling=True, export_frame_step=1, export_optimize_animation_size=True)
print('EXPORTED')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'{D3}/zeek_v3_rigged.glb')
for o in bpy.data.objects:
    if o.type=='MESH':
        sk=len(o.data.shape_keys.key_blocks)-1 if o.data.shape_keys else 0
        arm=[m.object.name for m in o.modifiers if m.type=='ARMATURE']
        print('VERIFY',o.name,'tris',sum(len(p.vertices)-2 for p in o.data.polygons),'mats',[m.name for m in o.data.materials],'arm',arm,'keys',sk,'parent',o.parent.name if o.parent else None, o.parent_bone)
    elif o.type=='ARMATURE': print('VERIFY ARM',o.name,len(o.data.bones))
print('ANIMS',sorted(a.name for a in bpy.data.actions))

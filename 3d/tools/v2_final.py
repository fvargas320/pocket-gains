import bpy, sys, os, math
sys.path.insert(0,'/workspace/gym-app/3d/tools'); from v2_common import *
OUT='/workspace/gym-app/3d/previews/v2'; os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/05_gear.blend')
sc=setup_scene(1024,24)
O=bpy.data.objects; body,tank,bean,chain,rig=O['Zeek_Body'],O['Zeek_Tank'],O['Zeek_Beanie'],O['Zeek_GoldChain'],O['Zeek_Rig']
for o in (tank,chain):
    vg=o.vertex_groups.get(P+'Head')
    if vg: o.vertex_groups.remove(vg)
build_body_material(body); add_outline(body,0.0035)
def texcol(nt): return [n for n in nt.nodes if n.type=='TEX_IMAGE'][0].outputs[0]
for o in (tank,bean):
    m=o.data.materials[0]; nt=m.node_tree
    for n in list(nt.nodes):
        if n.type=='BSDF_PRINCIPLED': nt.nodes.remove(n)
    toon_nodes(m,texcol,shadow=0.62); add_outline(o,0.0025,quality=False)
    th=o.modifiers.get('Thickness'); th.use_even_offset=False; th.use_quality_normals=False
gm=chain.data.materials[0]; nt=gm.node_tree
for n in list(nt.nodes):
    if n.type=='BSDF_PRINCIPLED': nt.nodes.remove(n)
def goldcol(nt):
    c=nt.nodes.new('ShaderNodeRGB'); c.outputs[0].default_value=(1.0,0.72,0.12,1); return c.outputs[0]
_,d=toon_nodes(gm,goldcol,shadow=0.5)
r=nt.nodes['ToonRamp'].color_ramp; r.elements[-1].position=0.6; r.elements[-1].color=(1.6,1.5,1.2,1)
add_outline(chain,0.0008)
# modifier order: Armature first
for o in (body,tank,bean,chain):
    for m in list(o.modifiers):
        if m.type=='ARMATURE':
            bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0)
    print('MODS',o.name,[m.name for m in o.modifiers])
rig.hide_render=True; rig.show_in_front=True
sc.render.film_transparent=False
kb=body.data.shape_keys.key_blocks
UP=['arms_biceps','arms_triceps','shoulders','chest','back_lats','abs_core']; LG=['legs_quads','legs_glutes','legs_calves']
def setkeys(vals):
    for o in (body,tank,chain):
        if not o.data.shape_keys: continue
        for k in o.data.shape_keys.key_blocks[1:]: k.value=vals.get(k.name,0.0)
def gear(t=False,b=False,c=False):
    tank.hide_render=not t; bean.hide_render=not b; chain.hide_render=not c
    tank.hide_viewport=not t; bean.hide_viewport=not b; chain.hide_viewport=not c
S={
 'a_base':({},(0,0,0)),
 'b_default_outfit':({},(1,1,0)),
 'c_chest_day':({'chest':1,'shoulders':0.85,'arms_biceps':0.85,'arms_triceps':0.75,'back_lats':0.35,'abs_core':0.3},(0,1,0)),
 'd_leg_day':({'legs_quads':1,'legs_glutes':1,'legs_calves':1,'chest':0.4,'shoulders':0.4,'arms_biceps':0.4,'arms_triceps':0.4,'back_lats':0.4,'abs_core':0.5},(0,1,0)),
 'e_maxed_chain':({k:1 for k in UP+LG},(0,1,1)),
 'e2_maxed_full_outfit':({k:1 for k in UP+LG},(1,1,1)),
 'x_noodle':({'noodle':1},(1,1,0)),
}
only=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for name,(vals,g) in S.items():
    if only and name not in only: continue
    setkeys(vals); gear(*g)
    camera(28,1.12,0.5); sc.render.filepath=f'{OUT}/zeek_v2_{name}.png'; bpy.ops.render.render(write_still=True)
    if name in ('c_chest_day','d_leg_day'):
        camera(28,0.40,0.19,name='CamLeg'); sc.render.filepath=f'{OUT}/zeek_v2_{name}_legs.png'; bpy.ops.render.render(write_still=True)
        sc.camera=O['Cam']
    if name in ('e2_maxed_full_outfit','b_default_outfit'):
        camera(100,1.12,0.5); sc.render.filepath=f'{OUT}/zeek_v2_{name}_side.png'; bpy.ops.render.render(write_still=True)
setkeys({}); gear(1,1,0)
for o in (tank,bean,chain): o.hide_viewport=False
if not only:
    bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v2work/06_final.blend')
print('DONE')

import bpy
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/03_shapes.blend')
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=4
body=bpy.data.objects['Zeek_Body']
for o in bpy.context.view_layer.objects: o.select_set(False)
body.select_set(True); bpy.context.view_layer.objects.active=body
R=2048
def img(name,non_color):
    i=bpy.data.images.get(name) or bpy.data.images.new(name,R,R,alpha=False,float_buffer=False)
    if non_color: i.colorspace_settings.name='Non-Color'
    return i
m=bpy.data.materials.new('BakeLegDef'); m.use_nodes=True; nt=m.node_tree; N=nt.nodes; L=nt.links
for n in list(N):
    if n.type!='OUTPUT_MATERIAL': N.remove(n)
out=N['Material Output']
attr=N.new('ShaderNodeAttribute'); attr.attribute_name='leg_def_mask'
tc=N.new('ShaderNodeTexCoord')
def stretched(sx,sy,sz,dist,ns):
    mp=N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(sx,sy,sz); L.new(tc.outputs['Object'],mp.inputs[0])
    nz=N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=ns; L.new(mp.outputs[0],nz.inputs[0])
    mix=N.new('ShaderNodeMix'); mix.data_type='VECTOR'; mix.inputs[0].default_value=dist
    L.new(mp.outputs[0],mix.inputs[4]); L.new(nz.outputs['Color'],mix.inputs[5]); return mix.outputs[1]
def edge_line(vec,scale,width,soft):
    v=N.new('ShaderNodeTexVoronoi'); v.feature='DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value=scale; L.new(vec,v.inputs['Vector'])
    r=N.new('ShaderNodeMapRange'); r.inputs[1].default_value=width; r.inputs[2].default_value=width+soft; r.inputs[3].default_value=1; r.inputs[4].default_value=0
    L.new(v.outputs['Distance'],r.inputs[0]); return r.outputs[0]
veins=edge_line(stretched(1,1,0.33,0.25,6),38,0.012,0.03)
# break up veins so they are sparse branches
br=N.new('ShaderNodeTexNoise'); br.inputs['Scale'].default_value=55; L.new(tc.outputs['Object'],br.inputs[0])
brr=N.new('ShaderNodeMapRange'); brr.inputs[1].default_value=0.48; brr.inputs[2].default_value=0.6; L.new(br.outputs[0],brr.inputs[0])
vm=N.new('ShaderNodeMath'); vm.operation='MULTIPLY'; L.new(veins,vm.inputs[0]); L.new(brr.outputs[0],vm.inputs[1])
grooves=edge_line(stretched(1,1,0.45,0.12,3),13,0.0,0.06)
def mul(a,b):
    n=N.new('ShaderNodeMath'); n.operation='MULTIPLY'; L.new(a,n.inputs[0]); L.new(b,n.inputs[1]); return n.outputs[0]
vM=mul(vm.outputs[0],attr.outputs['Fac']); gM=mul(grooves,attr.outputs['Fac'])
comb=N.new('ShaderNodeCombineColor'); L.new(vM,comb.inputs[0]); L.new(gM,comb.inputs[1]); L.new(attr.outputs['Fac'],comb.inputs[2])
em=N.new('ShaderNodeEmission'); L.new(comb.outputs[0],em.inputs[0])
# height for normal bake: veins raised, grooves sunk
h=N.new('ShaderNodeMath'); h.operation='SUBTRACT'; L.new(vM,h.inputs[0]); hg=N.new('ShaderNodeMath'); hg.operation='MULTIPLY'; hg.inputs[1].default_value=0.9; L.new(gM,hg.inputs[0]); L.new(hg.outputs[0],h.inputs[1])
bump=N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=1.0; bump.inputs['Distance'].default_value=0.0015; L.new(h.outputs[0],bump.inputs['Height'])
pb=N.new('ShaderNodeBsdfPrincipled'); L.new(bump.outputs[0],pb.inputs['Normal'])
ti=N.new('ShaderNodeTexImage'); N.active=ti
orig=list(body.data.materials); body.data.materials.clear(); body.data.materials.append(m)
# emission bake
iD=img('zeek_v2_leg_detail',True); ti.image=iD; L.new(em.outputs[0],out.inputs[0])
sc.cycles.samples=2; sc.render.bake.margin=12
bpy.ops.object.bake(type='EMIT',margin=12)
iD.filepath_raw='/workspace/gym-app/3d/tex/zeek_v2_leg_detail.png'; iD.file_format='PNG'; iD.save()
iN=img('zeek_v2_leg_normal',True); ti.image=iN; L.new(pb.outputs[0],out.inputs[0]); N.active=ti
sc.cycles.samples=4
bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',margin=12)
iN.filepath_raw='/workspace/gym-app/3d/tex/zeek_v2_leg_normal.png'; iN.file_format='PNG'; iN.save()
body.data.materials.clear()
for mm in orig: body.data.materials.append(mm)
bpy.data.materials.remove(m)
for i in (iD,iN): i.source='FILE'; i.filepath=i.filepath_raw; i.reload(); i.pack()
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v2work/04_legdef.blend')
print('BAKED')

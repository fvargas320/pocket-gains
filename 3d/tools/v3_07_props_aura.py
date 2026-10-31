import bpy, bmesh, sys, os, json, math
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(__file__))
from v2_common import toon_nodes, add_outline
D3='/workspace/gym-app/3d'
bpy.ops.wm.open_mainfile(filepath=f'{D3}/v3work/06_anim.blend')
rig=bpy.data.objects['Zeek_Rig']; body=bpy.data.objects['Zeek_Body']
FIST=json.loads(rig['fist_pose'])
col=bpy.context.scene.collection
def tcol(name,rgb,shadow=0.6):
    m=bpy.data.materials.new(name); m.use_nodes=True
    toon_nodes(m,lambda nt:(rgb[0],rgb[1],rgb[2],1),shadow=shadow) if False else None
    nt=m.node_tree; rgbn=nt.nodes.new('ShaderNodeRGB'); rgbn.outputs[0].default_value=(*rgb,1)
    toon_nodes(m,lambda nt:rgbn.outputs[0],shadow=shadow); return m
def cyl(bm,p0,p1,r,seg,mat):
    ax=(p1-p0); L=ax.length; ax.normalize()
    q=Vector((0,0,1)).rotation_difference(ax)
    res=bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r,radius2=r,depth=L)
    bmesh.ops.transform(bm,matrix=Matrix.Translation((p0+p1)/2)@q.to_matrix().to_4x4(),verts=res['verts'])
    for f in {f for v in res['verts'] for f in v.link_faces}: f.material_index=mat
def mkobj(name,build,mats):
    me=bpy.data.meshes.new(name); bm=bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    for p in me.polygons: p.use_smooth=False
    o=bpy.data.objects.new(name,me); col.objects.link(o); o['prop']=True; return o
M_steel=tcol('Prop_Steel',(0.72,0.75,0.78),0.55); M_rub=tcol('Prop_Rubber',(0.10,0.11,0.13),0.6)
M_teal=tcol('Prop_PlateTeal',(0.05,0.70,0.66),0.6); M_purp=tcol('Prop_PlatePurple',(0.45,0.20,0.75),0.6)
M_pad=tcol('Prop_BenchPad',(0.13,0.13,0.16),0.6); M_frame=tcol('Prop_BenchFrame',(0.80,0.82,0.85),0.6)
# --- dumbbells (local X = grip axis) ---
def db(bm):
    cyl(bm,Vector((-0.024,0,0)),Vector((0.024,0,0)),0.0065,12,0)
    for s in (-1,1):
        cyl(bm,Vector((s*0.024,0,0)),Vector((s*0.048,0,0)),0.026,6,1)
    bmesh.ops.rotate(bm,verts=bm.verts,cent=(0,0,0),matrix=Matrix.Rotation(0,3,'X'))
rig.animation_data.action=None
for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0)
bpy.context.view_layer.update()
DBS={}
for S in ('Left','Right'):
    o=mkobj(f'Prop_Dumbbell_{S}',db,[M_steel,M_rub]); add_outline(o,0.002,quality=False)
    B=rig.data.bones
    a=(B[f'mixamorig:{S}HandIndex1'].head_local-B[f'mixamorig:{S}HandLittle1'].head_local).normalized()
    pn=Vector(rig[f'palm_normal_{S}']); z=pn-a*pn.dot(a); z.normalize(); y=z.cross(a)
    R=Matrix((a,y,z)).transposed().to_4x4(); R.translation=Vector(rig[f'fist_center_{S}'])
    o.parent=rig; o.parent_type='BONE'; o.parent_bone=f'mixamorig:{S}Hand'
    bpy.context.view_layer.update(); o.matrix_world=R; o.hide_render=o.hide_viewport=True; DBS[S]=o
# --- barbell (world-baked per action) ---
def bb(bm):
    cyl(bm,Vector((-0.33,0,0)),Vector((0.33,0,0)),0.0048,10,0)
    for s in (-1,1):
        cyl(bm,Vector((s*0.17,0,0)),Vector((s*0.19,0,0)),0.012,10,0)
        cyl(bm,Vector((s*0.19,0,0)),Vector((s*0.215,0,0)),0.082,24,2)
        cyl(bm,Vector((s*0.215,0,0)),Vector((s*0.235,0,0)),0.066,24,3)
        cyl(bm,Vector((s*0.235,0,0)),Vector((s*0.25,0,0)),0.012,10,0)
BAR=mkobj('Prop_Barbell',bb,[M_steel,M_rub,M_teal,M_purp]); add_outline(BAR,0.002,quality=False); BAR.hide_render=BAR.hide_viewport=True
def fistw(S):
    pb=rig.pose.bones[f'mixamorig:{S}Hand']; b=pb.bone
    return rig.matrix_world@pb.matrix@(b.matrix_local.inverted()@Vector(rig[f'fist_center_{S}']))
def bake_bar(act):
    rig.animation_data.action=act; n=act['frames']; sc=bpy.context.scene
    ba=bpy.data.actions.new('Bar_'+act.name); ba.use_fake_user=True
    BAR.animation_data_create(); BAR.animation_data.action=ba; BAR.rotation_mode='QUATERNION'; prev=None
    for f in range(1,n+1):
        sc.frame_set(f); L=fistw('Left'); Rr=fistw('Right')
        x=(L-Rr); x.z=0; x.normalize(); 
        fw=rig.matrix_world.to_3x3()@(rig.pose.bones['mixamorig:Spine2'].matrix.to_3x3()@Vector((0,0,1)))
        z=fw-x*fw.dot(x); z.normalize(); y=z.cross(x)
        q=Matrix((x,y,z)).transposed().to_quaternion()
        if prev: q.make_compatible(prev)
        prev=q; BAR.location=(L+Rr)/2; BAR.rotation_quaternion=q
        BAR.keyframe_insert('location',frame=f); BAR.keyframe_insert('rotation_quaternion',frame=f)
    act['bar_action']=ba.name
    BAR.animation_data.action=None
# ---------- bench press (hand keyed) ----------
order=[]
def walk(b):
    order.append(b.name); [walk(c) for c in b.children]
walk(rig.data.bones['mixamorig:Hips'])
TREST={b.name:b.matrix_local.copy() for b in rig.data.bones}
def sub(bn):
    out=[]; st=[rig.data.bones[bn]]
    while st:
        b=st.pop(); out.append(b.name); st+=list(b.children)
    return out
Qb=Quaternion((1,0,0),math.radians(-90))
HIPZ=0.262
def bench_pose(t):  # t 0=top(locked out) 1=bottom
    def lerp(a,b): return a.lerp(b,t)
    D={}
    D['mixamorig:Neck']=Vector((0,0.85,0.5)); D['mixamorig:Head']=Vector((0,0.8,0.6))
    for S,s in (('Left',1),('Right',-1)):
        D[f'mixamorig:{S}UpLeg']=Vector((s*0.38,-0.9,-0.22)); D[f'mixamorig:{S}Leg']=Vector((s*0.12,-0.12,-1))
        D[f'mixamorig:{S}Foot']=Vector((s*0.05,-1,-0.35)); D[f'mixamorig:{S}ToeBase']=Vector((0,-1,0))
        D[f'mixamorig:{S}Arm']=lerp(Vector((s*0.30,-0.45,1)),Vector((s*0.85,-0.55,-0.05)))
        D[f'mixamorig:{S}ForeArm']=lerp(Vector((s*0.04,-0.2,1)),Vector((s*0.06,-0.25,1)))
        D[f'mixamorig:{S}Hand']=Vector((s*0.05,0.25,1))
    W={}
    for n in order:
        rr=TREST[n].to_quaternion(); base=(Qb@rr)
        if n in D:
            rd=(base@Vector((0,1,0))); W[n]=(rd.rotation_difference(D[n].normalized())@base).normalized()
        else:
            p=rig.data.bones[n].parent
            W[n]=base if p is None else (W[p.name]@TREST[p.name].to_quaternion().inverted()@rr).normalized()
    return W
def key_world(W,hp,fi,fist,prevq):
    PM={}
    for n in order:
        b=rig.data.bones[n]; pb=rig.pose.bones[n]
        if b.parent is None: M=Matrix.Translation(hp)@W[n].to_matrix().to_4x4(); basis=TREST[n].inverted()@M
        else:
            P=PM[b.parent.name]; rel=TREST[b.parent.name].inverted()@TREST[n]
            M=Matrix.Translation((P@rel).translation)@W[n].to_matrix().to_4x4(); basis=rel.inverted()@P.inverted()@M
        q=basis.to_quaternion()
        if n in FIST and fist>0:
            q=Quaternion().slerp(Quaternion(FIST[n]),fist); M=PM[b.parent.name]@(TREST[b.parent.name].inverted()@TREST[n])@q.to_matrix().to_4x4()
        PM[n]=M
        if n in prevq: q.make_compatible(prevq[n])
        prevq[n]=q; pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=q; pb.keyframe_insert('rotation_quaternion',frame=fi,group=n)
        if b.parent is None: pb.location=basis.translation; pb.keyframe_insert('location',frame=fi,group=n)
act=bpy.data.actions.new('Zeek_BenchPress'); act.use_fake_user=True; rig.animation_data.action=act
REP=36; NR=3; prevq={}
for fi in range(1,REP*NR+1):
    ph=((fi-1)%REP)/REP
    t=0.5-0.5*math.cos(2*math.pi*ph)   # top->bottom->top
    t=t**0.8
    hp=Vector((0,0,HIPZ+0.004*t))
    key_world(bench_pose(t),hp,fi,1.0,prevq)
act['frames']=REP*NR; act['source']='Hand-keyed (procedural) in Blender'; act['fist']=1.0
# bench
def bench(bm):
    bmesh.ops.create_cube(bm,size=1.0)
    bmesh.ops.scale(bm,vec=(0.15,0.62,0.045),verts=bm.verts); bmesh.ops.translate(bm,vec=(0,0.16,HIPZ-0.075),verts=bm.verts)
    for y in (-0.08,0.40):
        r=bmesh.ops.create_cube(bm,size=1.0); bmesh.ops.scale(bm,vec=(0.05,0.05,HIPZ-0.1),verts=r['verts'])
        bmesh.ops.translate(bm,vec=(0,y,(HIPZ-0.1)/2),verts=r['verts'])
        for f in {f for v in r['verts'] for f in v.link_faces}: f.material_index=1
        r=bmesh.ops.create_cube(bm,size=1.0); bmesh.ops.scale(bm,vec=(0.26,0.06,0.02),verts=r['verts'])
        bmesh.ops.translate(bm,vec=(0,y,0.01),verts=r['verts'])
        for f in {f for v in r['verts'] for f in v.link_faces}: f.material_index=1
BENCH=mkobj('Prop_Bench',bench,[M_pad,M_frame]); add_outline(BENCH,0.0025,quality=False); BENCH.hide_render=BENCH.hide_viewport=True
for a in ('Zeek_Lifting','Zeek_BenchPress'): bake_bar(bpy.data.actions[a])
PROPS={'Zeek_BicepCurl':['Prop_Dumbbell_Left','Prop_Dumbbell_Right'],'Zeek_Lifting':['Prop_Barbell'],'Zeek_BenchPress':['Prop_Barbell','Prop_Bench']}
for a,p in PROPS.items(): bpy.data.actions[a]['props']=','.join(p)
# ---------- aura ----------
TIERS={'Teal':((0.15,1.0,0.85),(0.75,1.0,0.95)),'Gold':((1.0,0.62,0.08),(1.0,0.93,0.55)),'Purple':((0.62,0.25,1.0),(0.92,0.75,1.0))}
def drv_time(sock,speed):
    d=sock.driver_add('default_value').driver; d.expression=f'frame*{speed}'
def aura_shell_mat(t,c1,c2):
    m=bpy.data.materials.new(f'Aura_Shell_{t}'); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    o=nt.nodes.new('ShaderNodeOutputMaterial'); gm=nt.nodes.new('ShaderNodeNewGeometry')
    nz=nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions='4D'; nz.inputs['Scale'].default_value=7; drv_time(nz.inputs['W'],0.06)
    st=nt.nodes.new('ShaderNodeMath'); st.operation='GREATER_THAN'; st.inputs[1].default_value=0.5; nt.links.new(nz.outputs[0],st.inputs[0])
    mx=nt.nodes.new('ShaderNodeMix'); mx.data_type='RGBA'; mx.inputs[6].default_value=(*c1,1); mx.inputs[7].default_value=(*c2,1); nt.links.new(st.outputs[0],mx.inputs[0])
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs[1].default_value=1.4; nt.links.new(mx.outputs[2],em.inputs[0])
    tr=nt.nodes.new('ShaderNodeBsdfTransparent'); ms=nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(gm.outputs['Backfacing'],ms.inputs[0]); nt.links.new(tr.outputs[0],ms.inputs[1]); nt.links.new(em.outputs[0],ms.inputs[2]); nt.links.new(ms.outputs[0],o.inputs[0])
    m.surface_render_method='BLENDED'; m.use_backface_culling=False; return m
def flame_mat(t,c1,c2):
    m=bpy.data.materials.new(f'Aura_Flame_{t}'); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    o=nt.nodes.new('ShaderNodeOutputMaterial'); tc=nt.nodes.new('ShaderNodeTexCoord'); sep=nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['UV'],sep.inputs[0])
    mp=nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(14,2.2,1); nt.links.new(tc.outputs['UV'],mp.inputs[0]);     d=mp.inputs['Location'].driver_add('default_value',1).driver; d.expression='-frame*0.045'
    nz=nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=1.6; nz.inputs['Detail'].default_value=3; nt.links.new(mp.outputs[0],nz.inputs[0])
    # f = noise*1.25 - v*1.15 + 0.1   (v=0 bottom)
    a1=nt.nodes.new('ShaderNodeMath'); a1.operation='MULTIPLY_ADD'; a1.inputs[1].default_value=1.25; a1.inputs[2].default_value=0.12; nt.links.new(nz.outputs[0],a1.inputs[0])
    vm=nt.nodes.new('ShaderNodeMath'); vm.operation='MULTIPLY'; vm.inputs[1].default_value=-1.15; nt.links.new(sep.outputs[1],vm.inputs[0])
    f=nt.nodes.new('ShaderNodeMath'); f.operation='ADD'; nt.links.new(a1.outputs[0],f.inputs[0]); nt.links.new(vm.outputs[0],f.inputs[1])
    g1=nt.nodes.new('ShaderNodeMath'); g1.operation='GREATER_THAN'; g1.inputs[1].default_value=0.45; nt.links.new(f.outputs[0],g1.inputs[0])
    g2=nt.nodes.new('ShaderNodeMath'); g2.operation='GREATER_THAN'; g2.inputs[1].default_value=0.72; nt.links.new(f.outputs[0],g2.inputs[0])
    gm=nt.nodes.new('ShaderNodeNewGeometry'); bf=nt.nodes.new('ShaderNodeMath'); bf.operation='MULTIPLY'; nt.links.new(g1.outputs[0],bf.inputs[0]); nt.links.new(gm.outputs['Backfacing'],bf.inputs[1])
    mx=nt.nodes.new('ShaderNodeMix'); mx.data_type='RGBA'; mx.inputs[6].default_value=(*c1,1); mx.inputs[7].default_value=(*c2,1); nt.links.new(g2.outputs[0],mx.inputs[0])
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs[1].default_value=1.5; nt.links.new(mx.outputs[2],em.inputs[0])
    tr=nt.nodes.new('ShaderNodeBsdfTransparent'); ms=nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(bf.outputs[0],ms.inputs[0]); nt.links.new(tr.outputs[0],ms.inputs[1]); nt.links.new(em.outputs[0],ms.inputs[2]); nt.links.new(ms.outputs[0],o.inputs[0])
    m.surface_render_method='BLENDED'; m.use_backface_culling=False; return m
for t,(c1,c2) in TIERS.items():
    for mm in (aura_shell_mat(t,c1,c2),flame_mat(t,c1,c2)): mm.use_fake_user=True
# shell: body copy (shares mesh) + displace
sh=body.copy(); sh.data=body.data; sh.name='Zeek_Aura_Shell'; col.objects.link(sh)
for md in list(sh.modifiers):
    if md.type!='ARMATURE': sh.modifiers.remove(md)
dp=sh.modifiers.new('Inflate','DISPLACE'); dp.strength=0.006; dp.mid_level=0
sh.data=body.data.copy(); sh.data.materials.clear(); sh.data.materials.append(bpy.data.materials['Aura_Shell_Teal'])
for p in sh.data.polygons: p.material_index=0
# flames: open cylinder around body, uv v=0 bottom, parented to hips location only
me=bpy.data.meshes.new('Zeek_Aura_Flames'); bm=bmesh.new(); NS=48; NV=8; R=0.30; H=1.05
uvl=bm.loops.layers.uv.new()
vs=[[bm.verts.new((R*(1+0.15*(j/NV))*math.cos(2*math.pi*i/NS),R*(1+0.15*(j/NV))*math.sin(2*math.pi*i/NS)*0.8,-0.02+H*j/NV)) for i in range(NS+1)] for j in range(NV+1)]
for j in range(NV):
    for i in range(NS):
        f=bm.faces.new((vs[j][i],vs[j][i+1],vs[j+1][i+1],vs[j+1][i]))
        for l,(a,b) in zip(f.loops,((i,j),(i+1,j),(i+1,j+1),(i,j+1))): l[uvl].uv=(a/NS,b/NV)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6); bm.to_mesh(me); bm.free()
fl=bpy.data.objects.new('Zeek_Aura_Flames',me); col.objects.link(fl); me.materials.append(bpy.data.materials['Aura_Flame_Teal'])
c=fl.constraints.new('COPY_LOCATION'); c.target=rig; c.subtarget='mixamorig:Hips'; c.use_z=False
for o in (sh,fl): o['aura']=True; o.hide_render=o.hide_viewport=True
rig['aura_tier']=0; rig['aura_tiers']='0 off, 1 Teal, 2 Gold, 3 Purple'
rig.animation_data.action=None
for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=f'{D3}/v3work/07_full.blend'); print('saved')

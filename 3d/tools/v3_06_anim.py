# Retarget Mixamo FBX clips (Y Bot, T-pose) onto Zeek_Rig (A-pose). World-delta method with rest-direction correction.
import bpy, sys, os, json, math, glob
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(__file__))
D3='/workspace/gym-app/3d'
bpy.ops.wm.open_mainfile(filepath=f'{D3}/v3work/05_gear.blend')
rig=bpy.data.objects['Zeek_Rig']; body=bpy.data.objects['Zeek_Body']
FIST=json.loads(rig['fist_pose'])
CLIPS={ # name: (fist factor, arm spread deg, max frames)
 'Bicep Curl':(1.0,14,None),'Air Squat':(0.6,10,None),'Push Up':(0.0,0,None),'Lifting':(1.0,6,None),
 'Jumping Jacks':(0.35,6,None),'Burpee':(0.2,0,None),'Bicycle Crunch':(0.6,0,None),
 'Mutant Flexing Muscles':(1.0,12,None),'Breathing Idle':(0.35,16,None),'Victory':(1.0,10,None),'Running Tired':(0.7,12,None)}
FLOOR_CLIPS={'Push Up','Burpee','Bicycle Crunch'}
HEADC=Vector((0.001,0.0066,0.7641)); HEADR=0.108
bones=[b for b in rig.data.bones]
order=[]  # parent-first
def walk(b):
    order.append(b.name); [walk(c) for c in b.children]
for b in bones:
    if b.parent is None: walk(b)
TREST={b.name:b.matrix_local.copy() for b in bones}
ARMCH={'Left':['mixamorig:LeftArm','mixamorig:LeftForeArm','mixamorig:LeftHand'],
       'Right':['mixamorig:RightArm','mixamorig:RightForeArm','mixamorig:RightHand']}
def sub(bn):  # all descendants incl self
    out=[]; st=[rig.data.bones[bn]]
    while st:
        b=st.pop(); out.append(b.name); st+=list(b.children)
    return out
def swing(a,b):
    a=a.normalized(); b=b.normalized()
    return a.rotation_difference(b)

def retarget(fn):
    name=os.path.splitext(os.path.basename(fn))[0]
    fist,spread,maxf=CLIPS[name]
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fn)
    new=[o for o in bpy.data.objects if o not in before]
    src=[o for o in new if o.type=='ARMATURE'][0]
    sact=src.animation_data.action; f0,f1=map(int,sact.frame_range)
    if maxf: f1=min(f1,f0+maxf-1)
    SW=src.matrix_world.copy()
    srest={b.name:(SW@b.matrix_local) for b in src.data.bones}
    def srot(m): return m.to_3x3().normalized().to_quaternion()
    common=[n for n in order if n in srest]
    C={}
    for n in common:
        ty=TREST[n].to_3x3().col[1]; sy=srest[n].to_3x3().normalized().col[1]
        C[n]=swing(ty,sy)
    shrest=srest['mixamorig:Hips'].translation
    k=TREST['mixamorig:Hips'].translation.z/shrest.z
    act=bpy.data.actions.new('Zeek_'+name.replace(' ','')); act.use_fake_user=True
    rig.animation_data_create(); rig.animation_data.action=act
    for pb in rig.pose.bones: pb.rotation_mode='QUATERNION'
    sc=bpy.context.scene
    frames=list(range(f0,f1+1)); prevq={}
    hipsZ=[]
    for fi,f in enumerate(frames):
        sc.frame_set(f)
        W={}  # target world rotations
        for n in common:
            sm=SW@src.pose.bones[n].matrix
            Dq=srot(sm)@srot(srest[n]).inverted()
            W[n]=(Dq@C[n]@srot(TREST[n])).normalized()
        # arm spread (down-pointing arms) + head avoidance (up-pointing arms)
        for S,ch in ARMCH.items():
            sh=TREST[ch[0]].translation
            def chainpos(Wr):
                p=sh.copy(); pts=[]
                for n in ch:
                    L=(rig.data.bones[n].tail_local-rig.data.bones[n].head_local).length
                    p=p+(Wr[n]@Vector((0,1,0)))*L; pts.append(p.copy())
                return pts
            d=W[ch[0]]@Vector((0,1,0))
            sgn=-1 if S=='Left' else 1
            a=math.radians(spread)*max(0.0,-d.z)
            Q=Quaternion((0,1,0),sgn*a)
            for _ in range(14):
                Wr={n:Q@W[n] for n in ch}
                pts=chainpos(Wr)
                bad=min(((p-HEADC).length for p in pts))<HEADR+0.028
                if not bad: break
                Q=Quaternion((0,1,0),-sgn*math.radians(5))@Q  # rotate outward (left arm toward +X)
            if Q.angle>1e-5:
                for n in sub(ch[0]):
                    if n in W: W[n]=(Q@W[n]).normalized()
        # chin-up when torso horizontal (big head vs floor)
        sp=W['mixamorig:Spine2']; hz=abs((sp@Vector((0,1,0))).z)
        hf=max(0.0,1.0-hz/0.7)
        if hf>0:
            Qn=Quaternion(sp@Vector((1,0,0)),-math.radians(34)*hf)
            for n in sub('mixamorig:Neck'):
                if n in W: W[n]=(Qn@W[n]).normalized()
        # hips position
        shp=(SW@src.pose.bones['mixamorig:Hips'].matrix).translation
        hp=TREST['mixamorig:Hips'].translation+(shp-shrest)*k
        # build pose matrices parent-first & local basis
        PM={}
        for n in order:
            b=rig.data.bones[n]; pb=rig.pose.bones[n]
            if b.parent is None:
                M=Matrix.Translation(hp)@W[n].to_matrix().to_4x4()
            else:
                P=PM[b.parent.name]
                rel=TREST[b.parent.name].inverted()@TREST[n]
                head=(P@rel).translation
                rq=W[n] if n in W else (P.to_quaternion()@rel.to_quaternion())
                if n.endswith(tuple(f'{i}' for i in '12')) and 'Hand' in n and fist>0:
                    pass
                M=Matrix.Translation(head)@rq.to_matrix().to_4x4()
            PM[n]=M
            if b.parent is None: basis=TREST[n].inverted()@M
            else: basis=(TREST[b.parent.name].inverted()@TREST[n]).inverted()@PM[b.parent.name].inverted()@M
            q=basis.to_quaternion()
            if n in FIST and fist>0:
                q=Quaternion().slerp(Quaternion(FIST[n]),fist)
                # rebuild PM for finger with fist rotation
                PM[n]=PM[b.parent.name]@(TREST[b.parent.name].inverted()@TREST[n])@q.to_matrix().to_4x4()
            if n in prevq: q.make_compatible(prevq[n])
            prevq[n]=q
            pb.rotation_quaternion=q
            pb.keyframe_insert('rotation_quaternion',frame=fi+1,group=n)
            if b.parent is None:
                pb.location=basis.translation
                pb.keyframe_insert('location',frame=fi+1,group=n)
    nf=len(frames)
    # ground fix
    dg=bpy.context.evaluated_depsgraph_get()
    mins=[]
    for f in range(1,nf+1):
        sc.frame_set(f); dg=bpy.context.evaluated_depsgraph_get()
        e=body.evaluated_get(dg); me=e.to_mesh()
        mins.append(min(v.co.z for v in me.vertices)); e.to_mesh_clear()
    lift=[max(0.0,0.002-m) for m in mins]
    if name not in FLOOR_CLIPS:
        floatd=min(mins)
        if floatd>0.002: lift=[l-(floatd-0.002) for l in lift]
    # smooth lift (keep max envelope)
    sm=[max(lift[max(0,i-2):i+3]) for i in range(nf)]
    sm=[sum(sm[max(0,i-2):i+3])/len(sm[max(0,i-2):i+3]) for i in range(nf)]
    hb=rig.pose.bones['mixamorig:Hips']
    fcs=[fc for fc in act.fcurves if fc.data_path=='pose.bones["mixamorig:Hips"].location']
    # hips local location axis for world Z: basis loc in rest frame -> world z = rest Y? compute
    Rz=TREST['mixamorig:Hips'].to_3x3().inverted()@Vector((0,0,1))
    for fc in fcs:
        for i,kp in enumerate(fc.keyframe_points):
            kp.co.y+=Rz[fc.array_index]*sm[i]; kp.handle_left.y=kp.co.y; kp.handle_right.y=kp.co.y
    act['frames']=nf; act['source']=f'Mixamo: {name}'; act['fist']=fist
    for o in new: bpy.data.objects.remove(o,do_unlink=True)
    for a in list(bpy.data.actions):
        if a.users==0 and not a.use_fake_user: bpy.data.actions.remove(a)
    print('CLIP',name,act.name,nf,'k=%.3f'%k,'minz %.3f..%.3f'%(min(mins),max(mins)),'maxlift %.3f'%max(sm))
    return act

only=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for fn in sorted(glob.glob(f'{D3}/mixamo/*.fbx')):
    if only and os.path.splitext(os.path.basename(fn))[0] not in only: continue
    retarget(fn)
for m in bpy.data.meshes:
    if m.users==0: bpy.data.meshes.remove(m)
for m in bpy.data.armatures:
    if m.users==0: bpy.data.armatures.remove(m)
rig.animation_data.action=None
for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=f'{D3}/v3work/06_anim.blend')
print('saved')

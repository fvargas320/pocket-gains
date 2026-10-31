import bpy, bmesh, math, json
from mathutils import Vector
from mathutils.kdtree import KDTree
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/01_body.blend')
body=bpy.data.objects['Zeek_Body']; me=body.data
kd=KDTree(len(me.vertices))
for v in me.vertices: kd.insert(v.co,v.index)
kd.balance()
def refine(p,r=0.022):
    pts=[c for c,i,d in kd.find_range(Vector(p),r)]
    if len(pts)<5: return Vector(p)
    c=sum(pts,Vector())/len(pts); return c
P='mixamorig:'
J={}
def mir(v): return (-v[0],v[1],v[2])
base={
 'Hips':((0,0.0,0.40),(0,0.0,0.45)),'Spine':((0,0,0.45),(0,0,0.51)),'Spine1':((0,0,0.51),(0,0.0,0.57)),
 'Spine2':((0,0.0,0.57),(0,0.008,0.645)),'Neck':((0,0.008,0.645),(0,0.005,0.69)),'Head':((0,0.005,0.69),(0,0,0.86)),
 'HeadTop_End':((0,0,0.86),(0,0,0.89)),
}
side={
 'Shoulder':((0.02,0.008,0.625),(0.092,0.008,0.603)),
 'Arm':(None,(0.16,0.01,0.515)),'ForeArm':(None,(0.225,0.01,0.425)),'Hand':(None,(0.262,0.0,0.36)),
 'UpLeg':((0.055,0.0,0.385),(0.065,0.0,0.20)),'Leg':(None,(0.065,0.012,0.058)),
 'Foot':(None,(0.07,-0.035,0.018)),'ToeBase':(None,(0.075,-0.08,0.015)),
}
refine_names={'Arm':1,'ForeArm':1,'UpLeg':1,'Leg':1}
arm=bpy.data.armatures.new('Zeek_Rig'); rig=bpy.data.objects.new('Zeek_Rig',arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig; bpy.ops.object.mode_set(mode='EDIT')
eb=arm.edit_bones
parents={'Spine':'Hips','Spine1':'Spine','Spine2':'Spine1','Neck':'Spine2','Head':'Neck','HeadTop_End':'Head'}
for n,(h,t) in base.items():
    b=eb.new(P+n); b.head=h; b.tail=t
    if n in parents: b.parent=eb[P+parents[n]]; b.use_connect=True
chain=['Shoulder','Arm','ForeArm','Hand']; leg=['UpLeg','Leg','Foot','ToeBase']
for S,sg in (('Left',1),('Right',-1)):
    for seq,root in ((chain,'Spine2'),(leg,'Hips')):
        prev=None
        for n in seq:
            h,t=side[n]
            t=Vector((t[0]*sg,t[1],t[2]))
            if n in ('Arm','ForeArm','UpLeg','Leg'): t=refine(t) if n!='UpLeg' else t
            b=eb.new(P+S+n)
            b.head = prev.tail if prev else Vector((h[0]*sg,h[1],h[2]))
            if n=='UpLeg': b.head=Vector((h[0]*sg,h[1],h[2]))
            b.tail=t
            b.parent = prev if prev else eb[P+root]
            if prev: b.use_connect=True
            prev=b
    # antennae
    pts=[(0.036,0.018,0.845),(0.06,0.012,0.905),(0.088,-0.005,0.948),(0.115,-0.025,0.982)]
    prev=None
    for i in range(3):
        b=eb.new(f'Antenna_{S[0]}_{i+1:02d}')
        b.head=(pts[i][0]*sg,pts[i][1],pts[i][2]); b.tail=(pts[i+1][0]*sg,pts[i+1][1],pts[i+1][2])
        b.parent= prev if prev else eb[P+'Head']; b.use_connect=bool(prev); prev=b
# rolls: point bone local Z forward-ish (-Y) for limbs, consistent
for b in eb:
    b.align_roll(Vector((0,-1,0)) if abs(b.vector.normalized().y)<0.9 else Vector((0,0,1)))
J={b.name:[list(b.head),list(b.tail)] for b in eb}
bpy.ops.object.mode_set(mode='OBJECT')
json.dump(J,open('/workspace/gym-app/3d/v2work/joints.json','w'),indent=1)
# bind
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
cnt={vg.index:0 for vg in body.vertex_groups}
for v in me.vertices:
    for g in v.groups:
        if g.weight>0.2: cnt[g.group]+=1
empty={body.vertex_groups[i].name:c for i,c in cnt.items() if c<15}
unweighted=sum(1 for v in me.vertices if not v.groups or sum(g.weight for g in v.groups)<1e-4)
print('RIG bones',len(arm.bones),'groups',len(body.vertex_groups),'unweighted verts',unweighted,'sparse groups',empty)
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v2work/02_rigged.blend')

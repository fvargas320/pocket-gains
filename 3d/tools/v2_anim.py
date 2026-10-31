import bpy, sys, math, os
sys.path.insert(0,'/workspace/gym-app/3d/tools'); from v2_common import *
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/06_final.blend')
sc=bpy.context.scene; sc.render.resolution_x=sc.render.resolution_y=768; sc.eevee.taa_render_samples=12
sc.frame_start=1; sc.frame_end=120; sc.render.fps=24
O=bpy.data.objects; rig=O['Zeek_Rig']; body=O['Zeek_Body']; tank=O['Zeek_Tank']
bpy.context.view_layer.objects.active=rig; bpy.ops.object.mode_set(mode='POSE')
for pb in rig.pose.bones: pb.rotation_mode='QUATERNION'
BONES=[P+n for n in ('Spine','Spine1','Spine2','Neck','Head')]+[P+s+n for s in ('Left','Right') for n in ('Shoulder','Arm','ForeArm','Hand')]+[f'Antenna_{s}_0{i}' for s in 'LR' for i in (1,2,3)]
def reset():
    for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0)
    bpy.context.view_layer.update()
def pose_flex(fa_tilt=0.2, arm_up=0.1, lean=0.0, head=0.0):
    reset()
    if lean: set_world_rot(rig,P+'Spine1',Quaternion((1,0,0),math.radians(lean)))
    for S,sg in (('Left',1),('Right',-1)):
        aim(rig,P+S+'Shoulder',(sg*1,0.0,0.05+arm_up*0.3))
        aim(rig,P+S+'Arm',(sg*1,0.05,arm_up))
        aim(rig,P+S+'ForeArm',(sg*-fa_tilt,-0.2,1))
        aim(rig,P+S+'Hand',(sg*-(fa_tilt+0.1),-0.15,1))
    if head: set_world_rot(rig,P+'Head',Quaternion((0,1,0),math.radians(head)))
def antenna(f):
    for S,sg in (('L',1),('R',-1)):
        for i,amp in ((2,6),(3,10)):
            pb=rig.pose.bones[f'Antenna_{S}_0{i}']
            pb.rotation_quaternion=Quaternion((1,0,0),math.radians(amp*math.sin(f*0.35+sg+i)))@Quaternion((0,0,1),math.radians(amp*0.6*math.cos(f*0.27+i)))
def key(f):
    for n in BONES: rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
def skey(f,vals):
    for o in (body,tank):
        kb=o.data.shape_keys.key_blocks
        for k,v in vals.items():
            if k in kb: kb[k].value=v; kb[k].keyframe_insert('value',frame=f)
plan=[(1,'rest',0),(14,'rest',0),(32,(-0.15,0.08,-4,4),0.35),(44,(0.12,0.15,-6,-3),1.0),(54,(-0.12,0.08,-4,3),0.45),(66,(0.15,0.16,-7,-4),1.0),(76,(-0.12,0.08,-4,4),0.45),(88,(0.15,0.16,-7,0),1.0),(100,(-0.1,0.06,-3,2),0.4),(118,'rest',0),(120,'rest',0)]
for f,p,bic in plan:
    if p=='rest': reset()
    else: pose_flex(*p)
    antenna(f); key(f)
    skey(f,{'arms_biceps':0.3+bic*0.7,'chest':0.25*bic,'shoulders':0.2*bic})
for f in range(4,120,6):
    # extra antenna wiggle keys only
    for S in 'LR':
        for i in (2,3):
            pass
# antenna wiggle on separate keys
for f in range(1,121,5):
    antenna(f)
    for S in 'LR':
        for i in (2,3): rig.pose.bones[f'Antenna_{S}_0{i}'].keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.object.mode_set(mode='OBJECT')
camera(22,1.2,0.52)
out='/tmp/v2/anim_frames_v1/'; os.makedirs(out,exist_ok=True)
sc.render.filepath=out+'f_'; sc.render.image_settings.file_format='PNG'
if '--still' in sys.argv:
    for f in (1,44,66): sc.frame_set(f); sc.render.filepath=f'/tmp/v2/animstill2_{f}.png'; bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
    bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v2work/07_anim.blend')
print('ANIMDONE')

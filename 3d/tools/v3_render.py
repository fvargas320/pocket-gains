# Portable per-clip toon render. usage: blender -b 08_render.blend -P v3_render.py -- '<json>'
import bpy, sys, json, math
def setslot(ad,A):
    if hasattr(ad,'action_slot') and len(getattr(A,'slots',[])):
        try: ad.action_slot=A.slots[0]
        except Exception as e: print('slot',e)
    print('SLOT',A.name,getattr(ad,'action_slot',None))
def run(cfg):
    sc=bpy.context.scene; O=bpy.data.objects
    rig=O['Zeek_Rig']; body=O['Zeek_Body']
    PRE={'noodle':dict(noodle=1.0),'base':{},
         'mid':dict(arms_biceps=.5,arms_triceps=.5,shoulders=.5,chest=.5,back_lats=.5,abs_core=.5,legs_quads=.4,legs_glutes=.4,legs_calves=.4),
         'max':dict(arms_biceps=1,arms_triceps=1,shoulders=1,chest=1,back_lats=1,abs_core=1,legs_quads=1,legs_glutes=1,legs_calves=1),
         'chest':dict(arms_biceps=1,arms_triceps=1,shoulders=1,chest=1,back_lats=1,abs_core=.6,legs_quads=-.3,legs_glutes=-.3,legs_calves=-.3),
         'legday':dict(arms_biceps=.6,arms_triceps=.6,shoulders=.6,chest=.6,back_lats=.6,abs_core=.6,legs_quads=1,legs_glutes=1,legs_calves=1)}
    mus=PRE[cfg.get('muscles','base')] if isinstance(cfg.get('muscles','base'),str) else cfg['muscles']
    for kb in body.data.shape_keys.key_blocks[1:]: kb.value=mus.get(kb.name,0.0)
    body['vascularity']=cfg.get('vasc',0.0); body.update_tag()
    gear=cfg.get('gear',['Zeek_Tank','Zeek_Beanie','Zeek_GoldChain'])
    for o in O:
        if o.get('accessory'):
            o.hide_render=o.name not in gear
            if o.data.shape_keys:
                for kb in o.data.shape_keys.key_blocks[1:]:
                    if kb.name in body.data.shape_keys.key_blocks: kb.value=body.data.shape_keys.key_blocks[kb.name].value
    # aura
    tier=cfg.get('aura',0); T={1:'Teal',2:'Gold',3:'Purple'}
    for o in O:
        if o.get('aura'):
            o.hide_render= tier==0
            if tier and o.name=='Zeek_Aura_Shell':
                o.data.materials[0]=bpy.data.materials['Aura_Shell_'+T[tier]]
                for kb in (o.data.shape_keys.key_blocks[1:] if o.data.shape_keys else []): kb.value=body.data.shape_keys.key_blocks[kb.name].value
            if tier and o.name=='Zeek_Aura_Flames': o.data.materials[0]=bpy.data.materials['Aura_Flame_'+T[tier]]
    # action & props
    act=cfg.get('action'); props=[]
    for o in O:
        if o.get('prop'): o.hide_render=True
    if act:
        A=bpy.data.actions[act]; rig.animation_data_create(); rig.animation_data.action=A; setslot(rig.animation_data,A)
        props=A.get('props','').split(',') if A.get('props') else []
        for p in props: O[p].hide_render=False
        if 'Prop_Barbell' in props:
            O['Prop_Barbell'].animation_data_create(); O['Prop_Barbell'].animation_data.action=bpy.data.actions[A['bar_action']]; setslot(O['Prop_Barbell'].animation_data,bpy.data.actions[A['bar_action']])
    else:
        rig.animation_data.action=None
        for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0)
        for bn,(x,y,z,w_) in cfg.get('pose',{}).items(): pass
    # expressions: list of [frame, name]
    ex=cfg.get('expr',[[1,'Smirk']])
    for n in ('Smirk','Grin','Grit','Tired'):
        o=O['Zeek_Face_'+n]; o.animation_data_clear(); o.hide_render=True
        for f,e in ex:
            o.hide_render=(e!=n); o.keyframe_insert('hide_render',frame=f)
    O['Floor'].hide_render=not cfg.get('floor',True)
    # camera
    piv=O['CamPivot']; piv.constraints[0].mute=not cfg.get('follow',False)
    cam=O['ShotCam']; yaw=math.radians(cfg.get('yaw',25)); e=math.radians(cfg.get('elev',6)); d=4
    zc=cfg.get('zc',0.5)
    cam.location=(d*math.sin(yaw)*math.cos(e),-d*math.cos(yaw)*math.cos(e),zc+d*math.sin(e)); cam.rotation_euler=(math.radians(90)-e,0,yaw)
    cam.data.ortho_scale=cfg.get('ortho',1.1); sc.camera=cam
    r=cfg.get('res',720); sc.render.resolution_x=cfg.get('resx',r); sc.render.resolution_y=r
    sc.eevee.taa_render_samples=cfg.get('samples',16)
    fr=cfg.get('frames')
    if fr is None: fr=[1,int(A['frames'])] if act else [1,1]
    sc.frame_start,sc.frame_end=fr[0],fr[1]; sc.frame_step=cfg.get('step',1)
    mk=cfg.get('muscle_keys')
    if mk:
        objs=[body]+[o for o in O if (o.get('accessory') or o.get('aura')) and o.data.shape_keys]
        for o in objs:
            if o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
        for f,pre in mk:
            mm=PRE[pre]
            for o in objs:
                for kb in o.data.shape_keys.key_blocks[1:]:
                    kb.value=mm.get(kb.name,0.0); kb.keyframe_insert('value',frame=f)
    else:
        for o in O:
            if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
    for o in O:
        if o.get('aura'): o.animation_data_clear() if o.animation_data and o.animation_data.action else None
    if cfg.get('aura_on') and tier:
        for o in O:
            if o.get('aura'):
                o.hide_render=True; o.keyframe_insert('hide_render',frame=1)
                o.hide_render=False; o.keyframe_insert('hide_render',frame=cfg['aura_on'])
    vk=cfg.get('vasc_keys')
    if vk:
        for f,v in vk: body['vascularity']=v; body.keyframe_insert('["vascularity"]',frame=f)
    elif body.animation_data: body.animation_data_clear()
    imsf=sc.render.image_settings
    if cfg.get('video'):
        if hasattr(imsf,'media_type'): imsf.media_type='VIDEO'
        imsf.file_format='FFMPEG'; sc.render.ffmpeg.format='MPEG4'; sc.render.ffmpeg.codec='H264'
        sc.render.ffmpeg.constant_rate_factor='HIGH'; sc.render.ffmpeg.ffmpeg_preset='GOOD'
    else:
        if hasattr(imsf,'media_type'): imsf.media_type='IMAGE'
        imsf.file_format='PNG'
    sc.render.filepath=cfg['out']
    if cfg.get('still'):
        sc.frame_set(cfg['still']); bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
    print('DONE',cfg['out'])

arg=sys.argv[sys.argv.index('--')+1]
if arg.endswith('.json'):
    jobs=json.load(open(arg))
    import os
    for j in jobs:
        if j.get('skip_existing') and os.path.exists(j['out'].rstrip('/\\')+'.done'): continue
        run(j); open(j['out'].rstrip('/\\')+'.done','w').write('ok')
else: run(json.loads(arg))

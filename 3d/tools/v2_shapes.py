import bpy, numpy as np, json
P='mixamorig:'
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/02_rigged.blend')
body=bpy.data.objects['Zeek_Body']; rig=bpy.data.objects['Zeek_Rig']; me=body.data
J=json.load(open('/workspace/gym-app/3d/v2work/joints.json'))
# HeadTop_End: non-deforming, merge weights into Head
vgH=body.vertex_groups[P+'Head']; vgE=body.vertex_groups.get(P+'HeadTop_End')
if vgE:
    for v in me.vertices:
        for g in v.groups:
            if g.group==vgE.index: vgH.add([v.index],g.weight,'ADD')
    body.vertex_groups.remove(vgE)
rig.data.bones[P+'HeadTop_End'].use_deform=False
N=len(me.vertices)
co=np.zeros(N*3); me.vertices.foreach_get('co',co); co=co.reshape(N,3)
nr=np.zeros(N*3); me.vertices.foreach_get('normal',nr); nr=nr.reshape(N,3)
W={vg.name:np.zeros(N) for vg in body.vertex_groups}
idx={vg.index:vg.name for vg in body.vertex_groups}
for v in me.vertices:
    for g in v.groups: W[idx[g.group]][v.index]=g.weight
def w(*names):
    s=np.zeros(N)
    for n in names:
        for S in ('Left','Right'):
            k=P+n.replace('#',S)
            if k in W: s+=W[k]
        if P+n in W: s+=W[P+n]
    return np.clip(s,0,1)
E=np.zeros(len(me.edges)*2,dtype=int); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
deg=np.bincount(E.ravel(),minlength=N).astype(float)
def smooth(d,it=6,f=0.5):
    for _ in range(it):
        acc=np.zeros_like(d); np.add.at(acc,E[:,0],d[E[:,1]]); np.add.at(acc,E[:,1],d[E[:,0]])
        d=d*(1-f)+f*acc/np.maximum(deg,1)[:,None]
    return d
x,y,z=co[:,0],co[:,1],co[:,2]; ax=np.abs(x); sx=np.sign(x)+(x==0)
nx,ny,nz=nr[:,0],nr[:,1],nr[:,2]
def ss(e0,e1,t): t=np.clip((t-e0)/(e1-e0),0,1); return t*t*(3-2*t)
def g2(dx,dz,rx,rz): return np.exp(-((dx/rx)**2+(dz/rz)**2))
front=np.clip(-ny*1.2+0.15,0,1); back=np.clip(ny*1.2+0.15,0,1)
def seg_param(bone):
    a=np.array(J[P+'Left'+bone][0]); b=np.array(J[P+'Left'+bone][1])
    p=co.copy(); p[:,0]=ax; ab=b-a; t=((p-a)@ab)/(ab@ab); return np.clip(t,0,1)
keys={}
# arms
ua=w('#Arm'); fa=w('#ForeArm'); t_u=seg_param('Arm'); t_f=seg_param('ForeArm')
prof_u=np.sin(np.pi*np.clip((t_u-0.05)/0.9,0,1))**1.2; prof_f=np.sin(np.pi*np.clip(t_f/0.8,0,1))*(1-t_f*0.5)
keys['arms_biceps']=(ua*prof_u*(0.35+front*1.0)*0.011 + fa*prof_f*(0.3+front*0.4)*0.0045)[:,None]*nr
keys['arms_triceps']=(ua*prof_u*(0.25+back*1.0)*0.010 + fa*prof_f*(0.3+back*0.3)*0.003)[:,None]*nr
# shoulders: deltoid + traps
aJ=np.array(J[P+'LeftArm'][0]); dl=np.sqrt((ax-aJ[0]-0.004)**2+(y-aJ[1])**2*0.8+(z-aJ[2]+0.008)**2)
outw=np.clip(nx*sx*0.8+nz*0.5+0.2,0,1)
delt=np.exp(-(dl/0.038)**2)*outw*(1-w('Head','Neck'))
trap=g2(ax-0.045,z-0.64,0.03,0.022)*np.clip(nz+0.3,0,1)*np.clip(1-w('Head'),0,1)*(ax>0.012)
keys['shoulders']=((delt*0.011+trap*0.005)*(1-w('#Hand','#ForeArm')))[:,None]*nr
# chest
pec=g2(ax-0.043,z-0.572,0.042,0.034)*np.clip(-ny*1.3,0,1)*(1-w('#Arm','#ForeArm','Head'))
pec*=1+0.35*np.clip((0.585-z)/0.03,0,1)*(z>0.545)
keys['chest']=(pec*0.017)[:,None]*nr
# back/lats
torso=np.clip(w('Spine','Spine1','Spine2','#Shoulder')*(1-w('#Arm')),0,1)
latz=ss(0.465,0.53,z)*(1-ss(0.61,0.65,z))
lat_side=latz*ss(0.025,0.07,ax)*torso
lat_back=g2(ax-0.055,z-0.56,0.05,0.06)*back*torso
d=(lat_back*0.009)[:,None]*nr; d[:,0]+=sx*lat_side*0.010
keys['back_lats']=d
# abs
reg=g2(x,z-0.495,0.05,0.06)*np.clip(-ny*1.4,0,1)*(1-w('#Arm','#UpLeg'))*(z>0.43)
bumps=np.zeros(N)
for cz in (0.462,0.495,0.528):
    for cx in (-0.0175,0.0175): bumps+=g2(x-cx,z-cz,0.0115,0.0115)
keys['abs_core']=(reg*(0.25+bumps)*0.0065)[:,None]*nr
# legs
ul=w('#UpLeg'); lg=w('#Leg')
quad=ul*np.exp(-((z-0.27)/0.07)**2)*(0.35+front*0.9)
quad+=ul*g2(ax-0.05,z-0.225,0.03,0.025)*front*0.6  # teardrop (inner, near knee)
keys['legs_quads']=(quad*0.0085)[:,None]*nr
glu=g2(ax-0.048,z-0.375,0.045,0.04)*back*(ul+w('Hips')).clip(0,1)
keys['legs_glutes']=(glu*0.011)[:,None]*nr
calf=lg*np.exp(-((z-0.145)/0.045)**2)*(0.3+back*1.0)
keys['legs_calves']=(calf*0.0085)[:,None]*nr
# noodle: thin everything except head/hands/feet/antennae
limb=w('#Arm','#ForeArm','#UpLeg','#Leg'); tor=w('Spine','Spine1','Spine2','Hips','#Shoulder')*0.7
nood=np.clip(limb+tor,0,1)*(1-w('Head','Neck','#Hand','#Foot','#ToeBase'))
keys['noodle']=(-nood*0.0055)[:,None]*nr
GAIN={'arms_biceps':1.8,'arms_triceps':1.7,'shoulders':2.0,'chest':1.7,'back_lats':1.7,'abs_core':1.5,'legs_quads':1.3,'legs_glutes':1.25,'legs_calves':1.3,'noodle':1.2}
# write shape keys
if not me.shape_keys: body.shape_key_add(name='Basis',from_mix=False)
order=['arms_biceps','arms_triceps','shoulders','chest','back_lats','abs_core','legs_quads','legs_glutes','legs_calves','noodle']
for k in order:
    d=smooth(keys[k]*GAIN[k],8,0.5)
    sk=me.shape_keys.key_blocks.get(k) or body.shape_key_add(name=k,from_mix=False)
    sk.data.foreach_set('co',(co+d).ravel())
    sk.slider_min=0.0 if k=='noodle' else -0.5; sk.slider_max=1.0; sk.value=0
    print('KEY',k,'maxdisp %.4f'%np.linalg.norm(d,axis=1).max(),'verts>0.5mm',int((np.linalg.norm(d,axis=1)>5e-4).sum()))
# leg definition mask attribute (for baking)
m=np.clip(ul+lg,0,1)*ss(0.055,0.085,z)*(1-ss(0.27,0.295,z))
a=me.color_attributes.get('leg_def_mask') or me.color_attributes.new('leg_def_mask','FLOAT_COLOR','POINT')
a.data.foreach_set('color',np.repeat(m,4).reshape(N,4).clip(0,1).ravel())
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v2work/03_shapes.blend')

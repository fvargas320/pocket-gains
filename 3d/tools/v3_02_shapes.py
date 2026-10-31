# v3 dramatic shape keys: radial volume growth about bone axes + sculpted torso pushes
import bpy, numpy as np, json
P='mixamorig:'
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v3work/01_rig.blend')
body=bpy.data.objects['Zeek_Body']; rig=bpy.data.objects['Zeek_Rig']; me=body.data
J=json.load(open('/workspace/gym-app/3d/v2work/joints.json'))
if me.shape_keys:
    body.shape_key_clear()
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
            if k in W and '#' in n: s+=W[k]
        if P+n in W: s+=W[P+n]
    return np.clip(s,0,1)
handall=np.clip(sum(W[k] for k in W if 'Hand' in k),0,1)
E=np.zeros(len(me.edges)*2,dtype=int); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
deg=np.bincount(E.ravel(),minlength=N).astype(float)
def smooth(d,it=6,f=0.5):
    for _ in range(it):
        acc=np.zeros_like(d); np.add.at(acc,E[:,0],d[E[:,1]]); np.add.at(acc,E[:,1],d[E[:,0]])
        d=d*(1-f)+f*acc/np.maximum(deg,1)[:,None]
    return d
x,y,z=co[:,0],co[:,1],co[:,2]; ax=np.abs(x); sx=np.where(x>=0,1.0,-1.0)
nx,ny,nz=nr[:,0],nr[:,1],nr[:,2]
def ss(e0,e1,t): t=np.clip((t-e0)/(e1-e0),0,1); return t*t*(3-2*t)
def g2(dx,dz,rx,rz): return np.exp(-((dx/rx)**2+(dz/rz)**2))
def bump(t,c,wd): return np.exp(-((t-c)/wd)**2)
def axis_frame(bone):
    a=np.array(J[P+'Left'+bone][0]); b=np.array(J[P+'Left'+bone][1])
    p=co.copy(); p[:,0]=ax; ab=b-a; L=np.linalg.norm(ab); dn=ab/L
    t=((p-a)@dn)/L; tc=np.clip(t,0,1)
    foot=a+np.outer(tc*L,dn); r=p-foot; rl=np.linalg.norm(r,axis=1)+1e-9; u=r/rl[:,None]
    u_w=u.copy(); u_w[:,0]*=sx  # back to world (mirror)
    wb=w('#'+bone); m=(wb>0.8)&(tc>0.05)&(tc<0.95)
    cap=np.median(rl[m])*1.15 if m.sum()>20 else rl.max()
    r_w=u_w*np.minimum(rl,cap)[:,None]
    return t,u,u_w,r_w,rl
keys={}
# ---------- ARMS
ua=w('#Arm'); fa=w('#ForeArm')
tU,uU,uUw,rU,_=axis_frame('Arm'); tF,uF,uFw,rF,_=axis_frame('ForeArm')
frU=np.clip(-uU[:,1],0,1); bkU=np.clip(uU[:,1],0,1)
frF=np.clip(-uF[:,1],0,1); bkF=np.clip(uF[:,1],0,1)
# biceps: peaked ball on the front, forearm flexor mass near elbow
sB=ua*(0.6+1.3*frU**1.5)*bump(tU,0.58,0.3)*2.0 + fa*(0.7+0.6*frF)*bump(tF,0.28,0.35)*1.35
sT=ua*(0.5+1.1*bkU**1.3+0.4*np.clip(uU[:,0],0,1))*bump(tU,0.45,0.34)*1.6 + fa*(0.3+0.4*bkF)*bump(tF,0.22,0.3)*0.8
keys['arms_biceps']=sB[:,None]*rU*(ua>0)[:,None]*(ua/np.maximum(ua+fa,1e-6))[:,None]+ (sB[:,None]*rF)*(fa/np.maximum(ua+fa,1e-6))[:,None]
keys['arms_triceps']=sT[:,None]*rU*(ua/np.maximum(ua+fa,1e-6))[:,None]+(sT[:,None]*rF)*(fa/np.maximum(ua+fa,1e-6))[:,None]
# ---------- SHOULDERS: round deltoid caps + traps
aJ=np.array(J[P+'LeftArm'][0])
c=np.array([aJ[0]+0.006,aJ[1],aJ[2]-0.006])
dv=np.stack([ax-c[0],y-c[1],z-c[2]],1); dl=np.linalg.norm(dv,axis=1)+1e-9; du=dv/dl[:,None]; du[:,0]*=sx
outw=np.clip(nx*sx*0.9+nz*0.6+0.25,0,1)
nohead=1-w('Head','Neck')
delt=np.exp(-(dl/0.05)**2.2)*outw*nohead*(1-handall)*(1-w('#ForeArm'))
trap=g2(ax-0.04,z-0.655,0.035,0.03)*np.clip(nz+0.4,0,1)*(1-w('Head'))*ss(0.008,0.025,ax)
neck=w('Neck')*(1-w('Head'))*ss(0.64,0.68,z)
d=du*(delt*0.036)[:,None]; d[:,2]+=trap*0.024; d[:,0]+=sx*trap*0.006
d[:,0]+=x*neck*0.35; d[:,1]+=y*neck*0.25
keys['shoulders']=d
# ---------- CHEST: thick slab pecs with a lower shelf
armx=w('#Arm','#ForeArm','Head')
zc=0.58; below=z<zc
rz=np.where(below,0.026,0.05)
pec=np.exp(-((ax-0.045)/0.055)**2-((z-zc)/rz)**2)*np.clip(-ny*1.4+0.1,0,1)*(1-armx)
d=np.zeros((N,3)); d[:,1]=-pec*0.036; d[:,0]=sx*pec*0.008*ss(0.03,0.09,ax); d[:,2]=pec*0.004
keys['chest']=d
# ---------- BACK / LATS: V-taper wings
torso=np.clip(w('Spine','Spine1','Spine2','#Shoulder','Hips')*(1-w('#Arm')),0,1)
latz=ss(0.47,0.575,z)*(1-ss(0.6,0.655,z))
side=np.clip(nx*sx*1.2+0.1,0,1)
lat=latz*side*torso*ss(0.03,0.065,ax)
upb=g2(ax-0.05,z-0.585,0.055,0.06)*np.clip(ny*1.3,0,1)*torso
d=np.zeros((N,3)); d[:,0]=sx*lat*0.05; d[:,1]=upb*0.022+lat*0.006
keys['back_lats']=d
# ---------- ABS: six-pack blocks + obliques
reg=g2(x,z-0.495,0.055,0.065)*np.clip(-ny*1.4,0,1)*(1-w('#Arm','#UpLeg'))*(z>0.43)
bumps=np.zeros(N)
for cz in (0.46,0.493,0.526):
    for cx in (-0.019,0.019): bumps+=g2(x-cx,z-cz,0.012,0.0115)**0.8
obl=g2(ax-0.062,z-0.49,0.02,0.04)*np.clip(nx*sx,0,1)*torso
keys['abs_core']=((reg*(0.2+bumps)*0.009)[:,None]*nr) + np.stack([sx*obl*0.008,np.zeros(N),np.zeros(N)],1)
# ---------- LEGS
ul=w('#UpLeg'); lg=w('#Leg')
tQ,uQ,uQw,rQ,_=axis_frame('UpLeg'); tC,uC,uCw,rC,_=axis_frame('Leg')
frQ=np.clip(-uQ[:,1],0,1); outQ=np.clip(uQ[:,0],0,1); inQ=np.clip(-uQ[:,0],0,1); bkQ=np.clip(uQ[:,1],0,1)
sQ=ul*(0.4+0.95*frQ+0.6*outQ-0.2*inQ+0.3*bkQ).clip(0.1)*bump(tQ,0.62,0.36)
sQ+=ul*1.0*g2(uQ[:,0]+0.6,tQ-0.85,0.5,0.13)*frQ  # teardrop above knee, inner front
sQ*=(1-0.6*ss(0.255,0.32,z))
keys['legs_quads']=(sQ*1.0)[:,None]*rQ
glu=g2(ax-0.05,z-0.37,0.05,0.045)*np.clip(ny*1.3+0.1,0,1)*np.clip(ul+w('Hips'),0,1)
d=np.zeros((N,3)); d[:,1]=glu*0.03; d[:,2]=glu*0.004
keys['legs_glutes']=d
bkC=np.clip(uC[:,1],0,1); sdC=np.abs(uC[:,0])
sC=lg*(0.2+1.25*bkC**1.2+0.35*sdC)*bump(tC,0.3,0.25)
keys['legs_calves']=(sC*0.95)[:,None]*rC
# ---------- NOODLE: skinny limbs, narrow chest, small butt
nh=(1-w('Head','Neck')-handall).clip(0,1)*(1-w('#Foot','#ToeBase'))
s=-(ua*0.5*ss(0.0,0.15,tU) + fa*0.38*(1-ss(0.8,1.0,tF)))
dN=s[:,None]*np.where((ua>=fa)[:,None],rU,rF)
dN+=(-(ul*0.42*ss(0.05,0.25,tQ)+lg*0.4*(1-ss(0.85,1.0,tC))))[:,None]*np.where((ul>=lg)[:,None],rQ,rC)
tz=torso*(1-ss(0.6,0.64,z))
dN[:,0]+=-x*0.2*tz; dN[:,1]+=-(y+0.004)*0.22*tz
dN[:,1]+=-glu*0.012
keys['noodle']=dN*nh[:,None]
GAIN={k:1.0 for k in keys}
if not me.shape_keys: body.shape_key_add(name='Basis',from_mix=False)
order=['arms_biceps','arms_triceps','shoulders','chest','back_lats','abs_core','legs_quads','legs_glutes','legs_calves','noodle']
for k in order:
    dd=keys[k]*GAIN[k]
    dd[handall>0.5]*=0
    dd=smooth(dd,10,0.5)
    sk=body.shape_key_add(name=k,from_mix=False)
    sk.data.foreach_set('co',(co+dd).ravel())
    sk.slider_min=0.0 if k=='noodle' else -0.5; sk.slider_max=1.0; sk.value=0
    print('KEY',k,'maxdisp %.4f'%np.linalg.norm(dd,axis=1).max())
# masks for texture bakes
m=np.clip(ul+lg,0,1)*ss(0.055,0.085,z)*(1-ss(0.27,0.295,z))
vein=np.clip(ua+fa*1.0+np.clip(ul+lg,0,1)*ss(0.06,0.1,z)*(1-ss(0.3,0.33,z))*0.9+np.exp(-((ax-0.045)/0.05)**2-((z-0.58)/0.04)**2)*np.clip(-ny*1.4,0,1)*0.8,0,1)*(1-handall)*(1-w('Head','Neck'))
for nm,val in (('leg_def_mask',m),('vein_mask',vein)):
    a=me.color_attributes.get(nm) or me.color_attributes.new(nm,'FLOAT_COLOR','POINT')
    a.data.foreach_set('color',np.repeat(val,4).reshape(N,4).clip(0,1).ravel())
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v3work/02_shapes.blend')

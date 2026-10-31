# v3 rig: from v2 02_rigged -> merge HeadTop, antenna weight cleanup, add finger bones (2 per digit) + weights
import bpy, numpy as np, json, math, sys
from mathutils import Vector, Matrix
P='mixamorig:'
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/02_rigged.blend')
body=bpy.data.objects['Zeek_Body']; rig=bpy.data.objects['Zeek_Rig']; me=body.data
J=json.load(open('/workspace/gym-app/3d/v2work/joints.json'))
N=len(me.vertices)
# HeadTop_End -> Head
vgH=body.vertex_groups[P+'Head']; vgE=body.vertex_groups.get(P+'HeadTop_End')
if vgE:
    for v in me.vertices:
        for g in v.groups:
            if g.group==vgE.index: vgH.add([v.index],g.weight,'ADD')
    body.vertex_groups.remove(vgE)
rig.data.bones[P+'HeadTop_End'].use_deform=False
# antenna cleanup (same as v2_gear)
def seg_dist(p,a,b):
    ab=b-a; t=np.clip(((p-a)@ab)/(ab@ab),0,1); return np.linalg.norm(p-(a+np.outer(t,ab)),axis=1)
co=np.array([v.co[:] for v in me.vertices])
for S in 'LR':
    names=[f'Antenna_{S}_0{i}' for i in (1,2,3)]
    pts=[np.array(J[names[0]][0])]+[np.array(J[n][1]) for n in names]
    tip=pts[-1]+(pts[-1]-pts[-2])*0.6
    dmin=np.min([seg_dist(co,pts[i],pts[i+1] if i<2 else tip) for i in range(3)],axis=0)
    a0,a1=pts[0],pts[1]; ax_=(a1-a0)/np.linalg.norm(a1-a0); tb=(co-a0)@ax_
    keepf=np.clip((tb+0.004)/0.022,0,1)*(dmin<0.03)
    gidx=[body.vertex_groups[n].index for n in names]
    for v in me.vertices:
        tot=0
        for g in v.groups:
            if g.group in gidx:
                nw=g.weight*keepf[v.index]; tot+=g.weight-nw; g.weight=nw
        if tot>1e-4: vgH.add([v.index],tot,'ADD')
# ---- fingers
E=np.array([e.vertices[:] for e in me.edges])
gi={vg.name:vg.index for vg in body.vertex_groups}
def wget(name):
    w=np.zeros(N); i=gi[name]
    for v in me.vertices:
        for g in v.groups:
            if g.group==i: w[v.index]=g.weight
    return w
FINGERS={}
def comps_at(sel):
    sel=set(sel); adj={}
    for u,v in E:
        if u in sel and v in sel: adj.setdefault(u,[]).append(v); adj.setdefault(v,[]).append(u)
    seen=set(); out=[]
    for s in sel:
        if s in seen: continue
        st=[s]; seen.add(s); c=[]
        while st:
            x=st.pop(); c.append(x)
            for y in adj.get(x,[]):
                if y not in seen: seen.add(y); st.append(y)
        out.append(c)
    return out
for S,sg in (('Left',1),('Right',-1)):
    hb=P+S+'Hand'; a=np.array(J[hb][0]); b=np.array(J[hb][1]); d=(b-a)/np.linalg.norm(b-a)
    hw=wget(hb); hv=np.where(hw>0.2)[0]; t=(co-a)@d
    # seeds: finger comps at 0.060 (>10 verts) + thumb comp at 0.045 not overlapping them
    seeds=[]
    for c in comps_at(hv[t[hv]>0.060]):
        if len(c)>10: seeds.append(max(c,key=lambda i:t[i]))
    for c in comps_at(hv[t[hv]>0.045]):
        if len(c)>10 and not any(sd in c for sd in seeds): seeds.append(max(c,key=lambda i:t[i]))
    info=[]
    for sd in seeds:
        base=None
        for t0 in np.arange(0.075,0.02,-0.0025):
            for c in comps_at(hv[t[hv]>t0]):
                if sd in c:
                    if any(o in c for o in seeds if o!=sd): break
                    base=t0; cc=c
            else:
                continue
            break
        # base = lowest t0 where still alone
        if base is None: continue
        vs=np.array(cc); pts=co[vs]
        bpt=co[vs[t[vs]<base+0.006]].mean(0)
        dist=np.linalg.norm(pts-bpt,axis=1); tip=pts[dist>np.percentile(dist,92)].mean(0)
        info.append(dict(verts=vs,base=bpt,tip=tip,t0=base))
    print('FINGERS',S,[(len(i['verts']),round(i['t0'],4),np.round(i['base'],3).tolist()) for i in info])
    bases=np.array([i['base'] for i in info])
    th=int(np.argmin([((i['tip']-i['base'])/np.linalg.norm(i['tip']-i['base']))@d for i in info]))  # thumb: least aligned with hand axis
    thumb=info.pop(th); info.sort(key=lambda i:i['base'][1])
    names=['Index','Middle','Ring','Pinky','Little'][:len(info)]
    FINGERS[S]={'Thumb':thumb}; FINGERS[S].update({n:i for n,i in zip(names,info)})
# palm-side direction: from hand centre toward body midline (x->0), slightly
bpy.context.view_layer.objects.active=rig; bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
newb={}
for S,F in FINGERS.items():
    hbn=P+S+'Hand'
    for fn,i in F.items():
        base=Vector(i['base']); tip=Vector(i['tip'])
        # pull base slightly back into palm for nicer pivot
        dirv=(tip-base).normalized(); L=(tip-base).length
        base2=base-dirv*L*0.12; mid=base2+(tip-base2)*0.5
        b1=eb.new(f'{P}{S}Hand{fn}1'); b1.head=base2; b1.tail=mid; b1.parent=eb[hbn]; b1.use_deform=True
        b2=eb.new(f'{P}{S}Hand{fn}2'); b2.head=mid; b2.tail=tip; b2.parent=b1; b2.use_connect=True; b2.use_deform=True
        # roll: align z axis with palm normal guess (toward -x*sg)
        sg=1 if S=='Left' else -1
        for bb in (b1,b2): bb.align_roll(Vector((-sg,0,0)))
        newb[(S,fn)]=(base2.copy(),mid.copy(),tip.copy())
bpy.ops.object.mode_set(mode='OBJECT')
# weights
for S,F in FINGERS.items():
    hbn=P+S+'Hand'; hvg=body.vertex_groups[hbn]
    for fn,i in F.items():
        base2,mid,tip=[np.array(v) for v in newb[(S,fn)]]
        v1=body.vertex_groups.new(name=f'{P}{S}Hand{fn}1'); v2=body.vertex_groups.new(name=f'{P}{S}Hand{fn}2')
        # include a margin ring below the island: verts within hand within small distance of base
        vs=i['verts']; d=tip-base2; Ld=np.linalg.norm(d); dn=d/Ld
        hw=wget(hbn); cand=np.where(hw>0.05)[0]
        tt=(co[cand]-base2)@dn/Ld
        rad=np.linalg.norm((co[cand]-base2)-np.outer(tt*Ld,dn),axis=1)
        isl=set(vs.tolist())
        for k,vi in enumerate(cand):
            if vi not in isl:
                if not (-0.25<tt[k]<0.15 and rad[k]<0.011): continue
                f=np.clip((tt[k]+0.25)/0.35,0,1)*0.8
            else:
                f=np.clip((tt[k]+0.05)/0.15,0.6,1)
            tk=tt[k]
            s2=np.clip((tk-0.42)/0.16,0,1)   # blend to segment 2 near mid joint
            w2=f*s2; w1=f*(1-s2); wh=1-f
            ow=hw[vi]
            v1.add([int(vi)],float(w1*ow),'REPLACE'); v2.add([int(vi)],float(w2*ow),'REPLACE'); hvg.add([int(vi)],float(wh*ow),'REPLACE')
# ---- store fist pose (local quats) as custom property
bpy.context.view_layer.update()
fist={}
for S in ('Left','Right'):
    sg=1 if S=='Left' else -1
    F=FINGERS[S]
    # palm normal: cross of finger dir and spread dir, sign toward body (−x*sg)
    FN=[k for k in F if k!='Thumb']
    fdir=np.mean([F[k]['tip']-F[k]['base'] for k in FN],axis=0); fdir/=np.linalg.norm(fdir)
    spread=F[FN[-1]]['base']-F[FN[0]]['base']; spread-= fdir*(spread@fdir); spread/=np.linalg.norm(spread)
    pn=np.cross(fdir,spread)
    if pn[0]*sg>0: pn=-pn
    for fn in F:
        a1,a2=((40,35) if fn=='Thumb' else (80,95))
        tdir=Vector(F[fn]['tip']-F[fn]['base']).normalized()
        ax=tdir.cross(Vector(pn)).normalized()
        for seg,ang in ((1,a1),(2,a2)):
            bn=f'{P}{S}Hand{fn}{seg}'; M=rig.data.bones[bn].matrix_local.to_3x3()
            R=Matrix.Rotation(math.radians(ang),3,ax)
            q=(M.inverted()@R@M).to_quaternion()
            fist[bn]=list(q)
    rig[f'palm_normal_{S}']=list(pn); rig[f'fist_center_{S}']=list(np.mean([F[k]['base'] for k in FN],axis=0)+pn*0.012)
rig['fist_pose']=json.dumps(fist)
json.dump({S:{k:{'base':v['base'].tolist(),'tip':v['tip'].tolist()} for k,v in F.items()} for S,F in FINGERS.items()},open('/workspace/gym-app/3d/v3work/fingers.json','w'))
print('BONES',len(rig.data.bones))
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v3work/01_rig.blend')

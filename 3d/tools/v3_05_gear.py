import bpy, bmesh, numpy as np, math, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path.insert(0,'/workspace/gym-app/3d/tools')
from v3_common import *
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v3work/04_facemat.blend')
body=bpy.data.objects['Zeek_Body']; rig=bpy.data.objects['Zeek_Rig']; bme=body.data
N=len(bme.vertices)
bco=np.array([v.co[:] for v in bme.vertices]); bnr=np.array([v.normal[:] for v in bme.vertices])
KEYS=[k.name for k in bme.shape_keys.key_blocks[1:]]
kco={}
for k in KEYS:
    a=np.zeros(N*3); bme.shape_keys.key_blocks[k].data.foreach_get('co',a); kco[k]=a.reshape(N,3)
gi={vg.name:vg.index for vg in body.vertex_groups}
def wsum(names):
    s=np.zeros(N); ids={gi[n] for n in names if n in gi}
    for v in bme.vertices:
        for g in v.groups:
            if g.group in ids: s[v.index]+=g.weight
    return s
LR=lambda n:[P+'Left'+n,P+'Right'+n]
armw=wsum(LR('Arm')+LR('ForeArm')+LR('Hand')); headw=wsum([P+'Head',P+'Neck'])
antw=wsum([f'Antenna_{s}_0{i}' for s in 'LR' for i in (1,2,3)])
def link(o): bpy.context.scene.collection.objects.link(o); return o
def finish(o):
    o.parent=rig; o.matrix_parent_inverse=rig.matrix_world.inverted()
    m=o.modifiers.new('Armature','ARMATURE'); m.object=rig
def head_only(o):
    g=o.vertex_groups.new(name=P+'Head'); g.add(list(range(len(o.data.vertices))),1.0,'REPLACE'); finish(o)
def toon_tex(name,fn,shadow=0.68):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes):
        if n.type!='OUTPUT_MATERIAL': nt.nodes.remove(n)
    t=nt.nodes.new('ShaderNodeTexImage'); t.image=load_img(fn); toon_nodes(m,lambda nt:t.outputs[0],shadow); return m
def toon_col(name,col,shadow=0.6):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes):
        if n.type!='OUTPUT_MATERIAL': nt.nodes.remove(n)
    rgb=nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value=col; toon_nodes(m,lambda nt:rgb.outputs[0],shadow); return m
def toon_shiny(name,col,shadow=0.5,spec=0.9,rough=0.25,thr=0.55):
    m=toon_col(name,col,shadow); nt=m.node_tree
    out=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'][0]; em=out.inputs[0].links[0].from_node
    g=nt.nodes.new('ShaderNodeBsdfGlossy'); g.inputs['Roughness'].default_value=rough
    s=nt.nodes.new('ShaderNodeShaderToRGB'); nt.links.new(g.outputs[0],s.inputs[0])
    bw=nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(s.outputs[0],bw.inputs[0])
    r=nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.interpolation='CONSTANT'
    r.color_ramp.elements[0].color=(0,0,0,1); r.color_ramp.elements[1].position=thr; r.color_ramp.elements[1].color=(spec,spec,spec*0.95,1)
    nt.links.new(bw.outputs[0],r.inputs[0])
    add=nt.nodes.new('ShaderNodeMix'); add.data_type='RGBA'; add.blend_type='ADD'; add.inputs[0].default_value=1
    src=em.inputs[0].links[0].from_socket
    nt.links.new(src,add.inputs[6]); nt.links.new(r.outputs[0],add.inputs[7]); nt.links.new(add.outputs[2],em.inputs[0])
    return m
# ---------- body-dup gear (inherits shape keys + weights)
def dup_region(name, keepv, off, uv_fn=None, keep_keys=None, relax=4):
    me=bme.copy(); me.name=name; o=link(bpy.data.objects.new(name,me))
    for vg in body.vertex_groups: o.vertex_groups.new(name=vg.name)
    for a in [a.name for a in me.color_attributes]:
        try: me.color_attributes.remove(me.color_attributes[a])
        except Exception: pass
    oa=me.attributes.new('orig','INT','POINT'); oa.data.foreach_set('value',np.arange(N))
    bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if not all(keepv[v.index] for v in f.verts)],context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    # largest island only
    seen=set(); isl=[]
    for v in bm.verts:
        if v in seen: continue
        st=[v]; cur=[]; seen.add(v)
        while st:
            a=st.pop(); cur.append(a)
            for e in a.link_edges:
                b=e.other_vert(a)
                if b not in seen: seen.add(b); st.append(b)
        isl.append(cur)
    isl.sort(key=len,reverse=True)
    for c in isl[1:]:
        if len(c)<0.25*len(isl[0]): bmesh.ops.delete(bm,geom=c,context='VERTS')
    bm.to_mesh(me); bm.free()
    n=len(me.vertices); oi=np.zeros(n,dtype=int); me.attributes['orig'].data.foreach_get('value',oi)
    offv=(off(oi) if callable(off) else np.full(n,off))[:,None]*bnr[oi]
    # boundary relax
    bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bnd={v.index:[e.other_vert(v).index for e in v.link_edges if e.is_boundary] for v in bm.verts if v.is_boundary}; bm.free()
    P0=bco[oi]+offv; Q=P0.copy()
    for _ in range(relax):
        R=Q.copy()
        for i,nb in bnd.items():
            if len(nb)==2: R[i]=0.5*Q[i]+0.25*(Q[nb[0]]+Q[nb[1]])
        Q=R
    rel=Q-P0
    kb=me.shape_keys.key_blocks
    kb['Basis'].data.foreach_set('co',(P0+rel).ravel()); me.vertices.foreach_set('co',(P0+rel).ravel())
    for k in KEYS:
        d=kco[k][oi]-bco[oi]
        if (keep_keys is not None and k not in keep_keys) or np.abs(d).max()<1e-5:
            o.shape_key_remove(kb[k]); continue
        kb[k].data.foreach_set('co',(kco[k][oi]+offv+rel).ravel())
    me.attributes.remove(me.attributes['orig'])
    me.materials.clear()
    for p in me.polygons: p.use_smooth=True
    used=set(g.group for v in me.vertices for g in v.groups if g.weight>1e-4)
    for vg in [vg for vg in o.vertex_groups if vg.index not in used]: o.vertex_groups.remove(vg)
    if uv_fn:
        while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
        uv=me.uv_layers.new(name='UVMap'); co=np.array([v.co[:] for v in me.vertices])
        for p in me.polygons:
            uvs=[uv_fn(co[me.loops[li].vertex_index]) for li in p.loop_indices]
            us=[x for x,_ in uvs]
            if max(us)-min(us)>0.5: uvs=[(x+1 if x<0.5 else x,y) for x,y in uvs]
            for li,(x,y) in zip(p.loop_indices,uvs): uv.data[li].uv=(x,y)
    finish(o); return o
x,y,z=bco[:,0],bco[:,1],bco[:,2]; ax=np.abs(x)
# ---------------- TANK (v2 cut, refit over v3 muscles: deeper armholes for big lats/delts)
armlim=0.060+np.maximum(0,0.56-z)*0.6
keep=(z>0.425)&(z<0.668)&(armw<0.30)&(headw<0.5)
keep&=~((z>0.52)&(ax>armlim))
keep&=~((y<0.0)&(z>0.592+(ax/0.036)**2*0.045))
keep&=~((y>=0.0)&(z>0.632+(ax/0.036)**2*0.03))
keep&=~((ax<0.012)&(z>0.655))
tank=dup_region('Zeek_Tank',keep,0.005,lambda c:((0.5*(c[0]+0.11)/0.22) if c[1]<0 else (1-0.5*(c[0]+0.11)/0.22),(c[2]-0.41)/0.27),
    keep_keys=['chest','back_lats','shoulders','abs_core','arms_biceps','arms_triceps','noodle'],relax=8)
tank.data.materials.append(toon_tex('Zeek_Tank_Toon','zeek_v2_tank.png'))
s=tank.modifiers.new('Thickness','SOLIDIFY'); s.thickness=0.0025; s.offset=-1; s.use_even_offset=False
add_outline(tank,0.003)
# ---------------- WRIST WRAPS
def wrap_keep(S):
    fa=rig.data.bones[P+S+'ForeArm']; a=np.array(fa.head_local); b=np.array(fa.tail_local); d=b-a; L=np.linalg.norm(d); d/=L
    t=((bco-a)@d)/L; r=np.linalg.norm((bco-a)-np.outer(t*L,d),axis=1)
    return (t>0.70)&(t<1.03)&(r<0.045)&(np.sign(bco[:,0])==(1 if S=='Left' else -1)),a,d,L
wraps=[]
for S in ('Left','Right'):
    k,a,d,L=wrap_keep(S)
    up=np.cross(d,[0,1,0]); up/=np.linalg.norm(up); sd=np.cross(d,up)
    def uvf(c,a=a,d=d,L=L,up=up,sd=sd):
        q=np.array(c)-a; t=(q@d)/L; return ((math.atan2(q@up,q@sd)/(2*math.pi))%1,(t-0.70)/0.33)
    o=dup_region(f'Zeek_Wrap_{S}',k,0.0045,uvf,keep_keys=['arms_biceps','arms_triceps','noodle'],relax=3)
    o.data.materials.append(toon_tex('Zeek_Wraps_Toon' if S=='Left' else 'Zeek_Wraps_Toon_R','zeek_v3_wraps.png'))
    sm=o.modifiers.new('Thickness','SOLIDIFY'); sm.thickness=0.002; sm.offset=-1
    add_outline(o,0.0025); wraps.append(o)
# ---------------- HEAD helpers
HC=Vector((0.001,0.0066,0.7641)); RAD=(0.1088,0.1088,0.107)
bmH=bmesh.new(); bmH.from_mesh(bme); bmH.verts.ensure_lookup_table()
hv=np.where((antw<0.05)&(np.linalg.norm(bco-np.array(HC),axis=1)<0.14)&(z>0.69))[0]; hs=set(hv.tolist())
bmesh.ops.delete(bmH,geom=[f for f in bmH.faces if not all(v.index in hs for v in f.verts)],context='FACES')
bvhH=BVHTree.FromBMesh(bmH)
def surf(d):
    d=Vector(d).normalized(); h=bvhH.ray_cast(HC,d)
    if h[0] is None:
        h=bvhH.find_nearest(HC+Vector((d.x*RAD[0],d.y*RAD[1],d.z*RAD[2])))
    p,n=h[0],h[1]
    if n.dot(d)<0: n=-n
    return p,n
def dirf(phi,th): return Vector((math.sin(phi)*math.sin(th),-math.sin(phi)*math.cos(th),math.cos(phi)))
def phi_at_z(th,zt):
    lo,hi=0.05,2.4
    for _ in range(28):
        mid=(lo+hi)/2
        if surf(dirf(mid,th))[0].z>zt: lo=mid
        else: hi=mid
    return lo
ANT=[]
for S in 'LR':
    b1=rig.data.bones[f'Antenna_{S}_01']; b2=rig.data.bones[f'Antenna_{S}_02']
    ANT.append((Vector(b1.head_local),Vector(b2.tail_local)))
def ant_dist(p):
    best=9
    for a,b in ANT:
        ab=b-a; t=max(-0.3,min(1,(p-a).dot(ab)/ab.length_squared)); best=min(best,(p-(a+ab*t)).length)
    return best
def grid_obj(name,grid,uvs,close=True,cap=None,cap_uv=None,mat_idx=None):
    bm=bmesh.new(); uvl=bm.loops.layers.uv.new('UVMap')
    V=[[bm.verts.new(p) for p in col] for col in grid]
    nc=len(V); nr=len(V[0])
    rng=range(nc) if close else range(nc-1)
    for i in rng:
        i2=(i+1)%nc
        for j in range(nr-1):
            f=bm.faces.new((V[i][j],V[i2][j],V[i2][j+1],V[i][j+1]))
            u0=uvs[i][j][0]; u1=uvs[i2][j][0] if i2>i else 1.0
            for lp,(uu,vv) in zip(f.loops,[(u0,uvs[i][j][1]),(u1,uvs[i2][j][1]),(u1,uvs[i2][j+1][1]),(u0,uvs[i][j+1][1])]): lp[uvl].uv=(uu,vv)
            if mat_idx: f.material_index=mat_idx(i,j)
    if cap is not None:
        c=bm.verts.new(cap)
        for i in rng:
            i2=(i+1)%nc; f=bm.faces.new((V[i][-1],V[i2][-1],c))
            u0=uvs[i][-1][0]; u1=uvs[i2][-1][0] if i2>i else 1.0
            for lp,uv_ in zip(f.loops,[(u0,1),(u1,1),((u0+u1)/2,1)]): lp[uvl].uv=uv_
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth=True
    return link(bpy.data.objects.new(name,me))
# ---------------- SLOUCHY BEANIE with cuff + antenna holes
NT=96
BC=Vector((0.0,0.040,0.825)); BR=(0.108,0.118,0.080); BT=Matrix.Rotation(math.radians(-28),3,'X')
def bag_r(d):
    Ri=BT.inverted(); o=Ri@(HC-BC); dd=Ri@d
    o=Vector((o.x/BR[0],o.y/BR[1],o.z/BR[2])); dd=Vector((dd.x/BR[0],dd.y/BR[1],dd.z/BR[2]))
    A=dd.dot(dd); B=2*o.dot(dd); C=o.dot(o)-1; disc=B*B-4*A*C
    if disc<0: return 0.0
    return max(0.0,(-B+math.sqrt(disc))/(2*A))
def zb(th): return 0.797+0.008*math.cos(th)
grid=[]; uvs=[]
CUFF=[0.0,0.004,0.016,0.028,0.038]
for i in range(NT):
    th=2*math.pi*i/NT+math.pi; col=[]; cu=[]
    u=(i/NT)
    # lip (fold under)
    for j,dz in enumerate(CUFF):
        ph=phi_at_z(th,zb(th)+dz); p,n=surf(dirf(ph,th))
        off=0.006 if j==0 else 0.015
        if j==len(CUFF)-1: off=0.013
        col.append(p+n*off); cu.append((u,0.32*dz/0.038))
    ph0=phi_at_z(th,zb(th)+0.044)
    NRD=16
    for j in range(1,NRD+1):
        t=j/NRD; ph=max(ph0*(1-t),0.03); d=dirf(ph,th); p,n=surf(d)
        rh=(p-HC).length+0.010
        rb=bag_r(d)
        k=0.018; rr=0.5*(rh+rb+math.sqrt((rh-rb)**2+k*k))   # smooth max
        w=min(1,t/0.25)
        r=rh*(1-w)+rr*w
        col.append(HC+d*r); cu.append((u,0.34+0.66*t))
    grid.append(col); uvs.append(cu)
# smooth dome columns lightly around
G=np.array([[c[:] for c in col] for col in grid])
for _ in range(1): G[:,5:]=0.5*G[:,5:]+0.25*(np.roll(G[:,5:],1,0)+np.roll(G[:,5:],-1,0))
grid=[[Vector(G[i,j]) for j in range(G.shape[1])] for i in range(NT)]
top=Vector(G[:,-1].mean(0))+Vector((0,0.0,0.002))
bean=grid_obj('Zeek_Beanie',grid,uvs,cap=top)
# antenna holes
bm=bmesh.new(); bm.from_mesh(bean.data)
bvhB=BVHTree.FromBMesh(bm); hits=[]
for a_,b_ in ANT:
    h=bvhB.ray_cast(a_,(b_-a_).normalized())
    if h[0] is not None: hits.append(h[0])
print('antenna hits',hits)
kill=[f for f in bm.faces if min((f.calc_center_median()-hp).length for hp in hits)<0.0125] if hits else []
bmesh.ops.delete(bm,geom=kill,context='FACES'); bm.to_mesh(bean.data); bm.free()
print('beanie hole faces',len(kill))
bean.data.materials.append(toon_tex('Zeek_Beanie_Toon','zeek_v3_beanie.png'))
head_only(bean)
s=bean.modifiers.new('Thickness','SOLIDIFY'); s.thickness=0.003; s.offset=-1; s.use_rim=True
add_outline(bean,0.003)
# ---------------- HEADBAND
grid=[]; uvs=[]
for i in range(NT):
    th=2*math.pi*i/NT; col=[]; cu=[]
    for j,(dz,off) in enumerate([(0,0.003),(0.004,0.0065),(0.014,0.008),(0.024,0.0065),(0.028,0.003)]):
        zz=0.800+0.010*math.cos(th)+dz
        p,n=surf(dirf(phi_at_z(th,zz),th)); col.append(p+n*off); cu.append((i/NT,dz/0.028))
    grid.append(col); uvs.append(cu)
hb=grid_obj('Zeek_Headband',grid,uvs)
hb.data.materials.append(toon_tex('Zeek_Headband_Toon','zeek_v3_headband.png',0.75)); head_only(hb); add_outline(hb,0.0025)
# ---------------- SHIELD SUNGLASSES
NA=84; A0=math.radians(100)
def ell(az,zz,off):
    lat=math.asin(max(-0.99,min(0.99,(zz-HC.z)/RAD[2])))
    d=Vector((RAD[0]*math.cos(lat)*math.sin(az),-RAD[1]*math.cos(lat)*math.cos(az),RAD[2]*math.sin(lat)))
    n=Vector((d.x/RAD[0]**2,d.y/RAD[1]**2,d.z/RAD[2]**2)).normalized()
    return HC+d+n*off
grid=[]; uvs=[]; LENS=math.radians(64)
for i in range(NA+1):
    az=-A0+2*A0*i/NA; ad=abs(math.degrees(az)); col=[]; cu=[]
    if abs(az)<=LENS:
        top=0.795+0.003*math.cos(az*2); bot=0.733+0.028*math.exp(-(ad/11)**2)+0.022*(ad/64)**4
        off=0.013-0.004*(ad/64)**2
    else:
        f=(abs(az)-LENS)/(A0-LENS); top=0.795-0.004*f; bot=0.787-0.002*f; off=0.009*(1-f)+0.003
    for j in range(7):
        t=j/6; col.append(ell(az,bot+(top-bot)*t,off)); cu.append((i/NA,t))
    grid.append(col); uvs.append(cu)
def gl_mat(i,j):
    az=-A0+2*A0*(i+0.5)/NA
    return 1 if (abs(az)<=LENS and j<5) else 0
gl=grid_obj('Zeek_Sunglasses',grid,uvs,close=False,mat_idx=gl_mat)
gl.data.materials.append(toon_shiny('Zeek_Shades_Frame',(0.04,0.04,0.05,1),0.6,0.5,0.3,0.6))
lm=toon_shiny('Zeek_Shades_Lens',(0.10,0.05,0.22,1),0.7,0.9,0.15,0.45)
# lens gradient (top darker purple -> bottom teal tint) via UV v
nt=lm.node_tree; uvn=nt.nodes.new('ShaderNodeUVMap'); sp=nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uvn.outputs[0],sp.inputs[0])
cr=nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color=(0.05,0.35,0.40,1); cr.color_ramp.elements[1].color=(0.12,0.03,0.25,1)
nt.links.new(sp.outputs[1],cr.inputs[0])
mulnode=[n for n in nt.nodes if n.type=='MIX' and n.blend_type=='MULTIPLY'][0]; nt.links.new(cr.outputs[0],mulnode.inputs[6])
gl.data.materials.append(lm)
head_only(gl)
s=gl.modifiers.new('Thickness','SOLIDIFY'); s.thickness=0.0025; s.offset=1
add_outline(gl,0.0025)
# ---------------- CUBAN LINK CHAIN
bmB=bmesh.new(); bmB.from_mesh(bme); bvh=BVHTree.FromBMesh(bmB)
kd=KDTree(N)
for i,c in enumerate(bco): kd.insert(c,i)
kd.balance()
path=[]
for j in range(160):
    th=2*math.pi*j/160; d=Vector((math.sin(th),-math.cos(th),0)); fr=((1+math.cos(th))/2)**2.0
    zz=0.655-0.068*fr; o=Vector((0,0.006,zz))+d*0.16
    hit=bvh.ray_cast(o,-d)
    if hit[0] is None: continue
    path.append(hit[0]+hit[1]*0.0055)
pts=np.array([p[:] for p in path])
for _ in range(24): pts=0.5*pts+0.25*(np.roll(pts,1,0)+np.roll(pts,-1,0))
seg=np.linalg.norm(np.roll(pts,-1,0)-pts,axis=1); Ltot=seg.sum(); cum=np.concatenate([[0],np.cumsum(seg)])
spacing=0.0088; nl=int(Ltot/spacing); nl-=nl%2
bm=bmesh.new(); link_of=[]
def cuban(center,tan,nrm,tilt):
    Rx,Ry,r=0.0085,0.0058,0.0032; S_,s_=12,6
    t=Vector(tan).normalized(); n=Vector(nrm).normalized(); side=t.cross(n).normalized(); n=side.cross(t).normalized()
    q=Matrix.Rotation(tilt,3,t); side2=q@side; n2=q@n
    rings=[]
    for i in range(S_):
        a=2*math.pi*i/S_
        c=Vector(center)+t*(Rx*math.cos(a))+side2*(Ry*math.sin(a))
        rad=(t*math.cos(a)*Ry+side2*math.sin(a)*Rx).normalized()
        ring=[bm.verts.new(c+rad*(r*math.cos(b)*1.15)+n2*(r*math.sin(b)*0.62)) for b in [2*math.pi*k/s_ for k in range(s_)]]
        rings.append(ring)
    for i in range(S_):
        for k in range(s_):
            bm.faces.new((rings[i][k],rings[(i+1)%S_][k],rings[(i+1)%S_][(k+1)%s_],rings[i][(k+1)%s_]))
    return [v for rg in rings for v in rg]
for li in range(nl):
    sd=li*Ltot/nl; j=min(max(np.searchsorted(cum,sd)-1,0),len(pts)-1)
    a=pts[j]; b=pts[(j+1)%len(pts)]; f=(sd-cum[j])/max(seg[j],1e-9); c=a+(b-a)*f
    _,nidx,_=kd.find(c)
    vs=cuban(c,b-a,bnr[nidx],math.radians(32 if li%2 else -32))
    link_of.append((vs,nidx))
# pendant: chunky dumbbell
front_i=int(np.argmin(pts[:,1])); pc=Vector(pts[front_i])+Vector((0,-0.008,-0.02))
_,pidx,_=kd.find(pc)
def cyl(c,axis,r,h,seg=12):
    axv=Vector(axis).normalized(); u=axv.orthogonal().normalized(); w=axv.cross(u); tp=[];bt=[]
    for i in range(seg):
        a=2*math.pi*i/seg; off=(u*math.cos(a)+w*math.sin(a))*r
        bt.append(bm.verts.new(c+off-axv*h/2)); tp.append(bm.verts.new(c+off+axv*h/2))
    for i in range(seg): bm.faces.new((bt[i],bt[(i+1)%seg],tp[(i+1)%seg],tp[i]))
    bm.faces.new(tp); bm.faces.new(bt[::-1]); return tp+bt
pv=cyl(pc,(1,0,0),0.0018,0.026)
for sx in (-1,1): pv+=cyl(pc+Vector((sx*0.012,0,0)),(1,0,0),0.0065,0.006,14)
pv+=cyl(pc+Vector((0,0,0.009)),(0,0,1),0.0012,0.012,8)
link_of.append((pv,pidx))
cme=bpy.data.meshes.new('Zeek_GoldChain'); bm.to_mesh(cme); bm.free()
chain=link(bpy.data.objects.new('Zeek_GoldChain',cme))
vmap=np.zeros(len(cme.vertices),dtype=int); c0=0
for vs,nidx in link_of: vmap[c0:c0+len(vs)]=nidx; c0+=len(vs)
for vg in body.vertex_groups: chain.vertex_groups.new(name=vg.name)
for i,bi in enumerate(vmap):
    for g in bme.vertices[bi].groups: chain.vertex_groups[g.group].add([i],g.weight,'ADD')
used=set(g.group for v in cme.vertices for g in v.groups if g.weight>1e-4)
for vg in [vg for vg in chain.vertex_groups if vg.index not in used]: chain.vertex_groups.remove(vg)
chain.shape_key_add(name='Basis'); cc=np.array([v.co[:] for v in cme.vertices])
# per-link rigid offset (avoid link distortion): mean delta of the link's anchor neighbourhood
for k in KEYS:
    d=kco[k][vmap]-bco[vmap]
    if np.abs(d).max()<1e-5: continue
    # outward push so chain stays on top of grown muscles
    sk=chain.shape_key_add(name=k); sk.data.foreach_set('co',(cc+d*1.05).ravel())
cme.materials.append(toon_shiny('Zeek_Gold_Toon',(0.95,0.62,0.10,1),0.5,0.35,0.25,0.85))
for p in cme.polygons: p.use_smooth=True
finish(chain); add_outline(chain,0.0012,False)
# default visibility + tags for app toggles
for o,vis in ((tank,True),(bean,True),(chain,True),(hb,False),(gl,False),(wraps[0],False),(wraps[1],False)):
    o['accessory']=True; o.hide_render=o.hide_viewport=not vis
def tris(o): return sum(len(p.vertices)-2 for p in o.data.polygons)
for o in (tank,bean,chain,hb,gl,*wraps):
    print('GEAR',o.name,'tris',tris(o),'keys',[k.name for k in o.data.shape_keys.key_blocks[1:]] if o.data.shape_keys else [])
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v3work/05_gear.blend')

import bpy, bmesh, numpy as np, math, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P='mixamorig:'
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/04_legdef.blend')
body=bpy.data.objects['Zeek_Body']; rig=bpy.data.objects['Zeek_Rig']; bme=body.data
# ---- clean antenna weights: only the stalks, ramp at the base, scalp -> Head
import json
J=json.load(open('/workspace/gym-app/3d/v2work/joints.json'))
def seg_dist(p,a,b):
    ab=b-a; t=np.clip(((p-a)@ab)/(ab@ab),0,1); return np.linalg.norm(p-(a+np.outer(t,ab)),axis=1)
cof=np.array([v.co[:] for v in bme.vertices])
hidx=body.vertex_groups[P+'Head'].index
moved=0
for S in 'LR':
    names=[f'Antenna_{S}_0{i}' for i in (1,2,3)]
    pts=[np.array(J[names[0]][0])]+[np.array(J[n][1]) for n in names]
    tip=pts[-1]+(pts[-1]-pts[-2])*0.6
    dmin=np.min([seg_dist(cof,pts[i],pts[i+1] if i<2 else tip) for i in range(3)],axis=0)
    a0,a1=pts[0],pts[1]; ax_=(a1-a0)/np.linalg.norm(a1-a0); tb=(cof-a0)@ax_
    keepf=np.clip((tb+0.004)/0.022,0,1)*(dmin<0.03)
    gidx=[body.vertex_groups[n].index for n in names]
    for v in bme.vertices:
        tot=0
        for g in v.groups:
            if g.group in gidx:
                nw=g.weight*keepf[v.index]; tot+=g.weight-nw; g.weight=nw
        if tot>1e-4:
            body.vertex_groups[P+'Head'].add([v.index],tot,'ADD'); moved+=1
print('ANTFIX moved',moved)
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
armw=wsum(LR('Arm')+LR('ForeArm')+LR('Hand')); headw=wsum([P+'Head',P+'Neck']); antw=wsum([f'Antenna_{s}_0{i}' for s in 'LR' for i in (1,2,3)])
def link(o):
    bpy.context.scene.collection.objects.link(o); return o
def dup(name):
    me=bme.copy(); me.name=name
    o=bpy.data.objects.new(name,me); link(o); o.matrix_world=body.matrix_world
    for a in list(me.color_attributes): me.color_attributes.remove(a)
    oi=me.attributes.new('orig','INT','POINT'); oi.data.foreach_set('value',np.arange(N))
    for vg in body.vertex_groups: o.vertex_groups.new(name=vg.name)
    # copy weights
    for v in bme.vertices:
        for g in v.groups: o.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
    return o
def keep_faces(o, keepv_fn):
    me=o.data; bm=bmesh.new(); bm.from_mesh(me)
    orig=bm.verts.layers.int['orig']
    kill=[f for f in bm.faces if not all(keepv_fn(v[orig]) for v in f.verts)]
    bmesh.ops.delete(bm,geom=kill,context='FACES')
    # largest island only
    bm.verts.ensure_lookup_table(); seen=set(); islands=[]
    for v in bm.verts:
        if v in seen: continue
        st=[v]; isl=[]; seen.add(v)
        while st:
            a=st.pop(); isl.append(a)
            for e in a.link_edges:
                b=e.other_vert(a)
                if b not in seen: seen.add(b); st.append(b)
        islands.append(isl)
    islands.sort(key=len,reverse=True)
    for isl in islands[1:]: bmesh.ops.delete(bm,geom=isl,context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()
def offset_and_relax(o, off_fn, relax_iters=6, keep_keys=None):
    me=o.data; n=len(me.vertices)
    oi=np.zeros(n,dtype=int); me.attributes['orig'].data.foreach_get('value',oi)
    nr=bnr[oi]; off=off_fn(oi)[:,None]*nr
    # boundary relax delta (computed on basis, applied to all)
    bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bnd={v.index:[e.other_vert(v).index for e in v.link_edges if e.is_boundary] for v in bm.verts if v.is_boundary}
    bm.free()
    P0=bco[oi]+off; Q=P0.copy()
    for _ in range(relax_iters):
        R=Q.copy()
        for i,nb in bnd.items():
            if len(nb)==2: R[i]=0.5*Q[i]+0.25*(Q[nb[0]]+Q[nb[1]])
        Q=R
    rel=Q-P0
    kb=me.shape_keys.key_blocks
    kb['Basis'].data.foreach_set('co',(P0+rel).ravel()); me.vertices.foreach_set('co',(P0+rel).ravel())
    for k in KEYS:
        d=kco[k][oi]-bco[oi]
        if keep_keys is not None and (k not in keep_keys or np.abs(d).max()<1e-5):
            o.shape_key_remove(kb[k]); continue
        kb[k].data.foreach_set('co',(kco[k][oi]+off+rel).ravel())
    me.update()
    return oi
def prune_groups(o):
    me=o.data; used=set(g.group for v in me.vertices for g in v.groups if g.weight>1e-4)
    names=[vg.name for vg in o.vertex_groups if vg.index not in used]
    for n in names: o.vertex_groups.remove(o.vertex_groups[n])
def finish(o, rig):
    o.parent=rig; o.matrix_parent_inverse=rig.matrix_world.inverted()
    m=o.modifiers.new('Armature','ARMATURE'); m.object=rig
def set_uv(o,name,fn):
    me=o.data
    while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
    uv=me.uv_layers.new(name=name)
    co=np.array([v.co[:] for v in me.vertices])
    for p in me.polygons:
        uvs=[fn(co[me.loops[li].vertex_index],p) for li in p.loop_indices]
        us=[u for u,_ in uvs]
        if max(us)-min(us)>0.5: uvs=[(u+1 if u<0.5 else u,v) for u,v in uvs]
        for li,(u,v) in zip(p.loop_indices,uvs): uv.data[li].uv=(u,v)
def mat_tex(name,path,cull=False):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree
    pb=nt.nodes['Principled BSDF']; t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(path); t.image.pack()
    nt.links.new(t.outputs[0],pb.inputs['Base Color']); pb.inputs['Roughness'].default_value=0.85
    m.use_backface_culling=cull
    return m
# ---------------- TANK
x,y,z=bco[:,0],bco[:,1],bco[:,2]; ax=np.abs(x)
armlim=0.064+np.maximum(0,0.56-z)*0.6
keep=(z>0.425)&(z<0.668)&(armw<0.35)&(headw<0.5)
keep&=~((z>0.53)&(ax>armlim))
keep&=~((y<0.0)&(z>0.592+(ax/0.036)**2*0.045))
keep&=~((y>=0.0)&(z>0.632+(ax/0.036)**2*0.03))
keep&=~((ax<0.012)&(z>0.655))
tank=dup('Zeek_Tank'); keep_faces(tank,lambda i:keep[i])
oi=offset_and_relax(tank,lambda oi:np.full(len(oi),0.0045),8,keep_keys=['chest','back_lats','shoulders','abs_core','arms_biceps','arms_triceps','noodle'])
def tank_uv(c,p):
    u=0.5*(c[0]+0.11)/0.22; v=(c[2]-0.41)/0.27
    return (u if p.normal.y<0 else 0.5+(1-(u*2))*0.5, v)
set_uv(tank,'UVMap',tank_uv)
tank.data.materials.clear(); tank.data.materials.append(mat_tex('Zeek_Tank_Toon','/workspace/gym-app/3d/tex/zeek_v2_tank.png'))
prune_groups(tank); finish(tank,rig)
s=tank.modifiers.new('Thickness','SOLIDIFY'); s.thickness=0.0025; s.offset=-1; s.use_even_offset=True
# ---------------- BEANIE (raycast dome from head centre, clean brim; antennae poke through)
bmB0=bmesh.new(); bmB0.from_mesh(bme)
bmH=bmesh.new(); bmH.from_mesh(bme)
# keep only head-weighted faces (no antennae) for the ray target
hv=set(i for i in range(N) if headw[i]>0.5 and antw[i]<0.2)
bmesh.ops.delete(bmH,geom=[f for f in bmH.faces if not all(v.index in hv for v in f.verts)],context='FACES')
bvhH=BVHTree.FromBMesh(bmB0)
HC=Vector((0,0.004,0.79))
def surf(d):
    h=bvhH.ray_cast(HC,d)
    if h[0] is None: return (HC+d*0.09,d)
    n=h[1] if h[1].dot(d)>0 else -h[1]
    return (h[0],n)
def zc(th):  # brim height: lower at back (+y)
    return 0.771+0.011*math.cos(th)  # front (th=0) higher, back lower
NT,NR=72,18
def dirf(phi,th): return Vector((math.sin(phi)*math.sin(th),-math.sin(phi)*math.cos(th),math.cos(phi)))
rows=[]
for i in range(NT):
    th=2*math.pi*i/NT
    lo,hi=0.2,2.2
    for _ in range(30):
        mid=(lo+hi)/2
        if surf(dirf(mid,th))[0].z>zc(th): lo=mid
        else: hi=mid
    rows.append(lo)
bmb=bmesh.new(); grid=[]
top_p,top_n=surf(Vector((0,0,1))); top=bmb.verts.new(top_p+top_n*0.010)
for i in range(NT):
    th=2*math.pi*i/NT; col=[]
    for j in range(1,NR+1):
        t=j/NR; phi=t*rows[i]; p,n=surf(dirf(phi,th))
        off=0.010+ (0.006 if t>0.80 else 0.0) + (0.003 if 0.78<t<=0.80 else 0)
        col.append(bmb.verts.new(p+n*off))
    # lip: fold back under
    p,n=surf(dirf(rows[i]*1.0,th)); col.append(bmb.verts.new(p+n*0.004))
    grid.append(col)
R=len(grid[0])
for i in range(NT):
    a_,b_=grid[i],grid[(i+1)%NT]
    bmb.faces.new((top,b_[0],a_[0]))
    for j in range(R-1): bmb.faces.new((a_[j],b_[j],b_[j+1],a_[j+1]))
bmesh.ops.recalc_face_normals(bmb,faces=bmb.faces[:])
bmesh.ops.triangulate(bmb,faces=bmb.faces[:])
# smooth the dome lightly
for _ in range(3): bmesh.ops.smooth_vert(bmb,verts=[v for v in bmb.verts if not v.is_boundary],factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
beme=bpy.data.meshes.new('Zeek_Beanie'); bmb.to_mesh(beme); bmb.free()
bean=bpy.data.objects.new('Zeek_Beanie',beme); link(bean)
vh=bean.vertex_groups.new(name=P+'Head'); vh.add(list(range(len(beme.vertices))),1.0,'REPLACE')
def bean_uv(c,p):
    d=Vector(c)-HC
    return (math.atan2(d.x,-d.y)/(2*math.pi)+0.5, max(0.0,(c[2]-0.756)/0.13))
set_uv(bean,'UVMap',bean_uv)
bean.data.materials.append(mat_tex('Zeek_Beanie_Toon','/workspace/gym-app/3d/tex/zeek_v2_beanie.png'))
finish(bean,rig)
s=bean.modifiers.new('Thickness','SOLIDIFY'); s.thickness=0.003; s.offset=-1
# ---------------- GOLD CHAIN
bmB=bmesh.new(); bmB.from_mesh(bme); bvh=BVHTree.FromBMesh(bmB)
kd=KDTree(N)
for i,c in enumerate(bco): kd.insert(c,i)
kd.balance()
path=[]
M=120
for j in range(M):
    th=2*math.pi*j/M
    d=Vector((math.sin(th),-math.cos(th),0))
    fr=((1+math.cos(th))/2)**2.2
    zz=0.652-0.062*fr
    o=Vector((0,0.004,zz))+d*0.15
    hit=bvh.ray_cast(o,-d)
    if hit[0] is None: continue
    path.append(hit[0]+hit[1]*0.0035)
# smooth path
pts=np.array([p[:] for p in path])
for _ in range(20): pts=0.5*pts+0.25*(np.roll(pts,1,0)+np.roll(pts,-1,0))
seg=np.linalg.norm(np.roll(pts,-1,0)-pts,axis=1); L=seg.sum(); cum=np.concatenate([[0],np.cumsum(seg)])
spacing=0.0085; nl=int(L/spacing)
bm=bmesh.new()
def torus(center,tan,nrm,flip):
    R,r,S,s=0.0056,0.0016,8,4
    t=Vector(tan).normalized(); n=Vector(nrm).normalized()
    side=t.cross(n).normalized()
    up=side if flip else n
    rings=[]
    for i in range(S):
        a=2*math.pi*i/S
        c=Vector(center)+t*(R*math.cos(a)*1.25)+up*(R*math.sin(a)*0.75)
        rad=(t*math.cos(a)+up*math.sin(a)).normalized(); ax2=t.cross(up).normalized()
        ring=[]
        for k in range(s):
            b=2*math.pi*k/s
            ring.append(bm.verts.new(c+rad*(r*math.cos(b))+ax2*(r*math.sin(b))))
        rings.append(ring)
    for i in range(S):
        for k in range(s):
            bm.faces.new((rings[i][k],rings[(i+1)%S][k],rings[(i+1)%S][(k+1)%s],rings[i][(k+1)%s]))
    return [v for rg in rings for v in rg]
link_of=[]
for li in range(nl):
    sd=li*L/nl; j=np.searchsorted(cum,sd)-1; j=min(max(j,0),len(pts)-1)
    a=pts[j]; b=pts[(j+1)%len(pts)]; f=(sd-cum[j])/max(seg[j],1e-9); c=a+(b-a)*f
    _,nidx,_=kd.find(c); nn=bnr[nidx]
    vs=torus(c,b-a,nn,li%2==1)
    link_of.append((vs,nidx))
# pendant: tiny dumbbell at front-most lowest point
front_i=int(np.argmin(pts[:,1]-0*pts[:,2])); pc=Vector(pts[front_i])+Vector((0,-0.004,-0.011))
_,pidx,_=kd.find(pc)
def cyl(c,axis,r,h,seg=10):
    ax=Vector(axis).normalized(); u=ax.orthogonal().normalized(); w=ax.cross(u)
    top=[];bot=[]
    for i in range(seg):
        a=2*math.pi*i/seg; off=(u*math.cos(a)+w*math.sin(a))*r
        bot.append(bm.verts.new(c+off-ax*h/2)); top.append(bm.verts.new(c+off+ax*h/2))
    for i in range(seg): bm.faces.new((bot[i],bot[(i+1)%seg],top[(i+1)%seg],top[i]))
    bm.faces.new(top); bm.faces.new(bot[::-1]); return top+bot
pv=cyl(pc,(1,0,0),0.0012,0.018,8)
for sx in (-1,1):
    pv+=cyl(pc+Vector((sx*0.0085,0,0)),(1,0,0),0.0042,0.004,12)
pv+=cyl(pc+Vector((0,0,0.006)),(0,0,1),0.0007,0.008,6)
link_of.append((pv,pidx))
cme=bpy.data.meshes.new('Zeek_GoldChain'); bm.to_mesh(cme); bm.free()
chain=bpy.data.objects.new('Zeek_GoldChain',cme); link(chain)
vmap=np.zeros(len(cme.vertices),dtype=int); c0=0
for vs,nidx in link_of:
    vmap[c0:c0+len(vs)]=nidx; c0+=len(vs)
# weights
for vg in body.vertex_groups: chain.vertex_groups.new(name=vg.name)
for i,bi in enumerate(vmap):
    for g in bme.vertices[bi].groups: chain.vertex_groups[g.group].add([i],g.weight,'ADD')
prune_groups(chain)
chain.shape_key_add(name='Basis')
cc=np.array([v.co[:] for v in cme.vertices])
for k in ['chest','back_lats','shoulders','abs_core','noodle']:
    d=kco[k][vmap]-bco[vmap]
    if np.abs(d).max()<1e-5: continue
    sk=chain.shape_key_add(name=k); sk.data.foreach_set('co',(cc+d).ravel())
gm=bpy.data.materials.new('Zeek_Gold_Toon'); gm.use_nodes=True
pb=gm.node_tree.nodes['Principled BSDF']; pb.inputs['Base Color'].default_value=(0.95,0.68,0.16,1); pb.inputs['Metallic'].default_value=1.0; pb.inputs['Roughness'].default_value=0.3
cme.materials.append(gm)
for p in cme.polygons: p.use_smooth=True
finish(chain,rig)
for o in (tank,bean):
    for p in o.data.polygons: p.use_smooth=True
    if 'orig' in o.data.attributes: o.data.attributes.remove(o.data.attributes['orig'])
def tris(o): return sum(len(p.vertices)-2 for p in o.data.polygons)
for o in (body,tank,bean,chain):
    print('GEAR',o.name,'tris',tris(o),'keys',[k.name for k in o.data.shape_keys.key_blocks[1:]] if o.data.shape_keys else [],'groups',len(o.vertex_groups))
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v2work/05_gear.blend')

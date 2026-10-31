# v3: re-dome the face (remove sculpted lids/muzzle), bake masks + vein/groove detail + normal
import bpy, numpy as np, math
P='mixamorig:'
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v3work/02_shapes.blend')
body=bpy.data.objects['Zeek_Body']; me=body.data; N=len(me.vertices)
co=np.zeros(N*3); me.vertices.foreach_get('co',co); co=co.reshape(N,3)
nr=np.zeros(N*3); me.vertices.foreach_get('normal',nr); nr=nr.reshape(N,3)
gi=body.vertex_groups[P+'Head'].index
hw=np.zeros(N)
for v in me.vertices:
    for g in v.groups:
        if g.group==gi: hw[v.index]=g.weight
def ss(e0,e1,t): t=np.clip((t-e0)/(e1-e0),0,1); return t*t*(3-2*t)
x,y,z=co.T
head=(hw>0.95)&(z>0.70)
ell=((x/0.115)**2+((z-0.762)/0.05)**2)
facem=np.clip(1-ss(0.75,1.2,ell),0,1)*ss(-0.0,-0.25,-(-nr[:,1]))*0+np.clip(1-ss(0.75,1.2,ell),0,1)*np.clip((-nr[:,1]-0.05)/0.3,0,1)
facem*=(hw>0.9)
fit=head&(facem<0.01)&(y<0.03)
X=co[fit]; A=np.stack([X[:,0]**2,X[:,1]**2,X[:,2]**2,X[:,0],X[:,1],X[:,2]],1)
coef,*_=np.linalg.lstsq(A,np.ones(len(X)),rcond=None)
a,b,c,d,e,f=coef; cen=np.array([-d/(2*a),-e/(2*b),-f/(2*c)])
k=1+d*d/(4*a)+e*e/(4*b)+f*f/(4*c); rad=np.sqrt(k/np.array([a,b,c]))
print('ELLIPSOID',cen.round(4),rad.round(4))
# project face verts radially onto ellipsoid
dv=co-cen; s=1/np.sqrt(((dv/rad)**2).sum(1))
proj=cen+dv*s[:,None]
ellB=((x/0.118)**2+((z-0.758)/0.056)**2)
facem=(1-ss(0.85,1.25,ellB))*(y<cen[1]-0.01)*(hw>0.9)
delta=(proj-co)*facem[:,None]
# smooth delta for continuity
E=np.zeros(len(me.edges)*2,dtype=int); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
deg=np.bincount(E.ravel(),minlength=N).astype(float)
raw=delta.copy()
for _ in range(3):
    acc=np.zeros_like(delta); np.add.at(acc,E[:,0],delta[E[:,1]]); np.add.at(acc,E[:,1],delta[E[:,0]])
    delta=delta*0.5+0.5*acc/np.maximum(deg,1)[:,None]
core=facem>0.97
delta[core]=raw[core]
print('FACE verts moved',int((np.linalg.norm(delta,axis=1)>2e-4).sum()),'max %.4f'%np.linalg.norm(delta,axis=1).max())
for kb in me.shape_keys.key_blocks:
    kc=np.zeros(N*3); kb.data.foreach_get('co',kc); kb.data.foreach_set('co',(kc.reshape(N,3)+delta).ravel())
me.vertices.foreach_set('co',(co+delta).ravel()); me.update()
bpy.context.view_layer.objects.active=body
with bpy.context.temp_override(object=body,active_object=body):
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
for p in me.polygons: p.use_smooth=True
me.update()
np.save('/workspace/gym-app/3d/v3work/head_ellipsoid.npy',np.concatenate([cen,rad]))
# masks attr: R face (wider), G antenna
ant=np.zeros(N)
for vg in body.vertex_groups:
    if 'Antenna' in vg.name:
        for v in me.vertices:
            for g in v.groups:
                if g.group==vg.index: ant[v.index]=max(ant[v.index],g.weight)
co2=co+delta
ell2=((co2[:,0]/0.12)**2+((co2[:,2]-0.758)/0.058)**2)
fm2=(ell2<1.25)*(co2[:,1]<cen[1])*(hw>0.5)
mk=np.stack([fm2.astype(float),ant,np.zeros(N),np.ones(N)],1)
at=me.color_attributes.get('tex_masks') or me.color_attributes.new('tex_masks','FLOAT_COLOR','POINT')
at.data.foreach_set('color',mk.ravel())
# ---- bakes
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=2
for o in bpy.context.view_layer.objects: o.select_set(False)
body.select_set(True); bpy.context.view_layer.objects.active=body
R=2048
def img(name):
    i=bpy.data.images.new(name,R,R,alpha=False,float_buffer=False); i.colorspace_settings.name='Non-Color'; return i
m=bpy.data.materials.new('BakeV3'); m.use_nodes=True; nt=m.node_tree; Nn=nt.nodes; L=nt.links
for n in list(Nn):
    if n.type!='OUTPUT_MATERIAL': Nn.remove(n)
out=Nn['Material Output']
def attr(nm):
    a_=Nn.new('ShaderNodeAttribute'); a_.attribute_name=nm; return a_
legm=attr('leg_def_mask').outputs['Fac']; veinm=attr('vein_mask').outputs['Fac']; tmask=attr('tex_masks').outputs['Color']
tc=Nn.new('ShaderNodeTexCoord')
def stretched(sx,sy,sz,dist,ns):
    mp=Nn.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(sx,sy,sz); L.new(tc.outputs['Object'],mp.inputs[0])
    nz=Nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=ns; L.new(mp.outputs[0],nz.inputs[0])
    mix=Nn.new('ShaderNodeMix'); mix.data_type='VECTOR'; mix.inputs[0].default_value=dist
    L.new(mp.outputs[0],mix.inputs[4]); L.new(nz.outputs['Color'],mix.inputs[5]); return mix.outputs[1]
def edge_line(vec,scale,width,soft):
    v=Nn.new('ShaderNodeTexVoronoi'); v.feature='DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value=scale; L.new(vec,v.inputs['Vector'])
    r=Nn.new('ShaderNodeMapRange'); r.inputs[1].default_value=width; r.inputs[2].default_value=width+soft; r.inputs[3].default_value=1; r.inputs[4].default_value=0
    L.new(v.outputs['Distance'],r.inputs[0]); return r.outputs[0]
def mul(a_,b_):
    n=Nn.new('ShaderNodeMath'); n.operation='MULTIPLY'; L.new(a_,n.inputs[0])
    if isinstance(b_,float): n.inputs[1].default_value=b_
    else: L.new(b_,n.inputs[1])
    return n.outputs[0]
veins=edge_line(stretched(1,1,0.3,0.3,5),30,0.018,0.03)
br=Nn.new('ShaderNodeTexNoise'); br.inputs['Scale'].default_value=40; L.new(tc.outputs['Object'],br.inputs[0])
brr=Nn.new('ShaderNodeMapRange'); brr.inputs[1].default_value=0.45; brr.inputs[2].default_value=0.56; L.new(br.outputs[0],brr.inputs[0])
vM=mul(mul(veins,brr.outputs[0]),veinm)
grooves=edge_line(stretched(1,1,0.45,0.12,3),13,0.0,0.06)
gM=mul(grooves,legm)
sep=Nn.new('ShaderNodeSeparateColor'); L.new(tmask,sep.inputs[0])
comb=Nn.new('ShaderNodeCombineColor'); L.new(vM,comb.inputs[0]); L.new(gM,comb.inputs[1]); L.new(sep.outputs[0],comb.inputs[2])
em=Nn.new('ShaderNodeEmission'); L.new(comb.outputs[0],em.inputs[0])
comb2=Nn.new('ShaderNodeCombineColor'); L.new(sep.outputs[0],comb2.inputs[0]); L.new(sep.outputs[1],comb2.inputs[1])
em2=Nn.new('ShaderNodeEmission'); L.new(comb2.outputs[0],em2.inputs[0])
h=Nn.new('ShaderNodeMath'); h.operation='SUBTRACT'; L.new(vM,h.inputs[0]); L.new(mul(gM,0.9),h.inputs[1])
bump=Nn.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=1.0; bump.inputs['Distance'].default_value=0.002; L.new(h.outputs[0],bump.inputs['Height'])
pb=Nn.new('ShaderNodeBsdfPrincipled'); L.new(bump.outputs[0],pb.inputs['Normal'])
ti=Nn.new('ShaderNodeTexImage'); Nn.active=ti
orig=list(me.materials); me.materials.clear(); me.materials.append(m)
sc.render.bake.margin=12
for name,src,typ in (('zeek_v3_detail',em,'EMIT'),('zeek_v3_masks',em2,'EMIT'),('zeek_v3_detail_normal',pb,'NORMAL')):
    im=img(name); ti.image=im; L.new(src.outputs[0],out.inputs[0]); Nn.active=ti
    sc.cycles.samples=4 if typ=='NORMAL' else 2
    if typ=='NORMAL': bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',margin=12)
    else: bpy.ops.object.bake(type='EMIT',margin=12)
    im.filepath_raw=f'/workspace/gym-app/3d/tex/{name}.png'; im.file_format='PNG'; im.save(); print('BAKED',name)
me.materials.clear()
for mm in orig: me.materials.append(mm)
bpy.data.materials.remove(m)
for nm in ('zeek_v3_detail','zeek_v3_masks','zeek_v3_detail_normal'):
    bpy.data.images.remove(bpy.data.images[nm])
bpy.ops.wm.save_as_mainfile(filepath='/workspace/gym-app/3d/v3work/03_face.blend')

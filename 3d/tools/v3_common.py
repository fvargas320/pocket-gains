import bpy, math, numpy as np, sys
sys.path.insert(0,'/workspace/gym-app/3d/tools')
from v2_common import setup_scene, toon_nodes, outline_mat, add_outline, camera, set_world_rot, aim
P='mixamorig:'
TEX='/workspace/gym-app/3d/tex/'
def load_img(fn, noncolor=False, name=None):
    name=name or fn.rsplit('.',1)[0]
    i=bpy.data.images.get(name)
    if not i:
        i=bpy.data.images.load(TEX+fn); i.name=name
    if noncolor: i.colorspace_settings.name='Non-Color'
    if not i.packed_file: i.pack()
    return i
def mathn(nt,op,a,b):
    m=nt.nodes.new('ShaderNodeMath'); m.operation=op
    for k,s in enumerate((a,b)):
        if isinstance(s,(int,float)): m.inputs[k].default_value=s
        else: nt.links.new(s,m.inputs[k])
    return m.outputs[0]
def mixmul(nt,fac,a,bcol):
    m=nt.nodes.new('ShaderNodeMix'); m.data_type='RGBA'; m.blend_type='MULTIPLY'
    nt.links.new(fac,m.inputs[0]); nt.links.new(a,m.inputs[6]); m.inputs[7].default_value=bcol; return m.outputs[2]
def build_body_material_v3(body):
    mat=bpy.data.materials.new('Zeek_Body_Toon'); body.data.materials.clear(); body.data.materials.append(mat)
    mat.use_nodes=True; nt=mat.node_tree; N=nt.nodes; L=nt.links
    for n in list(N):
        if n.type!='OUTPUT_MATERIAL': N.remove(n)
    uv=N.new('ShaderNodeUVMap')
    base=N.new('ShaderNodeTexImage'); base.image=load_img('zeek_v3_body_basecolor.jpg'); base.name='BaseColor'
    det=N.new('ShaderNodeTexImage'); det.image=load_img('zeek_v3_detail.png',True); det.name='Detail'
    nrm=N.new('ShaderNodeTexImage'); nrm.image=load_img('zeek_v3_detail_normal.png',True); nrm.name='DetailNormal'
    for t in (base,det,nrm): L.new(uv.outputs[0],t.inputs[0])
    lg=N.new('ShaderNodeValue'); lg.name='LegDef'; lg.label='LegDef (driver)'
    fc=nt.driver_add('nodes["LegDef"].outputs[0].default_value'); dr=fc.driver; dr.type='AVERAGE'
    for k in ('legs_quads','legs_glutes','legs_calves'):
        v=dr.variables.new(); v.name=k; v.type='SINGLE_PROP'; v.targets[0].id_type='KEY'
        v.targets[0].id=body.data.shape_keys; v.targets[0].data_path=f'key_blocks["{k}"].value'
    va=N.new('ShaderNodeValue'); va.name='Vascularity'; va.label='Vascularity 0-1'
    # driver from body custom prop so the app/anim can key it
    body['vascularity']=0.0
    fc=nt.driver_add('nodes["Vascularity"].outputs[0].default_value'); dr=fc.driver; dr.type='AVERAGE'
    v=dr.variables.new(); v.name='v'; v.type='SINGLE_PROP'; v.targets[0].id_type='OBJECT'; v.targets[0].id=body; v.targets[0].data_path='["vascularity"]'
    sep=N.new('ShaderNodeSeparateColor'); L.new(det.outputs[0],sep.inputs[0])
    lv=mathn(nt,'MINIMUM',mathn(nt,'MAXIMUM',lg.outputs[0],0.0),1.0)
    vv=mathn(nt,'MINIMUM',mathn(nt,'MAXIMUM',va.outputs[0],0.0),1.0)
    gF=mathn(nt,'MULTIPLY',mathn(nt,'MULTIPLY',sep.outputs[1],lv),0.55)
    vF=mathn(nt,'MINIMUM',mathn(nt,'MULTIPLY',mathn(nt,'MULTIPLY',sep.outputs[0],vv),1.6),1.0)
    c=mixmul(nt,gF,base.outputs[0],(0.55,0.68,0.45,1))
    c=mixmul(nt,vF,c,(0.40,0.60,0.50,1))
    _,d=toon_nodes(mat,lambda nt:c)
    nm=N.new('ShaderNodeNormalMap'); L.new(nrm.outputs[0],nm.inputs['Color'])
    L.new(mathn(nt,'MULTIPLY',mathn(nt,'MAXIMUM',lv,vv),1.5),nm.inputs['Strength'])
    L.new(nm.outputs[0],d.inputs['Normal'])
    return mat
def decal_material(name,fn):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes):
        if n.type!='OUTPUT_MATERIAL': nt.nodes.remove(n)
    t=nt.nodes.new('ShaderNodeTexImage'); t.image=load_img(fn); t.name='DecalTex'; t.interpolation='Cubic'
    _,d=toon_nodes(m,lambda nt:t.outputs[0],shadow=0.8)
    out=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'][0]
    em=out.inputs[0].links[0].from_node
    tr=nt.nodes.new('ShaderNodeBsdfTransparent'); mx=nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(t.outputs['Alpha'],mx.inputs[0]); nt.links.new(tr.outputs[0],mx.inputs[1]); nt.links.new(em.outputs[0],mx.inputs[2])
    nt.links.new(mx.outputs[0],out.inputs[0])
    try: m.surface_render_method='BLENDED'
    except Exception: pass
    m.blend_method='BLEND'
    try: m.use_transparency_overlap=False
    except Exception: pass
    m.show_transparent_back=False; m.use_backface_culling=True
    return m

import bpy, math
from mathutils import Vector, Matrix, Quaternion
P='mixamorig:'
def setup_scene(res=1024, samples=16):
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE_NEXT'
    sc.render.resolution_x=sc.render.resolution_y=res
    sc.eevee.taa_render_samples=samples
    sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
    w=bpy.data.worlds.get('W') or bpy.data.worlds.new('W'); sc.world=w; w.use_nodes=True
    bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.80,0.82,0.84,1); bg.inputs[1].default_value=1.0
    sc.render.film_transparent=False
    if 'Sun' not in bpy.data.objects:
        L=bpy.data.lights.new('Sun','SUN'); L.energy=3.2; L.angle=math.radians(3)
        o=bpy.data.objects.new('Sun',L); sc.collection.objects.link(o)
        o.rotation_euler=(math.radians(50),0,math.radians(-35))
    return sc
def toon_nodes(mat, color_out_fn, shadow=0.68, outline=False):
    """color_out_fn(nt) -> socket giving base color"""
    mat.use_nodes=True; nt=mat.node_tree
    out=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'][0]
    col=color_out_fn(nt)
    d=nt.nodes.new('ShaderNodeBsdfDiffuse'); d.name='ToonDiffuse'
    s2r=nt.nodes.new('ShaderNodeShaderToRGB'); nt.links.new(d.outputs[0],s2r.inputs[0])
    rmp=nt.nodes.new('ShaderNodeValToRGB'); rmp.name='ToonRamp'; r=rmp.color_ramp; r.interpolation='CONSTANT'
    r.elements[0].position=0.0; r.elements[0].color=(shadow,shadow,shadow*1.05,1)
    r.elements[1].position=0.22; r.elements[1].color=(1,1,1,1)
    e=r.elements.new(0.75); e.color=(1.08,1.08,1.06,1)
    bw=nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(s2r.outputs[0],bw.inputs[0]); nt.links.new(bw.outputs[0],rmp.inputs[0])
    mul=nt.nodes.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.inputs[0].default_value=1
    nt.links.new(col,mul.inputs[6]); nt.links.new(rmp.outputs[0],mul.inputs[7])
    em=nt.nodes.new('ShaderNodeEmission'); nt.links.new(mul.outputs[2],em.inputs[0])
    nt.links.new(em.outputs[0],out.inputs[0])
    return nt, d
def outline_mat():
    m=bpy.data.materials.get('Outline')
    if m: return m
    m=bpy.data.materials.new('Outline'); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes):
        if n.type!='OUTPUT_MATERIAL': nt.nodes.remove(n)
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value=(0.03,0.04,0.03,1)
    nt.links.new(em.outputs[0],nt.nodes['Material Output'].inputs[0])
    m.use_backface_culling=True
    return m
def add_outline(obj, thick=0.0035, quality=True):
    m=outline_mat()
    if m.name not in [s.name for s in obj.data.materials if s]: obj.data.materials.append(m)
    idx=[i for i,s in enumerate(obj.data.materials) if s and s.name=='Outline'][0]
    md=obj.modifiers.get('Outline') or obj.modifiers.new('Outline','SOLIDIFY')
    md.thickness=thick; md.offset=1.0; md.use_flip_normals=True; md.use_rim=False
    md.material_offset=idx; md.material_offset_rim=idx
    md.use_quality_normals=quality
    return md
def camera(yaw_deg=0, ortho=1.15, zc=0.5, name='Cam', dist=4.0, elev=4):
    sc=bpy.context.scene
    c=bpy.data.objects.get(name)
    if not c:
        cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c)
    c.data.type='ORTHO'; c.data.ortho_scale=ortho
    a=math.radians(yaw_deg); e=math.radians(elev)
    c.location=(dist*math.sin(a)*math.cos(e), -dist*math.cos(a)*math.cos(e), zc+dist*math.sin(e))
    c.rotation_euler=(math.radians(90)-e,0,a)
    sc.camera=c; return c
def set_world_rot(rig, bone, q_world):
    """rotate posed bone so its world rotation = q_world * rest world rotation (keeps head)"""
    pb=rig.pose.bones[bone]
    rest=rig.matrix_world @ pb.bone.matrix_local
    loc=pb.matrix.to_translation() if pb.parent else rest.to_translation()
    R=(q_world.to_matrix().to_4x4() @ Matrix(rest.to_3x3()).to_4x4())
    R.translation=loc
    pb.matrix=rig.matrix_world.inverted() @ R
    bpy.context.view_layer.update()
def aim(rig, bone, direction, extra_roll=None):
    pb=rig.pose.bones[bone]
    rest_dir=(rig.matrix_world.to_3x3() @ (pb.bone.matrix_local.to_3x3() @ Vector((0,1,0)))).normalized()
    q=rest_dir.rotation_difference(Vector(direction).normalized())
    set_world_rot(rig,bone,q)

def build_body_material(body):
    mat=body.data.materials[0]; mat.name='Zeek_Body_Toon'; nt=mat.node_tree; N=nt.nodes; L=nt.links
    base=[n for n in N if n.type=='TEX_IMAGE'][0]
    for n in list(N):
        if n.type not in ('TEX_IMAGE','OUTPUT_MATERIAL'): N.remove(n)
    uv=N.new('ShaderNodeUVMap')
    def li(n):
        i=bpy.data.images.get(n) or bpy.data.images.load(f'/workspace/gym-app/3d/tex/{n}.png')
        i.name=n; i.colorspace_settings.name='Non-Color'
        if not i.packed_file: i.pack()
        return i
    det=N.new('ShaderNodeTexImage'); det.image=li('zeek_v2_leg_detail'); det.name='LegDetail'
    nrm=N.new('ShaderNodeTexImage'); nrm.image=li('zeek_v2_leg_normal'); nrm.name='LegNormal'
    for t in (det,nrm): L.new(uv.outputs[0],t.inputs[0])
    val=N.new('ShaderNodeValue'); val.name='LegDef'; val.label='LegDef (driver)'
    fc=nt.driver_add('nodes["LegDef"].outputs[0].default_value'); dr=fc.driver; dr.type='AVERAGE'
    for k in ('legs_quads','legs_glutes','legs_calves'):
        v=dr.variables.new(); v.name=k; v.type='SINGLE_PROP'; v.targets[0].id_type='KEY'
        v.targets[0].id=body.data.shape_keys; v.targets[0].data_path=f'key_blocks["{k}"].value'
    sep=N.new('ShaderNodeSeparateColor'); L.new(det.outputs[0],sep.inputs[0])
    def mathn(op,a,b):
        m=N.new('ShaderNodeMath'); m.operation=op
        for i,s in enumerate((a,b)):
            if isinstance(s,(int,float)): m.inputs[i].default_value=s
            else: L.new(s,m.inputs[i])
        return m.outputs[0]
    lv=mathn('MINIMUM',mathn('MAXIMUM',val.outputs[0],0.0),1.0)
    gF=mathn('MULTIPLY',mathn('MULTIPLY',sep.outputs[1],lv),0.55)
    vF=mathn('MULTIPLY',mathn('MULTIPLY',sep.outputs[0],lv),0.9)
    def mix(fac,a,bcol):
        m=N.new('ShaderNodeMix'); m.data_type='RGBA'; m.blend_type='MULTIPLY'; L.new(fac,m.inputs[0]); L.new(a,m.inputs[6]); m.inputs[7].default_value=bcol; return m.outputs[2]
    c=mix(gF,base.outputs[0],(0.55,0.68,0.45,1))
    c=mix(vF,c,(0.42,0.62,0.48,1))
    _,d=toon_nodes(mat,lambda nt:c)
    nm=N.new('ShaderNodeNormalMap'); L.new(nrm.outputs[0],nm.inputs['Color']); L.new(lv,nm.inputs['Strength'])
    L.new(nm.outputs[0],d.inputs['Normal'])
    return mat

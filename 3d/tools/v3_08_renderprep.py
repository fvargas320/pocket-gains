import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from v2_common import setup_scene, toon_nodes, camera
D3='/workspace/gym-app/3d'
bpy.ops.wm.open_mainfile(filepath=f'{D3}/v3work/07_full.blend')
setup_scene(720,16); sc=bpy.context.scene
sc.render.fps=30
# floor disc w/ toon (receives shadow)
bpy.ops.mesh.primitive_circle_add(vertices=96,radius=0.75,fill_type='NGON',location=(0,0,0))
fl=bpy.context.object; fl.name='Floor'
m=bpy.data.materials.new('Floor_Toon'); m.use_nodes=True; nt=m.node_tree
rgb=nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value=(0.80,0.83,0.86,1)
toon_nodes(m,lambda nt:rgb.outputs[0],shadow=0.78); fl.data.materials.append(m)
# camera rig to follow hips xy
cam=camera(25,1.1,0.5,'ShotCam',4,6)
emp=bpy.data.objects.new('CamPivot',None); sc.collection.objects.link(emp)
c=emp.constraints.new('COPY_LOCATION'); c.target=bpy.data.objects['Zeek_Rig']; c.subtarget='mixamorig:Hips'; c.use_z=False; c.mute=True
cam.parent=emp
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=f'{D3}/v3work/08_render.blend'); print('saved', sc.render.engine)

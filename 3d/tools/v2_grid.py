import bpy, math, sys
from mathutils import Vector
out=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath='/workspace/gym-app/3d/v2work/01_body.blend')
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='FLAT'; sc.display.shading.color_type='TEXTURE'
sc.render.resolution_x=sc.render.resolution_y=1024
cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=1.1
co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co
for name,loc,rot in [('front',(0,-3,0.5),(90,0,0)),('side',(3,0,0.5),(90,0,90))]:
    co.location=loc; co.rotation_euler=[math.radians(r) for r in rot]
    sc.render.filepath=f'{out}/grid_{name}.png'; bpy.ops.render.render(write_still=True)

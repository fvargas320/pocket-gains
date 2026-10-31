# blender -b -P preview.py -- in.glb outdir prefix [turntable]
import bpy, sys, math, os, bmesh, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--')+1:]
src, out, prefix = a[0], a[1], a[2]
turn = 'turn' in a[3:]
yaw = float(next((x.split('=')[1] for x in a[3:] if x.startswith('yaw=')), 0))
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
# stats
stats = {'objects': len(meshes), 'tris': 0, 'verts': 0, 'textures': [], 'non_manifold_edges': 0, 'boundary_edges': 0, 'islands': 0}
dg = bpy.context.evaluated_depsgraph_get()
for o in meshes:
    bm = bmesh.new(); bm.from_mesh(o.data)
    stats['tris'] += sum(len(f.verts) - 2 for f in bm.faces)
    stats['verts'] += len(bm.verts)
    stats['boundary_edges'] += sum(1 for e in bm.edges if e.is_boundary)
    stats['non_manifold_edges'] += sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
    # islands
    seen = set(); n = 0
    for v in bm.verts:
        if v.index in seen: continue
        n += 1; stack = [v]; seen.add(v.index)
        while stack:
            x = stack.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); stack.append(y)
    stats['islands'] += n
    bm.free()
for img in bpy.data.images:
    if img.size[0]: stats['textures'].append([img.name, img.size[0], img.size[1]])
# bounds
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
stats['bounds'] = [list(mn), list(mx)]
json.dump(stats, open(os.path.join(out, prefix + '_stats.json'), 'w'), indent=1)
print('STATS', json.dumps(stats))
ctr = (mn + mx) / 2; h = mx.z - mn.z
root = bpy.data.objects.new('root', None); bpy.context.scene.collection.objects.link(root)
for o in meshes:
    if o.parent is None: o.parent = root
# move root so model centred at origin
for o in [x for x in bpy.context.scene.objects if x.parent is None and x != root]:
    o.parent = root
root.location = -ctr
pivot = bpy.data.objects.new('pivot', None); bpy.context.scene.collection.objects.link(pivot)
root.parent = pivot
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.eevee.taa_render_samples = 32
w = sc.world = bpy.data.worlds.new('w'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.82, 0.83, 0.85, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.45
sc.view_settings.view_transform = 'Standard'
def light(name, loc, e, size):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = e; L.size = size
    o = bpy.data.objects.new(name, L); o.location = loc; sc.collection.objects.link(o)
    d = Vector((0, 0, 0)) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
s = h
light('key', (s*1.2, -s*1.6, s*1.2), 15*s*s, s*1.5)
light('fill', (-s*1.5, -s*1.0, s*0.4), 5*s*s, s*1.5)
light('rim', (0, s*1.6, s*1.0), 9*s*s, s*1.5)
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = h * 1.12
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = (0, -h*4, 0); co.rotation_euler = (math.radians(90), 0, 0)
# glTF is +Y up -> Blender Z up, model front faces -Y typically
views = {'front': 0, 'three_quarter': -45, 'side': -90, 'back': 180}
if not turn:
    for n, d in views.items():
        pivot.rotation_euler = (0, 0, math.radians(d + yaw))
        sc.render.filepath = os.path.join(out, f'{prefix}_{n}.png')
        bpy.ops.render.render(write_still=True)
else:
    sc.render.resolution_x = sc.render.resolution_y = 768
    sc.eevee.taa_render_samples = 16
    sc.frame_start, sc.frame_end = 1, 96
    pivot.rotation_euler = (0, 0, math.radians(yaw)); pivot.keyframe_insert('rotation_euler', frame=1)
    pivot.rotation_euler = (0, 0, math.radians(360 + yaw)); pivot.keyframe_insert('rotation_euler', frame=97)
    for fc in pivot.animation_data.action.fcurves:
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    sc.render.fps = 24
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = os.path.join(out, f'_frames_{prefix}/f_')
    bpy.ops.render.render(animation=True)

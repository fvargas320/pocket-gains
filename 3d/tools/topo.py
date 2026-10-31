import bpy, bmesh, sys, json
p = sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=p)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bm = bmesh.new()
for o in ms:
    me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me)
size = max(o.dimensions.length for o in ms)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5*size)
bm.verts.ensure_lookup_table()
bnd = sum(1 for e in bm.edges if e.is_boundary)
nm = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
seen=set(); isl=[]
for v in bm.verts:
    if v.index in seen: continue
    st=[v]; seen.add(v.index); n=0
    while st:
        x=st.pop(); n+=1
        for e in x.link_edges:
            y=e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    isl.append(n)
isl.sort(reverse=True)
# holes = boundary loops
loops=0; used=set()
for e in bm.edges:
    if e.is_boundary and e.index not in used:
        loops+=1; st=[e]
        while st:
            x=st.pop(); used.add(x.index)
            for v in x.verts:
                for f in v.link_edges:
                    if f.is_boundary and f.index not in used: used.add(f.index); st.append(f)
print('TOPO', json.dumps(dict(objects=len(ms), tris=sum(len(f.verts)-2 for f in bm.faces), verts_welded=len(bm.verts), boundary_edges=bnd, hole_loops=loops, nonmanifold_edges=nm, islands=len(isl), island_sizes=isl[:8])))

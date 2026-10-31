"""Build parts + composites + rig.json for Zeek (v2 seamless joints)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_rig as B
tw = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tweaks.json')))
parts = B.build_parts(tw.get('parts'))
rest = tw['rest_angles']
ROOT = B.ROOT
COMPOSITES = {
 'assembled-normal': dict(lo=dict(torso='normal', arms='normal', legs='normal', head='smirk')),
 'assembled-buff': dict(lo=dict(torso='buff', arms='buff', legs='buff', head='smirk')),
 'assembled-skipped-legday': dict(lo=dict(torso='buff', arms='buff', legs='noodle', head='tired')),
 'assembled-curl-demo': dict(lo=dict(torso='buff', arms='buff', legs='normal', head='hyped'),
     angles={'upper_arm_R': -10, 'forearm_R': -140}, z_over={'forearm_R': 23},
     props={'prop_dumbbell': ['forearm_R', 90, 37]}),
}
for fn, c in COMPOSITES.items():
    B.crop(B.render(parts, c['lo'], dict(rest, **c.get('angles', {})), props=c.get('props'), z_over=c.get('z_over'))).save(f'{ROOT}/{fn}.png')
os.makedirs(f'{ROOT}/_checks', exist_ok=True)
for t in ('noodle', 'normal', 'buff'):
    B.crop(B.render(parts, dict(torso=t, arms=t, legs=t, head='hyped'),
        dict(rest, upper_arm_R=-10, forearm_R=-150, upper_arm_L=70, forearm_L=-125, thigh_L=-70, shin_L=100),
        z_over={'forearm_R': 23, 'forearm_L': 23, 'shin_L': 17})).save(f'{ROOT}/_checks/bend-test-{t}.png')

rig = {
 "character": "zeek", "version": 2,
 "units": "pixels, part-local, origin top-left of each PNG, y down",
 "side_convention": "L = SCREEN-LEFT (viewer's left, i.e. Zeek's right). *_R_* files are horizontal mirrors of *_L_*.",
 "rotation_convention": "degrees, positive = clockwise on screen (y-down).",
 "how_to_place": "child.position (parent-local px) = parent anchor point; child.anchor = child.pivot / child.size. Flame: SpriteComponent(anchor: Anchor(pivot.x/size.x, pivot.y/size.y), position: Vector2(parentAnchor), priority: z) as a child of the parent sprite. Note: Flame child priority is relative to siblings; for the torso-behind/in-front ordering below, either flatten all parts under one root PositionComponent and compute transforms, or use a parent component with priorities per the z table.",
 "joint_scheme": {
   "shoulders": "upper arms render BEHIND the torso (z 24 < 30). The shoulder anchor sits inside the torso's own deltoid, so the arm emerges from under the shoulder. Never draw the upper arm above the torso.",
   "hips": "thighs render behind the torso; the shorts cover the hip joint.",
   "elbows_knees": "forearm/shin tops are alpha-feathered (feather_px) with no outline ring and render ABOVE the upper segment at rest, so the joint is invisible. The upper segment's rounded end (child_anchor) becomes the elbow/knee silhouette when bent.",
   "deep_bend_rule": "when |elbow or knee angle| > 90 deg, drop the lower segment just below its upper segment (forearm z 23 / shin z 17) so the upper segment's outlined end draws the elbow/knee point and the feathered top is hidden. assembled-curl-demo.png uses this."
 },
 "root": {"node": "torso", "pivot": "top-centre of torso image (x = size.x/2, y = 0)"},
 "z": B.Z,
 "deep_bend_z": {"forearm_L": 23, "forearm_R": 23, "shin_L": 17, "shin_R": 17},
 "hierarchy": {
   "torso": {"parent": None, "parent_anchor": None},
   "head": {"parent": "torso", "parent_anchor": "neck"},
   "antenna_L": {"parent": "head", "parent_anchor": "antenna_L", "file": "antenna_left", "note": "renders behind head"},
   "antenna_R": {"parent": "head", "parent_anchor": "antenna_R", "file": "antenna_right"},
   "upper_arm_L": {"parent": "torso", "parent_anchor": "shoulder_L"},
   "forearm_L": {"parent": "upper_arm_L", "parent_anchor": "child_anchor"},
   "upper_arm_R": {"parent": "torso", "parent_anchor": "shoulder_R"},
   "forearm_R": {"parent": "upper_arm_R", "parent_anchor": "child_anchor"},
   "thigh_L": {"parent": "torso", "parent_anchor": "hip_L"},
   "shin_L": {"parent": "thigh_L", "parent_anchor": "child_anchor"},
   "thigh_R": {"parent": "torso", "parent_anchor": "hip_R"},
   "shin_R": {"parent": "thigh_R", "parent_anchor": "child_anchor"}
 },
 "slots": {"head": {"variants": ["head_smirk", "head_chill", "head_hyped", "head_tired"], "default": "head_smirk"},
           **{s: {"pattern": f"{s}_{{tier}}"} for s in ["torso"]},
           **{f"{k}_{S}": {"pattern": f"{k}_{S}_{{tier}}"} for k in ["upper_arm", "forearm", "thigh", "shin"] for S in "LR"}},
 "tiers": ["noodle", "normal", "buff"],
 "tier_groups": {"torso": ["torso"], "arms": ["upper_arm_L", "upper_arm_R", "forearm_L", "forearm_R"], "legs": ["thigh_L", "thigh_R", "shin_L", "shin_R"]},
 "rest_angles": rest,
 "props": {
   "prop_dumbbell": {"attach_to": "forearm_L|forearm_R", "attach_anchor": "grip", "rotation": 90, "z": 37, "note": "pivot = handle centre"},
   "prop_barbell": {"attach_to": "forearm_L+forearm_R", "attach_anchor": "grip", "z": 37, "note": "pivot = bar centre; place at midpoint of both grips"}
 },
 "composites": {f"{k}.png": v for k, v in COMPOSITES.items()},
 "parts": {k: dict(file=f"{k}.png", **v) for k, v in sorted(parts.items())}
}
json.dump(rig, open(f'{ROOT}/rig.json', 'w'), indent=1)
print(len(parts), 'parts')

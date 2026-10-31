"""Scale Zeek parts, hide joints, find pivots, render composites.  (v2: seamless joints)

Joint scheme (v2):
  * shoulders: upper arms render BEHIND the torso; their pivot sits inside the torso's own
    deltoid, so the arm emerges from under the shoulder/armhole instead of being pasted on top.
  * hips: thighs render behind the torso (shorts cover the hip).
  * elbows / knees: the LOWER segment renders on top of the upper one and its top end is
    alpha-feathered (no outline ring). The upper segment's rounded end sits under the lower
    segment's opaque area at rest and becomes the elbow/knee silhouette when bent.
"""
import numpy as np, json, math, os, glob
from PIL import Image

ROOT = '/workspace/gym-app/prototype-art/zeek'
RAW = f'{ROOT}/_raw'

# raw sheet px -> final px. head = 1.0 reference (head ~375 px tall incl. neck stub)
SCALE = dict(head=1.0, antenna=0.55, torso=0.78, upper_arm=0.37, forearm=0.36,
             thigh=0.40, shin=0.42, prop_dumbbell=0.36, prop_barbell=0.58)
TIER_SCALE = {'upper_arm_buff': 1.12, 'forearm_buff': 1.08,
              'thigh_buff': 1.18, 'shin_buff': 1.2, 'thigh_normal': 1.0, 'shin_normal': 1.0}
X_STRETCH = {'upper_arm_normal': 1.18, 'forearm_normal': 1.08}
TIERS = ['noodle', 'normal', 'buff']
FEATHER = 0.30          # feather length on lower-segment tops, as a fraction of the top width

def fam(name):
    for k in SCALE:
        if name.startswith(k): return k
    raise KeyError(name)

def load_scaled(name):
    im = Image.open(f'{RAW}/{name}.png')
    s = SCALE[fam(name)] * TIER_SCALE.get(name, 1.0)
    sx = s * X_STRETCH.get(name, 1.0)
    if s != 1.0 or sx != s:
        im = im.resize((max(1, round(im.width * sx)), max(1, round(im.height * s))), Image.LANCZOS)
    return im

def runs(m, y):
    xs = np.where(m[y])[0]
    return (int(xs.min()), int(xs.max())) if len(xs) else None

def end_info(m, top=True, at=0.06):
    """width + centre of the limb a little in from one end (shaft just past the rounded cap)."""
    h = m.shape[0]
    y = int(h * at) if top else int(h * (1 - at))
    a, b = runs(m, y)
    return (a + b) / 2, b - a

def feather_top(im, length):
    a = np.asarray(im).copy(); m = a[..., 3] > 128
    y0 = int(np.where(m.any(1))[0][0])
    n = max(6, int(length))
    ramp = np.clip((np.arange(a.shape[0]) - y0) / n, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)      # smoothstep
    a[..., 3] = (a[..., 3] * ramp[:, None]).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')

def torso_anchors(im):
    a = np.asarray(im).astype(int); m = a[..., 3] > 128
    h, w = m.shape
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    skin = m & (g > 150) & (g > r + 10) & (g > b + 40)
    out = {}
    for side, sl in (('L', slice(0, int(w * 0.32))), ('R', slice(int(w * 0.68), w))):
        sub = np.zeros_like(m); sub[: int(h * 0.30), sl] = True
        ys, xs = np.where(skin & sub)
        # deltoid blob: pivot pulled inward (towards armhole) and slightly below its centre
        cx, cy = xs.mean(), ys.mean()
        outer = xs.min() if side == 'L' else xs.max()
        px = cx + (cx - outer) * 0.05
        out['shoulder_' + side] = [round(float(px), 1), round(float(cy + (ys.max() - cy) * 0.2), 1)]
    y = int(h * 0.985)
    while True:
        xs = np.where(m[y])[0]; gaps = np.where(np.diff(xs) > 4)[0]
        if len(gaps): break
        y -= 1
    g0 = gaps[0]; lx = (xs[0] + xs[g0]) / 2; rx = (xs[g0 + 1] + xs[-1]) / 2
    cx = w / 2; spread = 1.10; hy = h * 0.78
    out['hip_L'] = [round(float(cx - (cx - lx) * spread), 1), round(hy, 1)]
    out['hip_R'] = [round(float(cx + (rx - cx) * spread), 1), round(hy, 1)]
    out['neck'] = [round(w / 2, 1), round(h * 0.035, 1)]
    return out

def build_parts(tweak=None):
    tweak = tweak or {}
    parts = {}
    for f in glob.glob(f'{ROOT}/*.png'):
        os.remove(f)
    for f in sorted(glob.glob(f'{RAW}/*.png')):
        name = os.path.basename(f)[:-4]
        im = load_scaled(name); m = np.asarray(im)[..., 3] > 128
        p = {}; k = fam(name); h = im.height
        if k in ('upper_arm', 'thigh'):
            cx, wt = end_info(m, True); bx, wb = end_info(m, False)
            p['pivot'] = [round(cx, 1), round(wt * 0.45, 1)]                 # inside the top end
            p['child_anchor'] = [round(bx, 1), round(h - wb * 0.55, 1)]      # centre of the rounded bottom end
            p['end_width'] = wb
        elif k in ('forearm', 'shin'):
            cx, wt = end_info(m, True)
            F = wt * FEATHER
            im = feather_top(im, F)
            p['pivot'] = [round(cx, 1), round(F + wt * 0.42, 1)]
            p['feather_px'] = round(F, 1)
            if k == 'forearm':
                y = int(h * 0.85); a, b = runs(m, y)
                p['grip'] = [round((a + b) / 2, 1), float(y)]
        elif k == 'antenna':
            ys, xs = np.where(m[-6:]); p['pivot'] = [round(float(xs.mean()), 1), float(h - 4)]
        elif k == 'head':
            ys, xs = np.where(m[-4:]); p['pivot'] = [round(float(xs.mean()), 1), float(h - 2)]
            p['antenna_L'] = [round(im.width * 0.36, 1), round(h * 0.10, 1)]
            p['antenna_R'] = [round(im.width * 0.64, 1), round(h * 0.10, 1)]
            a = np.asarray(im).copy(); n = 14
            a[-n:, :, 3] = (a[-n:, :, 3] * np.linspace(1, 0, n)[:, None]).astype(np.uint8)
            im = Image.fromarray(a, 'RGBA')
        elif k == 'torso':
            p.update(torso_anchors(im))
        elif k.startswith('prop'):
            p['pivot'] = [round(im.width / 2, 1), round(h / 2, 1)]
        p['size'] = list(im.size)
        p.update(tweak.get(name, {}))
        im.save(f'{ROOT}/{name}.png'); parts[name] = p
    for k in ('upper_arm', 'forearm', 'thigh', 'shin'):
        for t in TIERS:
            src = f'{k}_{t}'; im = Image.open(f'{ROOT}/{src}.png')
            os.replace(f'{ROOT}/{src}.png', f'{ROOT}/{k}_L_{t}.png')
            im.transpose(Image.FLIP_LEFT_RIGHT).save(f'{ROOT}/{k}_R_{t}.png')
            pl = parts.pop(src); w = pl['size'][0]
            parts[f'{k}_L_{t}'] = pl
            parts[f'{k}_R_{t}'] = {kk: ([round(w - v[0], 1), v[1]] if isinstance(v, list) and kk != 'size' else v) for kk, v in pl.items()}
    return parts

# ---------- hierarchy / rendering ----------
Z = dict(antenna_L=5, antenna_R=5, thigh_L=18, thigh_R=18, shin_L=19, shin_R=19,
         upper_arm_L=24, upper_arm_R=24, torso=30, forearm_L=36, forearm_R=36, head=50)

def nodes_for(lo):
    n = {'torso': (f"torso_{lo['torso']}", None, None),
         'head': (f"head_{lo.get('head', 'smirk')}", 'torso', 'neck'),
         'antenna_L': ('antenna_left', 'head', 'antenna_L'),
         'antenna_R': ('antenna_right', 'head', 'antenna_R')}
    for S in 'LR':
        n[f'upper_arm_{S}'] = (f"upper_arm_{S}_{lo['arms']}", 'torso', f'shoulder_{S}')
        n[f'forearm_{S}'] = (f"forearm_{S}_{lo['arms']}", f'upper_arm_{S}', 'child_anchor')
        n[f'thigh_{S}'] = (f"thigh_{S}_{lo['legs']}", 'torso', f'hip_{S}')
        n[f'shin_{S}'] = (f"shin_{S}_{lo['legs']}", f'thigh_{S}', 'child_anchor')
    return n

def mat(tx=0, ty=0, deg=0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, tx], [s, c, ty], [0, 0, 1.0]])

def render(parts, lo, angles=None, canvas=(1400, 1800), origin=(700, 520), bg=(24, 40, 36, 255), props=None, z_over=None):
    angles = angles or {}; nodes = nodes_for(lo); z = dict(Z, **(z_over or {}))
    world = {}
    def W(n):
        if n in world: return world[n]
        pf, par, anc = nodes[n]; p = parts[pf]
        if par is None:
            M = mat(*origin) @ mat(deg=angles.get(n, 0)) @ mat(-p['size'][0] / 2, 0)
        else:
            a = parts[nodes[par][0]][anc]; piv = p['pivot']
            M = W(par) @ mat(a[0], a[1]) @ mat(deg=angles.get(n, 0)) @ mat(-piv[0], -piv[1])
        world[n] = M; return M
    out = Image.new('RGBA', canvas, bg)
    def draw(file, M):
        im = Image.open(f'{ROOT}/{file}.png')
        out.alpha_composite(im.transform(canvas, Image.AFFINE, tuple(np.linalg.inv(M)[:2].ravel()), Image.BICUBIC))
    layers = [(z[n], n) for n in nodes]
    for pname, (node, deg, pz) in (props or {}).items():
        layers.append((pz, ('prop', pname, node, deg)))
    for _, n in sorted(layers, key=lambda t: t[0]):
        if isinstance(n, tuple):
            _, pname, node, deg = n; g = parts[nodes[node][0]]['grip']; pv = parts[pname]['pivot']
            draw(pname, W(node) @ mat(*g) @ mat(deg=deg) @ mat(-pv[0], -pv[1]))
        else:
            draw(nodes[n][0], W(n))
    return out

def crop(im, m=40, bg=(24, 40, 36)):
    a = np.asarray(im).astype(int); d = np.abs(a[..., :3] - np.array(bg)).sum(-1) > 6
    ys, xs = np.where(d)
    return im.crop((max(0, xs.min() - m), max(0, ys.min() - m), min(im.width, xs.max() + m), min(im.height, ys.max() + m)))

"""Cut Zeek puppet parts out of the magenta part sheets."""
import numpy as np, json, os
from PIL import Image
from scipy import ndimage as ndi

ROOT = '/workspace/gym-app/prototype-art/zeek'
SRC = f'{ROOT}/_source'
RAW = f'{ROOT}/_raw'
os.makedirs(RAW, exist_ok=True)

def key(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = np.minimum(r, b) - g             # magenta-ness: bg ~ 244
    bg = np.array([248, 4, 248], np.float32)
    alpha = np.clip((215 - m) / (215 - 110), 0, 1)
    # unpremultiply edge pixels against the magenta bg (despill)
    A = np.maximum(alpha, 1e-3)[..., None]
    rgb = (a - (1 - A) * bg) / A
    rgb = np.clip(rgb, 0, 255)
    # residual spill: magenta tint where r,b both exceed g a lot on edges
    edge = (alpha < 0.98)
    spill = np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]
    fix = edge & (spill > 0)
    for c in (0, 2):
        rgb[..., c][fix] -= spill[fix]
    rgb = np.clip(rgb, 0, 255)
    # edge pixels take the colour of the nearest solid pixel (kills magenta/red fringe)
    solid = alpha >= 0.95
    _, (iy, ix) = ndi.distance_transform_edt(~solid, return_indices=True)
    edge = ~solid
    rgb[edge] = rgb[iy[edge], ix[edge]]
    return rgb, alpha

def pieces(path, min_area=1500, merge=12):
    rgb, alpha = key(path)
    solid = alpha > 0.5
    lab, n = ndi.label(ndi.binary_dilation(solid, iterations=merge))
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        mask = (lab[sl] == i)
        area = (solid[sl] & mask).sum()
        if area < min_area:
            continue
        y0, x0 = sl[0].start, sl[1].start
        al = alpha[sl] * mask
        rgba = np.dstack([rgb[sl], al * 255]).astype(np.uint8)
        im = Image.fromarray(rgba, 'RGBA')
        bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
        im = im.crop(bb)
        out.append(dict(img=im, x=x0 + bb[0], y=y0 + bb[1], cx=x0 + (bb[0] + bb[2]) / 2, cy=y0 + (bb[1] + bb[3]) / 2, area=int(area)))
    return out

def rows(ps, gap=150):
    ps = sorted(ps, key=lambda p: p['cy'])
    groups = []
    for p in ps:
        if groups and abs(p['cy'] - groups[-1][-1]['cy']) < gap:
            groups[-1].append(p)
        else:
            groups.append([p])
    return [sorted(g, key=lambda p: p['cx']) for g in groups]

names = {
  'sheet-heads-props.png': [['head_smirk', 'head_chill', 'head_hyped', 'head_tired'], ['antenna_left', 'antenna_right', 'prop_dumbbell'], ['prop_barbell']],
  'sheet-torsos.png': [['torso_noodle', 'torso_normal', 'torso_buff']],
  'sheet-arms-v2.png': [['upper_arm_noodle', 'upper_arm_normal', 'upper_arm_buff'], ['forearm_noodle', 'forearm_normal', 'forearm_buff']],
  'sheet-legs-v2.png': [['thigh_noodle', 'thigh_normal', 'thigh_buff'], ['shin_noodle', 'shin_normal', 'shin_buff']],
}
meta = {}
for sheet, layout in names.items():
    rs = rows(pieces(f'{SRC}/{sheet}'))
    print(sheet, [len(r) for r in rs])
    assert len(rs) == len(layout), (sheet, [[(p['cx'], p['cy'], p['area']) for p in r] for r in rs])
    for r, nm in zip(rs, layout):
        if nm is None: continue
        assert len(r) == len(nm), (sheet, nm, [(p['cx'], p['cy'], p['area']) for p in r])
        for p, n in zip(r, nm):
            p['img'].save(f'{RAW}/{n}.png')
            meta[n] = dict(sheet=sheet, size=p['img'].size, sheet_xy=[p['x'], p['y']])
            print(' ', n, p['img'].size, p['area'])
json.dump(meta, open(f'{RAW}/_meta.json', 'w'), indent=1)

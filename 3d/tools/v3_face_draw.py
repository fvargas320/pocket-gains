# Draw 4 expression decals (RGBA). Canvas = ortho front of head: x=(px/S-0.5)*0.24, z=0.77+(0.5-py/S)*0.24
import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter
S=2048; OUT=1024
SKIN=(196,239,102); LID=(178,226,90); INK=(22,40,14); BLK=(12,14,12); WHT=(255,255,255)
def P(x,z): return ((x/0.24+0.5)*S,(0.5-(z-0.77)/0.24)*S)
def eye_poly(cx,cz,w,h_top,h_bot,slant,side,n=48):
    pts=[]
    for i in range(n+1):
        t=i/n; x=cx+(t-0.5)*w; z=cz+h_top*math.sin(math.pi*t)**0.55
        pts.append((x,z))
    for i in range(n,-1,-1):
        t=i/n; x=cx+(t-0.5)*w; z=cz-h_bot*math.sin(math.pi*t)**0.6
        pts.append((x,z))
    out=[]
    for x,z in pts:  # slant: outer corner up
        dx=x-cx; z2=z+dx*slant*side
        out.append(P(x,z2))
    return out
def mask(poly):
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).polygon(poly,fill=255); return np.array(m)>0
def lid_mask(cx,cz,w,side,lid_z_in,lid_z_out,curve=0.0):
    # region above a line from inner corner (toward x=0) to outer corner
    xi=cx-side*w*0.62; xo=cx+side*w*0.62
    pts=[P(xi,lid_z_in)]
    for i in range(1,20):
        t=i/20; x=xi+(xo-xi)*t; z=lid_z_in+(lid_z_out-lid_z_in)*t+curve*math.sin(math.pi*t)
        pts.append(P(x,z))
    pts+= [P(xo,lid_z_out),P(xo,1.2),P(xi,1.2)]
    return mask(pts),pts[:21]
def draw_face(kind):
    img=np.zeros((S,S,4),np.uint8)
    def paint(m,col,a=255):
        img[m,:3]=col; img[m,3]=a
    d_lines=[]  # (pts,width,col)
    for side in (-1,1):   # side=+1 => character left (+x)
        cx=side*0.05; cz=0.752
        if kind=='smirk': w,ht,hb,sl,lin,lout,cur=0.068,0.028,0.022,0.18,0.764,0.772,0.003
        if kind=='grin':  w,ht,hb,sl,lin,lout,cur=0.068,0.031,0.024,0.15,0.778,0.786,0.005
        if kind=='grit':  w,ht,hb,sl,lin,lout,cur=0.066,0.026,0.016,0.10,0.759,0.768,0.0
        if kind=='tired': w,ht,hb,sl,lin,lout,cur=0.068,0.027,0.02,0.06,0.758,0.753,0.003
        if kind=='smirk' and side==1: lin,lout=0.768,0.777   # one lid a touch higher: cocky asymmetry
        poly=eye_poly(cx,cz,w,ht,hb,sl,side)
        em=mask(poly)
        lm,lpts=lid_mask(cx,cz,w,side,lin,lout,cur)
        paint(em&~lm,BLK)
        paint(em&lm,LID)
        # highlight
        hx,hz=cx-side*0.012,cz+0.001
        if kind=='grit': hx,hz=cx-side*0.006,cz-0.001
        hm=Image.new('L',(S,S),0); a,b=P(hx-0.0065,hz+0.0065),P(hx+0.0065,hz-0.0065); ImageDraw.Draw(hm).ellipse([a,b],fill=255); paint(np.array(hm)>0,WHT)
        if kind=='grin':
            hm=Image.new('L',(S,S),0); a,b=P(hx+side*0.012-0.002,hz-0.006+0.002),P(hx+side*0.012+0.002,hz-0.006-0.002); ImageDraw.Draw(hm).ellipse([a,b],fill=255); paint(np.array(hm)>0,WHT)
        # outline of visible eye + lid line
        d_lines.append((poly+[poly[0]],10,INK))
        # lid line clipped to eye width (extend a bit past outer corner)
        lp=lpts[2:]  # skip inner overhang
        d_lines.append((lp,22 if kind!='grin' else 16,INK))
        if kind=='tired':  # bag line
            bp=[P(cx+(t-0.5)*w*0.8, cz-hb-0.006-0.002*math.sin(math.pi*t)) for t in np.linspace(0,1,12)]
            d_lines.append((bp,8,(90,130,50)))
        if kind=='grit':  # angry brows
            bi=P(cx-side*0.03,0.784); bo=P(cx+side*0.028,0.799)
            d_lines.append(([bi,bo],26,INK))
    # mouth
    mz=0.722
    if kind=='smirk':
        pts=[]
        for i in range(41):
            t=i/40; x=-0.016+0.04*t
            z=mz-0.0045*abs(math.sin(2*math.pi*t))+0.008*max(0,t-0.6)**1.5*3
            pts.append(P(x,z))
        d_lines.append((pts,16,INK))
    if kind=='grin':
        poly=[]
        for i in range(41):
            t=i/40; x=-0.026+0.052*t; poly.append(P(x,mz+0.004+0.002*math.sin(math.pi*t)))
        for i in range(40,-1,-1):
            t=i/40; x=-0.026+0.052*t; poly.append(P(x,mz+0.004-0.024*math.sin(math.pi*t)**0.8))
        mm=mask(poly); paint(mm,(70,20,30))
        tg=Image.new('L',(S,S),0); a,b=P(-0.014,mz-0.008),P(0.016,mz-0.024); ImageDraw.Draw(tg).ellipse([a,b],fill=255)
        paint(np.array(tg)>0 & mm,(240,110,130))
        th=Image.new('L',(S,S),0); a,b=P(-0.024,mz+0.007),P(0.024,mz+0.0); ImageDraw.Draw(th).rectangle([a,b],fill=255)
        paint(np.array(th)>0 & mm,WHT)
        d_lines.append((poly+[poly[0]],12,INK))
    if kind=='grit':
        poly=[P(-0.024,mz+0.004),P(0.024,mz+0.006),P(0.022,mz-0.010),P(-0.022,mz-0.009)]
        paint(mask(poly),WHT)
        d_lines.append((poly+[poly[0]],12,INK))
        d_lines.append(([P(-0.023,mz-0.0025),P(0.023,mz-0.002)],7,INK))
        for xx in (-0.012,0.0,0.012): d_lines.append(([P(xx,mz+0.005),P(xx,mz-0.009)],6,INK))
    if kind=='tired':
        pts=[P(-0.012+0.024*t, mz-0.002+0.0022*math.sin(3*math.pi*t)) for t in np.linspace(0,1,40)]
        d_lines.append((pts,12,INK))
    im=Image.fromarray(img,'RGBA'); dr=ImageDraw.Draw(im)
    for pts,wd,col in d_lines:
        dr.line(pts,fill=col+(255,),width=wd,joint='curve')
        for p in (pts[0],pts[-1]): dr.ellipse([p[0]-wd/2,p[1]-wd/2,p[0]+wd/2,p[1]+wd/2],fill=col+(255,))
    if kind in ('grit','tired'):  # sweat drop
        dm=Image.new('L',(S,S),0); dd=ImageDraw.Draw(dm)
        cx,cz=(0.078,0.792) if kind=='grit' else (0.08,0.79)
        a=P(cx,cz); r=0.008*S/0.24
        dd.ellipse([a[0]-r,a[1]-r*0.2,a[0]+r,a[1]+r*1.8],fill=255); dd.polygon([(a[0]-r*0.9,a[1]+r*0.5),(a[0]+r*0.9,a[1]+r*0.5),(a[0],a[1]-r*1.6)],fill=255)
        dmn=np.array(dm)>0; arr=np.array(im); arr[dmn]=(120,200,255,255); im=Image.fromarray(arr)
        ImageDraw.Draw(im).ellipse([a[0]-r,a[1]-r*0.2,a[0]+r,a[1]+r*1.8],outline=INK+(255,),width=8)
    return im.resize((OUT,OUT),Image.LANCZOS)
for k in ('smirk','grin','grit','tired'):
    draw_face(k).save(f'tex/zeek_v3_face_{k}.png')
print('ok')

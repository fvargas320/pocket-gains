import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter
T='/workspace/gym-app/3d/tex/'
leaf=Image.open(T+'leaf_logo.png').convert('RGBA')
S=1024
# ---- beanie: u around (front at u=.5), v 0=cuff bottom .. 1=top. cuff v<0.32
RUST=np.array([214,84,52]); RUSTD=np.array([168,58,38]); RUSTL=np.array([236,120,80])
u=np.linspace(0,1,S,endpoint=False)[None,:].repeat(S,0); v=np.linspace(1,0,S)[:,None].repeat(S,1)
img=np.zeros((S,S,3))
rib=0.5+0.5*np.cos(u*2*math.pi*96)
cuff=v<0.32
img[cuff]=(RUSTD+(RUST-RUSTD)*rib[...,None]**0.6)[cuff]
# knit V stitches above
cols=u*80; rows=(v-0.32)*60
fx=cols%1; fy=rows%1
vst=np.abs((fx-0.5)*2-(fy-0.5)*0)  # placeholder
chev=1-np.clip(np.abs(np.abs(fx-0.5)*1.4-(fy))*3,0,1)
k=0.55+0.45*np.cos((fx-0.5)*math.pi)  # column roundness
kn=RUSTD+(RUST-RUSTD)*k[...,None]
kn=kn*(0.92+0.08*chev[...,None])
img[~cuff]=kn[~cuff]
# fold line shadow
fold=(v>0.30)&(v<0.335); img[fold]*=0.72
img[(v<0.012)]*=0.8
im=Image.fromarray(img.clip(0,255).astype(np.uint8))
# leaf patch on cuff front
pt=Image.new('RGBA',(130,130),(0,0,0,0)); d=ImageDraw.Draw(pt); d.rounded_rectangle([4,4,125,125],22,fill=(40,60,38,255),outline=(230,220,190,255),width=6)
lf=leaf.resize((90,90)); pt.alpha_composite(lf,(20,20))
pt=pt.resize((80,110))  # compensate for u stretch (around is long)
im.paste(pt,(int(0.5*S)-40,int(S*(1-0.16))-55),pt)
im.save(T+'zeek_v3_beanie.png')
# ---- headband: u around, v across band (0 bottom,1 top). terry white + 2 teal stripes
W=np.array([245,242,232]); TEAL=np.array([28,170,160]); ORG=np.array([240,120,60])
img=np.zeros((256,S,3)); vv=np.linspace(1,0,256)[:,None].repeat(S,1); uu=np.linspace(0,1,S)[None,:].repeat(256,0)
img[:]=W
for c in (0.22,0.78): img[np.abs(vv-c)<0.07]=TEAL
noise=np.random.RandomState(1).rand(256,S)*14-7
img+=noise[...,None]
im=Image.fromarray(img.clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
lf=leaf.resize((110,110)); im.paste(lf,(int(0.5*S)-55,73),lf)
im.save(T+'zeek_v3_headband.png')
# ---- wrist wraps: u around, v along. black w/ diagonal pink-teal stripes and white velcro tab line
img=np.zeros((256,512,3)); uu=np.linspace(0,1,512)[None,:].repeat(256,0); vv=np.linspace(0,1,256)[:,None].repeat(512,1)
img[:]=(30,32,36)
diag=((uu*6+vv*3)%1)<0.12
img[diag]=(20,180,170)
img[(vv<0.07)|(vv>0.93)]=(235,235,235)
img+=np.random.RandomState(2).rand(256,512,1)*10
Image.fromarray(img.clip(0,255).astype(np.uint8)).save(T+'zeek_v3_wraps.png')
print('ok')

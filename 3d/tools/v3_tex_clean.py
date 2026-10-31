import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.color import rgb2hsv
from skimage.measure import regionprops
B=np.asarray(Image.open('tex/zeek_body_basecolor.jpg').convert('RGB')).astype(np.float32)/255
H,W,_=B.shape
M=Image.open('tex/zeek_v3_masks.png').convert('RGB').resize((W,H),Image.BILINEAR)
M=np.asarray(M).astype(np.float32)/255
face=ndi.binary_dilation(M[...,0]>0.5,iterations=10); ant=M[...,1]>0.3
hsv=rgb2hsv(B); h,s,v=hsv[...,0],hsv[...,1],hsv[...,2]
skin=(h>0.14)&(h<0.45)&(s>0.22)&(v>0.18)
base=np.median(B[skin&(v>np.percentile(v[skin],45))],axis=0)
print('base skin',base)
# local brightness
sk=skin.astype(np.float32)
num=ndi.gaussian_filter(v*sk,25); den=ndi.gaussian_filter(sk,25)+1e-6; loc=num/den
dark=skin&(v<loc*0.8)
lab,n=ndi.label(dark)
keep=np.zeros(n+1,bool)
for rp in regionprops(lab):
    a=rp.area
    if 25<=a<=6000 and rp.eccentricity<0.88 and rp.solidity>0.8: keep[rp.label]=True
spots=keep[lab]&~face
print('components',n,'spots kept',keep.sum())
spot_col=base*np.array([0.62,0.78,0.5])
out=B.copy()
skin_like=(skin|dark|face)&~ant
out[skin_like]=base
sm=ndi.gaussian_filter(ndi.binary_dilation(spots,iterations=1).astype(np.float32),1.0)[...,None]
out=np.where(skin_like[...,None],out*(1-sm)+spot_col*sm,out)
# stray dark slivers (eye paint across seams etc.)
blk=(v<0.3)&~ant
lb,nb=ndi.label(blk); sz=ndi.sum(np.ones_like(v),lb,index=np.arange(nb+1))
small=(sz<6000)[lb]&blk
out[small]=base
print('slivers removed',int((sz[1:]<6000).sum()))
# face region: also cover black eye paint (non-skin) with base
out[face&~ant]=base
Image.fromarray((out.clip(0,1)*255).astype(np.uint8)).save('tex/zeek_v3_body_basecolor.jpg',quality=93)
Image.fromarray((out.clip(0,1)*255).astype(np.uint8)).resize((1024,1024)).save('/tmp/v2/v3base_small_q.png')

# Style metrics beyond frame_stats.py: background blur ratio (DOF), vignette, ink colour, warm/cool split.
# usage: python -I references/scripts/style_metrics.py <dir-with-ch-and-v4>  (see references/reports/replication_playbook_2026-11.md)
import json, sys, glob, numpy as np, statistics as st
from PIL import Image, ImageFilter
S=sys.argv[1]
def lapvar(g):
    l=np.abs(4*g[1:-1,1:-1]-g[:-2,1:-1]-g[2:,1:-1]-g[1:-1,:-2]-g[1:-1,2:]); return float(l.mean())
def blobs(mask):
    h,w=mask.shape; seen=np.zeros_like(mask); best=[]
    for y in range(0,h,2):
        for x in range(0,w,2):
            if mask[y,x] and not seen[y,x]:
                st_=[(y,x)]; seen[y,x]=1; ys=[];xs=[]
                while st_:
                    a,b=st_.pop(); ys.append(a); xs.append(b)
                    for c,d in ((a+1,b),(a-1,b),(a,b+1),(a,b-1)):
                        if 0<=c<h and 0<=d<w and mask[c,d] and not seen[c,d]: seen[c,d]=1; st_.append((c,d))
                if len(ys)>30: best.append((len(ys),max(ys)-min(ys)+1,max(xs)-min(xs)+1,min(ys)))
    return best
def one(p):
    im=Image.open(p).convert('RGB').resize((270,480)); a=np.asarray(im).astype(float)/255
    g=a@np.array([.2126,.7152,.0722]); m=np.ones_like(g,bool); m[288:360]=False
    top=lapvar(g[20:150]); mid=lapvar(g[180:330])
    corners=np.mean([g[:60,:45].mean(),g[:60,-45:].mean(),g[-60:,:45].mean(),g[-60:,-45:].mean()]); center=g[160:320,70:200].mean()
    dark=a[(a.max(2)<0.22)&m]; ink=dark.mean(0) if len(dark) else np.zeros(3)
    # heads: near-white, low-sat round blobs
    white=(a.min(2)>0.86)&((a.max(2)-a.min(2))<0.10); white[288:360]=False
    bl=[b for b in blobs(white) if 0.6<b[1]/max(b[2],1)<1.6]
    head=max((b[1] for b in bl),default=0)/480
    # warm light vs cool shadow: mean hue tint of bright vs dark halves
    L=g[m]; rgb=a[m]; hi=rgb[L>np.percentile(L,75)].mean(0); lo=rgb[L<np.percentile(L,25)].mean(0)
    return dict(dof=mid/(top+1e-6), vign=corners/(center+1e-6), ink=ink.tolist(), head=head, nheads=len(bl),
                warm_hi=float(hi[0]-hi[2]), warm_lo=float(lo[0]-lo[2]))
out={}
for name,pat in (('Ricks',S+'/ch/RicksClips3000/*.jpg'),('SegmentZero',S+'/ch/segmentzero/*.jpg'),('Ours v4',S+'/v4/frames/f_0*[05]0.jpg')):
    fs=sorted(glob.glob(pat))
    if name=='Ricks':
        ex={r['id'] for r in json.load(open(S+'/ch/RicksClips3000_explainers.json'))}; fs=[f for f in fs if f.split('/')[-1][:11] in ex]
    if name.startswith('Ours'): fs=fs[::3]
    R=[one(f) for f in fs]
    def med(k): return st.median([r[k] for r in R])
    def frac(f): return sum(1 for r in R if f(r))/len(R)
    ink=np.median(np.array([r['ink'] for r in R]),0)
    print(f"{name} n={len(R)} | sharp mid/top {med('dof'):.2f} (bg blurred >1.5x: {frac(lambda r:r['dof']>1.5)*100:.0f}%) | vignette corner/center {med('vign'):.2f} | dark ink rgb {np.round(ink*255).astype(int)} | head height med {med('head')*100:.0f}% H, heads>=25%H {frac(lambda r:r['head']>=.25)*100:.0f}%, >=2 heads {frac(lambda r:r['nheads']>=2)*100:.0f}% | highlights warm(R-B) {med('warm_hi'):+.2f}, shadows {med('warm_lo'):+.2f}")

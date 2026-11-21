import sys, subprocess, numpy as np, json, statistics as st
f=sys.argv[1]; W,H=72,128
raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf',f'scale={W}:{H},format=rgb24','-f','rawvideo','-'],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3).astype(np.float32)
n=len(fr); g=fr.mean(3)
# colour-histogram distance for cuts
def hist(a): return np.concatenate([np.histogram(a[...,c],16,(0,256))[0] for c in range(3)])/(W*H)
hs=np.array([hist(x) for x in fr]); hd=np.abs(np.diff(hs,axis=0)).sum(1)
md=np.abs(np.diff(g,axis=0)).mean((1,2))
cut=(hd>0.5)|((md>28)&(hd>0.3))
idx=np.where(cut)[0]+1
# merge cuts within 3 frames (transitions)
cuts=[];
for i in idx:
    if not cuts or i-cuts[-1]>3: cuts.append(int(i))
bounds=[0]+cuts+[n]; lens=np.diff(bounds)/30
# motion within shots: median frame diff excluding cuts
mask=np.ones(len(md),bool); 
for c in cuts: mask[max(0,c-2):c+2]=False
still=(md[mask]<0.6).mean()
print(json.dumps(dict(file=f.split('/')[-1][:40],frames=n,dur=round(n/30,2),shots=len(lens),cuts_per_10s=round(len(cuts)/(n/30)*10,2),
  shot_len_median=round(float(np.median(lens)),2),shot_len_min=round(float(lens.min()),2),shot_len_max=round(float(lens.max()),2),
  motion_median=round(float(np.median(md[mask])),2),frac_near_still=round(float(still),2),cut_times=[round(c/30,2) for c in cuts])))

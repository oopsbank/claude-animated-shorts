import sys,subprocess,numpy as np
f=sys.argv[1]; sr=16000
x=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar',str(sr),'-f','s16le','-'],capture_output=True).stdout,np.int16).astype(np.float32)/32768
hop=int(0.02*sr); fr=x[:len(x)//hop*hop].reshape(-1,hop)
rms=20*np.log10(np.sqrt((fr**2).mean(1))+1e-6)
# speech band energy (300-3400Hz) vs full via FFT per 40ms
win=int(0.04*sr); n=len(x)//win; X=np.abs(np.fft.rfft(x[:n*win].reshape(n,win)*np.hanning(win),axis=1)); fq=np.fft.rfftfreq(win,1/sr)
sp=X[:,(fq>300)&(fq<3400)].sum(1); lo=X[:,fq<200].sum(1)
e=20*np.log10(X.sum(1)+1e-6); thr=np.percentile(e,90)-18
voiced=e>thr
# syllable-ish peaks of speech band envelope
env=np.convolve(sp,np.ones(3)/3,'same'); pk=((env[1:-1]>env[:-2])&(env[1:-1]>=env[2:])&(env[1:-1]>np.percentile(env,55))).sum()
# pauses: runs of non-voiced >= 0.2s
runs=[];c=0
for v in voiced:
    if not v: c+=1
    else:
        if c: runs.append(c*0.04)
        c=0
p=[r for r in runs if r>=0.2]
# music bed level: frames quieter than speech (10th pct) relative to median
print(f"{f.split('/')[-1][:38]:38s} voiced {voiced.mean()*100:.0f}% | syllable-peaks/s {pk/(len(x)/sr):.1f} | pauses>=0.2s: {len(p)}, total {sum(p):.1f}s, longest {max(p) if p else 0:.2f}s | bed (p10 vs p50 rms) {np.percentile(rms,10)-np.percentile(rms,50):.0f} dB | bass share {lo.sum()/X.sum()*100:.0f}%")

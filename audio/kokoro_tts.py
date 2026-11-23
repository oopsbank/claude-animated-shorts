import sys, re, json, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
k = Kokoro('models/kokoro-v1.0.onnx', 'models/voices-v1.0.bin')
voice, speed, outdir = sys.argv[1], float(sys.argv[2]), sys.argv[3]
text = open('vo.txt').read().strip()
sents = re.split(r'(?<=[.?!])\s+(?=[A-Z"])', text)
sr = 24000; parts = []; words = []; t = 0.0
lead = 0.05
parts.append(np.zeros(int(lead*sr))); t = lead
for s in sents:
    a, sr = k.create(s, voice=voice, speed=speed, lang='en-us')
    nz = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0]-240): nz[-1]+480]
    dur = len(a)/sr; ws = s.split()
    # weight words by letters (+ small base), pauses after commas
    wts = [len(re.sub(r'[^A-Za-z0-9]', '', w)) + 2 + (3 if w.endswith((',', ':', ';')) else 0) for w in ws]
    tot = sum(wts); x = t + .01; span = dur - .03
    for w, wt in zip(ws, wts):
        d = span * wt / tot; words.append({"word": w, "start": round(x, 3), "end": round(x + d*.92, 3)}); x += d
    parts += [a, np.zeros(int(.18*sr))]; t += dur + .18
y = np.concatenate(parts)
sf.write(outdir + '/voice_24k.wav', y, sr)
json.dump(words, open(outdir + '/words.json', 'w'), indent=0)
print(len(words), 'words; last end', words[-1]['end'], 'total', round(len(y)/sr, 2))

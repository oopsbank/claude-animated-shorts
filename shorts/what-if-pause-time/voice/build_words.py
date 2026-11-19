# Splice the separately generated line (ins.wav) into voice.wav after "Top marks." and build words.json from the
# character alignments. Writes voice.wav (spliced), words.json [{w, s, e}].
import json, numpy as np
from scipy.io import wavfile


def rd(p):
    r, a = wavfile.read(p)
    return (a.astype(float) / 32768.0 if a.dtype == np.int16 else a.astype(float)), r

SR = 48000


def words(al, off=0.0):
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, cur = [], None
    for c, s, e in zip(ch, st, en):
        if c.isspace():
            if cur: out.append(cur); cur = None
            continue
        if cur is None: cur = {"w": "", "s": s + off, "e": e + off}
        cur["w"] += c; cur["e"] = e + off
    if cur: out.append(cur)
    return out


A = json.load(open("alignment.json")); B = json.load(open("alignment_ins.json"))
v, _ = rd("voice_orig.wav"); x, _ = rd("ins.wav")
W = words(A)
k = next(i for i, w in enumerate(W) if w["w"] == "marks.")
cut = (W[k]["e"] + W[k + 1]["s"]) / 2        # middle of the pause after "Top marks."
gap_before, gap_after = 0.30, 0.15
# trim leading/trailing silence of the insert
env = np.abs(x) > 0.01
i0 = max(0, np.argmax(env) - int(0.03 * SR)); i1 = min(len(x), len(x) - np.argmax(env[::-1]) + int(0.08 * SR))
xi = 0.86 * x[i0:i1]; lead = i0 / SR
ins = np.concatenate([np.zeros(int(gap_before * SR)), xi, np.zeros(int(gap_after * SR))])
c = int(cut * SR)
out = np.concatenate([v[:c], ins, v[c:]])
wavfile.write("voice.wav", SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
d = len(ins) / SR
WI = words(B, cut + gap_before - lead)
W2 = W[:k + 1] + WI + [dict(w, s=w["s"] + d, e=w["e"] + d) for w in W[k + 1:]]
for w in W2: w["s"], w["e"] = round(w["s"], 3), round(w["e"], 3)
json.dump(W2, open("words.json", "w"), indent=0)
print(len(W2), "words, voice", round(len(out) / SR, 2), "s; insert at", round(cut, 2), "+", round(d, 2))

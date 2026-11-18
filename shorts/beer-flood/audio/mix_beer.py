# Final mix: voice (gain only) + music (ducked under the words, -10 LU under the voice) + SFX (-9 LU), master to
# -15 LUFS integrated, look-ahead limiter at -1.2 dBTP, exactly the picture length (1948 f @ 30 fps), 48 kHz stereo.
import json
import numpy as np
from scipy import ndimage
from dsp import SR, ns, read_wav, write_wav, integrated, true_peak, dbg, lp

N = ns(1948 / 30)
def load(p):
    x, sr = read_wav(p)
    assert sr == SR, (p, sr)
    x = np.atleast_2d(x)
    if x.shape[0] > x.shape[1]: x = x.T
    if x.shape[0] == 1: x = np.vstack([x, x])
    y = np.zeros((2, N)); y[:, :min(N, x.shape[1])] = x[:, :N]
    return y
voice, music, sfx = load("../voice/voice.wav"), load("music.wav"), load("sfx.wav")
words = json.load(open("../voice/words.json"))
# speech mask from words.json (not the audio): 0.12 s attack, 0.35 s release
m = np.zeros(N)
for w in words: m[ns(max(0, w["s"] - 0.12)):ns(w["e"] + 0.35)] = 1
m = ndimage.uniform_filter1d(m, ns(0.15))
duck = dbg(-4.0 * m)
LV = integrated(voice)
music = music * dbg(LV - 10 - integrated(music)) * duck
sfx = sfx * dbg(LV - 9 - integrated(sfx))
# per-section rides (dB): quiet bits of the score up, the flood's roar a little under the words, the hook roar up
tt_ = np.arange(N) / SR
ride = lambda pts: dbg(np.interp(tt_, [a for a, _ in pts], [b for _, b in pts]))
music = music * ride([(0, 0), (4.3, 0), (4.6, 0), (33.0, 0), (33.6, 4), (36.9, 4), (37.2, 6), (46.7, 6), (47.4, 5), (57.4, 5), (57.8, 2), (64.95, 2)])
sfx = sfx * ride([(0, 4), (3.6, 3), (4.4, 0), (21.5, 0), (21.8, -2), (32.5, -2), (33.0, 0), (64.95, 0)])
mix = voice + music + sfx
mix *= dbg(-15 - integrated(mix))
# look-ahead limiter: gain = min over the next 3 ms of ceiling/|x|, release 80 ms
ceil = dbg(-1.6)
pk = np.abs(mix).max(0)
g = np.minimum(1, ceil / np.maximum(pk, 1e-9))
g = ndimage.minimum_filter1d(g, ns(0.003), origin=-(ns(0.003) // 2 - 1))
rel = np.exp(-1 / (0.08 * SR)); out = np.empty_like(g); cur = 1.0
for i in range(len(g)):
    cur = g[i] if g[i] < cur else cur * rel + (1 - rel) * g[i]
    out[i] = cur
mix *= out
for k, x in [("voice", voice), ("music", music), ("sfx", sfx)]: write_wav(f"stem_{k}.wav", x * dbg(-15 - integrated(voice + music + sfx)), 24)
write_wav("mix.wav", mix, 24)
print("mix: %.2f s, %.1f LUFS, true peak %.2f dBTP" % (mix.shape[1] / SR, integrated(mix), true_peak(mix)))

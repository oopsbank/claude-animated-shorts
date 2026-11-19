# Measures value/colour/detail of frames against the reference targets in references/reports/recent_style_2026-11.md.
# usage: python -I frame_stats.py img1.png [img2.jpg ...]
import sys
import numpy as np
from PIL import Image
TARGET = {'lum': (0.40, 0.55), 'p98': (0.85, 1.0), 'sat': (0.35, 0.50), 'cool': (0.0, 0.35), 'edge': (0.04, 1.0)}
def stats(p):
    im = Image.open(p).convert('RGB').resize((270, 480)); a = np.asarray(im).astype(np.float32) / 255
    m = np.ones(a.shape[:2], bool); m[288:360, :] = False                   # ignore a caption band if present
    L = (a @ np.array([.2126, .7152, .0722]))[m]
    hsv = np.asarray(im.convert('HSV')).astype(np.float32) / 255; S = hsv[..., 1][m]; Hh = hsv[..., 0][m]
    g = np.asarray(im.convert('L')).astype(np.float32)
    e = ((np.abs(np.diff(g, axis=1))[:-1, :] + np.abs(np.diff(g, axis=0))[:, :-1]) > 60).mean()
    return {'lum': L.mean(), 'p98': np.percentile(L, 98), 'sat': S.mean(),
            'cool': ((Hh > .5) & (Hh < .75) & (S > .35)).mean(), 'edge': e}
ok_all = True
for p in sys.argv[1:]:
    s = stats(p); bad = [k for k, (lo, hi) in TARGET.items() if not lo <= s[k] <= hi]; ok_all &= not bad
    print(p, ' '.join(f'{k}={v:.2f}' for k, v in s.items()), 'PASS' if not bad else 'FAIL ' + ','.join(bad))
sys.exit(0 if ok_all else 1)

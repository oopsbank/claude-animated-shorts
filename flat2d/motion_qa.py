"""Motion QA for a rendered frames dir: frozen spans and pops.

usage: .venv/bin/python flat2d/motion_qa.py FRAMES_DIR [cut times in s ...]
Prints the mean abs difference between consecutive frames (0-255). A frozen frame is a diff < 0.25;
a pop is a diff > 4x the local median that is not on a cut or an impact (-1..+6 frames: render.py's cut
punch-in settles over 6 frames, its flash over 3). Frozen spans longer than 0.4 s (12 frames) or any pop -> FAIL.
"""
import os, sys
import numpy as np
from PIL import Image

d = sys.argv[1]; args = sys.argv[2:]
imp = [float(c) for c in args[args.index('--impacts') + 1:]] if '--impacts' in args else []
cuts = [float(c) for c in (args[:args.index('--impacts')] if '--impacts' in args else args)] + imp
fs = sorted(f for f in os.listdir(d) if f.endswith('.png'))
prev = None; diffs = []
for f in fs:
    a = np.asarray(Image.open(os.path.join(d, f)).convert('L').resize((270, 480)), np.float32)
    if prev is not None: diffs.append(float(np.abs(a - prev).mean()))
    prev = a
diffs = np.array(diffs); cutf = [round(c * 30) for c in cuts]
frozen = [i + 1 for i, v in enumerate(diffs) if v < .25]
pops = []
for i, v in enumerate(diffs):
    med = np.median(diffs[max(0, i - 8):i + 9])
    if v > 4 * med and v > 3 and not any(-1 <= i + 1 - c <= 6 for c in cutf): pops.append((i + 1, round(v, 2), round(float(med), 2)))
print(f'frames {len(fs)}  diff min {diffs.min():.2f} median {np.median(diffs):.2f} max {diffs.max():.2f}')
print('frozen frames (<0.25):', frozen[:40], '...' if len(frozen) > 40 else '')
print('pops (not on cuts):', pops)
run, longest = 0, 0
for i, v in enumerate(diffs):
    run = run + 1 if v < .25 else 0; longest = max(longest, run)
print(f'longest frozen span: {longest} frames ({longest / 30:.2f} s)')
print('PASS' if longest <= 12 and not pops else 'FAIL')

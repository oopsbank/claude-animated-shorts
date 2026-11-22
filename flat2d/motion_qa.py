"""Motion QA for a rendered frames dir: frozen spans and pops.

usage: .venv/bin/python flat2d/motion_qa.py FRAMES_DIR [cut times in s ...]
Prints the mean abs difference between consecutive frames (0-255). A frozen frame is a diff < 0.25;
a pop is a diff > 4x the local median that is not on a cut (+-1 frame).
"""
import os, sys
import numpy as np
from PIL import Image

d = sys.argv[1]; cuts = [float(c) for c in sys.argv[2:]]
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
    if v > 4 * med and v > 3 and not any(abs(i + 1 - c) <= 1 for c in cutf): pops.append((i + 1, round(v, 2), round(float(med), 2)))
print(f'frames {len(fs)}  diff min {diffs.min():.2f} median {np.median(diffs):.2f} max {diffs.max():.2f}')
print('frozen frames (<0.25):', frozen[:40], '...' if len(frozen) > 40 else '')
print('pops (not on cuts):', pops)

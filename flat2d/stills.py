"""One captioned still per shot (the review gate's input), at a chosen point of each shot.

usage: .venv/bin/python flat2d/stills.py WORDS.json OUTDIR [--size 540x960] [--at 0.7] [shot ...]
--at: fraction of the shot length (default 0.7: the shot's main action has landed). Also writes sheet.png.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import render

a = sys.argv[1:]; words, out = a[0], a[1]
opt = lambda k, d: a[a.index(k) + 1] if k in a else d
size = tuple(int(v) for v in opt('--size', '540x960').split('x')); at = float(opt('--at', .7))
only = [x for x in a[2:] if not x.startswith('--') and not x.replace('.', '').replace('x', '').isdigit()]
os.makedirs(out, exist_ok=True)
film = render.Film(words)
ims = []
for name, t0, t1, *_ in film.shots:
    if only and name not in only: continue
    T = t0 + (t1 - t0) * (render.bf.STILL_AT.get(name, at) if '--at' not in a else at)
    im = film.frame(T).resize(size, Image.LANCZOS)
    im.save(os.path.join(out, f'{name}.png')); ims.append(im); print(name, round(T, 2), flush=True)
cols = min(len(ims), 7); th = (216, 384)
S = Image.new('RGB', (cols * (th[0] + 6) + 6, ((len(ims) + cols - 1) // cols) * (th[1] + 6) + 6), (24, 24, 30))
for i, im in enumerate(ims): S.paste(im.resize(th, Image.LANCZOS), (6 + i % cols * (th[0] + 6), 6 + i // cols * (th[1] + 6)))
S.save(os.path.join(out, 'sheet.png'))

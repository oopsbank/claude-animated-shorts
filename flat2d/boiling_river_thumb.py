"""Caption-free thumbnail frame for the boiling river: the steaming river, the GEOLOGIST with his probe, a big
thermometer near 100 °C. Headline added by tools/thumbnail.py.

usage: .venv/bin/python flat2d/boiling_river_thumb.py OUT.png
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import boiling_river as B
import jungle as J
from blood_falls_2 import draw_x
from blood_falls import finish
import anim

B.HIDE_UI = True
u = 2.0
img = Image.new('RGBA', (J.W, J.H))
B.bank_scene(img, u, 0, steam_k=.9, horizon=900)
d = ImageDraw.Draw(img)
J.ground_bank(img, [(-60, 1480), (260, 1520), (470, 1600), (600, 1720), (680, 1990), (-60, 1990)])
pose = dict(anim.POSES['stand'], armR=(-38, -18))
g = B.geologist(img, u, pose, 'surprised', 250, 1640, .82, look=.55, lean=5, label_on=False)
hx, hy, _ = g['hands']['R']; px, py = hx + 170, hy + 260
d = ImageDraw.Draw(img)
d.line([(hx, hy), (px, py)], fill=J.INK, width=16); d.line([(hx, hy), (px, py)], fill=(220, 226, 230), width=8)
d.ellipse([hx - 18, hy - 18, hx + 18, hy + 18], fill=(246, 246, 242), outline=J.INK, width=4)
img = finish(img, u, 1.0, 540, 1200, vig=(.32, (20, 40, 30)))
J.thermometer(img, 900, 820, 860, .97, u, w=86, fs=42, label_side=-1)
img.convert('RGB').save(sys.argv[1])

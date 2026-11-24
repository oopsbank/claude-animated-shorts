"""Caption-free thumbnail frame for Moth Light: a big hawk moth banking round the glowing violet UV lamp in the night
cloud forest, other moths orbiting with long-exposure light trails; the top third kept dark for the headline that
tools/thumbnail.py adds (THEY'RE NOT / ATTRACTED).

usage: .venv/bin/python flat2d/moth_light_thumb.py OUT.png
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import moth_light as L
import moth as M
import cloudforest as CF
from kit import W, H
from blood_falls import finish

L.HIDE_UI = True
w = 3.3
lamp = (560, 1080)
img = Image.new('RGBA', (W, H))
CF.forest(img, w, 0, lamp=lamp, lamp_k=1.0)
orbs = L.default_orbs(21, 12, R=(240, 430), s=(100, 150), y=(-160, 200))
L.orbiters(img, w, lamp, orbs, front=False, trail_t=1.8)
CF.uv_lamp(img, lamp[0], lamp[1], 1.15, t=w, ground=2100)
CF.spores(img, w, lamp, 90, r=520)
L.orbiters(img, w, lamp, orbs, front=True, trail_t=1.8)
# the hero: big, banking in front of the lamp, a long arc of light behind it
a0 = math.radians(62)
pts = [(lamp[0] + 380 * math.cos(a0 + k * .06), lamp[1] + 380 * math.sin(a0 + k * .06) * .9) for k in range(34)][::-1]
M.trail(img, pts, (214, 190, 255), 12, 1.0, wave=3, phase=2)
x, y = pts[-1]
M.put(img, x, y, 300, heading=-28, view="top", roll=-18, flap=.5, spread=.5, blur=0, lamp=(lamp[0] - x, lamp[1] - y, -.4),
      lamp_k=.45, glow=(150, 110, 255), glow_a=.35)
CF.foreground(img, w, 0, seed=12)
a = np.asarray(img, np.float32)
yy = np.linspace(0, 1, H)[:, None, None]
a[..., :3] *= (.5 + .5 * np.clip((yy - .08) / .3, 0, 1))
img = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
img = finish(img, w, 1.0, 540, 1100, vig=(.32, (6, 4, 20)))
img.convert('RGB').save(sys.argv[1])

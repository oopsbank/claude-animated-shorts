"""Caption-free thumbnail frame for Plane Windows (the Producer's brief, approved by the Director): the hero image
itself, readable at a glance without text — the Comet fuselage sunk in the giant water tank of the 1954 test hangar,
its wings sticking out through the tank walls on jacks, engineers on the gantries, skylight shafts and caustics. A
steeper angle than frame 0 so the airliner's cross shape (fuselage + both wings) reads instantly; the top third is
kept darker for the headline that tools/thumbnail.py adds (WHY SINK / A PLANE?).

usage: .venv/bin/python flat2d/plane_windows_thumb.py OUT.png
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import persp as P3
import hangar as Hg
import plane_windows as PW
import cine

PW.HIDE_UI = True
T = 1.3
cam = P3.Cam((-17.0, -2.2, 46.0), (15.0, .3, 0.0), 44.0, shift=(0, 260))      # high over the nose end (the roof left out)
PW.DRAWN.clear()
img, _ = Hg.scene(cam, T, chars=PW.tank_chars(T), flex=.25, swell=.0, shafts_k=1.25, motes_k=1.2, roof=False)
img = cine.grade(img, 'hangar')
img = cine.bloom(img, 200, 26, .3)
a = np.asarray(img, np.float32)
yy = np.linspace(0, 1, img.height)[:, None, None]
a[..., :3] *= (.55 + .45 * np.clip((yy - .05) / .3, 0, 1))          # darker top third for the headline
img = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
cine.vignette(img, .3, (8, 10, 18))
img.convert('RGB').save(sys.argv[1])
print(sys.argv[1])

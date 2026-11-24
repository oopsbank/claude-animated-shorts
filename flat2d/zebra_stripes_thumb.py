"""Caption-free thumbnail frame for Zebra Stripes: the brown horse in the zebra-striped coat (head bare) big in the
2016 English field, horse flies circling it with dotted trails, one fly bonking off the coat; the top third kept
clear (sky) for the headline that tools/thumbnail.py adds (IT'S NOT / CAMOUFLAGE).

usage: .venv/bin/python flat2d/zebra_stripes_thumb.py OUT.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zebra_stripes as Z
import animals as A
from blood_falls import finish

Z.HIDE_UI = True
w = 1.3
hs, hx, hgy = 580, 740, 1700
img, hi = Z.field_world(w, 0.0, hs=hs, hx=hx, hgy=hgy, fg=True, flies=False)
fx, fy = hx + 40, hgy - hs * .8
Z.swarm(img, w, fx, fy, hs * .9, hs * .42, 7, 96, seed=5, speed=.9, r=8)
# one fly bonking off the coat
A.put_fly(img, hx + 120, hgy - hs * 1.05, 120, ang=25, wing='blur', ph=2.0)
Z.bonk_star(img, hx + 60, hgy - hs * .92, .35, 1.0)
img = finish(img, w, 1.0, 540, 1200, vig=(.24, (30, 40, 30)))
img.convert('RGB').save(sys.argv[1])

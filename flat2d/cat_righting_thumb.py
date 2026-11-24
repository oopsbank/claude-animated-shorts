"""Caption-free thumbnail frame for Cat righting: the new cat big, UPSIDE DOWN in mid-air with its face visible, lit
against the black velvet in Marey's 1894 lab; Marey on the stool below-left, eyes wide (beard on the chin).
Headline added by tools/thumbnail.py (THIS CAT / BROKE PHYSICS? / IN 1894, top third).

usage: .venv/bin/python flat2d/cat_righting_thumb.py OUT.png
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import cat_righting as B
import cat as C
from kit import W, H, radial, layer
from anim import POSES
from blood_falls import finish

B.HIDE_UI = True
img = Image.new('RGBA', (W, H))
B.lab(img, .6, 0, cam_xy=(960, 1500), warm=.9, velvet_glow=(600, 950))
pose = dict(POSES['stand'], armL=(160, 150), armR=(130, 150))
B.stool(img, 170, 1880)
B.marey(img, .6, pose, 'surprised', 170, 1880, .82, look=.6, lean=8, label_on=False, idle=0)
radial(img, 590, 930, 460, (255, 232, 196), .34, 1.5)
for i, x in enumerate((470, 560, 650, 740)):                       # falling streaks
    lay = layer(); ImageDraw.Draw(lay).line([(x, 520), (x, 640)], fill=(255, 240, 210, 110), width=8); img.alpha_composite(lay)
C.put_cat(img, 660, 880, 265, phf=math.pi - .18, phb=math.pi + .05, tuckf=.45, tuckb=.35, bend=14, rot=9, tail_ph=4.2)
img = finish(img, .6, 1.0, 560, 950, vig=(.42, (12, 8, 14)))
img.convert('RGB').save(sys.argv[1])

"""Caption-free thumbnail frame for Flamingo One Leg: a big flamingo asleep on one thin leg in the dawn salt lagoon
(head laid on its back, the other leg folded up), its reflection in the still water, the sun low behind; the single
leg lit with a soft glow; the top third kept clear (sky) for the headline that tools/thumbnail.py adds
(HOW IS IT / NOT FALLING?).

usage: .venv/bin/python flat2d/flamingo_one_leg_thumb.py OUT.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import flamingo_one_leg as F
import flamingo as FL
import lagoon as LG
from kit import W, H, mask, glow
from blood_falls import finish

F.HIDE_UI = True
w = 2.0
img = Image.new('RGBA', (W, H))
wc = LG.lagoon(img, w, 0, 'dawn', horizon=1120, sun=(760, 1080), flock_n=22)
FL.put(img, 200, 1330, 300, face=1, pose={'sleep': 1, 'fold': 1, 'breath': .5}, water=1324, reflect=.45, water_col=wc, t=w)
info = FL.put(img, 560, 1830, 1180, face=-1, pose={'sleep': 1, 'fold': 1, 'breath': .5}, water=1822, reflect=.5, water_col=wc, t=w,
              ret_layer=False)
m = mask(); ImageDraw.Draw(m).line([info['knee'], info['ankle'], info['foot']], fill=255, width=40)
glow(img, m, (255, 236, 170), .45, blur=26)
FL.ripples(img, info['foot'][0], 1826, 170, w)
img = finish(img, w, 1.0, 540, 1200, vig=(.26, (60, 30, 60)))
img.convert('RGB').save(sys.argv[1])

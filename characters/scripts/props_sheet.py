# Props for bike-countersteer: broom balanced on the palm (front + rear), held helmet with sticker, clipboard with text.
# usage: props_sheet.py <out.png>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bean import character, turned
from PIL import Image
I = dict(build='adult', skin='#c98e63', shirt='#2f6fb3', pants='#e8e2d0', hat='cap', hat_col='#2b2f3a', glasses=True, outfit=(('collar', '#f1efe6'),), seed=9)
D = dict(build='stout', skin='#ffe2c2', shirt='#d9452f', pants='#30343f', moustache='#6b4426', outfit=(('stripes', '#f1efe6'),), seed=4)
ims = [character(arm_pose=('hang', 'palm'), prop='broom_upright', expr='neutral', **I),
       character(arm_pose=('hang', 'palm'), prop='broom_tip_left', expr='smug', **I),
       turned('rear', pose=dict(handF=(150, 420)), prop='broom_upright', prop_hand='F', **I),
       character(arm_pose=('hold', 'hang'), prop='helmet:I STEER WITH MY HIPS', expr='pained', **D),
       character(arm_pose=('hang', 'hold'), prop='clipboard:CORNERS MADE: 0', expr='stern', **I)]
s = Image.new('RGBA', (600 * len(ims), 1000), (240, 237, 230, 255))
for i, im in enumerate(ims): s.alpha_composite(im, (600 * i, 0))
s.save(sys.argv[1])

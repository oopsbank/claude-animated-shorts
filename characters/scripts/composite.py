# Composite bean characters onto a plate using its JSON (ground_y, px_per_m). usage: composite.py plate.png out.png
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bean import character
from PIL import Image, ImageDraw, ImageFilter
plate = Image.open(sys.argv[1]).convert('RGBA')
meta = json.load(open(os.path.splitext(sys.argv[1].replace('_raw', ''))[0].replace('day_M', 'day_M_raw') + '.json')) if len(sys.argv) < 4 else json.load(open(sys.argv[3]))
H_FIG = 975 - 198            # adult figure height in card units (3.5 head-heights)
def place(img, x, height_m=1.75, tint=(1.0, 0.98, 0.95)):
    s = meta['px_per_m'] * height_m / H_FIG
    c = img.resize((int(600 * s), int(1000 * s)), Image.LANCZOS)
    r, g, b, a = c.split()
    c = Image.merge('RGBA', (r.point(lambda v: int(v * tint[0])), g.point(lambda v: int(v * tint[1])), b.point(lambda v: int(v * tint[2])), a))
    gy = meta['ground_y']
    sh = Image.new('L', plate.size, 0); ImageDraw.Draw(sh).ellipse((x - 70 * s, gy - 12 * s, x + 70 * s, gy + 12 * s), fill=110)
    plate.paste(Image.new('RGBA', plate.size, (40, 28, 30, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(6)))
    plate.alpha_composite(c, (int(x - 300 * s), int(gy - 975 * s)))
boss = character(build='stout', white_head=True, shirt='#2d2f3a', pants='#2d2f3a', hat='tophat', hat_col='#2b2d36',
                 outfit=(('buttons', 3, '#e8c45a'), ('tie', '#c0353a')), moustache='#4a3020', expr='grin', arm_pose=('hip', 'point'), seed=13, facing=0.5)
emp = character(skin='#c99067', shirt='#4a86e0', pants='#2f3540', hair='short', hair_col='#1f1a1a', outfit=(('tie', '#f2b234'),),
                expr='nervous', arm_pose=('chin', 'hang'), seed=17, facing=-0.4)
W = plate.width
place(boss, W * 0.30); place(emp, W * 0.70)
plate.convert('RGB').save(sys.argv[2], quality=92)

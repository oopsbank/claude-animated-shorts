# Renders the prototype cast sheet. usage: cast_sheet.py <out.png>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bean import character
from PIL import Image, ImageDraw, ImageFont
CAST = [
    ('Thợ điện', dict(shirt='#f2b234', pants='#3b4a6b', hat='hardhat', hat_col='#ff7a1a', outfit=(('overalls', '#2f5aa8'),), expr='neutral', arm_pose=('hang', 'hold'), prop='wrench', seed=3, facing=0.3)),
    ('Nhà khoa học', dict(skin='#f5c9a0', shirt='#7fc4c9', pants='#4a4a5a', hair='side', hair_col='#3a2a22', outfit=(('coat_open', '#f4f4f0'), ('tie', '#c0353a')), glasses=True, expr='smug', arm_pose=('hang', 'hold'), prop='clipboard', seed=5, facing=-0.3)),
    ('Bà nội', dict(skin='#ecd0b6', shirt='#8a5cd6', pants='#5a4a6a', hair='bun', hair_col='#c9c9cf', outfit=(('buttons', 3, '#f1efe6'), ('collar', '#f1efe6')), expr='smile', arm_pose=('hang', 'hold'), prop='mug', seed=8, build='stout')),
    ('Cậu bé', dict(build='kid', shirt='#3fae6a', pants='#3b5b9a', hat='cap', hat_col='#e2453c', outfit=(('stripes', '#f1efe6'),), expr='shock', arm_pose=('wave', 'wave'), seed=11, facing=0.4)),
    ('Ông chủ', dict(build='stout', white_head=True, shirt='#2d2f3a', pants='#2d2f3a', hat='tophat', hat_col='#2b2d36', outfit=(('buttons', 3, '#e8c45a'), ('tie', '#c0353a')), moustache='#4a3020', expr='grin', arm_pose=('hip', 'point'), seed=13, facing=0.5)),
    ('Nhân viên', dict(skin='#c99067', shirt='#4a86e0', pants='#2f3540', hair='short', hair_col='#1f1a1a', outfit=(('tie', '#f2b234'),), expr='nervous', arm_pose=('chin', 'hang'), seed=17, facing=-0.4)),
]
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
cw = 420; sheet = Image.new('RGBA', (cw * len(CAST), 1000 * cw // 600 + 90), (240, 237, 230, 255)); d = ImageDraw.Draw(sheet)
for i, (name, kw) in enumerate(CAST):
    im = character(**kw).resize((cw, 1000 * cw // 600), Image.LANCZOS)
    sheet.alpha_composite(im, (i * cw, 60))
    w = d.textlength(name, font=F); d.text((i * cw + (cw - w) / 2, 14), name, font=F, fill=(30, 30, 40))
sheet.save(sys.argv[1])

# Renders the cast in front, side and 3/4 views. usage: views_sheet.py <out.png>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bean import character
from PIL import Image, ImageDraw, ImageFont
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cast_sheet.py')).read()
ns = {}; exec(src[src.index('CAST ='):src.index('\nF =')], ns); CAST = ns['CAST']
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
ROWS = [('Chính diện', dict(view='front')), ('Nghiêng (phải)', dict(view='side', facing=1)),
        ('3/4 (trái)', dict(view='3q', facing=-1)), ('Nghiêng (trái)', dict(view='side', facing=-1))]
cw = 300; ch = cw * 1000 // 600; lab = 220
sheet = Image.new('RGBA', (lab + cw * len(CAST), 60 + ch * len(ROWS)), (240, 237, 230, 255)); d = ImageDraw.Draw(sheet)
for c, (name, _) in enumerate(CAST):
    w = d.textlength(name, font=F); d.text((lab + c * cw + (cw - w) / 2, 14), name, font=F, fill=(30, 30, 40))
for r, (rname, vk) in enumerate(ROWS):
    d.text((14, 60 + r * ch + ch // 2 - 20), rname, font=F, fill=(90, 90, 100))
    for c, (_, kw) in enumerate(CAST):
        kw = dict(kw); kw.update(vk)
        if vk['view'] != 'front': kw.pop('arm_pose', None)
        im = character(**kw).resize((cw, ch), Image.LANCZOS)
        sheet.alpha_composite(im, (lab + c * cw, 60 + r * ch))
sheet.save(sys.argv[1])

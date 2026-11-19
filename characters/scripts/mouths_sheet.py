# Lip-sync mouth sheet: every mouth shape over different expressions, in front, 3/4 and side views.
# usage: mouths_sheet.py <out.png>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bean import character, MOUTHS
from PIL import Image, ImageDraw, ImageFont
CH_ = dict(build='adult', skin='#c98e63', shirt='#2f6fb3', pants='#e8e2d0', hat='cap', hat_col='#2b2f3a', glasses=True, seed=9)
ROWS = [('Trước · neutral', dict(view='front', expr='neutral')), ('3/4 · grin', dict(view='3q', expr='grin', facing=1)),
        ('Nghiêng · stern', dict(view='side', expr='stern', facing=1)), ('Chớp mắt · smile', dict(view='front', expr='smile', blink=True))]
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
cw, lab = 260, 300
sheet = Image.new('RGBA', (lab + cw * (len(MOUTHS) + 1), 60 + cw * len(ROWS)), (240, 237, 230, 255)); d = ImageDraw.Draw(sheet)
for c, m in enumerate((None,) + MOUTHS):
    t = 'biểu cảm' if m is None else m; w = d.textlength(t, font=F); d.text((lab + c * cw + (cw - w) / 2, 14), t, font=F, fill=(30, 30, 40))
for r, (rn, kw) in enumerate(ROWS):
    d.text((14, 60 + r * cw + cw // 2 - 16), rn, font=F, fill=(90, 90, 100))
    for c, m in enumerate((None,) + MOUTHS):
        im = character(mouth=m, **CH_, **kw)
        bb = im.getbbox(); top = bb[1]
        face = im.crop((300 - 160, top - 10, 300 + 160, top + 310)).resize((cw - 10, cw - 10), Image.LANCZOS)
        sheet.alpha_composite(face, (lab + c * cw + 5, 60 + r * cw + 5))
sheet.save(sys.argv[1])

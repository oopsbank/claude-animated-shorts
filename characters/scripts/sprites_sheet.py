# Sheet of the video 2 engine sprites (sprites.py) on a playa-tan tile, plus t-strips for the animated ones.
# usage: sprites_sheet.py <out.png>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprites import sprite
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
STAT = ['gary_rock', 'gary_rock:askew', 'gary_buried', 'rock', 'gps_box', 'cooler', 'cooler_trophy', 'tent', 'tent_floating',
        'timelapse_cam', 'tour_sign:ALIEN ROCK TOURS · NIGHT ONLY · $20', 'tour_sign:ICE TOURS $5 (ALIEN crossed out)',
        'banner:FINAL FAIL · LIVE', 'livestream_counter:3', 'price_card:$40', 'fridge_silhouette', 'phone_silhouette']
ANIM = [('tour_sign_free:ALIEN ROCK TOURS · NIGHT ONLY', (0, 0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0)),
        ('flying_bills', (0.08, 0.16, 0.26, 0.36, 0.46, 0.58, 0.7, 0.82))]
cw, ch = 300, 300
cols = 6; rows = (len(STAT) + cols - 1) // cols
sw = 8 * 250
sheet = Image.new('RGBA', (max(cols * cw, sw), rows * (ch + 26) + len(ANIM) * 250 + 20), (226, 205, 170, 255))
d = ImageDraw.Draw(sheet)
for i, nm in enumerate(STAT):
    im = sprite(nm, 0.3, k=0.5)
    im.thumbnail((cw - 20, ch - 20))
    if im.height < 140 and im.width * 2 <= cw - 20:   # small props shown enlarged
        im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS); nm = nm + ' (x2)'
    x, y = (i % cols) * cw, (i // cols) * (ch + 26)
    d.line([(x + 10, y + 26 + ch - 12), (x + cw - 10, y + 26 + ch - 12)], fill=(170, 140, 100), width=2)
    sheet.alpha_composite(im, (x + (cw - im.width) // 2, y + 26 + ch - 12 - im.height))
    d.text((x + 8, y + 4), (nm.split(':')[0] + ('*' if ':' in nm else ''))[:24], font=F, fill=(30, 20, 30))
y0 = rows * (ch + 26) + 10
for j, (nm, ts) in enumerate(ANIM):
    for i, t in enumerate(ts):
        im = sprite(nm, t, k=0.195 if 'sign' in nm else 0.24)
        x, y = i * 250, y0 + j * 250
        sheet.alpha_composite(im, (x + (250 - im.width) // 2, y + 230 - im.height))
        d.text((x + 6, y + 2), (f'{nm.split(":")[0]}  ' if i == 0 else '') + ('(gone by 0.9) ' if i == 7 and 'bills' in nm else '') + f't={t:g}', font=F, fill=(30, 20, 30))
sheet.save(sys.argv[1])

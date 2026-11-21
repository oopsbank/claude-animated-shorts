# Video 2 (sailing-stones) wardrobe sheet: the antennae hat (up / half / droop, side, rear), seated='cooler', and every
# new held prop on the cast that uses it in shots.json.  usage: v2_sheet.py <out.png> [crop_out.png]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bean import character
from PIL import Image, ImageDraw, ImageFont
CAST = {   # mirrors scripts/sailing-stones/build.py CAST
    'kip':   dict(build='adult', skin='#f1c9a5', shirt='#3a8fd1', pants='#3b3b4f', hat='beanie', hat_col='#e8613c', seed=21),
    'lou':   dict(build='stout', skin='#8d5a3b', shirt='#f2b134', pants='#2f4b3a', hat='cap', hat_col='#2f6b4f', glasses=True, seed=22),
    'guide': dict(build='stout', skin='#ffd9b8', shirt='#7a3fb0', pants='#2b2f3a', hat='antennae', hat_col='#6fd16a', moustache='#5a3a22', outfit=('collar',), seed=23),
    'tour1': dict(build='adult', skin='#f6d2b0', shirt='#3fb37f', pants='#2f3f6b', hat='antennae', hat_col='#6fd16a', seed=31),
    'tour2': dict(build='kid', skin='#b87a55', shirt='#e85d8a', pants='#30343f', hat='antennae', hat_col='#6fd16a', seed=32),
    'tour3': dict(build='stout', skin='#ffe2c2', shirt='#2fb3c9', pants='#4a3b2f', hat='antennae', hat_col='#6fd16a', seed=33),
}
def C(cid, **kw): d = dict(CAST[cid]); d.update(kw); return d
ROWS = [
    [('antennae up', C('guide', expr='smug', arm_pose=('hip', 'point'))), ('droop 0.5', C('guide', expr='neutral', antennae=0.5)),
     ('antennae droop', C('guide', expr='neutral', antennae='droop')), ('sway +14', C('tour2', expr='grin', arm_pose=('wave', 'wave'), antennae_sway=14)),
     ('side', C('tour1', view='side', expr='smile')), ('rear', C('guide', view='rear')),
     ('seated cooler', C('kip', seated='cooler', arm_pose=('hold', 'hold'), prop='frying_pan', expr='stern')),
     ('seated cooler', C('lou', seated='cooler', arm_pose=('hold', 'hold'), prop='gps_box', expr='stern'))],
    [('gps_box', C('kip', arm_pose=('hold', 'hang'), prop='gps_box')), ('screwdriver', C('lou', arm_pose=('hold', 'hang'), prop='screwdriver')),
     ('googly_eyes', C('lou', arm_pose=('hold', 'hang'), prop='googly_eyes', expr='smile')), ('mug', C('kip', arm_pose=('hold', 'hang'), prop='mug')),
     ('laptop', C('kip', arm_pose=('hold', 'hang'), prop='laptop')), ('frying_pan', C('kip', arm_pose=('hang', 'hold'), prop='frying_pan', expr='stern')),
     ('ticket', C('guide', arm_pose=('hold', 'point'), prop='ticket', expr='smug')), ('cash_fan', C('guide', arm_pose=('hold', 'hip'), prop='cash_fan', expr='grin'))],
    [('camera', C('tour3', arm_pose=('hold', 'hang'), prop='camera', expr='smile')), ('flashlight', C('tour1', arm_pose=('wave', 'hold'), prop='flashlight', expr='grin')),
     ('phone x2', C('tour1', arm_pose=('hold', 'hold'), prop='phone', expr='grin')), ('selfie_stick', C('guide', arm_pose=('hold', 'point'), prop='selfie_stick', expr='grin')),
     ('megaphone', C('guide', arm_pose=('hang', 'hold'), prop='megaphone', expr='grin')), ('flag:ICE TOURS', C('guide', arm_pose=('point', 'hold'), prop='flag:ICE TOURS', expr='grin')),
     ('air_hockey_mallet', C('lou', arm_pose=('hold', 'hang'), prop='air_hockey_mallet')), ('gary_rock:askew', C('kip', arm_pose=('hold', 'hold'), prop='gary_rock:askew', expr='smug'))],
    [('night: flashlight', C('tour1', arm_pose=('wave', 'hold'), prop='flashlight', expr='grin')), ('night: ticket', C('guide', arm_pose=('hold', 'point'), prop='ticket', expr='smug')),
     ('night: camera', C('tour3', arm_pose=('hold', 'hang'), prop='camera', expr='smile')), ('night: kid', C('tour2', arm_pose=('wave', 'wave'), expr='grin')),
     ('phone x2', C('tour3', arm_pose=('hold', 'hold'), prop='phone', expr='smile')), ('laptop x2', C('kip', arm_pose=('hold', 'hold'), prop='laptop', expr='shock')),
     ('camera x2', C('tour1', arm_pose=('hold', 'hold'), prop='camera', expr='grin')), ('gps_box rear', C('kip', view='rear', arm_pose=('hold', 'hang'), prop='gps_box'))],
]
NIGHT = 3
if __name__ == '__main__':
    cw = 300; ch = 500
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
    sheet = Image.new('RGBA', (cw * 8, (ch + 34) * len(ROWS)), (240, 237, 230, 255)); d = ImageDraw.Draw(sheet)
    full = []
    for r, row in enumerate(ROWS):
        if r == NIGHT: d.rectangle((0, r * (ch + 34), cw * 4, (r + 1) * (ch + 34)), fill=(36, 34, 78))
        for i, (name, kw) in enumerate(row):
            im = character(**kw); full.append(im)
            sheet.alpha_composite(im.resize((cw, ch), Image.LANCZOS), (i * cw, r * (ch + 34) + 30))
            w = d.textlength(name, font=F); d.text((i * cw + (cw - w) / 2, r * (ch + 34) + 6), name, font=F, fill=(230, 230, 240) if (r == NIGHT and i < 4) else (30, 30, 40))
    sheet.save(sys.argv[1])
    if len(sys.argv) > 2:   # 2x-ish crops of the upper bodies (heads, hands, props) for the joint review
        cs = Image.new("RGBA", (600 * 8, 640 * 4), (240, 237, 230, 255))
        for k, im in enumerate(full):
            cs.alpha_composite(im.crop((0, 40, 600, 680)), ((k % 8) * 600, (k // 8) * 640))
        cs.save(sys.argv[2])

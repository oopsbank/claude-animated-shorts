# Self-check: composite the test stickman on every plate (scaled from its JSON) and build a contact sheet.
# usage: .venv/bin/python -I blender/sets/check.py <plates_dir> <sheet.jpg> [--bare] [--col 360]
import sys, os, json, glob
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SOLE_Y = 975
# Test character: the bean-head cast (characters/scripts/bean.py; BEAN_DIR overrides), else the old stickman.
_bd = os.environ.get('BEAN_DIR', os.path.join(ROOT, 'characters/scripts'))
try:
    sys.path.insert(0, _bd); from bean import character
    SPRITE = character(skin='#ffe2c2', shirt='#4a86e0', pants='#2f3540', hair='short', hair_col='#1f1a1a', expr='neutral', seed=17)
    HEAD_Y = 198                    # adult crown y (3.5 head-heights)
except Exception as e:
    print('bean cast not found, using stickman:', e)
    SPRITE = Image.open(os.path.join(ROOT, 'stickman/stick_neutral.png')).convert('RGBA'); HEAD_Y = 59

def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def composite(plate, js, x_frac=None):
    im = Image.open(plate).convert('RGB'); Wp, Hp = im.size; k = Wp / 1080
    x = (x_frac if x_frac is not None else js.get('stand_x', 0.5)) * Wp
    gy = js['ground_y'] * k; hpx = js['px_per_m'] * 1.75 * k
    s = hpx / (SOLE_Y - HEAD_Y)
    spr = SPRITE.resize((max(1, int(600 * s)), max(1, int(1000 * s))), Image.LANCZOS)
    t = hexrgb(js['tint']); r, g, b, a = spr.split()   # tint toward the scene light (multiply, 20%)
    tinted = Image.merge('RGB', [ch.point(lambda v, c=c: int(v * (0.80 + 0.20 * c / 255))) for ch, c in zip((r, g, b), t)])
    sh = Image.new('L', im.size, 0); d = ImageDraw.Draw(sh)    # soft contact shadow
    d.ellipse([x - 0.13 * hpx, gy - 0.025 * hpx, x + 0.13 * hpx, gy + 0.025 * hpx], fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(max(1, 0.012 * hpx)))
    im = Image.composite(Image.new('RGB', im.size, (10, 8, 20)), im, sh)
    im.paste(tinted, (int(x - 300 * s), int(gy - SOLE_Y * s)), a)
    return im

if __name__ == '__main__':
    d, out = sys.argv[1], sys.argv[2]; bare = '--bare' in sys.argv
    col = int(sys.argv[sys.argv.index('--col') + 1]) if '--col' in sys.argv else 360
    plates = sorted(p for p in glob.glob(os.path.join(d, '*__*__*.png')))
    cams = list(dict.fromkeys(os.path.basename(p).split('__')[1] for p in plates))
    lights = list(dict.fromkeys(os.path.basename(p).split('__')[2][:-4] for p in plates))
    rowh = int(col * 16 / 9)
    sheet = Image.new('RGB', (col * len(lights), (rowh + 22) * len(cams)), (20, 20, 24)); dr = ImageDraw.Draw(sheet)
    for p in plates:
        _, c, l = os.path.basename(p)[:-4].split('__')
        js = json.load(open(p[:-4] + '.json'))
        im = Image.open(p).convert('RGB') if bare else composite(p, js)
        cx, cy = lights.index(l) * col, cams.index(c) * (rowh + 22)
        sheet.paste(im.resize((col, rowh), Image.LANCZOS), (cx, cy + 22))
        dr.text((cx + 6, cy + 5), f'{c} / {l}  gy={js["ground_y"]:.0f} ppm={js["px_per_m"]:.0f}', fill=(230, 230, 230))
    sheet.save(out, quality=90); print(out, sheet.size)
    if '--comp' in sys.argv:   # full-size composites for frame_stats and the reviewer
        cd = sys.argv[sys.argv.index('--comp') + 1]; os.makedirs(cd, exist_ok=True)
        for p in plates: composite(p, json.load(open(p[:-4] + '.json'))).save(os.path.join(cd, os.path.basename(p)[:-4] + '.jpg'), quality=92)

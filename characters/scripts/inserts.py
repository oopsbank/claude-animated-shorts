# Close-up insert cards for the engine to cut to. broom_insert(): a hand balancing a broom on its palm, the broom
# filling >= 70% of the frame height (the bike-countersteer analogy: "to tip it left, flick your hand right first").
# usage: inserts.py <out_dir>
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from bean import Canvas, INK, S, hexrgb, mix, _broom, bend_path

POSES = {   # hand x (fraction of width), broom tilt (deg, + = top to screen right), motion lines
    'broom_upright':     dict(hx=0.55, tilt=0, flick=0),
    'broom_tip_left':    dict(hx=0.72, tilt=-15, flick=0),
    'broom_flick_right': dict(hx=0.66, tilt=-11, flick=1),     # the hand jumps right, the broom's top lags: it tips left
    'broom_tip_right':   dict(hx=0.28, tilt=15, flick=0),
    'broom_flick_left':  dict(hx=0.36, tilt=11, flick=-1),
}

def _hand(C, hx, hy, u, skin, alpha=255):
    """An open hand, palm up, seen from a little below the palm's edge: a flat rounded palm, four finger bumps on the
    far edge and a thumb on the near side, in skin with plum ink. (Close-up inserts only; the cast's normal hand is a dot.)"""
    lay = Image.new('RGBA', C.im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    col = hexrgb(skin) + (255,); ink = INK + (255,); w_ = 34 * u / 2.36; h_ = 11 * u / 2.36; lw = int(3.4 * u / 2.36 * S)
    parts = [('e', (hx - w_, hy - h_, hx + w_, hy + h_))]                                     # palm
    for i in range(4):                                                                       # fingers along the far (right) edge
        fx = hx + w_ * 0.55 + i * 0; fy = hy - h_ * 0.7 + i * h_ * 0.5
        parts.append(('e', (hx + w_ * (0.55 + 0.1 * i) - 9 * u / 2.36, hy - h_ * 1.1 + i * h_ * 0.55, hx + w_ * (1.25 - 0.05 * i), hy - h_ * 0.35 + i * h_ * 0.55)))
    parts.append(('e', (hx - w_ * 1.05, hy - h_ * 1.9, hx - w_ * 0.45, hy - h_ * 0.2)))       # thumb, up on the near side
    for _, bb in parts: d.ellipse([(bb[0] - 3) * S, (bb[1] - 3) * S, (bb[2] + 3) * S, (bb[3] + 3) * S], fill=ink)
    for _, bb in parts: d.ellipse([(bb[0] + 1) * S, (bb[1] + 1) * S, (bb[2] - 1) * S, (bb[3] - 1) * S], fill=col)
    d.arc([(hx - w_ * 0.7) * S, (hy - h_ * 0.6) * S, (hx + w_ * 0.5) * S, (hy + h_ * 0.7) * S], 200, 330, fill=mix(hexrgb(skin), INK, 0.35) + (255,), width=lw // 2)   # palm crease
    if alpha < 255: lay.putalpha(lay.getchannel('A').point(lambda v: v * alpha // 255))
    C.im.alpha_composite(lay); C.d = ImageDraw.Draw(C.im)

def broom_insert(pose='broom_upright', w=1080, h=1920, sleeve='#2f6fb3', skin='#c98e63', bg=None):
    """RGBA w x h. bg=None keeps it transparent (composite over a blurred plate); or pass '#rrggbb'."""
    P = POSES[pose]
    C = Canvas.__new__(Canvas); C.im = Image.new('RGBA', (w * S, h * S), hexrgb(bg) + (255,) if bg else (0, 0, 0, 0)); C.d = ImageDraw.Draw(C.im)
    k = (0.80 * h) / 357.0                                # the broom (handle + head = 357 units at k=1) is 80% of the frame
    u = k * 2.36 * 1.0
    hx, hy = P['hx'] * w, 0.86 * h
    arm_c = mix(hexrgb(sleeve), INK, 0.35)
    def arm(x, y, alpha=255):
        root = (x - 0.16 * w, h + 60); wrist = (x - 0.07 * w, y + 6 * u / 2.36)
        if alpha < 255:
            g = Canvas.__new__(Canvas); g.im = Image.new('RGBA', C.im.size, (0, 0, 0, 0)); g.d = ImageDraw.Draw(g.im)
            g.stroke([root, wrist], 26 * u / 2.36 + 2 * 6, mix(INK, (255, 255, 255), 0.3)); g.stroke([root, wrist], 26 * u / 2.36, mix(arm_c, (255, 255, 255), 0.35)); g.im.putalpha(g.im.getchannel('A').point(lambda v: v * alpha // 255))
            C.im.alpha_composite(g.im); C.d = ImageDraw.Draw(C.im); _hand(C, x, y, u, skin, alpha); return
        C.stroke([root, wrist], 26 * u / 2.36 + 2 * 8, INK); C.stroke([root, wrist], 26 * u / 2.36, arm_c)
        _hand(C, x, y, u, skin)
    if P['flick']:                                        # a ghost hand where the flick started, then speed lines
        sgn = P['flick']; gx = hx - sgn * 0.22 * w
        arm(gx, hy, alpha=200)
        for i, dy in enumerate((-0.02, 0.005, 0.03)):
            x0 = hx - sgn * (0.10 + 0.03 * i) * w; x1 = gx + sgn * 0.02 * w
            C.d.line([(x0 * S, (hy + dy * h) * S), (x1 * S, (hy + dy * h) * S)], fill=mix(INK, (255, 255, 255), 0.35), width=int(9 * S))
    arm(hx, hy)
    _broom(C, hx, hy - 9 * u / 2.36, u, P['tilt'], k=k, palm=False, wide=1.7)
    if P['flick']:
        ay = hy - 0.075 * h; ax0, ax1 = hx - sgn * 0.36 * w, hx - sgn * 0.12 * w
        C.d.line([(ax0 * S, ay * S), (ax1 * S, ay * S)], fill=(192, 53, 58), width=int(16 * S))
        C.d.polygon([(ax1 * S + sgn * 40 * S, ay * S), (ax1 * S - sgn * 10 * S, (ay - 34) * S), (ax1 * S - sgn * 10 * S, (ay + 34) * S)], fill=(192, 53, 58))
    return C.im.resize((w, h), Image.LANCZOS)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    names = ['broom_upright', 'broom_flick_right', 'broom_tip_left']
    cells = [broom_insert(n, 540, 960, bg='#bfd8e8') for n in names]
    sheet = Image.new('RGBA', (540 * len(cells) + 20 * (len(cells) - 1), 960), (240, 237, 230, 255))
    for i, c in enumerate(cells): sheet.alpha_composite(c, (i * 560, 0))
    sheet.save(os.path.join(out, 'broom_insert_v1.png'))
    for n in POSES: broom_insert(n).save(os.path.join(out, f'insert_{n}.png')) if '--all' in sys.argv else None
    print('ok')

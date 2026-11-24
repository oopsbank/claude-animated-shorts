"""World kit for flamingo-one-leg (video 10): the salt lagoon (dawn / morning / night / golden), the warm 2017
Atlanta biomechanics lab, the Zoo Atlanta enclosure, an evening living room, a street queue, the diagram stage.

Static parts are cached as layers; each world call adds the moving bits (water shimmer, drifting clouds, rays,
motes, flickers) per frame. cam = horizontal camera pan in px (parallax per depth layer).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit
from kit import W, H, INK, vgrad, radial, mask, fill_mask, glow, layer, lerp, rgb, font
import flamingo as FL

_C = {}
def cached(key, fn):
    if key not in _C:
        if len(_C) > 60: _C.clear()
        _C[key] = fn()
    return _C[key]


def paste_shift(img, lay, dx, dy=0):
    ox = int(round(dx)); oy = int(round(dy))
    x0, y0 = max(0, ox), max(0, oy)
    src = lay.crop((x0 - ox, y0 - oy, min(lay.width, W - ox), min(lay.height, H - oy)))
    img.alpha_composite(src, (x0, y0))


# ---------------------------------------------------------------- the salt lagoon
SKY = {
    'dawn': [(0, (58, 62, 128)), (.30, (132, 98, 160)), (.58, (236, 138, 150)), (.82, (255, 178, 138)), (1, (255, 218, 160))],
    'morning': [(0, (88, 150, 214)), (.45, (160, 202, 236)), (.8, (224, 232, 236)), (1, (252, 236, 214))],
    'night': [(0, (8, 12, 34)), (.5, (22, 30, 70)), (.85, (48, 58, 108)), (1, (78, 82, 130))],
    'golden': [(0, (70, 70, 140)), (.35, (196, 110, 140)), (.7, (255, 150, 110)), (1, (255, 206, 130))],
}
HILL = {'dawn': ((150, 100, 150), (120, 80, 132), (96, 70, 120)), 'morning': ((140, 168, 196), (110, 140, 170), (92, 122, 150)),
        'night': ((34, 40, 80), (26, 30, 64), (20, 22, 50)), 'golden': ((170, 100, 130), (134, 80, 116), (104, 64, 100))}
SUN = {'dawn': ((255, 236, 190), (255, 170, 120)), 'morning': ((255, 252, 236), (255, 236, 200)),
       'night': ((236, 240, 255), (150, 170, 230)), 'golden': ((255, 230, 170), (255, 150, 90))}


def _lagoon_static(kind, hz, sun):
    def build():
        img = Image.new('RGBA', (W + 240, H))
        sky = vgrad(SKY[kind], W + 240, hz + 4)
        img.paste(sky, (0, 0))
        sx, sy = sun[0] + 120, sun[1]
        c_in, c_out = SUN[kind]
        if kind == 'night':
            rng = np.random.default_rng(4); d = ImageDraw.Draw(img)
            for _ in range(260):
                x, y = rng.uniform(0, W + 240), rng.uniform(0, hz * .8) ** 1.0
                r = rng.choice([1, 1, 1.5, 2, 2.5]); a = int(rng.uniform(120, 255))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 240, a))
            radial(img, sx, sy, 520, c_out, .35, power=2.0)
            d.ellipse([sx - 70, sy - 70, sx + 70, sy + 70], fill=c_in)
            for cx, cy, r in ((-18, -10, 16), (20, 22, 11), (8, -30, 8)):
                d.ellipse([sx + cx - r, sy + cy - r, sx + cx + r, sy + cy + r], fill=(206, 212, 236))
        else:
            radial(img, sx, sy, 900, c_out, .55, power=1.6)
            radial(img, sx, sy, 300, c_in, .7, power=1.4)
            d = ImageDraw.Draw(img)
            r = 92 if kind != 'morning' else 70
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=c_in)
        # cloud streaks lit from below
        cl = {'dawn': ((255, 190, 170), (170, 110, 160)), 'morning': ((255, 255, 255), (206, 220, 236)),
              'night': ((70, 80, 130), (40, 46, 90)), 'golden': ((255, 196, 150), (180, 100, 140))}[kind]
        rng = np.random.default_rng(12)
        m1, m2 = mask(W + 240, H), mask(W + 240, H)
        d1, d2 = ImageDraw.Draw(m1), ImageDraw.Draw(m2)
        for _ in range(9):
            y = rng.uniform(hz * .12, hz * .72); x = rng.uniform(-200, W + 200); L = rng.uniform(320, 760); th = rng.uniform(18, 46)
            d2.rounded_rectangle([x, y, x + L, y + th], th / 2, fill=255)
            d2.rounded_rectangle([x + L * .15, y - th * .8, x + L * .65, y + th * .4], th / 2, fill=255)
            d1.rounded_rectangle([x + 10, y + th * .45, x + L - 10, y + th], th / 3, fill=255)
        fill_mask(img, m2, cl[1], .55, blur=8)
        fill_mask(img, m1, cl[0], .6, blur=5)
        # far hills (two ranges) sitting on the horizon, haze between
        h1, h2, h3 = HILL[kind]
        for seed, hmin, hmax, col, a in ((3, 70, 150, h1, .9), (5, 40, 100, h2, 1.0)):
            lay = Image.new('RGBA', (W + 240, H)); dl = ImageDraw.Draw(lay)
            rng = np.random.default_rng(seed)
            pts = [(0, hz + 2)]
            for x in range(0, W + 260, 40):
                y = hz - (hmin + (hmax - hmin) * (.5 + .5 * math.sin(x / 210 + seed) * math.sin(x / 97 + seed * 2))) * (.6 + .4 * rng.uniform())
                pts.append((x, y))
            pts.append((W + 240, hz + 2))
            dl.polygon(pts, fill=col + (int(255 * a),))
            img.alpha_composite(lay)
            kit.haze(img, hz - hmax, hz + 10, lerp(SKY[kind][-2][1], (255, 255, 255), .1), .25)
        # water: the sky mirrored, darker and bluer
        wh = H - hz
        refl = vgrad([(0, lerp(SKY[kind][-1][1], (120, 140, 180), .25)), (.25, lerp(SKY[kind][-2][1], (90, 110, 160), .35)),
                      (1, lerp(SKY[kind][1][1], (30, 50, 90), .45))], W + 240, wh)
        img.paste(refl, (0, hz))
        # reflected hills
        lay = Image.new('RGBA', (W + 240, H)); dl = ImageDraw.Draw(lay)
        rng = np.random.default_rng(5)
        pts = [(0, hz)]
        for x in range(0, W + 260, 40):
            y = hz + (40 + 60 * (.5 + .5 * math.sin(x / 210 + 5) * math.sin(x / 97 + 10))) * (.6 + .4 * rng.uniform()) * .7
            pts.append((x, y))
        pts.append((W + 240, hz))
        dl.polygon(pts, fill=lerp(h2, (40, 50, 90), .3) + (150,))
        img.alpha_composite(lay)
        # far salt flats / mud bars with a pale rim
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(21)
        for i in range(7):
            y = hz + 30 + i * 22 + rng.uniform(0, 14); x = rng.uniform(-100, W + 100); L = rng.uniform(200, 520)
            d.ellipse([x, y, x + L, y + 10 + i * 2], fill=lerp(SKY[kind][-1][1], (250, 240, 230), .5) + (200,))
        if kind != 'night':
            # the sun's broken reflection path
            for i in range(26):
                y = hz + 12 + i ** 1.5 * 9
                if y > H: break
                wv = 40 + i * 9 + rng.uniform(-20, 20)
                d.rounded_rectangle([sx - wv / 2 + rng.uniform(-30, 30), y, sx + wv / 2, y + 4 + i * .4], 4,
                                    fill=c_in + (int(200 * (1 - i / 26)),))
        else:
            for i in range(22):
                y = hz + 12 + i ** 1.5 * 10
                if y > H: break
                wv = 30 + i * 8 + rng.uniform(-20, 20)
                d.rounded_rectangle([sx - wv / 2 + rng.uniform(-30, 30), y, sx + wv / 2, y + 3 + i * .3], 3, fill=(220, 226, 255, int(170 * (1 - i / 22))))
        return img
    return cached(('lagoon', kind, hz, sun), build)


def lagoon(img, t, cam=0.0, kind='dawn', horizon=980, sun=(760, 900), flock=True, flock_y=None, flock_n=26, mist=True):
    """The shallow salt lagoon. Returns the water colour for reflections/veils."""
    st = _lagoon_static(kind, horizon, sun)
    paste_shift(img, st, -120 + cam * .35)
    # far flock on the far water (parallax .5): little sleeping flamingos with reflections
    if flock:
        fy = flock_y or horizon + 40
        lay = layer(); d = ImageDraw.Draw(lay)
        rng = np.random.default_rng(31)
        col = {'dawn': (240, 140, 160), 'morning': (246, 150, 164), 'night': (120, 96, 140), 'golden': (240, 140, 150)}[kind]
        for i in range(flock_n):
            x = rng.uniform(-60, W + 60) + cam * .5; y = fy + rng.uniform(0, 70) ** 1.1
            h = 34 + (y - fy) * .5
            sl = 1 if rng.uniform() < .7 else 0
            f = 1 if rng.uniform() < .5 else -1
            bob = 1.5 * math.sin(t * 1.3 + i)
            FL.flock_bird(d, x, y + bob, h, sleep=sl, col=col, leg=lerp(col, (160, 80, 110), .4), face=f)
            d.line([(x - h * .2, y + 3), (x + h * .2, y + 3)], fill=lerp(col, (255, 255, 255), .3) + (140,), width=2)
        img.alpha_composite(lay)
        # their reflections (faint)
    # moving water: drifting shimmer lines
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(41)
    hl = {'dawn': (255, 214, 200), 'morning': (255, 255, 255), 'night': (150, 170, 230), 'golden': (255, 220, 180)}[kind]
    lay = layer(); dl = ImageDraw.Draw(lay)
    for i in range(90):
        y0 = rng.uniform(horizon + 10, H)
        x = (rng.uniform(-200, W + 200) + t * rng.uniform(6, 18) + cam * (.4 + .6 * (y0 - horizon) / (H - horizon))) % (W + 400) - 200
        L = rng.uniform(20, 110) * (.4 + (y0 - horizon) / (H - horizon))
        a = int(rng.uniform(40, 120) * (.6 + .4 * math.sin(t * 1.7 + i)))
        dl.line([(x, y0), (x + L, y0)], fill=hl + (max(0, a),), width=2 if y0 < horizon + 300 else 3)
    img.alpha_composite(lay)
    if mist and kind in ('dawn', 'golden', 'night'):
        m = mask(); dm = ImageDraw.Draw(m)
        for i in range(5):
            x = (i * 300 + t * 12 + cam * .5) % (W + 600) - 300
            dm.ellipse([x, horizon - 40, x + 520, horizon + 50], fill=120)
        fill_mask(img, m, {'dawn': (255, 210, 200), 'golden': (255, 220, 190), 'night': (120, 130, 180)}[kind], .35, blur=30)
    return {'dawn': (150, 120, 170), 'morning': (120, 170, 200), 'night': (30, 40, 80), 'golden': (180, 120, 150)}[kind]


def reeds(img, t, x0, x1, gy, n, hmin, hmax, seed=1, col=(70, 60, 70), tip=(120, 90, 80), cam=0.0, alpha=255):
    """Foreground salt-marsh grass tufts (silhouettes swaying)."""
    rng = np.random.default_rng(seed); lay = layer(); d = ImageDraw.Draw(lay)
    for i in range(n):
        x = rng.uniform(x0, x1) + cam; h = rng.uniform(hmin, hmax); lean = rng.uniform(-.3, .3) + .06 * math.sin(t * 1.4 + i * .7)
        w = rng.uniform(5, 10)
        tx, ty = x + lean * h, gy - h
        d.line([(x, gy), ((x + tx) / 2 + lean * h * .2, (gy + ty) / 2), (tx, ty)], fill=col + (alpha,), width=int(w), joint='curve')
        if rng.uniform() < .35:
            d.ellipse([tx - 6, ty - 16, tx + 6, ty + 4], fill=tip + (alpha,))
    img.alpha_composite(lay)


# ---------------------------------------------------------------- the 2017 Atlanta lab (warm afternoon)
WALL = (236, 206, 168)
WALL_D = (196, 152, 118)
FLOOR = (150, 128, 112)


def _lab_static(variant=0):
    def build():
        img = Image.new('RGBA', (W + 240, H))
        Wd = W + 240
        img.paste(vgrad([(0, (214, 178, 140)), (.35, WALL), (.62, (226, 190, 150))], Wd, 1300), (0, 0))
        d = ImageDraw.Draw(img)
        # ceiling band + light panels
        d.rectangle([0, 0, Wd, 120], fill=(200, 170, 140))
        for x in (120, 640, 1100):
            d.rounded_rectangle([x, 40, x + 300, 90], 8, fill=(255, 246, 222), outline=(160, 130, 104), width=4)
        # window (left): afternoon Atlanta: sky, distant towers, trees
        wx0, wy0, wx1, wy1 = 70, 260, 560, 900
        win = vgrad([(0, (140, 190, 236)), (.6, (236, 226, 210)), (1, (255, 214, 160))], wx1 - wx0, wy1 - wy0)
        wd = ImageDraw.Draw(win)
        rng = np.random.default_rng(8)
        bx = 10
        while bx < wx1 - wx0:
            bw = rng.uniform(40, 90); bh = rng.uniform(140, 380)
            col = lerp((150, 170, 196), (110, 130, 160), rng.uniform())
            wd.rectangle([bx, wy1 - wy0 - 120 - bh, bx + bw, wy1 - wy0], fill=col)
            for yy in range(int(wy1 - wy0 - 110 - bh), int(wy1 - wy0 - 130), 22):
                for xx in range(int(bx + 8), int(bx + bw - 8), 16):
                    if rng.uniform() < .5: wd.rectangle([xx, yy, xx + 7, yy + 10], fill=(255, 236, 190))
            if rng.uniform() < .3: wd.polygon([(bx, wy1 - wy0 - 120 - bh), (bx + bw / 2, wy1 - wy0 - 180 - bh), (bx + bw, wy1 - wy0 - 120 - bh)], fill=col)
            bx += bw + rng.uniform(6, 30)
        for i in range(14):
            tx = rng.uniform(0, wx1 - wx0); r = rng.uniform(40, 80)
            wd.ellipse([tx - r, wy1 - wy0 - 150 - r * .6, tx + r, wy1 - wy0 - 150 + r * 1.4], fill=lerp((90, 130, 70), (130, 160, 80), rng.uniform()))
        img.paste(win, (wx0, wy0))
        d.rectangle([wx0 - 26, wy0 - 26, wx1 + 26, wy1 + 26], outline=(250, 240, 226), width=26)
        d.rectangle([wx0 - 30, wy0 - 30, wx1 + 30, wy1 + 30], outline=INK, width=6)
        d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(250, 240, 226), width=18)
        d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(250, 240, 226), width=18)
        d.rectangle([wx0 - 50, wy1 + 26, wx1 + 50, wy1 + 56], fill=(250, 240, 226), outline=INK, width=5)
        # a blind half down
        for y in range(wy0, wy0 + 140, 14):
            d.rectangle([wx0, y, wx1, y + 9], fill=(244, 232, 210))
        # right wall: shelves with binders, boxes, a bird skeleton poster, a whiteboard
        px0, py0 = 690, 230
        d.rectangle([px0, py0, px0 + 330, py0 + 420], fill=(250, 244, 230), outline=INK, width=6)
        d.text((px0 + 165, py0 + 36), 'AVIAN LEG', font=font(34, True), fill=(120, 70, 60), anchor='mm')
        # poster: a bird leg skeleton diagram
        lx = px0 + 160
        bone = (110, 96, 90)
        for a, b in (((lx, 110 + py0), (lx - 40, 230 + py0)), ((lx - 40, 230 + py0), (lx + 10, 370 + py0)), ((lx + 10, 370 + py0), (lx + 80, 384 + py0))):
            d.line([a, b], fill=bone, width=12)
        for p in ((lx, 110 + py0), (lx - 40, 230 + py0), (lx + 10, 370 + py0)):
            d.ellipse([p[0] - 12, p[1] - 12, p[0] + 12, p[1] + 12], fill=(230, 110, 100))
        d.text((lx - 60, 230 + py0), 'ANKLE', font=font(22, True), fill=(120, 70, 60), anchor='rm')
        # shelf
        for sy in (720, 880):
            d.rectangle([640, sy, Wd, sy + 20], fill=(170, 120, 80), outline=INK, width=4)
            x = 660
            while x < Wd - 40:
                bw = rng.uniform(26, 60); bh = rng.uniform(80, 140)
                col = [(70, 110, 160), (200, 90, 70), (90, 150, 110), (230, 180, 80), (130, 100, 150), (240, 236, 224)][int(rng.uniform(0, 6))]
                if rng.uniform() < .2:
                    d.rectangle([x, sy - 70, x + 110, sy], fill=(196, 160, 120), outline=INK, width=3); x += 120; continue
                d.rectangle([x, sy - bh, x + bw, sy], fill=col, outline=INK, width=3)
                d.line([(x + 6, sy - bh + 14), (x + bw - 6, sy - bh + 14)], fill=(255, 255, 255), width=3)
                x += bw + 4
        # wainscot + floor
        d.rectangle([0, 1180, Wd, 1300], fill=(206, 168, 130))
        d.line([(0, 1180), (Wd, 1180)], fill=(150, 112, 86), width=6)
        img.paste(vgrad([(0, (176, 150, 128)), (1, (120, 98, 90))], Wd, H - 1300), (0, 1300))
        d.line([(0, 1300), (Wd, 1300)], fill=INK, width=5)
        for i in range(-12, 24):                                     # floor tiles in perspective
            d.line([(Wd / 2 + i * 90, 1300), (Wd / 2 + i * 260, H)], fill=(140, 116, 100), width=3)
        for y in (1360, 1450, 1580, 1760):
            d.line([(0, y), (Wd, y)], fill=(140, 116, 100), width=3)
        # sun patch on the floor from the window + rays
        m = mask(Wd, H); ImageDraw.Draw(m).polygon([(300, 1310), (820, 1310), (1060, 1700), (380, 1760)], fill=255)
        fill_mask(img, m, (255, 220, 160), .35, blur=30)
        return img
    return cached(('lab', variant), build)


def lab(img, t, cam=0.0, rays=True):
    st = _lab_static()
    paste_shift(img, st, -120 + cam * .5)
    if rays:
        kit.light_rays(img, 200 + cam * .5, 300, (255, 220, 160), n=7, alpha=.16, spread=(20, 60), length=2000, seed=3,
                       phase=1.5 * math.sin(t * .4), blur=26)
    kit.dust(img, 13, 40, (100, 300, 1000, 1400), (255, 236, 200), 120, size=(2, 4), t=t)


def bench(img, x0, x1, top, cam=0.0, depth=60):
    """A lab bench: wooden top with a front lip, grey cabinets below."""
    d = ImageDraw.Draw(img)
    x0 += cam; x1 += cam
    d.rectangle([x0, top + 40, x1, H], fill=(150, 156, 170), outline=INK, width=6)
    for i in range(int((x1 - x0) // 240) + 1):
        cx = x0 + 20 + i * 240
        d.rectangle([cx, top + 70, cx + 210, H - 20], fill=(170, 176, 190), outline=INK, width=4)
        d.rounded_rectangle([cx + 90, top + 110, cx + 130, top + 124], 6, fill=(90, 96, 110))
    d.polygon([(x0 - 10, top), (x1 + 10, top), (x1 + 10, top + 40), (x0 - 10, top + 40)], fill=(196, 140, 92), outline=INK)
    d.rectangle([x0 - 10, top - 10, x1 + 10, top + 4], fill=(220, 168, 116), outline=INK, width=4)


def monitor(img, x, y, w, h, t, flat=True, label='MUSCLE ACTIVITY', k_flat=1.0, col=(90, 255, 150), sway=None, title_col=(255, 236, 200)):
    """A muscle-activity (EMG) monitor: dark screen, grid, a trace that is FLAT (or noisy for k_flat < 1)."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - w / 2 - 18, y - h / 2 - 18, x + w / 2 + 18, y + h / 2 + 18], 22, fill=(60, 64, 76), outline=INK, width=6)
    d.rectangle([x - 30, y + h / 2 + 18, x + 30, y + h / 2 + 70], fill=(60, 64, 76), outline=INK, width=5)
    d.rounded_rectangle([x - 110, y + h / 2 + 64, x + 110, y + h / 2 + 86], 8, fill=(60, 64, 76), outline=INK, width=5)
    sx0, sy0, sx1, sy1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
    d.rectangle([sx0, sy0, sx1, sy1], fill=(14, 26, 30))
    for gx in np.arange(sx0, sx1, w / 10): d.line([(gx, sy0), (gx, sy1)], fill=(30, 56, 56), width=2)
    for gy in np.arange(sy0, sy1, h / 6): d.line([(sx0, gy), (sx1, gy)], fill=(30, 56, 56), width=2)
    if label:
        d.text((sx0 + 16, sy0 + 12), label, font=font(int(h * .1), True), fill=title_col, anchor='lt')
    mid = sy0 + h * .62
    pts = []
    n = 120
    for i in range(n + 1):
        xx = sx0 + w * i / n
        ph = t * 3 - i * .2
        noise = (math.sin(ph * 3.1) * .6 + math.sin(ph * 7.3 + 1) * .4) * (1 - k_flat) * h * .28
        spike = 0.0
        if k_flat < .9:
            spike = (math.sin(ph * 13.7) ** 7) * (1 - k_flat) * h * .2
        pts.append((xx, mid + noise + spike + (math.sin(ph * 5) * .8 if k_flat > .9 else 0)))
    lay = layer(); dl = ImageDraw.Draw(lay)
    dl.line(pts, fill=col + (255,), width=5)
    m = mask(); ImageDraw.Draw(m).line(pts, fill=255, width=12)
    glow(img, m, col, .6, blur=10)
    img.alpha_composite(lay)
    # scanning dot
    k = (t * .35) % 1
    px = sx0 + w * k
    d = ImageDraw.Draw(img)
    d.ellipse([px - 8, mid - 8, px + 8, mid + 8], fill=(220, 255, 230))
    d.rounded_rectangle([sx1 - 64, sy0 + 14, sx1 - 18, sy0 + 34], 6, fill=(255, 80, 70) if int(t * 2) % 2 else (120, 40, 40))
    return (sx0, sy0, sx1, sy1)


def rig(img, x, gy, s, t, clamp_y, cam=0.0, plate=True):
    """The study rig: a force plate on the bench/floor, a vertical aluminium strut, a padded clamp holding the
    lower leg at clamp_y."""
    d = ImageDraw.Draw(img)
    x += cam
    if plate:
        d.rounded_rectangle([x - 230 * s, gy - 4, x + 230 * s, gy + 34 * s], 8, fill=(120, 130, 146), outline=INK, width=5)
        d.rectangle([x - 220 * s, gy - 4, x + 220 * s, gy + 6], fill=(200, 208, 220))
        d.text((x + 150 * s, gy + 16 * s), 'FORCE', font=font(int(18 * s + 4), True), fill=(236, 240, 246), anchor='mm')
    sx = x - 120 * s
    d.rectangle([sx - 16 * s, clamp_y - 40 * s, sx + 16 * s, gy], fill=(196, 204, 216), outline=INK, width=5)
    d.line([(sx - 6 * s, clamp_y - 30 * s), (sx - 6 * s, gy - 6)], fill=(236, 240, 248), width=max(2, int(5 * s)))
    d.rectangle([sx - 40 * s, gy - 26 * s, sx + 40 * s, gy], fill=(150, 160, 176), outline=INK, width=4)
    # the arm to the clamp
    d.rectangle([sx, clamp_y - 14 * s, x + 4, clamp_y + 14 * s], fill=(176, 184, 198), outline=INK, width=4)
    return sx


def clamp(img, x, y, s):
    """The padded clamp around the lower leg (drawn over the leg)."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - 34 * s, y - 30 * s, x + 34 * s, y + 30 * s], 12 * s, fill=(60, 66, 80), outline=INK, width=5)
    d.rounded_rectangle([x - 22 * s, y - 20 * s, x + 22 * s, y + 20 * s], 8 * s, fill=(90, 150, 190))
    d.ellipse([x + 22 * s, y - 10 * s, x + 42 * s, y + 10 * s], fill=(200, 206, 220), outline=INK, width=3)


# ---------------------------------------------------------------- Zoo Atlanta enclosure (green morning)
def _zoo_static():
    def build():
        img = Image.new('RGBA', (W + 240, H)); Wd = W + 240
        img.paste(vgrad([(0, (120, 190, 220)), (.5, (200, 230, 220)), (1, (236, 240, 210))], Wd, 900), (0, 0))
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(3)
        # back tree canopy layers
        for layer_i, (col, y0, r0) in enumerate((((96, 150, 110), 560, 140), ((70, 130, 90), 700, 120), ((50, 110, 70), 820, 100))):
            for i in range(26):
                x = rng.uniform(-100, Wd + 100); r = rng.uniform(r0 * .6, r0 * 1.2)
                d.ellipse([x - r, y0 - r, x + r, y0 + r * 1.4], fill=col)
        # palm-like big leaves at the sides
        def leaf(cx, cy, ang, L, col):
            a = math.radians(ang)
            tip = (cx + math.cos(a) * L, cy + math.sin(a) * L)
            n = (-math.sin(a), math.cos(a))
            mid = (cx + math.cos(a) * L * .5, cy + math.sin(a) * L * .5)
            pts = [(cx, cy), (mid[0] + n[0] * L * .18, mid[1] + n[1] * L * .18), tip, (mid[0] - n[0] * L * .18, mid[1] - n[1] * L * .18)]
            d.polygon(pts, fill=col, outline=INK)
            d.line([(cx, cy), tip], fill=lerp(col, (255, 255, 255), .3), width=4)
        for cx, cy, angs in ((-20, 900, (-60, -30, 0, 20)), (Wd + 20, 860, (-120, -150, 180, 160))):
            for a in angs: leaf(cx, cy, a, 380, (60, 140, 80))
        # the pond + sand bank
        img.paste(vgrad([(0, (110, 170, 170)), (1, (70, 130, 150))], Wd, 300), (0, 960))
        for i in range(30):
            y = rng.uniform(970, 1250); x = rng.uniform(0, Wd); L = rng.uniform(40, 140)
            d.line([(x, y), (x + L, y)], fill=(180, 220, 220), width=3)
        img.paste(vgrad([(0, (226, 206, 160)), (1, (196, 170, 126))], Wd, H - 1260), (0, 1260))
        for i in range(500):
            x, y = rng.uniform(0, Wd), rng.uniform(1270, H)
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(176, 150, 110))
        d.line([(0, 1262), (Wd, 1262)], fill=(150, 130, 100), width=6)
        # a low wooden rail fence in the foreground
        return img
    return cached(('zoo',), build)


def zoo(img, t, cam=0.0):
    paste_shift(img, _zoo_static(), -120 + cam * .5)
    kit.light_rays(img, 900, -100, (255, 250, 220), n=6, alpha=.12, spread=(100, 140), length=2200, seed=5, phase=math.sin(t * .4))


def rail(img, y, cam=0.0, col=(150, 104, 70)):
    d = ImageDraw.Draw(img)
    for x in range(-40, W + 80, 180):
        xx = x + (cam * 1.4) % 180
        d.rectangle([xx - 14, y - 160, xx + 14, H], fill=col, outline=INK, width=5)
    for yy in (y - 140, y - 60):
        d.rectangle([-10, yy, W + 10, yy + 26], fill=lerp(col, (255, 255, 255), .1), outline=INK, width=5)


# ---------------------------------------------------------------- an evening living room (s04b)
def _room_static():
    def build():
        img = Image.new('RGBA', (W + 240, H)); Wd = W + 240
        img.paste(vgrad([(0, (60, 62, 110)), (.6, (96, 86, 130)), (1, (120, 100, 136))], Wd, 1300), (0, 0))
        d = ImageDraw.Draw(img)
        # wallpaper stripes
        for x in range(0, Wd, 60):
            d.rectangle([x, 0, x + 24, 1300], fill=(70, 70, 120))
        # window with dusk + city
        wx0, wy0, wx1, wy1 = 640, 260, 1080, 820
        win = vgrad([(0, (40, 50, 110)), (.6, (190, 110, 140)), (1, (255, 170, 120))], wx1 - wx0, wy1 - wy0)
        wd = ImageDraw.Draw(win); rng = np.random.default_rng(6)
        bx = 0
        while bx < wx1 - wx0:
            bw = rng.uniform(40, 80); bh = rng.uniform(90, 260)
            wd.rectangle([bx, wy1 - wy0 - bh, bx + bw, wy1 - wy0], fill=(40, 40, 76))
            for yy in range(int(wy1 - wy0 - bh + 10), int(wy1 - wy0 - 10), 20):
                for xx in range(int(bx + 6), int(bx + bw - 6), 14):
                    if rng.uniform() < .35: wd.rectangle([xx, yy, xx + 6, yy + 9], fill=(255, 220, 140))
            bx += bw + 8
        img.paste(win, (wx0, wy0))
        d.rectangle([wx0 - 20, wy0 - 20, wx1 + 20, wy1 + 20], outline=(230, 220, 210), width=20)
        d.rectangle([wx0 - 24, wy0 - 24, wx1 + 24, wy1 + 24], outline=INK, width=5)
        d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(230, 220, 210), width=14)
        # curtains
        for cx in (wx0 - 60, wx1 + 20):
            d.polygon([(cx, wy0 - 60), (cx + 80, wy0 - 60), (cx + 100, wy1 + 120), (cx - 10, wy1 + 120)], fill=(170, 70, 80), outline=INK)
        # a framed picture + a floor lamp (left)
        d.rectangle([140, 380, 420, 600], fill=(240, 220, 190), outline=INK, width=8)
        d.polygon([(180, 560), (260, 450), (320, 520), (380, 470), (400, 560)], fill=(90, 130, 160))
        d.rectangle([0, 1180, Wd, 1300], fill=(80, 64, 96))
        img.paste(vgrad([(0, (150, 104, 80)), (1, (100, 66, 60))], Wd, H - 1300), (0, 1300))
        for y in range(1320, H, 60):
            d.line([(0, y), (Wd, y)], fill=(120, 80, 66), width=3)
        # rug
        d.ellipse([140, 1580, 1100, 1900], fill=(60, 110, 120), outline=INK, width=6)
        d.ellipse([200, 1610, 1040, 1870], outline=(230, 200, 140), width=8)
        # sofa (right, cut by the frame)
        d.rounded_rectangle([760, 1020, 1300, 1360], 50, fill=(200, 120, 70), outline=INK, width=7)
        d.rounded_rectangle([800, 1140, 1300, 1300], 30, fill=(220, 140, 86), outline=INK, width=5)
        return img
    return cached(('room',), build)


def room(img, t, cam=0.0):
    paste_shift(img, _room_static(), -120 + cam * .5)
    # floor lamp glow (warm) on the left
    d = ImageDraw.Draw(img)
    lx = 120 + cam * .5
    d.line([(lx, 700), (lx, 1500)], fill=INK, width=14); d.line([(lx, 700), (lx, 1500)], fill=(200, 170, 120), width=6)
    d.ellipse([lx - 70, 1490, lx + 70, 1520], fill=INK)
    d.polygon([(lx - 90, 700), (lx + 90, 700), (lx + 60, 580), (lx - 60, 580)], fill=(255, 220, 150), outline=INK)
    radial(img, lx, 680, 620, (255, 190, 120), .35 + .02 * math.sin(t * 3), power=1.8)


# ---------------------------------------------------------------- a street queue (s13)
def _street_static():
    def build():
        img = Image.new('RGBA', (W + 240, H)); Wd = W + 240
        img.paste(vgrad([(0, (110, 170, 220)), (.6, (240, 220, 190)), (1, (255, 200, 150))], Wd, 900), (0, 0))
        d = ImageDraw.Draw(img); rng = np.random.default_rng(9)
        # building facade (warm brick) with windows and an awning over a ticket window
        d.rectangle([0, 220, Wd, 1240], fill=(190, 100, 76))
        for y in range(240, 1240, 34):
            off = 0 if (y // 34) % 2 else 40
            for x in range(-40 + off, Wd, 80):
                d.rectangle([x, y, x + 76, y + 30], outline=(160, 80, 62), width=2)
        for x in range(60, Wd, 260):
            d.rectangle([x, 300, x + 160, 520], fill=(150, 190, 220), outline=INK, width=8)
            d.line([(x + 80, 300), (x + 80, 520)], fill=INK, width=5)
        d.rectangle([0, 640, Wd, 700], fill=(60, 120, 110), outline=INK, width=6)
        for x in range(0, Wd, 80):
            d.polygon([(x, 700), (x + 80, 700), (x + 40, 740)], fill=(240, 230, 210), outline=INK)
        d.rectangle([60, 780, 360, 1080], fill=(60, 50, 60), outline=INK, width=8)
        d.rectangle([90, 820, 330, 1000], fill=(255, 220, 150))
        d.rounded_rectangle([70, 740, 350, 790], 12, fill=(250, 210, 80), outline=INK, width=5)
        d.text((210, 765), 'TICKETS', font=font(36), fill=INK, anchor='mm')
        # sidewalk
        img.paste(vgrad([(0, (200, 190, 180)), (1, (160, 150, 146))], Wd, H - 1240), (0, 1240))
        d.line([(0, 1240), (Wd, 1240)], fill=INK, width=6)
        for i in range(-10, 30):
            d.line([(i * 120, 1240), (i * 200 - 600, H)], fill=(170, 160, 156), width=3)
        for y in (1330, 1480, 1700):
            d.line([(0, y), (Wd, y)], fill=(170, 160, 156), width=3)
        # queue rope posts
        return img
    return cached(('street',), build)


def street(img, t, cam=0.0):
    paste_shift(img, _street_static(), -120 + cam * .5)
    radial(img, 900, 200, 900, (255, 210, 150), .3, power=1.8)


# ---------------------------------------------------------------- the diagram stage (warm technical plate)
def _stage_static(kind):
    def build():
        if kind == 'paper':
            img = vgrad([(0, (246, 236, 214)), (1, (230, 212, 184))], W, H)
            d = ImageDraw.Draw(img)
            for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(222, 206, 180), width=2)
            for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(222, 206, 180), width=2)
            for x in range(0, W, 300): d.line([(x, 0), (x, H)], fill=(210, 188, 160), width=3)
            for y in range(0, H, 300): d.line([(0, y), (W, y)], fill=(210, 188, 160), width=3)
        else:   # x-ray lightbox
            img = vgrad([(0, (14, 30, 52)), (1, (8, 18, 34))], W, H)
            d = ImageDraw.Draw(img)
            for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(24, 48, 76), width=2)
            for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(24, 48, 76), width=2)
            radial(img, 540, 900, 900, (60, 140, 200), .35, power=1.5)
        return img
    return cached(('stage', kind), build)


def stage(img, t, kind='paper'):
    img.alpha_composite(_stage_static(kind))
    if kind == 'paper':
        radial(img, 540, 760, 1000, (255, 250, 236), .25 + .03 * math.sin(t * 1.2), power=1.4)

"""flat2d.savanna: the two worlds of video 9 (zebra-stripes) + props.

- `english_field(img, u, cam, horizon)`: the 2016 experiment: a fresh summer sky with drifting cumulus, a patchwork of
  far fields stitched with hedgerows, a hedgerow line with round oaks, the green pasture with a wooden post-and-rail
  fence, buttercups and daisies, grass that sways. Returns the pasture's crest function.
- `savanna(img, u, cam, horizon, sun)`: golden African savanna: a warm sunset sky, a big low sun with rays, violet far
  hills and a kopje, flat-topped acacias in three depths, golden grass plains, heat haze.
- `acacia`, `oak`, `fence`, `hedgerow`: cached layers.
- props: `tripod_camera`, `clipboard`, `thermometer`, `barrel`, `africa`, `dots_trail`.
Layers are drawn back to front; `cam` is the parallax pan (far layers move less).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit
import prairie as P
from kit import W, H, INK, radial, haze, mask, glow, fill_mask, layer, lerp, rgb

FIELD = ((180, 218, 112), (124, 182, 78), (86, 142, 60), (56, 100, 46))
FIELD_FAR = ((176, 206, 150), (150, 186, 132), (126, 164, 120), (100, 140, 104))
GOLD = P.GOLD
HEDGE = ((70, 120, 60), (48, 92, 48), (34, 70, 40))
WOOD = ((176, 132, 92), (132, 96, 66), (92, 64, 46))
cached = P.cached


# ---------------------------------------------------------------- trees and hedges
def oak(s=1.0, seed=1, cols=HEDGE, trunk=(84, 62, 46), light=(-1, -1)):
    """A round English oak: trunk + clustered canopy (shade, mid, lit puffs). Cached. Origin at the trunk base."""
    def build():
        rng = np.random.default_rng(seed)
        w, h = int(520 * s), int(560 * s)
        lay = layer(w, h); d = ImageDraw.Draw(lay)
        bx, by = w / 2, h - 4
        d.polygon([(bx - 22 * s, by), (bx - 12 * s, by - 200 * s), (bx + 12 * s, by - 200 * s), (bx + 26 * s, by)], fill=trunk + (255,))
        d.line([(bx, by - 150 * s), (bx - 70 * s, by - 250 * s)], fill=trunk + (255,), width=int(16 * s))
        d.line([(bx, by - 170 * s), (bx + 80 * s, by - 260 * s)], fill=trunk + (255,), width=int(14 * s))
        puffs = []
        for i in range(16):
            a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0, 150) * s
            puffs.append((bx + math.cos(a) * r * 1.25, by - 330 * s + math.sin(a) * r * .8, rng.uniform(70, 110) * s))
        m = Image.new('L', (w, h), 0); dm = ImageDraw.Draw(m)
        for x, y, r in puffs: dm.ellipse([x - r, y - r, x + r, y + r], fill=255)
        ink = m.filter(ImageFilter.BoxBlur(max(2, int(4 * s)))).point(lambda v: 255 if v > 4 else 0)
        lay.paste(Image.new('RGBA', (w, h), INK + (255,)), (0, 0), ink)
        lay.paste(Image.new('RGBA', (w, h), cols[2] + (255,)), (0, 0), m)
        m2 = Image.new('L', (w, h), 0); d2 = ImageDraw.Draw(m2)
        for x, y, r in puffs: d2.ellipse([x - r * .85, y - r * .95, x + r * .75, y + r * .45], fill=255)
        lay.paste(Image.new('RGBA', (w, h), cols[1] + (255,)), (0, 0), ImageChops.multiply(m2, m))
        m3 = Image.new('L', (w, h), 0); d3 = ImageDraw.Draw(m3)
        for x, y, r in puffs:
            if y < by - 300 * s: d3.ellipse([x - r * .7, y - r * .9, x + r * .3, y - r * .1], fill=255)
        lay.paste(Image.new('RGBA', (w, h), lerp(cols[0], (220, 230, 150), .35) + (255,)), (0, 0), ImageChops.multiply(m3, m))
        return lay
    return cached(('oak', round(s, 2), seed, cols), build)


def acacia(s=1.0, seed=1, col=(70, 52, 50), lit=None):
    """Flat-topped umbrella thorn acacia: a forked trunk and a layered flat canopy. Cached, origin at the trunk base."""
    def build():
        rng = np.random.default_rng(seed)
        w, h = int(760 * s), int(560 * s)
        lay = layer(w, h); d = ImageDraw.Draw(lay)
        bx, by = w / 2, h - 2
        c = col + (255,)
        top = by - 380 * s
        d.polygon([(bx - 16 * s, by), (bx - 6 * s, by - 160 * s), (bx + 8 * s, by - 160 * s), (bx + 18 * s, by)], fill=c)
        for sx, ex in ((-1, -230), (1, 210), (-1, -90), (1, 80)):
            d.line([(bx, by - 150 * s), (bx + ex * s * .6, by - 260 * s), (bx + ex * s, top + 30 * s)], fill=c, width=int(13 * s), joint='curve')
        for k in range(3):
            y = top - k * 34 * s; hw = (330 - 70 * k) * s * rng.uniform(.9, 1.05); xo = rng.uniform(-30, 30) * s
            pts = []
            for i in range(24):
                q = i / 23
                pts.append((bx + xo - hw + 2 * hw * q, y - (40 + 18 * math.sin(q * 11 + seed)) * s * math.sin(math.pi * q) ** .4))
            pts += [(bx + xo + hw * .97, y + 12 * s), (bx + xo - hw * .97, y + 12 * s)]
            d.polygon(pts, fill=c)
            if lit:
                d.polygon(pts[:12] + [(bx + xo, y - 8 * s), (bx + xo - hw * .9, y - 8 * s)], fill=lit + (255,))
        return lay
    return cached(('acacia', round(s, 2), seed, col, lit), build)


def paste_base(img, lay, x, y):
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height + 2)))


def hedgerow(seed, y, h, cols=HEDGE, w=W + 600, oaks=(), haze_a=0.0, haze_col=(200, 220, 230)):
    """A long lumpy hedge with oaks rising from it (cached layer, paste at -300 + cam*f)."""
    def build():
        rng = np.random.default_rng(seed)
        lay = layer(w, H)
        m = mask(w, H); dm = ImageDraw.Draw(m)
        x = -40
        bumps = []
        while x < w + 40:
            r = rng.uniform(.5, 1) * h; bumps.append((x, y - r * .5, r)); x += r * rng.uniform(.9, 1.5)
        for bx, by, r in bumps: dm.ellipse([bx - r * 1.2, by - r * .8, bx + r * 1.2, by + r * .9], fill=255)
        dm.rectangle([0, y - h * .2, w, y + h * .4], fill=255)
        lay.paste(Image.new('RGBA', (w, H), cols[2] + (255,)), (0, 0), m)
        m2 = mask(w, H); d2 = ImageDraw.Draw(m2)
        for bx, by, r in bumps: d2.ellipse([bx - r * 1.0, by - r * .78, bx + r * .7, by + r * .1], fill=255)
        lay.paste(Image.new('RGBA', (w, H), cols[1] + (255,)), (0, 0), ImageChops.multiply(m2, m))
        for ox, s_, sd in oaks:
            o = oak(s_, sd, cols)
            lay.alpha_composite(o, (int(ox - o.width / 2), int(y + 10 - o.height)))
        if haze_a:
            al = lay.split()[3]
            fill_mask(lay, al.point(lambda v: int(v * haze_a)), haze_col)
        return lay
    return cached(('hedge', seed, y, h, cols, w, oaks, haze_a, haze_col), build)


def patchwork(seed, y0, y1, w=W + 600):
    """Far fields: rolling bands of different greens and golds stitched with dark hedge lines (cached)."""
    def build():
        rng = np.random.default_rng(seed)
        lay = layer(w, H); d = ImageDraw.Draw(lay)
        cols = [(168, 198, 128), (148, 186, 118), (190, 206, 130), (206, 200, 128), (138, 176, 120), (176, 196, 140)]
        n = 5
        ys = np.linspace(y0, y1, n + 1)
        prev = [(x, y0 + 18 * math.sin(x / 260 + seed)) for x in range(0, w + 40, 40)]
        d.polygon(prev + [(w + 40, y1 + 60), (0, y1 + 60)], fill=(152, 186, 120))
        for i in range(n):
            nxt = [(x, ys[i + 1] + 14 * math.sin(x / (200 + 40 * i) + i * 1.7 + seed)) for x in range(0, w + 40, 40)]
            xs = sorted(rng.uniform(0, w, 4 + i))
            bounds = [0] + list(xs) + [w + 40]
            for a, b in zip(bounds, bounds[1:]):
                top = [(x, y) for x, y in prev if a <= x <= b]; bot = [(x, y) for x, y in nxt if a <= x <= b]
                if len(top) < 2 or len(bot) < 2: continue
                d.polygon(top + bot[::-1], fill=cols[int(rng.integers(0, len(cols)))])
                d.line([bot[0], top[0]], fill=(84, 112, 72), width=3 + i)
            d.line(nxt, fill=(80, 110, 70), width=3 + i)
            for k in range(int(w / 70)):                                   # little trees along the hedge
                x = rng.uniform(0, w)
                yy = float(np.interp(x, [p[0] for p in nxt], [p[1] for p in nxt]))
                if rng.random() < .35:
                    r = (5 + 2.2 * i) * rng.uniform(.8, 1.4)
                    d.ellipse([x - r, yy - r * 1.6, x + r, yy + r * .2], fill=(76, 108, 70))
            prev = nxt
        d.line([(x, y0 + 18 * math.sin(x / 260 + seed)) for x in range(0, w + 40, 40)], fill=(120, 150, 130), width=3)
        al = lay.split()[3]
        fill_mask(lay, al.point(lambda v: int(v * .14)), (214, 228, 236))
        return lay
    return cached(('patch', seed, y0, y1, w), build)


def fence(img, y_fn, x0, x1, cam=0.0, f=1.0, post_h=150, gap=230, s=1.0, ink=INK, seed=2):
    """Post-and-rail fence along the ground line y_fn(x) (frame px). Moves with the camera at factor f."""
    d = ImageDraw.Draw(img)
    off = (cam * f) % gap
    xs = np.arange(x0 - gap + off, x1 + gap, gap)
    tops = []
    for x in xs:
        gy = y_fn(x); h = post_h * s
        tops.append((x, gy - h))
    for k, yk in enumerate((.25, .62)):
        pts = [(x, gy + (y_fn(x) - gy) - post_h * s * (1 - yk)) for x, gy in [(x, y_fn(x)) for x in xs]]
        for a, b in zip(pts, pts[1:]):
            th = 15 * s
            poly = [(a[0], a[1] - th / 2), (b[0], b[1] - th / 2), (b[0], b[1] + th / 2), (a[0], a[1] + th / 2)]
            d.polygon(poly, fill=WOOD[1], outline=ink, width=max(2, int(3 * s)))
            d.line([(a[0], a[1] - th / 2 + 3), (b[0], b[1] - th / 2 + 3)], fill=WOOD[0], width=max(1, int(3 * s)))
    for x, ty in tops:
        gy = y_fn(x); pw = 16 * s
        d.polygon([(x - pw, gy + 4), (x - pw, ty + 6), (x - pw * .4, ty), (x + pw, ty + 4), (x + pw, gy + 4)], fill=WOOD[1], outline=ink, width=max(2, int(3 * s)))
        d.line([(x - pw * .5, ty + 10), (x - pw * .5, gy - 4)], fill=WOOD[0], width=max(2, int(4 * s)))


def flowers(img, seed, box, n, t=0.0, cam=0.0, par=1.0, size=(4, 9)):
    """Buttercups and daisies dotted in the grass (bob in the breeze)."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    for i in range(n):
        x = rng.uniform(x0, x1) + cam * par; y = rng.uniform(y0, y1)
        p = (y - y0) / max(1, y1 - y0)
        r = (size[0] + (size[1] - size[0]) * p) * rng.uniform(.8, 1.2)
        x += 3 * math.sin(t * 2.2 + i) * (.5 + p)
        if rng.random() < .6:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 214, 40))
            d.ellipse([x - r * .45, y - r * .6, x + r * .1, y - r * .1], fill=(255, 246, 170))
        else:
            for k in range(6):
                a = k * math.pi / 3
                d.ellipse([x + math.cos(a) * r * .8 - r * .45, y + math.sin(a) * r * .55 - r * .3, x + math.cos(a) * r * .8 + r * .45,
                           y + math.sin(a) * r * .55 + r * .3], fill=(252, 252, 246))
            d.ellipse([x - r * .35, y - r * .3, x + r * .35, y + r * .3], fill=(250, 200, 40))


# ---------------------------------------------------------------- the English field (2016)
def english_field(img, u, cam=0.0, horizon=880, near_y=None, sun=(860, 300), fence_on=True, fg=True, cloud_a=1.0, kind='morning'):
    """Back layers of the experiment field down to the pasture (characters and animals go on top). Returns ground(x).
    kind='evening': a warm low sun (s10-s12 variety)."""
    P.sky(img, kind)
    ev = kind == 'evening'
    radial(img, sun[0] + cam * .05, sun[1], 700 if not ev else 900, (255, 246, 214) if not ev else (255, 200, 140), .45 if not ev else .6)
    radial(img, sun[0] + cam * .05, sun[1], 160, (255, 252, 236), .8)
    P.cumulus(img, u, [(120, 360, .85, 21, 7), (700, 230, 1.1, 22, 5), (1060, 470, .7, 23, 8), (460, 560, .55, 24, 9)],
              lit=(255, 255, 250) if not ev else (255, 222, 190), shade=(196, 210, 232) if not ev else (190, 150, 170),
              mid=(232, 240, 250) if not ev else (236, 190, 180), alpha=cloud_a)
    if ev:
        kit.light_rays(img, sun[0] + cam * .05, sun[1], (255, 220, 170), n=10, alpha=.2, spread=(120, 260), length=2000, seed=5, phase=2 * math.sin(u * .3))
    P.paste_band(img, patchwork(5, horizon - 70, horizon + 40), cam, .12)
    haze(img, horizon - 140, horizon + 20, (226, 238, 246), .22)
    ImageDraw.Draw(img).rectangle([0, horizon + 30, W, horizon + 260], fill=(132, 170, 104))     # under the hedge: no sky gap
    P.paste_band(img, hedgerow(6, horizon + 60, 34, cols=((100, 146, 90), (80, 124, 76), (62, 104, 66)),
                               oaks=((260, .5, 1), (900, .62, 2), (1380, .45, 3)), haze_a=.25), cam, .25)
    ny = near_y or horizon + 105
    P.paste_band(img, P.hill(71, ny, 22, FIELD, ink=None, waves=(.6, 1.6)), cam, .5)
    ground = lambda x: P.edge_y(71, ny, 22, x - cam * .5, waves=(.6, 1.6))
    P.grass(img, u, (-60, ny - 30, W + 60, ny + 120), 260, 14, 30, cols=FIELD, seed=72, wind=.18, ytop=lambda x: ground(x) + 3, clump=(3, 5))
    if fence_on:
        fence(img, lambda x: ground(x) + 70, -100, W + 100, cam, .6, post_h=120, gap=250, s=.85)
    P.grass(img, u, (-60, ny + 90, W + 60, H), 260, 26, 60, cols=FIELD, seed=73, wind=.2, clump=(3, 7))
    flowers(img, 74, (-40, ny + 80, W + 40, H - 100), 90, u, cam, .7, size=(4, 10))
    return ground


def field_front(img, u, cam=0.0, y=1780):
    """Foreground grass + flowers over characters' feet."""
    P.grass(img, u, (-80, y, W + 80, H + 60), 70, 70, 150, cols=(lerp(FIELD[1], INK, .05), FIELD[2], FIELD[3], lerp(FIELD[3], INK, .3)),
            seed=75, wind=.22, w0=9, clump=(4, 8), ink=INK, cam=cam * .4)
    flowers(img, 76, (-40, y + 40, W + 40, H), 14, u, cam, 1.2, size=(12, 18))


# ---------------------------------------------------------------- the savanna
def savanna(img, u, cam=0.0, horizon=1020, sun=(760, 860), sun_r=110, kind='sunset', trees=True, hot=0.0):
    P.sky(img, kind)
    if hot: radial(img, sun[0], sun[1], 1400, (255, 230, 150), .35 * hot)
    sx = sun[0] + cam * .04
    radial(img, sx, sun[1], sun_r * 8, (255, 200, 120), .55)
    radial(img, sx, sun[1], sun_r * 2.6, (255, 236, 180), .8)
    ImageDraw.Draw(img).ellipse([sx - sun_r, sun[1] - sun_r, sx + sun_r, sun[1] + sun_r], fill=(255, 246, 214))
    P.cumulus(img, u, [(160, 520, .8, 31, 4), (980, 380, .9, 32, 3)], lit=(255, 226, 190), shade=(214, 150, 150), mid=(240, 190, 170), alpha=.7)
    kit.light_rays(img, sx, sun[1], (255, 220, 160), n=12, alpha=.2, spread=(0, 360), length=2200, seed=8, phase=2 * math.sin(u * .3), blur=24)
    # far hills + kopje
    cool = kind in ('noon', 'haze', 'fair')
    far = cached(('sv_far', horizon, cool), lambda: _far_hills(horizon, cool))
    P.paste_band(img, far, cam, .08)
    haze(img, horizon - 160, horizon + 30, (255, 214, 160) if not cool else (236, 236, 230), .5)
    if trees:
        for x, s_, sd, f in ((-30, .32, 1, .15), (330, .22, 2, .15), (1180, .3, 3, .15)):
            paste_base(img, acacia(s_, sd, col=(150, 96, 92) if not cool else (120, 120, 110)), x + cam * f, horizon + 6)
    P.paste_band(img, P.hill(81, horizon + 60, 18, GOLD, ink=None, streaks=True, waves=(.5, 1.3)), cam, .35)
    if trees:
        for x, s_, sd, f in ((820, .55, 4, .4), (120, .44, 5, .4)):
            paste_base(img, acacia(s_, sd, col=(96, 62, 58), lit=(196, 120, 80)), x + cam * f, horizon + 70)
    haze(img, horizon + 20, horizon + 140, (255, 220, 160) if not cool else (246, 236, 210), .3)
    ground = lambda x: P.edge_y(81, horizon + 60, 18, x - cam * .35, waves=(.5, 1.3))
    return ground


def _far_hills(horizon, cool=False):
    lay = layer(W + 600, H); d = ImageDraw.Draw(lay)
    c1, c2, c3 = ((176, 130, 150), (160, 112, 134), (196, 140, 130)) if not cool else ((150, 164, 176), (136, 150, 164), (176, 172, 150))
    xs = np.arange(0, W + 620, 20)
    ys = horizon - 40 - 50 * np.sin(xs / 400 + 1) - 30 * np.sin(xs / 170)
    d.polygon(list(zip(xs, ys)) + [(W + 600, H), (0, H)], fill=c1)
    # a flat kopje / mesa
    d.polygon([(860, horizon - 30), (900, horizon - 150), (1080, horizon - 165), (1130, horizon - 120), (1170, horizon - 30)], fill=c2)
    ys2 = horizon - 10 - 24 * np.sin(xs / 300 + 3)
    d.polygon(list(zip(xs, ys2)) + [(W + 600, H), (0, H)], fill=c3)
    return lay


def savanna_grass(img, u, box, n, hmin, hmax, seed=91, wind=.3, ink=None, w0=5.0, cols=GOLD, clump=(3, 7), ytop=None):
    P.grass(img, u, box, n, hmin, hmax, cols=cols, seed=seed, wind=wind, ink=ink, w0=w0, clump=clump, ytop=ytop)


# ---------------------------------------------------------------- props
def tripod_camera(img, x, gy, s=1.0, ang=0.0, t=0.0, rec=True):
    """A video camera on a tripod, lens to the left (aimed at the horse). Moves: the REC light blinks."""
    d = ImageDraw.Draw(img)
    hx, hy = x, gy - 330 * s
    for dx in (-90, 0, 80):
        d.line([(hx, hy + 30 * s), (x + dx * s, gy)], fill=INK, width=int(16 * s))
        d.line([(hx, hy + 30 * s), (x + dx * s, gy)], fill=(80, 80, 92), width=int(8 * s))
    bw, bh = 150 * s, 90 * s
    d.rounded_rectangle([hx - bw / 2, hy - bh, hx + bw / 2, hy], 14 * s, fill=(52, 54, 64), outline=INK, width=int(6 * s))
    d.rounded_rectangle([hx - bw / 2 + 10 * s, hy - bh + 10 * s, hx + bw / 2 - 30 * s, hy - bh + 28 * s], 6 * s, fill=(84, 88, 100))
    d.rectangle([hx - bw / 2 - 70 * s, hy - bh * .78, hx - bw / 2, hy - bh * .22], fill=(40, 42, 50), outline=INK, width=int(6 * s))
    d.ellipse([hx - bw / 2 - 90 * s, hy - bh * .85, hx - bw / 2 - 50 * s, hy - bh * .15], fill=(70, 110, 160), outline=INK, width=int(6 * s))
    d.ellipse([hx - bw / 2 - 82 * s, hy - bh * .7, hx - bw / 2 - 66 * s, hy - bh * .5], fill=(210, 236, 255))
    if rec and int(t * 2) % 2 == 0:
        d.ellipse([hx + bw / 2 - 26 * s, hy - bh + 8 * s, hx + bw / 2 - 10 * s, hy - bh + 24 * s], fill=(255, 60, 50))
    return (hx - bw / 2 - 90 * s, hy - bh * .5)


def clipboard(img, x, y, s=1.0, ang=-12, marks=0, cols=('COAT', 'HEAD'), counts=(0, 0)):
    """A clipboard with a tally sheet held at (x, y)."""
    w, h = int(180 * s), int(240 * s)
    lay = layer(w + 40, h + 40); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], int(12 * s), fill=(150, 104, 62), outline=INK, width=max(3, int(5 * s)))
    d.rectangle([32, 44, 8 + w, 8 + h], fill=(250, 248, 240))
    d.rounded_rectangle([20 + w * .3, 12, 20 + w * .7, 40], 6, fill=(170, 170, 180), outline=INK, width=3)
    for k in range(5):
        d.line([(44, 70 + k * 34 * s), (w - 4, 70 + k * 34 * s)], fill=(170, 190, 220), width=2)
    for i, c in enumerate(counts):
        yy = 80 + i * 90 * s
        for k in range(c):
            xx = 54 + (k % 4) * 22 * s + (k // 5) * 10
            if k % 5 == 4: d.line([(46 + (k // 5) * 10, yy + 26 * s), (126 * s, yy - 4)], fill=(200, 40, 40), width=max(2, int(4 * s)))
            else: d.line([(xx, yy - 2), (xx, yy + 30 * s)], fill=(40, 40, 60), width=max(2, int(4 * s)))
    r = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(r, (int(x - r.width / 2), int(y - r.height / 2)))


def thermometer(img, x, y, h, level, t=0.0, col=(232, 48, 40), s=1.0):
    """A big glass thermometer; level 0..1 (the red column rises). Returns the column top y."""
    d = ImageDraw.Draw(img)
    w = 46 * s; br = 44 * s
    d.rounded_rectangle([x - w / 2 - 6, y - h - 6, x + w / 2 + 6, y + 6], w / 2 + 6, fill=INK)
    d.ellipse([x - br - 6, y - br - 6 + 30 * s, x + br + 6, y + br + 6 + 30 * s], fill=INK)
    d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], w / 2, fill=(236, 244, 250))
    d.ellipse([x - br, y - br + 30 * s, x + br, y + br + 30 * s], fill=col)
    top = y - (h - 20 * s) * max(0.0, min(1.0, level))
    d.rounded_rectangle([x - w * .22, top, x + w * .22, y + 10 * s], w * .2, fill=col)
    for k in range(9):
        yy = y - 30 * s - k * (h - 50 * s) / 8
        d.line([(x + w / 2 - 4, yy), (x + w / 2 - 18 * s, yy)], fill=(120, 130, 150), width=max(2, int(3 * s)))
    d.ellipse([x - br * .5, y + 30 * s - br * .6, x - br * .1, y + 30 * s - br * .2], fill=(255, 190, 180))
    return top


def africa_pts():
    """A simplified Africa outline (lon, lat)."""
    return [(-17, 21), (-16, 24), (-13, 28), (-9, 31), (-6, 35.8), (0, 35.8), (10, 37), (11, 33), (20, 31), (25, 31.5), (32, 31.2),
            (34, 28), (37, 22), (39, 16), (43, 12.5), (51, 11.8), (51, 10), (47, 4), (41, -2), (39, -7), (40, -11), (40.5, -15),
            (36, -19), (35, -24), (32.5, -28.5), (27, -33.8), (20, -34.8), (18, -32), (16, -28), (14.5, -22), (12, -17), (12, -12),
            (13, -8), (12, -5), (9, -1), (9.5, 4), (7, 4.5), (3, 6.3), (-3, 5), (-8, 4.5), (-13, 8), (-15, 11), (-17, 14.7), (-17, 21)]


def madagascar_pts():
    return [(44, -25), (47, -25), (50.5, -15.5), (49.5, -12), (48, -13.5), (44, -17), (43.3, -22)]


def lonlat(x0, y0, sc):
    return lambda lo, la: (x0 + lo * sc, y0 - la * sc * 1.05)


def dots_trail(img, pts, r=7, col=(255, 255, 255), ink=INK, fade=True):
    """Dotted flight trail: one dot per equal time step (wide spacing = fast, tight = slow)."""
    d = ImageDraw.Draw(img)
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        k = (i + 1) / n if fade else 1.0
        rr = r * (.55 + .45 * k)
        d.ellipse([x - rr - 3, y - rr - 3, x + rr + 3, y + rr + 3], fill=ink)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)

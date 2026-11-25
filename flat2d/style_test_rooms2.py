"""Style test round 2: high-key, densely dressed perspective rooms (learned from the reference: white trims and
ceilings, plank floors with varied tones, tiled backsplash, calendar, wall phone, gingham curtain, panelled door,
rug with a border and speckle texture, inked inner edges, wide lens, bright grade, little grain).
usage: python rooms2.py OUTDIR"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_test_rooms as ST     # sets up paths, the big-head proportions and the ref face
from style_test_rooms import col, bw, lw, Part, box, Cam, Light, P3, cine, hangar, plant, sofa, bookshelf, floor_lamp
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out5'
os.makedirs(OUT, exist_ok=True)
INKC = (30, 26, 34)
WHITE = (250, 248, 242)

STORY = dict(lift=(.05, .05, .055), gamma=(1.06, 1.05, 1.03), gain=(1.08, 1.07, 1.05), contrast=1.06, sat=1.12,
             sh=(70, 60, 110), sh_k=.10, hi=(255, 252, 244), hi_k=.10)
NIGHT = dict(lift=(.04, .05, .12), gamma=(1.02, 1.04, 1.12), gain=(1.0, 1.06, 1.2), contrast=1.08, sat=1.25,
             sh=(20, 30, 110), sh_k=.30, hi=(220, 236, 255), hi_k=.10)


def shade(c, k): return tuple(int(max(0, min(255, v * k))) for v in c)


# ------------------------------------------------------------------ room kit 2
def room2(w=5.0, d=4.2, h=2.7, wall='#f2cf4f', wall_pattern=None, floor='planks', floor_col='#c8925a',
          checker=None, rng=None):
    rng = rng or np.random.default_rng(1)
    parts = []
    fl = Part('floor', sil=False)
    if checker:
        a, b, s = col(checker[0]), col(checker[1]), checker[2]
        for i in range(int(w / s) + 1):
            for j in range(int(d / s) + 1):
                x0, y0 = i * s, j * s
                fl.poly([(x0, y0, 0), (min(w, x0 + s), y0, 0), (min(w, x0 + s), min(d, y0 + s), 0), (x0, min(d, y0 + s), 0)],
                        a if (i + j) % 2 else b, ink=1.2)
    else:
        base = col(floor_col); pw = .18
        x = 0
        while x < w - 1e-6:
            y = 0
            while y < d - 1e-6:
                L = rng.uniform(.9, 1.8); y1 = min(d, y + L)
                fl.poly([(x, y, 0), (min(w, x + pw), y, 0), (min(w, x + pw), y1, 0), (x, y1, 0)],
                        shade(base, rng.uniform(.9, 1.08)), ink=1.0)
                y = y1
            x += pw
    parts.append(fl)
    c = col(wall)
    wb = Part('wall_b', sil=False); wb.poly([(0, d, 0), (w, d, 0), (w, d, h), (0, d, h)], c); parts.append(wb)
    wl = Part('wall_l', sil=False); wl.poly([(0, 0, 0), (0, d, 0), (0, d, h), (0, 0, h)], shade(c, .94)); parts.append(wl)
    wr = Part('wall_r', sil=False); wr.poly([(w, d, 0), (w, 0, 0), (w, 0, h), (w, d, h)], shade(c, .97)); parts.append(wr)
    ce = Part('ceiling', sil=False); ce.poly([(0, 0, h), (0, d, h), (w, d, h), (w, 0, h)], WHITE)
    for k in range(1, int(w / .16)):                                     # ceiling planks
        xx = k * .16
        ce.decal([(xx - .004, 0, h - .001), (xx - .004, d, h - .001), (xx + .004, d, h - .001), (xx + .004, 0, h - .001)],
                 (214, 214, 214), normal=(0, 0, -1))
    parts.append(ce)
    if wall_pattern:                                                     # small wallpaper motifs
        pc = shade(c, .9)
        for zz in np.arange(.3, h - .2, .26):
            for xx in np.arange(.15 + (zz * 7 % .26), w, .26):
                bw(wb, d, xx, xx + .025, zz, zz + .06, pc, eps=.0015)
            for yy in np.arange(.15 + (zz * 7 % .26), d, .26):
                lw(wl, 0, yy, yy + .025, zz, zz + .06, shade(pc, .95))
    trims = Part('trims', sil=False)                                    # white skirting + crown moulding, inked
    for (p0, p1, nrm) in [((0, d, 0), (w, d, 0), (0, -1, 0)), ((0, 0, 0), (0, d, 0), (1, 0, 0)), ((w, d, 0), (w, 0, 0), (-1, 0, 0))]:
        p0, p1, n = np.array(p0, float), np.array(p1, float), np.array(nrm, float)
        o = n * .004
        trims.decal([p0 + o, p1 + o, p1 + o + (0, 0, .12), p0 + o + (0, 0, .12)], WHITE, ink=True, normal=nrm)
        trims.decal([p0 + o + (0, 0, h - .1), p1 + o + (0, 0, h - .1), p1 + o + (0, 0, h), p0 + o + (0, 0, h)], WHITE, ink=True, normal=nrm)
    parts.append(trims)
    corner = Part('corners', sil=False)
    for p0, p1 in [((0, d, 0), (0, d, h)), ((w, d, 0), (w, d, h)), ((0, d, h), (w, d, h)), ((0, 0, h), (0, d, h))]:
        corner.line(p0, p1, .012, INKC)
    parts.append(corner)
    return parts


def window_b(part, d, x0, x1, z0, z1, view='day', curtain=None):
    bw(part, d, x0 - .09, x1 + .09, z0 - .12, z1 + .09, WHITE, ink=True, eps=.004)               # frame + sill
    if view == 'day':
        bw(part, d, x0, x1, z0, z1, (150, 206, 244), emit=1.0, eps=.005)
        bw(part, d, x0, x1, z0, z0 + (z1 - z0) * .32, (118, 190, 96), emit=1.0, eps=.006)          # garden
        bw(part, d, x0 + .1, x0 + .55, z0 + (z1 - z0) * .3, z0 + (z1 - z0) * .7, (238, 214, 160), emit=1.0, eps=.007)  # house
        bw(part, d, x0 + .25, x0 + .38, z0 + (z1 - z0) * .3, z0 + (z1 - z0) * .55, (60, 110, 200), emit=1.0, eps=.008)
    else:
        bw(part, d, x0, x1, z0, z1, (30, 50, 120), emit=1.0, eps=.005)
        rng = np.random.default_rng(5)
        for k in range(16):
            sx, sz = rng.uniform(x0, x1), rng.uniform(z0 + .2, z1)
            bw(part, d, sx, sx + .015, sz, sz + .015, (240, 240, 255), emit=1.0, eps=.006)
    xm = (x0 + x1) / 2
    bw(part, d, xm - .025, xm + .025, z0, z1, WHITE, ink=True, eps=.009)
    bw(part, d, x0, x1, (z0 + z1) / 2 - .025, (z0 + z1) / 2 + .025, WHITE, ink=True, eps=.009)
    if curtain == 'gingham':
        for (a, b) in [(x0 - .02, x0 + .3), (x1 - .3, x1 + .02)]:
            s = .05
            for i, xx in enumerate(np.arange(a, b, s)):
                for j, zz in enumerate(np.arange(z1 - .45, z1 + .05, s)):
                    cc = (214, 52, 50) if (i + j) % 2 else (250, 240, 238)
                    bw(part, d, xx, xx + s, zz, zz + s, cc, eps=.011)
    elif curtain:
        for (a, b) in [(x0 - .38, x0 + .02), (x1 - .02, x1 + .38)]:
            bw(part, d, a, b, z0 - .3, z1 + .12, col(curtain), ink=True, eps=.012)
            for k in range(1, 4):
                xx = a + k * (b - a) / 4
                bw(part, d, xx - .012, xx + .012, z0 - .3, z1 + .12, shade(col(curtain), .8), eps=.013)


def door_r(part, w, y0, y1, h=2.1, col_=(252, 250, 246), glass=True):
    """a white panelled door on the right wall (x=w, faces -x)."""
    def rw(ya, yb, za, zb, c, ink=True, emit=0.0, e=.004):
        part.decal([(w - e, yb, za), (w - e, ya, za), (w - e, ya, zb), (w - e, yb, zb)], c, ink=ink, emit=emit, normal=(-1, 0, 0))
    rw(y0 - .08, y1 + .08, 0, h + .08, WHITE)
    rw(y0, y1, 0, h, col_, e=.005)
    if glass:
        rw(y0 + .12, y1 - .12, 1.2, 1.95, (180, 220, 214), emit=.4, e=.006)
        for k in range(1, 4):
            zz = 1.2 + k * .75 / 4
            rw(y0 + .12, y1 - .12, zz - .01, zz + .01, col_, ink=False, e=.007)
    rw(y0 + .12, y1 - .12, .15, 1.05, shade(col_, .96), e=.006)
    part.dot((w - .06, y0 + .1, 1.02), .04, (226, 186, 80), ink=True)


def calendar(part, d, x, z):
    bw(part, d, x, x + .34, z, z + .5, (252, 250, 244), ink=True, eps=.006)
    bw(part, d, x + .02, x + .32, z + .26, z + .47, (250, 160, 60), eps=.007)
    bw(part, d, x + .02, x + .32, z + .26, z + .33, (110, 170, 80), eps=.008)
    for i in range(6):
        for j in range(4):
            cx, cz = x + .04 + i * .045, z + .04 + j * .05
            bw(part, d, cx, cx + .03, cz, cz + .03, (214, 60, 60) if (i + j * 6) < 15 else (210, 210, 210), eps=.008)


def wall_phone(parts, d, x, z):
    p = Part('wphone')
    box((x - .09, d - .1, z - .17), (x + .09, d, z + .17), (222, 70, 70), part=p)
    box((x - .13, d - .16, z + .08), (x + .13, d - .1, z + .16), (222, 70, 70), part=p)
    for k in range(10):                                                   # coiled cord
        zz = z - .2 - k * .06
        p.line((x - .03, d - .12, zz), (x + .03, d - .12, zz - .03), .012, (214, 60, 60))
    parts.append(p)


def tiles(part, d, x0, x1, z0, z1, s=.12):
    bw(part, d, x0, x1, z0, z1, (248, 248, 246), eps=.004)
    for zz in np.arange(z0, z1, s / 2):
        bw(part, d, x0, x1, zz - .002, zz + .002, (200, 204, 206), eps=.005)
    for r, zz in enumerate(np.arange(z0, z1, s / 2)):
        for xx in np.arange(x0 + (s / 2 if r % 2 else 0), x1, s):
            bw(part, d, xx - .002, xx + .002, zz, min(z1, zz + s / 2), (200, 204, 206), eps=.005)


def cabinets(parts, x0, x1, y_front, depth=.6, h=.9, c=(64, 182, 176)):
    p = Part('cab')
    box((x0, y_front, 0), (x1, y_front + depth, h), c, part=p, cols={'top': (246, 246, 244)})
    box((x0 - .02, y_front - .02, h), (x1 + .02, y_front + depth, h + .04), (246, 246, 244), part=p)
    n = max(1, int((x1 - x0) / .5))
    for k in range(n):
        xa = x0 + .04 + k * (x1 - x0) / n; xb = xa + (x1 - x0) / n - .08
        p.decal([(xa, y_front - .002, .1), (xb, y_front - .002, .1), (xb, y_front - .002, .8), (xa, y_front - .002, .8)],
                shade(c, 1.08), ink=True, normal=(0, -1, 0))
        p.dot(((xa + xb) / 2 + .15, y_front - .02, .72), .025, (240, 240, 240), ink=True)
    parts.append(p)


def rug(parts, x0, y0, x1, y1, base=(244, 232, 206), border=(214, 84, 52), rng=None):
    rng = rng or np.random.default_rng(2)
    p = Part('rug', sil=False)
    p.poly([(x0, y0, .004), (x1, y0, .004), (x1, y1, .004), (x0, y1, .004)], base, ink=1.0)
    m = .12; t = .05
    for (a, b, c_, d_) in [(x0 + m, y0 + m, x1 - m, y0 + m + t), (x0 + m, y1 - m - t, x1 - m, y1 - m),
                           (x0 + m, y0 + m, x0 + m + t, y1 - m), (x1 - m - t, y0 + m, x1 - m, y1 - m)]:
        p.decal([(a, b, .005), (c_, b, .005), (c_, d_, .005), (a, d_, .005)], border, normal=(0, 0, 1))
    for k in range(260):                                                  # speckle texture
        x, y = rng.uniform(x0 + .05, x1 - .05), rng.uniform(y0 + .05, y1 - .05)
        p.dot((x, y, .006), .012, shade(base, rng.uniform(.86, .95)))
    parts.append(p)


def side_table(parts, x, y, lampc=(70, 170, 160)):
    p = Part('stable')
    box((x - .22, y - .22, 0), (x + .22, y + .22, .55), (176, 120, 78), part=p)
    p.line((x, y, .55), (x, y, .85), .02, (60, 60, 60))
    t, b = .1, .17
    z0, z1 = .8, 1.0
    pb = [(x - b, y - b, z0), (x + b, y - b, z0), (x + b, y + b, z0), (x - b, y + b, z0)]
    pt = [(x - t, y - t, z1), (x + t, y - t, z1), (x + t, y + t, z1), (x - t, y + t, z1)]
    for i in range(4):
        j = (i + 1) % 4
        p.poly([pb[i], pb[j], pt[j], pt[i]], lampc, ink=True, two=True)
    parts.append(p)


def pumpkin(parts, x, y, z, r=.11):
    p = Part('pumpkin')
    p.dot((x, y, z + r), r, (240, 140, 40), ink=True)
    p.line((x, y, z + 2 * r), (x, y, z + 2 * r + .05), .02, (90, 120, 50))
    parts.append(p)


def frames_gallery(part, d, x0, z0):
    arts = [((.36, .44), (250, 250, 248), (40, 40, 40)), ((.3, .3), (120, 190, 240), (220, 160, 60)),
            ((.28, .36), (250, 236, 210), (90, 150, 200))]
    x = x0
    for k, ((fw, fh), bg_, fg_) in enumerate(arts):
        zz = z0 + (k % 2) * .25
        bw(part, d, x, x + fw, zz, zz + fh, (70, 52, 40), ink=True, eps=.006)
        bw(part, d, x + .03, x + fw - .03, zz + .03, zz + fh - .03, bg_, eps=.007)
        bw(part, d, x + fw * .3, x + fw * .7, zz + fh * .3, zz + fh * .65, fg_, eps=.008)
        x += fw + .14


def soft_ao(img, cam, segs, k=.22, blur=26):
    """fake ambient occlusion: dark soft strips along wall/floor seams (world segments)."""
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for p0, p1 in segs:
        a, b = cam.p(p0), cam.p(p1)
        d.line([a, b], fill=(30, 20, 40, int(255 * k)), width=40)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))


def finish2(img, look, vig=.14, grain=.012, bloom_k=.12):
    img = cine.grade(img, look)
    if bloom_k: img = cine.bloom(img, 215, 22, bloom_k)
    cine.vignette(img, vig, (30, 20, 50))
    if grain:
        import anim; anim.grain(img, grain, t=0.0)
    return img


# ------------------------------------------------------------------ frames
def frame_kitchen():
    img = Image.new('RGBA', (W, H), (240, 230, 200, 255))
    w, d = 4.2, 3.4
    parts = room2(w, d, wall='#f6d04e', checker=('#1f9aa0', '#f7f5ee', .42))
    wb = [p for p in parts if p.name == 'wall_b'][0]; wr = [p for p in parts if p.name == 'wall_r'][0]
    window_b(wb, d, 1.2, 2.1, 1.25, 2.15, 'day', curtain='gingham')
    tiles(wb, d, .0, 2.6, .94, 1.22)
    calendar(wb, d, 2.45, 1.55)
    door_r(wr, w, .5, 1.35)
    wall_phone(parts, d, 3.3, 1.45)
    cabinets(parts, 0, 2.6, d - .6)
    pumpkin(parts, .35, d - .3, .94)
    mug = Part('mug'); box((1.0, d - .45, .94), (1.1, d - .35, 1.06), (250, 250, 250), part=mug); parts.append(mug)
    lampc = Part('clamp'); ST.ceiling_lamp(1.7, 1.6, h=2.7, drop=.2, c=(70, 170, 170)); parts.append(ST.ceiling_lamp(1.0, 2.7, h=2.7, drop=.18, c=(70, 170, 170)))
    cam = Cam((2.2, -.2, 1.9), (2.4, 3.2, 1.0), fov=76)
    light = Light(d=(-.3, -.6, .75), amb=.74, bands=(.15, .5, .8), soft=.5, shadow=(90, 110, 150), shadow_k=.14)
    P3.render(img, cam, parts, light=light, order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'trims', 'corners'],
              ink=INKC, ink_w=3.2, sil_w=6.0)
    soft_ao(img, cam, [((0, d, 0), (w, d, 0)), ((w, d, 0), (w, 0, 0)), ((0, d, 0), (0, d, 2.7)), ((w, d, 0), (w, d, 2.7))])
    # sunlight patch from the window onto the floor
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    dd.polygon([cam.p((1.1, 2.4, .001)), cam.p((2.2, 2.4, .001)), cam.p((2.6, 1.3, .001)), cam.p((1.4, 1.3, .001))], fill=(255, 250, 220, 70))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18)))
    hangar.stand(img, cam, (1.35, 1.35, 0), 0.0, expr='worried', pose='hold', h=1.6, look=.3, shirt='#2fa59b',
                 pants='#3a4058', hair=('swept', '#7a4f2c'), glasses=True, rim=(255, 250, 230), rim_dir=(-1, -.4), blink_ok=False, prop='cup')
    return finish2(img, STORY)


def frame_living_high():
    img = Image.new('RGBA', (W, H), (240, 230, 200, 255))
    w, d = 4.6, 4.0
    rng = np.random.default_rng(4)
    parts = room2(w, d, wall='#f3e6c4', wall_pattern=True, floor_col='#c98d54', rng=rng)
    wb = [p for p in parts if p.name == 'wall_b'][0]; wl = [p for p in parts if p.name == 'wall_l'][0]
    window_b(wb, d, 1.6, 3.4, 1.0, 2.2, 'day', curtain='#f0b030')
    frames_gallery(wl, 0, 0, 0)  if False else None
    for k, (y0, fh, c) in enumerate([(.8, .42, (120, 190, 240)), (1.35, .3, (250, 236, 210)), (1.8, .36, (240, 150, 90))]):
        lw(wl, 0, y0, y0 + .32, 1.45 + (k % 2) * .2, 1.45 + (k % 2) * .2 + fh, (70, 52, 40), ink=True)
        lw(wl, .001, y0 + .03, y0 + .29, 1.48 + (k % 2) * .2, 1.42 + (k % 2) * .2 + fh, c)
    rug(parts, .9, .9, 3.9, 3.0, rng=rng)
    parts.append(sofa(1.4, 3.0, wdt=2.0, c='#e24c48'))
    side_table(parts, .75, 3.4)
    parts.append(plant(4.2, 3.6, .9))
    parts.append(floor_lamp(4.2, 2.7))
    pumpkin(parts, 3.3, 3.85, .95, r=.12)
    box_ = Part('cbox'); box((2.9, 2.2, 0), (3.4, 2.6, .35), (206, 160, 100), part=box_); parts.append(box_)
    cam = Cam((3.5, .55, 2.75), (2.2, 2.7, .45), fov=74)
    light = Light(d=(.2, -.7, .7), amb=.76, bands=(.15, .5, .8), soft=.5, shadow=(100, 90, 140), shadow_k=.14)
    P3.render(img, cam, parts, light=light, order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'trims', 'corners', 'rug'],
              ink=INKC, ink_w=3.2, sil_w=6.0)
    soft_ao(img, cam, [((0, d, 0), (w, d, 0)), ((0, 0, 0), (0, d, 0))])
    hangar.stand(img, cam, (2.4, 2.45, 0), 0.0, expr='neutral', pose='stand', h=1.55, look=0.0, shirt='#2fa59b',
                 pants='#3a4058', hair=('swept', '#6a4a30'), rim=(255, 250, 230), blink_ok=False)
    return finish2(img, STORY)


def frame_night_bed():
    img = Image.new('RGBA', (W, H), (20, 30, 90, 255))
    w, d = 4.0, 3.6
    parts = room2(w, d, wall='#7fa0e0', floor_col='#b08a6a')
    wb = [p for p in parts if p.name == 'wall_b'][0]
    window_b(wb, d, 2.3, 3.3, 1.1, 2.1, 'night', curtain='#4a6ab0')
    bed = Part('bed')
    box((.6, 1.6, 0), (2.2, 3.6, .45), (240, 240, 250), part=bed)
    box((.6, 3.45, 0), (2.2, 3.6, 1.1), (120, 90, 70), part=bed)
    box((.62, 1.6, .45), (2.18, 3.0, .6), (90, 130, 210), part=bed)                    # quilt
    for i in range(4):
        for j in range(5):
            if (i + j) % 2:
                bed.decal([(.62 + i * .39, 1.6 + j * .28, .601), (.62 + (i + 1) * .39, 1.6 + j * .28, .601),
                           (.62 + (i + 1) * .39, 1.6 + (j + 1) * .28, .601), (.62 + i * .39, 1.6 + (j + 1) * .28, .601)],
                          (110, 160, 230), normal=(0, 0, 1))
    rngq = np.random.default_rng(9)
    for k in range(26):                                                                  # stars on the quilt
        sx, sy = rngq.uniform(.7, 2.1), rngq.uniform(1.65, 2.95)
        bed.dot((sx, sy, .605), .025, (250, 236, 150), emit=.8)
    box((.8, 3.05, .45), (2.0, 3.4, .62), (250, 250, 255), part=bed)                    # pillow
    parts.append(bed)
    ns = Part('nstand'); box((2.35, 3.0, 0), (2.85, 3.5, .55), (150, 190, 220), part=ns)
    ns.dot((2.6, 3.25, .66), .1, (90, 230, 220), ink=True, emit=1.0); parts.append(ns)
    cam = Cam((2.75, 1.35, .95), (1.3, 3.2, .62), fov=62)
    light = Light(d=(.5, -.4, .75), amb=.7, bands=(.15, .5, .8), soft=.5, shadow=(30, 40, 140), shadow_k=.3)
    P3.render(img, cam, parts, light=light, order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'trims', 'corners'],
              ink=(16, 18, 50), ink_w=3.2, sil_w=6.0)
    # the sleeper's head on the pillow (a stickman head card cropped), drawn as a big round face
    hx, hy = cam.p((1.4, 3.15, .72)); r = cam.px_per_m((1.4, 3.15, .72)) * .17
    dd = ImageDraw.Draw(img)
    dd.ellipse((hx - r, hy - r, hx + r, hy + r), fill=(246, 246, 240), outline=(16, 18, 50), width=7)
    for ex in (-.38, .38):
        dd.ellipse((hx + ex * r - r * .2, hy - r * .25, hx + ex * r + r * .2, hy + r * .15), fill=(255, 255, 255), outline=(16, 18, 50), width=5)
        dd.ellipse((hx + ex * r - r * .07, hy - r * .1, hx + ex * r + r * .07, hy + r * .04), fill=(16, 18, 50))
    # glow from the clock and the window, stars
    ST.glow(img, *cam.p((2.6, 3.25, .66)), 260, c=(90, 240, 230), a=150)
    ST.glow(img, *cam.p((2.8, 3.6, 1.6)), 300, c=(120, 150, 255), a=60)
    ST.glow(img, *cam.p((1.4, 3.1, .9)), 420, c=(110, 140, 255), a=70)
    return finish2(img, NIGHT, vig=.24, bloom_k=.35)


if __name__ == '__main__':
    for name, fn in [('K_kitchen', frame_kitchen), ('L_living_high', frame_living_high), ('N_night_bed', frame_night_bed)]:
        try:
            fn().convert('RGB').save(os.path.join(OUT, name + '.png')); print('ok', name)
        except Exception as e:
            import traceback; traceback.print_exc(); print('FAIL', name, e)

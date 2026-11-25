"""Style test (2026-11-25): the Director's target look, stickmen in real-perspective toon rooms (persp + cine, CPU).
the video 12 toolkit (persp + cine) on CPU. Not a repo file; output goes to OUTDIR.
usage: python style_test.py OUTDIR"""
import os, sys, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'flat2d')); sys.path.insert(0, os.path.join(ROOT, 'stickman', 'scripts'))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import persp as P3
from persp import Part, box, quad, Cam, Light
import cine, kit, anim
import hangar  # for stand()
import stickman
CHIBI = os.environ.get('CHIBI', '1') == '1'
if CHIBI:   # bigger heads, shorter limbs (closer to the reference's proportions)
    stickman.R = 132; stickman.SEG_LEG = 170; stickman.SEG_ARM = 112

W, H = 1080, 1920
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)


def col(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------ shared room pieces
def room_shell(w=5.0, d=4.2, h=2.7, floor='#c89a6a', wall_b='#efe3c4', wall_l='#e6d8b6', wall_r='#e9dcbc',
               ceiling='#f4ecd8', planks=True, checker=None):
    parts = []
    fl = Part('floor', sil=False)
    if checker:
        a, b = col(checker[0]), col(checker[1]); s = checker[2]
        nx, ny = int(w / s) + 1, int(d / s) + 1
        for i in range(nx):
            for j in range(ny):
                x0, y0 = i * s, j * s
                fl.poly([(x0, y0, 0), (x0 + s, y0, 0), (x0 + s, y0 + s, 0), (x0, y0 + s, 0)], a if (i + j) % 2 else b)
    else:
        fl.poly([(0, 0, 0), (w, 0, 0), (w, d, 0), (0, d, 0)], col(floor))
        if planks:
            for k in range(1, int(w / .22)):
                x = k * .22
                fl.decal([(x - .004, 0, .001), (x + .004, 0, .001), (x + .004, d, .001), (x - .004, d, .001)],
                         tuple(int(c * .86) for c in col(floor)))
    parts.append(fl)
    wb = Part('wall_b', sil=False); wb.poly([(0, d, 0), (w, d, 0), (w, d, h), (0, d, h)], col(wall_b)); parts.append(wb)
    wl = Part('wall_l', sil=False); wl.poly([(0, 0, 0), (0, d, 0), (0, d, h), (0, 0, h)], col(wall_l)); parts.append(wl)
    wr = Part('wall_r', sil=False); wr.poly([(w, d, 0), (w, 0, 0), (w, 0, h), (w, d, h)], col(wall_r)); parts.append(wr)
    ce = Part('ceiling', sil=False); ce.poly([(0, 0, h), (0, d, h), (w, d, h), (w, 0, h)], col(ceiling)); parts.append(ce)
    # skirting boards
    sk = Part('skirt', sil=False)
    sk.poly([(0, d - .001, 0), (w, d - .001, 0), (w, d - .001, .1), (0, d - .001, .1)], (250, 246, 236))
    sk.poly([(.001, 0, 0), (.001, d, 0), (.001, d, .1), (.001, 0, .1)], (246, 240, 228))
    parts.append(sk)
    return parts



def bw(part, y, x0, x1, z0, z1, c, ink=False, emit=0.0, eps=.003):
    part.decal([(x0, y - eps, z0), (x1, y - eps, z0), (x1, y - eps, z1), (x0, y - eps, z1)], c, ink=ink, emit=emit,
               normal=(0, -1, 0))

def wall_stripes(part, y, x0, x1, z0, z1, c, every=.18, wide=.06):
    x = x0
    while x < x1:
        bw(part, y, x, x + wide, z0, z1, c, eps=.002)
        x += every


def frame_pic(part, c, wpx, hpx, y, inner, outer=(60, 44, 36)):
    """picture frame on the back wall (y): centre c=(x,z), size wpx x hpx metres."""
    x, z = c
    bw(part, y, x - wpx / 2, x + wpx / 2, z - hpx / 2, z + hpx / 2, outer, ink=True, eps=.004)
    m = .035
    bw(part, y, x - wpx / 2 + m, x + wpx / 2 - m, z - hpx / 2 + m, z + hpx / 2 - m, inner, eps=.005)


def sofa(x0, y0, wdt=2.2, dep=.9, c='#b8322c'):
    p = Part('sofa', spec=None)
    cc = col(c); dark = tuple(int(v * .82) for v in cc)
    box((x0, y0, 0), (x0 + wdt, y0 + dep, .42), cc, part=p)                            # base
    box((x0, y0 + dep - .22, .42), (x0 + wdt, y0 + dep, .95), dark, part=p)             # back
    box((x0 - .02, y0, .42), (x0 + .22, y0 + dep, .66), dark, part=p)                   # arms
    box((x0 + wdt - .22, y0, .42), (x0 + wdt + .02, y0 + dep, .66), dark, part=p)
    for k in range(3):                                                                  # cushions
        cx = x0 + .24 + k * (wdt - .48) / 3
        box((cx + .02, y0 + .05, .42), (cx + (wdt - .48) / 3 - .02, y0 + dep - .24, .52), cc, part=p)
    return p


def floor_lamp(x, y, h=1.65):
    p = Part('lamp', sil=True)
    p.line((x, y, 0), (x, y, h - .25), .025, (40, 36, 40))
    box((x - .14, y - .14, 0), (x + .14, y + .14, .03), (40, 36, 40), part=p)
    shade = P3.lathe(np.linspace(0, 1, 6), lambda u: .17 + .1 * u, lambda u, a: (255, 236, 190), n=18, part=None,
                     zc=None) if False else None
    # shade as a truncated pyramid (glowing)
    t, b = .14, .24
    z0, z1 = h - .3, h
    pts_b = [(x - b, y - b, z0), (x + b, y - b, z0), (x + b, y + b, z0), (x - b, y + b, z0)]
    pts_t = [(x - t, y - t, z1), (x + t, y - t, z1), (x + t, y + t, z1), (x - t, y + t, z1)]
    for i in range(4):
        j = (i + 1) % 4
        p.poly([pts_b[i], pts_b[j], pts_t[j], pts_t[i]], (255, 226, 160), ink=True, emit=1.0, two=True)
    return p


def bookshelf(x0, y, wdt=1.0, h=1.9):
    p = Part('shelf')
    wood = (122, 82, 52)
    box((x0, y - .32, 0), (x0 + wdt, y, h), wood, part=p)
    rng = np.random.default_rng(3)
    for r in range(4):
        z = .15 + r * .45
        x = x0 + .05
        while x < x0 + wdt - .08:
            bw = rng.uniform(.04, .08); bh = rng.uniform(.26, .36)
            c = [(196, 72, 60), (60, 110, 170), (230, 180, 70), (70, 140, 100), (150, 90, 160), (240, 236, 222)][rng.integers(6)]
            p.decal([(x, y - .325, z), (x, y - .325, z + bh), (x + bw, y - .325, z + bh), (x + bw, y - .325, z)], c,
                    ink=True, normal=(0, -1, 0))
            x += bw + .01
    return p


def night_window(part, y, x0, x1, z0, z1):
    """a window on a back wall at y: night sky + city silhouettes + lit windows (emissive), frame + sill."""
    part.decal([(x0 - .08, y - .002, z0 - .08), (x0 - .08, y - .002, z1 + .08), (x1 + .08, y - .002, z1 + .08),
                (x1 + .08, y - .002, z0 - .08)], (250, 248, 240), ink=True, normal=(0, -1, 0))
    part.decal([(x0, y - .003, z0), (x0, y - .003, z1), (x1, y - .003, z1), (x1, y - .003, z0)], (34, 46, 104), emit=1.0, normal=(0, -1, 0))
    rng = np.random.default_rng(7)
    x = x0
    while x < x1 - .05:
        bw = rng.uniform(.12, .28); bh = rng.uniform(.25, .7) * (z1 - z0)
        bx1 = min(x1, x + bw)
        part.decal([(x, y - .004, z0), (x, y - .004, z0 + bh), (bx1, y - .004, z0 + bh), (bx1, y - .004, z0)],
                   (20, 24, 52), emit=1.0, normal=(0, -1, 0))
        for k in range(int(bh / .07)):
            for m in range(int((bx1 - x) / .06)):
                if rng.random() < .35:
                    wx, wz = x + .02 + m * .06, z0 + .04 + k * .07
                    part.decal([(wx, y - .005, wz), (wx, y - .005, wz + .03), (wx + .025, y - .005, wz + .03),
                                (wx + .025, y - .005, wz)], (255, 214, 120), emit=1.0, normal=(0, -1, 0))
        x = bx1 + .02
    # cross bars
    xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
    part.decal([(xm - .02, y - .006, z0), (xm - .02, y - .006, z1), (xm + .02, y - .006, z1), (xm + .02, y - .006, z0)], (250, 248, 240), normal=(0, -1, 0))
    part.decal([(x0, y - .006, zm - .02), (x0, y - .006, zm + .02), (x1, y - .006, zm + .02), (x1, y - .006, zm - .02)], (250, 248, 240), normal=(0, -1, 0))



def lw(part, x, y0, y1, z0, z1, c, ink=False, emit=0.0):
    """rect on the left wall (x=0 plane, facing +x)."""
    part.decal([(x + .003, y0, z0), (x + .003, y1, z0), (x + .003, y1, z1), (x + .003, y0, z1)], c, ink=ink, emit=emit,
               normal=(1, 0, 0))


def door_left(part, y0=.6, y1=1.5, h=2.1):
    lw(part, 0, y0 - .07, y1 + .07, 0, h + .07, (250, 246, 236), ink=True)
    lw(part, .001, y0, y1, 0, h, (176, 112, 70), ink=True)
    lw(part, .002, y0 + .1, y1 - .1, 1.15, 1.95, (196, 132, 88), ink=True)
    lw(part, .002, y0 + .1, y1 - .1, .15, 1.0, (196, 132, 88), ink=True)
    part.dot((.06, y1 - .12, 1.05), .045, (236, 196, 90), ink=True)


def plant(x, y, s=1.0):
    p = Part('plant')
    box((x - .16 * s, y - .16 * s, 0), (x + .16 * s, y + .16 * s, .34 * s), (214, 120, 80), part=p)
    rng = np.random.default_rng(int(x * 10 + y))
    for k in range(14):
        a = rng.uniform(0, 6.28); r = rng.uniform(.05, .26) * s; z = rng.uniform(.45, 1.05) * s
        p.dot((x + r * math.cos(a), y + r * math.sin(a), z), rng.uniform(.09, .14) * s,
              [(70, 150, 90), (56, 128, 76), (96, 176, 104)][k % 3], ink=True)
    return p


def ceiling_lamp(x, y, h=2.7, drop=.28, c=(70, 170, 160)):
    p = Part('clamp')
    p.line((x, y, h), (x, y, h - drop), .015, (40, 40, 40))
    t, b = .08, .26
    z1, z0 = h - drop, h - drop - .2
    pts_b = [(x - b, y - b, z0), (x + b, y - b, z0), (x + b, y + b, z0), (x - b, y + b, z0)]
    pts_t = [(x - t, y - t, z1), (x + t, y - t, z1), (x + t, y + t, z1), (x - t, y + t, z1)]
    for i in range(4):
        j = (i + 1) % 4
        p.poly([pts_b[i], pts_b[j], pts_t[j], pts_t[i]], c, ink=True, two=True)
    p.dot((x, y, z0 - .02), .06, (255, 240, 200), emit=1.0)
    return p


def curtains(part, y, x0, x1, z0, z1, c=(226, 150, 60)):
    for xa, xb in [(x0 - .35, x0 + .05), (x1 - .05, x1 + .35)]:
        bw(part, y, xa, xb, z0 - .25, z1 + .15, c, ink=True, eps=.008)
        for k in range(3):
            xx = xa + (k + 1) * (xb - xa) / 4
            bw(part, y, xx - .01, xx + .01, z0 - .25, z1 + .15, tuple(int(v * .82) for v in c), eps=.009)


def glow(img, x, y, r, c=(255, 214, 140), a=120):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse((x - r, y - r, x + r, y + r), fill=c + (a,))
    lay = lay.filter(ImageFilter.GaussianBlur(r * .45)); img.alpha_composite(lay)


def pool(img, cam, P, rx, ry, c=(255, 220, 150), a=70):
    """a soft warm light pool on the floor around world point P."""
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pts = [cam.p((P[0] + rx * math.cos(t), P[1] + ry * math.sin(t), .002)) for t in np.linspace(0, 2 * math.pi, 40)]
    d.polygon(pts, fill=c + (a,)); lay = lay.filter(ImageFilter.GaussianBlur(40)); img.alpha_composite(lay)


def base():
    return Image.new('RGBA', (W, H), (20, 18, 30, 255))


# ------------------------------------------------------------------ A: living room at night, warm lamp
def frame_A():
    img = base()
    parts = room_shell(wall_b='#d9c79a', wall_l='#cdb98c', wall_r='#d4c193', floor='#a8774c', ceiling='#e8dcc0')
    wb = [p for p in parts if p.name == 'wall_b'][0]
    wall_stripes(wb, 4.2, 0, 5, .1, 2.7, (200, 182, 138))
    night_window(wb, 4.2, 2.9, 4.4, 1.0, 2.25)
    frame_pic(wb, (1.1, 1.75), .55, .42, 4.2, (120, 170, 200))
    frame_pic(wb, (1.85, 1.9), .34, .46, 4.2, (226, 150, 90))
    rug = Part('rug', sil=False)
    rug.poly([(1.0, 1.4, .003), (4.0, 1.4, .003), (4.0, 3.3, .003), (1.0, 3.3, .003)], (150, 52, 48))
    rug.decal([(1.12, 1.52, .004), (3.88, 1.52, .004), (3.88, 3.18, .004), (1.12, 3.18, .004)], (196, 96, 70))
    curtains(wb, 4.2, 2.9, 4.4, 1.0, 2.25)
    wl = [p for p in parts if p.name == 'wall_l'][0]; door_left(wl)
    parts += [rug, sofa(.7, 3.15), floor_lamp(3.35, 3.6), bookshelf(4.0, 4.2), plant(.45, 3.75), ceiling_lamp(1.6, 2.8)]
    tbl = Part('table'); box((2.0, 2.0, 0), (3.0, 2.6, .38), (110, 74, 48), part=tbl); parts.append(tbl)
    wr = [p for p in parts if p.name == 'wall_r'][0]
    # doorway on the right wall: a lit yellow kitchen beyond
    wr.decal([(4.997, 1.2, 0), (4.997, .2, 0), (4.997, .2, 2.15), (4.997, 1.2, 2.15)], (250, 246, 236), ink=True, normal=(-1, 0, 0))
    wr.decal([(4.996, 1.12, 0), (4.996, .28, 0), (4.996, .28, 2.07), (4.996, 1.12, 2.07)], (246, 206, 92), emit=.6, normal=(-1, 0, 0))
    cam = Cam((4.55, .05, 1.5), (2.6, 3.3, 1.1), fov=66)
    light = Light(d=(.4, -.3, .85), amb=.62, shadow=(80, 60, 120), shadow_k=.28)
    P3.render(img, cam, parts, light=light, order=['floor', 'rug', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'skirt'],
              ink_w=5.0, sil_w=8.0)
    lx, ly = cam.p((3.35, 3.6, 1.5))
    pool(img, cam, (3.0, 3.0), 1.6, 1.2)
    glow(img, lx, ly, 260)
    hangar.stand(img, cam, (3.25, 1.95, 0), 0.0, expr='worried', pose='think', h=1.75, look=-.4, coat='#2f7d78', pants='#3a4058',
                 rim=(255, 214, 150), rim_dir=(1, -.4), blink_ok=False)
    # blurred foreground: an armchair back at the left edge
    def fg(lay):
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle((-120, 1250, 260, 2100), 60, fill=(120, 36, 34, 255))
        d.rounded_rectangle((-80, 1320, 200, 2100), 40, fill=(150, 46, 40, 255))
    cine.fg_frame(img, fg, blur=22)
    img = cine.finish(img, 0.0, look='desk', vig=(.28, (12, 8, 26)), bloom_k=.3)
    return img


# ------------------------------------------------------------------ B: kitchen, checker floor, daytime
def frame_B():
    img = base()
    parts = room_shell(w=4.4, d=3.6, wall_b='#f3d35c', wall_l='#efcb4e', wall_r='#f0ce55', ceiling='#fbf3d8',
                       checker=('#2aa3a0', '#f5f3ea', .4))
    wb = [p for p in parts if p.name == 'wall_b'][0]
    # window with daylight
    wb.decal([(1.55, 3.598, 1.15), (1.55, 3.598, 2.2), (2.75, 3.598, 2.2), (2.75, 3.598, 1.15)], (250, 250, 246), ink=True, normal=(0, -1, 0))
    wb.decal([(1.62, 3.597, 1.22), (1.62, 3.597, 2.13), (2.68, 3.597, 2.13), (2.68, 3.597, 1.22)], (156, 214, 240), emit=1.0, normal=(0, -1, 0))
    wb.decal([(1.62, 3.596, 1.22), (1.62, 3.596, 1.5), (2.68, 3.596, 1.5), (2.68, 3.596, 1.22)], (120, 190, 110), emit=1.0, normal=(0, -1, 0))
    # counters (teal) along the back wall, sink, upper cabinets
    cnt = Part('counter')
    box((.0, 3.0, 0), (4.4, 3.6, .9), (40, 150, 150), part=cnt, cols={'top': (230, 236, 232)})
    for k in range(6):
        x = .1 + k * .72
        cnt.decal([(x, 2.998, .1), (x, 2.998, .8), (x + .62, 2.998, .8), (x + .62, 2.998, .1)], (52, 170, 168), ink=True, normal=(0, -1, 0))
    up = Part('upper')
    box((.0, 3.25, 1.6), (1.4, 3.6, 2.3), (40, 150, 150), part=up); box((3.0, 3.25, 1.6), (4.4, 3.6, 2.3), (40, 150, 150), part=up)
    fr = Part('fridge', spec=(30, .25))
    box((3.5, 2.3, 0), (4.35, 3.0, 1.9), (170, 222, 226), part=fr)
    fr.decal([(3.52, 2.298, 1.2), (3.52, 2.298, 1.22), (4.33, 2.298, 1.22), (4.33, 2.298, 1.2)], (90, 130, 140), normal=(0, -1, 0))
    fr.decal([(3.6, 2.297, 1.35), (3.6, 2.297, 1.7), (3.63, 2.297, 1.7), (3.63, 2.297, 1.35)], (80, 90, 100), normal=(0, -1, 0))
    fr.decal([(3.9, 2.297, 1.45), (3.9, 2.297, 1.62), (4.12, 2.297, 1.62), (4.12, 2.297, 1.45)], (240, 90, 80), ink=True, normal=(0, -1, 0))
    phone = Part('phone'); box((.0, 1.6, 1.3), (.08, 1.85, 1.62), (214, 60, 50), part=phone)
    parts += [cnt, up, fr, phone]
    cam = Cam((3.9, -.4, 1.7), (1.6, 2.5, .95), fov=66)
    light = Light(d=(-.2, -.6, .78), amb=.66, shadow=(40, 90, 120), shadow_k=.2)
    P3.render(img, cam, parts + [plant(.4, 2.6, .8), ceiling_lamp(1.2, 2.6, h=2.7, c=(240, 120, 80))], light=light,
              order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'skirt'], ink_w=5.0, sil_w=8.0)
    # sun patch on the floor from the window
    pool(img, cam, (2.1, 2.2), 1.0, .6, c=(255, 248, 220), a=60)
    hangar.stand(img, cam, (1.9, 1.2, 0), 0.0, expr='scared', pose='hold', h=1.75, look=-.3, coat='#2f7d78',
                 pants='#3a4058', rim=(255, 250, 230), rim_dir=(-1, -.4), blink_ok=False, prop='phone')
    img = cine.finish(img, 0.0, look='cabin', vig=(.30, (20, 16, 30)), bloom_k=.25)
    return img


# ------------------------------------------------------------------ C: low-angle close-up of a cop in the living room
def frame_C():
    img = base()
    parts = room_shell(wall_b='#ece2c8', wall_l='#e3d6b8', wall_r='#e6dabd', floor='#d6c3a2', ceiling='#f6f0e2')
    wb = [p for p in parts if p.name == 'wall_b'][0]
    frame_pic(wb, (1.4, 1.8), .6, .45, 4.2, (90, 160, 210))
    frame_pic(wb, (3.6, 1.7), .5, .6, 4.2, (240, 190, 90))
    parts += [sofa(1.6, 3.2, c='#c33a30'), bookshelf(4.0, 4.2), floor_lamp(.6, 3.7)]
    cam = Cam((2.35, -.45, .75), (2.6, 1.3, 1.35), fov=58)
    light = Light(d=(.3, -.5, .8), amb=.64, shadow=(70, 70, 120), shadow_k=.22)
    bg = base()
    P3.render(bg, cam, parts + [ceiling_lamp(2.0, 2.6), plant(3.7, 3.7)], light=light,
              order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'skirt'], ink_w=5.0, sil_w=8.0)
    bg = cine.defocus(bg, 7)
    img.alpha_composite(bg)
    # the cop, close and low: soles below the frame, head near the top third
    hangar.stand(img, cam, (2.6, 1.3, 0), 0.0, expr='smug', pose='point', h=1.85, look=.15,
                 uniform='#2e4a9e', hat='captain', hat_col='#2e4a9e', rim=(255, 236, 200), rim_dir=(1, -.5), blink_ok=False)
    img = cine.finish(img, 0.0, look='cabin', vig=(.26, (14, 10, 28)), bloom_k=.15)
    return img


if __name__ == '__main__':
    for name, fn in [('A_livingroom_night', frame_A), ('B_kitchen_day', frame_B), ('C_lowangle_cop', frame_C)]:
        try:
            fn().convert('RGB').save(os.path.join(OUT, name + '.png'))
            print('ok', name)
        except Exception as e:
            import traceback; traceback.print_exc(); print('FAIL', name, e)

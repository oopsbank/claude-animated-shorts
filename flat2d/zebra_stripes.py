"""Zebra stripes (video 9, "Why Do Zebras Have Stripes?"): shots as `sNN(u, D, cue) -> (img, info)`.

Same contract as wind_cave.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the shot's
voice-over LINE. info: 'faces' (face boxes) and 'avoid' (boxes the caption must not cover).
Hero image: a brown horse in a fitted zebra-striped coat (head bare) in a green English field in 2016, horse flies
circling it. Colour motif: black-and-white stripes against fresh green (England) / warm gold (the savanna).
The mechanism (s10-s12): the fly's dotted trail (one dot per equal time step: wide = fast, tight = braking).
Serious tone, no comedy. Every shot keeps moving.

Render: .venv/bin/python flat2d/render.py audio/zebra-stripes/words.json OUT.mp4 --film zebra_stripes --size 540x960
"""
import math, os, sys, re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import kit, anim
import prairie as P
import savanna as SV
import animals as A
from kit import W, H, INK, vgrad, radial, haze, dust, label, title, font, mask, glow, fill_mask, layer, lerp, rgb
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES, mix, add, damp
from blood_falls import finish, slam_title, face_box
from blood_falls_2 import put_chip, draw_x, path_point
import tunguska as TG
from tunguska import chip_t, flash

SLUG = 'zebra-stripes'
P.SKIES['noon'] = [(0, (96, 150, 214)), (.45, (176, 208, 234)), (.8, (236, 236, 226)), (1, (252, 244, 222))]
P.SKIES['haze'] = [(0, (150, 170, 196)), (.5, (214, 210, 206)), (1, (240, 220, 190))]
P.SKIES['evening'] = [(0, (70, 96, 160)), (.4, (150, 150, 186)), (.7, (246, 190, 150)), (1, (255, 214, 160))]
HIDE_UI = False
KEY = (255, 210, 63)                      # the key colour for titles (yellow)
SCI_COL = (70, 130, 80)
FARM_COL = (60, 110, 170)
SCI_A = dict(hat='cap', shirt='#5d7d43', pants='#9c855a')
SCI_B = dict(shirt='#3d6c9e', pants='#55525e')
FARMER = dict(hat='cap', shirt='#c8463c', pants='#4d6fa0')


def q(v, step):
    """Quantise a pose value (animal layers are cached by pose)."""
    return round(v / step) * step


def clue(img, txt, u, t0=.05, y=250):
    if HIDE_UI: return
    TG.clue(img, txt, u, t0, y)


def chip(img, txt, fill, x, y, u, t0, size=50, angle=0.0):
    if HIDE_UI: return
    chip_t(img, txt, fill, x, y, u, t0, size=size, angle=angle)


def stitle(img, key, lines, y, u, t0, size=104, stagger=.16):
    if HIDE_UI: return
    slam_title(img, key, lines, y, u, t0, size=size, stagger=stagger)


def sci(img, t, who, pose, expr, cx, gy, s, look=0.0, lean=0.0, label_on=False, board=False, counts=(0, 0), lbl='SCIENTIST',
        rim=(255, 236, 200), rim_dir=(1, -.5), bphase=0.0, aura=(255, 236, 190), aura_a=.3, lbl_dy=0, kw=None):
    """The 2016 field scientists: A (green cap, olive shirt) and B (blue shirt, clipboard). White stickmen, black outline."""
    kw = kw or (SCI_A if who == 'A' else SCI_B if who == 'B' else FARMER)
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, aura=aura, aura_alpha=aura_a, rim=rim, rim_dir=rim_dir,
              rim_w=12, bphase=bphase + (0 if who == 'A' else .9), **kw)
    if board:
        hx, hy, ha = g['hands']['R']
        SV.clipboard(img, hx - 20 * s, hy - 60 * s, s * 1.5, ang=-10 + .3 * g['lean'], counts=counts)
    if label_on and not HIDE_UI:
        hx, hy = g['head']
        label(img, lbl, min(W - 170, max(170, hx)), hy - g['R'] * 1.9 - 86 + lbl_dy, SCI_COL if who != 'F' else FARM_COL,
              size=int(44 * max(.9, min(1.1, s / .6))))
    return g


# ---------------------------------------------------------------- flies
def fly_at(img, pos, u, L, trail=0.7, dt=1 / 12, legs=0.0, wing='blur', r=7, t_min=-9.0, tcol=(255, 255, 255), alpha=1.0,
           max_ang=35, glow_=False):
    """A horse fly flying along pos(t) with a dotted trail of its last `trail` s (one dot per dt: spacing = speed)."""
    pts = []
    k = 1
    while k * dt <= trail:
        tt = u - k * dt
        if tt < t_min: break
        pts.append(pos(tt)); k += 1
    if pts and r > 0: SV.dots_trail(img, pts[::-1], r=r, col=tcol)
    x, y = pos(u)
    x2, y2 = pos(u + .03); x1, y1 = pos(u - .03)
    vx, vy = x2 - x1, y2 - y1
    face = 1 if vx >= 0 else -1
    ang = max(-max_ang, min(max_ang, -math.degrees(math.atan2(vy, abs(vx) + 1e-6))))
    A.put_fly(img, x, y, L * face, ang=ang, wing=wing, legs=legs, ph=u * 7.3, alpha=alpha, glow=glow_)
    return x, y


def orbit(cx, cy, rx, ry, w, ph, wob=.25):
    """Circling path (an ellipse with a wobble): flies around an animal."""
    return lambda t: (cx + rx * math.cos(w * t + ph) + rx * .12 * math.sin(3.1 * w * t + ph * 2),
                      cy + ry * math.sin(w * t + ph) * (1 - wob) + ry * wob * math.sin(2.3 * w * t + ph))


def swarm(img, u, cx, cy, rx, ry, n, L, seed=1, speed=1.0, trail=.45, r=5, alpha=1.0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        w = speed * rng.uniform(1.1, 1.8) * (1 if i % 2 else -1)
        f = rng.uniform(.65, 1.15)
        fly_at(img, orbit(cx + rng.uniform(-.15, .15) * rx, cy + rng.uniform(-.2, .2) * ry, rx * f, ry * f, w, rng.uniform(0, 6.3)),
               u, L * rng.uniform(.85, 1.1), trail=trail, r=r if alpha > .9 else 0, alpha=alpha)


def bonk_star(img, x, y, k, s=1.0):
    """Impact star (fly hits the coat). k: 0..1 life."""
    if k <= 0 or k >= 1: return
    d = ImageDraw.Draw(img)
    r = (40 + 90 * ease_out(k)) * s; a = 1 - k
    pts = []
    for i in range(16):
        rr = r if i % 2 == 0 else r * .45
        an = i * math.pi / 8 + .2
        pts.append((x + math.cos(an) * rr, y + math.sin(an) * rr))
    lay = layer(); dl = ImageDraw.Draw(lay)
    dl.polygon(pts, fill=(255, 236, 120, int(255 * a)), outline=INK + (int(255 * a),), width=max(3, int(6 * s)))
    img.alpha_composite(lay)


# ---------------------------------------------------------------- s01: the hook (2016 · ENGLAND)
HX, HGY, HS = 570, 1390, 450                  # the striped-coat horse in the s01 framing (faces left)


def horse_pose(w, graze=0.0):
    return {'neck': q(4 + 3 * math.sin(w * .9) + 40 * graze, 1), 'tail': q(16 * math.sin(w * 1.9), 4),
            'ear': q(max(0.0, math.sin(w * 2.7)) ** 6, .5), 'breath': q(.5 + .5 * math.sin(w * 2.2), .5)}


def field_world(u, cam=0.0, horse=True, kind='coat', hs=HS, hx=HX, hgy=HGY, chars=None, flies=True, fg=True, horizon=900, fly_a=1.0, extra=None):
    img = Image.new('RGBA', (W, H))
    SV.english_field(img, u, cam, horizon=horizon)
    info = None
    if horse:
        x = hx + cam * .85
        A.contact(img, x + 30, hgy + 6, hs * 1.6, .35, (40, 70, 30))
        info = A.put(img, kind, x, hgy, hs, face=-1, pose=horse_pose(u))
        if flies:
            fx, fy = x + 40, hgy - hs * .78
            if fly_a > .02: swarm(img, u, fx, fy, hs * 1.0, hs * .5, 8, 93 * hs / 400, seed=3, speed=.9, r=8, alpha=fly_a)
        if extra: extra(img)
    if chars: chars(img)
    if fg: SV.field_front(img, u, cam)
    dust(img, 9, 20, (0, 600, W, 1500), (255, 252, 230), 90, size=(2, 4), t=u)
    return img, info


def opening_title(img, u, k=1.0, t_pop=None):
    if HIDE_UI: return
    s = 1.0 + .006 * math.sin(u * 2.4)
    if t_pop is not None and u >= t_pop: s = max(s, slam(u, t_pop, .3, 1.12) if u < t_pop + .3 else s)
    lay, _ = tlayer('open', [('2016', KEY, 230)], 230)
    anim.scaled_paste(img, lay, 540, 300, s * k)
    put_chip(img, 'ENGLAND', (60, 120, 70), 540, 470, k, size=60)


_tl = {}
def tlayer(key, lines, size):
    if key not in _tl:
        _tl[key] = anim.text_layer(lambda l: title(l, lines, 60, size=size), W,
                                   int(sum((x[2] if len(x) > 2 else size) for x in lines) * 1.3 + 140))
    return _tl[key]


def s01_frame(u, w, cue=None):
    cue = cue or (lambda i: [0, .23, .74, 1.42, 1.65, 2.16, 2.67, 3.12, 3.35, 4.14, 4.75, 4.94, 5.14, 5.42, 5.58][min(i, 14)])
    cam = 8 * math.sin(w * .45)
    G = {}
    def chars(img):
        SV.tripod_camera(img, 860 + cam * 1.1, 1965, .78, t=w)
        G['b'] = sci(img, w, 'B', 'hold', 'thinking', 250 + cam * 1.1, 1990, .5, look=.35, board=True, counts=(1, 3), bphase=.4)
        G['a'] = sci(img, w, 'A', dict(POSES['stand'], armR=(-60, -100)), 'neutral', 960 + cam * 1.1, 2010, .5, look=-.6)
    img, hi = field_world(w, cam, chars=chars)
    z = 1.0 + .04 * smooth(u / 6)
    img = finish(img, w, z, 540, 1200, vig=(.24, (30, 40, 30)))
    if not HIDE_UI:
        opening_title(img, u, t_pop=cue(1))
        kc = pop(u, cue(8) - .1, .3)
        if kc > 0:
            put_chip(img, 'ZEBRA-STRIPED COAT', (40, 40, 48), 600, 760, kc, size=50)
    faces = [face_box(G['a'], 1.3), face_box(G['b'], 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 140, W, 560), (100, 700, 1000, 820)]}


def s01(u, D, cue):
    return s01_frame(u, u, cue)


def s01b(u, D, cue):
    """Close on the coat: the flies circle it; the scientist with the clipboard watches."""
    w = u + 4.7
    cam = -20 * smooth(u / D)
    G = {}
    img = Image.new('RGBA', (W, H))
    SV.english_field(img, w, cam, horizon=700)
    x = 690 + cam
    hgy = 1300
    A.contact(img, x + 40, hgy + 6, 1000, .35, (40, 70, 30))
    A.put(img, 'coat', x, hgy, 620, face=-1, pose=horse_pose(w))
    fc = (x + 20, hgy - 620 * .74)
    for i, (ph, ww, L) in enumerate(((0, 1.3, 130), (2.2, -1.1, 116), (4.1, 1.5, 108), (1.3, -1.6, 100))):
        fly_at(img, orbit(fc[0] - 40, fc[1] - 60, 470, 300, ww, ph), w, L, trail=.5, r=10)
    G['b'] = sci(img, w, 'B', 'hold', 'thinking', 200 + cam * 1.3, 2150, .8, look=.55, board=True, counts=(1, 3), label_on=True,
                 rim_dir=(1, -.3))
    img = finish(img, w, 1.02 + .04 * smooth(u / D), 540, 1290, vig=(.26, (30, 40, 30)))
    if not HIDE_UI:
        chip(img, 'WATCH THE FLIES', (40, 40, 48), 600, 300, u, cue(12) - .15, size=58)
    return img, {'faces': [face_box(G['b'], 1.3)], 'avoid': [(200, 230, 1000, 370)]}


# ---------------------------------------------------------------- s02: nobody could agree (savanna)
def zebra_pose(w, ph=0.0, walk_k=0.0, graze=0.0):
    p = {'neck': q(-4 + 3 * math.sin(w * .8 + ph) + 50 * graze, 1), 'tail': q(14 * math.sin(w * 1.6 + ph), 4),
         'ear': q(max(0.0, math.sin(w * 2.1 + ph)) ** 6, .5), 'breath': q(.5 + .5 * math.sin(w * 2 + ph), .5)}
    if walk_k:
        p['legs'] = {k: (q(v[0], 4), q(v[1], 6)) for k, v in A.walk(q(w * 4.2 + ph, .5), walk_k).items()}
    return p


def qmark(img, x, y, s, u, t0, col=(255, 255, 255)):
    k = pop(u, t0, .3)
    if k <= 0 or HIDE_UI: return
    lay = layer(260, 300); d = ImageDraw.Draw(lay)
    d.text((130, 150), '?', font=font(220), fill=col, anchor='mm', stroke_width=12, stroke_fill=INK)
    anim.scaled_paste(img, lay, x, y + 6 * math.sin(u * 3), k * s, angle=8 * math.sin(u * 2))


def s02(u, D, cue):
    w = u + 10
    cam = -24 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    ground = SV.savanna(img, w, cam, horizon=1000, sun=(800, 860))
    for x, gy, s_, ph in ((930, 1170, 160, 1.0), (180, 1250, 220, 2.5)):
        A.contact(img, x, gy + 4, s_ * 1.6, .3, (90, 60, 30))
        A.put(img, 'zebra', x + cam * .6 - 30 * u, gy, s_, face=-1, pose=zebra_pose(w, ph, walk_k=.8), sun_k=1.2)
    SV.savanna_grass(img, w, (-60, 1150, W + 60, 1420), 220, 26, 54, seed=92)
    A.contact(img, 600, 1540, 560, .35, (90, 60, 30))
    A.put(img, 'zebra', 600 + cam * .9, 1540, 360, face=1, pose=zebra_pose(w, 0.3), sun_k=1.3)
    SV.savanna_grass(img, w, (-60, 1420, W + 60, 1700), 160, 44, 90, seed=93)
    G = {}
    kk = out_back(seg(u, cue(1) - .2, cue(1) + .3), 1.4)
    pA = mix(POSES['stand'], POSES['shrug'], kk)
    G['a'] = sci(img, w, 'A', pA, 'worried', 190 + cam * 1.2, 1930, .62, look=.6, lean=-3 * kk, kw=dict(hat='cowboy', hat_col=(196, 170, 110), shirt='#b89a62', pants='#6c5a3e'))
    kb = out_back(seg(u, cue(3) - .2, cue(3) + .3), 1.4)
    pB = mix(POSES['stand'], POSES['shrug'], kb)
    G['b'] = sci(img, w, 'B', pB, 'thinking', 900 + cam * 1.2, 1950, .62, look=-.6, lean=3 * kb, kw=dict(shirt='#4f7aa6', pants='#5e4a3a'))
    SV.savanna_grass(img, w, (-80, 1840, W + 80, 2000), 60, 80, 150, seed=94, w0=9, ink=INK, cols=(P.GOLD[1], P.GOLD[2], P.GOLD[3], lerp(P.GOLD[3], INK, .3)))
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1300, vig=(.28, (60, 30, 30)))
    for g, t0 in ((G['a'], cue(1)), (G['b'], cue(3))):
        hx, hy = g['head']; qmark(img, hx, hy - 260, .8, u, t0)
    if not HIDE_UI:
        stitle(img, 's02_t', [('WHY THE', 'white', 120), ('STRIPES?', KEY, 170)], 170, u, cue(7) - .15, stagger=.18)
    return img, {'faces': [face_box(G['a'], 1.3), face_box(G['b'], 1.3)], 'avoid': [(0, 120, W, 560)]}


# ---------------------------------------------------------------- s03: camouflage? (tall grass)
def tall_grass(img, u, y0, y1, n, seed, hmin, hmax, alpha=1.0, cols=None, ink=INK):
    cols = cols or (P.GOLD[0], P.GOLD[1], P.GOLD[2], lerp(P.GOLD[3], INK, .2))
    P.grass(img, u, (-60, y0, W + 60, y1), n, hmin, hmax, cols=cols, seed=seed, wind=.12, gust=.2, w0=7, clump=(3, 6), ink=ink, spread=.2)


def s03(u, D, cue):
    w = u + 20
    cam = 20 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    SV.savanna(img, w, cam * .5, horizon=1060, sun=(260, 900), sun_r=95)
    tall_grass(img, w, 1060, 1250, 200, 101, 60, 140, ink=None)
    A.contact(img, 600, 1560, 600, .3, (90, 60, 30))
    A.put(img, 'zebra', 600 + cam * .8, 1560, 440, face=-1, pose=zebra_pose(w, 1.0), sun_k=1.2)
    tall_grass(img, w, 1320, 1500, 200, 102, 160, 300)
    # the lion's head peeks out of the grass (left) on "lions"
    kl = smooth(seg(u, cue(7) - .45, cue(7) + .25))
    if kl > 0:
        A.put(img, 'lion', 170 + cam, 1640 + 200 * (1 - kl), 480, face=1, pose={'tail': 0, 'breath': q(.5 + .5 * math.sin(w * 2), .5)})
    tall_grass(img, w, 1700, 1980, 160, 103, 180, 330)
    img = finish(img, w, 1.05 + .03 * smooth(u / D), 540, 1200, vig=(.3, (60, 30, 30)))
    if not HIDE_UI:
        stitle(img, 's03_t', [('CAMOUFLAGE?', 'white', 140)], 220, u, cue(3) - .1)
        chip(img, 'HIDE FROM LIONS', (200, 120, 40), 540, 430, u, cue(5) - .1, size=56)
    return img, {'faces': [], 'avoid': [(0, 150, W, 520)]}


# ---------------------------------------------------------------- s04: lions spot zebras easily
def open_plain(img, w, cam, horizon=1080, kind='noon', sun=(880, 360)):
    SV.savanna(img, w, cam, horizon=horizon, sun=sun, sun_r=80, kind=kind)
    SV.savanna_grass(img, w, (-60, horizon + 40, W + 60, H), 380, 10, 30, seed=111, clump=(2, 4))


def s04(u, D, cue):
    w = u + 30
    cam = -16 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    open_plain(img, w, cam)
    zx, zgy = 850 + cam * .6, 1250
    A.contact(img, zx, zgy + 4, 250 * 1.6, .3, (90, 60, 30))
    zi = A.put(img, 'zebra', zx, zgy, 250, face=-1, pose=zebra_pose(w, .7, graze=.6 * smooth(seg(u, .3, 1.2))))
    lx, lgy = 370 + cam * 1.2, 1800
    A.contact(img, lx, lgy + 6, 760, .35, (90, 60, 30))
    li = A.put(img, 'lion', lx, lgy, 430, face=1, pose={'tail': q(18 * math.sin(w * 1.3), 6), 'breath': q(.5 + .5 * math.sin(w * 2), .5)})
    SV.savanna_grass(img, w, (-80, 1760, W + 80, 2000), 90, 40, 90, seed=112, ink=INK, w0=7)
    # sight line: lion eye -> zebra
    ks = smooth(seg(u, cue(4) - .1, cue(5) + .1))
    if ks > 0:
        ex, ey = li['eye']; tx, ty = zi['flank']
        d = ImageDraw.Draw(img)
        n = 22
        for i in range(int(n * ks)):
            a_ = i / n; b_ = (i + .55) / n
            p0 = (ex + (tx - ex) * a_, ey + (ty - ey) * a_); p1 = (ex + (tx - ex) * b_, ey + (ty - ey) * b_)
            d.line([p0, p1], fill=INK, width=16); d.line([p0, p1], fill=(255, 236, 120), width=8)
        if ks >= 1:
            r = 210 + 10 * math.sin(u * 6)
            for wd, col in ((22, INK), (11, (255, 220, 80))):
                d.ellipse([tx - r * 1.2, ty - r, tx + r * 1.2, ty + r * .9], outline=col, width=wd)
    img = finish(img, w, 1.03 + .03 * smooth(u / D), 540, 1300, vig=(.3, (60, 30, 30)))
    if not HIDE_UI:
        chip(img, 'OPEN GRASSLAND', (150, 110, 50), 540, 230, u, cue(2) - .1, size=56)
        kx = pop(u, cue(4) - .2, .3)
        if kx > 0:
            put_chip(img, 'CAMOUFLAGE', (60, 60, 70), 540, 380, kx, size=70)
        if u > cue(7) - .05:
            draw_x(img, 880, 380, 70, (u - cue(7) + .05) / .12)
        chip(img, 'SPOTTED!', (220, 70, 50), 820, 760, u, cue(5), size=56, angle=-4)
    sx, sy = shake(u, cue(7), 10, .35)
    return img, {'faces': [], 'avoid': [(0, 160, W, 470), (500, 650, 1000, 800)]}


def s04b(u, D, cue):
    """Wide: lion bottom-left, the zebra far off (50 m tag); the LION'S VIEW inset: the stripes blur to grey."""
    w = u + 34
    cam = -10 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    open_plain(img, w, cam, horizon=1180, kind='haze', sun=(820, 700))
    zx, zgy = 860, 1300
    A.contact(img, zx, zgy + 3, 260, .3, (90, 60, 30))
    A.put(img, 'zebra', zx, zgy, 200, face=-1, pose=zebra_pose(w, .7))
    lx, lgy = 330, 1800
    A.contact(img, lx, lgy + 4, 420, .3, (90, 60, 30))
    li = A.put(img, 'lion', lx, lgy, 360, face=1, pose={'tail': q(16 * math.sin(w * 1.3), 6)})
    SV.savanna_grass(img, w, (-80, 1800, W + 80, 2000), 60, 40, 80, seed=113, ink=INK, w0=6)
    # the 50 m measure
    km = smooth(seg(u, cue(9) - .3, cue(10)))
    if km > 0:
        d = ImageDraw.Draw(img)
        a = (li['muzzle'][0] + 60, li['muzzle'][1] - 70); b = (zx - 60, 1310)
        e = (a[0] + (b[0] - a[0]) * km, a[1] + (b[1] - a[1]) * km)
        for wd, col in ((18, INK), (9, (255, 255, 255))):
            d.line([a, e], fill=col, width=wd)
        if km > .99:
            for p, dirn in ((a, 1), (b, -1)):
                d.ellipse([p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14], fill=(255, 255, 255), outline=INK, width=5)
        if not HIDE_UI:
            put_chip(img, '50+ METRES', (220, 120, 40), min(830, (a[0] + b[0]) / 2 + 120), (a[1] + b[1]) / 2 + 110, pop(u, cue(10) - .1, .3), size=52, angle=-12)
    # the lion's-eye view inset
    kin = out_back(seg(u, .15, .55), 1.4)
    if kin > 0:
        R = 290 * kin; cx, cy = 540, 600
        ins = Image.new('RGBA', (W, H))
        open_plain(ins, w, 0, horizon=900, kind='haze', sun=(820, 500))
        A.put(ins, 'zebra', 560, 1150, 380, face=-1, pose=zebra_pose(w, .7))
        kb = smooth(seg(u, cue(15) - .2, cue(16) + .45))
        box = (int(cx - 340), int(cy - 340), int(cx + 340), int(cy + 340))
        crop = ins.crop((540 - 340, 980 - 340, 540 + 340, 980 + 340))
        if kb > 0:
            bl = crop.filter(ImageFilter.GaussianBlur(1 + 14 * kb))
            g = bl.convert('L').convert('RGBA')
            g = Image.blend(bl, Image.merge('RGBA', (*g.split()[:3], bl.split()[3])), kb)
            crop = Image.blend(crop, g, min(1, kb * 1.3))
        m = Image.new('L', crop.size, 0); ImageDraw.Draw(m).ellipse([340 - R, 340 - R, 340 + R, 340 + R], fill=255)
        d = ImageDraw.Draw(img)
        d.ellipse([cx - R - 16, cy - R - 16, cx + R + 16, cy + R + 16], fill=INK)
        d.ellipse([cx - R - 9, cy - R - 9, cx + R + 9, cy + R + 9], fill=(255, 210, 90))
        img.paste(crop, (box[0], box[1]), m)
        # the inset hangs from the lion's eye: a dashed sight line
        ex, ey = li['eye']
        for i in range(14):
            a_, b_ = i / 14, (i + .5) / 14
            p0 = (ex + (cx - ex) * a_, ey + (cy + R - ey) * a_); p1 = (ex + (cx - ex) * b_, ey + (cy + R - ey) * b_)
            d.line([p0, p1], fill=INK, width=14); d.line([p0, p1], fill=(255, 220, 90), width=7)
        if not HIDE_UI:
            put_chip(img, "LION'S VIEW", (60, 60, 70), cx, cy + R + 20, kin, size=48)
            if kb > .6:
                put_chip(img, 'NO STRIPES', (110, 110, 120), cx, cy - R - 10, pop(u, cue(16) + .1, .3), size=46)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1200, vig=(.28, (60, 30, 30)))
    return img, {'faces': [], 'avoid': [(160, 260, 920, 1040), (300, 1350, 900, 1560)]}


# ---------------------------------------------------------------- s05: cooling?
def shimmer_lines(img, u, x0, x1, y0, y1, n=9, col=(255, 240, 210), a=150):
    lay = layer(); d = ImageDraw.Draw(lay)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + .5) / n
        ph = u * 3 + i
        pts = [(x + 14 * math.sin(ph + yy / 40), yy) for yy in np.arange(y1, y0, -12) - (u * 120 + i * 40) % 80]
        d.line(pts, fill=col + (a,), width=6, joint='curve')
    img.alpha_composite(kit.soft_layer(lay, 2))


def s05(u, D, cue):
    w = u + 40
    img = Image.new('RGBA', (W, H))
    SV.savanna(img, w, 0, horizon=1060, sun=(820, 520), sun_r=130, kind='noon', hot=1.0, trees=True)
    SV.savanna_grass(img, w, (-60, 1080, W + 60, H), 300, 14, 40, seed=121, clump=(2, 4))
    A.contact(img, 520, 1640, 800, .35, (90, 60, 30))
    A.put(img, 'zebra', 520, 1640, 520, face=1, pose=zebra_pose(w, 2.0), sun_k=1.4)
    shimmer_lines(img, w, 160, 880, 860, 1150, n=8)
    # sun heat rays pulsing
    radial(img, 820, 520, 520 * (1 + .05 * math.sin(u * 5)), (255, 220, 120), .35)
    th = SV.thermometer(img, 930, 1500, 420, .55 + .1 * smooth(seg(u, 0, D)), t=u, s=.9)
    img = finish(img, w, 1.03 + .03 * smooth(u / D), 520, 1300, vig=(.26, (70, 40, 20)))
    if not HIDE_UI:
        stitle(img, 's05_t', [('COOLING?', 'white', 150)], 220, u, cue(4) - .15)
    return img, {'faces': [], 'avoid': [(0, 160, W, 400), (840, 1000, 1040, 1600)]}


def barrel(img, x, gy, s, kind, t):
    """A metal water barrel WRAPPED in a hide: kind 'zebra' (zebra skin) or 'grey' (plain grey hide). The hide is
    folded over the rim with a ragged edge, tied with two ropes; the metal shows only at the bottom band."""
    w_, h_ = 300 * s, 420 * s
    lay = layer(int(w_ + 80), int(h_ + 120)); d = ImageDraw.Draw(lay)
    x0, y0 = 40, 60
    d.ellipse([x0, y0 + h_ - 40 * s, x0 + w_, y0 + h_ + 30 * s], fill=INK)
    d.rectangle([x0, y0, x0 + w_, y0 + h_], fill=(140, 144, 152))
    # the hide: from over the rim down to a ragged lower edge
    hp = [(x0 - 8 * s, y0 - 6 * s)]
    for k in range(13):
        xx = x0 - 8 * s + (w_ + 16 * s) * k / 12
        hp.append((xx, y0 + h_ - 70 * s + (18 * s if k % 2 else -6 * s) + 10 * s * math.sin(k * 2.3)))
    hp.append((x0 + w_ + 8 * s, y0 - 6 * s))
    top = [(x0 - 8 * s + (w_ + 16 * s) * k / 12, y0 - 34 * s + 14 * s * math.sin(k * 1.7) + 26 * s * math.sin(math.pi * k / 12)) for k in range(13)]
    hide = Image.new('L', lay.size, 0)
    ImageDraw.Draw(hide).polygon(top + hp[::-1][1:-1], fill=255)
    col = (242, 238, 228) if kind == 'zebra' else (150, 146, 142)
    lay.paste(Image.new('RGBA', lay.size, col + (255,)), (0, 0), hide)
    if kind == 'zebra':
        sm = Image.new('L', lay.size, 0); ds = ImageDraw.Draw(sm)
        for k in range(-2, 12):
            xx = x0 + k * 32 * s
            pts = [(xx + 30 * s * math.sin(yy / (90 * s) + k) * .5 + (yy - y0) * .08, yy) for yy in np.arange(y0 - 40 * s, y0 + h_, 12)]
            ds.line(pts, fill=255, width=int(17 * s - abs(k - 5) * .6))
        lay.paste(Image.new('RGBA', lay.size, (28, 26, 30, 255)), (0, 0), ImageChops.multiply(sm, hide))
    else:                                                              # a few darker hair tufts
        sm = Image.new('L', lay.size, 0); ds = ImageDraw.Draw(sm)
        for k in range(40):
            xx = x0 + (k * 37) % int(w_); yy = y0 + (k * 53) % int(h_ - 60 * s)
            ds.line([(xx, yy), (xx + 6, yy + 16)], fill=255, width=3)
        lay.paste(Image.new('RGBA', lay.size, (120, 116, 112, 255)), (0, 0), ImageChops.multiply(sm, hide))
    # cylinder shading over everything
    sh = Image.new('L', lay.size, 0); dsh = ImageDraw.Draw(sh)
    for i in range(int(w_ + 16 * s)):
        v = abs(i / (w_ + 16 * s) - .32) ** 1.4 * 210
        dsh.line([(x0 - 8 * s + i, 0), (x0 - 8 * s + i, lay.height)], fill=int(min(170, v)))
    lay.paste(Image.new('RGBA', lay.size, (30, 30, 50, 255)), (0, 0), ImageChops.multiply(sh, lay.split()[3]).point(lambda v: int(v * .45)))
    d.line(top + hp[::-1][1:-1] + [top[0]], fill=INK, width=6, joint='curve')
    for yy in (y0 + 90 * s, y0 + h_ - 130 * s):                          # ropes
        d.line([(x0 - 8 * s, yy), (x0 + w_ + 8 * s, yy + 8 * s)], fill=INK, width=int(16 * s))
        d.line([(x0 - 8 * s, yy), (x0 + w_ + 8 * s, yy + 8 * s)], fill=(196, 160, 100), width=int(9 * s))
    d.line([(x0, y0 + h_ - 60 * s), (x0, y0 + h_)], fill=INK, width=6); d.line([(x0 + w_, y0 + h_ - 60 * s), (x0 + w_, y0 + h_)], fill=INK, width=6)
    d.arc([x0, y0 + h_ - 30 * s, x0 + w_, y0 + h_ + 30 * s], 0, 180, fill=INK, width=6)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(gy - h_ - 60)))


def s05b(u, D, cue):
    w = u + 43
    img = Image.new('RGBA', (W, H))
    SV.savanna(img, w, 0, horizon=980, sun=(540, 420), sun_r=120, kind='noon', hot=1.0, trees=False)
    dm = mask(); ImageDraw.Draw(dm).rectangle([0, 1060, W, H], fill=255)
    fill_mask(img, dm, (214, 190, 150))
    yard = ImageDraw.Draw(img)
    for i in range(60):
        rx_ = (i * 137) % W; ry_ = 1080 + (i * 71) % 800
        yard.ellipse([rx_ - 18, ry_ - 5, rx_ + 18, ry_ + 5], fill=(190, 164, 124))
    SV.savanna_grass(img, w, (-60, 1040, W + 60, 1100), 120, 10, 26, seed=131, clump=(2, 4))
    radial(img, 540, 420, 620 * (1 + .04 * math.sin(u * 5)), (255, 226, 130), .3)
    kt = smooth(seg(u, .3, cue(13)))
    lvl = .25 + .6 * kt + .02 * math.sin(u * 7)
    for x, kind in ((250, 'zebra'), (700, 'grey')):
        A.contact(img, x, 1500, 380, .4, (90, 60, 30))
        barrel(img, x, 1500, 1.0, kind, w)
        SV.thermometer(img, x + 205, 1430, 360, lvl, t=u, s=.72)
    shimmer_lines(img, w, 120, 960, 900, 1100, n=10)
    G = {}
    kl = out_back(seg(u, cue(12) - .3, cue(13)), 1.4)
    pA = mix(POSES['stand'], POSES['point'] if False else dict(POSES['stand'], armR=(-75, -85)), kl)
    G['a'] = sci(img, w, 'A', pA, 'thinking', 985, 1930, .5, look=-.6, kw=dict(hat='cowboy', hat_col=(196, 170, 110), shirt='#b89a62', pants='#6c5a3e'))
    img = finish(img, w, 1.03 + .02 * smooth(u / D), 540, 1300, vig=(.26, (70, 40, 20)))
    if not HIDE_UI:
        put_chip(img, 'ZEBRA HIDE', (40, 40, 48), 260, 900, pop(u, cue(9) - .2, .3), size=44)
        put_chip(img, 'GREY HIDE', (120, 120, 126), 720, 900, pop(u, cue(9), .3), size=44)
        kx = pop(u, .1, .3)
        put_chip(img, 'COOLING?', (60, 60, 70), 540, 250, kx, size=70)
        if u > cue(14) - .05: draw_x(img, 840, 250, 70, (u - cue(14) + .05) / .12)
        chip(img, 'JUST AS HOT', (220, 70, 50), 540, 420, u, cue(12) - .1, size=60)
    return img, {'faces': [face_box(G['a'], 1.3)], 'avoid': [(0, 150, W, 500), (100, 850, 1000, 1520)]}


# ---------------------------------------------------------------- s06: CLUE 1, the map
def wall_bg(img, u, col=(64, 48, 40)):
    img.paste(vgrad([(0, (58, 44, 40)), (.5, (84, 62, 50)), (1, (40, 30, 30))]), (0, 0))
    d = ImageDraw.Draw(img)
    for x in range(-40, W + 40, 120):
        d.line([(x, 0), (x, H)], fill=(70, 52, 44), width=4)
    radial(img, 540, 900, 900, (255, 200, 130), .35 + .03 * math.sin(u * 2))


def zebra_icon(img, x, y, s, bold, u, ph=0.0):
    """Little zebra on the map. bold 0..1: faded = southern zebras with pale, brownish stripes."""
    lay, o = A.quad('zebra', s, pose={'tail': q(10 * math.sin(u * 2 + ph), 5)}, face=1, ink_w=3)
    if bold < .95:
        a = np.asarray(lay, np.float32).copy()
        lum = a[..., :3].mean(-1, keepdims=True)
        tan = np.array((206, 176, 130), np.float32)
        k = (1 - bold) * .8 * (lum < 120)
        a[..., :3] = a[..., :3] * (1 - k) + tan * k
        lay = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    A._paste(img, lay, int(x - o[0]), int(y - o[1]))


def s06(u, D, cue):
    w = u
    img = Image.new('RGBA', (W, H))
    wall_bg(img, u)
    bx0, by0, bx1, by1 = 70, 380, 1010, 1480
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([bx0 + 10, by0 + 14, bx1 + 10, by1 + 14], 24, fill=(20, 14, 16))
    d.rounded_rectangle([bx0, by0, bx1, by1], 24, fill=(226, 210, 172), outline=INK, width=8)
    radial(img, 540, 900, 700, (120, 180, 210), .25, add=False, box=None)
    tf = SV.lonlat(320, 770, 10.2)
    pts = [tf(lo, la) for lo, la in SV.africa_pts()]
    d.polygon(pts, fill=(176, 160, 112), outline=INK)
    d.line(pts, fill=INK, width=7, joint='curve')
    md = [tf(lo, la) for lo, la in SV.madagascar_pts()]
    d.polygon(md, fill=(176, 160, 112)); d.line(md + [md[0]], fill=INK, width=5)
    # the biting-fly heat zone grows on "biting flies"
    kz = smooth(seg(u, cue(7) - .4, cue(9) + .2))
    if kz > 0:
        zm = mask(); dz = ImageDraw.Draw(zm)
        for lo, la, r in ((30, 0, 15), (36, -6, 11), (22, 4, 12), (16, -2, 9), (34, 8, 9)):
            cx, cy = tf(lo, la); rr = r * 10.2 * kz * (1 + .04 * math.sin(u * 4 + lo))
            dz.ellipse([cx - rr * 1.2, cy - rr, cx + rr * 1.2, cy + rr], fill=255)
        am = mask(); ImageDraw.Draw(am).polygon(pts, fill=255)
        zm = ImageChops.multiply(zm.filter(ImageFilter.GaussianBlur(30)), am)
        fill_mask(img, zm, (230, 50, 40), .75)
        # tiny flies buzzing in the zone
        for i in range(7):
            cx, cy = tf(28 + 8 * math.sin(i * 2.1 + u * 1.3), 0 + 7 * math.cos(i * 1.7 + u * 1.1))
            A.put_fly(img, cx, cy, (32 if i % 2 else -32), wing='blur', ph=u * 7 + i)
    # zebras: bold in East Africa (in the zone), fading toward the south
    for (lo, la, bold, t0) in ((36, -3, 1.0, cue(2)), (24, -18, .5, cue(3)), (24, -29, .15, cue(4))):
        k = pop(u, t0 - .1, .35)
        if k > .05:
            x, y = tf(lo, la)
            zebra_icon(img, x, y + 50, (150 if bold > .9 else 110) * min(1, k), bold, u, lo)
    if not HIDE_UI:
        kb = pop(u, cue(5) - .1, .3)
        if kb > 0:
            x, y = tf(36, -3)
            put_chip(img, 'BOLDEST STRIPES', (40, 40, 48), 790, 560, kb, size=42)
            dd_ = ImageDraw.Draw(img)
            for wd, col in ((14, INK), (7, (255, 255, 255))): dd_.line([(790, 600), (x + 30, y - 60)], fill=col, width=wd)
        kf = pop(u, cue(8), .3)
        if kf > 0: put_chip(img, 'BITING FLIES', (220, 60, 50), 330, 620, kf, size=46)
    G = {}
    kp = out_back(seg(u, cue(5) - .3, cue(5) + .2), 1.4)
    pose = mix(POSES['stand'], dict(POSES['stand'], armL=(100, 110)), kp)
    G['a'] = sci(img, w, 'A', pose, 'thinking', 150, 1960, .44, look=.6, label_on=False, aura=(255, 210, 150))
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1000, vig=(.34, (20, 10, 10)))
    clue(img, 'CLUE 1', u, .05, 250)
    return img, {'faces': [face_box(G['a'], 1.3)], 'avoid': [(0, 160, W, 340), (200, 480, 900, 1400)]}


# ---------------------------------------------------------------- s07: CLUE 2, the horse fly
def bokeh_bg(img, u, cols=((120, 170, 90), (180, 200, 110), (240, 220, 150)), base=None):
    img.paste(vgrad(base or [(0, (110, 150, 120)), (.5, (150, 176, 110)), (1, (80, 110, 70))]), (0, 0))
    rng = np.random.default_rng(5)
    lay = layer(); d = ImageDraw.Draw(lay)
    for i in range(26):
        x = rng.uniform(0, W) + 30 * math.sin(u * .4 + i); y = rng.uniform(0, H); r = rng.uniform(40, 150)
        c = cols[i % len(cols)]
        d.ellipse([x - r, y - r, x + r, y + r], fill=c + (int(rng.uniform(50, 120)),))
    img.alpha_composite(kit.soft_layer(lay, 22))


def s07(u, D, cue):
    w = u + 50
    img = Image.new('RGBA', (W, H))
    bokeh_bg(img, u)
    # the fly on a patch of hide (bottom), big
    d = ImageDraw.Draw(img)
    hide_y = 1330
    hm = mask(); ImageDraw.Draw(hm).polygon([(-20, hide_y + 40), (W + 20, hide_y - 30), (W + 20, H), (-20, H)], fill=255)
    fill_mask(img, hm, (150, 88, 52))
    rng = np.random.default_rng(3)
    for i in range(500):
        x = rng.uniform(0, W); y = rng.uniform(hide_y - 20, H)
        if y < hide_y + 40 - x * 70 / W: continue
        d.line([(x, y), (x + 6, y - 22)], fill=(118, 66, 40) if i % 3 else (178, 110, 66), width=4)
    kit.light_rays(img, 980, -60, (255, 246, 210), n=8, alpha=.25, spread=(100, 160), length=2400, seed=6, phase=math.sin(u * .4))
    dust(img, 17, 40, (0, 200, W, 1300), (255, 252, 230), 130, size=(2, 6), t=u)
    kin = smooth(seg(u, 0, .7))
    x = 520 + 200 * (1 - kin); y = 1050 - 120 * (1 - kin) + 6 * math.sin(u * 3)
    legs = .55 + .45 * kin
    A.put_fly(img, x, y, 620, ang=4 * (1 - kin), wing='fold' if kin > .9 else 'blur', legs=legs, ph=u * 7)
    img = finish(img, w, 1.0 + .05 * smooth(u / D), 540, 1050, vig=(.3, (20, 30, 20)))
    if not HIDE_UI:
        chip(img, 'HORSE FLY', (40, 40, 48), 380, 560, u, cue(2) - .1, size=58)
        chip(img, 'SPREADS DEADLY DISEASES', (220, 60, 50), 540, 1560, u, cue(5) - .1, size=50)
    clue(img, 'CLUE 2', u, .05, 250)
    return img, {'faces': [], 'avoid': [(0, 160, W, 640), (100, 700, 1000, 1380), (80, 1500, 1000, 1620)]}


def s07b(u, D, cue):
    """Macro cross-section: zebra skin with short striped hair; the fly's blade mouth reaches the skin."""
    w = u + 53
    img = Image.new('RGBA', (W, H))
    bokeh_bg(img, u, cols=((240, 220, 160), (200, 180, 120), (255, 236, 190)),
             base=[(0, (180, 150, 100)), (.5, (210, 176, 120)), (1, (150, 110, 80))])
    kit.light_rays(img, 900, -60, (255, 240, 200), n=8, alpha=.25, spread=(100, 160), length=2400, seed=7, phase=math.sin(u * .4))
    dust(img, 18, 40, (0, 200, W, 1250), (255, 250, 230), 130, size=(2, 6), t=u)
    sy = 1300
    d = ImageDraw.Draw(img)
    # skin layers
    d.rectangle([0, sy, W, H], fill=(214, 150, 140))
    d.rectangle([0, sy + 70, W, H], fill=(190, 120, 116))
    d.rectangle([0, sy + 220, W, H], fill=(166, 100, 100))
    for x in range(0, W, 90):
        d.arc([x - 60, sy + 120, x + 60, sy + 200], 0, 180, fill=(150, 80, 84), width=5)
    d.line([(0, sy), (W, sy)], fill=INK, width=8)
    # short hair: groups of black and white
    rng = np.random.default_rng(9)
    for i in range(70):
        x = 10 + i * 15.4 + rng.uniform(-3, 3)
        black = (x // 154) % 2 == 0
        L = rng.uniform(70, 96); a = .35 + .1 * math.sin(u * 1.5 + i * .3)
        tip = (x + math.sin(a) * L, sy - math.cos(a) * L)
        d.line([(x, sy), tip], fill=INK, width=13)
        d.line([(x, sy), tip], fill=(30, 28, 32) if black else (246, 244, 236), width=8)
    # bracket: hair length
    kb = pop(u, cue(11) - .1, .3)
    if kb > 0 and not HIDE_UI:
        d.line([(990, sy - 100), (990, sy)], fill=INK, width=12); d.line([(990, sy - 100), (990, sy)], fill=(255, 210, 60), width=6)
        for yy in (sy - 100, sy):
            d.line([(970, yy), (1010, yy)], fill=INK, width=12); d.line([(970, yy), (1010, yy)], fill=(255, 210, 60), width=6)
        put_chip(img, 'SHORT HAIR', (40, 40, 48), 760, sy - 190, kb, size=50)
    # the fly lands on the hair tips; the mouth blade goes down to the skin on "bite"
    kd = smooth(seg(u, .0, cue(13)))
    fx, fy = 450, sy - 330 + 90 * kd
    A.put_fly(img, fx, fy, 640, ang=-18, wing='fold', legs=1.0)
    kp = smooth(seg(u, cue(14) - .3, cue(16)))
    if kp > 0:
        mx, my = fx + 150, fy + 150
        ey = my + (sy + 30 - my) * kp
        d.polygon([(mx - 14, my), (mx + 14, my), (mx + 6, ey), (mx - 2, ey + 14)], fill=(60, 50, 48), outline=INK)
        if kp > .95:
            r = 50 + 20 * math.sin(u * 9)
            m = mask(); ImageDraw.Draw(m).ellipse([mx - r, sy + 30 - r * .6, mx + r, sy + 30 + r * .6], fill=255)
            glow(img, m, (255, 60, 50), .8, blur=18)
            if not HIDE_UI: put_chip(img, 'BITE', (220, 60, 50), mx + 220, sy + 140, pop(u, cue(16), .3), size=60)
    img = finish(img, w, 1.03 + .03 * smooth(u / D), 540, 1200, vig=(.3, (40, 20, 20)))
    return img, {'faces': [], 'avoid': [(100, 700, 1060, 1500), (700, 1050, 1060, 1200)]}


# ---------------------------------------------------------------- s08: CLUE 3, fewer landings except on the bare head
def s08(u, D, cue):
    w = u + 60
    cam = 12 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    SV.english_field(img, w, cam, horizon=860)
    hx, hgy, hs = 700 + cam * .8, 1470, 400
    A.contact(img, hx, hgy + 6, hs * 1.6, .35, (40, 70, 30))
    hi = A.put(img, 'coat', hx, hgy, hs, face=-1, pose=horse_pose(w))
    # flies over the coat: they come close and veer off (no landing)
    fc = (hx + 60, hgy - hs * .78)
    for i, (ph, ww) in enumerate(((0, 1.4), (2.0, -1.2), (4.0, 1.6), (1.0, -1.5), (3.0, 1.3))):
        fly_at(img, orbit(fc[0], fc[1], hs * .7, hs * .3, ww, ph, wob=.4), w, 54, trail=.4, r=6)
    # landed flies on the bare head (they appear one by one)
    hd = hi['head']
    spots = [(-70, -50), (40, 10), (-20, 75), (70, -45), (-95, 40)]
    for i, (dx, dy) in enumerate(spots):
        t0 = cue(10) - .6 + i * .22
        if u < t0: continue
        k = smooth(seg(u, t0, t0 + .3))
        px, py = hd[0] + dx - 200 * (1 - k), hd[1] + dy - 160 * (1 - k)
        A.put_fly(img, px, py, -74, ang=10 * math.sin(u * 3 + i), wing='fold' if k > .95 else 'blur', legs=k, ph=u * 7 + i)
    G = {}
    G['b'] = sci(img, w, 'B', 'hold', 'thinking', 860 + cam * 1.1, 1990, .5, look=-.5, board=True,
                 counts=(min(2, int(u / 1.5)), min(9, int(max(0, u - cue(10) + .6) * 4))), bphase=.2)
    SV.field_front(img, w, cam)
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 560, 1200, vig=(.24, (30, 40, 30)))
    kr = smooth(seg(u, cue(13) - .2, cue(13) + .2))
    if kr > 0 and not HIDE_UI:
        d = ImageDraw.Draw(img); r = max(12.0, 160 * kr + 6 * math.sin(u * 6))
        z = 1.02 + .03 * smooth(u / D)
        cx, cy = 560 + (hd[0] - 560) * z, 1200 + (hd[1] - 1200) * z
        for wd, col in ((26, INK), (16, (255, 255, 255)), (9, (230, 50, 40))):
            d.ellipse([cx - r * 1.2, cy - r, cx + r * 1.2, cy + r], outline=col, width=wd)
        put_chip(img, 'BARE HEAD: BITTEN', (220, 60, 50), max(330, cx + 80), cy + r + 70, pop(u, cue(13), .3), size=46)
    if not HIDE_UI:
        chip(img, 'COAT: FEWER LANDINGS', (40, 40, 48), 600, 560, u, cue(7) - .1, size=48)
    clue(img, 'CLUE 3', u, .05, 250)
    return img, {'faces': [face_box(G['b'], 1.3)], 'avoid': [(0, 160, W, 620), (100, 760, 900, 1400)]}


# ---------------------------------------------------------------- s09: the riddle
def coat_close(img, w, cam, kind='coat', s=760, x=None, gy=2000, horizon=980, pose=None):
    """The horse's back close up, filling the frame width (s10-s12 framing), evening light."""
    SV.english_field(img, w, cam * .3, horizon=horizon, fence_on=True, fg=False, kind='evening', sun=(880, 760))
    x = 860 + cam if x is None else x
    A.put(img, kind, x, gy, s, face=-1, pose=pose or {'neck': 0, 'tail': 0, 'breath': q(.5 + .5 * math.sin(w * 2), .5)}, cache=True,
          light=(1, -.6), rim=(255, 200, 140), rim_a=.6)
    return lambda xx: gy - s * .985 + 0 * xx                          # the back line (approx)


def s09(u, D, cue):
    w = u + 70
    img = Image.new('RGBA', (W, H))
    SV.english_field(img, w, 0, horizon=820, fg=False)
    A.put(img, 'coat', 640, 2080, 820, face=-1, pose={'neck': 0, 'tail': 0, 'breath': q(.5 + .5 * math.sin(w * 2), .5)})
    fx, fy = 640 + 60 * math.sin(u * 1.7), 860 + 40 * math.sin(u * 2.3)
    radial(img, fx, fy, 380, (255, 240, 180), .55)
    A.put_fly(img, fx, fy, -330, ang=6 * math.sin(u * 3), wing='blur', legs=.2, ph=u * 7)
    G = {}
    G['a'] = sci(img, w, 'A', 'think', 'thinking', 170, 1990, .62, look=.5)
    img = finish(img, w, 1.0 + .05 * smooth(u / D), 560, 900, vig=(.3, (30, 40, 30)))
    qmark(img, 880, 560, 1.5, u, cue(1) - .1, KEY)
    return img, {'faces': [face_box(G['a'], 1.3)], 'avoid': [(300, 520, 900, 900), (700, 300, 1060, 720)]}


# ---------------------------------------------------------------- s10: the landing approach (diagram)
def approach_path(t, t0, t1, p0, p1, ease=3.0):
    """Position along an approach from p0 to p1 between t0 and t1: fast start, braking at the end (ease-out)."""
    v = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    e = 1 - (1 - v) ** ease
    x = p0[0] + (p1[0] - p0[0]) * e
    y = p0[1] + (p1[1] - p0[1]) * e - 140 * math.sin(math.pi * e) * .5
    return x, y


def stage_bg(img, u, top=(24, 34, 64), bot=(40, 60, 96)):
    img.paste(vgrad([(0, top), (1, bot)]), (0, 0))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=lerp(top, (255, 255, 255), .07), width=2)
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=lerp(top, (255, 255, 255), .07), width=2)
    radial(img, 540, 1100, 900, (120, 160, 255), .2)


def speed_bar(img, x, y, v, label_txt='SPEED'):
    """A horizontal speed meter (v 0..1)."""
    d = ImageDraw.Draw(img)
    w_, h_ = 420, 44
    d.rounded_rectangle([x - w_ / 2 - 6, y - h_ / 2 - 6, x + w_ / 2 + 6, y + h_ / 2 + 6], 28, fill=INK)
    d.rounded_rectangle([x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2], 22, fill=(60, 70, 90))
    col = lerp((90, 200, 120), (240, 80, 60), v)
    d.rounded_rectangle([x - w_ / 2, y - h_ / 2, x - w_ / 2 + max(44, w_ * v), y + h_ / 2], 22, fill=col)
    d.text((x - w_ / 2, y - h_ / 2 - 30), label_txt, font=font(40, True), fill='white', anchor='ls', stroke_width=5, stroke_fill=INK)


def _hide_strip(sy):
    """The plain horse-hide surface for the diagram (cached): a warm gradient, short hair lying in one direction,
    a lit bevel along the top edge."""
    def build():
        lay = layer(); d = ImageDraw.Draw(lay)
        lay.paste(vgrad([(0, (176, 104, 60)), (.3, (150, 86, 50)), (1, (96, 54, 34))], W, H - sy), (0, sy))
        rng = np.random.default_rng(1)
        for i in range(2600):
            x = rng.uniform(-20, W + 20); y = sy + 8 + (H - sy) * rng.uniform(0, 1) ** 1.4
            L_ = rng.uniform(12, 28) * (1 - .4 * (y - sy) / (H - sy))
            c = lerp((120, 66, 38), (200, 128, 76), rng.uniform(0, 1)) if i % 3 else (88, 48, 30)
            d.line([(x, y), (x + L_ * .8, y - L_ * .45)], fill=c, width=3)
        hl = mask(); ImageDraw.Draw(hl).rectangle([0, sy, W, sy + 22], fill=255)
        fill_mask(lay, hl, (236, 170, 110), .5, blur=6)
        d.line([(-20, sy), (W + 20, sy)], fill=INK, width=8)
        return lay
    return P.cached(('hide', sy), build)


def s10(u, D, cue):
    w = u + 80
    img = Image.new('RGBA', (W, H))
    stage_bg(img, u)
    sy = 1360
    p0, p1 = (-160, 520), (690, sy - 96)
    # a soft spotlight from above onto the landing spot
    cone = mask(); ImageDraw.Draw(cone).polygon([(620, -40), (780, -40), (980, sy), (400, sy)], fill=255)
    fill_mask(img, cone, (210, 226, 255), .10 + .015 * math.sin(u * 2), blur=40)
    img.alpha_composite(_hide_strip(sy))
    pool = mask(); ImageDraw.Draw(pool).ellipse([420, sy - 40, 960, sy + 110], fill=255)
    fill_mask(img, pool, (255, 236, 200), .32, blur=30)
    t0, t1 = .1, cue(14) - .05
    pos = lambda t: approach_path(t, t0, t1, p0, p1, 3.2) if t < t1 else (p1[0], p1[1] + 0 * t)
    v = max(0.0, min(1.0, (u - t0) / (t1 - t0)))
    sp = 3.2 * (1 - v) ** 2.2 if u < t1 else 0.0
    legs = smooth(seg(u, cue(10), t1))
    # the fly's shadow on the hide grows sharper as it comes down
    fx_, fy_ = pos(u)
    k_sh = max(0.0, min(1.0, 1 - (sy - fy_) / 900))
    shm = mask(); ImageDraw.Draw(shm).ellipse([fx_ - 120, sy + 18, fx_ + 120, sy + 48], fill=255)
    fill_mask(img, shm, (40, 20, 14), .45 * k_sh, blur=14 - 8 * k_sh)
    fly_at(img, pos, u, 300, trail=6, dt=.1, legs=legs, wing='blur' if u < t1 + .15 else 'fold', r=13, t_min=t0, tcol=(255, 236, 120))
    if not HIDE_UI:
        speed_bar(img, 540, 300, min(1, sp / 3.0))
        chip(img, 'FAST', (230, 80, 60), 200, 520, u, cue(5) - .2, size=56)
        chip(img, 'SLOWS DOWN', (90, 170, 110), 520, 1010, u, cue(7) - .1, size=56)
        chip(img, 'LANDS', (60, 140, 220), 900, 1150, u, cue(14) - .1, size=60)
        chip(img, 'DOTS = EVERY 0.1 S', (60, 70, 90), 540, 1720, u, .4, size=40)
    img = finish(img, w, 1.0 + .02 * smooth(u / D), 540, 1000, vig=(.3, (10, 10, 30)))
    dust(img, 21, 30, (0, 300, W, 1350), (200, 220, 255), 110, size=(2, 5), t=u)
    return img, {'faces': [], 'avoid': [(200, 200, 880, 360), (60, 440, 1040, 1420), (300, 1660, 780, 1780)]}


# ---------------------------------------------------------------- s11 / s12: plain horse vs stripes
def check_mark(img, x, y, r, k, col=(70, 190, 100)):
    if k <= 0: return
    d = ImageDraw.Draw(img)
    a, b, c = (x - r, y), (x - r * .3, y + r * .7), (x + r, y - r * .8)
    f = min(1, k * 2)
    pts = [a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]
    if k > .5:
        g = (k - .5) * 2; pts = [a, b, (b[0] + (c[0] - b[0]) * g, b[1] + (c[1] - b[1]) * g)]
    d.line(pts, fill=INK, width=38, joint='curve'); d.line(pts, fill=col, width=24, joint='curve')


def s11(u, D, cue):
    w = u + 90
    img = Image.new('RGBA', (W, H))
    back = coat_close(img, w, 0, kind='horse')
    by = back(540)
    t0, t1 = .05, cue(7) + .15
    p0, p1 = (-120, 560), (640, by - 86)
    pos = lambda t: approach_path(t, t0, t1, p0, p1, 3.4) if t < t1 else (p1[0] - 2 * math.sin(t * 3), p1[1])
    legs = smooth(seg(u, cue(4), t1))
    fly_at(img, pos, u, 200, trail=6, dt=.1, legs=legs, wing='blur' if u < t1 + .1 else 'fold', r=12, t_min=t0, tcol=(255, 236, 120))
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 560, 1100, vig=(.24, (30, 40, 30)))
    if not HIDE_UI:
        put_chip(img, 'PLAIN HORSE', (140, 80, 44), 540, 260, pop(u, .0, .3), size=62)
        chip(img, 'BRAKES', (90, 170, 110), 540, 400, u, cue(5) - .1, size=56)
        check_mark(img, 860, 980, 90, seg(u, cue(7), cue(8) + .1))
    return img, {'faces': [], 'avoid': [(200, 180, 880, 460), (0, 540, 1080, 1300)]}


def s12(u, D, cue):
    w = u + 100
    img = Image.new('RGBA', (W, H))
    back = coat_close(img, w, 0, kind='coat')
    by = back(540)
    d = ImageDraw.Draw(img)
    # fly 1: no braking -> bonk on "bumps", bounces off tumbling
    tb = cue(7)
    p0, p1 = (-140, 560), (620, by - 60)
    def pos1(t):
        if t < tb:
            v = max(0.0, (t - .05) / (tb - .05)); e = v ** 1.05
            return (p0[0] + (p1[0] - p0[0]) * e, p0[1] + (p1[1] - p0[1]) * e - 70 * math.sin(math.pi * e))
        k = t - tb
        return (p1[0] - 260 * k, p1[1] - 520 * k + 500 * k * k)
    if u < tb + 1.6:
        x, y = pos1(u)
        if u < tb:
            fly_at(img, pos1, u, 200, trail=6, dt=.1, legs=0.0, r=12, t_min=.05, tcol=(255, 236, 120))
        else:
            pts = [pos1(t) for t in np.arange(.05, tb, .1)]
            SV.dots_trail(img, pts, r=12, col=(255, 236, 120))
            A.put_fly(img, x, y, 200, ang=-(u - tb) * 700, wing='blur', legs=.3, ph=u * 7)
    bonk_star(img, p1[0] + 70, p1[1] + 40, (u - tb) / .45, 1.3)
    # fly 2: zooms past on "zooms"
    tz = cue(12) - .4
    if u > tz - .1:
        pos2 = lambda t: (-200 + 1600 * (t - tz) / .9, by - 190 + 40 * math.sin((t - tz) * 6))
        fly_at(img, pos2, u, 180, trail=.9, dt=.1, legs=0, r=11, t_min=tz, tcol=(255, 236, 120))
    sx, sy = shake(u, tb, 12, .35)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 560, 1100, dx=sx, dy=sy, vig=(.24, (30, 40, 30)))
    if not HIDE_UI:
        put_chip(img, 'STRIPES', (40, 40, 48), 540, 260, pop(u, .0, .3), size=62)
        chip(img, 'NO BRAKING', (230, 80, 60), 540, 400, u, cue(3) - .1, size=56)
        chip(img, 'BONK!', (255, 200, 40), 820, 1000, u, tb, size=60, angle=8)
        chip(img, 'ZOOMS PAST', (230, 80, 60), 700, 860, u, cue(12), size=52)
        if u > cue(12) + .2: draw_x(img, 880, 380, 80, (u - cue(12) - .2) / .12)
    return img, {'faces': [], 'avoid': [(200, 180, 880, 460), (0, 540, 1080, 1300)]}


# ---------------------------------------------------------------- s13: the fly's-eye view
_STRIPE = {}
def stripe_field():
    if 'f' not in _STRIPE:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        ph = xx / 120 + .35 * np.sin(yy / 260) + .15 * np.sin(yy / 90 + xx / 300)
        v = (np.sin(2 * np.pi * ph) > 0).astype(np.float32)
        v = np.asarray(Image.fromarray((v * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
        col = np.array((28, 26, 32), np.float32) * v[..., None] + np.array((240, 238, 230), np.float32) * (1 - v[..., None])
        _STRIPE['f'] = Image.fromarray(col.astype(np.uint8)).convert('RGBA')
    return _STRIPE['f']


def s13(u, D, cue):
    w = u + 110
    img = Image.new('RGBA', (W, H), (10, 30, 20, 255))
    base = stripe_field()
    ks = smooth(seg(u, cue(1) - .2, cue(2) + .2))          # the scramble grows
    r = 74
    hx = r * math.sqrt(3)
    rng = np.random.default_rng(13)
    d = ImageDraw.Draw(img)
    hexes = []
    row = 0
    y = -r
    while y < H + r:
        x = (hx / 2 if row % 2 else 0) - hx
        while x < W + hx:
            hexes.append((x, y)); x += hx
        y += r * 1.5; row += 1
    for i, (cx, cy) in enumerate(hexes):
        ph = rng.uniform(0, 6.3); amp = rng.uniform(30, 110)
        jx = ks * amp * math.sin(u * 7 + ph); jy = ks * amp * .4 * math.cos(u * 5.3 + ph * 2)
        sc = 1 + ks * .25 * math.sin(u * 4 + ph)
        poly = [(cx + r * math.cos(math.pi / 6 + k * math.pi / 3), cy + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
        m = mask(int(2 * r + 4), int(2 * r + 4)); ImageDraw.Draw(m).polygon([(p[0] - cx + r + 2, p[1] - cy + r + 2) for p in poly], fill=255)
        sx0, sy0 = int(cx - r - 2 + jx), int(cy - r - 2 + jy)
        crop = base.crop((sx0, sy0, sx0 + m.width, sy0 + m.height))
        img.paste(crop, (int(cx - r - 2), int(cy - r - 2)), m)
    # facet grid + green compound-eye tint
    for cx, cy in hexes:
        poly = [(cx + r * math.cos(math.pi / 6 + k * math.pi / 3), cy + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
        d.line(poly + [poly[0]], fill=(30, 90, 50), width=7)
    tint = Image.new('RGBA', img.size, (60, 180, 90, 50)); img.alpha_composite(tint)
    radial(img, 540, 900, 700, (180, 255, 200), .25 + .1 * ks * math.sin(u * 9))
    # dome vignette: the eye's curved edge
    anim.vignette(img, .75, (8, 40, 20), rx=.62, ry=.48, power=2.6)
    img = finish(img, w, 1.0 + .04 * smooth(u / D), 540, 960, vig=(.2, (8, 30, 16)))
    if not HIDE_UI:
        put_chip(img, "FLY'S-EYE VIEW", (40, 120, 70), 540, 250, pop(u, .0, .3), size=58)
        stitle(img, 's13_t', [('WHERE IS', 'white', 120), ('THE SURFACE?', KEY, 120)], 1540, u, cue(6) - .1, stagger=.2)
    return img, {'faces': [], 'avoid': [(150, 170, 930, 330), (60, 1470, 1020, 1800)]}


# ---------------------------------------------------------------- s14: painted cows in Japan
def _cloud_band(seed, y, h, col=(252, 253, 255), shade=(222, 232, 244), w=W + 900, alpha=.88):
    """A long soft stratus band (cached): lumpy tops, a flat soft base, a pale shaded underside."""
    def build():
        rng = np.random.default_rng(seed)
        m = mask(w, H); dm = ImageDraw.Draw(m)
        x = -60
        while x < w + 60:
            r = rng.uniform(.55, 1.0) * h; yy = y + rng.uniform(-.2, .15) * h
            dm.ellipse([x - r * 1.6, yy - r * .8, x + r * 1.6, yy + r * .5], fill=255)
            x += r * rng.uniform(1.1, 1.9)
        dm.rectangle([-60, y - h * .1, w + 60, y + h * .45], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(h * .25))
        lo = mask(w, H); ImageDraw.Draw(lo).rectangle([0, int(y + h * .05), w, H], fill=255)
        lo = ImageChops.multiply(lo.filter(ImageFilter.GaussianBlur(h * .35)), m)
        k = np.asarray(lo, np.float32)[..., None] / 255 * .8
        rgb_ = np.array(col, np.float32) * (1 - k) + np.array(shade, np.float32) * k
        arr = np.concatenate([rgb_, np.asarray(m, np.float32)[..., None] * alpha], 2)
        lay = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
        return lay
    return P.cached(('cband', seed, y, h, col, shade, w, alpha), build)


def _terraces(seed, horizon, w=W + 600):
    """Rice terraces stepped up a hillside on the right: water-bright flats, dark grassy lips, a few farmers' huts."""
    def build():
        lay = layer(w, H); d = ImageDraw.Draw(lay)
        x0, x1 = 820, w
        top = lambda x: horizon - 40 - 330 * P.smooth((x - x0) / 620)
        xs = np.arange(x0 - 40, x1 + 20, 10)
        d.polygon([(x, top(x)) for x in xs] + [(x1 + 20, horizon + 140), (x0 - 40, horizon + 140)], fill=(96, 140, 92))
        n = 9
        for i in range(n):
            f0, f1 = i / n, (i + 1) / n
            yA = lambda x, f=f0: top(x) + (horizon + 120 - top(x)) * f + 10 * math.sin(x / 90 + i)
            yB = lambda x, f=f1: top(x) + (horizon + 120 - top(x)) * f + 10 * math.sin(x / 90 + i + .7)
            pts = [(x, yA(x)) for x in xs] + [(x, yB(x)) for x in xs[::-1]]
            flat = lerp((150, 196, 120), (186, 214, 150), (i % 3) / 2)
            d.polygon(pts, fill=flat)
            # the water sheen on the flat and the dark lip below it
            d.line([(x, yA(x) + (yB(x) - yA(x)) * .35) for x in xs], fill=(214, 234, 226), width=3)
            d.line([(x, yB(x) - 4) for x in xs], fill=(70, 108, 70), width=7)
            d.line([(x, yB(x) + 2) for x in xs], fill=(120, 160, 104), width=3)
        al = lay.split()[3]
        fill_mask(lay, al.point(lambda v: int(v * .18)), (210, 226, 232))
        return lay
    return P.cached(('terr', seed, horizon, w), build)


def _farmhouse(img, x, y, s):
    """A small farmhouse with a dark curved (irimoya-style) roof and white plaster walls, far off."""
    d = ImageDraw.Draw(img)
    iw = max(2, int(4 * s))
    d.rectangle([x - 120 * s, y - 90 * s, x + 120 * s, y], fill=(238, 232, 218), outline=INK, width=iw)
    for k in range(5): d.line([(x - 120 * s + k * 60 * s, y - 90 * s), (x - 120 * s + k * 60 * s, y)], fill=(110, 80, 60), width=iw)
    d.line([(x - 120 * s, y - 45 * s), (x + 120 * s, y - 45 * s)], fill=(110, 80, 60), width=iw)
    roof = [(x - 175 * s, y - 80 * s), (x - 130 * s, y - 120 * s), (x - 70 * s, y - 175 * s), (x + 70 * s, y - 175 * s), (x + 130 * s, y - 120 * s),
            (x + 175 * s, y - 80 * s), (x + 150 * s, y - 95 * s), (x - 150 * s, y - 95 * s)]
    d.polygon(roof, fill=(58, 62, 76), outline=INK)
    d.line(roof[:6], fill=INK, width=iw)
    d.line([(x - 70 * s, y - 175 * s), (x + 70 * s, y - 175 * s)], fill=(120, 126, 140), width=iw + 2)
    d.rectangle([x - 20 * s, y - 60 * s, x + 25 * s, y], fill=(70, 50, 40), outline=INK, width=iw)


def japan_farm(img, u, cam=0.0, horizon=1000, house=(250, .55)):
    """Rural Japan: a morning sky with a cloud band, layered blue-green mountains with cedar forest, rice terraces on
    the right, a tree line, a farmhouse, a fenced paddock. Returns the paddock's ground line."""
    P.sky(img, 'morning')
    radial(img, 900 + cam * .05, 260, 760, (255, 246, 214), .4)
    P.cumulus(img, u, [(180, 300, .75, 41, 5), (900, 200, .95, 42, 4)], lit=(255, 255, 250), shade=(196, 210, 232), mid=(232, 240, 250))
    P.paste_band(img, P.pine_ridge(181, horizon - 330, 300, (168, 190, 210), tree=(10, 22), dens=.7, haze_col=(214, 228, 238), haze_a=.35), cam, .05)
    img.alpha_composite(_cloud_band(182, horizon - 470, 40), (int(-450 + cam * .07 + (u * 6) % 300 - 150), 0))
    P.paste_band(img, P.pine_ridge(183, horizon - 170, 260, (122, 160, 170), tree=(16, 36), dens=.9, lit=(150, 186, 190),
                                   haze_col=(200, 222, 232), haze_a=.35), cam, .1)
    img.alpha_composite(_cloud_band(184, horizon - 300, 26, col=(244, 248, 252), shade=(206, 222, 232)), (int(-450 + cam * .12 - (u * 4) % 300), 0))
    haze(img, horizon - 420, horizon - 60, (226, 238, 242), .16)
    P.paste_band(img, P.pine_ridge(185, horizon - 40, 200, (84, 128, 110), tree=(22, 48), dens=1.1, lit=(112, 156, 124),
                                   haze_col=(190, 214, 214), haze_a=.25), cam, .18)
    P.paste_band(img, _terraces(186, horizon), cam, .25)
    P.paste_band(img, SV.hedgerow(187, horizon + 40, 30, cols=((92, 140, 84), (70, 116, 72), (52, 92, 62)),
                                  oaks=((200, .42, 4), (760, .5, 5), (1300, .4, 6)), haze_a=.15), cam, .3)
    if house: _farmhouse(img, house[0] + cam * .35, horizon + 60, house[1])
    P.paste_band(img, P.hill(161, horizon + 120, 18, SV.FIELD, ink=None, waves=(.6, 1.4)), cam, .5)
    ground = lambda x: P.edge_y(161, horizon + 120, 18, x - cam * .5, waves=(.6, 1.4))
    SV.fence(img, lambda x: ground(x) + 40, -100, W + 100, cam, .6, post_h=110, gap=240, s=.8)
    P.grass(img, u, (-60, horizon + 100, W + 60, H), 380, 16, 46, cols=SV.FIELD, seed=162, clump=(3, 6))
    SV.flowers(img, 164, (-40, horizon + 180, W + 40, H - 100), 50, u, cam, .7, size=(4, 9))
    return ground


# the stripe columns of the painted cow: boundaries between white stripes (unit X), see animals._paint (pb = X * 6.2)
def _cow_reveal(paint_lay, o, cs, cur, y_top=-1.06, y_bot=-0.30):
    """Mask of the painted part on a face=-1 cow layer: every column behind `cur` (unit X, rump -> head) fully painted,
    the current column painted down to its progress. Returns (mask, (x_col_mid, y_brush) in unit, column [Xa, Xb])."""
    k = math.floor(cur * 6.2 - .75); fr = cur * 6.2 - .75 - k
    Xa, Xb = (.75 + k) / 6.2, (1.75 + k) / 6.2
    yb = y_top + (y_bot - y_top) * fr
    Wd, Hd = paint_lay.size
    xx = np.arange(Wd)[None, :]; yy = np.arange(Hd)[:, None]
    Xl = (o[0] - xx) / cs; Yl = (yy - o[1]) / cs
    m = (Xl < Xa) | ((Xl < Xb) & (Yl < yb))
    return Image.fromarray((m * 255).astype(np.uint8)), ((Xa + Xb) / 2, yb), (Xa, Xb)


def s14(u, D, cue):
    """Japan: the farmer stands BESIDE the cow (right of the rump) and paints white stripes on it from the rump
    forward with a long brush: the rump is done, a wet stroke runs down the current stripe."""
    w = u + 120
    cam = -14 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    ground = japan_farm(img, w, cam, house=(130, .5))
    cx, cgy, cs = 455 + cam * .8, 1640, 310
    A.contact(img, cx + 20, cgy + 6, cs * 1.9, .38, (40, 70, 30))
    pose = {'tail': q(10 * math.sin(w * 1.7), 5), 'ear': q(max(0, math.sin(w * 2)) ** 6, .5), 'neck': q(2 * math.sin(w * .8), 1),
            'breath': q(.5 + .5 * math.sin(w * 2.1), .5)}
    plain, o = A.quad('cow', cs, pose=pose, face=-1, painted=False)
    paint, _ = A.quad('cow', cs, pose=pose, face=-1, painted=True)
    cur = -0.42 + 0.46 * smooth(seg(u, .0, D - .1)) ** .9                 # rump done at the start, mid-barrel by the end
    mk, (bxu, byu), (Xa, Xb) = _cow_reveal(paint, o, cs, cur)
    lay = plain.copy()
    lay.paste(paint, (0, 0), ImageChops.multiply(mk, paint.split()[3]))
    # the wet stroke: the current column glistens
    wet = mask(*lay.size); dw = ImageDraw.Draw(wet)
    xa_px, xb_px = o[0] - Xb * cs, o[0] - Xa * cs
    dw.rectangle([xa_px, 0, xb_px, o[1] + byu * cs], fill=150)
    wet = ImageChops.multiply(ImageChops.multiply(wet, mk), paint.split()[3])
    lay.paste(Image.new('RGBA', lay.size, (255, 255, 255, 255)), (0, 0), wet.point(lambda v: int(v * .35)))
    ox, oy = int(cx - o[0]), int(cgy - o[1])
    A._paste(img, lay, ox, oy)
    # drips under the wet stroke
    d = ImageDraw.Draw(img)
    bx, by = cx - bxu * cs, cgy + byu * cs
    for k in range(5):
        dx_ = (k - 2) * 9
        L_ = (u * 70 + k * 23) % 60
        top_y = cgy - .36 * cs if byu > -.4 else by
        d.line([(bx + dx_, by - 10), (bx + dx_, min(top_y, by) + L_ * .6)], fill=(246, 246, 240), width=5)
    # paint bucket on the grass between the cow's hind legs and the farmer
    bkx, bky = 770 + cam * .8, 1700
    d.polygon([(bkx - 52, bky - 92), (bkx + 52, bky - 92), (bkx + 42, bky), (bkx - 42, bky)], fill=(170, 176, 190), outline=INK, width=5)
    d.ellipse([bkx - 52, bky - 106, bkx + 52, bky - 78], fill=(248, 248, 242), outline=INK, width=5)
    d.arc([bkx - 50, bky - 170, bkx + 50, bky - 60], 200, 340, fill=INK, width=5)
    for k in range(3): d.line([(bkx - 30 + k * 26, bky - 80), (bkx - 32 + k * 26, bky - 50 - k * 8)], fill=(248, 248, 242), width=6)
    # the farmer beside the rump, both hands on a long brush reaching the flank
    G = {}
    fx = 905 + cam * .8
    st = math.sin(u * 7)                                                     # the stroke rhythm
    pp = dict(POSES['stand'], armL=(58 + 6 * st, 70 + 8 * st), armR=(44 + 6 * st, 84 + 6 * st), legL=(14, 2), legR=(-6, -1))
    G['f'] = sci(img, w, 'F', pp, 'determined' if u > cue(3) else 'neutral', fx, 1740, .5, look=-.8, lean=-4, label_on=True,
                 lbl='FARMER', lbl_dy=-30)
    hL, hR = G['f']['hands']['L'], G['f']['hands']['R']
    hx, hy = (hL[0] + hR[0]) / 2, (hL[1] + hR[1]) / 2
    tx, ty = bx + 26, by + 8 * st                                             # the brush head rides the wet stroke
    vx, vy = tx - hx, ty - hy; ln = math.hypot(vx, vy) or 1; ux, uy = vx / ln, vy / ln
    butt = (hx - ux * 70, hy - uy * 70)
    neck_ = (tx - ux * 46, ty - uy * 46)
    d.line([butt, neck_], fill=INK, width=17); d.line([butt, neck_], fill=(184, 134, 82), width=8)
    nx_, ny_ = -uy, ux
    head = [(neck_[0] + nx_ * 34, neck_[1] + ny_ * 34), (neck_[0] - nx_ * 34, neck_[1] - ny_ * 34),
            (tx - nx_ * 40, ty - ny_ * 40), (tx + nx_ * 40, ty + ny_ * 40)]
    d.polygon(head, fill=(196, 150, 96), outline=INK, width=5)
    bristle = [(tx - ux * 6 + nx_ * 40, ty - uy * 6 + ny_ * 40), (tx - ux * 6 - nx_ * 40, ty - uy * 6 - ny_ * 40),
               (tx + ux * 22 - nx_ * 38, ty + uy * 22 - ny_ * 38), (tx + ux * 22 + nx_ * 38, ty + uy * 22 + ny_ * 38)]
    d.polygon(bristle, fill=(248, 248, 242), outline=INK, width=4)
    for hh in (hL, hR):                                                     # hands over the pole
        d.ellipse([hh[0] - 13, hh[1] - 13, hh[0] + 13, hh[1] + 13], fill=(246, 246, 242), outline=INK, width=4)
    P.grass(img, w, (-80, 1860, W + 80, 2000), 60, 70, 140, cols=(SV.FIELD[1], SV.FIELD[2], SV.FIELD[3], lerp(SV.FIELD[3], INK, .3)),
            seed=163, w0=9, ink=INK)
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1300, vig=(.22, (30, 40, 30)))
    if not HIDE_UI:
        chip(img, 'JAPAN', (200, 50, 60), 540, 250, u, cue(2) - .1, size=64)
        chip(img, 'PAINTED STRIPES', (40, 40, 48), 540, 400, u, cue(4) - .1, size=52)
    return img, {'faces': [face_box(G['f'], 1.3)], 'avoid': [(0, 160, W, 470), (0, 1240, 820, 1760)]}


def s14b(u, D, cue):
    """Far fewer bites: the plain black cow (swarmed) up top, the striped cow (two flies) below."""
    w = u + 125
    img = Image.new('RGBA', (W, H))
    japan_farm(img, w, 0, horizon=760, house=(900, .42))
    for i, (painted, gy, n) in enumerate(((False, 1180, 12), (True, 1780, 2))):
        x = 560 if i == 0 else 520
        A.contact(img, x + 20, gy + 6, 600, .38, (40, 70, 30))
        A.put(img, 'cow', x, gy, 300, face=1 if i else -1, painted=painted,
              pose={'tail': q(14 * math.sin(w * 2 + i), 7), 'ear': q(max(0, math.sin(w * 2.4 + i)) ** 6, .5), 'neck': q(3 * math.sin(w + i), 1.5)})
        cy = gy - 300 * .72
        swarm(img, w, x, cy, 330, 170, n, 74, seed=7 + i, speed=1.2, trail=.3, r=6)
    if not HIDE_UI:
        put_chip(img, 'PLAIN: MANY BITES', (220, 60, 50), 540, 560, pop(u, .0, .25), size=48)
        put_chip(img, 'STRIPED: FAR FEWER', (60, 150, 90), 540, 1300, pop(u, cue(8) - .1, .25), size=48)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1200, vig=(.24, (30, 40, 30)))
    return img, {'faces': [], 'avoid': [(150, 500, 930, 620), (150, 1240, 930, 1360)]}


# ---------------------------------------------------------------- s15: striped stairs
ST_TOP, ST_EDGE = 470, 760                     # the landing: back edge, front edge (frame y)


def _st_x(y):
    """Half-width of the staircase at frame y (one-point perspective: wider toward the camera)."""
    return 300 + (y - ST_TOP) * .27


def _stairs_set():
    """The static stairwell (cached): back wall with a window, side walls with handrails and a lamp, the landing and
    the steps coming down toward us. Returns (layer, step list [(y_riser_top, y_tread_top, y_next)])."""
    def build():
        img = layer(); d = ImageDraw.Draw(img)
        # back wall + side walls (warm plaster)
        img.paste(vgrad([(0, (226, 208, 184)), (1, (204, 184, 160))], W, ST_TOP + 10), (0, 0))
        for side in (-1, 1):
            pts = [(540 + side * _st_x(ST_TOP), 0), (540 + side * _st_x(ST_TOP), ST_TOP), (540 + side * _st_x(H), H),
                   (540 + side * 900, H), (540 + side * 900, 0)]
            d.polygon(pts, fill=(196, 174, 150) if side < 0 else (212, 190, 164))
        rng = np.random.default_rng(15)
        for i in range(900):                                          # plaster texture
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            c = (180, 158, 136) if i % 2 else (232, 214, 192)
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=c)
        for side in (-1, 1):                                         # wall/stair corner lines
            d.line([(540 + side * _st_x(ST_TOP), 0), (540 + side * _st_x(ST_TOP), ST_TOP), (540 + side * _st_x(H), H)], fill=(130, 110, 96), width=6)
        # skirting along the walls
        for side in (-1, 1):
            d.line([(540 + side * (_st_x(ST_TOP) + 4), ST_TOP - 30), (540 + side * (_st_x(ST_TOP) + 4), ST_TOP)], fill=(150, 120, 96), width=8)
        # the window on the back wall
        wx0, wy0, wx1, wy1 = 600, 110, 800, 380
        d.rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14], fill=(150, 116, 90), outline=INK, width=6)
        img.paste(vgrad([(0, (150, 200, 240)), (1, (226, 240, 246))], wx1 - wx0, wy1 - wy0), (wx0, wy0))
        d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(150, 116, 90), width=10)
        d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(150, 116, 90), width=10)
        d.rectangle([wx0 - 24, wy1 + 10, wx1 + 24, wy1 + 28], fill=(236, 222, 200), outline=INK, width=4)
        # landing (wooden floor boards)
        L0 = [(540 - _st_x(ST_TOP), ST_TOP), (540 + _st_x(ST_TOP), ST_TOP), (540 + _st_x(ST_EDGE), ST_EDGE), (540 - _st_x(ST_EDGE), ST_EDGE)]
        d.polygon(L0, fill=(196, 158, 118))
        for k in range(1, 9):
            f = k / 9
            d.line([(540 + (-_st_x(ST_TOP) + 2 * _st_x(ST_TOP) * f), ST_TOP), (540 + (-_st_x(ST_EDGE) + 2 * _st_x(ST_EDGE) * f), ST_EDGE)], fill=(170, 132, 96), width=3)
        # steps: riser (faces us, shaded) then tread (lit), spacing grows toward the camera
        steps = []; y = ST_EDGE; dk = 118
        while y < H + 40:
            yr, yt, yn = y, y + dk * .40, y + dk
            steps.append((yr, yt, yn)); y = yn; dk *= 1.11
        for yr, yt, yn in steps:
            xa, xb = _st_x(yr), _st_x(yt); xc = _st_x(yn)
            d.polygon([(540 - xa, yr), (540 + xa, yr), (540 + xb, yt), (540 - xb, yt)], fill=(150, 140, 132))      # riser
            d.polygon([(540 - xb, yt), (540 + xb, yt), (540 + xc, yn), (540 - xc, yn)], fill=(222, 214, 202))      # tread
            d.line([(540 - xa, yr), (540 + xa, yr)], fill=(252, 248, 240), width=6)                               # nosing highlight
            d.line([(540 - xa, yr + 5), (540 + xa, yr + 5)], fill=(70, 62, 58), width=4)                         # crisp edge
            sh = mask(); ImageDraw.Draw(sh).polygon([(540 - xb, yt), (540 + xb, yt), (540 + xb, yt + 26), (540 - xb, yt + 26)], fill=255)
            fill_mask(img, sh, (90, 80, 76), .45, blur=8)                                                         # shadow under the nosing
        for i in range(500):                                         # stone speckle on the steps
            x, y_ = rng.uniform(0, W), rng.uniform(ST_EDGE, H)
            if abs(x - 540) < _st_x(y_): d.point((x, y_), fill=(176, 168, 160))
        # handrails along both walls, with brackets
        for side in (-1, 1):
            p0 = (540 + side * (_st_x(ST_TOP) - 10), ST_TOP - 140); p1 = (540 + side * (_st_x(H) + 150), H - 300)
            for k in range(1, 5):
                f = k / 5; bx, by = p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f
                d.line([(bx, by), (bx + side * 26, by - 8)], fill=(70, 60, 56), width=8)
            d.line([p0, p1], fill=INK, width=26); d.line([p0, p1], fill=(150, 98, 62), width=16)
            d.line([(p0[0] - side * 2, p0[1] - 5), (p1[0] - side * 2, p1[1] - 5)], fill=(200, 146, 100), width=4)
        # a brass wall lamp on the left wall
        lx, ly = 130, 560
        d.rectangle([lx - 14, ly - 4, lx + 14, ly + 60], fill=(120, 90, 50), outline=INK, width=4)
        d.polygon([(lx - 44, ly - 70), (lx + 44, ly - 70), (lx + 30, ly), (lx - 30, ly)], fill=(255, 232, 170), outline=INK)
        return img, steps
    return P.cached('stairs_set', build)


def s15(u, D, cue):
    """Looking down a wide staircase from above. The LEFT half stays plain (every step edge crisp, with a shadow);
    the RIGHT half gets painted with bold diagonal stripes (on "painted ... stripes") that hide the edges. A person on
    the top landing at the edge of the painted half hovers a foot over the first step, leaning back, worried."""
    w = u + 130
    img = Image.new('RGBA', (W, H))
    lay, steps = _stairs_set()
    img.alpha_composite(lay)
    # window light falling onto the landing and the first steps; the lamp glow
    lm = mask(); ImageDraw.Draw(lm).polygon([(600, ST_TOP + 10), (800, ST_TOP + 10), (760, ST_EDGE + 230), (480, ST_EDGE + 230)], fill=255)
    fill_mask(img, lm, (255, 244, 214), .22 + .03 * math.sin(u * 1.3), blur=26)
    kit.light_rays(img, 700, 250, (255, 240, 210), n=6, alpha=.14, spread=(80, 140), length=1400, seed=3, phase=math.sin(u * .4))
    radial(img, 130, 520, 260, (255, 214, 140), .45 + .04 * math.sin(u * 5))
    # the paint: the right half of the steps, wiped in top -> bottom
    kp = smooth(seg(u, cue(1) - .1, cue(4)))
    if kp > 0:
        sa = mask(); ImageDraw.Draw(sa).polygon([(540, ST_EDGE), (540 + _st_x(ST_EDGE), ST_EDGE), (540 + _st_x(H), H), (540, H)], fill=255)
        wipe = mask(); ImageDraw.Draw(wipe).rectangle([0, 0, W, ST_EDGE + (H - ST_EDGE) * kp], fill=255)
        mm = ImageChops.multiply(sa, wipe)
        fill_mask(img, mm, (242, 240, 232), .94)
        sl = mask(); dd = ImageDraw.Draw(sl)
        for k in range(-20, 30):
            y0_ = ST_EDGE - 200 + k * 120
            dd.polygon([(500, y0_), (1100, y0_ - 330), (1100, y0_ - 270), (500, y0_ + 60)], fill=255)
        fill_mask(img, ImageChops.multiply(sl, mm), (26, 24, 30), .95)
        dd2 = ImageDraw.Draw(img)
        for yr, yt, yn in steps:                                       # the edges barely survive under the paint
            if yr < ST_EDGE + (H - ST_EDGE) * kp:
                dd2.line([(546, yr + 3), (540 + _st_x(yr) - 4, yr + 3)], fill=(150, 146, 140), width=2)
        d = ImageDraw.Draw(img); d.line([(540, ST_EDGE), (540, H)], fill=(120, 112, 104), width=4)
    # the person on the top landing, at the edge of the painted half
    G = {}
    kf = smooth(seg(u, cue(5) - .3, cue(7)))
    hov = .5 + .5 * math.sin(u * 3.4)
    pose = dict(POSES['stand'], legL=(8, 2), legR=(-12 - 48 * kf - 6 * hov * kf, -2 + 10 * kf + 6 * hov * kf),
                armL=(70 + 10 * kf, 40), armR=(-70 - 10 * kf, -40))
    fx, gy = 640, ST_EDGE - 14
    A.contact(img, fx + 30, gy + 4, 150, .35, (90, 70, 50))
    fsh = mask(); ImageDraw.Draw(fsh).ellipse([fx + 50, ST_EDGE + 60, fx + 150, ST_EDGE + 84], fill=255)     # the hovering foot's shadow below
    fill_mask(img, fsh, (40, 40, 50), .25 * kf, blur=8)
    G['p'] = actor(img, 'worried' if u > cue(5) else 'neutral', pose, fx, gy, .5, w, look=-.3 * kf, lean=4 * kf,
                   aura=(255, 240, 210), aura_alpha=.25, rim=(255, 240, 210), shirt='#d0743c', pants='#3e4660')
    dust(img, 15, 30, (100, 100, 980, 1500), (255, 250, 230), 120, size=(2, 5), t=u)
    img = finish(img, w, 1.0 + .04 * smooth(u / D), 540, 900, vig=(.3, (40, 28, 24)))
    if not HIDE_UI:
        put_chip(img, 'PLAIN', (110, 104, 98), 300, 1220, pop(u, .1, .3), size=50)
        put_chip(img, 'PAINTED', (40, 40, 48), 790, 1220, pop(u, cue(2) - .1, .3), size=50)
        chip(img, "WHERE'S THE STEP?", (220, 70, 50), 760, 1000, u, cue(7), size=46)
        hx, hy = G['p']['head']
        qmark(img, hx + 150, hy - 60, .8, u, cue(8))
    return img, {'faces': [face_box(G['p'], 1.3)], 'avoid': [(500, 930, 1020, 1070), (150, 1150, 950, 1290)]}


# ---------------------------------------------------------------- s16: the flip
def s16(u, D, cue):
    w = u + 140
    cam = 16 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    SV.savanna(img, w, cam, horizon=1180, sun=(300, 1060), sun_r=150)
    SV.savanna_grass(img, w, (-60, 1200, W + 60, H), 300, 16, 50, seed=171, clump=(2, 5))
    zx, zgy, zs = 560 + cam * .8, 1720, 560
    A.contact(img, zx, zgy + 6, zs * 1.6, .35, (90, 60, 30))
    zi = A.put(img, 'zebra', zx, zgy, zs, face=1, pose=zebra_pose(w, .2), sun_k=1.5, light=(-1, -.3))
    # flies bonk and veer off around the zebra
    for i, tb in enumerate((cue(2), cue(5) - .2, cue(8), cue(10))):
        tz = tb - .6
        if not (tz <= u < tb + 1.0): continue
        side = 1 if i % 2 else -1
        tx, ty = zx + side * 120 + 40 * i, zgy - zs * (.7 + .1 * (i % 2))
        def pos(t, tz=tz, tb=tb, side=side, tx=tx, ty=ty):
            if t < tb:
                e = (t - tz) / (tb - tz)
                return (tx + side * 700 * (1 - e), ty - 200 * (1 - e))
            k = t - tb
            return (tx + side * 360 * k, ty - 520 * k + 420 * k * k)
        if u < tb: fly_at(img, pos, u, 70, trail=.5, dt=.08, r=6, t_min=tz)
        else: A.put_fly(img, *pos(u), 70 * side, ang=-(u - tb) * 600, wing='blur', ph=u * 7)
        bonk_star(img, tx, ty, (u - tb) / .4, .6)
    SV.savanna_grass(img, w, (-80, 1820, W + 80, 2000), 60, 70, 140, seed=172, w0=8, ink=INK)
    img = finish(img, w, 1.03 + .03 * smooth(u / D), 540, 1200, vig=(.3, (60, 30, 30)))
    if not HIDE_UI:
        stitle(img, 's16_a', [('NOT HIDING', 'white', 118), ('THE ZEBRA.', 'white', 118)], 160, u, cue(3) - .15, stagger=cue(5) - cue(3))
        stitle(img, 's16_b', [('HIDING THE', KEY, 128), ('LANDING SPOT.', KEY, 128)], 470, u, cue(7) - .15, stagger=cue(9) - cue(7))
    sx, sy = shake(u, cue(9), 8, .3)
    return img, {'faces': [], 'avoid': [(0, 120, W, 780)]}


# ---------------------------------------------------------------- s17: the loop back to 2016
def s17(u, D, cue):
    w = u - D                                               # the s01 world clock meets s01's frame 0 at the end
    if u > D - 1.5 / 30:                                   # the loop frame: exactly s01's frame 0 (same idle clock too)
        now = anim.NOW; anim.NOW = 0.0
        try: return s01_frame(0.0, 0.0)
        finally: anim.NOW = now
    kz = smooth(seg(u, .3, D - .5))
    z = 1.55 - .55 * kz
    cam = 8 * math.sin(w * .45)
    G = {}
    def chars(img):
        SV.tripod_camera(img, 860 + cam * 1.1, 1965, .78, t=w)
        G['b'] = sci(img, w, 'B', 'hold', 'thinking', 250 + cam * 1.1, 1990, .5, look=.35, board=True, counts=(1, 3), bphase=.4)
        G['a'] = sci(img, w, 'A', dict(POSES['stand'], armR=(-60, -100)), 'neutral', 960 + cam * 1.1, 2010, .5, look=-.6)
    fa = smooth(seg(u, D - .7, D - 2 / 30))
    def extra(img):
        # flies overshoot the coat: they dive at it, fail to brake, bounce off or fly straight past
        for i, tb in enumerate((cue(2), cue(4), cue(7), cue(9))):
            if not (tb - .7 <= u < tb + 1.6): continue
            sd = 1 if i % 2 else -1
            tx, ty = HX + cam * .85 + 40 * sd + 60 * i - 90, HGY - HS * (.72 + .08 * (i % 2))
            def pos(t, tb=tb, tx=tx, ty=ty, sd=sd):
                if t < tb:
                    e = (t - tb + .7) / .7
                    return (tx - sd * 620 * (1 - e), ty - 200 * (1 - e))
                k = t - tb
                return (tx + sd * 520 * k, ty - 430 * k + 360 * k * k)
            if u < tb: fly_at(img, pos, u, 92, trail=.6, dt=.08, r=8, t_min=tb - .7)
            else:
                pts = [pos(t) for t in np.arange(tb - .5 + min(.5, (u - tb) * .8), tb, .08)]
                if pts: SV.dots_trail(img, pts, r=7)
                A.put_fly(img, *pos(u), 92 * sd, ang=-(u - tb) * 500, wing='blur', ph=u * 7, alpha=max(0.0, 1 - fa) * (1 - smooth(seg(u, tb + 1.1, tb + 1.6))))
            bonk_star(img, tx, ty, (u - tb) / .4, .6)
    img, hi = field_world(w, cam, chars=chars, fly_a=fa, extra=extra)
    img = finish(img, w, z, 540 + (HX - 540) * (1 - kz), HGY - 20, vig=(.24, (30, 40, 30)))
    if not HIDE_UI:
        k = smooth(seg(u, D - .9, D - .2))
        if k > 0: opening_title(img, 0.0, k)
        if u < D - 1.0: chip(img, 'THE FLIES KEPT MISSING', (40, 40, 48), 540, 300, u, cue(8) - .3, size=50)
    faces = [face_box(G['a'], 1.3), face_box(G['b'], 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 140, W, 560)]}


SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [('s01', 1, 0), ('s01b', 1, 10), ('s02', 2, 0), ('s03', 3, 0), ('s04', 4, 0), ('s04b', 4, 8), ('s05', 5, 0),
             ('s05b', 5, 5), ('s06', 6, 0), ('s07', 7, 0), ('s07b', 7, 7), ('s08', 8, 0), ('s09', 9, 0), ('s10', 10, 0),
             ('s11', 11, 0), ('s12', 12, 0), ('s13', 13, 0), ('s14', 14, 0), ('s14b', 14, 7), ('s15', 15, 0), ('s16', 16, 0),
             ('s17', 17, 0)]
END = 1951 / 30                 # 65.033 s (length.json)
NO_PUNCH = ()
BAND_AT = {}
BAND_FIX = {'s01': 1500, 's01b': 1405, 's17': 1500}        # caption on the grass under the horse, above the scientists
STILL_AT = {'s01': .02, 's01b': .8, 's02': .95, 's03': .95, 's04': .9, 's04b': .95, 's05': .9, 's05b': .97, 's06': .9,
            's07': .9, 's07b': .97, 's08': .95, 's09': .8, 's10': .97, 's11': .95, 's12': .62, 's13': .9, 's14': .55, 's14b': .9,
            's15': .9, 's16': .95, 's17': .5}

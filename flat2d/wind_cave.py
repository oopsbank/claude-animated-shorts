"""Wind Cave (video 7, "This Cave Has Been Breathing Since 1881"): shots as `sNN(u, D, cue) -> (img, info)`.

Same contract as boiling_river.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the
shot's voice-over LINE. info: 'faces' (face boxes) and 'avoid' (boxes the caption must not cover).
Hero image: the small dark hole in a rock outcrop on the golden Black Hills prairie, BREATHING (pale blue-white wind
ribbons + flying grass/dust, OUT or IN). Colour motif: cool breath on warm gold; storms in slate purple; the cave in
deep teal with an amber helmet lamp. Serious mystery, no comedy. Every shot keeps moving.

Render: .venv/bin/python flat2d/render.py audio/wind-cave/words.json OUT.mp4 --film wind_cave --size 540x960
"""
import math, os, sys, re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit, anim
import prairie as P
from kit import W, H, INK, vgrad, radial, haze, dust, label, title, font, mask, glow, fill_mask, layer, lerp, rgb
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES, mix, add, damp
from blood_falls import finish, slam_title, face_box
from blood_falls_2 import put_chip, draw_x, stars, path_point, partial
import tunguska as TG
from tunguska import chip_t, flash, thought

SLUG = 'wind-cave'
HIDE_UI = False                          # thumbnail frames: no chips, titles or labels
KEY = (130, 206, 255)                    # BREATHING / breath key colour for titles
TOM_COL = (196, 92, 52)                  # TOM label
JESSE_COL = (70, 120, 190)               # JESSE label
BRO_COL = (176, 112, 52)                 # TOM & JESSE BINGHAM · 1881
CAVER_COL = (220, 120, 30)
TOM_KW = dict(hat='cowboy', hat_col=P.TOM_HAT, shirt='#b4553c', pants='#3e4660')
JESSE_KW = dict(hat='cowboy', hat_col=P.JESSE_HAT, shirt='#4f7aa6', pants='#5e4a3a')
CAVER_KW = dict(hat='hardhat', shirt='#d8742c', pants='#b85e24')


def clue(img, txt, u, t0=.05, y=250):
    if HIDE_UI: return
    TG.clue(img, txt, u, t0, y)


def chip(img, txt, fill, x, y, u, t0, size=50, angle=0.0):
    if HIDE_UI: return
    chip_t(img, txt, fill, x, y, u, t0, size=size, angle=angle)


def stitle(img, key, lines, y, u, t0, size=104, stagger=.16):
    if HIDE_UI: return
    slam_title(img, key, lines, y, u, t0, size=size, stagger=stagger)


def brother(img, t, who, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, hat=True, label_on=False, rim=(255, 226, 170),
            rim_dir=(1, -.5), bphase=0.0, aura=(255, 210, 140), aura_a=.4, lbl_dy=0, lbl_txt=None):
    """TOM (brown hat, rust shirt) or JESSE (grey hat, denim shirt) BINGHAM: white stickmen with black outline."""
    kw = dict(TOM_KW if who == 'tom' else JESSE_KW)
    if not hat: kw.pop('hat'); kw.pop('hat_col')
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=aura, aura_alpha=aura_a, rim=rim,
              rim_dir=rim_dir, rim_w=12, bphase=bphase + (0 if who == 'tom' else .9), **kw)
    if label_on and not HIDE_UI:
        hx, hy = g['head']
        txt = lbl_txt or ('TOM' if who == 'tom' else 'JESSE')
        label(img, txt, min(W - 150, max(150, hx)), hy - g['R'] * 1.75 - 80 + lbl_dy, TOM_COL if who == 'tom' else JESSE_COL,
              size=int(44 * max(.9, min(1.1, s / .6))))
    return g


def caver(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, beam=None, label_on=True, lbl_dy=0):
    """CAVER: orange coveralls, hard hat with a helmet lamp (the beam is drawn by the shot behind/after)."""
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, aura=(255, 190, 110), aura_alpha=.35, rim=(255, 210, 150),
              rim_dir=(1 if look >= 0 else -1, -.4), bphase=.3, **CAVER_KW)
    hx, hy = g['head']; R = g['R']
    lx, ly = hx + look * R * .3, hy - R * .78
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([lx - R * .22, ly - R * .16, lx + R * .22, ly + R * .16], R * .08, fill=(70, 70, 80), outline=INK, width=4)
    d.ellipse([lx - R * .13, ly - R * .12, lx + R * .13, ly + R * .12], fill=(255, 246, 200), outline=INK, width=3)
    g['lamp'] = (lx, ly)
    if label_on and not HIDE_UI:
        label(img, 'CAVER', min(W - 150, max(150, hx)), hy - R * 1.9 - 80 + lbl_dy, CAVER_COL, size=int(44 * max(.9, min(1.1, s / .6))))
    return g


def sound_arcs(img, x, y, u, t0, ang=-math.pi / 2, n=3, col=(236, 246, 255), k=1.0):
    """'))) ' whistle arcs rising from the ground. Moves: arcs expand and fade on a loop after t0."""
    if u < t0: return
    d = ImageDraw.Draw(img)
    for i in range(n):
        q = ((u - t0) * .9 + i / n) % 1.0
        r = 40 + 170 * q; a = int(255 * (1 - q) * k * min(1, (u - t0) / .2))
        lay = layer(); dl = ImageDraw.Draw(lay)
        a0 = math.degrees(ang) - 32; a1 = math.degrees(ang) + 32
        dl.arc([x - r, y - r, x + r, y + r], a0, a1, fill=INK + (a,), width=16)
        dl.arc([x - r, y - r, x + r, y + r], a0, a1, fill=col + (a,), width=9)
        img.alpha_composite(lay)


# ---------------------------------------------------------------- the prairie world (s01, s03, s06, s16)
HOLE = (540, 1150)                       # the hole in the s01 framing
SRC_OUT = lambda k: (HOLE[0], HOLE[1], 1.1 * k, 1, -math.pi / 2 - .25)


def prairie_back(img, u, cam, kind='fair', kind2=None, mixk=0.0, horizon=1000, storm_far=0.0, sunp=(900, 800), warm=1.0,
                 clouds=True, ridge_cols=None):
    """Sky, sun, clouds, the Black Hills pine ridges and the far rolling hills (parallax: far slow, near fast)."""
    P.sky(img, kind, H, mixk, kind2)
    if sunp and kind != 'storm':
        P.sun(img, sunp[0] + cam * .05, sunp[1], 46, u, a=warm * (1 - mixk))
    if clouds:
        P.cumulus(img, u, [(150, 520, .9, 11, 6), (760, 380, 1.15, 12, 5), (1080, 610, .75, 13, 7), (420, 700, .6, 14, 8)],
                  lit=(255, 248, 234), shade=(204, 196, 214), mid=(240, 230, 230), alpha=1 - .8 * mixk)
    if storm_far > 0:                                  # a storm building on the far horizon (left): it is why the hole blows out
        P.thunderhead(img, u, 170 + cam * .08, horizon - 40, .95, seed=5, alpha=storm_far, rain_a=.45)
        if storm_far > .5:
            P.lightning(img, u % 3.3, 2.1, 200 + cam * .08, horizon - 200, horizon - 20, seed=3, dur=.25, cloud=(190, 170, 240))
    rc = ridge_cols or ((150, 150, 188), (96, 116, 132), (58, 82, 78))
    far = P.pine_ridge(31, horizon - 10, 130, rc[0], tree=(18, 34), dens=1.2, haze_col=(236, 210, 190), haze_a=.35)
    P.paste_band(img, far, cam, .15)
    haze(img, horizon - 200, horizon + 40, (255, 226, 190), .32 * warm)
    mid = P.pine_ridge(32, horizon + 50, 120, rc[1], tree=(26, 52), dens=1.1, lit=lerp(rc[1], (220, 180, 120), .35),
                       haze_col=(230, 200, 170), haze_a=.25)
    P.paste_band(img, mid, cam, .3)
    near = P.pine_ridge(33, horizon + 110, 90, rc[2], tree=(34, 70), dens=.9, lit=lerp(rc[2], (200, 160, 90), .4))
    P.paste_band(img, near, cam, .45)
    haze(img, horizon + 20, horizon + 180, (255, 220, 170), .28 * warm)
    if sunp and kind != 'storm' and mixk < .7:
        kit.light_rays(img, sunp[0] + cam * .05, sunp[1], (255, 236, 190), n=11, alpha=.22 * warm * (1 - mixk), spread=(95, 250),
                       length=2200, seed=4, phase=2 * math.sin(u * .3), blur=22)


def prairie_world(u, cam=0.0, k_breath=1.2, sign=1, kind='fair', storm_far=.0, hole=HOLE, rock_s=1.25, near_y=1210,
                  gold=P.GOLD, kind2=None, mixk=0.0, breath_ang=-math.pi / 2 - .25, wind=.25, chars=None, fg=True,
                  breath_scale=1.0, spread=1.4, hill_cols=None, front=None):
    """The opening framing: golden hills, the outcrop with the breathing hole, grass bending in its breath.
    chars(img) draws characters between the outcrop/field and the foreground grass."""
    img = Image.new('RGBA', (W, H))
    prairie_back(img, u, cam, kind=kind, kind2=kind2, mixk=mixk, storm_far=storm_far)
    hc = hill_cols or (lerp(gold[0], (230, 200, 190), .25), lerp(gold[1], (200, 170, 170), .25), lerp(gold[2], (170, 140, 150), .25), gold[3])
    P.paste_band(img, P.hill(41, 1120, 40, hc, ink=None, streaks=False), cam, .55)
    P.paste_band(img, P.hill(42, near_y, 55, gold, ink=INK, ink_w=5, waves=(.8, 2.1)), cam, .8)
    haze(img, near_y - 80, near_y + 160, (255, 236, 200) if kind != 'storm' else (170, 160, 200), .3)
    src = (hole[0], hole[1], 1.1 * k_breath, sign, breath_ang)
    ny = lambda x: P.edge_y(42, near_y, 55, x - cam * .8, waves=(.8, 2.1))
    P.grass(img, u, (-60, near_y - 70, W + 60, near_y + 40), 260, 22, 46, cols=gold, seed=3, src=src, wind=wind, ytop=lambda x: ny(x) + 4,
            clump=(3, 6))
    P.grass(img, u, (-60, near_y + 40, W + 60, 1500), 150, 30, 56, cols=gold, seed=13, src=src, wind=wind, clump=(3, 7))
    hx, hy = hole[0] + cam * .85, hole[1]
    P.outcrop(img, hx, hy, rock_s, seed=3, breath_glow=min(1, k_breath), t=u)
    P.grass(img, u, (hx - 400 * rock_s, hy + 100 * rock_s, hx + 400 * rock_s, hy + 150 * rock_s), 40, 34, 70, cols=gold, seed=8,
            src=src, wind=wind, clump=(4, 8), ink=INK)
    P.breath(img, u, hx, hy - 6, ang=breath_ang, sign=sign, k=k_breath, scale=breath_scale, n=12, spread=spread, seed=7,
             Lr=(700, 1050), Ar=(40, 90), width=20, particles=50)
    P.grass(img, u, (-60, 1480, W + 60, 1780), 150, 50, 96, cols=gold, seed=4, src=src, wind=wind, clump=(4, 8))
    if chars: chars(img, src)
    if fg:
        P.grass(img, u, (-80, 1850, W + 80, 1990), 60, 90, 170, cols=(lerp(gold[1], INK, .1), gold[2], gold[3], lerp(gold[3], INK, .3)),
                seed=5, src=src, wind=wind, w0=9, clump=(5, 9), ink=INK)
        P.seed_heads(img, u, (-40, 1760, W + 40, 1900), 14, seed=6, src=src)
    if fg: fg_frame(img, u, col=lerp(gold[3], INK, .5))
    if front: front(img)
    dust(img, 3, 26, (0, 700, W, 1500), (255, 246, 220), 110, size=(2, 5), t=u)
    return img


def fg_frame(img, u, col=(54, 34, 26), seed=3, h=(200, 380), alpha=.93, sides=(0, 1)):
    """Out-of-focus foreground grass silhouettes in the bottom corners (depth). Moves: they sway."""
    m = mask(); d = ImageDraw.Draw(m); rng = np.random.default_rng(seed)
    for side in sides:
        for i in range(16):
            x = (rng.uniform(-80, 240) if side == 0 else rng.uniform(840, 1160))
            L = rng.uniform(*h); a = rng.uniform(-.35, .35) + .08 * math.sin(u * 1.7 + i) + (.15 if side == 0 else -.15)
            tx, ty = x + math.sin(a) * L, H + 20 - math.cos(a) * L
            wb = rng.uniform(14, 26)
            d.polygon([(x - wb, H + 20), ((x + tx) / 2 - wb * .5, (H + ty) / 2), (tx, ty), ((x + tx) / 2 + wb * .5, (H + ty) / 2), (x + wb, H + 20)], fill=255)
    fill_mask(img, m, col, alpha, blur=5)


def opening_title(img, u, t_pop=0.0, alpha=1.0, scale=1.0):
    if HIDE_UI: return
    k = scale * (1.0 + .006 * math.sin(u * 2.4))
    lay, _ = tlayer('open', [('1881', (255, 214, 120), 230)], 230)
    anim.scaled_paste(img, lay, 540, 330, k, alpha=alpha)


_tl = {}
def tlayer(key, lines, size):
    if key not in _tl:
        _tl[key] = anim.text_layer(lambda l: title(l, lines, 60, size=size), W,
                                   int(sum((x[2] if len(x) > 2 else size) for x in lines) * 1.3 + 140))
    return _tl[key]


def s01_frame(u, w, D=5.3, cue=None, loop=False):
    """s01 at shot time u (w = the world clock). The brothers have just stopped (left Tom, right Jesse), facing the
    breathing hole between them; Jesse points on 'whistle'."""
    cue = cue or (lambda i: [0, .32, .82, 1.1, 1.65, 1.87, 2.26, 2.7, 3.09, 3.26, 3.75, 4.2, 4.53, 4.81][min(i, 13)])
    cam = 8 * math.sin(w * .45)
    G = {}
    t_pt = cue(9) - .25
    def chars(img, src):
        # Tom (left, front): stopped mid-step, leaning back, hand going to his hat brim in the wind
        kst = smooth(seg(u, 0, .7))
        kh = 1.0 if loop else .75 + .25 * smooth(seg(u, 0, .5))
        pT = mix(POSES['stand'], dict(POSES['stand'], armR=(-110, -160), armL=(30, 60)), kh)
        pT = add(pT, armR=(3 * math.sin(w * 3.1), 4 * math.sin(w * 3.1)))
        G['tom'] = brother(img, w, 'tom', pT, 'surprised', 240 + cam * 1.05, 1820, .76, look=.55, lean=-3 - 2 * (1 - kst) + 1.2 * math.sin(w * 2.3),
                           bphase=.6)
        # Jesse (right): stops, then points at the hole on 'whistle'
        kp = out_back(seg(u, t_pt, t_pt + .45), 1.4)
        pJ = mix(POSES['stand'], dict(POSES['stand'], armL=(70, 76)), kp)
        G['jesse'] = brother(img, w, 'jesse', pJ, 'worried' if u < t_pt else 'surprised', 850 + cam * 1.05, 1770, .68,
                             look=-.6, lean=2 + 1.2 * math.sin(w * 2.1 + 1), rim_dir=(1, -.6))
    img = prairie_world(w, cam, k_breath=1.15, chars=chars, storm_far=.75)
    sound_arcs(img, HOLE[0] + cam * .85, HOLE[1] - 40, u, cue(9) - .1, k=.9)
    zoom = 1.0 + .05 * smooth(u / D)
    img = finish(img, w, zoom, 540, 1250, vig=(.28, (40, 24, 30)))
    if not HIDE_UI:
        opening_title(img, u)
        tom, jes = G['tom'], G['jesse']
        y = min(tom['head'][1], jes['head'][1]) - tom['R'] * 1.9 - 80
        # pill over both brothers' heads
        label(img, 'TOM & JESSE BINGHAM', 540, 520, BRO_COL, size=48)
    faces = [face_box(G['tom'], 1.3), face_box(G['jesse'], 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 150, W, 620), (HOLE[0] - 260, HOLE[1] - 200, HOLE[0] + 260, HOLE[1] + 160)]}


def s01(u, D, cue):
    return s01_frame(u, u, D, cue)


# ---------------------------------------------------------------- s02: THE HOLE IS BREATHING (close-up)
def pulse(u, period=1.6, lo=.55, hi=1.45, phase=0.0):
    """Breathing strength: slow exhale pulses (never fully calm)."""
    q = (u / period + phase) % 1.0
    return lo + (hi - lo) * (math.sin(math.pi * q) ** 2)


def closeup_rock(img, u, cam, hole, s, k, sign=1, ang=-math.pi / 2 + .25, gold=P.GOLD, kind='fair', mixk=0.0, kind2=None,
                 horizon=880, spread=1.2, Lr=(800, 1250), chars=None, gust_bits=60):
    prairie_back(img, u, cam * .3, kind=kind, kind2=kind2, mixk=mixk, horizon=horizon, sunp=(880, 640))
    P.paste_band(img, P.hill(52, horizon + 90, 40, gold, ink=INK, ink_w=5, waves=(.7, 1.9)), cam, .5)
    src = (hole[0], hole[1], 1.4 * k, sign, ang)
    P.grass(img, u, (-60, horizon + 40, W + 60, horizon + 200), 120, 30, 60, cols=gold, seed=21, src=src, clump=(3, 6),
            ytop=lambda x: P.edge_y(52, horizon + 90, 40, x - cam * .5, waves=(.7, 1.9)) + 4)
    P.outcrop(img, hole[0], hole[1], s, seed=3, breath_glow=min(1, k), t=u, src=src)
    P.grass(img, u, (-80, hole[1] + 110 * s, W + 80, hole[1] + 220 * s), 70, 60, 120, cols=gold, seed=22, src=src, clump=(4, 8), ink=INK)
    if chars: chars(img, src)
    P.breath(img, u, hole[0], hole[1], ang=ang, sign=sign, k=k, scale=s / 1.6, n=9, spread=spread, seed=9, Lr=Lr, Ar=(40, 90),
             width=22, particles=gust_bits)
    return src


def s02(u, D, cue):
    cam = -14 * smooth(u / D)
    hole = (600 + cam, 1230)
    k = pulse(u, 1.5, .7, 1.5, .1)
    G = {}
    def chars(img, src):
        kl = smooth(seg(u, cue(1), cue(4)))
        pose = mix(POSES['stand'], dict(POSES['stand'], armL=(18, 4), armR=(-62, -40)), kl)
        G['j'] = brother(img, u, 'jesse', pose, 'worried' if u < cue(10) else 'surprised', 175 + cam * 1.2, 1985, 1.02, look=.75,
                         lean=11 * kl + 1.5 * math.sin(u * 2), rim=(190, 230, 255), rim_dir=(1, -.3), aura=(160, 210, 255), aura_a=.3)
    img = Image.new('RGBA', (W, H))
    closeup_rock(img, u, cam, hole, 3.3, k, chars=chars)
    # a ring finds the hole on 'hole'
    kr = out_back(seg(u, cue(4) - .1, cue(4) + .25), 1.6) * (1 - smooth(seg(u, cue(8), cue(9))))
    if kr > 0 and not HIDE_UI:
        d = ImageDraw.Draw(img); r = 190 * kr
        for wdt, col in ((18, INK), (9, (255, 214, 90))):
            d.ellipse([hole[0] - r * 1.1, hole[1] - r * .8 + 20, hole[0] + r * 1.1, hole[1] + r * .8 + 20], outline=col, width=wdt)
    fg_frame(img, u, sides=(1,))
    img = finish(img, u, 1.1 + .04 * smooth(u / D), 600, 1500, vig=(.3, (30, 30, 50)))
    if not HIDE_UI:
        stitle(img, 's02_t', [('THE HOLE IS', 'white', 118), ('BREATHING', KEY, 168)], 190, u, cue(9) - .1, stagger=cue(12) - cue(9))
    return img, {'faces': [face_box(G['j'], 1.3)], 'avoid': [(0, 120, W, 560), (330, 820, 870, 940), (hole[0] - 300, hole[1] - 220, hole[0] + 300, hole[1] + 160)]}


# ---------------------------------------------------------------- s03: the gust takes Tom's hat (low angle, sky)
def hat_flight(u, t0, start, end, spin=720, s0=1.0, s1=.5, arc=-260):
    """(x, y, angle, scale) of a hat flying from start to end along an arc, from t0 (0.85 s)."""
    v = seg(u, t0, t0 + .95)
    e = 1 - (1 - v) ** 2.2
    x = start[0] + (end[0] - start[0]) * e
    y = start[1] + (end[1] - start[1]) * e + arc * math.sin(math.pi * e)
    return x, y, spin * e + 12 * math.sin(u * 9), s0 + (s1 - s0) * e


def s03(u, D, cue):
    cam = 16 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    horizon = 1330
    prairie_back(img, u, cam * .4, horizon=horizon, sunp=(300, 900), storm_far=.0, kind='fair', kind2='storm', mixk=.42)
    gold = P.GOLD
    hole = (380 + cam * .8, 1430)
    gust = smooth(seg(u, cue(0) - .2, cue(1) + .1)) * (1.0 + .3 * smooth(seg(u, cue(6), cue(9))))
    k = .6 + 1.25 * gust + .1 * math.sin(u * 7)
    ang = -math.pi / 2 + .28
    src = (hole[0], hole[1], 1.4 * k, 1, ang)
    P.paste_band(img, P.hill(61, horizon + 40, 30, gold, ink=INK, waves=(.6, 1.7)), cam, .6)
    P.grass(img, u, (-60, horizon, W + 60, horizon + 160), 150, 26, 52, cols=gold, seed=31, src=src, clump=(3, 6),
            ytop=lambda x: P.edge_y(61, horizon + 40, 30, x - cam * .6, waves=(.6, 1.7)) + 4)
    P.outcrop(img, hole[0], hole[1], 1.45, seed=3, breath_glow=min(1, k), t=u, src=src)
    t_hat = cue(9) - .3
    G = {}
    P.breath(img, u, hole[0], hole[1], ang=ang, sign=1, k=k, scale=1.3, n=10, spread=1.0, seed=11, Lr=(900, 1300), Ar=(40, 90),
             width=22, particles=60)
    kb = out_back(seg(u, cue(1), cue(1) + .35), 1.8)
    pose = mix(dict(POSES['stand'], armL=(30, 20), armR=(-40, -30)), dict(POSES['stand'], armL=(95, 150), armR=(-100, -150)), kb)
    hat_on = u < t_hat
    G['t'] = brother(img, u, 'tom', pose, 'surprised' if u < cue(1) else 'scared', 740 + cam, 1640, .64, look=-.6,
                     lean=-6 * kb + 4 * (1 - kb) + 1.5 * math.sin(u * 8) * kb, hat=hat_on, rim=(190, 230, 255), rim_dir=(-1, -.4),
                     aura=(150, 210, 255), aura_a=.3)
    if not hat_on:
        hx, hy = G['t']['head']; R = G['t']['R']
        x, y, a, sc = hat_flight(u, t_hat, (hx, hy - R * .85), (300, 420), spin=-540, s0=.85, s1=.75, arc=-160)
        P.put_hat(img, P.TOM_HAT, x, y, sc, angle=a)
        G['hat'] = (x, y)
    P.grass(img, u, (-80, 1880, W + 80, 1990), 40, 80, 150, cols=(lerp(gold[1], INK, .1), gold[2], gold[3], lerp(gold[3], INK, .3)),
            seed=35, src=src, w0=10, clump=(5, 9), ink=INK)
    sx, sy = shake(u, cue(1), 9, .4)
    rot = -7 - 1.5 * smooth(u / D); z = 1.28 + .03 * smooth(u / D)
    img = img.rotate(rot, resample=Image.BICUBIC, center=(540, 960))       # dutch angle: the gust tilts the world
    img = finish(img, u, z, 540, 960, dx=sx, dy=sy, vig=(.26, (30, 40, 70)))
    def xf(p):                                                    # scene px -> screen px (rotation, then zoom)
        a = math.radians(-rot); x, y = p[0] - 540, p[1] - 960
        x, y = 540 + x * math.cos(a) - y * math.sin(a), 960 + x * math.sin(a) + y * math.cos(a)
        return 540 + (x - 540) * z, 960 + (y - 960) * z
    G['t'] = dict(G['t'], head=xf(G['t']['head']), R=G['t']['R'] * z)
    hole = xf(hole)
    if not HIDE_UI:
        hx, hy = G['t']['head']
        label(img, 'TOM BINGHAM', min(W - 220, hx), hy - G['t']['R'] * 1.25 - 80, TOM_COL, size=46)
    faces = [face_box(G['t'], 1.3)]
    return img, {'faces': faces, 'avoid': [(hole[0] - 170, hole[1] - 110, hole[0] + 170, hole[1] + 80), (0, 700, W, 1000)]}


# ---------------------------------------------------------------- s04 / s05a: the imagined tunnel (hill cross-section)
def surf(x): return 760 + .00062 * (x - 600) ** 2 + 14 * math.sin(x / 90)


HOLE_S = (250, None)
EXIT_S = (900, None)


def section_scene(img, u, cam, tunnel_k=0.0, tunnel_a=1.0, exit_k=0.0, flow_k=0.0, crack=0.0):
    P.sky(img, 'morning')
    P.cumulus(img, u, [(260, 300, .8, 41, 6), (860, 420, .9, 42, 5)], lit=(255, 252, 244), shade=(200, 210, 230), mid=(236, 238, 246))
    far = P.pine_ridge(71, 760, 150, (130, 150, 186), tree=(18, 34), dens=1.2, haze_col=(230, 236, 240), haze_a=.4)
    P.paste_band(img, far, cam, .2)
    mid = P.pine_ridge(72, 800, 110, (78, 104, 116), tree=(26, 50), lit=(150, 160, 130))
    P.paste_band(img, mid, cam, .35)
    haze(img, 650, 900, (240, 240, 236), .35)
    # the hill section: grass cap, strata, roots
    P.earth_section(img, 0, H + 40, cols=((168, 124, 82), (146, 104, 72), (124, 88, 66), (104, 74, 60), (84, 60, 54), (64, 46, 48)),
                    seed=7, edge_fn=surf, ink=True)
    d = ImageDraw.Draw(img)
    xs = list(range(-20, W + 21, 12))
    top = [(x, surf(x)) for x in xs]
    d.polygon(top + [(x, surf(x) + 34) for x in xs[::-1]], fill=P.GOLD[1])
    d.line([(x, surf(x) + 34) for x in xs], fill=lerp(P.GOLD[3], INK, .3), width=5)
    d.line(top, fill=INK, width=7)
    rng = np.random.default_rng(3)
    for _ in range(40):                                              # grass roots
        x = rng.uniform(0, W); y = surf(x) + 34
        d.line([(x, y), (x + rng.uniform(-14, 14), y + rng.uniform(30, 70))], fill=(92, 64, 44), width=3)
    P.grass(img, u, (-20, 600, W + 20, 610), 160, 20, 40, cols=P.GOLD, seed=77, ytop=lambda x: surf(x) + 2, clump=(3, 6))
    kit.depth_fade(img, 900, H, (30, 18, 24), 0.0, .6)
    rngg = np.random.default_rng(12); dg = ImageDraw.Draw(img)
    for i in range(40):                                              # quartz glints in the rock
        gx, gy = rngg.uniform(0, W), rngg.uniform(surf(500) + 120, H - 60)
        q = .5 + .5 * math.sin(u * rngg.uniform(2, 4) + i); r = rngg.uniform(3, 7) * (.6 + .4 * q)
        dg.polygon([(gx, gy - 3 * r), (gx + r, gy), (gx, gy + 3 * r), (gx - r, gy)], fill=(255, 236, 200))
        dg.polygon([(gx - 3 * r, gy), (gx, gy - r), (gx + 3 * r, gy), (gx, gy + r)], fill=(255, 236, 200))
    kit.light_rays(img, 900, 120, (255, 240, 200), n=8, alpha=.18, spread=(100, 170), length=1400, seed=7, phase=2 * math.sin(u * .4))
    hx, hy = HOLE_S[0], surf(HOLE_S[0])
    ex, ey = EXIT_S[0], surf(EXIT_S[0])
    hy = hy + 22
    # the real passage: a short dark throat under the hole
    d.line([(hx, hy + 10), (hx + 20, hy + 120), (hx + 60, hy + 200)], fill=INK, width=60, joint='curve')
    d.line([(hx, hy + 10), (hx + 20, hy + 120), (hx + 60, hy + 200)], fill=(26, 20, 30), width=46, joint='curve')
    P.outcrop(img, hx, hy, .55, seed=3, breath_glow=.8, t=u, tufts=False)
    path = [(hx + 60, hy + 200), (330, 1150), (520, 1260), (720, 1180), (840, 1000), (ex, ey + 10)]
    if tunnel_k > 0:                                                 # the imagined tunnel: a glowing dashed tube
        pts = partial(_smooth_path(path, 8), tunnel_k)
        lay = layer(); dl = ImageDraw.Draw(lay)
        dl.line(pts, fill=(200, 230, 255, int(110 * tunnel_a)), width=96, joint='curve')
        dashed(dl, pts, (240, 250, 255, int(255 * tunnel_a)), 10, 34, 22, off=48, phase=u * 40)
        dashed(dl, pts, (240, 250, 255, int(255 * tunnel_a)), 10, 34, 22, off=-48, phase=u * 40)
        if crack > 0:
            lay.putalpha(ImageChops.multiply(lay.split()[3], crack_mask(crack)))
        glow(img, lay.split()[3], (150, 205, 255), .8 * tunnel_a, blur=26, add=True)
        img.alpha_composite(lay)
    if flow_k > 0 and tunnel_k > .9:                                 # air flowing through it: in at the far end, out of the hole
        sp = _smooth_path(path, 8)[::-1]
        for i in range(7):
            q = (i / 7 + u * .35) % 1.0
            x, y = path_point(sp, q)
            x2, y2 = path_point(sp, min(1, q + .03))
            a = math.atan2(y2 - y, x2 - x); al = math.sin(math.pi * q) * flow_k * tunnel_a
            chev(img, x, y, a, 26, (230, 246, 255), al)
    if exit_k > 0:                                                   # the imagined second opening
        k = exit_k
        m = mask(); ImageDraw.Draw(m).ellipse([ex - 46, ey - 26, ex + 46, ey + 30], fill=255)
        glow(img, m, (170, 215, 255), .6 * k * tunnel_a, blur=20, add=True)
        lay = layer(); dl = ImageDraw.Draw(lay)
        dashed(dl, ellipse_pts(ex, ey + 2, 46, 26), (240, 250, 255, int(255 * k * tunnel_a)), 8, 18, 12)
        img.alpha_composite(lay)
    return (hx, hy), (ex, ey)


def crack_mask(k):
    m = Image.new('L', (W, H), 255); d = ImageDraw.Draw(m); rng = np.random.default_rng(5)
    for i in range(70):
        x = rng.uniform(250, W); y = rng.uniform(850, 1350); r = 45 * k * rng.uniform(.5, 1.5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=0)
    return m.point(lambda q: int(q * (1 - k * .2)))


def ellipse_pts(cx, cy, rx, ry, n=40):
    return [(cx + math.cos(a) * rx, cy + math.sin(a) * ry) for a in np.linspace(0, 2 * math.pi, n)]


def dashed(d, pts, col, w, on, off_len, off=0.0, phase=0.0):
    """Dashed polyline (optionally offset sideways by `off` px), dashes marching by phase."""
    if off:
        q = []
        for i, (x, y) in enumerate(pts):
            a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) + 1e-6
            q.append((x - ty / L * off, y + tx / L * off))
        pts = q
    acc = -phase % (on + off_len); cur = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); s0 = 0.0
        while s0 < L:
            per = on + off_len; ph = acc % per
            if ph < on:
                step = min(on - ph, L - s0)
                p0 = (ax + (bx - ax) * s0 / L, ay + (by - ay) * s0 / L); s1 = s0 + step
                p1 = (ax + (bx - ax) * s1 / L, ay + (by - ay) * s1 / L)
                d.line([p0, p1], fill=col, width=w)
            else:
                step = min(per - ph, L - s0)
            s0 += step; acc += step


def chev(img, x, y, a, s, col, al):
    if al <= .02: return
    lay = layer(); d = ImageDraw.Draw(lay)
    p = [(x + math.cos(a + 2.5) * s, y + math.sin(a + 2.5) * s), (x + math.cos(a) * s * .6, y + math.sin(a) * s * .6),
         (x + math.cos(a - 2.5) * s, y + math.sin(a - 2.5) * s)]
    d.line(p, fill=INK + (int(255 * al),), width=16, joint='curve')
    d.line(p, fill=rgb(col) + (int(255 * al),), width=9, joint='curve')
    img.alpha_composite(lay)


def _smooth_path(pts, n=8):
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(len(pts) - 1, i + 2)]
        for q in np.linspace(0, 1, n, endpoint=False):
            q2, q3 = q * q, q * q * q
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * q + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * q2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * q3) for j in range(2)))
    out.append(pts[-1])
    return out


def bros_small(img, u, hole, s=.34, tom_hat=False, jesse_hat=True, exprT='thinking', exprJ='thinking', poseT='think', poseJ='stand',
               dx=(-150, -60), lookT=.5, lookJ=.4, labels=False):
    gT = brother(img, u, 'tom', poseT, exprT, hole[0] + dx[0], surf(hole[0] + dx[0]) + 6, s, look=lookT, hat=tom_hat, label_on=labels)
    gJ = brother(img, u, 'jesse', poseJ, exprJ, hole[0] + dx[1], surf(hole[0] + dx[1]) + 6, s * .96, look=lookJ, hat=jesse_hat, label_on=labels)
    return gT, gJ


def s04(u, D, cue):
    cam = -10 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    tk = smooth(seg(u, cue(3) - .2, cue(5) + .2))
    ek = out_back(seg(u, cue(6), cue(7) + .2), 1.5)
    hole, ex = section_scene(img, u, cam, tunnel_k=tk, exit_k=ek, flow_k=smooth(seg(u, cue(6), cue(8))))
    P.breath(img, u, hole[0], hole[1] - 10, ang=-math.pi / 2 - .35, sign=1, k=.75, scale=.5, n=8, spread=1.0, seed=13,
             Lr=(500, 800), Ar=(30, 60), width=22, particles=20)
    gT, gJ = bros_small(img, u, hole, dx=(110, 190), lookT=-.6, lookJ=-.5)
    img = finish(img, u, 1.1 + .03 * smooth(u / D), 600, 800, vig=(.34, (30, 20, 24)))
    if not HIDE_UI:
        stitle(img, 's04_t', [('A TUNNEL?', 'white', 130)], 200, u, cue(4) - .1)
        if ek > 0:
            chip(img, 'ANOTHER OPENING?', (70, 120, 190), 700, ex[1] + 120, u, cue(6) - .05, size=50)
            q = pop(u, cue(8), .3)
            if q > 0:
                lay, _ = tlayer('q4', [('?', (255, 214, 90), 150)], 150)
                anim.scaled_paste(img, lay, ex[0] + 10, ex[1] - 300 + 6 * math.sin(u * 3), q)
    faces = [face_box(gT, 1.3), face_box(gJ, 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 130, W, 380), (360, ex[1] + 60, W, ex[1] + 180)]}


def s05a(u, D, cue):
    cam = -16 + 10 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    fade = smooth(seg(u, cue(4), cue(6) + .2))
    hole, ex = section_scene(img, u, cam, tunnel_k=1.0, tunnel_a=1 - .4 * fade, exit_k=1.0, flow_k=1 - fade, crack=fade)
    P.breath(img, u, hole[0], hole[1] - 10, ang=-math.pi / 2 - .35, sign=1, k=.75, scale=.5, n=8, spread=1.0, seed=13,
             Lr=(500, 800), Ar=(30, 60), width=22, particles=20)
    kx = seg(u, cue(5) - .1, cue(6) + .25) * 2
    gT, gJ = bros_small(img, u, hole, dx=(110, 190), lookT=-.6, lookJ=.6, exprT='worried', exprJ='surprised',
                        poseJ=mix(POSES['stand'], dict(POSES['stand'], armL=(70, 76)), smooth(seg(u, .2, .6))))
    if kx > 0: draw_x(img, ex[0] - 30, ex[1] + 70, 80, kx, w=28)
    rr = np.random.default_rng(4); dR = ImageDraw.Draw(img)
    for i in range(14):                                            # rubble falling through where the tunnel was
        bx = 600 + rr.uniform(-200, 320); by = 900 + ((u * rr.uniform(150, 260) + rr.uniform(0, 400)) % 420) * fade
        r_ = rr.uniform(8, 18); dR.polygon([(bx - r_, by), (bx, by - r_), (bx + r_, by + 3), (bx + 2, by + r_)], fill=(120, 90, 70), outline=INK)
    fill_mask(img, Image.new('L', (W, H), int(255 * .16 * fade)), (90, 120, 190))
    sx, sy = shake(u, cue(6), 7, .3)
    img = finish(img, u, 1.2 - .02 * smooth(u / D), 760, 880, dx=sx, dy=sy, vig=(.34, (30, 20, 24)))
    if not HIDE_UI:
        chip(img, 'NO OTHER ENTRANCE', (200, 60, 50), 540, 1560, u, cue(2) - .05, size=56)
        stitle(img, 's05a_t', [('NEVER FOUND', 'white', 124)], 200, u, cue(6) - .15)
    faces = [face_box(gT, 1.3), face_box(gJ, 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 130, W, 380), (700, 640, W, 960), (160, 1440, 920, 1560)]}


# ---------------------------------------------------------------- s05b: smaller than a sheet of paper
def s05b(u, D, cue):
    """Top-down: the hole in the rock seen from above, breathing up at us; a sheet of paper laid beside it (Jesse's
    hand holds its corner) with the hole's own outline traced on it: the hole fits inside the sheet."""
    cam = -10 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (196, 184, 164)), (.5, (176, 162, 144)), (1, (140, 126, 116))]))
    rng = np.random.default_rng(8)
    fl = layer(); dfl = ImageDraw.Draw(fl)                          # weathered facets: lit and shaded planes
    for i in range(26):
        cx_, cy_, r_ = rng.uniform(-100, W + 100) + cam, rng.uniform(150, H + 100), rng.uniform(120, 300)
        pts = [(cx_ + math.cos(a_) * r_ * rng.uniform(.7, 1.1), cy_ + math.sin(a_) * r_ * .7 * rng.uniform(.7, 1.1)) for a_ in np.linspace(0, 6.28, 7)]
        dfl.polygon(pts, fill=((236, 224, 200, 70) if i % 2 else (90, 78, 80, 60)))
    img.alpha_composite(fl)
    d = ImageDraw.Draw(img)
    for i in range(9):                                             # slab joints
        x0 = rng.uniform(-100, W); y0 = rng.uniform(300, 1900)
        pts = [(x0, y0)]
        for _ in range(5): pts.append((pts[-1][0] + rng.uniform(60, 160), pts[-1][1] + rng.uniform(-60, 60)))
        d.line([(x + cam, y) for x, y in pts], fill=(110, 98, 96), width=6, joint='curve')
    for i in range(70):                                            # lichen + pits
        x, y, r = rng.uniform(0, W) + cam, rng.uniform(250, H), rng.uniform(6, 22)
        d.ellipse([x - r, y - r * .7, x + r, y + r * .7], fill=(198, 192, 124) if i % 3 else (226, 170, 100))
    radial(img, 260, 400, 1300, (255, 230, 170), .5)
    kit.light_rays(img, 0, 0, (255, 236, 190), n=7, alpha=.2, spread=(30, 70), length=2400, seed=5, phase=2 * math.sin(u * .5))
    hole = (380 + cam, 1120)
    hw, hh = 118, 94                                               # ~8 x 10 in at this scale
    hp = [(hole[0] + math.cos(a_) * hw * (1 + .08 * math.sin(3 * a_)), hole[1] + math.sin(a_) * hh * (1 + .1 * math.cos(2 * a_)))
          for a_ in np.linspace(0, 2 * math.pi, 36, endpoint=False)]
    d.polygon([(hole[0] + (x - hole[0]) * 1.22, hole[1] + (y - hole[1]) * 1.25) for x, y in hp], fill=(120, 106, 102))
    d.polygon(hp, fill=(16, 12, 24))
    d.polygon([(hole[0] + (x - hole[0]) * .55, hole[1] + (y - hole[1]) * .55 + 8) for x, y in hp], fill=(4, 2, 10))
    d.line(hp + hp[:1], fill=INK, width=7, joint='curve')
    # breath coming up at us: rings + motes rising out of the hole
    lay = layer(); dl = ImageDraw.Draw(lay)
    for i in range(4):
        q = (i / 4 + u * .7) % 1.0
        r = hw * (.5 + 1.6 * q); al = int(230 * math.sin(math.pi * q))
        dl.ellipse([hole[0] - r, hole[1] - r * .8, hole[0] + r, hole[1] + r * .8], outline=P.BREATH_EDGE + (al,), width=14)
        dl.ellipse([hole[0] - r, hole[1] - r * .8, hole[0] + r, hole[1] + r * .8], outline=P.BREATH + (al,), width=7)
    img.alpha_composite(lay)
    radial(img, hole[0], hole[1], 260, (200, 232, 255), .45 + .1 * math.sin(u * 4))
    dust(img, 9, 40, (hole[0] - 250, hole[1] - 250, hole[0] + 250, hole[1] + 250), (240, 250, 255), 200, size=(3, 8), t=u * 3)
    for side, (gx, gy) in enumerate(((0, 300), (W, 1700), (0, 1900), (W, 420), (300, 1950), (800, 1990))):   # grass tufts at the rock's edges
        P.grass(img, u, (gx - 160, gy - 40, gx + 160, gy + 40), 16, 90, 160, seed=200 + side, clump=(5, 9), ink=INK)
    # the sheet of paper, laid flat beside the hole
    kp = out_back(seg(u, cue(13) - .45, cue(13)), 1.4)
    if kp > 0:
        pw = 400 * min(1.0, .4 + .6 * kp)
        px, py = 790 + cam + (1 - kp) * 200, 1150
        P.paper(img, px, py, pw, ang=-8, t=u * .2, alpha=min(1, kp * 1.5), lines=False)
        if kp > .85 and not HIDE_UI:
            lay = layer(); dl = ImageDraw.Draw(lay)
            dashed(dl, ellipse_pts(px, py, hw * 1.15, hh * 1.18), (220, 60, 50, 255), 12, 26, 14, phase=u * 30)
            img.alpha_composite(lay)
        # Jesse's arm from the right edge holding the corner
        hx, hy = px + pw * .45, py + pw * .55
        dd = ImageDraw.Draw(img)                                   # Jesse's arm reaches in from the frame edge
        sx_, sy_ = W + 80, hy + 420
        for wdt, col in ((70, INK), (58, (246, 246, 242))):
            dd.line([(sx_, sy_), (hx + 40, hy + 20)], fill=col, width=wdt)
        a_ = math.atan2(hy + 20 - sy_, hx + 40 - sx_); L_ = math.hypot(hx + 40 - sx_, hy + 20 - sy_)
        mx_, my_ = sx_ + math.cos(a_) * L_ * .45, sy_ + math.sin(a_) * L_ * .45
        dd.line([(sx_, sy_), (mx_, my_)], fill=INK, width=84); dd.line([(sx_, sy_), (mx_, my_)], fill=(79, 122, 166), width=72)
        dd.ellipse([hx + 40 - 40, hy + 20 - 40, hx + 40 + 40, hy + 20 + 40], fill=(246, 246, 242), outline=INK, width=5)
    img = finish(img, u, 1.1 + .04 * smooth(u / D), 560, 1150, vig=(.36, (40, 30, 30)))
    if not HIDE_UI:
        chip(img, 'TOP VIEW', (90, 110, 140), 210, 560, u, .05, size=44)
        stitle(img, 's05b_t', [('SMALLER THAN', 'white', 104), ('A SHEET OF PAPER', (255, 214, 90), 96)], 230, u, cue(10) - .1,
               stagger=cue(13) - cue(10))
        chip(img, 'ONE HOLE ~20 x 25 CM', (176, 112, 52), 420, 1420, u, cue(8) - .1, size=44)
    return img, {'faces': [], 'avoid': [(0, 180, W, 470), (120, 1360, 720, 1480), (160, 780, 1080, 1420), (640, 1420, W, 1800)]}


# ---------------------------------------------------------------- s06: CLUE 1 - it breathes IN, Jesse's hat is sucked inside
def s06(u, D, cue):
    cam = 10 * math.sin(u * .4)
    hole = (470 + cam * .85, 1190)
    kin = smooth(seg(u, cue(4) - .3, cue(6))) * (1 + .4 * smooth(seg(u, cue(7), cue(9))))
    k = .25 + 1.1 * kin
    ang = -math.pi / 2 + .45                                    # the air comes from the upper right, into the hole
    G = {}
    t_hat = cue(8) - .1
    hat_on = u < t_hat
    def chars(img, src):
        kr = out_back(seg(u, t_hat + .1, t_hat + .45), 1.6)
        pose = mix(dict(POSES['stand'], armL=(30, 14)), dict(POSES['stand'], armL=(78, 60), armR=(-40, -20)), kr)
        G['j'] = brother(img, u, 'jesse', pose, 'neutral' if u < cue(5) else ('surprised' if u < t_hat + .5 else 'scared'),
                         800 + cam, 1840, .78, look=-.7, lean=-8 * kr + 1.5 * math.sin(u * 2.3), hat=hat_on,
                         rim=(255, 236, 190), rim_dir=(-1, -.5), aura=(255, 230, 170), aura_a=.3)
    img = prairie_world(u, cam, k_breath=k, sign=-1, kind='morning', hole=hole, rock_s=1.7, near_y=1150, gold=tuple(lerp(a_, b_, .45) for a_, b_ in zip(P.GREEN, P.GOLD)),
                        breath_ang=-math.pi / 2, chars=chars, spread=2.6, breath_scale=1.1, wind=-.05)
    if not hat_on:                                              # the hat lifts, spins and shrinks into the hole
        hx, hy = G['j']['head']; R = G['j']['R']
        v = seg(u, t_hat, cue(11) + .1)
        e = v * v * (3 - 2 * v)
        x = hx + (hole[0] - hx) * e + 60 * math.sin(math.pi * e)
        y = hy - R * .85 + (hole[1] - (hy - R * .85)) * e - 420 * math.sin(math.pi * e)
        sc = 1.35 * (1 - .7 * e ** 2.4)
        if v < 1:
            hm = mask(); ImageDraw.Draw(hm).ellipse([x - 150 * sc, y - 70 * sc, x + 150 * sc, y + 60 * sc], fill=255)
            glow(img, hm, (255, 255, 255), .6 * (1 - v), blur=24, add=True)
            dS = ImageDraw.Draw(img); aa = math.atan2(hole[1] - y, hole[0] - x)
            for kq in (-1, 0, 1):                                  # motion streaks behind the hat
                ox, oy = -math.sin(aa) * 40 * kq * sc, math.cos(aa) * 40 * kq * sc
                dS.line([(x + ox - math.cos(aa) * 260 * sc, y + oy - math.sin(aa) * 260 * sc), (x + ox - math.cos(aa) * 110 * sc, y + oy - math.sin(aa) * 110 * sc)],
                        fill=(255, 255, 255), width=8)
            P.put_hat(img, P.JESSE_HAT, x, y, sc, angle=35 * math.sin(u * 7) - 30 * e, alpha=1 - smooth(seg(v, .85, 1)))
    img = finish(img, u, 1.0 + .04 * smooth(u / D), 520, 1200, vig=(.26, (30, 40, 60)))
    clue(img, 'CLUE 1', u, .05, 230)
    if not HIDE_UI:
        chip(img, 'LATER: BREATHING IN', (60, 130, 210), 540, 430, u, cue(2) - .05, size=54)
    return img, {'faces': [face_box(G['j'], 1.3)], 'avoid': [(0, 130, W, 580), (hole[0] - 320, hole[1] - 200, hole[0] + 320, hole[1] + 160)]}


# ---------------------------------------------------------------- s07: CLUE 2 - it follows the weather (split screen)
def half_scene(u, which, cam, k):
    """One half (full frame drawn, the half is clipped): storm -> blows OUT, fair -> pulls IN."""
    storm = which == 'storm'
    cx = 270 if storm else 810
    img = Image.new('RGBA', (W, H))
    gold = P.GOLD_STORM if storm else P.GOLD
    P.sky(img, 'storm' if storm else 'fair')
    if storm:
        P.storm_deck(img, u, 760, seed=7, drift=40)
        P.thunderhead(img, u, cx - 40, 1020, .6, seed=9, rain_a=.0, alpha=.9, cols=((70, 62, 100), (100, 90, 130), (150, 136, 176)))
    else:
        P.sun(img, cx + 160, 620, 50, u)
        P.cumulus(img, u, [(cx - 120, 520, .7, 51, 10), (cx + 160, 780, .5, 52, 8)])
    rc = ((100, 96, 136), (70, 76, 100), (48, 58, 66)) if storm else ((150, 150, 188), (96, 116, 132), (58, 82, 78))
    P.paste_band(img, P.pine_ridge(81, 1060, 120, rc[0], tree=(18, 34), dens=1.2), cam, .2)
    P.paste_band(img, P.pine_ridge(82, 1120, 100, rc[1], tree=(26, 50), dens=1.1), cam, .35)
    haze(img, 950, 1200, (150, 130, 170) if storm else (255, 226, 190), .35)
    P.paste_band(img, P.hill(83, 1230, 40, gold, ink=INK, waves=(.8, 2.0)), cam, .7)
    hole = (cx, 1330)
    sign = 1 if storm else -1
    ang = -math.pi / 2 + (-.15 if storm else .2)
    src = (hole[0], hole[1], 1.3 * k, sign, ang)
    P.grass(img, u, (cx - 330, 1200, cx + 330, 1480), 110, 30, 60, cols=gold, seed=84 + storm, src=src, clump=(3, 6),
            ytop=lambda x: P.edge_y(83, 1230, 40, x - cam * .7, waves=(.8, 2.0)) + 4)
    P.outcrop(img, hole[0], hole[1], 1.05, seed=3, breath_glow=k, t=u, src=src, gold=gold)
    P.grass(img, u, (cx - 330, 1460, cx + 330, 1990), 70, 60, 110, cols=gold, seed=86 + storm, src=src, clump=(4, 8))
    if storm:
        P.rain(img, u, (0, 0, W, H), n=170, slant=.35)
    return img, hole, src, ang, sign


def s07(u, D, cue):
    cam = 6 * math.sin(u * .5)
    ks = .6 + .7 * smooth(seg(u, cue(6) - .2, cue(10))) + .1 * math.sin(u * 6)
    kf = .5 + .7 * smooth(seg(u, cue(12) - .2, cue(16))) + .1 * math.sin(u * 5)
    A, ha, srcA, angA, _ = half_scene(u, 'storm', cam, ks)
    B, hb, srcB, angB, _ = half_scene(u, 'fair', cam, kf)
    radial(A, 200, 760, 520, (180, 160, 255), .35 + .1 * math.sin(u * 3))
    lf = P.lightning(A, u, cue(8) - .05, 160, 300, 1000, seed=4, dur=.35)
    G = {}
    # breath on each side (clipped to its half)
    clipA = mask(); ImageDraw.Draw(clipA).rectangle([0, 0, 540, H], fill=255)
    clipB = mask(); ImageDraw.Draw(clipB).rectangle([540, 0, W, H], fill=255)
    G['t'] = brother(A, u, 'tom', dict(POSES['stand'], armL=(40, 70), armR=(-60, -100)), 'worried', 170, 1910, .68, look=.6,
                     lean=-5 + 1.5 * math.sin(u * 7), hat=False, rim=(200, 190, 255), rim_dir=(1, -.4), aura=(170, 160, 230), aura_a=.3)
    G['j'] = brother(B, u, 'jesse', dict(POSES['stand'], armL=(30, 20)), 'thinking', 915, 1910, .68, look=-.6,
                     lean=2 + 1.0 * math.sin(u * 2), hat=False, rim=(255, 226, 170), rim_dir=(-1, -.4))
    P.breath(A, u, ha[0], ha[1], ang=angA, sign=1, k=ks, scale=.85, n=10, spread=1.0, seed=17, Lr=(700, 1000), Ar=(30, 70), width=24,
             particles=36, clip=clipA)
    P.breath(B, u, hb[0], hb[1], ang=angB, sign=-1, k=kf, scale=.85, n=10, spread=1.3, seed=18, Lr=(650, 950), Ar=(30, 70), width=24,
             particles=36, clip=clipB)
    img = A.copy(); img.paste(B, (0, 0), clipB)
    d = ImageDraw.Draw(img)                                     # the divider: a jagged lightning seam
    seam = [(540 + 18 * math.sin(i * 1.7), y) for i, y in enumerate(range(-20, H + 40, 80))]
    d.line(seam, fill=INK, width=22, joint='curve'); d.line(seam, fill=(250, 246, 236), width=10, joint='curve')
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 540, 1300, vig=(.24, (30, 30, 50)))
    clue(img, 'CLUE 2', u, .05, 230)
    if not HIDE_UI:
        chip(img, 'FOLLOWS THE WEATHER', (90, 110, 140), 540, 420, u, cue(3) - .05, size=46)
        chip(img, 'STORM', (90, 70, 150), 270, 620, u, cue(7) - .1, size=50)
        chip(img, 'BLOWS OUT', (60, 130, 210), 270, 720, u, cue(10) - .1, size=44)
        chip(img, 'FAIR', (220, 150, 40), 810, 620, u, cue(13) - .1, size=50)
        chip(img, 'PULLS IN', (60, 130, 210), 810, 720, u, cue(16) - .1, size=44)
    return img, {'faces': [face_box(G['t'], 1.3), face_box(G['j'], 1.3)], 'avoid': [(0, 130, W, 780), (60, 1000, 1020, 1460)]}


# ---------------------------------------------------------------- s08a / s08b: CLUE 3 - the maze behind the hole
CAVE_ROCK = ((52, 50, 58), (44, 44, 54), (38, 38, 50), (32, 34, 46), (26, 28, 40), (20, 22, 34))


def surface_strip(img, u, y, cam=0.0, hole_x=540, k=.8, sign=1, sky='fair', storm=0.0):
    """A thin slice of the prairie on top of a cutaway: sky band, ridges and a grass line at y (clipped to y + 40),
    composited over whatever is below. Returns the hole position for the outcrop."""
    lay = layer()
    P.sky(lay, sky, y + 40, storm, 'storm' if storm else None)
    P.paste_band(lay, P.pine_ridge(91, y - 40, 110, (110, 126, 160), tree=(18, 34), dens=1.2, haze_col=(230, 220, 220), haze_a=.3), cam, .3)
    P.paste_band(lay, P.pine_ridge(92, y, 80, (70, 92, 98), tree=(24, 44)), cam, .45)
    d = ImageDraw.Draw(lay)
    d.rectangle([0, y - 4, W, y + 40], fill=P.GOLD[1])
    d.line([(0, y + 40), (W, y + 40)], fill=INK, width=6)
    m = mask(); ImageDraw.Draw(m).rectangle([0, 0, W, y + 43], fill=255)
    lay.putalpha(ImageChops.multiply(lay.split()[3], m))
    img.alpha_composite(lay)
    P.grass(img, u, (-20, y - 2, W + 20, y + 2), 120, 18, 36, cols=P.GOLD, seed=93, clump=(3, 6), src=(hole_x, y - 30, 1.0 * k, sign, -math.pi / 2))
    return (hole_x + cam, y - 26)


def cave_dark(img, lights, dark=(4, 8, 16), a=.86):
    """Darkness over the cutaway except pools of light [(x, y, r, strength)]."""
    m = np.full((H, W), a, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    for x, y, r, st in lights:
        dd = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
        m *= 1 - np.clip(1 - dd, 0, 1) ** 1.2 * st
    fill_mask(img, Image.fromarray((m * 255).astype(np.uint8)), dark)


NET8 = (11, (40, 760, 1040, 1880))
NET8B = (12, (-60, 380, 1140, 1980))


def chamber(img, cx, floor, rx, ry, air=(96, 132, 128), seed=2):
    """A cave chamber the caver stands in: a lumpy vault with a flat floor, rock lip and a few stalactites."""
    rng = np.random.default_rng(seed)
    m = mask(); d = ImageDraw.Draw(m)
    for i in range(7):
        a = math.pi + math.pi * i / 6
        x, y = cx + math.cos(a) * rx * .7, floor - ry * .55 + math.sin(a) * ry * .5
        r = rng.uniform(.4, .6) * rx
        d.ellipse([x - r, y - r * .8, x + r, y + r * .8], fill=255)
    d.rectangle([cx - rx * .95, floor - ry * .6, cx + rx * .95, floor], fill=255)
    fill_mask(img, m.filter(ImageFilter.MaxFilter(17)), (8, 10, 16))
    fill_mask(img, m, air)
    sh = ImageChops.subtract(m, ImageChops.offset(m, 0, 14))
    fill_mask(img, sh, (200, 214, 190), .7)
    dd = ImageDraw.Draw(img)
    dd.rectangle([cx - rx * .95, floor, cx + rx * .95, floor + 26], fill=(40, 40, 50))
    dd.line([(cx - rx * .95, floor), (cx + rx * .95, floor)], fill=INK, width=6)
    for i in range(6):
        x = cx + rng.uniform(-.7, .7) * rx; ytop = floor - ry * 1.0 + abs(x - cx) / rx * ry * .45
        L = rng.uniform(20, 60)
        dd.polygon([(x - 10, ytop - 4), (x + 10, ytop - 4), (x, ytop + L)], fill=(150, 170, 160), outline=INK)


def maze_scene(img, u, net, lamp, beam_ang, reveal=1.0, origin=None, dark_a=.84, air=(96, 132, 128), extra_lights=(), room=None):
    P.earth_section(img, 0, H + 40, cols=CAVE_ROCK, seed=19, edge_fn=lambda x: -10, ink=False)
    img.alpha_composite(P.boxwork(3))
    nt = P.maze_net(*net, n_nodes=40 if net is NET8 else 60, extra=24 if net is NET8 else 40)
    P.draw_maze(img, nt, reveal=reveal, order_from=origin, wall=(8, 10, 16), air=air, rim=(200, 214, 190))
    if room: chamber(img, *room, air=air)
    lights = [(lamp[0] + math.cos(beam_ang) * 260, lamp[1] + math.sin(beam_ang) * 260, 520, .95), (lamp[0], lamp[1], 300, .9)] + list(extra_lights)
    cave_dark(img, lights, a=dark_a)
    P.lamp_light(img, lamp[0], lamp[1], beam_ang, u, reach=760, spread=.38, a=.6)
    return nt


def s08a(u, D, cue):
    """CLUE 3: from the hole at the surface the camera pulls back and the maze opens up below it, lit by a caver's lamp."""
    world = Image.new('RGBA', (W, H))
    reveal = .25 + .75 * smooth(seg(u, cue(2) - .3, D))
    lamp = (720, 1300)
    ba = math.pi * .92 + .3 * math.sin(u * 1.4)
    maze_scene(world, u, NET8, lamp, ba, reveal=reveal, origin=(540, 700),
               extra_lights=[(540, 700, 260, .7)], room=(lamp[0] + 20, lamp[1] + 330, 230, 400))
    hole = surface_strip(world, u, 600, hole_x=540, k=.8)
    P.outcrop(world, hole[0], hole[1], .9, seed=3, breath_glow=.8, t=u, tufts=False)
    d = ImageDraw.Draw(world)                                  # the throat from the hole down into the maze
    throat = [(hole[0], hole[1] + 20), (560, 700), (520, 780), (560, 860)]
    d.line(throat, fill=(8, 10, 16), width=76, joint='curve'); d.line(throat, fill=(96, 132, 128), width=52, joint='curve')
    P.breath(world, u, hole[0], hole[1] - 6, ang=-math.pi / 2 - .2, sign=1, k=.7, scale=.5, n=7, spread=1.0, seed=21,
             Lr=(400, 560), Ar=(20, 50), width=20, particles=14)
    g = caver(world, u, dict(POSES['stand'], armR=(-70, -50)), 'surprised', lamp[0] + 40, lamp[1] + 330, .4, look=-.8, label_on=False)
    z = 2.0 - 1.0 * smooth(seg(u, .0, D * .8))
    img = finish(world, u, z, 540, 600 + 300 * (z - 1), vig=(.4, (4, 8, 16)))
    clue(img, 'CLUE 3', u, .05, 230)
    if not HIDE_UI:
        stitle(img, 's08a_t', [('A MAZE', (255, 206, 120), 150)], 1700, u, cue(7) - .1)
    return img, {'faces': [], 'avoid': [(0, 130, W, 340), (0, 1660, W, 1900)]}


def km_counter(img, u, t0, t1, x, y, size=150):
    v = smooth(seg(u, t0, t1))
    n = int(round(260 * v))
    txt = f'{n}+ KM' if v >= 1 else f'{n} KM'
    lay = anim.text_layer(lambda l: title(l, [(txt, (255, 206, 120), size)], 60, size=size), W, int(size * 2.2))
    s = 1.0 + .08 * math.exp(-max(0, u - t1) * 8) * (u >= t1)
    anim.scaled_paste(img, lay[0], x, y, s)


def s08b(u, D, cue):
    world = Image.new('RGBA', (W, H))
    lamp = (300 + 50 * smooth(u / D), 1120)
    ba = -.15 + .5 * math.sin(u * 1.1)
    qs = [(120, 560), (980, 640), (110, 1480), (990, 1400), (760, 1080)]
    extra = [(x, y, 200, .55 * smooth(seg(u, cue(16) - .3, cue(18)))) for x, y in qs]
    maze_scene(world, u, NET8B, lamp, ba, reveal=1.0, dark_a=.62, extra_lights=extra, room=(lamp[0] - 30, lamp[1] + 395, 230, 400))
    g = caver(world, u, dict(POSES['stand'], armR=(-50, -20), armL=(20, 10)), 'surprised', lamp[0] - 30, lamp[1] + 395, .42,
              look=.8, label_on=not HIDE_UI)
    ke = smooth(seg(u, cue(16) - .2, cue(18)))
    if ke > 0 and not HIDE_UI:                                 # the dark, unexplored ends
        for i, (x, y) in enumerate(qs):
            q = pop(u, cue(16) + i * .12, .3)
            if q > 0:
                radial(world, x, y, 160, (120, 200, 255), .5 * q)
                lay, _ = tlayer('q8', [('?', (150, 220, 255), 130)], 130)
                anim.scaled_paste(world, lay, x, y + 6 * math.sin(u * 3 + i), q)
    img = finish(world, u, 1.08 - .08 * smooth(u / D), 480, 1200, vig=(.42, (4, 8, 16)))
    if not HIDE_UI:
        km_counter(img, u, cue(9) - .1, cue(13), 540, 330)
        chip(img, 'OF TUNNELS', (40, 110, 130), 540, 470, u, cue(15) - .1, size=56)
        chip(img, 'NOT FULLY EXPLORED', (60, 80, 120), 600, 1800, u, cue(17) - .1, size=58)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 200, W, 520), (240, 1730, 960, 1880)]}


# ---------------------------------------------------------------- s09: dusk - what makes a hole breathe?
def s09(u, D, cue):
    cam = -12 * smooth(u / D)
    hole = (430 + cam * .85, 1210)
    G = {}
    def chars(img, src):
        G['t'] = brother(img, u, 'tom', 'think', 'thinking', 680 + cam, 1900, .66, look=-.5, hat=False, rim=(255, 170, 120), rim_dir=(1, -.4),
                         aura=(255, 150, 110), aura_a=.35)
        G['j'] = brother(img, u, 'jesse', dict(POSES['stand'], armL=(18, 6)), 'worried', 870 + cam, 1860, .6, look=-.6, hat=False,
                         rim=(255, 170, 120), rim_dir=(1, -.4), aura=(255, 150, 110), aura_a=.3)
    dusk_gold = ((236, 150, 110), (190, 104, 92), (140, 74, 80), (96, 52, 66))
    img = Image.new('RGBA', (W, H))
    prairie_back(img, u, cam, kind='dusk', sunp=(760, 960), warm=1.0, clouds=False,
                 ridge_cols=((120, 76, 120), (84, 52, 96), (56, 36, 70)))
    P.cumulus(img, u, [(200, 420, .9, 61, 5), (820, 300, 1.1, 62, 4)], lit=(255, 196, 150), shade=(150, 90, 130), mid=(220, 140, 140))
    P.paste_band(img, P.hill(42, 1180, 50, dusk_gold, ink=INK, waves=(.8, 2.1)), cam, .8)
    k = pulse(u, 1.6, .6, 1.1)
    src = (hole[0], hole[1], 1.0 * k, 1, -math.pi / 2 - .1)
    P.grass(img, u, (-60, 1130, W + 60, 1260), 200, 22, 46, cols=dusk_gold, seed=3, src=src, clump=(3, 6),
            ytop=lambda x: P.edge_y(42, 1180, 50, x - cam * .8, waves=(.8, 2.1)) + 4)
    rock = ((214, 150, 140), (160, 104, 112), (110, 70, 90), (74, 46, 66))
    P.outcrop(img, hole[0], hole[1], 1.5, seed=3, cols=rock, breath_glow=k, t=u, src=src, gold=dusk_gold)
    P.grass(img, u, (-60, 1350, W + 60, 1700), 120, 40, 80, cols=dusk_gold, seed=4, src=src, clump=(4, 7))
    P.breath(img, u, hole[0], hole[1], ang=-math.pi / 2 - .1, sign=1, k=k, scale=1.0, n=10, spread=1.1, seed=23, Lr=(700, 1000),
             Ar=(30, 70), width=22, particles=30)
    chars(img, src)
    # the question mark rides up on the breath
    q = smooth(seg(u, cue(1), cue(8)))
    if not HIDE_UI and q > 0:
        lay, _ = tlayer('q9', [('?', (255, 214, 120), 300)], 300)
        anim.scaled_paste(img, lay, hole[0] + 20 * math.sin(u * 3), hole[1] - 260 - 360 * q, .4 + .7 * q, angle=6 * math.sin(u * 2.4))
    P.grass(img, u, (-80, 1860, W + 80, 1990), 50, 90, 170, cols=dusk_gold, seed=5, src=src, w0=9, clump=(5, 9), ink=INK)
    fg_frame(img, u, col=(50, 24, 40), sides=(0,))
    img = finish(img, u, 1.0 + .05 * smooth(u / D), 500, 1200, vig=(.32, (40, 16, 40)))
    return img, {'faces': [face_box(G['t'], 1.3), face_box(G['j'], 1.3)], 'avoid': [(hole[0] - 260, 300, hole[0] + 260, hole[1] + 150)]}


# ---------------------------------------------------------------- s10: the air above us is heavy (the pressure column)
def air_column(img, u, x0, x1, y_top, y_bot, k=1.0, n=9, arrows=1.0, drop=0.0, col=(150, 205, 255)):
    """A stack of translucent air slabs pressing down (denser toward the ground) with down arrows beside it.
    k = thickness 0..1 (thin under a storm, thick in fair weather). Moves: slabs breathe 1%, arrows pulse."""
    lay = layer(); d = ImageDraw.Draw(lay)
    m = int(round(3 + (n - 3) * k))
    hseg = (y_bot - y_top) / n
    for i in range(m):
        yb = y_bot - i * hseg - drop * (1 - i / max(1, m)) * 0
        yt = yb - hseg * .9
        dens = 1 - i / n
        a = int((70 + 120 * dens) * (.6 + .4 * k))
        wob = 4 * math.sin(u * 2 + i)
        d.rounded_rectangle([x0 - wob, yt, x1 + wob, yb], 26, fill=lerp(col, (255, 255, 255), .3 * (1 - dens)) + (a,),
                            outline=(60, 110, 180, min(255, a + 60)), width=5)
        for j in range(3):                                      # air molecules: denser below
            for q in range(int(3 + 7 * dens)):
                xx = x0 + 40 + ((q * 97 + j * 53 + i * 31) % int(x1 - x0 - 80))
                yy = yt + 20 + (j * .33) * (hseg * .9 - 40) + 6 * math.sin(u * 3 + q + i)
                d.ellipse([xx - 7, yy - 7, xx + 7, yy + 7], fill=(255, 255, 255, int(a * 1.2) if a * 1.2 < 255 else 255))
    img.alpha_composite(lay)
    if arrows > 0:
        dd = ImageDraw.Draw(img)
        for i, x in enumerate((x0 - 80, x1 + 80)):
            for j in range(3):
                yy = y_top + (y_bot - y_top) * (.2 + .3 * j) + 30 * ((u * 1.2 + j * .33) % 1.0)
                L = 120 * (.6 + .6 * k)
                al = arrows
                import jungle as J
                J.arrow(dd, [(x, yy), (x, yy + L)], lerp((120, 180, 255), (255, 255, 255), .2), w=int(14 + 10 * k), head=int(34 + 16 * k))


def land_strip(img, u, y, cam=0.0, src=None, gold=P.GOLD):
    P.paste_band(img, P.pine_ridge(101, y - 30, 90, (96, 116, 132), tree=(20, 40)), cam, .3)
    P.paste_band(img, P.hill(102, y + 40, 26, gold, ink=INK, waves=(.6, 1.7)), cam, .6)
    P.grass(img, u, (-60, y + 10, W + 60, y + 200), 130, 26, 52, cols=gold, seed=103, src=src, clump=(3, 6),
            ytop=lambda x: P.edge_y(102, y + 40, 26, x - cam * .6, waves=(.6, 1.7)) + 4)


def s10(u, D, cue):
    """The air above us is heavy: the whole sky as a blanket of air (denser low down) that drops onto the land on
    'heavy' and presses down (arrows) on 'presses'. Jesse looks up."""
    img = Image.new('RGBA', (W, H))
    P.sky(img, 'deep')
    stars(img, 5, 70, 360, u)
    y_land = 1420
    hole = (400, y_land + 70)
    radial(img, 540, y_land - 40, 900, (255, 214, 160), .55)
    P.cumulus(img, u, [(120, y_land - 60, .9, 75, 6), (560, y_land - 90, 1.2, 76, 5), (980, y_land - 50, .8, 77, 7)],
              lit=(255, 236, 214), shade=(176, 186, 220), mid=(230, 220, 230))
    land_strip(img, u, y_land, src=(hole[0], hole[1], .25, 1, -math.pi / 2))
    P.outcrop(img, hole[0], hole[1], 1.25, seed=3, breath_glow=.45, t=u)
    drop = 1 - out_back(seg(u, cue(5) - .4, cue(5) + .02), 1.2)
    P.cumulus(img, u, [(200, 760, 1.1, 91, 6), (820, 640, 1.3, 92, 5), (520, 1020, .9, 93, 7), (980, 1120, .8, 94, 8), (100, 1180, .7, 95, 9)],
              lit=(236, 244, 255), shade=(120, 150, 210), mid=(190, 210, 240))
    radial(img, 540, 300, 700, (120, 170, 255), .3)
    lay = layer()
    P.air_blanket(lay, u, 380, y_land - 70, k=1.0, arrows=smooth(seg(u, cue(6), cue(7) + .1)) * (1 + .15 * math.sin(u * 5)))
    img.alpha_composite(lay, (0, int(-900 * drop)))
    sx, sy = shake(u, cue(5), 12, .45)
    kp = smooth(seg(u, cue(7) - .1, cue(8)))
    g = brother(img, u, 'jesse', mix(dict(POSES['stand'], armL=(36, 20), armR=(-36, -20)), dict(POSES['stand'], armL=(60, 110), armR=(-60, -110)), kp),
                'surprised' if u > cue(5) else 'neutral', 780, 1900, .86, look=-.3, lean=-1.5 * kp, hop=-6 * kp, hat=False,
                rim=(200, 230, 255), rim_dir=(1, -.5), aura=(160, 210, 255), aura_a=.3)
    P.grass(img, u, (-80, 1850, W + 80, 1990), 50, 80, 150, seed=104, w0=9, clump=(5, 9), ink=INK)
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 540, 1200, dx=sx, dy=sy, vig=(.32, (10, 14, 40)))
    if not HIDE_UI:
        stitle(img, 's10_t', [('THE AIR', 'white', 120), ('IS HEAVY', KEY, 150)], 110, u, cue(1) - .1, stagger=cue(5) - cue(1))
        chip(img, 'AIR PRESSURE', (60, 110, 190), 330, 1170, u, cue(7) - .1, size=56)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 90, W, 420), (40, 1110, 620, 1230), (0, 1250, 900, 1700)]}


# ---------------------------------------------------------------- s11: a storm comes - the pressure drops, the cave exhales
def cutaway(img, u, y_surf, hole_x, cam=0.0, air_k=0.0, air_col=(150, 210, 255), sky='fair', storm=0.0, swell=0.0, rock=CAVE_ROCK):
    """Top: sky + land; below y_surf: rock cutaway with the cave chambers (glowing CAVE AIR when air_k > 0)."""
    P.sky(img, sky, H, storm, 'storm' if sky != 'storm' else None)
    P.earth_section(img, y_surf, H + 40, cols=((150, 112, 84), (120, 90, 70), (96, 72, 62), (74, 58, 56), (58, 46, 50), (44, 36, 44)),
                    seed=29, ink=True)
    nt = P.maze_net(13, (40, y_surf + 160, 1040, 1880), n_nodes=26, extra=16)
    mi = P.draw_maze(img, nt, wall=(30, 24, 30), air=(60, 70, 84), rim=(120, 120, 130))
    d = ImageDraw.Draw(img)
    throat = [(hole_x, y_surf - 10), (hole_x + 20, y_surf + 90), (hole_x - 10, y_surf + 170)]
    d.line(throat, fill=(30, 24, 30), width=64, joint='curve'); d.line(throat, fill=(60, 70, 84), width=42, joint='curve')
    if air_k > 0:
        a = np.asarray(mi, np.float32) / 255
        m = Image.fromarray((a * 255 * min(1, air_k)).astype(np.uint8))
        glow(img, m, air_col, .9 * air_k, blur=int(16 + 30 * swell), add=True)
        fill_mask(img, m.filter(ImageFilter.MaxFilter(int(3 + 2 * int(4 * swell)) | 1)), lerp(air_col, (255, 255, 255), .3), .55 * air_k)
    return nt


def s11(u, D, cue):
    cam = 0.0
    y_surf = 1000
    hole_x = 600
    ks = smooth(seg(u, cue(2) - .3, cue(5)))
    kd = smooth(seg(u, cue(5), cue(6) + .3))
    kp = smooth(seg(u, cue(10), cue(12)))
    kout = smooth(seg(u, cue(13) - .2, cue(15)))
    img = Image.new('RGBA', (W, H))
    cutaway(img, u, y_surf, hole_x, sky='fair', storm=ks, air_k=.5 + .6 * kp, swell=kp)
    P.storm_deck(img, u, 380 + 120 * ks, seed=31, drift=50, k=ks, y_top=-200)
    lf = P.lightning(img, u, cue(2) + .05, 820, 200, y_surf - 40, seed=6, dur=.35) if ks > .3 else 0
    P.rain(img, u, (0, 300, W, y_surf), n=int(140 * ks), slant=.3, a=int(150 * ks))
    land = layer()
    P.paste_band(land, P.hill(111, y_surf + 6, 10, P.GOLD_STORM if ks > .5 else P.GOLD, ink=INK, waves=(.5, 1.5)), cam, .6)
    m = mask(); ImageDraw.Draw(m).rectangle([0, 0, W, y_surf + 40], fill=255)
    land.putalpha(ImageChops.multiply(land.split()[3], m))
    img.alpha_composite(land)
    src = (hole_x, y_surf - 20, .4 + 1.2 * kout, 1, -math.pi / 2)
    P.grass(img, u, (-20, y_surf - 10, W + 20, y_surf + 10), 110, 18, 34, cols=P.GOLD_STORM if ks > .5 else P.GOLD, seed=113, src=src, clump=(3, 6))
    P.outcrop(img, hole_x, y_surf - 30, 1.2, seed=3, breath_glow=.5 + kout, t=u, tufts=False)
    # the blanket of air above thins as the storm comes (pressure drops)
    P.air_blanket(img, u, 300, y_surf - 30, k=1 - .72 * kd, n=5, arrows=1 - .75 * kd, xs=(330, 760))
    # pressure arrows inside the cave push outward when the cave air pushes harder
    if kp > 0:
        dd = ImageDraw.Draw(img)
        import jungle as J
        for (x, y, a) in ((260, 1380, -2.4), (720, 1300, -.6), (520, 1650, -1.57), (880, 1600, -.9), (180, 1750, -2.0)):
            L = 70 + 40 * kp + 10 * math.sin(u * 6)
            J.arrow(dd, [(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], (210, 236, 255), w=14, head=34)
    P.breath(img, u, hole_x, y_surf - 30, ang=-math.pi / 2 - .15, sign=1, k=.3 + 1.3 * kout, scale=.9, n=11, spread=1.0, seed=29,
             Lr=(700, 950), Ar=(30, 70), width=24, particles=40)
    g = brother(img, u, 'tom', mix(POSES['stand'], dict(POSES['stand'], armL=(40, 70), armR=(-60, -100)), kout), 'worried' if kout < .3 else 'scared',
                165, y_surf + 8, .46, look=.6, lean=-5 * kout, hat=False, rim=(200, 190, 255), rim_dir=(1, -.4))
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.3, (20, 14, 30)))
    if not HIDE_UI:
        P.barometer(img, 890, 500, 128, 1 - .85 * kd, u)
        chip(img, 'PRESSURE DROPS', (90, 70, 150), 800, 680, u, cue(5) - .1, size=50)
        chip(img, 'CAVE AIR', (60, 130, 210), 330, 1560, u, cue(9) - .1, size=56)
        if u < cue(13) - .1: stitle(img, 's11_t', [('A STORM COMES', 'white', 104)], 130, u, cue(2) - .1)
        else: stitle(img, 's11_t2', [('RUSHES OUT', KEY, 140)], 120, u, cue(13) - .1)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 100, W, 290), (560, 360, W, 700), (150, 1500, 520, 1620), (200, 760, 700, 1180)]}


def barometer_ui(img, u, x, y, needle, r=120):
    P.barometer(img, x, y, r, needle, u)


# ---------------------------------------------------------------- s12: the storm passes - the sky pushes air back in
def s12(u, D, cue):
    cam = 8 * math.sin(u * .5)
    hole = (380 + cam * .85, 1360)
    kc = smooth(seg(u, cue(1), cue(4)))                         # storm clears
    kr = smooth(seg(u, cue(5), cue(6) + .3))                    # pressure rises
    kin = smooth(seg(u, cue(9) - .3, cue(12)))
    img = Image.new('RGBA', (W, H))
    P.sky(img, 'storm', H, kc, 'sunset')                       # the storm moves off: a low golden sun breaks through
    if kc > .2:
        P.sun(img, 860, 900, 62, u, col=(255, 200, 130), a=kc)
        kit.light_rays(img, 860, 900, (255, 214, 150), n=12, alpha=.3 * kc, spread=(160, 330), length=2000, seed=9, phase=2 * math.sin(u * .4))
        rb = layer(); drb = ImageDraw.Draw(rb)                  # a rainbow on the departing storm
        for i, c_ in enumerate(((230, 70, 60), (250, 160, 50), (250, 230, 90), (90, 190, 90), (70, 130, 220), (120, 80, 190))):
            r_ = 900 - i * 26
            drb.arc([200 - r_, 1250 - r_, 200 + r_, 1250 + r_], 255, 335, fill=c_ + (int(170 * kc),), width=26)
        img.alpha_composite(kit.soft_layer(rb, 4))
    P.storm_deck(img, u, 420 - 500 * kc, seed=41, drift=60, k=1 - kc * .8, y_top=-300)
    P.cumulus(img, u, [(220, 760, .8, 81, 10), (900, 700, .7, 82, 8)], lit=(255, 214, 170), shade=(170, 130, 150), mid=(240, 180, 160), alpha=kc)
    gold = P.GOLD if kc > .5 else P.GOLD_STORM
    rc = ((160, 120, 150), (110, 96, 120), (70, 70, 80))
    P.paste_band(img, P.pine_ridge(121, 1150, 120, rc[0], tree=(18, 34), dens=1.2, haze_col=(236, 220, 210), haze_a=.3), cam, .2)
    P.paste_band(img, P.pine_ridge(122, 1210, 100, rc[1], tree=(26, 50)), cam, .35)
    P.paste_band(img, P.hill(123, 1290, 40, gold, ink=INK, waves=(.7, 1.9)), cam, .7)
    src = (hole[0], hole[1], 1.2 * (.3 + kin), -1, -math.pi / 2 + .3)
    P.grass(img, u, (-60, 1250, W + 60, 1420), 160, 26, 52, cols=gold, seed=124, src=src, clump=(3, 6),
            ytop=lambda x: P.edge_y(123, 1290, 40, x - cam * .7, waves=(.7, 1.9)) + 4)
    P.outcrop(img, hole[0], hole[1], 1.3, seed=3, breath_glow=.3 + .7 * kin, t=u, src=src, gold=gold)
    # the blanket of air thickens again and presses down (pressure rises)
    P.air_blanket(img, u, 380, 1240, k=.3 + .7 * kr, n=5, arrows=.4 + .6 * kr, xs=(110, 600), col=(255, 200, 160), arrow_col=(255, 240, 220))
    P.breath(img, u, hole[0], hole[1], ang=-math.pi / 2 + .3, sign=-1, k=.2 + 1.2 * kin, scale=1.05, n=11, spread=1.8, seed=31,
             Lr=(700, 1000), Ar=(30, 70), width=24, particles=40)
    g = brother(img, u, 'jesse', dict(POSES['stand'], armL=(30, 14)), 'surprised' if kin > .3 else 'thinking', 820 + cam, 1860, .66,
                look=-.5 + .4 * (1 - kin), hat=False, rim=(255, 230, 180), rim_dir=(1, -.5))
    P.grass(img, u, (-80, 1860, W + 80, 1990), 50, 90, 170, cols=gold, seed=125, src=src, w0=9, clump=(5, 9), ink=INK)
    fg_frame(img, u, sides=(0,))
    img = finish(img, u, 1.0 + .04 * smooth(u / D), 520, 1300, vig=(.28, (30, 30, 60)))
    if not HIDE_UI:
        P.barometer(img, 860, 560, 128, .15 + .8 * kr, u)
        chip(img, 'PRESSURE RISES', (220, 150, 40), 810, 740, u, cue(5) - .1, size=50)
        stitle(img, 's12_t', [('BACK IN', KEY, 140)], 160, u, cue(12) - .1)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 120, W, 340), (640, 440, W, 780), (hole[0] - 280, hole[1] - 200, hole[0] + 280, hole[1] + 160)]}


# ---------------------------------------------------------------- s13: a huge maze, one small hole
def s13(u, D, cue):
    img = Image.new('RGBA', (W, H))
    y_surf = 470
    P.sky(img, 'fair', y_surf + 60)
    P.paste_band(img, P.pine_ridge(131, y_surf - 30, 100, (110, 126, 160), tree=(18, 34), dens=1.2), 0, .3)
    P.paste_band(img, P.hill(132, y_surf + 10, 16, P.GOLD, ink=INK, waves=(.5, 1.4)), 0, .5)
    P.earth_section(img, y_surf + 20, H + 40, cols=((96, 92, 110), (76, 74, 96), (60, 60, 84), (46, 48, 72), (34, 38, 60), (24, 28, 48)), seed=33)
    nt = P.maze_net(14, (20, y_surf + 220, 1060, 1900), n_nodes=70, extra=50)
    breathe = .5 + .5 * math.sin(u * 2.2)
    kh = smooth(seg(u, cue(7), cue(10)))
    mi = P.draw_maze(img, nt, wall=(16, 18, 34), air=(40, 64, 100), rim=(100, 130, 170), glow_col=(120, 190, 255),
                     glow_a=.35 + .35 * breathe * (.4 + .6 * kh))
    hole = (540, y_surf - 10)
    cave_dark(img, [(540, 760, 700, .9), (540, 1200, 600, .5)], dark=(6, 8, 22), a=.62)     # light hierarchy: bright near the shaft
    radial(img, 540, 620, 420, (150, 210, 255), .45 + .15 * breathe)
    kit.depth_fade(img, 1150, H, (6, 8, 22), 0.0, .7)
    d = ImageDraw.Draw(img)
    shaft = [(hole[0], hole[1] + 20), (560, y_surf + 120), (530, y_surf + 220), (560, y_surf + 300)]
    d.line(shaft, fill=(16, 18, 34), width=46, joint='curve'); d.line(shaft, fill=(80, 130, 190), width=26, joint='curve')
    # the flow converging up the one shaft
    sp = _smooth_path(shaft[::-1], 8)
    for i in range(6):
        q = (i / 6 + u * .9) % 1.0
        x, y = path_point(sp, q); x2, y2 = path_point(sp, min(1, q + .05))
        chev(img, x, y, math.atan2(y2 - y, x2 - x), 16, (230, 246, 255), math.sin(math.pi * q) * (.4 + .6 * kh))
    P.outcrop(img, hole[0], hole[1], .5, seed=3, breath_glow=.8, t=u, tufts=False)
    P.breath(img, u, hole[0], hole[1] - 4, ang=-math.pi / 2, sign=1, k=.5 + .9 * kh, scale=.45, n=8, spread=1.0, seed=33,
             Lr=(500, 700), Ar=(20, 40), width=20, particles=14)
    pts, tunnels = nt                                           # air pulses run through every tunnel toward the hole
    for ti, (poly, w_, (i, j)) in enumerate(tunnels):
        if math.dist(pts[i], hole) < math.dist(pts[j], hole): poly = poly[::-1]
        for kk in range(2):
            q = (kk / 2 + u * (.5 + .4 * kh) + ti * .137) % 1.0
            x, y = path_point(poly, q); x2, y2 = path_point(poly, min(1, q + .08))
            chev(img, x, y, math.atan2(y2 - y, x2 - x), 13, (210, 236, 255), math.sin(math.pi * q) * (.35 + .65 * kh))
    kc = out_back(seg(u, cue(14) - .2, cue(15)), 1.6)
    if kc > 0 and not HIDE_UI:
        rm = mask(); ImageDraw.Draw(rm).ellipse([hole[0] - 120 * kc, hole[1] - 85 * kc, hole[0] + 120 * kc, hole[1] + 70 * kc], outline=255, width=14)
        glow(img, rm, (255, 214, 90), .9, blur=16, add=True)
        d = ImageDraw.Draw(img)
        for wdt, col in ((20, INK), (10, (255, 214, 90))):
            d.ellipse([hole[0] - 120 * kc, hole[1] - 85 * kc, hole[0] + 120 * kc, hole[1] + 70 * kc], outline=col, width=wdt)
    img = finish(img, u, 1.0 + .04 * smooth(u / D), 540, 900, vig=(.34, (6, 8, 24)))
    if not HIDE_UI:
        chip(img, '260+ KM OF TUNNELS', (60, 80, 140), 540, 1760, u, cue(2) - .1, size=48)
        chip(img, 'TINY CHANGE', (90, 110, 140), 790, 600, u, cue(5) - .1, size=52)
        stitle(img, 's13_t', [('ONE SMALL HOLE', KEY, 110)], 140, u, cue(14) - .2)
        chip(img, 'A HUGE AMOUNT OF AIR', (60, 110, 190), 540, 1040, u, cue(9) - .1, size=52)
    return img, {'faces': [], 'avoid': [(0, 100, W, 300), (600, 540, W, 660), (160, 1700, 920, 1820), (140, 980, 940, 1100), (0, 380, W, 980)]}


# ---------------------------------------------------------------- s14: a chips bag on a plane
def s14(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = -8 * smooth(u / D)
    P.cabin(img, u, cam)
    kp = smooth(seg(u, cue(8) - .1, cue(14) + .2))
    G = {}
    dW = ImageDraw.Draw(img)
    for x_ in (140, 980):                                      # wall panel seams
        dW.line([(x_, 380), (x_ - 20, 1500)], fill=(170, 172, 186), width=5)
    radial(img, 600 + cam * .2, 700, 520, (210, 230, 255), .5)
    d0 = ImageDraw.Draw(img)                                    # his seat (headrest + back) behind him
    d0.rounded_rectangle([60 + cam, 900, 500 + cam, 2000], 90, fill=(52, 72, 116), outline=INK, width=7)
    d0.rounded_rectangle([110 + cam, 940, 450 + cam, 1120], 60, fill=(236, 236, 240), outline=INK, width=5)
    radial(img, 600, 900, 900, (255, 236, 190), .45 + .03 * math.sin(u * 2))
    fill_mask(img, Image.new('L', (W, H), 50), (255, 200, 140))
    fill_mask(img, Image.fromarray(np.tile(np.clip((np.arange(H) - 1100) / 820, 0, 1)[:, None] * 120, (1, W)).astype(np.uint8)), (40, 50, 80))
    # the passenger behind the tray, upper body
    g = actor(img, 'neutral' if kp < .3 else 'surprised', dict(POSES['stand'], armL=(30, 60), armR=(-40, -70)), 300 + cam, 2150, 1.15, u,
              look=.5, aura=(255, 230, 190), aura_alpha=.25, rim=(255, 240, 210), rim_dir=(1, -.4), shirt='#6a8a5a', pants='#3a4058')
    G['p'] = g
    d = ImageDraw.Draw(img)
    # seat back + tray table in front of him
    d.rounded_rectangle([-40, 1560, 640, 2000], 40, fill=(60, 80, 120), outline=INK, width=7)
    d.rounded_rectangle([20, 1600, 580, 1720], 30, fill=(80, 104, 150), outline=INK, width=5)
    d.rectangle([-40, 1500, W + 40, 1580], fill=(200, 202, 210), outline=INK, width=6)
    d.rectangle([-40, 1572, W + 40, 1600], fill=(150, 152, 164))
    # warm light from the window across the tray
    lm = mask(); ImageDraw.Draw(lm).polygon([(450, 920), (760, 920), (1080, 1560), (380, 1560)], fill=150)
    glow(img, lm, (255, 230, 170), .4, blur=40, add=True)
    P.chips_bag(img, 730 + cam, 1515, 1.3, kp, u)
    if kp > .2:                                                 # the air inside pushes out
        import jungle as J
        d = ImageDraw.Draw(img)
        for a in (0.0, math.pi):
            L = 40 + 40 * kp
            x0, y0 = 730 + cam + math.cos(a) * (180 + 50 * kp), 1300
            J.arrow(d, [(x0, y0), (x0 + math.cos(a) * L, y0)], (255, 240, 200), w=18, head=42)
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 600, 1300, vig=(.26, (30, 30, 50)))
    if not HIDE_UI:
        stitle(img, 's14_t', [('LIKE A BAG OF CHIPS', 'white', 92), ('ON A PLANE', (255, 214, 90), 110)], 130, u, cue(2) - .1,
               stagger=cue(7) - cue(2))
        chip(img, 'LESS AIR OUTSIDE', (60, 110, 190), 610, 470, u, cue(12) - .1, size=54)
    hx, hy = g['head']
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 100, W, 520), (540, 1040, 940, 1540)]}


# ---------------------------------------------------------------- s15: NOT BREATHING. THE SKY IS.
def s15(u, D, cue):
    img = Image.new('RGBA', (W, H))
    P.sky(img, 'storm')
    # a slowly turning storm sky: concentric cloud bands around a point
    cx, cy = 540, 520
    lay = layer(); dl = ImageDraw.Draw(lay)
    for i in range(7):
        r = 180 + i * 150
        a0 = u * (10 - i) * 2 + i * 40
        for j in range(3):
            st = a0 + j * 120
            dl.arc([cx - r * 1.2, cy - r * .7, cx + r * 1.2, cy + r * .7], st, st + 80, fill=lerp((70, 60, 110), (150, 130, 190), i / 7) + (235,), width=70)
            dl.arc([cx - r * 1.2, cy - r * .7 - 18, cx + r * 1.2, cy + r * .7 - 18], st + 8, st + 70, fill=lerp((140, 126, 190), (220, 206, 240), i / 7) + (200,), width=18)
    img.alpha_composite(kit.soft_layer(lay, 4))
    kb = .6 + .4 * math.sin(u * 2.5)
    radial(img, cx, cy, 500, (200, 180, 255), .25 + .1 * kb)
    P.air_blanket(img, u, 760, 1380, k=.45 + .25 * math.sin(u * 2.6), n=4, arrows=.0, col=(170, 160, 240))
    P.lightning(img, u, cue(5) - .1, 880, 120, 900, seed=8, dur=.35)
    hole = (540, 1560)
    rc = ((84, 76, 116), (58, 56, 84), (40, 44, 58))
    P.paste_band(img, P.pine_ridge(151, 1400, 110, rc[0], tree=(18, 34), dens=1.2), 0, .2)
    P.paste_band(img, P.pine_ridge(152, 1460, 100, rc[1], tree=(26, 50)), 0, .35)
    gold = P.GOLD_STORM
    P.paste_band(img, P.hill(153, 1520, 26, gold, ink=INK, waves=(.6, 1.6)), 0, .6)
    src = (hole[0], hole[1], 1.4, 1, -math.pi / 2)
    P.grass(img, u, (-60, 1490, W + 60, 1640), 150, 26, 52, cols=gold, seed=154, src=src, clump=(3, 6),
            ytop=lambda x: P.edge_y(153, 1520, 26, x, waves=(.6, 1.6)) + 4)
    P.outcrop(img, hole[0], hole[1], 1.3, seed=3, breath_glow=1.0, t=u, src=src, gold=gold)
    radial(img, 200, 300, 500, (190, 170, 255), .3 + .15 * math.sin(u * 3)); radial(img, 900, 200, 400, (190, 170, 255), .25)
    P.breath(img, u, hole[0], hole[1], ang=-math.pi / 2, sign=1, k=1.2, scale=1.05, n=12, spread=.9, seed=37, Lr=(700, 900),
             Ar=(40, 80), width=24, particles=50)
    gT = brother(img, u, 'tom', dict(POSES['stand'], armL=(30, 20)), 'surprised', 170, 1930, .76, look=.4, hat=False, rim=(200, 190, 255))
    gJ = brother(img, u, 'jesse', dict(POSES['stand'], armR=(-30, -20)), 'surprised', 910, 1920, .74, look=-.4, hat=False, rim=(200, 190, 255),
                 rim_dir=(-1, -.4))
    P.rain(img, u, (0, 0, W, H), n=90, slant=.25, a=110)
    sx, sy = shake(u, cue(3), 10, .35)
    sx2, sy2 = shake(u, cue(5), 12, .4)
    img = finish(img, u, 1.04 - .04 * smooth(u / D), 540, 900, dx=sx + sx2, dy=sy + sy2, vig=(.34, (14, 10, 30)))
    if not HIDE_UI:
        stitle(img, 's15_a', [('NOT BREATHING.', 'white', 116)], 300, u, cue(2) - .1)
        stitle(img, 's15_b', [('THE SKY IS.', KEY, 184)], 470, u, cue(5) - .12)
    return img, {'faces': [face_box(gT, 1.3), face_box(gJ, 1.3)], 'avoid': [(0, 250, W, 760), (300, 1380, 780, 1680), (380, 800, 700, 1380)]}


# ---------------------------------------------------------------- s16a / s16b: the storm rolls over the hills; back to 1881 (loop)
def s16a(u, D, cue):
    """Wide: a storm front rolls over the pine hills (the deck slides in from the left); the little outcrop far off
    breathes out; a cowboy hat tumbles through the foreground grass."""
    cam = -30 * smooth(u / D)
    ks = smooth(seg(u, 0, cue(6)))
    hole = (640 + cam * .6, 1270)
    img = Image.new('RGBA', (W, H))
    P.sky(img, 'fair', H, .45 + .55 * ks, 'storm')
    P.sun(img, 900, 700, 40, u, a=.6 * (1 - ks))
    front = layer()
    P.storm_deck(front, u, 760, seed=51, drift=40, y_top=-300)
    m = mask(); xf = -300 + 1600 * (.45 + .55 * ks)
    ImageDraw.Draw(m).polygon([(-50, -50), (xf, -50), (xf - 260, 1100), (-50, 1100)], fill=255)
    front.putalpha(ImageChops.multiply(front.split()[3], m.filter(ImageFilter.GaussianBlur(50))))
    img.alpha_composite(front)
    P.lightning(img, u, cue(3) - .1, 260, 300, 1000, seed=9, dur=.35)
    P.thunderhead(img, u, 820, 1000, .7, seed=6, alpha=.8, rain_a=.0, cols=((84, 76, 116), (118, 106, 150), (176, 160, 196)))
    rc = ((100, 96, 136), (70, 76, 100), (48, 58, 66))
    P.paste_band(img, P.pine_ridge(161, 1060, 160, rc[0], tree=(18, 34), dens=1.2, haze_col=(150, 140, 170), haze_a=.3), cam, .2)
    P.paste_band(img, P.pine_ridge(162, 1130, 130, rc[1], tree=(26, 50)), cam, .35)
    haze(img, 980, 1200, (150, 136, 170), .3)
    gold = P.GOLD_STORM
    P.paste_band(img, P.hill(163, 1230, 50, gold, ink=INK, waves=(.7, 1.9)), cam, .7)
    k = .8 + .3 * math.sin(u * 3)
    src = (hole[0], hole[1], 1.0 * k, 1, -math.pi / 2 - .3)
    P.grass(img, u, (-60, 1190, W + 60, 1400), 200, 22, 46, cols=gold, seed=164, src=src, clump=(3, 6), wind=.6,
            ytop=lambda x: P.edge_y(163, 1230, 50, x - cam * .7, waves=(.7, 1.9)) + 4)
    P.outcrop(img, hole[0], hole[1], .75, seed=3, breath_glow=1.0, t=u, src=src, gold=gold)
    P.breath(img, u, hole[0], hole[1], ang=-math.pi / 2 - .3, sign=1, k=k, scale=.6, n=8, spread=1.1, seed=41,
             Lr=(700, 950), Ar=(30, 60), width=22, particles=24)
    P.grass(img, u, (-60, 1400, W + 60, 1700), 120, 40, 90, cols=gold, seed=166, src=src, clump=(4, 7), wind=.7)
    # Tom's lost hat tumbling through the grass in the gusts
    v = u / D
    hx, hy = -200 + 1450 * v, 1690 - 110 * abs(math.sin(u * 4.2))
    hm = mask(); ImageDraw.Draw(hm).ellipse([hx - 260, hy - 120, hx + 260, hy + 110], fill=255)
    glow(img, hm, (255, 200, 140), .35, blur=40, add=True)
    P.put_hat(img, P.TOM_HAT, hx, hy, 1.8, angle=-300 * v * 2)
    P.grass(img, u, (-60, 1760, W + 60, 1990), 70, 80, 160, cols=gold, seed=165, src=src, clump=(4, 8), wind=.7, ink=INK)
    P.rain(img, u, (0, 0, W, H), n=int(80 + 140 * ks), slant=.35, a=int(80 + 80 * ks))
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 540, 1200, vig=(.32, (20, 16, 40)))
    if not HIDE_UI:
        stitle(img, 's16a_t', [('EVERY STORM', 'white', 118)], 200, u, cue(2) - .1)
    return img, {'faces': [], 'avoid': [(0, 160, W, 360), (hole[0] - 220, hole[1] - 160, hole[0] + 220, hole[1] + 120), (0, 1500, W, 1900)]}


def s16b(u, D, cue):
    """Present day, the s01 world under the same building storm: close on the little hole breathing out, the camera
    pulls back to the s01 framing; on 'just like in 1881' a gust sweeps across and the brothers are there again:
    the last frame is s01's frame 0 (the loop)."""
    w = u - D                                                     # the s01 world clock meets s01's at the last frame
    t_g = D - 1.5                                                 # gust: hides the brothers' arrival
    kg = math.sin(math.pi * seg(u, t_g, D - .3)) ** 1.1
    if u < t_g + .6:
        cam = 8 * math.sin(w * .45)
        img = prairie_world(w, cam, k_breath=1.15, storm_far=1.0)
        z = 1.0 + 1.1 * (1 - smooth(seg(u, .0, t_g + .5)))
        hx = HOLE[0] + cam * .85
        img = finish(img, w, z, hx, HOLE[1] - 40 - 200 * (z - 1), vig=(.28, (40, 24, 30)))
        if not HIDE_UI:
            chip(img, 'STILL BREATHING', (60, 130, 210), 540, 330, u, cue(11) - .1, size=56)
        info = {'faces': [], 'avoid': [(200, 250, 880, 410), (300, 900, 780, 1320)]}
    else:
        img, info = s01_frame(0.0, w)
    if kg > 0:                                                    # the gust: a wall of breath ribbons sweeping across
        P.breath(img, u, -200, 1500, ang=-.35, sign=1, k=1.6 * kg, scale=2.4, n=16, spread=.9, seed=47, Lr=(900, 1200), Ar=(60, 120),
                 width=40, particles=60, glow_a=.9)
        fill_mask(img, Image.new('L', (W, H), int(255 * .5 * kg ** 2)), (236, 244, 255))
    return img, info


SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [('s01', 1, 0), ('s02', 2, 0), ('s03', 3, 0), ('s04', 4, 0), ('s05a', 5, 0), ('s05b', 5, 7), ('s06', 6, 0),
             ('s07', 7, 0), ('s08a', 8, 0), ('s08b', 8, 8), ('s09', 9, 0), ('s10', 10, 0), ('s11', 11, 0), ('s12', 12, 0),
             ('s13', 13, 0), ('s14', 14, 0), ('s15', 15, 0), ('s16a', 16, 0), ('s16b', 16, 8)]
END = 1945 / 30                 # 64.833 s (length.json); with the 0.1 s cover ~64.93 s
NO_PUNCH = ()
BAND_AT = {}
STILL_AT = {'s01': .02, 's02': .97, 's03': .93, 's04': .95, 's05a': .95, 's05b': .97, 's06': .66, 's07': .97, 's08a': .9,
            's08b': .97, 's09': .9, 's10': .95, 's11': .97, 's12': .95, 's13': .97, 's14': .95, 's15': .97, 's16a': .55, 's16b': .45}

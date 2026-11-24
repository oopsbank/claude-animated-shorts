"""Flamingo one leg (video 10, "Why Do Flamingos Stand on One Leg?"): shots as `sNN(u, D, cue) -> (img, info)`.

Same contract as zebra_stripes.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the
shot's voice-over LINE. info: 'faces' (face boxes) and 'avoid' (boxes the caption must not cover).
Hero image: the 2017 study flamingo standing on one leg in a lab clamp, the muscle monitor FLAT. Colour motif:
flamingo pink against teal water / the warm lab. The mechanism (s09-s11) on a warm paper diagram stage: the weight
arrow straight down the leg, the hip and knee turning until they hit their stop, gravity locks it, the muscle meter
barely moves. Serious tone, no comedy. Every shot keeps moving.

Render: .venv/bin/python flat2d/render.py audio/flamingo-one-leg/words.json OUT.mp4 --film flamingo_one_leg --size 540x960
"""
import math, os, sys, re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import kit, anim
import flamingo as FL
import lagoon as LG
from kit import W, H, INK, vgrad, radial, dust, label, title, font, mask, glow, fill_mask, layer, lerp, rgb
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES, mix, add, damp
from blood_falls import finish, slam_title, face_box
from blood_falls_2 import put_chip, draw_x
import tunguska as TG
from tunguska import chip_t, flash

SLUG = 'flamingo-one-leg'
HIDE_UI = False
KEY = (255, 210, 63)
PINK = (255, 120, 158)
SCI_COL = (196, 70, 100)
SCI_A = dict(coat='#f2f1ec', shirt='#6d8fb8', pants='#44506a')
SCI_B = dict(coat='#f2f1ec', shirt='#c8805a', pants='#5a4a44', hair=('tuft', '#5a4436'))
PERSON = dict(shirt='#e0703c', pants='#3e5578')
ONE_LEG = dict(armL=(80, 70), armR=(-80, -70), legL=(6, 1), legR=(-55, -150))


def q(v, step):
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


def sci(img, t, who, pose, expr, cx, gy, s, look=0.0, lean=0.0, label_on=False, lbl='SCIENTIST', rim=(255, 226, 180),
        rim_dir=(-1, -.5), bphase=0.0, aura=(255, 226, 180), aura_a=.25, kw=None):
    kw = kw or (SCI_A if who == 'A' else SCI_B if who == 'B' else PERSON)
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, aura=aura, aura_alpha=aura_a, rim=rim, rim_dir=rim_dir,
              rim_w=12, bphase=bphase + (0 if who == 'A' else .9), **kw)
    if label_on and not HIDE_UI:
        hx, hy = g['head']
        label(img, lbl, min(W - 170, max(170, hx)), hy - g['R'] * 1.9 - 86, SCI_COL if who != 'P' else (60, 110, 170),
              size=int(44 * max(.9, min(1.1, s / .6))))
    return g


def idle(w, ph=0.0, awake=True):
    """Idle pose values for a bird (quantised: layers are cached by pose)."""
    p = {'breath': q(.5 + .5 * math.sin(w * 2.0 + ph), .25)}
    if awake:
        p['sway'] = q(.05 * math.sin(w * .7 + ph), .01)
        p['nod'] = q(.06 * math.sin(w * .5 + ph * 2), .02)
    return p


# ---------------------------------------------------------------- UI helpers
def arrow(img, p0, p1, w, col, head=2.4, ink=8, alpha=255):
    """A thick arrow p0 -> p1 with an ink outline."""
    x0, y0 = p0; x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 4: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux
    hl = min(L * .45, w * head)
    bx, by = x1 - ux * hl, y1 - uy * hl
    pts = [(x0 + nx * w / 2, y0 + ny * w / 2), (bx + nx * w / 2, by + ny * w / 2), (bx + nx * w * 1.2, by + ny * w * 1.2), (x1, y1),
           (bx - nx * w * 1.2, by - ny * w * 1.2), (bx - nx * w / 2, by - ny * w / 2), (x0 - nx * w / 2, y0 - ny * w / 2)]
    lay = layer(); d = ImageDraw.Draw(lay)
    d.polygon(pts, fill=INK + (alpha,))
    d.line(pts + [pts[0]], fill=INK + (alpha,), width=ink * 2, joint='curve')
    d.polygon(pts, fill=rgb(col) + (alpha,))
    d.line([(x0 + nx * w * .25, y0 + ny * w * .25), (bx + nx * w * .25, by + ny * w * .25)], fill=lerp(rgb(col), (255, 255, 255), .45) + (alpha,), width=max(2, int(w * .15)))
    img.alpha_composite(lay)


def dashed(img, p0, p1, col=(255, 255, 255), w=6, dash=26, gap=16, phase=0.0, ink=True):
    d = ImageDraw.Draw(img)
    L = math.dist(p0, p1)
    if L < 1: return
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    s = -((phase * 40) % (dash + gap))
    while s < L:
        a, b = max(0, s), min(L, s + dash)
        if b > a:
            A = (p0[0] + ux * a, p0[1] + uy * a); B = (p0[0] + ux * b, p0[1] + uy * b)
            if ink: d.line([A, B], fill=INK, width=w + 6)
            d.line([A, B], fill=col, width=w)
        s += dash + gap


def dot(img, x, y, r, col, ink=True):
    d = ImageDraw.Draw(img)
    if ink: d.ellipse([x - r - 5, y - r - 5, x + r + 5, y + r + 5], fill=INK)
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def check_mark(img, x, y, r, k, col=(70, 190, 100)):
    if k <= 0: return
    d = ImageDraw.Draw(img)
    a, b, c = (x - r, y), (x - r * .3, y + r * .7), (x + r, y - r * .8)
    f = min(1, k * 2)
    pts = [a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]
    if k > .5:
        g = (k - .5) * 2; pts = [a, b, (b[0] + (c[0] - b[0]) * g, b[1] + (c[1] - b[1]) * g)]
    d.line(pts, fill=INK, width=int(r * .42), joint='curve'); d.line(pts, fill=col, width=int(r * .27), joint='curve')


def qmark(img, x, y, s, u, t0, col=(255, 255, 255)):
    k = pop(u, t0, .3)
    if k <= 0 or HIDE_UI: return
    lay = layer(260, 300); d = ImageDraw.Draw(lay)
    d.text((130, 150), '?', font=font(220), fill=col, anchor='mm', stroke_width=12, stroke_fill=INK)
    anim.scaled_paste(img, lay, x, y + 6 * math.sin(u * 3), k * s, angle=8 * math.sin(u * 2))


def meter(img, x, y, h, v, lbl='MUSCLE EFFORT', w=90, col=None):
    """A vertical effort meter (v 0..1) with a label above."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - w / 2 - 8, y - h - 8, x + w / 2 + 8, y + 8], 26, fill=INK)
    d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], 20, fill=(60, 64, 80))
    for i in range(1, 5):
        yy = y - h * i / 5; d.line([(x - w / 2 + 10, yy), (x + w / 2 - 10, yy)], fill=(90, 96, 112), width=3)
    col = col or lerp((90, 200, 120), (240, 80, 60), v)
    hh = max(18, h * v)
    d.rounded_rectangle([x - w / 2 + 8, y - hh, x + w / 2 - 8, y - 8], 14, fill=col)
    lay, _ = TG_text(lbl, 40)
    anim.scaled_paste(img, lay, x, y - h - 50, 1.0)


_txt = {}
def TG_text(txt, size, col='white'):
    k = (txt, size, col)
    if k not in _txt:
        _txt[k] = anim.text_layer(lambda l: ImageDraw.Draw(l).text((540, 100), txt, font=font(size), fill=col, anchor='mm',
                                                                   stroke_width=max(4, size // 9), stroke_fill=INK), W, 200)
    return _txt[k]


def tag(img, txt, x, y, size=44, col='white', s=1.0):
    if HIDE_UI or s <= .01: return
    lay, _ = TG_text(txt, size, col); anim.scaled_paste(img, lay, x, y, s)


_tl = {}
def tlayer(key, lines, size):
    if key not in _tl:
        _tl[key] = anim.text_layer(lambda l: title(l, lines, 60, size=size), W,
                                   int(sum((x[2] if len(x) > 2 else size) for x in lines) * 1.3 + 140))
    return _tl[key]


def opening_title(img, u, k=1.0, t_pop=None):
    if HIDE_UI: return
    s = 1.0 + .006 * math.sin(u * 2.4)
    if t_pop is not None and t_pop <= u < t_pop + .3: s = max(s, slam(u, t_pop, .3, 1.12))
    lay, _ = tlayer('open', [('2017', KEY, 230)], 230)
    anim.scaled_paste(img, lay, 540, 250, s * k)
    put_chip(img, 'ATLANTA', (196, 70, 100), 540, 420, k, size=60)


# ---------------------------------------------------------------- the 2017 lab scene (s01, s12, s15)
SPEC_X, SPEC_GY, SPEC_S = 560, 1470, 960


def specimen(img, w, x, gy, s, face=1, pose=None, clamp=True, plate=True):
    """The 2017 study bird: whole, clean, eyes closed, standing on one leg; its lower leg held in a padded clamp on
    an aluminium strut, the foot on a force plate."""
    pose = dict({'sleep': 1.0, 'fold': 1.0, 'fx': 0.0, 'breath': .5}, **(pose or {}))
    cy = gy - .17 * s
    if plate or clamp:
        d = ImageDraw.Draw(img)
        # force plate
        d.rounded_rectangle([x - .36 * s, gy - 6, x + .36 * s, gy + 40], 10, fill=(120, 130, 146), outline=INK, width=5)
        d.rectangle([x - .34 * s, gy - 6, x + .34 * s, gy + 6], fill=(206, 214, 226))
        if not HIDE_UI: d.text((x + face * .2 * s, gy + 24), 'FORCE PLATE', font=font(22, True), fill=(236, 240, 246), anchor='mm')
        # strut behind the leg
        sx = x - face * .2 * s
        d.rectangle([sx - 15, cy - 30, sx + 15, gy - 6], fill=(196, 204, 216), outline=INK, width=5)
        d.line([(sx - 5, cy - 20), (sx - 5, gy - 12)], fill=(240, 244, 250), width=4)
        d.rectangle([sx - 40, gy - 30, sx + 40, gy - 4], fill=(150, 160, 176), outline=INK, width=4)
    contact = mask(); ImageDraw.Draw(contact).ellipse([x - .25 * s, gy - 10, x + .3 * s, gy + 12], fill=255)
    fill_mask(img, contact, (60, 40, 40), .3, blur=10)
    info = FL.put(img, x, gy, s, face=face, kind='specimen', pose=pose, light=(-.6 * face if face > 0 else .6, -1.0))
    if clamp:
        d = ImageDraw.Draw(img)
        ax, ay = info['ankle']; fx_, fy_ = info['foot']
        k = (cy - ay) / max(1, fy_ - ay)
        lx = ax + (fx_ - ax) * k
        sx = x - face * .2 * s
        d.rectangle([min(sx, lx), cy - 11, max(sx, lx), cy + 11], fill=(176, 184, 198), outline=INK, width=4)
        LG.clamp(img, lx, cy, s / 900)
    return info


def lab_scene(w, cam=0.0, k_flat=1.0, pose=None, chars=True, mon=True, sci_pose=None):
    img = Image.new('RGBA', (W, H))
    LG.lab(img, w, cam)
    LG.bench(img, 700, 1300, 1160, cam * .9)
    G = {}
    if mon:
        LG.monitor(img, 880 + cam * .9, 960, 300, 210, w, k_flat=k_flat, label='MUSCLE ACTIVITY')
    info = specimen(img, w, SPEC_X + cam, SPEC_GY, SPEC_S, pose=pose)
    if chars:
        G['a'] = sci(img, w, 'A', dict(POSES['stand'], armR=(-60, -100)), 'thinking', 150 + cam * 1.2, 1990, .5, look=.5)
        G['b'] = sci(img, w, 'B', 'hold', 'neutral', 950 + cam * 1.2, 2010, .5, look=-.55, bphase=.4)
    return img, info, G


def s01_frame(u, w, cue=None):
    cue = cue or (lambda i: [0, .23, .76, 1.4, 1.6, 2.1, 2.6, 2.75, 3.0, 3.4, 3.55, 3.75][min(i, 11)])
    cam = 8 * math.sin(w * .45)
    img, info, G = lab_scene(w, cam)
    z = 1.0 + .04 * smooth(u / 6)
    img = finish(img, w, z, 540, 1150, vig=(.26, (50, 30, 30)))
    if not HIDE_UI:
        opening_title(img, u, t_pop=cue(1))
        put_chip(img, 'MUSCLES: OFF', (40, 40, 48), 880, 760, 1.0 if u == 0 else max(pop(u, cue(8) - .1, .3), 0), size=44)
    faces = [face_box(G['a'], 1.3), face_box(G['b'], 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 120, W, 500)]}


def s01(u, D, cue):
    return s01_frame(u, u, cue)


def s01b(u, D, cue):
    """Close: the specimen's leg in the clamp and the FLAT muscle line, big."""
    w = u + 4
    img = Image.new('RGBA', (W, H))
    LG.lab(img, w, -60)
    LG.bench(img, 600, 1400, 1120, 0)
    k_settle = smooth(seg(u, cue(13) - .3, cue(13) + .25))
    drop = .02 * (1 - k_settle) - .005 * damp(max(0, u - cue(13)), 1, 7, 18)
    info = specimen(img, w, 330, 1700, 1250, pose={'drop': q(-.02 + drop * 1.0, .002) if u < cue(13) + 1 else 0.0})
    LG.monitor(img, 790, 620, 480, 330, w, k_flat=1.0, label='MUSCLE ACTIVITY')
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.26, (50, 30, 30)))
    if not HIDE_UI:
        chip(img, 'HOLDS THE POSE', (60, 140, 110), 360, 230, u, cue(13) - .05, size=50)
        chip(img, 'MUSCLES: OFF', (40, 40, 48), 790, 900, u, cue(17) - .1, size=54)
        if u > cue(18):
            tag(img, 'FLAT LINE', 790, 1000, 40, KEY, pop(u, cue(18), .3))
    return img, {'faces': [], 'avoid': [(500, 400, 1080, 1060), (120, 160, 620, 300)]}


# ---------------------------------------------------------------- s02: live flamingos, hours, even asleep
def clock_chip(img, x, y, u, t0, txt='HOURS'):
    k = pop(u, t0, .3)
    if k <= 0 or HIDE_UI: return
    lay = layer(420, 160); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([6, 14, 414, 154], 70, fill=INK)
    d.rounded_rectangle([0, 6, 408, 146], 70, fill=(60, 120, 170), outline=INK, width=6)
    cx, cy, r = 76, 76, 50
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 248, 240), outline=INK, width=6)
    a = u * 4.0; b = u * .33
    d.line([(cx, cy), (cx + math.sin(a) * r * .75, cy - math.cos(a) * r * .75)], fill=INK, width=6)
    d.line([(cx, cy), (cx + math.sin(b) * r * .5, cy - math.cos(b) * r * .5)], fill=INK, width=8)
    d.text((270, 76), txt, font=font(64), fill='white', anchor='mm', stroke_width=5, stroke_fill=INK)
    anim.scaled_paste(img, lay, x, y, k)


def s02(u, D, cue):
    w = u + 10
    cam = -30 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    wc = LG.lagoon(img, w, cam, 'dawn', horizon=960, sun=(780, 900))
    for x, gy, s, ph, f in ((900, 1150, 300, 1.3, 1), (230, 1300, 470, 2.0, 1)):
        FL.put(img, x + cam * .7, gy, s, face=f, pose=dict(idle(w, ph, False), sleep=1), water=gy - 6, reflect=.5, water_col=wc, t=w)
        FL.ripples(img, x + cam * .7, gy - 4, s * .18, w + ph)
    ks = smooth(seg(u, cue(7) - .3, cue(8) + .2))
    p = dict(idle(w, .2, ks < .5), sleep=q(ks, .05), eye=1 - ks)
    bx = 640 + cam
    FL.put(img, bx, 1720, 820, face=-1, pose=p, water=1712, reflect=.5, water_col=wc, t=w)
    FL.ripples(img, bx, 1716, 140, w)
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1300, vig=(.26, (60, 30, 60)))
    if not HIDE_UI:
        clock_chip(img, 540, 330, u, cue(5) - .15)
        chip(img, 'EVEN ASLEEP', (120, 80, 150), 540, 490, u, cue(7) - .1, size=56)
    return img, {'faces': [], 'avoid': [(200, 230, 880, 560)]}


# ---------------------------------------------------------------- s03: the usual answer (thermal view)
THERM = [(0, (16, 8, 50)), (.28, (70, 20, 140)), (.48, (190, 40, 130)), (.66, (250, 110, 40)), (.84, (255, 214, 70)), (1, (255, 252, 220))]
_tp = {}
def therm_lut():
    if 'l' not in _tp:
        xs = np.linspace(0, 1, 256)
        ts = [a for a, _ in THERM]; cs = np.array([c for _, c in THERM], np.float32)
        _tp['l'] = np.stack([np.interp(xs, ts, cs[:, i]) for i in range(3)], 1).astype(np.uint8)
    return _tp['l']


def s03(u, D, cue):
    """Thermal-camera view: the body glows warm, the standing leg is cool; as the leg tucks up into the feathers
    its foot warms up."""
    w = u + 20
    kf = smooth(seg(u, cue(3) - .2, cue(5) + .1))
    img = Image.new('RGBA', (W, H))
    bg = vgrad([(0, (30, 14, 70)), (.6, (40, 20, 90)), (1, (24, 10, 60))])
    img.alpha_composite(bg)
    # water band (cold)
    d = ImageDraw.Draw(img)
    for i in range(40):
        y = 1500 + i * 12
        d.line([(0, y), (W, y)], fill=(30 + i, 20, 100 + i), width=8)
    tmp = Image.new('RGBA', (W, H))
    s = 1250; bx, gy = 560, 2020
    info = FL.put(tmp, bx, gy, s, face=1, pose=dict(idle(w, .5, True), fold=q(kf, .05), fx=.03, fx2=-.09))
    a = np.asarray(tmp, np.float32)
    L = a[..., :3].mean(-1) / 255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = info['center']; bel = info['belly'][1]
    v = np.clip(.95 - np.hypot((xx - cx) / (s * .55), (yy - cy) / (s * .35)) * .45, 0, 1)
    v = np.where(yy > bel + 20, .22 + .05 * np.clip((bel + 200 - yy) / 200, 0, 1), v)
    # the tucked foot warms up inside the feathers
    ffx, ffy = info['far_foot']
    hot = np.clip(1 - np.hypot(xx - ffx, yy - ffy) / 170, 0, 1) * kf
    v = np.maximum(v, .2 + .75 * hot)
    v = v * (.55 + .45 * np.clip(L * 1.3, 0, 1))
    lut = therm_lut()
    col = lut[(np.clip(v, 0, 1) * 255).astype(np.uint8)].astype(np.float32)
    col *= np.clip(L * 2.5, 0, 1)[..., None] * .4 + .6
    out = np.dstack([col, a[..., 3]]).clip(0, 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(out, 'RGBA'))
    # heat shimmer rings around the tucked foot
    if kf > .3:
        for i in range(3):
            k = ((w * .7) + i / 3) % 1
            r = 60 + 200 * k
            m = mask(); ImageDraw.Draw(m).ellipse([ffx - r, ffy - r * .8, ffx + r, ffy + r * .8], outline=255, width=6)
            fill_mask(img, m, (255, 200, 90), .5 * (1 - k) * kf, blur=3)
    # camera HUD
    d = ImageDraw.Draw(img)
    for (x0, y0, sx, sy) in ((60, 140, 1, 1), (W - 60, 140, -1, 1), (60, 1820, 1, -1), (W - 60, 1820, -1, -1)):
        d.line([(x0, y0), (x0 + sx * 90, y0)], fill=(240, 240, 255), width=6)
        d.line([(x0, y0), (x0, y0 + sy * 90)], fill=(240, 240, 255), width=6)
    bar = vgrad([(0, THERM[-1][1]), (.25, THERM[-2][1]), (.5, THERM[-3][1]), (.75, THERM[-4][1]), (1, THERM[1][1])], 34, 520)
    img.paste(bar, (W - 110, 620)); d.rectangle([W - 112, 618, W - 74, 1142], outline=(240, 240, 255), width=4)
    d.text((W - 92, 590), 'WARM', font=font(30, True), fill=(255, 240, 200), anchor='mb')
    d.text((W - 92, 1176), 'COLD', font=font(30, True), fill=(190, 190, 255), anchor='mt')
    d.ellipse([86, 176, 110, 200], fill=(255, 60, 60) if int(w * 2) % 2 else (120, 30, 30))
    d.text((124, 188), 'THERMAL CAMERA', font=font(32, True), fill=(240, 240, 255), anchor='lm')
    img = finish(img, w, 1.0 + .04 * smooth(u / D), 540, 1200, vig=(.3, (10, 0, 30)))
    if not HIDE_UI:
        chip(img, 'WARMTH?', (220, 110, 40), 540, 330, u, cue(2) - .15, size=64)
        if kf > .5: tag(img, 'TUCKED IN: WARM', ffx - 40, ffy - 230, 40, (255, 236, 160), pop(u, cue(5) + .1, .3))
        tag(img, 'LEG IN WATER: COLD', 360, 1740, 40, (200, 200, 255), pop(u, cue(8) - .2, .3))
    return img, {'faces': [], 'avoid': [(260, 260, 820, 400)]}


# ---------------------------------------------------------------- s04: why, not how / s04b: you on one leg
def s04(u, D, cue):
    w = u + 30
    cam = 24 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    wc = LG.lagoon(img, w, cam, 'morning', horizon=1040, sun=(250, 700), flock_n=18)
    LG.reeds(img, w, -40, 300, 1240, 30, 60, 160, seed=2, col=(70, 100, 90), tip=(150, 130, 90), cam=cam * .8)
    bx = 560 + cam
    info = FL.put(img, bx, 1640, 840, face=1, pose=dict(idle(w, 1.1, True), fold=1), water=1632, reflect=.5, water_col=wc, t=w)
    FL.ripples(img, info['foot'][0], 1636, 130, w)
    LG.reeds(img, w, 700, 1140, 1900, 26, 120, 300, seed=4, col=(50, 80, 70), tip=(130, 110, 70), cam=cam * 1.4)
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1200, vig=(.24, (20, 40, 70)))
    if not HIDE_UI:
        chip(img, 'WHY: WARMTH', (60, 150, 110), 330, 300, u, cue(3) - .1, size=52)
        check_mark(img, 600, 300, 44, seg(u, cue(3) + .1, cue(3) + .4))
        stitle(img, 's04_t', [('HOW?', KEY, 220)], 400, u, cue(7) - .1)
        if u > cue(7): qmark(img, info['knee'][0] + 170, info['ankle'][1] - 20, .8, u, cue(7) + .15, KEY)
    return img, {'faces': [], 'avoid': [(100, 220, 980, 700)]}


def s04b(u, D, cue):
    """You, on one leg with your eyes closed, wobble within seconds."""
    w = u + 40
    img = Image.new('RGBA', (W, H))
    LG.room(img, w, -20 * smooth(u / D))
    tw = cue(18) - .2
    amp = 3 + 10 * smooth(seg(u, .3, tw)) + 6 * smooth(seg(u, tw, tw + .4))
    lean = amp * math.sin(u * 3.4) + 4 * math.sin(u * 7.1) * smooth(seg(u, tw, tw + .3))
    pose = add(dict(ONE_LEG), armL=(10 * math.sin(u * 3.4 + 1), 15 * math.sin(u * 3.4)), armR=(-10 * math.sin(u * 3.4 + 1.5), -15 * math.sin(u * 3.4 + .5)))
    g = actor(img, 'blink', pose, 560, 1700, .85, w, lean=lean, blink_ok=False, aura=(255, 210, 150), aura_alpha=.25,
              rim=(255, 210, 150), rim_dir=(-1, -.4), rim_w=12, idle=0.4, **PERSON)
    hx, hy = g['head']
    # sway arcs over the head
    if u > .6:
        a = min(1, (u - .6) / .5)
        lay = layer(); dl = ImageDraw.Draw(lay)
        r = 150 + 4 * amp
        for k, col in ((0, (255, 255, 255)), (1, (255, 200, 120))):
            rr = r + k * 50
            dl.arc([hx - rr, hy - rr * .6 + 40, hx + rr, hy + rr * .6 + 40], 200, 340, fill=INK + (int(220 * a),), width=16)
            dl.arc([hx - rr, hy - rr * .6 + 40, hx + rr, hy + rr * .6 + 40], 200, 340, fill=col + (int(255 * a),), width=8)
        img.alpha_composite(lay)
    if u > tw:
        k = (u - tw) % 1.0
        d = ImageDraw.Draw(img)
        sx, sy = hx + 110, hy - 40 + 60 * k
        d.ellipse([sx - 14, sy - 10, sx + 14, sy + 22], fill=(140, 200, 255), outline=INK, width=4)
    img = finish(img, w, 1.03 + .03 * smooth(u / D), 560, 1200, vig=(.3, (30, 20, 50)))
    if not HIDE_UI:
        lbl_k = pop(u, .05, .3)
        if lbl_k > 0: put_chip(img, 'YOU', (60, 110, 170), hx, hy - 220, lbl_k, size=50)
        chip(img, 'EYES CLOSED', (90, 80, 130), 540, 300, u, cue(14) - .1, size=52)
        secs = max(0, int((u - cue(8)) / ((cue(20) - cue(8)) / 3)) + 1) if u > cue(8) else 0
        if secs:
            tag(img, f'0:0{min(3, secs)}', 880, 470, 70, (255, 236, 160))
        chip(img, 'WOBBLE!', (230, 80, 60), 560, 470, u, tw, size=56, angle=-4)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(200, 220, 980, 540)]}


# ---------------------------------------------------------------- s05: CLUE 1 the ankle (x-ray)
def xray_bird(img, info_layer, a=.45, col=(110, 190, 240)):
    lay, ox, oy = info_layer
    al = np.asarray(lay.split()[3], np.float32)
    L = np.asarray(lay.convert('L'), np.float32)
    edge = np.clip((255 - L) / 255, 0, 1)
    rgbv = np.array(col, np.float32)[None, None] * (.55 + .45 * edge[..., None])
    alpha = al * (a + .4 * edge)
    out = Image.fromarray(np.dstack([rgbv, alpha]).clip(0, 255).astype(np.uint8), 'RGBA')
    FL._paste(img, out, ox, oy)


def bone(img, p0, p1, w, glow_a=.5, col=(236, 246, 255)):
    m = mask(); ImageDraw.Draw(m).line([p0, p1], fill=255, width=int(w * 1.8))
    glow(img, m, (120, 200, 255), glow_a, blur=18)
    d = ImageDraw.Draw(img)
    d.line([p0, p1], fill=(40, 70, 110), width=int(w + 6))
    d.line([p0, p1], fill=col, width=int(w))
    for p in (p0, p1):
        d.ellipse([p[0] - w * .75, p[1] - w * .75, p[0] + w * .75, p[1] + w * .75], fill=col, outline=(40, 70, 110), width=3)


def joint(img, p, r, col, k=1.0, pulse=0.0):
    if k <= 0: return
    rr = r * (1 + .15 * pulse)
    m = mask(); ImageDraw.Draw(m).ellipse([p[0] - rr * 2, p[1] - rr * 2, p[0] + rr * 2, p[1] + rr * 2], fill=255)
    glow(img, m, col, .6 * k, blur=24)
    d = ImageDraw.Draw(img)
    d.ellipse([p[0] - rr - 5, p[1] - rr - 5, p[0] + rr + 5, p[1] + rr + 5], fill=INK)
    d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=col)


def clue1_scene(w, u, cue, focus_knee=0.0):
    img = Image.new('RGBA', (W, H))
    LG.stage(img, w, 'xray')
    s = 1000; bx, gy = 650, 1780
    tmp = Image.new('RGBA', (W, H))
    info = FL.put(tmp, bx, gy, s, face=1, pose=dict(idle(w, .3, True), fold=1), ret_layer=True)
    xray_bird(img, info['layer'])
    K, A, F = info['knee'], info['ankle'], info['foot']
    hip = (bx - .05 * s, gy - .70 * s)
    bone(img, hip, K, 26)
    bone(img, K, A, 20); bone(img, A, F, 16)
    for dx, dy in ((.10, 0.0), (.085, .006), (.06, .007)):
        bone(img, F, (F[0] + dx * s, F[1] + dy * s - 4), 9, .3)
    # pelvis + spine hint
    d = ImageDraw.Draw(img)
    d.line([(bx - .25 * s, gy - .72 * s), (bx + .12 * s, gy - .74 * s)], fill=(200, 226, 255), width=10)
    # the ghost human leg (left), for comparison
    hx = 230
    Hh, Hk, Ha, Hf = (hx, 900), (hx + 30, 1330), (hx, 1730), (hx + 120, 1770)
    ga = .55
    lay = layer(); dl = ImageDraw.Draw(lay)
    dl.polygon([(hx - 70, 880), (hx + 70, 880), (hx + 80, 1320), (hx + 50, 1720), (hx + 150, 1760), (hx + 150, 1790), (hx - 50, 1790), (hx - 40, 1720), (hx - 30, 1340)],
               fill=(240, 230, 255, 50), outline=(220, 210, 255, 140))
    img.alpha_composite(lay)
    for a_, b_, ww in ((Hh, Hk, 28), (Hk, Ha, 22), (Ha, Hf, 14)):
        bone(img, a_, b_, ww, .25, col=(214, 206, 236))
    k_knee = pop(u, cue(13) - .1, .3)
    k_ank = pop(u, cue(16) - .1, .3)
    k_hk = pop(u, cue(18) - .1, .3)
    joint(img, A, 22, (255, 210, 63), max(k_ank, .0) if u > cue(16) - .1 else 0, math.sin(w * 5) * .5)
    joint(img, Hk, 18, (200, 190, 240), .8 if u > cue(13) - .1 else 0)
    joint(img, Ha, 18, (255, 210, 63), .9 if u > cue(16) - .1 else 0)
    joint(img, K, 22, (120, 255, 170), k_hk, math.sin(w * 5) * .5)
    if u > cue(16) + .1:
        dashed(img, (A[0] - 30, A[1] + 10), (Ha[0] + 34, Ha[1] - 10), col=(255, 210, 63), w=5, phase=w)
    return img, info, (K, A, F, Hk, Ha)


def s05(u, D, cue):
    w = u + 50
    img, info, (K, A, F, Hk, Ha) = clue1_scene(w, u, cue)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1300, vig=(.3, (0, 10, 30)))
    if not HIDE_UI:
        clue(img, 'CLUE 1', u, .05, 230)
        tag(img, 'YOUR LEG', 230, 820, 40, (220, 210, 255), pop(u, .3, .3))
        chip(img, 'NOT A KNEE', (120, 110, 170), A[0] + 150, A[1] - 120, u, cue(13) - .1, size=46)
        if u > cue(13) + .3 and u < cue(16): draw_x(img, A[0] + 150, A[1] - 120, 50, (u - cue(13) - .3) / .15, w=14)
        chip(img, 'ANKLE', (230, 160, 30), A[0] + 150, A[1] + 10, u, cue(16) - .1, size=60)
        tag(img, 'KNEE', Hk[0] + 110, Hk[1], 40, (220, 210, 255), pop(u, cue(13) - .1, .3))
        tag(img, 'ANKLE', Ha[0] + 120, Ha[1] - 70, 40, KEY, pop(u, cue(16), .3))
    return img, {'faces': [], 'avoid': [(300, 150, 780, 320)]}


def s05b(u, D, cue):
    """Push up to the body: the real knee, hidden in the feathers, close to the body."""
    w = u + 55
    cu = lambda i: cue(i) if i >= 17 else -1.0
    img, info, (K, A, F, Hk, Ha) = clue1_scene(w, D + 10, lambda i: -5.0)
    k = smooth(seg(u, 0, .9))
    z = 1.0 + .7 * k
    fx, fy = 540 + (K[0] - 540) * k, 1300 + (K[1] - 40 - 1300) * k
    # the knee pulses
    joint(img, K, 26, (120, 255, 170), 1.0, math.sin(w * 6))
    img = finish(img, w, z, fx, fy, vig=(.3, (0, 10, 30)))
    if not HIDE_UI:
        chip(img, 'THE KNEE', (60, 170, 110), 540, 560, u, cue(18) - .1, size=64)
        chip(img, 'HIDDEN IN THE FEATHERS', (40, 60, 90), 540, 700, u, cue(22) - .1, size=46)
    return img, {'faces': [], 'avoid': [(120, 480, 960, 760)]}


# ---------------------------------------------------------------- s06: CLUE 2 the foot under the middle
def s06(u, D, cue):
    w = u + 60
    img = Image.new('RGBA', (W, H))
    wc = LG.lagoon(img, w, 0, 'golden', horizon=900, sun=(300, 860), flock_n=14)
    t_lift0, t_lift1 = cue(2) - .2, cue(4) + .2
    t_mv0, t_mv1 = cue(7) - .1, cue(9) + .2
    kl = smooth(seg(u, t_lift0, t_lift1)); km = smooth(seg(u, t_mv0, t_mv1))
    fx = q(.10 * (1 - km), .005)
    pose = dict(idle(w, .7, True), fold=q(kl, .05), fx=fx, fx2=-.08)
    bx, gy, s = 520, 1700, 1000
    # the body glides over the foot: keep the body still and slide the foot (bird space), so shift x by the foot
    info = FL.put(img, bx, gy, s, face=1, pose=pose, water=gy - 8, reflect=.5, water_col=wc, t=w)
    FL.ripples(img, info['foot'][0], gy - 4, 150, w)
    cx, cy = info['center']
    if u > t_mv0 - .4:
        a = smooth(seg(u, t_mv0 - .4, t_mv0))
        dashed(img, (cx, cy), (cx, gy + 30), col=(255, 255, 255), w=6, phase=w)
        dot(img, cx, cy, 16, (255, 210, 63))
        if km > .05 and km < .98:
            fx0 = info['foot'][0]
            arrow(img, (fx0 + 120, gy + 60), (fx0 + 20, gy + 60), 26, (255, 210, 63))
    img = finish(img, w, 1.02 + .02 * smooth(u / D), 540, 1300, vig=(.26, (60, 30, 40)))
    if not HIDE_UI:
        clue(img, 'CLUE 2', u, .05, 230)
        chip(img, 'ONE LEG', (196, 70, 100), 300, 420, u, cue(4) - .1, size=52)
        chip(img, 'FOOT UNDER THE MIDDLE', (40, 40, 48), 540, 560, u, cue(14) - .1, size=48)
        if km > .97: dot(img, cx, gy + 2, 14, (120, 255, 170))
    return img, {'faces': [], 'avoid': [(160, 150, 920, 620)]}


# ---------------------------------------------------------------- s07: CLUE 3 Zoo Atlanta, sway trace
def trace_panel(img, x, y, w, h, u, k_closed, t):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - w / 2 - 14, y - h / 2 - 14, x + w / 2 + 14, y + h / 2 + 14], 22, fill=(60, 64, 76), outline=INK, width=6)
    d.rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], fill=(16, 26, 34))
    d.text((x - w / 2 + 16, y - h / 2 + 12), 'BODY SWAY', font=font(32, True), fill=(255, 236, 200), anchor='lt')
    rows = (('ALERT', y - h * .12, 1.0, (255, 150, 90)), ('EYES CLOSED', y + h * .28, .12, (120, 255, 170)))
    for i, (lbl, yy, amp, col) in enumerate(rows):
        n = 90
        show = 1.0 if i == 0 else k_closed
        if show <= 0: continue
        pts = []
        for j in range(int(n * show) + 1):
            xx = x - w / 2 + 20 + (w - 40) * j / n
            ph = j * .35 + t * 2
            pts.append((xx, yy + amp * h * .12 * (math.sin(ph) + .6 * math.sin(ph * 2.7 + 1) + .3 * math.sin(ph * 5.3))))
        if len(pts) > 1:
            m = mask(); ImageDraw.Draw(m).line(pts, fill=255, width=10); glow(img, m, col, .5, blur=8)
            d.line(pts, fill=col, width=4)
        d.text((x - w / 2 + 20, yy - h * .2), lbl, font=font(28, True), fill=col, anchor='lm')


def s07(u, D, cue):
    w = u + 70
    cam = -20 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    LG.zoo(img, w, cam)
    kc = smooth(seg(u, cue(8) - .3, cue(10) + .1))
    sway = (1 - kc) * 3.0 * math.sin(w * 5.3) + (1 - kc) * 2 * math.sin(w * 8.1)
    bx, gy = 400 + cam, 1560
    d = ImageDraw.Draw(img)
    d.polygon([(bx - 260, gy - 20), (bx + 300, gy - 20), (bx + 340, gy + 50), (bx - 300, gy + 50)], fill=(140, 150, 164), outline=INK)
    d.polygon([(bx - 260, gy - 20), (bx + 300, gy - 20), (bx + 290, gy - 6), (bx - 250, gy - 6)], fill=(210, 216, 226))
    if not HIDE_UI: d.text((bx + 20, gy + 26), 'FORCE PLATE', font=font(24, True), fill=(240, 244, 250), anchor='mm')
    FL.put(img, bx, gy - 10, 760, face=1, kind='juv',
           pose=dict(breath=q(.5 + .5 * math.sin(w * 2), .25), tilt=q(sway, .5), sway=q(.05 * (1 - kc) * math.sin(w * 3), .01),
                     eye=q(1 - kc, .1), sleep=q(.35 * kc, .05), fold=1))
    trace_panel(img, 760 + cam * .4, 640, 560, 380, u, smooth(seg(u, cue(8) - .3, cue(10) + .6)), w)
    LG.rail(img, 1900, cam)
    g = sci(img, w, 'A', 'point', 'thinking', 900 + cam * 1.3, 2060, .5, look=-.5, kw=dict(shirt='#3f7a5a', pants='#4a5a44', hat='cap'))
    img = finish(img, w, 1.02 + .02 * smooth(u / D), 540, 1200, vig=(.24, (20, 50, 30)))
    if not HIDE_UI:
        clue(img, 'CLUE 3', u, .05, 230)
        chip(img, 'ZOO ATLANTA', (60, 130, 80), 300, 400, u, cue(2) - .1, size=50)
        chip(img, 'LEAST SWAY', (60, 160, 110), 760, 900, u, cue(5) - .1, size=50)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(160, 150, 1060, 960)]}


# ---------------------------------------------------------------- s08: the riddle (night)
def s08(u, D, cue):
    w = u + 80
    cam = 20 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    wc = LG.lagoon(img, w, cam, 'night', horizon=1000, sun=(800, 420), flock_n=16)
    bx = 460 + cam
    info = FL.put(img, bx, 1640, 900, face=1, pose=dict(idle(w, 2, False), sleep=1), water=1632, reflect=.45, water_col=(40, 50, 100),
                  t=w, light=(.6, -1.0))
    FL.ripples(img, info['foot'][0], 1636, 130, w, col=(200, 210, 255))
    # moonlight rim on the single leg
    img = finish(img, w, 1.03 + .04 * smooth(u / D), 540, 1300, vig=(.34, (0, 0, 20)))
    if not HIDE_UI:
        qmark(img, 840, 760, 1.4, u, cue(1) - .1, KEY)
        chip(img, 'ASLEEP', (90, 80, 150), 300, 360, u, cue(4) - .1, size=52)
        chip(img, 'ONE THIN LEG', (196, 70, 100), 680, 500, u, cue(10) - .1, size=52)
    return img, {'faces': [], 'avoid': [(120, 280, 1000, 940)]}


# ---------------------------------------------------------------- s09-s11: the mechanism (paper diagram stage)
DX, DGY, DS = 470, 1720, 1060


def diagram_bird(img, w, pose_extra=None, s=DS, x=DX, gy=DGY):
    d = ImageDraw.Draw(img)
    d.line([(60, gy + 2), (W - 60, gy + 2)], fill=(150, 120, 90), width=6)
    for i in range(14):
        xx = 80 + i * 70
        d.line([(xx, gy + 6), (xx - 30, gy + 40)], fill=(170, 140, 110), width=4)
    m = mask(); ImageDraw.Draw(m).ellipse([x - .3 * s, gy - 14, x + .35 * s, gy + 18], fill=255)
    fill_mask(img, m, (120, 90, 70), .35, blur=10)
    p = dict(idle(w, .4, True), fold=1)
    p.update(pose_extra or {})
    return FL.put(img, x, gy, s, face=1, pose=p)


def s09(u, D, cue):
    w = u + 90
    img = Image.new('RGBA', (W, H))
    LG.stage(img, w, 'paper')
    info = diagram_bird(img, w)
    cx, cy = info['center']; fx, fy = info['foot']
    k0 = smooth(seg(u, .1, cue(5)))
    if k0 > 0:
        dashed(img, (cx, cy), (cx, DGY + 20), col=(120, 100, 200), w=5, phase=w)
        dot(img, cx, cy, 16, (120, 100, 200))
    ka = smooth(seg(u, cue(8) - .2, cue(11) + .2))
    if ka > 0:
        # the weight arrow from the body straight down the leg to the foot
        top = cy - 60
        bot = top + (fy - 30 - top) * ka
        arrow(img, (cx + 110, top), (cx + 110, bot), 64, (230, 80, 60), alpha=230)
        m = mask(); ImageDraw.Draw(m).line([(fx, cy), (fx, fy)], fill=255, width=40)
        glow(img, m, (255, 140, 90), .45 * ka, blur=24)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1200, vig=(.18, (120, 90, 60)))
    if not HIDE_UI:
        chip(img, 'FOOT UNDER THE BODY', (120, 100, 200), 540, 260, u, cue(1) - .1, size=48)
        chip(img, 'ALL THE WEIGHT', (230, 80, 60), 790, 620, u, cue(8) - .1, size=50)
        chip(img, 'STRAIGHT DOWN', (40, 40, 48), 790, 760, u, cue(10) - .1, size=50)
    return img, {'faces': [], 'avoid': [(200, 180, 880, 340), (560, 540, 1060, 840)]}


def dial(img, cx, cy, r, ang, stop, name, k_stop, col=(230, 80, 60), lbl_side=1):
    """A joint dial: a bone rotating about the joint toward a stop block; when it touches, the block flashes."""
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8], fill=INK)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 244, 230))
    # the range of motion arc
    a0 = stop - 100
    d.arc([cx - r * .82, cy - r * .82, cx + r * .82, cy + r * .82], a0, stop, fill=(200, 190, 170), width=14)
    # stop block
    sa = math.radians(stop + 6)
    bxp, byp = cx + math.cos(sa) * r * .74, cy + math.sin(sa) * r * .74
    blk = [(bxp + math.cos(sa + q_) * 34, byp + math.sin(sa + q_) * 34) for q_ in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]
    flash_k = max(0.0, 1 - k_stop) if k_stop >= 0 else 0
    d.polygon(blk, fill=lerp(col, (255, 255, 200), flash_k * .7), outline=INK)
    if 0 <= k_stop < .6:
        m = mask(); ImageDraw.Draw(m).ellipse([bxp - 80, byp - 80, bxp + 80, byp + 80], fill=255)
        glow(img, m, (255, 220, 120), .8 * (1 - k_stop / .6), blur=20)
    # the bone
    a = math.radians(ang)
    ex, ey = cx + math.cos(a) * r * .9, cy + math.sin(a) * r * .9
    d = ImageDraw.Draw(img)
    d.line([(cx, cy), (ex, ey)], fill=INK, width=44); d.line([(cx, cy), (ex, ey)], fill=(250, 246, 236), width=30)
    d.ellipse([ex - 24, ey - 24, ex + 24, ey + 24], fill=(250, 246, 236), outline=INK, width=6)
    d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(255, 210, 63), outline=INK, width=7)
    if not HIDE_UI:
        d.text((cx, cy - r - 30), name, font=font(48), fill='white', anchor='mb', stroke_width=7, stroke_fill=INK)


def s10(u, D, cue):
    w = u + 100
    img = Image.new('RGBA', (W, H))
    LG.stage(img, w, 'paper')
    info = diagram_bird(img, w, s=900, x=300, gy=1760)
    K = info['knee']
    cx, cy = info['center']
    arrow(img, (cx + 60, cy - 220), (cx + 60, cy - 70), 50, (230, 80, 60), alpha=220)
    # the two dials (hip, knee), linked to the bird's knee region
    hx_, hy_ = 760, 640; kx_, ky_ = 760, 1120; r = 200
    lay = layer(); dl = ImageDraw.Draw(lay)
    for (px, py) in ((hx_, hy_), (kx_, ky_)):
        dl.line([(K[0], K[1] - 30), (px - r, py)], fill=(120, 100, 200, 200), width=5)
    img.alpha_composite(lay)
    th, tk = cue(3) - .1, cue(5) - .1
    te = cue(8)
    kh = smooth(seg(u, th, te)); kk = smooth(seg(u, tk, te))
    stop_h, stop_k = 40, 120
    dial(img, hx_, hy_, r, stop_h - 70 * (1 - kh) + 1.5 * math.sin(w * 8) * (1 - kh), stop_h, 'HIP', (u - te) / .5 if u >= te else -1)
    dial(img, kx_, ky_, r, stop_k - 80 * (1 - kk) + 1.5 * math.sin(w * 8 + 1) * (1 - kk), stop_k, 'KNEE', (u - te) / .5 if u >= te else -1)
    joint(img, K, 18, (255, 210, 63), 1.0, math.sin(w * 6) * .4)
    sx, sy = shake(u, te, 6, .25)
    img = finish(img, w, 1.0 + .02 * smooth(u / D), 540, 1100, dx=sx, dy=sy, vig=(.18, (120, 90, 60)))
    if not HIDE_UI:
        chip(img, 'END OF THE BEND', (230, 80, 60), 760, 1390, u, cue(8) - .05, size=50)
        chip(img, "CAN'T FOLD", (40, 40, 48), 760, 1510, u, cue(15) - .1, size=54)
    return img, {'faces': [], 'avoid': [(520, 380, 1040, 1560)]}


def lock_icon(img, x, y, s, k):
    if k <= 0: return
    lay = layer(200, 220); d = ImageDraw.Draw(lay)
    d.arc([50, 10, 150, 120], 180, 360, fill=INK, width=30); d.arc([56, 16, 144, 114], 180, 360, fill=(200, 206, 220), width=16)
    d.rounded_rectangle([30, 80, 170, 200], 20, fill=(255, 210, 63), outline=INK, width=8)
    d.ellipse([88, 120, 112, 144], fill=INK); d.rectangle([96, 136, 104, 170], fill=INK)
    anim.scaled_paste(img, lay, x, y, s * k)


def s11(u, D, cue):
    w = u + 110
    img = Image.new('RGBA', (W, H))
    LG.stage(img, w, 'paper')
    ks = smooth(seg(u, cue(1), cue(4) + .3))
    info = diagram_bird(img, w, {'sleep': q(ks, .05), 'eye': 1 - ks}, s=1000, x=430)
    cx, cy = info['center']; K = info['knee']
    # gravity arrow pressing down from above
    kg = smooth(seg(u, -.1, .5))
    yb = 560 + 20 * math.sin(w * 2)
    arrow(img, (cx, 230 + 40 * (1 - kg)), (cx, yb), 90, (70, 120, 220), alpha=int(230 * kg))
    lock_icon(img, K[0] + 40, K[1] - 20, .55, pop(u, cue(1) - .05, .3))
    lock_icon(img, info['far_ankle'][0] - 10, info['far_ankle'][1] - 10, 0, 0)
    v = .06 + .02 * math.sin(w * 9) + .05 * (1 - smooth(seg(u, cue(5), cue(7))))
    meter(img, 900, 1500, 600, v, 'MUSCLES')
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1200, vig=(.18, (120, 90, 60)))
    if not HIDE_UI:
        tag(img, 'GRAVITY', cx, 200, 64, (90, 140, 240), pop(u, cue(0) - .05, .3))
        chip(img, 'HOLDS IT', (70, 120, 220), cx + 10, 680, u, cue(1) - .1, size=50)
        chip(img, 'BARELY WORK', (60, 150, 110), 860, 760, u, cue(7) - .1, size=48)
    return img, {'faces': [], 'avoid': [(250, 120, 1080, 820), (780, 820, 1020, 1520)]}


# ---------------------------------------------------------------- s12: back in the lab: one leg steady, two legs not
def s12(u, D, cue):
    w = u + 120
    cam = -10 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    LG.lab(img, w, 80 + cam)
    LG.bench(img, -200, 330, 1160, cam * .9)
    LG.monitor(img, 160 + cam, 960, 270, 190, w, k_flat=1.0, label='MUSCLES')
    info = specimen(img, w, 620 + cam, 1560, 1000, face=-1)
    g = sci(img, w, 'B', dict(POSES['stand'], armR=(-60, -100)), 'surprised', 140 + cam * 1.2, 2010, .5, look=.5, bphase=.4)
    img = finish(img, w, 1.03 + .03 * smooth(u / D), 540, 1200, vig=(.26, (50, 30, 30)))
    if not HIDE_UI:
        chip(img, 'ONE LEG: STEADY', (60, 150, 110), 600, 330, u, cue(4) - .1, size=56)
        check_mark(img, 600, 470, 70, seg(u, cue(5), cue(6) + .2))
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(220, 240, 980, 560)]}


def s12b(u, D, cue):
    w = u + 125
    img = Image.new('RGBA', (W, H))
    LG.lab(img, w, 80)
    LG.bench(img, -200, 330, 1160, 0)
    LG.monitor(img, 160, 960, 270, 190, w, k_flat=1.0, label='MUSCLES')
    tf = cue(11) - .1
    kf = smooth(seg(u, tf, tf + .7))
    wob = 3 * math.sin(u * 9) * (1 - kf) * smooth(seg(u, .2, tf))
    pose = {'fold': 0.0, 'fx': .06, 'fx2': -.10, 'tilt': q(-wob - 14 * kf, .5), 'drop': q(.07 * kf, .005)}
    x, gy, s = 620, 1560, 1000
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - .4 * s, gy - 6, x + .4 * s, gy + 40], 10, fill=(120, 130, 146), outline=INK, width=5)
    d.rectangle([x - .38 * s, gy - 6, x + .38 * s, gy + 6], fill=(206, 214, 226))
    m = mask(); ImageDraw.Draw(m).ellipse([x - .3 * s, gy - 10, x + .3 * s, gy + 12], fill=255)
    fill_mask(img, m, (60, 40, 40), .3, blur=10)
    FL.put(img, x, gy, s, face=-1, kind='specimen', pose=dict(pose, sleep=1.0, breath=.5))
    sx, sy = shake(u, tf + .45, 8, .3)
    img = finish(img, w, 1.03, 540, 1200, dx=sx, dy=sy, vig=(.26, (50, 30, 30)))
    if not HIDE_UI:
        chip(img, 'TWO LEGS', (40, 40, 48), 600, 330, u, cue(8) - .1, size=56)
        chip(img, 'UNSTEADY', (230, 80, 60), 600, 460, u, tf + .3, size=56)
        if u > tf + .4: draw_x(img, 880, 400, 60, (u - tf - .4) / .12, w=18)
    return img, {'faces': [], 'avoid': [(260, 240, 980, 540)]}


# ---------------------------------------------------------------- s13: locked knees in a queue
def s13(u, D, cue):
    w = u + 130
    cam = -30 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    LG.street(img, w, cam)
    G = []
    people = [(1000, 1560, .44, dict(shirt='#5b8a5a', pants='#3a3a48'), 2.1), (800, 1600, .48, dict(shirt='#c85a5a', pants='#40405a'), 1.3),
              (180, 1690, .54, dict(shirt='#d8a040', pants='#3a4a6a'), .7)]
    for x, gy, s, kw, ph in people:
        G.append(actor(img, 'neutral', 'stand', x + cam * 1.1, gy, s, w + ph, look=-.6, bphase=ph, aura=None, **kw))
    lk = smooth(seg(u, cue(2) - .2, cue(4)))
    you = sci(img, w, 'P', dict(POSES['stand'], legL=(6, 0), legR=(-6, 0)), 'neutral', 520 + cam * 1.1, 1660, .58, look=-.5, lean=-1.5 * lk)
    hx, hy = you['head']
    # x-ray inset: the leg bones stacked straight (femur on tibia), muscles relaxed
    ix, iy, ir = 560, 680, 230
    k_in = smooth(seg(u, cue(9) - .4, cue(9) + .1))
    if k_in > 0 and not HIDE_UI:
        lay = layer(); dl = ImageDraw.Draw(lay)
        dl.ellipse([ix - ir - 10, iy - ir - 10, ix + ir + 10, iy + ir + 10], fill=INK + (255,))
        dl.ellipse([ix - ir, iy - ir, ix + ir, iy + ir], fill=(16, 32, 56, 255))
        msk = mask(); ImageDraw.Draw(msk).ellipse([ix - ir, iy - ir, ix + ir, iy + ir], fill=255)
        sub = layer()
        sd = ImageDraw.Draw(sub)
        sd.polygon([(ix - 70, iy - 260), (ix + 70, iy - 260), (ix + 56, iy + 260), (ix - 56, iy + 260)], fill=(200, 120, 130, 90))
        sub.putalpha(ImageChops.multiply(sub.split()[3], msk))
        lay.alpha_composite(sub)
        img2 = layer(); img2.alpha_composite(lay)
        bone(img2, (ix, iy - 260), (ix, iy - 14), 40)
        bone(img2, (ix, iy + 14), (ix, iy + 260), 34)
        joint(img2, (ix, iy), 24, (255, 210, 63), 1.0, math.sin(w * 5) * .3)
        arrow(img2, (ix + 130, iy - 180), (ix + 130, iy + 120), 34, (230, 80, 60))
        a = img2.split()[3]
        cm = mask(); ImageDraw.Draw(cm).ellipse([ix - ir - 12, iy - ir - 12, ix + ir + 12, iy + ir + 12], fill=255)
        img2.putalpha(ImageChops.multiply(a, cm))
        anim.scaled_paste(img, img2.crop((ix - ir - 14, iy - ir - 14, ix + ir + 14, iy + ir + 14)), ix, iy, .3 + .7 * out_back(k_in))
        lay2 = layer(); ImageDraw.Draw(lay2).line([(ix - 60, iy + ir), (hx + 10, hy + 380)], fill=(255, 255, 255, int(200 * k_in)), width=5)
        img.alpha_composite(lay2)
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1250, vig=(.24, (60, 30, 20)))
    if not HIDE_UI:
        chip(img, 'LOCKED KNEES', (60, 110, 170), 540, 240, u, cue(2) - .1, size=54)
        chip(img, 'BONES CARRY IT', (230, 120, 40), 300, 1000, u, cue(10) - .1, size=46)
        chip(img, 'MUSCLES RELAX', (60, 150, 110), 800, 1000, u, cue(16) - .1, size=46)
    return img, {'faces': [face_box(you, 1.3)] + [face_box(g, 1.2) for g in G], 'avoid': [(260, 160, 860, 1060)]}


# ---------------------------------------------------------------- s14: the flip (the biggest title)
def s14(u, D, cue):
    w = u + 140
    img = Image.new('RGBA', (W, H))
    left = Image.new('RGBA', (W, H))
    LG.room(left, w, 80)
    radial(left, 270, 1300, 700, (120, 160, 255), .15)
    lean = (6 + 4 * smooth(seg(u, cue(6), cue(7)))) * math.sin(u * 3.6) + 3 * math.sin(u * 7.3)
    g = actor(left, 'worried', add(dict(ONE_LEG), armL=(8 * math.sin(u * 3.6), 12 * math.sin(u * 3.6))), 280, 1720, .62, w, lean=lean,
              aura=None, rim=(200, 210, 255), rim_dir=(1, -.4), rim_w=10, idle=.4, **PERSON)
    right = Image.new('RGBA', (W, H))
    wc = LG.lagoon(right, w, -300, 'dawn', horizon=900, sun=(900, 860), flock_n=20)
    info = FL.put(right, 820, 1660, 640, face=-1, pose=dict(idle(w, 1, False), sleep=1), water=1652, reflect=.5, water_col=wc, t=w)
    FL.ripples(right, info['foot'][0], 1656, 110, w)
    m = mask(); ImageDraw.Draw(m).polygon([(0, 0), (552, 0), (528, H), (0, H)], fill=255)
    img.alpha_composite(right); img.paste(left, (0, 0), m)
    d = ImageDraw.Draw(img)
    d.line([(552, 0), (528, H)], fill=INK, width=18); d.line([(552, 0), (528, H)], fill=(255, 255, 255), width=8)
    img = finish(img, w, 1.0 + .02 * smooth(u / D), 540, 1200, vig=(.26, (40, 20, 40)))
    if not HIDE_UI:
        stitle(img, 's14_a', [('FOR US:', 'white', 110), ('HARD.', PINK, 190)], 110, u, cue(0) - .1, stagger=cue(6) - cue(0))
        stitle(img, 's14_b', [('FOR A FLAMINGO:', 'white', 96), ('EASY.', KEY, 250)], 520, u, cue(10) - .1, stagger=cue(15) - cue(10))
        put_chip(img, 'HARD WAY', (90, 100, 150), 280, 1840, pop(u, cue(6), .3), size=42)
        put_chip(img, 'EASY WAY', (196, 70, 100), 810, 1840, pop(u, cue(15), .3), size=42)
    sx, sy = shake(u, cue(15), 6, .25)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 90, W, 1000)]}


# ---------------------------------------------------------------- s15: the loop back to 2017
def s15(u, D, cue):
    w = u - D
    if u > D - 1.5 / 30:
        now = anim.NOW; anim.NOW = 0.0
        try: return s01_frame(0.0, 0.0)
        finally: anim.NOW = now
    kz = smooth(seg(u, .2, D - .4))
    z = 1.5 - .5 * kz
    cam = 8 * math.sin(w * .45)
    img, info, G = lab_scene(w, cam)
    fx = 540 + (info['knee'][0] - 540) * (1 - kz); fy = 1150 + (info['knee'][1] - 1150) * (1 - kz)
    img = finish(img, w, z, fx, fy, vig=(.26, (50, 30, 30)))
    if not HIDE_UI:
        k = smooth(seg(u, D - .9, D - .2))
        if k > 0:
            opening_title(img, 0.0, k)
            put_chip(img, 'MUSCLES: OFF', (40, 40, 48), 880, 760, k, size=44)
        if u < D - 1.0:
            chip(img, 'NO WORKING MUSCLES', (40, 40, 48), 540, 300, u, cue(6) - .1, size=50)
            chip(img, 'STILL STANDING', (60, 150, 110), 540, 430, u, cue(9) - .1, size=50)
    faces = [face_box(G['a'], 1.3), face_box(G['b'], 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 120, W, 500)]}


SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [('s01', 1, 0), ('s01b', 1, 12), ('s02', 2, 0), ('s03', 3, 0), ('s04', 4, 0), ('s04b', 4, 8), ('s05', 5, 0),
             ('s05b', 5, 17), ('s06', 6, 0), ('s07', 7, 0), ('s08', 8, 0), ('s09', 9, 0), ('s10', 10, 0), ('s11', 11, 0),
             ('s12', 12, 0), ('s12b', 12, 7), ('s13', 13, 0), ('s14', 14, 0), ('s15', 15, 0)]
END = 1888 / 30                  # 62.933 s (length.json)
NO_PUNCH = ()
BAND_AT = {}
BAND_FIX = {}
STILL_AT = {'s01': .02, 's01b': .9, 's02': .95, 's03': .9, 's04': .9, 's04b': .9, 's05': .95, 's05b': .9, 's06': .92,
            's07': .95, 's08': .9, 's09': .95, 's10': .9, 's11': .92, 's12': .9, 's12b': .9, 's13': .92, 's14': .95, 's15': .5}

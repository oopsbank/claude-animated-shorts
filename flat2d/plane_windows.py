"""Plane windows (video 12, "Why Are Airplane Windows Round?"): shots as `sNN(u, D, cue) -> (img, info)`.

The first video in the cinematic 2D style: the house flat2d look (white stickmen with a black outline, rich flat
colour, "sentence" captions) shot like a film: real perspective sets drawn from a moving 3D camera (`persp.py`),
depth of field (blurred foreground framing layers, soft backgrounds), varied angles (high crane, low angle, top-down,
over-the-shoulder, POV through a round window, macro), few hard cuts (one continuous crane in s01, a pan in s11,
match cuts porthole <-> cabin window, push-through a window into the sky, plane -> newspaper photo), per-scene grades
with a soft vignette, light shafts, water caustics and dust (`cine.py`).

Contract (as moth_light.py): u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the shot's
voice-over LINE. info: 'faces' (face boxes) and 'avoid' (boxes the caption must not cover). anim.NOW = film time.
Hero image (frame 0 and the loop frame, the thumbnail): the Comet fuselage sunk in a giant water tank in a 1954 test
hangar, its wings out through the tank walls on jacks. Serious tone; the two 1954 losses are shown with respect
(a fading silhouette, newspaper headlines, map markers): no explosions, fire, debris or people in danger.

Render: .venv/bin/python flat2d/render.py audio/plane-windows/words.json OUT.mp4 --film plane_windows --size 540x960
"""
import math, os, sys, re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit, anim, cine
import persp as P3
import airliner as A
import hangar as Hg
from kit import W, H, INK, vgrad, radial, font, mask, glow, fill_mask, layer, lerp, rgb
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES, add, damp
from blood_falls import slam_title, face_box
from blood_falls_2 import put_chip, draw_x, path_point, partial
import tunguska as TG
import flamingo_one_leg as F

SLUG = 'plane-windows'
HIDE_UI = False
KEY = (255, 210, 63)
RED = (226, 64, 52)
TEAL = (40, 150, 150)
CYAN = (110, 228, 255)
NAVY = (14, 22, 52)
if '1080x1920' in sys.argv: P3.SS = 2


def q(v, step): return round(v / step) * step


# ---------------------------------------------------------------- UI wrappers (HIDE_UI for the thumbnail frame)
def clue(img, txt, u, t0=.05, y=250):
    if not HIDE_UI: TG.clue(img, txt, u, t0, y)


def chip(img, txt, fill, x, y, u, t0, size=50, angle=0.0, until=None):
    if HIDE_UI or u < t0: return
    k = pop(u, t0, .3, 2.0)
    if until is not None: k *= 1 - smooth(seg(u, until, until + .25))
    if k > .01: put_chip(img, txt, fill, x, y, k, size=size, angle=angle)


def stitle(img, key, lines, y, u, t0, size=104, stagger=.16):
    if not HIDE_UI: slam_title(img, key, lines, y, u, t0, size=size, stagger=stagger)


def tag(img, txt, x, y, size=44, col='white', s=1.0):
    if not HIDE_UI: F.tag(img, txt, x, y, size, col, s)


def qmark(img, x, y, s, u, t0, col=(255, 255, 255)):
    if not HIDE_UI: F.qmark(img, x, y, s, u, t0, col)


def check(img, x, y, r, k):
    if not HIDE_UI: F.check_mark(img, x, y, r, k)


def xmark(img, x, y, r, prog, w=26):
    if not HIDE_UI: draw_x(img, x, y, r, prog, w)


def dashed(img, p0, p1, col=(255, 255, 255), w=6, phase=0.0, frac=1.0):
    if frac <= 0: return
    p1 = (p0[0] + (p1[0] - p0[0]) * frac, p0[1] + (p1[1] - p0[1]) * frac)
    F.dashed(img, p0, p1, col, w, 26, 16, phase)


def arrow(img, p0, p1, col=(255, 255, 255), w=16, head=34, ink=True, alpha=1.0):
    """A bold arrow p0 -> p1 with an ink edge."""
    if alpha <= .01: return
    lay = layer(); d = ImageDraw.Draw(lay)
    L = math.dist(p0, p1)
    if L < 2: return
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L; nx, ny = -uy, ux
    hb = (p1[0] - ux * head, p1[1] - uy * head)
    tri = [p1, (hb[0] + nx * head * .62, hb[1] + ny * head * .62), (hb[0] - nx * head * .62, hb[1] - ny * head * .62)]
    if ink:
        d.line([p0, hb], fill=INK, width=w + 10); d.polygon(tri, fill=INK, outline=INK, width=8)
    d.line([p0, hb], fill=tuple(col), width=w); d.polygon(tri, fill=tuple(col))
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)


def fin(img, t, look, vig=(.32, (8, 10, 18)), bloom_k=.22, grain=.03, look_b=None, kb=0.0):
    return cine.finish(img, t, look, vig=vig, grain=grain, bloom_k=bloom_k, look_b=look_b, kb=kb)


def flash(img, u, t0, dur=.3, a=.8, col=(255, 250, 240)):
    TG.flash(img, u, t0, dur, a, col)


# ---------------------------------------------------------------- 1954 instruments (2D, close-up art)
def gauge(img, cx, cy, r, val, t=0.0, label='PRESSURE', red_from=.78, blur=0.0):
    """A 1950s pressure gauge: brass bezel, cream dial, ticks 0-10, a red zone, a black needle (val 0..1)."""
    lay = layer(int(r * 2.6), int(r * 2.6)); d = ImageDraw.Draw(lay); o = r * 1.3
    d.ellipse([o - r * 1.12, o - r * 1.12 + 8, o + r * 1.12, o + r * 1.12 + 8], fill=(20, 18, 24))
    d.ellipse([o - r * 1.12, o - r * 1.12, o + r * 1.12, o + r * 1.12], fill=(176, 140, 70), outline=INK, width=6)
    d.ellipse([o - r * 1.02, o - r * 1.02, o + r * 1.02, o + r * 1.02], fill=(214, 178, 96))
    d.ellipse([o - r, o - r, o + r, o + r], fill=(240, 232, 208), outline=(60, 50, 40), width=4)
    a0, a1 = 225, -45
    for k in range(51):
        a = math.radians(a0 + (a1 - a0) * k / 50); big = k % 5 == 0
        r0 = r * (.78 if big else .86)
        col = RED if k / 50 >= red_from else (40, 34, 30)
        d.line([(o + math.cos(a) * r0, o - math.sin(a) * r0), (o + math.cos(a) * r * .93, o - math.sin(a) * r * .93)],
               fill=col, width=5 if big else 2)
        if big:
            d.text((o + math.cos(a) * r * .63, o - math.sin(a) * r * .63), str(k // 5), font=font(int(r * .17), True),
                   fill=(40, 34, 30), anchor='mm')
    d.arc([o - r * .93, o - r * .93, o + r * .93, o + r * .93], -45, -45 + 270 * (1 - red_from), fill=RED, width=int(r * .06))
    d.text((o, o + r * .38), label, font=font(int(r * .13), True), fill=(70, 60, 50), anchor='mm')
    a = math.radians(a0 + (a1 - a0) * max(0, min(1.04, val)) + 1.2 * math.sin(t * 23) * (val > .05))
    tip = (o + math.cos(a) * r * .86, o - math.sin(a) * r * .86); tail = (o - math.cos(a) * r * .2, o + math.sin(a) * r * .2)
    d.line([tail, tip], fill=(20, 18, 22), width=int(r * .06))
    d.ellipse([o - r * .09, o - r * .09, o + r * .09, o + r * .09], fill=(30, 26, 30))
    d.arc([o - r * .9, o - r * .9, o + r * .55, o + r * .55], 200, 250, fill=(255, 255, 255), width=int(r * .05))
    if blur: lay = cine.defocus(lay, blur)
    img.alpha_composite(lay, (int(cx - o), int(cy - o)))


def counter(img, cx, cy, n, digits=4, h=110, label='CYCLES', roll=0.0, blur=0.0):
    """A mechanical cycle counter: black drums with white digits; `roll` (0..1) rolls the last drum to the next digit."""
    w = h * .66; Wt = digits * w + 40
    lay = layer(int(Wt + 40), int(h * 1.9)); d = ImageDraw.Draw(lay)
    x0 = 20; y0 = h * .55
    d.rounded_rectangle([x0 - 10, y0 - 14, x0 + Wt - 10, y0 + h + 14], 16, fill=(60, 66, 64), outline=INK, width=6)
    d.text((x0 + Wt / 2 - 10, y0 - 40), label, font=font(int(h * .3), True), fill=(236, 230, 210), anchor='mm',
           stroke_width=4, stroke_fill=INK)
    s = str(int(n) % 10 ** digits).rjust(digits, '0'); s2 = str(int(n + 1) % 10 ** digits).rjust(digits, '0')
    for i in range(digits):
        xa = x0 + 10 + i * w
        cell = layer(int(w - 8), int(h)); dc = ImageDraw.Draw(cell)
        dc.rectangle([0, 0, w, h], fill=(22, 22, 26))
        off = (roll * h) if (s[i] != s2[i]) else 0
        dc.text(((w - 8) / 2, h / 2 - off), s[i], font=font(int(h * .72), True), fill=(244, 240, 228), anchor='mm')
        if off: dc.text(((w - 8) / 2, h / 2 - off + h), s2[i], font=font(int(h * .72), True), fill=(244, 240, 228), anchor='mm')
        dc.rectangle([0, 0, w, h * .18], fill=(0, 0, 0, 90)); dc.rectangle([0, h * .82, w, h], fill=(0, 0, 0, 90))
        lay.alpha_composite(cell, (int(xa), int(y0)))
    if blur: lay = cine.defocus(lay, blur)
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


# ---------------------------------------------------------------- the 1954 tank sequence (s01, s01b, s07, s15)
ENG = [  # (world feet position, outfit, expression, pose, bphase)
    ((-1.2, -5.65, Hg.TZ), Hg.ENG_A, 'neutral', 'point', .2),
    ((8.6, -5.65, Hg.TZ), Hg.ENG_C, 'thinking', 'hold', .8),
    ((5.0, 5.65, Hg.TZ), Hg.ENG_B, 'neutral', 'stand', .5),
    ((16.5, 5.65, Hg.TZ), Hg.ENG_A, 'thinking', 'think', 1.3),
]


def tank_chars(T, expr_over=None, react=0.0, hide=()):
    """Engineers on the gantries; they look toward the tank (screen-space), react (0..1) = startled at the split."""
    def draw(img, cam, where):
        tx, ty = cam.p((13.0, 0.0, Hg.WZ))
        for i, (P, kw, ex, pose, bp) in enumerate(ENG):
            if i in hide: continue
            far = P[1] > 0
            if (where == 'far') != far or where == 'front': continue
            x, y = cam.p(P)
            look = max(-.8, min(.8, (tx - x) / 260))
            e = expr_over or ex
            ps = pose
            if react > 0:
                e = 'surprised' if react > .5 else e
                ps = anim.mix(POSES[pose] if isinstance(pose, str) else pose, POSES['shrug'], smooth(react) * .6)
            g = Hg.stand(img, cam, P, T, e, ps, look=look, bphase=bp, **kw)
            if g is not None: DRAWN.append(g)
    return draw


DRAWN = []

# camera: one continuous crane from the frame-0 pose (high over the nose end) down to porthole 9.6 (s01 + s01b)
PORT = (6.8, -(Hg.TY + Hg.WALL + .44), Hg.PORT_Z)
CAM0 = ((-13.0, -12.0, 17.0), (15.0, .5, 1.0), 60.0)
SHIFT0 = (0, 140)
S01_PATH = P3.Path([(0.0, CAM0[0], CAM0[1], CAM0[2]), (2.6, (-10.5, -13.5, 14.5), (14.0, .2, 1.4), 58.0),
                    (4.9, (-3.5, -16.0, 9.5), (9.0, -2.0, 2.6), 54.0), (6.4, (4.2, -14.0, 4.6), (6.8, -3.0, 3.0), 46.0),
                    (7.22, (6.8, -10.4, PORT[2]), (6.8, -4.0, PORT[2]), 40.0)], ease_ends=True, shift=SHIFT0)


def s01_cam(T):
    c = S01_PATH.at(T)
    k = smooth(seg(T, 4.2, 7.0))                    # lens shift relaxes to centre for the porthole close-up
    return P3.Cam(c.pos, c.target, c.fov, c.roll, shift=(0, SHIFT0[1] * (1 - k)))


PUMPS = (6.0, 6.55, 6.98)        # 'pumped it up', 'again', 'again'


def pump_cycle(T):
    """Pressure 0..1: three pulses on 'pumped it up, again and again' (then rest)."""
    return .08 + .82 * max(math.exp(-((T - p) / (.2 if i == 0 else .15)) ** 2) for i, p in enumerate(PUMPS))


def opening_title(img, u, k=1.0, t_pop=None):
    if HIDE_UI or k <= .01: return
    s = 1.0 + .006 * math.sin(u * 2.4)
    if t_pop is not None and t_pop <= u < t_pop + .3: s = max(s, slam(u, t_pop, .3, 1.12))
    lay, _ = F.tlayer('open_pw', [('1954', KEY, 230)], 230)
    anim.scaled_paste(img, lay, 540, 230, s * k)
    put_chip(img, 'ENGLAND', (36, 104, 86), 540, 420, k, size=58)


def tank_frame(T, cam, chars=None, flex=0.0, swell=0.0, surge=0.0, fg=None, bloom_k=.24, focus_fg=None, porthole_glow=0.0,
               extra_mid=None, extra_after=None):
    DRAWN.clear()
    img, info = Hg.scene(cam, T, chars=chars, flex=flex, swell=swell, surge=surge, fg=fg, porthole_glow=porthole_glow,
                         extra_mid=extra_mid, extra_after=extra_after)
    return fin(img, T, 'hangar', bloom_k=bloom_k)


def s01_frame(T, cue=None):
    """The continuous crane over the tank (T = film time 0..7.22). T = 0 is frame 0 (the hook and the loop frame)."""
    cam = s01_cam(T)
    pv = pump_cycle(T)
    flex = (pv - .08) * 1.1
    img = tank_frame(T, cam, tank_chars(T), flex=flex, swell=max(0, pv - .3))
    faces = [face_box(g, 1.3) for g in DRAWN if g['R'] > 6]
    if not HIDE_UI:
        k = 1 - smooth(seg(T, 2.3, 2.8))
        opening_title(img, T, k, t_pop=.28)
        # chips that name the hero image
        if 2.35 < T < 5.0:
            x, y = cam.p((12.5, 0, Hg.WZ)); chip(img, 'A WHOLE AIRLINER', (40, 92, 150), 540, max(330, y - 330), T, 2.45, size=50, until=4.6)
        if 3.75 < T < 5.6:
            chip(img, 'GIANT WATER TANK', TEAL, 540, 360, T, 3.85, size=50, until=5.3)
    return img, faces


def s01(u, D, cue):
    img, faces = s01_frame(anim.NOW, cue)
    return img, {'faces': faces, 'avoid': [(0, 100, W, 520)]}


def s01b(u, D, cue):
    T = anim.NOW
    img, faces = s01_frame(T, cue)
    pv = pump_cycle(T)
    # the pressure gauge rises into the foreground (rack focus: soft -> sharp) and the cycle counter ticks
    k = smooth(seg(u, .05, .45)) * (1 - smooth(seg(T, 6.95, 7.2)))
    if k > .01 and not HIDE_UI:
        blur = 6 * (1 - smooth(seg(u, .1, .7)))
        gauge(img, 250, 1520 + 260 * (1 - k), 190, pv, T, blur=blur)
        n = sum(T >= p for p in PUMPS)
        nxt = [p for p in PUMPS if p > T]
        roll = smooth(seg(T, nxt[0] - .12, nxt[0])) if nxt else 0.0
        counter(img, 790, 1590 + 260 * (1 - k), n, 4, 96, 'CYCLES', roll=roll, blur=blur)
    return img, {'faces': faces, 'avoid': [(0, 1280, W, 1800)] if k > .3 else []}


def s07_cam(u):
    """Low angle at the foot of the near tank wall, looking up at the gantry, the wing overhead, porthole 9.6."""
    return P7_PATH.at(u)


P7_PATH = P3.Path([(0.0, (1.2, -14.6, .8), (7.4, -4.0, 5.6), 66.0), (1.6, (2.4, -13.6, 1.0), (7.2, -4.0, 5.2), 62.0),
                   (3.24, (3.6, -12.6, 1.2), (7.0, -4.2, 4.6), 58.0)], ease_ends=False)


def splash(img, cam, k, t):
    """Water heaving over the near rim at the split (a white sheet + drops above the rim, around porthole x)."""
    if k <= .01: return
    lay = layer(); d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(4)
    for i in range(26):
        x = 1.0 + 12.0 * i / 25; y = -(Hg.TY + Hg.WALL)
        a, b = cam.p((x, y, Hg.TZ)), cam.p((x, y, Hg.TZ + 1.6 * k * (.5 + .5 * math.sin(i * 1.7))))
        d.line([a, b], fill=(236, 252, 250, 220), width=int(26 * k + 6))
    for i in range(40):
        x = rng.uniform(1, 13); h_ = rng.uniform(.6, 2.6) * k; dx = rng.uniform(-.6, .6)
        p = cam.p((x + dx * k, -(Hg.TY + Hg.WALL) - rng.uniform(0, 1.2) * k, Hg.TZ + h_))
        r = rng.uniform(5, 14); d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(236, 252, 250, 230))
    img.alpha_composite(kit.soft_layer(lay, 2))
SPLIT_AT = 30.05            # 'split'


def s07(u, D, cue):
    T = anim.NOW
    cam = s07_cam(u)
    sp = cue(9)                                       # split
    react = smooth(seg(u, sp + .05, sp + .35))
    surge = math.exp(-max(0, u - sp) * 2.2) * (u > sp) * 1.0
    pv = .08 + .78 * (.5 - .5 * math.cos(2 * math.pi * u / .62)) if u < sp else max(0, .86 * math.exp(-(u - sp) * 6))
    flex = (pv - .08) * 1.1
    sx, sy = shake(u, sp, 16, .5)
    img = tank_frame(T, cam, tank_chars(T, react=react, hide=(2, 3)), flex=flex, surge=surge, porthole_glow=.6,
                     extra_after=lambda im, c: splash(im, c, surge, u))
    if sx or sy: img = cine.cam2d(img, 1.03, dx=sx, dy=sy)
    faces = [face_box(g, 1.3) for g in DRAWN if g['R'] > 6]
    if not HIDE_UI:
        clue(img, 'CLUE 3', u, cue(0) - .05, y=230)
        # the cycle counter on the control desk (foreground, lower left) stops at the split; the gauge drops
        n = 1795 + int(min(u, sp) / .62 * 6) if u < sp else 1830
        if u >= sp: n = 1830
        gauge(img, 210, 1610, 170, pv, T, blur=0)
        counter(img, 770, 1650, n, 4, 92, 'TANK CYCLES')
        if u > sp:
            kit.radial(img, 210, 1610, 260, (255, 60, 40), .35 * (.6 + .4 * math.sin(u * 18)) * react, add=True)
            chip(img, 'SPLIT OPEN!', RED, 540, 470, u, sp + .05, size=58)
        chip(img, 'THE TEST PLANE', (40, 92, 150), 540, 470, u, cue(6) - .05, size=50, until=sp - .05)
    flash(img, u, sp, .25, .55, (255, 236, 220))
    return img, {'faces': faces, 'avoid': [(0, 1400, W, 1800), (0, 150, W, 540)]}


S15_KEYS = None


def s15(u, D, cue):
    """Back to the 1954 tank: from the porthole close-up the camera pulls back and cranes up to the frame-0 pose; the last
    frame IS s01's frame 0 (the loop). World time w runs to 0 at the last frame."""
    end = D - 1 / 30
    w = u - end
    if u >= end - 1e-6:
        anim.NOW = 0.0
        img, faces = s01_frame(0.0)
        return img, {'faces': faces, 'avoid': [(0, 100, W, 520)]}
    anim.NOW = w
    keys = [(0.0, (6.8, -10.6, Hg.PORT_Z - .15), (6.8, -4.0, Hg.PORT_Z - .15), 40.0),
            (.9, (4.6, -14.5, 4.4), (6.8, -2.6, 3.4), 46.0),
            (2.2, (-3.0, -16.5, 9.5), (11.5, -1.5, 2.4), 54.0),
            (end, CAM0[0], CAM0[1], CAM0[2])]
    path = P3.Path(keys, ease_ends=True)
    c = path.at(u)
    k = smooth(seg(u, .4, 2.6))
    cam = P3.Cam(c.pos, c.target, c.fov, c.roll, shift=(0, SHIFT0[1] * k))
    img = tank_frame(w, cam, tank_chars(w), flex=0.0, swell=0.0)
    faces = [face_box(g, 1.3) for g in DRAWN if g['R'] > 6]
    if not HIDE_UI:
        t54 = cue(10) - .05
        if u >= t54:
            s = slam(u, t54, .3, 1.12)
            lay, _ = F.tlayer('open_pw', [('1954', KEY, 230)], 230)
            anim.scaled_paste(img, lay, 540, 230, s if u < t54 + .3 else 1.0 + .006 * math.sin(w * 2.4))
            put_chip(img, 'ENGLAND', (36, 104, 86), 540, 420, pop(u, t54 + .12, .3, 2.0), size=58)
        chip(img, 'A TANK OF WATER', TEAL, 540, 420, u, cue(6) - .05, size=52, until=t54 - .15)
    # the match cut in: the cabin window (s14's last frame) dissolves into the porthole for the first 0.3 s
    if u < .3:
        prev = s14_frame(S14_END, None)
        img = cine.xfade(prev, img, smooth(u / .3))
    return img, {'faces': faces, 'avoid': [(0, 100, W, 520)]}


# ---------------------------------------------------------------- the modern cabin (s02, s03, s14)
def window_sky(lay, box, t, pan=0.0, sun=True, warm=0.0):
    """A small altitude sky inside a window box: deep blue, cloud tops, the sun's glow."""
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = max(2, x1 - x0), max(2, y1 - y0)
    sub = Image.new('RGBA', (W, H)); import skyworld as SW
    SW.sky(sub, horizon=1250)
    SW.cirrus(sub, t, pan, 200, 900, 6, .28)
    SW.cloud_sea(sub, t, pan, 0, horizon=1150, rows=4, drift=24, warm=warm)
    if sun: SW.sun(sub, W * .78, 520, .9)
    sub = sub.resize((int(W * max(w / W, h / H) * 1.05), int(H * max(w / W, h / H) * 1.05)), Image.BILINEAR)
    lay.alpha_composite(sub, (x0 - (sub.width - w) // 2, y0 - (sub.height - h) // 2))


_SKYC = {}


def sky_cached(t, w=W, h=H):
    """The full-frame altitude sky (cached per 1/10 s): used through windows."""
    k = (round(t * 10), w, h)
    if k not in _SKYC:
        if len(_SKYC) > 8: _SKYC.clear()
        import skyworld as SW
        sub = Image.new('RGBA', (W, H)); SW.sky(sub, horizon=1250)
        SW.cirrus(sub, t, 0, 200, 900, 6, .28)
        SW.cloud_sea(sub, t, 0, 0, horizon=1150, rows=4, drift=24)
        SW.sun(sub, W * .74, 520, .9)
        _SKYC[k] = sub if (w, h) == (W, H) else sub.resize((w, h), Image.BILINEAR)
    return _SKYC[k]


def sky_into(lay, box, t, zoom=1.0):
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    sub = sky_cached(t)
    sc = max(w / W, h / H) * 1.25 * zoom
    s2 = sub.resize((max(2, int(W * sc)), max(2, int(H * sc))), Image.BILINEAR)
    lay.alpha_composite(s2, (x0 - (s2.width - w) // 2, y0 - (s2.height - h) // 2 - int(h * .12)))


def wall_panel(img, t, col=A.WALLC, seams=(), light=(.75, .2)):
    """The warm cabin sidewall filling the frame: a soft gradient, a faint texture, panel seams."""
    img.paste(vgrad([(0, kit.lerp(col, (255, 246, 230), .25)), (.55, col), (1, kit.lerp(col, (150, 130, 120), .35))]))
    kit.radial(img, W * light[0], H * light[1], 900, (255, 236, 200), .25)
    d = ImageDraw.Draw(img)
    for x in seams: d.line([(x, 0), (x, H)], fill=kit.lerp(col, (120, 110, 100), .35), width=4)


def passenger_back(img, x, y, s, shirt=(70, 120, 170), blur=10.0):
    """Over-the-shoulder foreground: a passenger seen from behind (head disc + shoulders), defocused."""
    lay = layer(); d = ImageDraw.Draw(lay)
    R = 150 * s
    d.rounded_rectangle([x - R * 1.6, y + R * .8, x + R * 1.6, y + R * 4.2], R * .9, fill=kit.rgb(shirt), outline=INK, width=int(8 * s))
    d.ellipse([x - R, y - R, x + R, y + R], fill=(236, 236, 230), outline=INK, width=int(8 * s))
    d.arc([x - R * .9, y - R * .9, x + R * .9, y + R * .9], 200, 300, fill=(255, 255, 255), width=int(10 * s))
    img.alpha_composite(cine.defocus(lay, blur))


def seat_back_fg(img, x, y, s, blur=12.0, col=A.SEAT):
    lay = layer(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x - 300 * s, y, x + 300 * s, y + 900 * s], 120 * s, fill=kit.rgb(col), outline=INK, width=int(8 * s))
    d.rounded_rectangle([x - 250 * s, y + 30 * s, x + 250 * s, y + 230 * s], 60 * s, fill=A.HEADREST)
    img.alpha_composite(cine.defocus(lay, blur))


def corner_fit(img, box, r, k, col=(120, 230, 255), which='tr'):
    """Highlight a window's round corner: a dashed circle that fits it (k 0..1 draws it on)."""
    if k <= .01 or HIDE_UI: return
    x0, y0, x1, y1 = box
    cx = x1 - r if 'r' in which else x0 + r; cy = y0 + r if 't' in which else y1 - r
    lay = layer(); d = ImageDraw.Draw(lay)
    n = 28
    for i in range(int(n * k)):
        if i % 2: continue
        a0 = 360 * i / n; a1 = 360 * (i + 1) / n
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=INK, width=14)
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=col, width=8)
    img.alpha_composite(lay)
    return cx, cy


S02_W = .42     # window art scale at the end of the pull-back


def s02_frame(u, D, cue):
    T = anim.NOW
    # pull back from the window (match size with the porthole), the OTS shoulder slides in
    k = ease_out(seg(u, 0, 2.3))
    s = 1.55 - .55 * k                                  # window scale
    par = (10 * (1 - k), -6 * (1 - k))
    img = Image.new('RGBA', (W, H))
    wall_panel(img, T, seams=(140 - 260 * k, 940 + 260 * k))
    cx, cy = 560 - 40 * k, 900 - 60 * k
    # neighbour window (left) appears as we pull back
    if k > .2:
        A.window_art(img, cx - 760 * s, cy + 10, s * .98, lambda l, b: sky_into(l, b, T - .3), T, shade=.42, par=(16, -6))
    box = A.window_art(img, cx, cy, s, lambda l, b: sky_into(l, b, T), T, shade=.16, par=par)
    r = 132 * s
    # light from the window onto the wall
    kit.radial(img, cx, cy, 700 * s, (255, 246, 220), .18)
    # OTS: the passenger's head and shoulder, defocused, slide in from the lower right
    hx = 1140 - 330 * k; hy = 1420 + 240 * (1 - k)
    passenger_back(img, hx, hy, 1.15, blur=16)
    seat_back_fg(img, -120 + 60 * k, 1500 + 200 * (1 - k), 1.2, blur=18)
    img = fin(img, T, 'cabin', bloom_k=.3)
    if not HIDE_UI:
        kc = smooth(seg(u, cue(7) - .1, cue(8) + .1))
        p = corner_fit(img, box, r, kc, which='tr')
        if kc > .6 and p:
            tag(img, 'NO SHARP CORNERS', 540, box[1] - 120, 50, 'white', pop(u, cue(7), .3))
        qmark(img, box[2] + 120, box[1] + 20, .9, u, cue(8) + .02)
    return img, box


def s02(u, D, cue):
    img, box = s02_frame(u, D, cue)
    if u < .2:                                          # match cut: the 1954 porthole dissolves into the cabin window
        prev, _ = s01_frame(7.22)
        img = cine.xfade(prev, img, smooth(u / .2))
    return img, {'faces': [], 'avoid': [(box[0] - 120, box[1] - 200, box[2] + 220, box[3] + 40)]}


# s03: the reverse angle, looking aft down the aisle at the passengers; the hero at the window seat shrugs
_CAB = {}


def cabin_parts():
    if _CAB: return _CAB
    x0 = -.41 - .82 * 19
    _CAB['shell'] = A.cabin_shell(x0, x0 + .82 * 22)
    rows = []
    rng = np.random.default_rng(12)
    for k in range(1, 16):
        x = -.82 * k + .3
        occ = []
        for j, y in enumerate(A.SEAT_Y):
            if k == 1 and j == 0: occ.append((y, 'hero'))
            elif rng.random() < .62: occ.append((y, tuple(int(v) for v in rng.choice([(196, 90, 70), (70, 120, 170), (90, 150, 110), (200, 160, 70),
                                                                                         (150, 100, 170), (60, 70, 90)]))))
        rows.append((x, A.seat_row(x), occ))
    _CAB['rows'] = rows
    return _CAB


def seated(img, cam, P, t, expr='neutral', pose='stand', shirt=(70, 120, 170), look=0.0, bphase=0.0, h=1.7, **kw):
    """A passenger sitting: the stickman is drawn standing with its hip on the seat, then cut below the hip line."""
    C = cam.to_cam([P])[0]
    if C[2] < .3: return None
    ppm = cam.fpx / C[2]; s = h * ppm / 930.0
    hx, hy = cam.proj_cam(C[None])[0]
    lay = layer()
    g = anim.actor(lay, expr, pose, hx, hy + 520 * s, s, t, look=look, bphase=bphase, shirt=kit.rgb(shirt) if not isinstance(shirt, str) else shirt,
                   pants='#3a4058', rim=(255, 236, 210), rim_dir=(-1, -.3), rim_w=8, **kw)
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).rectangle([0, 0, W, hy + 40 * s], fill=255)
    lay.putalpha(ImageChops.multiply(lay.split()[3], m))
    img.alpha_composite(lay)
    return g


S03_PATH = P3.Path([(0.0, (2.3, -.25, 1.32), (-4.0, -.95, .92), 54.0), (1.71, (1.9, -.38, 1.3), (-4.0, -1.05, .92), 50.0)], ease_ends=False)


def s03_frame(u, D, cue, T=None):
    T = anim.NOW if T is None else T
    cam = S03_PATH.at(u)
    C = cabin_parts()
    img = Image.new('RGBA', (W, H), (60, 52, 50, 255))
    light = P3.Light(d=(.3, .2, .93), amb=.6, bands=(.2, .55, .82), soft=.5, shadow=(90, 70, 80), shadow_k=.25)
    fogc = P3.fog_linear((214, 196, 176), 2.0, 16.0, .55)
    P3.render(img, cam, C['shell'], light=light, fog=lambda c, P, d: fogc(c, P, d), ink_w=2, sil_w=3)
    hero = None
    for x, part, occ in reversed(C['rows']):
        P3.render(img, cam, [part], light=light, fog=lambda c, P, d: fogc(c, P, d), ink_w=2, sil_w=3)
        for y, who in occ:
            P = (x - .12, y, .52)
            if who == 'hero':
                sh = smooth(seg(u, cue(4) - .15, cue(5) + .1))
                pose = anim.mix(POSES['stand'], POSES['shrug'], sh)
                hero = seated(img, cam, P, T, 'thinking' if sh < .5 else 'neutral', pose, shirt=(214, 120, 60), look=.35, bphase=.3)
            else:
                seated(img, cam, P, T, 'neutral', 'stand', shirt=who, look=.2 * math.sin(x * 3 + y), bphase=abs(x * 1.7 + y))
    # warm light falling from the windows across the seats
    cine.shafts(img, [[(0, 520), (300, 470), (760, 1240), (380, 1380)]], col=(255, 236, 200), alpha=.18, blur=40)
    img = fin(img, T, 'cabin', bloom_k=.25)
    faces = [face_box(hero, 1.25)] if hero else []
    return img, cam, hero, faces


def s03(u, D, cue):
    img, cam, hero, faces = s03_frame(u, D, cue)
    if not HIDE_UI:
        chip(img, 'JUST STYLE?', (214, 90, 150), 540, 430, u, cue(5) - .05, size=60)
    # push through the window beside the hero into the sky (s04's first frame)
    kp = smooth(seg(u, D - .42, D))
    if kp > 0:
        wc = cam.p((-.82 + .3 + .41 - .41, -1.81, 1.12))
        img = cine.cam2d(img, 1 + 5.0 * kp ** 2, wc[0], wc[1])
        r = 60 + 1400 * kp ** 2
        sky = s04_frame(0.0, 3.24, None, T=anim.NOW)[0]
        m = cine.rrect_mask(img.size, [wc[0] - r * .74, wc[1] - r, wc[0] + r * .74, wc[1] + r], r * .45, 3)
        img = cine.through(img, sky, m)
    return img, {'faces': faces, 'avoid': [(0, 300, W, 560)]}


S14_END = 3.22


def s14_frame(u, cue):
    T = anim.NOW
    img = Image.new('RGBA', (W, H))
    wall_panel(img, T, seams=(70, 1010), light=(.5, .6))
    z = 1 + .05 * smooth(u / 3.2)
    cx, cy = 540, 1330
    box = A.window_art(img, cx, cy, 1.15 * z, lambda l, b: sky_into(l, b, T), T, shade=.08, par=(6 * math.sin(u * .6), -4))
    kit.radial(img, cx + 60, cy - 120, 420, (255, 244, 220), .22)
    img = fin(img, T, 'cabin', bloom_k=.32)
    return img, box


def s14(u, D, cue):
    img, box = s14_frame(u, cue)
    if not HIDE_UI:
        stitle(img, 's14a', [('NOT ABOUT', 'white', 124), ('LOOKS.', 'white', 140)], 130, u, cue(0) - .02, stagger=.12)
        if u > cue(8) - .05:
            stitle(img, 's14b', [('ABOUT NOT', KEY, 150), ('TEARING', KEY, 190), ('OPEN.', KEY, 190)], 430, u, cue(8) - .05, stagger=.09)
    sx, sy = shake(u, cue(8), 14, .4)
    if sx or sy: img = cine.cam2d(img, 1.02, dx=sx, dy=sy)
    return img, {'faces': [], 'avoid': [(0, 100, W, 1000), (box[0] - 60, box[1] - 40, box[2] + 60, box[3] + 30)]}


# ---------------------------------------------------------------- the Comet at altitude (s04, s04b, s05b)
_CM = {}


def comet_parts(att=(7.0, 0.0, 0.0)):
    k = ('c', att)
    if k not in _CM:
        if len(_CM) > 6: _CM.clear()
        R = A.attitude(*att)
        _CM[k] = list(A.place(A.comet(), R=R, t=(0, 0, 0)).values())
    return _CM[k]


SKY_LIGHT = P3.Light(d=(.25, -.45, .86), amb=.52, bands=(.2, .55, .82), soft=.45, shadow=(80, 104, 150), shadow_k=.3)


def altitude_bg(T, pan=0.0, tilt=0.0, horizon=1460, sun=(860, 330), dark=0.0):
    import skyworld as SW
    img = Image.new('RGBA', (W, H))
    SW.sky(img, horizon=horizon)
    SW.sun(img, sun[0], sun[1], 1.0)
    SW.cirrus(img, T, pan, 160, 760, 8, .3)
    SW.cloud_sea(img, T, pan, tilt, horizon=horizon, rows=5, drift=30)
    if dark: img.alpha_composite(Image.new('RGBA', img.size, (40, 50, 70, int(120 * dark))))
    return img


S04_PATH = P3.Path([(0.0, (58.0, -64.0, 2.0), (46.0, 0.0, 1.0), 34.0), (.9, (30.0, -56.0, 6.0), (15.0, 0.0, .8), 36.0),
                    (1.9, (17.0, -36.0, 5.0), (11.5, 0.0, .6), 32.0), (3.24, (11.0, -17.0, 3.2), (11.0, 0.0, .2), 24.0)],
                   ease_ends=False)


def s04_frame(u, D, cue, T=None):
    T = anim.NOW if T is None else T
    cam = S04_PATH.at(u)
    img = altitude_bg(T, pan=u * 420, tilt=0)
    import skyworld as SW
    SW.wisps(img, u, 1300, 10, 3, 70, (0, 700, W, 1500), -7)
    pl = layer(); P3.render(pl, cam, comet_parts(), light=SKY_LIGHT, ink_w=2.2, sil_w=5)
    img.alpha_composite(pl)
    return fin(img, T, 'altitude', bloom_k=.28), cam


def window_marks(img, cam, xs, k, col=RED, att=(7.0, 0.0, 0.0)):
    """Corner brackets on the Comet's near-side windows (screen space), drawn on with k."""
    if k <= .01 or HIDE_UI: return
    R = A.attitude(*att); d = ImageDraw.Draw(img)
    for i, x in enumerate(xs):
        kk = smooth(k * 3 - i * .5)
        if kk <= 0: continue
        cs = []
        for a, b in ((-.25, -.22), (.25, -.22), (.25, .22), (-.25, .22)):
            P = A._surface_poly([(x + a, .27 + b)], -1, .03)[0]
            cs.append(cam.p(tuple(R @ np.array(P))))
        cx = sum(p[0] for p in cs) / 4; cy = sum(p[1] for p in cs) / 4
        for p in cs:
            vx, vy = (cx - p[0]) * .35 * kk, (cy - p[1]) * .35 * kk
            for q in ((p[0] + vx, p[1]), (p[0], p[1] + vy)):
                d.line([p, q], fill=INK, width=16); d.line([p, q], fill=col, width=9)
            d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=col, outline=INK, width=3)


def s04(u, D, cue):
    img, cam = s04_frame(u, D, cue)
    if not HIDE_UI:
        chip(img, 'FIRST JET AIRLINER', (40, 92, 150), 540, 330, u, cue(2) - .05, size=52, until=cue(8) - .3)
        if u > cue(6) - .05: stitle(img, 's04c', [('THE COMET', KEY, 140)], 150, u, cue(6) - .05)
        km = smooth(seg(u, cue(8) - .1, cue(9) + .3))
        window_marks(img, cam, A.COMET_WINDOWS_X[4:8], km)
        chip(img, 'SQUARISH WINDOWS', RED, 540, 1650, u, cue(8) + .05, size=56)
    return img, {'faces': [], 'avoid': [(0, 100, W, 420), (0, 1560, W, 1740)]}


# s04b: the plane flies on into the clouds and fades (respectful), and the picture match-cuts into a 1954 newspaper
def paper_layer(kind=1, t=0.0):
    """A 1954 newspaper front page (RGBA 1300 x 1800, generic, no real masthead)."""
    k = ('paper', kind)
    if k in _CM: return _CM[k]
    w, h = 1300, 1800
    lay = Image.new('RGBA', (w, h), (236, 226, 200, 255)); d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(kind)
    a = np.asarray(lay, np.float32); a[..., :3] *= (1 + rng.normal(0, .02, (h, w, 1)))
    lay = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(lay)
    d.rectangle([40, 40, w - 40, 54], fill=(30, 26, 24))
    d.text((w / 2, 112), 'LATE EDITION', font=font(64), fill=(30, 26, 24), anchor='mm')
    date = 'MONDAY, 11 JANUARY 1954' if kind == 1 else 'FRIDAY, 9 APRIL 1954'
    d.text((60, 186), date, font=font(30, True), fill=(60, 52, 46), anchor='lm')
    d.text((w - 60, 186), 'ONE PENNY', font=font(30, True), fill=(60, 52, 46), anchor='rm')
    d.rectangle([40, 214, w - 40, 222], fill=(30, 26, 24))
    lines = (('COMET AIRLINER', 'LOST OFF ELBA') if kind == 1 else ('SECOND COMET LOST', 'ALL COMETS GROUNDED'))
    for i, ln in enumerate(lines):
        f = font(150 if kind == 1 else 118); tw = kit.text_w(ln, f); sc = min(1.0, (w - 100) / tw)
        f = font(int((150 if kind == 1 else 118) * sc))
        d.text((w / 2, 330 + i * 168 * (1 if kind == 1 else .92)), ln, font=f, fill=(22, 18, 18), anchor='mm')
    # photo box (the plane photo is pasted by the shot) and text columns
    d.rectangle([60, 560, 820, 1060], fill=(150, 140, 120), outline=(40, 34, 30), width=4)
    for col in range(3):
        x0 = 60 + col * 420 if col < 2 else 850
        y0 = 1100 if col < 2 else 560
        for j in range(30 if col < 2 else 46):
            ww = rng.uniform(.75, 1.0) * (380 if col < 2 else 390)
            d.rectangle([x0, y0 + j * 22, x0 + ww, y0 + j * 22 + 9], fill=(120, 110, 96))
    _CM[k] = lay
    return lay


def halftone(img, dot=7, tint=(40, 34, 30), paper=(236, 226, 200)):
    """Turn an RGBA picture into a sepia halftone print (for the newspaper photo)."""
    g = np.asarray(img.convert('L'), np.float32) / 255
    h, w = g.shape
    out = Image.new('RGBA', (w, h), paper + (255,)); d = ImageDraw.Draw(out)
    for y in range(0, h, dot):
        for x in range(0, w, dot):
            v = 1 - g[y:y + dot, x:x + dot].mean()
            r = dot * .72 * math.sqrt(max(0, v))
            if r > .4: d.ellipse([x + dot / 2 - r, y + dot / 2 - r, x + dot / 2 + r, y + dot / 2 + r], fill=tint)
    return out


def comet_photo(cam_u=1.0):
    """The photo printed in the paper: the Comet in the sky, as halftone (cached)."""
    k = ('photo', round(cam_u, 2))
    if k in _CM: return _CM[k]
    cam = S04B_PATH.at(cam_u)
    img = altitude_bg(14.98 + cam_u, pan=cam_u * 300)
    pl = layer(); P3.render(pl, cam, comet_parts(), light=SKY_LIGHT, ink_w=2.2, sil_w=5); img.alpha_composite(pl)
    ph = img.crop((0, 560, W, 1440)).resize((760, 619), Image.LANCZOS)
    ph = halftone(ph.convert('RGBA'), 6)
    _CM[k] = ph
    return ph


S04B_PATH = P3.Path([(0.0, (11.0, -17.0, 3.2), (11.0, 0.0, .2), 24.0), (1.1, (26.0, -70.0, 8.0), (16.0, 0.0, 2.0), 30.0)], ease_ends=True)


def s04b(u, D, cue):
    T = anim.NOW
    t_cut = 1.05
    if u < t_cut + .3:
        cam = S04B_PATH.at(min(u, t_cut))
        img = altitude_bg(T, pan=(3.24 + u) * 420, dark=.35 * smooth(seg(u, .2, 1.0)))
        pl = layer(); P3.render(pl, cam, comet_parts(), light=SKY_LIGHT, ink_w=2.2, sil_w=5)
        fade = 1 - .78 * smooth(seg(u, .35, 1.05))                         # the plane fades into the cloud
        pl.putalpha(pl.split()[3].point(lambda v: int(v * fade)))
        import skyworld as SW
        img.alpha_composite(pl)
        kit.haze(img, 700, 1500, (236, 240, 246), .35 * smooth(seg(u, .3, 1.0)))
        sky = fin(img, T, 'altitude', look_b='archive', kb=smooth(seg(u, .3, 1.05)), bloom_k=.2)
    if u >= t_cut:
        img = newspaper_frame(u - t_cut, T, cue, t_cut)
        if u < t_cut + .3: img = cine.xfade(sky, img, smooth((u - t_cut) / .3))
    else:
        img = sky
    if not HIDE_UI and u >= t_cut:
        kx = cue(15) - .1                                  # 'broke apart' -> the wrong answer is crossed out
        chip(img, 'JUST STYLE?', (214, 90, 150), 540, 1620, u, kx - .15, size=62)
        if u > cue(16) - .2: xmark(img, 540, 1620, 110, (u - (cue(16) - .2)) * 5)
    return img, {'faces': [], 'avoid': [(0, 1500, W, 1760)]}


def newspaper_frame(v, T, cue, t_cut):
    """v = time since the match cut. The camera starts zoomed into the photo (the plane where the sky plane was) and
    pulls back over the desk; the April paper slides in on 'two Comets'."""
    img = Image.new('RGBA', (W, H), (52, 40, 34, 255))
    d = ImageDraw.Draw(img)
    for k in range(9):                                      # desk planks
        d.rectangle([0, k * 230, W, k * 230 + 226], fill=(70 + 4 * (k % 2), 52, 42))
    kit.radial(img, 560, 760, 1100, (255, 214, 160), .3)
    p1 = paper_layer(1).copy(); p1.alpha_composite(comet_photo(1.05), (60, 560 + 3))
    ImageDraw.Draw(p1).rectangle([60, 560, 820, 1060], outline=(40, 34, 30), width=4)
    paste_paper(img, p1, 540, 900, .78, -4)
    t2 = cue(13) - t_cut - .2 if cue else 1.0
    if v > t2:
        k = ease_out(seg(v, t2, t2 + .45))
        p2 = paper_layer(2)
        paste_paper(img, p2, 560 + 700 * (1 - k), 1240 - 160 * (1 - k), .64, 6 - 8 * (1 - k), shadow=True)
    # camera: from the photo (zoomed so the printed plane sits where the sky plane was) pulling back
    z = 1.0 + 1.25 * (1 - ease_out(seg(v, 0, 1.6)))
    img = cine.cam2d(img, z, 420, 740, roll=-3 * (1 - ease_out(seg(v, 0, 1.6))))
    return fin(img, T, 'archive', bloom_k=.12, vig=(.42, (12, 8, 6)))


def paste_paper(img, lay, cx, cy, s, ang, shadow=True):
    p = lay.resize((int(lay.width * s), int(lay.height * s)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
    if shadow:
        sh = Image.new('RGBA', p.size, (0, 0, 0, 0)); sh.putalpha(p.split()[3].point(lambda v: int(v * .55)))
        img.alpha_composite(kit.soft_layer(sh, 14), (int(cx - p.width / 2 + 18), int(cy - p.height / 2 + 26)))
    img.alpha_composite(p, (int(cx - p.width / 2), int(cy - p.height / 2)))


# ---------------------------------------------------------------- s05: the map (top-down), climb-outs from Rome
ITALY = [(8.0, 46.5), (8.0, 44.4), (8.9, 44.4), (9.5, 44.2), (9.85, 44.05), (10.1, 43.95), (10.25, 43.8), (10.3, 43.55),
         (10.45, 43.32), (10.53, 42.98), (10.75, 42.88), (10.95, 42.72), (11.1, 42.55), (11.1, 42.42), (11.3, 42.4),
         (11.55, 42.28), (11.8, 42.1), (12.0, 41.95), (12.22, 41.76), (12.45, 41.6), (12.62, 41.45), (12.85, 41.33),
         (13.05, 41.24), (13.3, 41.28), (13.55, 41.21), (13.75, 41.2), (13.95, 41.05), (14.05, 40.86), (14.25, 40.83),
         (14.45, 40.72), (14.37, 40.62), (14.6, 40.63), (14.8, 40.67), (14.95, 40.43), (14.94, 40.25), (15.15, 40.1),
         (15.3, 40.03), (15.6, 40.05), (15.8, 39.75), (15.85, 39.4), (16.05, 39.0), (16.2, 38.6), (15.95, 38.4),
         (17.5, 38.3), (17.5, 41.9), (15.9, 41.95), (15.3, 41.93), (15.0, 42.02), (14.72, 42.12), (14.45, 42.3),
         (14.2, 42.47), (13.95, 42.75), (13.75, 43.05), (13.6, 43.45), (13.48, 43.62), (13.2, 43.75), (12.9, 43.92),
         (12.6, 44.08), (12.35, 44.35), (12.28, 44.62), (12.38, 44.85), (12.28, 45.2), (12.42, 45.45), (12.9, 45.62),
         (13.3, 45.7), (13.7, 45.75), (14.2, 46.5)]
CORSICA = [(9.45, 43.0), (9.5, 42.7), (9.55, 42.3), (9.5, 42.05), (9.4, 41.6), (9.22, 41.37), (8.85, 41.55), (8.65, 41.85),
           (8.62, 42.15), (8.7, 42.5), (9.0, 42.65), (9.3, 42.75)]
SARDINIA = [(9.55, 41.15), (9.75, 40.85), (9.75, 40.4), (9.68, 39.95), (9.6, 39.4), (9.1, 39.2), (8.5, 39.0), (8.4, 39.5),
            (8.45, 40.2), (8.2, 40.6), (8.3, 41.0), (8.75, 41.0), (9.2, 41.2)]
DALMATIA = [(13.7, 45.75), (13.9, 45.45), (14.3, 45.3), (14.7, 45.1), (15.2, 44.5), (15.4, 44.1), (15.9, 43.6), (16.4, 43.5),
            (17.0, 43.1), (17.5, 42.9), (17.5, 46.5), (14.2, 46.5)]
ELBA = (10.27, 42.78); NAPLES_X = (14.0, 40.55); ELBA_X = (10.45, 42.95); ROME = (12.59, 41.8)


def geo(lon, lat, ox=540, oy=1000, k=2.55):
    return (ox + (lon - ROME[0]) * 82.5 * k, oy - (lat - ROME[1]) * 111.0 * k)


def map_layer():
    k = ('map',)
    if k in _CM: return _CM[k]
    w, h = 1500, 2300; ox, oy = w / 2, h / 2 + 20
    lay = Image.new('RGBA', (w, h), (162, 196, 204, 255)); d = ImageDraw.Draw(lay)
    P = lambda pts: [geo(a, b, ox, oy) for a, b in pts]
    # coast ripple lines (1950s map engraving)
    for poly in (ITALY, CORSICA, SARDINIA, DALMATIA):
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).polygon(P(poly), fill=255)
        for r, a in ((34, 60), (22, 90), (12, 120)):
            ring = m.filter(ImageFilter.GaussianBlur(r * .5)).point(lambda v: 255 if v > 8 else 0)
            lay.paste((140, 176, 186), (0, 0), ImageChops.subtract(ring, m.filter(ImageFilter.GaussianBlur(r * .5 - 3)).point(lambda v: 255 if v > 8 else 0)))
    for poly in (ITALY, CORSICA, SARDINIA, DALMATIA):
        d.polygon(P(poly), fill=(232, 214, 172), outline=(84, 64, 44))
        d.line(P(poly) + [P(poly)[0]], fill=(84, 64, 44), width=4)
    ex, ey = geo(*ELBA, ox, oy); d.ellipse([ex - 30, ey - 14, ex + 30, ey + 14], fill=(232, 214, 172), outline=(84, 64, 44), width=3)
    for lon, lat, r in ((13.9, 40.73, 10), (14.22, 40.55, 7), (12.96, 40.9, 6), (10.9, 42.36, 6)):
        x, y = geo(lon, lat, ox, oy); d.ellipse([x - r, y - r * .7, x + r, y + r * .7], fill=(232, 214, 172), outline=(84, 64, 44), width=2)
    # relief hatching inland (the Apennines), graticule, labels
    rng = np.random.default_rng(3)
    for _ in range(140):
        lon = rng.uniform(11.5, 15.0); lat = 44.2 - (lon - 11.0) * .85 + rng.uniform(-.5, .5)
        x, y = geo(lon, lat, ox, oy)
        d.line([(x, y), (x + 12, y - 16), (x + 24, y)], fill=(176, 150, 110), width=3)
    for lon in range(8, 18):
        d.line([geo(lon, 37, ox, oy), geo(lon, 47, ox, oy)], fill=(120, 110, 90), width=1)
    for lat in range(37, 47):
        d.line([geo(7, lat, ox, oy), geo(18, lat, ox, oy)], fill=(120, 110, 90), width=1)
    for name, lon, lat, sz in (('TYRRHENIAN SEA', 11.3, 40.4, 40), ('ADRIATIC SEA', 14.6, 43.3, 34), ('ITALY', 13.0, 42.55, 56),
                               ('CORSICA', 9.15, 42.2, 26), ('ELBA', 10.27, 42.55, 30), ('NAPLES', 14.55, 40.95, 30)):
        x, y = geo(lon, lat, ox, oy)
        d.text((x, y), name, font=font(sz, True), fill=(70, 56, 40) if name not in ('TYRRHENIAN SEA', 'ADRIATIC SEA') else (60, 96, 110), anchor='mm')
    # compass rose
    cx, cy = w - 230, 380
    for a, L in ((0, 110), (90, 70), (180, 70), (270, 70)):
        r = math.radians(a - 90); d.polygon([(cx + math.cos(r) * L, cy + math.sin(r) * L), (cx + math.cos(r + 1.4) * 18, cy + math.sin(r + 1.4) * 18),
                                             (cx + math.cos(r - 1.4) * 18, cy + math.sin(r - 1.4) * 18)], fill=(84, 64, 44))
    d.text((cx, cy - 140), 'N', font=font(40), fill=(84, 64, 44), anchor='mm')
    a = np.asarray(lay, np.float32); a[..., :3] *= (1 + rng.normal(0, .025, (h, w, 1)))
    lay = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    _CM[k] = (lay, ox, oy)
    return _CM[k]


def climb_path(dst, n=40, bow=.18):
    """A dotted climb-out from Rome to dst, bowed a little (screen coords in map-layer space)."""
    lay, ox, oy = map_layer()
    a = np.array(geo(*ROME, ox, oy)); b = np.array(geo(*dst, ox, oy))
    m = (a + b) / 2; nrm = np.array([-(b - a)[1], (b - a)[0]]) * bow
    return [tuple(a * (1 - t) ** 2 + 2 * (m + nrm) * t * (1 - t) + b * t * t) for t in np.linspace(0, 1, n)]


def plane_icon(d, x, y, ang, s=1.0, col=(200, 40, 40)):
    pts = [(28, 0), (8, -4), (-2, -26), (-8, -26), (-2, -4), (-20, -4), (-26, -14), (-30, -14), (-26, 0),
           (-30, 14), (-26, 14), (-20, 4), (-2, 4), (-8, 26), (-2, 26), (8, 4)]
    c, si = math.cos(ang), math.sin(ang)
    P = [(x + (px * c - py * si) * s, y + (px * si + py * c) * s) for px, py in pts]
    d.polygon(P, fill=col, outline=INK); d.line(P + [P[0]], fill=INK, width=3)


def s05(u, D, cue):
    T = anim.NOW
    lay, ox, oy = map_layer()
    img = Image.new('RGBA', (W, H), (40, 32, 28, 255))
    m = lay.copy(); d = ImageDraw.Draw(m)
    rx, ry = geo(*ROME, ox, oy)
    # the two climb-outs draw on together on 'climbing away from Rome'; markers + dates
    k = smooth(seg(u, cue(2) - .1, cue(8)))
    for dst, lbl, s_ in ((ELBA_X, '10 JAN 1954', -1), (NAPLES_X, '8 APR 1954', 1)):
        pts = climb_path(dst, 48, .16 * s_)
        part = partial(pts, k)
        for i in range(0, len(part) - 1, 2):
            d.line([part[i], part[i + 1]], fill=(170, 30, 30), width=9)
        if k > .02:
            (x0, y0), (x1, y1) = part[max(0, len(part) - 2)], part[-1]
            if k < .999: plane_icon(d, x1, y1, math.atan2(y1 - y0, x1 - x0), 1.3)
        if k > .97:
            ex, ey = pts[-1]; mk = smooth(seg(u, cue(8) - .2, cue(8) + .2))
            r = 30 * mk
            d.ellipse([ex - r - 6, ey - r - 6, ex + r + 6, ey + r + 6], fill=INK)
            d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=(250, 246, 236))
            d.ellipse([ex - r * .35, ey - r * .35, ex + r * .35, ey + r * .35], fill=(170, 30, 30))
            if mk > .5:
                d.text((ex + s_ * -10, ey - 70 if s_ < 0 else ey + 70), lbl, font=font(40, True), fill=(40, 30, 24), anchor='mm',
                       stroke_width=6, stroke_fill=(236, 222, 186))
    d.ellipse([rx - 22, ry - 22, rx + 22, ry + 22], fill=(170, 30, 30), outline=INK, width=5)
    # top-down camera: a slow rotate + push over the map
    z = 1.0 + .12 * smooth(u / D); roll = -7 + 5 * smooth(u / D)
    mm = cine.cam2d(m, z, rx, ry, roll=roll)
    img.alpha_composite(mm.crop((int(rx - W / 2), int(ry - 1000), int(rx - W / 2) + W, int(ry - 1000) + H)))
    # desk-lamp light pool and a blurred magnifier rim in the foreground (DOF)
    kit.radial(img, 620, 900, 900, (255, 226, 170), .22)
    def pencil(l):
        dd = ImageDraw.Draw(l)
        dd.line([(1240, 1500), (700, 2060)], fill=(222, 170, 60, 255), width=70)
        dd.line([(1240, 1500), (700, 2060)], fill=(40, 30, 26, 255), width=8)
        dd.polygon([(700 - 40, 2060 - 30), (700 + 30, 2060 + 40), (610, 2150)], fill=(236, 210, 170, 255))
    cine.fg_frame(img, pencil, blur=16)
    img = fin(img, T, 'archive', bloom_k=.1, vig=(.4, (14, 10, 8)))
    if not HIDE_UI:
        clue(img, 'CLUE 1', u, cue(0) - .05, y=230)
        x, y = 540, 1000 - 20
        if u > cue(8) - .1:
            tag(img, 'ROME', x + 120, y + 6, 52, 'white', pop(u, cue(8) - .1, .3))
        chip(img, 'BOTH WHILE CLIMBING', RED, 540, 420, u, cue(5) - .05, size=50)
    return img, {'faces': [], 'avoid': [(0, 150, W, 500), (300, 900, 800, 1080)]}


# s05b: the climb profile: the Comet climbs, the air outside thins
def air_dots(img, t, box, dens, col=(255, 255, 255), seed=5, r=5, alpha=200, jitter=6):
    """Air molecules: density dens(y) (0..1) per row; dots jitter (thermal motion)."""
    rng = np.random.default_rng(seed); x0, y0, x1, y1 = box
    lay = layer(); d = ImageDraw.Draw(lay)
    N = int((x1 - x0) * (y1 - y0) / 1400)
    for i in range(N):
        x = rng.uniform(x0, x1); y = rng.uniform(y0, y1); keep = rng.random()
        if keep > dens(y): continue
        ph = rng.uniform(0, 6.28)
        xx = x + jitter * math.sin(t * 5.3 + ph); yy = y + jitter * math.cos(t * 4.7 + ph * 1.3)
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=tuple(col) + (alpha,))
    img.alpha_composite(lay)


def s05b(u, D, cue):
    T = anim.NOW
    img = Image.new('RGBA', (W, H))
    tilt = 520 * smooth(u / D)                              # the camera cranes up with the plane
    img.paste(vgrad([(0, (18, 40, 96)), (.45, (40, 92, 170)), (.8, (110, 170, 226)), (1, (180, 214, 240))]))
    d = ImageDraw.Draw(img)
    gy = 1720 + tilt
    if gy < H - 2:
        d.rectangle([0, gy, W, H], fill=(96, 128, 86)); d.line([(0, gy), (W, gy)], fill=INK, width=5)
        for x in range(0, W, 90): d.line([(x, gy + 30), (x + 40, gy + 30)], fill=(150, 170, 120), width=6)
    dens = lambda y: max(.03, min(.9, ((y + tilt * .9 - 150) / 1700) ** 2.2))
    air_dots(img, T, (0, 0, W, gy), dens, (210, 236, 255), r=7, alpha=150, jitter=4)
    # altitude scale
    for k_, lbl in enumerate(('0 FT', '10,000', '20,000', '30,000')):
        y = gy - 160 - k_ * 470
        d.line([(40, y), (90, y)], fill=(255, 255, 255), width=4)
        d.text((100, y), lbl, font=font(30, True), fill=(230, 240, 255), anchor='lm', stroke_width=3, stroke_fill=INK)
    # the Comet climbing (side view, small): position along the climb
    f = .25 + .6 * smooth(u / D)
    px, py = 200 + 640 * f, gy - 360 - 1500 * f ** 1.2 + tilt * .0
    cam = P3.Cam((14.0, 95.0, 0.0), (14.0, 0.0, 0.0), 30.0)
    pl = layer(); P3.render(pl, cam, comet_parts((14.0, 0.0, 0.0)), light=SKY_LIGHT, ink_w=2, sil_w=4)
    pl = pl.crop(pl.getbbox()); sc = 520 / pl.width
    pl = pl.resize((int(pl.width * sc), int(pl.height * sc)), Image.LANCZOS)
    img.alpha_composite(pl, (int(px - pl.width / 2), int(py - pl.height / 2)))
    img = fin(img, T, 'altitude', bloom_k=.15)
    if not HIDE_UI:
        chip(img, 'AIR OUTSIDE: THINNER', (40, 92, 150), 540, 380, u, cue(11) - .1, size=54)
        if u > cue(13) - .2: arrow(img, (900, 560), (900, 860), (255, 255, 255), 16, 40, alpha=smooth(seg(u, cue(13) - .2, cue(13))))
    return img, {'faces': [], 'avoid': [(0, 280, W, 480)]}


# ---------------------------------------------------------------- s06: the records office (logbooks, ~1,000 flights)
def logbook(img, cx, cy, s, title, n, k_cnt, ang=0.0):
    lay = layer(760, 560); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([20, 30, 740, 540], 18, fill=(40, 30, 26))
    d.rounded_rectangle([30, 20, 380, 520], 12, fill=(242, 234, 212), outline=INK, width=4)
    d.rounded_rectangle([380, 20, 730, 520], 12, fill=(238, 230, 206), outline=INK, width=4)
    d.text((205, 60), title, font=font(30, True), fill=(40, 30, 26), anchor='mm')
    for j in range(16):
        y = 100 + j * 25
        d.line([(50, y), (360, y)], fill=(170, 160, 140), width=2); d.line([(400, y), (710, y)], fill=(170, 160, 140), width=2)
        if j < 15:
            d.text((60, y + 12), f'{1954 - 2 + (j > 7)} - FLT', font=font(14, True), fill=(80, 70, 60), anchor='lm')
            for q_ in range(5): d.line([(420 + q_ * 14, y + 4), (420 + q_ * 14, y + 20)], fill=(60, 50, 44), width=2)
            d.line([(414, y + 18), (490, y + 6)], fill=(60, 50, 44), width=2)
    d.line([(380, 22), (380, 518)], fill=(120, 110, 96), width=6)
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    lay = lay.resize((int(lay.width * s), int(lay.height * s)), Image.LANCZOS)
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


def s06(u, D, cue):
    T = anim.NOW
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (58, 66, 70)), (.5, (70, 74, 72)), (1, (40, 34, 32))]))
    d = ImageDraw.Draw(img)
    # background: filing cabinets + a window with blinds (to be defocused)
    bg = layer(); db = ImageDraw.Draw(bg)
    db.rectangle([600, 120, 1000, 760], fill=(200, 210, 206)); 
    for y in range(130, 760, 26): db.rectangle([600, y, 1000, y + 14], fill=(150, 160, 156))
    for i in range(3):
        x = 60 + i * 180; db.rectangle([x, 380, x + 160, 980], fill=(92, 104, 96), outline=INK, width=4)
        for j in range(4): db.rectangle([x + 20, 410 + j * 140, x + 140, 520 + j * 140], fill=(108, 120, 112), outline=INK, width=3)
    img.alpha_composite(cine.defocus(bg, 9))
    # desk
    d.polygon([(0, 1060), (W, 1000), (W, H), (0, H)], fill=(96, 62, 40)); d.line([(0, 1060), (W, 1000)], fill=INK, width=6)
    # the investigator behind the desk (medium)
    z = 1 + .06 * smooth(u / D)
    g = actor(img, 'thinking' if u < cue(6) else 'neutral', 'hold' if u < cue(2) else 'point', 540, 1520, .62, T, look=.3 if u < cue(6) else -.2,
              coat='#5a5248', pants='#3a3434', rim=(255, 220, 170), rim_dir=(1, -.4))
    d.polygon([(0, 1180), (W, 1120), (W, H), (0, H)], fill=(110, 72, 46)); d.line([(0, 1180), (W, 1120)], fill=INK, width=6)
    # the lamp pool + two logbooks
    kit.radial(img, 560, 1400, 700, (255, 220, 150), .35)
    logbook(img, 300, 1480, .7, 'PLANE 1 · LOG', 0, 0, ang=6)
    logbook(img, 790, 1500, .7, 'PLANE 2 · LOG', 0, 0, ang=-5)
    kc = smooth(seg(u, cue(9) - .2, cue(12) + .1))
    n1 = int(1290 * kc); n2 = int(900 * kc)
    counter(img, 300, 1760, n1, 4, 80, 'FLIGHTS'); counter(img, 790, 1780, n2, 4, 80, 'FLIGHTS')
    # foreground lamp shade, defocused (DOF frame)
    def lamp(l):
        dd = ImageDraw.Draw(l); dd.polygon([(-60, 0), (420, 0), (300, 260), (-60, 300)], fill=(36, 96, 70, 255))
        dd.ellipse([20, 220, 300, 320], fill=(255, 236, 180, 255))
    cine.fg_frame(img, lamp, blur=16)
    img = cine.cam2d(img, z, 540, 1300)
    img = fin(img, T, 'desk', bloom_k=.25)
    faces = [face_box(g, 1.25)]
    if not HIDE_UI:
        clue(img, 'CLUE 2', u, cue(0) - .05, y=230)
        chip(img, 'NEITHER WAS OLD', (60, 130, 80), 540, 420, u, cue(2) - .05, size=52, until=cue(9) - .3)
        if u > cue(12) - .1:
            chip(img, '~1,000 FLIGHTS EACH', RED, 540, 420, u, cue(12) - .1, size=54)
    return img, {'faces': faces, 'avoid': [(0, 1600, W, 1880), (0, 150, W, 500)]}


# ---------------------------------------------------------------- the mechanism: stretch flowing round windows (s11, s11b, s12)
PANEL_W, PANEL_H = 2300, 1920
HOLE_R = (560, 900, 175)                   # round window: centre x, y, radius (panel px)
HOLE_S = (1720, 900, 330, 330, 10)         # square window: centre x, y, w, h, corner radius (sharp-ish)
_FLOW = {}


def _inside(X, Y):
    cx, cy, r = HOLE_R
    a = (X - cx) ** 2 + (Y - cy) ** 2 <= r * r
    sx, sy, w, h, rr = HOLE_S
    b = (np.abs(X - sx) <= w / 2) & (np.abs(Y - sy) <= h / 2)
    return a, b


def stress_field(step=6):
    """Stream function psi of a uniform vertical 'stretch' past the two holes (psi = x far away, psi = const on each
    hole), solved by Jacobi relaxation coarse-to-fine. Returns (psi, speed) on a grid of `step` px."""
    if 'f' in _FLOW: return _FLOW['f']
    psi = None
    for st in (48, 24, 12, step):
        nx, ny = PANEL_W // st + 1, PANEL_H // st + 1
        X, Y = np.meshgrid(np.arange(nx) * st, np.arange(ny) * st)
        a, b = _inside(X, Y)
        if psi is None: p = X.astype(np.float64).copy()
        else:
            from PIL import Image as _I
            p = np.asarray(_I.fromarray(psi.astype(np.float32)).resize((nx, ny), _I.BILINEAR), np.float64)
        p[a] = HOLE_R[0]; p[b] = HOLE_S[0]
        fixed = a | b
        fixed[0, :] = fixed[-1, :] = True; fixed[:, 0] = fixed[:, -1] = True
        bx = X.astype(np.float64)
        p[0, :] = bx[0, :]; p[-1, :] = bx[-1, :]; p[:, 0] = bx[:, 0]; p[:, -1] = bx[:, -1]
        iters = {48: 1500, 24: 1200, 12: 900, step: 700}[st]
        for _ in range(iters):
            q = .25 * (np.roll(p, 1, 0) + np.roll(p, -1, 0) + np.roll(p, 1, 1) + np.roll(p, -1, 1))
            p = np.where(fixed, p, p + 1.85 * (q - p)) if False else np.where(fixed, p, q)
        psi = p
    gy, gx = np.gradient(psi, step)
    speed = np.sqrt(gx ** 2 + gy ** 2)
    speed[_inside(*np.meshgrid(np.arange(psi.shape[1]) * step, np.arange(psi.shape[0]) * step))[0] |
          _inside(*np.meshgrid(np.arange(psi.shape[1]) * step, np.arange(psi.shape[0]) * step))[1]] = 0
    _FLOW['f'] = (psi, speed, step)
    return _FLOW['f']


def flow_lines(spacing=46, dy=6):
    """Streamlines psi = c (vertical lines bending round the holes) as polylines in panel px, with the local speed."""
    if 'l' in _FLOW: return _FLOW['l']
    psi, speed, st = stress_field()
    ys = np.arange(0, PANEL_H, dy, dtype=np.float64)
    gx = np.arange(psi.shape[1]) * st
    lines = []
    for c in np.arange(spacing / 2, PANEL_W, spacing):
        pts, sp = [], []
        for y in ys:
            j = min(psi.shape[0] - 2, int(y / st)); f = y / st - j
            row = psi[j] * (1 - f) + psi[j + 1] * f
            srow = speed[j] * (1 - f) + speed[j + 1] * f
            row = np.maximum.accumulate(row)                       # monotone along the row (flat on the holes)
            if c <= row[0] or c >= row[-1]: continue
            i = int(np.searchsorted(row, c)); i = max(1, min(len(row) - 1, i))
            r0, r1 = row[i - 1], row[i]
            t = 0 if r1 == r0 else (c - r0) / (r1 - r0)
            x = gx[i - 1] + (gx[i] - gx[i - 1]) * t
            pts.append((x, y)); sp.append(srow[i - 1] * (1 - t) + srow[i] * t)
        lines.append((pts, sp))
    _FLOW['l'] = lines
    return lines


def heat(v):
    """Stress colour: calm cyan -> white -> orange -> red as the stretch piles up (v = speed / far-field)."""
    stops = [(0.0, (90, 200, 255)), (1.2, (120, 224, 255)), (2.0, (220, 246, 255)), (2.8, (255, 196, 80)), (3.6, (255, 90, 40)),
             (5.0, (255, 40, 30))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b: return kit.lerp(ca, cb, max(0, (v - a) / (b - a)))
    return stops[-1][1]


def corner_boost(x, y):
    """Extra stress colour near the square window's corners (the singular points the lines crowd into)."""
    sx, sy, w, h, rr = HOLE_S
    d = min(math.hypot(x - (sx + a * w / 2), y - (sy + b * h / 2)) for a in (-1, 1) for b in (-1, 1))
    return 3.2 * math.exp(-d / 60.0)


def panel_static(kind='both'):
    """The aluminium skin panel with both windows (cached): skin, rivet lines, window frames + glass."""
    k = ('panel', kind)
    if k in _FLOW: return _FLOW[k]
    img = A.skin_panel(PANEL_W, PANEL_H, seed=3, base=(150, 162, 182), frames=(120, 1140, 2190), stringers=(260, 1560), sheen=True)
    d = ImageDraw.Draw(img)
    cx, cy, r = HOLE_R
    d.ellipse([cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30], fill=(196, 204, 218), outline=INK, width=6)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 40, 70), outline=INK, width=6)
    sx, sy, w, h, rr = HOLE_S
    d.rounded_rectangle([sx - w / 2 - 30, sy - h / 2 - 30, sx + w / 2 + 30, sy + h / 2 + 30], rr + 10, fill=(196, 204, 218), outline=INK, width=6)
    d.rounded_rectangle([sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2], rr, fill=(26, 40, 70), outline=INK, width=6)
    # a dim navy wash so the glowing lines read (the diagram stage look)
    img.alpha_composite(Image.new('RGBA', img.size, (14, 22, 52, 120)))
    _FLOW[k] = img
    return img


def window_sky_small(img, box, round_=True, t=0.0):
    sky = sky_cached(t, 600, 1067)
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    s2 = sky.resize((max(2, int(w * 1.6)), max(2, int(w * 1.6 * 1067 / 600))), Image.BILINEAR)
    lay = layer(img.width, img.height); lay.alpha_composite(s2, (x0 - (s2.width - w) // 2, y0 - (s2.height - h) // 2 - h // 3))
    m = Image.new('L', img.size, 0)
    if round_: ImageDraw.Draw(m).ellipse(box, fill=255)
    else: ImageDraw.Draw(m).rounded_rectangle(box, HOLE_S[4], fill=255)
    img.paste(lay, (0, 0), m)


def flow_frame(t, camx, camy, zoom, show='both', pulse=0.0, dash_speed=160.0, crack=0.0, rip=0.0, glow_k=1.0, lines_k=1.0):
    """Render the panel with the flowing stretch lines for a 2D camera (camx, camy panel px at the frame centre)."""
    base = panel_static().copy()
    lines = flow_lines()
    lay = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    core = Image.new('RGBA', base.size, (0, 0, 0, 0)); dc = ImageDraw.Draw(core)
    x_lo, x_hi = camx - 760 / zoom, camx + 760 / zoom
    for pts, sp in lines:
        if not pts or pts[0][0] < x_lo - 200 or pts[0][0] > x_hi + 200: continue
        prev = None; s_acc = 0.0
        for (a, b, v) in zip(pts, pts[1:], sp):
            vv = v * (1 + .25 * pulse) + corner_boost(*a) * (1 + .6 * pulse) * (a[0] > 1150)
            col = heat(vv)
            d.line([a, b], fill=col + (int(140 * lines_k),), width=10)
            s_acc += math.dist(a, b)
            ph = (s_acc - t * dash_speed * max(.6, min(2.2, v))) % 90
            if ph < 36 and lines_k > .2: dc.line([a, b], fill=(255, 255, 255, int(235 * lines_k)), width=6)
            else: dc.line([a, b], fill=col + (int(255 * lines_k),), width=4)
    glow_l = kit.soft_layer(lay, 7)
    base.alpha_composite(glow_l); base.alpha_composite(core)
    # windows show the sky through them (over the lines)
    cx, cy, r = HOLE_R
    window_sky_small(base, (cx - r, cy - r, cx + r, cy + r), True, t)
    sx, sy, w, h, rr = HOLE_S
    window_sky_small(base, (sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2), False, t)
    dd = ImageDraw.Draw(base)
    dd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=8)
    dd.rounded_rectangle([sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2], rr, outline=INK, width=8)
    # the hot point at the top-right corner of the square window
    hx, hy = sx + w / 2, sy - h / 2
    if glow_k > 0:
        kit.radial(base, hx, hy, 120 + 60 * pulse, (255, 70, 40), (.55 + .35 * pulse) * glow_k, add=True)
        kit.radial(base, hx, hy, 34, (255, 240, 200), (.7 + .3 * pulse) * glow_k, power=.8, add=True)
    if crack > 0: draw_crack(base, hx, hy, crack, rip)
    img = Image.new('RGBA', (W, H), NAVY + (255,))
    v = cine.cam2d(base, zoom, camx, camy, dx=W / 2 - camx, dy=H / 2 - camy)
    img.alpha_composite(v.crop((0, 0, W, H)) if v.size != (W, H) else v)
    return img


CRACK = None


def crack_pts():
    global CRACK
    if CRACK is None:
        rng = np.random.default_rng(9); pts = [(0.0, 0.0)]; a = math.radians(-38)
        for i in range(60):
            a += rng.normal(0, .28); a = max(math.radians(-70), min(math.radians(-10), a))
            L = rng.uniform(10, 22); x, y = pts[-1]; pts.append((x + math.cos(a) * L, y + math.sin(a) * L))
        CRACK = pts
    return CRACK


def draw_crack(img, hx, hy, k, rip=0.0):
    """A fatigue crack from the window corner (k 0..1 = its length); rip opens it into a gap."""
    pts = [(hx + x * (1 + 2.6 * rip), hy + y * (1 + 2.6 * rip)) for x, y in partial(crack_pts(), k)]
    if len(pts) < 2: return
    d = ImageDraw.Draw(img)
    gl = layer(img.width, img.height); dg = ImageDraw.Draw(gl)
    dg.line(pts, fill=(255, 90, 40, 230), width=int(26 + 40 * rip), joint='curve')
    img.alpha_composite(kit.soft_layer(gl, 10))
    d.line(pts, fill=INK, width=int(10 + 30 * rip), joint='curve')
    d.line(pts, fill=(255, 200, 120) if rip < .3 else (20, 16, 20), width=int(3 + 18 * rip), joint='curve')


def s11_cam(T):
    """One continuous pan along the panel: the round window (s11) to the square window (s11b) to its corner (s12)."""
    t0, t1 = 45.38, 46.25                         # the pan runs across the s11 -> s11b cut ('At' 45.78)
    k = smooth(seg(T, t0, t1))
    camx = HOLE_R[0] + (HOLE_S[0] - HOLE_R[0]) * k
    return camx, 930, 1.18 + .04 * math.sin(T * .4)


def s11(u, D, cue):
    T = anim.NOW
    camx, camy, z = s11_cam(T)
    img = flow_frame(T, camx, camy, z, glow_k=smooth(seg(T, 46.4, 47.0)))
    img = fin(img, T, 'navy', bloom_k=.3)
    if not HIDE_UI:
        if T < 45.6:
            tag(img, 'ROUND WINDOW', 540, 300, 60, 'white', pop(u, cue(2) - .05, .3))
            arrow(img, (540, 200), (540, 110), CYAN, 14, 36); arrow(img, (540, 1720), (540, 1810), CYAN, 14, 36)
            chip(img, 'STRETCH', (40, 120, 170), 540, 1640, u, cue(5) - .05, size=48)
            if u > cue(7) - .1:
                chip(img, 'FLOWS SMOOTHLY PAST', (40, 150, 110), 540, 400, u, cue(7) - .1, size=50)
                check(img, 540 + 300, 400 - 2, 40, smooth(seg(u, cue(7), cue(8))))
    return img, {'faces': [], 'avoid': [(0, 100, W, 460)]}


def s11b(u, D, cue):
    T = anim.NOW
    camx, camy, z = s11_cam(T)
    pk = smooth(seg(u, cue(14) - .1, cue(17)))
    z += .25 * pk
    camx += 120 * pk; camy -= 120 * pk
    pulse = .5 + .5 * math.sin((T - 47.0) * 9) if T > 47.4 else 0.0
    img = flow_frame(T, camx, camy, z, pulse=pulse * pk, glow_k=smooth(seg(T, 46.4, 47.0)))
    img = fin(img, T, 'navy', bloom_k=.35)
    if not HIDE_UI:
        if u > cue(11) - .2: tag(img, 'SHARP CORNER', 540, 300, 60, 'white', pop(u, cue(11) - .1, .3))
        if u > cue(14) - .1: chip(img, 'PILES UP', (200, 110, 40), 540, 410, u, cue(14) - .1, size=50, until=cue(16) - .1)
        if u > cue(16) - .1:
            chip(img, 'ONE TINY POINT', RED, 540, 410, u, cue(16) - .1, size=54)
            hx = (HOLE_S[0] + HOLE_S[2] / 2 - camx) * z + W / 2; hy = (HOLE_S[1] - HOLE_S[3] / 2 - camy) * z + H / 2
            arrow(img, (hx - 220, hy - 260), (hx - 40, hy - 50), (255, 255, 255), 14, 38, alpha=smooth(seg(u, cue(16), cue(17))))
    return img, {'faces': [], 'avoid': [(0, 100, W, 470)]}


SQUEEZES = (48.53, 49.18, 49.55, 49.9, 50.25, 50.6, 50.95, 51.3)


def s12(u, D, cue):
    """Squeeze after squeeze the crack grows from the corner; it rips on 'gives way'; METAL FATIGUE."""
    T = anim.NOW
    sx, sy, w, h, rr = HOLE_S; hx, hy = sx + w / 2, sy - h / 2
    z = 1.75 + .35 * smooth(seg(u, 0, 2.2)) - .45 * smooth(seg(u, cue(11) - .2, cue(12) + .3))
    camx = hx - 60 + 120 * smooth(seg(u, 0, 2.2)); camy = hy + 120 - 140 * smooth(seg(u, 0, 2.2))
    n = sum(T >= s for s in SQUEEZES)
    ph = min([T - s for s in SQUEEZES if T >= s] or [9])
    pulse = math.exp(-ph * 6) if ph < 2 else 0.0
    crack = .04 + .5 * smooth(seg(u, cue(4) - .2, cue(8))) + .46 * smooth(seg(u, cue(10), cue(12)))
    crack = min(1.0, crack + .02 * n)
    rip = smooth(seg(u, cue(11) - .05, cue(12) + .2))
    img = flow_frame(T, camx, camy, z, pulse=pulse, crack=crack, rip=rip, lines_k=1 - .6 * rip, glow_k=1.0)
    sxk, syk = shake(u, cue(11), 18, .45)
    if sxk or syk: img = cine.cam2d(img, 1.03, dx=sxk, dy=syk)
    flash(img, u, cue(11), .25, .5, (255, 230, 210))
    img = fin(img, T, 'navy', bloom_k=.35)
    if not HIDE_UI:
        counter(img, 540, 330, int(1000 * n / len(SQUEEZES) * 3) if n else 0, 4, 90, 'SQUEEZES', blur=0)
        if u > cue(5) - .1 and u < cue(11):
            chip(img, 'A TINY CRACK', RED, 540, 520, u, cue(5) - .1, size=50)
        if u > cue(13) - .05:
            stitle(img, 's12mf', [('METAL', 'white', 150), ('FATIGUE', KEY, 170)], 1180, u, cue(13) - .05, stagger=.2)
    return img, {'faces': [], 'avoid': [(0, 200, W, 600), (0, 1100, W, 1560)]}


# ---------------------------------------------------------------- the cross-section (s09, s09b, s10)
SEC = (540, 1000, 330)


def section(img, t, sw=1.0, cx=SEC[0], cy=SEC[1], R=SEC[2], air=1.0, arrows=0.0, ghost=0.0, inward=0.0, people=True):
    """A modern fuselage cross-section seen from the nose: skin ring (radius R*sw), cabin, floor, bins, seats with
    passengers, windows in the ring, warm air dots inside (density air), outward/inward arrows, a dashed ghost ring."""
    Rs = R * sw
    # interior (clipped to the inner circle)
    inner = layer(); di = ImageDraw.Draw(inner)
    ri = Rs - 26
    di.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=(236, 228, 212))
    fy = cy + R * .42
    di.rectangle([cx - ri, fy, cx + ri, cy + ri], fill=(70, 74, 90))
    di.rectangle([cx - ri, fy, cx + ri, fy + 16], fill=(96, 104, 130))
    for s_ in (-1, 1):
        di.rounded_rectangle([cx + s_ * R * .42 - (R * .5 if s_ > 0 else 0), cy - R * .78, cx + s_ * R * .42 + (R * .5 if s_ < 0 else 0), cy - R * .52], 18,
                             fill=(214, 208, 196), outline=INK, width=4)
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=255)
    if people:
        for k, x in enumerate((-.62, -.4, -.18, .18, .4, .62)):
            sxp = cx + x * R
            di.rounded_rectangle([sxp - 34, fy - 130, sxp + 34, fy - 8], 14, fill=A.SEAT, outline=INK, width=3)
            di.rounded_rectangle([sxp - 30, fy - 140, sxp + 30, fy - 110], 10, fill=A.HEADREST, outline=INK, width=3)
    # air molecules inside
    if air > 0:
        air_dots(inner, t, (cx - ri, cy - ri, cx + ri, fy), lambda y: .85 * air, (255, 170, 90), seed=8, r=6, alpha=230, jitter=5)
    img.paste(inner, (0, 0), ImageChops.multiply(inner.split()[3], m))
    if people:
        for k, x in enumerate((-.62, -.18, .4)):
            pl = layer()
            g = actor(pl, 'neutral', 'stand', cx + x * R, fy + 150, .24, t, look=.1 * (k - 1), bphase=k * .7,
                      shirt=[(196, 90, 70), (70, 120, 170), (90, 150, 110)][k], pants='#3a4058')
            mk = Image.new('L', img.size, 0); ImageDraw.Draw(mk).rectangle([0, 0, W, fy - 30], fill=255)
            pl.putalpha(ImageChops.multiply(pl.split()[3], mk)); img.alpha_composite(pl)
        di2 = ImageDraw.Draw(img)
        for k, x in enumerate((-.62, -.4, -.18, .18, .4, .62)):          # armrests / seat fronts cover the legs
            sxp = cx + x * R
            di2.rounded_rectangle([sxp - 40, fy - 50, sxp + 40, fy + 4], 12, fill=P3.rgb_mul(A.SEAT, 1.15), outline=INK, width=3)
    # the skin ring + windows
    d = ImageDraw.Draw(img)
    d.ellipse([cx - Rs - 6, cy - Rs - 6, cx + Rs + 6, cy + Rs + 6], outline=INK, width=8)
    ring = Image.new('L', img.size, 0); dr = ImageDraw.Draw(ring)
    dr.ellipse([cx - Rs, cy - Rs, cx + Rs, cy + Rs], fill=255); dr.ellipse([cx - Rs + 26, cy - Rs + 26, cx + Rs - 26, cy + Rs - 26], fill=0)
    img.paste((214, 220, 232), (0, 0), ring)
    d.ellipse([cx - Rs + 26, cy - Rs + 26, cx + Rs - 26, cy + Rs - 26], outline=INK, width=5)
    for s_ in (-1, 1):
        a = math.radians(-14); wx = cx + s_ * (Rs - 13) * math.cos(a); wy = cy + (Rs - 13) * math.sin(a)
        d.rounded_rectangle([wx - 15, wy - 32, wx + 15, wy + 32], 12, fill=(150, 200, 240), outline=INK, width=4)
    for k in range(24):
        a = 2 * math.pi * k / 24; x, y = cx + math.cos(a) * (Rs - 13), cy + math.sin(a) * (Rs - 13)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(150, 156, 170))
    if ghost > 0:
        n = 60
        for i in range(0, n, 2):
            d.arc([cx - R, cy - R, cx + R, cy + R], 360 * i / n, 360 * (i + 1) / n, fill=(255, 255, 255, int(255 * ghost)), width=5)
    if arrows > 0 or inward > 0:
        for k in range(12):
            a = 2 * math.pi * (k + .5) / 12
            if inward > 0:
                p0 = (cx + math.cos(a) * (Rs + 150), cy + math.sin(a) * (Rs + 150)); p1 = (cx + math.cos(a) * (Rs + 30), cy + math.sin(a) * (Rs + 30))
                arrow(img, p0, p1, (150, 220, 255), 14, 34, alpha=inward)
            else:
                p0 = (cx + math.cos(a) * (Rs - 70), cy + math.sin(a) * (Rs - 70)); p1 = (cx + math.cos(a) * (Rs + 90 * arrows), cy + math.sin(a) * (Rs + 90 * arrows))
                arrow(img, p0, p1, (255, 150, 70), 14, 34, alpha=min(1, arrows * 2))


def outside(T, alt=1.0, dots=True):
    """Outside the section: the thin-blue sky at altitude (sparse air) sliding to the ground at landing (dense air)."""
    img = Image.new('RGBA', (W, H))
    top = kit.lerp((118, 170, 220), (24, 64, 140), alt); low = kit.lerp((200, 220, 236), (120, 176, 232), alt)
    img.paste(vgrad([(0, top), (1, low)]))
    gy = 1520 + 900 * alt
    if gy < H:
        d = ImageDraw.Draw(img)
        d.rectangle([0, gy, W, H], fill=(104, 132, 88)); d.rectangle([0, gy + 40, W, gy + 200], fill=(70, 72, 80))
        for x in range(-100, W, 160): d.rectangle([x + (T * 200) % 160, gy + 112, x + 80 + (T * 200) % 160, gy + 126], fill=(236, 236, 230))
        d.line([(0, gy), (W, gy)], fill=INK, width=5)
    if dots:
        air_dots(img, T, (0, 0, W, min(H, gy)), lambda y: .12 + .7 * (1 - alt), (255, 255, 255), seed=3, r=6, alpha=150)
    return img


def balloon(img, x, y, k, t):
    if k <= .01: return
    r = 40 + 90 * k
    lay = layer(); d = ImageDraw.Draw(lay)
    d.line([(x, y + r * 1.15), (x + 10 * math.sin(t * 2), y + r * 1.15 + 160)], fill=INK, width=4)
    d.ellipse([x - r - 6, y - r * 1.2 - 6, x + r + 6, y + r * 1.1 + 6], fill=INK)
    d.ellipse([x - r, y - r * 1.2, x + r, y + r * 1.1], fill=(226, 64, 70))
    d.ellipse([x - r * .55, y - r * .9, x - r * .1, y - r * .35], fill=(255, 150, 150))
    d.polygon([(x - 14, y + r * 1.2), (x + 14, y + r * 1.2), (x, y + r * 1.02)], fill=(200, 50, 56), outline=INK)
    img.alpha_composite(lay)


def s09(u, D, cue):
    """Up high: a modern airliner comes at us nose-on, its fuselage dissolves into the cross-section; the cabin fills
    with air (pumped), the passengers breathe."""
    T = anim.NOW
    t_x = 1.0                                               # x-ray dissolve
    img = outside(T, 1.0, dots=True)
    if u < t_x + .35:
        cam = P3.Cam((-15.8 + 14 * (1 - ease_out(seg(u, 0, t_x))) * -1, 0.0, -.4), (12.0, 0.0, 0.0), 40.0)
        pl = layer(); P3.render(pl, cam, list(A.place(A.twinjet(), t=(0, 0, 0)).values()), light=SKY_LIGHT, ink_w=2, sil_w=5)
        k = 1 - smooth(seg(u, t_x, t_x + .35))
        pl.putalpha(pl.split()[3].point(lambda v: int(v * k)))
        sec = img.copy()
        section(sec, T, air=.25)
        img = cine.xfade(img, sec, smooth(seg(u, t_x - .2, t_x + .3)))
        img.alpha_composite(pl)
    else:
        air = .25 + .75 * smooth(seg(u, cue(5) - .1, cue(8) + .2))
        section(img, T, air=air)
        if cue(5) - .2 < u < cue(9) + .3 and not HIDE_UI:
            for s_ in (-1, 1):
                arrow(img, (540 + s_ * 120, 1560), (540 + s_ * 120, 1300), (255, 150, 70), 16, 40, alpha=smooth(seg(u, cue(5) - .2, cue(5) + .2)))
    img = fin(img, T, 'altitude', bloom_k=.2)
    if not HIDE_UI:
        chip(img, 'UP HIGH: THIN AIR', (40, 92, 150), 540, 300, u, cue(0) - .05, size=52, until=cue(5) - .2)
        if u > cue(5) - .1: chip(img, 'CABIN: PUMPED FULL OF AIR', (200, 110, 40), 540, 300, u, cue(5) - .1, size=48)
        if u > cue(12) - .15: chip(img, 'SO YOU CAN BREATHE', (60, 130, 80), 540, 1560, u, cue(12) - .15, size=48)
    return img, {'faces': [], 'avoid': [(0, 200, W, 400), (0, 1480, W, 1640)]}


def s09b(u, D, cue):
    T = anim.NOW
    img = outside(T, 1.0)
    sw = 1 + .075 * smooth(seg(u, cue(15) - .15, cue(16) + .1))
    section(img, T, sw=sw, air=1.0, arrows=smooth(seg(u, cue(14) - .1, cue(15) + .2)), ghost=smooth(seg(u, cue(15), cue(16))))
    balloon(img, 870, 470, smooth(seg(u, cue(17) - .1, cue(19) + .1)), T)
    img = fin(img, T, 'altitude', bloom_k=.2)
    if not HIDE_UI:
        stitle(img, 's09sw', [('SWELLS', (255, 170, 90), 130)], 160, u, cue(15) - .05)
        if u > cue(17) - .1: tag(img, 'LIKE A BALLOON', 760, 700, 46, 'white', pop(u, cue(17) - .1, .3))
        tag(img, '(EXAGGERATED)', 540, 1560, 34, (220, 230, 255), pop(u, cue(16), .3) * .9)
    return img, {'faces': [], 'avoid': [(0, 120, W, 330), (0, 1500, W, 1620)]}


FLIGHTS = (41.44, 41.95, 42.3, 42.6)      # extra quick cycles after 'One flight, one squeeze'


def s10(u, D, cue):
    T = anim.NOW
    # landing: altitude falls on 'Every landing', the ring shrinks back on 'shrinks back'
    alt = 1 - smooth(seg(u, cue(0) - .1, cue(2)))
    sh = smooth(seg(u, cue(3) - .1, cue(4) + .1))
    sw = 1.075 - .075 * sh
    # then quick flight cycles: up (swell) and down (shrink)
    ncyc = 0; cyc_ph = 0.0
    for f in FLIGHTS:
        if T >= f:
            ncyc += 1; cyc_ph = T - f
    if ncyc:
        a = math.sin(math.pi * min(1.0, cyc_ph / .48)) if cyc_ph < .48 else 0.0
        sw = 1 + .06 * a; alt = .0 + .9 * a * (u > cue(5) - .1)
    img = outside(T, alt)
    section(img, T, sw=sw, air=1.0, inward=sh * (1 - smooth(seg(u, cue(5) - .2, cue(5)))), ghost=1 - smooth(seg(u, cue(5) - .3, cue(5))))
    img = fin(img, T, 'altitude', bloom_k=.2)
    if not HIDE_UI:
        if u < cue(5) - .1:
            chip(img, 'LANDING', (60, 130, 80), 540, 300, u, cue(0) - .05, size=52)
            if u > cue(3) - .1: tag(img, 'SHRINKS BACK', 540, 1560, 56, 'white', pop(u, cue(3) - .1, .3))
        else:
            # flight arc + counter
            d = ImageDraw.Draw(img)
            pts = [(140 + 800 * i / 40, 520 - 260 * math.sin(math.pi * i / 40)) for i in range(41)]
            for i in range(0, 40, 2): d.line([pts[i], pts[i + 1]], fill=(255, 255, 255), width=7)
            f = min(1.0, cyc_ph / .48) if ncyc else 0
            x, y = path_point(pts, f)
            plane_icon(d, x, y, math.atan2(-260 * math.pi / 40 * math.cos(math.pi * f) / 20, 1), 1.3, (255, 210, 63))
            chip(img, '1 FLIGHT = 1 SQUEEZE', RED, 540, 230, u, cue(5) - .1, size=54)
            counter(img, 540, 1620, ncyc, 3, 80, 'SQUEEZES')
    return img, {'faces': [], 'avoid': [(0, 150, W, 600), (0, 1480, W, 1720)]}


# ---------------------------------------------------------------- macro: the hatch window corner (s07b), the riddle (s08)
def hatch_skin(w=1500, h=2100, crack=0.0, t=0.0):
    """Close-up art of the Comet skin round the hatch window: white top, the blue cheatline band, polished metal below,
    the riveted hatch outline and the squarish window; the fatigue crack runs from the window's top-right corner."""
    img = Image.new('RGBA', (w, h), A.WHITE + (255,)); d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    d.rectangle([0, cy - 210, w, cy + 230], fill=A.CHEAT)
    d.rectangle([0, cy + 230, w, h], fill=A.METAL)
    for y in (cy - 520, cy + 520):
        d.line([(0, y), (w, y)], fill=(176, 182, 192), width=4)
        for x in range(20, w, 44): d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(160, 166, 178))
    for x in (cx - 560, cx + 560):
        d.line([(x, 0), (x, h)], fill=(176, 182, 192), width=4)
        for y in range(20, h, 44): d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(160, 166, 178))
    # hatch panel outline
    d.rounded_rectangle([cx - 330, cy - 420, cx + 330, cy + 420], 40, outline=INK, width=8)
    d.rounded_rectangle([cx - 318, cy - 408, cx + 318, cy + 408], 34, outline=(250, 250, 250), width=3)
    box = A.squarish_window(img, cx, cy - 20, 400, 360, 26, rivets=True, ink=7)
    if crack > 0:
        draw_crack(img, box[2] - 2, box[1] + 2, crack, 0.0)
    return img, box


def s07b(u, D, cue):
    T = anim.NOW
    art, box = hatch_skin(crack=.05 + .95 * smooth(seg(u, 0, cue(15) - (30.58 - 30.58))))
    hx, hy = box[2], box[1]
    z = .62 + .55 * smooth(seg(u, 0, 2.2))
    img = cine.cam2d(art, z, hx - 60, hy + 40, dx=W / 2 - (hx - 60), dy=H / 2 - (hy + 40), roll=-4 + 4 * smooth(u / D)).crop((0, 0, W, H))
    # under water: teal veil, caustics, light rays, drifting particles, a slight wobble
    img.alpha_composite(Image.new('RGBA', img.size, (20, 110, 118, 92)))
    cine.caustics(img, T, box=(0, 0, W, H), col=(200, 255, 236), alpha=.3, scale=1 / 90, res=3)
    cine.shafts(img, [[(200, -50), (420, -50), (900, 1900), (520, 1900)], [(700, -50), (820, -50), (1200, 1500), (1000, 1600)]],
                col=(210, 255, 240), alpha=.2, blur=40)
    cine.motes(img, T, (0, 0, W, H), n=70, col=(220, 255, 240), alpha=150, size=(2, 6), drift=(4, -18))
    cine.wobble(img, (0, 0, W, H), T, amp=2.5, wl=70, speed=2.0)
    img = fin(img, T, 'water', bloom_k=.25)
    if not HIDE_UI:
        sx_ = (hx - (hx - 60)) * z + W / 2; sy_ = (hy - (hy + 40)) * z + H / 2
        if u > cue(14) - .15:
            chip(img, 'THE SHARP CORNER', RED, 540, 380, u, cue(14) - .15, size=54)
            arrow(img, (sx_ - 300, sy_ - 330), (sx_ - 50, sy_ - 50), (255, 255, 255), 16, 40, alpha=smooth(seg(u, cue(14), cue(15))))
        if u > cue(18) - .15: tag(img, 'OF A HATCH WINDOW', 540, 1640, 52, 'white', pop(u, cue(18) - .15, .3))
    return img, {'faces': [], 'avoid': [(0, 260, W, 480), (0, 1560, W, 1720)]}


def _persp_coeffs(src, dst):
    """PIL PERSPECTIVE coefficients mapping output (dst quad) back to input (src quad)."""
    A_ = []; B_ = []
    for (x, y), (u, v) in zip(dst, src):
        A_.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B_.append(u)
        A_.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B_.append(v)
    return np.linalg.solve(np.array(A_, float), np.array(B_, float)).tolist()


def s08(u, D, cue):
    """The riddle: the cracked panel on a workbench under a lamp; an engineer behind it with a magnifier (soft focus)."""
    T = anim.NOW
    img = Image.new('RGBA', (W, H)); img.paste(vgrad([(0, (40, 44, 46)), (.6, (58, 56, 52)), (1, (30, 26, 24))]))
    kit.radial(img, 560, 900, 900, (255, 214, 150), .3)
    # the engineer behind the bench (soft focus), magnifier raised
    bgc = layer()
    g = actor(bgc, 'thinking', anim.add(POSES['hold'], armR=(-20, -30)), 600, 1460, .62, T, look=.45, bphase=.4, **Hg.ENG_A)
    hx, hy, _ = g['hands']['R']; dd = ImageDraw.Draw(bgc)
    dd.ellipse([hx - 70, hy - 150, hx + 70, hy - 10], outline=INK, width=18); dd.ellipse([hx - 70, hy - 150, hx + 70, hy - 10], outline=(180, 140, 70), width=10)
    dd.line([(hx, hy - 10), (hx, hy + 40)], fill=(80, 54, 34), width=22)
    img.alpha_composite(cine.defocus(bgc, 4.0 * (1 - smooth(seg(u, 0, .6))) + 2.5))
    # bench top (perspective) and the panel lying on it
    d = ImageDraw.Draw(img)
    d.polygon([(-200, 1180), (1280, 1180), (1500, H), (-420, H)], fill=(120, 84, 54)); d.line([(-200, 1180), (1280, 1180)], fill=INK, width=6)
    art, box = hatch_skin(1500, 1500, crack=1.0)
    art = art.crop((150, 200, 1350, 1300))
    dst = [(160, 1250), (930, 1240), (1090, 1800), (-20, 1830)]
    coeffs = _persp_coeffs([(0, 0), (art.width, 0), (art.width, art.height), (0, art.height)], dst)
    warped = art.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(dst, fill=255)
    sh = layer(); ImageDraw.Draw(sh).polygon([(p[0] + 18, p[1] + 26) for p in dst], fill=(0, 0, 0, 120)); img.alpha_composite(kit.soft_layer(sh, 12))
    img.paste(warped, (0, 0), m)
    d.line(dst + [dst[0]], fill=INK, width=6)
    kit.radial(img, 620, 1420, 520, (255, 226, 170), .25)
    img = fin(img, T, 'desk', bloom_k=.22)
    faces = [face_box(g, 1.25)]
    if not HIDE_UI:
        qmark(img, 860, 640, 1.25, u, cue(1) - .05, KEY)
        chip(img, 'WHY THE CORNER?', (200, 90, 50), 540, 300, u, cue(4) - .1, size=56)
    return img, {'faces': faces, 'avoid': [(0, 200, W, 400), (700, 480, 1020, 800)]}


# ---------------------------------------------------------------- s13: the paperclip (macro, shallow focus)
CLIP = [(0, 0), (0, -300), (40, -340), (90, -340), (130, -300), (130, 40), (100, 70), (60, 70), (30, 40), (30, -240), (60, -270),
        (80, -240), (80, 0)]


def clip_pts(theta, cx, cy, s=1.0, snap=0.0):
    """The paperclip lying sideways: its two loops to the left of the hinge (cx, cy), the straightened leg to the right,
    bent about the hinge by theta (deg, + = up). snap > 0 breaks the leg off and lets it fall away."""
    body = [(cx + y * s, cy - x * s) for x, y in CLIP]
    a = math.radians(-theta - 40 * snap)
    L = 330 * s
    leg = [(cx + math.cos(a) * L * k, cy + math.sin(a) * L * k) for k in (0, .5, 1)]
    if snap > 0:
        leg = [(x + 90 * snap + 18 * snap * k, y + 160 * snap * snap) for k, (x, y) in enumerate(leg)]
    return body, leg


def wire(img, pts, w=16):
    d = ImageDraw.Draw(img)
    d.line(pts, fill=INK, width=w + 10, joint='curve')
    d.line(pts, fill=(178, 186, 198), width=w, joint='curve')
    d.line([(x - 3, y - 3) for x, y in pts], fill=(244, 248, 255), width=max(2, w // 4), joint='curve')
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - (w + 10) / 2, p[1] - (w + 10) / 2, p[0] + (w + 10) / 2, p[1] + (w + 10) / 2], fill=INK)
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=(178, 186, 198))


BENDS_FAST = (56.45, 57.2)


def s13(u, D, cue):
    T = anim.NOW
    img = Image.new('RGBA', (W, H)); img.paste(vgrad([(0, (44, 34, 40)), (.55, (70, 52, 46)), (1, (40, 30, 28))]))
    cine.bokeh(img, [(140, 260, 1.2), (330, 160, .8), (900, 220, 1.4), (980, 520, .9), (70, 700, 1.0), (760, 120, .7)], 70,
               (255, 214, 150), .4)
    # the person: soft in the background (shallow focus on the clip), watching it
    hd = layer()
    gh = actor(hd, 'thinking' if u < cue(8) else ('surprised' if u > cue(15) else 'neutral'), 'stand', 760, 1700, 1.25, T,
               look=-.5, bphase=.3, shirt='#4a6a9a', pants='#3a4058')
    img.alpha_composite(cine.defocus(hd, 8.0))
    # bend angle: one slow bend on 'once', then fast bends 'a hundred times', snap on 'snaps'
    once = math.sin(math.pi * smooth(seg(u, cue(2) - .1, cue(5) + .3))) * 55
    fast = 0.0; t_f0, t_f1 = cue(8) - .05, cue(15) - .05
    if t_f0 < u < t_f1:
        fast = 50 * math.sin((u - t_f0) * 2 * math.pi * 6.0) * smooth(seg(u, t_f0, t_f0 + .15))
    snap = smooth(seg(u, cue(15) - .05, cue(15) + .35))
    theta = once + fast
    cx, cy, s = 560, 1120, 1.3
    body, leg = clip_pts(theta if snap == 0 else 25, cx, cy, s, snap)
    # the hands (stickman dot hands) with arms from the bottom corners; the left holds the loops, the right the leg
    d = ImageDraw.Draw(img)
    lh = (cx - 300 * s, cy - 40 * s); rh = leg[-1]
    for (x0, y0), (x1, y1) in (((-80, 1990), lh), ((1160, 1990), rh)):
        d.line([(x0, y0), (x1, y1)], fill=INK, width=72); d.line([(x0, y0), (x1, y1)], fill=(246, 246, 242), width=60)
    wire(img, body, 18)
    wire(img, leg, 18)
    heat_k = min(1.0, .1 + (.35 if u > cue(7) else 0) + .55 * smooth(seg(u, t_f0, t_f1)))
    kit.radial(img, cx, cy, 70 + 60 * heat_k, (255, 90, 40), .75 * heat_k, add=True)
    for (x, y) in (lh, rh):
        d.ellipse([x - 44, y - 44, x + 44, y + 44], fill=INK); d.ellipse([x - 37, y - 37, x + 37, y + 37], fill=(246, 246, 242))
    if snap > 0:
        for k in range(8):
            a = 2 * math.pi * k / 8; r0, r1 = 30 + 60 * snap, 60 + 140 * snap
            d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)],
                   fill=(255, 240, 200), width=8)
    img = fin(img, T, 'desk', bloom_k=.3)
    if not HIDE_UI:
        nb = 0
        if u > cue(5) - .1: nb = 1
        if u > t_f0: nb = 1 + int(99 * smooth(seg(u, t_f0, t_f1)))
        counter(img, 540, 330, nb, 3, 96, 'BENDS')
        if cue(5) - .1 < u < cue(8) - .1:
            chip(img, 'ONCE IS FINE', (60, 130, 80), 540, 520, u, cue(5) - .1, size=54)
            check(img, 540 + 230, 518, 40, smooth(seg(u, cue(6), cue(7) + .1)))
        if u > cue(11) - .1 and u < cue(15) - .05: chip(img, 'x100', RED, 540, 520, u, cue(11) - .1, size=70)
        if u > cue(15) - .05: stitle(img, 's13snap', [('SNAP!', KEY, 160)], 560, u, cue(15) - .05)
    sx, sy = shake(u, cue(15), 12, .35)
    if sx or sy: img = cine.cam2d(img, 1.02, dx=sx, dy=sy)
    return img, {'faces': [], 'avoid': [(0, 220, W, 620)]}


# ---------------------------------------------------------------- the shot list
SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [('s01', 1, 0), ('s01b', 1, 14), ('s02', 2, 0), ('s03', 3, 0), ('s04', 4, 0), ('s04b', 4, 10), ('s05', 5, 0),
             ('s05b', 5, 9), ('s06', 6, 0), ('s07', 7, 0), ('s07b', 7, 11), ('s08', 8, 0), ('s09', 9, 0), ('s09b', 9, 13),
             ('s10', 10, 0), ('s11', 11, 0), ('s11b', 11, 9), ('s12', 12, 0), ('s13', 13, 0), ('s14', 14, 0), ('s15', 15, 0)]
END = 1956 / 30                  # 65.20 s (length.json)
NO_PUNCH = ('s01b', 's02', 's04', 's04b', 's05b', 's07b', 's09b', 's10', 's11b', 's12', 's15')
BAND_AT = {}
BAND_FIX = {'s01': 1500, 's01b': 1290, 's15': 1500, 's14': 1790, 's11': 1780, 's11b': 1780, 's12': 1790, 's09': 1760,
            's09b': 1760, 's10': 1810, 's04': 1520, 's05': 1720, 's13': 1760, 's07': 1330, 's07b': 1530, 's04b': 1790}
STILL_AT = {'s01': .0, 's01b': .8, 's02': .95, 's03': .78, 's04': .9, 's04b': .75, 's05': .92, 's05b': .85, 's06': .9,
            's07': .9, 's07b': .9, 's08': .9, 's09': .85, 's09b': .9, 's10': .85, 's11': .92, 's11b': .9, 's12': .93,
            's13': .93, 's14': .95, 's15': .55}

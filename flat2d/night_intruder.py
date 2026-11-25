"""Night Intruder (video 13, `night-intruder`): an 80 s wordless night thriller in the stickman story style with
real perspective sets (scripts/night-intruder/SCRIPT.md is the contract: 15 shots, fixed times).

Look (HANDOFF > Direction set on 2026-11-25, LESSONS > Style test rounds 1-3): white round-head stickmen with a black
outline, `FACE_STYLE='ref'`, `BODY_STYLE='round'`, the bigger-head proportions; persp toon sets night-mapped onto a
LOW-KEY blue ramp (darker than the style test) and lit by three sources only: the phone screen (shots 1-3), the
street lamp (warm sodium stripes through the window blinds, the door gap, the open door in shot 12) and the
thief's flashlight (a visible cone with dust + its hot spot). Characters go on their own layers, moon-tinted and
rim-lit by the nearest source. Close-ups draw big stickman heads (`big_card`: the card drawn at a higher
supersample, not upscaled) and cartoon hands (`hand2d`) on defocused set renders.

usage:
  .venv/bin/python flat2d/night_intruder.py stills OUT [shot ...]          key frame of each shot (540x960)
  .venv/bin/python flat2d/night_intruder.py frames OUT [--t0 A --t1 B]     all frames, 4 processes
  .venv/bin/python flat2d/night_intruder.py encode FRAMES OUT.mp4 [--audio WAV]
  .venv/bin/python flat2d/night_intruder.py sheet FRAMES OUT.jpg            one frame every 2 s
  .venv/bin/python flat2d/night_intruder.py thumbframe OUT.png             the thumbnail frame at 1080x1920
  SIZE=1080x1920 for the final (persp.SS = 2).
"""
import os, sys, math, functools, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'flat2d')); sys.path.insert(0, os.path.join(ROOT, 'stickman', 'scripts'))
_argv = sys.argv; sys.argv = [_argv[0], os.environ.get('TMPDIR', '/tmp')]       # the style-test modules mkdir argv[1]
import style_test_rooms3 as R3
sys.argv = _argv
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import persp as P3
from persp import Part, box, Cam, Light, prism, round_rect2d
import cine, kit, anim, stickman
import toonlight as TL

stickman.R = 132; stickman.SEG_LEG = 170; stickman.SEG_ARM = 112; stickman.OUT = 4.4
stickman.FACE_STYLE = 'ref'; stickman.BODY_STYLE = 'round'

SIZE = tuple(int(v) for v in os.environ.get('SIZE', '540x960').split('x'))
W, H = SIZE
KK = W / 1080                       # px scale vs the 1080 design
P3.SS = 2 if W >= 1080 else 1
FPS = 30
END = 80.0
INKC = (22, 20, 28)
WHITE = (250, 248, 242)
shade = R3.shade
wrect, frect, wall, picture, door_panel = R3.wrect, R3.frect, R3.wall, R3.picture, R3.door_panel

# light colours
SODIUM = (255, 168, 84)             # the street lamp (warm)
TORCH = (236, 244, 255)             # the flashlight (cold white)
PHONE = (150, 214, 255)             # the phone screen
LOW_RAMP = [(0.0, (3, 4, 14)), (.22, (9, 14, 46)), (.5, (20, 36, 98)), (.75, (44, 76, 150)), (1.0, (120, 150, 210))]
NLIGHT = Light(d=(-.3, -.5, .8), amb=.74, bands=(.15, .5, .8), soft=.5, shadow=(30, 40, 110), shadow_k=.25)
LOOK = dict(lift=(.0, .0, .01), gamma=(1.0, 1.0, 1.0), gain=(1.02, 1.02, 1.03), contrast=1.06, sat=1.06,
            sh=(6, 10, 50), sh_k=.12, hi=(255, 246, 230), hi_k=.04)


def S(v): return v * KK
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= b)
def sm(t): t = clamp(t); return t * t * (3 - 2 * t)
def eo(t): t = clamp(t); return 1 - (1 - t) ** 3
def ei(t): t = clamp(t); return t ** 3
def lerp(a, b, t): return a + (b - a) * t
def lerp2(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def lerp3(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def noise(t, s=0): return math.sin(t * 1.7 + s) * .5 + math.sin(t * 3.1 + 2 * s) * .3 + math.sin(t * 7.3 + 3 * s) * .2


def shake(t, amp, freq=1.0, s=0):
    """Handheld wobble (px): smooth multi-sine noise."""
    return amp * noise(t * freq * 2.0, s), amp * noise(t * freq * 2.0 + 11, s + 5)


def jolt(t, t0, amp, dur=.35):
    """A decaying impact shake (px) after t0."""
    u = t - t0
    if u < 0 or u > dur: return 0.0, 0.0
    e = (1 - u / dur) ** 2
    return amp * e * math.sin(u * 95), amp * e * .7 * math.cos(u * 77)


def new(col=(0, 0, 0)): return Image.new('RGBA', SIZE, col + (255,))
def layer(): return Image.new('RGBA', SIZE, (0, 0, 0, 0))


def camxf(img, zoom=1.0, dx=0.0, dy=0.0, roll=0.0, fx=None, fy=None):
    if abs(zoom - 1) < 1e-4 and abs(dx) < .05 and abs(dy) < .05 and abs(roll) < .01: return img
    out = cine.cam2d(img, zoom, fx, fy, dx, dy, roll)
    bg = new((2, 3, 10)); bg.alpha_composite(out); return bg


def night(img, ramp=LOW_RAMP, keep=.14):
    return TL.night_map(img, ramp=ramp, keep=keep)


def finish(img, t, vig=.32, bloom_k=.3, grain=.012):
    img = cine.grade(img, LOOK)
    if bloom_k: img = cine.bloom(img, 190, 26 * KK, bloom_k)
    cine.vignette(img, vig, (2, 3, 14))
    if grain: anim.grain(img, grain, t=t)
    return img


def darken(img, k):
    """Multiply the frame toward black (k = 0 keeps, 1 = black)."""
    if k <= 0: return img
    a = np.asarray(img, np.float32); a[..., :3] *= (1 - k)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), img.mode)


def soft_mask_poly(pts, blur):
    m = Image.new('L', SIZE, 0); ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


def add(img, m, col, k=1.0, mix=0.0): return TL.add_light(img, m, col, k, mix)


# ------------------------------------------------------------------ light helpers
def beam(img, src, dst, r0, r1, col=TORCH, k=.85, t=0.0, motes=True, clipm=None, spot=True):
    """A flashlight beam that READS: a soft-edged cone from src (lens, px) to dst (where it lands, px) widening from
    r0 to r1 px, brighter core, fading along its length, dust motes in it, a hot spot at dst. clipm: L mask."""
    x0, y0 = src; x1, y1 = dst
    L = math.hypot(x1 - x0, y1 - y0) or 1.0; ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux
    def cone(a0, a1, val, blur):
        m = Image.new('L', SIZE, 0)
        ImageDraw.Draw(m).polygon([(x0 + nx * a0, y0 + ny * a0), (x1 + nx * a1, y1 + ny * a1),
                                   (x1 - nx * a1, y1 - ny * a1), (x0 - nx * a0, y0 - ny * a0)], fill=val)
        return m.filter(ImageFilter.GaussianBlur(blur))
    outer = cone(r0, r1, 170, max(2, r1 * .18)); core = cone(r0 * .4, r1 * .45, 140, max(2, r1 * .2))
    m = ImageChops.add(outer, core)
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    u = (((xx - x0) * ux + (yy - y0) * uy) / L).clip(0, 1)
    g = Image.fromarray(((1 - .55 * u) * 255).astype(np.uint8)).resize(SIZE, Image.BILINEAR)
    m = ImageChops.multiply(m, g)
    if clipm is not None: m = ImageChops.multiply(m, clipm)
    add(img, m, col, k, mix=.25)
    if motes:
        mm = m.point(lambda v: 255 if v > 60 else 0)
        bb = mm.getbbox()
        if bb:
            cine.motes(img, t, bb, n=int(40 + L / (6 * KK)), col=(255, 255, 255), alpha=150, size=(1.0 * KK + .6, 3.0 * KK + .8),
                       seed=7, mask=mm)
    if spot:
        s = Image.new('L', SIZE, 0); rr = r1 * 1.1
        ImageDraw.Draw(s).ellipse((x1 - rr, y1 - rr * .75, x1 + rr, y1 + rr * .75), fill=255)
        s = s.filter(ImageFilter.GaussianBlur(rr * .35))
        if clipm is not None: s = ImageChops.multiply(s, clipm)
        add(img, s, col, k * 1.1, mix=.3)
    return img


def lens(img, x, y, r, col=TORCH, k=1.0):
    TL.glow_at(img, x, y, r * 3.5, col, k=k * .8, core=.3, mix=.2)


def rim_layer(lay, dirv, col, k=.9, w=None, blur=None):
    """Rim light on a character layer: the edge facing dirv (screen unit vector toward the light) gets col."""
    w = w or max(2, int(7 * KK)); a = lay.split()[3]
    dx, dy = -int(round(dirv[0] * w)), -int(round(dirv[1] * w))
    sh = ImageChops.offset(a, dx, dy)
    edge = ImageChops.subtract(a, sh)
    edge = edge.filter(ImageFilter.GaussianBlur(blur or max(1, w * .35)))
    edge = ImageChops.multiply(edge, a)
    rgb = Image.new('RGBA', lay.size, tuple(col) + (255,))
    al = edge.point(lambda v: int(min(255, v * k)))
    out = Image.composite(rgb, lay, al)
    out.putalpha(a)
    return out


def tint(lay, col):
    a = np.asarray(lay, np.float32); a[..., :3] *= np.array(col, np.float32) / 255
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def glint(img, x, y, r, col=(235, 245, 255), k=1.0, ang=15):
    """A cold metal glint: a 4-point star + glow."""
    TL.glow_at(img, x, y, r * 1.6, col, k=.7 * k, core=.25, mix=.1)
    m = Image.new('L', SIZE, 0); d = ImageDraw.Draw(m)
    for a, L in ((ang, r * 2.4), (ang + 90, r * 1.5), (ang + 45, r * .8), (ang + 135, r * .8)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.polygon([(x - ca * L, y - sa * L), (x - sa * r * .09, y + ca * r * .09), (x + ca * L, y + sa * L), (x + sa * r * .09, y - ca * r * .09)], fill=255)
    add(img, m.filter(ImageFilter.GaussianBlur(max(1, r * .05))), col, k)


def sparks(img, x, y, u, n=14, r=120, col=(255, 220, 140), seed=1):
    """Small impact sparks (u = s since the hit, 0..0.5): streaks flying out, falling, fading."""
    if u < 0 or u > .55: return
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    lay = layer(); dl = ImageDraw.Draw(lay)
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi); v = rng.uniform(.5, 1.0) * r * KK / .35
        px, py = x + math.cos(a) * v * u, y + math.sin(a) * v * u + 900 * KK * u * u
        tx, ty = px - math.cos(a) * v * .035, py - math.sin(a) * v * .035
        al = int(255 * (1 - u / .55))
        dl.line([(tx, ty), (px, py)], fill=col + (al,), width=max(1, int(4 * KK)))
    img.alpha_composite(lay)
    if u < .12: TL.glow_at(img, x, y, 140 * KK, (255, 230, 170), k=1.0 - u / .12, core=.3)


# ------------------------------------------------------------------ characters
ME = dict(pyjamas='#d9bf94', hair=('wild', '#3a2a22'))
ME_BACK = dict(shirt='#d9bf94', pants='#d9bf94')
THIEF1 = dict(uniform='#3b4252')
THIEF1_C = (59, 66, 82)             # his jacket
MASK_C = (16, 16, 22)
THIEF2 = dict(coat='#15151c', pants='#111117')
HAIR_C = (58, 42, 34)
PROP_K = 1.7                        # props drawn bigger than life next to the big-head figures


def _pose_of(pose):
    return dict(anim.POSES[pose]) if isinstance(pose, str) else dict(pose)


def fig(lay, x, y, s, expr='neutral', pose='stand', t=0.0, look=0.0, lean=0.0, flip=False, idle=1.0, bphase=0.0,
        sx=1.0, **kw):
    """A stickman card with its soles at (x, y) px, s = px per card px. lean (deg, + = toward screen right) rotates
    about the soles; flip mirrors (faces the other way); sx stretches the width (THIEF 2 is broad).
    Returns dict(head=(x, y), R=head radius px, hands={'L'/'R': (x, y, ang)}, look, s, flip)."""
    p = _pose_of(pose)
    p2, dl, dn, dh = anim.secondary(p, t, bphase, idle)
    look = max(-1.0, min(1.0, look + dl)); lean += dn
    c = anim.card(expr, p2, look, **kw)
    head = c.info['head']
    ha = stickman.hand_anchors(p2, fixed=True)
    br = anim.breath(t, phase=bphase) if idle else 1.0
    if flip:
        c = ImageOps.mirror(c); c.info['head'] = (600 - head[0], head[1]); head = c.info['head']
        ha = {('R' if h == 'L' else 'L'): (600 - v[0], v[1], 180 - v[2]) for h, v in ha.items()}
    sc = s * br
    if sx != 1.0: c = c.resize((int(600 * sx), 1000), Image.LANCZOS)
    cwid = c.width
    ox, oy = 1000 - cwid / 2, 1000 - 975                    # the card pasted on a 2000x2000 canvas, soles at the centre
    if abs(lean) > .05:
        big = Image.new('RGBA', (2000, 2000), (0, 0, 0, 0)); big.paste(c, (int(ox), int(oy)))
        c = big.rotate(-lean, resample=Image.BICUBIC, center=(1000, 1000))
        bb = c.getbbox() or (0, 0, 1, 1); c = c.crop(bb); cx0, cy0 = bb[0], bb[1]
    else:
        cx0, cy0 = ox, oy
    cr = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))), Image.LANCZOS)
    px, py = int(round(x + (cx0 - 1000) * sc)), int(round(y + (cy0 - 1000) * sc))
    _paste(lay, cr, px, py)
    def tr(u, v):
        u = (u - 300) * sx + 300
        a = math.radians(lean); u0, v0 = u - 300, v - 975
        u, v = u0 * math.cos(a) - v0 * math.sin(a), u0 * math.sin(a) + v0 * math.cos(a)
        return x + u * sc, y + v * sc
    return dict(head=tr(*head), R=stickman.R * sc, hands={h: tr(v[0], v[1]) + (v[2] + lean,) for h, v in ha.items()},
                look=look, s=sc, flip=flip, lean=lean)


def _paste(lay, im, px, py):
    tmp = Image.new('RGBA', lay.size, (0, 0, 0, 0)); tmp.paste(im, (px, py), im); lay.alpha_composite(tmp)


def hood_mask(lay, g, back=False, col=THIEF1_C):
    """THIEF 1's hood (up) and black balaclava over a placed card: only an eye slot shows (back=True: all hood)."""
    hx, hy = g['head']; R = g['R']; k = R / 98.0 * 98 / 132 * 132 / 98   # card head radius px
    kk = R / stickman.R                                                   # px per card px
    kf = stickman.R / 98.0
    lk = g['look'] * (-1 if g['flip'] else 1) * (-1 if False else 1)
    lk = g['look'] if not g['flip'] else -g['look']
    a = math.radians(g.get('lean', 0))
    d = ImageDraw.Draw(lay)
    ow = max(2, int(stickman.OUT * 2 * kk))
    # hood: a big rounded shell around the head, a little higher, a peak at the top
    hood = [(hx + R * 1.2 * math.cos(th), hy - R * .06 + R * 1.18 * math.sin(th)) for th in np.linspace(0, 2 * math.pi, 48)]
    d.polygon(hood, fill=INKC);
    hood_i = [(hx + R * 1.12 * math.cos(th), hy - R * .06 + R * 1.10 * math.sin(th)) for th in np.linspace(0, 2 * math.pi, 48)]
    d.polygon(hood_i, fill=col)
    if back:
        d.arc((hx - R * .9, hy - R * 1.0, hx + R * .9, hy + R * .9), 200, 340, fill=shade(col, .7), width=ow)
        d.line([(hx, hy - R * 1.1), (hx, hy + R * .8)], fill=shade(col, .75), width=max(1, ow // 2))
        return
    cx0 = hx + lk * 30 * kf * kk
    face = [(cx0 + R * .86 * math.cos(th), hy + R * .06 + R * .9 * math.sin(th)) for th in np.linspace(0, 2 * math.pi, 48)]
    d.polygon(face, fill=INKC)
    face_i = [(cx0 + R * .80 * math.cos(th), hy + R * .06 + R * .84 * math.sin(th)) for th in np.linspace(0, 2 * math.pi, 48)]
    d.polygon(face_i, fill=MASK_C)
    # the eye slot: the card's eyes show through (re-pasted from the card layer by the caller via eye_slot box)
    return (cx0 - R * .66, hy - R * .22, cx0 + R * .66, hy + R * .36)


def masked_head(lay, g, back=False, col=THIEF1_C):
    """Draw hood + balaclava, keeping the card's eyes visible through a rounded slot."""
    eyes = lay.copy()
    box_ = hood_mask(lay, g, back, col)
    if back or not box_: return
    m = Image.new('L', lay.size, 0)
    r = (box_[3] - box_[1]) / 2
    ImageDraw.Draw(m).rounded_rectangle(box_, r, fill=255)
    lay.paste(eyes, (0, 0), m)
    ImageDraw.Draw(lay).rounded_rectangle(box_, r, outline=INKC, width=max(2, int(stickman.OUT * 2 * g['R'] / stickman.R)))


def hair_back(lay, g, col=HAIR_C):
    """ME seen from behind: the back of his head is messy hair."""
    hx, hy = g['head']; R = g['R']; d = ImageDraw.Draw(lay)
    ow = max(2, int(stickman.OUT * 2 * R / stickman.R))
    pts = []
    for i, th in enumerate(np.linspace(math.pi * .92, math.pi * 2.08, 15)):
        rr = R * (1.13 if i % 2 else .98)
        pts.append((hx + rr * math.cos(th), hy - R * .02 + rr * math.sin(th)))
    lower = [(hx + R * 1.0 * math.cos(th), hy + R * .2 * math.sin(th) + R * .55 * math.sin(th)) for th in np.linspace(.0, math.pi, 12)]
    poly = pts + [(hx + R * .98, hy + R * .25)] + [(hx + R * .9 * math.cos(th), hy + R * .25 + R * .45 * math.sin(th)) for th in np.linspace(0, math.pi, 10)] + [(hx - R * .98, hy + R * .25)]
    d.polygon(poly, fill=INKC)
    sh = [(x + (hx - x) * .06, y + (hy - y) * .06) for x, y in poly]
    d.polygon(sh, fill=col)
    for j in range(5):
        a = math.pi * (1.15 + j * .17)
        d.arc((hx - R * .7, hy - R * .7, hx + R * .7, hy + R * .7), math.degrees(a), math.degrees(a) + 25, fill=shade(col, 1.5), width=max(1, ow // 2))


def fist(lay, x, y, r, col=(236, 240, 250), ang=0.0):
    """A gripping hand drawn over a prop's handle: round fist + knuckle creases (reads as a hand, not a dot)."""
    d = ImageDraw.Draw(lay); o = max(2, r * .22)
    d.ellipse((x - r - o, y - r - o, x + r + o, y + r + o), fill=INKC)
    d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for j in (-.45, 0, .45):
        cx, cy = x + ca * r * .35 - sa * r * j, y + sa * r * .35 + ca * r * j
        d.line([(cx - ca * r * .3, cy - sa * r * .3), (cx + ca * r * .25, cy + sa * r * .25)], fill=INKC, width=max(1, int(o * .45)))
    tx, ty = x - ca * r * .1 - sa * r * .75, y - sa * r * .1 + ca * r * .75
    d.ellipse((tx - r * .38, ty - r * .38, tx + r * .38, ty + r * .38), fill=col, outline=INKC, width=max(1, int(o * .5)))


def hand2d(lay, x, y, ang, s, kind='open', col=(236, 240, 252), spread=1.0):
    """A cartoon hand for close-ups (white, black outline): palm + 4 rounded fingers + thumb. ang = direction the
    fingers point (deg, screen), s = palm radius px. kind: 'open', 'grip' (fingers curled round a handle), 'fist'."""
    d = ImageDraw.Draw(lay); o = max(2, s * .13)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang)); nx, ny = -sa, ca
    def caps(p0, p1, w):
        d.line([p0, p1], fill=INKC, width=int(w + 2 * o));
        for p in (p0, p1): d.ellipse((p[0] - w / 2 - o, p[1] - w / 2 - o, p[0] + w / 2 + o, p[1] + w / 2 + o), fill=INKC)
    def capf(p0, p1, w):
        d.line([p0, p1], fill=col, width=int(w))
        for p in (p0, p1): d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=col)
    fw = s * .42
    fingers = []
    for j, (off, ln) in enumerate(((-.62, .95), (-.2, 1.08), (.22, 1.02), (.6, .82))):
        b = (x + ca * s * .55 + nx * s * off * spread, y + sa * s * .55 + ny * s * off * spread)
        if kind == 'open':
            e = (b[0] + ca * s * ln + nx * s * off * .35 * spread, b[1] + sa * s * ln + ny * s * off * .35 * spread)
        elif kind == 'grip':
            e = (b[0] + ca * s * .45 - nx * s * .1, b[1] + sa * s * .45 - ny * s * .1)
        else:
            e = (b[0] + ca * s * .15, b[1] + sa * s * .15)
        fingers.append((b, e))
    th_b = (x + nx * s * .75, y + ny * s * .75)
    th_e = (th_b[0] + (ca * .6 + nx * .55) * s, th_b[1] + (sa * .6 + ny * .55) * s) if kind == 'open' else \
        (th_b[0] + (ca * .55 - nx * .05) * s, th_b[1] + (sa * .55 - ny * .05) * s)
    for b, e in fingers: caps(b, e, fw)
    caps(th_b, th_e, fw * 1.05)
    d.ellipse((x - s - o, y - s - o, x + s + o, y + s + o), fill=INKC)
    d.ellipse((x - s, y - s, x + s, y + s), fill=col)
    for b, e in fingers: capf(b, e, fw)
    capf(th_b, th_e, fw * 1.05)
    capf((x, y), (x + ca * s * .5, y + sa * s * .5), s * 1.5)
    if kind != 'open':
        for b, e in fingers[1:]:
            m = ((b[0] + e[0]) / 2 - ca * s * .1, (b[1] + e[1]) / 2 - sa * s * .1)
            d.line([(m[0] - nx * fw * .5, m[1] - ny * fw * .5), (m[0] - nx * fw * .5 - ca * fw * .3, m[1] - ny * fw * .5 - sa * fw * .3)], fill=INKC, width=max(1, int(o * .7)))


def sleeve(lay, p0, p1, w, col, stripes=True):
    """A pyjama arm (forearm in a striped sleeve) from p0 to p1, w px wide, with a black outline."""
    d = ImageDraw.Draw(lay); o = max(2, w * .08)
    d.line([p0, p1], fill=INKC, width=int(w + 2 * o))
    d.ellipse((p1[0] - w / 2 - o, p1[1] - w / 2 - o, p1[0] + w / 2 + o, p1[1] + w / 2 + o), fill=INKC)
    d.line([p0, p1], fill=col, width=int(w))
    if stripes:
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1; ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        for j in (-.28, .0, .28):
            d.line([(p0[0] - uy * w * j, p0[1] + ux * w * j), (p1[0] - uy * w * j - ux * w * .1, p1[1] + ux * w * j - uy * w * .1)],
                   fill=shade(col, 1.25), width=max(1, int(w * .07)))
    d.line([(p1[0] - uy * w * .5 if stripes else p1[0], p1[1] + ux * w * .5 if stripes else p1[1]),
            (p1[0] + uy * w * .5 if stripes else p1[0], p1[1] - ux * w * .5 if stripes else p1[1])], fill=INKC, width=int(o * 1.2)) if stripes else None


# ------------------------------------------------------------------ 2D props (screen px; m = px per metre)
STEEL = (150, 158, 172); STEEL_HI = (236, 242, 252); STEEL_LO = (62, 66, 80)


def _rot(pts, x, y, ang):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(x + u * ca - v * sa, y + u * sa + v * ca) for u, v in pts]


def ipoly(d, pts, col, o):
    d.polygon(pts, fill=INKC); 
    if o > 0:
        d.line(pts + pts[:1], fill=INKC, width=int(o * 2), joint='curve')
    d.polygon(pts, fill=col)


def lamp2d(lay, x, y, ang, m, hilite=1.0, cord=True):
    """THE metal desk lamp held at its stem (grip at x, y). ang: direction from the grip to the heavy round base
    (deg, screen). The arm + cone shade trail the other way. m = px per metre."""
    d = ImageDraw.Draw(lay); o = max(1.5, .006 * m)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang)); nx, ny = -sa, ca
    P = lambda u, v: (x + ca * u * m + nx * v * m, y + sa * u * m + ny * v * m)
    # heavy base: a thick disc seen edge-on-ish (a rounded slab across the stem)
    base = [P(.08, -.11), P(.08, .11), P(.15, .12), P(.15, -.12)]
    ipoly(d, base, STEEL, o)
    d.line([P(.09, -.1), P(.09, .1)], fill=STEEL_HI, width=max(1, int(o * 1.4 * hilite)))
    # stem (from base to the elbow behind the grip), then the upper arm and the cone shade
    e1 = P(-.30, .02); e2 = P(-.46, -.16)
    for a_, b_, w in ((P(.09, 0), e1, .028), (e1, e2, .024)):
        d.line([a_, b_], fill=INKC, width=int(w * m + 2 * o)); d.line([a_, b_], fill=STEEL, width=int(w * m))
        d.line([(a_[0] + nx * w * m * .25, a_[1] + ny * w * m * .25), (b_[0] + nx * w * m * .25, b_[1] + ny * w * m * .25)],
               fill=STEEL_HI, width=max(1, int(w * m * .25 * hilite)))
    j = e1; r = .03 * m
    d.ellipse((j[0] - r - o, j[1] - r - o, j[0] + r + o, j[1] + r + o), fill=INKC); d.ellipse((j[0] - r, j[1] - r, j[0] + r, j[1] + r), fill=STEEL_LO)
    # the cone shade at e2, opening away from the stem
    a2 = math.atan2(e2[1] - e1[1], e2[0] - e1[0]) + math.radians(55)
    c2, s2 = math.cos(a2), math.sin(a2); n2x, n2y = -s2, c2
    sh = [(e2[0] - n2x * .03 * m, e2[1] - n2y * .03 * m), (e2[0] + n2x * .03 * m, e2[1] + n2y * .03 * m),
          (e2[0] + c2 * .13 * m + n2x * .08 * m, e2[1] + s2 * .13 * m + n2y * .08 * m),
          (e2[0] + c2 * .13 * m - n2x * .08 * m, e2[1] + s2 * .13 * m - n2y * .08 * m)]
    ipoly(d, sh, (120, 128, 146), o)
    d.line([sh[0], sh[3]], fill=STEEL_HI, width=max(1, int(o * 1.2 * hilite)))
    if cord:
        b = P(.15, 0); pts = [b]
        for i in range(1, 9):
            u = i / 8; pts.append((b[0] + ca * .1 * m * u + nx * .05 * m * math.sin(u * 3), b[1] + .35 * m * u * u + sa * .1 * m * u))
        d.line(pts, fill=(14, 14, 18), width=max(1, int(.012 * m)), joint='curve')
        e = pts[-1]; d.rectangle((e[0] - .018 * m, e[1], e[0] + .018 * m, e[1] + .04 * m), fill=(230, 230, 236), outline=INKC)
    return P(.15, 0)


def crowbar2d(lay, x, y, ang, m, L=.62, hilite=1.0):
    """A short crowbar gripped at x, y: ang = direction from the grip to the hooked end."""
    d = ImageDraw.Draw(lay); o = max(1.5, .006 * m); w = .03 * m
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang)); nx, ny = -sa, ca
    P = lambda u, v: (x + ca * u * m + nx * v * m, y + sa * u * m + ny * v * m)
    pts = [P(-.12, 0), P(L * .82, 0)]
    hook = [P(L * .82, 0), P(L * .95, .03), P(L * 1.0, .1), P(L * .96, .16), P(L * .9, .17)]
    for path in (pts, hook):
        d.line(path, fill=INKC, width=int(w + 2 * o), joint='curve')
    for path in (pts, hook):
        d.line(path, fill=(46, 50, 62), width=int(w), joint='curve')
    d.line([P(-.1, -.009), P(L * .82, -.009)], fill=STEEL_HI, width=max(1, int(w * .28 * hilite)))
    d.polygon([P(-.12, -.02), P(-.17, -.005), P(-.17, .005), P(-.12, .02)], fill=(46, 50, 62), outline=INKC)
    return P(L * .97, .12)


def wrench2d(lay, x, y, ang, m, hilite=1.0):
    """THIEF 2's heavy metal object: a big adjustable wrench, gripped at x, y; ang = grip -> jaw."""
    d = ImageDraw.Draw(lay); o = max(1.5, .007 * m)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang)); nx, ny = -sa, ca
    P = lambda u, v: (x + ca * u * m + nx * v * m, y + sa * u * m + ny * v * m)
    body = [P(-.1, -.025), P(.3, -.03), P(.36, -.07), P(.45, -.075), P(.47, -.02), P(.41, -.005), P(.41, .02), P(.47, .04),
            P(.44, .085), P(.35, .08), P(.3, .03), P(-.1, .025)]
    ipoly(d, body, (128, 136, 150), o)
    d.line([P(-.08, -.012), P(.3, -.017)], fill=STEEL_HI, width=max(1, int(.012 * m * hilite)))
    return P(.44, -.06)


def backpack2d(lay, x, y, w, h, ang=0.0, open_=0.0, col=(34, 40, 56)):
    """A backpack (rounded body, front pocket, zipper, a strap), centre x, y, size w x h px."""
    d = ImageDraw.Draw(lay); o = max(2, w * .035)
    pts = _rot([(u * w / 2, v * h / 2) for u, v in [(-1, -.75), (-.8, -1), (.8, -1), (1, -.75), (1.05, .85), (.85, 1), (-.85, 1), (-1.05, .85)]], x, y, ang)
    ipoly(d, pts, col, o)
    pk = _rot([(u * w / 2, v * h / 2) for u, v in [(-.7, .15), (.7, .15), (.75, .85), (-.75, .85)]], x, y, ang)
    ipoly(d, pk, shade(col, 1.25), o * .7)
    z = _rot([(-.8 * w / 2, -.82 * h / 2), (.8 * w / 2, -.82 * h / 2)], x, y, ang)
    d.line(z, fill=(150, 150, 160), width=max(1, int(o * .6)))
    zp = _rot([(.6 * w / 2, -.82 * h / 2)], x, y, ang)[0]
    d.rectangle((zp[0] - o, zp[1] - o * .3, zp[0] + o, zp[1] + o * 2.5), fill=(200, 200, 210))
    st = _rot([(-.4 * w / 2, -h / 2), (-.3 * w / 2, -1.35 * h / 2), (.3 * w / 2, -1.35 * h / 2), (.4 * w / 2, -h / 2)], x, y, ang)
    d.line(st, fill=INKC, width=int(o * 2.4), joint='curve'); d.line(st, fill=shade(col, .8), width=int(o * 1.2), joint='curve')


def laptop2d(lay, x, y, w, ang=0.0, open_=.0, screen=False):
    """A closed (open_=0) or half-open laptop, centre x, y, width w px."""
    d = ImageDraw.Draw(lay); o = max(1.5, w * .02); hh = w * .07
    pts = _rot([(-w / 2, -hh / 2), (w / 2, -hh / 2), (w / 2, hh / 2), (-w / 2, hh / 2)], x, y, ang)
    ipoly(d, pts, (176, 182, 196), o)
    d.line(_rot([(-w / 2 + o, -hh / 2 + o), (w / 2 - o, -hh / 2 + o)], x, y, ang), fill=STEEL_HI, width=max(1, int(o)))
    if open_ > 0:
        lid = _rot([(-w / 2, -hh / 2), (-w / 2 + w * math.cos(math.radians(180 - 100 * open_)) * -1, -hh / 2 - w * math.sin(math.radians(100 * open_))),
                    (-w / 2 + w * math.cos(math.radians(180 - 100 * open_)) * -1 + hh * .6, -hh / 2 - w * math.sin(math.radians(100 * open_))),
                    (-w / 2 + hh * .6, -hh / 2)], x, y, ang)
        ipoly(d, lid, (160, 166, 182), o)


# ------------------------------------------------------------------ the house (one 3D set for shots 4-15)
# Ground floor z=0 (tiles), ceiling 2.7, upstairs floor ZT=2.8. The living room is x 0..6, y 0..7.5; the front wall
# y=0 holds the display cabinet, the window with blinds (street lamp outside), the sideboard with the laptop and the
# front door. The stairs run along the left wall x 0..SX, from the landing (y >= YTOP, z=ZT) DOWN toward -y to the
# hall floor at y=YBOT, enclosed by the partition x=SX that ends at y=YMOUTH (the stair mouth, a header above it).
ZT, ZC, ZUP = 2.8, 2.7, 5.4
SX = 1.1
NST = 11
RISE = ZT / NST
RUN = .28
YTOP = 7.4
YBOT = YTOP - NST * RUN          # 4.32: the bottom of the last step
YMOUTH = 3.6
RX, RY = 6.0, 7.5
DOOR = (3.5, 4.4)                # front door x range on the front wall
WIN = (2.05, 2.95, .95, 2.2)     # window on the front wall (x0, x1, z0, z1)
SIDEB = (1.8, 3.1)               # sideboard x range
CAB = (.15, 1.5)                 # the display cabinet x range
WALLC = (150, 170, 196)
TILE_A, TILE_B = (214, 206, 190), (190, 182, 168)


def tread_z(i): return ZT - (i + 1) * RISE                 # top of step i (i = 0 just below the landing)
def tread_y(i): return YTOP - (i + .5) * RUN               # centre of step i


def stairs_point(s):
    """ME's foot position going down the stairs: s = steps descended (0 = on the landing edge, NST = on the floor)."""
    if s <= 0: return (.55, YTOP + .25 - s * .0, ZT)
    i = min(NST - 1, int(math.floor(s - 1e-6)))
    u = s - math.floor(s - 1e-6) if s < NST else 1.0
    y = YTOP - (s - .5) * RUN if s <= NST else YBOT - (s - NST) * .5
    zi = max(0.0, ZT - s * RISE)                          # continuous: on tread k-1 when s = k
    # the body lifts a little between treads (stepping down)
    return (.55, y, max(0.0, zi + .06 * math.sin(math.pi * clamp(u))))


def rbox(p0, p1, col, r=.08, part=None, cols=None, n=4, z_round=True):
    """A rounded box: an extruded rounded rectangle (soft furniture), x/y rounded corners of radius r."""
    x0, y0, z0 = p0; x1, y1, z1 = p1
    out = round_rect2d(x1 - x0, y1 - y0, r, n)
    P = prism(out, z0, z1, col, ink=True, side_col=col, top_col=(cols or {}).get('top', col), t=((x0 + x1) / 2, (y0 + y1) / 2, 0))
    if part is not None: part.add(P); return part
    return P


@functools.lru_cache(maxsize=4)
def house_parts(door_ang=0.0):
    parts = []
    rng = np.random.default_rng(13)
    # tiled floor
    fl = Part('floor', sil=False); s = .5
    for i in range(int(RX / s)):
        for j in range(int(RY / s)):
            x0, y0 = i * s, j * s
            c = TILE_A if (i + j) % 2 else TILE_B
            fl.poly([(x0, y0, 0), (x0 + s, y0, 0), (x0 + s, y0 + s, 0), (x0, y0 + s, 0)], shade(c, rng.uniform(.95, 1.04)), ink=1.0)
    parts.append(fl)
    rug = Part('rug', sil=False)
    cx, cy = 4.55, 3.7
    rug.poly([(cx + 1.25 * math.cos(a), cy + .95 * math.sin(a), .004) for a in np.linspace(0, 2 * math.pi, 40)[:-1]], (150, 64, 70), ink=1.0)
    rug.decal([(cx + .95 * math.cos(a), cy + .7 * math.sin(a), .005) for a in np.linspace(0, 2 * math.pi, 40)[:-1]], (200, 150, 110), normal=(0, 0, 1))
    rug.decal([(cx + .8 * math.cos(a), cy + .58 * math.sin(a), .006) for a in np.linspace(0, 2 * math.pi, 40)[:-1]], (150, 64, 70), normal=(0, 0, 1))
    parts.append(rug)
    # walls of the living room (the front wall has holes for the door and the window)
    wf = Part('wall_f', sil=False); c = shade(WALLC, 1.02)
    d0, d1 = DOOR; x0, x1, z0, z1 = WIN
    for (a, b, za, zb) in [(0, x0, 0, ZC), (x0, x1, 0, z0), (x0, x1, z1, ZC), (x1, d0, 0, ZC), (d0, d1, 2.15, ZC), (d1, RX, 0, ZC)]:
        wf.poly([(b, 0, za), (a, 0, za), (a, 0, zb), (b, 0, zb)][::-1], c)
    parts.append(wf)
    wl = wall('wall_l', 'x', 0, 0, RY + 2, 0, ZUP, WALLC, 1)
    wr = wall('wall_r', 'x', RX, 0, RY, 0, ZC, shade(WALLC, .96), -1)
    wb = wall('wall_b', 'y', RY, SX, RX, 0, ZC, shade(WALLC, .98), -1)
    parts += [wl, wr, wb]
    # stripes of wallpaper (living room) for texture
    dec = Part('wallpaper', sil=False)
    for yy in np.arange(.2, RY, .32):
        wrect(dec, 'x', RX, yy, yy + .05, .1, ZC - .12, shade(WALLC, .9), -1, e=.002)
    for xx in np.arange(.15, RX, .32):
        if CAB[0] - .05 < xx < CAB[1] + .05 or WIN[0] - .1 < xx < WIN[1] + .1 or DOOR[0] - .12 < xx < DOOR[1] + .12: continue
        wrect(dec, 'y', 0, xx, xx + .05, .1, ZC - .12, shade(WALLC, .92), 1, e=.002)
    parts.append(dec)
    # partition (both faces) and the header over the stair mouth; stairwell walls upstairs
    pa = Part('partition', sil=False)
    pa.poly([(SX + .12, YMOUTH, 0), (SX + .12, RY + 2, 0), (SX + .12, RY + 2, ZC), (SX + .12, YMOUTH, ZC)], shade(WALLC, .97))    # room face (+x)
    pa.poly([(SX, YMOUTH, 0), (SX, YMOUTH, ZT), (SX, RY + 2, ZT), (SX, RY + 2, 0)], shade(WALLC, .9))                          # stair face (-x)
    pa.poly([(SX, YMOUTH, 0), (SX + .12, YMOUTH, 0), (SX + .12, YMOUTH, ZC), (SX, YMOUTH, ZC)][::-1], shade(WALLC, 1.1), ink=True)  # end
    pa.poly([(SX, YMOUTH, ZT), (SX, YTOP, ZT), (SX, YTOP, ZUP), (SX, YMOUTH, ZUP)], shade(WALLC, .9), two=True)
    parts.append(pa)
    hd = Part('header'); box((0, YMOUTH - .1, 2.12), (SX, YMOUTH + .02, ZT), shade(WALLC, 1.05), part=hd); parts.append(hd)
    sw = Part('stair_ceiling', sil=False)
    sw.poly([(0, YMOUTH, ZUP), (SX, YMOUTH, ZUP), (SX, RY + 2, ZUP), (0, RY + 2, ZUP)], WHITE)
    sw.poly([(0, YMOUTH + .02, ZT), (SX, YMOUTH + .02, ZT), (SX, YMOUTH + .02, ZUP), (0, YMOUTH + .02, ZUP)], shade(WALLC, .92), two=True)
    parts.append(sw)
    ce = Part('ceiling', sil=False); ce.poly([(0, 0, ZC), (0, YMOUTH, ZC), (RX, YMOUTH, ZC), (RX, 0, ZC)], WHITE)
    ce.poly([(SX, YMOUTH, ZC), (SX, RY, ZC), (RX, RY, ZC), (RX, YMOUTH, ZC)], WHITE); parts.append(ce)
    # skirting
    tr = Part('trims', sil=False)
    for (ax, v, a0, a1, n) in [('x', RX, 0, RY, -1), ('y', 0, 0, x0 - .02, 1), ('y', 0, x1 + .02, d0 - .1, 1), ('y', 0, d1 + .1, RX, 1),
                               ('x', 0, 0, YMOUTH, 1), ('x', SX + .12, YMOUTH, RY, 1)]:
        wrect(tr, ax, v, a0, a1, 0, .1, WHITE, n, ink=True, e=.004)
    parts.append(tr)
    # the stairs (white risers, wood treads, a dark runner), stringer on the left wall
    for i in range(NST):
        st = Part(f'step{i}')
        z = tread_z(i); y1, y0 = YTOP - i * RUN, YTOP - (i + 1) * RUN
        box((0, y0, 0), (SX, y1, z), WHITE, part=st, cols={'top': (214, 168, 120), 'ny': (236, 234, 228)})
        st.decal([(0, y0 + .005, z + .002), (SX, y0 + .005, z + .002), (SX, y0 + .05, z + .002), (0, y0 + .05, z + .002)], (250, 246, 236), normal=(0, 0, 1))
        frect(st, .22, y0 + .06, SX - .22, y1 - .01, z + .003, (160, 64, 74))
        st.decal([(SX - .22, y0 - .003, z - RISE), (.22, y0 - .003, z - RISE), (.22, y0 - .003, z), (SX - .22, y0 - .003, z)], (104, 42, 52), normal=(0, -1, 0))
        parts.append(st)
    lt = Part('landing', sil=True)
    box((0, YTOP, ZT - .1), (2.6, RY + 2, ZT), WHITE, part=lt, cols={'top': (182, 132, 86)}); parts.append(lt)
    # pictures going down the stair wall (x=0), a wall clock on the partition's room face
    pic = Part('pics', sil=False)
    for k_, yy in enumerate((6.6, 5.6, 4.6)):
        zb = tread_z(int((YTOP - yy) / RUN)) + 1.2
        picture(pic, 'x', 0, yy, zb, .42, .52, [(200, 120, 90), (110, 160, 200), (220, 190, 110)][k_], 1, motif=(240, 236, 220))
    picture(pic, 'x', SX + .12, 5.2, 1.3, .7, .5, (90, 140, 120), 1, motif=(230, 200, 120))
    parts.append(pic)
    # --- front wall dressing: display cabinet, window + blinds, sideboard + laptop, the door frame, coat hooks
    cab = Part('cabinet')
    a, b = CAB
    box((a, 0, 0), (b, .42, 2.0), (120, 82, 56), part=cab, cols={'top': (140, 98, 66)})
    for zz in (.05, .7, 1.15, 1.6):
        cab.decal([(a + .06, .425, zz), (b - .06, .425, zz), (b - .06, .425, zz + .03), (a + .06, .425, zz + .03)], (90, 60, 40), normal=(0, 1, 0))
    for k_, (xx, zz, w_, h_, c_) in enumerate([(.25, .74, .12, .32, (200, 70, 60)), (.4, .74, .1, .36, (70, 120, 190)), (.52, .74, .14, .28, (230, 190, 90)),
                                              (.9, .74, .22, .22, (90, 160, 120)), (1.2, .74, .16, .3, (220, 220, 230)),
                                              (.3, 1.19, .3, .2, (160, 120, 200)), (.75, 1.19, .1, .34, (230, 230, 240)), (1.0, 1.19, .3, .14, (200, 110, 70)),
                                              (.35, 1.64, .2, .25, (240, 200, 120)), (.85, 1.64, .4, .1, (110, 170, 210))]):
        box((xx, .12, zz), (xx + w_, .34, zz + h_), c_, part=cab)
    box((a + .05, .42, .08), (b - .05, .46, .62), (140, 98, 66), part=cab)                 # lower doors
    cab.dot(((a + b) / 2 - .05, .47, .45), .02, (226, 186, 80)); cab.dot(((a + b) / 2 + .05, .47, .45), .02, (226, 186, 80))
    parts.append(cab)
    win = Part('window', sil=False)
    wrect(win, 'y', 0, x0 - .08, x1 + .08, z0 - .1, z1 + .08, WHITE, 1, ink=True, e=.004)
    wrect(win, 'y', 0, x0, x1, z0, z1, (60, 40, 30), 1, e=.005)
    for k_ in range(14):                                       # blinds: lit slats (street lamp behind) with dark gaps
        zz = z0 + .02 + k_ * (z1 - z0) / 14
        wrect(win, 'y', 0, x0 + .01, x1 - .01, zz, zz + (z1 - z0) / 14 * .62, (150, 120, 92), 1, e=.006)
    parts.append(win)
    sb = Part('sideboard')
    a, b = SIDEB
    rbox((a, .02, 0), (b, .5, .78), (96, 70, 52), r=.05, part=sb, cols={'top': (120, 88, 64)})
    for xx in (a + .1, (a + b) / 2 + .03):
        sb.decal([(xx, .505, .12), (xx + (b - a) / 2 - .16, .505, .12), (xx + (b - a) / 2 - .16, .505, .66), (xx, .505, .66)], (110, 80, 60), ink=True, normal=(0, 1, 0))
    box((2.0, .12, .78), (2.16, .26, 1.05), (210, 210, 222), part=sb)                          # a vase
    parts.append(sb)
    df = Part('doorframe', sil=False)
    d0, d1 = DOOR
    wrect(df, 'y', 0, d0 - .1, d0, 0, 2.22, WHITE, 1, ink=True, e=.006); wrect(df, 'y', 0, d1, d1 + .1, 0, 2.22, WHITE, 1, ink=True, e=.006)
    wrect(df, 'y', 0, d0 - .1, d1 + .1, 2.15, 2.25, WHITE, 1, ink=True, e=.006)
    parts.append(df)
    hooks = Part('coats')
    for k_, (xx, c_) in enumerate([(4.75, (150, 70, 60)), (5.1, (70, 100, 140))]):
        rbox((xx - .15, .02, .95), (xx + .15, .2, 1.7), c_, r=.06, part=hooks)
    box((4.55, .0, 1.72), (5.35, .06, 1.78), (120, 82, 56), part=hooks)
    rbox((4.55, .05, 0), (5.3, .4, .42), (90, 66, 50), r=.04, part=hooks)                      # shoe bench
    parts.append(hooks)
    # right side: sofa (rounded), coffee table, TV, floor lamp (off), plant
    so = Part('sofa')
    rbox((3.95, 2.55, 0), (4.85, 4.85, .44), (70, 110, 150), r=.12, part=so)
    rbox((3.95, 2.55, .44), (4.18, 4.85, .95), (70, 110, 150), r=.1, part=so)                  # back
    rbox((3.95, 2.4, 0), (4.85, 2.7, .66), (64, 100, 140), r=.12, part=so)                     # arms
    rbox((3.95, 4.7, 0), (4.85, 5.0, .66), (64, 100, 140), r=.12, part=so)
    for yy in (2.75, 3.75):
        rbox((4.2, yy, .44), (4.8, yy + .95, .56), (84, 126, 168), r=.12, part=so)
    parts.append(so)
    ct = Part('ctable'); rbox((5.0, 3.2, .0), (5.5, 4.3, .4), (120, 86, 60), r=.06, part=ct, cols={'top': (140, 100, 70)})
    box((5.1, 3.4, .4), (5.35, 3.7, .45), (200, 70, 60), part=ct); parts.append(ct)
    tv = Part('tv'); box((RX - .45, 2.8, 0), (RX, 4.6, .5), (60, 50, 46), part=tv); box((RX - .12, 2.95, .55), (RX - .06, 4.45, 1.35), (24, 26, 34), part=tv)
    parts.append(tv)
    pl = Part('plant'); rbox((5.5, 6.7, 0), (5.85, 7.05, .4), (180, 90, 60), r=.12, part=pl)
    for k_ in range(7):
        a_ = k_ * 2 * math.pi / 7
        pl.line((5.67, 6.87, .4), (5.67 + .35 * math.cos(a_), 6.87 + .35 * math.sin(a_), .9 + .3 * (k_ % 2)), .07, (70, 140, 80))
    parts.append(pl)
    return parts


def door_part(ang):
    """The front door leaf (hinged at x=DOOR[1], opens inward toward +y by ang deg)."""
    d0, d1 = DOOR; Wd = d1 - d0; a = math.radians(ang)
    hx, hy = d1, 0.0
    def P(u, z, off=0.0):         # u = distance from the hinge along the leaf (0..Wd), off = thickness
        return (hx - u * math.cos(a) - off * math.sin(a), hy + u * math.sin(a) - off * math.cos(a) * -1 * 0 + off * 0, z)
    dp = Part('door', sil=True)
    col = (56, 86, 74)
    pts = lambda off: [(hx - u * math.cos(a) + off * math.sin(a), hy + u * math.sin(a) + off * math.cos(a), z) for u, z in ((0, 0), (Wd, 0), (Wd, 2.15), (0, 2.15))]
    q0 = pts(0.0); q1 = pts(.05)
    dp.poly(q1, col, ink=True, two=True)
    dp.poly([q1[1], q0[1], q0[2], q1[2]], shade(col, .8), ink=True, two=True)
    for (u0, u1, z0, z1) in ((.12, Wd - .12, 1.2, 2.0), (.12, Wd - .12, .15, 1.05)):
        dp.decal([(hx - u * math.cos(a) + .052 * math.sin(a), hy + u * math.sin(a) + .052 * math.cos(a), z) for u, z in ((u0, z0), (u1, z0), (u1, z1), (u0, z1))],
                 shade(col, .9), ink=True, normal=(math.sin(a), math.cos(a), 0))
    kx = hx - (Wd - .1) * math.cos(a) + .09 * math.sin(a); ky = (Wd - .1) * math.sin(a) + .09 * math.cos(a)
    dp.dot((kx, ky, 1.0), .035, (226, 186, 80), ink=True)
    return dp


HOUSE_ORDER = ['floor', 'rug', 'wall_l', 'wall_r', 'wall_b', 'wall_f', 'stair_ceiling', 'ceiling', 'wallpaper', 'trims', 'window', 'doorframe', 'pics']


def outside_door(img, cam, k=1.0):
    """What the open door shows: the street at night (a sodium-lit pavement + lamp post)."""
    d0, d1 = DOOR
    q = [cam.p((d0, -.02, 0)), cam.p((d1, -.02, 0)), cam.p((d1, -.02, 2.15)), cam.p((d0, -.02, 2.15))]
    m = soft_mask_poly(q, 0)
    out = layer(); d = ImageDraw.Draw(out)
    d.polygon(q, fill=(40, 30, 40, 255))
    lx = cam.p((d0 + .3, -3.0, 0)); lt = cam.p((d0 + .3, -3.0, 3.2))
    yy = q[0][1]
    g = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    bb = m.getbbox() or (0, 0, 1, 1)
    for i in range(24):
        f = i / 23; y = bb[1] + (bb[3] - bb[1]) * f
        c = lerp3((70, 50, 60), (255, 190, 110), f ** 1.6)
        gd.rectangle((bb[0], y, bb[2], y + (bb[3] - bb[1]) / 23 + 1), fill=tuple(int(v) for v in c) + (255,))
    out.alpha_composite(g)
    d.line([lx, lt], fill=(20, 18, 26, 255), width=max(2, int(cam.px_per_m((d0, -3, 1.5)) * .08)))
    TL.glow_at(out, lt[0], lt[1], cam.px_per_m((d0, -3, 3)) * .9 * k, (255, 200, 120), k=1.0)
    out.putalpha(ImageChops.multiply(out.split()[3], m))
    img.alpha_composite(out)


def render_house(cam, door_ang=0.0, extra=(), order=HOUSE_ORDER, fg_d=0.0, fg_blur=0.0, exclude=()):
    """Far set (night-mapped) + list of near parts (rendered separately, for the foreground blur)."""
    img = new((3, 4, 14))
    parts = [p for p in house_parts() if p.name not in exclude] + [door_part(door_ang)] + list(extra)
    far, near = R3.split_near(parts, cam, fg_d) if fg_d else (parts, [])
    if door_ang > 1: outside_door(img, cam)
    P3.render(img, cam, far, light=NLIGHT, order=order, ink=INKC, ink_w=3.2 * KK, sil_w=6.0 * KK)
    img = night(img)
    return img, near


def near_layer(cam, near, blur):
    if not near: return None
    lay = layer(); P3.render(lay, cam, near, light=NLIGHT, ink=INKC, ink_w=3.2 * KK, sil_w=6.0 * KK)
    lay = night(lay)
    return cine.defocus(lay, blur * KK) if blur else lay


def blinds_light(img, cam, k=1.0, door_gap=True, clipm=None, window=True):
    """The street lamp: warm stripes thrown by the window blinds onto the floor (+ a faint glow at the window),
    and a hot line in the gap under the front door."""
    x0, x1, z0, z1 = WIN
    Ld = np.array([.18, .62, -.55]); Ld = Ld / np.linalg.norm(Ld)          # from the lamp outside, into the room
    m = Image.new('L', SIZE, 0); d = ImageDraw.Draw(m)
    def hit(p): t = -p[2] / Ld[2]; return (p[0] + Ld[0] * t, p[1] + Ld[1] * t, .003)
    n = 14
    for i in range(n):
        za = z0 + .02 + i * (z1 - z0) / n; zb = za + (z1 - z0) / n * .55
        q = [hit((x0, 0, za)), hit((x1, 0, za)), hit((x1, 0, zb)), hit((x0, 0, zb))]
        if all(cam.depth(p) > .2 for p in q): d.polygon([cam.p(p) for p in q], fill=210)
    m = m.filter(ImageFilter.GaussianBlur(1.5 * KK + .5))
    if clipm is not None: m = ImageChops.multiply(m, clipm)
    add(img, m, SODIUM, .55 * k, mix=.35)
    if not window: return
    wm = Image.new('L', SIZE, 0); wd = ImageDraw.Draw(wm)
    for i in range(n):                                         # the lit slats of the blinds themselves
        za = z0 + .02 + i * (z1 - z0) / n; zb = za + (z1 - z0) / n * .62
        q = [(x0 + .01, .008, za), (x1 - .01, .008, za), (x1 - .01, .008, zb), (x0 + .01, .008, zb)]
        if all(cam.depth(p) > .2 for p in q): wd.polygon([cam.p(p) for p in q], fill=255)
    add(img, wm, SODIUM, .55 * k, mix=.75)
    c = ((x0 + x1) / 2, .02, (z0 + z1) / 2)
    if cam.depth(c) > .3:
        TL.glow_at(img, *cam.p(c), cam.px_per_m(c) * .9, SODIUM, k=.45 * k, core=0)
    if door_gap:
        a, b = (DOOR[0], .002, .002), (DOOR[1], .002, .002)
        if cam.depth(a) > .3 and cam.depth(b) > .3:
            TL.under_door(img, cam, a, b, depth=.5, col=SODIUM, k=.7 * k)


# ------------------------------------------------------------------ characters in the set
PIN = dict(armL=(85, 95), armR=(95, 100), legL=(-30, 40), legR=(-10, 60), _side=True, _name='pin')
POSE = dict(
    lamp_high=dict(armL=(75, 100), armR=(-155, -178), legL=(10, 1), legR=(-10, -1)),
    lamp_ready=dict(armL=(40, 70), armR=(-130, -175), legL=(12, 2), legR=(-12, -2)),
    back_wall=dict(armL=(30, 15), armR=(-120, -170), legL=(8, 1), legR=(-8, -1)),
    stuff=dict(armL=(-40, -95, .9), armR=(-30, -80, .9), legL=(-12, 2), legR=(12, 4), _side=True, _name='stuff'),
    frozen=dict(armL=(35, 60), armR=(-35, -60), legL=(14, 2), legR=(-14, -2)),
    swing_back=dict(armL=(-60, -100), armR=(140, 175), legL=(-25, 5), legR=(25, 50), _side=True, _name='swingb'),
    swing_fwd=dict(armL=(30, 0), armR=(-90, -92), legL=(-30, 8), legR=(28, 40), _side=True, _name='swingf'),
    dodge=dict(armL=(60, 100), armR=(-120, -165), legL=(-20, 5), legR=(20, 30), _side=True, _name='dodge'),
    lunge=dict(armL=(-40, -80), armR=(-150, -110), legL=(-35, 10), legR=(30, 60), _side=True, _name='lunge'),
    hit=dict(armL=(-60, -90), armR=(-80, -70), legL=(-35, 10), legR=(30, 60), _side=True, _name='hit'),
    hurt=dict(armL=(20, 40), armR=(-10, 20), legL=(15, 30), legR=(-25, 5), _side=True, _name='hurt'),
    shove=dict(armL=(-85, -90), armR=(-80, -86), legL=(-40, 10), legR=(35, 60), _side=True, _name='shove'),
    fall=dict(armL=(120, 150), armR=(-100, -140), legL=(-40, -20), legR=(10, 40), _side=True, _name='fall'),
    lie=dict(armL=(60, 90), armR=(-50, -80), legL=(8, 1), legR=(-8, -1)),
    kneel=dict(armL=(-20, -60, .9), armR=(-25, -60, .9), legL=(-80, 10), legR=(-60, 20), _side=True, _name='kneel'),
    walk_a=dict(armL=(12, 4), armR=(-6, -2), legL=(4, 0), legR=(-14, -2)),
    raise_obj=dict(armL=(25, 10), armR=(-160, -175), legL=(14, 2), legR=(-14, -2)),
    shield=dict(armL=(-25, -150, 1.0, .8), armR=(25, 150, 1.0, .8), legL=(14, 2), legR=(-14, -2)),
    push_up=dict(armL=(10, 5), armR=(-10, -5), legL=(10, 1), legR=(-10, -1)),
)


def mix_pose(a, b, u):
    """Blend two pose dicts (joint angles), keeping a's style keys."""
    a, b = _pose_of(a), _pose_of(b); out = dict(a)
    for k_ in ('armL', 'armR', 'legL', 'legR'):
        va, vb = a[k_], b[k_]; n = max(len(va), len(vb))
        va = tuple(va) + (1.0,) * (n - len(va)); vb = tuple(vb) + (1.0,) * (n - len(vb))
        out[k_] = tuple(x + (y - x) * u for x, y in zip(va, vb))
    if u > .5:
        for k_ in ('_side', '_name'):
            if k_ in b: out[k_] = b[k_]
            elif k_ in out: out.pop(k_)
    return out


def at3d(cam, P, h):
    """Screen soles (x, y) and card scale s for a figure of height h m at world point P, plus px per metre."""
    C = cam.to_cam([P])[0]
    if C[2] < .3: return None
    x, y = cam.proj_cam(C[None])[0]; ppm = float(cam.fpx / C[2])
    return float(x), float(y), h * ppm / 930.0, ppm


def me(lay, x, y, s, t, expr='worried', pose='stand', look=0.0, lean=0.0, flip=False, back=False, lamp=None, idle=1.0,
       m=None, **kw):
    """ME (20s, messy hair, mustard striped pyjamas, barefoot). lamp: grip angle (deg) of the metal lamp in his
    right hand, or None. back: seen from behind (hair over the head, no pyjama buttons)."""
    g = fig(lay, x, y, s, expr, pose, t, look, lean, flip, idle, **(ME_BACK if back else ME), **kw)
    if back: hair_back(lay, g)
    m = (m or s * 930 / 1.75) * PROP_K
    if lamp is not None:
        hx, hy, ha = g['hands']['R']
        lamp2d(lay, hx, hy, lamp, m)
        fist(lay, hx, hy, g['R'] * .3, ang=lamp)
    return g


def thief1(lay, x, y, s, t, expr='angry', pose='stand', look=0.0, lean=0.0, flip=False, back=False, bar=None, idle=1.0,
           pack=False, m=None):
    """THIEF 1: dark hooded jacket (hood up), black balaclava (eyes only), a short crowbar (bar = grip angle in his
    right hand, 'hip' = hanging at his hip, None = gone), backpack on his back (pack=True, side views)."""
    m = (m or s * 930 / 1.75) * PROP_K
    pl = layer()
    g = fig(pl, x, y, s, expr, pose, t, look, lean, flip, idle, **THIEF1)
    if pack:
        hx, hy = g['head']; R = g['R']; d = -1 if (g['look'] >= 0) != g['flip'] else 1
        d = -1 if g['look'] > 0 else 1
        if flip: d = -d
        bp = layer(); backpack2d(bp, hx + d * R * .95, hy + R * 2.3, R * 1.1, R * 1.6, ang=d * 8, col=(30, 34, 48))
        bp.alpha_composite(pl); pl = bp
    masked_head(pl, g, back)
    if bar == 'hip':
        hx, hy = g['head']; R = g['R']
        crowbar2d(pl, hx + R * .55, hy + R * 3.0, 95, m * .55)
    elif bar is not None:
        hx, hy, ha = g['hands']['R']
        crowbar2d(pl, hx, hy, bar, m)
        fist(pl, hx, hy, g['R'] * .3, col=THIEF1_C, ang=bar)
    lay.alpha_composite(pl)
    return g


def thief2(lay, x, y, s, t, pose='stand', look=0.0, lean=0.0, idle=1.0, obj=None, m=None):
    """THIEF 2: tall, broad, a black silhouette (the card tinted near-black), a big wrench in his right hand."""
    m = (m or s * 930 / 2.0) * 1.15
    pl = layer()
    g = fig(pl, x, y, s, 'angry', pose, t, look, lean, False, idle, sx=1.28, **THIEF2)
    a = np.asarray(pl, np.uint8).copy(); a[..., :3] = (12, 12, 17)      # a flat silhouette: no face, no clothes detail
    pl = Image.fromarray(a, 'RGBA')
    if obj is not None:
        hx, hy, ha = g['hands']['R']
        wrench2d(pl, hx, hy, obj, m)
        fist(pl, hx, hy, g['R'] * .32, col=(16, 16, 22), ang=obj)
    lay.alpha_composite(pl)
    return g


def light_chars(lay, rims=(), tint_col=(150, 168, 215), k_tint=1.0):
    """Moon-ish tint (low key) then rim lights [(dir, col, k)] on a character layer."""
    lay = tint(lay, tint_col) if k_tint else lay
    for dv, col, k in rims: lay = rim_layer(lay, dv, col, k)
    return lay


# ------------------------------------------------------------------ big close-up heads
_heads = {}


def big_card(expr, pose='stand', look=0.0, mult=2.0, **kw):
    """The stickman card drawn at mult x the card size (600*mult x 1000*mult) with a matching supersample, so close-ups
    stay crisp (an upscaled card goes soft). stickman.draw ends with a resize to (W, H): intercepted here."""
    key = (expr, repr(sorted(_pose_of(pose).items())) if not isinstance(pose, str) else pose, round(look, 2), round(mult, 2),
           tuple(sorted(kw.items())))
    if key in _heads: return _heads[key]
    if len(_heads) > 80: _heads.clear()
    oldS = stickman.S; Sm = max(4, int(math.ceil(2.4 * mult)))
    orig = Image.Image.resize
    def rs(self, size, *a, **k):
        if tuple(size) == (stickman.W, stickman.H) and self.size == (stickman.W * Sm, stickman.H * Sm):
            size = (int(stickman.W * mult), int(stickman.H * mult))
        return orig(self, size, *a, **k)
    stickman.S = Sm; Image.Image.resize = rs
    try:
        c = stickman.draw(expr=expr, pose=pose, color='#f6f6f2', look=look, fixed=True, **kw)
    finally:
        stickman.S = oldS; Image.Image.resize = orig
    hx, hy = c.info['head']
    c.info['head_px'] = (hx * mult, hy * mult); c.info['R_px'] = stickman.R * mult
    _heads[key] = c
    return c


def paste_card(lay, c, hx, hy, scale=1.0, rot=0.0):
    """Paste a big card so its head centre lands at (hx, hy) px; scale on top of the card's own size; rot deg (ccw)."""
    cx, cy = c.info['head_px']
    im = c
    if abs(scale - 1) > 1e-3: im = c.resize((max(1, int(c.width * scale)), max(1, int(c.height * scale))), Image.LANCZOS); cx *= scale; cy *= scale
    if abs(rot) > .05:
        big = Image.new('RGBA', (im.width * 2, im.height * 2), (0, 0, 0, 0)); big.paste(im, (int(im.width - cx), int(im.height - cy)))
        big = big.rotate(rot, resample=Image.BICUBIC, center=(im.width, im.height))
        _paste(lay, big, int(hx - im.width), int(hy - im.height))
    else:
        _paste(lay, im, int(round(hx - cx)), int(round(hy - cy)))


# ------------------------------------------------------------------ the bedroom (shots 1-3): defocused background
@functools.lru_cache(maxsize=4)
def bedroom_bg(which):
    """A dark, defocused render of the bedroom behind the nightstand macros (cached per shot)."""
    parts, w, d = R3.bedroom()
    parts = [p for p in parts if p.name not in ('mushroom', 'nstand', 'toybox', 'shelf_toys')]
    back, front, quilt = R3.bed_parts()
    if which == 1: cam = Cam((2.2, 2.5, .62), (2.6, 4.0, .9), fov=50, size=SIZE)
    else: cam = Cam((2.6, 2.4, 1.25), (2.1, 3.3, .45), fov=55, size=SIZE)
    img = new((3, 4, 14))
    P3.render(img, cam, parts + [back, front, quilt], light=NLIGHT, order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'trims', 'corners', 'rug'],
              ink=INKC, ink_w=3.2 * KK, sil_w=6.0 * KK)
    img = night(img)
    img = darken(img, .45)
    return cine.defocus(img, 20 * KK)


def phone_screen(w, h, lit, t, tilt=0.0):
    """The phone lock screen (RGBA w x h): dark wallpaper, a big 00:00, the date, flashlight + camera icons."""
    im = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = w * .13
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=(12, 12, 16, 255))
    sx0, sy0, sx1, sy1 = w * .05, h * .035, w * .95, h * .965
    if lit <= 0:
        d.rounded_rectangle((sx0, sy0, sx1, sy1), r * .8, fill=(18, 20, 28, 255))
        d.line([(sx0 + w * .15, sy0 + h * .1), (sx0 + w * .45, sy0 + h * .02)], fill=(40, 44, 60, 255), width=max(1, int(w * .02)))
        return im
    scr = Image.new('RGBA', im.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(scr)
    for i in range(30):
        f = i / 29; y0 = sy0 + (sy1 - sy0) * f
        c = lerp3((40, 52, 120), (110, 60, 130), f ** 1.3)
        ds.rectangle((sx0, y0, sx1, y0 + (sy1 - sy0) / 29 + 1), fill=tuple(int(v) for v in c) + (255,))
    for (cx, cy, rr, c) in ((.25, .72, .35, (150, 90, 170)), (.8, .62, .3, (60, 120, 200))):
        ds.ellipse((w * (cx - rr), h * cy - w * rr, w * (cx + rr), h * cy + w * rr), fill=c + (120,))
    scr = scr.filter(ImageFilter.GaussianBlur(w * .02))
    mk = Image.new('L', im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((sx0, sy0, sx1, sy1), r * .8, fill=255)
    im.paste(scr, (0, 0), mk); d = ImageDraw.Draw(im)
    f1 = kit.font(max(8, int(w * .31)), bold=True); f2 = kit.font(max(6, int(w * .065)), bold=True)
    tw = kit.text_w('00:00', f1)
    d.text(((w - tw) / 2, h * .2), '00:00', font=f1, fill=(255, 255, 255, 255))
    dt = 'Thursday, 26 November'; tw2 = kit.text_w(dt, f2)
    d.text(((w - tw2) / 2, h * .155), dt, font=f2, fill=(235, 235, 250, 255))
    # lock + bottom icons
    lx, ly = w / 2, h * .1
    d.rounded_rectangle((lx - w * .035, ly - w * .01, lx + w * .035, ly + w * .05), w * .01, fill=(255, 255, 255, 255))
    d.arc((lx - w * .025, ly - w * .045, lx + w * .025, ly + w * .02), 180, 360, fill=(255, 255, 255, 255), width=max(1, int(w * .012)))
    for ix in (.18, .82):
        cx, cy, rr = w * ix, h * .9, w * .075
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(40, 40, 60, 200))
        if ix < .5: d.rectangle((cx - rr * .25, cy - rr * .55, cx + rr * .25, cy + rr * .55), fill=(255, 255, 255, 230))
        else: d.rounded_rectangle((cx - rr * .55, cy - rr * .35, cx + rr * .55, cy + rr * .45), rr * .15, fill=(255, 255, 255, 230))
    d.rounded_rectangle((w * .35, h * .945, w * .65, h * .952), 2, fill=(255, 255, 255, 200))
    if lit < 1:
        a = np.asarray(im, np.float32); dark = np.array([18, 20, 28], np.float32)
        a[..., :3] = a[..., :3] * lit + dark * (1 - lit); im = Image.fromarray(a.astype(np.uint8), 'RGBA')
    return im


def wood_top(lay, top_y, bot_y, xl, xr, vx, col=(92, 64, 44)):
    """A nightstand top seen from low: a trapezoid from the back edge (top_y) to the front edge (bot_y) with grain
    lines converging toward vx; then the front edge band."""
    d = ImageDraw.Draw(lay)
    back_l, back_r = lerp(xl, vx, .35), lerp(xr, vx, .35)
    d.polygon([(back_l, top_y), (back_r, top_y), (xr, bot_y), (xl, bot_y)], fill=col + (255,))
    for j in range(9):
        f = (j + .5) / 9
        d.line([(lerp(back_l, back_r, f), top_y), (lerp(xl, xr, f), bot_y)], fill=shade(col, .86) + (255,), width=max(1, int(S(3))))
    d.line([(back_l, top_y), (back_r, top_y)], fill=INKC + (255,), width=max(2, int(S(5))))
    d.rectangle((xl, bot_y, xr, bot_y + S(70)), fill=shade(col, .7) + (255,), outline=INKC + (255,), width=max(2, int(S(5))))
    d.line([(xl, bot_y + S(4)), (xr, bot_y + S(4))], fill=shade(col, 1.25) + (255,), width=max(1, int(S(4))))


def lamp_shapes():
    """The metal desk lamp in its own frame (card-ish units; base centre at 0,0, up = -y): heavy round base, stem,
    elbow, arm and the cone shade. [(kind, pts|box, colour)]."""
    sh = []
    sh.append(('ell', (-150, -40, 150, 40), INKC)); sh.append(('ell', (-142, -46, 142, 30), STEEL_LO)); sh.append(('ell', (-142, -60, 142, 16), STEEL))
    sh.append(('line', [(0, -40), (40, -700)], 46, STEEL)); sh.append(('line', [(40, -700), (-200, -940)], 40, STEEL))
    sh.append(('dot', (40, -700), 34, STEEL_LO))
    sh.append(('poly', [(-230, -960), (-170, -915), (-40, -760), (-380, -680)], (128, 136, 152)))
    sh.append(('hi', [(-8, -60), (28, -690)], 10)); sh.append(('hi', [(30, -715), (-185, -930)], 8))
    sh.append(('hi', [(-60, -54), (110, -52)], 7))
    return sh


def lamp_standing(lay, bx, by, sc, rot=0.0, hilite=1.0):
    """Draw the desk lamp with its base centre at (bx, by), scale sc (px per unit), rotated by rot deg (cw)."""
    d = ImageDraw.Draw(lay); ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    T = lambda p: (bx + (p[0] * ca - p[1] * sa) * sc, by + (p[0] * sa + p[1] * ca) * sc)
    o = max(2, 6 * sc)
    for kind, *a in lamp_shapes():
        if kind == 'ell':
            x0, y0, x1, y1 = a[0]; pts = [T((x0 + (x1 - x0) * (.5 + .5 * math.cos(th)), y0 + (y1 - y0) * (.5 + .5 * math.sin(th)))) for th in np.linspace(0, 2 * math.pi, 32)]
            d.polygon(pts, fill=tuple(a[1]) + (255,))
        elif kind == 'line':
            pts = [T(p) for p in a[0]]; w = a[1] * sc
            d.line(pts, fill=INKC + (255,), width=int(w + 2 * o))
            for p in pts: d.ellipse((p[0] - w / 2 - o, p[1] - w / 2 - o, p[0] + w / 2 + o, p[1] + w / 2 + o), fill=INKC + (255,))
            d.line(pts, fill=tuple(a[2]) + (255,), width=int(w))
        elif kind == 'dot':
            p = T(a[0]); r = a[1] * sc
            d.ellipse((p[0] - r - o, p[1] - r - o, p[0] + r + o, p[1] + r + o), fill=INKC + (255,)); d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=tuple(a[2]) + (255,))
        elif kind == 'poly':
            pts = [T(p) for p in a[0]]; d.polygon(pts, fill=INKC + (255,)); d.line(pts + pts[:1], fill=INKC + (255,), width=int(2 * o))
            d.polygon(pts, fill=tuple(a[1]) + (255,))
        elif kind == 'hi':
            d.line([T(p) for p in a[0]], fill=STEEL_HI + (int(255 * hilite),), width=max(1, int(a[1] * sc)))


def s01(t, u):
    """ECU level with the nightstand top: the phone lights up by itself in the dark, 00:00. Slow push in."""
    img = bedroom_bg(1).copy()
    lit = sm(seg(u, .55, .75)) * (1 + .15 * math.exp(-max(0, u - .75) * 6))
    # the nightstand top
    lay = layer()
    wood_top(lay, S(1240), S(1560), S(-200), S(1280), S(540))
    d = ImageDraw.Draw(lay)
    bx, by = S(850), S(1262)
    # the wall socket + the lamp's plug behind (shot 3 yanks it), a glass of water and a book on the left
    d.rounded_rectangle((S(1000), S(1010), S(1110), S(1130)), S(10), fill=(200, 200, 206, 255), outline=INKC + (255,), width=max(2, int(S(5))))
    d.rectangle((S(1030), S(1050), S(1060), S(1095)), fill=(20, 20, 24, 255), outline=INKC + (255,))
    d.line([(S(1045), S(1095)), (S(1040), S(1200)), (bx + S(130), by - S(20))], fill=(10, 10, 14, 255), width=max(2, int(S(10))), joint='curve')
    d.rounded_rectangle((S(10), S(1225), S(290), S(1262)), S(6), fill=(150, 50, 56, 255), outline=INKC + (255,), width=max(2, int(S(4))))
    d.rounded_rectangle((S(20), S(1195), S(300), S(1228)), S(6), fill=(60, 90, 140, 255), outline=INKC + (255,), width=max(2, int(S(4))))
    d.polygon([(S(80), S(980)), (S(210), S(980)), (S(200), S(1196)), (S(90), S(1196))], fill=(120, 150, 190, 140), outline=INKC + (255,))
    d.polygon([(S(84), S(1060)), (S(206), S(1060)), (S(200), S(1196)), (S(90), S(1196))], fill=(90, 130, 190, 150))
    d.line([(S(110), S(1000)), (S(116), S(1180))], fill=(230, 240, 255, 200), width=max(1, int(S(8))))
    lamp_standing(lay, bx, by, S(1.0))
    lay = tint(lay, (120, 128, 170))
    img.alpha_composite(lay)
    # the phone on a little stand (screen toward us), slightly turned
    pw, ph = S(400), S(800)
    scr = phone_screen(pw, ph, lit, u)
    scr = scr.transform(scr.size, Image.PERSPECTIVE, _persp_coeffs(scr.size, .04), Image.BICUBIC)
    px, py = S(330), S(1270)
    stand = ImageDraw.Draw(img)
    stand.polygon([(px - S(20), py), (px + pw + S(20), py), (px + pw - S(20), py - S(40)), (px + S(20), py - S(40))], fill=(30, 30, 38, 255), outline=INKC)
    if lit > 0:
        TL.glow_at(img, px + pw / 2, py - ph / 2, S(700), PHONE, k=.55 * lit, core=0, mix=.3)
        TL.add_light(img, TL.ellipse_soft(SIZE, px + pw / 2, py + S(40), S(380), S(70), S(30)), PHONE, .45 * lit, mix=.2)
        TL.add_light(img, TL.ellipse_soft(SIZE, bx - S(70), by - S(30), S(90), S(26), S(10)), (210, 236, 255), .6 * lit)
        TL.add_light(img, TL.ellipse_soft(SIZE, bx - S(40), S(900), S(12), S(300), S(8)), (210, 236, 255), .45 * lit)
        TL.add_light(img, TL.ellipse_soft(SIZE, S(150), S(1080), S(50), S(110), S(20)), (210, 236, 255), .35 * lit)
    _paste(img, scr, int(px), int(py - ph))
    if lit > 0:
        TL.glow_at(img, px + pw / 2, py - ph * .62, S(260), (200, 220, 255), k=.25 * lit, core=0, mix=.1)
    img = finish(img, u, vig=.4, bloom_k=.45)
    z = 1.0 + .07 * sm(u / 4.0)
    dx, dy = shake(u, S(6), .8)
    jx, jy = jolt(u, 2.55, S(12))
    return camxf(img, z, dx + jx, dy + jy, fx=px + pw / 2, fy=py - ph / 2)


def _persp_coeffs(size, k):
    """Perspective coefficients for a slight 'turned away on the right' keystone (k = shrink of the right edge)."""
    w, h = size
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [(0, 0), (w * (1 - k * .3), h * k), (w * (1 - k * .3), h * (1 - k)), (0, h)]
    A = []; B = []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); B.append(X)
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y]); B.append(Y)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def quilt_edge(d, y, x0, x1, amp, col, ph=0.0):
    pts = [(x, y + amp * math.sin(x / S(140) + ph)) for x in np.linspace(x0, x1, 40)]
    return pts


def s02(t, u):
    """CU from above: ME in bed, eyes snap open in the dark; he holds his breath and tilts his head to listen."""
    u0 = u - 4.0
    img = new((6, 8, 26))
    d = ImageDraw.Draw(img)
    # mattress sheet with soft folds
    for k_ in range(9):
        y = S(80 + k_ * 230)
        d.arc((S(-300), y, S(1400), y + S(500)), 200, 340, fill=(18, 26, 66, 255), width=max(2, int(S(16))))
    # the pillow (rounded, with a seam + creases)
    pl = layer(); dp = ImageDraw.Draw(pl)
    dp.rounded_rectangle((S(60), S(420), S(1020), S(1160)), S(170), fill=INKC + (255,))
    dp.rounded_rectangle((S(70), S(430), S(1010), S(1150)), S(160), fill=(196, 206, 236, 255))
    dp.rounded_rectangle((S(110), S(470), S(970), S(1110)), S(130), outline=(160, 172, 210, 255), width=max(1, int(S(5))))
    for (a, b) in (((S(130), S(560)), (S(260), S(620))), ((S(820), S(500)), (S(940), S(600))), ((S(150), S(1040)), (S(300), S(980)))):
        dp.line([a, b], fill=(150, 162, 200, 255), width=max(1, int(S(6))))
    img.alpha_composite(tint(pl, (120, 132, 180)))
    # ME's head on the pillow (a big card), the quilt up to his chin
    ex = ('blink' if u0 < .3 else 'surprised' if u0 < 1.2 else 'worried' if u0 < 3.05 else 'scared')
    tilt = 16 * sm(seg(u0, 1.2, 2.0)) - 5 * sm(seg(u0, 3.05, 3.3)) + 3 * math.sin(u0 * 40) * math.exp(-max(0, u0 - 3.58) * 6) * (u0 > 3.58)
    look = -.55 * sm(seg(u0, 1.1, 1.9)) + .15 * sm(seg(u0, 3.05, 3.3))
    mult = S(250) / stickman.R
    c = big_card(ex, 'stand', round(look * 20) / 20, mult, **ME)
    pop = 1 + .04 * math.exp(-max(0, u0 - .3) * 10) * (u0 > .3) + .03 * math.exp(-max(0, u0 - 3.05) * 8) * (u0 > 3.05)
    br = 1 + .006 * math.sin(u0 * 2.4) * (u0 < .3)
    hl = layer()
    paste_card(hl, c, S(540), S(760), pop * br, tilt)
    hl = tint(hl, (150, 166, 214))
    img.alpha_composite(hl)
    # the quilt over the body
    q = layer(); dq = ImageDraw.Draw(q)
    top = quilt_edge(dq, S(1120), S(-40), S(1120), S(18), None, .3)
    poly = top + [(S(1120), S(2000)), (S(-40), S(2000))]
    dq.polygon(poly, fill=(36, 56, 120, 255)); dq.line(top, fill=INKC + (255,), width=max(2, int(S(8))))
    fold = [(x, y + S(70)) for x, y in top]
    dq.line(fold, fill=(70, 96, 170, 255), width=max(2, int(S(16))))
    for i in range(7):
        for j in range(5):
            if (i + j) % 2: dq.rectangle((S(-40 + i * 170), S(1240 + j * 170), S(-40 + i * 170 + 170), S(1240 + j * 170 + 170)), fill=(44, 68, 140, 255))
    for k_ in range(3):
        dq.arc((S(100 + k_ * 300), S(1300), S(500 + k_ * 300), S(1900)), 200, 300, fill=(26, 40, 90, 255), width=max(2, int(S(10))))
    img.alpha_composite(tint(q, (150, 160, 210)))
    # the phone glow from his right (the nightstand off frame right) + a faint cool fill
    TL.add_light(img, TL.ellipse_soft(SIZE, S(1100), S(700), S(420), S(600), S(160)), PHONE, .55, mix=.2)
    TL.add_light(img, TL.ellipse_soft(SIZE, S(780), S(740), S(160), S(240), S(80)), (190, 225, 255), .22, mix=.0)
    img = finish(img, u, vig=.45, bloom_k=.25)
    z = 1.02 + .1 * sm(u0 / 4.0)
    dx, dy = shake(u, S(4), .4, 2)
    return camxf(img, z, dx, dy, fx=S(560), fy=S(760))


def s03(t, u):
    """CU handheld: a shaking hand fumbles on the nightstand, grips the metal lamp and yanks its plug out."""
    u0 = u - 8.0
    img = bedroom_bg(3).copy()
    lay = layer(); d = ImageDraw.Draw(lay)
    # wall + socket (top right), the nightstand top seen from above at an angle
    d.polygon([(S(-50), S(-50)), (S(1130), S(-50)), (S(1130), S(760)), (S(-50), S(760))], fill=(40, 50, 90, 255))
    for xx in range(-40, 1130, 90): d.line([(S(xx), S(-50)), (S(xx), S(760))], fill=(36, 46, 84, 255), width=max(1, int(S(30))))
    sx_, sy_ = S(830), S(380)
    d.rounded_rectangle((sx_ - S(80), sy_ - S(90), sx_ + S(80), sy_ + S(90)), S(14), fill=(206, 206, 212, 255), outline=INKC + (255,), width=max(2, int(S(6))))
    for ox in (-28, 28): d.rounded_rectangle((sx_ + S(ox - 8), sy_ - S(30), sx_ + S(ox + 8), sy_ + S(10)), S(4), fill=(30, 30, 34, 255))
    d.polygon([(S(-60), S(760)), (S(1140), S(760)), (S(1300), S(2000)), (S(-220), S(2000))], fill=(100, 70, 48, 255))
    d.line([(S(-60), S(760)), (S(1140), S(760))], fill=INKC + (255,), width=max(2, int(S(8))))
    for j in range(10):
        f = (j + .5) / 10
        d.line([(lerp(S(-60), S(1140), f), S(760)), (lerp(S(-220), S(1300), f), S(2000))], fill=(86, 60, 42, 255), width=max(1, int(S(4))))
    lay = tint(lay, (110, 120, 170))
    img.alpha_composite(lay)
    # the phone lying flat, screen up (light source), nudged by the groping hand at ~1.0 s
    nud = S(40) * sm(seg(u0, .95, 1.15))
    ph = Image.new('RGBA', (int(S(330)), int(S(600))), (0, 0, 0, 0))
    ph.paste(phone_screen(S(330), S(600), 1.0, u), (0, 0))
    ph = ph.transform(ph.size, Image.PERSPECTIVE, _persp_coeffs(ph.size, 0), Image.BICUBIC)
    ph = ph.resize((ph.width, int(ph.height * .55)), Image.LANCZOS).rotate(8, expand=True, resample=Image.BICUBIC)
    ppx, ppy = S(90) - nud, S(1250) + nud * .3
    TL.add_light(img, TL.ellipse_soft(SIZE, ppx + ph.width / 2, ppy + ph.height / 2, S(420), S(260), S(90)), PHONE, .5, mix=.2)
    _paste(img, ph, int(ppx), int(ppy))
    # hand path (wrist position, finger direction, kind) over time
    keys = [(0.0, (1250, 2050), -125, 'open'), (.6, (880, 1500), -140, 'open'), (.85, (640, 1430), -150, 'open'),
            (1.05, (560, 1360), -160, 'open'), (1.3, (700, 1250), -120, 'open'), (1.65, (760, 1040), -110, 'open'),
            (2.0, (700, 930), 180, 'grip'), (5.0, (700, 930), 180, 'grip')]
    i = max(j for j in range(len(keys)) if keys[j][0] <= u0) if u0 >= 0 else 0
    i = min(i, len(keys) - 2)
    a, b = keys[i], keys[i + 1]; f = sm(seg(u0, a[0], b[0]))
    wx, wy = lerp2(a[1], b[1], f); ang = lerp(a[2], b[2], f); kind = b[3] if f > .6 else a[3]
    if u0 < 2.0:                                                   # the trembling search: small pats
        wy += 14 * math.sin(u0 * 23) * (1 - f * .5); wx += 8 * math.sin(u0 * 17)
    # the yank: the lamp lifts + tips, the cord goes taut, the plug pops out (2.95 s), lamp leaves frame top
    lift = sm(seg(u0, 2.6, 3.55)) * 70 + ei(seg(u0, 3.7, 4.9)) * 1500
    tip = -10 * sm(seg(u0, 2.6, 3.55)) + 25 * sm(seg(u0, 3.65, 4.3))
    trem = 3 * math.sin(u0 * 31) * (u0 > 2.0)
    gx, gy = S(wx + trem), S(wy - lift)
    if u0 >= 2.0: wx2, wy2 = gx / KK, gy / KK
    G = (21, -400); sc = S(1.0) * .95
    rot = tip
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    if u0 < 2.0:
        bx, by = S(560), S(1140)
    else:
        bx = gx + S(25) - (G[0] * ca - G[1] * sa) * sc; by = gy - (G[0] * sa + G[1] * ca) * sc
    pulled = u0 >= 3.6
    L2 = layer(); d2 = ImageDraw.Draw(L2)
    # cord: socket -> lamp base (taut while lifting, the plug flies after 2.95 s)
    base_end = (bx + 130 * ca * sc, by + 130 * sa * sc)
    if not pulled:
        sag = S(160) * (1 - sm(seg(u0, 2.6, 3.55)))
        mid = ((sx_ + base_end[0]) / 2, max(sy_, base_end[1]) + sag)
        pts = [(sx_, sy_ + S(30))] + [(lerp(lerp(sx_, mid[0], v), lerp(mid[0], base_end[0], v), v), lerp(lerp(sy_ + S(30), mid[1], v), lerp(mid[1], base_end[1], v), v)) for v in np.linspace(.1, 1, 12)]
        d2.line(pts, fill=(8, 8, 12, 255), width=max(2, int(S(12))), joint='curve')
        d2.rounded_rectangle((sx_ - S(40), sy_ - S(40), sx_ + S(40), sy_ + S(30)), S(8), fill=(234, 234, 240, 255), outline=INKC + (255,), width=max(2, int(S(5))))
    else:
        v = seg(u0, 3.6, 4.3)
        plug = (lerp(sx_, base_end[0] + S(100), eo(v)), lerp(sy_, base_end[1] + S(380), eo(v)) + S(200) * math.sin(math.pi * v))
        pts = [plug, ((plug[0] + base_end[0]) / 2 + S(60) * math.sin(u0 * 9), (plug[1] + base_end[1]) / 2 + S(80)), base_end]
        d2.line(pts, fill=(8, 8, 12, 255), width=max(2, int(S(12))), joint='curve')
        pr = _rot([(-40, -40), (40, -40), (40, 30), (-40, 30)], 0, 0, 200 * v)
        d2.polygon([(plug[0] + S(x), plug[1] + S(y)) for x, y in pr], fill=(234, 234, 240, 255), outline=INKC + (255,))
        for ox in (-14, 14):
            q = _rot([(ox, -40), (ox, -75)], 0, 0, 200 * v); d2.line([(plug[0] + S(x), plug[1] + S(y)) for x, y in q], fill=(220, 190, 90, 255), width=max(1, int(S(8))))
    lamp_standing(L2, bx, by, sc, rot)
    # the arm (pyjama sleeve) + the hand
    fa = ang if u0 < 2.0 else 175
    wr = (gx - math.cos(math.radians(fa)) * S(70), gy - math.sin(math.radians(fa)) * S(70))
    el = (wr[0] + S(330), wr[1] + S(520))
    sleeve(L2, (S(1500), S(2300)), el, S(150), (217, 191, 148))
    d2 = ImageDraw.Draw(L2)
    d2.line([el, wr], fill=INKC + (255,), width=int(S(120)))
    d2.line([el, wr], fill=(236, 240, 252, 255), width=int(S(104)))
    sleeve(L2, (S(1500), S(2300)), el, S(150), (217, 191, 148))
    hand2d(L2, gx, gy, fa, S(78), kind if u0 < 2.0 else 'grip', spread=.9)
    L2 = tint(L2, (140, 150, 200))
    L2 = rim_layer(L2, (-1, .3), PHONE, .8)
    img.alpha_composite(L2)
    if pulled: sparks(img, sx_, sy_, u0 - 3.6, n=6, r=60, col=(255, 240, 200))
    img = finish(img, u, vig=.42, bloom_k=.3)
    dx, dy = shake(u, S(9), .9, 4)
    jx, jy = jolt(u0, 3.6, S(16))
    return camxf(img, 1.04, dx + jx, dy + jy)


# ------------------------------------------------------------------ house shots: common renderer
def torch_beam(img, cam, src_px, target, cone=.32, k=.9, t=0.0, clipm=None):
    """THIEF 1's flashlight from the lens (px) to a world target: the cone widens to `cone` m at the target."""
    if cam.depth(target) < .2: return
    dst = cam.p(target); r1 = cam.px_per_m(target) * cone
    beam(img, src_px, dst, S(10), r1, TORCH, k, t, clipm=clipm)


def side_dir(cam, frm, to):
    a = cam.p(frm); b = cam.p(to); dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1
    return dx / n, dy / n


WINDOW_C = ((WIN[0] + WIN[1]) / 2, 0.0, 1.6)


LAST_BBOX = [None]


def chars_pass(img, lay, rims, tint_col=(150, 168, 215), shift=(0, 0)):
    """Light the character layer and composite it; shift (1080 px) slides a lying pile into frame (the tiles are
    uniform, so a small sideways cheat does not show)."""
    lay = light_chars(lay, rims, tint_col)
    LAST_BBOX[0] = lay.split()[3].getbbox()
    img.alpha_composite(lay)


def ground_shadow(img, cam, P, rx=.35, ry=.25, k=.55):
    pts = [cam.p((P[0] + rx * math.cos(a), P[1] + ry * math.sin(a), .004)) for a in np.linspace(0, 2 * math.pi, 24)]
    m = soft_mask_poly(pts, S(10))
    a = np.asarray(img, np.float32); w = np.asarray(m, np.float32)[..., None] / 255 * k
    a[..., :3] *= (1 - w); img.paste(Image.fromarray(a.astype(np.uint8), 'RGBA'))


# ------------------------------------------------------------------ shot 4: down the stairs (OTS from behind)
def s04(t, u):
    u0 = u - 13.0
    # ME: walks from the bedroom door to the landing edge, then creeps down one step every ~0.85 s
    if u0 < 1.35:
        f = sm(seg(u0, .3, 1.35)); P = (.58, lerp(8.75, YTOP + .12, f), ZT); stepph = u0 * 2.2
    else:
        sdone = (u0 - 1.35) / 1.2
        sf = math.floor(sdone) + sm(min(1.0, (sdone - math.floor(sdone)) * 1.2 / .55))
        P = stairs_point(sf); P = (P[0], P[1] + .1, P[2]); stepph = sdone * math.pi
    # the camera glides (it does not copy each step): a smoothed path along the stairs
    walk_y = lerp(8.75, YTOP + .12, sm(seg(u0, .3, 1.35)))
    Pc = stairs_point(max(0.0, (u0 - 1.0) / 1.2))
    k_ = sm(seg(u0, .9, 1.7))
    Pc = (Pc[0], lerp(walk_y, Pc[1] + .1, k_), lerp(ZT, Pc[2], k_))
    cam_pos = (.92 + .03 * math.sin(u0 * .8), Pc[1] + 1.9, Pc[2] + 1.95)
    cam_tgt = (.42, Pc[1] - 4.0, Pc[2] - 1.6 + .1 * math.sin(u0 * .5))
    cam = Cam(cam_pos, cam_tgt, fov=60, roll=1.5 * math.sin(u0 * .6), size=SIZE)
    img, near = render_house(cam)
    # the flashlight beam sweeping the cabinet, seen through the stair mouth
    mouth = [cam.p((0, YMOUTH, 0)), cam.p((SX, YMOUTH, 0)), cam.p((SX, YMOUTH, 2.12)), cam.p((0, YMOUTH, 2.12))]
    clipm = soft_mask_poly(mouth, S(2))
    blinds_light(img, cam, .8, clipm=clipm, window=False)
    sweep = math.sin(u0 * .9) * .55
    tgt = (.85 + sweep, .44, 1.15 + .2 * math.sin(u0 * 1.7))
    src = cam.p((2.4, 1.0, 1.45))
    if u0 > .8: torch_beam(img, cam, src, tgt, .42, .95 * sm(seg(u0, .8, 1.4)), t, clipm)
    lay = layer()
    xy = at3d(cam, P, 1.75)
    if xy:
        x, y, sc, ppm = xy
        legs = .5 + .5 * math.sin(stepph)
        pose = mix_pose(POSE['lamp_high'], dict(armL=(75, 100), armR=(-150, -178), legL=(16, 20), legR=(-6, -1)), legs * .8)
        me(lay, x, y, sc, u, 'neutral', pose, back=True, lamp=-95, idle=.5)
    chars_pass(img, lay, [((0, 1), (200, 220, 255), .55), ((-1, 0), SODIUM, .35)])
    nl = near_layer(cam, near, 0)
    if nl: img.alpha_composite(nl)
    # the door crack at the start: black frame, a slit that opens to the right
    if u0 < 1.4:
        k = sm(seg(u0, .0, 1.35)); xs = W * (.5 - .5 * k) - S(20)
        dl = layer(); dd = ImageDraw.Draw(dl)
        if xs > 0: dd.rectangle((0, 0, xs, H), fill=(4, 4, 10, 255))
        dd.line([(xs, 0), (xs, H)], fill=(120, 110, 140, 255), width=max(2, int(S(6))))
        if xs + S(30) + W * k * .9 < W: dd.rectangle((xs + S(30) + W * k * .9, 0, W, H), fill=(4, 4, 10, int(255 * (1 - k))))
        img.alpha_composite(dl)
    img = finish(img, u, vig=.42)
    dx, dy = shake(u, S(5), .7, 6)
    return camxf(img, 1.0, dx, dy)


# ------------------------------------------------------------------ shot 5: back to the wall, the peek
def s05(t, u):
    u0 = u - 22.0
    cam = Cam((.12 + .03 * math.sin(u0), 4.55, 1.38), (1.15, 3.55, 1.2), fov=66, roll=-1.0, size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, .7)
    # the torch light playing in the room beyond the corner (flicker on the far wall/floor)
    fl = .6 + .4 * math.sin(u0 * 2.3) * math.sin(u0 * .9 + 1)
    tg = (2.0 + .5 * math.sin(u0 * 1.1), .4, 1.0)
    if cam.depth(tg) > .3:
        TL.glow_at(img, *cam.p(tg), cam.px_per_m(tg) * .6, TORCH, k=.5 * fl, core=.2, mix=.2)
    peek = sm(seg(u0, 1.6, 2.6)) - .55 * sm(seg(u0, 3.9, 4.6))
    lay = layer()
    xy = at3d(cam, (1.02, 3.92, 0), 1.75)
    if xy:
        x, y, sc, ppm = xy
        pose = mix_pose(POSE['back_wall'], dict(armL=(40, 30), armR=(-130, -172), legL=(8, 1), legR=(-8, -1)), peek)
        g = me(lay, x, y, sc, u, 'worried', pose, look=.15 + .75 * peek, lean=13 * peek, lamp=-100, idle=.8)
        # beads of sweat on the forehead
        hx, hy = g['head']; R = g['R']; dd = ImageDraw.Draw(lay)
        for (ox, oy, rr) in ((-.45, -.62, .07), (-.15, -.75, .06), (.25, -.7, .055), (.5, -.5, .05)):
            sy = oy + .05 * ((u0 * .3 + ox) % 1)
            dd.ellipse((hx + ox * R - rr * R, hy + sy * R - rr * R * 1.3, hx + ox * R + rr * R, hy + sy * R + rr * R), fill=(170, 220, 255, 255), outline=INKC + (255,))
    rims = [((1, -.1), TORCH, .3 + .6 * peek * fl), ((1, .4), SODIUM, .25)]
    chars_pass(img, lay, rims)
    if peek > .2 and xy:
        TL.add_light(img, TL.ellipse_soft(SIZE, g['head'][0] + g['R'] * .6, g['head'][1], g['R'] * .9, g['R'] * 1.1, g['R'] * .5), TORCH, .35 * peek * fl, mix=.1)
    img = finish(img, u, vig=.45)
    dx, dy = shake(u, S(4), .6, 8)
    return camxf(img, 1.0 + .05 * sm(u0 / 5), dx, dy)


# ------------------------------------------------------------------ shot 6: POV, THIEF 1 at the sideboard
TH_POS = (2.2, .95, 0)


def s06(t, u):
    u0 = u - 27.0
    cam = Cam((1.0 + .02 * math.sin(u0 * .7), 3.72, 1.56), (2.45, .75, 1.0), fov=42, roll=.8 * math.sin(u0 * .5), size=SIZE)
    img, near = render_house(cam, fg_d=.9)
    blinds_light(img, cam, .9)
    lay = layer()
    xy = at3d(cam, TH_POS, 1.75)
    lens_px = None
    if xy:
        x, y, sc, ppm = xy
        stuff = math.sin(u0 * 7.5) * (u0 < 2.8)
        zip_ = sm(seg(u0, 2.8, 3.2))
        pose = dict(POSE['stuff']); pose['armR'] = (-30 - 14 * stuff - 30 * zip_, -80 - 20 * stuff - 10 * zip_, .9)
        pose['armL'] = (-40 + 10 * stuff, -95 + 15 * stuff, .9)
        # the backpack on the sideboard, the laptop going in (behind his hands)
        g = thief1(lay, x, y, sc, u, 'angry', pose, look=.7, back=True, bar='hip', idle=.6)
        hxr, hyr, _ = g['hands']['R']
        bx, by = hxr + ppm * .16, hyr + ppm * .12
        pk = layer()
        ldown = sm(seg(u0, .0, 1.4))
        if ldown < .98: laptop2d(pk, bx, by - ppm * (.32 - .3 * ldown), ppm * .34, ang=-80)
        backpack2d(pk, bx, by, ppm * .36, ppm * .44, ang=-6, col=(52, 58, 80))
        lay.alpha_composite(pk)
        hx, hy = g['head']; R = g['R']
        lens_px = (hx + R * .95, hy + R * .75)
        if u0 > 2.8:                          # the decisive zip: a bright zipper pull travelling across the pack top
            zx = lerp(bx - ppm * .14, bx + ppm * .14, zip_)
            ImageDraw.Draw(lay).ellipse((zx - S(7), by - ppm * .19 - S(7), zx + S(7), by - ppm * .19 + S(7)), fill=(230, 230, 240, 255))
    torchk = 1.0
    chars_pass(img, lay, [((1, -.2), TORCH, .6), ((-1, 0), SODIUM, .5)])
    if lens_px:
        beam(img, lens_px, (bx, by), S(5), cam.px_per_m((2.75, .25, .82)) * .1, TORCH, .5, t)
        lens(img, *lens_px, S(7), k=.7)
    nl = near_layer(cam, near, 12)
    if nl: img.alpha_composite(nl)
    img = finish(img, u, vig=.45)
    dx, dy = shake(u, S(6), .5, 10)
    jx, jy = jolt(u, 30.0, S(4))
    return camxf(img, 1.0 + .06 * sm(u0 / 5), dx + jx, dy + jy)


# ------------------------------------------------------------------ shot 7: the bare foot and the plastic cup
def foot2d(lay, x, y, s, ang=0.0, col=(236, 240, 252), hem=(217, 191, 148)):
    """A cartoon bare foot seen from the side, toes to the right, heel at (x, y) on the sole line; s = foot length px.
    The shin rises from the ankle into the striped pyjama trouser."""
    d = ImageDraw.Draw(lay); o = max(2, s * .03)
    T = lambda pts: _rot([(u * s, v * s) for u, v in pts], x, y, ang)
    shin = T([(.04, -.3), (.34, -.3), (.36, -2.6), (.02, -2.6)])
    foot = T([(-.04, -.08), (.02, -.3), (.34, -.34), (.6, -.22), (.9, -.14), (1.0, -.06), (.97, 0), (.05, 0)])
    for poly in (shin, foot): d.polygon(poly, fill=INKC); d.line(poly + poly[:1], fill=INKC, width=int(o * 2), joint='curve')
    for (tx, ty, tr) in ((.93, -.08, .07), (.83, -.12, .06), (.74, -.15, .055), (.66, -.18, .05)):
        c = T([(tx, ty)])[0]; r = tr * s
        d.ellipse((c[0] - r - o, c[1] - r - o, c[0] + r + o, c[1] + r + o), fill=INKC)
    d.polygon(shin, fill=col); d.polygon(foot, fill=col)
    for (tx, ty, tr) in ((.93, -.08, .07), (.83, -.12, .06), (.74, -.15, .055), (.66, -.18, .05)):
        c = T([(tx, ty)])[0]; r = tr * s
        d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=col)
    pant = T([(-.06, -.75), (.42, -.8), (.44, -2.7), (-.08, -2.7)])
    d.polygon(pant, fill=INKC); d.line(pant + pant[:1], fill=INKC, width=int(o * 2))
    d.polygon(T([(-.04, -.78), (.4, -.83), (.42, -2.7), (-.06, -2.7)]), fill=hem)
    for j in (.06, .18, .3):
        d.line(T([(j, -.82), (j, -2.7)]), fill=(240, 222, 190), width=max(1, int(o * .8)))


def cup2d(lay, x, y, s, broken=0.0, t=0.0):
    """A small plastic cup lying on its side (red), cracked flat when broken (shards)."""
    d = ImageDraw.Draw(lay); o = max(2, s * .05); col = (220, 70, 64)
    if broken <= 0:
        pts = [(x - s * .5, y - s * .55), (x + s * .5, y - s * .42), (x + s * .5, y), (x - s * .5, y)]
        d.polygon(pts, fill=INKC); d.line(pts + pts[:1], fill=INKC, width=int(o * 2)); d.polygon(pts, fill=col)
        d.ellipse((x + s * .38, y - s * .45, x + s * .62, y + s * .02), fill=shade(col, .6), outline=INKC, width=int(o))
        d.line([(x - s * .45, y - s * .42), (x + s * .4, y - s * .33)], fill=(255, 170, 160), width=max(1, int(o)))
        return
    rng = np.random.default_rng(4)
    flat = [(x - s * .62, y - s * .12), (x + s * .6, y - s * .1), (x + s * .64, y), (x - s * .66, y)]
    d.polygon(flat, fill=INKC); d.polygon([(px_, py_ + o * .6) for px_, py_ in flat], fill=col)
    for i in range(7):
        a = rng.uniform(math.pi * 1.05, math.pi * 1.95); v = rng.uniform(.6, 1.4) * s * 2.2
        k_ = min(1.0, broken * 3)
        cx, cy = x + math.cos(a) * v * k_, y + math.sin(a) * v * k_ * .5 + s * 1.5 * k_ * k_ * 0
        cy = min(y, cy + s * 2.0 * max(0, broken - .2))
        r = s * rng.uniform(.07, .14)
        tri = _rot([(-r, 0), (r, -r * .5), (r * .3, r)], cx, cy, rng.uniform(0, 360) + 500 * broken)
        d.polygon(tri, fill=col, outline=INKC)


def s07(t, u):
    u0 = u - 32.0
    cam = Cam((1.4, 3.3, .2), (.55, 4.15, .14), fov=44, size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, 1.0)
    # torch light sweeping the floor far behind
    gx, gy = cam.p((1.4, 2.6 - .4 * math.sin(u0 * 1.5), 0))
    TL.add_light(img, TL.ellipse_soft(SIZE, gx, gy, S(180), S(40), S(30)), TORCH, .25)
    lay = layer()
    land = 1.2
    f = seg(u0, .0, land)
    Ppos = (lerp(.55, .55, f), lerp(4.42, 4.05, eo(f)), max(0.0, lerp(.3, 0.0, sm(f)) + .08 * math.sin(math.pi * f)))
    fx_, fy_ = cam.p(Ppos); ppm = cam.px_per_m(Ppos)
    cxy = cam.p((.58, 4.02, 0)); cs = cam.px_per_m((.58, 4.02, 0)) * .11
    broken = seg(u0, land, land + .6)
    toycar2d(lay, cxy[0], cxy[1], cs * 1.6, broken, u)
    tremble = S(2) * math.sin(u0 * 40) * (u0 > land)
    foot2d(lay, fx_ - ppm * .12 + tremble, fy_ - ppm * .01 * (u0 > land), ppm * .27, -4 * (1 - f))
    chars_pass(img, lay, [((1, 0), SODIUM, .5), ((0, -1), (200, 210, 255), .3)])
    if u0 > land:
        sparks(img, cxy[0], cxy[1] - cs * .3, u0 - land, n=10, r=90, col=(255, 210, 200), seed=3)
        k_ = max(0.0, 1 - (u0 - land) / .25)
        if k_ > 0:
            m = Image.new('L', SIZE, 0); dm = ImageDraw.Draw(m)
            for i in range(10):
                a = i * math.pi / 5; dm.line([(cxy[0] + math.cos(a) * S(40), cxy[1] - S(20) + math.sin(a) * S(40)),
                                              (cxy[0] + math.cos(a) * S(150), cxy[1] - S(20) + math.sin(a) * S(150))], fill=255, width=max(1, int(S(6))))
            add(img, m, (255, 255, 255), k_)
    img = finish(img, u, vig=.45)
    jx, jy = jolt(u0, land, S(18), .45)
    z = 1.0 + .05 * sm(u0 / 2.3) + .05 * eo(seg(u0, land, land + .2))
    return camxf(img, z, jx, jy, fx=cxy[0], fy=cxy[1])


# ------------------------------------------------------------------ shot 8: he freezes, the torch dies
def s08(t, u):
    u0 = u - 34.3
    cam = Cam((1.15 + .12 * u0, 3.35 - .1 * u0, 1.5), (2.3, 1.15, 1.25), fov=46 - 2 * u0, size=SIZE)
    if 0.7 <= u0 < 2.7: return new((0, 0, 0))
    img, near = render_house(cam)
    blinds_light(img, cam, .9)
    lay = layer()
    xy = at3d(cam, (2.3, 1.25, 0), 1.75)
    on = u0 < .6
    g = None
    if xy:
        x, y, sc, ppm = xy
        g = thief1(lay, x, y, sc, u, 'surprised', POSE['frozen'], look=-.05, bar='hip', idle=.15)
        bk = layer(); backpack2d(bk, x + ppm * .32, y - ppm * .55, ppm * .3, ppm * .4, ang=12, col=(30, 34, 50)); bk.alpha_composite(lay); lay = bk
    if on and g:
        hx, hy = g['head']; R = g['R']
        chars_pass(img, lay, [((0, 1), TORCH, 1.0), ((-1, 0), SODIUM, .4)])
        TL.add_light(img, TL.ellipse_soft(SIZE, hx, hy + R * .2, R * 1.0, R * 1.0, R * .5), TORCH, .45, mix=.1)
        lens(img, hx + R * .05, hy + R * 1.12, S(16))
        beam(img, (hx, hy + R * 1.12), (hx - ppm * .9, hy + R * 4.5), S(6), ppm * .25, TORCH, .5, t, motes=False)
    else:
        chars_pass(img, lay, [((-1, 0), SODIUM, .5)])
    img = finish(img, u, vig=.5)
    if not on:                          # after the click: the eye adapts, two shapes in the street-lamp spill
        img = darken(img, 1 - .22 * sm(seg(u0, 2.7, 3.7)))
    return img


# ------------------------------------------------------------------ shots 9-11: the fight
SH11, SH12, SH13 = 1000, 600, 450
THF = (1.95, 2.55)
MEF = (1.05, 3.28)


def fight_cam(u0, base, roll=0.0):
    return Cam(base[0], base[1], base[2], roll, size=SIZE)


def s09(t, u):
    u0 = u - 38.0
    pan = 1 - eo(seg(u0, 0, .32))                      # whip pan in from the left
    tgt = (lerp(1.45, 2.4, pan * .9), lerp(2.95, 1.6, pan), 1.05)
    cam = Cam((2.95 + .05 * math.sin(u0), 5.0, 1.3), tgt, fov=56, size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, 1.0)
    lay = layer()
    # THIEF 1: spins (0-0.15 back to us), winds up, swings at 38.30-38.50, the bar hits the wall corner at 38.50
    sw = seg(u0, .3, .5); back = sm(seg(u0, .1, .3)) * (1 - sw); rec = sm(seg(u0, .85, 1.4))
    pose_t = mix_pose(mix_pose(POSE['stuff'], POSE['swing_back'], sm(seg(u0, .05, .3))), POSE['swing_fwd'], ei(sw))
    pose_t = mix_pose(pose_t, POSE['swing_back'], rec * .5)
    xt = at3d(cam, (THF[0], THF[1], 0), 1.75)
    lead = .12 * ei(sw) - .1 * rec
    if xt:
        x, y, sc, ppm = xt
        bar_ang = lerp(lerp(-100, 200, sm(seg(u0, .05, .3))), 360 + 0, ei(sw))
        bar_ang = lerp(bar_ang, 250, rec)
        g1 = thief1(lay, x + ppm * lead, y, sc, u, 'angry', pose_t, look=.7, lean=8 * ei(sw) - 6 * rec, bar=bar_ang, pack=True, idle=.4)
    # ME: dodges back (lean away) as the bar comes, recovers, raises the lamp
    d_ = sm(seg(u0, .28, .48)) * (1 - .7 * sm(seg(u0, 1.0, 1.8)))
    pm = mix_pose(POSE['lamp_ready'], POSE['dodge'], d_)
    pm['_side'] = True; pm['_name'] = 'dodge'
    xm = at3d(cam, (MEF[0], MEF[1], 0), 1.75)
    if xm:
        x, y, sc, ppm = xm
        windup = sm(seg(u0, 3.3, 4.0))
        pm = mix_pose(pm, POSE['lunge'], windup * .4)
        me(lay, x + ppm * .12 * d_, y, sc, u, 'scared' if u0 < 1.5 else 'determined', pm, look=-.7, lean=-24 * d_ + 6 * windup,
           flip=True, lamp=-120 + 40 * d_)
    sun = side_dir(cam, (1.5, 2.9, 1.0), WINDOW_C)
    chars_pass(img, lay, [(sun, SODIUM, .9), ((0, -1), (170, 190, 255), .3)])
    corner = cam.p((SX + .12, YMOUTH, 1.45))
    sparks(img, corner[0], corner[1], u0 - .5, n=16, r=130)
    img = finish(img, u, vig=.45)
    if pan > .01:
        a = np.asarray(img, np.float32); acc = np.zeros_like(a); n = 0; rad = int(S(90) * pan)
        for o in range(-rad, rad + 1, max(1, rad // 6 or 1)):
            acc += np.roll(a, o, axis=1); n += 1
        img = Image.fromarray((acc / n).astype(np.uint8), 'RGBA')
    jx, jy = jolt(u0, .5, S(22), .4)
    dx, dy = shake(u, S(5), .8, 12)
    return camxf(img, 1.0, jx + dx, jy + dy)


def crowbar_floor(u0):
    """The dropped crowbar: (world centre, screen-plane angle deg, z) after the THWACK (u0 = s since 43.05)."""
    if u0 < .5:
        f = u0 / .5; z = lerp(1.15, .02, f * f); x = lerp(1.82, 1.6, f); y = lerp(2.75, 2.95, f); ang = lerp(200, 160, f) + 200 * f
        return (x, y, z), ang
    b = u0 - .5
    hop = abs(math.sin(b * 9)) * .12 * math.exp(-b * 4.5)
    roll = 1 - math.exp(-b * 1.1)
    return (1.6 - .55 * roll, 2.95 + .4 * roll, .02 + hop), 360 + 175 + 40 * math.sin(b * 6) * math.exp(-b * 2) + 160 * roll


def s10(t, u):
    u0 = u - 42.0
    cam = Cam((3.05 + .03 * math.sin(u0), 4.85, 1.1), (1.5, 2.85, .95), fov=52, roll=-15 - 2 * sm(seg(u0, 1.0, 1.3)), size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, 1.0)
    lay = layer()
    hit = 1.05
    wind = sm(seg(u0, .2, .85)); swing = ei(seg(u0, .85, hit)); after = sm(seg(u0, hit, hit + .5))
    xt = at3d(cam, (THF[0] - .2, THF[1] + .2, 0), 1.75)
    if xt:
        x, y, sc, ppm = xt
        pt = mix_pose(POSE['swing_back'], POSE['hurt'], after)
        bar = None if u0 > hit + .05 else 230
        g1 = thief1(lay, x, y, sc, u, 'angry' if u0 < hit else 'sad', pt, look=.7, lean=-14 * after, bar=bar, pack=True, idle=.4)
    xm = at3d(cam, (MEF[0] + .05, MEF[1] - .05, 0), 1.75)
    if xm:
        x, y, sc, ppm = xm
        pm = mix_pose(mix_pose(POSE['lamp_ready'], dict(POSE['lunge']), wind), POSE['hit'], swing)
        pm['_side'] = True; pm['_name'] = 'lunge'
        lamp_a = lerp(lerp(-110, -40, wind), 120, swing)
        me(lay, x - ppm * .25 * swing, y, sc, u, 'angry', pm, look=-.7, lean=-15 * swing + 6 * wind, flip=True, lamp=lamp_a)
    if u0 >= hit - .02:
        cp, ca = crowbar_floor(u0 - hit)
        if cam.depth(cp) > .2:
            px_, py_ = cam.p(cp); m = cam.px_per_m(cp)
            crowbar2d(lay, px_ - m * .25, py_, ca, m)
    sun = side_dir(cam, (1.5, 2.9, 1.0), WINDOW_C)
    chars_pass(img, lay, [(sun, SODIUM, .9), ((0, -1), (170, 190, 255), .3)])
    if xt:
        hp = (x, y)
    imp = cam.p((1.7, 2.8, 1.2))
    sparks(img, imp[0], imp[1], u0 - hit, n=10, r=90, col=(255, 236, 200), seed=5)
    if 0 <= u0 - hit < .08: img = TL.add_light(img, Image.new('L', SIZE, 70), (255, 255, 255), 1.0)
    img = finish(img, u, vig=.45)
    jx, jy = jolt(u0, hit, S(26), .45)
    j2x, j2y = jolt(u0, 1.55, S(6), .25)
    dx, dy = shake(u, S(5), .8, 14)
    return camxf(img, 1.05, jx + j2x + dx, jy + j2y + dy)


def toycar2d(lay, x, y, s, broken=0.0, t=0.0):
    """A small hard-plastic child's toy car (red body, yellow cabin, black wheels), side view, wheels on y; s = length px.
    broken > 0: flattened, the cabin snapped off, shards and a wheel flying."""
    d = ImageDraw.Draw(lay); o = max(2, s * .035)
    red, yel = (226, 56, 48), (255, 206, 60)
    k = min(1.0, broken * 4)
    def P(pts): return [(x + u * s, y + v * s * (1 - .45 * k)) for u, v in pts]
    body = P([(-.5, -.12), (-.46, -.3), (.42, -.3), (.5, -.18), (.5, -.08), (-.5, -.08)])
    cab = [(x + u * s + k * s * .25, y + v * s * (1 - .45 * k) - k * s * .35 * (1 - min(1, broken * 2) * .0) + s * .9 * max(0, broken - .25) ** 2)
           for u, v in [(-.28, -.3), (-.2, -.52), (.18, -.52), (.26, -.3)]]
    for poly, c in ((cab, yel), (body, red)):
        d.polygon(poly, fill=INKC); d.line(poly + poly[:1], fill=INKC, width=int(o * 2), joint='curve'); d.polygon(poly, fill=c)
    win = [(cab[0][0] + s * .08, cab[0][1] - s * .03), (cab[1][0] + s * .05, cab[1][1] + s * .05), (cab[2][0] - s * .05, cab[2][1] + s * .05), (cab[3][0] - s * .08, cab[3][1] - s * .03)]
    d.polygon(win, fill=(140, 200, 240), outline=INKC)
    d.line([body[1], body[2]], fill=(255, 150, 140), width=max(1, int(o)))
    for i, wx in enumerate((-.3, .3)):
        cx, cy = x + wx * s, y - .07 * s
        if broken > 0 and i == 1: cx += s * 1.2 * broken; cy -= s * .8 * math.sin(math.pi * min(1, broken * 1.4))
        r = .11 * s
        d.ellipse((cx - r - o, cy - r - o, cx + r + o, cy + r + o), fill=INKC); d.ellipse((cx - r * .45, cy - r * .45, cx + r * .45, cy + r * .45), fill=(200, 200, 210))
    if broken > 0:
        rng = np.random.default_rng(4)
        for i in range(8):
            a = rng.uniform(math.pi * 1.05, math.pi * 1.95); v = rng.uniform(.5, 1.4) * s * 1.3 * min(1, broken * 2.5)
            cx_, cy_ = x + math.cos(a) * v, min(y, y + math.sin(a) * v * .7 + s * 3 * max(0, broken - .3) ** 2)
            r = s * rng.uniform(.03, .06)
            d.polygon(_rot([(-r, 0), (r, -r * .5), (r * .3, r)], cx_, cy_, rng.uniform(0, 360) + 400 * broken), fill=red if i % 2 else yel, outline=INKC)


def s11(t, u):
    u0 = u - 47.0
    sh = 1.0 if u0 > .3 else .4
    cam = Cam((2.7, 4.5, 2.4), (1.5, 2.35, .3), fov=60, roll=3 * math.sin(u0 * 1.3), size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, 1.0)
    lay = layer()
    shove = .1
    fall = eo(seg(u0, shove, shove + .2))
    grp = (1.75, 2.6)
    # THIEF 1: pushed backwards, falls flat (lean -> -84 deg), legs kicking afterwards
    xt = at3d(cam, (grp[0] + .55 * fall, grp[1] - .2 * fall, 0), 1.75)
    kick = math.sin(u0 * 9) * (u0 > 1.2)
    if xt:
        x, y, sc, ppm = xt; x += S(SH11) * fall
        pt = mix_pose(POSE['hurt'], POSE['fall'], fall)
        if u0 > .5: pt = dict(POSE['lie']); pt['legL'] = (20 + 25 * kick, 10); pt['legR'] = (-10 - 20 * kick, -5); pt['armL'] = (70 + 30 * kick, 120); pt['armR'] = (-70, -110 - 20 * kick)
        thief1(lay, x, y, sc, u, 'angry', pt, look=.4 if u0 < 1 else 0, lean=-84 * fall, bar=None, pack=u0 < shove + .1, idle=.3)
    # the backpack flies and bursts: the stolen things spill across the tiles
    bpu = seg(u0, shove + .05, shove + .7)
    if u0 > shove:
        bp = (lerp(grp[0] + .3, 2.9, bpu), lerp(grp[1] - .1, 1.45, bpu), .9 * math.sin(math.pi * bpu) + .15)
        bx, by = cam.p(bp); m = cam.px_per_m(bp)
        backpack2d(lay, bx, by, m * .32, m * .42, ang=400 * bpu, col=(30, 34, 50))
        items = [((2.55, 1.2), 'laptop'), ((3.15, 1.75), 'watch'), ((2.75, 2.05), 'phone'), ((3.25, 1.25), 'box'), ((2.45, 1.65), 'cash'), ((3.4, 1.55), 'neck')]
        for i, (dst, kind) in enumerate(items):
            f = eo(seg(u0, shove + .55 + i * .05, shove + 1.3 + i * .08))
            if f <= 0: continue
            P = (lerp(2.9, dst[0], f), lerp(1.45, dst[1], f), .002)
            px_, py_ = cam.p(P); mm = cam.px_per_m(P)
            if kind == 'laptop': laptop2d(lay, px_, py_, mm * .36, ang=10 + 30 * f)
            elif kind == 'phone': ImageDraw.Draw(lay).rounded_rectangle((px_ - mm * .04, py_ - mm * .07, px_ + mm * .04, py_ + mm * .07), mm * .015, fill=(30, 30, 40), outline=(150, 160, 190))
            elif kind == 'watch':
                dd = ImageDraw.Draw(lay); dd.ellipse((px_ - mm * .05, py_ - mm * .035, px_ + mm * .05, py_ + mm * .035), fill=(230, 200, 100), outline=INKC)
            elif kind == 'box': ipoly(ImageDraw.Draw(lay), [(px_ - mm * .09, py_ - mm * .05), (px_ + mm * .09, py_ - mm * .05), (px_ + mm * .09, py_ + mm * .05), (px_ - mm * .09, py_ + mm * .05)], (150, 40, 60), 1)
            elif kind == 'cash':
                for j in range(3): ImageDraw.Draw(lay).rectangle((px_ + j * mm * .05, py_ - mm * .02 + j * mm * .02, px_ + j * mm * .05 + mm * .12, py_ + mm * .04 + j * mm * .02), fill=(120, 190, 120), outline=INKC)
            else:
                ImageDraw.Draw(lay).arc((px_ - mm * .08, py_ - mm * .04, px_ + mm * .08, py_ + mm * .06), 0, 300, fill=(240, 220, 140), width=max(1, int(mm * .012)))
            if kind in ('watch', 'neck'): glint(img, px_, py_, S(10), k=.6 + .4 * math.sin(u0 * 5 + i))
    # ME: the shove, then on top of him pinning the collar (a lean over the fallen body), struggling
    xm = at3d(cam, (grp[0] - .2 + 1.15 * fall, grp[1] + .25 - .05 * fall, .1 * fall), 1.75)
    if xm:
        x, y, sc, ppm = xm; x += S(SH11) * fall; y -= ppm * .45 * fall
        pm = mix_pose(POSE['lamp_ready'], POSE['shove'], sm(seg(u0, 0, shove)))
        pm['_side'] = True; pm['_name'] = 'shove'
        if fall > .5:
            pm = mix_pose(pm, PIN, sm((fall - .5) * 2))
        strug = 4 * math.sin(u0 * 11) * (u0 > 1.0)
        me(lay, x, y, sc, u, 'angry', pm, look=-.7, lean=-62 * fall + strug, lamp=None)
    sun = side_dir(cam, (1.8, 2.5, .5), WINDOW_C)
    chars_pass(img, lay, [(sun, SODIUM, .9), ((0, -1), (170, 190, 255), .3)])
    img = finish(img, u, vig=.45)
    dx, dy = shake(u, S(14) * sh, 1.6, 16)
    jx, jy = jolt(u0, shove, S(20))
    j2x, j2y = jolt(u0, shove + .55, S(16))
    return camxf(img, 1.04, dx + jx + j2x, dy + jy + j2y)


# ------------------------------------------------------------------ shot 12: the door opens, THIEF 2
def s12(t, u):
    u0 = u - 55.0
    opn = sm(seg(u0, .2, 1.6)) * (1 - ei(seg(u0, 4.7, 5.0)))
    ang = 78 * opn
    cam = Cam((1.25, 6.0, 1.55), (3.55, .3, 1.0), fov=58, roll=.6 * math.sin(u0 * .4), size=SIZE)
    img, near = render_house(cam, door_ang=ang)
    blinds_light(img, cam, .9)
    # the light spill through the open door: a warm wedge on the floor + a haze
    if opn > .02:
        d0, d1 = DOOR
        L = 3.2 * opn
        wedge = [(d0, .02, .003), (d1 - (d1 - d0) * (1 - math.cos(math.radians(ang))), .02 + (d1 - d0) * math.sin(math.radians(ang)) * 0, .003), (d1 + .6, L, .003), (d0 - .5, L, .003)]
        m = soft_mask_poly([cam.p(p) for p in wedge], S(14))
        add(img, m, SODIUM, .75 * opn, mix=.45)
        dm = soft_mask_poly([cam.p((d0, .0, 0)), cam.p((d1, 0, 0)), cam.p((d1, 0, 2.15)), cam.p((d0, 0, 2.15))], S(4))
        add(img, dm, SODIUM, .5 * opn, mix=.3)
    lay = layer(); lay2 = layer()
    # THIEF 2 fills the doorway, steps in at 59.5
    step = sm(seg(u0, 4.5, 4.9))
    P2 = (3.95, lerp(-.35, .45, step), 0)
    x2 = at3d(cam, P2, 2.05)
    if x2 and u0 > .25:
        x, y, sc, ppm = x2
        g2 = thief2(lay2, x, y, sc, u, POSE['walk_a'] if 0 < step < 1 else 'stand', obj=95, idle=.5)
    # ME on top of THIEF 1 (seen from behind), turning toward the door
    xt = at3d(cam, (3.35, 2.3, 0), 1.75)
    if xt:
        x, y, sc, ppm = xt; x += S(SH12)
        pt = dict(POSE['lie']); kick = math.sin(u0 * 8) * (u0 < 1.5)
        pt['legL'] = (20 + 15 * kick, 10)
        thief1(lay, x, y, sc, u, 'angry', pt, look=0, lean=-84, idle=.3)
    xm = at3d(cam, (3.5, 2.35, .1), 1.75)
    if xm:
        x, y, sc, ppm = xm; x += S(SH12); y -= ppm * .4
        me(lay, x, y, sc, u, 'scared', PIN, look=-.7 + .9 * sm(seg(u0, 1.2, 2.0)), lean=-62 + 14 * sm(seg(u0, 1.2, 2.0)))
    dv = side_dir(cam, (2.4, 2.6, .6), (3.95, -.2, 1.2))
    k_open = opn
    if x2 and u0 > .25:                    # THIEF 2 is further back: drawn before the pile
        lay2 = rim_layer(lay2, (0, -1), SODIUM, 1.0 * opn + .15, w=max(2, int(S(9))))
        lay2 = rim_layer(lay2, (1, 0), SODIUM, .8 * opn, w=max(2, int(S(7))))
        img.alpha_composite(lay2)
        hx, hy, _ = g2['hands']['R']
        glint(img, hx + S(10), hy + S(110) * sc / .3, S(16), k=.7 * opn + .2)
    chars_pass(img, lay, [(dv, SODIUM, .9 * k_open + .2), ((0, -1), (170, 190, 255), .25)])
    img = finish(img, u, vig=.45)
    jx, jy = jolt(u0, 5.0, S(14), .4)
    return camxf(img, 1.0 + .04 * sm(u0 / 7), jx, jy)


# ------------------------------------------------------------------ shot 13: the smug eyes, the elbow, the slide
@functools.lru_cache(maxsize=2)
def floor_bg(which):
    if which == 'thief':
        cam = Cam((1.9, 3.2, .35), (1.0, 1.4, .1), fov=50, size=SIZE)
    else:
        cam = Cam((3.2, 4.6, .5), (1.6, 2.2, .25), fov=55, size=SIZE)
    img, _ = render_house(cam)
    blinds_light(img, cam, 1.0)
    return cine.defocus(img, 5 * KK), cam


def s13(t, u):
    u0 = u - 62.0
    elbow = .9
    if u0 < 1.55:
        img = floor_bg('thief')[0].copy()
        lay = layer()
        # THIEF 1's head lying on the tiles (big, sideways), his eyes narrowing, ME's hands on his collar
        ex = 'angry' if u0 < .55 else 'smug'
        lk = -.4 + .35 * sm(seg(u0, .2, .55))
        mult = S(250) / stickman.R
        c = big_card(ex, 'stand', round(lk * 20) / 20, mult, **THIEF1)
        hl = layer()
        hx, hy = S(470), S(1120)
        paste_card(hl, c, hx, hy, 1.0, 78)
        g = dict(head=(hx, hy), R=S(250), look=lk, flip=False, lean=0)
        rot = layer(); masked_head(rot, dict(head=(S(540), S(960)), R=S(250), look=lk, flip=False))
        # draw the hood/mask unrotated on a copy around a temporary centre, rotate it the same way
        tmp = layer(); paste_card(tmp, c, S(540), S(960), 1.0, 0); masked_head(tmp, dict(head=(S(540), S(960)), R=S(250), look=lk, flip=False))
        tmp = tmp.rotate(78, resample=Image.BICUBIC, center=(S(540), S(960)), translate=(hx - S(540), hy - S(960)))
        lay.alpha_composite(tmp)
        # ME's arms + hands gripping the collar from the top right
        dd = ImageDraw.Draw(lay)
        lift = S(300) * ei(seg(u0, elbow + .05, elbow + .45))
        for (a_, b_) in (((S(1200), S(250) - lift), (S(760), S(860) - lift)), ((S(1250), S(560) - lift), (S(820), S(1130) - lift))):
            sleeve(lay, a_, lerp2(a_, b_, .6), S(110), (217, 191, 148))
            dd.line([lerp2(a_, b_, .6), b_], fill=INKC, width=int(S(96))); dd.line([lerp2(a_, b_, .6), b_], fill=(236, 240, 252), width=int(S(82)))
            sleeve(lay, a_, lerp2(a_, b_, .6), S(110), (217, 191, 148))
            fist(lay, b_[0], b_[1], S(52), ang=120)
        # the elbow: his dark sleeve swinging up across the frame
        if u0 > elbow - .25:
            e = sm(seg(u0, elbow - .25, elbow))
            p0 = (S(250), S(1700)); p1 = (lerp(S(200), S(820), e), lerp(S(1500), S(700), e))
            dd.line([p0, p1], fill=INKC, width=int(S(150))); dd.line([p0, p1], fill=THIEF1_C, width=int(S(130)))
            dd.ellipse((p1[0] - S(75), p1[1] - S(75), p1[0] + S(75), p1[1] + S(75)), fill=INKC); dd.ellipse((p1[0] - S(65), p1[1] - S(65), p1[0] + S(65), p1[1] + S(65)), fill=THIEF1_C)
        lay = light_chars(lay, [((1, -.4), SODIUM, .8)])
        img.alpha_composite(lay)
        if u0 > elbow: sparks(img, S(820), S(720), u0 - elbow, n=8, r=80, col=(255, 255, 255))
        img = finish(img, u, vig=.5)
        jx, jy = jolt(u0, elbow, S(24))
        dx, dy = shake(u, S(4), .7, 18)
        z = 1.0 + .08 * sm(u0 / .9)
        out = camxf(img, z, jx + dx, jy + dy, fx=S(470), fy=S(1000))
        if u0 > 1.35:                         # whip pan to the slide
            k = seg(u0, 1.35, 1.55)
            nxt = s13_slide(t, 1.55, u)
            return cine.whip(out, nxt, k, dx=-1.0, blur=S(60)).convert('RGBA')
        return out
    return s13_slide(t, u0, u)


def s13_slide(t, u0, u):
    img, cam = floor_bg('slide'); img = img.copy()
    f = eo(seg(u0, 1.6, 3.6))
    P = (lerp(2.6, 1.6, f), lerp(2.7, 2.1, f), 0)
    lay = layer()
    xy = at3d(cam, P, 1.75)
    if xy:
        x, y, sc, ppm = xy; x += S(SH13)
        rise = sm(seg(u0, 4.3, 5.8))
        pm = dict(armL=(60, 100), armR=(-40, -80), legL=(-30, 20), legR=(-10, 40), _side=True, _name='slide')
        me(lay, x, y, sc, u, 'sad' if u0 < 4 else 'scared', pm, look=.5, lean=-82 + 20 * rise, idle=.3, flip=True)
        if f < .98:
            dd = ImageDraw.Draw(lay)
            for j in range(5):
                yy = y - ppm * (.08 + j * .08); L = ppm * (.8 + j * .15) * (1 - f)
                dd.line([(x + ppm * .3, yy), (x + ppm * .3 + L, yy)], fill=(220, 230, 255, 160), width=max(1, int(S(4))))
    sun = side_dir(cam, P, WINDOW_C)
    chars_pass(img, lay, [(sun, SODIUM, .9)])
    img = finish(img, u, vig=.48)
    dx, dy = shake(u, S(5), .8, 20)
    return camxf(img, 1.0, dx, dy)


# ------------------------------------------------------------------ shot 14: from the floor, THIEF 2 walks closer
STEPS = (68.5, 69.9, 71.25, 72.5, 73.65, 74.7)


def thief2_progress(T):
    n = sum(1 for s_ in STEPS if T >= s_ - .25)
    prev = max([s_ for s_ in STEPS if s_ - .25 <= T], default=None)
    part = sm(seg(T, prev - .25, prev + .25)) if prev else 0.0
    return max(0, n - 1) + part, n


def s14(t, u):
    u0 = u - 68.0
    cam = Cam((1.55, 4.55, .16), (2.75, 1.0, 1.45), fov=64, size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, 1.0)
    prog, n = thief2_progress(u)
    f = prog / 5.0
    P2 = (lerp(3.75, 2.2, f), lerp(.9, 3.25, f ** 1.3), 0)
    lay2 = layer()
    x2 = at3d(cam, P2, 2.05)
    if x2:
        x, y, sc, ppm = x2
        ph = prog % 1
        pose = mix_pose('stand', dict(armL=(14, 4), armR=(-6, -2), legL=(-8, -2), legR=(22, 30)) if int(prog) % 2 else dict(armL=(6, 2), armR=(-14, -4), legL=(-22, -30), legR=(8, 2)), math.sin(math.pi * ph))
        g2 = thief2(lay2, x, y - ppm * .03 * math.sin(math.pi * ph), sc, u, pose, obj=95, idle=.4)
        lay2 = rim_layer(lay2, (0, -1), SODIUM, .9, w=max(2, int(S(8))))
        lay2 = rim_layer(lay2, (-1, -.3), SODIUM, .6, w=max(2, int(S(6))))
        img.alpha_composite(lay2)
        hx, hy, _ = g2['hands']['R']
        glint(img, hx, hy + ppm * .4, S(18), k=.5 + .5 * abs(math.sin(u0 * 2.2)))
    # ME in the foreground (back to us, bottom-left), pushing up on his hands
    lay = layer()
    pu = sm(seg(u0, .2, 2.0))
    me(lay, S(60), S(3150) - S(160) * pu, S(2.3), u, 'neutral', dict(armL=(40, 10), armR=(-40, -10), legL=(10, 1), legR=(-10, -1)), back=True, idle=.6)
    chars_pass(img, lay, [((1, -.5), SODIUM, .4)])
    img = finish(img, u, vig=.45)
    jx = jy = 0.0
    for s_ in STEPS:
        a, b = jolt(u, s_, S(10) * (1 + STEPS.index(s_) * .4), .3); jx += a; jy += b
    return camxf(img, 1.0, jx, jy)


# ------------------------------------------------------------------ shot 15: the panic, the raised wrench, black
def s15(t, u):
    u0 = u - 74.0
    if u >= 76.0: return new((0, 0, 0))
    if u < 75.3:
        img = floor_bg('slide')[0].copy()
        img = darken(img, .35)
        lay = layer()
        mult = S(300) / stickman.R
        c = big_card('scared', 'stand', 0.0, mult, **ME)
        paste_card(lay, c, S(540), S(900), 1.0 + .03 * sm(u0 / 1.3), -6)
        # arms coming up over the face (from 0.9 s)
        a = sm(seg(u0, .85, 1.25))
        for side_ in (-1, 1):
            b0 = (S(540 + side_ * 520), S(2100)); b1 = (S(540 + side_ * 120 * (1 - a) + side_ * 60), lerp(S(1900), S(1080), a))
            sleeve(lay, b0, lerp2(b0, b1, .55), S(150), (217, 191, 148))
            dd = ImageDraw.Draw(lay); dd.line([lerp2(b0, b1, .55), b1], fill=INKC, width=int(S(124))); dd.line([lerp2(b0, b1, .55), b1], fill=(236, 240, 252), width=int(S(108)))
            sleeve(lay, b0, lerp2(b0, b1, .55), S(150), (217, 191, 148))
            hand2d(lay, b1[0], b1[1] - S(40), -90 + side_ * 10, S(80), 'open', spread=.8)
        lay = light_chars(lay, [((1, -1), SODIUM, .9)])
        img.alpha_composite(lay)
        img = finish(img, u, vig=.5)
        jx, jy = jolt(u, 74.7, S(14))
        return camxf(img, 1.0, jx, jy)
    # the low angle: THIEF 2 towering, the wrench raised high, swinging down at 75.45
    cam = Cam((2.0, 3.75, .12), (2.35, 2.4, 2.2), fov=74, size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, 1.0)
    lay2 = layer()
    x2 = at3d(cam, (2.6, 1.75, 0), 2.05)
    sw = ei(seg(u, 75.45, 75.98))
    if x2:
        x, y, sc, ppm = x2
        pose = mix_pose(POSE['raise_obj'], dict(armL=(25, 10), armR=(-40, -10), legL=(14, 2), legR=(-14, -2)), sw)
        g2 = thief2(lay2, x, y, sc, u, pose, obj=lerp(-95, 60, sw), idle=.3)
        lay2 = rim_layer(lay2, (0, -1), SODIUM, .9, w=max(2, int(S(9))))
        img.alpha_composite(lay2)
        hx, hy, _ = g2['hands']['R']
        if sw < .2: glint(img, hx, hy - ppm * .35, S(26), k=1.0)
    if sw > .3: img = cine.defocus(img, S(6) * sw)
    img = finish(img, u, vig=.5)
    img = darken(img, sm(seg(u, 75.8, 76.0)) * .9)
    jx, jy = jolt(u, 75.3, S(8))
    return camxf(img, 1.0 + .25 * sw, jx, jy, fy=H * .4)


# ------------------------------------------------------------------ thumbnail
def thumb_frame():
    """ME on the stairs with the metal lamp raised high, THIEF 1 below at the stair mouth lit by the flashlight under
    his chin (a still built for the thumbnail; the top third stays dark for the headline)."""
    cam = Cam((.6, .9, .8), (.5, 5.6, 2.0), fov=56, size=SIZE)
    img, near = render_house(cam)
    blinds_light(img, cam, 1.0)
    lay = layer()
    xm = at3d(cam, (.38,) + stairs_point(5.0)[1:], 1.75)
    if xm:
        x, y, sc, ppm = xm
        me(lay, x, y, sc, 0.0, 'scared', dict(armL=(40, 70), armR=(-150, -178), legL=(12, 2), legR=(-12, -2)), look=.1, lamp=-100, idle=0)
    chars_pass(img, lay, [((0, 1), TORCH, .5), ((1, 0), SODIUM, .6)])
    lay = layer()
    xt = at3d(cam, (.92, 2.95, 0), 1.75)
    if xt:
        x, y, sc, ppm = xt
        g = thief1(lay, x, y, sc, 0.0, 'angry', dict(armL=(30, 50), armR=(-60, -150, .9), legL=(12, 2), legR=(-12, -2)), look=-.25, bar=None, idle=0)
        hx, hy = g['head']; R = g['R']
        chars_pass(img, lay, [((0, 1), TORCH, 1.0), ((1, 0), SODIUM, .5)])
        TL.add_light(img, TL.ellipse_soft(SIZE, hx, hy + R * .3, R * 1.05, R * 1.0, R * .45), TORCH, .5, mix=.1)
        hxr, hyr, _ = g['hands']['R']
        lens(img, hx + R * .05, hy + R * 1.1, S(18))
        beam(img, (hx + R * .05, hy + R * 1.1), cam.p(stairs_point(4.0)[:2] + (2.2,)), S(8), ppm * .25, TORCH, .22, 0.0)
        crowbar2d(img, hxr, hyr, -125, ppm * .9)
        fist(img, hxr, hyr, R * .3, col=THIEF1_C, ang=-125)
    return finish(img, 0.0, vig=.42, bloom_k=.35)


# ------------------------------------------------------------------ timeline, captions, render
SHOTS = [('s01', 0.0, 4.0, s01), ('s02', 4.0, 8.0, s02), ('s03', 8.0, 13.0, s03), ('s04', 13.0, 22.0, s04),
         ('s05', 22.0, 27.0, s05), ('s06', 27.0, 32.0, s06), ('s07', 32.0, 34.3, s07), ('s08', 34.3, 38.0, s08),
         ('s09', 38.0, 42.0, s09), ('s10', 42.0, 47.0, s10), ('s11', 47.0, 55.0, s11), ('s12', 55.0, 62.0, s12),
         ('s13', 62.0, 68.0, s13), ('s14', 68.0, 74.0, s14), ('s15', 74.0, 80.0, s15)]
KEY_AT = {'s01': 2.0, 's02': 5.6, 's03': 10.3, 's04': 19.5, 's05': 24.8, 's06': 29.0, 's07': 33.3, 's08': 34.6, 's09': 38.55,
          's10': 43.1, 's11': 51.0, 's12': 58.0, 's13': 62.7, 's14': 72.6, 's15': 75.5}
CAPS = [(56.63, 57.27, 'You done'), (57.27, 57.82, 'yet?'), (57.82, 58.33, "What's all"), (58.33, 59.45, 'the noise?')]


def draw_caption(img, text, base, scale=1.0):
    size = int(round(0.037 * img.height * scale)); f = kit.font(size, bold=True)
    w = kit.text_w(text, f); x = (img.width - w) / 2
    sh = layer()
    ImageDraw.Draw(sh).text((x + 3 * KK, base + 5 * KK), text, font=f, fill=(0, 0, 0, 200), anchor='ls', stroke_width=int(size * .16), stroke_fill=(0, 0, 0, 200))
    img.alpha_composite(cine.defocus(sh, 7 * KK))
    ImageDraw.Draw(img).text((x, base), text, font=f, fill='white', anchor='ls', stroke_width=max(2, int(size * .1)), stroke_fill='black')


def frame(T, captions=True):
    anim.NOW = T
    for name, a, b, fn in SHOTS:
        if a <= T < b or (b == END and T >= a):
            img = fn(T, T)
            break
    img = img.convert('RGBA')
    if captions:
        for a, b, txt in CAPS:
            if a <= T < b:
                sc = 1.0 + .08 * max(0.0, 1 - (T - a) * FPS / 4)
                draw_caption(img, txt, H * .70, sc)
    return img.convert('RGB')


def _job(f):
    out, = _job.args
    p = os.path.join(out, f'f{f:05d}.png')
    if not os.path.exists(p): frame(f / FPS).save(p)
    return f


def _init(out): _job.args = (out,)


def main():
    a = sys.argv[1:]
    cmd = a[0]
    if cmd == 'stills':
        out = a[1]; os.makedirs(out, exist_ok=True)
        names = a[2:] or [s_[0] for s_ in SHOTS]
        for n in names:
            T = KEY_AT[n] if ':' not in n else float(n.split(':')[1]); n = n.split(':')[0]
            frame(T).save(os.path.join(out, f'{n}_{T:.2f}.png')); print('ok', n, T, flush=True)
    elif cmd == 'frames':
        out = a[1]; os.makedirs(out, exist_ok=True)
        t0 = float(a[a.index('--t0') + 1]) if '--t0' in a else 0.0
        t1 = float(a[a.index('--t1') + 1]) if '--t1' in a else END
        fs = list(range(int(round(t0 * FPS)), int(round(t1 * FPS))))
        from multiprocessing import Pool
        with Pool(int(os.environ.get('JOBS', '4')), _init, (out,)) as pool:
            for i, _ in enumerate(pool.imap_unordered(_job, fs, chunksize=4)):
                if i % 100 == 0: print(i, '/', len(fs), flush=True)
    elif cmd == 'encode':
        frames, out = a[1], a[2]
        audio = a[a.index('--audio') + 1] if '--audio' in a else None
        cmdl = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, 'f%05d.png')]
        if audio: cmdl += ['-i', audio, '-c:a', 'aac', '-b:a', '128k', '-shortest']
        cmdl += ['-c:v', 'libx264', '-preset', 'slow', '-crf', os.environ.get('CRF', '24'), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
        subprocess.run(cmdl, check=True)
    elif cmd == 'sheet':
        frames, out = a[1], a[2]
        ims = []
        for k_ in range(0, int(END), 2):
            p = os.path.join(frames, f'f{k_ * FPS + 15:05d}.png')
            im = Image.open(p).convert('RGB').resize((135, 240)); d = ImageDraw.Draw(im)
            d.text((5, 5), f'{k_ + .5:.1f}s', fill='white', font=kit.font(18, bold=True), stroke_width=2, stroke_fill='black'); ims.append(im)
        cols = 10; rows = math.ceil(len(ims) / cols)
        sh = Image.new('RGB', (135 * cols, 240 * rows), (0, 0, 0))
        for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 135, (i // cols) * 240))
        sh.save(out, quality=85)
    elif cmd == 'thumbframe':
        anim.NOW = 0.0
        thumb_frame().convert('RGB').save(a[1])


if __name__ == '__main__':
    main()

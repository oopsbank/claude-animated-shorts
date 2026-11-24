"""flat2d.animals: the animal cast of video 9 (zebra-stripes), drawn as proper flat 2D side views.

Every quadruped is built from smooth shapes in UNIT space (1 unit = the withers height, ground at y=0, y down,
facing right) and painted through a LABEL image: each pixel knows which part it belongs to (torso, neck, head,
near leg, far leg, ear, mane, tail, hoof ...). Colour, patterns (zebra stripes that follow the body: vertical on
the barrel, sweeping round over the haunch to horizontal, rings on the legs, across the neck into the mane, fine
across the face), a form shadow under the barrel, a warm rim light on the back and one ink outline around the
whole silhouette are then computed per label, so the animal reads as one clean shape with inner lines only where a
near leg crosses the body. Far legs are a separate darker group drawn first.

quad(kind, s, pose=None, face=1, **kw) -> (RGBA layer, (gx, gy) ground point in the layer)
  kind: 'zebra' | 'horse' (bay) | 'coat' (bay horse in a fitted zebra-striped rug, head bare) | 'lion' | 'cow'
        (Japanese Black, `painted=True` for white painted stripes)
  s: px per unit; face: 1 = facing right, -1 = facing left.
  pose: dict(neck=deg (+ = head down), head=deg, ear=0..1 flick, tail=deg swing, breath=0..1, legs={'fn','ff','hn','hf':
        (d_upper, d_lower)} deg offsets, mouth=0..1, blink=bool)
put(img, kind, x, y, s, **kw): paste with the ground point at (x, y); returns info (eye, head, flank points in px).
walk(ph, amp) -> legs dict for a walk cycle phase.

fly_layer(L, wing='blur', legs=0.0, ph=0.0, eye=True) -> (RGBA, (cx, cy)): the HORSE FLY, side view, facing right,
  L = body length px: huge green compound eye with zigzag violet bands, humped thorax with pale stripes and
  bristles, a banded abdomen, a stubby blade mouth, clear veined wings ('blur' = beating in flight, 'fold' = laid
  back at rest, 'up' = raised), six legs (0 tucked under for fast flight .. 1 stretched forward-down to land).
put_fly(img, x, y, L, ang=0, **kw): paste centred at (x, y), rotated by ang (deg, + = nose up), flipped if L < 0.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

INK = (20, 16, 24)
WHITE_FUR = (246, 242, 232)
BLACK_FUR = (30, 27, 32)
BAY = (156, 88, 48)
BAY_D = (84, 46, 30)
LION = (214, 160, 86)
LION_BELLY = (238, 210, 160)
MANE = (128, 70, 34)
MANE_D = (84, 44, 26)
COW = (40, 38, 44)

# labels
T_TORSO, T_NECK, T_HEAD, T_LEGN, T_HOOF, T_MANE, T_EARN, T_EARF, T_TAIL, T_LEGF, T_TUFT, T_MUZ, T_HORN = range(1, 14)


# ---------------------------------------------------------------- geometry helpers
def _cr(pts, k=6, closed=True):
    """Catmull-Rom resample through the control points (closed loop by default)."""
    n = len(pts)
    if n < 3: return list(pts)
    P = list(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if closed else P[max(0, i - 1)]
        p1 = P[i]; p2 = P[(i + 1) % n] if closed else P[i + 1]
        p3 = P[(i + 2) % n] if closed else P[min(n - 1, i + 2)]
        for j in range(k):
            t = j / k; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in range(2)))
    if not closed: out.append(P[-1])
    return out


def _rot(p, c, a):
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def _bez(a, c, b, n=10):
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1])
            for t in np.linspace(0, 1, n)]


def _limb_poly(pts, ws):
    """Closed outline of a tapered limb through pts with widths ws (unit)."""
    L, R = [], []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]; b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        r = ws[i] / 2
        L.append((pts[i][0] + nx * r, pts[i][1] + ny * r)); R.append((pts[i][0] - nx * r, pts[i][1] - ny * r))
    return L + R[::-1]


def _chain(root, segs, offs):
    """Leg chain: segs = [(length, angle rad from straight down, + = forward)], offs = per-joint extra angles (rad,
    cumulative). Returns the joint points."""
    pts = [root]; a = 0.0
    for i, (ln, base) in enumerate(segs):
        a = base + sum(offs[:i + 1]) if i < len(offs) else base + sum(offs)
        p = pts[-1]
        pts.append((p[0] + math.sin(a) * ln, p[1] + math.cos(a) * ln))
    return pts


def _head_tf(poll, th):
    """Local head (u forward along the face, v toward the jaw) -> unit space."""
    c, s_ = math.cos(th), math.sin(th)
    return lambda u, v: (poll[0] + u * c - v * s_, poll[1] + u * s_ + v * c)


def walk(ph, amp=1.0):
    """Leg offsets (deg) for a walk cycle at phase ph (rad). Diagonal pairs move together."""
    out = {}
    for k, off in (('fn', 0.0), ('hf', .3), ('ff', math.pi), ('hn', math.pi + .3)):
        p = ph + off
        swing = math.sin(p)
        lift = max(0.0, math.cos(p)) ** 2
        out[k] = (amp * 20 * swing, amp * (34 * lift if k[0] == 'f' else -30 * lift))
    return out


# ---------------------------------------------------------------- species shapes
def _equine(pose, kind):
    """Zebra / horse geometry. Returns dict of parts in unit space."""
    zeb = kind == 'zebra'
    br = pose.get('breath', 0.0) * .012
    torso = [(0.63, -0.70), (0.55, -0.88), (0.36, -1.02), (0.12, -0.965), (-0.16, -0.975), (-0.40, -1.00), (-0.60, -0.95),
             (-0.69, -0.80), (-0.66, -0.62), (-0.52, -0.52), (-0.30, -0.50 + br), (0.02, -0.465 + br), (0.30, -0.50), (0.48, -0.55),
             (0.61, -0.60)]
    if zeb:   # a zebra is stockier: rounder belly, shorter legs feel, upright neck
        torso = [(x, y + (.015 if -.3 < x < .4 and y > -.6 else 0)) for x, y in torso]
    pivot = (0.46, -0.90)
    a = math.radians(pose.get('neck', 0.0))
    poll0 = (0.80, -1.50) if not zeb else (0.78, -1.52)
    poll = _rot(poll0, pivot, a)
    th = math.radians(58 + pose.get('neck', 0.0) * .9 + pose.get('head', 0.0))
    hf = _head_tf(poll, th)
    head_uv = [(-.03, -.075), (.09, -.10), (.22, -.093), (.37, -.072), (.49, -.058), (.565, -.03), (.592, .02), (.585, .072),
               (.56, .098), (.525, .112), (.46, .102), (.37, .118), (.25, .17), (.15, .212), (.05, .196), (-.03, .13), (-.06, .03)]
    if zeb:
        head_uv = [(u * .94, v * 1.04) for u, v in head_uv]
    head = [hf(u, v) for u, v in head_uv]
    crest0 = (0.24, -1.0); front0 = (0.64, -0.76)
    crest_end = hf(-.02, -.06); throat = hf(-.02, .15)
    mid = ((crest0[0] + crest_end[0]) / 2 - .06 * math.cos(a) - (.07 if zeb else .05), (crest0[1] + crest_end[1]) / 2 - .1)
    crest = _bez(crest0, mid, crest_end, 22)
    fmid = ((front0[0] + throat[0]) / 2 + .07, (front0[1] + throat[1]) / 2 + .02)
    front = _bez(throat, fmid, front0, 12)
    neck = crest + front + [(0.40, -0.80)]
    legs = pose.get('legs', {})
    def L(k): return [math.radians(v) for v in legs.get(k, (0, 0))]
    def fleg(root, k):
        o = L(k)
        return _chain(root, [(.29, .04), (.22, 0.0), (.075, .55)], [o[0], -o[0] * .2 + o[1] * .0, o[1]])
    def hleg(root, k):
        o = L(k)
        return _chain(root, [(.27, -.46), (.245, .06), (.075, .5)], [o[0], -o[1] * .3 + abs(o[1]) * .1, o[1] * .6])
    fw = [.16, .092, .068, .074] if not zeb else [.165, .095, .07, .076]
    hw = [.21, .105, .068, .074] if not zeb else [.21, .108, .07, .076]
    out = {'torso': torso, 'neck': neck, 'head': head, 'hf': hf, 'poll': poll, 'th': th, 'crest': crest,
           'legs': [('ff', fleg((0.50, -0.60), 'ff'), fw, False), ('hf', hleg((-0.36, -0.60), 'hf'), hw, False),
                    ('hn', hleg((-0.42, -0.60), 'hn'), hw, True), ('fn', fleg((0.46, -0.60), 'fn'), fw, True)]}
    # ears (unit space, from the poll), flick rotates them back
    ef = pose.get('ear', 0.0)
    def ear(du, back):
        b0 = hf(.01 + du, -.075); b1 = hf(.07 + du, -.09)
        tipd = math.radians(-100 - 35 * ef - back) + th
        ln = .17 if not zeb else .2
        tip = ((b0[0] + b1[0]) / 2 + math.cos(tipd) * ln, (b0[1] + b1[1]) / 2 + math.sin(tipd) * ln)
        wid = .05 if not zeb else .06
        midl = ((b0[0] + tip[0]) / 2 + math.cos(tipd - 1.57) * wid, (b0[1] + tip[1]) / 2 + math.sin(tipd - 1.57) * wid)
        midr = ((b1[0] + tip[0]) / 2 - math.cos(tipd - 1.57) * wid * .8, (b1[1] + tip[1]) / 2 - math.sin(tipd - 1.57) * wid * .8)
        return _cr([b0, midl, tip, midr, b1], 4)
    out['ear_n'] = ear(0, 0); out['ear_f'] = ear(-.035, -14)
    # mane: along the crest
    m_out = []
    n = len(crest)
    for i, p in enumerate(crest):
        a_ = crest[max(0, i - 1)]; b_ = crest[min(n - 1, i + 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]; ln = math.hypot(dx, dy) or 1
        nx, ny = dy / ln, -dx / ln                      # outward (up-back) normal
        q = i / (n - 1)
        h = (.035 + .07 * math.sin(math.pi * min(1, q * 1.1)) + .022 * (i % 2)) if zeb else (.02 + .035 * math.sin(math.pi * q))
        m_out.append((p[0] + nx * h, p[1] + ny * h))
    out['mane'] = [(p[0], p[1] + .01) for p in crest] + m_out[::-1]
    # tail
    sw = math.radians(pose.get('tail', 0.0))
    root = (-0.64, -0.93)
    if zeb:
        tp = [root, (-0.71, -0.84), (-0.745, -0.68), (-0.745, -0.52), (-0.735, -0.40)]
        tw = [.05, .04, .032, .03, .02]
    else:
        tp = [root, (-0.73, -0.86), (-0.78, -0.68), (-0.77, -0.48), (-0.72, -0.33)]
        tw = [.07, .12, .15, .13, .05]
    tp = [_rot(p, root, sw * (i / 4) ** .8) for i, p in enumerate(tp)]
    out['tail'] = _limb_poly(_cr(tp, 4, False), np.interp(np.linspace(0, 4, len(_cr(tp, 4, False))), range(5), tw))
    out['tail_pts'] = tp
    if zeb:
        tq = tp[3:]
        tuft = [(tq[0][0], tq[0][1]), (tq[1][0] - .02, tq[1][1] + .02), (tq[1][0], tq[1][1] + .1)]
        out['tuft'] = _limb_poly(_cr([tp[2], tp[3], (tp[4][0], tp[4][1] + .08)], 4, False), [.03, .07, .09, .08, .06, .05, .04, .03, .02])
    return out


def _lion(pose):
    br = pose.get('breath', 0.0) * .01
    cr = pose.get('crouch', 1.0)                       # 1 = stalking low, 0 = standing
    dy = .18 * (1 - cr)
    torso = [(0.50, -0.34 - dy), (0.47, -0.52 - dy), (0.36, -0.665 - dy), (0.20, -0.62 - dy), (0.02, -0.565 - dy), (-0.20, -0.575 - dy),
             (-0.40, -0.625 - dy), (-0.56, -0.57 - dy), (-0.62, -0.44 - dy), (-0.56, -0.30 - dy), (-0.36, -0.245 - dy + br),
             (-0.05, -0.235 - dy + br), (0.22, -0.26 - dy), (0.42, -0.29 - dy)]
    poll = (0.60, -0.60 - dy * .9)
    th = math.radians(18 + pose.get('head', 0.0))
    hf = _head_tf(poll, th)
    head_uv = [(-.05, -.12), (.06, -.16), (.18, -.15), (.27, -.09), (.31, -.02), (.33, .05), (.31, .11), (.24, .15), (.15, .165),
               (.06, .15), (-.03, .1), (-.07, .01)]
    head = [hf(u, v) for u, v in head_uv]
    neck = [(0.30, -0.62 - dy), hf(-.05, -.12), hf(-.07, .1), (0.50, -0.38 - dy)]
    legs = pose.get('legs', {})
    def L(k): return [math.radians(v) for v in legs.get(k, (0, 0))]
    def fleg(root, k):
        o = L(k)
        return _chain(root, [(.22 + .08 * (1 - cr), .25 * cr), (.15 + .05 * (1 - cr), -.1 * cr), (.07, 1.45)], [o[0], o[1], 0])
    def hleg(root, k):
        o = L(k)
        return _chain(root, [(.26, -1.0 * cr - .3 * (1 - cr)), (.24 + .06 * (1 - cr), .35 * cr), (.07, 1.5)], [o[0], o[1], 0])
    fw = [.14, .09, .08, .09]; hw = [.17, .095, .075, .09]
    out = {'torso': torso, 'neck': neck, 'head': head, 'hf': hf, 'poll': poll, 'th': th,
           'legs': [('ff', fleg((0.38, -0.38 - dy), 'ff'), fw, False), ('hf', hleg((-0.36, -0.42 - dy), 'hf'), hw, False),
                    ('hn', hleg((-0.42, -0.42 - dy), 'hn'), hw, True), ('fn', fleg((0.33, -0.38 - dy), 'fn'), fw, True)]}
    # mane: a shaggy ruff around the head and down the neck
    cx, cy = hf(.04, 0.0)
    pts = []
    rng = np.random.default_rng(3)
    for i in range(26):
        ang = math.radians(100 + 230 * i / 25) + th
        r = (.25 if i % 2 else .228) + .012 * rng.uniform(-1, 1)
        if 160 < 100 + 230 * i / 25 < 280: r *= 1.1
        pts.append((cx + math.cos(ang) * r * 1.05, cy + math.sin(ang) * r))
    pts += [(0.16, -0.50 - dy), (0.22, -0.66 - dy)]
    out['mane'] = pts
    out['ear_n'] = _cr([hf(.04, -.14), hf(.06, -.22), hf(.13, -.21), hf(.14, -.14)], 4)
    out['ear_f'] = _cr([hf(.0, -.13), hf(.0, -.2), hf(.06, -.2), hf(.07, -.13)], 4)
    sw = math.radians(pose.get('tail', 0.0))
    root = (-0.58, -0.52 - dy)
    tp = [root, (-0.74, -0.50 - dy), (-0.86, -0.40 - dy), (-0.92, -0.26 - dy), (-0.90, -0.14 - dy)]
    tp = [_rot(p, root, sw * (i / 4)) for i, p in enumerate(tp)]
    sm = _cr(tp, 4, False)
    out['tail'] = _limb_poly(sm, np.linspace(.05, .03, len(sm)))
    e = tp[-1]
    out['tuft'] = _cr([(e[0] - .05, e[1] - .02), (e[0] + .04, e[1] - .03), (e[0] + .03, e[1] + .07), (e[0] - .03, e[1] + .08)], 4)
    out['tail_pts'] = tp
    return out


def _cow(pose):
    br = pose.get('breath', 0.0) * .012
    torso = [(0.70, -0.56), (0.62, -0.82), (0.42, -1.0), (0.10, -0.985), (-0.25, -0.99), (-0.50, -1.03), (-0.70, -0.98),
             (-0.78, -0.86), (-0.76, -0.62), (-0.62, -0.46), (-0.30, -0.38 + br), (0.05, -0.36 + br), (0.35, -0.39), (0.55, -0.42),
             (0.68, -0.48)]
    pivot = (0.58, -0.80)
    a = math.radians(pose.get('neck', 0.0))
    poll = _rot((0.90, -0.98), pivot, a)
    th = math.radians(68 + pose.get('neck', 0.0) * .9 + pose.get('head', 0.0))
    hf = _head_tf(poll, th)
    head_uv = [(-.03, -.11), (.10, -.12), (.24, -.11), (.36, -.10), (.43, -.085), (.47, -.03), (.475, .05), (.45, .11),
               (.38, .14), (.26, .16), (.14, .18), (.04, .17), (-.04, .11), (-.06, .0)]
    head = [hf(u, v) for u, v in head_uv]
    neck = [(0.40, -1.0), hf(-.03, -.1), hf(-.04, .14), (0.76, -0.62), (0.70, -0.50), (0.62, -0.66)]
    dew = _cr([(0.66, -0.66), hf(.0, .17), (0.82, -0.62), (0.74, -0.44), (0.66, -0.48)], 4)
    legs = pose.get('legs', {})
    def L(k): return [math.radians(v) for v in legs.get(k, (0, 0))]
    def fleg(root, k):
        o = L(k)
        return _chain(root, [(.25, .03), (.17, 0.0), (.07, .3)], [o[0], 0, o[1]])
    def hleg(root, k):
        o = L(k)
        return _chain(root, [(.26, -.42), (.2, .08), (.07, .3)], [o[0], 0, o[1]])
    fw = [.19, .12, .095, .1]; hw = [.24, .12, .095, .1]
    out = {'torso': torso, 'neck': neck + dew[:0], 'dew': dew, 'head': head, 'hf': hf, 'poll': poll, 'th': th,
           'legs': [('ff', fleg((0.50, -0.50), 'ff'), fw, False), ('hf', hleg((-0.48, -0.55), 'hf'), hw, False),
                    ('hn', hleg((-0.54, -0.55), 'hn'), hw, True), ('fn', fleg((0.44, -0.50), 'fn'), fw, True)]}
    ef = pose.get('ear', 0.0)
    def ear(back):
        b = hf(.06, -.1); d = th - math.radians(150 + 20 * ef + back)
        tip = (b[0] + math.cos(d) * .17, b[1] + math.sin(d) * .17)
        n_ = (math.cos(d + 1.57) * .05, math.sin(d + 1.57) * .05)
        return _cr([(b[0] + n_[0] * .6, b[1] + n_[1] * .6), ((b[0] + tip[0]) / 2 + n_[0], (b[1] + tip[1]) / 2 + n_[1]), tip,
                    ((b[0] + tip[0]) / 2 - n_[0], (b[1] + tip[1]) / 2 - n_[1]), (b[0] - n_[0] * .6, b[1] - n_[1] * .6)], 4)
    out['ear_n'] = ear(0); out['ear_f'] = ear(-30)
    hb = hf(.02, -.12)
    out['horn'] = _cr([(hb[0] - .03, hb[1] + .01), (hb[0] - .01, hb[1] - .09), (hb[0] + .06, hb[1] - .13), (hb[0] + .02, hb[1] - .07),
                       (hb[0] + .03, hb[1] + .0)], 4)
    sw = math.radians(pose.get('tail', 0.0))
    root = (-0.74, -0.96)
    tp = [root, (-0.80, -0.82), (-0.82, -0.62), (-0.81, -0.42), (-0.80, -0.30)]
    tp = [_rot(p, root, sw * (i / 4)) for i, p in enumerate(tp)]
    sm = _cr(tp, 4, False)
    out['tail'] = _limb_poly(sm, np.linspace(.035, .025, len(sm)))
    e = tp[-1]
    out['tuft'] = _cr([(e[0] - .03, e[1] - .06), (e[0] + .03, e[1] - .06), (e[0] + .035, e[1] + .08), (e[0] - .035, e[1] + .08)], 4)
    out['tail_pts'] = tp
    return out


# ---------------------------------------------------------------- the painter
def _poly(d, pts, s, o, lab):
    d.polygon([(o[0] + x * s, o[1] + y * s) for x, y in pts], fill=lab)


def _dilate(m, r):
    """Fast binary dilation (r px) of an L mask: blur + threshold (rank filters are slow)."""
    if r <= 0: return m
    return m.filter(ImageFilter.BoxBlur(r)).point(lambda v: 255 if v > 4 else 0)


def _erode(m, r):
    if r <= 0: return m
    return m.filter(ImageFilter.BoxBlur(r)).point(lambda v: 255 if v > 250 else 0)


def _sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def _stripe(phase, th, fw):
    """Soft stripe mask from a phase field: 1 where sin(2 pi phase) > th (anti-aliased over fw)."""
    return np.clip((np.sin(2 * np.pi * phase) - th) / fw + .5, 0, 1)


_LAY = {}


def quad(kind, s, pose=None, face=1, painted=True, light=(-.55, -1.0), rim=(255, 236, 200), rim_a=.42, shade_col=None,
         ink_w=None, sun_k=1.0, cache=True):
    pose = pose or {}
    key = (kind, round(s, 1), tuple(sorted((k, (tuple(sorted((kk, tuple(round(x, 1) for x in vv)) for kk, vv in v.items()))
                                               if isinstance(v, dict) else round(v, 2) if isinstance(v, float) else v))
                                          for k, v in pose.items())), face, painted, light, rim, rim_a, ink_w, sun_k)
    if cache and key in _LAY: return _LAY[key]
    eq = kind in ('zebra', 'horse', 'coat')
    G = _equine(pose, 'zebra' if kind == 'zebra' else 'horse') if eq else _lion(pose) if kind == 'lion' else _cow(pose)
    iw = ink_w or max(2, int(round(s * .016)))
    x0u, x1u, y0u = (-1.15 if kind == 'lion' else -0.95), (1.25 if kind != 'cow' else 1.25), -1.95
    Wd, Hd = int((x1u - x0u) * s) + 2 * iw + 8, int((-y0u + .08) * s) + 2 * iw + 8
    o = (-x0u * s + iw + 4, -y0u * s + iw + 4)               # unit origin (ground point under the body centre)
    lab = Image.new('L', (Wd, Hd), 0); d = ImageDraw.Draw(lab)
    labf = Image.new('L', (Wd, Hd), 0); df = ImageDraw.Draw(labf)
    for nm, pts, ws, near in G['legs']:
        if near: continue
        sm = _cr(pts, 5, False); wv = np.interp(np.linspace(0, len(pts) - 1, len(sm)), range(len(pts)), ws)
        _poly(df, _limb_poly(sm, wv), s, o, T_LEGF)
        _hoof(df, pts, ws, s, o, kind, T_HOOF, T_LEGF)
    _poly(df, G['ear_f'], s, o, T_EARF)
    # near group, back to front
    _poly(d, G['tail'], s, o, T_TAIL)
    if 'tuft' in G: _poly(d, G['tuft'], s, o, T_TUFT)
    _poly(d, _cr(G['torso'], 6), s, o, T_TORSO)
    _poly(d, G['neck'] if kind in ('lion', 'cow') else G['neck'], s, o, T_NECK)
    if kind == 'cow': _poly(d, G['dew'], s, o, T_NECK)
    if kind == 'lion': _poly(d, _cr(G['mane'][:26], 4), s, o, T_MANE)
    if kind in ('zebra', 'horse'): _poly(d, G['mane'], s, o, T_MANE)
    _poly(d, _cr(G['head'], 5), s, o, T_HEAD)
    if kind == 'cow': _poly(d, G['horn'], s, o, T_HORN)
    _poly(d, G['ear_n'], s, o, T_EARN)
    for nm, pts, ws, near in G['legs']:
        if not near: continue
        sm = _cr(pts, 5, False); wv = np.interp(np.linspace(0, len(pts) - 1, len(sm)), range(len(pts)), ws)
        _poly(d, _limb_poly(sm, wv), s, o, T_LEGN)
        _hoof(d, pts, ws, s, o, kind, T_HOOF, T_LEGN)
    lay = _paint(kind, G, lab, labf, s, o, iw, pose, painted, light, rim, rim_a, sun_k)
    if face < 0:
        lay = ImageOps.mirror(lay); o = (Wd - o[0], o[1])
    res = (lay, o)
    if cache:
        if len(_LAY) > 160: _LAY.clear()
        _LAY[key] = res
    return res


def _hoof(d, pts, ws, s, o, kind, lab, leglab=None):
    a, b = pts[-2], pts[-1]
    w = ws[-1] * (1.15 if kind != 'lion' else 1.25)
    if kind == 'lion':                                         # a round paw
        cx, cy = b[0] + .03, b[1] - .035
        d.ellipse([o[0] + (cx - w * .75) * s, o[1] + (cy - w * .5) * s, o[0] + (cx + w * .75) * s, o[1] + (cy + w * .45) * s], fill=leglab)
        return
    h = .06 if kind != 'cow' else .07
    pts_ = [(b[0] - w * .55, b[1] - h), (b[0] + w * .5, b[1] - h), (b[0] + w * .75, b[1] + .005), (b[0] - w * .6, b[1] + .005)]
    _poly(d, pts_, s, o, lab)


def _paint(kind, G, lab, labf, s, o, iw, pose, painted, light, rim, rim_a, sun_k):
    Hd, Wd = lab.size[1], lab.size[0]
    L = np.asarray(lab); Lf = np.asarray(labf)
    yy, xx = np.mgrid[0:Hd, 0:Wd]
    X = (xx - o[0]) / s; Y = (yy - o[1]) / s
    rgb = np.zeros((Hd, Wd, 3), np.float32)
    zeb = kind == 'zebra'
    hf, th, poll = G['hf'], G['th'], G['poll']
    # head-local coordinates
    c, s_ = math.cos(th), math.sin(th)
    U = (X - poll[0]) * c + (Y - poll[1]) * s_
    V = -(X - poll[0]) * s_ + (Y - poll[1]) * c

    def fill(mask_, col):
        rgb[mask_] = col

    def zebra_field(Xa, Ya, la, coat=False):
        """Stripe amount (0 white .. 1 black) for the zebra pattern over labels la."""
        warp = .10 * np.sin(Ya * 9 + Xa * 2.5) + .05 * np.sin(Xa * 23 + Ya * 4)
        f = 7.6 if not coat else 7.0
        pb = Xa * f + warp
        S = (-0.30, -0.50)
        dist = np.hypot((Xa - S[0]) * 1.0, (Ya - S[1]) * 1.15)
        ph_h = -dist * f * 1.05 + .6 + warp
        w = _sstep(-0.12, -0.34, Xa)
        ph = pb * (1 - w) + ph_h * w
        thr = -.08 + .55 * _sstep(-0.66, -0.47, Ya) * (1 - w) + .1 * _sstep(-0.62, -0.5, Ya) * w
        st = _stripe(ph, thr, .22)
        # neck: stripes across the neck axis, running up into the mane
        base = np.array((0.46, -0.85)); ax = np.array(poll) - base; ax = ax / np.linalg.norm(ax)
        pn = ((Xa - base[0]) * ax[0] + (Ya - base[1]) * ax[1]) * 8.5 + .1 * np.sin(Ya * 14)
        stn = _stripe(pn, -.05, .22)
        # legs: rings, thinner toward the hoof
        pl = Ya * 15 + .05 * np.sin(Xa * 30)
        stl = _stripe(pl, .05 + .25 * _sstep(-.5, -.1, Ya), .25)
        # face: fine stripes across the head, a black muzzle
        ph_f = U * 17 + 1.5 * np.clip(V, -.1, .2) ** 2 * 10
        stf = _stripe(ph_f, .15, .25)
        return st, stn, stl, stf

    m_torso = L == T_TORSO; m_neck = L == T_NECK; m_head = L == T_HEAD; m_leg = L == T_LEGN; m_hoof = L == T_HOOF
    m_mane = L == T_MANE; m_earn = L == T_EARN; m_tail = L == T_TAIL; m_tuft = L == T_TUFT; m_horn = L == T_HORN
    mf_leg = Lf == T_LEGF; mf_hoof = Lf == T_HOOF; mf_ear = Lf == T_EARF
    rgbf = np.zeros((Hd, Wd, 3), np.float32)
    lines = []                                                 # inner feature strokes (unit pts, width k)

    if kind in ('zebra', 'coat', 'horse'):
        base_col = WHITE_FUR if zeb else BAY
        for m_ in (m_torso, m_neck, m_head, m_leg, m_earn): fill(m_, base_col)
        fill(m_hoof, (44, 40, 44)); fill(m_tail, BLACK_FUR if not zeb else WHITE_FUR); fill(m_tuft, BLACK_FUR)
        fill(m_mane, WHITE_FUR if zeb else BLACK_FUR)
        rgbf[mf_leg] = base_col; rgbf[mf_hoof] = (40, 36, 40); rgbf[mf_ear] = base_col
        if zeb:
            st, stn, stl, stf = zebra_field(X, Y, L)
            blk = np.zeros((Hd, Wd), np.float32)
            blk[m_torso] = st[m_torso]; blk[m_neck] = stn[m_neck]; blk[m_leg] = stl[m_leg]
            blk[m_head] = stf[m_head]
            blk[m_mane] = np.clip(stn[m_mane] * 1.0, 0, 1)
            muz = m_head & (U > .43)
            blk[muz] = 1.0
            blk[m_earn] = 0.0
            fb = np.zeros((Hd, Wd), np.float32); fb[mf_leg] = stl[mf_leg]
            col_b = np.array(BLACK_FUR, np.float32); col_w = np.array(WHITE_FUR, np.float32)
            rgb[...] = rgb * (1 - blk[..., None]) + col_b * blk[..., None]
            rgbf[...] = rgbf * (1 - fb[..., None]) + col_b * fb[..., None]
            # tail: striped top, black tuft
            tb = _stripe(Y * 14, .1, .3); tm = m_tail
            rgb[tm] = col_w * (1 - tb[tm][..., None]) + col_b * tb[tm][..., None]
            rgb[muz] = (44, 36, 38)
        else:
            # bay: black points (lower legs, mane, tail), a darker muzzle, a white star
            lowleg = m_leg & (Y > -0.30)
            rgb[lowleg] = (52, 34, 28)
            rgbf[mf_leg & (Y > -0.30)] = (40, 26, 22)
            muz = m_head & (U > .45)
            rgb[muz] = rgb[muz] * .55 + np.array((60, 38, 32)) * .45
            star = m_head & (((U - .12) / .045) ** 2 + ((V + .06) / .03) ** 2 < 1)
            rgb[star] = (244, 236, 222)
            if kind == 'coat':
                # the fitted zebra-striped rug: torso + neck above the hem, the head stays bare
                hem = -0.50 - .09 * _sstep(.25, .62, X) - .06 * _sstep(-.3, -.62, X) - .012 * np.sin(X * 16)
                coat = (m_torso | m_neck | m_mane | (m_leg & (Y < hem)) | (m_tail & (Y < -.88))) & (Y < hem)
                coat &= ~m_head
                near_head = np.hypot(X - poll[0], Y - poll[1]) < .17
                coat &= ~((m_neck | m_mane) & near_head)
                st, stn, stl, stf = zebra_field(X, Y, L, coat=True)
                blk = np.where(m_neck | m_mane, stn, st)
                col_b = np.array((26, 24, 30), np.float32); col_w = np.array((244, 242, 236), np.float32)
                cc = col_w * (1 - blk[..., None]) + col_b * blk[..., None]
                # fabric folds: soft vertical darker bands
                fold = 1 - .07 * (np.sin(X * 23 + 1.3) > .6) * _sstep(-.85, -.55, Y)
                cc *= fold[..., None]
                rgb[coat] = cc[coat]
                # binding along the hem and the hood front
                bind = coat & ((hem - Y) < .028)
                rgb[bind] = (34, 30, 38)
                dpp = np.hypot(X - poll[0], Y - poll[1])
                hood = (m_neck | m_mane) & (dpp >= .17) & (dpp < .195)
                rgb[hood] = (34, 30, 38)
                G['coat'] = coat
    elif kind == 'lion':
        for m_ in (m_torso, m_neck, m_leg, m_tail, m_earn): fill(m_, LION)
        fill(m_head, LION); fill(m_hoof, LION); fill(m_mane, MANE); fill(m_tuft, MANE_D)
        rgbf[mf_leg] = LION; rgbf[mf_hoof] = LION; rgbf[mf_ear] = MANE
        bw = (_sstep(-0.42, -0.26, Y) * .55)[..., None]
        bel = m_torso | m_leg
        rgb[bel] = (rgb * (1 - bw) + np.array(LION_BELLY, np.float32) * bw)[bel]
        muz = m_head & (U > .18) & (V > -.04)
        rgb[muz] = rgb[muz] * .35 + np.array(LION_BELLY) * .65
        # mane shading: darker toward the outside, wisps
        mm = m_mane
        cxm, cym = hf(.04, .0)
        r = np.hypot(X - cxm, Y - cym)
        k = np.clip((r - .12) / .16, 0, 1)
        wisp = .5 + .5 * np.sin(np.arctan2(Y - cym, X - cxm) * 13 + r * 30)
        mcol = np.array(MANE, np.float32) * (1 - .45 * k[..., None]) + np.array((176, 110, 52), np.float32) * (.25 * wisp[..., None] * (1 - k[..., None]))
        rgb[mm] = mcol[mm]
        rgb[m_earn] = (150, 96, 56)
    else:   # cow
        for m_ in (m_torso, m_neck, m_head, m_leg, m_earn, m_tail): fill(m_, COW)
        fill(m_hoof, (60, 56, 62)); fill(m_tuft, (24, 22, 26)); fill(m_horn, (226, 214, 186))
        rgbf[mf_leg] = (30, 28, 34); rgbf[mf_hoof] = (50, 46, 52); rgbf[mf_ear] = (30, 28, 34)
        muz = m_head & (U > .38)
        rgb[muz] = (104, 92, 98)
        if painted:
            rng = np.random.default_rng(7)
            rough = .05 * np.sin(Y * 37 + X * 7) + .03 * np.sin(Y * 90 + 2.0)
            pb = X * 6.2 + .06 * np.sin(Y * 9) + rough * .5
            stp = _stripe(pb, .25, .18)
            pl = Y * 9 + rough * .4
            stl = _stripe(pl, .25, .2)
            pn = ((X - .5) * .6 + (Y + .9) * .8) * 7 + rough * .5
            stn = _stripe(pn, .25, .18)
            wm = np.zeros((Hd, Wd), np.float32)
            wm[m_torso] = stp[m_torso]; wm[m_leg & (Y < -.12)] = stl[m_leg & (Y < -.12)]; wm[m_neck] = stn[m_neck]
            fbw = np.zeros((Hd, Wd), np.float32); fbw[mf_leg & (Y < -.12)] = stl[mf_leg & (Y < -.12)]
            paint = np.array((240, 240, 236), np.float32)
            rgb[...] = rgb * (1 - wm[..., None]) + paint * wm[..., None]
            rgbf[...] = rgbf * (1 - .85 * fbw[..., None]) + paint * .85 * fbw[..., None]
            G['paint'] = wm

    # ---- shading: form shadow toward the belly / far side, light from `light`
    body = L > 0
    shade = np.ones((Hd, Wd), np.float32)
    if kind == 'lion':
        y_top, y_bot = -0.62, -0.25
    elif kind == 'cow':
        y_top, y_bot = -1.0, -0.36
    else:
        y_top, y_bot = -1.0, -0.47
    tor = m_torso | m_neck | (G.get('coat', np.zeros_like(body)) if isinstance(G.get('coat'), np.ndarray) else False)
    f = _sstep(y_top + (y_bot - y_top) * .45, y_bot + .02, Y)
    shade[m_torso] -= .30 * f[m_torso]
    shade[m_neck] -= .16 * _sstep(-1.1, -0.7, Y)[m_neck]
    shade[m_leg] -= .14 * _sstep(-.6, -.35, Y)[m_leg]
    shade[m_head] -= .14 * _sstep(-.02, .18, V)[m_head]
    # a shadow under the head on the neck (jowl) and where the near leg meets the body
    rgb *= shade[..., None]
    cool = np.array((70, 80, 130), np.float32)
    rgb[m_torso] = rgb[m_torso] * (1 - .12 * f[m_torso][..., None]) + cool * .12 * f[m_torso][..., None]
    rgbf *= .70
    rgbf = rgbf * .85 + np.array((40, 46, 90), np.float32) * .15

    # ---- assemble the two groups with ink outlines
    def group(Lm, col, inner_pairs):
        m = Image.fromarray(((Lm > 0) * 255).astype(np.uint8))
        out = Image.new('RGBA', (Wd, Hd), INK + (0,))
        ink = _dilate(m, iw)
        out.putalpha(ink)
        arr = np.asarray(out).copy()
        sel = Lm > 0
        arr[sel, :3] = np.clip(col[sel], 0, 255).astype(np.uint8)
        # inner ink: boundaries between chosen label pairs
        for a_, b_ in inner_pairs:
            if not a_: continue
            A = Lm == a_; B = Lm == b_
            Bd = np.asarray(_dilate(Image.fromarray((B * 255).astype(np.uint8)), max(1, iw // 2))) > 0
            edge = A & Bd
            arr[edge, :3] = INK
        return Image.fromarray(arr, 'RGBA')
    far = group(Lf, rgbf, [])
    near = group(L, rgb, [(T_LEGN, T_TORSO) if kind != 'lion' else (0, 0), (T_HEAD, T_NECK), (T_HEAD, T_MANE), (T_EARN, T_HEAD),
                          (T_HOOF, T_LEGN), (T_TAIL, T_TORSO), (T_NECK, T_MANE) if kind in ('lion', 'zebra') else (0, 0),
                          (T_HORN, T_HEAD), (T_MANE, T_TORSO) if kind == 'lion' else (0, 0)])
    # ---- rim light on the lit edge (inside the ink), sun side
    a = (L > 0).astype(np.float32)
    inner = np.asarray(_erode(Image.fromarray((a * 255).astype(np.uint8)), iw), np.float32) / 255
    Ld = np.array(light, np.float32); Ld /= np.linalg.norm(Ld)
    sh = max(2, int(s * .02))
    dx, dy = int(round(Ld[0] * sh)), int(round(Ld[1] * sh))
    mv = np.zeros_like(inner)
    ys_, ye = max(0, -dy), Hd - max(0, dy); xs_, xe = max(0, -dx), Wd - max(0, dx)
    mv[ys_:ye, xs_:xe] = inner[ys_ + dy:ye + dy, xs_ + dx:xe + dx]
    r_ = np.clip(inner * (1 - mv), 0, 1)
    r_ = np.asarray(Image.fromarray((r_ * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(1, s * .006))), np.float32) / 255 * rim_a * sun_k
    na = np.asarray(near, np.float32).copy()
    rc = np.array(rim, np.float32)
    na[..., :3] = na[..., :3] * (1 - r_[..., None]) + (na[..., :3] * .35 + rc * .75).clip(0, 255) * r_[..., None]
    near = Image.fromarray(na.clip(0, 255).astype(np.uint8), 'RGBA')
    # ---- features: eye, nostril, mouth, cheek line, ear insides
    dn = ImageDraw.Draw(near)
    P = lambda u, v: (o[0] + hf(u, v)[0] * s, o[1] + hf(u, v)[1] * s)
    lw = max(2, int(iw * .7))
    blink = pose.get('blink', False)
    if kind in ('zebra', 'horse', 'coat'):
        ex, ey = P(.15, -.035); er = s * (.026 if not zeb else .03)
        if zeb: dn.ellipse([ex - er * 1.8, ey - er * 1.5, ex + er * 1.8, ey + er * 1.5], fill=(60, 54, 58))
        if blink:
            dn.line([(ex - er, ey), (ex + er, ey + er * .2)], fill=INK, width=lw)
        else:
            dn.ellipse([ex - er * 1.25, ey - er, ex + er * 1.25, ey + er], fill=(40, 26, 22), outline=INK, width=max(1, lw // 2))
            dn.ellipse([ex - er * .2, ey - er * .55, ex + er * .35, ey], fill=(236, 230, 220))
            dn.arc([ex - er * 1.6, ey - er * 1.7, ex + er * 1.6, ey + er * .6], 200, 330, fill=INK, width=max(1, lw // 2))
        nx_, ny_ = P(.52, .0); nr = s * .022
        dn.ellipse([nx_ - nr * .8, ny_ - nr * 1.2, nx_ + nr * .8, ny_ + nr * 1.2], fill=(20, 14, 16))
        dn.line([P(.585, .072), P(.545, .082), P(.50, .074)], fill=INK, width=lw, joint='curve')
        dn.line([P(.34, .108), P(.27, .045), P(.17, .03), P(.09, .07)], fill=INK if not zeb else (60, 56, 64), width=max(2, lw - 1), joint='curve')
        ei = ImageDraw.Draw(near)
    elif kind == 'lion':
        ex, ey = P(.17, -.07); er = s * .022
        dn.ellipse([ex - er * 1.3, ey - er * .9, ex + er * 1.3, ey + er * .9], fill=(214, 170, 60) if not blink else LION, outline=INK, width=max(1, lw // 2))
        if not blink:
            dn.ellipse([ex - er * .45, ey - er * .8, ex + er * .55, ey + er * .8], fill=(20, 16, 18))
        dn.line([(ex - er * 1.6, ey - er * 1.1), (ex + er * 1.2, ey - er * 1.5)], fill=INK, width=lw)   # brow: intent
        nx_, ny_ = P(.31, .0)
        dn.polygon([P(.335, -.03), P(.335, .04), P(.29, .025), P(.285, -.015)], fill=(60, 36, 34))
        dn.line([P(.30, .04), P(.30, .09), P(.23, .12)], fill=INK, width=lw, joint='curve')
        for k in range(3):
            dn.line([P(.27, .07 + k * .02), P(.40, .05 + k * .035)], fill=(250, 240, 220), width=max(1, lw // 2))
    else:
        ex, ey = P(.14, -.03); er = s * .025
        dn.ellipse([ex - er * 1.2, ey - er, ex + er * 1.2, ey + er], fill=(30, 22, 22) if not blink else COW, outline=(200, 190, 190), width=max(1, lw // 2))
        if not blink: dn.ellipse([ex - er * .2, ey - er * .6, ex + er * .3, ey - er * .1], fill=(230, 224, 220))
        nx_, ny_ = P(.44, .0); nr = s * .022
        dn.ellipse([nx_ - nr, ny_ - nr * 1.2, nx_ + nr, ny_ + nr * 1.2], fill=(40, 30, 34))
        dn.line([P(.47, .09), P(.40, .11)], fill=INK, width=lw)
    # ear insides
    if kind in ('zebra', 'horse', 'coat'):
        ep = G['ear_n']; cx_ = sum(p[0] for p in ep) / len(ep); cy_ = sum(p[1] for p in ep) / len(ep)
        inner_ear = [(cx_ + (x - cx_) * .55, cy_ + (y - cy_) * .55 + .01) for x, y in ep]
        dn.polygon([(o[0] + x * s, o[1] + y * s) for x, y in inner_ear], fill=(196, 186, 184) if zeb else (110, 62, 40))
        if zeb:   # black band + tip on the ear
            tip = min(ep, key=lambda p: p[1])
            bm = Image.new('L', near.size, 0)
            ImageDraw.Draw(bm).polygon([(o[0] + x * s, o[1] + y * s) for x, y in ep], fill=255)
            tm_ = Image.new('L', near.size, 0)
            ImageDraw.Draw(tm_).ellipse([o[0] + (tip[0] - .06) * s, o[1] + (tip[1] - .04) * s, o[0] + (tip[0] + .06) * s, o[1] + (tip[1] + .065) * s], fill=255)
            near.paste(Image.new('RGBA', near.size, BLACK_FUR + (255,)), (0, 0), ImageChops.multiply(bm, tm_))
    out = far
    out.alpha_composite(near)
    return out


def put(img, kind, x, y, s, alpha=1.0, **kw):
    """Draw an animal with its ground point at (x, y). Returns info with key points in frame px."""
    lay, o = quad(kind, s, **kw)
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    ox, oy = int(round(x - o[0])), int(round(y - o[1]))
    _paste(img, lay, ox, oy)
    face = kw.get('face', 1)
    pose = kw.get('pose') or {}
    G = _equine(pose, 'zebra' if kind == 'zebra' else 'horse') if kind in ('zebra', 'horse', 'coat') else _lion(pose) if kind == 'lion' else _cow(pose)
    def P(u):
        return (x + face * u[0] * s, y + u[1] * s)
    hf = G['hf']
    eye = hf(.15, -.035) if kind != 'lion' else hf(.17, -.07)
    head_c = hf(.25, .03) if kind != 'lion' else hf(.12, 0)
    return {'eye': P(eye), 'head': P(head_c), 'muzzle': P(hf(.5, .03) if kind != 'lion' else hf(.3, .03)), 'flank': P((0.0, -0.72)),
            'back': P((0.0, -0.98)), 'haunch': P((-0.45, -0.78)), 'shoulder': P((0.4, -0.78)), 'neck': P((0.62, -1.15)),
            'poll': P(G['poll']), 'box': (x - 1.0 * s, y - 1.9 * s, x + 1.0 * s, y), 's': s, 'face': face,
            'belly': P((0.0, -0.5)), 'rump': P((-0.55, -0.92))}


def _paste(img, lay, ox, oy):
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(img.width, ox + lay.width), min(img.height, oy + lay.height)
    if x1 <= x0 or y1 <= y0: return
    img.alpha_composite(lay.crop((x0 - ox, y0 - oy, x1 - ox, y1 - oy)), (x0, y0))


def contact(img, x, y, w, alpha=.45, col=(40, 50, 30)):
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).ellipse([x - w / 2, y - w * .06, x + w / 2, y + w * .06], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(max(3, w * .03)))
    img.paste(Image.new('RGBA', img.size, col + (255,)), (0, 0), m.point(lambda v: int(v * alpha)))


# ---------------------------------------------------------------- the horse fly
EYE_G = (64, 176, 92)
EYE_G2 = (150, 220, 96)
EYE_V = (120, 60, 150)
FLY_BODY = (96, 86, 80)
FLY_DARK = (54, 46, 44)
FLY_PALE = (196, 180, 150)
_FLY = {}


def fly_layer(L, wing='blur', legs=0.0, ph=0.0, eye=True, glow=False):
    """Side view, facing right. L = body length in px. Returns (layer, centre)."""
    L = max(8, int(L))
    key = (L, wing, round(legs, 2), int(ph * 6) % 6 if wing == 'blur' else 0, glow)
    if key in _FLY: return _FLY[key]
    S = 2 if L < 160 else 1                                    # small flies: supersample for clean edges
    Ls = L * S
    pad = int(Ls * .9)
    Wd, Hd = int(Ls * 1.5) + 2 * pad // 2, int(Ls * 1.5) + pad // 2
    lay = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = Wd * .5, Hd * .52
    P = lambda x, y: (cx + x * Ls, cy + y * Ls)
    iw = max(2, int(Ls * .022))
    # wings behind the body: the far wing first (fainter)
    def wing_poly(base, ang, ln, wd):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
        pts = []
        for k in range(17):
            q = k / 16
            x = q * ln; y = wd * math.sin(math.pi * min(1, q * 1.08)) ** .7 * (1.0 - .25 * q)
            pts.append((base[0] + ux * x + nx * y, base[1] + uy * x + ny * y))
        for k in range(16, -1, -1):
            q = k / 16
            x = q * ln; y = -wd * .45 * math.sin(math.pi * q) ** .9
            pts.append((base[0] + ux * x + nx * y, base[1] + uy * x + ny * y))
        return pts, (ux, uy, nx, ny)
    base = P(.12, -.16)
    wl = []
    if wing == 'blur':
        q = (ph * 6) % 6 / 6
        angs = [200 - 70 * math.sin(2 * math.pi * (q + j / 5)) for j in range(5)]
        for j, ag in enumerate(sorted(angs)):
            wl.append((ag, .10 + .05 * j))
        for ag, al in wl:
            pts, _ = wing_poly(base, ag, Ls * .78, Ls * .2)
            m = Image.new('L', lay.size, 0); ImageDraw.Draw(m).polygon(pts, fill=int(255 * al * 1.6))
            lay.paste(Image.new('RGBA', lay.size, (220, 236, 250, 255)), (0, 0), ImageChops.lighter(m, Image.new('L', lay.size, 0)))
        # the blur fan edges
        fan = Image.new('L', lay.size, 0); df = ImageDraw.Draw(fan)
        df.pieslice([base[0] - Ls * .8, base[1] - Ls * .8, base[0] + Ls * .8, base[1] + Ls * .8], 125, 272, fill=70)
        fan = fan.filter(ImageFilter.GaussianBlur(Ls * .03))
        lay.alpha_composite(Image.merge('RGBA', [Image.new('L', lay.size, 230), Image.new('L', lay.size, 240), Image.new('L', lay.size, 255), fan]))
    else:
        ag = {'fold': 182, 'up': 230, 'spread': 205}[wing]
        for k, (dag, al, off) in enumerate(((10, .55, (-.02, -.02)), (0, .8, (0, 0)))):
            b = (base[0] + off[0] * Ls, base[1] + off[1] * Ls)
            pts, (ux, uy, nx, ny) = wing_poly(b, ag - dag, Ls * .8, Ls * .17)
            m = Image.new('L', lay.size, 0); ImageDraw.Draw(m).polygon(pts, fill=int(255 * al * .75))
            col = (214, 226, 236)
            lay.paste(Image.new('RGBA', lay.size, col + (255,)), (0, 0), m)
            d.line(pts + [pts[0]], fill=(70, 70, 86), width=max(1, iw // 2))
            for vq, vw in ((.25, .55), (.5, .75), (.75, .55)):          # veins
                a0 = (b[0] + ux * Ls * .05, b[1] + uy * Ls * .05)
                e = (b[0] + ux * Ls * .8 * vw + nx * Ls * .17 * (vq - .3), b[1] + uy * Ls * .8 * vw + ny * Ls * .17 * (vq - .3))
                d.line([a0, e], fill=(90, 90, 110), width=max(1, iw // 2))
            # a smoky patch near the leading edge
            sm_ = Image.new('L', lay.size, 0)
            ImageDraw.Draw(sm_).ellipse([b[0] + ux * Ls * .3 + nx * Ls * .05 - Ls * .07, b[1] + uy * Ls * .3 + ny * Ls * .05 - Ls * .05,
                                         b[0] + ux * Ls * .3 + nx * Ls * .05 + Ls * .07, b[1] + uy * Ls * .3 + ny * Ls * .05 + Ls * .05], fill=70)
            lay.paste(Image.new('RGBA', lay.size, (90, 80, 76, 255)), (0, 0), ImageChops.multiply(sm_, m))
    # legs (far legs drawn darker first, then near)
    def leg(rootx, k, near):
        r = P(rootx, .10)
        # tucked: folded back under the body; extended: reaching forward-down
        a1 = math.radians(120 - 70 * legs + k * 18 * (1 - legs) - k * 14 * legs)
        a2 = math.radians(150 - 95 * legs + k * 10)
        l1, l2 = Ls * .2, Ls * .22
        p1 = (r[0] + math.cos(a1) * l1, r[1] + math.sin(a1) * l1)
        p2 = (p1[0] + math.cos(a2) * l2, p1[1] + math.sin(a2) * l2)
        col = (36, 30, 30) if near else (70, 62, 60)
        w = max(2, int(Ls * .028))
        d.line([r, p1, p2], fill=col, width=w, joint='curve')
        d.ellipse([p2[0] - w, p2[1] - w, p2[0] + w, p2[1] + w], fill=col)
    for k, rx in enumerate((.18, .10, .02)):
        leg(rx + .03, k - 1, False)
    # abdomen
    abd = [P(.02, -.10), P(-.15, -.14), P(-.34, -.13), P(-.50, -.08), P(-.60, .0), P(-.56, .07), P(-.40, .11), P(-.18, .12), P(.03, .09)]
    abd = _cr(abd, 5)
    d.polygon(abd, fill=FLY_BODY, outline=INK, width=iw)
    m_abd = Image.new('L', lay.size, 0); ImageDraw.Draw(m_abd).polygon(abd, fill=255)
    bands = Image.new('L', lay.size, 0); db = ImageDraw.Draw(bands)
    for k in range(5):
        x = .0 - .12 * k
        db.polygon([P(x - .015, -.2), P(x + .02, -.2), P(x - .01, .2), P(x - .045, .2)], fill=255)
    lay.paste(Image.new('RGBA', lay.size, FLY_PALE + (255,)), (0, 0), ImageChops.multiply(bands, m_abd.filter(ImageFilter.MinFilter(max(3, iw | 1)))))
    sh = Image.new('L', lay.size, 0); ImageDraw.Draw(sh).polygon([P(.1, .02), P(-.7, .02), P(-.7, .3), P(.1, .3)], fill=110)
    lay.paste(Image.new('RGBA', lay.size, FLY_DARK + (255,)), (0, 0), ImageChops.multiply(sh, m_abd.filter(ImageFilter.MinFilter(max(3, iw | 1)))))
    d.polygon(abd, outline=INK, width=iw)
    # thorax: humped
    th = _cr([P(.02, -.04), P(.04, -.17), P(.14, -.23), P(.27, -.19), P(.33, -.08), P(.31, .08), P(.20, .13), P(.06, .11)], 5)
    d.polygon(th, fill=FLY_BODY)
    m_th = Image.new('L', lay.size, 0); ImageDraw.Draw(m_th).polygon(th, fill=255)
    st = Image.new('L', lay.size, 0); ds = ImageDraw.Draw(st)
    for k in range(3):
        ds.line([P(.05, -.15 + k * .07), P(.3, -.15 + k * .055)], fill=200, width=max(2, int(Ls * .02)))
    lay.paste(Image.new('RGBA', lay.size, FLY_PALE + (255,)), (0, 0), ImageChops.multiply(st, m_th))
    lay.paste(Image.new('RGBA', lay.size, FLY_DARK + (255,)), (0, 0), ImageChops.multiply(sh, m_th))
    d.polygon(th, outline=INK, width=iw)
    if L > 120:                                                 # bristles
        rng = np.random.default_rng(4)
        for k in range(26):
            a_ = rng.uniform(-2.6, -.3); x0_, y0_ = P(.17 + .14 * math.cos(a_), -.04 + .17 * math.sin(a_))
            d.line([(x0_, y0_), (x0_ + math.cos(a_) * Ls * .035, y0_ + math.sin(a_) * Ls * .035)], fill=INK, width=max(1, iw // 2))
    # near legs
    for k, rx in enumerate((.20, .12, .04)):
        leg(rx, k - 1, True)
    # head + the huge compound eye
    hd = _cr([P(.30, -.12), P(.38, -.19), P(.47, -.17), P(.53, -.06), P(.52, .07), P(.45, .14), P(.36, .13), P(.30, .05)], 5)
    d.polygon(hd, fill=(70, 60, 56), outline=INK, width=iw)
    eye_b = [P(.335, -.135), P(.40, -.18), P(.47, -.155), P(.51, -.06), P(.50, .055), P(.45, .115), P(.38, .11), P(.34, .04), P(.325, -.05)]
    eye_b = _cr(eye_b, 5)
    m_eye = Image.new('L', lay.size, 0); ImageDraw.Draw(m_eye).polygon(eye_b, fill=255)
    lay.paste(Image.new('RGBA', lay.size, EYE_G + (255,)), (0, 0), m_eye)
    if eye:
        # iridescent bands (zigzag violet) and a light gradient
        bandm = Image.new('L', lay.size, 0); dbm = ImageDraw.Draw(bandm)
        for k in range(4):
            y = -.13 + k * .07
            pts = [P(.32 + j * .025, y + (.012 if j % 2 else -.012)) for j in range(10)]
            dbm.line(pts, fill=255, width=max(2, int(Ls * .022)))
        lay.paste(Image.new('RGBA', lay.size, EYE_V + (255,)), (0, 0), ImageChops.multiply(bandm, m_eye))
        hi = Image.new('L', lay.size, 0)
        ImageDraw.Draw(hi).ellipse([P(.35, -.16)[0], P(.35, -.16)[1], P(.47, -.04)[0], P(.47, -.04)[1]], fill=150)
        hi = hi.filter(ImageFilter.GaussianBlur(Ls * .02))
        lay.paste(Image.new('RGBA', lay.size, EYE_G2 + (255,)), (0, 0), ImageChops.multiply(hi, m_eye))
        if L > 120:                                              # facets
            fm = Image.new('L', lay.size, 0); dfm = ImageDraw.Draw(fm)
            st_ = max(4, int(Ls * .025))
            for yy in range(int(P(0, -.2)[1]), int(P(0, .14)[1]), st_):
                for xx in range(int(P(.32, 0)[0]) + (yy // st_ % 2) * st_ // 2, int(P(.52, 0)[0]), st_):
                    dfm.ellipse([xx - 1, yy - 1, xx + 1, yy + 1], fill=90)
            lay.paste(Image.new('RGBA', lay.size, (20, 60, 40, 255)), (0, 0), ImageChops.multiply(fm, m_eye))
        gl = Image.new('L', lay.size, 0)
        ImageDraw.Draw(gl).ellipse([P(.38, -.14)[0], P(.38, -.14)[1], P(.42, -.10)[0], P(.42, -.10)[1]], fill=230)
        lay.paste(Image.new('RGBA', lay.size, (240, 255, 240, 255)), (0, 0), gl)
    d.polygon(eye_b, outline=INK, width=max(2, iw - 1))
    # antennae + mouthparts (a short stout blade)
    d.line([P(.50, -.12), P(.58, -.17), P(.64, -.16)], fill=INK, width=max(2, int(Ls * .02)), joint='curve')
    d.polygon([P(.44, .12), P(.49, .11), P(.52, .25), P(.47, .26)], fill=(60, 50, 48), outline=INK)
    if glow:
        m = lay.split()[3].filter(ImageFilter.GaussianBlur(Ls * .05))
        g = Image.new('RGBA', lay.size, (255, 250, 200, 0)); g.putalpha(m.point(lambda v: int(v * .5)))
        g.alpha_composite(lay); lay = g
    if S > 1:
        lay = lay.resize((lay.width // S, lay.height // S), Image.LANCZOS)
        cx, cy = cx / S, cy / S
    res = (lay, (cx, cy))
    if len(_FLY) > 400: _FLY.clear()
    _FLY[key] = res
    return res


def put_fly(img, x, y, L, ang=0.0, alpha=1.0, **kw):
    """Paste the fly centred on its thorax at (x, y). L < 0 faces left. ang: deg, + = nose up."""
    face = 1 if L >= 0 else -1
    lay, (cx, cy) = fly_layer(abs(L), **kw)
    if face < 0:
        lay = ImageOps.mirror(lay); cx = lay.width - cx
    if ang:
        lay = lay.rotate(ang * face, resample=Image.BICUBIC, center=(cx, cy))
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    _paste(img, lay, int(round(x - cx)), int(round(y - cy)))

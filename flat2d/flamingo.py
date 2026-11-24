"""The flamingo kit (video 10, flamingo-one-leg): a careful side-view flamingo for flat2d.

Unit space: 1 unit ~ the height of the back above the ground (the ground point under the body centre is (0, 0),
y grows DOWN, the bird faces +x). Parts are built as unit polygons, rasterised at 2x into masks, painted per part
(gradients, feather scallops, black flight feathers, rim light, form shadow) and given ONE ink outline round the
silhouette (LESSONS: label/mask painting, one outline), the far leg behind in its own darker group.

Anatomy kept true: a long S-shaped neck, a small head, a thick bill bent down halfway (pale pink base, black tip), a
yellow eye, graded pink-coral plumage with deep coral wing coverts and black flight feathers along the folded wing's
lower rear edge, long thin legs with the ANKLE (the backward-bending joint) halfway down, a webbed foot, the knee
hidden in the belly feathers. The lifted leg folds into a backward '<' under the belly with the foot tucked up.

pose keys: sleep 0..1 (neck laid back, head on the back, eyes shut), eye 0..1, nod (rad), sway (rad, neck),
  fold 0..1 (far leg lifted), fx (near foot x), fx2 (far foot x when down), tilt (deg, body), drop (unit, body lowered),
  breath 0..1, ruffle 0..1.
kinds: 'adult' (Caribbean pink-coral), 'pale' (greater flamingo, paler), 'juv' (grey juvenile), 'specimen'
  (the 2017 study bird: an adult, eyes closed, a little less saturated).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
from animals import _cr, _limb_poly, _dilate, _erode, _paste, contact

INK = (24, 16, 26)
PAL = {
    'adult': dict(body=(250, 168, 172), body_hi=(255, 214, 210), body_lo=(226, 104, 124), wing=(236, 78, 102),
                  wing_hi=(255, 140, 146), wing_lo=(190, 46, 78), neck=(252, 172, 176), neck_lo=(232, 118, 136),
                  head=(248, 150, 160), face=(250, 226, 220), beak=(246, 220, 214), beak_lo=(214, 168, 170),
                  leg=(238, 120, 146), leg_lo=(196, 76, 108), leg_hi=(255, 178, 192), black=(26, 22, 30),
                  eye=(252, 214, 60), rim=(255, 236, 226)),
    'pale': dict(body=(252, 206, 206), body_hi=(255, 234, 230), body_lo=(234, 160, 170), wing=(242, 112, 128),
                 wing_hi=(255, 170, 172), wing_lo=(202, 70, 96), neck=(252, 212, 210), neck_lo=(236, 168, 176),
                 head=(250, 200, 202), face=(252, 236, 230), beak=(248, 196, 200), beak_lo=(214, 150, 160),
                 leg=(240, 140, 162), leg_lo=(200, 92, 120), leg_hi=(255, 190, 204), black=(26, 22, 30),
                 eye=(252, 220, 80), rim=(255, 240, 232)),
    'juv': dict(body=(196, 188, 184), body_hi=(226, 220, 214), body_lo=(150, 140, 140), wing=(150, 138, 132),
                wing_hi=(196, 186, 178), wing_lo=(108, 96, 94), neck=(204, 196, 192), neck_lo=(160, 150, 150),
                head=(190, 182, 180), face=(214, 206, 200), beak=(150, 146, 150), beak_lo=(110, 106, 112),
                leg=(92, 88, 94), leg_lo=(60, 56, 62), leg_hi=(140, 134, 140), black=(40, 36, 40),
                eye=(216, 200, 120), rim=(240, 236, 230), blush=(240, 190, 190)),
}
PAL['specimen'] = {k: tuple(int(c * .9 + sum(v) / 3 * .1) for c in v) for k, v in PAL['adult'].items()}

SS = 2                      # supersample
LT, LM = 0.29, 0.36         # tibiotarsus (knee -> ankle), tarsometatarsus (ankle -> foot)


def lerp(a, b, t): return a + (b - a) * t
def lerpc(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def lerpp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _rotp(p, c, a):
    ca, sa = math.cos(a), math.sin(a); x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def ik(K, F, back=True):
    """Ankle position of a two-link leg (knee K, foot F); the ankle bends BACKWARD (-x), as in a bird."""
    dx, dy = F[0] - K[0], F[1] - K[1]; d = math.hypot(dx, dy)
    d = min(d, LT + LM - 1e-4); d = max(d, abs(LM - LT) + 1e-4)
    a = (LT * LT - LM * LM + d * d) / (2 * d); h = math.sqrt(max(0.0, LT * LT - a * a))
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    mx, my = K[0] + ux * a, K[1] + uy * a
    # the two solutions: perpendicular (-uy, ux) / (uy, -ux); pick the one toward -x (backward)
    s1 = (mx - uy * h, my + ux * h); s2 = (mx + uy * h, my - ux * h)
    return s1 if (s1[0] < s2[0]) == back else s2


# ---------------------------------------------------------------- geometry
BODY = [(0.140, -0.800), (0.195, -0.750), (0.205, -0.690), (0.170, -0.625), (0.090, -0.585), (-0.020, -0.580),
        (-0.120, -0.605), (-0.200, -0.645), (-0.255, -0.680), (-0.225, -0.715), (-0.130, -0.775), (0.000, -0.815),
        (0.085, -0.818)]
WING = [(0.090, -0.790), (0.120, -0.745), (0.090, -0.690), (0.010, -0.660), (-0.100, -0.655), (-0.200, -0.672),
        (-0.240, -0.690), (-0.200, -0.728), (-0.110, -0.778), (-0.010, -0.808), (0.050, -0.810)]
PRIM = [(0.010, -0.672), (-0.090, -0.652), (-0.200, -0.650), (-0.320, -0.668), (-0.330, -0.690), (-0.250, -0.712),
        (-0.150, -0.705), (-0.060, -0.690)]
# neck centrelines (base in the chest -> head centre) for the upright and sleeping poses
NECK_UP = [(0.140, -0.735), (0.190, -0.810), (0.225, -0.905), (0.200, -1.000), (0.130, -1.075), (0.105, -1.160),
           (0.140, -1.240), (0.195, -1.280)]
NECK_SLEEP = [(0.140, -0.735), (0.185, -0.785), (0.185, -0.830), (0.140, -0.850), (0.070, -0.850), (0.000, -0.840),
              (-0.060, -0.830), (-0.105, -0.825)]
NECK_W = [0.085, 0.066, 0.052, 0.046, 0.044, 0.042, 0.044, 0.050]


def geometry(pose, kind='adult'):
    p = pose or {}
    sl = float(p.get('sleep', 0.0)); br = float(p.get('breath', .5))
    tilt = math.radians(p.get('tilt', 0.0)); drop = float(p.get('drop', 0.0))
    rise = -0.006 * br
    piv = (0.02, -0.62)                                           # knee/hip pivot of the body
    def B(pt):                                                    # body space -> unit space (tilt about the pivot, drop)
        q = _rotp(pt, piv, tilt)
        return (q[0], q[1] + drop + rise)
    G = {}
    G['body'] = [B(q) for q in _cr(BODY, 6)]
    G['wing'] = [B(q) for q in _cr(WING, 6)]
    G['prim'] = [B(q) for q in _cr(PRIM, 5)]
    # primaries as individual feathers (long, narrow, overlapping) along the lower rear edge
    feathers = []
    for i in range(6):
        f = i / 5
        a = lerpp((0.00, -0.672), (-0.20, -0.700), f)
        b = lerpp((-0.15, -0.656), (-0.335, -0.680), f)
        feathers.append([B(a), B(lerpp(a, b, .5)), B(b)])
    G['feathers'] = feathers
    # neck: blend upright -> sleep, sway bends the upper neck
    sway = float(p.get('sway', 0.0))
    cl = []
    for i, (u_, s_) in enumerate(zip(NECK_UP, NECK_SLEEP)):
        q = lerpp(u_, s_, sl)
        k = i / (len(NECK_UP) - 1)
        q = _rotp(q, NECK_UP[0], sway * k * (1 - sl))
        cl.append(B(q))
    G['neck_c'] = cl
    ncl = _cr(cl, 6, False)
    ws = np.interp(np.linspace(0, len(cl) - 1, len(ncl)), range(len(cl)), NECK_W)
    G['neck'] = _limb_poly(ncl, ws)
    # head: centre + direction. upright: facing forward, a little down; sleep: lying on the back, facing backward
    hc = cl[-1]
    d_up = math.atan2(cl[-1][1] - cl[-2][1], cl[-1][0] - cl[-2][0])
    a_up = 0.35 + float(p.get('nod', 0.0))                         # rad, + = beak down
    a_sl = math.pi - 0.25
    ha = lerp(a_up, a_sl, sl) if sl < .5 else lerp(a_up + 2 * math.pi * 0, a_sl, sl)
    ha += tilt
    G['head_c'], G['head_a'] = hc, ha
    flip = sl > .5                                               # head upside down vs. the head frame when sleeping
    G['head_flip'] = flip
    def Hf(x, y):
        y = -y if flip else y
        ca, sa = math.cos(ha), math.sin(ha)
        return (hc[0] + x * ca - y * sa, hc[1] + x * sa + y * ca)
    G['Hf'] = Hf
    G['head'] = [Hf(x, y) for x, y in _cr([(0.048, -0.004), (0.030, -0.040), (-0.010, -0.050), (-0.048, -0.030),
                                           (-0.056, 0.006), (-0.036, 0.036), (0.004, 0.044), (0.040, 0.030)], 5)]
    G['face'] = [Hf(x, y) for x, y in _cr([(0.046, -0.010), (0.034, -0.030), (0.014, -0.032), (0.006, -0.004),
                                           (0.016, 0.026), (0.040, 0.026)], 4)]
    up = [(0.034, -0.030), (0.072, -0.030), (0.100, -0.020), (0.118, 0.004), (0.128, 0.040), (0.126, 0.074)]
    lo = [(0.126, 0.074), (0.114, 0.078), (0.104, 0.054), (0.088, 0.036), (0.064, 0.034), (0.034, 0.030)]
    beak = _cr(up, 4, False) + _cr(lo, 4, False)
    G['beak'] = [Hf(x, y) for x, y in beak]
    tip = [q for q in beak if q[0] > 0.092 or (q[0] > 0.084 and q[1] > 0.030)]
    G['beak_tip'] = [Hf(x, y) for x, y in _cr([(0.106, -0.016), (0.117, -0.004), (0.124, 0.016), (0.131, 0.040),
                                               (0.127, 0.076), (0.112, 0.079), (0.105, 0.058), (0.099, 0.042)], 4)]
    G['gape'] = [Hf(x, y) for x, y in [(0.036, 0.006), (0.066, 0.010), (0.092, 0.016), (0.110, 0.036)]]
    G['eye'] = Hf(-0.006, -0.012)
    G['beak_tip_pt'] = Hf(0.125, 0.074)
    # legs: knees hidden in the belly feathers
    Kn, Kf = B((0.035, -0.615)), B((0.000, -0.618))
    fx, fx2, fold = float(p.get('fx', 0.0)), float(p.get('fx2', -0.07)), float(p.get('fold', 1.0))
    Fn = (fx, 0.0)
    An = ik(Kn, Fn)
    # far leg: interpolate joint angles between standing and tucked
    Ff_down = (fx2, 0.0); Af_down = ik(Kf, Ff_down)
    def angs(K, A, F):
        return math.atan2(A[1] - K[1], A[0] - K[0]), math.atan2(F[1] - A[1], F[0] - A[0])
    a1d, a2d = angs(Kf, Af_down, Ff_down)
    a1t, a2t = math.atan2(0.80, -0.60) + tilt, math.atan2(-0.70, 0.71) + tilt          # tucked: '<' pointing back
    k = fold * fold * (3 - 2 * fold)
    a1 = lerp(a1d, a1t, k); a2 = lerp(a2d, a2t if a2t > a2d - math.pi else a2t + 2 * math.pi, k)
    Af = (Kf[0] + math.cos(a1) * LT, Kf[1] + math.sin(a1) * LT)
    Ff = (Af[0] + math.cos(a2) * LM, Af[1] + math.sin(a2) * LM)
    G['legs'] = {'near': (Kn, An, Fn), 'far': (Kf, Af, Ff)}
    G['far_fold'] = k
    G['piv'] = B(piv)
    G['belly'] = B((0.03, -0.592))
    G['center'] = B((0.0, -0.69))
    G['back'] = B((-0.02, -0.785))
    return G


def _leg_poly(K, A, F, wt=0.026, wa=0.030, wm=0.018):
    """Tapered leg: knee -> ankle (a knobbly joint) -> foot."""
    pts = [K, lerpp(K, A, .5), lerpp(K, A, .9), A, lerpp(A, F, .1), lerpp(A, F, .55), F]
    ws = [wt * 1.4, wt, wa * .9, wa, wa * .8, wm, wm * .85]
    sm = _cr(pts, 4, False)
    wv = np.interp(np.linspace(0, len(pts) - 1, len(sm)), range(len(pts)), ws)
    return _limb_poly(sm, wv)


def _foot_poly(F, A, tucked=0.0):
    """A webbed foot in side view: three front toes spread a little, joined by the web; a small hind toe.
    tucked: the toes curl and point down/back (foot folded up under the body)."""
    dirx = 1.0
    if tucked > 0:
        a = math.atan2(F[1] - A[1], F[0] - A[0]) + math.pi * .55 * tucked
        L = 0.085 * (1 - .35 * tucked)
        tipc = (F[0] + math.cos(a) * L, F[1] + math.sin(a) * L)
        n = (-math.sin(a), math.cos(a))
        web = [(F[0] - n[0] * .012, F[1] - n[1] * .012), (tipc[0] - n[0] * .022, tipc[1] - n[1] * .022),
               (tipc[0] + n[0] * .022, tipc[1] + n[1] * .022), (F[0] + n[0] * .012, F[1] + n[1] * .012)]
        return web, []
    x, y = F
    web = [(x - 0.022, y - 0.012), (x + 0.012, y - 0.016), (x + 0.060, y - 0.010), (x + 0.100, y - 0.003),
           (x + 0.104, y + 0.004), (x + 0.086, y + 0.006), (x + 0.074, y + 0.003), (x + 0.060, y + 0.008),
           (x + 0.044, y + 0.004), (x + 0.020, y + 0.008), (x - 0.026, y + 0.006)]
    toes = [[(x, y - .004), (x + 0.100, y + 0.000)], [(x, y - .002), (x + 0.082, y + 0.005)], [(x, y), (x + 0.060, y + 0.007)]]
    return web, toes


# ---------------------------------------------------------------- painting
_LAY = {}


def _grad(shape, p0, p1, c0, c1):
    """Linear gradient (h, w, 3) float from point p0 (c0) to p1 (c1), in pixel space."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L2 = dx * dx + dy * dy or 1
    t = np.clip(((xx - p0[0]) * dx + (yy - p0[1]) * dy) / L2, 0, 1)[..., None]
    return np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t


def bird(s, pose=None, kind='adult', light=(-.5, -1.0), cache=True, ink_w=None):
    """Render the flamingo. Returns (RGBA layer, origin px of the unit origin, G)."""
    pose = pose or {}
    key = (kind, round(s), tuple(sorted((k, round(v, 3)) for k, v in pose.items())), light, ink_w)
    if cache and key in _LAY: return _LAY[key]
    G = geometry(pose, kind)
    C = PAL[kind]
    S = s * SS
    allp = G['body'] + G['neck'] + G['beak'] + G['prim'] + [q for leg in G['legs'].values() for q in leg]
    x0u = min(q[0] for q in allp) - .12; x1u = max(q[0] for q in allp) + .16
    y0u = min(q[1] for q in allp) - .08; y1u = max(0.03, max(q[1] for q in allp) + .05)
    Wd, Hd = int((x1u - x0u) * S) + 8, int((y1u - y0u) * S) + 8
    o = (-x0u * S + 4, -y0u * S + 4)
    P = lambda pts: [(o[0] + x * S, o[1] + y * S) for x, y in pts]
    pt = lambda q: (o[0] + q[0] * S, o[1] + q[1] * S)
    iw = (ink_w or max(2, s * .0075)) * SS
    def M(polys, line=None):
        m = Image.new('L', (Wd, Hd), 0); d = ImageDraw.Draw(m)
        for pl in polys: d.polygon(P(pl), fill=255)
        return m
    sleep = float(pose.get('sleep', 0)); eye_open = float(pose.get('eye', 1.0)) * (1 - sleep)
    if kind == 'specimen': eye_open = 0.0
    lay = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
    shape = (Hd, Wd)
    lx, ly = light; ln = math.hypot(lx, ly); lx, ly = lx / ln, ly / ln

    def paint(m, spec, hi=None, lo=None, k_hi=.55, k_lo=.6, spread=.03):
        """Paint a part through mask m on its bounding box only. spec: a colour, or ('g', p0, p1, c0, c1[, mixc, k])."""
        bb = m.getbbox()
        if not bb: return
        pad = int(spread * S) + 4
        x0, y0, x1, y1 = max(0, bb[0] - pad), max(0, bb[1] - pad), min(Wd, bb[2] + pad), min(Hd, bb[3] + pad)
        mc = m.crop((x0, y0, x1, y1)); sh_ = (y1 - y0, x1 - x0)
        if isinstance(spec[0], str):
            _, p0, p1, c0, c1, *rest = spec
            base = _grad(sh_, (p0[0] - x0, p0[1] - y0), (p1[0] - x0, p1[1] - y0), c0, c1)
            if rest: base = base * (1 - rest[1]) + np.array(rest[0], np.float32) * rest[1]
        else:
            base = np.broadcast_to(np.array(spec, np.float32), sh_ + (3,)).copy()
        if hi is not None:
            arr = np.asarray(mc, np.float32) / 255
            sh = max(1, int(spread * S))
            lit = arr - np.asarray(ImageChops.offset(mc, int(-lx * sh), int(-ly * sh)), np.float32) / 255
            dark = arr - np.asarray(ImageChops.offset(mc, int(lx * sh), int(ly * sh)), np.float32) / 255
            lit = np.asarray(Image.fromarray((np.clip(lit, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sh * .5)), np.float32)[..., None] / 255
            dark = np.asarray(Image.fromarray((np.clip(dark, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sh * .6)), np.float32)[..., None] / 255
            base = base * (1 - k_lo * dark) + np.array(lo, np.float32) * (k_lo * dark)
            base = base * (1 - k_hi * lit) + np.array(hi, np.float32) * (k_hi * lit)
        a = Image.fromarray(np.dstack([base.clip(0, 255).astype(np.uint8), np.asarray(mc)]), 'RGBA')
        lay.alpha_composite(a, (x0, y0))

    # ---- far leg group (behind, darker)
    Kf, Af, Ff = G['legs']['far']; tk = G['far_fold']
    mfar = M([_leg_poly(Kf, Af, Ff, .024, .028, .017)])
    web, toes = _foot_poly(Ff, Af, tucked=tk)
    ImageDraw.Draw(mfar).polygon(P(web), fill=255)
    far_ink = _dilate(mfar, int(iw))
    lay.paste(Image.new('RGBA', (Wd, Hd), INK + (255,)), (0, 0), far_ink)
    fc = lerpc(C['leg'], C['leg_lo'], .45)
    paint(mfar, fc, lerpc(C['leg'], C['leg_hi'], .4), C['leg_lo'], .4, .5, .02)
    d = ImageDraw.Draw(lay)
    d.ellipse([*pt((Af[0] - .02, Af[1] - .017)), *pt((Af[0] + .02, Af[1] + .017))], fill=lerpc(fc, C['leg_lo'], .5))

    # ---- near group masks
    mb = M([G['body']]); mn = M([G['neck']]); mh = M([G['head']]); mbk = M([G['beak']])
    mw = M([G['wing']]); mp = M([G['prim']] + [_limb_poly(_cr(f, 4, False), np.linspace(.028, .010, len(_cr(f, 4, False)))) for f in G['feathers']])
    Kn, An, Fn = G['legs']['near']
    ml = M([_leg_poly(Kn, An, Fn)])
    webn, toesn = _foot_poly(Fn, An)
    ImageDraw.Draw(ml).polygon(P(webn), fill=255)
    near = ImageChops.lighter(ImageChops.lighter(ImageChops.lighter(mb, mn), ImageChops.lighter(mh, mbk)), ImageChops.lighter(ImageChops.lighter(mw, mp), ml))
    ink = _dilate(near, int(iw))
    lay.paste(Image.new('RGBA', (Wd, Hd), INK + (255,)), (0, 0), ink)

    # legs (near)
    paint(ml, C['leg'], C['leg_hi'], C['leg_lo'], .55, .6, .016)
    d = ImageDraw.Draw(lay)
    # ankle knob + scales on the tarsus
    d.ellipse([*pt((An[0] - .021, An[1] - .018)), *pt((An[0] + .021, An[1] + .018))], fill=lerpc(C['leg'], C['leg_lo'], .35))
    d.arc([*pt((An[0] - .021, An[1] - .018)), *pt((An[0] + .021, An[1] + .018))], 200, 320, fill=C['leg_hi'], width=max(1, int(S * .005)))
    for i in range(1, 9):
        q = lerpp(An, Fn, .1 + i * .095)
        d.line([pt((q[0] - .007, q[1])), pt((q[0] + .007, q[1] + .002))], fill=lerpc(C['leg'], C['leg_lo'], .6), width=max(1, int(S * .003)))
    for tl in toesn:
        d.line([pt(tl[0]), pt(tl[1])], fill=lerpc(C['leg'], C['leg_lo'], .7), width=max(1, int(S * .004)))

    # body: graded pale back -> deeper belly, scallops
    bb = mb.getbbox() or (0, 0, Wd, Hd)
    paint(mb, ('g', (0, bb[1]), (0, bb[3]), C['body_hi'], C['body_lo'], C['body'], .55), C['rim'], C['body_lo'], .5, .55, .05)
    tex = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0)); dt = ImageDraw.Draw(tex)
    rng = np.random.default_rng(7)
    r = .022 * S
    for row in range(12):
        yy = bb[1] + (row + .5) * (bb[3] - bb[1]) / 14
        off = (row % 2) * r
        for xx in np.arange(bb[0] - r + off, bb[2] + r, r * 2.0):
            j = rng.uniform(-.25, .25) * r
            col = lerpc(C['body'], C['body_lo'], .35) if row > 5 else lerpc(C['body'], C['body_hi'], .6)
            dt.arc([xx - r + j, yy - r * .7, xx + r + j, yy + r * .7], 20, 160, fill=col + (70,), width=max(1, int(S * .003)))
    tex.putalpha(ImageChops.multiply(tex.split()[3], mb))
    lay.alpha_composite(tex)

    # neck + head
    nb = mn.getbbox() or bb
    nspec = ('g', (0, nb[1]), (0, nb[3]), lerpc(C['neck'], C['body_hi'], .3), C['neck'])
    paint(mn, nspec, C['rim'], C['neck_lo'], .55, .55, .025)
    hb = mh.getbbox() or nb
    paint(mh, C['head'], C['rim'], C['neck_lo'], .5, .5, .02)
    mf = M([G['face']])
    fa = np.asarray(mf.filter(ImageFilter.GaussianBlur(S * .006)), np.float32)[..., None] / 255
    face = Image.fromarray(np.dstack([np.broadcast_to(np.array(C['face'], np.uint8), shape + (3,)), (fa[..., 0] * 200 * (np.asarray(mh) > 0)).astype(np.uint8)]), 'RGBA')
    lay.alpha_composite(face)
    # neck/head over the body (sleep): an inner ink line where they overlap
    if sleep > .25:
        over = ImageChops.multiply(_dilate(ImageChops.lighter(mn, mh), int(iw * .7)), mb)
        over = ImageChops.subtract(over, ImageChops.lighter(mn, mh))
        lay.paste(Image.new('RGBA', (Wd, Hd), INK + (255,)), (0, 0), over)
        paint(mn, nspec, C['rim'], C['neck_lo'], .55, .55, .025)
        paint(mh, C['head'], C['rim'], C['neck_lo'], .5, .5, .02)
        lay.alpha_composite(face)

    # beak: pale base, black tip, the gape line
    bk_ink = ImageChops.subtract(_dilate(mbk, int(iw * .7)), mbk)
    bk_ink = ImageChops.multiply(bk_ink, ImageChops.lighter(mh, ImageChops.lighter(mn, mb)))
    lay.paste(Image.new('RGBA', (Wd, Hd), INK + (255,)), (0, 0), bk_ink)
    paint(mbk, C['beak'], (255, 248, 244), C['beak_lo'], .5, .5, .012)
    mt = ImageChops.multiply(M([G['beak_tip']]), mbk)
    paint(mt, C['black'], (110, 104, 116), (0, 0, 0), .6, .2, .012)
    d = ImageDraw.Draw(lay)
    d.line(P(G['gape']), fill=INK, width=max(2, int(S * .006)), joint='curve')
    # eye
    ex, ey = pt(G['eye']); er = .0125 * S
    if eye_open > .15:
        d.ellipse([ex - er * 1.25, ey - er * 1.25, ex + er * 1.25, ey + er * 1.25], fill=INK)
        d.ellipse([ex - er, ey - er * eye_open, ex + er, ey + er * eye_open], fill=C['eye'])
        d.ellipse([ex - er * .42, ey - er * .42 * eye_open, ex + er * .42, ey + er * .42 * eye_open], fill=(10, 8, 12))
        d.ellipse([ex - er * .55, ey - er * .65, ex - er * .15, ey - er * .25], fill=(255, 255, 250))
    else:
        flip = G['head_flip']
        d.arc([ex - er * 1.3, ey - er * 1.0, ex + er * 1.3, ey + er * 1.0], 200 if flip else 20, 340 if flip else 160, fill=INK, width=max(2, int(S * .0055)))

    # wing coverts: deep coral, layered scallops; black primaries along the lower rear edge
    wb = mw.getbbox() or bb
    # primaries first (under the coverts)
    pink_edge = ImageChops.subtract(_dilate(mp, int(iw * .6)), mp)
    lay.paste(Image.new('RGBA', (Wd, Hd), INK + (255,)), (0, 0), ImageChops.multiply(pink_edge, mb))
    paint(mp, C['black'], (90, 84, 100), (0, 0, 0), .5, .3, .01)
    d = ImageDraw.Draw(lay)
    for f in G['feathers']:
        sm = _cr(f, 4, False)
        d.line(P(sm), fill=(70, 66, 80), width=max(1, int(S * .003)))
    wing_ink = ImageChops.subtract(_dilate(mw, int(iw * .55)), mw)
    lay.paste(Image.new('RGBA', (Wd, Hd), lerpc(C['wing_lo'], INK, .55) + (255,)), (0, 0), ImageChops.multiply(wing_ink, mb))
    paint(mw, ('g', (wb[2], wb[1]), (wb[0], wb[3]), C['wing_hi'], C['wing_lo'], C['wing'], .5), C['wing_hi'], C['wing_lo'], .5, .5, .03)
    tex = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0)); dt = ImageDraw.Draw(tex)
    rr = .034 * S
    for row in range(5):
        f = row / 4
        yy = lerp(wb[1] + rr * 1.2, wb[3] - rr * .6, f)
        off = (row % 2) * rr * .9
        for xx in np.arange(wb[0] + off - rr, wb[2] + rr, rr * 1.8):
            # a covert feather: rounded tip pointing back (-x), darker under-edge, pale fringe
            box = [xx - rr * 1.3, yy - rr * .75, xx + rr * .5, yy + rr * .75]
            dt.chord(box, 100, 260, fill=lerpc(C['wing'], C['wing_lo'], .3 + .3 * f) + (60,))
            dt.arc(box, 120, 240, fill=lerpc(C['wing_hi'], (255, 255, 255), .2) + (95,), width=max(1, int(S * .003)))
    # long scapular plumes drooping back over the black flight feathers
    for i in range(6):
        f = i / 5
        a0 = (lerp(wb[0] + (wb[2] - wb[0]) * .55, wb[0] + (wb[2] - wb[0]) * .2, f), lerp(wb[1] + (wb[3] - wb[1]) * .45, wb[1] + (wb[3] - wb[1]) * .6, f))
        a1 = (a0[0] - (wb[2] - wb[0]) * (.35 + .1 * f), a0[1] + (wb[3] - wb[1]) * (.25 + .05 * f))
        mid = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2 - (wb[3] - wb[1]) * .08)
        dt.line([a0, mid, a1], fill=lerpc(C['wing_lo'], (0, 0, 0), .15) + (110,), width=max(1, int(S * .0045)), joint='curve')
        dt.line([(a0[0], a0[1] - S * .004), (mid[0], mid[1] - S * .004)], fill=lerpc(C['wing_hi'], (255, 255, 255), .3) + (90,), width=max(1, int(S * .003)))
    tex.putalpha(ImageChops.multiply(tex.split()[3], mw))
    lay.alpha_composite(tex)
    # ruffle: a few loose covert tips over the lower wing edge (wind / settling)
    # rim light inside the ink on the top edges, form shadow under the belly
    near_in = _erode(near, int(iw * .5))
    arr = np.asarray(near_in, np.float32) / 255
    sh = int(.012 * S)
    lit = np.clip(arr - np.asarray(ImageChops.offset(near_in, int(-lx * sh), int(-ly * sh)), np.float32) / 255, 0, 1)
    lit = np.asarray(Image.fromarray((lit * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sh * .4)), np.float32) / 255
    lit *= 1 - np.asarray(ml, np.float32) / 255 * .5
    la = np.asarray(lay, np.float32)
    rc = np.array(C['rim'], np.float32)
    la[..., :3] = la[..., :3] * (1 - .55 * lit[..., None]) + rc * (.55 * lit[..., None])
    lay = Image.fromarray(la.clip(0, 255).astype(np.uint8), 'RGBA')
    if SS != 1:
        lay = lay.resize((max(1, Wd // SS), max(1, Hd // SS)), Image.LANCZOS)
        o = (o[0] / SS, o[1] / SS)
    res = (lay, o, G)
    if cache:
        if len(_LAY) > 240: _LAY.clear()
        _LAY[key] = res
    return res


def put(img, x, y, s, face=1, kind='adult', pose=None, alpha=1.0, light=(-.5, -1.0), water=None, reflect=0.0,
        water_col=(120, 160, 190), t=0.0, ink_w=None, ret_layer=False):
    """Draw the flamingo with its ground point at (x, y), facing `face` (+1 right, -1 left).
    water: the water surface y in px (feet below it are hidden under a tinted veil); reflect: reflection alpha."""
    lay, o, G = bird(s, pose, kind, light, ink_w=ink_w)
    if face < 0:
        lay = ImageOps.mirror(lay); o = (lay.width - o[0], o[1])
    ox, oy = int(round(x - o[0])), int(round(y - o[1]))
    if reflect > 0 and water is not None:
        reflection(img, lay, ox, oy, water, reflect, water_col, t)
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    if water is not None and water < oy + lay.height:
        cut = int(water - oy)
        top = lay.crop((0, 0, lay.width, max(0, cut)))
        bot = lay.crop((0, max(0, cut), lay.width, lay.height))
        if top.height: _paste(img, top, ox, oy)
        if bot.height:
            a = np.asarray(bot, np.float32)
            k = np.linspace(.55, .15, bot.height)[:, None]
            a[..., :3] = a[..., :3] * (1 - .5) + np.array(water_col, np.float32) * .5
            a[..., 3] *= k
            _paste(img, Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA'), ox, oy + max(0, cut))
    else:
        _paste(img, lay, ox, oy)
    def F(q): return (x + face * q[0] * s, y + q[1] * s)
    Kn, An, Fn = G['legs']['near']; Kf, Af, Ff = G['legs']['far']
    info = {'head': F(G['head_c']), 'eye': F(G['eye']), 'beak': F(G['beak_tip_pt']), 'knee': F(Kn), 'ankle': F(An),
            'foot': F(Fn), 'far_ankle': F(Af), 'far_foot': F(Ff), 'far_knee': F(Kf), 'center': F(G['center']),
            'belly': F(G['belly']), 'back': F(G['back']), 'piv': F(G['piv']), 's': s, 'face': face,
            'neck': [F(q) for q in G['neck_c']], 'box': (ox, oy, ox + lay.width, oy + lay.height)}
    if ret_layer: info['layer'] = (lay, ox, oy)
    return info


def reflection(img, lay, ox, oy, water, alpha, col, t):
    """Mirror the bird about the water line, tint toward the water colour, ripple it in rows, fade with depth."""
    ref = ImageOps.flip(lay)
    ry = int(2 * water - (oy + lay.height))
    a = np.asarray(ref, np.float32).copy()
    a[..., :3] = a[..., :3] * .55 + np.array(col, np.float32) * .45
    hh = a.shape[0]
    fade = np.clip(1 - np.linspace(0, 1, hh) * 1.1, 0, 1) ** 1.2
    a[..., 3] *= fade[:, None] * alpha
    ref = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    out = Image.new('RGBA', ref.size, (0, 0, 0, 0))
    band = 6
    for yb in range(0, ref.height, band):
        dx = int(round(4 * math.sin(yb * .09 + t * 3.1) + 2 * math.sin(yb * .23 - t * 2.3)))
        out.alpha_composite(ref.crop((0, yb, ref.width, min(ref.height, yb + band))), (max(0, dx), yb))
    _paste(img, out, ox, ry)


def ripples(img, x, y, w, t, col=(255, 240, 236), n=3, alpha=.6, period=2.2):
    """Expanding ellipse rings around a leg standing in still water."""
    d = Image.new('L', img.size, 0); dd = ImageDraw.Draw(d)
    for i in range(n):
        k = ((t / period) + i / n) % 1.0
        r = w * (.15 + .85 * k); a = alpha * (1 - k) ** 1.4
        dd.ellipse([x - r, y - r * .16, x + r, y + r * .16], outline=int(255 * a), width=max(2, int(w * .025)))
    img.paste(Image.new('RGBA', img.size, col + (255,)), (0, 0), d)


def flock_bird(d, x, y, h, sleep=1.0, col=(240, 140, 150), leg=(220, 110, 130), ink=None, face=1, seed=0):
    """A small distant flamingo (h = height px): body, neck (up or laid back), one leg, quick to draw."""
    f = face
    bw, bh = h * .30, h * .12
    by = y - h * .55
    body = [(x - f * bw * .55, by), (x + f * bw * .5, by - bh * .4), (x + f * bw * .45, by + bh * .5), (x - f * bw * .2, by + bh * .55)]
    d.line([(x, by + bh * .3), (x - f * h * .02, y - h * .27), (x, y)], fill=leg, width=max(1, int(h * .03)))
    if ink: d.polygon(body, fill=ink)
    d.ellipse([x - bw * .5, by - bh * .55, x + bw * .5, by + bh * .55], fill=col)
    d.polygon([(x - f * bw * .45, by - bh * .1), (x - f * bw * .8, by + bh * .1), (x - f * bw * .4, by + bh * .4)], fill=(30, 24, 30))
    if sleep > .5:
        xa, xb = sorted((x - f * bw * .05, x + f * bw * .3))
        d.ellipse([xa, by - bh * 1.05, xb, by - bh * .3], fill=col)
    else:
        nx = x + f * bw * .42
        d.line([(nx, by - bh * .2), (nx + f * h * .06, by - h * .2), (nx - f * h * .01, by - h * .32), (nx + f * h * .04, by - h * .42)],
               fill=col, width=max(1, int(h * .045)), joint='curve')
        d.ellipse([nx + f * h * .04 - h * .03, by - h * .45, nx + f * h * .04 + h * .03, by - h * .39], fill=col)  # head
        d.line([(nx + f * h * .06, by - h * .42), (nx + f * h * .10, by - h * .38)], fill=(30, 24, 30), width=max(1, int(h * .025)))


if __name__ == '__main__':
    # a test sheet: poses and kinds
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/flamingo_sheet.png'
    img = Image.new('RGBA', (2200, 1500), (120, 170, 196, 255))
    ImageDraw.Draw(img).rectangle([0, 1200, 2200, 1500], fill=(90, 140, 170))
    put(img, 250, 1200, 900, pose={'fold': 1, 'fx': 0.0})
    put(img, 700, 1200, 900, pose={'fold': 1, 'sleep': 1})
    put(img, 1150, 1200, 900, pose={'fold': 0, 'fx': .07, 'fx2': -.07})
    put(img, 1600, 1200, 700, kind='juv', pose={'fold': 1})
    put(img, 1950, 1200, 900, kind='specimen', pose={'fold': 1, 'sleep': 1})
    img.convert('RGB').save(out)

"""The moth kit (video 11, moth-light): a careful hawk moth for flat2d, built as a tiny 3D model projected flat.

LESSONS (cat/zebra/flamingo): hero animals drawn as flat shapes read crude. So the moth is a small 3D model:
- moth-local axes: x forward (head), y to the moth's right, z up (its BACK); unit = the forewing length;
- the body is a chain of shaded fuzzy spheres (head, big eyes, a furry thorax with pale tegula lines, a long tapered
  striped abdomen), drawn back to front, each with its own thin ink edge;
- each wing is a flat plane: its painted texture (hawk-moth forewing: olive-brown, a pale diagonal band, fine oblique
  lines, veins, a discal spot, a dark apex streak, a checkered fringe; hindwing: warm rose-orange with a dark border)
  is mapped onto the projected plane by one affine transform (an orthographic projection of a plane IS affine), so the
  pattern stays right at any roll, pitch or flap angle; the underside texture shows when the wing turns its belly side;
- feathery (bipectinate) antennae: a shaft with paired barbs, tapering; six thin jointed legs tucked in flight;
- wing motion blur: several flap phases averaged (`blur` = the fraction of a wing beat the shutter sees).

`render(s, view, ...)` -> (RGBA layer, (ox, oy) of the thorax centre in the layer, info). `put(img, x, y, s, ...)`
pastes it with the thorax at (x, y) and returns info in frame px: 'back' (top of the thorax), 'up' (unit 2D screen
vector of the moth's dorsal normal), 'up_z' (its depth part: < 0 = the back faces the camera), 'head', 'tail'.
Views: 'top' (camera above, the moth's back faces us), 'rear' (behind the moth, looking where it flies), 'side'
(profile, flying screen-right), 'front'. `elev` tilts the camera (deg) for 3/4 views; `heading` rotates the result
in the screen plane (deg); `roll`/`pitch` are the moth's own (deg, roll + = right wing down).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

INK = (20, 16, 22)
SS = 2
TEX = 700                      # texture px per unit

# ---------------------------------------------------------------- palette (hawk moth)
OLIVE = (118, 106, 72)
OLIVE_D = (78, 70, 48)
OLIVE_L = (150, 138, 96)
BAND = (218, 202, 156)
LINE_D = (56, 48, 34)
HIND = (232, 132, 78)
HIND_R = (214, 96, 96)
HIND_D = (58, 40, 34)
FRINGE = (226, 214, 180)
UNDER = (182, 156, 112)
UNDER_D = (134, 112, 78)
FUR = (128, 116, 82)
FUR_L = (176, 162, 118)
ABD = (112, 100, 70)
ABD_PINK = (214, 120, 120)
EYE = (30, 26, 28)

# ---------------------------------------------------------------- wing outlines (u = out along the span, v = forward)
FORE = [(0.00, 0.060), (0.18, 0.080), (0.40, 0.068), (0.62, 0.030), (0.82, -0.032), (0.95, -0.088), (1.03, -0.128),
        (0.985, -0.150), (0.92, -0.175), (0.80, -0.225), (0.66, -0.268), (0.52, -0.290), (0.40, -0.282),
        (0.26, -0.240), (0.12, -0.170), (0.00, -0.080)]
HINDW = [(0.00, -0.030), (0.12, -0.065), (0.26, -0.110), (0.37, -0.165), (0.44, -0.220), (0.45, -0.268),
         (0.40, -0.310), (0.30, -0.332), (0.19, -0.318), (0.09, -0.268), (0.03, -0.185), (0.00, -0.105)]
U0, U1, V0, V1 = -0.04, 1.06, -0.48, 0.14       # texture box


def _cr(pts, k=6):
    n = len(pts); out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(k):
            t = j / k; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in range(2)))
    return out


def _tp(u, v):
    return ((u - U0) * TEX, (V1 - v) * TEX)


def _uv():
    w, h = int((U1 - U0) * TEX), int((V1 - V0) * TEX)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return xx / TEX + U0, V1 - yy / TEX, (h, w)


def _mask(poly):
    w, h = int((U1 - U0) * TEX), int((V1 - V0) * TEX)
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon([_tp(*p) for p in _cr(poly, 8)], fill=255)
    return m


def _lines(arr, segs, col, wpx, alpha, blur=0.0):
    """Draw polylines (in u,v) onto a float RGB array through a temp mask."""
    h, w = arr.shape[:2]
    m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m)
    for pts in segs:
        d.line([_tp(*p) for p in pts], fill=255, width=max(1, int(wpx)), joint='curve')
    if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(m, np.float32)[..., None] / 255 * alpha
    arr[:] = arr * (1 - a) + np.array(col, np.float32) * a


def _edge(m, r):
    e = m.filter(ImageFilter.BoxBlur(r))
    return np.clip((255 - np.asarray(e, np.float32)) / 255 * 2.2, 0, 1) * (np.asarray(m, np.float32) / 255)


def _noise(shape, scale, seed):
    rng = np.random.default_rng(seed)
    h, w = shape
    sm = rng.normal(0, 1, (max(2, int(h / scale)) + 2, max(2, int(w / scale)) + 2)).astype(np.float32)
    im = Image.fromarray(((sm * 40 + 128).clip(0, 255)).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(im, np.float32) - 128) / 40


_TEXC = {}


def textures():
    """(fore_top, fore_under, hind_top, hind_under) RGBA texture images (cached)."""
    if 'k' in _TEXC: return _TEXC['k']
    u, v, shape = _uv()
    rng = np.random.default_rng(5)
    # ---- forewing, upper side
    mf = _mask(FORE)
    base = np.zeros(shape + (3,), np.float32)
    k = np.clip(u / 1.0, 0, 1)[..., None]
    base[:] = np.array(OLIVE_D, np.float32) * (1 - k) + np.array(OLIVE, np.float32) * k
    # paler costal (front) zone, darker inner-margin zone
    cz = np.clip((v + .05) / .14, 0, 1)[..., None] * np.clip(1 - u * .6, 0, 1)[..., None]
    base = base * (1 - .35 * cz) + np.array(OLIVE_L, np.float32) * (.35 * cz)
    tz = np.clip((-v - .12 - u * .02) / .16, 0, 1)[..., None]
    base = base * (1 - .3 * tz) + np.array(OLIVE_D, np.float32) * (.3 * tz)
    # the pale diagonal band: from the inner margin near the base to the apex
    def segdist(p, q):
        vx, vy = q[0] - p[0], q[1] - p[1]; L2 = vx * vx + vy * vy
        t = np.clip(((u - p[0]) * vx + (v - p[1]) * vy) / L2, 0, 1)
        return np.hypot(u - p[0] - t * vx, v - p[1] - t * vy), t
    APEX = (1.0, -0.128)
    P0, P1 = (0.10, -0.15), APEX
    dd, tt = segdist(P0, P1)
    bw = .014 + .026 * np.sin(np.pi * np.clip(tt * .85 + .1, 0, 1))
    band = np.clip(1 - (dd - bw) / .010, 0, 1)[..., None]
    nx, ny = -(P1[1] - P0[1]), (P1[0] - P0[0]); nl = math.hypot(nx, ny); nx, ny = nx / nl, ny / nl
    side = (u - P0[0]) * nx + (v - P0[1]) * ny            # > 0: toward the costa / the base
    # the zone in front of the band is darker olive-brown, the zone behind it paler and greyer
    front = np.clip(side / .05, 0, 1)[..., None]
    base = base * (1 - .25 * front) + np.array((96, 84, 56), np.float32) * (.25 * front)
    base = base * (1 - .3 * (1 - front)) + np.array((150, 140, 104), np.float32) * (.3 * (1 - front))
    base = base * (1 - .9 * band) + np.array(BAND, np.float32) * (.9 * band)
    under = np.clip(1 - (dd - bw) / .035, 0, 1) * (side > 0)
    base = base * (1 - .4 * under[..., None]) + np.array(OLIVE_D, np.float32) * (.4 * under[..., None])
    # a dark basal patch
    bp = np.clip(1 - np.hypot(u / .16, (v + .05) / .12), 0, 1)[..., None]
    base = base * (1 - .5 * bp) + np.array(OLIVE_D, np.float32) * (.5 * bp)
    # speckled scales
    nz = _noise(shape, 3, 2) * .5 + _noise(shape, 14, 3) * .5
    mot = _noise(shape, 40, 9)
    base *= (1 + .07 * nz + .09 * mot)[..., None]
    # a dark wedge in front of the band toward the apex, pale spots behind it
    wedge = np.clip(side / .06, 0, 1) * np.clip((u - .35) / .3, 0, 1) * np.clip(1 - dd / .14, 0, 1)
    base = base * (1 - .45 * wedge[..., None]) + np.array((70, 58, 40), np.float32) * (.45 * wedge[..., None])
    arr = base
    # veins radiating from the root (faint, a little darker)
    veins = []
    for a_ in np.linspace(-.42, .06, 8):
        pts = [(0.02, -0.04 + a_ * .1)]
        for i in range(1, 7):
            f = i / 6; pts.append((0.02 + f * .96, -0.04 + a_ * (0.1 + f * .55) - .07 * f * f))
        veins.append(pts)
    _lines(arr, veins, OLIVE_D, TEX * .004, .3, 1)
    # fine oblique lines parallel to the band, crossing the wing from the costa to the inner margin
    dx_, dy_ = P1[0] - P0[0], P1[1] - P0[1]; dl_ = math.hypot(dx_, dy_); dx_, dy_ = dx_ / dl_, dy_ / dl_
    for k_, off in enumerate((.055, .08, .105, -.05, -.072, -.094, -.116, -.14)):
        a_ = (P0[0] + nx * off - dx_ * .5, P0[1] + ny * off - dy_ * .5); b_ = (P1[0] + nx * off * .5 + dx_ * .1, P1[1] + ny * off * .5 + dy_ * .1)
        wob = [(a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f + .005 * math.sin(f * 31 + k_ * 1.7)) for f in np.linspace(0, 1, 40)]
        _lines(arr, [wob], LINE_D, TEX * (.006 if k_ in (0, 3) else .0042), .75, .5)
    # a small dark discal spot and a dark streak to the apex
    _lines(arr, [[(0.36, 0.02), (0.37, 0.018)]], LINE_D, TEX * .03, .8, 1)
    _lines(arr, [[(0.78, -0.05), (0.92, -0.095), (0.99, -0.13)]], LINE_D, TEX * .012, .6, 1.5)
    # outer margin: a dark border then a checkered pale fringe
    edge = _edge(mf, int(TEX * .028))
    outer = np.clip((u - .55) / .2, 0, 1) * np.clip((-v - .03) / .1, 0, 1)
    arr = arr * (1 - .45 * (edge * outer)[..., None]) + np.array(OLIVE_D, np.float32) * (.45 * (edge * outer)[..., None])
    rim = _edge(mf, int(TEX * .008))
    chk = (np.sin((u * 1.0 - v * 1.4) * 150) > 0).astype(np.float32)
    fr = rim * outer
    fc = np.array(FRINGE, np.float32) * chk[..., None] + np.array(OLIVE_D, np.float32) * (1 - chk[..., None])
    arr = arr * (1 - fr[..., None]) + fc * fr[..., None]
    # thin ink line round the wing
    ink = _edge(mf, max(2, int(TEX * .006)))
    arr = arr * (1 - .9 * ink[..., None]) + np.array(INK, np.float32) * (.9 * ink[..., None])
    fore_top = Image.fromarray(np.dstack([arr.clip(0, 255), np.asarray(mf, np.float32)]).astype(np.uint8), 'RGBA')
    # ---- forewing underside: dull ochre, a faint band
    ua = np.zeros(shape + (3,), np.float32); ua[:] = UNDER
    ua = ua * (1 - .35 * band) + np.array((210, 190, 150), np.float32) * (.35 * band)
    ua = ua * (1 - .25 * k) + np.array(UNDER_D, np.float32) * (.25 * k)
    ua *= (1 + .05 * nz)[..., None]
    ua = ua * (1 - .9 * ink[..., None]) + np.array(INK, np.float32) * (.9 * ink[..., None])
    fore_under = Image.fromarray(np.dstack([ua.clip(0, 255), np.asarray(mf, np.float32)]).astype(np.uint8), 'RGBA')
    # ---- hindwing, upper: warm rose-orange, a dark outer border, hairy dark root, pale fringe
    mh = _mask(HINDW)
    hb = np.zeros(shape + (3,), np.float32)
    r = np.hypot(u / .55, (v + .2) / .25)
    kk = np.clip(r, 0, 1)[..., None]
    hb[:] = np.array(HIND_R, np.float32) * (1 - kk) + np.array(HIND, np.float32) * kk
    root = np.clip(1 - u / .12, 0, 1)[..., None]
    hb = hb * (1 - .7 * root) + np.array(HIND_D, np.float32) * (.7 * root)
    dist_edge = _edge(mh, int(TEX * .07))
    border = np.clip(dist_edge * 1.4, 0, 1) * np.clip(u / .2, 0, 1)
    hb = hb * (1 - .85 * border[..., None]) + np.array(HIND_D, np.float32) * (.85 * border[..., None])
    hb *= (1 + .06 * nz)[..., None]
    rim2 = _edge(mh, int(TEX * .008))
    hb = hb * (1 - rim2[..., None]) + np.array(FRINGE, np.float32) * rim2[..., None]
    ink2 = _edge(mh, max(2, int(TEX * .006)))
    hb = hb * (1 - .9 * ink2[..., None]) + np.array(INK, np.float32) * (.9 * ink2[..., None])
    hind_top = Image.fromarray(np.dstack([hb.clip(0, 255), np.asarray(mh, np.float32)]).astype(np.uint8), 'RGBA')
    hu = np.zeros(shape + (3,), np.float32); hu[:] = (196, 150, 110)
    hu *= (1 + .05 * nz)[..., None]
    hu = hu * (1 - .9 * ink2[..., None]) + np.array(INK, np.float32) * (.9 * ink2[..., None])
    hind_under = Image.fromarray(np.dstack([hu.clip(0, 255), np.asarray(mh, np.float32)]).astype(np.uint8), 'RGBA')
    _TEXC['k'] = (fore_top, fore_under, hind_top, hind_under)
    return _TEXC['k']


# ---------------------------------------------------------------- 3D helpers
def rx(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


# camera bases: rows = camera X (screen right), Y (screen down), Z (depth, away) in moth-local coords
BASES = {
    'top': np.array([[1, 0, 0], [0, 1, 0], [0, 0, -1]], float),      # head screen-right, right wing screen-down
    'side': np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float),     # head right, back up, right wing away
    'rear': np.array([[0, 1, 0], [0, 0, -1], [1, 0, 0]], float),     # looking along +x: right wing screen-right
    'front': np.array([[0, -1, 0], [0, 0, -1], [-1, 0, 0]], float),
}


def view_matrix(view='top', elev=0.0, yaw=0.0, roll=0.0, pitch=0.0):
    """moth-local -> camera. roll about x (+ = right wing down), pitch about y (+ = nose up), yaw about z (+ = nose to
    the moth's left). elev: the camera tilts so it sees more of the back (deg)."""
    R_local = rz(math.radians(yaw)) @ ry(-math.radians(pitch)) @ rx(math.radians(roll))
    # roll + = right wing down: rotation about x by +roll moves +y toward -z? rx(+a): y -> (0, c, s): z = +s (up).
    # we want right wing down for +roll, so use -roll
    R_local = rz(math.radians(yaw)) @ ry(-math.radians(pitch)) @ rx(-math.radians(roll))
    B = BASES[view]
    E = rx(math.radians(elev))                                    # camera tilt about the screen x axis
    return E @ B @ R_local


# ---------------------------------------------------------------- body geometry (local)
def body_spheres():
    S = []
    # abdomen (tail first), tapered, slightly drooping; tag 'abd'
    n = 14
    for i in range(n):
        f = i / (n - 1)
        x = -0.64 + f * 0.56
        r = 0.020 + 0.060 * math.sin(min(1, f * 1.12) * math.pi / 2) ** .75
        z = -0.025 * (1 - f) ** 2
        S.append(('abd', (x, 0.0, z), r, i))
    S += [('thx', (-0.05, 0.0, 0.012), 0.092, 0), ('thx', (0.02, 0.0, 0.024), 0.118, 1), ('thx', (0.10, 0.0, 0.02), 0.104, 2),
          ('thx', (0.158, 0.0, 0.006), 0.074, 3), ('head', (0.205, 0.0, -0.004), 0.062, 0),
          ('eye', (0.222, 0.046, -0.004), 0.038, 0), ('eye', (0.222, -0.046, -0.004), 0.038, 1),
          ('palp', (0.255, 0.0, -0.03), 0.032, 0)]
    return S


def antenna(side):
    """Shaft points (local) of one antenna: from the head top-front, out, forward and up, tip curving back."""
    pts = []
    for i in range(14):
        f = i / 13
        x = 0.225 + 0.30 * f - 0.05 * f ** 3
        y = side * (0.028 + 0.30 * f ** 1.05)
        z = 0.035 + 0.12 * math.sin(f * 2.2) - 0.03 * f
        pts.append((x, y, z))
    return pts


def legs(side, fold=1.0):
    out = []
    for i, x in enumerate((0.13, 0.05, -0.03)):
        b = (x, side * 0.03, -0.06)
        k = (x + 0.03 - 0.02 * i, side * (0.11 + 0.01 * i), -0.10)
        t = (x - 0.06 - 0.03 * i, side * (0.13 + 0.015 * i), -0.13 - 0.01 * i)
        e = (x - 0.13 - 0.04 * i, side * (0.12 + 0.02 * i), -0.15)
        if fold < 1:                                              # legs spread out (landing / resting)
            k = (x + 0.02, side * 0.14, -0.08); t = (x + 0.06 - 0.06 * i, side * 0.24, -0.16); e = (x + 0.08 - 0.12 * i, side * 0.30, -0.20)
            k = tuple(a * (1 - fold) + b_ * fold for a, b_ in zip(k, (x + 0.03 - 0.02 * i, side * (0.11 + 0.01 * i), -0.10)))
        out.append([b, k, t, e])
    return out


# ---------------------------------------------------------------- sprites
_SPH = {}


def sphere_sprite(R, col, L, fur=0.0, seed=0, stripe=None):
    """A shaded sphere disc of radius R px (lambert + ambient, light L = camera-space unit vector), with optional fur
    streak texture. Cached."""
    R = max(2, int(R))
    key = (R, col, tuple(round(x, 1) for x in L), round(fur, 1), seed % 5, stripe)
    if key in _SPH: return _SPH[key]
    n = 2 * R + 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    X = (xx - R - .5) / R; Y = (yy - R - .5) / R
    rr = X * X + Y * Y
    inside = rr <= 1
    Z = -np.sqrt(np.clip(1 - rr, 0, 1))                          # toward the camera
    lam = np.clip(-(X * L[0] + Y * L[1] + Z * L[2]), 0, 1)
    sh = .55 + .6 * lam
    c = np.array(col, np.float32)[None, None, :] * sh[..., None]
    if stripe is not None:                                       # a pale or pink ring at the sphere's rear rim
        ring = np.clip((np.sqrt(rr) - .62) / .3, 0, 1) * np.clip((np.abs(X) - .2) / .4, 0, 1)
        c = c * (1 - .55 * ring[..., None]) + np.array(stripe, np.float32) * (.55 * ring[..., None])
    if fur > 0:
        rng = np.random.default_rng(seed)
        f = Image.new('L', (n, n), 128); d = ImageDraw.Draw(f)
        for _ in range(int(R * R * .25)):
            x, y = rng.uniform(0, n), rng.uniform(0, n)
            a = math.atan2(y - R, x - R) + rng.uniform(-.5, .5)
            ln = R * rng.uniform(.12, .3)
            d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=int(rng.choice([60, 200])), width=max(1, R // 18))
        f = np.asarray(f.filter(ImageFilter.GaussianBlur(max(.6, R / 40))), np.float32) / 128 - 1
        c *= (1 + fur * .32 * f)[..., None]
    # soft dark rim (form shadow) + alpha with a soft fuzzy edge
    edge = np.clip((np.sqrt(rr) - .75) / .25, 0, 1)
    c *= (1 - .18 * edge)[..., None]
    a = np.clip((1 - np.sqrt(rr)) * R * .9, 0, 1) * 255
    spr = Image.fromarray(np.dstack([c.clip(0, 255), a]).astype(np.uint8), 'RGBA')
    if len(_SPH) > 3000: _SPH.clear()
    _SPH[key] = spr
    return spr


# ---------------------------------------------------------------- render
_LAY = {}


def _q(v, step): return round(v / step) * step


def render(s, view='top', elev=0.0, yaw=0.0, roll=0.0, pitch=0.0, flap=0.0, blur=0.0, sweep=None, spread=1.0,
           light=(-.4, -.7, -.6), lamp=None, lamp_col=(190, 150, 255), lamp_k=0.0, ink_w=None, fur=1.0, rest=False,
           legs_fold=1.0, cache=True):
    """Render the moth. s = forewing length px. flap: wing-beat phase 0..1 (amp set by `spread`); rest=True: wings
    swept back flat (a resting delta). lamp: camera-space unit vector toward a light (adds lamp_col by lamp_k)."""
    if s < 40: SSl = 3
    else: SSl = SS
    key = (int(s), view, _q(elev, 2), _q(yaw, 2), _q(roll, 3), _q(pitch, 3), _q(flap % 1, 1 / 24), _q(blur, .05),
           sweep, spread, light, lamp and tuple(_q(x, .1) for x in lamp), lamp_col, _q(lamp_k, .05), ink_w, fur, rest, legs_fold)
    if cache and key in _LAY: return _LAY[key]
    M = view_matrix(view, elev, yaw, roll, pitch)
    S = s * SSl
    L = np.array(light, float); L /= np.linalg.norm(L)
    Lc = L                                                        # light is given in camera space
    lampv = None if lamp is None else np.array(lamp, float) / (np.linalg.norm(lamp) or 1)
    # bounding: everything within ~1.25 units of the thorax
    half = int(S * 1.25) + 8
    Wd = Hd = 2 * half
    o = np.array([half, half], float)
    def P(p):
        c = M @ np.array(p, float); return (o[0] + c[0] * S, o[1] + c[1] * S, c[2])
    iw = max(1.0, (ink_w or max(1.4, s * .012))) * SSl
    tex = textures()
    parts = []                                                  # (depth, kind, payload)
    # ---- wings
    if rest:
        sw = math.radians(sweep if sweep is not None else 58); phases = [0.0]
    else:
        sw = math.radians(sweep if sweep is not None else 12)
        nb = 1 if blur <= .02 else max(3, int(blur * 14))
        phases = [flap + (i / max(1, nb - 1) - .5) * blur for i in range(nb)] if nb > 1 else [flap]
    def flap_angle(ph):
        if rest: return math.radians(-4)
        return math.radians(14 + 52 * spread * math.sin(2 * math.pi * ph))
    for side in (1, -1):
        for wing in ('fore', 'hind'):
            subs = []
            for ph in phases:
                phi = flap_angle(ph)
                if wing == 'hind': phi *= .92
                # wing frame in local coords
                eu = np.array([-math.sin(sw), side * math.cos(sw), 0.0])
                ev = np.array([math.cos(sw), side * math.sin(sw), 0.0])
                if wing == 'hind':
                    swh = sw * .7
                    eu = np.array([-math.sin(swh), side * math.cos(swh), 0.0]); ev = np.array([math.cos(swh), side * math.sin(swh), 0.0])
                Rf = rx(side * phi)
                eu, ev = Rf @ eu, Rf @ ev
                nrm = Rf @ np.array([0, 0, 1.0])
                root = np.array([0.06 if wing == 'fore' else -0.01, side * 0.055, 0.03 if wing == 'fore' else 0.022])
                cu, cv, cr = M @ eu, M @ ev, M @ root
                ncam = M @ nrm
                subs.append((cu, cv, cr, ncam))
            cu, cv, cr, ncam = subs[len(subs) // 2]
            cen = cr + cu * .16 + cv * -.08                          # a point near the root decides wing vs body
            parts.append((cen[2] + (0.004 if wing == 'hind' else 0), 'wing', (side, wing, subs)))
    # ---- body: one group of spheres (one ink outline round the union)
    sph = [(tag, M @ np.array(p, float), r, i) for tag, p, r, i in body_spheres()]
    thx_d = (M @ np.array((0.02, 0, 0.022)))[2] - 0.104
    parts.append((thx_d, 'body', sph))
    # ---- antennae + legs
    for side in (1, -1):
        pts = [M @ np.array(p) for p in antenna(side)]
        parts.append((min(q[2] for q in pts[:4]) - .02, 'ant', (side, pts)))
        for lg in legs(side, legs_fold):
            pts = [M @ np.array(p) for p in lg]
            parts.append((sum(q[2] for q in pts) / len(pts), 'leg', pts))
    parts.sort(key=lambda t: -t[0])

    lay = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
    ink_img = Image.new('RGBA', (Wd, Hd), INK + (255,))

    def shade_k(ncam):
        vis_top = ncam[2] < 0
        n = ncam if vis_top else -ncam
        lam = max(0.0, -float(n @ Lc))
        k = .72 + .42 * lam
        lk = 0.0
        if lampv is not None and lamp_k > 0: lk = lamp_k * max(0.0, -float(n @ lampv))
        return vis_top, k, lk

    for depth, kind, pay in parts:
        if kind == 'wing':
            side, wing, subs = pay
            acc = None; n_ = len(subs)
            for cu, cv, cr, ncam in subs:
                vis_top, k, lk = shade_k(ncam)
                t = tex[(0 if wing == 'fore' else 2) + (0 if vis_top else 1)]
                # tex px -> screen px
                A = np.array([[cu[0], cv[0]], [cu[1], cv[1]]]) * S
                b = o + cr[:2] * S
                Mx = np.array([[A[0, 0] / TEX, -A[0, 1] / TEX, b[0] + A[0, 0] * U0 + A[0, 1] * V1],
                               [A[1, 0] / TEX, -A[1, 1] / TEX, b[1] + A[1, 0] * U0 + A[1, 1] * V1]])
                det = Mx[0, 0] * Mx[1, 1] - Mx[0, 1] * Mx[1, 0]
                if abs(det) < 1e-6: continue
                inv = np.linalg.inv(np.vstack([Mx, [0, 0, 1]]))[:2]
                wl = t.transform((Wd, Hd), Image.AFFINE, tuple(inv.flatten()), resample=Image.BICUBIC)
                a = np.asarray(wl, np.float32)
                rgbv = a[..., :3] * k
                if lk > 0: rgbv = rgbv * (1 - .45 * lk) + np.array(lamp_col, np.float32) * (.45 * lk) * (k + .2)
                pre = np.dstack([rgbv * a[..., 3:] / 255, a[..., 3:]])
                acc = pre if acc is None else acc + pre
            if acc is None: continue
            acc /= n_
            if n_ > 1:                                             # blurred wings: denser near the slow ends of the beat
                acc[..., 3] = np.clip(acc[..., 3] * 1.25, 0, 255)
            al = acc[..., 3:]
            col = np.where(al > 0, acc[..., :3] / np.maximum(al, 1e-3) * 255, 0)
            wimg = Image.fromarray(np.dstack([col.clip(0, 255), al]).astype(np.uint8), 'RGBA')
            m = wimg.split()[3]
            if n_ == 1:
                ink = m.filter(ImageFilter.BoxBlur(iw)).point(lambda v: 255 if v > 10 else 0)
                lay.paste(ink_img, (0, 0), ink)
            lay.alpha_composite(wimg)
        elif kind == 'body':
            sph = sorted(pay, key=lambda t: -t[1][2])
            bl = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
            um = Image.new('L', (Wd, Hd), 0); du = ImageDraw.Draw(um)
            fz = Image.new('L', (Wd, Hd), 0); dfz = ImageDraw.Draw(fz)
            rng = np.random.default_rng(3)
            for tag, c, r, i in sph:
                R = r * S; x, y = o[0] + c[0] * S, o[1] + c[1] * S
                if tag != 'eye': du.ellipse([x - R, y - R, x + R, y + R], fill=255)
                if tag in ('thx', 'head', 'palp'):
                    for _ in range(int(20 + R * .9)):                 # fine fur tufts breaking the outline
                        a_ = rng.uniform(0, 2 * math.pi); r0 = R * .85; r1 = R * rng.uniform(1.03, 1.12 if tag == 'thx' else 1.08)
                        dfz.line([(x + math.cos(a_) * r0, y + math.sin(a_) * r0), (x + math.cos(a_ + .1) * r1, y + math.sin(a_ + .1) * r1)],
                                 fill=255, width=max(1, int(R * .035)))
            for tag, c, r, i in sph:
                R = r * S
                col = {'abd': ABD, 'thx': FUR, 'head': FUR, 'eye': EYE, 'palp': FUR_L}[tag]
                stripe = None
                if tag == 'abd':
                    col = (ABD[0] + 12 * (i % 2), ABD[1] + 8 * (i % 2), ABD[2] + 4 * (i % 2))
                    stripe = ABD_PINK if i % 2 == 0 and 2 <= i <= 12 else (190, 178, 140)
                if tag == 'thx' and i == 1: col = (140, 128, 90)
                spr = sphere_sprite(R, col, tuple(Lc), fur * (0 if tag == 'eye' else 1.0), seed=i, stripe=stripe)
                x, y = o[0] + c[0] * S, o[1] + c[1] * S
                bl.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2)))
                if tag == 'eye':
                    d = ImageDraw.Draw(bl)
                    d.ellipse([x - R - iw * .5, y - R - iw * .5, x + R + iw * .5, y + R + iw * .5], outline=INK, width=max(1, int(iw * .6)))
                    hx, hy = x - R * .32, y - R * .36
                    d.ellipse([hx - R * .2, hy - R * .2, hx + R * .2, hy + R * .2], fill=(210, 206, 228))
                if tag == 'thx' and i == 1:
                    d = ImageDraw.Draw(bl)
                    for sd in (1, -1):                               # pale tegula lines (seen when the back faces us)
                        pts3 = [M @ np.array((x_, sd * (0.03 + 0.05 * math.sin((x_ + .08) / .2 * math.pi) ** .7 if x_ > -.08 else 0.03), 0.11)) for x_ in (-0.07, -0.03, 0.01, 0.05, 0.09, 0.12)]
                        if np.mean([p_[2] for p_ in pts3]) < c[2]:
                            d.line([(o[0] + p_[0] * S, o[1] + p_[1] * S) for p_ in pts3], fill=(184, 170, 126), width=max(1, int(S * .008)), joint='curve')
                    pts3 = [M @ np.array((x_, 0.0, 0.135)) for x_ in (-0.07, 0.02, 0.11)]
                    if np.mean([p_[2] for p_ in pts3]) < c[2]:
                        d.line([(o[0] + p_[0] * S, o[1] + p_[1] * S) for p_ in pts3], fill=(96, 86, 58), width=max(1, int(S * .01)), joint='curve')
            # fuzzy silhouette: tufts outside the union, in fur colour, then the ink outline round body + tufts
            fz = ImageChops.subtract(fz, um)
            ink = um.filter(ImageFilter.BoxBlur(iw * .8)).point(lambda v: 255 if v > 14 else 0)
            lay.paste(ink_img, (0, 0), ink)
            lay.paste(Image.new('RGBA', (Wd, Hd), (110, 100, 70, 255)), (0, 0), fz)
            lay.alpha_composite(bl)
            if lampv is not None and lamp_k > 0:                   # lamp rim along the body's lit edge
                lx, ly = lampv[0], lampv[1]; ln = math.hypot(lx, ly) or 1
                sh = max(2, int(S * .03))
                rm = ImageChops.subtract(um, ImageChops.offset(um, int(-lx / ln * sh), int(-ly / ln * sh))).filter(ImageFilter.GaussianBlur(sh * .4))
                lay.paste(Image.new('RGBA', (Wd, Hd), lamp_col + (255,)), (0, 0), rm.point(lambda v: int(v * min(1, lamp_k) * .7)))
        elif kind == 'ant':
            side, pts = pay
            d = ImageDraw.Draw(lay)
            sp = [(o[0] + p[0] * S, o[1] + p[1] * S) for p in pts]
            wsh = max(1, int(S * .010))
            # barbs: in the plane of the shaft and the moth's y axis, angled forward, tapering
            if s > 60:
                for i in range(1, len(pts) - 1):
                    f = i / (len(pts) - 1)
                    bl = .06 * (1 - f) ** .7 + .008
                    t3 = np.array(pts[i + 1]) - np.array(pts[i - 1]); t3 /= np.linalg.norm(t3)
                    side3 = M @ np.array([0.0, 0, 1.0]); side3 = np.cross(t3, side3)
                    if np.linalg.norm(side3) < 1e-3: continue
                    side3 /= np.linalg.norm(side3)
                    for sgn in (1, -1):
                        for j in range(3):
                            q = np.array(pts[i]) + (np.array(pts[i + 1]) - np.array(pts[i])) * j / 3
                            e = q + (side3 * sgn * .85 + t3 * .5) * bl
                            d.line([(o[0] + q[0] * S, o[1] + q[1] * S), (o[0] + e[0] * S, o[1] + e[1] * S)],
                                   fill=(150, 136, 100), width=max(1, int(S * .004)))
            d.line(sp, fill=INK, width=wsh + int(iw * .9), joint='curve')
            d.line(sp, fill=(186, 170, 128), width=max(1, wsh), joint='curve')
        elif kind == 'leg':
            pts = pay
            d = ImageDraw.Draw(lay)
            sp = [(o[0] + p[0] * S, o[1] + p[1] * S) for p in pts]
            d.line(sp, fill=INK, width=max(2, int(S * .018)), joint='curve')
            d.line(sp, fill=(150, 132, 96), width=max(1, int(S * .008)), joint='curve')
    # info
    back_l = M @ np.array((0.02, 0, 0.13)); thx = M @ np.array((0.02, 0, 0.022))
    up = M @ np.array((0, 0, 1.0))
    head = M @ np.array((0.24, 0, 0)); tail = M @ np.array((-0.66, 0, 0))
    out = lay.resize((Wd // SSl, Hd // SSl), Image.LANCZOS)
    info = {'o': (o[0] / SSl, o[1] / SSl), 'back': (back_l[0] * s, back_l[1] * s), 'up': (float(up[0]), float(up[1])),
            'up_z': float(up[2]), 'head': (head[0] * s, head[1] * s), 'tail': (tail[0] * s, tail[1] * s), 'thx': (thx[0] * s, thx[1] * s)}
    res = (out, info)
    if cache:
        if len(_LAY) > 600: _LAY.clear()
        _LAY[key] = res
    return res


def _rot2(p, a):
    c, s_ = math.cos(a), math.sin(a); return (p[0] * c - p[1] * s_, p[0] * s_ + p[1] * c)


def put(img, x, y, s, heading=0.0, alpha=1.0, glow=None, glow_a=.0, shadow=None, **kw):
    """Paste the moth with its thorax at (x, y). heading (deg) rotates it in the screen plane (+ = clockwise on
    screen). Returns info in frame px ('back', 'up', 'head', 'tail', 'thx', 'up_z')."""
    lay, inf = render(s, **kw)
    a = math.radians(heading)
    if abs(heading) > .05:
        lay = lay.rotate(-heading, resample=Image.BICUBIC, center=inf['o'])
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    ox, oy = inf['o']
    px, py = int(round(x - ox)), int(round(y - oy))
    if glow is not None and glow_a > 0:
        m = Image.new('L', img.size, 0); m.paste(lay.split()[3], (px, py))
        g = m.filter(ImageFilter.GaussianBlur(max(4, s * .12)))
        img.paste(Image.new('RGBA', img.size, glow + (255,)), (0, 0), g.point(lambda v: int(v * glow_a)))
    img.alpha_composite(lay, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    out = {}
    for k in ('back', 'head', 'tail', 'thx'):
        q = _rot2(inf[k], a); out[k] = (x + q[0], y + q[1])
    out['up'] = _rot2(inf['up'], a); out['up_z'] = inf['up_z']
    out['size'] = s
    return out


# ---------------------------------------------------------------- light trails (long exposure)
def trail(img, pts, col=(200, 170, 255), w=6, alpha=1.0, core=(255, 248, 255), wave=0.0, phase=0.0, blur=None):
    """A long-exposure light trail along pts (oldest first): a soft wide glow and a bright thin core, both fading
    toward the old end; `wave` adds the wing-beat ripple of a real long exposure."""
    if len(pts) < 2: return
    n = len(pts)
    if wave > 0:
        q = []
        for i, (x, y) in enumerate(pts):
            a = pts[max(0, i - 1)]; b = pts[min(n - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
            o = wave * math.sin(i * 1.3 + phase)
            q.append((x - dy / L * o, y + dx / L * o))
        pts = q
    m = Image.new('L', img.size, 0); d = ImageDraw.Draw(m)
    mc = Image.new('L', img.size, 0); dc = ImageDraw.Draw(mc)
    for i in range(n - 1):
        f = (i + 1) / n
        v = int(255 * f ** 1.4)
        d.line([pts[i], pts[i + 1]], fill=v, width=int(w * 3.2))
        dc.line([pts[i], pts[i + 1]], fill=v, width=max(1, int(w * (.4 + .6 * f))))
    g = m.filter(ImageFilter.GaussianBlur(blur or w * 2.2))
    _add(img, g, col, alpha * .9)
    _add(img, mc.filter(ImageFilter.GaussianBlur(max(.6, w * .25))), core, alpha)


def _add(img, m, col, alpha):
    a = np.asarray(m, np.float32)[..., None] / 255 * alpha
    if a.max() <= 0: return
    bb = m.getbbox()
    if not bb: return
    x0, y0, x1, y1 = bb
    base = np.asarray(img.crop(bb), np.float32)
    c = np.array(col, np.float32)
    aa = a[y0:y1, x0:x1]
    base[..., :3] = 255 - (255 - base[..., :3]) * (1 - aa * c / 255)
    img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)), (x0, y0))


def add_light(img, m, col, alpha):
    _add(img, m, col, alpha)


# ---------------------------------------------------------------- the BACK arrow
_ARW = {}


def back_arrow(img, base, up, length, col=(255, 210, 63), w=None, label='BACK', alpha=1.0, label_side=1, font_fn=None,
               up_z=0.0, label_size=None):
    """A thick arrow standing out of the moth's back along its dorsal normal `up` (2D screen vector), with a label.
    Foreshortened by up_z (a back that faces the camera gets a shorter arrow and a ring at its base)."""
    from kit import font
    k2 = math.hypot(*up)
    if k2 < .05: return None
    ux, uy = up[0] / k2, up[1] / k2
    L = length * max(.35, k2)
    w = w or max(26, length * .2)
    x0, y0 = base; x1, y1 = x0 + ux * L, y0 + uy * L
    nx, ny = -uy, ux
    hl = min(L * .45, w * 1.9)
    bx, by = x1 - ux * hl, y1 - uy * hl
    pts = [(x0 + nx * w * .42, y0 + ny * w * .42), (bx + nx * w * .42, by + ny * w * .42), (bx + nx * w, by + ny * w), (x1, y1),
           (bx - nx * w, by - ny * w), (bx - nx * w * .42, by - ny * w * .42), (x0 - nx * w * .42, y0 - ny * w * .42)]
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sw = max(5, int(w * .2))
    d.polygon(pts, fill=INK + (255,)); d.line(pts + [pts[0]], fill=INK + (255,), width=sw * 2, joint='curve')
    d.polygon(pts, fill=col + (255,))
    d.line([(x0 + nx * w * .14, y0 + ny * w * .14), (bx + nx * w * .14, by + ny * w * .14)], fill=(255, 246, 210, 255), width=max(2, int(w * .14)))
    # base dot on the back
    r = w * .42
    d.ellipse([x0 - r - sw, y0 - r - sw, x0 + r + sw, y0 + r + sw], fill=INK + (255,))
    d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=col + (255,))
    if label:
        fs = label_size or max(34, int(w * 1.15))
        f = font(fs)
        mx, my = x0 + ux * L * .5, y0 + uy * L * .5
        lx, ly = mx + nx * label_side * (w * 1.1 + fs * 1.3), my + ny * label_side * (w * 1.1 + fs * .7)
        d.text((lx, ly), label, font=f, fill=col + (255,), anchor='mm', stroke_width=max(4, fs // 8), stroke_fill=INK + (255,))
    if alpha < 1:
        lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)
    return (x1, y1)

"""flat2d.persp: a small perspective camera + toon mesh renderer for flat2d sets and vehicles (video 12 on).

Why: the cinematic 2D look (real perspective sets, a moving camera, low/high/top-down angles) needs sets that are
drawn from a camera, not painted once. Everything here stays in the house flat2d look: flat toon-shaded facets
(faceted light/shadow planes), a cool shadow tint, ink outlines on silhouettes and on chosen edges.

World: right-handed, z up, metres. Screen: 1080x1920 px (y down).
- `Cam(pos, target, fov, roll)`: a look-at pinhole camera (vertical fov in degrees). `project`, `to_cam`,
  `px_per_m`, `Cam.lerp`.
- `Path(keys)`: a camera move through keyframes [(t, pos, target, fov, roll)], Catmull-Rom through the keys (no stops
  at the keys), eased over the whole move, with an optional handheld drift.
- `Part`: one convex-ish group of polygons drawn as a unit (painter's sort between parts by depth, back-face culling
  inside a part, then its decals). Items: `poly` (filled, optional ink edges), `decal` (drawn after the part's
  polygons, only when its normal faces the camera: windows, stripes, rivets), `line` (a 3D beam of a width in metres:
  trusses, rails, pipes), `dot` (a round 3D point of a radius in metres: rivets, bulbs).
- Builders: `box`, `lathe` (surfaces of revolution: fuselages, tanks, pipes), `loft` (sections along a path: wings,
  fins), `prism` (an extruded outline), `quad`, `grid`.
- `render(layer, cam, parts, ...)`: toon shading (Lambert in soft bands + a cool shadow tint + optional specular),
  per-face `fog(col, P)` hook (haze, under-water tint), near-plane clipping (the camera may fly inside a set),
  supersampling (SS), a silhouette ink rim per part (blur+threshold dilation, not MaxFilter: LESSONS).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

INK = (18, 16, 26)
SS = 1                  # supersampling; the 540 preview downsizes 1080 frames anyway (set 2 for a 1080 final)
W, H = 1080, 1920


def _n(v):
    v = np.asarray(v, float); n = np.linalg.norm(v); return v / n if n > 1e-12 else v


def lerp3(a, b, k): return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def rgb_mul(c, k): return tuple(int(max(0, min(255, c[i] * k))) for i in range(3))


def rgb_mix(a, b, k): return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------------------------------------------------------------- camera
class Cam:
    """Look-at pinhole camera. fov = vertical field of view (deg); roll (deg, + = clockwise on screen);
    shift = lens shift in px (keeps verticals straight while framing up/down, like a tilt-shift)."""
    def __init__(self, pos, target, fov=45.0, roll=0.0, size=(W, H), near=0.08, shift=(0.0, 0.0), up=(0, 0, 1)):
        self.pos = np.array(pos, float); self.target = np.array(target, float)
        self.fov, self.roll, self.size, self.near, self.shift = fov, roll, size, near, shift
        f = _n(self.target - self.pos); upv = np.array(up, float)
        if abs(f @ upv) > .9995: upv = np.array([0, 1.0, 0]) if abs(f[1]) < .9 else np.array([1.0, 0, 0])
        r = _n(np.cross(f, upv)); u = np.cross(r, f)
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        self.r, self.u = r * c - u * s, r * s + u * c
        self.f = f
        self.fpx = (size[1] / 2) / math.tan(math.radians(fov) / 2)
        self.cx, self.cy = size[0] / 2 + shift[0], size[1] / 2 + shift[1]

    def to_cam(self, P):
        d = np.asarray(P, float) - self.pos
        return np.stack([d @ self.r, d @ self.u, d @ self.f], -1)

    def proj_cam(self, C):
        z = np.maximum(C[..., 2], 1e-6)
        return np.stack([self.cx + self.fpx * C[..., 0] / z, self.cy - self.fpx * C[..., 1] / z], -1)

    def project(self, P):
        """(N,3) world -> ((N,2) screen px, (N,) depth along the view axis)."""
        C = self.to_cam(np.atleast_2d(P)); return self.proj_cam(C), C[..., 2]

    def p(self, P):
        """One point -> (x, y) screen px."""
        s, _ = self.project([P]); return float(s[0, 0]), float(s[0, 1])

    def depth(self, P): return float(self.to_cam(np.atleast_2d(P))[0, 2])

    def px_per_m(self, P): return self.fpx / max(1e-6, self.depth(P))

    @staticmethod
    def lerp(a, b, k):
        return Cam(lerp3(a.pos, b.pos, k), lerp3(a.target, b.target, k), a.fov + (b.fov - a.fov) * k,
                   a.roll + (b.roll - a.roll) * k, a.size, a.near, (a.shift[0] + (b.shift[0] - a.shift[0]) * k,
                                                                     a.shift[1] + (b.shift[1] - a.shift[1]) * k))


def _cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(.5 * (2 * p1[i] + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2
                       + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3) for i in range(len(p1)))


def ease_io(t, a=2.2):
    t = max(0.0, min(1.0, t)); return t ** a / (t ** a + (1 - t) ** a) if 0 < t < 1 else t


class Path:
    """A camera move through keys [(t, pos, target, fov, roll)]: Catmull-Rom through the positions and targets, so
    the camera never stops at a key; `ease` reshapes time per segment (default: linear between keys, eased only at
    the first and last key, so the whole move starts and lands softly). `drift` adds a slow handheld wander (m)."""
    def __init__(self, keys, ease_ends=True, drift=0.0, seed=0, shift=(0.0, 0.0)):
        self.keys = sorted(keys, key=lambda k: k[0]); self.ease_ends = ease_ends; self.drift = drift
        self.seed = seed; self.shift = shift

    def at(self, t):
        ks = self.keys
        if t <= ks[0][0]: i, u = 0, 0.0
        elif t >= ks[-1][0]: i, u = len(ks) - 2, 1.0
        else:
            i = max(j for j in range(len(ks) - 1) if ks[j][0] <= t)
            u = (t - ks[i][0]) / (ks[i + 1][0] - ks[i][0])
        if len(ks) == 1:
            k = ks[0]; return Cam(k[1], k[2], k[3], k[4] if len(k) > 4 else 0.0, shift=self.shift)
        if self.ease_ends:
            T0, T1 = ks[0][0], ks[-1][0]
            g = ease_io((min(max(t, T0), T1) - T0) / (T1 - T0)) * (T1 - T0) + T0      # eased global time
            if g >= ks[-1][0]: i, u = len(ks) - 2, 1.0
            else:
                i = max(j for j in range(len(ks) - 1) if ks[j][0] <= g)
                u = (g - ks[i][0]) / (ks[i + 1][0] - ks[i][0])
        a = ks[max(0, i - 1)]; b = ks[i]; c = ks[i + 1]; d = ks[min(len(ks) - 1, i + 2)]
        pos = _cr(a[1], b[1], c[1], d[1], u); tgt = _cr(a[2], b[2], c[2], d[2], u)
        su = u * u * (3 - 2 * u)
        fov = b[3] + (c[3] - b[3]) * su
        roll = (b[4] if len(b) > 4 else 0) + ((c[4] if len(c) > 4 else 0) - (b[4] if len(b) > 4 else 0)) * su
        if self.drift:
            s = self.seed
            dx = self.drift * (math.sin(t * .71 + s) + .5 * math.sin(t * 1.33 + 2 * s))
            dz = self.drift * (math.sin(t * .53 + 3 * s) + .5 * math.sin(t * 1.21 + s))
            tgt = (tgt[0] + dx * .6, tgt[1] + dx * .4, tgt[2] + dz)
            roll += self.drift * 3 * math.sin(t * .37 + s)
        return Cam(pos, tgt, fov, roll, shift=self.shift)


# ---------------------------------------------------------------- geometry
class Part:
    """A unit drawn in one go: polygons (back-face culled, painter-sorted), then decals, lines and dots.
    opts: sil (ink rim around the part), sil_w (px), spec (power, strength), shade (bool), two (no culling),
    fog (bool: apply the render's fog), order (fixed draw order; None = by depth)."""
    def __init__(self, name='', sil=True, sil_w=None, spec=None, two=False, order=None, bias=0.0):
        self.name = name; self.sil = sil; self.sil_w = sil_w; self.spec = spec; self.two = two
        self.order = order; self.bias = bias
        self.polys = []      # [P (k,3), col, ink (bool or width), emit (0..1), two]
        self.decals = []     # [P (k,3), col, ink, emit, normal or None]
        self.lines = []      # [P (2,3), w_m, col, ink]
        self.dots = []       # [P (3,), r_m, col, ink, emit]

    def poly(self, pts, col, ink=False, emit=0.0, two=None):
        self.polys.append([np.asarray(pts, float), tuple(col), ink, emit, self.two if two is None else two]); return self

    def decal(self, pts, col, ink=False, emit=0.0, normal=None):
        self.decals.append([np.asarray(pts, float), tuple(col), ink, emit, None if normal is None else _n(normal)]); return self

    def line(self, p0, p1, w, col, ink=True):
        self.lines.append([np.asarray([p0, p1], float), w, tuple(col), ink]); return self

    def dot(self, p, r, col, ink=False, emit=0.0):
        self.dots.append([np.asarray(p, float), r, tuple(col), ink, emit]); return self

    def add(self, other):
        self.polys += [list(x) for x in other.polys]; self.decals += [list(x) for x in other.decals]
        self.lines += [list(x) for x in other.lines]; self.dots += [list(x) for x in other.dots]; return self

    def xform(self, R=None, t=(0, 0, 0), s=1.0):
        """A transformed copy (R: 3x3 rotation, s: uniform scale, then translate t)."""
        R = np.eye(3) if R is None else np.asarray(R, float); t = np.asarray(t, float)
        f = lambda P: (np.asarray(P, float) * s) @ R.T + t
        o = Part(self.name, self.sil, self.sil_w, self.spec, self.two, self.order, self.bias)
        o.polys = [[f(P), c, i, e, tw] for P, c, i, e, tw in self.polys]
        o.decals = [[f(P), c, i, e, None if nm is None else nm @ R.T] for P, c, i, e, nm in self.decals]
        o.lines = [[f(P), w * s, c, i] for P, w, c, i in self.lines]
        o.dots = [[f(P[None])[0], r * s, c, i, e] for P, r, c, i, e in self.dots]
        return o

    def bounds(self):
        pts = [P for P, *_ in self.polys] + [P for P, *_ in self.decals] + [P for P, *_ in self.lines]
        pts += [P[None] for P, *_ in self.dots]
        A = np.concatenate(pts, 0); return A.min(0), A.max(0)

    def centre(self):
        a, b = self.bounds(); return (a + b) / 2


def rot_x(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def box(p0, p1, col, ink=True, part=None, cols=None, sil=True, emit=0.0, skip=()):
    """Axis-aligned box from corner p0 to p1. cols: {face: colour} for 'top','bottom','px','nx','py','ny'."""
    P = part or Part('box', sil=sil)
    x0, y0, z0 = p0; x1, y1, z1 = p1
    F = {'top': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
         'bottom': [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
         'px': [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
         'nx': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
         'py': [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)],
         'ny': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]}
    for k, pts in F.items():
        if k in skip: continue
        P.poly(pts, (cols or {}).get(k, col), ink=ink, emit=emit)
    return P


def obox(c, size, R, col, ink=True, part=None, cols=None):
    """An oriented box: centre c, size (sx, sy, sz), rotation R."""
    sx, sy, sz = size
    b = box((-sx / 2, -sy / 2, -sz / 2), (sx / 2, sy / 2, sz / 2), col, ink, cols=cols)
    b = b.xform(R, c)
    if part is not None: part.add(b); return part
    return b


def lathe(xs, radius, col_fn, n=24, part=None, zc=None, yc=None, phase=0.0, ink=False, caps=(False, False),
          cap_col=None):
    """Surface of revolution along x: rings at xs with radius(x[, phi]) (callable or list) about the axis
    (y=yc(x), z=zc(x)); col_fn(x, phi) -> colour per facet (phi: 0 = +y side, pi/2 = top). Facets face outwards."""
    P = part or Part('lathe')
    phis = [phase + 2 * math.pi * i / n for i in range(n)]
    def R(x, ph):
        if callable(radius):
            try: return radius(x, ph)
            except TypeError: return radius(x)
        return radius[list(xs).index(x)]
    rings = []
    for x in xs:
        z0 = zc(x) if zc else 0.0; y0 = yc(x) if yc else 0.0
        rings.append([(x, y0 + math.cos(ph) * R(x, ph), z0 + math.sin(ph) * R(x, ph)) for ph in phis])
    for i in range(len(xs) - 1):
        for j in range(n):
            a, b = rings[i][j], rings[i][(j + 1) % n]; c, d = rings[i + 1][(j + 1) % n], rings[i + 1][j]
            ph = phis[j] + math.pi / n
            # outward winding (counter-clockwise seen from outside): a -> b -> c -> d
            P.poly([a, b, c, d], col_fn((xs[i] + xs[i + 1]) / 2, ph), ink=ink)
    if caps[0]: P.poly(rings[0][::-1], cap_col or col_fn(xs[0], 0))
    if caps[1]: P.poly(rings[-1], cap_col or col_fn(xs[-1], 0))
    return P


def loft(sections, col, part=None, ink=False, caps=True, col_fn=None):
    """Join closed cross-sections (lists of 3D points, same count, same winding) into a skin; caps close the ends.
    Wings: sections from root to tip, each an airfoil-ish outline."""
    P = part or Part('loft')
    for i in range(len(sections) - 1):
        A, B = sections[i], sections[i + 1]; n = len(A)
        for j in range(n):
            c = col_fn(i, j) if col_fn else col
            P.poly([A[j], A[(j + 1) % n], B[(j + 1) % n], B[j]], c, ink=ink)
    if caps:
        P.poly(sections[0][::-1], col, ink=ink); P.poly(sections[-1], col, ink=ink)
    return P


def prism(outline, z0, z1, col, part=None, ink=True, side_col=None, top_col=None, R=None, t=(0, 0, 0)):
    """An outline (counter-clockwise (x, y) list) extruded from z0 to z1, then rotated/moved."""
    P = Part('prism')
    n = len(outline)
    for i in range(n):
        (xa, ya), (xb, yb) = outline[i], outline[(i + 1) % n]
        P.poly([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], side_col or col, ink=ink)
    P.poly([(x, y, z1) for x, y in outline], top_col or col, ink=ink)
    P.poly([(x, y, z0) for x, y in outline[::-1]], col, ink=ink)
    if R is not None or any(t): P = P.xform(R, t)
    if part is not None: part.add(P); return part
    return P


def quad(c, u, v, col, part=None, ink=False, emit=0.0):
    """A flat rectangle: centre c, half-axes u and v (3D vectors). Normal = u x v."""
    c, u, v = np.asarray(c, float), np.asarray(u, float), np.asarray(v, float)
    pts = [c - u - v, c + u - v, c + u + v, c - u + v]
    P = part or Part('quad')
    P.poly(pts, col, ink=ink, emit=emit); return P


def round_rect2d(w, h, r, n=6):
    """Rounded rectangle outline in 2D (counter-clockwise), centred on 0: w, h full sizes, corner radius r."""
    r = min(r, w / 2, h / 2); pts = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ---------------------------------------------------------------- rendering
def _clip_near(C, near):
    """Sutherland-Hodgman against z >= near in camera space. C: (k,3)."""
    out = []; k = len(C)
    for i in range(k):
        a, b = C[i], C[(i + 1) % k]; ina, inb = a[2] >= near, b[2] >= near
        if ina: out.append(a)
        if ina != inb:
            t = (near - a[2]) / (b[2] - a[2]); out.append(a + (b - a) * t)
    return np.array(out) if len(out) >= 3 else None


def _newell(P):
    n = np.zeros(3)
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n += ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1]))
    return _n(n)


class Light:
    """Toon light: key direction (towards the light), ambient, band softness, a cool shadow tint, rim."""
    def __init__(self, d=(-.35, -.45, .82), amb=.46, bands=(.18, .52, .8), soft=.35, shadow=(70, 84, 130),
                 shadow_k=.28, key_col=(255, 248, 236), key_k=.0):
        self.d = _n(d); self.amb, self.bands, self.soft = amb, bands, soft
        self.shadow, self.shadow_k, self.key_col, self.key_k = shadow, shadow_k, key_col, key_k

    def shade(self, col, n, v=None, spec=None, emit=0.0):
        if emit >= 1: return col
        l = max(0.0, float(n @ self.d))
        q = sum(.25 for b in self.bands if l >= b) / (.25 * len(self.bands))      # 0..1 in bands
        k = q * (1 - self.soft) + l * self.soft
        val = self.amb + (1 - self.amb) * k
        c = rgb_mul(col, val)
        if self.shadow_k: c = rgb_mix(c, rgb_mul(self.shadow, val * 1.1), (1 - k) * self.shadow_k)
        if self.key_k and k > .6: c = rgb_mix(c, self.key_col, (k - .6) * self.key_k)
        if spec and v is not None:
            h = _n(self.d + v); s = max(0.0, float(n @ h)) ** spec[0] * spec[1]
            c = rgb_mix(c, (255, 255, 255), min(1.0, s))
        if emit: c = rgb_mix(c, col, emit)
        return c


DEFAULT_LIGHT = Light()


def _dilate(a, r):
    """Binary-ish dilation of an L alpha by ~r px (blur + threshold: fast at any r)."""
    if r <= 0: return a
    b = a.filter(ImageFilter.GaussianBlur(r * .55))
    return b.point(lambda v: 255 if v > 18 else int(v * 255 / 18))


def render(layer, cam, parts, light=None, fog=None, ink=INK, ink_w=3.0, sil_w=5.0, ss=None, ox=0, oy=0,
           cull=True, order=None, clip=None, return_alpha=False):
    """Draw parts onto `layer` (RGBA, frame px) with camera `cam`. fog(col, P_world, depth) -> col per face.
    Parts are drawn far -> near by the depth of their centre (part.bias m added; part.order or `order`, a list of
    names, fixes it instead). clip: optional (x0, y0, x1, y1) screen box to limit the canvas (speed).
    Returns the screen bbox drawn (or None)."""
    light = light or DEFAULT_LIGHT; ss = ss or SS
    Wl, Hl = layer.size
    items = []
    for p in parts:
        if not (p.polys or p.decals or p.lines or p.dots): continue
        c = p.centre(); d = cam.depth(c) + p.bias
        key = p.order if p.order is not None else -d
        if order is not None and p.name in order: key = order.index(p.name) - 1e6
        items.append((key, p))
    items.sort(key=lambda x: x[0])
    # screen bbox of everything (clamped): project each part's box corners; anything behind the camera -> full frame
    if clip is None:
        xs, ys, full = [], [], False
        for _, p in items:
            lo, hi = p.bounds()
            cs = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
            C = cam.to_cam(cs)
            if (C[:, 2] < cam.near).any(): full = True; break
            S = cam.proj_cam(C); xs += [S[:, 0].min(), S[:, 0].max()]; ys += [S[:, 1].min(), S[:, 1].max()]
        if not full and xs:
            pad = 24 + sil_w * 2
            clip = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    X0, Y0, X1, Y1 = (clip if clip else (0, 0, Wl, Hl))
    X0, Y0, X1, Y1 = int(max(0, X0)), int(max(0, Y0)), int(min(Wl, X1)), int(min(Hl, Y1))
    if X1 <= X0 or Y1 <= Y0: return None
    cw, ch = (X1 - X0) * ss, (Y1 - Y0) * ss
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    alpha_total = Image.new('L', (cw, ch), 0) if return_alpha else None
    drew = False
    V = cam.pos
    for _, p in items:
        lay = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)) if p.sil else canvas
        d = ImageDraw.Draw(lay)
        polys = []
        # ---- polygons: cull, shade, clip, project
        for P, col, ink_e, emit, two in p.polys:
            n = _newell(P); cen = P.mean(0)
            facing = float(n @ (V - cen)) > 0
            if cull and not facing and not two: continue
            if not facing: n = -n
            C = cam.to_cam(P)
            if (C[:, 2] < cam.near).any():
                C = _clip_near(C, cam.near)
                if C is None: continue
            S = cam.proj_cam(C)
            if S[:, 0].max() < X0 - 50 or S[:, 0].min() > X1 + 50 or S[:, 1].max() < Y0 - 50 or S[:, 1].min() > Y1 + 50:
                continue
            vdir = _n(V - cen)
            cc = light.shade(col, n, vdir, p.spec, emit)
            if fog: cc = fog(cc, cen, float(C[:, 2].mean()))
            polys.append((float(C[:, 2].mean()), S, cc, ink_e))
        polys.sort(key=lambda x: -x[0])
        for _, S, cc, ink_e in polys:
            pts = [((x - X0) * ss, (y - Y0) * ss) for x, y in S]
            d.polygon(pts, fill=cc + (255,))
            if ink_e:
                wv = (ink_w if ink_e is True else ink_e) * ss
                d.line(pts + [pts[0]], fill=ink + (255,), width=max(1, int(round(wv))), joint='curve')
            drew = True
        # ---- decals (after the part's polygons; only when facing)
        for P, col, ink_e, emit, nm in p.decals:
            cen = P.mean(0); n = nm if nm is not None else _newell(P)
            if cull and float(n @ (V - cen)) <= 0: continue
            C = cam.to_cam(P)
            if (C[:, 2] < cam.near).any():
                C = _clip_near(C, cam.near)
                if C is None: continue
            S = cam.proj_cam(C)
            cc = light.shade(col, n, _n(V - cen), p.spec, emit)
            if fog: cc = fog(cc, cen, float(C[:, 2].mean()))
            pts = [((x - X0) * ss, (y - Y0) * ss) for x, y in S]
            d.polygon(pts, fill=cc + (255,))
            if ink_e:
                wv = (ink_w if ink_e is True else ink_e) * ss
                d.line(pts + [pts[0]], fill=ink + (255,), width=max(1, int(round(wv))), joint='curve')
            drew = True
        # ---- beams and dots (depth-sorted among themselves)
        segs = []
        for P, wm, col, ink_e in p.lines:
            C = cam.to_cam(P)
            if (C[:, 2] < cam.near).all(): continue
            if (C[:, 2] < cam.near).any():
                a, b = C; t = (cam.near - a[2]) / (b[2] - a[2])
                if a[2] < cam.near: a = a + (b - a) * t
                else: b = a + (b - a) * t
                C = np.array([a, b])
            S = cam.proj_cam(C)
            wpx = [cam.fpx * wm / max(1e-3, z) for z in C[:, 2]]
            cc = col
            if fog: cc = fog(cc, P.mean(0), float(C[:, 2].mean()))
            segs.append((float(C[:, 2].mean()), S, wpx, cc, ink_e))
        for P, r, col, ink_e, emit in p.dots:
            C = cam.to_cam(P[None])[0]
            if C[2] < cam.near: continue
            S = cam.proj_cam(C[None])[0]; rp = cam.fpx * r / C[2]
            cc = col
            if fog: cc = fog(cc, P, float(C[2]))
            segs.append((float(C[2]), S, rp, cc, ink_e))
        segs.sort(key=lambda x: -x[0])
        for _, S, wpx, cc, ink_e in segs:
            if isinstance(wpx, list):
                (xa, ya), (xb, yb) = S; dx, dy = xb - xa, yb - ya; L = math.hypot(dx, dy) or 1
                nx, ny = -dy / L, dx / L
                wa, wb = wpx[0] / 2, wpx[1] / 2
                pts = [(xa + nx * wa, ya + ny * wa), (xb + nx * wb, yb + ny * wb), (xb - nx * wb, yb - ny * wb),
                       (xa - nx * wa, ya - ny * wa)]
                pts = [((x - X0) * ss, (y - Y0) * ss) for x, y in pts]
                if ink_e:
                    iw = (ink_w if ink_e is True else ink_e) * ss
                    d.line(pts + [pts[0]], fill=ink + (255,), width=max(1, int(round(iw * 2))), joint='curve')
                d.polygon(pts, fill=cc + (255,))
            else:
                x, y = (S[0] - X0) * ss, (S[1] - Y0) * ss; r = max(.6, wpx * ss)
                if ink_e:
                    iw = (ink_w if ink_e is True else ink_e) * ss
                    d.ellipse([x - r - iw, y - r - iw, x + r + iw, y + r + iw], fill=ink + (255,))
                d.ellipse([x - r, y - r, x + r, y + r], fill=cc + (255,))
            drew = True
        if p.sil and lay is not canvas:
            a = lay.split()[3]
            if a.getbbox():
                sw = (p.sil_w if p.sil_w is not None else sil_w) * ss
                ring = _dilate(a, sw)
                inkl = Image.new('RGBA', (cw, ch), ink + (0,)); inkl.putalpha(ring)
                canvas.alpha_composite(inkl); canvas.alpha_composite(lay)
                if alpha_total is not None: alpha_total.paste(255, (0, 0), ring)
        elif alpha_total is not None:
            alpha_total.paste(255, (0, 0), lay.split()[3])
    if not drew: return None
    if ss > 1: canvas = canvas.resize((X1 - X0, Y1 - Y0), Image.LANCZOS)
    layer.alpha_composite(canvas, (X0, Y0))
    if return_alpha:
        if ss > 1: alpha_total = alpha_total.resize((X1 - X0, Y1 - Y0), Image.BILINEAR)
        full = Image.new('L', layer.size, 0); full.paste(alpha_total, (X0, Y0)); return full
    return (X0, Y0, X1, Y1)


def fog_linear(col, d0, d1, k1, P_unused=None):
    """Helper: a distance-haze fog function factory: fog(col, P, depth) mixes toward col by depth."""
    def f(c, P, depth):
        k = max(0.0, min(1.0, (depth - d0) / (d1 - d0))) * k1
        return rgb_mix(c, col, k)
    return f

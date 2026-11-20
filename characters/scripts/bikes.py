# Bicycle, motorbike and "nobs" bike (a motorbike with a second, fixed handlebar) drawn in the bean-cast style
# (plum ink, flat fills, soft crescent shading). Each bike is a tiny 3D model (tubes, wheels, extruded panels)
# projected orthographically, so one rig gives side / 3q / rear / front / top views, a steer angle that turns
# the front assembly about the head tube, and a lean angle about the ground line.
# ride() seats a bean character on it (hip on the saddle, hands on the grips, feet on pedals or pegs via IK).
# Canvas 1000x1000 design units, ground at y=975 (same pixel scale as the 600x1000 character cards).
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from bean import INK, S, Canvas, mix, mul, hexrgb, turned, BUILDS

CW, CH, GROUND, CX = 1000, 1000, 975, 500
VIEWS = {'side': (-90, 0), '3q': (-38, 10), 'rear': (180, 14), 'front': (0, 14), 'top': (None, 90)}
TIRE, RIM, CHROME, DARK, SEAT = (52, 46, 58), (206, 210, 218), (196, 202, 212), (58, 56, 66), (44, 40, 48)

def V(*a): return a
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mulv(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a): n = math.sqrt(dot(a, a)) or 1.0; return mulv(a, 1 / n)

def rodrigues(p, o, k, ang):
    """Rotate point p about the axis through o with unit direction k by ang degrees (right-hand rule)."""
    t = math.radians(ang); v = sub(p, o)
    r = add(add(mulv(v, math.cos(t)), mulv(cross(k, v), math.sin(t))), mulv(k, dot(k, v) * (1 - math.cos(t))))
    return add(o, r)

def camera(view):
    """Orthographic camera: (right, up, forward) unit vectors. Bike frame: x forward, y to the bike's left, z up."""
    if view == 'top': return (0, -1, 0), (1, 0, 0), (0, 0, -1)
    az, el = map(math.radians, VIEWS[view])
    pos = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
    f = mulv(pos, -1); r = norm(cross(f, (0, 0, 1))); up = cross(r, f)
    return r, up, f

# ----------------------------------------------------------------------------------- models
def model(kind='bicycle', color='#2f8fd8', fixed_color='#f2c230', leg=330):
    """Parts in the bike frame (px; 1 m ~ 420 px). Each part: dict(kind, group 'frame'|'steer', lat (y of the part),
    + geometry). Anchors: seat, grips (L/R), feet (L/R), steer axis."""
    col = hexrgb(color); P = []; A = {}
    def tube(a, b, w, c, grp='frame', tag=None): P.append(dict(kind='tube', a=a, b=b, w=w, col=c, grp=grp, lat=(a[1] + b[1]) / 2 if tag != 'bar' else 0, tag=tag))
    def wheel(c, R, tw, grp, spokes): P.append(dict(kind='wheel', c=c, R=R, tw=tw, grp=grp, lat=0, spokes=spokes))
    def prism(poly, y0, y1, c, grp='frame', shade=True): P.append(dict(kind='prism', poly=poly, y0=y0, y1=y1, col=c, grp=grp, lat=(y0 + y1) / 2, shade=shade))
    def disc(c, n, r, cl, grp='frame', glow=False): P.append(dict(kind='disc', c=c, n=n, r=r, col=cl, grp=grp, lat=c[1], glow=glow))
    def quad(corners, cl, grp='frame', marks=False): P.append(dict(kind='quad', pts=corners, col=cl, grp=grp, lat=sum(q[1] for q in corners) / 4, marks=marks))
    if kind == 'bicycle':
        R = 140; ra, fa = (-220, 0, R), (220, 0, R); bb = (-25, 0, 118)
        sz = bb[2] + 0.86 * leg                                    # saddle fitted to the rider: the low leg is nearly straight
        dz = sz - 352
        head_t, head_b = (160, 0, 335 + dz), (180, 0, 282)
        wheel(ra, R, 15, 'frame', 18); wheel(fa, R, 15, 'steer', 18)
        st_top = (-88, 0, 322 + dz * 0.6)
        for y in (-13, 13):
            tube(bb[:1] + (y,) + bb[2:], ra[:1] + (y,) + ra[2:], 11, col)             # chain stays
            tube((st_top[0] + 4, y, st_top[2] - 14), ra[:1] + (y,) + ra[2:], 11, col)  # seat stays
        tube(bb, st_top, 16, col); tube(head_b, bb, 18, col); tube((head_t[0] + 2, 0, head_t[2] - 13), st_top, 15, col)
        tube(head_t, head_b, 19, col)
        tube((st_top[0] - 2, 0, st_top[2] - 4), (-97, 0, sz - 14), 10, CHROME)          # seat post
        prism([(-140, sz), (-70, sz), (-58, sz - 10), (-100, sz - 20), (-140, sz - 16)], -16, 16, SEAT)
        A['seat'] = (-102, 0, sz)
        for y in (-14, 14): tube((head_b[0] + 3, y, head_b[2]), (fa[0], y, fa[2]), 10, col, 'steer')   # fork blades
        bz = head_t[2] + 31
        tube(head_t, (150, 0, bz - 2), 10, CHROME, 'steer')                              # stem
        tube((152, -105, bz), (152, 105, bz), 10, CHROME, 'steer', tag='bar')            # bar
        for y in (-1, 1): tube((150, y * 82, bz), (146, y * 108, bz), 15, DARK, 'steer', tag='grip')
        A['grips'] = {'R': (148, -96, bz), 'L': (148, 96, bz)}
        disc((bb[0], -22, bb[2]), (0, 1, 0), 30, CHROME)                                 # chainring
        A['crank'] = dict(bb=bb, L=50, y=34)
        A['axis'] = (head_t, head_b)
        A['tilt_fwd'] = 26; A['kind'] = 'bicycle'
    else:
        R = 148; ra, fa = (-262, 0, R), (268, 0, R)
        head_t, head_b = (178, 0, 372), (205, 0, 300)
        # fat tyres: from behind a motorbike must never read as a bicycle (a bicycle tyre is 15)
        wheel(ra, R, 92, 'frame', 0); wheel(fa, R, 72, 'steer', 0)
        tube((-40, 0, 205), ra, 24, mul(col, (0.55, 0.55, 0.6)))                                        # swing arm
        tube(head_b, (-60, 0, 292), 26, mul(col, (0.55, 0.55, 0.6)))                                    # frame spine
        prism([(-62, 268), (100, 280), (128, 192), (78, 138), (-52, 148)], -112, 112, (122, 126, 136))   # engine: wide, shows between the legs
        prism([(-20, 250), (60, 255), (70, 170), (-10, 165)], -128, 128, (98, 102, 112))                  # cylinder heads jutting out each side
        tube((80, -96, 150), (-230, -96, 220), 26, CHROME)                                                # exhaust pipe (right side)
        prism([(-180, 236), (-300, 250), (-306, 210), (-186, 200)], -128, -66, CHROME)                   # exhaust can, set wide
        disc((-307, -97, 230), (-1, 0, 0), 17, (52, 50, 60))                                              # the can's dark end, seen from behind
        prism([(-305, 334), (-200, 340), (-55, 322), (-48, 262), (-190, 266), (-296, 298)], -62, 62, col)   # tail / side covers: bulky
        prism([(-215, 350), (25, 360), (32, 330), (-205, 322)], -64, 64, SEAT)                          # seat
        prism([(18, 362), (150, 372), (188, 326), (132, 282), (16, 292)], -82, 82, col)                 # tank bulk
        prism([(-330, 300), (-240, 306), (-215, 262), (-322, 236)], -40, 40, mul(col, (0.85, 0.85, 0.85)))   # rear mudguard
        disc((-308, 0, 318), (-1, 0, 0), 22, (226, 50, 60))                                              # tail light, big
        tube((-318, 0, 300), (-334, 0, 262), 10, DARK)                                                   # plate bracket
        quad([(-336, -52, 262), (-336, 52, 262), (-340, 52, 216), (-340, -52, 216)], (246, 210, 64), marks=True)   # number plate
        A['seat'] = (-85, 0, 352)
        for y in (-38, 38): tube((head_b[0] - 5, y, head_b[2] + 30), (fa[0], y, fa[2]), 18, CHROME, 'steer')   # fork legs
        prism([(fa[0] - 92, R + 18), (fa[0] + 70, R + 30), (fa[0] + 74, R + 18), (fa[0] - 88, R + 6)], -24, 24, col, 'steer')  # front fender
        tube(head_t, head_b, 30, mul(col, (0.6, 0.6, 0.65)), 'steer')                                   # head / triple clamp
        hx_, hz_ = head_t[0] + 18, head_t[2] - 28                                                         # headlight housing + lens
        prism([(hx_, hz_ - 30), (hx_ + 40, hz_ - 36), (hx_ + 52, hz_), (hx_ + 40, hz_ + 34), (hx_, hz_ + 28)], -30, 30, DARK, 'steer')
        disc((hx_ + 53, 0, hz_), (1, 0, 0), 30, (255, 236, 170), 'steer', glow=True)
        tube(head_t, (170, 0, 392), 14, CHROME, 'steer')
        tube((168, -142, 398), (168, 142, 398), 12, CHROME, 'steer', tag='bar')                         # bar
        for y in (-1, 1): tube((166, y * 112, 398), (162, y * 150, 398), 19, DARK, 'steer', tag='grip')
        A['grips'] = {'R': (164, -132, 398), 'L': (164, 132, 398)}
        for y in (-1, 1): tube((-25, y * 112, 178), (-25, y * 160, 178), 16, CHROME)                    # foot pegs, outside the engine
        A['pegs'] = {'R': (-25, -146, 184), 'L': (-25, 146, 184)}
        A['axis'] = (head_t, head_b)
        A['tilt_fwd'] = 14; A['kind'] = 'motorbike'
        if kind == 'nobs_bike':          # a second handlebar bolted to the frame: it cannot steer
            fc = hexrgb(fixed_color)
            for y in (-1, 1): tube((150, y * 40, 360), (128, y * 110, 478), 22, fc)                     # thick posts bolted to the tank
            prism([(108, 466), (150, 466), (150, 494), (108, 494)], -128, 128, mul(fc, (0.8, 0.8, 0.8)))   # wide clamp block
            tube((126, -265, 480), (126, 265, 480), 22, fc, tag='bar')                                    # the fixed bar: high and wide,
            for y in (-1, 1): tube((124, y * 222, 480), (120, y * 272, 480), 24, DARK, tag='grip')      # its ends clear the rider's back
            for y in (-1, 1): disc((152, y * 110, 480), (1, 0, 0), 10, (90, 92, 104))                  # bolt heads
            A['fixed_grips'] = {'R': (122, -250, 480), 'L': (122, 250, 480)}
            A['kind'] = 'nobs_bike'
    return P, A

# ----------------------------------------------------------------------------------- posing + projection
def pose_point(p, grp, A, steer, lean):
    if grp == 'steer' and steer:
        o, b = A['axis']; k = norm(sub(o, b))                 # up the steering axis; + steer turns the front to the bike's right
        p = rodrigues(p, o, k, -steer)
    if lean:                                                  # + lean tips the bike to its right (about the ground line)
        p = rodrigues(p, (0, 0, 0), (1, 0, 0), lean)
    return p

class Proj:
    def __init__(self, view, cam_shift=(0, 0), contacts=()):
        self.view = view; self.r, self.u, self.f = camera(view)
        self.oy = 600 if view == 'top' else GROUND; self.ox = CX; self.sh = cam_shift
        if view != 'top' and contacts:                     # an elevated camera: lift so the lowest tyre touches the ground line
            self.oy = GROUND + min(dot(c, self.u) for c in contacts) - 2
    def __call__(self, p):
        return (self.ox + dot(p, self.r) + self.sh[0], self.oy - dot(p, self.u) + self.sh[1])
    def depth(self, p): return dot(p, self.f)

def _circle(c, R, e1, e2, n=72):
    return [add(c, add(mulv(e1, R * math.cos(2 * math.pi * i / n)), mulv(e2, R * math.sin(2 * math.pi * i / n)))) for i in range(n)]

def _hull(pts):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3: return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]

def _area(poly): return abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))) / 2

OW = 3.6   # ink rim around tubes and wheels (design units each side)

def fill_fast(C, pts, col, shadow_k, shift, blur, light=(-0.7, -0.7)):
    """Canvas.fill_shaded, but on a crop around the shape (same look, ~50x faster on a big canvas)."""
    from PIL import ImageFilter, ImageChops
    xs = [x for x, _ in pts]; ys = [y for _, y in pts]; pad = shift + 3 * blur + 4
    x0, y0 = int((min(xs) - pad) * S), int((min(ys) - pad) * S); x1, y1 = int((max(xs) + pad) * S), int((max(ys) + pad) * S)
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    loc = [(x * S - x0, y * S - y0) for x, y in pts]
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).polygon(loc, fill=255)
    lit = Image.new('L', (w, h), 0); ImageDraw.Draw(lit).polygon([(x + light[0] * shift * S, y + light[1] * shift * S) for x, y in loc], fill=255)
    lit = ImageChops.multiply(lit.filter(ImageFilter.GaussianBlur(blur * S)), m)
    lay = Image.new('RGBA', (w, h), mul(col, shadow_k) + (255,)); lay.putalpha(m)
    top = Image.new('RGBA', (w, h), col + (255,)); top.putalpha(lit); lay.alpha_composite(top)
    C.im.alpha_composite(lay, (x0, y0)); C.d = ImageDraw.Draw(C.im)

def _contacts(P, A, steer, lean):
    out = []
    for p in P:
        if p['kind'] == 'wheel':
            c = p['c']; out += [pose_point((c[0] + dx, c[1], c[2] - p['R']), p['grp'], A, steer, lean) for dx in (-p['R'] * 0.6, 0, p['R'] * 0.6)]
    return out

def build_drawables(P, A, pr, steer, lean):
    """-> list of (depth, lat, draw_fn(C))"""
    out = []
    for part in P:
        g = part['grp']; T = lambda p: pose_point(p, g, A, steer, lean)
        if part['kind'] == 'tube':
            a, b = T(part['a']), T(part['b']); d = (pr.depth(a) + pr.depth(b)) / 2
            pa, pb = pr(a), pr(b); w, c = part['w'], part['col']
            def f(C, pa=pa, pb=pb, w=w, c=c):
                C.stroke([pa, pb], w + 2 * OW, INK); C.stroke([pa, pb], w, c)
            out.append((d, part['lat'], f, part.get('tag')))
        elif part['kind'] == 'wheel':
            c = T(part['c']); e1 = norm(sub(T(add(part['c'], (1, 0, 0))), c)); e2 = norm(sub(T(add(part['c'], (0, 0, 1))), c))
            R, tw = part['R'], part['tw']
            tire = [pr(p) for p in _circle(c, R - tw / 2, e1, e2)]
            rim = [pr(p) for p in _circle(c, R - tw - 5, e1, e2)]
            hubc = pr(c); spokes = part['spokes']
            def f(C, tire=tire, rim=rim, hubc=hubc, tw=tw, spokes=spokes):
                L = lambda pts, w, col: C.d.line([(x * S, y * S) for x, y in pts + pts[:1]], fill=col, width=max(1, int(w * S)), joint='curve')
                if spokes:
                    for i in range(spokes):
                        q = rim[i * len(rim) // spokes]; C.d.line([(hubc[0] * S, hubc[1] * S), (q[0] * S, q[1] * S)], fill=(150, 154, 164), width=int(2.2 * S))
                else:                                                   # motorbike: a solid dark wheel disc + bright rim
                    C.d.polygon([(x * S, y * S) for x, y in rim], fill=(70, 68, 78))
                L(tire, tw + 2 * OW, INK); L(tire, tw, TIRE)
                L(rim, 6 if spokes else 9, RIM)
                r = (8 if spokes else 18); C.d.ellipse(((hubc[0] - r) * S, (hubc[1] - r) * S, (hubc[0] + r) * S, (hubc[1] + r) * S), fill=RIM, outline=INK, width=int(2.4 * S))
            out.append((pr.depth(c), 0, f, None))
        elif part['kind'] == 'prism':
            c0 = [T((x, part['y0'], z)) for x, z in part['poly']]; c1 = [T((x, part['y1'], z)) for x, z in part['poly']]
            d0 = sum(pr.depth(p) for p in c0) / len(c0); d1 = sum(pr.depth(p) for p in c1) / len(c1)
            near = c0 if d0 < d1 else c1
            hull = _hull([pr(p) for p in c0 + c1]); face = [pr(p) for p in near]
            col = part['col']
            def f(C, hull=hull, face=face, col=col):
                cx = sum(x for x, _ in hull) / len(hull); cy = sum(y for _, y in hull) / len(hull)
                fill_fast(C, hull, mul(col, (0.82, 0.82, 0.88)), (0.78, 0.78, 0.86), 6, 4)
                if _area(face) > 0.25 * _area(hull):
                    fill_fast(C, face, col, (0.78, 0.78, 0.86), 14, 8)
                    C.d.line([(x * S, y * S) for x, y in face + face[:1]], fill=mix(col, INK, 0.55), width=int(1.8 * S), joint='curve')
                C.outline(hull, cx, cy, 4.2)
            out.append(((d0 + d1) / 2, part['lat'], f, None))
        elif part['kind'] == 'quad':
            q3 = [T(p) for p in part['pts']]; poly = [pr(p) for p in q3]; col = part['col']; marks = part['marks']
            def f(C, poly=poly, col=col, marks=marks):
                if _area(poly) < 40: C.d.line([(x * S, y * S) for x, y in poly + poly[:1]], fill=INK, width=int(4 * S)); return
                C.d.polygon([(x * S, y * S) for x, y in poly], fill=col); C.d.line([(x * S, y * S) for x, y in poly + poly[:1]], fill=INK, width=int(3.4 * S), joint='curve')
                if marks:                                  # plate lettering as chunky dashes
                    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = poly
                    for k in range(4):
                        t0, t1 = 0.14 + k * 0.19, 0.27 + k * 0.19
                        a = (x0 + (x1 - x0) * t0, (y0 + y3) / 2 + (y1 - y0) * t0); b = (x0 + (x1 - x0) * t1, (y0 + y3) / 2 + (y1 - y0) * t1)
                        C.d.line([(a[0] * S, a[1] * S), (b[0] * S, b[1] * S)], fill=INK, width=int(7 * S))
            out.append((sum(pr.depth(p) for p in q3) / 4, part['lat'], f, None))
        elif part['kind'] == 'disc':
            c = T(part['c']); n = norm(sub(T(add(part['c'], part['n'])), c))
            e1 = norm(cross(n, (0, 0, 1))) if abs(n[2]) < 0.9 else (1, 0, 0); e2 = cross(n, e1)
            poly = [pr(p) for p in _circle(c, part['r'], e1, e2, 40)]; col = part['col']; glow = part['glow']
            def f(C, poly=poly, col=col):
                if _area(poly) < 30:                       # edge-on: a short lens in its colour, not a bare ink line
                    xs = [x for x, _ in poly]; ys = [y for _, y in poly]; c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
                    hh = max(max(ys) - min(ys), max(xs) - min(xs)) / 2; vert = (max(ys) - min(ys)) >= (max(xs) - min(xs))
                    seg = [(c[0], c[1] - hh), (c[0], c[1] + hh)] if vert else [(c[0] - hh, c[1]), (c[0] + hh, c[1])]
                    C.stroke(seg, 9 + 2 * OW, INK); C.stroke(seg, 9, col); return
                C.d.polygon([(x * S, y * S) for x, y in poly], fill=col); C.d.line([(x * S, y * S) for x, y in poly + poly[:1]], fill=INK, width=int(3.4 * S), joint='curve')
            out.append((pr.depth(c), part['lat'], f, None))
    return out

def anchors(A, pr, steer, lean, crank=0.0, hold='steer'):
    """Projected rider contact points: seat, grips, feet, plus the screen tilt of the bike's up axis."""
    T = lambda p, g='frame': pose_point(p, g, A, steer, lean)
    out = dict(seat=pr(T(add(A['seat'], (0, 0, A.get('hip_up', 6))))), seat_depth=pr.depth(T(A['seat'])))
    gs = A['fixed_grips'] if hold == 'fixed' and 'fixed_grips' in A else A['grips']
    grp = 'frame' if gs is A.get('fixed_grips') else 'steer'
    out['grips'] = {k: pr(T(p, grp)) for k, p in gs.items()}; out['grip_depth'] = {k: pr.depth(T(p, grp)) for k, p in gs.items()}
    if 'crank' in A:
        cr = A['crank']; bb = cr['bb']; out['feet'] = {}; out['foot_depth'] = {}
        for k, y, ph in (('R', -cr['y'] - 22, crank), ('L', cr['y'] + 22, crank + 180)):
            p = (bb[0] + cr['L'] * math.cos(math.radians(ph)), y, bb[2] + cr['L'] * math.sin(math.radians(ph)))
            out['feet'][k] = pr(T(p)); out['foot_depth'][k] = pr.depth(T(p))
    else:
        out['feet'] = {k: pr(T(p)) for k, p in A['pegs'].items()}; out['foot_depth'] = {k: pr.depth(T(p)) for k, p in A['pegs'].items()}
    o = pr(T((0, 0, 0))); t = pr(T((0, 0, 100)))
    out['tilt'] = math.degrees(math.atan2(t[0] - o[0], o[1] - t[1]))      # screen tilt of the bike's up axis, + = toward screen right
    return out

def crank_parts(A, pr, steer, lean, crank):
    """Cranks and pedals (bicycle) drawn as their own group: they always sit under the feet."""
    if 'crank' not in A: return []
    cr = A['crank']; bb = cr['bb']; out = []
    T = lambda p: pose_point(p, 'frame', A, steer, lean)
    for y, ph in ((-cr['y'], crank), (cr['y'], crank + 180)):
        a = T((bb[0], y, bb[2])); e3 = (bb[0] + cr['L'] * math.cos(math.radians(ph)), y, bb[2] + cr['L'] * math.sin(math.radians(ph)))
        b = T(e3); pa, pb = pr(a), pr(b)
        q0, q1 = pr(T((e3[0], y + (-26 if y < 0 else 26), e3[2]))), pr(T((e3[0], y + (-4 if y < 0 else 4), e3[2])))
        def f(C, pa=pa, pb=pb, q0=q0, q1=q1):
            C.stroke([pa, pb], 9 + 2 * OW, INK); C.stroke([pa, pb], 9, CHROME)
            C.stroke([q0, q1], 12 + 2 * OW, INK); C.stroke([q0, q1], 12, DARK)
        out.append((pr.depth(b), y, f, None))
    return out

def draw_bike(kind='bicycle', view='side', steer=0.0, lean=0.0, crank=0.0, color='#2f8fd8', fixed_color='#f2c230'):
    """The bike alone (a prop): 1000x1000 RGBA, ground at y=975."""
    P, A = model(kind, color, fixed_color); pr = Proj(view, contacts=_contacts(P, A, 0, lean))
    C = Canvas.__new__(Canvas); C.im = Image.new('RGBA', (CW * S, CH * S), (0, 0, 0, 0)); C.d = ImageDraw.Draw(C.im)
    ds = build_drawables(P, A, pr, steer, lean) + crank_parts(A, pr, steer, lean, crank)
    for t in sorted(ds, key=lambda t: -t[0]): t[2](C)
    return C.im.resize((CW, CH), Image.LANCZOS)

# ----------------------------------------------------------------------------------- rider
RIDE_VIEW = {'side': ('side', 1), '3q': ('3q', 1), 'rear': ('rear', 1), 'front': ('front', 1)}

def ride(char, bike='bicycle', view='rear', steer=0.0, lean=0.0, body_lean=0.0, bike_lean=None, crank=30.0,
         hold='steer', knee_out=False, color='#2f8fd8', fixed_color='#f2c230', expr=None, mouth=None, blink=False,
         sticker=None, cam_shift=(0, 0)):
    """A bean character riding a bike. char: character() keyword dict (build, skin, shirt, pants, hat, ...).
       lean: rider and bike together (+ = to the bike's right); bike_lean / body_lean: separate (the body leans
       relative to the bike, about the hips). steer: + turns the front wheel to the bike's right.
       hold: 'steer' grips the steering bar, 'fixed' grips the nobs_bike's fixed bar. crank: pedal angle (bicycle).
       Returns a 1000x1000 RGBA card with the ground at y=975."""
    bl = lean if bike_lean is None else bike_lean
    Bd = BUILDS[char.get('build', 'adult')]; HHb = 2 * Bd['b']; ub = 2 * Bd['a'] / 100
    hip_y = 975 - HHb * (Bd['legs']) - 0.12 * HHb * 0 ; leg = (975 - 3.75 * ub - ((975 - HHb * (1 + Bd['torso'] + Bd['legs'])) + 2 * Bd['b'] + Bd['torso'] * HHb - 0.12 * HHb))
    P, A = model(bike, color, fixed_color, leg - 0.1 * HHb); A['hip_up'] = 0.1 * HHb; pr = Proj(view, cam_shift, _contacts(P, A, steer, bl))
    an = anchors(A, pr, steer, bl, crank, hold)
    ds = build_drawables(P, A, pr, steer, bl); cranks = crank_parts(A, pr, steer, bl, crank)
    kw = dict(char); kw.pop('arm_pose', None); kw.pop('view', None); kw.pop('facing', None); kw.pop('prop', None)
    if expr: kw['expr'] = expr
    PAD = (CW - 600) // 2; OX = 0                                       # the rider card is padded to the bike canvas width
    rc = lambda p: (p[0] - OX, p[1])
    B = BUILDS[kw.get('build', 'adult')]; u = 2 * B['a'] / 100
    C = Canvas.__new__(Canvas); C.im = Image.new('RGBA', (CW * S, CH * S), (0, 0, 0, 0)); C.d = ImageDraw.Draw(C.im)
    def paste(img): C.im.alpha_composite(img); C.d = ImageDraw.Draw(C.im)
    def draw_list(lst): [t[2](C) for t in sorted(lst, key=lambda t: -t[0])]

    if view == 'top':
        draw_list(ds + cranks); _top_rider(C, kw, an, A, pr, steer, bl, body_lean, sticker)
        return C.im.resize((CW, CH), Image.LANCZOS)

    rv, fac = RIDE_VIEW[view]
    # which bike side is N (near / screen-right) for the rider rig
    if view in ('side', '3q'): N, F = 'R', 'L'
    elif view == 'rear': N, F = 'R', 'L'
    else: N, F = 'L', 'R'
    seat = an['seat']; g, ft = an['grips'], an['feet']
    if rv in ('side', '3q'):
        foot_off = (-8 * u, -6 * u)
        pose = dict(hip=rc(seat), handN=rc(g[N]), handF=rc(g[F]),
                    footN=rc((ft[N][0] + foot_off[0], ft[N][1] + foot_off[1])), footF=rc((ft[F][0] + foot_off[0], ft[F][1] + foot_off[1])),
                    lean=A['tilt_fwd'] + (0.35 * body_lean if view == '3q' else 0), tilt=-A['tilt_fwd'] * 0.5)
    else:
        tilt_total = an['tilt'] + body_lean
        pose = dict(hip=rc(seat), handN=rc(g[N]), handF=rc(g[F]),
                    footN=rc((ft[N][0], ft[N][1] - 6 * u)), footF=rc((ft[F][0], ft[F][1] - 6 * u)),
                    lean=tilt_total, tilt=-0.4 * tilt_total, knee_out=True, arms_front=(view == 'front'), arm_reach=1.35)
        if knee_out:                                                       # the inside knee pokes out into the turn
            side_in = N if (tilt_total > 0) == (view == 'rear') else F
            pose['knee_out_' + ('N' if side_in == N else 'F')] = True
    L = {}
    turned(view=rv, facing=fac, pose=pose, layers=L, mouth=mouth, blink=blink, sticker=sticker, pad=PAD, **kw)

    if view in ('side', '3q'):          # lateral layering: far side | far limbs | centre | near side | near leg | body | near arm
        bars = [t for t in ds if t[3] in ('bar', 'grip')]; rest = [t for t in ds if t[3] not in ('bar', 'grip')]
        far = [t for t in rest if t[1] > 8]; mid = [t for t in rest if -8 <= t[1] <= 8]; near = [t for t in rest if t[1] < -8]
        draw_list(far + [c for c in cranks if c[1] > 0]); paste(L['far'])
        draw_list(mid); draw_list(near + [c for c in cranks if c[1] < 0])
        paste(L['legs']); paste(L['upper']); draw_list(bars); paste(L['near'])
    else:                               # depth layering around the rider (rear: camera behind; front: camera ahead)
        dR = an['seat_depth']
        back = [t for t in ds if t[0] > dR + 25]; front = [t for t in ds if t[0] <= dR + 25]
        if view == 'rear':
            draw_list(back); paste(L['far']); draw_list(cranks); paste(L['legs']); paste(L['upper']); draw_list(front); paste(L['near'])
        else:
            back2 = [t for t in ds if t[0] > dR - 25]; front2 = [t for t in ds if t[0] <= dR - 25]
            draw_list(back2); paste(L['far']); draw_list(cranks); paste(L['legs']); paste(L['upper']); draw_list(front2); paste(L['near'])
    return C.im.resize((CW, CH), Image.LANCZOS)

def _top_rider(C, kw, an, A, pr, steer, lean, body_lean, sticker):
    """Seen from above: shoulders bean, arms to the grips, head (or helmet) on top."""
    from bean import hexrgb as hx_, SH_CLOTH, mul as mul_
    B = BUILDS[kw.get('build', 'adult')]; u = 2 * B['a'] / 100; a = B['a']
    sx, sy = an['seat']; shift = math.sin(math.radians(lean + body_lean)) * 120     # a leaning body slides sideways from above
    hip = (sx + shift * 0.4, sy); sh = (sx + shift, sy - 60)
    shirt = hx_(kw.get('shirt', '#f08a2c')); armc = mix(shirt, INK, 0.5)
    for k in ('L', 'R'):
        gx, gy = an['grips'][k]; side = 1 if gx > sh[0] else -1
        root = (sh[0] + side * 60, sh[1]); C.stroke([root, ((root[0] + gx) / 2 + side * 10, (root[1] + gy) / 2), (gx, gy)], 5.2 * u, armc); C.dot(gx, gy, 5.5 * u)
    from bean import blob
    body = blob(sh[0], sh[1] + 20, 0.42 * 2 * a, 0.26 * 2 * a, nTop=2.2, nBot=2.4, egg=0, seed=3, noise=0.004)
    C.fill_shaded(body, shirt, SH_CLOTH, 20, 10, sh[0], sh[1]); C.outline(body, sh[0], sh[1], 5 * u)
    hat = kw.get('hat'); hc = hx_(kw.get('hat_col', '#e2453c')) if hat else hx_(kw.get('skin', '#ffe2c2'))
    head = blob(sh[0], sh[1] - 4, 0.95 * a, 0.95 * a, nTop=2, nBot=2, egg=0, seed=5, noise=0.004)
    C.fill_shaded(head, hc, (0.86, 0.86, 0.9), 22, 12, sh[0], sh[1]); C.outline(head, sh[0], sh[1], 5 * u)
    if hat == 'helmet': C.d.line([(sh[0] * S, (sh[1] - 0.9 * a) * S), (sh[0] * S, (sh[1] + 0.85 * a) * S)], fill=mul_(hc, (0.72, 0.72, 0.78)), width=int(6 * u * S))

if __name__ == '__main__':
    draw_bike(*(sys.argv[2:4] if len(sys.argv) > 3 else ('bicycle', 'side'))).save(sys.argv[1] if len(sys.argv) > 1 else 'bike.png')

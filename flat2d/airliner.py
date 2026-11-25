"""The airliner kit (video 12, plane-windows): a de Havilland Comet 1 style jet airliner and a modern twinjet, built
as small 3D models for `persp.render` (any camera angle, real perspective), plus 2D close-up art of their windows.

The Comet (1952-54 look, no airline name or logo): a slim fuselage (3.05 m wide, 28.4 m long) with a rounded drooping
nose and a stepped cockpit (a raised brow over the windscreen), an upswept tail cone; a low swept wing whose thick
roots bury the four engines (two oval intakes per side in the leading edge, two round exhausts at the trailing
edge); a swept fin and tailplane; twelve SQUARISH cabin windows per side (rectangles with small corner radii) inside
a dark blue cheatline; a white top and a polished-metal belly.

The modern twinjet: a wider fuselage, a pointed nose, small ROUND-CORNERED (oval) windows, two engines in pods
under the wings, winglets.

Model axes: x from the nose (0) to the tail, y to the left wing (+y = the model's left side as seen from behind is
NOT used: +y is simply one side), z up; metres. `comet()` / `twinjet()` return a dict of Parts; `place(parts, R, t)`
moves them into the world; `clip_z` splits parts at a water line.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit
from kit import INK, layer
import persp as P3
from persp import Part, rot_x, rot_y, rot_z

WHITE = (240, 241, 243)
METAL = (176, 184, 196)
METAL_D = (140, 148, 162)
CHEAT = (30, 60, 128)
GLASS = (36, 52, 74)
GLASS_HI = (120, 156, 196)
FRAME = (206, 212, 220)
INTAKE = (26, 24, 32)

# ---------------------------------------------------------------- Comet geometry
CR = 1.52                      # fuselage radius (3.05 m)
CL = 28.4                      # length


def c_r(x, ph=math.pi / 2):
    """Comet fuselage radius at x (and at angle ph, 0 = side, pi/2 = top): elliptical drooping nose, the cockpit
    brow (a raised step over the windscreen), a straight cabin, an upswept tapering tail cone."""
    if x <= 0: return 0.0
    if x < 5.2:
        r = CR * (1 - (1 - x / 5.2) ** 2.0) ** .6
    elif x <= 20.0:
        r = CR
    else:
        s = min(1.0, (x - 20.0) / (CL - 20.0)); r = .2 + (CR - .2) * (1 - s ** 1.55)
    # stepped cockpit: a brow over the windscreen (top only)
    top = max(0.0, math.sin(ph)) ** 3
    brow = .055 * math.exp(-((x - 4.35) / .55) ** 2) - .045 * math.exp(-((x - 3.25) / .45) ** 2)
    return r * (1 + brow * top)


def c_zc(x):
    if x < 5.2: return -.32 * (1 - x / 5.2) ** 2
    if x <= 20.0: return 0.0
    s = min(1.0, (x - 20.0) / (CL - 20.0))
    return (CR - .24 * s) - c_r(x, math.pi / 2) if s > 0 else 0.0


def c_surf(x, ph, eps=0.0):
    r = c_r(x, ph) + eps; return (x, math.cos(ph) * r, c_zc(x) + math.sin(ph) * r)


def c_normal(x, ph):
    a = np.array(c_surf(x, ph)); b = np.array(c_surf(x + .05, ph)); c = np.array(c_surf(x, ph + .02))
    n = np.cross(c - a, b - a); n /= np.linalg.norm(n)          # outward
    return n


def _surface_poly(pts2d, side, eps=.012):
    """Map (x, arc-height above the centre line) 2D points onto the fuselage side (side +1 = +y, -1 = -y)."""
    out = []
    for x, h in pts2d:
        r = c_r(x, 0); zc = c_zc(x)
        ph = math.asin(max(-.99, min(.99, (h - zc) / max(.05, r))))
        X, Y, Z = c_surf(x, ph, eps); out.append((X, Y * side if side > 0 else -abs(Y), Z))
    return out


def comet(windows=True, hatch_x=None, crack=0.0, cabin_glow=0.0, livery=True, n=32, detail=1.0):
    """The Comet as Parts {'fus', 'wingL', 'wingR', 'fin', 'tailL', 'tailR'} (model axes). cabin_glow lights the
    windows (night/inside light). hatch_x: x of the window drawn as a hatch window (s07)."""
    parts = {}
    xs = [0.0, .08, .25, .5, .85, 1.3, 1.85, 2.5, 3.0, 3.4, 3.8, 4.2, 4.6, 5.2, 6.5, 8.0, 10, 12, 14, 16, 18, 20,
          21.2, 22.4, 23.6, 24.8, 26.0, 27.1, CL]

    def colf(x, ph):
        s = math.sin(ph)
        if not livery: return METAL
        if s > -.05: return WHITE
        return METAL if s > -.75 else METAL_D
    fus = Part('fus', spec=(30, .25), sil_w=5)
    P3.lathe(xs, lambda x, ph: c_r(x, ph), colf, n=n, part=fus, zc=c_zc, phase=math.pi / n)
    fus.poly([c_surf(CL, 2 * math.pi * i / n) for i in range(n)], METAL_D)                  # tail cap
    # cheatline (decal strips on both sides): from under the windscreen to the tail cone
    if livery:
        for side in (1, -1):
            xs2 = np.arange(1.6, CL - .5, .4)
            def band(x):
                if x < 5.2:
                    k = (5.2 - x) / 3.6; return -.05 - .34 * k, .56 - .52 * k ** 1.3
                if x > 20.0:
                    k = (x - 20.0) / (CL - 20.5); zc = c_zc(x); r = c_r(x, 0)
                    return zc - .05 + (.12 - .05) * k, zc + .56 * (1 - .7 * k) * min(1, r / .9)
                return -.05, .56
            for xa, xb in zip(xs2[:-1], xs2[1:]):
                (a0, a1), (b0, b1) = band(xa), band(xb)
                if a1 - a0 < .03: continue
                for j in range(3):
                    ha0 = a0 + (a1 - a0) * j / 3; ha1 = a0 + (a1 - a0) * (j + 1) / 3
                    hb0 = b0 + (b1 - b0) * j / 3; hb1 = b0 + (b1 - b0) * (j + 1) / 3
                    pts = _surface_poly([(xa, ha0), (xb, hb0), (xb, hb1), (xa, ha1)], side, .008)
                    if side < 0: pts = pts[::-1]
                    nrm = c_normal((xa + xb) / 2, math.asin(max(-.99, min(.99, (ha0 + ha1) / 2 / CR))))
                    if side < 0: nrm = nrm * np.array([1, -1, 1])
                    fus.decal(pts, CHEAT, normal=nrm)
    # windows: squarish (small corner radius), centred .27 m above the centre line
    WX = [6.1 + 1.02 * i for i in range(12)]
    if windows:
        for side in (1, -1):
            for x in WX:
                hatch = hatch_x is not None and abs(x - hatch_x) < .3
                for (w, h, r, col, ink) in (((.66, .58, .09, FRAME, False), (.56, .48, .06, GLASS, True)) if not hatch else
                                            ((.86, 1.06, .07, WHITE, 2), (.66, .58, .09, FRAME, False), (.56, .48, .06, GLASS, True))):
                    rr = P3.round_rect2d(w, h, r, 4)
                    pts = _surface_poly([(x + a, .27 + b) for a, b in rr], side, .016)
                    if side < 0: pts = pts[::-1]
                    nrm = c_normal(x, math.asin(.27 / CR)); nrm = nrm if side > 0 else nrm * np.array([1, -1, 1])
                    g = col
                    if col == GLASS and cabin_glow: g = P3.rgb_mix(GLASS, (255, 226, 160), cabin_glow)
                    fus.decal(pts, g, ink=ink, normal=nrm, emit=1.0 if (col == GLASS and cabin_glow) else 0.0)
                # glare stripe on the glass
                g2 = [(x - .17, .27 - .12), (x - .07, .27 - .12), (x + .1, .27 + .16), (x + .0, .27 + .16)]
                pts = _surface_poly(g2, side, .02)
                if side < 0: pts = pts[::-1]
                nrm = c_normal(x, math.asin(.27 / CR)); nrm = nrm if side > 0 else nrm * np.array([1, -1, 1])
                if not cabin_glow: fus.decal(pts, GLASS_HI, normal=nrm)
    # windscreen: front panes on the nose top + side panes (dark glass, ink)
    for side in (1, -1):
        for (x0, x1, p0, p1) in ((3.45, 4.3, 48, 82), (3.65, 4.4, 24, 46), (4.05, 4.55, 8, 22)):
            pts = []
            for k in range(5): pts.append(c_surf(x0 + (x1 - x0) * .08 * k / 4, math.radians(p0 + (p1 - p0) * k / 4), .02))
            for k in range(5): pts.append(c_surf(x1 - (x1 - x0) * .08 * k / 4, math.radians(p1 - (p1 - p0) * k / 4), .02))
            pts = [pts[0], *pts[1:5], *pts[5:]]
            quad = [c_surf(x0, math.radians(p0), .02), c_surf(x1, math.radians(p0 + 3), .02),
                    c_surf(x1 - .06, math.radians(p1), .02), c_surf(x0 + .05, math.radians(p1 - 2), .02)]
            if side < 0: quad = [(a, -b, c) for a, b, c in quad][::-1]
            nrm = c_normal((x0 + x1) / 2, math.radians((p0 + p1) / 2)); nrm = nrm if side > 0 else nrm * np.array([1, -1, 1])
            fus.decal(quad, GLASS, ink=2, normal=nrm)
    # roof ADF windows (two small ones on top, the real Comet had them)
    for x in (9.2, 9.9):
        rr = P3.round_rect2d(.36, .3, .05, 3)
        pts = [(x + a, b, c_zc(x) + c_r(x) + .015) for a, b in rr]
        fus.decal(pts, GLASS, ink=2, normal=(0, 0, 1))
    parts['fus'] = fus
    # ---- wings (engines buried in the roots)
    def wing(side):
        yR, yB, yT = 1.18, 3.9, 17.4
        def zw(y): return -.86 + (y - yR) * math.tan(math.radians(2.2))
        # section: (LE x, chord, thickness)
        secs = [(yR, 8.55, 9.25, 1.32), (2.3, 8.62, 9.05, 1.30), (yB, 9.75, 7.35, .86), (8.0, 11.55, 5.2, .52),
                (13.0, 13.8, 3.5, .34), (yT, 15.85, 2.25, .2)]
        foil = [(0, 0), (.05, .40), (.22, .55), (.55, .42), (1.0, .03), (.6, -.22), (.25, -.36), (.05, -.27)]
        blunt = [(0, .06), (.02, .44), (.22, .55), (.55, .42), (1.0, .03), (.6, -.22), (.25, -.36), (.02, -.34)]   # engine bay: a deep flat face for the intakes
        S = []
        for y, le, c, th in secs:
            S.append([(le + c * fx, side * y, zw(y) + th * fz) for fx, fz in (blunt if y < 3.95 else foil)])
        if side < 0: S = [s[::-1] for s in S]
        w = Part('wingR' if side > 0 else 'wingL', spec=(26, .18), sil_w=5)
        P3.loft(S, METAL, part=w)
        # intakes: two dark ovals per side in the thick root leading edge; exhausts at the trailing edge
        for yi in (1.78, 3.02):
            le = 8.55 + (9.75 - 8.55) * max(0, (yi - 2.3) / (3.9 - 2.3)) if yi > 2.3 else 8.58
            cz = zw(yi) + .1
            for rad, col in ((.5, (104, 110, 124)), (.4, INTAKE)):
                pts = []
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    pts.append((le - .015, side * (yi + rad * 1.15 * math.cos(a)), cz + rad * .52 * math.sin(a)))
                if side > 0: pts = pts[::-1]
                w.decal(pts, col, ink=1.5 if col == INTAKE else False, normal=(-1, 0, 0))
            te = 8.55 + 9.25 if yi < 2.3 else 9.75 + 7.35 + (8.62 + 9.05 - 17.1) * 0
            ex = 17.75 if yi < 2.5 else 17.25
            pts = []
            for k in range(14):
                a = 2 * math.pi * k / 14
                pts.append((ex + .03, side * (yi + .34 * math.cos(a)), zw(yi) + .02 + .3 * math.sin(a)))
            if side < 0: pts = pts[::-1]
            w.decal(pts, (54, 50, 56), ink=1.5, normal=(1, 0, 0))
        return w
    parts['wingR'] = wing(1); parts['wingL'] = wing(-1)
    # ---- fin
    zt = lambda x: c_zc(x) + c_r(x)
    fin_secs = [(22.2, 28.0 - 22.2, .34, zt(24.0) - .25), (24.6, 3.7, .22, 3.0), (26.0, 2.35, .12, 5.15)]
    foil = [(0, 0), (.1, .5), (.5, .45), (1.0, .05), (1.0, -.05), (.5, -.45), (.1, -.5)][::-1]
    S = [[(le + c * fx, th * fy, z) for fx, fy in foil] for le, c, th, z in fin_secs]
    fin = Part('fin', spec=(26, .2), sil_w=5)
    P3.loft(S, WHITE, part=fin)
    parts['fin'] = fin
    # ---- tailplane
    def tail(side):
        x0 = 24.3; zz = c_zc(25.5) + .05
        secs = [(.55, x0, 3.2, .3), (5.1, x0 + 2.35, 1.55, .12)]
        foil = [(0, 0), (.08, .45), (.4, .5), (1.0, .05), (.4, -.4), (.08, -.35)]
        S = [[(le + c * fx, side * y, zz + (y - .55) * math.tan(math.radians(6)) + th * fz) for fx, fz in foil]
             for y, le, c, th in secs]
        if side < 0: S = [s[::-1] for s in S]
        p = Part('tailR' if side > 0 else 'tailL', spec=(26, .2), sil_w=5)
        P3.loft(S, METAL, part=p); return p
    parts['tailR'] = tail(1); parts['tailL'] = tail(-1)
    return parts


COMET_WINDOWS_X = [6.1 + 1.02 * i for i in range(12)]


# ---------------------------------------------------------------- modern twinjet
MR = 1.98; ML = 37.6


def m_r(x, ph=math.pi / 2):
    if x <= 0: return 0.0
    if x < 6.2: return MR * (1 - (1 - x / 6.2) ** 2.3) ** .55
    if x <= 27.0: return MR
    s = min(1.0, (x - 27.0) / (ML - 27.0)); return .32 + (MR - .32) * (1 - s ** 1.5)


def m_zc(x):
    if x < 6.2: return -.28 * (1 - x / 6.2) ** 2
    if x <= 27.0: return 0.0
    s = min(1.0, (x - 27.0) / (ML - 27.0)); return (MR - .3 * s) - m_r(x)


def twinjet(windows=True, stripe=(40, 150, 170), n=32):
    """A generic modern twinjet (no airline): white, light-grey belly, a teal stripe, small oval windows,
    two engines in pods under the wings, winglets."""
    parts = {}
    xs = [0, .1, .3, .6, 1.0, 1.6, 2.4, 3.3, 4.3, 5.3, 6.2, 8, 11, 14, 17, 20, 23, 25, 27, 29, 31, 33, 35, 36.6, ML]

    def colf(x, ph):
        s = math.sin(ph)
        return WHITE if s > -.35 else (206, 212, 222)
    fus = Part('fus', spec=(30, .22), sil_w=5)
    P3.lathe(xs, m_r, colf, n=n, part=fus, zc=m_zc, phase=math.pi / n)
    fus.poly([(ML, math.cos(2 * math.pi * i / n) * m_r(ML), m_zc(ML) + math.sin(2 * math.pi * i / n) * m_r(ML))
              for i in range(n)], (190, 196, 206))
    def surf(x, h, side, eps=.014):
        r = m_r(x); zc = m_zc(x); ph = math.asin(max(-.99, min(.99, (h - zc) / max(.05, r))))
        return (x, side * math.cos(ph) * (r + eps), zc + math.sin(ph) * (r + eps))
    for side in (1, -1):
        # stripe under the windows
        for xa in np.arange(5.5, 33.5, .5):
            pts = [surf(xa, -.42, side, .008), surf(xa + .5, -.42, side, .008), surf(xa + .5, -.2, side, .008), surf(xa, -.2, side, .008)]
            if side < 0: pts = pts[::-1]
            fus.decal(pts, stripe, normal=(0, side, 0))
        if windows:
            for i in range(26):
                x = 7.4 + .76 * i
                if 11.4 < x < 12.4: continue           # over-wing exit gap
                for w, h, r, col, ink in ((.36, .46, .16, FRAME, False), (.27, .37, .12, GLASS, True)):
                    rr = P3.round_rect2d(w, h, r, 5)
                    pts = [surf(x + a, .32 + b, side) for a, b in rr]
                    if side < 0: pts = pts[::-1]
                    fus.decal(pts, col, ink=ink, normal=(0, side, 0))
        # cockpit
        quad = [surf(3.2, .55, side, .02), surf(4.05, .62, side, .02), surf(4.0, 1.0, side, .02), surf(3.35, .92, side, .02)]
        if side < 0: quad = quad[::-1]
        fus.decal(quad, GLASS, ink=2, normal=(0, side, .4))
    parts['fus'] = fus

    def wing(side):
        def zw(y): return -1.2 + (y - 1.6) * math.tan(math.radians(5))
        secs = [(1.6, 12.4, 6.6, .9), (6.0, 14.6, 4.4, .55), (16.5, 19.2, 1.7, .22)]
        foil = [(0, 0), (.05, .40), (.22, .55), (.55, .42), (1.0, .03), (.6, -.22), (.25, -.36), (.05, -.27)]
        S = [[(le + c * fx, side * y, zw(y) + th * fz) for fx, fz in foil] for y, le, c, th in secs]
        if side < 0: S = [s[::-1] for s in S]
        w = Part('wingR' if side > 0 else 'wingL', spec=(26, .16), sil_w=5)
        P3.loft(S, (214, 220, 228), part=w)
        # winglet: vertical, its sections in horizontal planes (thin in y)
        wf = [(0, 0), (.1, .5), (.5, .45), (1.0, .05), (1.0, -.05), (.5, -.45), (.1, -.5)][::-1]
        bot = [(19.25 + 1.6 * fx, side * (16.5 + .1 * fy), zw(16.5) + .05) for fx, fy in wf]
        top = [(20.5 + .75 * fx, side * (16.75 + .05 * fy), zw(16.5) + 1.95) for fx, fy in wf]
        if side < 0: bot, top = bot[::-1], top[::-1]
        P3.loft([bot, top], (214, 220, 228), part=w)
        return w
    parts['wingR'] = wing(1); parts['wingL'] = wing(-1)
    for side in (1, -1):
        e = Part('eng' + ('R' if side > 0 else 'L'), spec=(30, .3), sil_w=5)
        yc = side * 5.6; zc = -2.15
        P3.lathe([9.6, 9.75, 10.4, 12.2, 13.4, 13.9], lambda x: {9.6: .98, 9.75: 1.08, 10.4: 1.1, 12.2: 1.02, 13.4: .78, 13.9: .55}[round(x, 2)],
                 lambda x, ph: (226, 230, 236) if x < 12.5 else (150, 156, 168), n=20, part=e, zc=lambda x: zc, yc=lambda x: yc)
        pts = [(9.62, yc + .86 * math.cos(2 * math.pi * k / 20), zc + .86 * math.sin(2 * math.pi * k / 20)) for k in range(20)]
        e.poly(pts[::-1] if side > 0 else pts[::-1], (40, 40, 48), ink=2)
        # pylon
        P3.box((10.8, yc - .14, zc + .7), (13.6, yc + .14, -1.15), (206, 212, 220), ink=False, part=e)
        parts[e.name] = e
    fin_secs = [(29.5, 7.6, .4, m_zc(31) + m_r(31) - .3), (33.0, 4.2, .2, 4.6), (35.0, 2.6, .12, 7.4)]
    foil = [(0, 0), (.1, .5), (.5, .45), (1.0, .05), (1.0, -.05), (.5, -.45), (.1, -.5)][::-1]
    S = [[(le + c * fx, th * fy, z) for fx, fy in foil] for le, c, th, z in fin_secs]
    fin = Part('fin', spec=(26, .2), sil_w=5); P3.loft(S, WHITE, part=fin)
    parts['fin'] = fin
    for side in (1, -1):
        zz = m_zc(34) + .1
        secs = [(.6, 32.2, 3.6, .3), (6.2, 35.2, 1.6, .12)]
        foil = [(0, 0), (.08, .45), (.4, .5), (1.0, .05), (.4, -.4), (.08, -.35)]
        S = [[(le + c * fx, side * y, zz + (y - .6) * math.tan(math.radians(6)) + th * fz) for fx, fz in foil] for y, le, c, th in secs]
        if side < 0: S = [s[::-1] for s in S]
        p = Part('tail' + ('R' if side > 0 else 'L'), spec=(26, .2), sil_w=5); P3.loft(S, (214, 220, 228), part=p)
        parts[p.name] = p
    return parts


# ---------------------------------------------------------------- placing and clipping
def place(parts, R=None, t=(0, 0, 0), s=1.0):
    return {k: v.xform(R, t, s) for k, v in parts.items()}


def attitude(pitch=0.0, yaw=0.0, roll=0.0):
    """Rotation for a model: roll about x, pitch (nose up +, deg) about y, then yaw about z (deg)."""
    return rot_z(math.radians(yaw)) @ rot_y(math.radians(pitch)) @ rot_x(math.radians(roll))   # nose (x = 0) up for pitch > 0


def clip_part(p, n, d):
    """Split a Part by the plane n.x = d: returns (front: n.x >= d, back). Polygons are clipped; decals, lines and
    dots go wholly to the side of their centre."""
    n = np.asarray(n, float)
    A = Part(p.name + '+', p.sil, p.sil_w, p.spec, p.two, p.order, p.bias)
    B = Part(p.name + '-', p.sil, p.sil_w, p.spec, p.two, p.order, p.bias)
    def cl(Pts, sgn):
        out = []; k = len(Pts)
        for i in range(k):
            a, b = Pts[i], Pts[(i + 1) % k]; da, db = sgn * (a @ n - d), sgn * (b @ n - d)
            if da >= 0: out.append(a)
            if (da >= 0) != (db >= 0): out.append(a + (b - a) * (da / (da - db)))
        return np.array(out) if len(out) >= 3 else None
    for Pts, c, ink, e, tw in p.polys:
        s = Pts @ n - d
        if (s >= 0).all(): A.polys.append([Pts, c, ink, e, tw])
        elif (s <= 0).all(): B.polys.append([Pts, c, ink, e, tw])
        else:
            a = cl(Pts, 1); b = cl(Pts, -1)
            if a is not None: A.polys.append([a, c, ink, e, tw])
            if b is not None: B.polys.append([b, c, ink, e, tw])
    for x in p.decals: (A if x[0].mean(0) @ n >= d else B).decals.append(x)
    for x in p.lines: (A if x[0].mean(0) @ n >= d else B).lines.append(x)
    for x in p.dots: (A if x[0] @ n >= d else B).dots.append(x)
    return A, B


# ---------------------------------------------------------------- 2D close-up art
def skin_panel(w, h, seed=1, base=(184, 192, 204), rivet_step=46, frames=(), stringers=(), sheen=True):
    """Aluminium skin close-up (RGBA w x h): brushed tone variation, lap joints, rivet rows along the given frame
    x positions and stringer y positions."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 3), np.float32) + np.array(base, np.float32)
    yy = np.arange(h, dtype=np.float32)[:, None]; xx = np.arange(w, dtype=np.float32)[None, :]
    streak = np.repeat(rng.normal(0, 1, (1, w)).astype(np.float32), h, 0)
    a += (np.convolve(streak[0], np.ones(9) / 9, 'same')[None, :, None] * 4)
    if sheen:
        a += (np.exp(-((xx - w * .38) / (w * .28)) ** 2) * 18)[..., None] + (yy / h * -14)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(img)
    for x in frames:
        d.line([(x, 0), (x, h)], fill=(150, 158, 172), width=4)
        d.line([(x + 3, 0), (x + 3, h)], fill=(214, 220, 230), width=2)
        for y in range(rivet_step // 2, h, rivet_step):
            for xx_ in (x - 16, x + 18):
                d.ellipse([xx_ - 6, y - 6, xx_ + 6, y + 6], fill=(130, 138, 152)); d.ellipse([xx_ - 4, y - 5, xx_ + 3, y + 2], fill=(222, 228, 236))
    for y in stringers:
        d.line([(0, y), (w, y)], fill=(156, 164, 178), width=3)
        for x in range(rivet_step // 2, w, rivet_step):
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(130, 138, 152)); d.ellipse([x - 4, y - 5, x + 3, y + 2], fill=(222, 228, 236))
    return img


def window_shape(cx, cy, w, h, r):
    """Rounded-rect window outline in screen px (for close-ups): r small = squarish (Comet), big = modern."""
    return [(cx + x, cy + y) for x, y in P3.round_rect2d(w, h, r, 8)]


# ---------------------------------------------------------------- the modern cabin (3D set, axis x = forward, floor z = 0)
SEAT = (46, 84, 112)
SEAT_D = (36, 64, 88)
HEADREST = (236, 232, 222)
WALLC = (232, 226, 212)
BIN = (218, 214, 204)
CARPET = (74, 84, 112)
SEAT_Y = (-1.47, -.97, -.47, .47, .97, 1.47)
ROW_PITCH = .82


def cabin_shell(x0=-16.0, x1=3.0, sky=(176, 214, 246)):
    """Floor, sidewalls with windows (one per row), overhead bins, ceiling + light strips. Returns [Part]."""
    out = []
    fl = Part('c_floor', sil=False, order=-1e9)
    fl.poly([(x0, -1.8, 0), (x1, -1.8, 0), (x1, 1.8, 0), (x0, 1.8, 0)], CARPET)
    fl.decal([(x0, -.28, .005), (x1, -.28, .005), (x1, .28, .005), (x0, .28, .005)], (92, 100, 128), normal=(0, 0, 1))
    for x in np.arange(x0, x1, 2.0):
        fl.decal([(x, -.04, .006), (x + .8, -.04, .006), (x + .8, .04, .006), (x, .04, .006)], (206, 170, 90), normal=(0, 0, 1))
    out.append(fl)
    for side in (1, -1):
        w = Part('c_wall%d' % side, sil=False, order=-1e8 + 1)
        for k, x in enumerate(np.arange(x0, x1, ROW_PITCH)):
            xa, xb = x, x + ROW_PITCH
            prof = [(1.84, 0.0), (1.86, .35), (1.8, 1.1), (1.66, 1.62)]            # (|y|, z) up the wall
            for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
                pts = [(xa, side * ya, za), (xb, side * ya, za), (xb, side * yb, zb), (xa, side * yb, zb)]
                if side > 0: pts = pts[::-1]
                w.poly(pts, WALLC if za > .3 else (206, 200, 188))
            xc = (xa + xb) / 2; yw = 1.82
            for (ww, hh, rr, col, ink, em) in ((.42, .54, .17, (204, 198, 186), 1.5, 0), (.3, .4, .12, sky, 2, 1.0)):
                rr2 = P3.round_rect2d(ww, hh, rr, 5)
                pts = [(xc + a, side * (yw - .012 - (b + .2) * .05), 1.12 + b) for a, b in rr2]
                if side > 0: pts = pts[::-1]
                w.decal(pts, col, ink=ink, emit=em, normal=(0, -side, .1))
            pts = [(xc - .14, side * 1.78, 1.27), (xc + .14, side * 1.78, 1.27), (xc + .14, side * 1.78, 1.33), (xc - .14, side * 1.78, 1.33)]
            if side > 0: pts = pts[::-1]
            w.decal(pts, (226, 222, 214), normal=(0, -side, .1))                       # the pulled-up shade edge
        out.append(w)
        b = Part('c_bins%d' % side, sil=True, sil_w=2)
        P3.box((x0, side * 1.12 if side > 0 else -1.72, 1.62), (x1, 1.72 if side > 0 else -1.12, 2.02), BIN, ink=1.5, part=b,
               cols={'bottom': (176, 172, 164)})
        for x in np.arange(x0, x1, 1.64):
            b.line((x, side * 1.11, 1.64), (x, side * 1.11, 2.0), .012, (150, 146, 140), ink=False)
        out.append(b)
    ce = Part('c_ceiling', sil=False, order=-1e8 + 2)
    ce.poly([(x0, -1.12, 2.16), (x0, 1.12, 2.16), (x1, 1.12, 2.16), (x1, -1.12, 2.16)], (226, 222, 214))
    for side in (1, -1):
        ce.decal([(x0, side * 1.0, 2.15), (x1, side * 1.0, 2.15), (x1, side * 1.06, 2.15), (x0, side * 1.06, 2.15)][::(1 if side < 0 else -1)],
                 (255, 214, 170), emit=1.0, normal=(0, 0, -1))
    out.append(ce)
    return out


def seat_row(x, occupied=(), col=SEAT):
    """One row of six seats facing +x at row position x. Returns a Part."""
    p = Part('row%.2f' % x, sil=True, sil_w=2.5)
    for y in SEAT_Y:
        P3.box((x - .24, y - .22, .36), (x + .24, y + .22, .5), col, ink=1.2, part=p, cols={'top': P3.rgb_mul(col, 1.12)})
        # backrest (slightly reclined: top further back)
        bp = [(x - .3, y - .23, .48), (x - .18, y - .23, .48), (x - .28, y - .23, 1.16), (x - .4, y - .23, 1.16)]
        P3.prism([(0, 0), (.12, 0), (.1, .68), (-.02, .68)], -.23, .23, col, ink=1.2,
                 R=P3.rot_x(math.pi / 2), t=(x - .3, y, .48), part=p, side_col=P3.rgb_mul(col, .9))
        P3.box((x - .37, y - .19, .94), (x - .23, y + .19, 1.15), HEADREST, ink=1.0, part=p)
        for yy in (y - .235, y + .235):
            P3.box((x - .26, yy - .03, .5), (x + .2, yy + .03, .66), (70, 76, 86), ink=False, part=p)
    return p


# ---------------------------------------------------------------- 2D: a cabin window close-up (inside view)
def window_art(img, cx, cy, s, sky_fn, t=0.0, shade=.18, par=(0.0, 0.0), wall=WALLC, corner=None, frame_only=False,
               glare=True):
    """A modern cabin window seen from inside, centred at (cx, cy), scale s (1 = the opening 330 x 450 px):
    the warm sidewall panel, the moulded bezel with its deep reveal (shifted by `par` px for parallax), the pulled-up
    shade, the opening with the sky (sky_fn(layer, box)), glass glare and the breather hole. corner (0..1) highlights
    the round corner (a dashed circle that fits it). Returns the opening box."""
    w, h, r = 330 * s, 450 * s, 132 * s
    if not frame_only:
        d = ImageDraw.Draw(img)
    # bezel outer
    bw, bh, br = w * 1.55, h * 1.38, r * 1.9
    lay = layer(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2 + 10 * s, cx + bw / 2, cy + bh / 2 + 10 * s], br, fill=(150, 140, 126, 120))
    lay = kit.soft_layer(lay, 18 * s); img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], br, fill=(214, 208, 196), outline=INK, width=max(3, int(5 * s)))
    # reveal: from the bezel lip to the opening (deeper -> shifted by par)
    ox, oy = cx + par[0], cy + par[1]
    steps = 7
    for i in range(steps):
        f = i / (steps - 1)
        ww = bw * .9 + (w - bw * .9) * f; hh = bh * .9 + (h - bh * .9) * f; rr = br * .9 + (r - br * .9) * f
        xx = cx + (ox - cx) * f; yy = cy + (oy - cy) * f
        c = P3.rgb_mix((236, 232, 222), (170, 162, 150), f ** .8)
        d.rounded_rectangle([xx - ww / 2, yy - hh / 2, xx + ww / 2, yy + hh / 2], rr, fill=c)
    box = (ox - w / 2, oy - h / 2, ox + w / 2, oy + h / 2)
    sky = layer(); sky_fn(sky, box)
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    img.paste(sky, (0, 0), m)
    d = ImageDraw.Draw(img)
    # the shade (blind) pulled down a little from the top of the opening
    if shade > 0:
        sm = Image.new('L', img.size, 0); ImageDraw.Draw(sm).rectangle([box[0] - 4, box[1] - 4, box[2] + 4, box[1] + h * shade], fill=255)
        sm = ImageChops.multiply(sm, m.filter(ImageFilter.MaxFilter(3)))
        img.paste((226, 222, 212), (0, 0), sm)
        yb = box[1] + h * shade
        d.line([(box[0] + r * .25, yb), (box[2] - r * .25, yb)], fill=(150, 144, 134), width=max(3, int(8 * s)))
        d.rounded_rectangle([cx + par[0] - 26 * s, yb - 4 * s, cx + par[0] + 26 * s, yb + 12 * s], 6 * s, fill=(170, 164, 152))
    if glare:
        gl = layer(); dg = ImageDraw.Draw(gl)
        dg.polygon([(box[0] + w * .14, box[3] - h * .1), (box[0] + w * .3, box[3] - h * .1), (box[0] + w * .62, box[1] + h * .3),
                    (box[0] + w * .48, box[1] + h * .3)], fill=(255, 255, 255, 46))
        gl.putalpha(ImageChops.multiply(gl.split()[3], m)); img.alpha_composite(gl)
    d.rounded_rectangle(box, r, outline=INK, width=max(3, int(6 * s)))
    d.ellipse([ox - 5 * s, box[3] - 40 * s, ox + 5 * s, box[3] - 30 * s], fill=(60, 66, 80))         # breather hole
    return box


def squarish_window(img, cx, cy, w, h, r, skin=(232, 234, 238), sky_fn=None, frame=(206, 212, 220), rivets=True, ink=4):
    """A Comet-style squarish window seen from outside on the skin (close-ups): a riveted frame, small corner radii."""
    d = ImageDraw.Draw(img)
    fw, fh, fr = w * 1.34, h * 1.36, r * 1.6
    d.rounded_rectangle([cx - fw / 2, cy - fh / 2, cx + fw / 2, cy + fh / 2], fr, fill=frame, outline=INK, width=ink)
    if rivets:
        n = 7
        for i in range(n):
            for yy in (cy - fh / 2 + 12, cy + fh / 2 - 12):
                x = cx - fw / 2 + 16 + (fw - 32) * i / (n - 1); d.ellipse([x - 5, yy - 5, x + 5, yy + 5], fill=(150, 156, 168))
            for xx in (cx - fw / 2 + 12, cx + fw / 2 - 12):
                y = cy - fh / 2 + 16 + (fh - 32) * i / (n - 1); d.ellipse([xx - 5, y - 5, xx + 5, y + 5], fill=(150, 156, 168))
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    if sky_fn:
        sky = layer(); sky_fn(sky, box)
        m = Image.new('L', img.size, 0); ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255); img.paste(sky, (0, 0), m)
    else:
        d.rounded_rectangle(box, r, fill=GLASS)
        d.polygon([(box[0] + w * .15, box[3] - h * .12), (box[0] + w * .32, box[3] - h * .12), (box[0] + w * .66, box[1] + h * .18),
                   (box[0] + w * .49, box[1] + h * .18)], fill=GLASS_HI)
    d.rounded_rectangle(box, r, outline=INK, width=ink)
    return box

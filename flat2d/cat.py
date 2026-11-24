"""flat2d.cat: a flat 2D tabby cat built for the falling-cat explanation (video 8, cat-righting).

The cat is two halves joined at a bendy spine. Each half has its own ROLL about its own axis (0 = feet down,
pi = upside down) and is drawn from a tiny 3D model projected flat: the body is a chain of spheres (a deep chest,
a narrow waist, round haunches), the head a skull + cheek ruff + muzzle with two almond eyes, a nose, whiskers and
two ears on the dorsal side; the head always turns its face a little toward the camera, so the face reads upside
down and mid-twist. Tabby stripes follow the body rings, the belly/chest/muzzle are cream, the legs taper to paws.

render_cat(x, y, s, rot=0, bend=0, phf=pi, phb=pi, tuckf=.5, tuckb=.5, tail=True, ...) -> (layer, (x0, y0), info)
- x, y: the waist joint in frame px; s: px per cat unit (the body is ~2 units long, the head ~.65 wide);
- rot: screen angle of the spine (deg, 0 = head to the right); bend: the V at the waist (deg, + = both ends up);
- phf / phb: roll of the front / back half (rad); tuckf / tuckb: 0 = legs stretched wide, ~.4 = standing, 1 = tucked;
- tail: False = the tailless (Manx) cat (a short rounded rump); tail_ph: swing phase; glow: None or k (front blue,
  back orange halves); seam: ink line between the halves. info: 'head', 'rh', 'front', 'back', 'F', 'B', 'J', 'tf',
  'tb', 'masks': {'front', 'back'} L masks on the layer, 'origin'.
Rules: ink outline on every piece, far limbs darker, a form shadow away from the light and a warm rim toward it.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

INK = (22, 18, 24)
TABBY = (172, 136, 100)
TABBY_D = (78, 56, 42)
WHITE = (238, 222, 196)          # cream belly / chest / muzzle (not a stark white)
PINK = (226, 140, 140)
NOSE = (196, 112, 112)
EYE = (200, 206, 92)
FRONT_COL = (90, 170, 255)
BACK_COL = (255, 150, 60)


def _v(a): return (math.cos(a), math.sin(a))


def _add(p, *vs):
    x, y = p
    for k, v in vs: x += k * v[0]; y += k * v[1]
    return (x, y)


def _shade(c, k): return tuple(int(min(255, v * k)) for v in c)


def _lerp(a, b, k): return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# 3D helpers (screen x right, y down, z toward the camera)
def _v3(*cs):
    x = y = z = 0.0
    for k, v in cs: x += k * v[0]; y += k * v[1]; z += k * v[2]
    return (x, y, z)


def _norm(v):
    L = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1
    return (v[0] / L, v[1] / L, v[2] / L)


def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _limb(d, pts, w0, w1, col, ink, iw, cap=True, widths=None):
    """Tapered limb along pts, widths w0 -> w1 (or per-point widths), ink first then fill (round joints)."""
    n = len(pts)
    ws = widths or [w0 + (w1 - w0) * i / (n - 1) for i in range(n)]
    for c, grow in ((ink, iw), (col, 0)):
        if c is None: continue
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            ra, rb = ws[i] / 2 + grow, ws[i + 1] / 2 + grow
            d.polygon([(a[0] + nx * ra, a[1] + ny * ra), (b[0] + nx * rb, b[1] + ny * rb),
                       (b[0] - nx * rb, b[1] - ny * rb), (a[0] - nx * ra, a[1] - ny * ra)], fill=c)
            for p, r in ((a, ra), (b, rb)):
                d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=c)


def _smooth_pts(pts, k=4):
    """Catmull-Rom resample of a polyline (k points per span)."""
    if len(pts) < 3: return pts
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(k):
            t = j / k; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in range(2)))
    out.append(pts[-1])
    return out


def _interp(keys, x):
    """Piecewise-linear interpolation of tuples keyed by x (sorted list of (x, tuple))."""
    if x <= keys[0][0]: return keys[0][1]
    for (x0, a), (x1, b) in zip(keys, keys[1:]):
        if x <= x1:
            k = (x - x0) / (x1 - x0)
            return tuple(a[i] + (b[i] - a[i]) * k for i in range(len(a)))
    return keys[-1][1]


# body profiles: f (0 at the waist, 1 at the shoulder / rump) -> (dorsal radius, ventral radius) in cat units
PROF_F = [(0, (.18, .19)), (.35, (.2, .27)), (.68, (.23, .37)), (.88, (.24, .33)), (1.0, (.22, .26))]
PROF_B = [(0, (.18, .19)), (.4, (.21, .23)), (.72, (.265, .29)), (.9, (.255, .26)), (1.0, (.22, .2))]

# leg poses by tuck: (segment betas..., lengths...) in cat units; beta = angle from the belly direction toward +axis
LEG_F = [(0.0, (.62, .84, .9, .44, .44, .13)),       # stretched wide, reaching
         (0.4, (-.12, .08, .5, .42, .42, .13)),       # standing
         (1.0, (-1.0, 2.3, 2.0, .36, .34, .11))]       # tucked to the chest
LEG_B = [(0.0, (.55, .75, .85, .42, .4, .26)),
         (0.4, (-.6, .8, -.05, .42, .4, .25)),
         (1.0, (-1.25, 2.3, 1.1, .38, .34, .2))]


def render_cat(x, y, s, rot=0.0, bend=0.0, phf=math.pi, phb=math.pi, tuckf=.5, tuckb=.5, tail=True, tail_ph=0.0,
               glow=None, ink_w=None, light=(-.6, -.8), head_tilt=0.0, sepia=False, legs_k=1.0, paw_spread=0.0,
               fur=TABBY, fur_d=TABBY_D, belly=WHITE, eyes_closed=False, scale_front=1.0, seam=False):
    S = s
    iw = ink_w if ink_w is not None else max(2, int(S * .032))
    pad = int(S * 2.3)
    Wd = Hd = 2 * pad
    ox, oy = x - pad, y - pad
    J = (pad, pad)
    af = math.radians(rot - bend / 2); ab = math.radians(rot + bend / 2)
    tf, tb = _v(af), _v(ab)
    nf, nb = (-tf[1], tf[0]), (-tb[1], tb[0])
    Lf, Lb = .8 * S, .8 * S
    F = _add(J, (Lf, tf)); B = _add(J, (-Lb, tb))
    lay = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    mfront = Image.new('L', (Wd, Hd), 0); mback = Image.new('L', (Wd, Hd), 0)
    dmf, dmb = ImageDraw.Draw(mfront), ImageDraw.Draw(mback)
    fur_far = _shade(fur, .7)

    # ---------------- the halves as chains of spheres (screen circles)
    def chain(front):
        prof = PROF_F if front else PROF_B
        t = tf if front else (-tb[0], -tb[1])
        n = nf if front else nb
        phi = phf if front else phb
        L = Lf if front else Lb
        sc = scale_front if front else 1.0
        out = []
        for i in range(25):
            f = i / 24
            rd, rv = _interp(prof, f)
            rd, rv = rd * S * sc, rv * S * sc
            r = (rd + rv) / 2; o = (rv - rd) / 2
            c = _add(J, (L * f, t), (o * math.cos(phi), n))
            out.append((c, r, f))
        return out, t, n, phi

    CH = {True: chain(True), False: chain(False)}

    def circles(dr, ch, grow, col):
        for c, r, _ in ch:
            rr = r + grow
            dr.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=col)

    def half_fns(front):
        ch, t, n, phi = CH[front]
        mk = dmf if front else dmb
        def ink_fn():
            circles(d, ch, iw, INK)
        def fn():
            if seam: circles(d, ch, iw, INK)
            m = Image.new('L', (Wd, Hd), 0); circles(ImageDraw.Draw(m), ch, 0, 255)
            sub = Image.new('RGBA', (Wd, Hd), fur + (255,)); ds = ImageDraw.Draw(sub)
            # cream belly band (ventral side, centred on roll phi), soft edged
            bm = Image.new('L', (Wd, Hd), 0); db = ImageDraw.Draw(bm)
            half = 1.0 if front else .85
            for i in range(len(ch)):
                c, r, f = ch[i]
                hw = half + (.35 * max(0, f - .55) / .45 if front else 0)     # the chest bib widens toward the neck
                a0, a1 = max(phi - hw, 0.0), min(phi + hw, math.pi)
                segs = []
                for kk in (-1, 0, 1):
                    lo, hi = phi - hw + 2 * math.pi * kk, phi + hw + 2 * math.pi * kk
                    lo, hi = max(lo, 0.0), min(hi, math.pi)
                    if hi > lo: segs.append((lo, hi))
                for lo, hi in segs:
                    p1 = _add(c, (r * math.cos(lo), n)); p2 = _add(c, (r * math.cos(hi), n))
                    rr = S * .045
                    db.line([p1, p2], fill=255, width=int(S * .09))
            bm = bm.filter(ImageFilter.GaussianBlur(S * .03))
            sub.paste(Image.new('RGBA', (Wd, Hd), belly + (255,)), (0, 0), bm)
            # tabby stripes: rings over the dorsal side, tapered at the flanks, a dark spine line
            dors = phi + math.pi
            nst = 7
            for j in range(nst):
                f0 = .1 + j * (.82 / (nst - 1))
                idx = min(24, int(f0 * 24)); c, r, _ = ch[idx]
                c = _add(c, (S * .02 * math.sin(j * 1.7), t))
                lo, hi = dors - 1.25, dors + 1.25
                left, right = [], []
                for q in range(17):
                    a = lo + (hi - lo) * q / 16
                    if math.sin(a) <= -.05: continue
                    off = math.cos(a) * r
                    w = S * .036 * max(0.0, 1 - min(1.0, abs((a - dors) / 1.25)) ** 3) ** .6 + S * .003
                    bow = S * .07 * (1 - ((a - dors) / 1.25) ** 2) * (1 if front else -1)
                    p = _add(c, (off, n), (-bow, t))
                    left.append(_add(p, (w, t))); right.append(_add(p, (-w, t)))
                if len(left) > 1:
                    ds.polygon(left + right[::-1], fill=fur_d)
            if math.sin(dors) > -.2:                          # spine line
                k = max(0, min(1, (math.sin(dors) + .2) / .5))
                pts = [_add(c, (r * .97 * math.cos(dors), n)) for c, r, f in ch[2:23]]
                ds.line(pts, fill=_lerp(fur, fur_d, .8 * k), width=max(2, int(S * .06 * k + 1)), joint='curve')
            sub.putalpha(m)
            lay.alpha_composite(sub)
            mk.bitmap((0, 0), m, fill=255)
            circles(mk, ch, iw, 255)
        return ink_fn, fn

    # ---------------- legs
    items = []

    def leg(front, side):
        ch, t, n, phi = CH[front]
        keys = LEG_F if front else LEG_B
        tuck = tuckf if front else tuckb
        pose = _interp(keys, tuck)
        nseg = 3
        betas, lens = pose[:3], pose[3:]
        th = phi + side * .42                                  # attach angle on the cross-section
        cth, sth = math.cos(th), math.sin(th)
        fi = .78 if front else .74
        c, r, _ = ch[int(fi * 24)]
        hip = _add(c, (r * .62 * cth, n))
        spread = (1 - min(1, tuck / .4)) * (.35 + paw_spread) + .05
        pts = [hip]; zsum = 0
        for k_ in range(nseg):
            thl = th + side * (spread * (k_ + 1) / nseg)
            vn = math.cos(betas[k_]) * math.cos(thl); vz = math.cos(betas[k_]) * math.sin(thl)
            vt = math.sin(betas[k_])
            l = lens[k_] * S * legs_k
            p = pts[-1]
            pts.append((p[0] + vt * l * t[0] + vn * l * n[0], p[1] + vt * l * t[1] + vn * l * n[1]))
            zsum += vz
        depth = sth + .25 * zsum / nseg
        far = depth < 0
        col = fur_far if far else fur
        dk = _shade(fur_d, .8 if far else 1)
        lo = _shade(belly, .78 if far else 1)
        if front: widths = [S * .22, S * .13, S * .105, S * .1]
        else: widths = [S * .32, S * .17, S * .11, S * .1]
        def fn():
            mk = dmf if front else dmb
            _limb(d, pts, 0, 0, col, INK, iw, widths=widths)
            # stripes across the lower leg
            for a_, b_, fr in ((pts[1], pts[2], .35), (pts[1], pts[2], .7)):
                p = (a_[0] + (b_[0] - a_[0]) * fr, a_[1] + (b_[1] - a_[1]) * fr)
                dx, dy = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(dx, dy) or 1
                nx, ny = -dy / L_, dx / L_; w = widths[1] * .42
                d.line([(p[0] - nx * w, p[1] - ny * w), (p[0] + nx * w, p[1] + ny * w)], fill=dk, width=max(2, int(S * .035)))
            # paw: an oval along the last segment, cream, with two toe lines
            a_, b_ = pts[-2], pts[-1]
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(dx, dy) or 1
            ux, uy = dx / L_, dy / L_
            pc = (b_[0] + ux * S * .03, b_[1] + uy * S * .03)
            pl, pw = S * .085, S * .065
            def oval(g):
                return [(pc[0] + ux * (pl + g) * math.cos(q * math.pi / 10) - uy * (pw + g) * math.sin(q * math.pi / 10),
                         pc[1] + uy * (pl + g) * math.cos(q * math.pi / 10) + ux * (pw + g) * math.sin(q * math.pi / 10)) for q in range(20)]
            d.polygon(oval(iw), fill=INK); d.polygon(oval(0), fill=lo)
            for sgn in (-1, 1):
                q0 = (pc[0] + ux * pl * .2 - uy * sgn * pw * .35, pc[1] + uy * pl * .2 + ux * sgn * pw * .35)
                q1 = (pc[0] + ux * pl * .95 - uy * sgn * pw * .3, pc[1] + uy * pl * .95 + ux * sgn * pw * .3)
                d.line([q0, q1], fill=_shade(lo, .7), width=max(1, int(S * .015)))
            _limb(mk, pts, 0, 0, 255, None, 0, widths=[w_ + 2 * iw for w_ in widths])
            mk.polygon(oval(iw), fill=255)
        items.append((depth * 2.0 + (.01 if front else 0), fn))

    for side in (-1, 1):
        leg(True, side)
        leg(False, side)

    # ---------------- tail (or the Manx stub)
    def tail_fn():
        ch, t, n, phi = CH[False]
        c_end, r_end, _ = ch[22]
        base = _add(c_end, (-r_end * .55 * math.cos(phi), n))   # high on the rump (dorsal side)
        pts = [base]; zs = []
        p3 = [0.0, 0.0, 0.0]
        dors_n, dors_z = -math.cos(phi), -math.sin(phi)
        lat_n, lat_z = -math.sin(phi), math.cos(phi)
        for i in range(16):
            f = i / 15
            curl = .15 + 1.6 * f ** 1.3
            sw = .55 * math.sin(tail_ph + f * 2.4)
            dt = math.cos(curl)
            dn = math.sin(curl) * dors_n + sw * lat_n
            dz = math.sin(curl) * dors_z + sw * lat_z
            Lseg = S * .075
            p3 = [p3[0] + dt * Lseg, p3[1] + dn * Lseg, p3[2] + dz * Lseg]
            pts.append(_add(base, (p3[0], t), (p3[1], n))); zs.append(p3[2])
        z = sum(zs) / len(zs) / S
        sp = _smooth_pts(pts, 3)
        ws = [S * (.15 - .07 * (i / (len(sp) - 1))) for i in range(len(sp))]
        def fn():
            _limb(d, sp, 0, 0, fur, INK, iw, widths=ws)
            for j in range(5, len(sp) - 3, 6):
                a_, b_ = sp[j - 1], sp[j + 1]
                dx, dy = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(dx, dy) or 1
                nx, ny = -dy / L_, dx / L_; w = ws[j] * .46
                c = sp[j]
                d.line([(c[0] - nx * w, c[1] - ny * w), (c[0] + nx * w, c[1] + ny * w)], fill=fur_d, width=max(2, int(S * .05)))
            _limb(d, sp[-5:], 0, 0, fur_d, None, 0, widths=ws[-5:])          # dark tip
            _limb(dmb, sp, 0, 0, 255, None, 0, widths=[w + 2 * iw for w in ws])
        return z, fn

    # ---------------- head (a tiny 3D model, face turned toward the camera)
    phh = phf + head_tilt
    rh = S * .3 * scale_front
    T3 = (tf[0], tf[1], 0.0); N3 = (nf[0], nf[1], 0.0); Z3 = (0.0, 0.0, 1.0)
    D3 = _v3((math.cos(phh), N3), (math.sin(phh), Z3))              # chin / belly direction
    S3 = _v3((-math.sin(phh), N3), (math.cos(phh), Z3))
    Fh = _norm(_v3((.62, T3), (.78 * math.cos(phh), S3), (.45 * math.sin(phh) ** 2, D3)))
    U0 = (-D3[0], -D3[1], -D3[2])
    Uh = _norm(_v3((1, U0), (-_dot(U0, Fh), Fh)))
    Rh = _cross(Fh, Uh)
    Hc = _add(F, (S * .2, tf), (-S * .1 * math.cos(phh), nf))

    def P(*cs):
        v = _v3(*cs)
        return (Hc[0] + rh * v[0], Hc[1] + rh * v[1]), v[2]

    def disc(c3, r):
        p, z = P(*c3)
        return p, r * rh, z

    def head_parts():
        skull = disc(((1, (0, 0, 0)),), 1.0)
        cheeks = [disc(((.22, Fh), (.38, (-Uh[0], -Uh[1], -Uh[2])), (sg * .46, Rh)), .64) for sg in (-1, 1)]
        muzzle = disc(((.7, Fh), (.36, (-Uh[0], -Uh[1], -Uh[2]))), .42)
        return [skull] + cheeks + [muzzle]

    def ear(sg):
        cdir = _norm(_v3((.82, Uh), (sg * .55, Rh), (-.08, Fh)))
        tang = _norm(_v3((.55, Uh), (-sg * .82, Rh)))
        tipd = _norm(_v3((.9, Uh), (sg * .42, Rh), (.06, Fh)))
        b1, _ = P((.92, cdir), (.42, tang)); b2, _ = P((.92, cdir), (-.42, tang))
        tip, _ = P((.95, cdir), (.95, tipd))
        front_vis = _dot(Fh, Z3)
        cdz = _dot(cdir, Z3)
        def fn():
            cx = (b1[0] + b2[0] + tip[0]) / 3; cy = (b1[1] + b2[1] + tip[1]) / 3
            def grow(p, g):
                dx, dy = p[0] - cx, p[1] - cy; L_ = math.hypot(dx, dy) or 1
                return (p[0] + dx / L_ * g, p[1] + dy / L_ * g)
            d.polygon([grow(p, iw * 1.4) for p in (b1, tip, b2)], fill=INK)
            d.polygon([b1, tip, b2], fill=fur if cdz > -.3 else fur_far)
            if front_vis > -.1:
                ib1, _ = P((.92, cdir), (.24, tang), (.08, Fh)); ib2, _ = P((.92, cdir), (-.24, tang), (.08, Fh))
                it, _ = P((.95, cdir), (.6, tipd), (.06, Fh))
                d.polygon([ib1, it, ib2], fill=PINK)
                # ear tufts
                d.line([it, ((ib1[0] + ib2[0]) / 2, (ib1[1] + ib2[1]) / 2)], fill=_lerp(PINK, belly, .6), width=max(1, int(S * .012)))
            dmf.polygon([grow(p, iw * 1.4) for p in (b1, tip, b2)], fill=255)
        return fn

    def head_fn():
        parts = head_parts()
        for (c, r, z) in parts:
            rr = r + iw
            d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=INK)
        hm = Image.new('L', (Wd, Hd), 0); dhm = ImageDraw.Draw(hm)
        for (c, r, z) in parts:
            dhm.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
        sub = Image.new('RGBA', (Wd, Hd), fur + (255,)); ds = ImageDraw.Draw(sub)
        Dn = (-Uh[0], -Uh[1], -Uh[2])
        # cream muzzle pads + chin, cream throat
        for sg in (-1, 1):
            c, r, z = disc(((.86, Fh), (.4, Dn), (sg * .2, Rh)), .27)
            ds.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=belly)
        c, r, z = disc(((.62, Fh), (.66, Dn)), .26); ds.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=belly)
        c, r, z = disc(((.1, Fh), (.85, Dn)), .45); ds.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=_lerp(belly, fur, .15))
        # eye patches (lighter rings around the eyes)
        for sg in (-1, 1):
            c, r, z = disc(((.78, Fh), (.16, Uh), (sg * .44, Rh)), .26)
            if z > -.1: ds.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=_lerp(fur, belly, .45))
        # forehead 'M' and cheek stripes
        sw = max(2, int(S * .028))
        for k in (-1, 0, 1):
            a, za = P((.66, Fh), (.62, Uh), (k * .2, Rh))
            b, zb = P((.2, Fh), (.98, Uh), (k * .26, Rh))
            if za > -.2: ds.line([a, b], fill=fur_d, width=sw + (1 if k == 0 else 0))
        for sg in (-1, 1):
            for j in range(2):
                a, za = P((.35, Fh), (-.05 - j * .2, Uh), (sg * .8, Rh))
                b, zb = P((-.15, Fh), (-.1 - j * .24, Uh), (sg * .98, Rh))
                if za > -.1: ds.line([a, b], fill=fur_d, width=sw)
        sub.putalpha(hm)
        lay.alpha_composite(sub)
        # eyes: almond, on the face, a little above the muzzle
        for sg in (-1, 1):
            En = _norm(_v3((.8, Fh), (.17, Uh), (sg * .5, Rh)))
            if _dot(En, Z3) < .08: continue
            e1 = _norm(_v3((sg, Rh), (-_dot(_v3((sg, Rh)), En), En)))
            e1 = _norm(_v3((1, e1), (.22, Uh)))                      # outer corner tilts up
            e2 = _norm(_cross(En, e1))
            if _dot(e2, Uh) < 0: e2 = (-e2[0], -e2[1], -e2[2])
            a_, b_ = .25, .175
            pts = []
            for q in range(24):
                th = 2 * math.pi * q / 24
                ya = math.sin(th) * (abs(math.sin(th)) ** .25)
                pts.append(P((1.0, En), (a_ * math.cos(th), e1), (b_ * ya, e2))[0])
            if eyes_closed:
                lo_ = [P((1.0, En), (a_ * math.cos(th), e1), (-b_ * .2 * math.sin(th), e2))[0] for th in np.linspace(0, math.pi, 9)]
                d.line(lo_, fill=INK, width=max(2, int(S * .03)), joint='curve')
                continue
            d.polygon(pts, fill=INK)
            inner = [P((1.0, En), (a_ * .82 * math.cos(th), e1), (b_ * .78 * math.sin(th) * (abs(math.sin(th)) ** .25), e2))[0]
                     for th in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
            d.polygon(inner, fill=EYE)
            pup = [P((1.0, En), (.085 * math.cos(th), e1), (.15 * math.sin(th), e2))[0] for th in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
            d.polygon(pup, fill=INK)
            hl, _ = P((1.0, En), (-.07 * sg, e1), (.06, e2)); r = max(1.5, S * .022)
            d.ellipse([hl[0] - r, hl[1] - r, hl[0] + r, hl[1] + r], fill=(255, 255, 250))
            # upper lid
            lid = [P((1.0, En), (a_ * math.cos(th), e1), (b_ * math.sin(th) * (abs(math.sin(th)) ** .25), e2))[0] for th in np.linspace(0, math.pi, 10)]
            d.line(lid, fill=INK, width=max(2, int(S * .03)), joint='curve')
        # nose + mouth
        Nn = _norm(_v3((1.05, Fh), (.12, Dn)))
        if _dot(Nn, Z3) > -.3:
            nc = (1.06, Nn)
            tri = [P(nc, (-.11, Rh), (.06, Uh))[0], P(nc, (.11, Rh), (.06, Uh))[0], P(nc, (.08, Dn))[0]]
            d.polygon(tri, fill=NOSE, outline=INK, width=max(1, int(S * .014)))
            m0 = P(nc, (.08, Dn))[0]; m1 = P(nc, (.24, Dn), (-.05, Fh))[0]
            d.line([m0, m1], fill=INK, width=max(1, int(S * .016)))
            for sg in (-1, 1):
                m2 = P(nc, (.3, Dn), (sg * .13, Rh), (-.1, Fh))[0]
                d.line([m1, m2], fill=INK, width=max(1, int(S * .016)))
        # whiskers
        for sg in (-1, 1):
            for j in range(3):
                a, za = P((.92, Fh), (.38 + j * .05, Dn), (sg * .28, Rh))
                b, zb = P((1.1, Fh), (.2 + j * .22, Dn), (sg * 1.35, Rh))
                if za > -.2:
                    d.line([a, b], fill=(244, 238, 226), width=max(1, int(S * .01)))
        for (c, r, z) in parts:
            rr = r + iw
            dmf.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=255)

    # ---------------- draw order
    order = []
    for dep, fn in items:
        order.append((dep if dep >= 0 else dep - 3, fn))
    ib, fb = half_fns(False); ifr, ff = half_fns(True)
    if not seam:
        order.append((-.65, ib)); order.append((-.64, ifr))
    order.append((-.6, fb))
    order.append((-.5, ff))
    if tail:
        zt, tfn = tail_fn(); order.append(((-2.5 if zt < 0 else .4), tfn))
    for sg in (-1, 1):
        order.append((-.45 + .001 * sg, ear(sg)))
    order.append((-.3, head_fn))
    for dep, fn in sorted(order, key=lambda p: p[0]):
        fn()

    # ---------------- form shadow + rim (inner-shadow trick on the alpha)
    a = np.asarray(lay.split()[3], np.float32) / 255
    if a.max() > 0:
        lx, ly = light; sh = int(S * .09)
        A = Image.fromarray((a * 255).astype(np.uint8))
        A = A.filter(ImageFilter.MinFilter(2 * max(1, iw) + 1))       # shade/rim inside the ink line
        a_in = np.asarray(A, np.float32) / 255
        away = np.asarray(ImageChops.offset(A, int(-lx * sh), int(-ly * sh)).filter(ImageFilter.GaussianBlur(S * .05)), np.float32) / 255
        toward = np.asarray(ImageChops.offset(A, int(lx * sh * .45), int(ly * sh * .45)).filter(ImageFilter.GaussianBlur(S * .02)), np.float32) / 255
        arr = np.asarray(lay, np.float32).copy()
        shade = np.clip(a_in - away, 0, 1) * .34
        rim = np.clip(a_in - toward, 0, 1) * .55
        arr[..., :3] *= (1 - shade)[..., None]
        rimc = np.array((255, 238, 206), np.float32)
        arr[..., :3] = arr[..., :3] * (1 - rim[..., None]) + rimc * rim[..., None]
        lay = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')

    # ---------------- glowing halves
    if glow:
        k = float(glow) if not isinstance(glow, (tuple, list)) else glow[0]
        kf = k if not isinstance(glow, (tuple, list)) else glow[1]
        kb = k if not isinstance(glow, (tuple, list)) else glow[2]
        out = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
        for m, col, kk in ((mback, BACK_COL, kb), (mfront, FRONT_COL, kf)):
            if kk <= 0: continue
            mm = m.filter(ImageFilter.GaussianBlur(S * .16)).point(lambda v: int(min(255, v * 1.6 * kk)))
            out.paste(Image.new('RGBA', (Wd, Hd), col + (255,)), (0, 0), mm)
        out.alpha_composite(lay)
        arr = np.asarray(out, np.float32).copy()
        for m, col, kk in ((mback, BACK_COL, kb), (mfront, FRONT_COL, kf)):
            if kk <= 0: continue
            mm = np.asarray(m, np.float32)[..., None] / 255 * .5 * kk * (np.asarray(lay.split()[3], np.float32)[..., None] / 255)
            c = np.array(col, np.float32)
            arr[..., :3] = arr[..., :3] * (1 - mm) + (arr[..., :3] * .35 + c * .75).clip(0, 255) * mm
        lay = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')

    info = {'head': (Hc[0] + ox, Hc[1] + oy), 'rh': rh, 'J': (x, y),
            'front': ((J[0] + F[0]) / 2 + ox, (J[1] + F[1]) / 2 + oy), 'back': ((J[0] + B[0]) / 2 + ox, (J[1] + B[1]) / 2 + oy),
            'F': (F[0] + ox, F[1] + oy), 'B': (B[0] + ox, B[1] + oy), 'tf': tf, 'tb': tb, 'masks': {'front': mfront, 'back': mback},
            'origin': (ox, oy)}
    return lay, (int(ox), int(oy)), info


def put_cat(img, x, y, s, alpha=1.0, **kw):
    """Draw the cat onto img; returns info (frame px)."""
    lay, (ox, oy), info = render_cat(x, y, s, **kw)
    if alpha < 1:
        lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    _paste(img, lay, ox, oy)
    return info


def _paste(img, lay, ox, oy):
    """alpha_composite that tolerates layers partly off the frame."""
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(img.width, ox + lay.width), min(img.height, oy + lay.height)
    if x1 <= x0 or y1 <= y0: return
    img.alpha_composite(lay.crop((x0 - ox, y0 - oy, x1 - ox, y1 - oy)), (x0, y0))


# ---------------------------------------------------------------- the righting program
def _sm(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def righting(p, start=math.pi, end=0.0):
    """The cat's moves for progress p 0..1 (Kane & Scher, simplified as 'tuck and turn'):
    0.00-0.12  upside down, legs neutral, bending at the waist;
    0.12-0.22  front legs tuck in, back legs stretch out;
    0.22-0.50  the FRONT half turns ~195 deg (tucked: easy), the BACK half turns ~15 deg the other way;
    0.50-0.60  swap: back legs tuck, front legs stretch;
    0.60-0.88  the BACK half turns ~195 deg and catches up, the front turns ~15 deg back;
    0.88-1.00  both halves feet-down, the spine straightens, legs reach for the ground.
    Returns dict(phf, phb, tuckf, tuckb, bend)."""
    tot = start - end
    k1 = _sm((p - .22) / .28); k2 = _sm((p - .60) / .28)
    big, small = tot * 1.083, tot * .083
    phf = start - big * k1 + small * k2
    phb = start + small * k1 - big * k2
    t_a = _sm((p - .12) / .1); t_b = _sm((p - .5) / .1); t_c = _sm((p - .88) / .1)
    tuckf = .5 + .5 * t_a - 1.0 * t_b + .25 * t_c          # .5 -> 1 (tucked) -> 0 (stretched) -> .25 (reach)
    tuckb = .5 - .5 * t_a + 1.0 * t_b - .75 * t_c          # .5 -> 0 (stretched) -> 1 (tucked) -> .25
    bend = 34 * _sm(p / .12) * (1 - _sm((p - .86) / .12)) - 6 * _sm((p - .9) / .1)
    return dict(phf=phf, phb=phb, tuckf=tuckf, tuckb=tuckb, bend=bend)

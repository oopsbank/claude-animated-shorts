"""flat2d.cat: a flat 2D cat built for the falling-cat explanation (video 8, cat-righting).

The cat is two halves joined at a bendy spine. Each half is a fur "cylinder" seen from the side with its own ROLL
about its own axis (0 = feet down, pi = upside down). Roll is drawn honestly: the white belly band, the tabby
stripes, the legs (attached on the belly side, foreshortened when they point at the camera), the ears (dorsal side
of the head) and the eyes all move with it, so the silhouette reads upside down and mid-twist.

render_cat(x, y, s, rot=0, bend=0, phf=pi, phb=pi, tuckf=.5, tuckb=.5, tail=True, ...) -> (layer, (x0, y0), info)
- x, y: the waist joint in frame px; s: px per cat unit (the body is ~2.1 units long, the head ~.6 wide);
- rot: screen angle of the spine (deg, 0 = head to the right); bend: the V at the waist (deg, + = both ends up);
- phf / phb: roll of the front / back half (rad); tuckf / tuckb: 0 = legs stretched wide, 1 = tucked in;
- tail: False = the tailless (Manx) cat; tail_ph: swing phase; glow: None or k (front blue, back orange halves);
- sepia: True for film-strip frames (no glow, flat sepia palette later). info: 'head', 'front', 'back' (centres),
  'masks': {'front', 'back'} L masks on the layer, 'spine': [B, J, F].
Rules: ink outline on every piece, far limbs darker, a form shadow away from the light and a warm rim toward it.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

INK = (22, 18, 24)
TABBY = (164, 138, 112)
TABBY_D = (92, 70, 56)
WHITE = (246, 242, 234)
PINK = (236, 150, 150)
EYE = (196, 214, 86)
FRONT_COL = (90, 170, 255)
BACK_COL = (255, 150, 60)


def _v(a): return (math.cos(a), math.sin(a))


def _add(p, *vs):
    x, y = p
    for k, v in vs: x += k * v[0]; y += k * v[1]
    return (x, y)


def _shade(c, k): return tuple(int(v * k) for v in c)


def _limb(d, pts, w0, w1, col, ink, iw, cap=True):
    """Tapered limb along pts (2-4 points), widths w0 -> w1, ink first then fill (round joints)."""
    n = len(pts)
    for pass_, (c, grow) in enumerate(((ink, iw), (col, 0))):
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]
            wa = w0 + (w1 - w0) * i / (n - 1); wb = w0 + (w1 - w0) * (i + 1) / (n - 1)
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            ra, rb = wa / 2 + grow, wb / 2 + grow
            d.polygon([(a[0] + nx * ra, a[1] + ny * ra), (b[0] + nx * rb, b[1] + ny * rb),
                       (b[0] - nx * rb, b[1] - ny * rb), (a[0] - nx * ra, a[1] - ny * ra)], fill=c)
            for p, r in ((a, ra), (b, rb)):
                d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=c)


def _sausage(J, t, n, L, prof, k=14):
    """Outline of a body half from J along t (length L) with radius profile prof(f) (f 0 at J, 1 at the end)."""
    left, right = [], []
    for i in range(k + 1):
        f = i / k; c = _add(J, (L * f, t)); r = prof(f)
        left.append(_add(c, (r, n))); right.append(_add(c, (-r, n)))
    # rounded caps
    end = _add(J, (L, t)); r1 = prof(1.0); cap1 = []
    for i in range(1, 8):
        a = math.pi * i / 8
        cap1.append(_add(end, (r1 * math.cos(a), n), (r1 * math.sin(a) * .9, t)))
    r0 = prof(0.0); cap0 = []
    for i in range(1, 8):
        a = math.pi * i / 8
        cap0.append(_add(J, (-r0 * math.cos(a), n), (-r0 * math.sin(a) * .7, t)))
    return left + cap1 + right[::-1] + cap0, (left, right)


def _intervals(phi, half=1.2):
    """Visible screen-offset intervals (cos theta, along n) of the belly band centred on roll phi (+-half rad)."""
    out = []
    lo, hi = phi - half, phi + half
    for k in (-1, 0, 1):
        a, b = max(lo + 2 * math.pi * k, 0.0), min(hi + 2 * math.pi * k, math.pi)
        if b > a: out.append((math.cos(b), math.cos(a)))
    return out


def render_cat(x, y, s, rot=0.0, bend=0.0, phf=math.pi, phb=math.pi, tuckf=.5, tuckb=.5, tail=True, tail_ph=0.0,
               glow=None, ink_w=None, light=(-.6, -.8), head_tilt=0.0, sepia=False, legs_k=1.0, paw_spread=0.0,
               fur=TABBY, fur_d=TABBY_D, belly=WHITE, eyes_closed=False, scale_front=1.0, seam=False):
    S = s
    iw = ink_w if ink_w is not None else max(2, int(S * .028))
    pad = int(S * 2.3)
    Wd = Hd = 2 * pad
    ox, oy = x - pad, y - pad
    J = (pad, pad)
    af = math.radians(rot - bend / 2); ab = math.radians(rot + bend / 2)
    tf, tb = _v(af), _v(ab)
    nf, nb = (-tf[1], tf[0]), (-tb[1], tb[0])
    Lf, Lb = .9 * S, .9 * S
    F = _add(J, (Lf, tf)); B = _add(J, (-Lb, tb))
    lay = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    mfront = Image.new('L', (Wd, Hd), 0); mback = Image.new('L', (Wd, Hd), 0)
    dmf, dmb = ImageDraw.Draw(mfront), ImageDraw.Draw(mback)

    prof_f = lambda f: S * (.28 + .08 * math.sin(min(1, f * 1.15) * math.pi * .85) - .05 * max(0, f - .8) / .2) * scale_front
    prof_b = lambda f: S * (.27 + .09 * math.sin(min(1, f * 1.1) * math.pi * .8))

    items = []          # (depth, fn)

    # ---------------- legs
    def leg(J0, t, n, phi, side, front, tuck, which):
        th = phi + side * .5                                  # attach angle on the cross-section
        cth, sth = math.cos(th), math.sin(th)
        L = Lf if front else Lb
        r = (prof_f if front else prof_b)(.72)
        hip = _add(J0, ((.68 if front else .74) * L, t), (r * .78 * cth, n))
        # beta: angle from the belly direction toward +t (head); per segment, stretched -> tucked
        # t points away from the waist for both halves: + beta = toward the head (front) / the tail (back)
        b1 = (1 - tuck) * .62 + tuck * (-.95); b2 = (1 - tuck) * .84 + tuck * 2.35
        l1 = S * (.5 * (1 - tuck) + .30 * tuck); l2 = S * (.52 * (1 - tuck) + .30 * tuck)
        l1 *= legs_k; l2 *= legs_k
        spread = (1 - tuck) * (.35 + paw_spread)              # stretched legs splay sideways too
        def proj(beta, l, extra=0.0):
            # 3D dir: cos(beta) * belly(th + side*spread) + sin(beta) * t
            thl = th + side * (spread + extra)
            vn, vz = math.cos(beta) * math.cos(thl), math.cos(beta) * math.sin(thl)
            vt = math.sin(beta)
            return (vt * l * t[0] + vn * l * n[0], vt * l * t[1] + vn * l * n[1]), vz
        v1, z1 = proj(b1, l1); v2, z2 = proj(b2, l2, .1)
        knee = (hip[0] + v1[0], hip[1] + v1[1]); paw = (knee[0] + v2[0], knee[1] + v2[1])
        depth = sth + .3 * (z1 + z2) / 2
        far = depth < 0
        k = .72 if far else 1.0
        up = _shade(fur, k); lo = _shade(belly, k * (.96 if far else 1))
        w0 = S * (.19 if front else .25); w1 = S * .1
        def fn(dr=d, mk=(dmf if front else dmb)):
            _limb(dr, [hip, knee, paw], w0, w1, up, INK, iw)
            sock = (knee[0] + (paw[0] - knee[0]) * .55, knee[1] + (paw[1] - knee[1]) * .55)
            _limb(dr, [sock, paw], w1 * 1.02, w1, lo, lo, 0)
            pr = S * .075
            dx, dy = paw[0] - knee[0], paw[1] - knee[1]; L_ = math.hypot(dx, dy) or 1
            pc = (paw[0] + dx / L_ * pr * .4, paw[1] + dy / L_ * pr * .4)
            for c, g in ((INK, iw), (lo, 0)):
                dr.ellipse([pc[0] - pr - g, pc[1] - pr - g, pc[0] + pr + g, pc[1] + pr + g], fill=c)
            _limb(mk, [hip, knee, paw], w0 + 2 * iw, w1 + 2 * iw, 255, 255, 0)
            mk.ellipse([pc[0] - pr - iw, pc[1] - pr - iw, pc[0] + pr + iw, pc[1] + pr + iw], fill=255)
        items.append((depth * 2.0 + (.01 if front else 0), fn))

    items.clear()
    tbr = (-tb[0], -tb[1]); nbr = (-nb[0], -nb[1])
    for side in (-1, 1):
        leg(J, tf, nf, phf, side, True, tuckf, 'f')
    nfront = len(items)
    # hind legs: reversed axis; flip roll so that belly stays on the same screen side (n -> -n means phi -> pi - phi)
    for side in (-1, 1):
        leg(J, tbr, nbr, math.pi - phb, -side, False, tuckb, 'b')

    # ---------------- body halves
    def half(front):
        t = tf if front else tbr; n = nf if front else nbr
        prof = prof_f if front else prof_b
        phi = phf if front else (math.pi - phb)
        outline, (Lft, Rgt) = _sausage(J, t, n, Lf if front else Lb, prof)
        ink_out, _ = _sausage(J, t, n, Lf if front else Lb, lambda f: prof(f) + iw)
        def ink_fn():
            d.polygon(ink_out, fill=INK)
        def fn():
            if seam: d.polygon(ink_out, fill=INK)
            sub = Image.new('RGBA', (Wd, Hd), fur + (255,)); ds = ImageDraw.Draw(sub)
            k = 16; L = Lf if front else Lb
            # stripes: dorsal centre at phi + pi; visible where sin > 0
            dors = phi + math.pi
            for j in range(6 if front else 6):
                f = .14 + j * .145
                if f > 1.0: break
                c = _add(J, (L * f, t)); r = prof(min(1, f))
                a0, a1 = dors - 1.05, dors + 1.05
                pts = []
                for q in range(13):
                    a = a0 + (a1 - a0) * q / 12
                    if math.sin(a) <= 0.02: continue
                    off = math.cos(a) * r
                    wav = S * .035 * math.sin(a * 3 + j)
                    pts.append(_add(c, (off, n), (wav, t)))
                if len(pts) > 1:
                    ds.line(pts, fill=fur_d, width=max(2, int(S * .075)), joint='curve')
            # white belly band
            for lo, hi in _intervals(phi, 1.45):
                poly = []
                for i in range(k + 1):
                    f = i / k; c = _add(J, (L * f, t)); r = prof(f) * 1.08
                    poly.append(_add(c, (hi * r, n)))
                for i in range(k, -1, -1):
                    f = i / k; c = _add(J, (L * f, t)); r = prof(f) * 1.08
                    poly.append(_add(c, (lo * r, n)))
                ds.polygon(poly, fill=belly)
            m = Image.new('L', (Wd, Hd), 0); ImageDraw.Draw(m).polygon(outline, fill=255)
            sub.putalpha(m)
            lay.alpha_composite(sub)
            (dmf if front else dmb).polygon(ink_out, fill=255)
        return ink_fn, fn

    # ---------------- tail
    def tail_fn():
        phi = math.pi - phb
        base = _add(B, (S * .05, tbr), (0, nbr))
        pts = []; zs = []
        p3 = [0.0, 0.0, 0.0]                                    # (t, n, z) in the reversed back frame
        ang = 0.0
        for i in range(14):
            f = i / 13
            # direction: along the axis, curling toward the dorsal side, swinging sideways
            curl = .2 + 1.5 * f
            dors_n, dors_z = -math.cos(phi), -math.sin(phi)
            sw = .5 * math.sin(tail_ph + f * 2.2)
            lat_n, lat_z = -math.sin(phi), math.cos(phi)      # lateral (left side) direction
            dt = math.cos(curl) * .9
            dn = math.sin(curl) * dors_n + sw * lat_n
            dz = math.sin(curl) * dors_z + sw * lat_z
            Lseg = S * .085
            p3 = [p3[0] + dt * Lseg, p3[1] + dn * Lseg, p3[2] + dz * Lseg]
            pts.append(_add(base, (p3[0], tbr), (p3[1], nbr))); zs.append(p3[2])
        z = sum(zs) / len(zs) / S
        def fn():
            _limb(d, [base] + pts[::2] + [pts[-1]], S * .17, S * .1, fur, INK, iw)
            # rings
            for j in range(3, len(pts) - 1, 3):
                a, b = pts[j - 1], pts[j + 1]
                dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
                nx, ny = -dy / L, dx / L; r = S * .065
                c = pts[j]
                d.line([(c[0] - nx * r, c[1] - ny * r), (c[0] + nx * r, c[1] + ny * r)], fill=fur_d, width=max(2, int(S * .06)))
            e = pts[-1]; r = S * .055
            d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=fur_d)
            _limb(dmb, [base] + pts[::2] + [pts[-1]], S * .17 + 2 * iw, S * .1 + 2 * iw, 255, 255, 0)
        return z, fn

    # ---------------- head
    phh = phf + head_tilt
    Hc = _add(F, (S * .2, tf), (-S * .03 * math.cos(phh), nf))
    rh = S * .32
    def ear(side):
        th = phh + math.pi + side * .62
        c, sn = math.cos(th), math.sin(th)
        base = _add(Hc, (rh * .78 * c, nf), (-S * .02 + (S * .09 if sn < 0 else -S * .02), tf))
        ln = S * .32 * max(.35, abs(c))
        tip = _add(base, (ln * (1 if c >= 0 else -1), nf), (S * .04, tf))
        wb = S * .13
        b1 = _add(base, (wb, tf)); b2 = _add(base, (-wb, tf))
        def fn():
            for col, g in ((INK, iw * 1.3), (fur if sn > -.2 else _shade(fur, .75), 0)):
                cx = (b1[0] + b2[0] + tip[0]) / 3; cy = (b1[1] + b2[1] + tip[1]) / 3
                tri = [(p[0] + (p[0] - cx) * g / (S * .12), p[1] + (p[1] - cy) * g / (S * .12)) for p in (b1, tip, b2)]
                d.polygon(tri, fill=col)
            if sn > -.1:
                ib1 = _add(base, (wb * .55, tf), (S * .02 * (1 if c >= 0 else -1), nf))
                ib2 = _add(base, (-wb * .5, tf), (S * .02 * (1 if c >= 0 else -1), nf))
                itip = _add(tip, (-ln * .28 * (1 if c >= 0 else -1), nf))
                d.polygon([ib1, itip, ib2], fill=PINK)
            dmf.polygon([b1, tip, b2], fill=255)
        return sn, fn

    def head_fn():
        # skull + cheeks (white chin band on the belly side), muzzle, eyes, nose, whiskers
        for col, g in ((INK, iw), (fur, 0)):
            r = rh + g
            d.ellipse([Hc[0] - r, Hc[1] - r, Hc[0] + r, Hc[1] + r], fill=col)
        sub = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0)); ds = ImageDraw.Draw(sub)
        for lo, hi in _intervals(phh, 1.05):
            poly = [_add(Hc, (hi * rh * 1.05, nf), (-rh * 1.2, tf)), _add(Hc, (hi * rh * 1.05, nf), (rh * 1.2, tf)),
                    _add(Hc, (lo * rh * 1.05, nf), (rh * 1.2, tf)), _add(Hc, (lo * rh * 1.05, nf), (-rh * 1.2, tf))]
            ds.polygon(poly, fill=belly + (255,))
        # forehead stripes ('M') on the dorsal side
        dors = phh + math.pi
        if math.sin(dors) > -.3:
            for j in (-1, 0, 1):
                c = _add(Hc, (rh * .55 * math.cos(dors), nf), (j * rh * .28, tf))
                e = _add(c, (rh * .32 * (1 if math.cos(dors) >= 0 else -1), nf))
                ds.line([c, e], fill=fur_d + (255,), width=max(2, int(S * .05)))
        m = Image.new('L', (Wd, Hd), 0); ImageDraw.Draw(m).ellipse([Hc[0] - rh, Hc[1] - rh, Hc[0] + rh, Hc[1] + rh], fill=255)
        sub.putalpha(ImageChops.multiply(sub.split()[3], m))
        lay.alpha_composite(sub)
        # muzzle: forward along tf, a little to the chin side
        Mz = _add(Hc, (rh * .66, tf), (rh * .24 * math.cos(phh), nf))
        mr = rh * .33
        for col, g in ((INK, iw), (belly, 0)):
            d.ellipse([Mz[0] - mr * 1.1 - g, Mz[1] - mr * .85 - g, Mz[0] + mr * 1.1 + g, Mz[1] + mr * .85 + g], fill=col)
        # nose
        Nz = _add(Mz, (mr * .78, tf), (-mr * .25 * math.cos(phh), nf))
        nr = rh * .1
        d.polygon([_add(Nz, (-nr, tf), (-nr, nf)), _add(Nz, (nr * .6, tf)), _add(Nz, (-nr, tf), (nr, nf))], fill=PINK, outline=INK)
        # whiskers
        for j in (-1, 0, 1):
            a = _add(Mz, (mr * .3, tf), (j * mr * .25, nf))
            e = _add(a, (rh * 1.0, tf), (j * rh * .35 + rh * .1 * math.cos(phh), nf))
            d.line([a, e], fill=(250, 248, 240), width=max(1, int(S * .012)))
        # eyes (near and far): on the sides, a little toward the dorsal side
        for side in (1, -1):
            th = phh + side * (math.pi / 2 + .5)
            sn = math.sin(th)
            if sn < .12: continue
            E = _add(Hc, (rh * .3, tf), (rh * .82 * math.cos(th), nf))
            ew, eh = rh * .26 * (.5 + .5 * sn), rh * .2
            if eyes_closed:
                d.line([_add(E, (-ew, tf)), _add(E, (ew, tf))], fill=INK, width=max(2, int(S * .03)))
                continue
            poly = []
            for q in range(16):
                a = 2 * math.pi * q / 16
                poly.append(_add(E, (ew * math.cos(a), tf), (eh * math.sin(a) * (abs(math.sin(a)) ** .35), nf)))
            d.polygon(poly, fill=EYE, outline=INK, width=max(2, int(S * .022)))
            d.line([_add(E, (0, tf), (-eh * .85, nf)), _add(E, (0, tf), (eh * .85, nf))], fill=INK, width=max(2, int(S * .04)))
            hl = _add(E, (-ew * .35, tf), (-eh * .35, nf)); r = S * .016
            d.ellipse([hl[0] - r, hl[1] - r, hl[0] + r, hl[1] + r], fill=(255, 255, 255))
        dmf.ellipse([Hc[0] - rh - iw, Hc[1] - rh - iw, Hc[0] + rh + iw, Hc[1] + rh + iw], fill=255)
        dmf.ellipse([Mz[0] - mr * 1.1 - iw, Mz[1] - mr * .85 - iw, Mz[0] + mr * 1.1 + iw, Mz[1] + mr * .85 + iw], fill=255)

    # ---------------- draw order
    legs_items = items
    order = []
    for dep, fn in legs_items:
        order.append((dep if dep >= 0 else dep - 3, fn))
    ib, fb = half(False); ifr, ff = half(True)
    if not seam:
        order.append((-.65, ib)); order.append((-.64, ifr))
    order.append((-.6, fb))
    order.append((-.5, ff))
    if tail:
        zt, tfn = tail_fn(); order.append(((-2.5 if zt < 0 else .4), tfn))
    for side in (-1, 1):
        sn, efn = ear(side)
        order.append(((-.55 if sn < -.2 else -.2) + .001 * side, efn))
    order.append((-.3, head_fn))
    for dep, fn in sorted(order, key=lambda p: p[0]):
        fn()

    # ---------------- form shadow + rim (inner-shadow trick on the alpha)
    a = np.asarray(lay.split()[3], np.float32) / 255
    if a.max() > 0:
        lx, ly = light; sh = int(S * .09)
        A = Image.fromarray((a * 255).astype(np.uint8))
        away = np.asarray(ImageChops.offset(A, int(-lx * sh), int(-ly * sh)).filter(ImageFilter.GaussianBlur(S * .05)), np.float32) / 255
        toward = np.asarray(ImageChops.offset(A, int(lx * sh * .6), int(ly * sh * .6)).filter(ImageFilter.GaussianBlur(S * .03)), np.float32) / 255
        arr = np.asarray(lay, np.float32).copy()
        shade = np.clip(a - away, 0, 1) * .38
        rim = np.clip(a - toward, 0, 1) * .55
        arr[..., :3] *= (1 - shade)[..., None]
        rimc = np.array((255, 236, 200), np.float32)
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
        # tint each half (screen-ish) so the halves read blue / orange
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

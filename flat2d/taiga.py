"""flat2d kit additions for the Tunguska video (video 4): taiga forest, radial treefall, bare upright trunks,
Siberian sky and fireball, atmosphere cross-section with altitude ruler, hairdryer and grass.

Same contract as kit.py: every helper draws one layer onto an RGBA image in place, back to front, and its
arguments (offset, seed, t, phase, progress) are the animation parameters. Static heavy layers are cached.
"""
import math
import numpy as np
from PIL import Image, ImageDraw
import kit
from kit import W, H, INK, rgb, lerp, layer, mask, glow, fill_mask, radial, font, text_w

_cache = {}


def cached(key, fn):
    if key not in _cache:
        if len(_cache) > 80: _cache.clear()
        _cache[key] = fn()
    return _cache[key]


# ---------------------------------------------------------------- forest (side view)
def spruce(d, x, gy, h, lit, shade, ink=INK, iw=3, sway=0.0, tiers=5, snow=None):
    """A faceted spruce: stacked tiers, lit left plane, shadow right plane, ink outline. sway = tip offset
    as a fraction of h (wind)."""
    w = h * .42
    d.rectangle([x - h * .025, gy - h * .12, x + h * .025, gy], fill=lerp(rgb(shade), (40, 20, 10), .4))
    for k in range(tiers):
        f0 = k / tiers; f1 = (k + 1.45) / tiers
        yb = gy - h * .1 - (h * .9) * f0 * .82; yt = gy - h * .1 - (h * .9) * min(1, f1 * .82 + .18 * (k == tiers - 1))
        wb = w * (1 - f0 * .78) / 2
        sx = sway * h * (1 - yt / gy * 0 - (gy - yt) / h * 0) * ((gy - yt) / h)
        bx = x + sway * h * ((gy - yb) / h) ** 1.5
        tx = x + sway * h * ((gy - yt) / h) ** 1.5
        poly = [(bx - wb, yb), (tx, yt), (bx + wb, yb), (bx + wb * .45, yb - h * .03), (bx, yb + h * .012), (bx - wb * .45, yb - h * .03)]
        if iw: d.polygon([(px + (2 if px > bx else -2), py + (2 if py >= yb - 1 else -2)) for px, py in poly], fill=ink)
        d.polygon(poly, fill=rgb(shade))
        d.polygon([(bx - wb, yb), (tx, yt), (bx - wb * .1, yb + h * .006), (bx - wb * .45, yb - h * .03)], fill=rgb(lit))
        if snow:
            d.polygon([(tx, yt), (tx - wb * .3, yt + h * .07), (tx + wb * .1, yt + h * .05)], fill=rgb(snow))


def forest_row(img, seed, y_base, hmin, hmax, lit, shade, n=26, x_shift=0.0, ink=INK, iw=3, t=0.0, wind=0.012,
               fill_below=True, x_range=(-120, W + 120), snow=None):
    """A row of spruces along y_base (a forest band). Moves: x_shift (parallax), t (wind sway)."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    xs = np.sort(rng.uniform(*x_range, n)); hs = rng.uniform(hmin, hmax, n); ys = rng.uniform(-14, 14, n)
    if fill_below:
        d.rectangle([0, y_base - hmin * .15, W, y_base + 60], fill=rgb(shade))
    order = np.argsort(ys)
    for i in order:
        x = (xs[i] + x_shift - x_range[0]) % (x_range[1] - x_range[0]) + x_range[0]
        sw = wind * math.sin(t * 1.3 + i * .7)
        spruce(d, x, y_base + ys[i], hs[i], lit, shade, ink, iw, sway=sw, snow=snow)


def bare_trunk(d, x, gy, h, w, col=(92, 70, 58), lit=(150, 120, 98), ink=INK, iw=5, lean=0.0, seed=0, burnt=True,
               stubs=4):
    """An upright, branchless trunk (a 'telegraph pole'): tapered, a lit stripe, broken branch stubs, a
    snapped top. lean in degrees (+ = right)."""
    rng = np.random.default_rng(seed)
    a = math.radians(lean); ux, uy = math.sin(a), -math.cos(a)
    top = (x + ux * h, gy + uy * h); wt = w * .55
    nx, ny = -uy, ux
    poly = [(x - nx * w / 2, gy - ny * w / 2), (top[0] - nx * wt / 2, top[1] - ny * wt / 2),
            (top[0] - nx * wt * .1, top[1] - ny * wt * .1 - 22), (top[0] + nx * wt * .2, top[1] + ny * wt * .2 - 8),
            (top[0] + nx * wt / 2, top[1] + ny * wt / 2 - 16), (x + nx * w / 2, gy + ny * w / 2)]
    d.polygon(poly, fill=rgb(col), outline=ink, width=iw)
    d.line([(x - nx * w * .22, gy - 6), (top[0] - nx * wt * .2, top[1] + 10)], fill=rgb(lit), width=max(2, int(w * .18)))
    for k in range(stubs):
        f = rng.uniform(.3, .92); side = 1 if k % 2 else -1
        px, py = x + ux * h * f, gy + uy * h * f; L = w * rng.uniform(.6, 1.1)
        e = (px + side * L, py - L * .45)
        d.line([(px, py), e], fill=ink, width=max(4, int(w * .2)) + 4)
        d.line([(px, py), e], fill=rgb(col), width=max(2, int(w * .2)))
    if burnt:
        d.line([(top[0] - nx * wt * .3, top[1] + 30), (top[0] - nx * wt * .3, top[1] + 90)], fill=lerp(rgb(col), (20, 16, 18), .6), width=max(2, int(w * .15)))


def fallen_side(d, x, gy, L, w, ang, col=(110, 82, 62), lit=(160, 126, 96), ink=INK, root=True, seed=0):
    """A fallen tree seen from the side/ground: a log lying along angle ang (deg, 0 = to the right), its root
    plate standing up at the base end."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a) * .35
    e = (x + ux * L, gy + uy * L)
    d.line([(x, gy - w / 2), (e[0], e[1] - w * .3)], fill=ink, width=int(w) + 8)
    d.line([(x, gy - w / 2), (e[0], e[1] - w * .3)], fill=rgb(col), width=int(w))
    d.line([(x, gy - w * .75), (e[0], e[1] - w * .45)], fill=rgb(lit), width=max(2, int(w * .25)))
    rng = np.random.default_rng(seed)
    for k in range(4):
        f = rng.uniform(.35, .95); px, py = x + ux * L * f, gy + uy * L * f - w / 2
        d.line([(px, py), (px + ux * 30 + rng.uniform(-10, 10), py - w * .9)], fill=ink, width=5)
    if root:
        r = w * 1.3
        d.ellipse([x - r * .5, gy - w / 2 - r, x + r * .5, gy - w / 2 + r * .6], fill=lerp(rgb(col), (60, 40, 30), .4), outline=ink, width=4)


# ---------------------------------------------------------------- top-down views
def log_top(d, x, y, ang, L, w, col=(122, 92, 66), lit=(170, 136, 100), ink=INK, iw=3, twigs=True):
    """One fallen trunk seen from above: base (root plate) at (x, y), top along angle ang (rad)."""
    ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
    d.line([(x, y), (ex, ey)], fill=ink, width=int(w + 2 * iw))
    d.line([(x, y), (ex, ey)], fill=rgb(col), width=int(w))
    nx, ny = -math.sin(ang), math.cos(ang)
    d.line([(x - nx * w * .2, y - ny * w * .2), (ex - nx * w * .2, ey - ny * w * .2)], fill=rgb(lit), width=max(1, int(w * .3)))
    r = w * .9
    d.ellipse([x - r, y - r, x + r, y + r], fill=lerp(rgb(col), (70, 46, 34), .45), outline=ink, width=iw)
    if twigs:
        for f in (.55, .75, .9):
            px, py = x + math.cos(ang) * L * f, y + math.sin(ang) * L * f
            for s in (-1, 1):
                d.line([(px, py), (px + (math.cos(ang) * .6 + s * nx) * w * 1.3, py + (math.sin(ang) * .6 + s * ny) * w * 1.3)], fill=ink, width=max(2, iw))


def crown_top(d, x, y, r, col=(46, 104, 70), lit=(84, 150, 96), ink=INK, iw=3):
    """A standing spruce seen from above: a star-like crown with a lit side."""
    pts = []
    for i in range(14):
        a = i * math.pi / 7; rr = r if i % 2 == 0 else r * .62
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    d.polygon(pts, fill=rgb(col), outline=ink, width=iw)
    d.ellipse([x - r * .55, y - r * .6, x + r * .1, y + r * .05], fill=rgb(lit))


def pole_top(d, x, y, r, shadow_ang=.6, col=(96, 74, 60), ink=INK):
    """A bare upright trunk seen from above: a small disc with a long shadow."""
    L = r * 6
    d.line([(x, y), (x + math.cos(shadow_ang) * L, y + math.sin(shadow_ang) * L)], fill=(40, 34, 30), width=int(r * 1.2))
    d.ellipse([x - r, y - r, x + r, y + r], fill=rgb(col), outline=ink, width=3)


def treefall_items(seed, R0, R1, n, standing):
    """Positions of the radial treefall (deterministic): fallen logs (radius, angle) in R0..R1 and bare
    trunks inside R0."""
    rng = np.random.default_rng(seed)
    logs = []
    for i in range(n):
        r = R0 + (R1 - R0) * math.sqrt(rng.random()); a = rng.uniform(0, 2 * math.pi)
        logs.append((r, a, rng.uniform(.7, 1.2), rng.uniform(-.12, .12)))
    logs.sort(key=lambda v: -v[0])
    poles = []
    for i in range(standing):
        r = R0 * .9 * math.sqrt(rng.random()); a = rng.uniform(0, 2 * math.pi); poles.append((r, a))
    return logs, poles


def radial_treefall(img, cx, cy, R0, R1, seed=1, n=520, standing=36, wave=None, Lmul=1.0, w=9, iw=3,
                    ground=((96, 92, 60), (70, 70, 48)), log=((126, 96, 68), (178, 144, 104)), crown=((40, 92, 64), (78, 140, 92)),
                    squash=1.0, poles=True, map_style=False):
    """The Tunguska pattern from above: trunks lie radially with their tops pointing outward, away from
    (cx, cy); inside R0 bare trunks still stand. wave = radius of the blast front (None = all fallen):
    beyond it the trees still stand (crowns). squash < 1 tilts the disc toward a 3/4 view."""
    d = ImageDraw.Draw(img)
    logs, pl = treefall_items(seed, R0, R1, n, standing)
    for r, a, lk, da in logs:
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * squash
        if wave is not None and r > wave:
            crown_top(d, x, y, 15 * lk * (1 + .4 * (squash < 1)), *crown, iw=iw) if not map_style else None
            continue
        ang = math.atan2(math.sin(a + da) * squash, math.cos(a + da))
        L = 44 * lk * Lmul
        if map_style:
            ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
            d.line([(x, y), (ex, ey)], fill=log[0], width=w)
            d.ellipse([x - w * .7, y - w * .7, x + w * .7, y + w * .7], fill=log[0])
        else:
            log_top(d, x, y, ang, L, w * lk, *log, iw=iw)
    if poles:
        for r, a in pl:
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * squash
            if map_style:
                d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=log[0])
            else:
                pole_top(d, x, y, 7)


# ---------------------------------------------------------------- sky, fireball, blast
def fireball(img, x, y, r, ang, trail, t, core=(255, 252, 230), hot=(255, 210, 90), warm=(255, 120, 40), alpha=1.0):
    """A bolide: white-hot core, yellow/orange halo, a tapering trail behind it (ang = direction of travel,
    rad), sparks shed along the trail. Moves: x, y along its path; t flickers the trail."""
    bx, by = -math.cos(ang), -math.sin(ang); nx, ny = -by, bx
    m = mask(); md = ImageDraw.Draw(m)
    tip = (x + bx * trail, y + by * trail)
    md.polygon([(x + nx * r * 1.1, y + ny * r * 1.1), tip, (x - nx * r * 1.1, y - ny * r * 1.1)], fill=255)
    glow(img, m, warm, .75 * alpha, blur=int(r * .8) + 6, add=True)
    m2 = mask(); ImageDraw.Draw(m2).polygon([(x + nx * r * .6, y + ny * r * .6), (x + bx * trail * .7, y + by * trail * .7), (x - nx * r * .6, y - ny * r * .6)], fill=255)
    glow(img, m2, hot, .9 * alpha, blur=int(r * .4) + 4, add=True)
    radial(img, x, y, r * 6, hot, .5 * alpha)
    radial(img, x, y, r * 2.2, core, .95 * alpha, power=.8)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(3)
    for i in range(16):
        f = (rng.random() + t * 1.7) % 1; s = rng.uniform(-1, 1)
        px, py = x + bx * trail * f + nx * s * r * (1 + f * 2), y + by * trail * f + ny * s * r * (1 + f * 2)
        q = 5 * (1 - f) + 2
        d.ellipse([px - q, py - q, px + q, py + q], fill=lerp(hot, warm, f))
    d.ellipse([x - r * .7, y - r * .7, x + r * .7, y + r * .7], fill=core)


def shock_ring(img, cx, cy, r, w, color=(255, 240, 210), alpha=.7, squash=.28):
    """An expanding flattened shockwave ring (a dome front seen from the side)."""
    if r <= 2 or alpha <= .01: return
    m = mask(); ImageDraw.Draw(m).ellipse([cx - r, cy - r * squash, cx + r, cy + r * squash], outline=255, width=max(2, int(w)))
    glow(img, m, color, alpha, blur=max(3, int(w * .6)), add=True)


def smoke(img, seed, box, t, color=(90, 80, 84), n=18, alpha=150, rise=.12, size=(40, 120)):
    """Slow drifting smoke puffs (soft). Moves: t rises and drifts them."""
    rng = np.random.default_rng(seed); lay = layer(); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    for i in range(n):
        ph = rng.uniform(0, 1); u = (ph + t * rise) % 1
        x = rng.uniform(x0, x1) + 60 * math.sin(t * .4 + i) + u * 80
        y = y1 - (y1 - y0) * u; s = rng.uniform(*size) * (.6 + u * .8)
        d.ellipse([x - s, y - s * .7, x + s, y + s * .7], fill=rgb(color) + (int(alpha * math.sin(math.pi * u)),))
    img.alpha_composite(kit.soft_layer(lay, 14))


# ---------------------------------------------------------------- atmosphere cross-section
def altitude_ruler(img, x, y_ground, px_per_km, kms=(0, 2, 4, 6, 8, 10, 12), col=(220, 236, 255), hi=None, fs=30):
    """Left-edge altitude ruler (KM ticks). hi = the km to highlight (8)."""
    d = ImageDraw.Draw(img)
    top = y_ground - px_per_km * kms[-1]
    d.line([(x, y_ground), (x, top)], fill=INK, width=10); d.line([(x, y_ground), (x, top)], fill=col, width=5)
    for k in kms:
        y = y_ground - k * px_per_km
        big = hi is not None and k == hi
        d.line([(x - 18, y), (x + 18, y)], fill=INK, width=9); d.line([(x - 16, y), (x + 16, y)], fill=col, width=4)
        if not big:
            d.text((x + 30, y), f'{k} KM', font=font(fs, True), fill=col, anchor='lm', stroke_width=4, stroke_fill=INK)
    return top


def dashed(d, a, b, col, w=5, dash=24, gap=16, phase=0.0):
    L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    s = -(phase % (dash + gap))
    while s < L:
        s0, s1 = max(0, s), min(L, s + dash)
        if s1 > s0: d.line([(a[0] + ux * s0, a[1] + uy * s0), (a[0] + ux * s1, a[1] + uy * s1)], fill=col, width=w)
        s += dash + gap


def rock(d, x, y, r, ang=0.0, col=(120, 100, 92), lit=(176, 150, 134), dark=(78, 62, 60), ink=INK, iw=6, seed=5):
    """A faceted space rock (lit and shadow facets)."""
    rng = np.random.default_rng(seed); n = 9
    pts = []
    for i in range(n):
        a = ang + i * 2 * math.pi / n; rr = r * rng.uniform(.78, 1.08)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    d.polygon(pts, fill=rgb(col), outline=ink, width=iw)
    d.polygon([pts[4], pts[5], pts[6], (x, y)], fill=rgb(lit))
    d.polygon([pts[0], pts[1], pts[2], (x + r * .1, y + r * .1)], fill=rgb(dark))
    for i in range(3):
        cx_, cy_ = x + r * rng.uniform(-.4, .4), y + r * rng.uniform(-.4, .4); q = r * rng.uniform(.1, .18)
        d.ellipse([cx_ - q, cy_ - q, cx_ + q, cy_ + q], fill=lerp(rgb(dark), (0, 0, 0), .2), outline=ink, width=3)
    return pts


def building(d, x, gy, w, h, col=(196, 206, 222), win=(255, 226, 140), ink=INK, floors=8):
    """A plain block building (scale reference)."""
    d.rectangle([x - w / 2, gy - h, x + w / 2, gy], fill=rgb(col), outline=ink, width=5)
    d.rectangle([x - w / 2 + 6, gy - h + 6, x - w / 2 + w * .3, gy - 6], fill=lerp(rgb(col), (255, 255, 255), .3))
    cols = 3
    for f in range(floors):
        for c in range(cols):
            wx = x - w / 2 + w * (c + .5) / cols; wy = gy - h + h * (f + .5) / (floors + .4)
            d.rectangle([wx - w * .09, wy - h * .025, wx + w * .09, wy + h * .025], fill=rgb(win) if (f + c) % 3 else lerp(rgb(win), INK, .5))


# ---------------------------------------------------------------- hairdryer and grass
def hairdryer(img, x, y, s=1.0, body=(120, 200, 214), dark=(60, 128, 150), on=1.0, t=0.0):
    """A generic hairdryer (no brand) pointing straight down: nozzle at (x, y), body above it, intake
    grille on top, handle angled out to the right. Returns the handle grip point (for a hand)."""
    d = ImageDraw.Draw(img); S = lambda v: v * s
    # handle (behind the body)
    hp = [(x + S(40), y - S(250)), (x + S(90), y - S(330)), (x + S(330), y - S(250)), (x + S(300), y - S(185))]
    d.polygon([(px + 6 * (1 if px > x + S(100) else -1), py) for px, py in hp], fill=INK)
    d.polygon(hp, fill=rgb(dark), outline=INK, width=int(S(7)))
    d.rounded_rectangle([x + S(170), y - S(300), x + S(210), y - S(262)], S(8), fill=(240, 80, 60) if on > .5 else (130, 130, 140), outline=INK, width=4)
    # body
    d.rounded_rectangle([x - S(108), y - S(520), x + S(108), y - S(90)], S(100), fill=INK)
    d.rounded_rectangle([x - S(98), y - S(510), x + S(98), y - S(98)], S(92), fill=rgb(body))
    d.rounded_rectangle([x - S(78), y - S(470), x - S(30), y - S(140)], S(24), fill=lerp(rgb(body), (255, 255, 255), .5))
    d.line([(x + S(98), y - S(300)), (x - S(98), y - S(300))], fill=lerp(rgb(body), INK, .35), width=int(S(6)))
    # intake grille (top)
    d.ellipse([x - S(92), y - S(560), x + S(92), y - S(470)], fill=INK)
    d.ellipse([x - S(84), y - S(552), x + S(84), y - S(478)], fill=(60, 70, 84))
    for k in range(5):
        yy = y - S(540) + k * S(13); w = S(70) * math.sin(math.pi * (k + 1) / 6)
        d.line([(x - w, yy), (x + w, yy)], fill=(140, 150, 166), width=int(S(4)))
    # nozzle (bottom)
    d.polygon([(x - S(80), y - S(110)), (x + S(80), y - S(110)), (x + S(56), y), (x - S(56), y)], fill=rgb(dark), outline=INK, width=int(S(7)))
    d.rectangle([x - S(58), y - S(14), x + S(58), y + S(4)], fill=(40, 46, 56), outline=INK, width=4)
    if on > .5:
        radial(img, x, y + S(30), S(120), (255, 230, 200), .25 + .05 * math.sin(t * 20))
    return x + S(320), y - S(220)


def grass_side(img, x0, x1, gy, t, cx, push=1.0, col=(74, 160, 70), lit=(140, 210, 100), ink=INK, n=60, h=(70, 130),
               seed=4, core=70):
    """A strip of grass blades seen from the side. Air blown straight down at x = cx: the blades right
    under it stay up (|x - cx| < core), the blades around bend outward, more the further out (to a point)
    and flutter. push 0..1 = the blower's strength."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + rng.uniform(-.3, .3)) / n; hh = rng.uniform(*h)
        dx = x - cx; side = 1 if dx > 0 else -1
        k = max(0.0, (abs(dx) - core) / 120); k = min(1.0, k) * max(0.0, 1 - max(0, abs(dx) - 520) / 300)
        bend = push * (1.1 * k) + .05 * math.sin(t * 2 + i)
        bend += push * k * .12 * math.sin(t * 23 + i * 1.7)                # flutter in the airflow
        if abs(dx) < core: bend = .04 * math.sin(t * 9 + i) * push + .03 * math.sin(t * 2 + i)
        pts = []
        for j in range(7):
            f = j / 6; a = side * bend * f ** 1.4 * 1.25
            pts.append((x + math.sin(a) * hh * f, gy - math.cos(a) * hh * f))
        d.line(pts, fill=ink, width=11, joint='curve')
        d.line(pts, fill=rgb(col) if i % 3 else rgb(lit), width=6, joint='curve')

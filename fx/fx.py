# Procedural 2D cartoon effects for the shorts pipeline, in the bean-head cast style (characters/scripts/bean.py,
# spec references/reports/characters.md §2): flat saturated fills, plum ink #241726 thin on the top-left and ~3x thicker
# on the bottom-right (shadow) side, soft crescent shading. Contract (PIPELINE.md > FX):
#     render(name, t, size, **kw) -> RGBA PIL.Image  (size x size), t runs 0..1 over the effect's life.
# Every effect is empty at t=0 and t=1 and goes: anticipation (small build / squash) -> peak (ease + overshoot)
# -> fade (shrink + alpha), see fx/RULES.md.
# Common kwargs: color (hex or rgb), scale (content size, 1 = fills ~90% of the canvas), line (outline px in
# the OUTPUT image, default scales with size), seed (layout variation). Effect-specific kwargs are listed in NAMES.
# usage: python fx.py <name> <t> [size] out.png
import math, os, random, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 4                                   # supersampling, like bean.py
INK = (36, 23, 38)                      # #241726 plum ink, same as the bean cast (characters/scripts/bean.py)


# ---------------------------------------------------------------- easing / timing
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, x): return a + (b - a) * x
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def in_cubic(x): x = clamp(x); return x ** 3
def in_quad(x): x = clamp(x); return x * x
def out_quad(x): x = clamp(x); return 1 - (1 - x) ** 2
def out_back(x, s=1.70158):
    x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def bump(x): x = clamp(x); return math.sin(math.pi * x)


def pop(t, a, b, pre=0.35, dip=0.22, s=1.9):
    """Scale curve with anticipation: grow to `pre` by 0.6a, pull back to `dip` at a (the wind-up),
    then out_back overshoot to 1 at b."""
    if t <= 0: return 0.0
    a0 = a * 0.6
    if t < a0: return pre * smooth(t / a0)
    if t < a: return lerp(pre, dip, smooth(seg(t, a0, a)))
    if t < b: return dip + (1 - dip) * out_back(seg(t, a, b), s)
    return 1.0


def fade(t, a, b=1.0): return 1 - smooth(seg(t, a, b))
def shrink(t, a, b=1.0): return 1 - smooth(seg(t, a, b))   # ease in-out: gone well before b, no exit pop


# ---------------------------------------------------------------- colour helpers
def rgb(c):
    if isinstance(c, str):
        c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(v) for v in c[:3])
def mixc(a, b, x): return tuple(int(round(a[i] + (b[i] - a[i]) * clamp(x))) for i in range(3))
WHITE = (255, 255, 255)
def light(c, x=0.3): return mixc(c, WHITE, x)
def dark(c, x=0.3): return mixc(c, INK, x)


# ---------------------------------------------------------------- drawing primitives (coords in OUTPUT px)
# A shape is a tuple: ('c', x, y, r, col) circle | ('e', x, y, rx, ry, col) ellipse
#                     ('s', [(x, y, w), ...], col) round stroke with per-point width | ('p', [(x, y), ...], col) polygon
# group(): every shape's ink (grown by `e`) first, then every fill -> one merged silhouette, no seams (DRAWING_RULES 8).

def new(n): return Image.new('RGBA', (n * S, n * S), (0, 0, 0, 0))


def resample(pts, step):
    """Densify a polyline of (x, y, w) so stamped circles overlap smoothly."""
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        dist = math.hypot(q[0] - p[0], q[1] - p[1])
        k = max(1, int(dist / max(step, 0.25)))
        for i in range(1, k + 1):
            f = i / k; out.append(tuple(lerp(p[j], q[j], f) for j in range(3)))
    return out


THICK = (math.cos(math.radians(64)) * 0.5, math.sin(math.radians(64)) * 0.5)   # ink shift per unit e -> 1:3 thin/thick
SH_FX = (0.86, 0.80, 0.90)              # crescent shade multiplier (cool, like the cast's cloth/skin shadow)


def shape(d, sh, e, col=None, off=(0.0, 0.0)):
    """Draw one shape grown by `e` px and moved by off*e_eff (the ink pass uses THICK: thin top-left, thick bottom-right)."""
    k = sh[0]; c = col or sh[-1]
    if k == 'c':
        _, x, y, r, _c = sh
        if r < 0.3: return
        ee = min(e, r * 0.6); x += off[0] * ee; y += off[1] * ee     # tiny shapes get a thinner line: no lone ink dot
        r = (r + ee) * S
        d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=c)
    elif k == 'e':
        _, x, y, rx, ry, _c = sh
        if min(rx, ry) < 0.3: return
        e = min(e, min(rx, ry) * 0.6); x += off[0] * e; y += off[1] * e
        rx = (rx + e) * S; ry = (ry + e) * S
        d.ellipse((x * S - rx, y * S - ry, x * S + rx, y * S + ry), fill=c)
    elif k == 's':
        pts = sh[1]
        if not pts: return
        wmin = min(p[2] for p in pts)
        if max(p[2] for p in pts) < 0.3: return
        e = min(e, max(p[2] for p in pts) * 0.5)
        ox, oy = off[0] * e, off[1] * e
        for x, y, w in resample(pts, max(0.4, (wmin + 2 * e) * 0.2)):
            r = (w / 2 + e) * S
            if r > 0: d.ellipse(((x + ox) * S - r, (y + oy) * S - r, (x + ox) * S + r, (y + oy) * S + r), fill=c)
    elif k == 'p':
        pts = sh[1]
        if len(pts) < 3: return
        if e > 0:
            xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
            e = min(e, max(0.5, min(max(xs) - min(xs), max(ys) - min(ys)) * 0.3))
        P = [((x + off[0] * e) * S, (y + off[1] * e) * S) for x, y in pts]
        d.polygon(P, fill=c)
        if e > 0:
            w = max(1, int(round(2 * e * S)))
            d.line(P + [P[0]], fill=c, width=w, joint='curve')
            r = e * S
            for x, y in P: d.ellipse((x - r, y - r, x + r, y + r), fill=c)


def size_of(sh):
    k = sh[0]
    if k == 'c': return sh[3]
    if k == 'e': return min(sh[3], sh[4])
    if k == 's': return max(p[2] for p in sh[1]) / 2 if sh[1] else 0
    xs = [q[0] for q in sh[1]]; ys = [q[1] for q in sh[1]]
    return min(max(xs) - min(xs), max(ys) - min(ys)) / 2


def crescent(lay, size, light=(-0.7, -0.7), k=SH_FX):
    """Cast-style soft crescent shadow: darken the fill except where the mask shifted toward the light still covers it
    (same idea as fill_shaded() in characters/scripts/bean.py). `size` = typical shape radius in px."""
    if size < 2: return lay
    a = lay.getchannel('A')
    sh = int(round(0.3 * size * S))
    lit = ImageChops.offset(a, int(light[0] * sh), int(light[1] * sh))
    lit = lit.filter(ImageFilter.GaussianBlur(max(1, 0.12 * size * S)))
    lit = ImageChops.multiply(lit, a)
    r, g, b, _ = lay.split()
    dark = Image.merge('RGBA', (r.point(lambda v: int(v * k[0])), g.point(lambda v: int(v * k[1])),
                                b.point(lambda v: int(v * k[2])), a))
    lay2 = lay.copy(); lay2.putalpha(lit)
    dark.alpha_composite(lay2)
    return dark


def group(n, shapes, e, details=(), alpha=1.0, ink=INK, shade=True):
    """One outlined silhouette layer in the cast style: plum ink (thin top-left, ~3x thicker bottom-right) under all
    fills (one merged silhouette, no seams), soft crescent shading on the fills, then `details` with no outline."""
    fills = new(n); d = ImageDraw.Draw(fills)
    for sh in shapes: shape(d, sh, 0)
    if shade and shapes:
        sizes = sorted(size_of(sh) for sh in shapes)
        fills = crescent(fills, sizes[len(sizes) // 2])
    lay = new(n)
    if e > 0:
        dd = ImageDraw.Draw(lay)
        for sh in shapes: shape(dd, sh, e, ink, THICK)
    lay.alpha_composite(fills)
    if details:
        dd = ImageDraw.Draw(lay)
        for sh in details: shape(dd, sh, 0)
    return opacity(lay, alpha)


def opacity(lay, a):
    a = clamp(a)
    if a >= 0.999: return lay
    if a <= 0.001: return Image.new('RGBA', lay.size, (0, 0, 0, 0))
    r, g, b, al = lay.split()
    return Image.merge('RGBA', (r, g, b, al.point(lambda v: int(v * a))))


def comp(base, *layers):
    for l in layers: base.alpha_composite(l)
    return base


def rot(x, y, cx, cy, ang):
    a = math.radians(ang); dx, dy = x - cx, y - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)


def star_pts(cx, cy, n, r_out, r_in, ang=0.0, jitter=None):
    pts = []
    for i in range(2 * n):
        r = (r_out * (jitter[i // 2] if jitter else 1)) if i % 2 == 0 else r_in
        a = math.radians(ang) + math.pi * i / n - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def ellipse_pts(cx, cy, rx, ry, ang=0.0, n=40):
    return [rot(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n), cx, cy, ang)
            for i in range(n)]


def bez(p0, p1, p2, n=24, w0=1.0, w1=1.0):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1], lerp(w0, w1, u))
            for u in (i / n for i in range(n + 1))]


def ink_w(e, s, full=0.3):
    """Outline width that grows in with the sprite so a tiny sprite is never a lone dark dot (no pop)."""
    return e * clamp(s / full)


# ---------------------------------------------------------------- effects
# each takes (t, n, u, e, kw): n canvas px, u = content half-size px, e = outline px. Returns an n*S RGBA image.

def fx_explosion(t, n, u, e, kw):
    rng = random.Random(kw.get('seed', 3))
    col = rgb(kw.get('color', '#ff8a1f')); hot = rgb(kw.get('core', '#ffd23a')); flash_c = rgb('#fff8dc')
    smoke = rgb(kw.get('smoke', '#9b93ad'))
    cx, cy = n / 2, n / 2 + u * 0.12
    im = new(n)
    # anticipation: a hot dot swells then sucks in just before the burst
    k = pop(t, 0.13, 0.34, pre=0.22, dip=0.12, s=1.4)
    cool = smooth(seg(t, 0.36, 0.78))                       # fire -> smoke
    rise = u * 0.32 * smooth(seg(t, 0.3, 1.0))
    out = fade(t, 0.9, 1.0)
    body = mixc(col, smoke, cool)
    puffs = []
    m = 9
    for i in range(m):
        a = 2 * math.pi * (i + rng.uniform(-0.2, 0.2)) / m - math.pi / 2
        dist = u * rng.uniform(0.42, 0.52) * (1 + 0.18 * smooth(seg(t, 0.35, 1)))
        r = u * rng.uniform(0.25, 0.33)
        late = 0.6 + 0.25 * rng.random()                    # each puff dissolves on its own beat
        rr = r * k * shrink(t, late - 0.25, min(1.0, late + 0.2))
        up = rise * (1.25 if math.sin(a) < 0 else 0.9)
        puffs.append(('c', cx + math.cos(a) * dist * k, cy + math.sin(a) * dist * k * 0.9 - up, rr, body))
    puffs.append(('c', cx, cy - rise, u * 0.42 * k * shrink(t, 0.55, 0.95), body))
    caps = [('c', p[1] - p[3] * 0.25, p[2] - p[3] * 0.3, p[3] * 0.42, light(body, 0.2)) for p in puffs[:-1]]
    # inner hot layer and flash core (no outline: inside the silhouette)
    hk = k * shrink(t, 0.34, 0.66)
    inner = [('c', cx + math.cos(a) * u * 0.2 * hk, cy + math.sin(a) * u * 0.18 * hk - rise, u * 0.24 * hk, hot)
             for a in (2 * math.pi * j / 5 - math.pi / 2 for j in range(5))]
    fl = (1 - smooth(seg(t, 0.2, 0.46))) if t >= 0.13 else 1.0
    core = [('c', cx, cy - rise, u * (0.24 if t >= 0.13 else 0.5) * k * fl, flash_c)]
    # debris sparks fly out on the burst, outlined like everything else
    sparks = []
    for i in range(7):
        a = 2 * math.pi * (i + 0.5 + rng.uniform(-0.3, 0.3)) / 7 - math.pi / 2
        p = seg(t, 0.15, 0.62)
        if 0 < p < 1:
            d0 = u * (0.45 + 0.5 * out_cubic(p))
            sr = u * 0.055 * bump(p ** 0.6)
            sparks.append(('c', cx + math.cos(a) * d0, cy + math.sin(a) * d0 + u * 0.35 * p * p, sr, hot))
    comp(im, group(n, sparks, e * 0.8, alpha=out))
    comp(im, group(n, puffs, ink_w(e, k), details=caps + inner + core, alpha=out * clamp(t / 0.03)))
    return im


def fx_impact_star(t, n, u, e, kw):
    rng = random.Random(kw.get('seed', 5))
    col = rgb(kw.get('color', '#ffd23a')); inner = rgb(kw.get('inner', '#fffbe6'))
    pts_n = kw.get('points', 8)
    cx, cy = n / 2, n / 2
    k = pop(t, 0.1, 0.28, pre=0.3, dip=0.16, s=2.4)
    k *= 1 + 0.05 * math.sin(2 * math.pi * seg(t, 0.28, 0.6) * 2) * fade(t, 0.4, 0.6)   # settling throb
    k *= 1 - 0.12 * smooth(seg(t, 0.35, 0.7))              # slow settle during the hold: never a frozen sprite
    k *= shrink(t, 0.64, 0.95)
    ang = kw.get('angle', 0) + 14 * (1 - out_cubic(seg(t, 0.1, 0.5))) - 12 * smooth(seg(t, 0.3, 1))
    jit = [rng.uniform(0.78, 1.0) for _ in range(pts_n)]
    outer = ('p', star_pts(cx, cy, pts_n, u * 0.78 * k, u * 0.36 * k, ang, jit), col)
    core = ('p', star_pts(cx, cy, pts_n, u * 0.42 * k, u * 0.2 * k, ang, jit), inner)
    im = new(n)
    # impact ticks shoot outward on the hit, after the star appears
    ticks = []
    for i in range(6):
        a = math.radians(ang + 30 + 60 * i)
        p = seg(t, 0.14, 0.5)
        if 0 < p < 1:
            h = u * (0.62 + 0.36 * out_cubic(p)); tl = u * (0.62 + 0.36 * in_quad(p))
            w = u * 0.07 * bump(p)
            ticks.append(('s', [(cx + math.cos(a) * tl, cy + math.sin(a) * tl, w * 0.4),
                                (cx + math.cos(a) * h, cy + math.sin(a) * h, w)], col))
    comp(im, group(n, ticks, e * 0.8))
    comp(im, group(n, [outer], ink_w(e, k), details=[core], alpha=fade(t, 0.92, 1.0) * clamp(t / 0.03)))
    return im


def fx_dust_puff(t, n, u, e, kw):
    rng = random.Random(kw.get('seed', 7))
    col = rgb(kw.get('color', '#d9c4a0'))
    side = kw.get('direction', 'both')                     # 'both' | 'left' | 'right'
    cx, gy = n / 2, n / 2 + u * 0.55                       # ground line
    sides = {'both': (-1, 1), 'left': (-1,), 'right': (1,)}[side]
    squash = 1 - smooth(seg(t, 0.06, 0.26))                # anticipation: flat and low before it billows
    shapes, caps = [], []
    m = 4
    for s in sides:
        for i in range(m):
            f = (i + 0.5) / m
            go = out_cubic(seg(t, 0.08 + 0.03 * i, 0.75))
            grow = pop(t, 0.06 + 0.02 * i, 0.32 + 0.03 * i, pre=0.35, dip=0.28, s=1.5)
            r = u * (0.26 - 0.1 * f) * grow * shrink(t, 0.42 + 0.08 * i, 0.86 + 0.03 * i) * rng.uniform(0.7, 1.25)
            hy = u * rng.uniform(0.0, 0.18) * smooth(seg(t, 0.3, 1.0))   # puffs drift up at different rates
            x = cx + s * u * (0.08 + 0.95 * f * go)
            y = gy - r * (1 - 0.35 * squash) - u * 0.22 * out_quad(seg(t, 0.15, 1)) * (1 - f * 0.5) - hy
            shapes.append(('e', x, y, r * (1 + 0.45 * squash), r * (1 - 0.35 * squash), col))
            caps.append(('e', x - r * 0.2, y - r * 0.3, r * 0.5, r * 0.4 * (1 - 0.35 * squash), light(col, 0.35)))
    rc = u * 0.24 * pop(t, 0.04, 0.28, pre=0.4, dip=0.3, s=1.3) * shrink(t, 0.3, 0.7)
    shapes.append(('e', cx, gy - rc * (1 - 0.35 * squash), rc * (1 + 0.5 * squash), rc * (1 - 0.35 * squash), col))
    k = max(p[3] for p in shapes) / (u * 0.26)
    return group(n, shapes, ink_w(e, k), details=caps, alpha=fade(t, 0.9, 1.0) * clamp(t / 0.03))


def fx_speed_lines(t, n, u, e, kw):
    rng = random.Random(kw.get('seed', 11))
    col = rgb(kw.get('color', '#ffffff'))
    cnt = kw.get('count', 7)
    ang = kw.get('angle', 0)                                # direction of travel (deg, 0 = moving right)
    cx, cy = n / 2, n / 2
    lines = []
    for i in range(cnt):
        y = cy + u * 0.85 * ((i + 0.5) / cnt * 2 - 1) + u * rng.uniform(-0.05, 0.05)
        d0 = 0.03 + 0.12 * abs((i + 0.5) / cnt * 2 - 1) + 0.03 * rng.random()   # one ordered wave, middle first
        p = seg(t, d0, d0 + 0.68)
        if not 0 < p < 1: continue
        L = u * rng.uniform(1.1, 1.7)
        x0 = cx + u * 0.85 - u * 0.15 * (1 - abs((i + 0.5) / cnt * 2 - 1))
        x0 += u * 0.06 * bump(seg(p, 0, 0.18))              # anticipation: tiny forward nudge before streaking back
        head = x0 - L * in_cubic(p)                         # tail end chases the head -> line grows then retracts
        tail = x0 - L * out_cubic(p) * 1.0
        a, b = (head, tail) if head > tail else (tail, head)
        w = u * rng.uniform(0.085, 0.12) * bump(p) ** 0.5
        lines.append(('s', [(b, y, w * 0.25), (a, y, w)], col))
    lay = group(n, lines, e)
    if ang: lay = lay.rotate(ang, resample=Image.BICUBIC, center=(cx * S, cy * S))
    return lay


def teardrop(cx, cy, r, tip, ang=0.0, sx=1.0, sy=1.0, nseg=36):
    """Drop with round bottom centred at (cx, cy), point `tip` px above the centre."""
    D = max(tip, r * 1.05)
    th = math.acos(r / D)                                  # tangent angle from the up axis
    pts = [(0, -D)]
    a0, a1 = -math.pi / 2 + th, 3 * math.pi / 2 - th
    for i in range(nseg + 1):
        a = lerp(a0, a1, i / nseg); pts.append((r * math.cos(a), r * math.sin(a)))
    return [rot(cx + x * sx, cy + y * sy, cx, cy, ang) for x, y in pts]


def fx_sweat_drop(t, n, u, e, kw):
    col = rgb(kw.get('color', '#5cc0ff'))
    flip = -1 if kw.get('flip', False) else 1
    k = pop(t, 0.12, 0.3, pre=0.4, dip=0.3, s=2.0)
    wob = 0.06 * math.sin(2 * math.pi * 2.5 * seg(t, 0.3, 0.55)) * fade(t, 0.35, 0.55)
    creep = 0.12 * smooth(seg(t, 0.28, 0.45))               # slow creep while it gathers weight
    slide = creep + 0.88 * in_quad(seg(t, 0.45, 0.86))
    hold = 0.12 * bump(seg(t, 0.36, 0.48)) - 0.05 * bump(seg(t, 0.48, 0.58))                # squash wide just before it lets go (anticipation)
    stretch = 0.32 * bump(seg(t, 0.46, 1.0))
    sx = (1 + wob + hold - 0.15 * stretch) * k * shrink(t, 0.7, 0.96)
    sy = (1 - wob - hold + stretch) * k * shrink(t, 0.7, 0.96)
    cx = n / 2 + flip * u * 0.12 * slide
    cy = n / 2 - u * 0.45 + u * 1.05 * slide
    r = u * 0.3
    body = ('p', teardrop(cx, cy, r, r * 2.2, ang=flip * -12 * slide, sx=sx, sy=sy), col)
    hl = ('e', cx - r * 0.38 * sx, cy - r * 0.15 * sy, r * 0.17 * sx, r * 0.3 * sy, light(col, 0.75))
    return group(n, [body], ink_w(e, k), details=[hl], alpha=fade(t, 0.92, 1.0) * clamp(t / 0.03))


def fx_anger_vein(t, n, u, e, kw):
    col = rgb(kw.get('color', '#ff3b4a'))
    cx, cy = n / 2, n / 2
    k = pop(t, 0.14, 0.36, pre=0.4, dip=0.26, s=2.6)
    for pk in (0.47, 0.6):                                  # two clear throbs through the hold
        k *= 1 + 0.18 * bump(seg(t, pk - 0.06, pk + 0.06))
    k *= shrink(t, 0.7, 0.96)
    jit = 4 * math.sin(t * 60) * bump(seg(t, 0.3, 0.75))
    strokes, hls = [], []
    R = u * 0.7 * k
    for q in (45, 135, 225, 315):
        a1, a2 = math.radians(q - 33 + jit), math.radians(q + 33 + jit)
        am = math.radians(q + jit)
        p0 = (cx + R * math.cos(a1), cy + R * math.sin(a1))
        p2 = (cx + R * math.cos(a2), cy + R * math.sin(a2))
        p1 = (cx + R * 0.18 * math.cos(am), cy + R * 0.18 * math.sin(am))
        pts = bez(p0, p1, p2, 28)
        w = u * 0.17 * k
        strokes.append(('s', [(x, y, w * (0.55 + 0.45 * bump(i / 28))) for i, (x, y, _) in enumerate(pts)], col))
        hls.append(('s', [(x, y, w * 0.18 * bump(i / 28)) for i, (x, y, _) in enumerate(pts) if 6 <= i <= 22], light(col, 0.55)))
    return group(n, strokes, ink_w(e, k), details=hls, alpha=fade(t, 0.92, 1.0) * clamp(t / 0.03))


def almond(cx, cy, rx, ry, ang, n=40):
    """Eye shape: two arcs meeting in points at the corners (pointed ends read as eyes, not coins)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = rx * math.cos(a); y = ry * math.sin(a) * (abs(math.sin(a)) ** 0.15) * (1 - 0.18 * math.cos(a) ** 2)
        pts.append(rot(cx + x, cy + y, cx, cy, ang))
    return pts


def fx_glow_eyes(t, n, u, e, kw):
    col = rgb(kw.get('color', '#ffcf3a'))
    gap = kw.get('gap', 0.42) * u
    r = kw.get('radius', 0.27) * u                          # half-width of each eye
    slant = kw.get('slant', 14)                             # inner corners low = menacing; 0 = neutral, <0 = sad
    cx, cy = n / 2, n / 2
    # eyelid: a slit opens a little, blinks shut (anticipation), then snaps open with overshoot
    if t < 0.1: o = 0.2 * smooth(t / 0.1)
    elif t < 0.16: o = lerp(0.2, 0.06, smooth(seg(t, 0.1, 0.16)))
    else: o = lerp(0.06, 1, out_back(seg(t, 0.16, 0.34), 2.2))
    o = max(0.0, o * shrink(t, 0.78, 0.97)) if t < 0.97 else 0.0
    pulse = bump(seg(t, 0.34, 0.76) * 3 % 1) * (0.34 < t < 0.76)   # three slow glow pulses during the hold
    flick = 1 + 0.05 * pulse
    glow = clamp(t / 0.12) * (0.7 + 0.3 * pulse + 0.3 * bump(seg(t, 0.16, 0.32))) * fade(t, 0.72, 0.98)
    im = new(n)
    # halo: ONE flat outlined almond ring, semi-opaque (cel glow, no blur; RULES 7), plus short outlined rays on the flare
    rings = [('p', almond(cx + s_ * gap, cy, r * 1.5 * flick, r * 0.62 * 1.5 * max(o, 0.35) * flick, -s_ * slant),
              light(col, 0.55)) for s_ in (-1, 1)]
    comp(im, group(n, rings, ink_w(e, o, 0.25), alpha=clamp(glow * 2)))   # solid flat fill, alpha only at the ends
    rp = seg(t, 0.2, 0.62)
    if 0 < rp < 1:
        rays = []
        for s_ in (-1, 1):
            for a_ in (-60, -90, -120):
                ar = math.radians(a_ - s_ * slant * 0.5); x = cx + s_ * gap
                r0 = r * (1.2 + 0.3 * in_quad(rp)); r1 = r * (1.25 + 0.6 * out_cubic(rp))
                rays.append(('s', [(x + math.cos(ar) * r0, cy + math.sin(ar) * r0 * 0.9, r * 0.05),
                                   (x + math.cos(ar) * r1, cy + math.sin(ar) * r1 * 0.9, r * 0.16 * bump(rp))], col))
        comp(im, group(n, rays, e * 0.8))
    eyes, cores = [], []
    for s_ in (-1, 1):
        x = cx + s_ * gap
        ang = -s_ * slant
        eyes.append(('p', almond(x, cy, r * flick, r * 0.62 * o * flick, ang), col))
        cores.append(('p', almond(x + s_ * r * 0.04, cy - r * 0.04 * o, r * 0.55, r * 0.3 * o, ang), light(col, 0.85)))
    comp(im, group(n, eyes, ink_w(e, o, 0.25), details=cores, alpha=clamp(t / 0.03) * fade(t, 0.94, 1.0)))
    return im


def fx_sparkle(t, n, u, e, kw):
    rng = random.Random(kw.get('seed', 13))
    col = rgb(kw.get('color', '#ffe45c'))
    cnt = kw.get('count', 5)
    cx, cy = n / 2, n / 2
    shapes, cores, ks = [], [], []
    for i in range(cnt):
        if i == 0: x, y, sz, d0 = cx, cy, 0.5, 0.0
        else:
            a = 2 * math.pi * i / (cnt - 1) + rng.uniform(-0.4, 0.4)
            dist = u * rng.uniform(0.5, 0.75)
            x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist
            sz, d0 = rng.uniform(0.18, 0.3), 0.08 + 0.32 * (i - 1) / max(1, cnt - 2)
        life = 0.6 if i == 0 else 0.5
        p = seg(t, d0, d0 + life)
        if not 0 < p < 1: continue
        k = pop(p, 0.15, 0.4, pre=0.3, dip=0.18, s=2.0) * shrink(p, 0.55, 1.0)
        ang = 50 * out_cubic(p) - 10
        R = u * sz * k; ks.append(k)
        shapes.append(('p', star_pts(x, y, 4, R, R * 0.22, ang), col))
        cores.append(('c', x, y, R * 0.16, WHITE))
    if not shapes: return new(n)
    return group(n, shapes, ink_w(e, max(ks)), details=cores, alpha=fade(t, 0.9, 1.0))


def fx_splash(t, n, u, e, kw):
    rng = random.Random(kw.get('seed', 17))
    col = rgb(kw.get('color', '#4fb6ff'))
    cx, by = n / 2, n / 2 + u * 0.5                        # base (water surface) point
    im = new(n)
    # anticipation: the surface dips into a small ring before the crown rises
    dip = bump(seg(t, 0.0, 0.16))
    k = pop(t, 0.14, 0.38, pre=0.0001, dip=0.0001, s=1.6) if t >= 0.14 else 0.0
    h = u * 0.85 * k * (1 - in_quad(seg(t, 0.42, 0.8)))
    base_r = u * (0.18 * dip + 0.42 * out_cubic(seg(t, 0.12, 0.5)))
    base_r *= shrink(t, 0.62, 0.92)
    shapes = []
    if base_r > 0.5:
        shapes.append(('e', cx, by, base_r, base_r * 0.22, col))
    if h > 1:                                               # crown: a cup that flares out into 5 points
        tips = 5; wb = u * 0.26 * min(1, k * 1.4); wt = u * 0.5 * min(1, k * 1.2)
        top = []
        for i in range(tips):
            f = i / (tips - 1) * 2 - 1
            hh = h * (1 - 0.3 * f * f) * (1.0 if i % 2 == 0 else 0.92)
            top.append((cx + f * wt, by - hh))
            if i < tips - 1:
                fm = (i + 0.5) / (tips - 1) * 2 - 1
                top.append((cx + fm * wt * 0.92, by - h * 0.5 * (1 - 0.2 * fm * fm)))
        wall = [(cx - wb, by)] + top + [(cx + wb, by)]
        shapes.append(('p', wall, col))
        tip_pts = top[::2]
    else:
        tip_pts = []
    # flying drops: ballistic, stretched along velocity, shrink as they fall
    drops = []
    for i in range(8):
        f = (i + 0.5) / 8 * 2 - 1
        p = seg(t, 0.3 + 0.03 * abs(f), 0.9)                # thrown off the crown rim as it peaks
        if not 0 < p < 1: continue
        vx = f * u * 0.75 * rng.uniform(0.85, 1.15); vy = -u * rng.uniform(0.7, 1.0); g = u * 1.7
        x0 = cx + f * u * 0.5; y0 = by - u * 0.85 * (1 - 0.3 * f * f)
        x = x0 + vx * p; y = y0 + vy * p + g * p * p
        dvx, dvy = vx, vy + 2 * g * p; sp = math.hypot(dvx, dvy) or 1
        rr = u * rng.uniform(0.045, 0.075) * min(1, p * 5) * shrink(p, 0.55, 1.0)
        tl = rr * 1.8
        drops.append(('s', [(x - dvx / sp * tl, y - dvy / sp * tl, rr * 0.7), (x, y, rr * 2)], col))
    hls = [('e', x + (cx - x) * 0.25, y + h * 0.28, u * 0.025, h * 0.12, light(col, 0.55)) for x, y in tip_pts[1:-1]]
    if base_r > 0.5: hls.append(('e', cx, by - base_r * 0.05, base_r * 0.7, base_r * 0.1, light(col, 0.3)))
    comp(im, group(n, drops, e * 0.85, alpha=fade(t, 0.8, 1.0)))
    kk = max([k, dip * 0.6])
    comp(im, group(n, shapes, ink_w(e, kk), details=hls, alpha=fade(t, 0.82, 1.0) * clamp(t / 0.03)))
    # expanding ring on the surface after the crown falls
    rp = seg(t, 0.5, 0.95)
    if 0 < rp < 1:
        rr = u * (0.4 + 0.5 * out_cubic(rp)); w = u * 0.06 * (1 - smooth(rp))
        ring = [(cx + rr * math.cos(a), by + rr * 0.2 * math.sin(a), w)
                for a in (2 * math.pi * j / 64 for j in range(65))]
        comp(im, group(n, [('s', ring, col)], e * 0.8, alpha=fade(rp, 0.85, 1.0)))
    return im


def squash_stretch(t, a, b):
    """(sx, sy) for a pop: wide and short during the wind-up, tall and thin on the release, then settle."""
    if t < a: s = smooth(seg(t, a * 0.5, a)) * 0.22; return 1 + s, 1 - s
    p = seg(t, a, b)
    v = 0.2 * math.sin(math.pi * 1.5 * p) * (1 - p)
    return 1 - v, 1 + v


def xform(pts, px, py, sx, sy, ang, k, dx=0, dy=0):
    out = []
    for p in pts:
        x = px + (p[0] - px) * sx * k; y = py + (p[1] - py) * sy * k
        x, y = rot(x, y, px, py, ang)
        out.append((x + dx, y + dy) + tuple(w * k for w in p[2:]))   # stroke widths shrink with the glyph
    return out


def fx_question_mark(t, n, u, e, kw):
    col = rgb(kw.get('color', '#ffd84a'))
    cx, cy = n / 2, n / 2
    k = pop(t, 0.12, 0.32, pre=0.35, dip=0.25, s=2.0) * shrink(t, 0.7, 0.96)
    sx, sy = squash_stretch(t, 0.12, 0.45)
    ang = kw.get('tilt', 8) + 14 * math.sin(2 * math.pi * 1.5 * seg(t, 0.2, 0.75)) * (1 - seg(t, 0.2, 0.75))
    lift = -u * 0.15 * smooth(seg(t, 0.72, 1.0))
    w = u * 0.21
    hook_c = (cx, cy - u * 0.38); R = u * 0.3
    pts = []
    for i in range(29):                                      # arc from left over the top to the right-hand side
        a = math.radians(lerp(195, 395, i / 28)); pts.append((hook_c[0] + R * math.cos(a), hook_c[1] + R * math.sin(a), w))
    pts += [(x, y, w) for x, y, _ in bez(pts[-1][:2], (cx + u * 0.04, cy - u * 0.05), (cx, cy + u * 0.16), 16)[1:]]
    pts[0] = pts[0][:2] + (w * 0.9,)
    piv = (cx, cy + u * 0.75)
    lift += u * 0.04 * math.sin(2 * math.pi * 1.5 * seg(t, 0.35, 0.85)) * bump(seg(t, 0.35, 0.85))
    grow = smooth(seg(t, 0.08, 0.16))                       # glyph grows out of a round blob
    stroke = ('s', xform(pts, *piv, sx, sy, ang, k, 0, lift), col)
    kd = pop(t, 0.18, 0.38, pre=0.3, dip=0.2, s=2.4) * shrink(t, 0.7, 0.96)  # the dot lands a beat later (overlap)
    dx, dy = xform([(cx, cy + u * 0.52)], *piv, sx, sy, ang, 1, 0, lift)[0]
    dot = ('c', dx, dy, u * 0.12 * kd, col)
    hl = [('c', *xform([(hook_c[0] - R * 0.7, hook_c[1] - R * 0.55)], *piv, sx, sy, ang, k, 0, lift)[0], w * 0.18 * k,
           light(col, 0.6))]
    blob = []
    if grow < 1:                                            # anticipation: a squashed ball, not a comma
        bk = pop(t, 0.12, 0.32, pre=0.35, dip=0.25, s=2.0) * (1 - grow)
        blob = [('e', cx, cy - u * 0.05 + lift, u * 0.32 * bk * sx, u * 0.32 * bk * sy, col)]
        stroke = ('s', [(x, y, w_ * grow) for x, y, w_ in stroke[1]], col)
        dot = ('c', dot[1], dot[2], dot[3] * grow, col)
    return group(n, blob + [stroke, dot], ink_w(e, k), details=hl if grow >= 1 else [], alpha=fade(t, 0.93, 1.0) * clamp(t / 0.03))


def fx_exclaim(t, n, u, e, kw):
    col = rgb(kw.get('color', '#ff4a3a'))
    cx, cy = n / 2, n / 2
    k = pop(t, 0.1, 0.28, pre=0.3, dip=0.2, s=3.0) * shrink(t, 0.7, 0.96)
    sx, sy = squash_stretch(t, 0.1, 0.4)
    shake = u * 0.04 * math.sin(t * 90) * bump(seg(t, 0.28, 0.55))
    ang = kw.get('tilt', -6) + 5 * math.sin(t * 70) * bump(seg(t, 0.28, 0.55))
    lift = -u * 0.15 * smooth(seg(t, 0.72, 1.0))
    piv = (cx, cy + u * 0.75)
    bar = [(cx, cy - u * 0.5, u * 0.28), (cx, cy - u * 0.15, u * 0.22), (cx, cy + u * 0.22, u * 0.11)]
    bar = ('s', xform(bar, *piv, sx, sy, ang, k, shake, lift), col)
    kd = pop(t, 0.16, 0.34, pre=0.3, dip=0.2, s=2.6) * shrink(t, 0.7, 0.96)
    dx, dy = xform([(cx, cy + u * 0.5)], *piv, sx, sy, ang, 1, shake, lift)[0]
    dot = ('c', dx, dy, u * 0.13 * kd, col)
    hl = [('c', *xform([(cx - u * 0.06, cy - u * 0.5)], *piv, sx, sy, ang, k, shake, lift)[0], u * 0.045 * k, light(col, 0.6))]
    im = new(n)
    # surprise ticks burst out around the top on the pop
    ticks = []
    p = seg(t, 0.14, 0.5)
    if 0 < p < 1:
        for a in (-150, -90, -30):
            ar = math.radians(a + ang); o = (cx, cy - u * 0.3 + lift)
            r0, r1 = u * (0.55 + 0.25 * in_quad(p)), u * (0.55 + 0.3 * out_cubic(p))
            if a == -90: continue
            ticks.append(('s', [(o[0] + math.cos(ar) * r0, o[1] + math.sin(ar) * r0, u * 0.03),
                                (o[0] + math.cos(ar) * r1, o[1] + math.sin(ar) * r1, u * 0.08 * bump(p))], col))
    comp(im, group(n, ticks, e * 0.8))
    comp(im, group(n, [bar, dot], ink_w(e, k), details=hl, alpha=fade(t, 0.93, 1.0) * clamp(t / 0.03)))
    return im


def note_shapes(x, y, h, ang, col, double=False):
    """Eighth note (or two beamed notes) with its head centre at (x, y); h = stem height px."""
    hr = h * 0.24
    heads = [(x, y)] + ([(x + h * 0.62, y - h * 0.16)] if double else [])
    out = []
    for hx, hy in heads:
        out.append(('p', [rot(*p, x, y, ang) for p in ellipse_pts(hx, hy, hr * 1.25, hr * 0.92, -22)], col))
        sx = hx + hr * 1.05
        out.append(('s', [rot(sx, hy - hr * 0.1, x, y, ang) + (h * 0.11,), rot(sx, hy - h, x, y, ang) + (h * 0.11,)], col))
    if double:
        a = (x + hr * 1.05, y - h); b = (heads[1][0] + hr * 1.05, heads[1][1] - h)
        out.append(('s', [rot(*a, x, y, ang) + (h * 0.2,), rot(*b, x, y, ang) + (h * 0.2,)], col))
    else:
        sx = x + hr * 1.05
        fl = bez((sx, y - h), (sx + h * 0.45, y - h * 0.62), (sx + h * 0.3, y - h * 0.3), 14, h * 0.15, h * 0.08)
        out.append(('s', [rot(px, py, x, y, ang) + (w,) for px, py, w in fl], col))
    return out


def fx_music_note(t, n, u, e, kw):
    rng = random.Random(kw.get('seed', 19))
    cols = kw.get('colors') or [kw.get('color', '#b58cff'), '#ff5fa8']
    cnt = kw.get('count', 2)
    cx, by = n / 2, n / 2 + u * 0.7                        # notes rise from bottom centre (a mouth / speaker)
    im = new(n)
    for i in range(cnt):
        d0 = 0.02 + 0.32 * i / max(1, cnt - 1); life = 0.64
        p = seg(t, d0, d0 + life)
        if not 0 < p < 1: continue
        k = pop(p, 0.14, 0.36, pre=0.35, dip=0.25, s=2.0) * shrink(p, 0.66, 0.98)
        side = (-1) ** i
        x = cx + side * u * (0.18 + 0.22 * (i // 2)) + side * u * 0.42 * smooth(p) + u * 0.08 * math.sin(p * 2 * math.pi * 1.2 + i)
        y = by - u * 1.1 * out_quad(p)
        ang = 14 * math.sin(p * 2 * math.pi * 1.2 + i + 1)
        h = u * 0.55 * k
        shp = note_shapes(x - h * 0.2, y, h, ang, rgb(cols[i % len(cols)]), double=(i % 2 == 1))
        comp(im, group(n, shp, ink_w(e, k), alpha=fade(p, 0.9, 1.0)))
    return im


# ---------------------------------------------------------------- diagram-style effects (first video: countersteering)

def sub_path(pts, f0, f1):
    """Part of a polyline of (x, y, w) between length fractions f0..f1 (for draw-on / retract)."""
    if f1 <= f0 or len(pts) < 2: return []
    L = [0.0]
    for p, q in zip(pts, pts[1:]): L.append(L[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    tot = L[-1] or 1
    def at(f):
        d = f * tot
        for i in range(1, len(L)):
            if L[i] >= d:
                k = (d - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
                return tuple(lerp(pts[i - 1][j], pts[i][j], k) for j in range(3))
        return pts[-1]
    out = [at(f0)] + [p for p, l in zip(pts, L) if f0 * tot < l < f1 * tot] + [at(f1)]
    return out


def arrow_head(tip, ang, size, col):
    """Triangle arrowhead pointing along `ang` (radians) with its point at `tip`."""
    a, b = ang, size
    return ('p', [(tip[0] + math.cos(a) * b * 0.55, tip[1] + math.sin(a) * b * 0.55),
                  (tip[0] + math.cos(a + 2.35) * b * 0.6, tip[1] + math.sin(a + 2.35) * b * 0.6),
                  (tip[0] + math.cos(a - 2.35) * b * 0.6, tip[1] + math.sin(a - 2.35) * b * 0.6)], col)


def fx_steer_arrow(t, n, u, e, kw):
    """Curved arrow over the top of a circle showing a turn direction (handlebar / steering overlay)."""
    if kw.get('direction') == 'blocked': return stop_bar(t, n, u, e, kw)
    col = rgb(kw.get('color', '#ff5a3c'))
    sgn = 1 if kw.get('direction', 'right') in ('right', 'cw', 1) else -1
    sweep = kw.get('sweep', 130)
    cx, cy = n / 2, n / 2 + u * 0.25
    R = u * 0.62
    # anticipation: a short nudge the opposite way, then the arrow draws on with overshoot, holds, shrinks out
    nudge = -0.06 * bump(seg(t, 0.0, 0.14))
    grow = out_back(seg(t, 0.1, 0.4), 1.6) if t >= 0.1 else 0.0
    k = smooth(seg(t, 0.0, 0.08)) * shrink(t, 0.62, 0.95) * (1 + 0.05 * bump(seg(t, 0.45, 0.62)))
    a_mid = -90 + sgn * sweep * nudge * 3
    a0 = math.radians(a_mid - sgn * sweep / 2)
    span = sweep * max(0.08, grow) * (1 + 0.05 * math.sin(2 * math.pi * 2 * seg(t, 0.4, 0.65)))   # head nudges in the hold
    w = u * 0.17 * k
    pts = []
    m = 40
    for i in range(m + 1):
        f = i / m; a = a0 + sgn * math.radians(span) * f
        pts.append((cx + R * k * math.cos(a), cy + R * k * math.sin(a), w * (0.45 + 0.55 * f)))
    a_end = a0 + sgn * math.radians(span)
    tang = a_end + sgn * math.pi / 2
    tip = (cx + R * k * math.cos(a_end) + math.cos(tang) * w * 0.4, cy + R * k * math.sin(a_end) + math.sin(tang) * w * 0.4)
    head = arrow_head(tip, tang, u * 0.5 * k * min(1.0, 0.25 + grow * 1.5), col)   # head grows with the arc
    return group(n, [('s', pts, col), head], ink_w(e, k), alpha=fade(t, 0.93, 1.0))


def stop_bar(t, n, u, e, kw):
    """steer_arrow(direction='blocked'): a greyed-out turn arrow with a red 'no' sign (ring + slash) slammed over it,
    which shakes 'no'."""
    col = rgb(kw.get('color', '#e8333a'))
    cx, cy = n / 2, n / 2
    lay = new(n)
    # the attempted turn, greyed out, appears first
    ghost = fx_steer_arrow(clamp(t * 0.9), n, u * 0.8, e * 0.8, dict(kw, direction=kw.get('turn', 'right'), color='#a9a2b6'))
    comp(lay, opacity(ghost, 0.85 * fade(t, 0.8, 0.95)))
    k = pop(t, 0.16, 0.36, pre=0.35, dip=0.22, s=2.6) * shrink(t, 0.66, 0.95)
    wig = math.sin(2 * math.pi * 3 * seg(t, 0.34, 0.66)) * (1 - seg(t, 0.34, 0.66)) ** 0.7   # damped 'no' shake
    x = cx + u * 0.3 + u * 0.12 * wig; cy = cy + u * 0.3; R_ = u * 0.42 * k; w = u * 0.12 * k   # sign sits low-right: the arrow stays readable
    ring = [(x + R_ * math.cos(a), cy + R_ * math.sin(a), w) for a in (2 * math.pi * i / 60 for i in range(61))]
    sa = math.radians(45 + 15 * wig)                         # the slash rocks +-15 deg with the shake
    slash = [(x - R_ * math.cos(sa), cy - R_ * math.sin(sa), w), (x + R_ * math.cos(sa), cy + R_ * math.sin(sa), w)]
    comp(lay, group(n, [('s', ring, col), ('s', slash, col)], ink_w(e, k), alpha=fade(t, 0.93, 1.0)))
    return lay


def chaikin(pts, it=4):
    for _ in range(it):
        out = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            out += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        pts = out + [pts[-1]]
    return pts


# top-down tracks in content units (x right, y down), all starting bottom-centre heading up and ending toward the left
PATHS = {
    'tight_left': [(0.3, 0.95), (0.3, 0.2), (0.3, -0.15), (0.05, -0.38), (-0.4, -0.4), (-0.95, -0.4)],
    'wide_arc': [(0.3, 0.95), (0.3, 0.2), (0.4, -0.45), (0.1, -0.85), (-0.5, -0.9), (-0.95, -0.85)],
    'kink_right_then_left': [(0.3, 0.95), (0.3, 0.45), (0.65, 0.22), (0.45, -0.18), (0.05, -0.38), (-0.4, -0.4), (-0.95, -0.4)],
}


def fx_path_line(t, n, u, e, kw):
    """Top-down track diagram: the planned path as a dashed line, then the actual path drawn on with a rider dot at
    its head. planned / actual = a name from PATHS (or a list of (x, y) points in -1..1)."""
    pc = rgb(kw.get('planned_color', '#f4f1ea')); ac = rgb(kw.get('color', '#ff8a1f'))
    cx, cy = n / 2, n / 2
    def track(spec, w):
        pts = PATHS[spec] if isinstance(spec, str) else spec
        return [(cx + x * u, cy + y * u, w) for x, y in chaikin(pts)]
    w = u * 0.06
    plan = track(kw.get('planned', 'tight_left'), w * 0.8)
    act = track(kw.get('actual', 'wide_arc'), w)
    # timing: planned path dashes in, actual path draws on with ease, both erase from the start at the end
    off = smooth(seg(t, 0.82, 0.98))
    pf = out_cubic(seg(t, 0.03, 0.3))
    af = smooth(seg(t, 0.28, 0.78))
    shapes = []
    nd = 14
    for i in range(nd):
        f0, f1 = i / nd, i / nd + 0.55 / nd
        f0, f1 = max(f0, off), min(f1, pf)
        if f1 > f0: shapes.append(('s', sub_path(plan, f0, f1), pc))
    lay = new(n)
    act_s = []
    if af > off + 0.002: act_s.append(('s', sub_path(act, off, af), ac))
    if 0 < t < 0.97 and af > 0.001:                         # rider dot at the head, pops in with the line
        hx, hy, _ = sub_path(act, 0, max(af, 0.002))[-1]
        dk = pop(t, 0.26, 0.4, pre=0.4, dip=0.3, s=2.2) * shrink(t, 0.8, 0.96)
        act_s.append(('c', hx, hy, u * 0.09 * dk, ac))
    if act_s: comp(lay, group(n, act_s, e, shade=False))
    comp(lay, group(n, shapes, e * 0.7, shade=False))      # planned dashes on top so the actual path never hides them
    return opacity(lay, fade(t, 0.84, 1.0))                  # the erase-along-path also fades: no flat leftovers



def fx_lean_arc(t, n, u, e, kw):
    """Lean-angle diagram: a vertical reference, a line that leans to `angle` degrees, and the arc between them
    with a tick at its middle. Pivot = bottom centre (the tyre contact point)."""
    col = rgb(kw.get('color', '#ffd23a')); ref = rgb(kw.get('ref', '#f4f1ea'))
    ang = kw.get('angle', 25) * (-1 if kw.get('side', 'left') == 'left' else 1)
    px, py = n / 2, n / 2 + u * 0.85
    L = u * 1.6 * out_cubic(seg(t, 0.0, 0.24))               # the lean line grows out of the pivot (no pop-in)
    k = smooth(seg(t, 0.0, 0.1)) * shrink(t, 0.62, 0.95)
    # the lean line swings out with anticipation (small opposite lean) and overshoot, then settles
    if t < 0.14: a = -0.15 * ang * bump(seg(t, 0.02, 0.14))
    else: a = ang * out_back(seg(t, 0.14, 0.42), 2.0)
    a += ang * 0.08 * math.sin(2 * math.pi * 2 * seg(t, 0.42, 0.7)) * (1 - seg(t, 0.42, 0.7))
    def ray(deg, length, w0, w1):
        r = math.radians(deg - 90)
        return [(px, py, w0), (px + math.cos(r) * length, py + math.sin(r) * length, w1)]
    w = u * 0.07 * k
    shapes = []
    # dashed vertical reference
    for i in range(5):
        f0, f1 = i / 5, i / 5 + 0.11
        shapes.append(('s', [(px, py - L * k * f0, w * 0.6), (px, py - L * k * f1, w * 0.6)], ref))
    shapes.append(('s', ray(a, L * k, w * 1.4, w * 1.0), col))
    # the angle itself: a pale filled wedge from the vertical to the lean line, edged by a clear arc (no crossing tick)
    Ra = L * 0.36 * k; steps = max(2, int(abs(a) / 2))
    arc = [(px + Ra * math.cos(math.radians(-90 + a * i / steps)), py + Ra * math.sin(math.radians(-90 + a * i / steps)), w * 1.1)
           for i in range(steps + 1)]
    wedge = []
    if abs(a) > 1.5:
        wedge = [('p', [(px, py)] + [(x, y) for x, y, _ in arc], light(col, 0.6))]
        shapes.insert(0, ('s', arc, ref))                   # arc in the reference colour, under the lean line
    shapes.append(('c', px, py, w * 1.3, col))                 # pivot dot
    lay = new(n)
    if wedge: comp(lay, group(n, wedge, 0, shade=False, alpha=0.92 * fade(t, 0.93, 1.0)))
    return comp(lay, group(n, shapes, ink_w(e, k), shade=False, alpha=fade(t, 0.93, 1.0)))


def fx_wobble_lines(t, n, u, e, kw):
    """Short curved motion arcs beside a wheel that wobble ('((( )))'); the wheel sits at the canvas centre."""
    col = rgb(kw.get('color', '#f4f1ea'))
    sides = {'both': (-1, 1), 'left': (-1,), 'right': (1,)}[kw.get('sides', 'both')]
    cx, cy = n / 2, n / 2
    shapes = []
    for s_ in sides:
        for i in range(3):
            d0 = 0.04 + 0.06 * i
            k = pop(seg(t, d0, 1.0), 0.12, 0.32, pre=0.35, dip=0.25, s=2.0) * shrink(t, 0.66 + 0.06 * i, 0.9 + 0.03 * i)
            if k <= 0.01: continue
            wob = 12 * math.sin(2 * math.pi * 3 * t + i * 1.1) * bump(seg(t, 0.2, 0.85))   # the wobble
            r = u * (0.5 + 0.16 * i)
            span = 55 - 8 * i
            m = 16; w = u * (0.1 - 0.015 * i) * k
            base = 0 if s_ > 0 else 180
            pts = []
            for j in range(m + 1):
                f = j / m; a = math.radians(base + wob * s_ + (f - 0.5) * span * k)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a), w * (0.5 + 0.5 * bump(f))))
            shapes.append(('s', pts, col))
    if not shapes: return new(n)
    return group(n, shapes, e * 0.8, shade=False, alpha=fade(t, 0.93, 1.0))


def fx_whoosh(t, n, u, e, kw):
    """Speed swoosh: a big tapered curve that draws on head-first and retracts tail-last, plus two thin trailers.
    angle = travel direction in degrees (0 = moving right)."""
    col = rgb(kw.get('color', '#e8f4ff'))
    ang = kw.get('angle', 0)
    cx, cy = n / 2, n / 2
    lay = new(n)
    curves = [(0.0, 1.0, 0.0), (0.22, 0.55, 0.08), (-0.24, 0.5, 0.12)]   # (y offset, thickness, delay)
    shapes = []
    for oy, th, d0 in curves:
        p = seg(t, 0.04 + d0, 0.8 + d0 * 0.5)
        if not 0 < p < 1: continue
        head = out_cubic(seg(p, 0.0, 0.55)); tail = in_quad(seg(p, 0.25, 1.0))
        base = bez((cx - u * 0.95, cy + u * (0.35 + oy)), (cx - u * 0.1, cy + u * (-0.45 + oy)), (cx + u * 0.9, cy + u * (0.05 + oy)), 40)
        w = u * 0.2 * th * (1 - 0.85 * smooth(seg(p, 0.55, 1.0)))   # thins as it retracts: no blob left
        base = [(x, y, w * (0.1 + 0.9 * (i / 40) ** 1.5)) for i, (x, y, _) in enumerate(base)]
        part = sub_path(base, tail, head)
        if len(part) >= 2: shapes.append(('s', part, col))
    if not shapes: return lay
    lay = group(n, shapes, e * 0.9, shade=False, alpha=fade(t, 0.92, 1.0))
    if ang: lay = lay.rotate(ang, resample=Image.BICUBIC, center=(cx * S, cy * S))
    return lay




# ---------------------------------------------------------------- video 2 (sailing-stones): playa, ice, weather
# Environment effects (ice_pane, dust_storm, flash_flood, rain) enter by spreading / rolling in and leave by receding,
# with only the last ~8% as an alpha fade; they are still empty at t=0 and t=1 (fx/RULES.md 1).

ICE = (178, 228, 244); ICE_DK = (120, 186, 214); WATER = (84, 170, 214); WATER_DK = (52, 128, 176)
DUSTC = (201, 162, 117); MUD = (138, 104, 66); FOAM = (246, 240, 226); ROCKC = (128, 116, 106)


def rock_poly(cx, cy, rx, ry, seed=0, n=24):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + 0.1 * (0.5 * math.sin(2 * a + ph[0]) + 0.35 * math.sin(3 * a + ph[1]) + 0.2 * math.sin(5 * a + ph[2]))
        y = math.sin(a) * ry * r
        pts.append((cx + math.cos(a) * rx * r, cy + (y * 0.7 if y > 0 else y)))
    return pts


def _cells(n, u, seed=5, m=5):
    """Ice panes as a jittered grid (shared corners, so cracks are shared edges), kept inside a round pond."""
    rnd = random.Random(seed); cx = cy = n / 2
    step = 2 * u / m
    P = [[(cx - u + i * step + (rnd.uniform(-0.28, 0.28) * step if 0 < i < m else 0),
           cy - u + j * step + (rnd.uniform(-0.28, 0.28) * step if 0 < j < m else 0)) for j in range(m + 1)] for i in range(m + 1)]
    def clamp_r(p):        # pull points outside the pond's (slightly wobbly) rim onto it: a round pond, not a grid
        dx, dy = p[0] - cx, p[1] - cy; d = math.hypot(dx, dy) or 1; a = math.atan2(dy, dx)
        R = u * (0.97 + 0.04 * math.sin(3 * a + 1) + 0.025 * math.sin(5 * a))
        return p if d <= R else (cx + dx / d * R, cy + dy / d * R)
    cells = []
    for i in range(m):
        for j in range(m):
            q0 = [P[i][j], P[i + 1][j], P[i + 1][j + 1], P[i][j + 1]]
            gx = sum(p[0] for p in q0) / 4; gy = sum(p[1] for p in q0) / 4
            dist = math.hypot(gx - cx, gy - cy) / u
            if dist > 1.12: continue
            q = []
            for a_, b_ in zip(q0, q0[1:] + q0[:1]):
                for k in range(4): q.append(clamp_r((lerp(a_[0], b_[0], k / 4), lerp(a_[1], b_[1], k / 4))))
            ar = 0.5 * abs(sum(q[k][0] * q[k - 1][1] - q[k - 1][0] * q[k][1] for k in range(len(q))))
            if ar < step * step * 0.12: continue
            gx = sum(p[0] for p in q) / len(q); gy = sum(p[1] for p in q) / len(q)
            cells.append((q, (gx, gy), min(1.0, math.hypot(gx - cx, gy - cy) / u), i, j))
    return cells


def _scale_pts(pts, c, k): return [(c[0] + (x - c[0]) * k, c[1] + (y - c[1]) * k) for x, y in pts]


def _jag(p, q, rnd, amt, k=3):
    out = [p]
    for i in range(1, k):
        f = i / k; out.append((lerp(p[0], q[0], f) + rnd.uniform(-amt, amt), lerp(p[1], q[1], f) + rnd.uniform(-amt, amt)))
    return out


def fx_ice_pane(t, n, u, e, kw):
    """The sailing-stones mechanism, one stage per call. stage: water (a shallow pond spreads, ripples) | freeze (thin
    ice grows in from the edge, frost glints) | panes (cracks race along the sheet, it splits into panes) | drift (the
    panes slide downwind, gaps of dark water opening behind). view: top (straight down) | side (low angle, thin sheet
    edge-on near the bottom). direction: left|right|up|down (drift)."""
    if kw.get('view', 'top') == 'side': return _ice_side(t, n, u, e, kw)
    stage = kw.get('stage', 'water')
    rnd = random.Random(kw.get('seed', 5))
    cx = cy = n / 2
    cells = _cells(n, u, kw.get('seed', 5))
    dvec = {'right': (1, 0), 'left': (-1, 0), 'up': (0, -1), 'down': (0, 1)}[kw.get('direction', 'right')]
    out_a = fade(t, 0.92, 1.0)
    im = new(n)
    if stage == 'water':
        g = pop(t, 0.04, 0.4, pre=0.3, dip=0.22, s=1.1) * (1 - 0.15 * smooth(seg(t, 0.85, 1.0)))
        shapes = [('p', _scale_pts(q, (cx, cy), g), WATER) for q, *_ in cells]
        det = []
        for r_i in range(3):                     # ripples running outward
            p = (t * 2.2 + r_i / 3) % 1
            rr = u * g * (0.15 + 0.75 * p); w = u * 0.025 * (1 - p) * g
            if w > 0.3:
                det.append(('s', [(cx + rr * math.cos(a), cy + rr * 0.92 * math.sin(a), w) for a in (2 * math.pi * j / 48 for j in range(49))], light(WATER, 0.45)))
        for j in range(5):                       # sky glints
            gx, gy = cx + u * g * (rnd.uniform(-0.5, 0.5)), cy + u * g * rnd.uniform(-0.5, 0.5)
            L = u * 0.12 * g * (0.6 + 0.4 * math.sin(t * 9 + j))
            det.append(('s', [(gx - L, gy + L * 0.4, u * 0.02 * g), (gx + L, gy - L * 0.4, u * 0.02 * g)], (236, 248, 255)))
        return comp(im, opacity(group(n, shapes, ink_w(e, g) * 0.8, details=det, alpha=0.88), out_a))
    if stage == 'freeze':
        g = smooth(seg(t, 0.0, 0.06))
        shapes, det = [], []
        for q, c, dist, i, j in cells:
            f = smooth(seg(t, 0.06 + 0.45 * (1 - dist), 0.2 + 0.45 * (1 - dist)))    # edge cells freeze first
            shapes.append(('p', q, mixc(WATER, ICE, f)))
            if f > 0.5:                                                               # frost needles on frozen cells
                for k_ in range(2):
                    a = rnd.uniform(0, math.pi); L = u * 0.08 * smooth(seg(f, 0.5, 1))
                    x, y = c[0] + rnd.uniform(-0.1, 0.1) * u, c[1] + rnd.uniform(-0.1, 0.1) * u
                    det.append(('s', [(x - math.cos(a) * L, y - math.sin(a) * L, u * 0.012), (x + math.cos(a) * L, y + math.sin(a) * L, u * 0.012)], WHITE))
            else: rnd.uniform(0, 1); rnd.uniform(0, 1); rnd.uniform(0, 1); rnd.uniform(0, 1); rnd.uniform(0, 1); rnd.uniform(0, 1)
        tw = bump(seg(t, 0.62, 0.9))                                                   # a sparkle when the sheet is whole
        if tw > 0.02: det.append(('p', star_pts(cx + u * 0.3, cy - u * 0.35, 4, u * 0.14 * tw, u * 0.03 * tw), WHITE))
        return opacity(group(n, [('p', _scale_pts(q, (cx, cy), 0.9 + 0.1 * g), col) for (_, q, col) in shapes], e * 0.8 * g, details=det, alpha=0.9 * g), out_a)
    # panes / drift share the cracked sheet
    gap = 0.0; shift = [(0, 0)] * len(cells); rot_ = [0] * len(cells)
    if stage == 'panes':
        crack_p = seg(t, 0.06, 0.55); gap = smooth(seg(t, 0.5, 0.8)) * 0.07
        g = smooth(seg(t, 0.0, 0.06))
    else:   # drift: panes slide downwind, upwind rows later, with a little spin
        crack_p = 1.0; gap = 0.07; g = smooth(seg(t, 0.0, 0.06))
        for k_, (q, c, dist, i, j) in enumerate(cells):
            proj = ((c[0] - cx) * dvec[0] + (c[1] - cy) * dvec[1]) / u          # downwind panes move first
            p = seg(t, 0.08 + 0.18 * (1 - proj) / 2, 0.9)
            back = -0.03 * bump(seg(p, 0, 0.15))                                 # anticipation: a tiny creak back
            d = u * (0.55 * in_quad(p) * (1 + 0.15 * math.sin(i * 1.7 + j)) + back)
            shift[k_] = (dvec[0] * d - dvec[1] * d * 0.08 * math.sin(i + j), dvec[1] * d + dvec[0] * d * 0.08 * math.sin(i * 2 + j))
            rot_[k_] = 6 * p * math.sin(i * 3.1 + j * 1.3)
    shapes, det = [], []
    under = [('p', q, WATER_DK) for q, *_ in cells]
    for k_, (q, c, dist, i, j) in enumerate(cells):
        qq = _scale_pts(q, c, (1 - gap) * (0.9 + 0.1 * g))
        qq = [rot(x, y, c[0], c[1], rot_[k_]) for x, y in qq]
        qq = [(x + shift[k_][0], y + shift[k_][1]) for x, y in qq]
        shapes.append(('p', qq, ICE))
        cc = (c[0] + shift[k_][0], c[1] + shift[k_][1])
        L = u * 0.07
        det.append(('s', [(cc[0] - L, cc[1] + L * 0.5, u * 0.016), (cc[0] + L, cc[1] - L * 0.5, u * 0.016)], WHITE))
    lay = new(n)
    if gap > 0.001:   # dark water shows in the opening gaps (and behind drifting panes)
        comp(lay, group(n, under, 0, alpha=0.75 * smooth(seg(gap, 0, 0.03))))
    comp(lay, group(n, shapes, e * 0.8, details=det, alpha=0.9))
    if stage == 'panes' and 0 < crack_p and gap < 0.069:   # white cracks race along the shared edges, from the centre
        cr = []
        rc = random.Random(9)
        for q, c, dist, i, j in cells:
            for a_, b_ in ((q[0], q[4]), (q[4], q[8])):
                md = math.hypot((a_[0] + b_[0]) / 2 - cx, (a_[1] + b_[1]) / 2 - cy) / u
                f = seg(crack_p, md * 0.7, md * 0.7 + 0.3)
                if f <= 0: continue
                pts = [(x, y, u * 0.028) for x, y in _jag(a_, b_, rc, u * 0.03)] + [(b_[0], b_[1], u * 0.028)]
                part = sub_path(pts, 0, f)
                if len(part) >= 2: cr.append(('s', part, WHITE))
        if cr: comp(lay, group(n, cr, e * 0.5, shade=False, alpha=1 - smooth(seg(gap, 0.0, 0.07))))
    return opacity(lay, out_a * g)


def _ice_side(t, n, u, e, kw):
    """Low-angle view: a phone-thin translucent sheet lying on the playa near the bottom of the canvas."""
    stage = kw.get('stage', 'drift'); sgn = -1 if kw.get('direction', 'right') == 'left' else 1
    gy = n * 0.74; th = u * 0.09; depth = u * 0.34
    g = smooth(seg(t, 0.0, 0.08)); out_a = fade(t, 0.92, 1.0)
    shapes, det = [], []
    if stage == 'water':
        w = u * 2 * pop(t, 0.04, 0.4, pre=0.3, dip=0.2, s=1.1)
        top = [(n / 2 - w / 2 + w * i / 30, gy - depth + u * 0.012 * math.sin(i * 1.3 + t * 30)) for i in range(31)]
        shapes.append(('p', top + [(n / 2 + w / 2, gy), (n / 2 - w / 2, gy)], WATER))
        det.append(('s', [(x, y + depth * 0.3, u * 0.012) for x, y in top[3:-3]], light(WATER, 0.5)))
        return opacity(group(n, shapes, e * 0.7, details=det, alpha=0.85), out_a)
    panes = 6; pw = 2.1 * u / panes
    for i in range(panes):
        x0 = n / 2 - 1.05 * u + i * pw
        d = 0.0
        if stage in ('drift',):
            p = seg(t, 0.08 + 0.04 * (panes - 1 - i if sgn > 0 else i), 0.92)
            d = sgn * u * (0.5 * in_quad(p) - 0.03 * bump(seg(p, 0, 0.15)))
        gap = u * 0.03 if stage in ('panes', 'drift') else 0
        a, b = x0 + gap / 2 + d, x0 + pw - gap / 2 + d
        tilt = (u * 0.02 * math.sin(i * 2.3)) if stage in ('panes', 'drift') else 0
        top = [(a + depth * 0.5, gy - depth + tilt), (b + depth * 0.5, gy - depth - tilt), (b, gy - th), (a, gy - th)]
        shapes.append(('p', top, ICE))
        shapes.append(('p', [(a, gy - th), (b, gy - th), (b, gy), (a, gy)], ICE_DK))
        det.append(('s', [(a + depth * 0.5 + pw * 0.1, gy - depth * 0.75 + tilt, u * 0.012), (b + depth * 0.2, gy - depth * 0.75 - tilt, u * 0.012)], WHITE))
        if stage == 'freeze':
            f = smooth(seg(t, 0.1 + 0.08 * abs(i - panes / 2), 0.5 + 0.08 * abs(i - panes / 2)))
            shapes[-2] = ('p', top, mixc(WATER, ICE, f))
    return opacity(group(n, shapes, e * 0.7 * g, details=det, alpha=0.9), out_a * g)


def fx_ice_crack(t, n, u, e, kw):
    """White crack lines racing out across a sheet of ice from the centre, branching; they erase from the centre out."""
    rnd = random.Random(kw.get('seed', 11)); col = rgb(kw.get('color', '#ffffff'))
    cx, cy = n / 2, n / 2
    paths = []
    for i in range(7):
        a = 2 * math.pi * i / 7 + rnd.uniform(-0.3, 0.3); L = u * rnd.uniform(0.7, 1.0)
        pts = [(cx, cy)]
        for k in range(1, 7):
            f = k / 6; aa = a + rnd.uniform(-0.35, 0.35)
            pts.append((cx + math.cos(aa) * L * f, cy + math.sin(aa) * L * f * 0.8))
        paths.append((0.0, pts))
        j = rnd.randint(2, 4); ba = a + rnd.choice([-1, 1]) * rnd.uniform(0.5, 0.9); bl = L * 0.35
        b0 = pts[j]; paths.append((j / 6, [b0, (b0[0] + math.cos(ba) * bl * 0.5, b0[1] + math.sin(ba) * bl * 0.4), (b0[0] + math.cos(ba) * bl, b0[1] + math.sin(ba) * bl * 0.8)]))
    shapes = []
    crack = bump(seg(t, 0.0, 0.08)) * 0.6                     # anticipation: a small star-burst at the centre first
    if crack > 0.02: shapes.append(('p', star_pts(cx, cy, 5, u * 0.09 * crack, u * 0.03 * crack), col))
    head_all = out_cubic(seg(t, 0.06, 0.45)); tail_all = in_quad(seg(t, 0.7, 0.98))
    for d0, pts in paths:
        head = seg(head_all, d0, 1.0); tail = seg(tail_all, d0 * 0.5, 1.0)
        w = u * 0.035 * (1 if d0 == 0 else 0.7)
        wp = [(x, y, w * (1 - 0.6 * k / (len(pts) - 1))) for k, (x, y) in enumerate(pts)]
        part = sub_path(wp, tail, head)
        if len(part) >= 2: shapes.append(('s', part, col))
    if not shapes: return new(n)
    return group(n, shapes, e * 0.55, shade=False, alpha=fade(t, 0.94, 1.0))


def fx_sliding_rock(t, n, u, e, kw):
    """Rocks gliding over the playa, each carving a groove trail. path: 'away' (from the bottom toward the horizon at
    the canvas middle, shrinking) or a list of [x, y] points in canvas fractions (0..1). count: rocks (spread across).
    sprite: rock | fridge. trail: draw the groove (default True). Rocks creak back, glide (ease in-out), then stop."""
    path = kw.get('path', 'away'); cnt = int(kw.get('count', 1)); trail = kw.get('trail', True)
    sprite = kw.get('sprite', 'rock'); rnd = random.Random(kw.get('seed', 21))
    lay_t, lay_r = [], []
    g_in = smooth(seg(t, 0.0, 0.08)); out_a = fade(t, 0.92, 1.0)
    for i in range(cnt):
        off = (i - (cnt - 1) / 2) / max(1, cnt - 1) if cnt > 1 else 0.0
        if path == 'away':
            p0 = (n / 2 + off * u * 1.5, n / 2 + u * (0.8 - 0.25 * abs(off))); p1 = (n / 2 + off * u * 0.55, n / 2 - u * 0.15)
            k0, k1 = 1.0, 0.45
        else:
            pts = [(x * n, y * n) for x, y in path]
            p0 = (pts[0][0] + off * u * 0.4, pts[0][1] + off * u * 0.3); p1 = (pts[-1][0] + off * u * 0.4, pts[-1][1] + off * u * 0.3)
            k0 = k1 = 1.0
        d0 = 0.06 * abs(off) + rnd.uniform(0, 0.08)
        p = seg(t, 0.06 + d0, 0.86)
        mv = smooth(p) - 0.04 * bump(seg(p, 0.0, 0.18))          # creak back, then glide
        x = lerp(p0[0], p1[0], mv); y = lerp(p0[1], p1[1], mv); k = lerp(k0, k1, mv) * (0.5 if cnt > 2 else 1.0)
        rx = u * 0.25 * k; ry = u * 0.19 * k
        wob = 3 * math.sin(t * 40 + i) * bump(p)
        if trail and mv > 0.01:     # groove: darker clay with a light rim, narrowing toward the horizon
            m = 16; tp, rim = [], []
            for j in range(m + 1):
                f = mv * j / m; kk = lerp(k0, k1, f) * (0.5 if cnt > 2 else 1.0)
                tx, ty = lerp(p0[0], p1[0], f), lerp(p0[1], p1[1], f) + u * 0.1 * kk
                tp.append((tx, ty, u * 0.2 * kk)); rim.append((tx, ty - u * 0.07 * kk, u * 0.035 * kk))
            lay_t.append(('s', tp, (150, 118, 86))); lay_t.append(('s', rim, (226, 198, 160)))
        sq = 1 + 0.08 * bump(seg(p, 0.0, 0.18))                      # a little squash on the creak
        if sprite == 'fridge':
            body = [(x - rx * 0.7, y - ry * 3.2), (x + rx * 0.7, y - ry * 3.2), (x + rx * 0.7, y + ry * 0.6), (x - rx * 0.7, y + ry * 0.6)]
            lay_r.append(('p', [rot(a, b, x, y, wob) for a, b in body], (236, 240, 244)))
        else:
            lay_r.append(('p', [rot(a, b, x, y, wob) for a, b in rock_poly(x, y, rx * sq, ry / sq, seed=i + 3)], ROCKC))
    im = new(n)
    if lay_t: comp(im, group(n, lay_t, 0, shade=False, alpha=0.85 * out_a * g_in))
    if lay_r: comp(im, group(n, lay_r, e, alpha=out_a * g_in))
    return im


def fx_gps_ping(t, n, u, e, kw):
    """Tracker ping: a green dot pops in and pulses while radar rings expand from it (3 rings, twice)."""
    col = rgb(kw.get('color', '#46d66e')); cx, cy = n / 2, n / 2
    k = pop(t, 0.05, 0.25, pre=0.35, dip=0.2, s=2.0) * shrink(t, 0.82, 0.97)
    shapes = []
    for c in range(2):
        for r_i in range(3):
            st = 0.12 + c * 0.32 + r_i * 0.08
            p = seg(t, st, st + 0.36)
            if not 0 < p < 1: continue
            rr = u * (0.15 + 0.85 * out_cubic(p)); w = u * 0.07 * (1 - smooth(p)) * (1 - 0.2 * r_i)
            if w > 0.3: shapes.append(('s', [(cx + rr * math.cos(a), cy + rr * math.sin(a), w) for a in (2 * math.pi * j / 64 for j in range(65))], col))
    dot = u * 0.16 * k * (1 + 0.12 * math.sin(t * 2 * math.pi * 4) * bump(seg(t, 0.25, 0.8)))
    im = new(n)
    if shapes: comp(im, group(n, shapes, e * 0.6, shade=False, alpha=fade(t, 0.92, 1.0)))
    if dot > 0.3: comp(im, group(n, [('c', cx, cy, dot, col)], ink_w(e, k), details=[('c', cx - dot * 0.3, cy - dot * 0.3, dot * 0.3, light(col, 0.6))]))
    return im


def fx_year_badge(t, n, u, e, kw):
    """A UI tag for the top third: white Poppins Bold on a plum pill. label (e.g. '1948', 'MONTH 1'). Pops in with a
    squash, bobs gently, shrinks out."""
    from PIL import ImageFont
    label = str(kw.get('label', '1948')); col = rgb(kw.get('color', '#5c2a6b'))
    cx, cy = n / 2, n / 2
    k = pop(t, 0.06, 0.22, pre=0.3, dip=0.18, s=1.8) * shrink(t, 0.84, 0.98)
    if k <= 0.01: return new(n)
    sx = 1 + 0.12 * bump(seg(t, 0.06, 0.16)); sy = 2 - sx
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine', 'fonts', 'Poppins-Bold.ttf')
    fpx = int(u * 0.3 * S)
    f = ImageFont.truetype(fp, fpx); tw = f.getlength(label) / S
    if tw > u * 1.55: f = ImageFont.truetype(fp, int(fpx * u * 1.55 / tw)); tw = u * 1.55
    w = (tw + u * 0.36) * k * sx; h = u * 0.42 * k * sy
    bob = u * 0.025 * math.sin(2 * math.pi * 1.5 * seg(t, 0.22, 0.84))
    pill = [(cx + (w / 2 - h / 2) * (1 if math.cos(a) > 0 else -1) + h / 2 * math.cos(a), cy + bob + h / 2 * math.sin(a))
            for a in (2 * math.pi * j / 48 for j in range(48))]
    lay = group(n, [('p', pill, col)], ink_w(e, k), details=[('s', [(cx - w / 2 + h * 0.4, cy + bob - h * 0.3, h * 0.08), (cx + w / 2 - h * 0.6, cy + bob - h * 0.3, h * 0.08)], light(col, 0.25))])
    txt = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((cx * S, (cy + bob) * S + u * 0.02 * S), label, font=f, fill=WHITE, anchor='mm')
    tk = txt.resize((max(1, int(txt.width * k * sx)), max(1, int(txt.height * k * sy))), Image.LANCZOS)
    lay.alpha_composite(tk, (int(cx * S - tk.width / 2), int((cy + bob) * S - tk.height / 2 + (1 - k * sy) * 0)))
    return lay


def fx_dust_storm(t, n, u, e, kw):
    """A brown wall of dust rolls across (direction=right|left), churning, buries the frame, then settles to the
    ground and clears. Fills the whole canvas at the peak (place it full-frame)."""
    rnd = random.Random(kw.get('seed', 31)); col = rgb(kw.get('color', '#c9a275'))
    sgn = -1 if kw.get('direction', 'right') == 'left' else 1
    front = lerp(-0.25 * n, 1.35 * n, smooth(seg(t, 0.06, 0.6)))           # front x in travel coordinates
    top = n * (0.08 + 0.85 * smooth(seg(t, 0.72, 0.97)))                    # the cloud top sinks while it settles
    wisp = bump(seg(t, 0.0, 0.12))                                          # anticipation: a few wisps run ahead
    X = (lambda x: x) if sgn > 0 else (lambda x: n - x)
    shapes, caps = [], []
    if front > 0:
        body = [(X(-10), top + n * 0.1), (X(min(front, n + 10)), top + n * 0.1), (X(min(front, n + 10)), n + 10), (X(-10), n + 10)]
        shapes.append(('p', body, col))
    for i in range(14):                                                     # churning billows along the front and top
        a = i / 13
        y = lerp(top + n * 0.05, n * 0.98, a)
        r = n * (0.11 + 0.05 * math.sin(i * 2.1 + t * 18))
        x = front + n * 0.06 * math.sin(a * 5 + t * 14) - r * 0.4
        if x > -r: shapes.append(('c', X(x), y, r, col)); caps.append(('c', X(x - r * 0.25), y - r * 0.3, r * 0.45, light(col, 0.18)))
    for i in range(int(n / 60) + 4):
        x = (i / (n / 60 + 3)) * min(front, n + 10)
        r = n * (0.09 + 0.03 * math.sin(i * 1.3 + t * 11))
        y = top + n * 0.08 + n * 0.025 * math.sin(i + t * 16)
        if r > 1 and x < front: shapes.append(('c', X(x), y, r, col)); caps.append(('c', X(x - r * 0.2), y - r * 0.35, r * 0.4, light(col, 0.18)))
    if wisp > 0.02:
        for i in range(3):
            x = n * (0.05 + 0.12 * i) * wisp; y = n * (0.85 - 0.08 * i)
            shapes.append(('e', X(x), y, n * 0.06 * wisp, n * 0.025 * wisp, col))
    specks = []
    for i in range(40):                                                     # grit streaking through the cloud
        x = (rnd.uniform(0, 1) * n + t * n * 3 * (0.6 + rnd.uniform(0, 0.8))) % (n * 1.2) - n * 0.1
        y = rnd.uniform(top + n * 0.1, n)
        if x < front - n * 0.05: specks.append(('s', [(X(x), y, n * 0.006), (X(x - n * 0.04), y + n * 0.004, n * 0.003)], mixc(col, INK, 0.45)))
    if not shapes: return new(n)
    lay = group(n, shapes, e, details=caps + specks)
    return opacity(lay, 0.95 * fade(t, 0.92, 1.0))


def fx_flash_flood(t, n, u, e, kw):
    """A muddy wall of water rushes in (direction=right|left) with a foaming crest, fills the bottom of the frame with
    a choppy brown flood, then recedes. Ground = canvas bottom; place it full-frame."""
    col = rgb(kw.get('color', '#8a6a45')); sgn = -1 if kw.get('direction', 'right') == 'left' else 1
    X = (lambda x: x) if sgn > 0 else (lambda x: n - x)
    front = lerp(-0.2 * n, 1.25 * n, smooth(seg(t, 0.08, 0.55)))
    level = n * (1 - 0.42 * smooth(seg(t, 0.1, 0.5)) + 0.42 * smooth(seg(t, 0.78, 0.98)))   # water surface y
    crest = n * 0.3 * bump(seg(t, 0.08, 0.6))
    trickle = bump(seg(t, 0.0, 0.12))                                       # anticipation: a thin trickle first
    surf, foam = [], []
    m = 40
    for j in range(m + 1):
        x = -10 + (front + 10) * j / m
        dist = (front - x) / n
        hump = crest * math.exp(-((dist - 0.08) / 0.09) ** 2)                 # the tall wave just behind the front
        y = level - hump + n * 0.012 * math.sin(j * 1.1 + t * 40)
        surf.append((X(x), y))
    shapes, det = [], []
    if front > 0 and level < n:
        shapes.append(('p', surf + [(X(front), n + 10), (X(-10), n + 10)], col))
        det.append(('p', [(x, y + n * 0.03) for x, y in surf] + [(x, y + n * 0.06) for x, y in surf[::-1]], light(col, 0.18)))
        for j in range(0, m, 3):                                             # foam streaks riding the surface
            x, y = surf[j]
            det.append(('s', [(x - sgn * n * 0.03, y + n * 0.008, n * 0.008), (x + sgn * n * 0.01, y - n * 0.004, n * 0.012)], FOAM))
        if crest > 1:                                                        # curling white crest at the front
            cxp = front - n * 0.04
            for i in range(5):
                a = i / 4
                foam.append(('c', X(cxp - n * 0.05 * a), level - crest * (0.95 - 0.35 * a) + n * 0.01 * math.sin(t * 30 + i), n * (0.035 - 0.004 * i) * min(1, crest / (n * 0.08)), FOAM))
    if trickle > 0.02 and front < n * 0.2:
        shapes.append(('e', X(n * 0.05 * trickle), n * 0.98, n * 0.08 * trickle, n * 0.015 * trickle, col))
    if not shapes: return new(n)
    lay = group(n, shapes, e, details=det)
    if foam: comp(lay, group(n, foam, e * 0.7))
    return opacity(lay, fade(t, 0.92, 1.0))


def fx_rain(t, n, u, e, kw):
    """Slanted rain streaks falling over the whole canvas, with little splash ticks at the bottom. angle (deg from
    vertical, default 15), density (default 1). Builds up, pours, eases off."""
    rnd = random.Random(kw.get('seed', 41)); col = rgb(kw.get('color', '#9fd0ff'))
    ang = math.radians(kw.get('angle', 15)); cnt = int(70 * kw.get('density', 1.0))
    amt = smooth(seg(t, 0.0, 0.2)) * (1 - smooth(seg(t, 0.8, 1.0)))
    L = n * 0.09; w = n * 0.007; sp = 2.6
    shapes, splashes = [], []
    for i in range(cnt):
        if rnd.uniform(0, 1) > amt: rnd.uniform(0, 1); rnd.uniform(0, 1); continue
        x0 = rnd.uniform(-0.2, 1.1) * n; ph = rnd.uniform(0, 1)
        f = (ph + t * sp * (0.85 + 0.3 * (i % 3) / 2)) % 1
        y = -L + f * (n * 1.0 + L); x = x0 + math.tan(ang) * y
        shapes.append(('s', [(x - math.sin(ang) * L, y - math.cos(ang) * L, w * 0.4), (x, y, w)], col))
        if f > 0.93:
            s = bump(seg(f, 0.93, 1.0))
            splashes.append(('e', x, n * 0.985, n * 0.018 * s, n * 0.006 * s, col))
    if not shapes: return new(n)
    return group(n, shapes + splashes, e * 0.35, shade=False, alpha=0.9 * fade(t, 0.95, 1.0))

NAMES = {
    'explosion': (fx_explosion, 'puffy fire cloud + white flash core + sparks, cools to smoke and rises. color, core, smoke'),
    'impact_star': (fx_impact_star, 'spiky hit star + impact ticks. color, inner, points, angle'),
    'dust_puff': (fx_dust_puff, 'ground puffs rolling out sideways. color, direction=both|left|right'),
    'speed_lines': (fx_speed_lines, 'streaks behind a moving thing. color, count, angle (travel direction, deg)'),
    'sweat_drop': (fx_sweat_drop, 'drop forms, wobbles, slides down. color, flip'),
    'anger_vein': (fx_anger_vein, 'four-arc anger mark that throbs twice. color'),
    'glow_eyes': (fx_glow_eyes, 'two glowing eye discs with a halo. color, gap, radius'),
    'sparkle': (fx_sparkle, 'staggered twinkling 4-point stars. color, count'),
    'splash': (fx_splash, 'water crown + ballistic drops + ring. color'),
    'question_mark': (fx_question_mark, 'popping, wobbling ?. color, tilt'),
    'exclaim': (fx_exclaim, 'popping, shaking ! with surprise ticks. color, tilt'),
    'music_note': (fx_music_note, 'notes rising and swaying. colors, count'),
    'steer_arrow': (fx_steer_arrow, 'curved arrow showing a turn direction, or a red stop bar. direction=left|right|blocked, color, sweep (deg)'),
    'path_line': (fx_path_line, 'top-down track: dashed planned path + actual path drawn on with a rider dot. planned, actual (tight_left|wide_arc|kink_right_then_left or points), color, planned_color'),
    'lean_arc': (fx_lean_arc, 'lean-angle diagram: vertical ref, leaning line, arc + tick; pivot at bottom centre. angle (deg), side=left|right, color, ref'),
    'wobble_lines': (fx_wobble_lines, 'wobbling motion arcs beside a wheel at the centre. color, sides=both|left|right'),
    'whoosh': (fx_whoosh, 'tapered speed swoosh with two trailers. color, angle (travel direction, deg)'),
    'ice_pane': (fx_ice_pane, 'the ice mechanism: stage=water|freeze|panes|drift, view=top|side, direction=left|right|up|down, seed'),
    'ice_crack': (fx_ice_crack, 'white crack lines racing out from the centre and branching. color, seed'),
    'sliding_rock': (fx_sliding_rock, "rocks gliding with a groove trail. path='away' or [[x, y], ...] canvas fractions, count, sprite=rock|fridge, trail"),
    'gps_ping': (fx_gps_ping, 'green tracker dot with expanding radar rings. color'),
    'year_badge': (fx_year_badge, "plum pill UI tag with white Poppins Bold text. label, color"),
    'dust_storm': (fx_dust_storm, 'brown wall of dust rolls across, buries the frame, settles. direction=right|left, color'),
    'flash_flood': (fx_flash_flood, 'muddy wall of water with a foam crest, floods the bottom, recedes. direction=right|left, color'),
    'rain': (fx_rain, 'slanted rain streaks with splash ticks. angle, density, color'),
}


def render(name, t, size=512, **kw):
    """Return a size x size RGBA image of effect `name` at life fraction t (0..1)."""
    if name not in NAMES: raise KeyError(f'unknown fx {name!r}; known: {", ".join(NAMES)}')
    n = int(size); t = clamp(float(t))
    u = n / 2 * 0.9 * kw.get('scale', 1.0)
    e = kw.get('line', 5.0 if n >= 160 else max(2.0, n / 32))   # mean ink px; thin 0.5x / thick 1.5x (cast props ~10*scale)
    im = NAMES[name][0](t, n, u, e, kw)
    return im.resize((n, n), Image.LANCZOS)


if __name__ == '__main__':
    name, t = sys.argv[1], float(sys.argv[2])
    size = int(sys.argv[3]) if len(sys.argv) > 4 else 512
    render(name, t, size).save(sys.argv[-1])

# Procedural 2D cartoon effects for the shorts pipeline (flat colour + thin dark ink outline, same style as
# stickman/scripts/stickman.py). Contract (PIPELINE.md > FX):
#     render(name, t, size, **kw) -> RGBA PIL.Image  (size x size), t runs 0..1 over the effect's life.
# Every effect is empty at t=0 and t=1 and goes: anticipation (small build / squash) -> peak (ease + overshoot)
# -> fade (shrink + alpha), see fx/RULES.md.
# Common kwargs: color (hex or rgb), scale (content size, 1 = fills ~90% of the canvas), line (outline px in
# the OUTPUT image, default scales with size), seed (layout variation). Effect-specific kwargs are listed in NAMES.
# usage: python fx.py <name> <t> [size] out.png
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter

S = 4                                   # supersampling, like stickman.py
INK = (18, 16, 26)                      # #12101a


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


def shape(d, sh, e, col=None):
    k = sh[0]; c = col or sh[-1]
    if k == 'c':
        _, x, y, r, _c = sh
        if r < 0.3: return
        r = (r + min(e, r * 0.6)) * S                      # tiny shapes get a thinner line: never a lone ink dot
        d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=c)
    elif k == 'e':
        _, x, y, rx, ry, _c = sh
        if min(rx, ry) < 0.3: return
        e = min(e, min(rx, ry) * 0.6); rx = (rx + e) * S; ry = (ry + e) * S
        d.ellipse((x * S - rx, y * S - ry, x * S + rx, y * S + ry), fill=c)
    elif k == 's':
        pts = sh[1]
        if not pts: return
        wmin = min(p[2] for p in pts)
        if max(p[2] for p in pts) < 0.3: return
        e = min(e, max(p[2] for p in pts) * 0.5)
        for x, y, w in resample(pts, max(0.4, (wmin + 2 * e) * 0.2)):
            r = (w / 2 + e) * S
            if r > 0: d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=c)
    elif k == 'p':
        P = [(x * S, y * S) for x, y in sh[1]]
        if len(P) < 3: return
        d.polygon(P, fill=c)
        if e > 0:
            w = max(1, int(round(2 * e * S)))
            d.line(P + [P[0]], fill=c, width=w, joint='curve')
            r = e * S
            for x, y in P: d.ellipse((x - r, y - r, x + r, y + r), fill=c)


def group(n, shapes, e, details=(), alpha=1.0, ink=INK):
    """Draw one outlined silhouette layer. `details` are extra shapes drawn after the fills with no outline."""
    lay = new(n); d = ImageDraw.Draw(lay)
    if e > 0:
        for sh in shapes: shape(d, sh, e, ink)
    for sh in shapes: shape(d, sh, 0)
    for sh in details: shape(d, sh, 0)
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
            r = u * (0.26 - 0.1 * f) * grow * shrink(t, 0.42 + 0.08 * i, 0.86 + 0.03 * i) * rng.uniform(0.9, 1.1)
            x = cx + s * u * (0.08 + 0.95 * f * go)
            y = gy - r * (1 - 0.35 * squash) - u * 0.22 * out_quad(seg(t, 0.15, 1)) * (1 - f * 0.5)
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
    col = rgb(kw.get('color', '#8fd8ff'))
    flip = -1 if kw.get('flip', False) else 1
    k = pop(t, 0.12, 0.3, pre=0.4, dip=0.3, s=2.0)
    wob = 0.06 * math.sin(2 * math.pi * 2.5 * seg(t, 0.3, 0.55)) * fade(t, 0.35, 0.55)
    creep = 0.12 * smooth(seg(t, 0.28, 0.45))               # slow creep while it gathers weight
    slide = creep + 0.88 * in_quad(seg(t, 0.45, 0.9))
    hold = 0.12 * bump(seg(t, 0.36, 0.48)) - 0.05 * bump(seg(t, 0.48, 0.58))                # squash wide just before it lets go (anticipation)
    stretch = 0.32 * bump(seg(t, 0.46, 1.0))
    sx = (1 + wob + hold - 0.15 * stretch) * k * shrink(t, 0.7, 0.96)
    sy = (1 - wob - hold + stretch) * k * shrink(t, 0.7, 0.96)
    cx = n / 2 + flip * u * 0.12 * slide
    cy = n / 2 - u * 0.3 + u * 0.75 * slide
    r = u * 0.3
    body = ('p', teardrop(cx, cy, r, r * 2.2, ang=flip * -12 * slide, sx=sx, sy=sy), col)
    hl = ('e', cx - r * 0.38 * sx, cy - r * 0.15 * sy, r * 0.17 * sx, r * 0.3 * sy, light(col, 0.75))
    return group(n, [body], ink_w(e, k), details=[hl], alpha=fade(t, 0.92, 1.0) * clamp(t / 0.03))


def fx_anger_vein(t, n, u, e, kw):
    col = rgb(kw.get('color', '#ff3b4a'))
    cx, cy = n / 2, n / 2
    k = pop(t, 0.1, 0.27, pre=0.35, dip=0.2, s=2.2)
    for pk in (0.4, 0.55, 0.7):                             # three throbs through the hold
        k *= 1 + 0.15 * bump(seg(t, pk - 0.05, pk + 0.07)) ** 2
    k *= shrink(t, 0.7, 0.96)
    jit = 4 * math.sin(t * 60) * bump(seg(t, 0.3, 0.75))
    strokes = []
    R = u * 0.7 * k
    for q in (45, 135, 225, 315):
        a1, a2 = math.radians(q - 38 + jit), math.radians(q + 38 + jit)
        am = math.radians(q + jit)
        p0 = (cx + R * math.cos(a1), cy + R * math.sin(a1))
        p2 = (cx + R * math.cos(a2), cy + R * math.sin(a2))
        p1 = (cx + R * 0.18 * math.cos(am), cy + R * 0.18 * math.sin(am))
        pts = bez(p0, p1, p2, 28)
        w = u * 0.17 * k
        strokes.append(('s', [(x, y, w * (0.55 + 0.45 * bump(i / 28))) for i, (x, y, _) in enumerate(pts)], col))
    return group(n, strokes, ink_w(e, k), alpha=fade(t, 0.92, 1.0) * clamp(t / 0.03))


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
    # halo: flat cel-style rings (no blur; DRAWING_RULES 1), two steps of the eye colour at low alpha
    for f, a in ((1.75, 0.28), (1.35, 0.45)):
        rings = [('p', almond(cx + s_ * gap, cy, r * f * flick, r * 0.62 * f * max(o, 0.3) * flick, -s_ * slant), col)
                 for s_ in (-1, 1)]
        comp(im, group(n, rings, 0, alpha=a * glow))
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
    rp = seg(t, 0.5, 1.0)
    if 0 < rp < 1:
        rr = u * (0.4 + 0.5 * out_cubic(rp)); w = u * 0.04 * (1 - rp)
        ring = [(cx + rr * math.cos(a), by + rr * 0.2 * math.sin(a), w)
                for a in (2 * math.pi * j / 64 for j in range(65))]
        comp(im, group(n, [('s', ring, light(col, 0.3))], e * 0.6 * (1 - rp), alpha=fade(rp, 0.3, 1.0)))
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
    cols = kw.get('colors') or [kw.get('color', '#a774ff'), '#2fa8ec', '#ff5fa8']
    cnt = kw.get('count', 3)
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
}


def render(name, t, size=512, **kw):
    """Return a size x size RGBA image of effect `name` at life fraction t (0..1)."""
    if name not in NAMES: raise KeyError(f'unknown fx {name!r}; known: {", ".join(NAMES)}')
    n = int(size); t = clamp(float(t))
    u = n / 2 * 0.9 * kw.get('scale', 1.0)
    e = kw.get('line', 3.0 if n >= 96 else max(1.5, n / 32))   # same px as the stickman's ~3 px line
    im = NAMES[name][0](t, n, u, e, kw)
    return im.resize((n, n), Image.LANCZOS)


if __name__ == '__main__':
    name, t = sys.argv[1], float(sys.argv[2])
    size = int(sys.argv[3]) if len(sys.argv) > 4 else 512
    render(name, t, size).save(sys.argv[-1])

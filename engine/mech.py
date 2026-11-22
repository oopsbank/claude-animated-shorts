# Engine-drawn mechanism diagrams (one causal chain each, big and readable at phone size). Drawn like an fx:
#   render(name, t, size, **kw) -> RGBA size x size, t 0..1 over the effect's life.
# pane_push_top (sailing-stones s17, top view): a big translucent ice pane fades in, a bold wind arrow sweeps in
#   behind it, the wind shoves the pane right until it touches the rock (squash + dust), the rock starts moving
#   `lag` of the life after the contact, and a groove trail grows behind it. Kwargs: lag (default 0.12), seed.
import math, random
from PIL import Image, ImageDraw, ImageFilter

INK = (36, 23, 38, 255)
SS = 2                                  # supersampling


def clamp(t, a=0.0, b=1.0): return a if t < a else b if t > b else t
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def bump(t): return math.sin(math.pi * clamp(t))


def _blob(cx, cy, rx, ry, seed, n=14, j=0.12):
    rnd = random.Random(seed); pts = []
    for i in range(n):
        a = 2 * math.pi * i / n; r = 1 + rnd.uniform(-j, j)
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return pts


def _pane(cx, cy, w, h, seed):
    rnd = random.Random(seed)       # an irregular sheet with straight-ish broken edges
    pts = [(-0.5, -0.42), (-0.1, -0.5), (0.3, -0.46), (0.5, -0.2), (0.47, 0.25), (0.2, 0.5), (-0.25, 0.46), (-0.5, 0.15)]
    return [(cx + (x + rnd.uniform(-0.03, 0.03)) * w, cy + (y + rnd.uniform(-0.03, 0.03)) * h) for x, y in pts]


def pane_push_top(t, n, lag=0.12, seed=7, **kw):
    N = n * SS; im = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im, 'RGBA')
    e = max(3, int(N * 0.008))                                  # ink width
    a_in = smooth(seg(t, 0.0, 0.1)) * (1 - smooth(seg(t, 0.94, 1.0)))
    if a_in <= 0.01: return Image.new('RGBA', (n, n), (0, 0, 0, 0))
    gy = N * 0.55
    # phases: pane in 0-0.12, wind 0.12-0.3, push 0.3-0.5 (contact at 0.5), rock moves from 0.5 + lag to 0.95
    tc = 0.5
    push = smooth(seg(t, 0.3, tc))
    rock_u = smooth(seg(t, tc + lag, 0.95))
    pw, ph = N * 0.46, N * 0.36
    rr = N * 0.075                                              # rock radius (0.15 of the canvas across)
    run = N * 0.32
    rock_x0 = N * 0.5; rock_x = rock_x0 + rock_u * run
    p_touch = rock_x0 - rr * 0.95 - pw * 0.5; p0 = p_touch - N * 0.14
    pane_x = p0 + push * (p_touch - p0) + rock_u * run
    # the pane: translucent cyan, plum ink edge, white glints
    poly = _pane(pane_x, gy, pw, ph, seed)
    d.polygon(poly, fill=(150, 225, 250, int(150 * a_in)))
    d.line(poly + [poly[0]], fill=INK[:3] + (int(255 * a_in),), width=e, joint='curve')
    for k in range(3):
        gx = pane_x - pw * 0.25 + k * pw * 0.2; gy0 = gy - ph * 0.25 + k * ph * 0.08
        d.line((gx, gy0, gx + pw * 0.1, gy0 - ph * 0.06), fill=(255, 255, 255, int(230 * a_in)), width=int(e * 1.3))
    # crack lines on the pane (it broke into panes)
    d.line((pane_x - pw * 0.1, gy - ph * 0.48, pane_x + pw * 0.02, gy + ph * 0.05, pane_x - pw * 0.05, gy + ph * 0.48),
           fill=(255, 255, 255, int(200 * a_in)), width=e)
    # groove trail behind the rock, over the translucent pane (it is cut into the clay under it)
    if rock_u > 0.002:
        x0, x1 = rock_x0, rock_x
        d.rounded_rectangle((x0 - rr * 0.2, gy - rr * 0.55, x1, gy + rr * 0.55), radius=int(rr * 0.5), fill=(96, 70, 52, int(245 * a_in)))
        d.line((x0, gy - rr * 0.55, x1, gy - rr * 0.55), fill=(250, 240, 220, int(240 * a_in)), width=int(e * 1.4))
        d.line((x0, gy + rr * 0.55, x1, gy + rr * 0.55), fill=(250, 240, 220, int(240 * a_in)), width=int(e * 1.4))
    # the rock (squashes on contact) and a dust puff
    sq = 1 + 0.15 * bump(seg(t, tc - 0.02, tc + 0.08))
    d.polygon(_blob(rock_x, gy, rr * sq, rr / sq, seed + 3), fill=(128, 116, 104, int(255 * a_in)))
    d.line(_blob(rock_x, gy, rr * sq, rr / sq, seed + 3) + [_blob(rock_x, gy, rr * sq, rr / sq, seed + 3)[0]], fill=INK[:3] + (int(255 * a_in),), width=e)
    d.ellipse((rock_x - rr * 0.5, gy - rr * 0.6, rock_x + rr * 0.1, gy - rr * 0.2), fill=(170, 158, 146, int(255 * a_in)))
    pf = bump(seg(t, tc - 0.02, tc + 0.18))
    if pf > 0.03:
        for k in range(3):
            px = rock_x - rr * 1.05; py = gy + (k - 1) * rr * 0.7
            r = rr * (0.25 + 0.15 * k % 2) * (0.5 + pf)
            d.ellipse((px - r - pf * rr * 0.4, py - r, px + r - pf * rr * 0.4, py + r), fill=(226, 206, 170, int(220 * pf * a_in)), outline=INK[:3] + (int(200 * pf * a_in),), width=max(2, e // 2))
    # the wind arrow: bold, white with plum ink, sweeps in from the left behind the pane, pulses with the push
    wa = smooth(seg(t, 0.12, 0.26)) * (1 - 0.5 * smooth(seg(t, 0.8, 0.95)))
    if wa > 0.01:
        x0 = N * 0.06; L = N * 0.56 * wa; x1 = x0 + L; ay = gy - ph * 0.85
        th = N * 0.045; hd = N * 0.11
        body = [(x0, ay - th / 2), (x1 - hd, ay - th / 2), (x1 - hd, ay - th), (x1, ay), (x1 - hd, ay + th), (x1 - hd, ay + th / 2), (x0, ay + th / 2)]
        d.polygon(body, fill=(255, 255, 255, int(245 * a_in)))
        d.line(body + [body[0]], fill=INK[:3] + (int(255 * a_in),), width=e, joint='curve')
        for k in range(2):           # two wind streaks under the arrow
            yy = gy + ph * (0.7 + 0.12 * k); xs = x0 + N * 0.05 * k
            d.line((xs, yy, xs + L * 0.7, yy), fill=(255, 255, 255, int(210 * a_in * wa)), width=int(e * 1.4))
        try:
            from PIL import ImageFont
            import os
            f = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'Poppins-Bold.ttf'), int(N * 0.05))
            d.text(((x0 + x1 - hd) / 2, ay), 'WIND', fill=INK[:3] + (int(255 * a_in * wa),), font=f, anchor='mm')
        except OSError: pass
    return im.resize((n, n), Image.LANCZOS)


NAMES = {'pane_push_top': pane_push_top}


def render(name, t, size, **kw):
    return NAMES[name](t, int(size), **kw)

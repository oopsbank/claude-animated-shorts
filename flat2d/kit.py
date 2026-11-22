"""flat2d: a rich flat-2D scene kit for 1080x1920 shorts (Pillow + numpy).

Every helper draws onto an RGBA PIL image in place (or returns a layer) so a scene is a stack of
calls, back to front. Each call is one *layer* that an animator can move on its own: keep the
arguments (offsets, seeds, phases) as the animation parameters.

Rules baked in (LESSONS.md / stickman/DRAWING_RULES.md):
- Blur only alpha masks (PIL blur on straight RGBA drags in black halos): see `glow`, `soft_layer`.
- Glow is warm or coloured *behind* characters; never over a face.
- Captions follow PIPELINE.md > Captions ("sentence" style).
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, ImageColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'stickman', 'scripts'))
import stickman  # noqa: E402

W, H = 1080, 1920
INK = (18, 16, 26)
FONT_XB = os.path.join(ROOT, 'engine/fonts/Poppins-ExtraBold.ttf')
FONT_B = os.path.join(ROOT, 'engine/fonts/Poppins-Bold.ttf')
_fonts = {}


def font(size, bold=False):
    k = (size, bold)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FONT_B if bold else FONT_XB, size)
    return _fonts[k]


def rgb(c):
    if isinstance(c, str):
        if not c.startswith('#'): return ImageColor.getrgb(c)[:3]
        c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(c[:3])


def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def layer(w=W, h=H): return Image.new('RGBA', (w, h), (0, 0, 0, 0))


def mask(w=W, h=H): return Image.new('L', (w, h), 0)


# ---------------------------------------------------------------- compositing
def fill_mask(img, m, color, alpha=1.0, blur=0):
    """Composite a flat colour through an L mask (blurred mask only: no dark halos)."""
    if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
    if alpha != 1.0: m = m.point(lambda v: int(v * alpha))
    img.paste(Image.new('RGBA', img.size, rgb(color) + (255,)), (0, 0), m)


def glow(img, m, color, alpha=0.6, blur=40, add=False):
    """Soft coloured glow from a mask. add=True brightens (screen-like) instead of covering."""
    m = m.filter(ImageFilter.GaussianBlur(blur))
    if add:
        a = np.asarray(m, np.float32)[..., None] / 255 * alpha
        base = np.asarray(img, np.float32)
        c = np.array(rgb(color), np.float32)
        base[..., :3] = 255 - (255 - base[..., :3]) * (1 - a * c / 255)
        img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)))
    else:
        fill_mask(img, m, color, alpha)


def soft_layer(lay, blur):
    """Blur an RGBA layer premultiplied (no black fringes)."""
    a = np.asarray(lay, np.float32)
    al = a[..., 3:] / 255
    pm = Image.fromarray((a[..., :3] * al).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    ab = lay.split()[3].filter(ImageFilter.GaussianBlur(blur))
    abf = np.asarray(ab, np.float32)[..., None] / 255
    col = np.asarray(pm, np.float32) / np.maximum(abf, 1e-3)
    out = np.dstack([col.clip(0, 255), abf * 255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


# ---------------------------------------------------------------- skies and light
def vgrad(stops, w=W, h=H, y0=0):
    """Vertical gradient. stops: [(t 0..1, colour), ...] over [y0, y0+h)."""
    t = np.linspace(0, 1, h)[:, None]
    ts = [s[0] for s in stops]; cs = np.array([rgb(s[1]) for s in stops], np.float32)
    col = np.stack([np.interp(t[:, 0], ts, cs[:, i]) for i in range(3)], 1)
    arr = np.repeat(col[:, None, :], w, 1)
    return Image.fromarray(np.dstack([arr, np.full((h, w, 1), 255)]).astype(np.uint8), 'RGBA')


def radial(img, cx, cy, r, color, alpha=0.8, power=1.6, add=True, box=None):
    """Radial light pool (sun, lamp, glowing pool). Moves: cx, cy, r (pulse)."""
    yy, xx = np.mgrid[0:img.height, 0:img.width]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    a = (np.clip(1 - d, 0, 1) ** power * alpha)[..., None]
    if box is not None: a = a * np.asarray(box, np.float32)[..., None] / 255
    base = np.asarray(img, np.float32); c = np.array(rgb(color), np.float32)
    if add: base[..., :3] = 255 - (255 - base[..., :3]) * (1 - a * c / 255)
    else: base[..., :3] = base[..., :3] * (1 - a) + c * a
    img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)))


def cloud_bands(img, seed, y0, y1, color, alpha=0.35, n=5, drift=0):
    """Long soft flat cloud streaks. Moves: drift (px, wraps)."""
    rng = np.random.default_rng(seed); m = mask(); d = ImageDraw.Draw(m)
    for _ in range(n):
        y = rng.uniform(y0, y1); x = (rng.uniform(-200, W) + drift) % (W + 600) - 300
        L = rng.uniform(300, 700); th = rng.uniform(14, 34)
        d.rounded_rectangle([x, y, x + L, y + th], th / 2, fill=255)
        d.rounded_rectangle([x + L * .2, y - th * .7, x + L * .7, y + th * .3], th / 2, fill=255)
    fill_mask(img, m, color, alpha, blur=6)


def haze(img, ya, yb, color, alpha=0.6):
    """Horizontal haze band peaking at the middle of [ya, yb]. Moves: alpha breathes, band rises."""
    m = np.zeros((img.height, img.width), np.float32)
    ys = np.arange(img.height); mid = (ya + yb) / 2; half = (yb - ya) / 2
    prof = np.clip(1 - np.abs(ys - mid) / half, 0, 1) ** 1.3
    m[:] = prof[:, None]
    fill_mask(img, Image.fromarray((m * 255 * alpha).astype(np.uint8)), color, 1.0)


def depth_fade(img, ya, yb, color, a_top, a_bot):
    """Linear fog ramp over [ya, yb] (aerial perspective on a whole layer)."""
    m = np.zeros((img.height, img.width), np.float32)
    ys = np.arange(img.height)
    m[:] = np.interp(ys, [ya, yb], [a_top, a_bot])[:, None]
    m[:int(ya)] = 0
    fill_mask(img, Image.fromarray((m * 255).astype(np.uint8)), color)


# ---------------------------------------------------------------- terrain
def peak_range(img, seed, y_base, hmin, hmax, lit, shade, snow=None, ink=None, ink_w=4,
               n=7, x_shift=0, snow_frac=0.38, ground=None):
    """Faceted mountain range: each peak has a lit left plane, a shadow right plane and a jagged
    snow cap. Moves: x_shift (parallax; far ranges slower)."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    xs = np.sort(rng.uniform(-250, W + 250, n)) + x_shift
    peaks = []
    for x in xs:
        h = rng.uniform(hmin, hmax); wl = rng.uniform(.75, 1.25) * h * 1.15; wr = rng.uniform(.75, 1.25) * h * 1.15
        peaks.append((x, y_base - h, wl, wr, h))
    for x, ay, wl, wr, h in sorted(peaks, key=lambda p: p[4]):
        L, R = (x - wl, y_base + 2), (x + wr, y_base + 2)
        mx = x + rng.uniform(-.15, .25) * wr; split = (mx, y_base + 2)
        knee = (x + (mx - x) * .5 + rng.uniform(-14, 14), ay + h * .5)
        if ink: d.polygon([L, (x, ay), R], fill=None, outline=rgb(ink), width=ink_w)
        d.polygon([L, (x, ay), knee, split], fill=rgb(lit))
        d.polygon([(x, ay), R, split, knee], fill=rgb(shade))
        if snow:
            f = snow_frac; pts = [(x, ay)]
            # right edge down, jagged across, left edge up
            pts.append((x + wr * f, ay + h * f))
            k = 6
            for i in range(1, k):
                u = 1 - i / k
                px = x - wl * f + (wl + wr) * f * u
                py = ay + h * f * (0.55 + 0.45 * ((i % 2) * rng.uniform(.6, 1)))
                pts.append((px, py))
            pts.append((x - wl * f, ay + h * f))
            d.polygon(pts, fill=rgb(snow))
            # snow shadow plane on the right of the cap
            d.polygon([(x, ay), (x + wr * f, ay + h * f), (knee[0] * .5 + x * .5, ay + h * f * .8)],
                      fill=lerp(rgb(snow), rgb(shade), .35))
        if ink: d.line([L, (x, ay), R], fill=rgb(ink), width=ink_w, joint='curve')
    if ground: d.rectangle([0, y_base, W, img.height], fill=rgb(ground))
    return peaks


def ice_cliff(img, x0, x1, top, bottom, seed, lit=(236, 246, 255), mid=(196, 222, 244),
              shade=(140, 182, 226), deep=(76, 118, 178), snow=(252, 253, 255), ink=INK, ink_w=6,
              lip_icicles=True):
    """Faceted glacier wall. top: callable x -> y of the lip. Columns get a lit plane, a mid plane and
    a shadow plane split on a diagonal; dark crevasse seams; strata; a snow cap; icicles.
    Static (moves only with the camera). Returns the lip polyline."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    xs = [x0]
    while xs[-1] < x1: xs.append(min(x1, xs[-1] + rng.uniform(60, 135)))
    lip = [(x, top(x) + rng.uniform(-10, 10)) for x in xs]
    sil = lip + [(x1, bottom(x1)), (x0, bottom(x0))]
    d.polygon(sil, fill=rgb(mid))
    for i in range(len(lip) - 1):
        (xa, ya), (xb, yb) = lip[i], lip[i + 1]
        ba, bb = bottom(xa), bottom(xb)
        k = rng.uniform(.35, .65); sx = xa + (xb - xa) * k
        kind = i % 3
        if kind == 0:
            d.polygon([(xa, ya), (xb, yb), (sx + 14, bb), (xa, ba)], fill=rgb(lit))
            d.polygon([(xb, yb), (xb, bb), (sx + 14, bb)], fill=rgb(shade))
        elif kind == 1:
            d.polygon([(xa, ya), (sx, (ya + yb) / 2), (sx - 20, ba), (xa, ba)], fill=rgb(shade))
            d.polygon([(sx, (ya + yb) / 2), (xb, yb), (xb, bb), (sx - 20, ba)], fill=rgb(lit))
        else:
            ym = ya + (ba - ya) * rng.uniform(.3, .5)
            d.polygon([(xa, ya), (xb, yb), (xb, ym + 30), (xa, ym)], fill=rgb(lit))
            d.polygon([(xa, ym), (xb, ym + 30), (xb, bb), (xa, ba)], fill=rgb(mid))
            d.polygon([(xa + (xb - xa) * .6, ym + 20), (xb, ym + 30), (xb, bb)], fill=rgb(shade))
        d.line([(xa, ya + 6), (xa + rng.uniform(-8, 8), ba)], fill=rgb(deep), width=5)
    # strata (thin, slightly sloped)
    for _ in range(46):
        x = rng.uniform(x0, x1 - 60); ytop = top(x) + 60
        y = rng.uniform(ytop, bottom(x) - 20); L = rng.uniform(40, 170)
        d.line([(x, y), (min(x1, x + L), y + rng.uniform(2, 8))], fill=lerp(rgb(mid), rgb(deep), .45), width=3)
    for _ in range(14):  # bright glints
        x = rng.uniform(x0 + 20, x1 - 30); y = rng.uniform(top(x) + 80, bottom(x) - 40)
        d.line([(x, y), (x + rng.uniform(16, 40), y - rng.uniform(4, 12))], fill=(255, 255, 255), width=4)
    # snow cap
    cap = lip + [(x, y + rng.uniform(22, 44)) for x, y in reversed(lip)]
    d.polygon(cap, fill=rgb(snow))
    if lip_icicles:
        for x in np.arange(x0 + 10, x1 - 10, 26):
            y = np.interp(x, [p[0] for p in lip], [p[1] for p in lip]) + 26
            L = rng.uniform(14, 64) * (rng.random() > .25)
            if L: d.polygon([(x, y), (x + 14, y), (x + 7, y + L)], fill=(232, 246, 255))
    d.line(lip, fill=rgb(ink), width=ink_w, joint='curve')
    d.line([(x0, lip[0][1]), (x0, bottom(x0))], fill=rgb(ink), width=ink_w)
    return lip


def snow_ground(img, y_fn, color=(246, 249, 253), shade=(196, 212, 236), ink=INK, ink_w=6, seed=3,
                drifts=6):
    """Snow ground with soft drift shading and an inked horizon. Static."""
    xs = np.arange(-10, W + 11, 10)
    edge = [(x, y_fn(x)) for x in xs]
    d = ImageDraw.Draw(img)
    d.polygon(edge + [(W + 10, img.height), (-10, img.height)], fill=rgb(color))
    # vertical shade ramp toward the bottom (snow in front is in shade)
    m = np.zeros((img.height, img.width), np.float32)
    ys = np.arange(img.height); y0 = min(p[1] for p in edge)
    m[:] = np.clip((ys - y0) / (img.height - y0), 0, 1)[:, None] ** 1.5 * 0.55
    gm = mask(); ImageDraw.Draw(gm).polygon(edge + [(W + 10, img.height), (-10, img.height)], fill=255)
    fill_mask(img, Image.fromarray((m * np.asarray(gm) ).astype(np.uint8)), shade)
    rng = np.random.default_rng(seed); dm = mask(); dd = ImageDraw.Draw(dm)
    for _ in range(drifts):
        cx = rng.uniform(0, W); cy = rng.uniform(y0 + 60, img.height); rx = rng.uniform(160, 380); ry = rx * .13
        dd.chord([cx - rx, cy - ry, cx + rx, cy + ry], 180, 360, fill=255)
    fill_mask(img, dm, shade, .55, blur=3)
    d.line(edge, fill=rgb(ink), width=ink_w)
    return edge


def rocks(img, seed, items, lit=(150, 116, 92), shade=(98, 72, 62), ink=INK, ink_w=5, snow=(250, 252, 255)):
    """Faceted boulders: items = [(cx, base_y, size), ...]. Static."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    for cx, by, s in items:
        n = 7; pts = []
        for i in range(n):
            a = math.pi + math.pi * i / (n - 1)
            r = s * rng.uniform(.75, 1.05)
            pts.append((cx + math.cos(a) * r * 1.25, by + math.sin(a) * r))
        top = min(pts, key=lambda p: p[1])
        d.polygon(pts, fill=rgb(shade))
        d.polygon([p for p in pts if p[0] <= top[0] + 1] + [(top[0] + s * .1, by)], fill=rgb(lit))
        d.polygon([(top[0] - s * .4, top[1] + s * .12), top, (top[0] + s * .45, top[1] + s * .16),
                   (top[0], top[1] + s * .3)], fill=rgb(snow))
        d.line(pts + [pts[0]], fill=rgb(ink), width=ink_w, joint='curve')


# ---------------------------------------------------------------- particles, texture, post
def snow_particles(img, seed, n=(70, 34, 10), sizes=(4, 9, 20), wind=(6, 1), alpha=(200, 220, 160),
                   t=0.0, color=(255, 255, 255), region=None):
    """Three depth planes of snow. Moves: t (s) -> y fall + x wind; near flakes fall faster and blur more.
    wind = (dx, dy) streak length per plane unit."""
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = region or (0, 0, img.width, img.height)
    for k, (cnt, sz, a) in enumerate(zip(n, sizes, alpha)):
        lay = layer(img.width, img.height); d = ImageDraw.Draw(lay)
        spd = (60, 140, 300)[k]
        for _ in range(cnt):
            x = (rng.uniform(x0, x1) + wind[0] * 20 * t * (k + 1)) % (x1 - x0) + x0
            y = (rng.uniform(y0, y1) + spd * t) % (y1 - y0) + y0
            s = sz * rng.uniform(.7, 1.2)
            if k == 2:
                d.line([(x, y), (x - wind[0] * 3, y - s * 1.6)], fill=tuple(color) + (int(a * .6),), width=int(s * .8))
            d.ellipse([x - s / 2, y - s / 2, x + s / 2, y + s / 2], fill=tuple(color) + (a,))
        img.alpha_composite(soft_layer(lay, (0, 1.2, 3.5)[k]) if k else lay)


def dust(img, seed, n, box, color, alpha=150, size=(3, 8), t=0.0):
    """Floating motes inside box (lamp beams, the brine pool). Moves: t -> slow sine drift."""
    rng = np.random.default_rng(seed); lay = layer(img.width, img.height); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = rng.uniform(x0, x1) + 14 * math.sin(t * .8 + rng.uniform(0, 6))
        y = rng.uniform(y0, y1) - 20 * t % (y1 - y0)
        s = rng.uniform(*size)
        d.ellipse([x - s, y - s, x + s, y + s], fill=rgb(color) + (int(alpha * rng.uniform(.5, 1)),))
    img.alpha_composite(soft_layer(lay, 1.0))


def grain(img, amount=0.035, paper=0.05, seed=11):
    """Paper texture: low-frequency mottling + fine grain (multiply). Static per shot, or re-seed per
    2 frames for a 'boiling' film look."""
    rng = np.random.default_rng(seed)
    a = np.asarray(img, np.float32)
    fine = rng.normal(0, 1, (img.height, img.width)) * amount
    low = Image.fromarray(((rng.normal(0, 1, (img.height // 24 + 1, img.width // 24 + 1)) * 40 + 128).clip(0, 255)).astype(np.uint8))
    low = np.asarray(low.resize((img.width, img.height), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6)), np.float32)
    low = (low - 128) / 128 * paper
    f = (1 + fine + low)[..., None]
    a[..., :3] = a[..., :3] * f
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8)))


def vignette(img, strength=0.35, color=(16, 14, 40), rx=0.75, ry=0.62, power=2.2):
    yy, xx = np.mgrid[0:img.height, 0:img.width]
    d = np.sqrt(((xx - img.width / 2) / (img.width * rx)) ** 2 + ((yy - img.height / 2) / (img.height * ry)) ** 2)
    a = (np.clip(d, 0, 1.6) ** power * strength).clip(0, 1)[..., None]
    base = np.asarray(img, np.float32)
    base[..., :3] = base[..., :3] * (1 - a) + np.array(rgb(color), np.float32) * a
    img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)))


def contact_shadow(img, cx, gy, w, color=(70, 90, 140), alpha=0.55, h=None):
    """Soft ellipse under feet/props. Moves with its owner; squashes with a hop."""
    m = mask(); h = h or w * 0.16
    ImageDraw.Draw(m).ellipse([cx - w / 2, gy - h / 2, cx + w / 2, gy + h / 2], fill=255)
    fill_mask(img, m, color, alpha, blur=max(4, w * .05))
    m2 = mask(); ImageDraw.Draw(m2).ellipse([cx - w * .3, gy - h * .25, cx + w * .3, gy + h * .25], fill=255)
    fill_mask(img, m2, lerp(rgb(color), (0, 0, 0), .3), alpha * .7, blur=max(3, w * .025))


# ---------------------------------------------------------------- characters
def stick(expr='neutral', pose='stand', look=0.0, **kw):
    """White stickman card (black outline), house colour."""
    return stickman.draw(expr=expr, pose=pose, color='#f6f6f2', look=look, **kw)


def head_of(card):
    """Head centre (card px) from the alpha: the top row of the head + radius."""
    a = np.asarray(card.split()[3]) > 0
    rows = np.where(a.any(1))[0]
    top = rows[0]
    cols = np.where(a[top + 30])[0]
    return (cols[0] + cols[-1]) / 2, top + stickman.R + stickman.OUT + 1


def place(img, card, cx, gy, scale, aura=None, aura_alpha=0.55, rim=None, rim_dir=(1, -0.4),
          rim_alpha=0.9, rim_w=9, shadow=(70, 90, 140), shadow_alpha=0.5, shadow_w=None):
    """Put a stickman card with soles at (cx, gy). Adds a contact shadow, a coloured aura behind it and
    a rim light on the side facing rim_dir (unit-ish vector toward the light). Returns geometry dict
    {'head': (x, y), 'top': y, 'scale': s, 'xy': (px, py)} for labels and props."""
    s = scale
    c = card.resize((int(card.width * s), int(card.height * s)), Image.LANCZOS)
    px, py = int(cx - c.width / 2), int(gy - 975 * s)
    a = c.split()[3]
    if shadow:
        bb = a.getbbox(); sw = shadow_w or (bb[2] - bb[0]) * 1.1
        contact_shadow(img, cx, gy, sw, shadow, shadow_alpha)
    if aura:
        m = mask(); m.paste(a, (px, py)); glow(img, m, aura, aura_alpha, blur=int(30 * s + 6))
        m2 = mask(); m2.paste(a, (px, py)); glow(img, m2, aura, aura_alpha * .6, blur=int(80 * s + 10))
    if rim:
        an = np.asarray(a, np.float32) / 255
        L = np.array(rim_dir, np.float32); L = L / np.linalg.norm(L)
        sh = int(round(rim_w * s / .9))
        dx, dy = int(round(L[0] * sh)), int(round(L[1] * sh))
        moved = np.zeros_like(an)  # moved[p] = an[p + L*sh]
        ys, ye = max(0, -dy), an.shape[0] - max(0, dy)
        xs, xe = max(0, -dx), an.shape[1] - max(0, dx)
        moved[ys:ye, xs:xe] = an[ys + dy:ye + dy, xs + dx:xe + dx]
        inner = np.asarray(a.filter(ImageFilter.MinFilter(7)), np.float32) / 255
        # only on the light-coloured fill (not on dark face marks / outline)
        lum = np.asarray(c.convert('L'), np.float32) / 255
        r = (inner * (1 - moved) * (lum > .8)).clip(0, 1)
        rm = Image.fromarray((r * 255 * rim_alpha).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
        col = Image.new('RGBA', c.size, rgb(rim) + (255,))
        c = c.copy(); c.paste(col, (0, 0), ImageChops.multiply(rm, a))
    img.alpha_composite(c, (px, py))
    hx, hy = head_of(card)
    bb = a.getbbox()
    return {'head': (px + hx * s, py + hy * s), 'top': py + bb[1], 'scale': s, 'xy': (px, py),
            'card': card, 'R': stickman.R * s}


# ---------------------------------------------------------------- text and UI
def text_w(txt, f): return ImageDraw.Draw(Image.new('L', (1, 1))).textlength(txt, font=f)


def label(img, text, cx, y, color, size=40, glow_alpha=0.5):
    """Role pill above a head (brief: small coloured label). Moves: bobs 4 px with the head."""
    f = font(size, bold=True); w = text_w(text, f); h = size * 1.6
    m = mask(); ImageDraw.Draw(m).rounded_rectangle([cx - w / 2 - 30, y - 6, cx + w / 2 + 30, y + h + 6], h / 2, fill=255)
    glow(img, m, color, glow_alpha, blur=16)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - w / 2 - 24, y + 6, cx + w / 2 + 24, y + h + 6], h / 2, fill=INK)  # drop
    d.rounded_rectangle([cx - w / 2 - 24, y, cx + w / 2 + 24, y + h], h / 2, fill=rgb(color), outline=INK, width=5)
    d.rounded_rectangle([cx - w / 2 - 14, y + 7, cx + w / 2 + 14, y + h * .42], h / 4, fill=lerp(rgb(color), (255, 255, 255), .22))
    d.text((cx - w / 2, y + h * .5), text, font=f, fill='white', anchor='lm')
    return y + h


def title(img, lines, y, size=96, gap=1.12, stroke=(40, 18, 44), sw=10, shadow=8):
    """House headline: bold white lines (keyword line coloured), thick plum outline, hard shadow.
    lines = [(text, colour[, size])]. Moves: slam-in scale 1.15 -> 1.0, then a 0.6% breathe."""
    d = ImageDraw.Draw(img)
    for item in lines:
        txt, col = item[0], item[1]; sz = item[2] if len(item) > 2 else size
        f = font(sz); w = text_w(txt, f); x = (img.width - w) / 2
        d.text((x + shadow * .6, y + shadow), txt, font=f, fill=(10, 6, 20), stroke_width=sw, stroke_fill=(10, 6, 20))
        d.text((x, y), txt, font=f, fill=rgb(col), stroke_width=sw, stroke_fill=rgb(stroke))
        y += sz * gap
    return y


def caption(img, text, avoid=()):
    """PIPELINE.md > Captions, 'sentence' style: Poppins Bold 3.7% H, white, 10% black outline, soft
    shadow, centred, baseline at 70% H; nudged down off any face box in `avoid` [(x0,y0,x1,y1)]."""
    size = int(round(0.037 * img.height)); f = font(size, bold=True)
    w = text_w(text, f); base = 0.70 * img.height
    for x0, y0, x1, y1 in avoid:
        if base > y0 and base - size < y1 and (img.width - w) / 2 < x1 and (img.width + w) / 2 > x0:
            base = y1 + size + 10
    x = (img.width - w) / 2
    sh = layer(img.width, img.height)
    ImageDraw.Draw(sh).text((x + 3, base + 5), text, font=f, fill=(0, 0, 0, 200), anchor='ls',
                            stroke_width=int(size * .16), stroke_fill=(0, 0, 0, 200))
    img.alpha_composite(soft_layer(sh, 7))
    ImageDraw.Draw(img).text((x, base), text, font=f, fill='white', anchor='ls',
                             stroke_width=int(size * .1), stroke_fill='black')


def pill(img, text, cx, cy, fill, size=44, fg='white', pad=26):
    """UI chip (meters, dimension tags)."""
    f = font(size); w = text_w(text, f); h = size * 1.5
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - w / 2 - pad, cy - h / 2 + 6, cx + w / 2 + pad, cy + h / 2 + 6], h / 2, fill=INK)
    d.rounded_rectangle([cx - w / 2 - pad, cy - h / 2, cx + w / 2 + pad, cy + h / 2], h / 2, fill=rgb(fill), outline=INK, width=5)
    d.text((cx, cy + 2), text, font=f, fill=fg, anchor='mm')


def rotated_paste(img, lay, cx, cy, angle):
    r = lay.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(r, (int(cx - r.width / 2), int(cy - r.height / 2)))


def light_rays(img, cx, cy, color, n=9, alpha=0.18, spread=(200, 340), length=1800, seed=1, phase=0.0, blur=18):
    """God rays fanning from a light (sun, window). Moves: phase rotates the fan slowly (+-2 deg) and
    each ray's alpha flickers 15%."""
    rng = np.random.default_rng(seed); m = mask(img.width, img.height); d = ImageDraw.Draw(m)
    a0, a1 = spread
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * (i + .5) / n + phase + rng.uniform(-4, 4))
        wa = math.radians(rng.uniform(1.5, 4.5))
        p1 = (cx + math.cos(a - wa) * length, cy + math.sin(a - wa) * length)
        p2 = (cx + math.cos(a + wa) * length, cy + math.sin(a + wa) * length)
        d.polygon([(cx, cy), p1, p2], fill=int(255 * rng.uniform(.5, 1)))
    glow(img, m, color, alpha, blur=blur, add=True)


def foreground_frame(img, shapes, color=(30, 24, 52), alpha=0.92, blur=7):
    """Out-of-focus foreground silhouettes (drifts, rocks, a bottle) framing the shot for depth.
    shapes = list of polygons. Moves: 1.6x the camera pan (strongest parallax)."""
    m = mask(img.width, img.height); d = ImageDraw.Draw(m)
    for p in shapes: d.polygon(p, fill=255)
    fill_mask(img, m, color, alpha, blur=blur)

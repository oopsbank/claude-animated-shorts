"""flat2d kit layers for the boiling river (video 6): rainforest, a steaming river, a frog, a thermometer, a Peru
map, the imagined volcano, the earth cross-section with faults and depth heat, rain on far mountains, a cutaway
coffee machine and a cutaway globe.

Same contract as kit.py / ocean.py: every call draws one layer in place, back to front; its arguments (t, cam,
seed, k) are the animation parameters. Static layers (far canopy, mid trees) are cached and moved with the
camera; steam is drawn into a quarter-size alpha mask, blurred and lifted (cheap and soft, no RGBA halos).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kit
from kit import W, H, INK, layer, mask, fill_mask, glow, radial, rgb, lerp, font

_cache = {}
def cached(key, fn):
    if key not in _cache:
        if len(_cache) > 60: _cache.clear()
        _cache[key] = fn()
    return _cache[key]


HOT = (255, 110, 40)
RED = (226, 54, 40)
COLD = (70, 170, 235)
LEAF = ((36, 92, 56), (58, 132, 70), (96, 170, 84))        # shade, mid, lit
JADE = ((150, 214, 196), (92, 172, 160), (52, 120, 120))   # hot river water: milky jade, top..deep


# ---------------------------------------------------------------- rainforest (side view)
def _crowns(d, rng, y_base, n, rmin, rmax, cols, ink=None, iw=3, x0=-200, x1=W + 200, trunk=None):
    for i in range(n):
        x = rng.uniform(x0, x1); r = rng.uniform(rmin, rmax); y = y_base - rng.uniform(.2, 1.0) * r * 2.2
        if trunk:
            d.rectangle([x - r * .09, y, x + r * .09, y_base + 40], fill=trunk, outline=ink, width=iw if ink else 0)
        for j in range(6):                                                    # a crown = a cluster of discs
            a = rng.uniform(0, 2 * math.pi); q = r * rng.uniform(.45, .75)
            cx, cy = x + math.cos(a) * r * .55, y + math.sin(a) * r * .35
            if ink: d.ellipse([cx - q - iw, cy - q - iw, cx + q + iw, cy + q + iw], fill=ink)
        for j in range(6):
            a = rng.uniform(0, 2 * math.pi); q = r * rng.uniform(.45, .75)
            cx, cy = x + math.cos(a) * r * .55, y + math.sin(a) * r * .35
            d.ellipse([cx - q, cy - q, cx + q, cy + q], fill=cols[j % len(cols)])


def canopy_layer(seed, y_base, rows, w=W + 400, h=H):
    """A cached RGBA band of tree crowns. rows: [(n, rmin, rmax, (colours), ink?, trunk?, dy)]"""
    def mk():
        lay = layer(w, h); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed)
        for n, rmin, rmax, cols, ink, trunk, dy in rows:
            _crowns(d, rng, y_base + dy, n, rmin, rmax, cols, ink=INK if ink else None, trunk=trunk, x0=0, x1=w)
            d.rectangle([0, y_base + dy, w, h], fill=cols[0])
        return lay
    return cached(('canopy', seed, y_base, str(rows), w, h), mk)


def jungle_back(img, t, cam=0.0, horizon=820, sky=((214, 236, 214), (176, 214, 180)), far=(120, 168, 140),
                mid=(70, 128, 90), haze_col=(220, 238, 220), sun=(820, 260), rays=True, warm=0.0):
    """Sky + far ridge + two canopy bands with haze between them (aerial perspective). Moves: parallax with cam,
    god rays sway, haze breathes."""
    sk = [lerp(rgb(sky[0]), (255, 196, 140), warm), lerp(rgb(sky[1]), (236, 160, 120), warm)]
    img.paste(kit.vgrad([(0, sk[0]), (.45, sk[1]), (1, mid)]))
    radial(img, sun[0], sun[1], 700, lerp((255, 250, 220), (255, 190, 120), warm), .5)
    # far ridge (Andes foothills): faint blue-green hills
    d = ImageDraw.Draw(img)
    pts = [(-50, horizon)] + [(x, horizon - 170 - 60 * math.sin(x * .006 + 1) - 40 * math.sin(x * .017)) for x in range(-50, W + 60, 30)] + [(W + 60, horizon)]
    d.polygon([(p[0] + cam * .1, p[1]) for p in pts], fill=lerp(rgb(far), rgb(sk[1]), .55))
    a = canopy_layer(11, horizon - 40, [(40, 50, 90, (lerp(far, sk[1], .25), lerp(far, (255, 255, 255), .1)), False, None, 0)])
    img.alpha_composite(a, (int(-200 + cam * .2), 0))
    kit.haze(img, horizon - 260, horizon + 80, lerp(rgb(haze_col), (255, 210, 170), warm), .55 + .05 * math.sin(t * .7))
    b = canopy_layer(12, horizon + 90, [(34, 70, 120, (mid, lerp(mid, (255, 255, 255), .12), lerp(mid, (200, 230, 120), .25)), False, (60, 50, 40), 0)])
    img.alpha_composite(b, (int(-200 + cam * .45), 0))
    kit.haze(img, horizon - 20, horizon + 200, lerp(rgb(haze_col), (255, 210, 170), warm), .32)
    if rays:
        kit.light_rays(img, sun[0], sun[1] - 200, (255, 250, 220), n=8, alpha=.16, spread=(95, 150), length=1900,
                       seed=4, phase=2 * math.sin(t * .3))


def frond(d, x, y, L, ang, t, cols=LEAF, ink=INK, iw=4, n=11, droop=.35, sway=0.0):
    """A palm frond: a curved stem with leaflets on both sides (flat, inked). ang in degrees (0 = right)."""
    a0 = math.radians(ang + sway); pts = []
    for i in range(n + 1):
        s = i / n; a = a0 + droop * s * s * (1 if math.cos(a0) >= 0 else -1)
        if i == 0: px, py = x, y
        else: px, py = pts[-1][0] + math.cos(a) * L / n, pts[-1][1] + math.sin(a) * L / n
        pts.append((px, py))
    for i in range(1, n + 1):
        px, py = pts[i]; qx, qy = pts[i - 1]; ta = math.atan2(py - qy, px - qx)
        ll = L * .32 * math.sin(math.pi * (i / (n + 1)) ** .8)
        for side in (-1, 1):
            b = ta + side * 1.05
            tip = (px + math.cos(b) * ll + math.cos(ta) * ll * .35, py + math.sin(b) * ll + math.sin(ta) * ll * .35 + ll * .2)
            poly = [(qx, qy), ((qx + tip[0]) / 2 + math.cos(ta) * 9, (qy + tip[1]) / 2 + math.sin(ta) * 9), tip, (px, py)]
            d.polygon(poly, fill=cols[1] if side < 0 else cols[2], outline=ink, width=iw)
    d.line(pts, fill=ink, width=iw + 4, joint='curve'); d.line(pts, fill=cols[0], width=max(2, iw - 1), joint='curve')


def broad_leaf(d, x, y, L, ang, cols=LEAF, ink=INK, iw=4, wfrac=.42):
    """A broad tropical leaf (pointed oval with a midrib and side veins)."""
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(25):
        s = i / 24; wv = math.sin(math.pi * s) ** .8 * L * wfrac / 2
        pts.append((s * L, wv))
    pts += [(p[0], -p[1]) for p in reversed(pts)]
    P = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
    d.polygon(P, fill=cols[1], outline=ink, width=iw)
    half = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts[:25]]
    d.polygon(half + [(x + L * ca, y + L * sa)], fill=cols[2])
    d.line([(x, y), (x + L * ca, y + L * sa)], fill=cols[0], width=max(3, iw))
    for k in range(1, 6):
        s = k / 6.5; bx, by = x + s * L * ca, y + s * L * sa
        for side in (-1, 1):
            ex = bx + (L * .12) * ca - side * (L * wfrac * .38) * sa; ey = by + (L * .12) * sa + side * (L * wfrac * .38) * ca
            d.line([(bx, by), (ex, ey)], fill=cols[0], width=2)
    d.polygon(P, outline=ink, width=iw)


def vines(img, t, xs, y1=900, cam=0.0, col=(40, 80, 50), ink=INK):
    """Hanging lianas from the top edge, swaying slowly, with a few small leaves."""
    d = ImageDraw.Draw(img)
    for i, x in enumerate(xs):
        L = y1 * (.6 + .4 * ((i * 37) % 10) / 10); sw = 18 * math.sin(t * .8 + i * 1.7)
        pts = [(x + cam + sw * (s / 10) ** 2 + 14 * math.sin(s * .9 + i), -20 + L * s / 10) for s in range(11)]
        d.line(pts, fill=ink, width=10, joint='curve'); d.line(pts, fill=col, width=5, joint='curve')
        for s in range(2, 11, 2):
            px, py = pts[s]; sd = 1 if s % 4 else -1
            d.ellipse([px + sd * 4 - 12, py - 8, px + sd * 4 + 12, py + 8], fill=lerp(col, (120, 180, 90), .5), outline=ink, width=3)


def side_walls(img, t, cam=0.0, seed=3, left=True, right=True, y0=-80, y1=1500, cols=LEAF, scale=1.0, dark=0.0):
    """Near foliage framing both edges: fronds and broad leaves, swaying (strong parallax: 1.4x cam)."""
    d = ImageDraw.Draw(img); rng = np.random.default_rng(seed)
    c = tuple(lerp(rgb(x), (20, 40, 30), dark) for x in cols)
    for side in ((-1,) if left else ()) + ((1,) if right else ()):
        for i in range(7):
            y = y0 + (y1 - y0) * (i + rng.uniform(0, .6)) / 7
            x = (-40 if side < 0 else W + 40) + cam * 1.4
            L = rng.uniform(300, 470) * scale; sw = 4 * math.sin(t * 1.1 + i * 1.3 + seed)
            ang = (rng.uniform(-30, 30) if side < 0 else 180 + rng.uniform(-30, 30))
            if i % 3 == 1: broad_leaf(d, x, y, L * .8, ang + sw * 2 + (25 if side < 0 else -25), cols=c)
            else: frond(d, x, y, L, ang, t, cols=c, sway=sw, droop=.5 * -side if side < 0 else .5)


def ground_bank(img, pts, top=(92, 70, 48), mid=(70, 52, 38), moss=(76, 130, 60), ink=INK):
    """A muddy bank polygon with a mossy rim and roots."""
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=mid, outline=ink, width=6)
    rim = pts[:max(2, len(pts) // 2)]
    d.line(rim, fill=moss, width=26, joint='curve'); d.line(rim, fill=INK, width=4)


# ---------------------------------------------------------------- the river
def river_band(img, t, y_far, y_near, x_far=(260, 900), x_near=(-300, W + 300), cam=0.0, cols=JADE, heat=1.0,
               seed=1):
    """A river receding toward y_far (perspective trapezoid), milky jade, flow streaks drifting toward the
    viewer, sun glints. Returns the polygon (for clipping steam and bubbles)."""
    poly = [(x_far[0] + cam * .3, y_far), (x_far[1] + cam * .3, y_far), (x_near[1] + cam, y_near), (x_near[0] + cam, y_near)]
    g = kit.vgrad([(0, cols[0]), (.4, cols[1]), (1, cols[2])], h=int(y_near - y_far), y0=0)
    m = mask(); ImageDraw.Draw(m).polygon(poly, fill=255)
    big = layer(); big.paste(g, (0, int(y_far)))
    img.paste(big, (0, 0), m)
    lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed)
    for i in range(60):                                                  # flow streaks (toward the viewer)
        s = (rng.uniform(0, 1) + t * .12) % 1; y = y_far + (y_near - y_far) * s ** 1.6
        f = (y - y_far) / (y_near - y_far)
        xl = x_far[0] + (x_near[0] - x_far[0]) * f + cam * (.3 + .7 * f); xr = x_far[1] + (x_near[1] - x_far[1]) * f + cam * (.3 + .7 * f)
        x = xl + (xr - xl) * rng.uniform(.05, .95); L = 30 + 200 * f
        d.line([(x - L / 2, y), (x + L / 2, y)], fill=(235, 255, 250, int(150 * math.sin(math.pi * s))), width=max(2, int(2 + 6 * f)))
    if heat > 0:                                                         # heat: warm glow on the surface
        hm = mask(); ImageDraw.Draw(hm).polygon(poly, fill=int(255 * min(1, heat)))
        glow(lay, hm, (255, 170, 90), .12, blur=60)
    img.alpha_composite(lay)
    ImageDraw.Draw(img).line(poly[:2], fill=lerp(cols[0], (255, 255, 255), .4), width=4)
    return poly


def bubbles(img, t, poly, n=40, seed=2, rate=1.6, size=(8, 34), heat=1.0, col=(236, 255, 250)):
    """Rolling boil: bubbles swell and pop on the surface inside poly (bigger near the viewer). heat scales the
    count and size. Moves: each bubble has its own phase."""
    if heat <= 0: return
    ys = [p[1] for p in poly]; y0, y1 = min(ys), max(ys)
    lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed)
    pm = mask(); ImageDraw.Draw(pm).polygon(poly, fill=255); pa = np.asarray(pm)
    for i in range(int(n * heat)):
        ph = rng.uniform(0, 1); sp = rng.uniform(.7, 1.3) * rate; u = (ph + t * sp) % 1
        k = int((ph + t * sp) // 1)
        r2 = np.random.default_rng(seed * 1000 + i * 31 + k)
        y = y0 + (y1 - y0) * r2.uniform(.03, 1) ** .7
        x = r2.uniform(0, W)
        if not pa[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))]: continue
        f = (y - y0) / max(1, y1 - y0); q = (size[0] + (size[1] - size[0]) * f) * heat ** .5
        if u < .75:
            r = q * (u / .75) ** .6
            d.ellipse([x - r, y - r * .62, x + r, y + r * .62], fill=(255, 255, 255, 60), outline=col + (230,), width=max(2, int(r * .18)))
            d.ellipse([x - r * .5, y - r * .45, x - r * .1, y - r * .2], fill=(255, 255, 255, 220))
        else:                                                            # pop: a fading ring + droplets
            v = (u - .75) / .25; r = q * (1 + v * 1.2)
            d.ellipse([x - r, y - r * .55, x + r, y + r * .55], outline=col + (int(200 * (1 - v)),), width=max(2, int(q * .12)))
            for j in range(3):
                a = -math.pi / 2 + (j - 1) * .7; dd = q * (.6 + v * 1.4)
                px, py = x + math.cos(a) * dd, y + math.sin(a) * dd - q * v * (1 - v) * 2
                d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=col + (int(220 * (1 - v)),))
    img.alpha_composite(lay)


def steam(img, t, sources, rise=900, dens=1.0, seed=5, n=60, size=(50, 150), rate=.22, wind=40, col=(250, 252, 250),
          shade=(176, 196, 196), warm=0.0, alpha=.9, clip=None):
    """Thick animated steam. sources: list of (x0, x1, y) lines it rises from. Drawn into a quarter-size mask,
    blurred and composited twice: a cool shade pass (offset down) and the white body. Moves: every puff rises,
    swells, drifts with wind and fades; the column wobbles."""
    q = 4; w4, h4 = W // q, H // q
    mb = Image.new('L', (w4, h4), 0); db = ImageDraw.Draw(mb)
    rng = np.random.default_rng(seed)
    nn = int(n * dens)
    for i in range(nn):
        x0, x1, y = sources[i % len(sources)]
        ph = rng.uniform(0, 1); sp = rate * rng.uniform(.75, 1.3); u = (ph + t * sp) % 1
        bx = rng.uniform(x0, x1); s = rng.uniform(*size) * (.5 + 1.3 * u)
        x = bx + wind * u * 2 + 50 * math.sin(t * .9 + i * 1.3) * u
        yy = y - rise * u ** .85
        a = (math.sin(math.pi * min(1, u * 1.25)) ** .7) * (1 - u) ** .4
        db.ellipse([(x - s) / q, (yy - s * .8) / q, (x + s) / q, (yy + s * .8) / q], fill=int(255 * min(1.0, a * 1.7)))
    blur = mb.filter(ImageFilter.GaussianBlur(5)).filter(ImageFilter.GaussianBlur(3))
    m = blur.resize((W, H), Image.BILINEAR)
    if clip is not None: m = Image.fromarray((np.asarray(m, np.float32) * np.asarray(clip, np.float32) / 255).astype(np.uint8))
    sh = Image.new('L', (W, H), 0); sh.paste(m, (0, 14))
    fill_mask(img, sh, lerp(rgb(shade), (255, 170, 120), warm), alpha * .55 * min(1, dens))
    fill_mask(img, m, lerp(rgb(col), (255, 226, 200), warm * .6), alpha * min(1, .8 + .2 * dens))


def wisps(img, t, box, n=14, seed=9, col=(255, 255, 255), a=120):
    """Thin curling steam wisps (detail over the soft body)."""
    lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        ph = rng.uniform(0, 1); u = (ph + t * .35) % 1; x = rng.uniform(x0, x1); yb = y1 - (y1 - y0) * u * .4
        pts = [(x + 26 * math.sin(s * .9 + t * 2 + i) * (s / 8), yb - s * 26) for s in range(9)]
        d.line(pts, fill=col + (int(a * math.sin(math.pi * u)),), width=6, joint='curve')
    img.alpha_composite(kit.soft_layer(lay, 3))


# ---------------------------------------------------------------- the frog
def frog(s=1.0, look=0.0, blink=False, splay=0.0, col=(94, 186, 70), belly=(220, 236, 150), spot=(54, 120, 52)):
    """A small tree frog, side view facing right, as an RGBA layer (400x300 * s, sitting on y = 230*s).
    splay 0..1: legs flung out (slipping)."""
    S = 2; w, h = int(400 * s * S), int(300 * s * S)
    lay = layer(w, h); d = ImageDraw.Draw(lay); k = s * S
    P = lambda x, y: (x * k, y * k)
    iw = max(3, int(6 * k / 2))
    # back leg (folded, or flung out)
    if splay > .05:
        hip = (120, 180); kn = (120 - 90 * splay, 180 + 20 - 40 * splay); ft = (60 - 120 * splay, 230 - 40 * splay)
        d.line([P(*hip), P(*kn), P(*ft)], fill=INK, width=int(34 * k) + 2 * iw, joint='curve')
        d.line([P(*hip), P(*kn), P(*ft)], fill=col, width=int(34 * k), joint='curve')
        for j in range(3):
            a = math.radians(160 + j * 25); fx, fy = ft[0] + 30 * math.cos(a), ft[1] + 30 * math.sin(a)
            d.line([P(*ft), P(fx, fy)], fill=INK, width=int(12 * k) + 2 * iw); d.line([P(*ft), P(fx, fy)], fill=col, width=int(12 * k))
    # body
    body = [P(70, 200), P(110, 120), P(200, 90), P(290, 110), P(330, 150), P(310, 200), P(230, 228), P(120, 230)]
    d.polygon(body, fill=col, outline=INK, width=iw)
    d.chord([P(150, 160), P(320, 250)], 0, 180, fill=belly)
    d.polygon(body, outline=INK, width=iw)
    for x, y, r in ((150, 140, 14), (200, 120, 10), (240, 150, 12), (120, 180, 10)):
        d.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=spot)
    if splay <= .05:                                                     # folded back leg (thigh)
        d.ellipse([P(60, 150), P(190, 235)], fill=col, outline=INK, width=iw)
        d.line([P(80, 228), P(200, 232)], fill=INK, width=iw)
        d.ellipse([P(180, 218), P(232, 240)], fill=col, outline=INK, width=iw)
    # front leg
    fa = (280, 190); ff = (300 + 30 * splay, 232 - 30 * splay)
    d.line([P(*fa), P(*ff)], fill=INK, width=int(22 * k) + 2 * iw); d.line([P(*fa), P(*ff)], fill=col, width=int(22 * k))
    for j in range(3):
        a = math.radians(-20 + j * 30 - 60 * splay); fx, fy = ff[0] + 22 * math.cos(a), ff[1] + 10 + 12 * math.sin(a)
        d.ellipse([P(fx - 9, fy - 7), P(fx + 9, fy + 7)], fill=(250, 200, 120), outline=INK, width=max(2, iw - 2))
    # eye bulge
    d.ellipse([P(250, 62), P(320, 132)], fill=col, outline=INK, width=iw)
    d.ellipse([P(260, 72), P(312, 124)], fill=(255, 210, 60) if not blink else col, outline=INK, width=max(2, iw - 1))
    if not blink:
        px = 288 + 8 * look
        d.ellipse([P(px - 13, 86), P(px + 13, 112)], fill=INK)
        d.ellipse([P(px - 5, 88), P(px + 3, 96)], fill='white')
    else:
        d.line([P(262, 98), P(310, 98)], fill=INK, width=iw)
    d.arc([P(270, 130), P(340, 175)], 20, 110, fill=INK, width=max(2, iw - 1))          # mouth line
    return lay.resize((int(400 * s), int(300 * s)), Image.LANCZOS)


# ---------------------------------------------------------------- instruments and graphics
def thermometer(img, x, y_top, h, level, t, w=70, scale=((0, '0°'), (.5, '50°'), (1.0, '100°C')), liquid=RED,
                glow_on=True, label_side=1, fs=34):
    """A big glass thermometer. level 0..1 (1.0 = 100 °C at the top mark). Moves: level, a shimmer on the glass."""
    d = ImageDraw.Draw(img)
    bulb_r = w * .9; top, bot = y_top, y_top + h
    yl = lambda v: bot - 40 - (h - 80) * v
    if glow_on and level > .5:
        m = mask(); ImageDraw.Draw(m).rounded_rectangle([x - w / 2, yl(level), x + w / 2, bot], w / 2, fill=255)
        glow(img, m, HOT, .45 * (level - .5) * 2, blur=40)
        d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - w / 2 - 6, top - 6, x + w / 2 + 6, bot + 6], w / 2 + 6, fill=INK)
    d.ellipse([x - bulb_r - 6, bot - bulb_r - 6 + 30, x + bulb_r + 6, bot + bulb_r + 6 + 30], fill=INK)
    d.rounded_rectangle([x - w / 2, top, x + w / 2, bot], w / 2, fill=(236, 244, 248))
    d.ellipse([x - bulb_r, bot - bulb_r + 30, x + bulb_r, bot + bulb_r + 30], fill=liquid)
    ww = w * .38
    d.rounded_rectangle([x - ww / 2, yl(level), x + ww / 2, bot + 10], ww / 2, fill=liquid)
    for v, txt in scale:
        yy = yl(v)
        d.line([(x - w / 2, yy), (x - w / 2 + 22, yy)], fill=INK, width=5)
        tx = x + label_side * (w / 2 + 18)
        d.text((tx, yy), txt, font=font(fs, True), fill='white', anchor='lm' if label_side > 0 else 'rm', stroke_width=5, stroke_fill=INK)
    for j in range(1, 10):
        yy = yl(j / 10); d.line([(x - w / 2, yy), (x - w / 2 + 12, yy)], fill=INK, width=3)
    sh = (math.sin(t * 2) + 1) / 2                                         # glass glint
    d.rounded_rectangle([x + w * .14, top + 20 + 40 * sh, x + w * .28, top + h * .5 + 40 * sh], 6, fill=(255, 255, 255))
    d.ellipse([x - bulb_r * .55, bot - bulb_r * .4 + 30, x - bulb_r * .15, bot + 30], fill=lerp(rgb(liquid), (255, 255, 255), .45))
    return yl(level)


def chip_box(img, x, y, txt, fill, size=40, fg='white'):
    f = font(size, True); w = kit.text_w(txt, f); d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - w / 2 - 22, y - size * .8 + 6, x + w / 2 + 22, y + size * .8 + 6], 14, fill=INK)
    d.rounded_rectangle([x - w / 2 - 22, y - size * .8, x + w / 2 + 22, y + size * .8], 14, fill=fill, outline=INK, width=5)
    d.text((x, y), txt, font=f, fill=fg, anchor='mm')


# Peru (lon, lat) simplified outline, the river and the nearest active volcano (stylised positions)
PERU = [(-75.3, -0.1), (-73.6, -1.2), (-72.9, -2.4), (-71.5, -2.2), (-70.1, -2.7), (-70.0, -4.2), (-72.8, -5.1),
        (-73.2, -6.6), (-73.9, -7.3), (-73.6, -8.8), (-72.4, -9.5), (-70.5, -9.5), (-70.5, -11.0), (-69.6, -11.0),
        (-68.7, -12.5), (-69.3, -14.0), (-68.8, -15.3), (-69.9, -16.5), (-69.5, -17.5), (-70.4, -18.35),
        (-71.3, -17.7), (-72.8, -16.8), (-75.0, -15.4), (-76.3, -13.6), (-77.2, -12.0), (-78.4, -10.0),
        (-79.5, -8.0), (-80.0, -6.8), (-81.3, -4.6), (-80.4, -3.4), (-79.4, -4.5), (-78.6, -4.4), (-78.3, -3.4),
        (-77.0, -2.6), (-75.6, -1.6)]
RIVER_LL = (-74.8, -8.8)
VOLC_LL = (-71.9, -15.0)


def ll(p, ox=40, oy=160, k=76):
    return (ox + (p[0] + 82) * k, oy + (-p[1]) * k)


def peru_map(img, t, ox=40, oy=160, k=76):
    """A stylised map: Pacific (left), Peru (Andes band, Amazon green east), neighbours pale."""
    img.paste(kit.vgrad([(0, (120, 176, 204)), (1, (82, 140, 180))]))
    d = ImageDraw.Draw(img)
    for i in range(14):                                                  # ocean swell lines drifting
        y = (i * 150 + t * 14) % (H + 100) - 50
        d.arc([-200, y, 500, y + 120], 200, 340, fill=(140, 196, 220), width=3)
    L = lambda q: ll(q, ox, oy, k)
    # neighbours (pale): everything east of the coastline; Peru is drawn over them
    d.polygon([L((-79.6, 2.5)), (1200, -50), (1200, 2000), L((-70.3, -25))] + [L(q) for q in PERU[19:30]]
              + [L((-80.6, -2.0)), L((-80.1, 0.5))], fill=(226, 218, 186), outline=INK, width=4)
    pp = [ll(p, ox, oy, k) for p in PERU]
    m = mask(); ImageDraw.Draw(m).polygon(pp, fill=255)
    pl = layer(); dp = ImageDraw.Draw(pl)
    dp.rectangle([0, 0, W, H], fill=(96, 168, 84))                     # Amazon lowland green
    # the Andes: a brown band along the coast, folded ridges
    band = [ll(p, ox, oy, k) for p in [(-80, -4), (-78.5, -7.8), (-76.5, -10.5), (-74.5, -13.5), (-71.5, -15.8), (-69.6, -16.6),
                                          (-69.3, -14.2), (-71.6, -13.3), (-73.6, -11.4), (-75.4, -8.8), (-77.1, -6.1), (-78.4, -3.3)]]
    dp.polygon(band, fill=(186, 150, 104))
    coastal = [ll(p, ox, oy, k) for p in [(-81.3, -4.6), (-80.0, -6.8), (-79.5, -8.0), (-78.4, -10.0), (-77.2, -12.0),
                                             (-76.3, -13.6), (-75.0, -15.4), (-72.8, -16.8), (-71.3, -17.7), (-71.9, -16.6),
                                             (-74.5, -14.6), (-76.0, -12.4), (-77.4, -10.3), (-78.5, -8.2), (-79.6, -5.6)]]
    dp.polygon(coastal, fill=(222, 200, 150))
    rng = np.random.default_rng(3)
    for i in range(70):                                                  # ridge ticks on the Andes
        s = rng.uniform(0, 1); a, b = band[int(s * 5.99)], band[int(s * 5.99) + 1]
        f = rng.uniform(0, 1); px, py = a[0] + (b[0] - a[0]) * f + rng.uniform(-30, 60), a[1] + (b[1] - a[1]) * f
        dp.line([(px - 16, py + 10), (px, py - 8), (px + 16, py + 10)], fill=(140, 108, 76), width=4)
    for i in range(120):                                                 # forest dots
        px, py = rng.uniform(300, 1080), rng.uniform(150, 1500); r = rng.uniform(6, 14)
        dp.ellipse([px - r, py - r, px + r, py + r], fill=(76, 146, 72))
    # Amazon rivers (wiggly, light)
    for pts in ([(-74.5, -4.6), (-73.5, -4.0), (-72, -3.6), (-70.2, -3.9)], [(-75.2, -5.0), (-74.6, -6.5), (-74.4, -8.0), (-74.6, -9.6), (-73.8, -11)],
                [(-77, -5.2), (-76.2, -4.9), (-74.5, -4.6)]):
        dp.line([ll(p, ox, oy, k) for p in pts], fill=(150, 200, 220), width=7, joint='curve')
    img.paste(pl, (0, 0), m)
    d = ImageDraw.Draw(img); d.polygon(pp, outline=INK, width=7)
    d.text(ll((-74.6, -1.6), ox, oy, k), 'PERU', font=font(70, True), fill=(255, 255, 255), anchor='mm', stroke_width=7, stroke_fill=INK)
    d.text(ll((-79.8, -13.5), ox, oy, k), 'PACIFIC', font=font(38, True), fill=(220, 240, 250), anchor='mm')
    d.text((ll((-70.8, -6.8), ox, oy, k)[0], ll((-70.8, -6.8), ox, oy, k)[1]), 'AMAZON', font=font(40, True), fill=(230, 250, 220), anchor='mm', stroke_width=4, stroke_fill=(40, 90, 50))
    d.text(ll((-77.6, -10.2), ox, oy, k), 'ANDES', font=font(34, True), fill=(110, 80, 50), anchor='mm')
    return pp


def map_pin(img, x, y, t, col, s=1.0, pulse=True):
    if pulse:
        for j in range(2):
            u = (t * .8 + j * .5) % 1
            r = 30 + 90 * u; ImageDraw.Draw(img).ellipse([x - r, y - r * .9, x + r, y + r * .9], outline=col + (0,) if False else col, width=max(1, int(6 * (1 - u))))
    radial(img, x, y, 110 * s, col, .5)
    d = ImageDraw.Draw(img); r = 22 * s
    d.ellipse([x - r - 5, y - r - 5, x + r + 5, y + r + 5], fill=INK); d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    d.ellipse([x - r * .4, y - r * .6, x, y - r * .2], fill=(255, 255, 255))


def volcano_icon(img, x, y, s, t, col=(150, 96, 72), lava=(255, 110, 40), smoke_on=True, alpha=1.0, ghost=False, wr=1.0):
    """A cone volcano (y = the base line), with a lava glow and a smoke puff. ghost=True: translucent and dashed
    (the imagined volcano)."""
    lay = layer(); d = ImageDraw.Draw(lay)
    w, h = 300 * s * wr, 260 * s
    cone = [(x - w, y), (x - w * .22, y - h), (x + w * .22, y - h), (x + w, y)]
    if ghost:
        m = mask(); ImageDraw.Draw(m).polygon(cone, fill=255)
        glow(lay, m, (255, 90, 50), .5, blur=int(30 * s + 4))
        fill_mask(lay, m, (255, 120, 70), .42)
        d = ImageDraw.Draw(lay)
        import taiga
        for a, b in zip(cone, cone[1:]): taiga.dashed(d, a, b, (255, 170, 120), w=int(10 * s + 3), dash=26, gap=14, phase=t * 30)
        # magma chamber + pipe
        d.ellipse([x - w * .7, y - h * .22, x + w * .7, y + h * .1], fill=(255, 100, 40, 190), outline=(255, 200, 140), width=int(6 * s + 2))
        d.rectangle([x - w * .07, y - h, x + w * .07, y - h * .1], fill=(255, 120, 60, 110))
    else:
        d.polygon(cone, fill=col, outline=INK, width=int(7 * s + 2))
        d.polygon([cone[1], (x, y - h), (x - w * .1, y), (x - w, y)], fill=lerp(rgb(col), (255, 255, 255), .15))
        d.polygon([(x - w * .22, y - h), (x + w * .22, y - h), (x + w * .1, y - h * .8), (x - w * .06, y - h * .7)], fill=lava, outline=INK, width=int(4 * s + 1))
        d.polygon(cone, outline=INK, width=int(7 * s + 2))
        radial(lay, x, y - h, 100 * s, lava, .5)
    if smoke_on:
        for j in range(4):
            u = (t * .3 + j * .25) % 1; r = (30 + 60 * u) * s
            px, py = x + 30 * s * u + 10 * math.sin(t + j), y - h - 40 * s - 200 * s * u
            ImageDraw.Draw(lay).ellipse([px - r, py - r, px + r, py + r], fill=(120, 110, 110, int(180 * (1 - u) * (.4 if ghost else 1))))
    if alpha < 1:
        a = lay.split()[3].point(lambda v: int(v * alpha)); lay.putalpha(a)
    img.alpha_composite(lay)
    return cone


# ---------------------------------------------------------------- the earth in section
BANDS = [(0.0, (124, 98, 76)), (.18, (150, 112, 86)), (.38, (176, 110, 76)), (.58, (206, 104, 60)), (.78, (232, 84, 44)), (1.0, (250, 70, 34))]


def heat_col(f):
    f = max(0.0, min(1.0, f))
    for (a, ca), (b, cb) in zip(BANDS, BANDS[1:]):
        if f <= b: return lerp(ca, cb, (f - a) / (b - a))
    return BANDS[-1][1]


def earth_section(img, t, y_top, y_bot=H, cam=0.0, n=6, wav=26, glow_bottom=True, seed=4, ft=1.0, labels=True):
    """Strata from y_top down, coloured by depth heat (cool brown -> glowing red), wavy band edges, speckle
    texture and a pulsing heat glow at the bottom. ft = fraction of the heat ramp to use (shallower = cooler)."""
    d = ImageDraw.Draw(img); rng = np.random.default_rng(seed)
    for i in range(n):
        f0 = i / n; y0 = y_top + (y_bot - y_top) * f0
        pts = [(x, y0 + (wav * math.sin(x * .006 + i * 1.7 + cam * .002) if i else 0)) for x in range(-60, W + 80, 40)]
        d.polygon(pts + [(W + 80, H + 10), (-60, H + 10)], fill=heat_col((i + .5) / n * ft), outline=INK, width=4 if i else 0)
    for j in range(260):                                                 # speckle (pebbles / grains)
        x = rng.uniform(0, W); y = rng.uniform(y_top + 20, y_bot); f = (y - y_top) / max(1, y_bot - y_top)
        r = rng.uniform(3, 9); c = lerp(heat_col(f * ft), (40, 20, 16), .35)
        d.ellipse([x - r, y - r * .7, x + r, y + r * .7], fill=c)
    if glow_bottom:
        radial(img, W / 2, y_bot + 200, 1100, (255, 120, 50), .35 + .08 * math.sin(t * 2.2))


def fault(d, pts, w=14, col=(40, 22, 20), ink=INK):
    w = int(w)
    d.line(pts, fill=ink, width=w + 8, joint='curve'); d.line(pts, fill=col, width=w, joint='curve')


def along(pts, s):
    """Point at arc fraction s (0..1) along a polyline."""
    L = [math.dist(a, b) for a, b in zip(pts, pts[1:])]; T = sum(L); x = s * T
    for (a, b), l in zip(zip(pts, pts[1:]), L):
        if x <= l: f = x / max(l, 1e-6); return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        x -= l
    return pts[-1]


def rising(img, t, pts, n=12, speed=.45, r=(10, 22), cold=None, hot=HOT, glow_a=.55, seed=1, k=1.0, reverse=False):
    """Water blobs travelling along a polyline (pts[0] -> pts[-1]), colour cold -> hot along the way when cold
    is given. k scales how far along they have got (0..1, for a reveal)."""
    lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed); m = mask(); dm = ImageDraw.Draw(m)
    for i in range(n):
        s = (i / n + t * speed) % 1
        if s > k: continue
        x, y = along(pts, s); q = rng.uniform(*r)
        c = lerp(rgb(cold), rgb(hot), s) if cold else rgb(hot)
        d.ellipse([x - q - 4, y - q - 4, x + q + 4, y + q + 4], fill=INK + (255,))
        d.ellipse([x - q, y - q, x + q, y + q], fill=c + (255,))
        d.ellipse([x - q * .5, y - q * .6, x - q * .05, y - q * .15], fill=(255, 255, 255, 200))
        dm.ellipse([x - q * 2, y - q * 2, x + q * 2, y + q * 2], fill=255)
    if glow_a: glow(img, m, hot, glow_a, blur=24)
    img.alpha_composite(lay)


def arrow(d, pts, col, w=18, head=40, ink=INK):
    d.line(pts, fill=ink, width=w + 10, joint='curve')
    a, b = pts[-2], pts[-1]; ang = math.atan2(b[1] - a[1], b[0] - a[0])
    tip = (b[0] + math.cos(ang) * head * .6, b[1] + math.sin(ang) * head * .6)
    l = (b[0] + math.cos(ang + 2.5) * head, b[1] + math.sin(ang + 2.5) * head)
    r = (b[0] + math.cos(ang - 2.5) * head, b[1] + math.sin(ang - 2.5) * head)
    d.polygon([tip, l, r], fill=col, outline=ink, width=5)
    d.line(pts, fill=col, width=w, joint='curve')


def rain(img, t, box, n=120, seed=3, col=(200, 220, 240), a=170, slant=.25, L=60):
    lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        ph = rng.uniform(0, 1); u = (ph + t * rng.uniform(1.4, 2.0)) % 1
        x = rng.uniform(x0, x1) - slant * (y1 - y0) * u; y = y0 + (y1 - y0) * u
        d.line([(x, y), (x + slant * L, y + L)], fill=col + (int(a * rng.uniform(.5, 1)),), width=3)
    img.alpha_composite(lay)


def storm_cloud(img, x, y, s, t, col=(108, 120, 140), lit=(160, 172, 190)):
    d = ImageDraw.Draw(img)
    for pass_, c in enumerate((INK, col, lit)):
        g = 6 if pass_ == 0 else 0
        for j, (dx, dy, r) in enumerate(((-160, 20, 90), (-60, -30, 120), (70, -10, 110), (170, 30, 80), (0, 40, 100))):
            if pass_ == 2 and dy > 10: continue
            ox = dx * s + 6 * math.sin(t * .5 + j); rr = r * s + g - (16 if pass_ == 2 else 0)
            d.ellipse([x + ox - rr, y + dy * s - rr - (10 if pass_ == 2 else 0), x + ox + rr, y + dy * s + rr - (10 if pass_ == 2 else 0)], fill=c)


# ---------------------------------------------------------------- the coffee machine (cutaway)
def coffee_machine(img, x, y, s, t, kin=1.0, kheat=1.0, kout=1.0, heat_glow=1.0):
    """A cutaway drip coffee machine, base centre at (x, y): a cold tank (blue) at the back, a tube down to a
    glowing heating plate, a riser up to the shower head, hot drips into a carafe, steam above the mug.
    kin/kheat/kout: how far the water has got (0..1 each). Returns key points."""
    d = ImageDraw.Draw(img)
    S = lambda px, py: (x + px * s, y + py * s)
    bx0, by0, bx1, by1 = -330, -1000, 330, 0
    d.rounded_rectangle([*S(bx0 + 12, by0 + 14), *S(bx1 + 12, by1 + 14)], int(40 * s), fill=INK)
    d.rounded_rectangle([*S(bx0, by0), *S(bx1, by1)], int(40 * s), fill=(62, 64, 74), outline=INK, width=int(8 * s))
    d.rounded_rectangle([*S(bx0 + 30, by0 + 30), *S(bx1 - 30, by0 + 130)], int(24 * s), fill=(84, 88, 100), outline=INK, width=int(5 * s))
    # the cutaway window (inside, lighter)
    d.rounded_rectangle([*S(bx0 + 30, by0 + 160), *S(bx1 - 30, by1 - 30)], int(24 * s), fill=(36, 40, 50), outline=INK, width=int(5 * s))
    # cold tank (right/back)
    tank = (110, -820, 280, -300)
    d.rounded_rectangle([*S(tank[0], tank[1]), *S(tank[2], tank[3])], int(20 * s), fill=(200, 226, 240), outline=INK, width=int(6 * s))
    lvl = tank[1] + 80 + 120 * (1 - kin) * 0 + 60 * math.sin(t * .6) * 0
    d.rounded_rectangle([*S(tank[0] + 10, tank[1] + 120 + 260 * kin * .4), *S(tank[2] - 10, tank[3] - 10)], int(14 * s), fill=COLD)
    for j in range(3):
        wy = tank[1] + 120 + 260 * kin * .4 + 6 * math.sin(t * 3 + j)
    d.text(S(195, tank[1] + 50), 'COLD', font=font(int(36 * s), True), fill=(30, 80, 130), anchor='mm')
    # the tube path: tank bottom -> heater -> riser -> shower head
    path_in = [(195, -300), (195, -250), (-20, -250)]
    heater = (-230, -300, 60, -200)
    riser = [(-200, -260), (-260, -260), (-260, -760), (-120, -760), (-120, -700)]
    for p in (path_in, riser):
        d.line([S(*q) for q in p], fill=INK, width=int(34 * s), joint='curve'); d.line([S(*q) for q in p], fill=(170, 176, 190), width=int(22 * s), joint='curve')
    # heating plate (glowing)
    gl = .6 + .25 * math.sin(t * 5)
    m = mask(); ImageDraw.Draw(m).rounded_rectangle([*S(heater[0], heater[1]), *S(heater[2], heater[3])], int(16 * s), fill=255)
    glow(img, m, HOT, (.5 + .3 * gl) * heat_glow, blur=int(50 * s))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([*S(heater[0], heater[1]), *S(heater[2], heater[3])], int(16 * s), fill=lerp((120, 60, 40), (255, 120, 40), gl * heat_glow), outline=INK, width=int(6 * s))
    for j in range(5):                                                   # the coil
        cx = heater[0] + 40 + j * 58
        d.arc([*S(cx - 24, heater[1] + 18), *S(cx + 24, heater[3] - 18)], 180, 360, fill=lerp((255, 200, 120), (255, 255, 220), gl), width=int(8 * s))
    # shower head + carafe + mug
    d.rounded_rectangle([*S(-200, -700), *S(-40, -660)], int(10 * s), fill=(120, 124, 136), outline=INK, width=int(5 * s))
    car = (-230, -560, -10, -340)
    d.rounded_rectangle([*S(car[0], car[1]), *S(car[2], car[3])], int(30 * s), fill=(230, 240, 246), outline=INK, width=int(6 * s))
    d.rounded_rectangle([*S(car[0] + 12, car[1] + 110 - 60 * kout), *S(car[2] - 12, car[3] - 12)], int(22 * s), fill=(110, 64, 40))
    pts = {'tank': S(195, -300), 'in': [S(*q) for q in path_in], 'riser': [S(*q) for q in riser], 'heater': S(-85, -250),
           'shower': S(-120, -660), 'car': S(-120, car[1] + 110 - 60 * kout), 'carafe': car}
    return pts


def mug(img, x, y, s, t, col=(232, 96, 70), coffee=(96, 56, 36)):
    d = ImageDraw.Draw(img)
    w, h = 130 * s, 160 * s
    d.arc([x + w * .6, y - h * .8, x + w * 1.4, y - h * .2], -90, 90, fill=INK, width=int(26 * s))
    d.arc([x + w * .6, y - h * .8, x + w * 1.4, y - h * .2], -90, 90, fill=col, width=int(14 * s))
    d.rounded_rectangle([x - w, y - h, x + w, y], int(24 * s), fill=col, outline=INK, width=int(7 * s))
    d.ellipse([x - w + 8, y - h - 14 * s, x + w - 8, y - h + 14 * s], fill=coffee, outline=INK, width=int(5 * s))
    d.rectangle([x - w + 16, y - h * .7, x - w + 30, y - h * .2], fill=lerp(rgb(col), (255, 255, 255), .35))


# ---------------------------------------------------------------- the globe (cutaway)
def globe(img, cx, cy, r, t, cut=1.0, spin=0.0, glow_a=.55, land=(80, 160, 90), sea=(56, 120, 190)):
    """The Earth with a wedge cut out (crust, mantle, outer core, inner core glowing). cut 0..1 opens the wedge."""
    m = mask(); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    glow(img, m, (120, 190, 255), .5, blur=int(r * .12))
    lay = layer(); d = ImageDraw.Draw(lay)
    d.ellipse([cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8], fill=INK)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sea)
    rng = np.random.default_rng(7)
    for i in range(22):                                                  # continents (blobs that slide with spin)
        a = rng.uniform(0, 2 * math.pi) + spin; b = rng.uniform(-1.1, 1.1)
        if math.cos(a) < -.1: continue
        px, py = cx + r * .8 * math.sin(a) * math.cos(b), cy + r * .8 * math.sin(b)
        q = r * rng.uniform(.14, .3) * (.5 + .5 * math.cos(a))
        d.ellipse([px - q, py - q * .7, px + q, py + q * .7], fill=land)
    lit = mask(); ImageDraw.Draw(lit).ellipse([cx - r * 1.3, cy - r * 1.3, cx + r * .3, cy + r * .3], fill=120)
    lit = lit.filter(ImageFilter.GaussianBlur(r * .3))
    cm = mask(); ImageDraw.Draw(cm).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    from PIL import ImageChops
    fill_mask(lay, ImageChops.multiply(lit, cm), (255, 255, 255), .5)
    if cut > 0:
        a0, a1 = -90 - 45 * cut, -90 + 45 * cut                          # the wedge opens at the top-right
        wm = mask(); ImageDraw.Draw(wm).pieslice([cx - r, cy - r, cx + r, cy + r], a0 + 45, a1 + 45, fill=255)
        wl = layer(); dw = ImageDraw.Draw(wl)
        for rr, c in ((1.0, (150, 110, 80)), (.92, (230, 110, 50)), (.55, (255, 160, 60)), (.3, (255, 236, 160))):
            dw.ellipse([cx - r * rr, cy - r * rr, cx + r * rr, cy + r * rr], fill=c, outline=INK, width=4)
        lay.paste(wl, (0, 0), wm)
        g = mask(); ImageDraw.Draw(g).pieslice([cx - r * .6, cy - r * .6, cx + r * .6, cy + r * .6], a0 + 45, a1 + 45, fill=255)
        glow(lay, g, (255, 190, 80), glow_a * (1 + .2 * math.sin(t * 3)), blur=int(r * .15))
        d = ImageDraw.Draw(lay)
        for a in (a0 + 45, a1 + 45):
            d.line([(cx, cy), (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))], fill=INK, width=6)
    img.alpha_composite(lay)

"""The world kit for video 11 (moth-light): a Costa Rican cloud forest at night lit by a glowing UV lamp, plus the
other sets of the film.

- `forest(img, w, cam, lamp, ...)`: layered night cloud forest (hazy far trunks in mist, moss-draped trunks with
  hanging moss and bromeliads, tree ferns with arching fronds, lianas, a fern-and-leaf-litter floor, dark out-of-focus
  foreground leaves); every layer is lit by the lamp (falloff + a rim on the edges that face it), the mist between
  layers glows violet near the lamp. Static layers are cached and slide with parallax; mist, spores and fronds move.
- `uv_lamp(...)`: a violet-blue UV tube lamp on a tripod stand with a soft halo, `lamp_glow(...)`.
- `ir_view(img, w, ...)`: the infrared high-speed camera look (grey-green monochrome, scan lines, noise, HUD).
- `night_stage`, `ancient_night`, `moon_sky`: the night-sky diagram stage, the ancient starry night, the Moon.
- `candle_room`, `street_lamp`, `desk_night`: s02 and s13 sets.
- props: `camera_rig` (high-speed camera on a tripod), `ir_lamp`, `laptop`, `headlamp` (on a stickman), `sheet`.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit
from kit import W, H, INK, vgrad, radial, mask, glow, fill_mask, layer, lerp, rgb, font

UV = (150, 110, 255)
UV_CORE = (236, 228, 255)
UV_HALO = (118, 92, 240)
MOSS = (64, 104, 58)
MOSS_L = (120, 160, 84)


def _rng(seed): return np.random.default_rng(seed)


# ---------------------------------------------------------------- lighting a layer by the lamp
def light_layer(lay, lamp, col=UV, k=1.0, r=520, rim=1.0, amb=None):
    """Light an RGBA layer by a point lamp: a smooth falloff plus a rim on the edges that face the lamp."""
    a = np.asarray(lay, np.float32)
    al = a[..., 3] / 255
    h, w = al.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lx, ly = lamp
    dx, dy = xx - lx, yy - ly
    d = np.sqrt(dx * dx + dy * dy) + 1
    f = k / (1 + (d / r) ** 2.2)
    c = np.array(col, np.float32) / 255
    rgbv = a[..., :3]
    out = rgbv * (1 + .55 * f[..., None]) + 255 * c * (f * .2)[..., None]
    if rim > 0:
        sm = np.asarray(lay.split()[3].filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
        gy, gx = np.gradient(sm)
        rr = np.clip(-(gx * dx + gy * dy) / d * 10, 0, 1) * np.clip(f * 1.6, 0, 1)
        out = out + 255 * c * (rr * rim * .8)[..., None]
    a[..., :3] = out.clip(0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def _haze(lay, col, k):
    a = np.asarray(lay, np.float32)
    a[..., :3] = a[..., :3] * (1 - k) + np.array(col, np.float32) * k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- plants
def trunk(d, x, y_top, y_bot, w0, w1, col, seed, lean=0.0, ink=None, iw=0):
    rng = _rng(seed)
    n = 26
    L, R = [], []
    for i in range(n + 1):
        f = i / n
        y = y_top + (y_bot - y_top) * f
        cx = x + lean * (1 - f) * (y_bot - y_top) * .15 + 6 * math.sin(f * 7 + seed)
        ww = (w0 + (w1 - w0) * f) / 2 * (1 + .06 * rng.normal())
        L.append((cx - ww, y)); R.append((cx + ww, y))
    poly = L + R[::-1]
    if ink: d.polygon(poly, fill=ink, outline=ink, width=iw * 2 if iw else 0)
    d.polygon(poly, fill=col)
    return L, R


def moss_clumps(d, pts_l, pts_r, col, col_l, seed, n=10, scale=1.0, hang=None, hang_col=None):
    rng = _rng(seed)
    for _ in range(n):
        i = int(rng.uniform(1, len(pts_l) - 1))
        side = rng.choice([0, 1])
        x, y = (pts_l if side == 0 else pts_r)[i]
        r = rng.uniform(10, 22) * scale
        for k in range(int(rng.uniform(6, 12))):                 # a bumpy cushion of small round tufts
            bx = x + rng.normal(0, r * .9); by = y + rng.normal(0, r * .5); br = r * rng.uniform(.35, .7)
            d.ellipse([bx - br, by - br, bx + br, by + br * .8], fill=col)
        for k in range(int(rng.uniform(4, 8))):
            bx = x + rng.normal(0, r * .7); by = y - r * .3 + rng.normal(0, r * .3); br = r * rng.uniform(.2, .4)
            d.ellipse([bx - br, by - br, bx + br, by + br * .6], fill=col_l)
        if hang is not None and rng.uniform() < .7:
            for j in range(int(rng.uniform(3, 8))):              # old-man's-beard strands hanging down
                hx = x + rng.uniform(-r, r); hl = rng.uniform(60, 260) * scale
                pts = [(hx + 4 * scale * math.sin(k * .9 + j), y + k * hl / 14) for k in range(15)]
                d.line(pts, fill=hang_col or col, width=max(1, int(rng.uniform(1.5, 3.5) * scale)))


def bromeliad(d, x, y, s, col, col_l, seed):
    rng = _rng(seed)
    for k in range(9):
        a = math.radians(-90 + (k - 4) * 22 + rng.uniform(-6, 6))
        L = s * rng.uniform(.7, 1.1)
        tip = (x + math.cos(a) * L, y + math.sin(a) * L * .8)
        mid = (x + math.cos(a) * L * .5 - math.sin(a) * s * .08, y + math.sin(a) * L * .4)
        d.polygon([(x - s * .06, y), mid, tip, (x + s * .06, y)], fill=col if k % 2 else col_l)


def fern_frond(d, base, ang, L, droop, col, col_d, width=1.0, n=16):
    """An arching frond: a spine curving down, leaflets on both sides tapering to the tip."""
    pts = []
    for i in range(n + 1):
        f = i / n
        a = ang + droop * f * f
        if i == 0: pts.append(base); continue
        px, py = pts[-1]
        pts.append((px + math.cos(a) * L / n, py + math.sin(a) * L / n))
    for i in range(1, n):
        f = i / n
        px, py = pts[i]; qx, qy = pts[i + 1]
        dx, dy = qx - px, qy - py; dl = math.hypot(dx, dy) or 1
        nx, ny = -dy / dl, dx / dl
        ll = L * .17 * width * math.sin(math.pi * min(1, f * 1.1)) ** .7 + 3
        for sgn in (1, -1):
            tip = (px + (nx * sgn * .9 + dx / dl * .45) * ll, py + (ny * sgn * .9 + dy / dl * .45) * ll + ll * .25)
            d.polygon([(px, py), (px + dx * .5, py + dy * .5), tip], fill=col if sgn > 0 else col_d)
    d.line(pts, fill=col_d, width=max(2, int(L * .012)))
    return pts


def tree_fern(d, x, y_bot, h, col, col_d, trunk_col, seed, t=0.0, sway=0.0):
    rng = _rng(seed)
    top = (x + 10 * math.sin(seed), y_bot - h)
    # fibrous trunk
    d.line([(x, y_bot), top], fill=trunk_col, width=int(h * .05))
    for k in range(int(h / 18)):
        yy = y_bot - k * 18; xx = x + (top[0] - x) * (k * 18 / h)
        d.line([(xx - h * .025, yy), (xx + h * .025, yy - 6)], fill=lerp(trunk_col, (0, 0, 0), .3), width=3)
    nf = 11
    for k in range(nf):
        a = math.radians(-90 + (k - (nf - 1) / 2) * 30 + rng.uniform(-8, 8)) + sway * math.sin(t * 1.1 + k)
        L = h * rng.uniform(.5, .72)
        fern_frond(d, top, a, L, 1.5 * (1 if math.cos(a) > 0 else -1) * (abs(math.cos(a)) + .25), col, col_d, 1.0)
    d.ellipse([top[0] - h * .04, top[1] - h * .03, top[0] + h * .04, top[1] + h * .03], fill=col_d)


def liana(d, x0, y0, x1, y1, sag, col, w):
    pts = []
    for i in range(21):
        f = i / 20
        pts.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f + sag * 4 * f * (1 - f)))
    d.line(pts, fill=col, width=w, joint='curve')
    return pts


def leaf(d, x, y, L, ang, col, col_v, wid=.32):
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(13):
        f = i / 12
        wdt = L * wid * math.sin(math.pi * f) ** .8
        pts.append((f * L, -wdt))
    pts += [(f * L, L * wid * math.sin(math.pi * f) ** .8) for f in np.linspace(1, 0, 13)]
    P = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
    d.polygon(P, fill=col)
    d.line([(x, y), (x + L * ca, y + L * sa)], fill=col_v, width=max(2, int(L * .03)))


# ---------------------------------------------------------------- forest layers (cached)
_CACHE = {}


def _layer_far(seed, haze_col):
    lay = layer(W + 400, H); d = ImageDraw.Draw(lay)
    rng = _rng(seed)
    for k in range(16):
        x = rng.uniform(-100, W + 500); wd = rng.uniform(26, 70)
        trunk(d, x, -50, rng.uniform(1100, 1350), wd * .7, wd, lerp(haze_col, (20, 30, 40), .25), seed + k)
        for j in range(3):                                       # branches with moss tufts
            by = rng.uniform(150, 900); bl = rng.uniform(80, 220) * rng.choice([-1, 1])
            d.line([(x, by), (x + bl, by - abs(bl) * .3)], fill=lerp(haze_col, (20, 30, 40), .25), width=int(wd * .35))
            d.ellipse([x + bl - 40, by - abs(bl) * .3 - 26, x + bl + 40, by - abs(bl) * .3 + 14], fill=lerp(haze_col, (30, 50, 40), .2))
    return lay


def _layer_mid(seed, base_col, moss, moss_l, fern):
    lay = layer(W + 400, H); d = ImageDraw.Draw(lay)
    rng = _rng(seed)
    for k in range(7):
        x = rng.uniform(-60, W + 460); wd = rng.uniform(60, 120)
        L, R = trunk(d, x, -60, rng.uniform(1300, 1500), wd * .75, wd * 1.1, base_col, seed + 10 + k)
        moss_clumps(d, L, R, moss, moss_l, seed + 20 + k, n=9, scale=1.0, hang=True, hang_col=lerp(moss, base_col, .3))
        for j in range(2):
            by = rng.uniform(200, 800); bl = rng.uniform(120, 300) * rng.choice([-1, 1])
            d.line([(x, by), (x + bl, by - abs(bl) * .25)], fill=base_col, width=int(wd * .3))
            bromeliad(d, x + bl * .8, by - abs(bl) * .22, rng.uniform(40, 70), lerp(moss, (60, 90, 50), .4), moss_l, seed + 30 + k + j)
    for k in range(4):
        tree_fern(d, rng.uniform(0, W + 400), rng.uniform(1250, 1420), rng.uniform(420, 620), fern, lerp(fern, (0, 0, 0), .35),
                  lerp(base_col, (40, 30, 20), .3), seed + 40 + k)
    return lay


def _layer_near(seed, base_col, moss, moss_l, fern, side_trunks=True):
    lay = layer(W + 400, H); d = ImageDraw.Draw(lay)
    rng = _rng(seed)
    if side_trunks:
        for x, wd in ((200 + 10, 230), (200 + W - 10, 260)):
            L, R = trunk(d, x, -80, H + 60, wd * .85, wd * 1.15, base_col, seed + 50, ink=INK, iw=3)
            moss_clumps(d, L, R, moss, moss_l, seed + 51 + int(x), n=16, scale=1.6, hang=True, hang_col=lerp(moss, (30, 40, 30), .2))
    # lianas from the top
    for k in range(5):
        x0 = rng.uniform(0, W + 400); x1 = x0 + rng.uniform(-300, 300)
        liana(d, x0, -40, x1, rng.uniform(300, 900), rng.uniform(60, 200), lerp(base_col, (60, 50, 30), .3), int(rng.uniform(5, 11)))
    # the floor: ferns and leaf litter
    gpts = [(0, H)] + [(x, 1660 + 40 * math.sin(x / 170 + seed) + 20 * math.sin(x / 61)) for x in range(0, W + 441, 40)] + [(W + 400, H)]
    d.polygon(gpts, fill=lerp(base_col, (30, 24, 16), .3))
    for k in range(70):
        x = rng.uniform(0, W + 400); y = rng.uniform(1650, H)
        leaf(d, x, y, rng.uniform(30, 60), rng.uniform(0, 6.28), lerp((70, 56, 36), base_col, rng.uniform(.3, .7)), (40, 30, 20), .3)
    for k in range(9):
        base = (rng.uniform(0, W + 400), rng.uniform(1700, 1900))
        for j in range(7):
            a = math.radians(-90 + (j - 3) * 26 + rng.uniform(-6, 6))
            fern_frond(d, base, a, rng.uniform(180, 300), 1.2 * (1 if math.cos(a) > 0 else -1) * (abs(math.cos(a)) + .3), fern, lerp(fern, (0, 0, 0), .35), .8)
    return lay


def _fg(seed, col):
    lay = layer(W + 400, H); d = ImageDraw.Draw(lay)
    rng = _rng(seed)
    for k in range(7):
        side = k % 2
        x = (-80 + rng.uniform(0, 160)) if side == 0 else (W + 320 + rng.uniform(0, 160))
        y = rng.uniform(1350, H + 100)
        leaf(d, x, y, rng.uniform(260, 400), math.radians(rng.uniform(-60, -15) if side == 0 else rng.uniform(195, 240)), col, lerp(col, (60, 90, 70), .3), .3)
    return lay


PAL = {
    'uv': dict(sky0=(4, 8, 18), sky1=(10, 22, 34), haze=(30, 46, 62), mid=(18, 28, 32), moss=(34, 70, 46), moss_l=(70, 116, 70),
               fern=(30, 74, 56), near=(12, 18, 20), fg=(6, 10, 12), mist=(110, 130, 170)),
}


def forest(img, w, cam=0.0, lamp=(540, 900), lamp_k=1.0, seed=7, mood='uv', fg=True, floor=True, mist_a=1.0, side_trunks=True,
           drift=1.0, lamp_r=1.0):
    """Draw the night cloud forest. cam = horizontal parallax offset (px). lamp: screen position of the lamp."""
    P = PAL[mood]
    img.alpha_composite(vgrad([(0, P['sky0']), (.55, P['sky1']), (1, lerp(P['sky1'], (20, 26, 20), .4))]))
    # a big soft violet bloom of lit fog around the lamp, behind everything
    radial(img, lamp[0], lamp[1], 900 * lamp_r, (70, 56, 150), .55 * lamp_k)
    lk = (int(lamp[0]), int(lamp[1]), seed, mood, side_trunks, round(lamp_k, 2), round(lamp_r, 2))
    def cached(name, fn, depth, kk, r, rim):
        key = (name,) + lk
        if key not in _CACHE:
            lay = fn()
            # light relative to where the lamp sits on this (wider) layer at cam = 0
            lay = light_layer(lay, (lamp[0] + 200, lamp[1]), UV, kk * lamp_k, r * lamp_r, rim)
            _CACHE[key] = lay
        return _CACHE[key]
    far = cached('far', lambda: _haze(_layer_far(seed, P['haze']), P['haze'], .45), .2, .35, 520, .3)
    img.alpha_composite(far, (int(-200 + cam * .25), 0))
    mist(img, w * drift, 300, 1500, (120, 130, 180), .22 * mist_a, seed=1, lamp=lamp, lamp_k=lamp_k)
    mid = cached('mid', lambda: _haze(_layer_mid(seed + 1, P['mid'], P['moss'], P['moss_l'], P['fern']), P['haze'], .15), .5, .7, 420, .8)
    img.alpha_composite(mid, (int(-200 + cam * .55), 0))
    mist(img, w * drift * 1.3, 900, 1800, (140, 150, 200), .18 * mist_a, seed=2, lamp=lamp, lamp_k=lamp_k)
    if floor:
        near = cached('near', lambda: _layer_near(seed + 2, P['near'], P['moss'], P['moss_l'], lerp(P['fern'], (0, 0, 0), .2), side_trunks), .9, .9, 420, 1.0)
        img.alpha_composite(near, (int(-200 + cam * 1.0), 0))
    return P


def foreground(img, w, cam=0.0, seed=9, col=(10, 22, 20), lamp=None):
    key = ('fg', seed, col)
    if key not in _CACHE:
        lay = _fg(seed, col).filter(ImageFilter.GaussianBlur(5))
        _CACHE[key] = lay
    img.alpha_composite(_CACHE[key], (int(-200 + cam * 1.5 + 10 * math.sin(w * .6)), int(6 * math.sin(w * .8))))


_MIST = {}


def mist(img, w, y0, y1, col, alpha, seed=1, lamp=None, lamp_k=1.0, speed=18):
    """Drifting fog: a large soft noise tile scrolled sideways, brighter (violet) near the lamp."""
    key = (seed,)
    if key not in _MIST:
        rng = _rng(seed)
        sm = rng.normal(0, 1, (14, 40)).astype(np.float32)
        a = Image.fromarray(((sm * 50 + 128).clip(0, 255)).astype(np.uint8)).resize((W * 2, 900), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
        a2 = Image.fromarray(((rng.normal(0, 1, (40, 120)) * 50 + 128).clip(0, 255)).astype(np.uint8)).resize((W * 2, 900), Image.BICUBIC).filter(ImageFilter.GaussianBlur(10))
        arr = np.clip((np.asarray(a, np.float32) * .7 + np.asarray(a2, np.float32) * .3 - 118) / 70, 0, 1)
        _MIST[key] = arr
    arr = _MIST[key]
    h = y1 - y0
    off = int(w * speed * (1 + seed * .3)) % W
    sub = np.roll(arr, -off, axis=1)[:, :W]
    sub = np.asarray(Image.fromarray((sub * 255).astype(np.uint8)).resize((W, h), Image.BILINEAR), np.float32) / 255
    yy = np.linspace(0, 1, h)[:, None]
    env = np.sin(np.pi * yy) ** .8
    a = sub * env * alpha
    if lamp is not None:
        xx = np.arange(W)[None, :]
        yv = (np.arange(h) + y0)[:, None]
        dd = np.hypot(xx - lamp[0], yv - lamp[1])
        boost = 1 + 2.6 * lamp_k / (1 + (dd / 380) ** 2)
        a = a * boost
        lc = np.array(UV, np.float32)
        mixk = np.clip(lamp_k / (1 + (dd / 420) ** 2), 0, 1)[..., None]
        c = np.array(col, np.float32) * (1 - mixk) + lc * mixk
    else:
        c = np.broadcast_to(np.array(col, np.float32), (h, W, 3))
    a = np.clip(a, 0, .9)[..., None]
    y0c, y1c = max(0, y0), min(H, y1)
    base = np.asarray(img.crop((0, y0c, W, y1c)), np.float32)
    a = a[y0c - y0:y1c - y0]; cc = c[y0c - y0:y1c - y0] if c.ndim == 3 else c
    base[..., :3] = base[..., :3] * (1 - a) + cc * a
    img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)), (0, y0c))


def spores(img, w, lamp, n=60, r=420, seed=3, col=(220, 210, 255)):
    """Specks of dust and tiny insects drifting in the lamp light (brighter near it)."""
    rng = _rng(seed)
    d = ImageDraw.Draw(img)
    for i in range(n):
        a0 = rng.uniform(0, 6.28); rr = r * rng.uniform(.1, 1.0) ** .7; sp = rng.uniform(.2, .8)
        a = a0 + w * sp * (1 if i % 2 else -1)
        x = lamp[0] + math.cos(a) * rr + 20 * math.sin(w * 1.3 + i)
        y = lamp[1] + math.sin(a) * rr * .8 + 15 * math.cos(w * 1.1 + i)
        b = max(0, 1 - rr / r)
        s = rng.uniform(1.5, 3.5)
        d.ellipse([x - s, y - s, x + s, y + s], fill=col + (int(80 + 170 * b),))


# ---------------------------------------------------------------- the UV lamp
def lamp_glow(img, x, y, k=1.0, r=1.0, t=0.0):
    fl = 1 + .03 * math.sin(t * 37) + .02 * math.sin(t * 11)
    radial(img, x, y, 760 * r, UV_HALO, .55 * k * fl)
    radial(img, x, y, 320 * r, UV, .7 * k * fl)
    radial(img, x, y, 120 * r, UV_CORE, .9 * k * fl)


def uv_lamp(img, x, y, s=1.0, t=0.0, k=1.0, stand=True, ground=None, glow_on=True, rays=False):
    """A UV tube lamp (tube centre at (x, y), s = 1: a 300 px tube) on a tripod stand down to `ground`."""
    d = ImageDraw.Draw(img)
    th = 300 * s; tw = 34 * s
    gy = ground if ground is not None else y + 640 * s
    if stand:
        pole = (x, y + th / 2 + 30 * s)
        for dx in (-150, 0, 150):
            d.line([(x, gy - 220 * s), (x + dx * s, gy)], fill=INK, width=int(16 * s))
            d.line([(x, gy - 220 * s), (x + dx * s, gy)], fill=(70, 74, 86), width=int(8 * s))
        d.line([pole, (x, gy - 200 * s)], fill=INK, width=int(22 * s)); d.line([pole, (x, gy - 200 * s)], fill=(96, 100, 114), width=int(12 * s))
    if glow_on: lamp_glow(img, x, y, k, s * 1.1, t)
    if rays and glow_on: kit.light_rays(img, x, y, (170, 140, 255), n=10, alpha=.10 * k, spread=(160, 300), length=1100 * s, seed=4, phase=t * .05)
    d = ImageDraw.Draw(img)
    # bracket + end caps
    d.rounded_rectangle([x - tw * 1.3, y - th / 2 - 34 * s, x + tw * 1.3, y - th / 2 + 4 * s], int(8 * s), fill=(110, 114, 128), outline=INK, width=max(3, int(5 * s)))
    d.rounded_rectangle([x - tw * 1.3, y + th / 2 - 4 * s, x + tw * 1.3, y + th / 2 + 34 * s], int(8 * s), fill=(110, 114, 128), outline=INK, width=max(3, int(5 * s)))
    # the glowing tube
    m = mask(); ImageDraw.Draw(m).rounded_rectangle([x - tw / 2, y - th / 2, x + tw / 2, y + th / 2], int(tw / 2), fill=255)
    glow(img, m, UV, .9 * k, blur=int(22 * s), add=True)
    d.rounded_rectangle([x - tw / 2, y - th / 2, x + tw / 2, y + th / 2], int(tw / 2), fill=lerp((200, 180, 255), UV_CORE, k))
    d.rounded_rectangle([x - tw / 5, y - th / 2 + 8 * s, x + tw / 5, y + th / 2 - 8 * s], int(tw / 5), fill=(252, 250, 255))
    return {'tube': (x - tw / 2, y - th / 2, x + tw / 2, y + th / 2), 'ground': gy}


# ---------------------------------------------------------------- props
def camera_rig(img, x, gy, s=1.0, face=1, rec=True, t=0.0, lit=(150, 120, 255), lit_k=.4, h=520):
    """A high-speed camera on a tripod (lens toward `face`)."""
    d = ImageDraw.Draw(img)
    top = gy - h * s
    for dx in (-110, -10, 100):
        d.line([(x, top + 40 * s), (x + dx * s, gy)], fill=INK, width=int(14 * s)); d.line([(x, top + 40 * s), (x + dx * s, gy)], fill=(80, 84, 96), width=int(7 * s))
    bw, bh = 170 * s, 110 * s
    d.rounded_rectangle([x - bw / 2, top - bh, x + bw / 2, top], int(12 * s), fill=(46, 48, 58), outline=INK, width=max(3, int(5 * s)))
    d.rectangle([x - bw / 2 + 8 * s, top - bh + 8 * s, x + bw / 2 - 8 * s, top - bh + 26 * s], fill=lerp((70, 72, 86), lit, lit_k * .5))
    lx = x + face * (bw / 2 + 40 * s)
    d.rounded_rectangle([min(x + face * bw / 2, lx) - 2, top - bh * .78, max(x + face * bw / 2, lx) + 2, top - bh * .22], int(6 * s), fill=(30, 32, 40), outline=INK, width=max(3, int(4 * s)))
    d.ellipse([lx - 14 * s, top - bh * .74, lx + 14 * s, top - bh * .26], fill=(40, 60, 110), outline=INK, width=max(2, int(3 * s)))
    d.ellipse([lx - 6 * s, top - bh * .62, lx + 2 * s, top - bh * .45], fill=(150, 170, 230))
    if rec and int(t * 2) % 2 == 0:
        d.ellipse([x - bw / 2 + 14 * s, top - bh + 34 * s, x - bw / 2 + 34 * s, top - bh + 54 * s], fill=(255, 60, 60))
    return (lx, top - bh / 2)


def ir_lamp(img, x, gy, s=1.0, t=0.0, face=1, h=420):
    d = ImageDraw.Draw(img)
    top = gy - h * s
    d.line([(x, top), (x, gy)], fill=INK, width=int(14 * s)); d.line([(x, top), (x, gy)], fill=(80, 84, 96), width=int(7 * s))
    for dx in (-80, 80): d.line([(x, gy - 120 * s), (x + dx * s, gy)], fill=INK, width=int(10 * s))
    pw, ph = 150 * s, 120 * s
    d.rounded_rectangle([x - pw / 2, top - ph, x + pw / 2, top], int(10 * s), fill=(40, 40, 48), outline=INK, width=max(3, int(5 * s)))
    for i in range(4):
        for j in range(3):
            cx = x - pw / 2 + (i + .5) * pw / 4; cy = top - ph + (j + .5) * ph / 3
            r = 11 * s
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(110 + int(20 * math.sin(t * 3 + i + j)), 28, 34))
    radial(img, x + face * 30 * s, top - ph / 2, 160 * s, (120, 20, 30), .25)


def laptop(img, x, y, s=1.0, t=0.0, screen_fn=None):
    """An open laptop on a small field table; the screen shows a moth's circling trail."""
    d = ImageDraw.Draw(img)
    sw, sh = 300 * s, 190 * s
    d.polygon([(x - sw / 2 - 20 * s, y), (x + sw / 2 + 20 * s, y), (x + sw / 2 + 50 * s, y + 40 * s), (x - sw / 2 - 50 * s, y + 40 * s)], fill=(70, 74, 84), outline=INK)
    d.rounded_rectangle([x - sw / 2, y - sh, x + sw / 2, y], int(10 * s), fill=(40, 42, 50), outline=INK, width=max(3, int(5 * s)))
    sx0, sy0, sx1, sy1 = x - sw / 2 + 12 * s, y - sh + 12 * s, x + sw / 2 - 12 * s, y - 12 * s
    d.rectangle([sx0, sy0, sx1, sy1], fill=(18, 30, 26))
    cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    pts = [(cx + math.cos(a) * 80 * s * (1 + .1 * math.sin(a * 3)), cy + math.sin(a) * 50 * s) for a in np.linspace(t * 2, t * 2 + 9, 60)]
    d.line(pts, fill=(140, 240, 160), width=max(2, int(3 * s)))
    d.ellipse([cx - 8 * s, cy - 8 * s, cx + 8 * s, cy + 8 * s], fill=(220, 200, 255))
    radial(img, cx, cy, 170 * s, (90, 200, 140), .2)


def headlamp(img, g, on=True, beam_to=None, col=(255, 244, 210), k=1.0):
    """A headlamp band + lamp on a stickman's head; an optional soft beam cone toward beam_to (behind the actor:
    draw the beam first with headlamp_beam)."""
    hx, hy = g['head']; R = g['R']
    d = ImageDraw.Draw(img)
    d.arc([hx - R * 1.02, hy - R * 1.02, hx + R * 1.02, hy + R * 1.02], 190, 350, fill=(50, 54, 66), width=max(4, int(R * .16)))
    lx, ly = hx + R * .25 * (1 if g.get('look', 0) >= 0 else -1), hy - R * .92
    d.rounded_rectangle([lx - R * .32, ly - R * .2, lx + R * .32, ly + R * .2], int(R * .1), fill=(60, 64, 78), outline=INK, width=max(2, int(R * .07)))
    if on:
        d.ellipse([lx - R * .16, ly - R * .13, lx + R * .16, ly + R * .13], fill=col)
        radial(img, lx, ly, R * 1.0, col, .4 * k)
    return (lx, ly)


def headlamp_beam(img, src, dst, width, col=(255, 240, 200), a=.16):
    m = mask(); dd = ImageDraw.Draw(m)
    dx, dy = dst[0] - src[0], dst[1] - src[1]; L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    dd.polygon([src, (dst[0] + nx * width, dst[1] + ny * width), (dst[0] - nx * width, dst[1] - ny * width)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(24))
    kit.glow(img, m, col, a, blur=10, add=True)


def sheet(img, x0, y0, x1, y1, t=0.0, k=1.0, col=(246, 244, 255)):
    """A white cotton sheet hung flat overhead (a perspective quad, x0..x1 at the far edge y0 and wider near y1),
    glowing like a sky; soft folds that ripple."""
    lay = layer(); d = ImageDraw.Draw(lay)
    sag = 18 + 4 * math.sin(t * 1.4)
    far = [(x0 + 80, y0), (x1 - 80, y0)]; near = [(x1 + 60, y1), (x0 - 60, y1)]
    poly = far + near
    d.polygon(poly, fill=col + (255,))
    for i in range(1, 7):
        f = i / 7
        a = (far[0][0] + (near[1][0] - far[0][0]) * 0 + (far[1][0] - far[0][0]) * f, y0)
        b = (near[1][0] + (near[0][0] - near[1][0]) * f, y1 + sag * math.sin(f * math.pi))
        d.line([a, b], fill=(206, 204, 230, 255), width=6)
    d.line(near, fill=(214, 210, 236, 255), width=10)
    lay = kit.soft_layer(lay, 1)
    m = lay.split()[3]
    glow(img, m, (220, 214, 255), .8 * k, blur=60, add=True)
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    d.line(poly + [poly[0]], fill=INK, width=5)
    for (px, py) in (far[0], far[1]):
        d.line([(px, py), (px + (-160 if px < W / 2 else 160), py - 300)], fill=(60, 56, 50), width=4)
    return poly


# ---------------------------------------------------------------- the infrared camera look
def ir_view(img, w, label='IR CAM 2', fps='HIGH-SPEED', clock=0.0, rec=True, gain=1.25, hud=True):
    """Convert a rendered frame to the infrared camera look: grey-green monochrome, bright subjects, scan lines,
    noise, a vignette, and the camera HUD."""
    a = np.asarray(img.convert('RGB'), np.float32)
    L = (a[..., 0] * .35 + a[..., 1] * .45 + a[..., 2] * .45) / 255
    L = np.clip(L * gain, 0, 1) ** .85
    col0 = np.array((10, 18, 14), np.float32); col1 = np.array((214, 236, 214), np.float32)
    out = col0 + (col1 - col0) * L[..., None]
    rng = np.random.default_rng(int(w * 30) % 997)
    out += rng.normal(0, 7, out.shape[:2])[..., None]
    out[::4] *= .9
    res = Image.fromarray(out.clip(0, 255).astype(np.uint8)).convert('RGBA')
    if hud:
        d = ImageDraw.Draw(res)
        for (x0, y0, sx, sy) in ((60, 150, 1, 1), (W - 60, 150, -1, 1), (60, 1790, 1, -1), (W - 60, 1790, -1, -1)):
            d.line([(x0, y0), (x0 + sx * 90, y0)], fill=(220, 240, 220), width=6)
            d.line([(x0, y0), (x0, y0 + sy * 90)], fill=(220, 240, 220), width=6)
        if rec:
            if int(w * 2) % 2 == 0: d.ellipse([88, 186, 116, 214], fill=(255, 60, 60))
            d.text((130, 200), 'REC', font=font(34, True), fill=(230, 245, 230), anchor='lm')
        d.text((W - 90, 200), label, font=font(32, True), fill=(230, 245, 230), anchor='rm')
        ms = int(clock * 1000)
        d.text((W - 90, 1750), f'00:{int(clock) // 60:02d}:{int(clock) % 60:02d}.{ms % 1000:03d}', font=font(32, True), fill=(230, 245, 230), anchor='rm')
        d.text((100, 1750), fps, font=font(32, True), fill=(230, 245, 230), anchor='lm')
    return res


# ---------------------------------------------------------------- night skies
def stars(img, seed, n, box, size=(1, 3), t=0.0, col=(240, 240, 255), bright=1.0):
    rng = _rng(seed); d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        s = rng.uniform(*size) * (1 if rng.uniform() > .08 else 1.8)
        tw = .65 + .35 * math.sin(t * rng.uniform(1, 3) + i)
        a = int(255 * min(1, bright * tw * rng.uniform(.5, 1)))
        d.ellipse([x - s, y - s, x + s, y + s], fill=col + (a,))
        if s > 2.6:
            d.line([(x - s * 3, y), (x + s * 3, y)], fill=col + (a // 2,), width=1)
            d.line([(x, y - s * 3), (x, y + s * 3)], fill=col + (a // 2,), width=1)


def milky_way(img, seed=5, a=.4, ang=-.5):
    lay = layer(); m = mask(); dm = ImageDraw.Draw(m)
    cx, cy = W / 2, 600
    ca, sa = math.cos(ang), math.sin(ang)
    dm.polygon([(cx - 1400 * ca + 160 * sa, cy - 1400 * sa - 160 * ca), (cx + 1400 * ca + 160 * sa, cy + 1400 * sa - 160 * ca),
                (cx + 1400 * ca - 160 * sa, cy + 1400 * sa + 160 * ca), (cx - 1400 * ca - 160 * sa, cy - 1400 * sa + 160 * ca)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(90))
    nz = Image.fromarray(((np.random.default_rng(seed).normal(0, 1, (H // 30, W // 30)) * 50 + 128).clip(0, 255)).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    m = ImageChops.multiply(m, nz.point(lambda v: min(255, int(v * 1.4))))
    glow(img, m, (170, 170, 230), a, blur=8, add=True)
    rng = _rng(seed + 1); d = ImageDraw.Draw(img)
    for i in range(500):
        f = rng.uniform(-1, 1); o = rng.normal(0, 70)
        x = cx + f * 1300 * ca - o * sa; y = cy + f * 1300 * sa + o * ca
        if 0 <= x < W and 0 <= y < H:
            d.point((x, y), fill=(230, 230, 255, int(rng.uniform(80, 220))))


def hills(img, seed, y, amp, col, n=6, rough=.3):
    rng = _rng(seed)
    pts = [(0, H)]
    ph = rng.uniform(0, 6)
    for i in range(0, W + 41, 20):
        yy = y - amp * (.5 + .5 * math.sin(i / W * n + ph)) - amp * rough * math.sin(i / 37 + ph * 2)
        pts.append((i, yy))
    pts.append((W, H))
    ImageDraw.Draw(img).polygon(pts, fill=col)


def treeline(img, seed, y, h, col, n=40):
    rng = _rng(seed); d = ImageDraw.Draw(img)
    d.rectangle([0, y, W, H], fill=col)
    for i in range(n):
        x = rng.uniform(-40, W + 40); hh = h * rng.uniform(.5, 1.2); wd = hh * rng.uniform(.35, .6)
        for k in range(4):
            r = wd * (1 - k * .18)
            d.ellipse([x - r / 2 + rng.uniform(-8, 8), y - hh + k * hh * .22, x + r / 2, y - hh + k * hh * .22 + r * .8], fill=col)
        d.rectangle([x - 4, y - hh * .3, x + 4, y + 4], fill=col)


def moon(img, x, y, r, a=1.0):
    radial(img, x, y, r * 6, (120, 140, 200), .35 * a)
    radial(img, x, y, r * 2.4, (200, 210, 240), .4 * a)
    d = ImageDraw.Draw(img)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(242, 240, 228))
    rng = _rng(4)
    for i in range(9):
        cx, cy = x + rng.uniform(-.6, .6) * r, y + rng.uniform(-.6, .6) * r; cr = r * rng.uniform(.08, .22)
        if math.hypot(cx - x, cy - y) + cr < r * .95:
            d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(214, 212, 200))
    m = mask(); ImageDraw.Draw(m).ellipse([x - r, y - r, x + r, y + r], fill=255)
    sh = mask(); ImageDraw.Draw(sh).ellipse([x - r * .7, y - r * 1.2, x + r * 1.5, y + r * 1.1], fill=255)
    m2 = ImageChops.subtract(m, sh).filter(ImageFilter.GaussianBlur(r * .15))
    fill_mask(img, ImageChops.multiply(m2, m), (170, 170, 170), .25)


def night_stage(img, w, cam=0.0, glow_xy=None, moon_xy=(830, 300), grid=True, ground_y=1560):
    """The clean night-sky diagram stage: a deep navy sky with stars, a soft Moon, a dark horizon of hills and a faint
    measuring grid."""
    img.alpha_composite(vgrad([(0, (10, 16, 44)), (.6, (30, 40, 92)), (1, (44, 54, 110))]))
    stars(img, 3, 200, (0, 0, W, ground_y - 100), t=w)
    if moon_xy: moon(img, moon_xy[0] + cam * .1, moon_xy[1], 70)
    if grid:
        d = ImageDraw.Draw(img)
        for x in range(60, W, 120): d.line([(x, 0), (x, ground_y)], fill=(120, 140, 220, 22), width=2)
        for y in range(60, ground_y, 120): d.line([(0, y), (W, y)], fill=(120, 140, 220, 22), width=2)
    hills(img, 8, ground_y + 40, 120, (24, 30, 58), 4)
    treeline(img, 9, ground_y + 90, 110, (14, 18, 34), 34)
    d = ImageDraw.Draw(img)
    d.rectangle([0, ground_y + 140, W, H], fill=(10, 12, 24))


def ancient_night(img, w, cam=0.0):
    """Millions of years ago: no lamps; a bright starry sky with the Milky Way over a dark wild land and a lake."""
    img.alpha_composite(vgrad([(0, (8, 12, 40)), (.5, (34, 44, 100)), (.72, (70, 80, 140)), (1, (14, 16, 30))]))
    milky_way(img, 5, .55)
    stars(img, 11, 360, (0, 0, W, 1250), (1, 3.2), t=w, bright=1.0)
    moon(img, 230 + cam * .1, 330, 60)
    hills(img, 21, 1260, 230, (40, 46, 84), 3)
    hills(img, 22, 1340, 160, (24, 28, 54), 5)
    treeline(img, 23, 1420, 170, (10, 12, 26), 40)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1520, W, H], fill=(8, 10, 22))


def moon_sky(img, w, mx=760, my=520, r=170, cam=0.0):
    img.alpha_composite(vgrad([(0, (10, 18, 48)), (.6, (36, 52, 104)), (1, (50, 64, 110))]))
    stars(img, 7, 140, (0, 0, W, 1300), t=w, bright=.8)
    moon(img, mx + cam * .1, my, r)
    hills(img, 31, 1360, 140, (34, 46, 80), 3)


# ---------------------------------------------------------------- s02 sets
def candle_room(img, w, cam=0.0, flame=(560, 1180)):
    """An old room at night: plank walls, a small window with the moon, a table and a candle."""
    img.alpha_composite(vgrad([(0, (34, 22, 18)), (1, (58, 36, 24))]))
    d = ImageDraw.Draw(img)
    for i in range(0, W + 120, 120):
        x = i + cam * .5 % 120
        d.line([(x, 0), (x, 1320)], fill=(26, 16, 12), width=6)
    # window
    wx, wy = 230 + cam * .5, 330
    d.rectangle([wx - 150, wy - 190, wx + 150, wy + 190], fill=(16, 22, 50), outline=(70, 46, 30), width=26)
    stars(img, 41, 30, (wx - 130, wy - 170, wx + 130, wy + 170), t=w)
    d = ImageDraw.Draw(img)
    d.ellipse([wx + 30, wy - 120, wx + 90, wy - 60], fill=(240, 236, 210))
    d.line([(wx, wy - 190), (wx, wy + 190)], fill=(70, 46, 30), width=16)
    d.line([(wx - 150, wy), (wx + 150, wy)], fill=(70, 46, 30), width=16)
    # shelf with jars and a book
    d.rectangle([640 + cam * .5, 520, 1040 + cam * .5, 540], fill=(80, 52, 32), outline=INK, width=4)
    for k, (xx, hh, c) in enumerate(((680, 90, (90, 110, 80)), (760, 120, (120, 80, 60)), (850, 70, (110, 100, 130)), (930, 100, (130, 110, 70)))):
        d.rounded_rectangle([xx + cam * .5, 520 - hh, xx + 60 + cam * .5, 520], 10, fill=c, outline=INK, width=4)
    # table
    d.rectangle([0, 1320, W, H], fill=(52, 32, 22))
    d.polygon([(80, 1290), (1000, 1290), (1060, 1380), (20, 1380)], fill=(104, 66, 40), outline=INK)
    d.rectangle([20, 1380, 1060, 1420], fill=(76, 46, 28), outline=INK, width=4)
    fx, fy = flame
    # candle glow
    radial(img, fx, fy, 900, (255, 160, 70), .55 * (1 + .05 * math.sin(w * 13)))
    radial(img, fx, fy, 260, (255, 210, 120), .6)
    d = ImageDraw.Draw(img)
    # candle holder + candle
    d.ellipse([fx - 110, 1300, fx + 110, 1340], fill=(150, 110, 60), outline=INK, width=5)
    d.rectangle([fx - 34, fy + 50, fx + 34, 1316], fill=(246, 236, 206), outline=INK, width=5)
    d.polygon([(fx - 34, fy + 50), (fx - 10, fy + 64), (fx + 12, fy + 54), (fx + 34, fy + 50)], fill=(230, 214, 180))
    d.line([(fx, fy + 52), (fx, fy + 30)], fill=INK, width=5)
    fl = 1 + .08 * math.sin(w * 17) + .05 * math.sin(w * 29)
    d.ellipse([fx - 18, fy - 40 * fl, fx + 18, fy + 34], fill=(255, 200, 80))
    d.ellipse([fx - 9, fy - 18 * fl, fx + 9, fy + 28], fill=(255, 250, 220))
    return (fx, fy)


def street_lamp(img, w, cam=0.0, head=(600, 560)):
    """A night street: brick buildings with lit windows, an old street lamp with an amber globe."""
    img.alpha_composite(vgrad([(0, (12, 14, 34)), (.6, (34, 30, 56)), (1, (30, 24, 30))]))
    stars(img, 51, 60, (0, 0, W, 700), t=w, bright=.6)
    d = ImageDraw.Draw(img)
    for k, (x0, x1, top, c) in enumerate(((-40, 380, 520, (70, 40, 40)), (360, 720, 700, (56, 46, 54)), (700, 1120, 460, (64, 44, 36)))):
        x0 += cam * .4; x1 += cam * .4
        d.rectangle([x0, top, x1, 1500], fill=c, outline=INK, width=5)
        for r_, yy in enumerate(range(top + 60, 1400, 150)):
            for c_, xx in enumerate(range(int(x0) + 50, int(x1) - 60, 120)):
                lit = ((c_ * 7 + r_ * 3 + k) % 5) < 2                  # by window index, so a camera pan can't flip them
                d.rectangle([xx, yy, xx + 60, yy + 90], fill=(250, 200, 110) if lit else (30, 30, 44), outline=INK, width=3)
    d.rectangle([0, 1500, W, H], fill=(40, 38, 44))
    d.rectangle([0, 1500, W, 1530], fill=(70, 66, 72))
    hx, hy = head
    hx += cam * .9
    radial(img, hx, hy, 900, (255, 170, 70), .5)
    radial(img, hx, hy, 260, (255, 210, 130), .7)
    d = ImageDraw.Draw(img)
    d.rectangle([hx - 16, hy + 70, hx + 16, 1520], fill=(36, 38, 46), outline=INK, width=4)
    d.rectangle([hx - 40, 1460, hx + 40, 1520], fill=(36, 38, 46), outline=INK, width=4)
    d.polygon([(hx - 70, hy - 70), (hx + 70, hy - 70), (hx + 46, hy + 70), (hx - 46, hy + 70)], fill=(255, 220, 140), outline=INK)
    d.polygon([(hx - 90, hy - 70), (hx + 90, hy - 70), (hx, hy - 140)], fill=(36, 38, 46), outline=INK)
    d.ellipse([hx - 30, hy - 30, hx + 30, hy + 30], fill=(255, 250, 220))
    # the cone of light on the pavement
    m = mask(); ImageDraw.Draw(m).polygon([(hx - 46, hy + 70), (hx + 46, hy + 70), (hx + 420, 1600), (hx - 420, 1600)], fill=255)
    glow(img, m, (255, 190, 100), .18, blur=40, add=True)
    return (hx, hy)


def desk_wall(img, w, cam=0.0):
    """s13 back wall: a window onto the night sky, a shelf."""
    img.alpha_composite(vgrad([(0, (20, 22, 40)), (1, (40, 34, 46))]))
    d = ImageDraw.Draw(img)
    wx = 640 + cam * .4
    d.rectangle([wx, 200, wx + 380, 640], fill=(14, 20, 50), outline=(70, 56, 52), width=20)
    stars(img, 61, 34, (wx + 20, 220, wx + 360, 620), t=w)
    d = ImageDraw.Draw(img)
    d.ellipse([wx + 250, 260, wx + 310, 320], fill=(240, 236, 214))
    d.line([(wx + 190, 200), (wx + 190, 640)], fill=(70, 56, 52), width=12)
    d.rectangle([60 + cam * .4, 420, 420 + cam * .4, 440], fill=(90, 60, 40), outline=INK, width=4)
    for k, (xx, hh, c) in enumerate(((80, 150, (70, 90, 130)), (130, 170, (150, 70, 60)), (186, 130, (60, 110, 80)), (236, 160, (180, 150, 80)), (300, 110, (120, 90, 140)))):
        d.rectangle([xx + cam * .4, 420 - hh, xx + 44 + cam * .4, 420], fill=c, outline=INK, width=4)


def desk_top(img, w, cam=0.0, top=980):
    """s13 desk surface (perspective) with a map and a warm desk lamp pool."""
    d = ImageDraw.Draw(img)
    d.polygon([(-60, top), (W + 60, top), (W + 260, H), (-260, H)], fill=(126, 80, 46))
    for k in range(10):
        y = top + 20 + k * k * 11
        d.line([(-260, y), (W + 260, y)], fill=(108, 66, 38), width=3)
    d.rectangle([-60, top - 26, W + 60, top], fill=(96, 60, 34))
    d.line([(-60, top - 26), (W + 60, top - 26)], fill=INK, width=6)
    d.polygon([(60, 1330), (470, 1270), (560, 1760), (110, 1840)], fill=(222, 206, 166), outline=INK)
    for k in range(6):
        d.line([(110 + k * 16, 1390 + k * 70), (480 + k * 12, 1340 + k * 70)], fill=(176, 156, 116), width=3)
    d.line([(150, 1500), (300, 1420), (420, 1560)], fill=(200, 80, 70), width=5)
    radial(img, 560, 1150, 1100, (255, 190, 110), .42)
    d = ImageDraw.Draw(img)
    d.line([(1010, top - 10), (960, 560)], fill=INK, width=22); d.line([(1010, top - 10), (960, 560)], fill=(60, 64, 76), width=12)
    d.line([(960, 560), (800, 640)], fill=INK, width=22); d.line([(960, 560), (800, 640)], fill=(60, 64, 76), width=12)
    d.polygon([(740, 590), (880, 630), (820, 720), (690, 700)], fill=(60, 120, 90), outline=INK)
    radial(img, 760, 740, 260, (255, 220, 150), .5)

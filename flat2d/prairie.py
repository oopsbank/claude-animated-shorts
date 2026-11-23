"""flat2d.prairie: kit layers for the Wind Cave video (Black Hills prairie, the breathing hole, storms, the cave).

Layers (each draws in place, back to front; `t` is time in s, `cam` the parallax pan in px):
- skies: `sky` (painted gradient: fair / storm / dusk / morning / deep), `sun`, `cumulus` (flat two-tone clouds that
  drift), `storm_deck` (heavy slate-purple cloud base), `lightning` (bolt + cloud glow).
- land: `pine_ridge` (Black Hills ridges with pine-tooth tops, cached), `hill` (rolling golden hill band with a lit
  crest and shade toward the base), `grass` (blades that bend with the breeze and with the hole's breath),
  `tufts` (crest grass), `outcrop` (faceted limestone ledge with the small dark hole), `rain`.
- the BREATH: `breath` (pale blue-white wind ribbons + flying grass/dust that stream OUT of the hole or IN to it;
  the direction is the whole point: out = dashes travel away and fan wide, in = they converge and shrink).
- props: `hat_layer` (a cowboy hat for flying / tumbling), `paper` (a sheet for scale), `barometer`.
- underground: `earth_section` (strata), `maze` (cached tunnel network), `lamp_light` (caver's helmet beam).
- `cabin` (airliner cabin wall + window), `chips_bag` (puffs up).

Rules: blur masks only (kit.fill_mask / glow); glow never on faces; ink outlines ~5-6 px at 1080.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit
from kit import W, H, INK, vgrad, radial, mask, glow, fill_mask, layer, lerp, rgb

# ---------------------------------------------------------------- palette
GOLD = ((255, 218, 124), (232, 174, 76), (186, 124, 52), (132, 82, 40))      # lit -> deep
GREEN = ((186, 210, 120), (140, 178, 86), (102, 140, 66), (72, 100, 52))
GOLD_STORM = ((176, 164, 120), (150, 132, 96), (116, 100, 78), (84, 72, 64))
BREATH = (226, 244, 255)                  # ribbon body
BREATH_EDGE = (104, 160, 226)             # ribbon ink edge (cool, not black)
BREATH_GLOW = (150, 205, 255)
ROCK = ((226, 212, 186), (178, 162, 142), (128, 114, 108), (88, 78, 82))    # top lit, face, shade, deep
TOM_HAT = (122, 74, 40)
JESSE_HAT = (128, 134, 146)

_cache = {}
def cached(key, fn):
    if key not in _cache:
        if len(_cache) > 120: _cache.clear()
        _cache[key] = fn()
    return _cache[key]


def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- skies
SKIES = {
    'fair':    [(0, (58, 104, 178)), (.35, (104, 158, 214)), (.62, (176, 204, 226)), (.8, (252, 222, 170)), (1, (255, 206, 140))],
    'morning': [(0, (84, 138, 200)), (.4, (146, 196, 232)), (.75, (214, 234, 240)), (1, (240, 236, 206))],
    'storm':   [(0, (34, 28, 56)), (.3, (66, 56, 96)), (.6, (104, 92, 128)), (.85, (150, 128, 150)), (1, (176, 150, 150))],
    'dusk':    [(0, (40, 34, 86)), (.35, (110, 62, 120)), (.6, (210, 104, 112)), (.8, (252, 164, 100)), (1, (255, 206, 130))],
    'sunset':  [(0, (70, 86, 150)), (.3, (150, 130, 170)), (.55, (250, 170, 120)), (.75, (255, 200, 120)), (1, (255, 222, 160))],
    'deep':    [(0, (10, 14, 40)), (.25, (24, 46, 104)), (.55, (64, 120, 200)), (.85, (150, 200, 240)), (1, (214, 234, 246))],
}


def sky(img, kind='fair', y1=H, mixk=0.0, kind2=None):
    """Painted vertical gradient over [0, y1). mixk blends toward kind2 (storm rolling in / clearing)."""
    def build(k):
        return vgrad(SKIES[k], W, y1)
    a = cached(('sky', kind, y1), lambda: build(kind))
    if kind2 and mixk > 0:
        b = cached(('sky', kind2, y1), lambda: build(kind2))
        a = Image.blend(a, b, min(1.0, mixk))
    img.paste(a, (0, 0))


def sun(img, x, y, r, t, col=(255, 236, 180), core=(255, 252, 236), a=.85):
    radial(img, x, y, r * 6, col, .5 * a + .03 * math.sin(t * 1.3))
    radial(img, x, y, r * 2.2, (255, 248, 220), .7 * a)
    d = ImageDraw.Draw(img); d.ellipse([x - r, y - r, x + r, y + r], fill=core)


def _cloud_lay(seed, s, lit, shade, mid=None, flat=True):
    """One flat two-tone cumulus (cached): shade body, lit top puffs, a crisp flat base."""
    def build():
        rng = np.random.default_rng(seed)
        w, h = int(620 * s), int(300 * s)
        lay = layer(w, h); d = ImageDraw.Draw(lay)
        n = 7; puffs = []
        for i in range(n):
            u = (i + .5) / n
            r = s * (60 + 70 * math.sin(math.pi * u) * rng.uniform(.75, 1.2))
            x = w * (.12 + .76 * u) + rng.uniform(-14, 14) * s
            y = h * .72 - r * rng.uniform(.55, .9)
            puffs.append((x, y, r))
        base = h * .74
        for x, y, r in puffs: d.ellipse([x - r, y - r, x + r, min(base, y + r)], fill=rgb(shade) + (255,))
        d.rectangle([w * .1, base - 34 * s, w * .9, base], fill=rgb(shade) + (255,))
        if mid:
            for x, y, r in puffs: d.ellipse([x - r * .9, y - r * .96, x + r * .9, y + r * .5], fill=rgb(mid) + (255,))
        for x, y, r in puffs: d.ellipse([x - r * .78, y - r * .98, x + r * .62, y + r * .22], fill=rgb(lit) + (255,))
        # flatten the base
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rectangle([0, 0, w, base], fill=255)
        lay.putalpha(ImageChops.multiply(lay.split()[3], m))
        return lay
    return cached(('cloud', seed, round(s, 2), lit, shade, mid), build)


def cumulus(img, t, items, lit=(255, 250, 240), shade=(198, 206, 228), mid=(232, 234, 244), alpha=1.0):
    """items = [(x, y, scale, seed, drift px/s)]. Clouds drift and wrap."""
    for x, y, s, seed, v in items:
        lay = _cloud_lay(seed, s, lit, shade, mid)
        xx = (x + v * t + 400) % (W + 900) - 500
        if alpha < 1:
            lay = lay.copy(); lay.putalpha(lay.split()[3].point(lambda q: int(q * alpha)))
        img.alpha_composite(lay, (int(xx - lay.width / 2), int(y - lay.height * .74)))


def storm_deck(img, t, y_base, dark=(46, 38, 70), mid=(78, 66, 104), lit=(128, 112, 150), seed=4, drift=30, k=1.0, y_top=-60):
    """A heavy storm-cloud ceiling: a dark mass from y_top down to a lumpy base at y_base, with lit rolls."""
    rng = np.random.default_rng(seed)
    m = mask(); d = ImageDraw.Draw(m)
    off = (t * drift) % 260
    d.rectangle([0, y_top, W, y_base - 60], fill=255)
    for i in range(-2, 9):
        x = i * 150 + off + rng.uniform(-30, 30); r = rng.uniform(90, 150)
        d.ellipse([x - r * 1.3, y_base - 60 - r * .8, x + r * 1.3, y_base - 60 + r * .7], fill=255)
    fill_mask(img, m, dark, k)
    m2 = mask(); d2 = ImageDraw.Draw(m2)
    for row in range(3):
        yy = y_top + (y_base - y_top) * (.25 + .22 * row)
        for i in range(-2, 8):
            x = i * 190 + (off * (1.3 + .3 * row)) % 190 + rng.uniform(-40, 40); r = rng.uniform(70, 120)
            d2.ellipse([x - r * 1.5, yy - r * .55, x + r * 1.5, yy + r * .35], fill=255)
    fill_mask(img, m2, mid, .85 * k, blur=3)
    m3 = mask(); d3 = ImageDraw.Draw(m3)
    for i in range(-2, 9):
        x = i * 150 + off + rng.uniform(-30, 30) + 20; r = rng.uniform(70, 120)
        d3.ellipse([x - r * 1.1, y_base - 60 - r * .78, x + r * .9, y_base - 60 - r * .3], fill=255)
    fill_mask(img, m3, lit, .7 * k, blur=2)


def thunderhead(img, t, x, base_y, s=1.0, seed=5, cols=((96, 86, 128), (132, 120, 160), (196, 180, 206)), rain_a=.5, alpha=1.0):
    """A distant cumulonimbus: a dark flat base, a towering puffy column, a flat anvil top, a rain curtain below.
    Cached shape; moves: the rain curtain streaks drift and the cloud breathes 1%."""
    def build():
        rng = np.random.default_rng(seed)
        w, h = int(760 * s), int(900 * s)
        lay = layer(w, h); d = ImageDraw.Draw(lay)
        cx, by = w / 2, h * .78
        puffs = []
        for i in range(16):
            q = i / 15
            yy = by - q * h * .62; spread = (1 - q) * .3 + .12
            r = s * rng.uniform(60, 110) * (1.1 - .3 * q)
            puffs.append((cx + rng.uniform(-1, 1) * w * spread, yy, r))
        for k in range(5):                                   # anvil
            puffs.append((cx + (k - 2) * w * .15 + rng.uniform(-20, 20) * s, by - h * .66, s * rng.uniform(50, 70)))
        for px, py, r in puffs: d.ellipse([px - r * 1.2, py - r, px + r * 1.2, min(by, py + r)], fill=rgb(cols[0]) + (255,))
        d.rectangle([cx - w * .34, by - 40 * s, cx + w * .34, by], fill=rgb(cols[0]) + (255,))
        for px, py, r in puffs: d.ellipse([px - r * 1.05, py - r * .98, px + r * .9, py + r * .3], fill=rgb(cols[1]) + (255,))
        for px, py, r in puffs:
            if py < by - h * .25: d.ellipse([px - r * .85, py - r * .98, px + r * .45, py - r * .1], fill=rgb(cols[2]) + (255,))
        d.polygon([(cx - w * .48, by - h * .6), (cx + w * .5, by - h * .64), (cx + w * .3, by - h * .7), (cx - w * .3, by - h * .7)],
                  fill=rgb(cols[2]) + (255,))
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rectangle([0, 0, w, by], fill=255)
        lay.putalpha(ImageChops.multiply(lay.split()[3], m))
        return lay, (cx, by)
    lay, (cx, by) = cached(('thunder', seed, round(s, 2), cols), build)
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.split()[3].point(lambda q: int(q * alpha)))
    img.alpha_composite(lay, (int(x - cx), int(base_y - by)))
    if rain_a > 0:                                           # rain curtain
        m = mask(); d = ImageDraw.Draw(m); rng = np.random.default_rng(seed + 3)
        for i in range(40):
            xx = x + rng.uniform(-.3, .3) * lay.width + ((t * 40 + i * 13) % 60) - 30
            d.line([(xx, base_y), (xx - 40 * s, base_y + rng.uniform(120, 260) * s)], fill=int(255 * rng.uniform(.4, 1)), width=max(2, int(5 * s)))
        fill_mask(img, m.filter(ImageFilter.GaussianBlur(3)), cols[0], rain_a * alpha)


def lightning(img, t, t0, x, y0, y1, seed=1, col=(236, 226, 255), dur=.32, cloud=(200, 180, 255)):
    """A bolt that flashes at t0 (two flickers) with a cloud glow. Returns the flash strength (0..1)."""
    u = t - t0
    if u < 0 or u > dur: return 0.0
    k = (1 - u / dur) ** 1.4 * (1 if (u < .06 or .11 < u < .2) else .35)
    rng = np.random.default_rng(seed)
    pts = [(x, y0)]; yy = y0
    while yy < y1:
        yy += rng.uniform(50, 110); pts.append((pts[-1][0] + rng.uniform(-60, 60), min(y1, yy)))
    m = mask(); d = ImageDraw.Draw(m); d.line(pts, fill=255, width=14, joint='curve')
    for i in (2, 4):
        if i < len(pts):
            b = [pts[i]]; bx, by = pts[i]
            for _ in range(3): bx += rng.uniform(-70, 70); by += rng.uniform(40, 80); b.append((bx, by))
            d.line(b, fill=255, width=7, joint='curve')
    glow(img, m, cloud, .9 * k, blur=40, add=True)
    radial(img, x, y0, 700, cloud, .55 * k)
    fill_mask(img, m, col, k)
    d2 = ImageDraw.Draw(img)
    return k


def rain(img, t, box, n=160, seed=3, col=(200, 210, 240), a=150, slant=.3, L=70, speed=1600):
    lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        x = rng.uniform(x0 - 200, x1); y = (rng.uniform(y0, y1) + speed * t * rng.uniform(.85, 1.15)) % (y1 - y0) + y0
        x = x + (y - y0) * slant
        if x0 <= x <= x1:
            d.line([(x, y), (x - L * slant, y - L)], fill=rgb(col) + (int(a * rng.uniform(.5, 1)),), width=3)
    img.alpha_composite(lay)


# ---------------------------------------------------------------- land
def pine_ridge(seed, y_base, h, col, w=W + 600, tree=(26, 60), dens=1.0, lit=None, haze_col=None, haze_a=0.0, ink=None):
    """Black Hills ridge (cached RGBA layer, w wide, paste at x = -300 + cam*f): a rounded ridge line covered
    in pine 'teeth'. lit: a lighter rim on the crest's sun side; haze_col: fades toward the base."""
    def build():
        rng = np.random.default_rng(seed)
        lay = layer(w, H); d = ImageDraw.Draw(lay)
        xs = np.arange(0, w + 20, 20)
        ph = rng.uniform(0, 6, 3)
        top = y_base - h * (.55 + .25 * np.sin(xs / w * 2 * math.pi * 1.3 + ph[0]) + .15 * np.sin(xs / w * 2 * math.pi * 3.1 + ph[1])
                            + .05 * np.sin(xs / w * 2 * math.pi * 7 + ph[2]))
        poly = [(x, y) for x, y in zip(xs, top)] + [(w, H), (0, H)]
        d.polygon(poly, fill=rgb(col))
        # pine teeth along the crest and scattered down the slope
        x = 0.0
        while x < w:
            yt = float(np.interp(x, xs, top)); th = rng.uniform(*tree); tw = th * rng.uniform(.32, .42)
            for k in range(3):                      # three stacked tiers per pine
                yy = yt - th * (1 - k * .28); ww = tw * (.55 + .25 * k)
                d.polygon([(x, yy - th * .25), (x - ww, yy + th * .3), (x + ww, yy + th * .3)], fill=rgb(col))
            if lit:
                d.polygon([(x, yt - th), (x - tw * .8, yt + 2), (x - tw * .15, yt + 2)], fill=rgb(lit))
            x += rng.uniform(.35, .9) * tw * 2 / dens
        if ink: d.line(list(zip(xs, top)), fill=rgb(ink), width=3)
        if haze_col and haze_a > 0:
            m = np.zeros((H, w), np.float32); ys = np.arange(H)
            m[:] = np.clip((ys - (y_base - h)) / (h * 1.6), 0, 1)[:, None] * haze_a
            hz = Image.fromarray((m * 255).astype(np.uint8)); al = lay.split()[3]
            fill_mask(lay, ImageChops.multiply(hz, al), haze_col)
        return lay
    return cached(('ridge', seed, y_base, h, col, w, tree, dens, lit, haze_col, haze_a, ink), build)


def hill_edge(seed, y, amp, w=W + 600, waves=(1.1, 2.7)):
    rng = np.random.default_rng(seed); ph = rng.uniform(0, 6, 2)
    xs = np.arange(0, w + 20, 20)
    ys = y - amp * (np.sin(xs / w * 2 * math.pi * waves[0] + ph[0]) * .7 + np.sin(xs / w * 2 * math.pi * waves[1] + ph[1]) * .3)
    return xs, ys


def hill(seed, y, amp, cols, w=W + 600, ink=INK, ink_w=5, shade_k=.5, streaks=True, waves=(1.1, 2.7), crest=None):
    """Rolling prairie hill band (cached layer): lit crest, darker toward the base, wind-combed grass streaks."""
    def build():
        xs, ys = hill_edge(seed, y, amp, w, waves)
        lay = layer(w, H); d = ImageDraw.Draw(lay)
        poly = list(zip(xs, ys)) + [(w, H), (0, H)]
        d.polygon(poly, fill=rgb(cols[1]))
        # shade toward the base
        m = np.zeros((H, w), np.float32); yy = np.arange(H)
        top = ys.min()
        m[:] = np.clip((yy - top) / 520, 0, 1)[:, None] ** 1.3 * shade_k
        pm = mask(w, H); ImageDraw.Draw(pm).polygon(poly, fill=255)
        fill_mask(lay, Image.fromarray((m * np.asarray(pm, np.float32)).astype(np.uint8)), cols[2])
        # lit crest band
        cm = mask(w, H); dc = ImageDraw.Draw(cm)
        dc.polygon(list(zip(xs, ys)) + list(zip(xs[::-1], ys[::-1] + 70)), fill=255)
        fill_mask(lay, cm, crest or cols[0], .8, blur=14)
        al = lay.split()[3]
        if streaks:                                   # wind-combed streaks (long thin strokes following the slope)
            rng = np.random.default_rng(seed + 7); sm = mask(w, H); ds = ImageDraw.Draw(sm)
            for _ in range(int(w / 6)):
                x = rng.uniform(0, w); y0 = float(np.interp(x, xs, ys)) + rng.uniform(20, 600)
                L = rng.uniform(40, 140)
                ds.line([(x, y0), (x + L, y0 - L * .08)], fill=int(rng.uniform(80, 200)), width=int(rng.uniform(3, 6)))
            sm = ImageChops.multiply(sm, al)
            fill_mask(lay, sm, cols[0], .35)
            rng2 = np.random.default_rng(seed + 9); sm2 = mask(w, H); ds2 = ImageDraw.Draw(sm2)
            for _ in range(int(w / 9)):
                x = rng2.uniform(0, w); y0 = float(np.interp(x, xs, ys)) + rng2.uniform(30, 700)
                L = rng2.uniform(30, 110)
                ds2.line([(x, y0), (x + L, y0 - L * .06)], fill=int(rng2.uniform(80, 200)), width=int(rng2.uniform(2, 5)))
            fill_mask(lay, ImageChops.multiply(sm2, al), cols[3], .25)
        if ink: d.line(list(zip(xs, ys)), fill=rgb(ink), width=ink_w, joint='curve')
        return lay
    return cached(('hill', seed, y, amp, cols, w, ink, ink_w, shade_k, streaks, waves, crest), build)


def edge_y(seed, y, amp, x, w=W + 600, waves=(1.1, 2.7)):
    """y of a hill's crest at frame x (for a layer pasted at -300)."""
    xs, ys = cached(('edge', seed, y, amp, w, waves), lambda: hill_edge(seed, y, amp, w, waves))
    return float(np.interp(x + 300, xs, ys))


def paste_band(img, lay, cam, f=1.0, dy=0):
    img.alpha_composite(lay, (int(-300 + cam * f), int(dy)))


# ---------------------------------------------------------------- grass that bends with the wind
def _blade_set(seed, box, n, hmin, hmax, ytop=None, clump=(1, 1), spread=.5):
    def build():
        rng = np.random.default_rng(seed); x0, y0, x1, y1 = box
        out = []
        for _ in range(n):
            x = rng.uniform(x0, x1); y = rng.uniform(y0, y1)
            if ytop is not None:
                yt = ytop(x)
                if y < yt: y = yt + rng.uniform(0, 30)
            p = min(1.0, max(0.0, (y - y0) / max(1, (y1 - y0))))
            hc = (hmin + (hmax - hmin) * p) * rng.uniform(.75, 1.2)
            ci0 = rng.integers(0, 3); ph = rng.uniform(0, 6.3)
            m = int(rng.integers(clump[0], clump[1] + 1))
            for j in range(m):
                f = (j + .5) / m - .5 if m > 1 else 0.0
                out.append((y + j * .01, x + f * hc * .25, hc * rng.uniform(.65, 1.1) * (1 - .35 * abs(f)), ph + j * .4,
                            int((ci0 + j) % 4) if j else int(ci0), rng.uniform(.8, 1.2), f * spread + rng.uniform(-.08, .08)))
        out.sort()
        return out
    return cached(('blades', seed, box, n, hmin, hmax, ytop is not None, clump, spread), build)


def flow_at(x, y, src):
    """Bend (+ = toward screen right) caused by the hole's breath at (x, y). src = (hx, hy, strength, sign, ang)
    sign +1 = out (blades bend away from the hole), -1 = in (toward it)."""
    if not src: return 0.0
    hx, hy, k, sign, ang = src
    dx, dy = x - hx, y - hy; r = math.hypot(dx, dy) + 1
    fall = math.exp(-r / 340.0)
    # radial unit direction; mostly horizontal component bends grass
    ux = dx / r
    # bias toward the main jet direction
    jx = math.cos(ang)
    return k * fall * sign * (ux * .7 + jx * .5) * 1.0


def grass(img, t, box, n, hmin, hmax, cols=GOLD, wind=.25, gust=.35, seed=1, src=None, ytop=None, w0=5.0, ink=None,
          cam=0.0, par=1.0, tip=None, light_dir=1, clump=(1, 1), spread=.5):
    """Grass blades rooted in box (back to front by y). Each blade bends by the breeze (wind + travelling gust
    waves across the field) + the hole's breath (flow_at). Moves: every blade sways on its own phase."""
    d = ImageDraw.Draw(img)
    tipc = tip or lerp(rgb(cols[0]), (255, 246, 214), .5)
    for y, x, h, ph, ci, ww, lean in _blade_set(seed, box, n, hmin, hmax, ytop, clump, spread):
        x = x + cam * par
        if x < -60 or x > W + 60: continue
        gw = math.sin(x * .006 - t * 2.1) * .5 + .5                 # gust band travelling across the field
        b = wind + lean + gust * gw * (.6 + .4 * math.sin(t * 3.3 + ph)) + .08 * math.sin(t * 2.4 + ph)
        b += flow_at(x, y, src) * (1 + .25 * math.sin(t * 9 + ph * 3))
        b = max(-1.6, min(1.6, b))
        a = b * 1.05                                                # bend angle (rad) at the tip
        tx, ty = x + math.sin(a) * h, y - math.cos(a) * h * (1 - .1 * abs(b))
        mx, my = x + math.sin(a * .45) * h * .55, y - math.cos(a * .45) * h * .55
        wb = w0 * ww * (h / hmax) ** .5 + 1.5
        col = rgb(cols[min(3, ci)]) if ci < 3 else lerp(rgb(cols[2]), rgb(cols[3]), .5)
        # tapered blade: two root corners, mid, tip
        nx, ny = math.cos(a * .45), math.sin(a * .45)
        pts = [(x - wb, y), (mx - wb * .6 * nx, my - wb * .6 * ny), (tx, ty), (mx + wb * .6 * nx, my + wb * .6 * ny), (x + wb, y)]
        d.polygon(pts, fill=col)
        if ink: d.line(pts, fill=rgb(ink), width=2)
        if ci == 0 or (ci == 1 and ph > 4.5):                      # sunlit tips
            d.line([(mx + (tx - mx) * .45, my + (ty - my) * .45), (tx, ty)], fill=tipc, width=max(2, int(wb * .6)))


def seed_heads(img, t, box, n, seed=5, col=(250, 226, 160), src=None, cam=0.0, wind=.3):
    """Tall grass seed heads (oat-like) poking above the field, nodding in the wind."""
    d = ImageDraw.Draw(img); rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        x = rng.uniform(x0, x1) + cam; y = rng.uniform(y0, y1); h = rng.uniform(60, 140) * (.6 + .6 * (y - y0) / max(1, y1 - y0))
        b = wind + .3 * math.sin(t * 2.2 + i) + flow_at(x, y, src)
        b = max(-1.5, min(1.5, b))
        tx, ty = x + math.sin(b) * h, y - math.cos(b) * h
        d.line([(x, y), ((x + tx) / 2 + b * 6, (y + ty) / 2), (tx, ty)], fill=(150, 110, 60), width=3, joint='curve')
        for k in range(4):
            q = .55 + k * .14; px, py = x + (tx - x) * q, y + (ty - y) * q
            d.ellipse([px - 6, py - 3, px + 6, py + 3], fill=col)


# ---------------------------------------------------------------- the outcrop and the hole
def _slab(rng, x0, x1, y0, y1, s, jit=10):
    """An irregular slab outline (clockwise from top-left), px relative to the hole."""
    n = 7
    top = [(x0 + (x1 - x0) * i / (n - 1), y0 + rng.uniform(-jit, jit) * s) for i in range(n)]
    top[0] = (x0 + 18 * s, y0 + 14 * s); top[-1] = (x1 - 14 * s, y0 + 12 * s)
    right = [(x1 + rng.uniform(-6, 10) * s, y0 + (y1 - y0) * .45)]
    bot = [(x1 - 10 * s, y1), (x0 + 10 * s, y1)]
    left = [(x0 - rng.uniform(0, 10) * s, y0 + (y1 - y0) * .5)]
    return top + right + bot + left


def outcrop_layer(s=1.0, seed=3, cols=ROCK, hole_k=1.0, wet=0.0):
    """A low limestone ledge in the hillside: three stacked slabs (lit tops, buff faces, dark undercuts, joints,
    lichen), the small dark hole in the bottom slab's face at (0, 0). Cached. Returns (layer, (ox, oy))."""
    def build():
        rng = np.random.default_rng(seed)
        slabs = [(-330, 320, -40, 120), (-250, 230, -125, -40), (-150, 120, -190, -125)]   # bottom -> top (x0, x1, y0, y1)
        shapes = [_slab(rng, x0 * s, x1 * s, y0 * s, y1 * s, s) for x0, x1, y0, y1 in slabs]
        pad = 30 * s + 20
        allp = [p for sh in shapes for p in sh]
        X0, Y0 = min(p[0] for p in allp) - pad, min(p[1] for p in allp) - pad
        w, h = int(max(p[0] for p in allp) - X0 + pad), int(max(p[1] for p in allp) - Y0 + pad)
        lay = layer(w, h); d = ImageDraw.Draw(lay)
        P_ = lambda pts: [(x - X0, y - Y0) for x, y in pts]
        iw = max(4, int(5.5 * min(1.8, s ** .6)))
        for k, ((x0, x1, y0, y1), sh) in reversed(list(enumerate(zip(slabs, shapes)))):     # top slab first (behind)
            x0, x1, y0, y1 = x0 * s, x1 * s, y0 * s, y1 * s
            d.polygon(P_(sh), fill=rgb(cols[1]))
            # lit top surface: the band between the top edge and a line ~22% down
            topn = sh[:7]
            topb = [(x, y + (y1 - y0) * .26 + rng.uniform(-3, 3) * s) for x, y in topn]
            d.polygon(P_(topn + topb[::-1]), fill=rgb(cols[0]))
            # right shade side and the undercut shadow along the bottom
            d.polygon(P_([sh[5], sh[6], sh[7], sh[8], (x1 - 70 * s, y1), (x1 - 60 * s, y0 + (y1 - y0) * .3)]), fill=rgb(cols[2]))
            d.polygon(P_([(x0 + 10 * s, y1 - 16 * s), (x1 - 10 * s, y1 - 16 * s), sh[8], sh[9]]), fill=lerp(rgb(cols[2]), rgb(cols[3]), .4))
            # vertical joints and fine bedding lines
            for _ in range(3):
                jx = rng.uniform(x0 + 50 * s, x1 - 60 * s)
                if k == 0 and abs(jx) < 110 * s: continue
                jy0 = y0 + (y1 - y0) * .26
                d.line(P_([(jx, jy0), (jx + rng.uniform(-8, 8) * s, (jy0 + y1) / 2), (jx + rng.uniform(-10, 10) * s, y1 - 18 * s)]),
                       fill=rgb(cols[3]), width=max(2, int(3.5 * s ** .5)), joint='curve')
            for j in range(2):
                yy = y0 + (y1 - y0) * (.45 + .22 * j)
                xa, xb = x0 + rng.uniform(20, 90) * s, x1 - rng.uniform(70, 140) * s
                seg_ = [(x, yy + 3 * s * math.sin(x / (40 * s) + j)) for x in np.linspace(xa, xb, 14)]
                seg_ = [p for p in seg_ if not (k == 0 and abs(p[0]) < 95 * s)]
                if len(seg_) > 1: d.line(P_(seg_), fill=lerp(rgb(cols[1]), rgb(cols[2]), .55), width=max(2, int(2.5 * s ** .5)))
            for _ in range(9):                                        # lichen
                lx, ly = rng.uniform(x0 + 20 * s, x1 - 30 * s), rng.uniform(y0 + 4 * s, y1 - 20 * s)
                if k == 0 and abs(lx) < 100 * s and abs(ly) < 70 * s: continue
                r = rng.uniform(5, 13) * s
                d.ellipse(P_([(lx - r, ly - r * .6), (lx + r, ly + r * .6)]), fill=(196, 192, 120) if rng.random() < .6 else (222, 168, 96))
            d.line(P_(sh + sh[:1]), fill=INK, width=iw, joint='curve')
        # the hole: recessed rim, lit lower lip, near-black depth, inked edge
        hw, hh = 36 * s * hole_k, 28 * s * hole_k
        hp = [(math.cos(a) * hw * (1 + .1 * math.sin(3 * a + seed)), math.sin(a) * hh * (1 + .12 * math.cos(2 * a)) + 10 * s)
              for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
        d.polygon(P_([(x * 1.5, y * 1.55 + 2 * s) for x, y in hp]), fill=rgb(cols[2]))
        d.polygon(P_([(x * 1.5, y * 1.55 + 2 * s) for x, y in hp if y > 10 * s] + [(x * 1.04, y * 1.04) for x, y in hp if y > 10 * s][::-1]),
                  fill=lerp(rgb(cols[0]), rgb(cols[1]), .3))
        d.polygon(P_(hp), fill=(18, 14, 26))
        d.polygon(P_([(x * .6, y * .5 + 8 * s) for x, y in hp]), fill=(4, 2, 10))
        d.line(P_(hp + hp[:1]), fill=INK, width=max(3, int(iw * .8)), joint='curve')
        return lay, (-X0, -Y0 - 10 * s)
    return cached(('outcrop2', round(s, 3), seed, cols, hole_k), build)


def outcrop(img, hx, hy, s=1.0, seed=3, cols=ROCK, breath_glow=0.0, t=0.0, tufts=True, src=None, gold=GOLD):
    """Draw the outcrop with its hole at (hx, hy). breath_glow > 0: a cold blue glow pulses inside the hole.
    Grass tufts sit on the slab tops and along the base (they sway with t and the breath)."""
    lay, (ox, oy) = outcrop_layer(s, seed, cols)
    img.alpha_composite(lay, (int(hx - ox), int(hy - oy)))
    if breath_glow > 0:
        m = mask(); ImageDraw.Draw(m).ellipse([hx - 30 * s, hy - 22 * s, hx + 30 * s, hy + 22 * s], fill=255)
        glow(img, m, BREATH_GLOW, breath_glow * (.6 + .15 * math.sin(t * 5)), blur=max(8, int(22 * s)), add=True)
    if tufts:
        for k, (x0, x1, y) in enumerate(((-140, 110, -186), (-240, 220, -121), (-320, 300, -36))):
            grass(img, t, (hx + x0 * s, hy + y * s, hx + x1 * s, hy + (y + 3) * s), 5 + 3 * k, 18 * s, 34 * s, cols=gold,
                  seed=seed + 60 + k, src=src, w0=4 * s ** .5, clump=(4, 7), spread=.7, ink=INK)
    return (hx, hy)


# ---------------------------------------------------------------- the breath
def _ribbons(seed, n, spread, Lr, Ar, swirl=0.0):
    """Ribbon params. swirl != 0 (the IN breath): every ribbon bends the same way, so together they form spiral arms
    winding into the hole (a vortex), with no curled tips."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        f = (i + .5) / n - .5
        if swirl:
            out.append(dict(off=f * spread + rng.uniform(-.05, .05), L=rng.uniform(*Lr), A=rng.uniform(*Ar) * .5, k=rng.uniform(.5, .9),
                            ph=rng.uniform(0, 6.3), v=rng.uniform(.8, 1.2), w=rng.uniform(.8, 1.15), bend=swirl * rng.uniform(.85, 1.15),
                            curl=0.0, dashes=int(rng.integers(1, 3)), dph=rng.uniform(0, 1), ln=rng.uniform(.55, .75)))
            continue
        out.append(dict(off=f * spread + rng.uniform(-.06, .06), L=rng.uniform(*Lr), A=rng.uniform(*Ar), k=rng.uniform(.6, 1.2),
                        ph=rng.uniform(0, 6.3), v=rng.uniform(.8, 1.2), w=rng.uniform(.7, 1.2), bend=rng.uniform(-.5, .5) + f * .6,
                        curl=(1 if f > 0 else -1) * rng.uniform(4.0, 7.0) * (rng.random() < .8), dashes=int(rng.integers(1, 3)),
                        dph=rng.uniform(0, 1), ln=rng.uniform(.6, .85)))
    return out


def _spine(r, ang, sign, N=64):
    """Base centreline of a ribbon (unit length): integrated heading with a gentle bend and a curled tip."""
    th = ang + r['off'] * (1.0 if sign > 0 else .85)
    x = y = 0.0; pts = [(0.0, 0.0)]; hs = []
    for i in range(1, N):
        s = i / (N - 1)
        a = th + r['bend'] * s + r['curl'] * max(0.0, s - .55) ** 2 * 8.0
        hs.append(a)
        step = (1 - .6 * max(0.0, s - .55) / .45) / (N - 1)          # steps shrink into the curl (a spiral)
        x += math.cos(a) * step; y += math.sin(a) * step; pts.append((x, y))
    hs.insert(0, hs[0])
    return np.array(pts), np.array(hs)


_spines = {}
def breath_point(r, hx, hy, ang, s, t, sign, scale):
    key = (r['key'], round(ang, 4), sign)
    if key not in _spines:
        if len(_spines) > 2000: _spines.clear()
        _spines[key] = _spine(r, ang, sign)
    sp, hs = _spines[key]
    i = s * (len(sp) - 1); i0 = int(min(len(sp) - 2, max(0, math.floor(i)))); f = i - i0
    x = sp[i0][0] + (sp[i0 + 1][0] - sp[i0][0]) * f; y = sp[i0][1] + (sp[i0 + 1][1] - sp[i0][1]) * f
    a = hs[i0]
    off = r['A'] * math.sin(2 * math.pi * r['k'] * s - sign * 4.0 * t * r['v'] + r['ph']) * s ** .9 * (1 - .7 * max(0, s - .62) / .38)
    L = r['L'] * scale
    return hx + x * L - math.sin(a) * off * scale, hy + y * L + math.cos(a) * off * scale


def breath(img, t, hx, hy, ang=-2.2, sign=1, k=1.0, scale=1.0, n=9, spread=1.3, seed=7, Lr=(520, 900), Ar=(30, 70),
           width=26, speed=.34, particles=40, bits=True, glow_a=.55, clip=None, edge=True, body=BREATH, plume=True, arrows=True, swirl=None):
    """The hole breathing. sign +1 = OUT: long ribbons stream away from the hole, widen, curl and fade; sign -1 = IN:
    they come from far away, narrow and vanish into the hole. ang = main direction (rad, screen: -pi/2 = up).
    k = strength (0 calm, 1 normal, 1.6 a hard gust): alpha, speed and width."""
    if k <= .01: return
    n = max(5, int(round(n * .72)))                     # fewer, cleaner streams
    if sign < 0:
        return breath_in(img, t, hx, hy, ang=ang, k=k, scale=scale, n=n, spread=spread, seed=seed, Lr=Lr, width=width, speed=speed,
                         particles=particles, glow_a=glow_a, clip=clip, swirl=.55 if swirl is None else swirl)
    if swirl is None: swirl = 0.0
    rs = cached(('ribbons', seed, n, spread, Lr, Ar, swirl), lambda: _ribbons(seed, n, spread, Lr, Ar, swirl))
    for i, r in enumerate(rs): r['key'] = (seed, n, spread, Lr, Ar, swirl, i)
    if plume and sign > 0:                              # a faint cone of cold air: the breath as a whole
        pm = mask(); dp = ImageDraw.Draw(pm)
        Lp = sum(Lr) / 2 * scale * .9
        a0, a1 = ang - spread * .45, ang + spread * .45
        dp.polygon([(hx, hy), (hx + math.cos(a0) * Lp, hy + math.sin(a0) * Lp), (hx + math.cos(ang) * Lp * 1.08, hy + math.sin(ang) * Lp * 1.08),
                    (hx + math.cos(a1) * Lp, hy + math.sin(a1) * Lp)], fill=int(90 * min(1.2, k)))
        if clip is not None: pm = ImageChops.multiply(pm, clip)
        glow(img, pm, (200, 232, 255), .55, blur=int(70 * max(.4, scale)), add=True)
    # the mouth: puffs of cold air bursting out (or swirling in) right at the hole
    mm = mask(); dm = ImageDraw.Draw(mm); rng = np.random.default_rng(seed + 50)
    for i in range(14):
        ph = rng.uniform(0, 1); a = ang + rng.uniform(-.5, .5) * spread
        q = (ph + sign * t * (1.1 + .5 * min(1.5, k))) % 1.0
        dist = q * 170 * scale; rr = (14 + 40 * q) * scale if sign > 0 else (12 + 34 * q) * scale
        al = math.sin(math.pi * q) * min(1.0, k)
        x, y = hx + math.cos(a) * dist, hy + math.sin(a) * dist
        dm.ellipse([x - rr, y - rr * .8, x + rr, y + rr * .8], fill=int(200 * al))
    if clip is not None: mm = ImageChops.multiply(mm, clip)
    mm = mm.filter(ImageFilter.GaussianBlur(max(2, 6 * scale)))
    fill_mask(img, mm, (236, 248, 255), .85)
    radial(img, hx, hy, 150 * scale, (210, 236, 255), .5 * min(1.2, k))
    if sign < 0:                                        # suction: rings tighten into the hole
        lay = layer(); dl = ImageDraw.Draw(lay)
        for i in range(3):
            q = (i / 3 - t * .9) % 1.0
            rr = (40 + 200 * q) * scale; al = int(200 * math.sin(math.pi * q) * min(1, k))
            a0 = math.degrees(t * 2.5) + i * 120
            dl.arc([hx - rr, hy - rr * .7, hx + rr, hy + rr * .7], a0, a0 + 230, fill=rgb(BREATH_EDGE) + (al,), width=max(4, int(12 * scale)))
            dl.arc([hx - rr, hy - rr * .7, hx + rr, hy + rr * .7], a0, a0 + 230, fill=rgb(BREATH) + (al,), width=max(2, int(6 * scale)))
        if clip is not None: lay.putalpha(ImageChops.multiply(lay.split()[3], clip))
        img.alpha_composite(lay)
    m = mask(); d = ImageDraw.Draw(m)
    core = mask(); dc = ImageDraw.Draw(core)
    for i, r in enumerate(rs):
        for j in range(r['dashes']):
            c = (r['dph'] + j / r['dashes'] + sign * speed * (.55 + .45 * min(1.5, k)) * r['v'] * t) % 1.0
            ln = r['ln']
            s0, s1 = max(0.0, c - ln / 2), min(1.0, c + ln / 2)
            if s1 - s0 < .03: continue
            if sign > 0:
                env = min(1.0, c / .18) * (1 - max(0.0, (c - .62) / .38)) ** 1.1
            else:
                env = min(1.0, (1 - c) / .22) * min(1.0, c / .14)
            env = max(0.0, env) * min(1.0, k)
            if env < .03: continue
            ss = np.linspace(s0, s1, 22)
            ptsL, ptsR, mid = [], [], []
            for q in ss:
                x, y = breath_point(r, hx, hy, ang, q, t, sign, scale)
                x2, y2 = breath_point(r, hx, hy, ang, min(1.0, q + .008), t, sign, scale)
                if q >= .992: x2, y2 = 2 * x - breath_point(r, hx, hy, ang, q - .008, t, sign, scale)[0], 2 * y - breath_point(r, hx, hy, ang, q - .008, t, sign, scale)[1]
                tx, ty = x2 - x, y2 - y; tl = math.hypot(tx, ty) + 1e-6
                nx, ny = -ty / tl, tx / tl
                v = (q - s0) / max(1e-3, s1 - s0)
                taper = (math.sin(math.pi * v) ** .45)
                grow = (.5 + .7 * min(q, .6)) * (1 - .5 * max(0, q - .6) / .4) if sign > 0 else (.3 + .9 * q)
                hw = width * scale * r['w'] * taper * grow * (.75 + .25 * min(1.5, k))
                ptsL.append((x + nx * hw, y + ny * hw)); ptsR.append((x - nx * hw, y - ny * hw)); mid.append((x + nx * hw * .45, y + ny * hw * .45))
            d.polygon(ptsL + ptsR[::-1], fill=int(255 * env))
            dc.line(mid[4:-5], fill=int(255 * env), width=max(2, int(width * scale * .14)), joint='curve')
            if arrows and env > .25 and i % 2 == 0:                    # an arrowhead on the leading end: the flow direction reads in a still
                if sign > 0: qa, qb = s1 - .035, s1
                else: qa, qb = s0 + .035, s0
                if (sign > 0 and s1 < .97) or (sign < 0 and s0 > .03) or True:
                    ax_, ay_ = breath_point(r, hx, hy, ang, qa, t, sign, scale); bx_, by_ = breath_point(r, hx, hy, ang, qb, t, sign, scale)
                    aa = math.atan2(by_ - ay_, bx_ - ax_); hs_ = width * scale * 1.25 * (.8 + .5 * (qb if sign > 0 else 1 - qb))
                    tip = (bx_ + math.cos(aa) * hs_ * .9, by_ + math.sin(aa) * hs_ * .9)
                    d.polygon([tip, (bx_ + math.cos(aa + 2.3) * hs_, by_ + math.sin(aa + 2.3) * hs_),
                               (bx_ + math.cos(aa - 2.3) * hs_, by_ + math.sin(aa - 2.3) * hs_)], fill=int(255 * env))
    if clip is not None:
        m = ImageChops.multiply(m, clip); core = ImageChops.multiply(core, clip)
    glow(img, m, BREATH_GLOW, glow_a * min(1.2, k), blur=int(24 * max(.5, scale)), add=True)
    if edge:
        fill_mask(img, m.filter(ImageFilter.MaxFilter(5)), BREATH_EDGE, .8)
    fill_mask(img, m, body, .94)
    fill_mask(img, core, (255, 255, 255), .95)
    if particles:
        breath_particles(img, t, hx, hy, ang, sign, k, scale, rs, particles, seed, bits, speed, clip)


def breath_in(img, t, hx, hy, ang=-math.pi / 2, k=1.0, scale=1.0, n=10, spread=2.4, seed=7, Lr=(600, 900), width=24,
              speed=.34, particles=30, glow_a=.55, clip=None, swirl=.55):
    """The hole breathing IN: a funnel. Streams start far away on a wide arc (spread rad around ang), bend a little
    (swirl) and narrow as they converge on the hole; each dash has a big arrowhead pointing at the hole; a ring of
    chevrons around the mouth marches inward. Reads as suction in a still."""
    rng = np.random.default_rng(seed)
    spread = max(spread, 2.2)
    paths = []
    for i in range(n):
        f = (i + .5) / n - .5
        a = ang + f * spread + rng.uniform(-.05, .05)
        R = rng.uniform(*Lr) * scale
        sx, sy = hx + math.cos(a) * R, hy + math.sin(a) * R
        # control point: off to one side (swirl), at mid distance
        ca = a + swirl * (1 if rng.random() < .85 else -1)
        cx, cy = hx + math.cos(ca) * R * .55, hy + math.sin(ca) * R * .55
        pts = [((1 - q) ** 2 * sx + 2 * (1 - q) * q * cx + q * q * hx, (1 - q) ** 2 * sy + 2 * (1 - q) * q * cy + q * q * hy)
               for q in np.linspace(0, 1, 40)]                       # q = 0 far -> 1 at the hole
        paths.append((pts, rng.uniform(.8, 1.2), rng.uniform(0, 1), int(rng.integers(1, 3)), rng.uniform(.35, .5)))
    m = mask(); d = ImageDraw.Draw(m); core = mask(); dc = ImageDraw.Draw(core)
    def P_(pts, q):
        i = q * (len(pts) - 1); i0 = int(min(len(pts) - 2, i)); f = i - i0
        return (pts[i0][0] + (pts[i0 + 1][0] - pts[i0][0]) * f, pts[i0][1] + (pts[i0 + 1][1] - pts[i0][1]) * f)
    for pts, w, ph, nd, ln in paths:
        for j in range(nd):
            c = (ph + j / nd + speed * (.6 + .4 * min(1.5, k)) * t) % 1.0      # 0 far -> 1 hole
            q0, q1 = max(0.0, c - ln), min(.9, c)
            if q1 - q0 < .04: continue
            env = min(1.0, c / .25) * min(1.0, (1 - c) / .15 + .2) * min(1.0, k)
            if env < .05: continue
            L, R_, mid = [], [], []
            qs = np.linspace(q0, q1, 18)
            for q in qs:
                x, y = P_(pts, q); x2, y2 = P_(pts, min(1, q + .01))
                tx, ty = x2 - x, y2 - y; tl = math.hypot(tx, ty) + 1e-6; nx, ny = -ty / tl, tx / tl
                v = (q - q0) / max(1e-3, q1 - q0)
                hw = width * scale * w * (1.25 - .9 * q) * (math.sin(math.pi * min(1, v * 1.1)) ** .4 if v < .9 else 1) * (.75 + .25 * min(1.5, k))
                L.append((x + nx * hw, y + ny * hw)); R_.append((x - nx * hw, y - ny * hw)); mid.append((x + nx * hw * .4, y + ny * hw * .4))
            d.polygon(L + R_[::-1], fill=int(255 * env))
            dc.line(mid[2:-3], fill=int(255 * env), width=max(2, int(width * scale * .14)))
            # arrowhead at the leading (hole-side) end
            x, y = P_(pts, q1); xa, ya = P_(pts, max(0, q1 - .03))
            aa = math.atan2(y - ya, x - xa); hs_ = width * scale * w * (1.9 - .9 * q1) * (.85 + .2 * min(1.5, k))
            tip = (x + math.cos(aa) * hs_ * 1.1, y + math.sin(aa) * hs_ * 1.1)
            d.polygon([tip, (x + math.cos(aa + 2.2) * hs_, y + math.sin(aa + 2.2) * hs_), (x + math.cos(aa - 2.2) * hs_, y + math.sin(aa - 2.2) * hs_)],
                      fill=int(255 * env))
    if clip is not None:
        m = ImageChops.multiply(m, clip); core = ImageChops.multiply(core, clip)
    glow(img, m, BREATH_GLOW, glow_a * min(1.2, k), blur=int(24 * max(.5, scale)), add=True)
    fill_mask(img, m.filter(ImageFilter.MaxFilter(5)), BREATH_EDGE, .8)
    fill_mask(img, m, BREATH, .94)
    fill_mask(img, core, (255, 255, 255), .95)
    # chevrons around the mouth, marching inward
    lay = layer(); dl = ImageDraw.Draw(lay)
    for i in range(7):
        a = ang + (i / 6 - .5) * 3.4
        for j in range(2):
            q = (j / 2 + t * 1.1) % 1.0
            r = (190 - 140 * q) * scale; al = int(255 * math.sin(math.pi * q) * min(1, k))
            x, y = hx + math.cos(a) * r, hy + math.sin(a) * r * .85
            ai = a + math.pi; sz = 30 * scale * (1.2 - .5 * q)
            pts = [(x + math.cos(ai + 2.4) * sz, y + math.sin(ai + 2.4) * sz), (x + math.cos(ai) * sz * .5, y + math.sin(ai) * sz * .5),
                   (x + math.cos(ai - 2.4) * sz, y + math.sin(ai - 2.4) * sz)]
            dl.line(pts, fill=rgb(BREATH_EDGE) + (al,), width=max(6, int(16 * scale)), joint='curve')
            dl.line(pts, fill=(255, 255, 255, al), width=max(3, int(8 * scale)), joint='curve')
    if clip is not None: lay.putalpha(ImageChops.multiply(lay.split()[3], clip))
    img.alpha_composite(lay)
    radial(img, hx, hy, 120 * scale, (190, 225, 255), .35 * min(1.2, k))
    if particles:                                       # grass bits and dust drawn in along the streams
        lay = layer(); dl = ImageDraw.Draw(lay)
        for i in range(particles):
            pts = paths[i % len(paths)][0]; ph = rng.uniform(0, 1)
            q = (ph + speed * 1.6 * (.6 + .4 * min(1.5, k)) * t) % 1.0
            x, y = P_(pts, q * .95); x += rng.uniform(-30, 30) * scale * (1 - q); y += rng.uniform(-30, 30) * scale * (1 - q)
            env = min(1, q / .1) * min(1, (1 - q) / .1) * min(1, k)
            if i % 3 == 1:
                Lb = rng.uniform(16, 30) * scale; a = t * 9 + i
                dx, dy = math.cos(a) * Lb / 2, math.sin(a) * Lb / 2
                dl.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(70, 46, 30, int(255 * env)), width=max(3, int(8 * scale)))
                dl.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(248, 206, 112, int(255 * env)), width=max(2, int(4.5 * scale)))
            else:
                rr = rng.uniform(3, 7) * scale
                dl.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(240, 250, 255, int(220 * env)))
        if clip is not None: lay.putalpha(ImageChops.multiply(lay.split()[3], clip))
        img.alpha_composite(lay)


def breath_particles(img, t, hx, hy, ang, sign, k, scale, rs, n, seed, bits, speed, clip=None):
    rng = np.random.default_rng(seed + 100)
    lay = layer(); d = ImageDraw.Draw(lay)
    for i in range(n):
        r = rs[i % len(rs)]
        ph = rng.uniform(0, 1); v = rng.uniform(.8, 1.5) * speed * (.6 + .5 * min(1.5, k)) * 1.3
        q = (ph + sign * v * t) % 1.0
        x, y = breath_point(r, hx, hy, ang, q * .8, t * 1.1, sign, scale)
        jx, jy = rng.uniform(-40, 40), rng.uniform(-40, 40)
        x += jx * scale * q; y += jy * scale * q
        env = min(1, q / .08) * (1 - q) ** .6 * min(1, k)
        if env < .05: continue
        kind = i % 4 if bits else 0
        if kind == 1:                                   # grass bit: a golden sliver spinning
            L = rng.uniform(18, 36) * scale; a = t * rng.uniform(6, 14) + i
            dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
            d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(70, 46, 30, int(255 * env)), width=max(3, int(8 * scale)))
            d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(248, 206, 112, int(255 * env)), width=max(2, int(4.5 * scale)))
        elif kind == 2:                                 # leaf flake
            rr = rng.uniform(7, 13) * scale; a = t * 5 + i
            pts = [(x + math.cos(a) * rr, y + math.sin(a) * rr * .5), (x - math.sin(a) * rr * .4, y + math.cos(a) * rr * .4),
                   (x - math.cos(a) * rr, y - math.sin(a) * rr * .5), (x + math.sin(a) * rr * .4, y - math.cos(a) * rr * .4)]
            d.polygon(pts, fill=(222, 156, 72, int(240 * env)), outline=(60, 40, 30, int(240 * env)))
        else:                                           # dust / breath mote
            rr = rng.uniform(3, 7) * scale
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(240, 250, 255, int(220 * env)))
    if clip is not None:
        lay.putalpha(ImageChops.multiply(lay.split()[3], clip))
    img.alpha_composite(lay)


# ---------------------------------------------------------------- props
def hat_layer(col, s=1.0, tilt=0.0):
    """A cowboy hat on its own (same shape as stickman's 'cowboy'), centre = the crown base. Cached."""
    def build():
        S = 2; w, h = int(360 * s), int(200 * s)
        lay = layer(w * S, h * S); d = ImageDraw.Draw(lay)
        cx, cy = w / 2, h * .62
        def P(pts): return [((cx + x * s) * S, (cy + y * s) * S) for x, y in pts]
        C = rgb(col); Cd = lerp(C, INK, .3); Cl = lerp(C, (255, 255, 255), .2)
        crown = [(-60, 4), (-54, -58), (-22, -70), (0, -58), (22, -70), (54, -58), (60, 4)]
        band = [(-59, -16), (59, -16), (60, 0), (-60, 0)]
        top = [(x, 16 - 34 * (x / 150) ** 2 - 12) for x in range(-150, 151, 10)]
        bot = [(x, 24 - 34 * (x / 150) ** 2) for x in range(150, -151, -10)]
        brim = top + bot
        for pts, fill in ((crown, C), (band, Cd), (brim, C)):
            q = P(pts); d.polygon(q, fill=fill); d.line(q + q[:1], fill=INK, width=int(4 * S * max(.7, s)), joint='curve')
        d.line(P([(-40, -50), (-30, -6)]), fill=Cl, width=int(8 * S * s))
        lay = lay.resize((w, h), Image.LANCZOS)
        return lay
    return cached(('hat', col, round(s, 2)), build)


def put_hat(img, col, x, y, s, angle=0.0, alpha=1.0):
    import anim
    lay = hat_layer(col, round(s, 2))
    anim.scaled_paste(img, lay, x, y, 1.0, angle=angle, alpha=alpha)


def paper(img, x, y, w, ang=0.0, t=0.0, alpha=1.0, lines=True):
    """A sheet of letter paper (8.5 x 11 in) centred at (x, y), w px wide, tilted ang deg; flutters a little."""
    import anim
    h = w * 11 / 8.5
    lay = layer(int(w + 40), int(h + 40)); d = ImageDraw.Draw(lay)
    d.rectangle([26, 28, w + 26, h + 28], fill=(30, 26, 40, 110))
    d.rectangle([20, 20, w + 20, h + 20], fill=(252, 250, 244), outline=INK, width=5)
    d.polygon([(w + 20 - w * .16, 20), (w + 20, 20 + w * .16), (w + 20 - w * .16, 20 + w * .16)], fill=(220, 216, 208), outline=INK)
    if lines:
        for i in range(7):
            yy = 20 + h * (.18 + i * .1); d.line([(20 + w * .12, yy), (20 + w * (.88 - .2 * (i == 6))), yy], fill=(170, 190, 220), width=3)
    anim.scaled_paste(img, lay, x, y, 1.0, angle=ang + 1.2 * math.sin(t * 3.1), alpha=alpha)


def barometer(img, x, y, r, needle, t, label_txt=True):
    """A round barometer dial: needle 0 = STORM (left) .. 1 = FAIR (right). Moves: needle (with a small jitter)."""
    d = ImageDraw.Draw(img)
    m = mask(); ImageDraw.Draw(m).ellipse([x - r, y - r, x + r, y + r], fill=255)
    glow(img, m, (255, 230, 170), .35, blur=30)
    d.ellipse([x - r + 8, y - r + 14, x + r + 8, y + r + 14], fill=INK)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(176, 130, 66), outline=INK, width=8)
    d.ellipse([x - r * .86, y - r * .86, x + r * .86, y + r * .86], fill=(250, 244, 226), outline=INK, width=5)
    for i in range(11):
        a = math.radians(210 - i * 24)
        d.line([(x + math.cos(a) * r * .7, y - math.sin(a) * r * .7), (x + math.cos(a) * r * .8, y - math.sin(a) * r * .8)],
               fill=INK, width=5 if i % 5 == 0 else 3)
    d.arc([x - r * .62, y - r * .62, x + r * .62, y + r * .62], 150, 210, fill=(110, 90, 200), width=14)
    d.arc([x - r * .62, y - r * .62, x + r * .62, y + r * .62], 330, 30, fill=(250, 180, 50), width=14)
    if label_txt:
        f = kit.font(int(r * .16))
        d.text((x - r * .36, y + r * .5), 'STORM', font=f, fill=(90, 70, 170), anchor='mm')
        d.text((x + r * .36, y + r * .5), 'FAIR', font=f, fill=(200, 120, 20), anchor='mm')
    a = math.radians(210 - 240 * (needle + .01 * math.sin(t * 13)))
    tip = (x + math.cos(a) * r * .74, y - math.sin(a) * r * .74)
    tail = (x - math.cos(a) * r * .18, y + math.sin(a) * r * .18)
    d.line([tail, tip], fill=INK, width=16); d.line([tail, tip], fill=(210, 50, 44), width=9)
    d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=INK)
    d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(230, 200, 120))


# ---------------------------------------------------------------- underground
STRATA = ((150, 112, 84), (128, 92, 72), (112, 80, 66), (92, 66, 58), (72, 52, 50), (54, 40, 44))


def earth_section(img, y_top, y_bot=H, cols=STRATA, seed=4, edge_fn=None, x0=-20, x1=W + 20, ink=True, alpha=1.0):
    """Layered strata from a ground line (edge_fn(x) or flat y_top) down to y_bot, with wavy boundaries,
    pebbles and fine texture. Static (cached by args)."""
    def build():
        lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(seed)
        xs = np.arange(x0, x1 + 1, 12)
        top = np.array([edge_fn(x) if edge_fn else y_top for x in xs])
        n = len(cols); span = y_bot - top.min()
        prev = top
        for i, c in enumerate(cols):
            nxt = top + span * (i + 1) / n + 24 * np.sin(xs / (180 + 40 * i) + i * 1.7) if i < n - 1 else np.full_like(top, y_bot + 40)
            poly = list(zip(xs, prev)) + list(zip(xs[::-1], nxt[::-1]))
            d.polygon(poly, fill=rgb(c))
            d.line(list(zip(xs, nxt)), fill=lerp(rgb(c), INK, .35), width=4)
            prev = nxt
        for _ in range(140):
            x = rng.uniform(x0, x1); yt = float(np.interp(x, xs, top)); y = rng.uniform(yt + 30, y_bot)
            r = rng.uniform(4, 13); c = rng.integers(0, n)
            d.ellipse([x - r, y - r * .7, x + r, y + r * .7], fill=lerp(rgb(cols[c]), (230, 210, 180), .25), outline=lerp(rgb(cols[c]), INK, .5), width=2)
        if ink: d.line(list(zip(xs, top)), fill=INK, width=7)
        return lay
    lay = cached(('earth', y_top, y_bot, cols, seed, edge_fn is not None and id(edge_fn), x0, x1, ink), build)
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.split()[3].point(lambda q: int(q * alpha)))
    img.alpha_composite(lay)


def maze_net(seed, box, n_nodes=46, extra=26):
    """A cave maze: random nodes in box joined by a tree + extra loops, with meandering tunnel polylines and
    varying widths (Wind Cave is a 3-D boxwork maze; drawn as a dense 2-D network). Cached."""
    def build():
        rng = np.random.default_rng(seed); x0, y0, x1, y1 = box
        pts = []
        while len(pts) < n_nodes:
            p = (rng.uniform(x0, x1), rng.uniform(y0, y1))
            if all(math.dist(p, q) > (x1 - x0) / 9 for q in pts): pts.append(p)
        edges = set()
        # minimum spanning tree (Prim)
        inn = {0}
        while len(inn) < len(pts):
            best = None
            for i in inn:
                for j in range(len(pts)):
                    if j in inn: continue
                    dd = math.dist(pts[i], pts[j])
                    if best is None or dd < best[0]: best = (dd, i, j)
            edges.add((best[1], best[2])); inn.add(best[2])
        cand = []
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dd = math.dist(pts[i], pts[j])
                if dd < (x1 - x0) / 3.2 and (i, j) not in edges and (j, i) not in edges: cand.append((dd, i, j))
        cand.sort()
        for dd, i, j in cand[:extra]: edges.add((i, j))
        tunnels = []
        for i, j in edges:
            a, b = pts[i], pts[j]; L = math.dist(a, b); nseg = max(3, int(L / 40))
            nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
            ph = rng.uniform(0, 6); amp = rng.uniform(8, 26)
            poly = [(a[0] + (b[0] - a[0]) * q + nx * amp * math.sin(q * math.pi * 2 + ph) * math.sin(q * math.pi),
                     a[1] + (b[1] - a[1]) * q + ny * amp * math.sin(q * math.pi * 2 + ph) * math.sin(q * math.pi))
                    for q in np.linspace(0, 1, nseg)]
            tunnels.append((poly, rng.uniform(26, 50), (i, j)))
        return pts, tunnels
    return cached(('maze', seed, box, n_nodes, extra), build)


def draw_maze(img, net, reveal=1.0, order_from=None, wall=(20, 30, 38), air=(52, 88, 100), rim=(110, 160, 160), glow_col=None,
              glow_a=0.0, scale=1.0, ox=0.0, oy=0.0, ink=True, frac=None):
    """Draw tunnels (dark rock outline, open passage, lit rim). reveal 0..1 grows the network outward from
    order_from (a point) by distance. frac(i) -> 0..1 for per-tunnel partial draw."""
    pts, tunnels = net
    T = lambda p: (ox + p[0] * scale, oy + p[1] * scale)
    if order_from is not None:
        dmax = max(math.dist(order_from, p) for p in pts)
    m = mask(); d = ImageDraw.Draw(m)
    mi = mask(); di = ImageDraw.Draw(mi)
    for poly, w, (i, j) in tunnels:
        f = 1.0
        if order_from is not None:
            da = math.dist(order_from, pts[i]) / dmax; db = math.dist(order_from, pts[j]) / dmax
            f = max(0.0, min(1.0, (reveal * 1.25 - min(da, db)) / max(.05, abs(db - da) + .05)))
            if da > db: poly = poly[::-1]
        if f <= 0: continue
        n = max(2, int(len(poly) * f)); pp = [T(p) for p in poly[:n]]
        d.line(pp, fill=255, width=int((w + 16) * scale), joint='curve')
        di.line(pp, fill=255, width=int(w * scale), joint='curve')
        for p in (pp[0], pp[-1]):
            r = (w + 16) * scale / 2; d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)
            r2 = w * scale / 2; di.ellipse([p[0] - r2, p[1] - r2, p[0] + r2, p[1] + r2], fill=255)
    if ink: fill_mask(img, m, wall)
    fill_mask(img, mi, air)
    # lit upper rim inside each passage (offset mask)
    sh = ImageChops.subtract(mi, ImageChops.offset(mi, 0, int(8 * scale)))
    fill_mask(img, sh, rim, .8)
    if glow_col and glow_a > 0:
        glow(img, mi, glow_col, glow_a, blur=18, add=True)
    return mi


def lamp_light(img, x, y, ang, t, reach=900, spread=.42, col=(255, 214, 140), a=.75):
    """A caver's helmet beam: a soft warm cone from (x, y) toward ang (rad) + a hot spot. Moves: flickers 4%."""
    m = mask(); d = ImageDraw.Draw(m)
    p1 = (x + math.cos(ang - spread) * reach, y + math.sin(ang - spread) * reach)
    p2 = (x + math.cos(ang + spread) * reach, y + math.sin(ang + spread) * reach)
    d.polygon([(x, y), p1, p2], fill=200)
    glow(img, m, col, a * (.96 + .04 * math.sin(t * 17)), blur=40, add=True)
    radial(img, x + math.cos(ang) * reach * .45, y + math.sin(ang) * reach * .45, reach * .45, col, .35 * a)
    radial(img, x, y, 90, (255, 246, 210), .9)


def boxwork(seed=1, cell=46, col=(150, 190, 180)):
    """Wind Cave's boxwork: a thin honeycomb of calcite fins on the rock (cached RGBA layer, low alpha)."""
    def build():
        rng = np.random.default_rng(seed); lay = layer(); d = ImageDraw.Draw(lay)
        for gy in range(0, H + cell, cell):
            for gx in range(0, W + cell, cell):
                x, y = gx + rng.uniform(-12, 12), gy + rng.uniform(-12, 12)
                if rng.random() < .8: d.line([(x, y), (x + cell + rng.uniform(-10, 10), y + rng.uniform(-10, 10))], fill=rgb(col) + (46,), width=3)
                if rng.random() < .8: d.line([(x, y), (x + rng.uniform(-10, 10), y + cell + rng.uniform(-10, 10))], fill=rgb(col) + (46,), width=3)
        return lay
    return cached(('boxwork', seed, cell, col), build)


def air_blanket(img, t, y_top, y_bot, k=1.0, n=6, col=(150, 205, 255), arrows=1.0, xs=(150, 400, 680, 930), arrow_col=(230, 244, 255)):
    """The atmosphere as a heavy blanket of air over the land: wavy translucent bands, denser toward the ground,
    full of air molecules, with big arrows pressing down. k = thickness (1 fair weather, ~.3 under a storm).
    Moves: the bands ripple, the molecules jiggle, the arrows march down."""
    import jungle as J
    top = y_bot - (y_bot - y_top) * (.25 + .75 * k)
    lay = layer(); d = ImageDraw.Draw(lay)
    for i in range(n):
        f0 = i / n; f1 = (i + 1) / n
        ya = top + (y_bot - top) * f0; yb = top + (y_bot - top) * f1 + 4
        xs_ = np.arange(-20, W + 21, 30)
        up = [(x, ya + 10 * math.sin(x / 120 + t * 1.3 + i)) for x in xs_]
        dens = (i + 1) / n
        a = int((40 + 110 * dens) * (.55 + .45 * k))
        d.polygon(up + [(W + 20, yb), (-20, yb)], fill=lerp(col, (255, 255, 255), .35 * (1 - dens)) + (a,))
        d.line(up, fill=(255, 255, 255, min(255, a + 70)), width=4)
        rng = np.random.default_rng(i + 7)
        for q in range(int(10 + 34 * dens * k)):
            x = rng.uniform(0, W); y = rng.uniform(ya + 14, yb - 10) + 5 * math.sin(t * 4 + q)
            x += 5 * math.cos(t * 3.3 + q * 1.7); r = 6 + 3 * dens
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, min(255, a + 90)), outline=(70, 120, 190, min(255, a + 60)), width=2)
    img.alpha_composite(lay)
    if arrows > 0:
        dd = ImageDraw.Draw(img)
        for j, x in enumerate(xs):
            q = (t * .8 + j * .27) % 1.0
            y0 = top + 30 + 60 * q
            L = (70 + 120 * k) * arrows
            J.arrow(dd, [(x, y0), (x, y0 + L)], arrow_col, w=int(10 + 14 * k), head=int(26 + 22 * k))
    return top


# ---------------------------------------------------------------- the airliner cabin
def cabin(img, t, cam=0.0, outside_k=1.0):
    """Cabin wall with a big oval window (clouds sliding by below, deep blue sky), overhead bins, seat backs."""
    img.paste(vgrad([(0, (206, 210, 220)), (.5, (226, 228, 234)), (1, (170, 176, 190))]))
    d = ImageDraw.Draw(img)
    # overhead bin
    d.rectangle([-20, -20, W + 20, 330], fill=(232, 234, 240), outline=INK, width=6)
    d.rectangle([-20, 300, W + 20, 360], fill=(188, 192, 204), outline=INK, width=6)
    for x in (300, 760):
        d.rounded_rectangle([x - 90, 120, x + 90, 170], 20, fill=(200, 204, 214), outline=INK, width=4)
    # reading lights
    for x in (180, 540, 900):
        d.ellipse([x - 26, 330, x + 26, 352], fill=(255, 236, 180), outline=INK, width=3)
    # window
    wx, wy, ww, wh = 600 + cam * .2, 700, 330, 470
    m = mask(); ImageDraw.Draw(m).rounded_rectangle([wx - ww / 2, wy - wh / 2, wx + ww / 2, wy + wh / 2], 150, fill=255)
    out = vgrad([(0, (20, 50, 130)), (.5, (70, 130, 210)), (.8, (170, 210, 245)), (1, (240, 246, 255))])
    cl = layer(); cumulus(cl, t * 6, [(200, 1000, 1.0, 3, -60), (700, 1080, 1.3, 5, -60), (1200, 950, .9, 8, -60)],
                          lit=(255, 255, 255), shade=(206, 220, 240))
    out.alpha_composite(cl)
    img.paste(out, (0, 0), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([wx - ww / 2 - 40, wy - wh / 2 - 40, wx + ww / 2 + 40, wy + wh / 2 + 40], 180, outline=(196, 200, 210), width=40)
    d.rounded_rectangle([wx - ww / 2 - 60, wy - wh / 2 - 60, wx + ww / 2 + 60, wy + wh / 2 + 60], 196, outline=INK, width=6)
    d.rounded_rectangle([wx - ww / 2, wy - wh / 2, wx + ww / 2, wy + wh / 2], 150, outline=INK, width=6)
    # shade (half drawn)
    d.rounded_rectangle([wx - ww / 2 + 6, wy - wh / 2 + 6, wx + ww / 2 - 6, wy - wh / 2 + 70], 60, fill=(236, 236, 240))
    d.line([(wx - 60, wy - wh / 2 + 60), (wx + 60, wy - wh / 2 + 60)], fill=INK, width=6)
    glare = mask(); ImageDraw.Draw(glare).polygon([(wx - 120, wy + 200), (wx - 40, wy - 160), (wx + 10, wy - 160), (wx - 70, wy + 200)], fill=255)
    fill_mask(img, ImageChops.multiply(glare, m), (255, 255, 255), .25)
    return (wx, wy, ww, wh)


def chips_bag(img, x, y, s, puff, t, col=(222, 60, 50), col2=(250, 200, 60)):
    """A sealed snack bag (pillow pouch, crimped seals top and bottom) standing on a tray, bottom-centre (x, y).
    puff 0 = slack, creased and caved in; 1 = round and taut (sides bulge, creases gone, highlight stretches)."""
    w = 250 * s; h = 330 * s
    bul = (-14 + 70 * puff) * s                                   # side bulge (negative = caved in)
    top, bot = y - h, y
    sh = 26 * s                                                  # seal height
    by0, by1 = top + sh, bot - sh
    def side(x0, sgn, n=14):
        return [(x0 + sgn * bul * math.sin(math.pi * q), by0 + (by1 - by0) * q) for q in np.linspace(0, 1, n)]
    L = side(x - w / 2, -1); R_ = side(x + w / 2, 1)
    body = L + R_[::-1]
    d = ImageDraw.Draw(img)
    kit.contact_shadow(img, x, y + 4, w * 1.2, (40, 40, 60), .55)
    d.polygon(body, fill=rgb(col)); d.line(body + body[:1], fill=INK, width=int(6 * s), joint='curve')
    # shading on the right side
    shade = [(px - 30 * s, py) for px, py in R_]
    d.polygon(R_ + shade[::-1], fill=lerp(rgb(col), INK, .25))
    for yy, yy2 in ((top, by0 + 4 * s), (by1 - 4 * s, bot)):     # crimped seals
        d.rectangle([x - w / 2 - 6 * s, yy, x + w / 2 + 6 * s, yy2], fill=lerp(rgb(col), INK, .15), outline=INK, width=int(5 * s))
        for i in range(12):
            xx = x - w / 2 + i * w / 11
            d.line([(xx, yy + 4 * s), (xx, yy2 - 4 * s)], fill=lerp(rgb(col), INK, .45), width=int(3 * s))
    cy = (by0 + by1) / 2
    r = 70 * s * (1 + .08 * puff)
    d.ellipse([x - r, cy - r * .85 - 20 * s, x + r, cy + r * .85 - 20 * s], fill=rgb(col2), outline=INK, width=int(4 * s))
    for k_ in range(3):                                           # chips on the label
        cx_, cy_ = x - 30 * s + k_ * 30 * s, cy - 20 * s + (k_ % 2) * 12 * s
        d.ellipse([cx_ - 22 * s, cy_ - 15 * s, cx_ + 22 * s, cy_ + 15 * s], fill=(250, 220, 130), outline=(170, 110, 40), width=int(3 * s))
    d.rectangle([x - w / 2 + 6 * s, cy + 80 * s, x + w / 2 - 6 * s, cy + 100 * s], fill=rgb(col2))
    hl = [(x - w / 2 + 34 * s - bul * .5 * math.sin(math.pi * q), by0 + 30 * s + (by1 - by0 - 60 * s) * q) for q in np.linspace(.05, .95, 10)]
    d.line(hl, fill=lerp(rgb(col), (255, 255, 255), .5), width=int((7 + 7 * puff) * s), joint='curve')
    if puff < .55:                                                # creases while slack
        a = int(255 * (1 - puff / .55))
        lay = layer(); dl = ImageDraw.Draw(lay)
        for i in range(4):
            yy = by0 + (by1 - by0) * (.2 + .2 * i)
            dl.line([(x - w * .4, yy), (x - w * .1, yy + 18 * s), (x + w * .2, yy - 6 * s), (x + w * .4, yy + 10 * s)],
                    fill=lerp(rgb(col), INK, .45) + (a,), width=int(4 * s))
        img.alpha_composite(lay)

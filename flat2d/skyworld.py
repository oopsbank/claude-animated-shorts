"""flat2d.skyworld: the high-altitude world (video 12 on): a thin bright-blue sky, a sun with flare, high cirrus, and a
sea of cumulus tops below, in depth rows that slide with the camera (parallax) and drift; plus small 2D helpers for
flight shots (speed wisps). Everything is a function of the camera pan (px) and time t, so a chase camera works.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kit, cine
from kit import W, H

_cache = {}


def sky(img, horizon=1300, top=(38, 92, 178), mid=(98, 160, 228), low=(196, 226, 250), haze=(236, 244, 252)):
    """Altitude sky gradient: deep blue overhead (thin air), pale at the cloud horizon."""
    img.paste(kit.vgrad([(0, top), (.45 * horizon / H, mid), (horizon / H, low), (min(1, horizon / H + .05), haze), (1, haze)]))


def cirrus(img, t, pan=0.0, y0=120, y1=700, n=9, alpha=.35, seed=4):
    rng = np.random.default_rng(seed); m = kit.mask(); d = ImageDraw.Draw(m)
    for _ in range(n):
        y = rng.uniform(y0, y1); L = rng.uniform(380, 900); x = (rng.uniform(-300, W) - pan * .15 + t * 6) % (W + 900) - 450
        th = rng.uniform(6, 16); sl = rng.uniform(-.08, .02)
        for k in range(5):
            xx = x + k * L * .18; d.line([(xx, y + k * 4), (xx + L * .5, y + k * 4 + L * .5 * sl)], fill=255, width=int(th * (1 - k * .12)))
    kit.fill_mask(img, m, (255, 255, 255), alpha, blur=5)


def _puff_row(w, h, seed, base, amp, rmin, rmax, lit=(255, 255, 255), shade=(196, 208, 236), deep=(150, 168, 214)):
    """One row of cumulus tops as an RGBA strip (w x h): overlapping round bumps, lit tops, cool shaded flanks."""
    k = (w, h, seed, base, amp, rmin, rmax, lit, shade)
    if k in _cache: return _cache[k]
    rng = np.random.default_rng(seed)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x = -rmax
    bumps = []
    while x < w + rmax:
        r = rng.uniform(rmin, rmax); y = base - amp * rng.uniform(.2, 1.0)
        bumps.append((x, y, r)); x += r * rng.uniform(.9, 1.4)
    d.rectangle([0, base, w, h], fill=deep + (255,))
    for x, y, r in bumps: d.ellipse([x - r, y - r, x + r, y + r * 1.4], fill=deep + (255,))
    for x, y, r in bumps: d.ellipse([x - r * .96, y - r * .96, x + r * .9, y + r * .9], fill=shade + (255,))
    for x, y, r in bumps: d.ellipse([x - r * .86, y - r * .94, x + r * .62, y + r * .5], fill=lit + (255,))
    lay = kit.soft_layer(lay, 1.5)
    _cache[k] = lay
    return lay


def cloud_sea(img, t, pan=0.0, tilt=0.0, horizon=1300, rows=5, drift=18.0, warm=0.0, seed=1, scale=1.0):
    """Rows of cumulus tops from the horizon down; nearer rows are bigger, lower, and slide faster with the camera."""
    for i in range(rows):
        f = i / max(1, rows - 1)                                  # 0 far .. 1 near
        hrow = int(260 + 520 * f) ; wrow = W + 1400
        rmin, rmax = (26 + 120 * f) * scale, (60 + 260 * f) * scale
        strip = _puff_row(wrow, hrow + int(rmax * 2), seed * 10 + i, int(rmax * 1.1), rmax * .8, rmin, rmax,
                          lit=kit.lerp((236, 242, 252), (255, 255, 255), f),
                          shade=kit.lerp((206, 218, 240), (190, 204, 236), f), deep=kit.lerp((190, 206, 236), (150, 166, 212), f))
        par = .2 + 1.4 * f
        x = -((pan * par + t * drift * par) % 700) - 300
        y = horizon - 40 + f * 520 - int(rmax * 1.1) + tilt * par
        img.alpha_composite(strip, (int(x), int(y)))
        if warm: kit.radial(img, W * .7, y + 40, 600, (255, 210, 160), .12 * warm)
        kit.haze(img, y - 60, y + 200, (230, 240, 252), .28 * (1 - f))


def wisps(img, t, speed=900, n=14, seed=2, alpha=90, region=(0, 0, W, H), angle=0.0):
    """Fast thin cloud wisps streaming past (speed lines for a flight shot)."""
    rng = np.random.default_rng(seed); lay = kit.layer(); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = region
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    for i in range(n):
        y = rng.uniform(y0, y1); L = rng.uniform(160, 420); ph = rng.uniform(0, 1)
        x = x1 + 300 - ((t * speed * rng.uniform(.7, 1.3) + ph * (x1 - x0 + 600)) % (x1 - x0 + 600))
        d.line([(x, y), (x + L * ca, y + L * sa)], fill=(255, 255, 255, int(alpha * rng.uniform(.5, 1))), width=int(rng.uniform(3, 9)))
    img.alpha_composite(kit.soft_layer(lay, 2.5))


def sun(img, x, y, k=1.0):
    kit.radial(img, x, y, 700 * k, (255, 236, 200), .38)
    kit.radial(img, x, y, 120 * k, (255, 255, 246), .95, power=.6)

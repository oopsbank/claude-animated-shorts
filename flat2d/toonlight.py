"""flat2d.toonlight: night grading, practical lights and frame metrics for the persp toon sets (style test round 3).

Night recipe (LESSONS > Style test > Round 3): render the set in its day palette, `night_map` it to a saturated blue
ramp (keeps every edge and tone step, kills the muddy grey), THEN add the practical lights additively so they stay
warm: `pool` / `glow_at` (lamps, fridge, phone), `floor_patch` (moonlight through a window onto the floor, with the
window bars), `under_door` (a hot line + a fan of light on the floor), `cone` (a flashlight beam + its hot spot).
Characters go on after `night_map` with `moon_tint` (pale blue-white, they must stay white with a black outline).
`measure(img)` prints the numbers we compare with the reference (mean L, p5, p95, saturation, edge density, 360x640).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

# blue night ramp: luminance 0..1 -> colour (deep indigo shadows, saturated mid blues, pale cyan highlights)
NIGHT_RAMP = [(0.0, (8, 10, 40)), (.25, (22, 36, 112)), (.5, (44, 82, 196)), (.75, (96, 150, 236)), (1.0, (206, 228, 255))]


def measure(img, size=(360, 640)):
    """dict(L, p5, p95, sat, edge) of a frame at 360x640: luminance 0..1, HSV saturation mean, the share of pixels
    whose luminance gradient exceeds 0.06 (edge density, the 'detail' number)."""
    a = np.asarray(img.convert('RGB').resize(size, Image.BILINEAR), np.float32) / 255
    L = a @ np.array([.299, .587, .114], np.float32)
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 1e-3, (mx - mn) / np.maximum(mx, 1e-3), 0)
    gx = np.abs(np.diff(L, axis=1))[:-1]; gy = np.abs(np.diff(L, axis=0))[:, :-1]
    edge = float((np.hypot(gx, gy) > .06).mean())
    return dict(L=round(float(L.mean()), 3), p5=round(float(np.percentile(L, 5)), 3), p95=round(float(np.percentile(L, 95)), 3),
                sat=round(float(sat.mean()), 3), edge=round(edge, 3))


def night_map(img, ramp=NIGHT_RAMP, keep=.18, gamma=1.0):
    """Gradient-map the frame's luminance onto the blue ramp; `keep` mixes a little of the original hue back
    (a red quilt stays a little purple-red, not just blue)."""
    a = np.asarray(img, np.float32)
    rgb = a[..., :3] / 255
    L = (rgb @ np.array([.2126, .7152, .0722], np.float32)) ** gamma
    xs = np.array([r[0] for r in ramp], np.float32); cs = np.array([r[1] for r in ramp], np.float32)
    out = np.stack([np.interp(L, xs, cs[:, i]) for i in range(3)], -1)
    if keep:
        out = out * (1 - keep) + rgb * 255 * np.array([.55, .68, 1.0], np.float32) * keep
    a[..., :3] = out.clip(0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA' if a.shape[2] == 4 else 'RGB')


def add_light(img, m, col, k=1.0, mix=0.0):
    """Light through an L mask: screen-add col * mask * k; mix > 0 first pulls the pixels toward col (a warm pool on
    a blue wall must turn orange, a pure screen only washes it toward white)."""
    a = np.asarray(img, np.float32)
    w = np.asarray(m, np.float32)[..., None] / 255
    c = np.array(col, np.float32)[None, None]
    if mix:
        a[..., :3] = a[..., :3] * (1 - w * mix) + c * (w * mix) * .72
    a[..., :3] = 255 - (255 - a[..., :3]) * (1 - (w * k * c / 255).clip(0, 1))
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), img.mode))
    return img


def _mask(img): return Image.new('L', img.size, 0)


def glow_at(img, x, y, r, col=(255, 200, 120), k=1.0, core=.25, mix=.5):
    """A practical's glow: a wide soft halo that tints toward col (mix), plus a hot screen-added core (r in px)."""
    m = _mask(img); d = ImageDraw.Draw(m)
    d.ellipse((x - r, y - r, x + r, y + r), fill=150)
    m = m.filter(ImageFilter.GaussianBlur(r * .5))
    add_light(img, m, col, k * .6, mix=mix)
    if core:
        c = _mask(img); rc = r * core
        ImageDraw.Draw(c).ellipse((x - rc, y - rc, x + rc, y + rc), fill=255)
        add_light(img, c.filter(ImageFilter.GaussianBlur(rc * .6)), col, k)
    return img


def pool(img, cam, P, rx, ry, col=(255, 190, 110), k=.8, z=.002, blur=.35):
    """A light pool on a horizontal surface around world point P (radii in m), soft edged."""
    pts = [cam.p((P[0] + rx * math.cos(t), P[1] + ry * math.sin(t), z)) for t in np.linspace(0, 2 * math.pi, 48)]
    m = _mask(img); ImageDraw.Draw(m).polygon(pts, fill=255)
    bb = m.getbbox()
    if not bb: return img
    m = m.filter(ImageFilter.GaussianBlur(max(4, (bb[2] - bb[0]) * blur * .5)))
    return add_light(img, m, col, k * .5, mix=min(.8, k))


def wall_pool(img, cam, C, nrm, rw, rh, col=(255, 190, 110), k=.6):
    """An elliptic light splash on a wall (centre C, wall normal nrm = 'x' or 'y', radii in m)."""
    pts = []
    for t in np.linspace(0, 2 * math.pi, 48):
        u, v = rw * math.cos(t), rh * math.sin(t)
        pts.append(cam.p((C[0], C[1] + u, C[2] + v) if nrm == 'x' else (C[0] + u, C[1], C[2] + v)))
    m = _mask(img); ImageDraw.Draw(m).polygon(pts, fill=255)
    bb = m.getbbox()
    if not bb: return img
    m = m.filter(ImageFilter.GaussianBlur(max(4, (bb[2] - bb[0]) * .2)))
    return add_light(img, m, col, k * .5, mix=min(.8, k))


def floor_patch(img, cam, win, L, col=(190, 220, 255), k=.75, bars=True, z=.003, blur=3, shaft=.18, cine=None):
    """Moonlight through a window: win = 4 world corners (bottom-left, bottom-right, top-right, top-left),
    L = direction of the light (from the moon into the room, z < 0). Projects the panes onto the floor (z=0), draws
    them with the window cross bars left dark, plus an optional volumetric shaft (cine.shafts3d)."""
    win = np.asarray(win, float); L = np.asarray(L, float)
    def hit(p): t = (p[2] - z) / -L[2]; return p + L * t
    m = _mask(img); d = ImageDraw.Draw(m)
    bl, br, tr, tl = win
    def lerp(a, b, s): return a + (b - a) * s
    panes = [(0, .48, 0, .47), (.52, 1, 0, .47), (0, .48, .53, 1), (.52, 1, .53, 1)] if bars else [(0, 1, 0, 1)]
    for u0, u1, v0, v1 in panes:
        q = [lerp(lerp(bl, br, u), lerp(tl, tr, u), v) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        d.polygon([cam.p(hit(p)) for p in q], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    add_light(img, m, col, k)
    if shaft and cine is not None:
        cine.shafts3d(img, cam, [win], L, 5.0, col=col, alpha=shaft, blur=30, floor_z=0.0)
    return img


def under_door(img, cam, a, b, depth=.9, col=(255, 176, 90), k=.9, z=.002, fan=.6):
    """Light spilling under a door: a hot line along the gap from world a to b (on the floor) and a soft fan on the
    floor reaching `depth` m into the room (direction = the floor normal of the door, pointing into the room)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = (b - a); t[2] = 0; t = t / np.linalg.norm(t)
    n = np.array([-t[1], t[0], 0.0])
    m = _mask(img); d = ImageDraw.Draw(m)
    sp = (b - a) * fan * .5
    d.polygon([cam.p(a), cam.p(b), cam.p(b + n * depth + sp), cam.p(a + n * depth - sp)], fill=150)
    pa, pb = cam.p(a), cam.p(b); dd = cam.px_per_m((a + b) / 2)
    m = m.filter(ImageFilter.GaussianBlur(max(3, dd * .12)))
    line = _mask(img); ImageDraw.Draw(line).line([pa, pb], fill=255, width=max(2, int(dd * .025)))
    add_light(img, m, col, k * .5, mix=.6)
    return add_light(img, line.filter(ImageFilter.GaussianBlur(1.2)), col, k)


def cone(img, x, y, ang, length, spread=18, col=(255, 236, 170), k=.55, spot=None, spot_k=.9):
    """A flashlight beam in screen space from (x, y) along ang (deg, 0 = right, 90 = down), `spread` half-angle;
    spot = (cx, cy, rx, ry) hot ellipse where it lands."""
    m = _mask(img); d = ImageDraw.Draw(m)
    a0, a1 = math.radians(ang - spread), math.radians(ang + spread)
    d.polygon([(x, y), (x + math.cos(a0) * length, y + math.sin(a0) * length),
               (x + math.cos(a1) * length, y + math.sin(a1) * length)], fill=200)
    # fade along the beam
    yy, xx = np.mgrid[0:img.height:4, 0:img.width:4].astype(np.float32)
    u = (((xx - x) * math.cos(math.radians(ang)) + (yy - y) * math.sin(math.radians(ang))) / length).clip(0, 1)
    g = Image.fromarray(((1 - .7 * u) * 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)
    m = ImageChops.multiply(m, g).filter(ImageFilter.GaussianBlur(length * .03))
    add_light(img, m, col, k, mix=.35)
    if spot == 'end':                     # a hot spot where the beam lands, sized by the spread
        e = length * .85; rr = e * math.tan(math.radians(spread)) * 1.1
        spot = (x + math.cos(math.radians(ang)) * e, y + math.sin(math.radians(ang)) * e, rr, rr * .75)
    if spot:
        cx, cy, rx, ry = spot
        s = _mask(img); ImageDraw.Draw(s).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
        add_light(img, s.filter(ImageFilter.GaussianBlur(rx * .25)), col, spot_k, mix=.4)
    return img


def moon_tint(img, box=None, col=(206, 220, 255), k=1.0):
    """Multiply a region (or the whole layer) by a pale moonlight colour: white characters read pale blue-white."""
    a = np.asarray(img, np.float32)
    a[..., :3] *= (1 - k) + k * np.array(col, np.float32) / 255
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), img.mode))
    return img


def ellipse_soft(size, cx, cy, rx, ry, blur):
    """A soft elliptic L mask (for add_light)."""
    m = Image.new('L', size, 0); ImageDraw.Draw(m).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))

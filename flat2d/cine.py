"""flat2d.cine: the cinematic toolkit (video 12 on): depth of field, a 2D camera with roll, a multiplane (2.5D)
camera, per-scene colour grades, bloom, light shafts, water caustics, dust motes, a refraction wobble, lens flare,
and shape-matched transitions (match cuts, iris, push-through, whip pan). Pair it with `persp.py` (3D sets).

Each tool is one call on an RGBA frame (or returns a layer/mask); every argument that should move is a plain number
(t, k, focus), so shots animate them freely. Speed: heavy fields (caustics, bloom, shafts) are computed at reduced
resolution and upscaled; blurs are premultiplied (no dark fringes, LESSONS) and cached where the input repeats.

Grades (`GRADES`): 'hangar' (cool grey-green 1950s industrial, teal shadows, warm skylight highlights), 'cabin'
(warm interior), 'altitude' (bright thin blue), 'navy' (the dark navy diagram stage), 'archive' (sepia paper/office),
'water' (teal under water), 'desk' (warm tungsten macro), 'steel' (cool studio light on metal).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import kit

W, H = 1080, 1920


def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))


def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- depth of field
_blur_cache = {}


def defocus(lay, r, key=None):
    """Premultiplied gaussian blur of an RGBA layer (no dark fringes). key: cache it (static layers)."""
    if r < .35: return lay
    r = round(r * 2) / 2
    if key is not None and (key, r) in _blur_cache: return _blur_cache[(key, r)]
    if r > 6 and lay.width * lay.height > 400_000:          # big radius: blur at half size (same look, 4x faster)
        sm = lay.resize((lay.width // 2, lay.height // 2), Image.BILINEAR)
        out = kit.soft_layer(sm, r / 2).resize(lay.size, Image.BILINEAR)
    else:
        out = kit.soft_layer(lay, r)
    if key is not None:
        if len(_blur_cache) > 60: _blur_cache.clear()
        _blur_cache[(key, r)] = out
    return out


def coc(z, focus, aperture=40.0, zmin=.05):
    """Circle of confusion (px) for a layer at depth z (m) with the focus at `focus` (m): aperture * |1/z - 1/f|
    scaled so a layer at half the focus distance gets `aperture` px."""
    z = max(zmin, z); return aperture * abs(1 / z - 1 / focus) * focus


def bokeh(img, pts, r, col=(255, 236, 200), alpha=.55, ring=.35, blur=1.5):
    """Out-of-focus point lights as soft discs with a brighter rim (pts: [(x, y[, size_k])])."""
    lay = kit.layer(img.width, img.height); d = ImageDraw.Draw(lay)
    for p in pts:
        x, y = p[0], p[1]; k = p[2] if len(p) > 2 else 1.0; rr = r * k
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=tuple(col) + (int(255 * alpha * .55),))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=tuple(col) + (int(255 * alpha * ring + 255 * alpha * .55),),
                  width=max(1, int(rr * .12)))
    img.alpha_composite(kit.soft_layer(lay, blur))


# ---------------------------------------------------------------- 2D camera (zoom, pan, roll)
def cam2d(img, zoom=1.0, fx=None, fy=None, dx=0.0, dy=0.0, roll=0.0):
    """Push in by `zoom` about (fx, fy), rotate by `roll` deg (clockwise) about it, then offset (dx, dy) px."""
    Wi, Hi = img.size; fx = Wi / 2 if fx is None else fx; fy = Hi / 2 if fy is None else fy
    if abs(zoom - 1) < 1e-4 and abs(dx) < .01 and abs(dy) < .01 and abs(roll) < .01: return img
    a = math.radians(roll); c, s = math.cos(a) / zoom, math.sin(a) / zoom
    # output (u, v): q = (u - fx - dx, v - fy - dy); input = R^-1 q / zoom + (fx, fy)
    A, B = c, s; D, E = -s, c
    C = fx - A * (fx + dx) - B * (fy + dy); F = fy - D * (fx + dx) - E * (fy + dy)
    return img.transform(img.size, Image.AFFINE, (A, B, C, D, E, F), resample=Image.BICUBIC)


# ---------------------------------------------------------------- multiplane (2.5D) camera
class Plane:
    """A painted layer at depth z (m). `img` is drawn for a camera at depth 0 looking at z_ref (its native scale is
    the scale at depth z), anchored at its own centre (ax, ay in frame px at the reference camera). draw(t) may
    return a fresh image per frame for animated planes."""
    def __init__(self, img=None, z=10.0, ax=W / 2, ay=H / 2, draw=None, key=None, blur_k=1.0):
        self.img, self.z, self.ax, self.ay, self.draw, self.key, self.blur_k = img, z, ax, ay, draw, key, blur_k


def multiplane(planes, cx=0.0, cy=0.0, dolly=0.0, focus=10.0, aperture=0.0, t=0.0, size=(W, H), roll=0.0,
               out=None):
    """Composite planes far -> near for a camera moved (cx, cy) metres sideways/up (in units where a plane at depth z
    shifts by cx * f / z px; f = 1000 px) and `dolly` metres forward (plane scale = z / (z - dolly)).
    DOF: blur = coc(z - dolly, focus) * aperture-scaled."""
    out = out or Image.new('RGBA', size, (0, 0, 0, 255))
    for p in sorted(planes, key=lambda q: -q.z):
        zz = p.z - dolly
        if zz <= .05: continue
        lay = p.draw(t) if p.draw else p.img
        if lay is None: continue
        s = p.z / zz
        ox = -cx * 1000 / zz; oy = cy * 1000 / zz
        r = coc(zz, focus - dolly if focus - dolly > .1 else .1, aperture) * p.blur_k if aperture else 0.0
        img = lay
        if abs(s - 1) > 1e-3 or abs(ox) > .05 or abs(oy) > .05 or abs(roll) > .01:
            img = cam2d(lay, s, p.ax, p.ay, ox, oy, roll)
        if r >= .35: img = defocus(img, r, key=None if p.draw else (p.key or id(p), round(s, 3), round(ox), round(oy)))
        out.alpha_composite(img)
    return out


# ---------------------------------------------------------------- grading
def _curve(lift, gamma, gain, contrast, offset=0.0):
    x = np.arange(256) / 255.0
    y = x * gain
    y = y * (1 - lift) + lift
    y = np.clip(y, 0, None) ** (1 / max(.05, gamma))
    y = .5 + (y - .5) * contrast + offset
    return np.clip(y * 255, 0, 255).astype(np.uint8)


GRADES = {
    # lift/gamma/gain per channel (r, g, b), contrast, saturation, shadows tint + amount, highlights tint + amount
    'hangar':   dict(lift=(.02, .035, .04), gamma=(.97, 1.0, 1.0), gain=(1.02, 1.0, .97), contrast=1.12, sat=.95,
                     sh=(26, 58, 64), sh_k=.20, hi=(255, 240, 214), hi_k=.14),
    'cabin':    dict(lift=(.05, .035, .03), gamma=(1.02, 1.0, .97), gain=(1.03, 1.0, .95), contrast=1.04, sat=1.04,
                     sh=(66, 38, 44), sh_k=.16, hi=(255, 234, 204), hi_k=.16),
    'altitude': dict(lift=(.03, .045, .07), gamma=(1.0, 1.02, 1.04), gain=(1.0, 1.01, 1.03), contrast=1.04, sat=1.06,
                     sh=(40, 70, 130), sh_k=.14, hi=(250, 250, 255), hi_k=.10),
    'navy':     dict(lift=(.02, .03, .06), gamma=(1.0, 1.0, 1.02), gain=(1.0, 1.0, 1.0), contrast=1.08, sat=1.02,
                     sh=(12, 20, 54), sh_k=.26, hi=(236, 246, 255), hi_k=.06),
    'archive':  dict(lift=(.06, .045, .03), gamma=(1.02, 1.0, .95), gain=(1.02, .99, .92), contrast=1.05, sat=.78,
                     sh=(58, 40, 30), sh_k=.22, hi=(255, 238, 206), hi_k=.18),
    'water':    dict(lift=(.02, .06, .07), gamma=(.96, 1.02, 1.03), gain=(.95, 1.0, 1.0), contrast=1.06, sat=.98,
                     sh=(8, 48, 60), sh_k=.26, hi=(214, 255, 246), hi_k=.10),
    'desk':     dict(lift=(.04, .03, .03), gamma=(1.03, 1.0, .95), gain=(1.04, 1.0, .93), contrast=1.08, sat=1.02,
                     sh=(40, 26, 34), sh_k=.22, hi=(255, 226, 180), hi_k=.18),
    'steel':    dict(lift=(.03, .04, .055), gamma=(1.0, 1.0, 1.02), gain=(1.0, 1.0, 1.01), contrast=1.07, sat=1.0,
                     sh=(16, 28, 56), sh_k=.22, hi=(240, 248, 255), hi_k=.08),
}
_luts = {}


def grade(img, look, k=1.0):
    """Apply a grade preset (name or dict) in place-ish; returns the graded RGBA image. k blends with the input
    (0 = none) so a shot can cross-grade between scenes (e.g. cabin -> altitude while pushing through a window)."""
    g = GRADES[look] if isinstance(look, str) else look
    key = (look if isinstance(look, str) else id(look), round(k, 3))
    if key not in _luts:
        x = np.arange(256) / 255.0
        chans = []
        for i in range(3):
            c = _curve(g['lift'][i], g['gamma'][i], g['gain'][i], g['contrast']).astype(np.float32) / 255
            # split toning per channel: shadows pull toward sh, highlights toward hi
            s_w = (1 - x) ** 2.2 * g['sh_k']; h_w = x ** 2.4 * g['hi_k']
            c = c * (1 - s_w) + (g['sh'][i] / 255) * s_w
            c = c * (1 - h_w) + (g['hi'][i] / 255) * h_w
            c = x * (1 - k) + c * k
            chans.append(np.clip(c * 255, 0, 255).astype(np.uint8))
        _luts[key] = list(np.concatenate(chans))
        if len(_luts) > 200: _luts.clear()
    rgb_ = img.convert('RGB').point(_luts[key])
    sat = 1 + (g['sat'] - 1) * k
    if abs(sat - 1) > .005: rgb_ = ImageEnhance.Color(rgb_).enhance(sat)
    out = rgb_.convert('RGBA')
    return out


def mix_grade(img, a, b, k):
    """Cross-grade between two presets (k 0 -> a, 1 -> b)."""
    if k <= 0: return grade(img, a)
    if k >= 1: return grade(img, b)
    return Image.blend(grade(img, a), grade(img, b), k)


def bloom(img, thr=200, r=26, k=.45, col=None):
    """Glow of the highlights (screen blend), computed at quarter size."""
    sm = img.convert('RGB').resize((img.width // 4, img.height // 4), Image.BILINEAR)
    a = np.asarray(sm, np.float32)
    lum = a @ np.array([.299, .587, .114], np.float32)
    m = np.clip((lum - thr) / (255 - thr), 0, 1)[..., None]
    b = a * m
    if col is not None: b = b * .5 + np.array(col, np.float32) * m * .5
    bi = Image.fromarray(b.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r / 4)).resize(img.size, Image.BILINEAR)
    base = np.asarray(img, np.float32); g = np.asarray(bi, np.float32) * k
    base[..., :3] = 255 - (255 - base[..., :3]) * (1 - g / 255)
    return Image.fromarray(base.clip(0, 255).astype(np.uint8), 'RGBA')


_vig = {}


def vignette(img, strength=.32, color=(10, 10, 22), rx=.8, ry=.66, power=2.4, cx=.5, cy=.5):
    """Soft cinematic vignette (cached mask)."""
    key = (img.size, strength, tuple(color), rx, ry, power, cx, cy)
    if key not in _vig:
        Wi, Hi = img.size; yy, xx = np.mgrid[0:Hi, 0:Wi].astype(np.float32)
        d = np.sqrt(((xx - Wi * cx) / (Wi * rx)) ** 2 + ((yy - Hi * cy) / (Hi * ry)) ** 2)
        a = (np.clip(d, 0, 1.7) ** power * strength).clip(0, .92)
        m = Image.fromarray((a * 255).astype(np.uint8))
        _vig[key] = (m, Image.new('RGBA', img.size, tuple(color) + (255,)))
        if len(_vig) > 30: _vig.clear()
    m, c = _vig[key]
    img.paste(c, (0, 0), m)
    return img


# ---------------------------------------------------------------- light
def shafts(img, polys, col=(255, 238, 200), alpha=.35, blur=26, fade=None, add=True):
    """Volumetric light shafts: polys = [[(x, y) ...], ...] screen polygons (a shaft from its source edge to where
    it lands). fade = [(x0, y0, x1, y1), ...] per poly: alpha ramps 1 -> .15 from (x0, y0) to (x1, y1)."""
    s = 4; m = Image.new('L', (img.width // s, img.height // s), 0)
    for i, p in enumerate(polys):
        if len(p) < 3: continue
        pm = Image.new('L', m.size, 0)
        ImageDraw.Draw(pm).polygon([(x / s, y / s) for x, y in p], fill=255)
        if fade and i < len(fade) and fade[i] is not None:
            x0, y0, x1, y1 = [v / s for v in fade[i]]
            yy, xx = np.mgrid[0:m.size[1], 0:m.size[0]].astype(np.float32)
            dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1
            u = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
            g = Image.fromarray(((1 - .85 * u) * 255).astype(np.uint8))
            pm = ImageChops.multiply(pm, g)
        m = ImageChops.lighter(m, pm)
    m = m.filter(ImageFilter.GaussianBlur(blur / s)).resize(img.size, Image.BILINEAR)
    kit.glow(img, m, col, alpha, blur=1, add=add)
    return m


def shafts3d(img, cam, quads, light_dir, length, col=(255, 238, 200), alpha=.35, blur=26, floor_z=None):
    """Shafts from 3D openings (skylights, windows): each quad (4 world points) is swept along light_dir (unit,
    pointing from the light into the room) for `length` m (or to floor_z). Returns the shaft mask."""
    polys, fades = [], []
    L = np.asarray(light_dir, float); L = L / np.linalg.norm(L)
    nz = max(cam.near, .5)
    for q in quads:
        q = np.asarray(q, float)
        if floor_z is not None and L[2] < 0:
            ln = (q[:, 2] - floor_z) / -L[2]; q2 = q + L[None] * ln[:, None]
        else: q2 = q + L[None] * length
        Ca, Cb = cam.to_cam(q), cam.to_cam(q2)
        pts, src, dst = [], [], []
        for a, b in zip(Ca, Cb):                           # clip each sweep edge (source -> floor) at the near plane
            if a[2] < nz and b[2] < nz: continue
            if a[2] < nz: a = a + (b - a) * ((nz - a[2]) / (b[2] - a[2]))
            elif b[2] < nz: b = a + (b - a) * ((nz - a[2]) / (b[2] - a[2]))
            pts += [a, b]; src.append(a); dst.append(b)
        if len(pts) < 4: continue
        S = cam.proj_cam(np.array(pts))
        S = np.clip(S, -4000, 6000)
        hl = _hull([tuple(p) for p in S])
        if len(hl) < 3: continue
        polys.append(hl)
        a = np.clip(cam.proj_cam(np.array(src)).mean(0), -4000, 6000); b = np.clip(cam.proj_cam(np.array(dst)).mean(0), -4000, 6000)
        fades.append((a[0], a[1], b[0], b[1]))
    if not polys: return None
    return shafts(img, polys, col, alpha, blur, fades)


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def motes(img, t, box, n=60, col=(255, 240, 210), alpha=170, size=(1.5, 4.5), seed=3, mask=None, drift=(6, -10),
          blur=.8):
    """Dust motes drifting in a box; with `mask` (an L image, e.g. the shafts mask) they only show in the light."""
    rng = np.random.default_rng(seed); lay = kit.layer(img.width, img.height); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    ma = np.asarray(mask, np.float32) / 255 if mask is not None else None
    for _ in range(n):
        ph = rng.uniform(0, 6.28); sp = rng.uniform(.5, 1.4)
        x = x0 + (rng.uniform(0, 1) * (x1 - x0) + drift[0] * t * sp + 18 * math.sin(t * .7 * sp + ph)) % (x1 - x0)
        y = y0 + (rng.uniform(0, 1) * (y1 - y0) + drift[1] * t * sp + 12 * math.sin(t * .5 + ph * 2)) % (y1 - y0)
        s = rng.uniform(*size); a = alpha * rng.uniform(.4, 1) * (.65 + .35 * math.sin(t * 2.3 * sp + ph))
        if ma is not None:
            xi, yi = int(min(img.width - 1, max(0, x))), int(min(img.height - 1, max(0, y)))
            a *= min(1.0, ma[yi, xi] * 2.2)
        if a < 6: continue
        d.ellipse([x - s, y - s, x + s, y + s], fill=tuple(col) + (int(a),))
    img.alpha_composite(kit.soft_layer(lay, blur) if blur else lay)


_caus = {}


def caustic_field(w, h, t, scale=1 / 70, seed=0, sharp=7.0, speed=1.0):
    """Animated water-caustic network (0..1 float array h x w): the zero lines of three warped sine fields."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rng = np.random.default_rng(seed)
    c = np.zeros((h, w), np.float32); acc = np.zeros((h, w), np.float32)
    for i in range(3):
        a = rng.uniform(0, math.pi); f = rng.uniform(.8, 1.3); g = rng.uniform(.9, 1.6)
        u = (xx * math.cos(a) - yy * math.sin(a)) * scale; v = (xx * math.sin(a) + yy * math.cos(a)) * scale
        ph = rng.uniform(0, 6.28)
        fld = np.sin(u * f * 6.28 + 1.6 * np.sin(v * g * 6.28 + t * 1.3 * speed + ph) + t * .9 * speed)
        acc += (1 - np.abs(fld)) ** sharp
    return np.clip(acc * .75, 0, 1)


def caustics(img, t, mask=None, box=None, col=(200, 255, 240), alpha=.55, scale=1 / 70, seed=0, res=3, sharp=7.0,
             speed=1.0):
    """Add moving caustic light inside `mask` (L, frame size) or `box`. res = downscale factor of the field."""
    x0, y0, x1, y1 = box if box else (0, 0, img.width, img.height)
    x0, y0, x1, y1 = int(max(0, x0)), int(max(0, y0)), int(min(img.width, x1)), int(min(img.height, y1))
    if x1 <= x0 or y1 <= y0: return
    w, h = max(2, (x1 - x0) // res), max(2, (y1 - y0) // res)
    f = caustic_field(w, h, t, scale * res, seed, sharp, speed)
    m = Image.fromarray((f * 255 * alpha).astype(np.uint8)).resize((x1 - x0, y1 - y0), Image.BILINEAR)
    full = Image.new('L', img.size, 0); full.paste(m, (x0, y0))
    if mask is not None: full = ImageChops.multiply(full, mask)
    kit.glow(img, full, col, 1.0, blur=1, add=True)


def wobble(img, box, t, amp=4.0, wl=60.0, speed=2.0, axis='x'):
    """Refraction wobble (under water / heat): shift rows (axis 'x') of the box region by a travelling sine."""
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1)
    if x1 - x0 < 4 or y1 - y0 < 4: return
    reg = np.asarray(img.crop((x0, y0, x1, y1))).copy(); out = reg.copy()
    if axis == 'x':
        for y in range(reg.shape[0]):
            s = int(round(amp * math.sin((y0 + y) / wl * 6.28 + t * speed)))
            if s: out[y] = np.roll(reg[y], s, axis=0)
    else:
        for x in range(reg.shape[1]):
            s = int(round(amp * math.sin((x0 + x) / wl * 6.28 + t * speed)))
            if s: out[:, x] = np.roll(reg[:, x], s, axis=0)
    img.paste(Image.fromarray(out), (x0, y0))


def flare(img, x, y, k=1.0, col=(255, 236, 200), axis=None):
    """Sun flare: a hot core, a soft halo, a horizontal streak and a few ghost discs along the line to the centre."""
    if k <= .01: return
    kit.radial(img, x, y, 520 * k, col, .45 * k)
    kit.radial(img, x, y, 150 * k, (255, 255, 250), .95 * k, power=.7)
    m = kit.mask(img.width, img.height)
    ImageDraw.Draw(m).ellipse([x - 700 * k, y - 9 * k, x + 700 * k, y + 9 * k], fill=255)
    kit.glow(img, m, (255, 246, 230), .55 * k, blur=10, add=True)
    cx, cy = axis or (img.width / 2, img.height / 2)
    for f, r, a, c in ((.45, 46, .16, (180, 220, 255)), (.8, 26, .2, (255, 210, 160)), (1.3, 80, .1, (190, 255, 220)),
                       (1.7, 34, .14, (255, 190, 230))):
        gx, gy = x + (cx - x) * f * 2, y + (cy - y) * f * 2
        m = kit.mask(img.width, img.height); ImageDraw.Draw(m).ellipse([gx - r * k, gy - r * k, gx + r * k, gy + r * k], fill=255)
        kit.glow(img, m, c, a * k, blur=4, add=True)


# ---------------------------------------------------------------- framing
def fg_frame(img, draw, blur=14.0, alpha=1.0, key=None):
    """An out-of-focus foreground layer framing the shot: draw(layer) paints sharp shapes, then it is defocused
    (DOF) and composited. Use for seat backs, window frames, railings, tool racks, shoulders."""
    lay = kit.layer(img.width, img.height); draw(lay)
    lay = defocus(lay, blur, key)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)


def rrect_mask(size, box, r, blur=0):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


def ellipse_mask(size, box, blur=0):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).ellipse(box, fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


# ---------------------------------------------------------------- transitions (shape-matched)
def xfade(a, b, k):
    if k <= 0: return a
    if k >= 1: return b
    return Image.blend(a.convert('RGBA'), b.convert('RGBA'), k)


def through(a, b, mask_b):
    """Show b through mask_b (L) over a: the push-through / match-cut core (a window opening onto the next shot)."""
    out = a.copy(); out.paste(b, (0, 0), mask_b); return out


def iris(a, b, k, cx, cy, r_max=None, soft=6):
    """Circle wipe from a to b, growing from (cx, cy)."""
    r_max = r_max or math.hypot(max(cx, W - cx), max(cy, H - cy)) + 20
    r = r_max * smooth(k)
    return through(a, b, ellipse_mask(a.size, [cx - r, cy - r, cx + r, cy + r], soft))


def whip(a, b, k, dx=1.0, dy=0.0, blur=60):
    """Whip pan: a slides out and b slides in along (dx, dy) with motion blur at the middle."""
    e = smooth(k); Wi, Hi = a.size
    out = Image.new('RGBA', a.size, (0, 0, 0, 255))
    oa = (-dx * Wi * e, -dy * Hi * e); ob = (dx * Wi * (1 - e), dy * Hi * (1 - e))
    out.alpha_composite(cam2d(a, 1.0, dx=oa[0], dy=oa[1]))
    bb = cam2d(b, 1.0, dx=ob[0], dy=ob[1]); out.paste(bb, (0, 0), _shift_mask(a.size, ob))
    s = math.sin(math.pi * clamp(k)) * blur
    if s > 1:
        rad = int(s)
        arr = np.asarray(out, np.float32); acc = np.zeros_like(arr); n = 0
        for o in range(-rad, rad + 1, max(1, rad // 6)):
            acc += np.roll(arr, o, axis=1 if dx else 0); n += 1
        out = Image.fromarray((acc / n).astype(np.uint8), 'RGBA')
    return out


def _shift_mask(size, off):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).rectangle([off[0], off[1], off[0] + size[0], off[1] + size[1]], fill=255)
    return m


def finish(img, t, look=None, vig=(.30, (10, 10, 22)), grain=.03, bloom_k=0.0, bloom_thr=205, look_b=None, kb=0.0):
    """The house finish for cinematic shots: grade (optionally cross-graded to look_b by kb), bloom, a soft vignette,
    and the boiling film grain."""
    import anim
    if look_b is not None and kb > 0: img = mix_grade(img, look, look_b, kb)
    elif look: img = grade(img, look)
    if bloom_k: img = bloom(img, bloom_thr, 26, bloom_k)
    if vig: vignette(img, vig[0], vig[1])
    if grain: anim.grain(img, grain, t=t)
    return img

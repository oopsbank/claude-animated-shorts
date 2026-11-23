"""Ocean kit (video 5, "The Sound From the Deep"): layers for 1080x1920 flat-2D scenes, back to front.

Every layer takes its animation parameters (t, cam offset, progress k) so the shots in bloop.py keep moving:
- `ocean_section`: a vertical cross-section of the sea: sky strip, a moving wave line, depth bands that darken
  with depth (sunlit / twilight / deep), god rays, marine snow, a faceted seafloor ridge; returns the surface y.
- `depth_ruler`: depth ticks down one edge (0 M ... 4 KM).
- `hydrophone`: a moored listening station (anchor, cable, float, sensor capsule with a glow ring).
- `sound_ring` / `pulse_train`: the glowing sound fronts (a circle clipped to the water), several emits.
- `waveform`: a trace drawn from a function across a box (with a playhead and progress).
- `blue_whale`: a side-view blue whale with a moving fluke and pectoral fin.
- `shelf`: an Antarctic ice shelf in side view (flat top, faceted face, submerged root), with a crack and a
  calving slab that tilts and drops.
- `ship`: a research vessel (red hull, white bridge, stern A-frame) rocking on the swell.
- `glass`, `ice_cube`: the drink-glass analogy.
- `headphones`: the scientist's identity item, drawn over a head.
- `sea_shadow`: the vague creature silhouette (only ever shown as speculation or a question).
"""
import math
import numpy as np
from PIL import Image, ImageDraw
import kit
from kit import W, H, INK, vgrad, radial, haze, mask, glow, fill_mask, layer, lerp, rgb

RED = (255, 72, 60)          # the Bloop's sound colour, the same in every shot
RED_HOT = (255, 170, 120)


def surface_pts(y, t, amp=10, x0=-60, x1=W + 60, n=40, cam=0.0, k=1.0):
    return [(x, y + amp * math.sin(x * .011 + t * 1.6 + cam * .011) * k + amp * .5 * math.sin(x * .027 - t * 2.3))
            for x in np.linspace(x0, x1, n)]


def ocean_section(img, t, surface=560, floor=1780, sky=((24, 30, 70), (70, 80, 140)), water=((40, 110, 170), (14, 46, 100), (6, 14, 40)),
                  cam=0.0, rays=True, snow=True, seed=3, floor_col=((40, 34, 52), (22, 20, 32)), sun=None):
    """The sea in cross-section. Moves: the wave line rolls, god rays sway, marine snow drifts, cam parallax."""
    d = ImageDraw.Draw(img)
    img.paste(vgrad([(0, sky[0]), (1, sky[1])], h=surface + 40), (0, 0))
    if sun: radial(img, sun[0] + cam * .9, sun[1], sun[2], sun[3], .6)
    wl = vgrad([(0, water[0]), (.35, water[1]), (1, water[2])], h=H - surface)
    m = mask(); ImageDraw.Draw(m).polygon(surface_pts(surface, t, cam=cam) + [(W + 60, H), (-60, H)], fill=255)
    img.paste(wl, (0, surface), m.crop((0, surface, W, H)))
    if rays:
        kit.light_rays(img, 540 + cam * .3, surface - 300, (190, 230, 255), n=8, alpha=.12, spread=(120, 260), length=1300,
                       seed=seed, phase=t * .25, blur=22)
    d = ImageDraw.Draw(img)
    pts = surface_pts(surface, t, cam=cam)
    d.line(pts, fill=(200, 236, 255), width=6)
    d.line([(x, y + 12) for x, y in pts], fill=lerp(water[0], (255, 255, 255), .25), width=4)
    # faceted seafloor ridge (parallax)
    rng = np.random.default_rng(seed + 7)
    xs = np.linspace(-200, W + 200, 14); ys = [floor + rng.uniform(-90, 40) for _ in xs]
    poly = [(x - cam * .6, y) for x, y in zip(xs, ys)] + [(W + 200, H), (-200, H)]
    d.polygon(poly, fill=floor_col[0], outline=INK, width=5)
    for i in range(len(xs) - 1):
        if i % 2: d.polygon([(xs[i] - cam * .6, ys[i]), (xs[i + 1] - cam * .6, ys[i + 1]), (xs[i + 1] - cam * .6, H)], fill=floor_col[1])
    if snow:
        kit.dust(img, seed, 70, (0, surface + 30, W, floor), (220, 236, 255), 120, size=(2, 5), t=t * .6)
    return surface


def depth_ruler(img, x, y0, px_per_km, kms=(0, 1, 2, 3, 4), col=(200, 226, 255), fs=26, a=200):
    lay = layer(); d = ImageDraw.Draw(lay); f = kit.font(fs, True)
    d.line([(x, y0), (x, y0 + px_per_km * kms[-1])], fill=col + (a,), width=4)
    for k in kms:
        y = y0 + k * px_per_km
        d.line([(x, y), (x + 22, y)], fill=col + (a,), width=4)
        d.text((x + 30, y), '0 M' if k == 0 else f'{k} KM', font=f, fill=col + (a,), anchor='lm')
    img.alpha_composite(lay)


def hydrophone(img, x, y, floor_y, t, lit=0.0, s=1.0, cable=(150, 170, 190), body=(240, 200, 60), phase=0.0):
    """A moored listening station: anchor block on the floor, a cable up to a float and a sensor capsule.
    Moves: sways with the current; lit 0..1 flashes a glow ring (it heard something)."""
    d = ImageDraw.Draw(img)
    sway = 6 * math.sin(t * 1.1 + phase) * s
    xs = x + sway
    if floor_y is not None:
        d.line([(x, floor_y), (xs, y)], fill=INK, width=int(9 * s)); d.line([(x, floor_y), (xs, y)], fill=cable, width=int(4 * s))
        d.rectangle([x - 26 * s, floor_y - 18 * s, x + 26 * s, floor_y + 8 * s], fill=(70, 70, 84), outline=INK, width=int(4 * s))
    if lit > 0:
        radial(img, xs, y, 220 * s, RED_HOT, .7 * lit)
        m = mask(); r = 70 * s + 60 * s * (1 - lit)
        ImageDraw.Draw(m).ellipse([xs - r, y - r, xs + r, y + r], outline=255, width=int(8 * s))
        glow(img, m, RED, .9 * lit, blur=10, add=True)
        d = ImageDraw.Draw(img)
    fy = y - 70 * s                                                       # float
    d.ellipse([xs - 30 * s, fy - 30 * s, xs + 30 * s, fy + 30 * s], fill=(236, 100, 50), outline=INK, width=int(5 * s))
    d.chord([xs - 22 * s, fy - 24 * s, xs + 16 * s, fy + 6 * s], 180, 330, fill=(255, 170, 120))
    d.line([(xs, fy + 30 * s), (xs, y - 24 * s)], fill=INK, width=int(6 * s))
    d.rounded_rectangle([xs - 20 * s, y - 26 * s, xs + 20 * s, y + 34 * s], 16 * s, fill=body, outline=INK, width=int(5 * s))
    d.ellipse([xs - 10 * s, y - 4 * s, xs + 10 * s, y + 16 * s], fill=lerp((40, 40, 50), RED_HOT, lit))


def sound_ring(img, cx, cy, r, w=18, col=RED, a=1.0, clip=None, squash=1.0, arc=None):
    """One glowing sound front. clip=(y_top, y_bot): only inside the water. arc: (start, end) degrees."""
    if r <= 2 or a <= .01: return
    m = mask(*img.size); dm = ImageDraw.Draw(m)
    box = [cx - r, cy - r * squash, cx + r, cy + r * squash]
    if arc: dm.arc(box, arc[0], arc[1], fill=255, width=int(w))
    else: dm.ellipse(box, outline=255, width=int(w))
    if clip:
        c = mask(*img.size); ImageDraw.Draw(c).rectangle([0, clip[0], img.width, clip[1]], fill=255)
        m = Image.fromarray((np.asarray(m, np.uint16) * np.asarray(c, np.uint16) // 255).astype(np.uint8))
    glow(img, m, col, .75 * a, blur=26, add=True)
    fill_mask(img, m, lerp(col, (255, 255, 255), .35), .9 * a, blur=2)


def pulse_train(img, cx, cy, t, t0=-3.0, every=.55, speed=520, n=10, w=16, col=RED, clip=None, rmax=2600, fade=2200, squash=1.0, arc=None):
    """Rings emitted every `every` s from t0 on; each grows at `speed` px/s and fades with radius."""
    for i in range(n):
        te = t0 + i * every
        if t < te: break
        r = (t - te) * speed
        if r > rmax: continue
        a = max(0.0, 1 - r / fade) * min(1.0, (t - te) / .15)
        sound_ring(img, cx, cy, r, w * (1 - .5 * r / rmax), col, a, clip, squash, arc)


def waveform(img, box, fn, k=1.0, col=(120, 255, 170), w=6, glow_a=.5, head=True):
    """Trace y = fn(x 0..1) (-1..1) across box up to progress k. Moves: k (it draws on)."""
    x0, y0, x1, y1 = box; cy = (y0 + y1) / 2; hh = (y1 - y0) / 2
    n = max(2, int(220 * k)); pts = [(x0 + (x1 - x0) * k * i / (n - 1), cy - hh * fn(k * i / (n - 1))) for i in range(n)]
    m = mask(*img.size); ImageDraw.Draw(m).line(pts, fill=255, width=w + 6, joint='curve')
    glow(img, m, col, glow_a, blur=14, add=True)
    ImageDraw.Draw(img).line(pts, fill=col, width=w, joint='curve')
    if head and k < 1:
        x, y = pts[-1]; radial(img, x, y, 40, (255, 255, 255), .6)
    return pts


def blue_whale(img, x, y, s, t, flip=False, body=(70, 104, 150), belly=(176, 200, 214), ink=INK, alpha=1.0):
    """Side view, facing right (flip: left). ~1000*s px long. Moves: the fluke beats, the fin paddles, the
    body undulates slightly."""
    L = 1000; lay = layer(int(L * 1.25), 420); d = ImageDraw.Draw(lay); ox, oy = 150, 200
    beat = math.sin(t * 2.2)
    def bp(f, side):                                                      # body outline point at f (0 tail .. 1 snout)
        th = 92 * min(1.0, (f / .3)) ** .75 * (.22 + .78 * min(1.0, f / .3))
        if f > .68: th = 92 * (1 - .5 * ((f - .68) / .32) ** 2)
        th = max(th, 12)
        und = 10 * math.sin(f * 3 - t * 2.2) * (1 - f)
        return (ox + f * L, oy + und + side * th * (1.0 if side < 0 else .92))
    top = [bp(f, -1) for f in np.linspace(0, 1, 40)]; bot = [bp(f, 1) for f in np.linspace(1, 0, 40)]
    nose = [(ox + L + 40 * math.cos(a), oy + 46 * math.sin(a)) for a in np.linspace(-math.pi / 2, math.pi / 2, 9)]
    top = top + nose
    # fluke
    tx, ty = top[0][0], (top[0][1] + bot[-1][1]) / 2
    fl = 70 * beat
    fluke = [(tx + 10, ty), (tx - 120, ty - 110 + fl), (tx - 70, ty + fl * .4), (tx - 120, ty + 110 + fl), (tx + 10, ty)]
    d.polygon(fluke, fill=body, outline=ink, width=8)
    d.polygon(top + bot, fill=body, outline=ink, width=8)
    # belly + throat grooves
    bel = [bp(f, 1) for f in np.linspace(.35, 1, 24)] + [(ox + L + 30, oy + 30)] + [(bp(f, 1)[0], bp(f, .25)[1]) for f in np.linspace(1, .35, 24)]
    d.polygon(bel, fill=belly)
    for i in range(7):
        f0 = .62 + i * .045; a = bp(f0, 1)
        d.line([(a[0], a[1] - 8), (a[0] + 110, a[1] - 14 - i * 3)], fill=lerp(belly, body, .45), width=4)
    d.line(top + bot + [top[0]], fill=ink, width=8)
    # mottling, dorsal fin, eye, fin
    rng = np.random.default_rng(3)
    for i in range(26):
        f = rng.uniform(.15, .85); px, py = bp(f, -1); q = rng.uniform(6, 14)
        oy_ = py + rng.uniform(14, 60); d.ellipse([px - q, oy_ - q * .6, px + q, oy_ + q * .6], fill=lerp(body, belly, .35))
    dx, dy = bp(.25, -1); d.polygon([(dx - 30, dy + 6), (dx + 10, dy - 34), (dx + 30, dy + 6)], fill=body, outline=ink, width=6)
    ex, ey = bp(.9, -1); d.ellipse([ex - 9, ey + 52, ex + 9, ey + 68], fill=ink)
    fx, fy = bp(.66, 1); fa = math.radians(30 + 14 * math.sin(t * 2.2 + 1))
    d.polygon([(fx - 20, fy - 30), (fx + 40, fy - 30), (fx - 30 + math.cos(fa) * -160, fy + math.sin(fa) * 160)], fill=lerp(body, belly, .2), outline=ink, width=6)
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    import anim
    anim.scaled_paste(img, lay, x, y, s, angle=2 * math.sin(t * 1.1), alpha=alpha)


def shelf_poly(x0, x1, top, water, root):
    return [(x0, top), (x1, top), (x1, water + root), (x0, water + root)]


def shelf(img, x0, x1, top, water, t, root=260, seed=5, crack_x=None, crack_k=0.0, calve=0.0, calve_dir=-1,
          lit=(244, 250, 255), mid=(200, 226, 246), shade=(150, 190, 228), under=(120, 190, 220), sky_tint=None):
    """An ice shelf, side view: a flat snow top, a faceted vertical face (from kit.ice_cliff) and a submerged
    root under the waterline (translucent). crack_x: where a crack opens (crack_k 0..1 runs it down);
    calve 0..1: the slab beyond the crack (toward calve_dir) tilts away and sinks. Returns the slab polygon."""
    # submerged root (drawn translucent: the water over it)
    lay = layer(); d = ImageDraw.Draw(lay)
    rx0, rx1 = x0 + 20, x1 - 20
    d.polygon([(rx0, water), (rx1, water), (rx1 - 40, water + root), (rx0 + 60, water + root * .8)], fill=under + (150,))
    img.alpha_composite(lay)
    slab = None
    if crack_x is not None and calve > 0:
        # the main shelf stops at the crack; the slab is drawn separately, rotated
        if calve_dir < 0: main = (crack_x, x1); sl = (x0, crack_x)
        else: main = (x0, crack_x); sl = (crack_x, x1)
    else:
        main = (x0, x1); sl = None
    def face(ax0, ax1, img_):
        kit.ice_cliff(img_, ax0, ax1, lambda x: top, lambda x: water + 8, seed, lit=lit, mid=mid, shade=shade, deep=(90, 140, 200),
                      lip_icicles=False, ink_w=5)
    face(*main, img)
    if sl:
        lay = layer(); face(*sl, lay)
        piv = (crack_x, water)
        ang = calve * 24 * (-1 if calve_dir < 0 else 1)
        sink = calve ** 1.6 * 260
        lay = lay.rotate(-ang, resample=Image.BICUBIC, center=piv, translate=(calve_dir * 50 * calve, sink))
        img.alpha_composite(lay)
        slab = True
    if crack_x is not None and crack_k > 0 and calve <= 0:
        d = ImageDraw.Draw(img); rng = np.random.default_rng(seed + 9)
        n = 9; pts = [(crack_x + rng.uniform(-14, 14), top + (water - top) * i / (n - 1) * crack_k) for i in range(n)]
        m = mask(); ImageDraw.Draw(m).line(pts, fill=255, width=26)
        glow(img, m, (120, 220, 255), .7 * crack_k, blur=18, add=True)
        d.line(pts, fill=INK, width=12); d.line(pts, fill=(40, 90, 140), width=5)
        for i in range(2, n - 1, 2):                                       # side branches
            x, y = pts[i]; dx = rng.uniform(30, 70) * (1 if i % 4 else -1)
            d.line([(x, y), (x + dx, y + 30), (x + dx * 1.4, y + 50)], fill=INK, width=6)
    return slab


def splash(img, x, y, t, k, w=420, col=(230, 246, 255), seed=4):
    """Spray and foam where a slab hits the water (k 0..1 the life of the splash)."""
    if k <= 0 or k >= 1: return
    d = ImageDraw.Draw(img); rng = np.random.default_rng(seed)
    for i in range(46):
        vx, vy = rng.uniform(-1, 1) * w, rng.uniform(-900, -300); q = rng.uniform(8, 22) * (1 - k * .6)
        px = x + vx * k; py = y + vy * k + 1300 * k * k
        if py < y + 10: d.ellipse([px - q, py - q, px + q, py + q], fill=col, outline=INK, width=3)
    m = mask(); ImageDraw.Draw(m).ellipse([x - w * (.6 + k), y - 40, x + w * (.6 + k), y + 40], fill=255)
    fill_mask(img, m, (240, 250, 255), .8 * (1 - k), blur=12)


def ship(img, x, y, s, t, hull=(206, 50, 46), roll=1.0):
    """Research ship, side view (bow right), waterline at y. Moves: rolls and heaves on the swell."""
    lay = layer(900, 560); d = ImageDraw.Draw(lay); ox, oy = 450, 400            # waterline at oy
    d.polygon([(ox - 380, oy - 110), (ox + 330, oy - 110), (ox + 420, oy - 150), (ox + 360, oy + 30), (ox - 360, oy + 30)], fill=hull, outline=INK, width=8)
    d.polygon([(ox - 370, oy - 30), (ox + 380, oy - 30), (ox + 360, oy + 30), (ox - 360, oy + 30)], fill=(40, 40, 52))   # boot top
    d.line([(ox - 380, oy - 110), (ox + 330, oy - 110), (ox + 420, oy - 150)], fill=(250, 250, 250), width=8)
    d.rectangle([ox - 60, oy - 300, ox + 220, oy - 110], fill=(244, 244, 240), outline=INK, width=7)          # bridge block
    d.rectangle([ox - 20, oy - 380, ox + 170, oy - 300], fill=(244, 244, 240), outline=INK, width=7)
    for i in range(5): d.rectangle([ox - 40 + i * 50, oy - 270, ox - 10 + i * 50, oy - 240], fill=(70, 130, 190), outline=INK, width=3)
    for i in range(3): d.rectangle([ox + 5 + i * 52, oy - 360, ox + 40 + i * 52, oy - 330], fill=(70, 130, 190), outline=INK, width=3)
    d.line([(ox + 80, oy - 380), (ox + 80, oy - 470)], fill=INK, width=7); d.line([(ox + 50, oy - 440), (ox + 110, oy - 440)], fill=INK, width=5)
    d.rectangle([ox + 230, oy - 180, ox + 320, oy - 110], fill=(244, 244, 240), outline=INK, width=6)
    # stern A-frame (the crane that lowers instruments)
    d.line([(ox - 330, oy - 110), (ox - 420, oy - 330)], fill=INK, width=18); d.line([(ox - 330, oy - 110), (ox - 420, oy - 330)], fill=(250, 170, 40), width=10)
    d.line([(ox - 250, oy - 110), (ox - 420, oy - 330)], fill=INK, width=14); d.line([(ox - 250, oy - 110), (ox - 420, oy - 330)], fill=(250, 170, 40), width=7)
    ang = 3 * math.sin(t * 1.3) * roll; heave = 6 * math.sin(t * 1.3 + 1) * roll
    import anim
    anim.scaled_paste(img, lay, x, y - (400 - 280) * s + heave, s, angle=ang)
    return (x - 420 * s, y - 330 * s + heave)                     # the A-frame tip (approx., ignoring the roll)


def glass(img, cx, base, w, h, t, liquid=(226, 150, 60), fill=.62, back=True):
    """A tumbler (front view). back=True draws the back wall and liquid; back=False the front rim and glints."""
    d = ImageDraw.Draw(img); x0, x1 = cx - w / 2, cx + w / 2; top = base - h
    if back:
        lay = layer(); dl = ImageDraw.Draw(lay)
        dl.polygon([(x0, top), (x1, top), (x1 - w * .06, base), (x0 + w * .06, base)], fill=(220, 240, 255, 70))
        ly = base - h * fill + 6 * math.sin(t * 2)
        dl.polygon([(x0 + w * .02, ly), (x1 - w * .02, ly), (x1 - w * .06, base - 10), (x0 + w * .06, base - 10)], fill=liquid + (215,))
        dl.ellipse([x0 + w * .02, ly - 18, x1 - w * .02, ly + 18], fill=lerp(liquid, (255, 255, 255), .3) + (230,))
        img.alpha_composite(lay)
        return ly
    d.polygon([(x0, top), (x1, top), (x1 - w * .06, base), (x0 + w * .06, base)], outline=INK, width=8)
    d.ellipse([x0, top - 22, x1, top + 22], outline=INK, width=7)
    d.ellipse([x0 + w * .06 - 4, base - 20, x1 - w * .06 + 4, base + 20], outline=INK, width=7)
    lay = layer(); dl = ImageDraw.Draw(lay)
    dl.line([(x0 + w * .12, top + 40), (x0 + w * .16, base - 40)], fill=(255, 255, 255, 170), width=14)
    dl.line([(x0 + w * .24, top + 60), (x0 + w * .26, top + h * .4)], fill=(255, 255, 255, 120), width=7)
    img.alpha_composite(lay)


def ice_cube(img, cx, cy, r, t, crack=0.0, ang=0.0, seed=2, tint=(214, 240, 255), alpha=1.0):
    """A faceted ice cube (3/4 view) of half-size r; crack 0..1 runs glowing fracture lines across it."""
    lay = layer(int(r * 3.2), int(r * 3.2)); d = ImageDraw.Draw(lay); o = r * 1.6
    k = r * .45
    front = [(o - r, o - r + k), (o + r - k, o - r + k), (o + r - k, o + r), (o - r, o + r)]
    topf = [(o - r, o - r + k), (o - r + k, o - r), (o + r, o - r), (o + r - k, o - r + k)]
    side = [(o + r - k, o - r + k), (o + r, o - r), (o + r, o + r - k), (o + r - k, o + r)]
    d.polygon(front, fill=tint, outline=INK, width=max(3, int(r * .06)))
    d.polygon(topf, fill=lerp(tint, (255, 255, 255), .6), outline=INK, width=max(3, int(r * .06)))
    d.polygon(side, fill=lerp(tint, (120, 170, 220), .5), outline=INK, width=max(3, int(r * .06)))
    d.line([(o - r * .7, o - r * .2), (o - r * .4, o - r * .5)], fill=(255, 255, 255), width=max(2, int(r * .08)))
    d.ellipse([o - r * .3, o + r * .1, o - r * .05, o + r * .35], fill=lerp(tint, (255, 255, 255), .5))
    if crack > 0:
        rng = np.random.default_rng(seed)
        paths = [[(o - r * .1, o - r + k)], [(o + r * .5, o - r * .6)]]
        for p in paths:
            for i in range(6): x, y = p[-1]; p.append((x + rng.uniform(-.25, .2) * r, y + r * .32))
        m = mask(lay.width, lay.height); dm = ImageDraw.Draw(m)
        for p in paths:
            n = max(2, int(len(p) * min(1, crack)))
            dm.line(p[:n], fill=255, width=max(4, int(r * .09)))
        glow(lay, m, (160, 230, 255), .8 * crack, blur=max(4, int(r * .15)), add=True)
        d = ImageDraw.Draw(lay)
        for p in paths:
            n = max(2, int(len(p) * min(1, crack))); d.line(p[:n], fill=(40, 90, 150), width=max(2, int(r * .04)))
    import anim
    anim.scaled_paste(img, lay, cx, cy, 1.0, angle=ang, alpha=alpha)


def headphones(img, head, R, col=(40, 44, 60), cup=(220, 60, 60), look=0.0):
    """Over-ear headphones: a band over the crown and two cups at the ears (identity item)."""
    hx, hy = head; d = ImageDraw.Draw(img); lx = look * R * .18
    bw = int(R * .22)
    box = [hx - R * 1.08 + lx, hy - R * 1.22, hx + R * 1.08 + lx, hy + R * .9]
    d.arc(box, 192, 348, fill=INK, width=bw + 10); d.arc(box, 192, 348, fill=col, width=bw)
    for sgn in (-1, 1):
        cx = hx + sgn * R * 1.02 + lx * (1 - sgn * .3); cy = hy + R * .05
        d.rounded_rectangle([cx - R * .26, cy - R * .42, cx + R * .26, cy + R * .42], R * .2, fill=cup, outline=INK, width=max(4, int(R * .09)))
        d.rounded_rectangle([cx - R * .14 + sgn * R * .05, cy - R * .28, cx + R * .08 + sgn * R * .05, cy + R * .1], R * .1, fill=lerp(cup, (255, 255, 255), .35))


def sea_shadow(img, x, y, s, t, col=(6, 10, 26), alpha=.85, eye=0.0, blur=6):
    """A vague giant silhouette in the deep (speculation only): a domed body and drifting tentacles."""
    m = mask(*img.size); d = ImageDraw.Draw(m)
    d.ellipse([x - 300 * s, y - 220 * s, x + 300 * s, y + 160 * s], fill=255)
    for i in range(7):
        bx = x + (i - 3) * 80 * s; pts = []
        for j in range(14):
            f = j / 13; pts.append((bx + 60 * s * math.sin(f * 4 + t * 1.6 + i) * f + (i - 3) * 40 * s * f, y + 100 * s + f * 560 * s))
        d.line(pts, fill=255, width=int((60 - 40 * 0) * s), joint='curve')
        d.line(pts[7:], fill=255, width=int(34 * s))
    fill_mask(img, m, col, alpha, blur=blur)
    if eye > 0:
        for sgn in (-1, 1):
            radial(img, x + sgn * 110 * s, y - 40 * s, 60 * s, (255, 220, 120), .6 * eye)

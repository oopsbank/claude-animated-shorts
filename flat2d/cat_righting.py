"""Cat righting (video 8, "Why Do Cats Always Land on Their Feet?"): shots as `sNN(u, D, cue) -> (img, info)`.

Same contract as wind_cave.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the
shot's voice-over LINE. info: 'faces' (face boxes) and 'avoid' (boxes the caption must not cover).
Hero image: the cat UPSIDE DOWN in mid-air, lit, in front of Marey's black velvet backdrop in his 1894 Paris lab.
Colour motif: warm sepia film (the 1894 chronophotograph strip) against the black velvet; the explanation splits the
cat into a BLUE front half and an ORANGE back half. Serious, curious tone, no comedy. Every shot keeps moving.

Render: .venv/bin/python flat2d/render.py audio/cat-righting/words.json OUT.mp4 --film cat_righting --size 540x960
"""
import math, os, sys, re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import kit, anim
import cat as C
from kit import W, H, INK, vgrad, radial, haze, dust, label, title, font, mask, glow, fill_mask, layer, lerp, rgb
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES, mix, add, damp
from blood_falls import finish, slam_title, face_box
from blood_falls_2 import put_chip, draw_x
import tunguska as TG
from tunguska import flash

SLUG = 'cat-righting'
HIDE_UI = False                          # thumbnail frames: no chips, titles or labels
SEPIA = (236, 206, 150)
SEPIA_D = (52, 34, 22)
KEY_B = C.FRONT_COL                      # front half
KEY_O = C.BACK_COL                       # back half
GOLD = (255, 206, 92)
MAREY_COL = (168, 104, 48)
MAREY_KW = dict(shirt='#ece4d2', coat='#3d3446', pants='#2c2830')
OWNER_KW = dict(shirt='#5a8fd0', pants='#3b3f58')
SCI_KW = dict(shirt='#f2f2ee', coat='#e9ecef', pants='#41506a')
GOOD = (70, 170, 90)
BAD = (220, 60, 50)


def chip(img, txt, fill, x, y, u, t0, size=50, angle=0.0, out=None):
    if HIDE_UI: return
    s = pop(u, t0, .3, 2.0)
    if out is not None: s *= 1 - smooth(seg(u, out, out + .25))
    put_chip(img, txt, fill, x, y, s, size=size, angle=angle)


def stitle(img, key, lines, y, u, t0, size=104, stagger=.16):
    if HIDE_UI: return
    slam_title(img, key, lines, y, u, t0, size=size, stagger=stagger)


def clue(img, txt, u, t0=.05, y=250):
    if HIDE_UI: return
    TG.clue(img, txt, u, t0, y)


def beard(img, g, look=0.0, col=(128, 112, 104)):
    """Marey's grey-brown full beard: it hugs the jaw along the head rim (cheek to cheek), stays BELOW the mouth
    (the stickman mouth sits at ~0.49 R under the head centre), ends in a soft rounded point, plus a thin moustache
    above the mouth. Drawn at 3x and downsampled so the edge is smooth; no straight edges, no side tufts."""
    hx, hy = g['head']; R = g['R']
    look = g.get('look', look); lean = g.get('lean', 0.0)
    fx = hx + look * R * .35                       # the face (mouth) shifts with look, like stickman's fx
    SS = 3
    x0, y0 = int(hx - R * 1.3), int(hy - R * .2)
    wpx, hpx = int(R * 2.6), int(R * 1.9)
    lay = Image.new('RGBA', (wpx * SS, hpx * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    P = lambda x, y: ((x - x0) * SS, (y - y0) * SS)
    outer = []                                     # along the head rim, slightly outside it, from the right cheek round the chin
    a0, a1 = math.radians(22), math.radians(158)
    for i in range(25):
        a = a0 + (a1 - a0) * i / 24
        k = math.sin(a) ** 3                        # bulge down into a rounded point under the chin
        r = R * (1.03 + .38 * k)
        outer.append((hx + math.cos(a) * R * 1.03 + look * R * .12 * k, hy + math.sin(a) * r))
    inner = []                                     # the top edge: a soft smile curve under the mouth, back to the right cheek
    for i in range(17):
        t = i / 16
        x = outer[-1][0] + (outer[0][0] - outer[-1][0]) * t
        dip = math.sin(math.pi * t)
        y = outer[-1][1] + (outer[0][1] - outer[-1][1]) * t + dip * (hy + R * .74 - (outer[0][1] + outer[-1][1]) / 2)
        inner.append((x + (fx - hx) * dip * .8, y))
    poly = [P(*q) for q in outer + inner]
    ow = max(3, int(R * .06)) * SS
    d.polygon(poly, fill=col + (255,))
    d.line(poly + [poly[0]], fill=INK + (255,) if len(INK) == 3 else INK, width=ow, joint='curve')
    hair = lerp(col, INK, .35)
    for k in range(5):                             # a few soft strands following the beard's flow
        t = (k + 1) / 6
        xa = hx + (t - .5) * R * 1.3 + (fx - hx) * .6
        d.line([P(xa, hy + R * .92), P(xa + (t - .5) * R * .18, hy + R * 1.22)], fill=hair + (255,), width=max(2, int(R * .04)) * SS)
    for s_ in (-1, 1):                             # thin moustache above the mouth, curving out
        pts = []
        for i in range(9):
            t = i / 8
            pts.append(P(fx + s_ * R * (.05 + .3 * t), hy + R * (.32 + .07 * t * t) ))
        for i in range(9):
            t = 1 - i / 8
            pts.append(P(fx + s_ * R * (.05 + .3 * t), hy + R * (.40 + .03 * t)))
        d.polygon(pts, fill=lerp(col, INK, .12) + (255,))
        d.line(pts + [pts[0]], fill=INK + (255,) if len(INK) == 3 else INK, width=max(2, int(R * .03)) * SS, joint='curve')
    if abs(lean) > .05:                            # tilt with the head (actor rotates the card by -lean)
        lay = lay.rotate(-lean, resample=Image.BICUBIC, center=((hx - x0) * SS, (hy - y0) * SS))
    lay = lay.resize((wpx, hpx), Image.LANCZOS)
    img.alpha_composite(lay, (x0, y0)) if img.mode == 'RGBA' else img.paste(lay, (x0, y0), lay)


def marey(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, rim=(255, 214, 160), rim_dir=(-1, -.4),
          aura=(255, 200, 140), aura_a=.35, lbl_dy=0, lbl_txt='MAREY · 1894', idle=1.0):
    """Etienne-Jules Marey: a white stickman with a full beard, 1890s jacket and waistcoat."""
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=aura, aura_alpha=aura_a, rim=rim, rim_dir=rim_dir,
              rim_w=12, bphase=.4, idle=idle, **MAREY_KW)
    beard(img, g, look)
    if label_on and not HIDE_UI:
        hx, hy = g['head']
        label(img, lbl_txt, min(W - 200, max(200, hx)), hy - g['R'] * 1.7 - 80 + lbl_dy, MAREY_COL, size=int(52 * max(.9, min(1.1, s / .6))))
    return g


# ---------------------------------------------------------------- the 1894 lab (cached static layers)
_cache = {}


def _cached(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]


def eiffel(d, x, base, h, col):
    """A small far Eiffel Tower silhouette (finished 1889)."""
    w = h * .42
    d.polygon([(x - w / 2, base), (x - w * .12, base - h * .45), (x - w * .05, base - h * .92), (x, base - h),
               (x + w * .05, base - h * .92), (x + w * .12, base - h * .45), (x + w / 2, base),
               (x + w * .28, base), (x, base - h * .2), (x - w * .28, base)], fill=col)
    d.rectangle([x - w * .2, base - h * .47, x + w * .2, base - h * .43], fill=col)
    d.rectangle([x - w * .1, base - h * .72, x + w * .1, base - h * .7], fill=col)


def _wall_layer():
    """Back wall (plaster + wainscot), the tall window onto Paris roofs, a shelf of jars. 1280 wide (parallax)."""
    Wl = W + 200
    img = vgrad([(0, (74, 52, 46)), (.5, (96, 66, 52)), (1, (58, 40, 36))], Wl, H)
    d = ImageDraw.Draw(img)
    # plaster mottling
    rng = np.random.default_rng(5)
    m = mask(Wl, H); dm = ImageDraw.Draw(m)
    for _ in range(90):
        x, y, r = rng.uniform(0, Wl), rng.uniform(0, 1300), rng.uniform(30, 120)
        dm.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=int(rng.uniform(10, 40)))
    fill_mask(img, m, (120, 86, 66), 1.0, blur=30)
    # wainscot
    d.rectangle([0, 1200, Wl, 1520], fill=(70, 42, 30))
    for x in range(-20, Wl, 170):
        d.rectangle([x + 18, 1230, x + 150, 1490], fill=(84, 52, 36), outline=(44, 26, 20), width=5)
        d.line([(x + 24, 1236), (x + 144, 1236)], fill=(120, 80, 54), width=3)
    d.rectangle([0, 1186, Wl, 1206], fill=(110, 72, 48), outline=INK, width=4)
    # window (left): arched, mullions, Paris roofs and the far tower
    wx0, wx1, wy0, wy1 = 90, 420, 200, 980
    win = vgrad([(0, (150, 176, 214)), (.55, (246, 214, 170)), (1, (252, 196, 150))], wx1 - wx0, wy1 - wy0)
    dw = ImageDraw.Draw(win)
    eiffel(dw, 238, 640, 330, (150, 132, 150))
    rng = np.random.default_rng(9)
    for row, (yb, col, hh) in enumerate(((610, (128, 120, 146), 70), (680, (98, 92, 118), 90), (760, (72, 66, 90), 120))):
        x = -30
        while x < wx1 - wx0 + 30:
            w_ = rng.uniform(60, 120); hb = rng.uniform(.6, 1.2) * hh
            dw.polygon([(x, yb), (x + w_ * .12, yb - hb), (x + w_ * .88, yb - hb), (x + w_, yb)], fill=col)   # mansard
            for c in range(int(rng.integers(1, 3))):                                                        # chimney pots
                cx = x + rng.uniform(.2, .8) * w_
                dw.rectangle([cx - 8, yb - hb - 26, cx + 8, yb - hb], fill=lerp(col, (40, 30, 40), .3))
            if row == 2:
                for wi in range(2):
                    wxx = x + w_ * (.3 + .35 * wi)
                    dw.rectangle([wxx - 7, yb - hb * .55, wxx + 7, yb - hb * .3], fill=(255, 214, 140))
            x += w_ - 6
    dw.rectangle([0, 760, wx1 - wx0, wy1 - wy0], fill=(64, 58, 82))
    am = mask(wx1 - wx0, wy1 - wy0); da = ImageDraw.Draw(am)
    da.rectangle([0, 165, wx1 - wx0, wy1 - wy0], fill=255); da.ellipse([0, 0, wx1 - wx0, 330], fill=255)
    img.paste(win, (wx0, wy0), am)
    # frame + mullions
    d.arc([wx0 - 14, wy0 - 14, wx1 + 14, wy0 + 344], 180, 360, fill=(46, 30, 24), width=30)
    d.rectangle([wx0 - 28, wy0 + 165, wx0, wy1 + 20], fill=(46, 30, 24)); d.rectangle([wx1, wy0 + 165, wx1 + 28, wy1 + 20], fill=(46, 30, 24))
    d.rectangle([wx0 - 40, wy1, wx1 + 40, wy1 + 34], fill=(120, 80, 54), outline=INK, width=5)
    d.rectangle([(wx0 + wx1) / 2 - 8, wy0 + 10, (wx0 + wx1) / 2 + 8, wy1], fill=(46, 30, 24))
    for yy in (wy0 + 330, wy0 + 560):
        d.rectangle([wx0, yy - 7, wx1, yy + 7], fill=(46, 30, 24))
    # shelf with jars and a skull-free specimen of course: jars, books
    d.rectangle([0, 1060, 300, 1080], fill=(120, 78, 50), outline=INK, width=4)
    for i, (x, w_, h_, c) in enumerate(((20, 40, 90, (120, 70, 50)), (64, 36, 110, (60, 80, 110)), (104, 30, 80, (140, 120, 60)),
                                        (180, 60, 70, (170, 200, 190)), (250, 44, 96, (200, 170, 120)))):
        if i < 3: d.rectangle([x, 1060 - h_, x + w_, 1060], fill=c, outline=INK, width=4)
        else:
            d.rounded_rectangle([x, 1060 - h_, x + w_, 1060], 12, fill=c, outline=INK, width=4)
            d.rectangle([x + 8, 1060 - h_ - 12, x + w_ - 8, 1060 - h_ + 4], fill=(90, 70, 60), outline=INK, width=3)
    return img


def _velvet_layer(x0=300, x1=1060, y0=210, y1=1560):
    """Marey's black velvet backdrop on a brass rod: deep black with soft folds and a faint sheen."""
    w, h = x1 - x0, y1 - y0
    lay = layer(w + 40, h + 80)
    base = np.zeros((h, w, 3), np.float32) + np.array((15, 13, 19), np.float32)
    xs = np.arange(w)
    fold = .5 + .5 * np.sin(xs / w * math.pi * 7.3 + np.sin(xs / 37.0) * .6)
    fold = fold ** 3
    base += fold[None, :, None] * np.array((22, 18, 28), np.float32)
    ys = np.arange(h)[:, None, None]
    base *= (1 - .25 * (ys / h))
    a = np.dstack([base.clip(0, 255), np.full((h, w, 1), 255)]).astype(np.uint8)
    v = Image.fromarray(a, 'RGBA')
    # scalloped top (hanging from rings) and a pooled hem
    m = mask(w, h); dm = ImageDraw.Draw(m); dm.rectangle([0, 18, w, h - 30], fill=255)
    for i in range(0, w, 60): dm.ellipse([i - 4, 0, i + 64, 40], fill=255)
    for i in range(0, w, 90): dm.ellipse([i - 20, h - 70, i + 110, h], fill=255)
    lay.paste(v, (20, 30), m)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 16, w + 40, 34], 9, fill=(196, 150, 70), outline=INK, width=4)
    for i in range(30, w, 60):
        d.ellipse([i, 22, i + 26, 48], outline=(210, 170, 90), width=5)
    return lay, (x0 - 20, y0 - 30)


def _floor_layer(y0=1500):
    img = vgrad([(0, (96, 62, 42)), (1, (140, 92, 58))], W + 200, H - y0)
    d = ImageDraw.Draw(img); vx = (W + 200) / 2
    for k in range(-14, 15):
        xb = vx + k * 150
        d.line([(vx + k * 22, 0), (xb, H - y0)], fill=(66, 40, 28), width=4)
    for yy in (40, 110, 210, 340):
        d.line([(0, yy), (W + 200, yy)], fill=(80, 50, 34), width=3)
    return img


def chrono_camera(img, x, y, u, s=1.0, spin=1.0, flash_k=0.0):
    """Marey's chronophotographic camera: a wooden box on a tripod, brass lens pointing left, a slotted disc
    shutter that spins (Moves: the disc turns with u*spin; flash_k lights the lens)."""
    d = ImageDraw.Draw(img)
    for lx, ly in ((-90, 400), (10, 430), (110, 400)):              # tripod
        d.line([(x + 10 * s, y + 120 * s), (x + lx * s, y + ly * s)], fill=INK, width=int(22 * s))
        d.line([(x + 10 * s, y + 120 * s), (x + lx * s, y + ly * s)], fill=(120, 80, 48), width=int(13 * s))
    d.rounded_rectangle([x - 130 * s, y - 100 * s, x + 150 * s, y + 120 * s], 14 * s, fill=(150, 96, 56), outline=INK, width=int(7 * s))
    d.rounded_rectangle([x - 112 * s, y - 84 * s, x + 132 * s, y - 40 * s], 8 * s, fill=(176, 118, 70))
    for yy in (-30, 40):
        d.line([(x - 130 * s, y + yy * s), (x + 150 * s, y + yy * s)], fill=(110, 70, 40), width=int(4 * s))
    # brass lens tube to the left
    d.rounded_rectangle([x - 230 * s, y - 34 * s, x - 125 * s, y + 46 * s], 10 * s, fill=(206, 164, 76), outline=INK, width=int(6 * s))
    d.rectangle([x - 206 * s, y - 34 * s, x - 196 * s, y + 46 * s], fill=(160, 120, 50))
    d.ellipse([x - 252 * s, y - 40 * s, x - 212 * s, y + 52 * s], fill=(40, 46, 60), outline=INK, width=int(6 * s))
    d.ellipse([x - 244 * s, y - 26 * s, x - 226 * s, y - 4 * s], fill=(120, 140, 170))            # glass reflection
    if flash_k > 0:
        m = mask(); ImageDraw.Draw(m).ellipse([x - 262 * s, y - 50 * s, x - 202 * s, y + 62 * s], fill=255)
        glow(img, m, (255, 240, 200), .9 * flash_k, blur=26, add=True)
    lens_glint(img, x - 235 * s, y - 14 * s, .45 + .25 * math.sin(u * 2.3) + 1.2 * flash_k, s)
    # the disc shutter on top
    cx, cy, r = x + 20 * s, y - 150 * s, 95 * s
    d.line([(cx, cy), (cx, y - 100 * s)], fill=INK, width=int(14 * s))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(60, 56, 64), outline=INK, width=int(7 * s))
    for k in range(12):
        a = u * spin * 6.0 + k * math.pi / 6
        p1 = (cx + math.cos(a) * r * .55, cy + math.sin(a) * r * .55); p2 = (cx + math.cos(a) * r * .86, cy + math.sin(a) * r * .86)
        d.line([p1, p2], fill=(230, 210, 160), width=int(9 * s))
    d.ellipse([cx - 16 * s, cy - 16 * s, cx + 16 * s, cy + 16 * s], fill=(206, 164, 76), outline=INK, width=int(4 * s))


def lens_glint(img, x, y, k, s=1.0):
    """A small star glint on glass (additive): a soft core + a long horizontal and a short vertical streak."""
    if k <= 0: return
    lay = layer(); d = ImageDraw.Draw(lay)
    L = 120 * s * min(1.6, k)
    for (dx, dy), w_ in (((L, 0), 5), ((0, L * .45), 4), ((L * .3, L * .3), 3), ((L * .3, -L * .3), 3)):
        d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(255, 244, 214, int(min(255, 200 * k))), width=max(2, int(w_ * s)))
    lay = lay.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(lay)
    radial(img, x, y, 70 * s, (255, 236, 190), min(.9, .5 * k), 1.8)


def low_angle(img, a=110, sy=.9, fill=(14, 10, 14)):
    """Fake a low camera: verticals converge upward (keystone) and the floor sinks toward the bottom."""
    def coeffs(src, dst):
        A = []; Bv = []
        for (x, y), (X, Y) in zip(dst, src):
            A.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y]); Bv += [X, Y]
        return np.linalg.solve(np.array(A, float), np.array(Bv, float)).tolist()
    src = [(-a, 0), (W + a, 0), (W, H * sy), (0, H * sy)]
    dst = [(0, 0), (W, 0), (W, H), (0, H)]
    base = Image.new('RGBA', img.size, fill + (255,))
    base.alpha_composite(img.transform(img.size, Image.PERSPECTIVE, coeffs(src, dst), Image.BICUBIC))
    return base


def stool(img, cx, gy, w=230, h=150):
    d = ImageDraw.Draw(img)
    for s_ in (-1, 1):
        d.line([(cx + s_ * w * .3, gy + 10), (cx + s_ * w * .45, gy + h)], fill=INK, width=24)
        d.line([(cx + s_ * w * .3, gy + 10), (cx + s_ * w * .45, gy + h)], fill=(120, 80, 50), width=12)
    d.line([(cx - w * .38, gy + h * .6), (cx + w * .38, gy + h * .6)], fill=INK, width=16)
    d.rounded_rectangle([cx - w / 2, gy - 6, cx + w / 2, gy + 26], 10, fill=(150, 100, 62), outline=INK, width=6)


def mattress(img, cx, y, w=520, h=86):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - w / 2, y - h / 2 + 10, cx + w / 2, y + h / 2 + 10], h / 2, fill=(40, 26, 18))
    d.rounded_rectangle([cx - w / 2, y - h / 2, cx + w / 2, y + h / 2], h / 2, fill=(206, 176, 112), outline=INK, width=6)
    d.rounded_rectangle([cx - w / 2 + 16, y - h / 2 + 8, cx + w / 2 - 16, y - 6], h / 3, fill=(226, 200, 140))
    for k in range(1, 6):
        x = cx - w / 2 + k * w / 6
        d.line([(x, y - h / 2 + 10), (x, y + h / 2 - 10)], fill=(150, 120, 70), width=3)


def lab(img, u, cam=0.0, light=1.0, velvet_glow=(560, 860), camera=True, cam_flash=0.0, spin=1.0, mat=True, rays=1.0, cam_xy=(900, 1170),
        warm=0.0):
    """The 1894 lab: wall + window (far, slow), velvet backdrop (mid), floor + mattress, the camera (near, fast)."""
    wall = _cached('wall', _wall_layer)
    img.alpha_composite(wall, (int(-100 + cam * .3), 0))
    vel, (vx, vy) = _cached('velvet', _velvet_layer)
    img.alpha_composite(vel, (int(vx + cam * .55), vy))
    floor = _cached('floor', _floor_layer)
    img.alpha_composite(floor, (int(-100 + cam * .8), 1500))
    haze(img, 1440, 1600, (60, 40, 30), .5)
    if rays > 0:
        kit.light_rays(img, 250 + cam * .3, 420, (255, 222, 170), n=7, alpha=.16 * rays * light, spread=(10, 70), length=1900, seed=3,
                       phase=1.5 * math.sin(u * .4), blur=26)
    if warm > 0:                                     # late-afternoon sun through the window vs the black velvet
        radial(img, 230 + cam * .3, 560, 520, (255, 190, 110), .42 * warm, 1.3)
        kit.light_rays(img, 200 + cam * .3, 380, (255, 200, 130), n=5, alpha=.22 * warm, spread=(30, 60), length=1700, seed=9,
                       phase=1.2 * math.sin(u * .3), blur=34)
        radial(img, 420 + cam * .8, 1620, 420, (255, 180, 100), .3 * warm, 1.4)
        lay = layer(); ImageDraw.Draw(lay).rectangle([560 + cam * .55, 200, 1080, 1480], fill=(4, 6, 14, int(90 * warm)))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(60)))
    if velvet_glow:
        radial(img, velvet_glow[0] + cam * .55, velvet_glow[1], 520, (255, 214, 160), .22 * light, 1.6)
    radial(img, 600 + cam * .8, 1640, 560, (255, 200, 140), .2, 1.5)
    if mat: mattress(img, 600 + cam * .8, 1600)
    if camera: chrono_camera(img, cam_xy[0] + cam * 1.1, cam_xy[1], u, .9, spin, cam_flash)
    dust(img, 4, 36, (300, 300, 1000, 1500), (255, 236, 200), 120, size=(2, 5), t=u)


# ---------------------------------------------------------------- the film strip motif (sepia, sprockets)
def sepia(im, lo=SEPIA_D, hi=SEPIA):
    g = ImageOps.grayscale(im.convert('RGB'))
    g = ImageOps.autocontrast(g, cutoff=1)
    out = ImageOps.colorize(g, lo, hi).convert('RGBA')
    if im.mode == 'RGBA': out.putalpha(im.split()[3])
    return out


def film_frame_img(key, w, h, cat_kw, cy=.5, s=None, ghost=None):
    """One sepia chronophotograph frame: the cat on black velvet (cached)."""
    def make():
        im = Image.new('RGBA', (w * 2, h * 2), (18, 14, 18, 255))
        radial(im, w, h * .9, w * 1.3, (90, 70, 60), .5, 1.4)
        C.put_cat(im, w, h * 2 * cy, (s or w * .42) * 2, ink_w=6, **cat_kw)
        im = sepia(im).resize((w, h), Image.LANCZOS)
        d = ImageDraw.Draw(im); rng = np.random.default_rng(len(key) * 7 + w)
        for _ in range(3):                                           # scratches
            x = rng.uniform(0, w); d.line([(x, 0), (x + rng.uniform(-6, 6), h)], fill=SEPIA + (60,), width=1)
        anim.vignette(im, .55, (30, 18, 10), .7, .7)
        return im
    return _cached(('ff', key, w, h), make)


def strip_layer(frames, fw, fh, gap=26, side=46, bg=(28, 20, 16), highlight=None):
    """A vertical celluloid strip: frames stacked with sprocket holes down both sides. Returns RGBA."""
    n = len(frames)
    Wd = fw + 2 * side; Hd = n * (fh + gap) + gap
    lay = Image.new('RGBA', (Wd, Hd), bg + (255,))
    d = ImageDraw.Draw(lay)
    for i, im in enumerate(frames):
        y = gap + i * (fh + gap)
        lay.alpha_composite(im, (side, y))
        d.rectangle([side - 3, y - 3, side + fw + 3, y + fh + 3], outline=(10, 8, 8), width=4)
    hs = 22
    for y in range(10, Hd, 44):
        for x in (side / 2, Wd - side / 2):
            d.rounded_rectangle([x - hs / 2, y, x + hs / 2, y + hs * 1.1], 5, fill=(240, 226, 196))
    d.rectangle([0, 0, Wd - 1, Hd - 1], outline=INK, width=6)
    return lay


def paste_rot(img, lay, cx, cy, angle=0.0, s=1.0, alpha=1.0):
    anim.scaled_paste(img, lay, cx, cy, s, angle, alpha)


# ---------------------------------------------------------------- shared cat helpers
FALL_KW = dict()


def ghost_trail(img, path, n=5, every=.33, u=0.0, s=150, alpha=.32, start=0.0, **base):
    """Chronophotograph ghosts: earlier positions of the cat, faint and sepia. path(t) -> (x, y, kw)."""
    for k in range(n, 0, -1):
        t = u - k * every
        if t < start: continue
        x, y, kw = path(t)
        lay, (ox, oy), _ = C.render_cat(x, y, s, **{**base, **kw})
        lay = sepia(lay, (60, 40, 30), (250, 226, 180))
        lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha * (1 - k / (n + 1.5)))))
        C._paste(img, lay, ox, oy)


def arc_arrow(img, cx, cy, rx, ry, a0, a1, col, w=16, head=40, alpha=255, front_only=False):
    """An elliptical rotation arrow from angle a0 to a1 (rad) around (cx, cy), arrowhead at a1."""
    if abs(a1 - a0) < .05: return
    lay = layer(); d = ImageDraw.Draw(lay)
    n = max(8, int(abs(a1 - a0) * 18))
    pts = [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    d.line(pts, fill=INK + (alpha,), width=w + 10, joint='curve')
    d.line(pts, fill=col + (alpha,), width=w, joint='curve')
    p, q = pts[-1], pts[-2]
    ang = math.atan2(p[1] - q[1], p[0] - q[0])
    tip = (p[0] + math.cos(ang) * head * .6, p[1] + math.sin(ang) * head * .6)
    l = (p[0] + math.cos(ang + 2.5) * head, p[1] + math.sin(ang + 2.5) * head)
    r = (p[0] + math.cos(ang - 2.5) * head, p[1] + math.sin(ang - 2.5) * head)
    d.polygon([tip, l, r], fill=col + (alpha,), outline=INK + (alpha,), width=5)
    img.alpha_composite(lay)


def straight_arrow(img, a, b, col, w=22, head=54, alpha=255):
    lay = layer(); d = ImageDraw.Draw(lay)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    e = (b[0] - math.cos(ang) * head * .7, b[1] - math.sin(ang) * head * .7)
    d.line([a, e], fill=INK + (alpha,), width=w + 12); d.line([a, e], fill=col + (alpha,), width=w)
    l = (b[0] - math.cos(ang - .5) * head, b[1] - math.sin(ang - .5) * head)
    r = (b[0] - math.cos(ang + .5) * head, b[1] - math.sin(ang + .5) * head)
    d.polygon([b, l, r], fill=col + (alpha,), outline=INK + (alpha,), width=6)
    img.alpha_composite(lay)


def opening_title(img, u, alpha=1.0):
    if HIDE_UI: return
    lay, _ = tlayer('open', [('1894', (255, 214, 120), 230)], 230)
    anim.scaled_paste(img, lay, 540, 300, 1.0 + .006 * math.sin(u * 2.4), alpha=alpha)


_tl = {}
def tlayer(key, lines, size):
    if key not in _tl:
        _tl[key] = anim.text_layer(lambda l: title(l, lines, 60, size=size), W,
                                   int(sum((x[2] if len(x) > 2 else size) for x in lines) * 1.3 + 140))
    return _tl[key]


def fall_path(t, x0=560, y0=840, y1=1480, t_land=3.5, rot0=0.0):
    """Slow-motion fall from (x0, y0) landing at t_land (eased like gravity, then a soft settle)."""
    k = max(0.0, min(1.0, t / t_land))
    y = y0 + (y1 - y0) * (k ** 1.7)
    return x0 + 20 * math.sin(t * .8), y


# ---------------------------------------------------------------- s01: frame 0 = the hook
CAT0 = dict(phf=math.pi, phb=math.pi, tuckf=.5, tuckb=.5, bend=12)


def s01_frame(u, w, D=4.5, cue=None, loop=False):
    """The cat upside down in mid-air in Marey's lab, slow motion; Marey's hands just opened above it; on 'filmed'
    the camera ticks and a sepia film strip of the drop unrolls along the bottom. w = the world clock."""
    if loop: anim.NOW = 0.0                         # the loop frame: Marey's idle motion at the film's start clock
    cue = cue or (lambda i: [.06, .3, .84, 1.02, 1.68, 1.92, 2.34, 2.88, 3.06, 3.35, 3.65, 4.13][min(i, 11)] - 0.0)
    cam = 6 * math.sin(w * .5)
    img = Image.new('RGBA', (W, H))
    t_film = cue(10) - .15
    fk = smooth(seg(u, t_film, t_film + .25)) * (1 - smooth(seg(u, t_film + .3, t_film + .9)))
    lab(img, w, cam, cam_flash=fk, spin=1.0 + 2.5 * smooth(seg(u, t_film - .2, t_film + .2)), cam_xy=(950, 1330), warm=.8)
    G = {}
    # Marey (left): hands up and open, just let go
    kr = smooth(seg(u, 0, .8))
    pose = mix(dict(POSES['stand'], armL=(165, 150), armR=(140, 150)), dict(POSES['stand'], armL=(172, 160), armR=(148, 160)), kr)
    pose = add(pose, armL=(3 * math.sin(w * 2.2), 4 * math.sin(w * 2.2)))
    stool(img, 230 + cam * .9, 1500)
    G['m'] = marey(img, w, pose, 'surprised', 230 + cam * .9, 1500, .74, look=.7, lean=8, label_on=False)
    # the cat: hovering (slow motion), slowly sinking, bending a little, tail swaying
    y = 990 + 26 * smooth(seg(u, 0, D)) + 6 * math.sin(w * 1.3)
    kw = dict(CAT0, bend=12 + 4 * math.sin(w * .9), tail_ph=w * 1.4, rot=-4 + 2 * math.sin(w * .7))
    radial(img, 660 + cam * .6, y, 320, (255, 230, 190), .28, 1.5)
    C.put_cat(img, 660 + cam * .6, y, 200, **kw)
    # motion streaks above the cat (it is falling)
    d = ImageDraw.Draw(img)
    for i, x in enumerate((540, 610, 680, 750)):
        a = int(90 + 40 * math.sin(w * 3 + i))
        lay = layer(); ImageDraw.Draw(lay).line([(x + 40 + cam * .6, y - 360), (x + 40 + cam * .6, y - 240)], fill=(255, 240, 210, a), width=6)
        img.alpha_composite(lay)
    # the film strip unrolls from the camera along the bottom on 'filmed'
    kf = smooth(seg(u, t_film, t_film + .8))
    if kf > 0 or loop:
        film_strip_bottom(img, u if not loop else 0, kf if not loop else 0)
    img = finish(img, w, 1.0 + .04 * smooth(u / D), 560, 900, vig=(.42, (12, 8, 14)))
    if not HIDE_UI:
        opening_title(img, u)
        label(img, 'PARIS', 540, 450, MAREY_COL, size=52)
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(0, 150, W, 560), (380, 700, 940, 1200)]}


def film_strip_bottom(img, u, k):
    """A horizontal sepia strip sliding out from the camera: 6 frames of the upside-down cat."""
    if k <= 0: return
    def frames():
        out = []
        for i in range(6):
            p = 0.0 if i < 4 else (i - 3) * .12
            kw = dict(C.righting(p)); kw.update(rot=0)
            out.append(film_frame_img(('bot', i), 170, 130, kw, cy=.45 + i * .02, s=44))
        return out
    fr = _cached('bot_frames', frames)
    lay = _cached('bot_strip', lambda: strip_layer(fr, 170, 130, gap=18, side=34).rotate(90, expand=True))
    x = 1100 - k * (lay.width + 40) + 30 * math.sin(u * .5)
    img.alpha_composite(lay, (int(x), 1600)) if x > -lay.width else None


def s01(u, D, cue):
    return s01_frame(u, u, D, cue)


# ---------------------------------------------------------------- s02: it flips and lands (slow motion + ghosts)
def s02(u, D, cue):
    cam = -10 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    lab(img, u + 4.5, cam, spin=3.0, mat=False, cam_xy=(930, 1230))
    img = low_angle(img)                             # LOW ANGLE: under the falling cat, the floor sinks, verticals converge
    radial(img, 560, 380, 700, (255, 220, 170), .18, 1.4)
    mattress(img, 560 + cam * .8, 1690, w=700, h=120)
    t0, t1 = cue(1), cue(15) - .05                   # starts turning on 'down,' ... lands on 'feet.'
    def path(t):
        p = smooth(seg(t, t0, t1 - .25))
        x = 560 + cam * .6 + 10 * math.sin(t)
        y = 700 + (1500 - 700) * (seg(t, 0, t1) ** 1.6)
        kw = dict(C.righting(p)); kw['tail_ph'] = t * 2
        return x, y, kw
    G = {}
    kreact = out_back(seg(u, cue(9), cue(9) + .4), 1.5)
    pose = mix(dict(POSES['stand'], armL=(150, 165), armR=(120, 150)), dict(POSES['stand'], armL=(40, 120), armR=(-50, -130)), kreact)
    G['m'] = marey(img, u, pose, 'surprised', 190 + cam * .9, 1990, .92, look=.55, lean=6 * kreact, label_on=True)
    ghost_trail(img, path, n=5, every=.34, u=u, s=190, alpha=.4, start=.2)
    if u < t1:
        x, y, kw = path(u)
        radial(img, x, y, 320, (255, 230, 190), .22, 1.5)
        C.put_cat(img, x, y, 190, **kw)
    else:                                            # landed: a squash and settle on the mattress
        v = u - t1
        sq = damp(v, .08, 7, 16)
        kw = dict(phf=0, phb=0, tuckf=.3, tuckb=.3, bend=-6 * (1 - smooth(v / .5)), tail_ph=u * 2)
        x = 560 + cam * .6 + 10 * math.sin(t1)
        C.put_cat(img, x, 1500 + 36 * sq, 190, legs_k=1 - .15 * max(0, sq) / .08, **kw)
        if v < .5:
            dd = ImageDraw.Draw(img)
            for s_ in (-1, 1):
                for j in range(3):
                    r = 60 + 160 * v
                    dd.line([(x + s_ * (190 + r * .6), 1650 - j * 20), (x + s_ * (240 + r), 1630 - j * 34)], fill=(255, 236, 200), width=7)
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 560, 1200, vig=(.4, (12, 8, 14)))
    if not HIDE_UI:
        chip(img, 'NOTHING TO PUSH ON', (70, 70, 96), 540, 300, u, cue(3) - .1, size=58)
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(200, 240, 880, 360)]}


# ---------------------------------------------------------------- s03: BROKE PHYSICS?
def s03(u, D, cue):
    cam = 8 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    lab(img, u + 9, cam, camera=False, warm=1.0, velvet_glow=None)
    G = {}
    C.put_cat(img, 800 + cam * .8, 1460, 170, phf=0, phb=0, tuckf=.4, tuckb=.4, bend=-4, tail_ph=u * 1.5, head_tilt=.15 * math.sin(u * 1.2))
    radial(img, 360 + cam, 1080, 420, (255, 200, 140), .3, 1.5)          # warm key on his face (CLOSE-UP)
    G['m'] = marey(img, u, mix(dict(POSES['think']), dict(POSES['stand'], armL=(120, 150), armR=(-120, -150)), out_back(seg(u, cue(4) - .2, cue(4) + .2), 1.6)), 'surprised', 360 + cam, 2380, 1.42, look=.5, lean=-5 + 2 * math.sin(u * 2), label_on=False)
    zf = 1.04 + .04 * smooth(u / D)
    img = finish(img, u, zf, 480, 1150, vig=(.45, (12, 8, 14)))
    t_b, t_p = cue(4) - .08, cue(8) - .08
    if not HIDE_UI:
        stitle(img, 's03', [('BREAKING A LAW', 'white', 104), ('OF PHYSICS?', (255, 120, 90), 150)], 230, u, t_b, stagger=t_p - t_b)
        if u > t_p:                                           # crack through the title on 'physics'
            k = smooth(seg(u, t_p, t_p + .15))
            d = ImageDraw.Draw(img)
            pts = [(140, 470), (330, 420), (420, 500), (560, 400), (690, 470), (820, 390), (950, 460)]
            n = max(2, int(len(pts) * k))
            d.line(pts[:n], fill=INK, width=14); d.line(pts[:n], fill=(255, 246, 230), width=5)
    sx, sy = shake(u, t_p, 12, .35)
    if sx or sy: img = anim.camera(img, 1.0, None, None, sx, sy)
    flash(img, u, t_p, .2, .35)
    hx, hy = G['m']['head']
    return img, {'faces': [face_box({'head': (480 + (hx - 480) * zf, 1150 + (hy - 1150) * zf), 'R': G['m']['R'] * zf}, 1.3)],
                 'avoid': [(0, 160, W, 700)]}


# ---------------------------------------------------------------- s04: nothing falling starts to spin on its own
def block_layer(s=1.0):
    def make():
        lay = layer(300, 300); d = ImageDraw.Draw(lay)
        d.rounded_rectangle([40, 70, 260, 230], 14, fill=(196, 140, 80), outline=INK, width=8)
        d.rounded_rectangle([52, 82, 248, 120], 10, fill=(222, 170, 104))
        d.line([(80, 160), (200, 160)], fill=INK, width=16); d.polygon([(190, 130), (236, 160), (190, 190)], fill=INK)
        d.line([(80, 160), (196, 160)], fill=(255, 230, 120), width=8); d.polygon([(196, 140), (226, 160), (196, 180)], fill=(255, 230, 120))
        return lay
    return _cached('block', make)


def s04(u, D, cue):
    cam = -8 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    lab(img, u + 13, cam, velvet_glow=(640, 900), camera=False)
    img.alpha_composite(Image.new('RGBA', img.size, (20, 40, 80, 70)))
    radial(img, 650, 900, 600, (170, 210, 255), .25, 1.4)
    G = {}
    G['m'] = marey(img, u, dict(POSES['think']), 'thinking', 190 + cam, 1760, .7, look=.6, lean=2 * math.sin(u * 1.5), label_on=False)
    blk = block_layer()
    # the block drops straight; ghosts every 0.28 s all point the same way (no spin)
    t_drop = .15
    def ypos(t): return 520 + 900 * (seg(t, t_drop, t_drop + 1.9) ** 1.5)
    for k in range(6, 0, -1):
        t = u - k * .3
        if t < t_drop: continue
        paste_rot(img, sepia(blk, (60, 40, 30), (250, 226, 180)), 650 + cam * .55, ypos(t), 0, .9, .35 * (1 - k / 7.5))
    paste_rot(img, blk, 650 + cam * .55, ypos(u), 0, .9)
    # a crossed-out spin arrow beside it
    if not HIDE_UI:
        k = pop(u, cue(5) - .1, .3, 1.8)
        if k > 0:
            cx, cy = 880 + cam * .55, 720
            arc_arrow(img, cx, cy, 80 * k, 80 * k, -2.6, 1.9, (255, 210, 90), w=14, head=34)
            if u > cue(5) + .2:
                draw_x(img, cx, cy, 90, smooth(seg(u, cue(5) + .2, cue(5) + .6)) * 2, w=20)
    img = finish(img, u, 1.08, 560, 1000, vig=(.4, (12, 8, 14)))
    if not HIDE_UI:
        stitle(img, 's04', [('NO PUSH,', 'white', 110), ('NO SPIN', GOLD, 150)], 200, u, cue(3) - .1, stagger=cue(5) - cue(3))
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(0, 160, W, 500)]}


# ---------------------------------------------------------------- s05: the obvious answer: it pushed off his hands?
def s05(u, D, cue):
    cam = 10 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    lab(img, u + 16, cam * .5, velvet_glow=(600, 900), camera=True, warm=1.3)
    G = {}
    t_p = cue(5) - .05
    kp = smooth(seg(u, t_p, t_p + .5))
    # Marey (left, on the stool) holds the cat up by its sides, upside down; on 'pushed' the imagined kick-off
    stool(img, 250 + cam, 1600)
    pose = dict(POSES['stand'], armL=(150, 140), armR=(110, 120))
    G['m'] = marey(img, u, pose, 'neutral' if u < t_p else 'surprised', 250 + cam, 1600, .8, look=.6, lean=5, label_on=False)
    hx, hy = G['m']['hands']['L'][:2]
    cx, cy = 560 + cam + 120 * kp, 820 - 60 * kp
    kw = dict(phf=math.pi + 1.3 * kp, phb=math.pi + 1.0 * kp, tuckf=.6 - .5 * kp, tuckb=.7 - .6 * kp, bend=10, tail_ph=u * 2, rot=-8 * kp)
    if kp > 0:                                        # 'what if': a dashed ghost at the start position
        lay, (ox, oy), _ = C.render_cat(560 + cam, 820, 185, **dict(kw, phf=math.pi, phb=math.pi, rot=0))
        lay = sepia(lay, (40, 40, 60), (200, 210, 240)); lay.putalpha(lay.split()[3].point(lambda v: int(v * .3)))
        C._paste(img, lay, ox, oy)
    C.put_cat(img, cx, cy, 185, **kw)
    if not HIDE_UI and kp > 0:
        for i, (a, b) in enumerate((((hx + 10, hy + 10), (cx - 170, cy + 70)), ((hx + 40, hy + 80), (cx - 60, cy + 150)))):
            k = out_back(seg(u, t_p + i * .12, t_p + .4 + i * .12), 1.6)
            if k > 0:
                bb = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
                straight_arrow(img, a, bb, (255, 196, 70), w=22, head=56)
        arc_arrow(img, cx, cy, 300, 140, -.4, -.4 + 1.8 * kp, (255, 196, 70), w=14, head=40, alpha=int(230 * kp))
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 540, 900, vig=(.42, (12, 8, 14)))
    if not HIDE_UI:
        stitle(img, 's05', [('PUSHED OFF', 'white', 120), ('HIS HANDS?', (255, 196, 70), 130)], 180, u, t_p - .05, stagger=cue(8) - t_p)
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(0, 150, W, 480), (cx - 340, cy - 220, cx + 340, cy + 220)]}


# ---------------------------------------------------------------- s06: the photos: it dropped straight, no spin
def marey_strip_frames():
    out = []
    for i in range(10):
        p = 0.0 if i < 4 else min(1.0, (i - 3) * .15)
        kw = dict(C.righting(p)); kw.update(rot=0, tail_ph=i * .6)
        out.append(film_frame_img(('s06', i), 300, 210, kw, cy=.36 + i * .028, s=78))
    return out


def s06(u, D, cue):
    cam = 0
    img = Image.new('RGBA', (W, H))
    lab(img, u + 20, 0, velvet_glow=(540, 900), camera=False, mat=False, light=.7)
    # darken toward a light-table mood
    img.alpha_composite(Image.new('RGBA', img.size, (10, 8, 12, 120)))
    radial(img, 540, 900, 760, (255, 214, 150), .35, 1.4)
    fr = _cached('s06_frames', marey_strip_frames)
    lay = _cached('s06_strip', lambda: strip_layer(fr, 300, 210))
    scroll = 60 - 260 * smooth(seg(u, 0, D))
    x0 = 540 - lay.width / 2
    sub = layer(); sub.alpha_composite(lay, (int(x0), int(150 + scroll)))
    sub = sub.rotate(-4, resample=Image.BICUBIC, center=(540, 960))
    img.alpha_composite(sub)
    G = {}
    G['m'] = marey(img, u, dict(POSES['hold']), 'thinking' if u < cue(10) else 'surprised', 905, 1950, .9, look=-.6, lean=-3,
                   label_on=False, rim_dir=(-1, -.4))
    def fpos(i):                                     # frame centre in screen px (approx, with the rotation)
        y = 150 + scroll + 26 + i * (210 + 26) + 105
        a = math.radians(4); x = 540 + (y - 960) * math.sin(a); yy = 960 + (y - 960) * math.cos(a)
        return x, yy
    if not HIDE_UI:
        t_ns = cue(8) - .1
        for i in range(4):
            k = pop(u, t_ns + i * .08, .25, 2.2)
            if k > 0:
                x, y = fpos(i); d = ImageDraw.Draw(img); r = 34 * k
                d.ellipse([x + 170 - r, y - r, x + 170 + r, y + r], fill=GOOD, outline=INK, width=5)
                d.line([(x + 170 - r * .45, y), (x + 170 - r * .1, y + r * .4), (x + 170 + r * .5, y - r * .4)], fill='white', width=int(9 * k))
        chip(img, 'NO SPIN AT FIRST', GOOD, 540, 250, u, t_ns, size=62)
        t_mid = cue(11) - .1
        if u > t_mid:
            x, y = fpos(4); k = out_back(seg(u, t_mid, t_mid + .3), 1.6)
            d = ImageDraw.Draw(img)
            for wd, col in ((20, INK), (10, GOLD)):
                d.rounded_rectangle([x - 180 * k, y - 125 * k, x + 180 * k, y + 125 * k], 16, outline=col, width=wd)
            chip(img, 'THE TURN STARTS HERE', (196, 120, 30), 540, y + 175, u, t_mid + .15, size=54)
        t_x = cue(14) - .05
        k = pop(u, cue(0), .3, 1.8) if u < t_x + .6 else 1
        if u > cue(0):
            put_chip(img, 'PUSHED OFF?', (150, 70, 70), 300, 420, k, size=60, angle=4)
            if u > t_x: draw_x(img, 300, 420, 100, smooth(seg(u, t_x, t_x + .3)) * 2, w=22)
    sx, sy = shake(u, cue(14), 10, .35)
    img = finish(img, u, 1.0, 540, 960, sx, sy, vig=(.45, (12, 8, 14)))
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(0, 180, W, 320), (180, 340, 460, 520)]}


# ---------------------------------------------------------------- living room (s07, s16, s18)
def _room_layer(warm=1.0):
    """A present-day living room in warm afternoon light: sage wall + wainscot, a window onto trees and roofs,
    a tall bookshelf (the cat's high shelf), a sofa, a floor lamp, a plant, a rug. 1280 wide (parallax)."""
    Wl = W + 200
    img = vgrad([(0, (92, 118, 110)), (.7, (120, 146, 132)), (1, (100, 124, 112))], Wl, H)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(3)
    for x in range(0, Wl, 64):                              # wallpaper: faint vertical leaf pattern
        for y in range(40, 1240, 90):
            yy = y + (x // 64 % 2) * 45
            d.ellipse([x + 22, yy, x + 40, yy + 30], fill=(108, 136, 124))
    d.rectangle([0, 1180, Wl, 1450], fill=(214, 204, 184)); d.rectangle([0, 1170, Wl, 1190], fill=(240, 232, 214), outline=INK, width=4)
    for x in range(0, Wl, 180): d.rectangle([x + 16, 1210, x + 164, 1420], outline=(186, 176, 156), width=5)
    # window with a view
    wx0, wy0, wx1, wy1 = 640, 230, 1080, 880
    view = vgrad([(0, (150, 200, 240)), (.7, (226, 232, 226)), (1, (250, 226, 190))], wx1 - wx0, wy1 - wy0)
    dv = ImageDraw.Draw(view)
    for i in range(7):
        x = i * 80 - 20; h_ = rng.uniform(140, 260)
        dv.rectangle([x, 650 - h_, x + 70, 650], fill=(176, 160, 170))
        for wy in range(int(650 - h_ + 20), 640, 40):
            dv.rectangle([x + 12, wy, x + 26, wy + 18], fill=(250, 236, 200)); dv.rectangle([x + 42, wy, x + 56, wy + 18], fill=(250, 236, 200))
    for x, r_ in ((60, 120), (230, 150), (390, 110)):
        dv.ellipse([x - r_, 480 - r_ * .7, x + r_, 480 + r_], fill=(96, 150, 104))
        dv.ellipse([x - r_ * .6, 440 - r_ * .7, x + r_ * .5, 440 + r_ * .4], fill=(130, 184, 120))
    img.paste(view, (wx0, wy0))
    d.rectangle([wx0 - 24, wy0 - 24, wx1 + 24, wy1 + 10], outline=(240, 232, 214), width=26)
    d.rectangle([wx0 - 36, wy0 - 36, wx1 + 36, wy1 + 22], outline=INK, width=5)
    d.rectangle([(wx0 + wx1) / 2 - 9, wy0, (wx0 + wx1) / 2 + 9, wy1], fill=(240, 232, 214))
    d.rectangle([wx0, 540, wx1, 556], fill=(240, 232, 214))
    d.rectangle([wx0 - 50, wy1 + 10, wx1 + 50, wy1 + 44], fill=(240, 232, 214), outline=INK, width=5)
    # curtain
    d.polygon([(590, 200), (690, 200), (668, 1000), (580, 1020)], fill=(186, 84, 64), outline=INK, width=5)
    for k in range(3): d.line([(610 + k * 22, 210), (600 + k * 20, 1000)], fill=(160, 66, 50), width=5)
    # sofa (under the window)
    d.rounded_rectangle([620, 1160, Wl + 40, 1330], 50, fill=(196, 120, 70), outline=INK, width=7)
    d.rounded_rectangle([600, 1270, Wl + 40, 1450], 30, fill=(214, 136, 82), outline=INK, width=7)
    d.rounded_rectangle([580, 1230, 680, 1440], 40, fill=(186, 110, 64), outline=INK, width=7)
    for x in (760, 960):
        d.rounded_rectangle([x, 1290, x + 180, 1340], 20, fill=(230, 158, 100))
    d.rounded_rectangle([720, 1180, 860, 1290], 30, fill=(240, 210, 120), outline=INK, width=5)       # cushion
    # framed picture over the shelf side
    d.rectangle([450, 360, 560, 500], fill=(240, 232, 214), outline=INK, width=6); d.rectangle([466, 376, 544, 484], fill=(200, 150, 110))
    d.ellipse([480, 400, 530, 450], fill=(250, 220, 150))
    # tall bookshelf (left); the top shelf is where the cat sits (y ~ 420)
    d.rectangle([40, 300, 430, 1450], fill=(124, 80, 50), outline=INK, width=8)
    for k, y in enumerate((440, 660, 880, 1100, 1320)):
        d.rectangle([52, y, 418, y + 24], fill=(156, 104, 64), outline=INK, width=4)
        if k > 0:
            x = 66; r2 = np.random.default_rng(k)
            while x < 400:
                bw = r2.uniform(22, 44); bh = r2.uniform(120, 190)
                c = [(170, 70, 60), (60, 100, 150), (210, 170, 80), (80, 130, 90), (230, 220, 200)][int(r2.integers(0, 5))]
                d.rectangle([x, y - bh, x + bw, y], fill=c, outline=INK, width=3); x += bw + 3
    # plant on the windowsill
    d.polygon([(960, 890), (976, 830), (1040, 830), (1056, 890)], fill=(200, 110, 70), outline=INK)
    for a_ in range(-60, 70, 24):
        x2 = 1008 + 90 * math.sin(math.radians(a_)); y2 = 830 - 120 * math.cos(math.radians(a_))
        d.polygon([(1008, 830), (x2 - 18, y2 + 24), (x2, y2), (x2 + 16, y2 + 30)], fill=(70, 140, 80), outline=INK)
    # floor
    d.rectangle([0, 1450, Wl, H], fill=(156, 108, 68))
    for k in range(-12, 14):
        d.line([(Wl / 2 + k * 34, 1450), (Wl / 2 + k * 200, H)], fill=(126, 84, 52), width=4)
    d.rectangle([0, 1440, Wl, 1458], fill=(90, 62, 44))
    d.ellipse([200, 1610, 1120, 1850], fill=(150, 64, 56), outline=INK, width=6)
    d.ellipse([260, 1640, 1060, 1820], outline=(240, 200, 120), width=8)
    d.ellipse([330, 1670, 990, 1790], outline=(220, 120, 80), width=5)
    return img


def _sun_patch():
    lay = layer(); ImageDraw.Draw(lay).polygon([(560, 1480), (930, 1480), (1060, 1800), (520, 1800)], fill=(255, 214, 150, 80))
    return lay.filter(ImageFilter.GaussianBlur(28))


def _fg_plant():
    """A dark, out-of-focus houseplant in the near foreground (bottom-left corner): depth."""
    lay = layer(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([-40, 1760, 200, 1990], 30, fill=(70, 40, 30), outline=INK, width=6)
    for k, (a, L) in enumerate(((-100, 330), (-70, 380), (-45, 300), (-125, 260), (-20, 240), (-85, 420))):
        r = math.radians(a); bx, by = 80 + k * 12, 1770
        tip = (bx + math.cos(r) * L, by + math.sin(r) * L)
        mid = (bx + math.cos(r) * L * .55, by + math.sin(r) * L * .55); nx, ny = -math.sin(r) * 46, math.cos(r) * 46
        d.polygon([(bx, by), (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny)], fill=(34, 62 + k * 6, 44), outline=(14, 26, 18), width=4)
    return lay.filter(ImageFilter.GaussianBlur(7))


def room(img, u, cam=0.0, fg=True):
    img.alpha_composite(_cached('room', _room_layer), (int(-100 + cam * .5), 0))
    img.alpha_composite(_cached('sun_patch', _sun_patch), (int(cam * .8), 0))
    kit.light_rays(img, 900 + cam * .5, 420, (255, 236, 200), n=6, alpha=.16, spread=(120, 200), length=1800, seed=6, phase=math.sin(u * .4), blur=24)
    radial(img, 700 + cam * .5, 1500, 800, (255, 226, 180), .22, 1.5)
    haze(img, 1380, 1700, (255, 230, 190), .12)
    radial(img, 60 + cam * .4, 900, 500, (20, 30, 40), .25, 1.2, add=False)          # the shaded corner away from the window
    dust(img, 9, 24, (500, 300, 1080, 1400), (255, 246, 220), 110, size=(2, 5), t=u)
    if fg: img.alpha_composite(_cached('fg_plant', _fg_plant), (int(cam * 1.6), 0))


def owner(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, label_txt='OWNER', label_on=True, lbl_dy=0):
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, aura=(255, 220, 170), aura_alpha=.3, rim=(255, 236, 200), rim_dir=(1, -.5),
              rim_w=10, bphase=.7, hair=('tuft', '#5a3a2a'), **OWNER_KW)
    if label_on and not HIDE_UI:
        hx, hy = g['head']
        label(img, label_txt, min(W - 160, max(160, hx)), hy - g['R'] * 1.9 - 80 + lbl_dy, (70, 120, 190), size=42)
    return g


# ---------------------------------------------------------------- s07: CLUE 1: tailless cats do it too
def s07(u, D, cue):
    cam = -12 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    room(img, u, cam)
    G = {}
    t0, t1 = .25, cue(9) - .05
    def path(t):
        p = .05 + .95 * smooth(seg(t, t0, t1 - .2))
        x = 600 + cam * .6
        y = 760 + (1480 - 760) * (seg(t, 0, t1) ** 1.6)
        kw = dict(C.righting(p)); kw.update(tail=False, rot=-6 * (1 - p))
        return x, y, kw
    G['o'] = owner(img, u, dict(POSES['stand'], armL=(40, 90), armR=(-40, -90)) if u > t1 else dict(POSES['point']),
                   'surprised', 900 + cam * .9, 1880, .66, look=-.6, label_on=False)
    ghost_trail(img, path, n=4, every=.3, u=u, s=185, alpha=.32, start=.3, tail=False)
    if u < t1:
        x, y, kw = path(u); C.put_cat(img, x, y, 185, **kw)
    else:
        v = u - t1; sq = damp(v, .07, 7, 16)
        C.put_cat(img, 600 + cam * .6, 1560 + 26 * sq, 185, phf=0, phb=0, tuckf=.3, tuckb=.3, bend=-4, tail=False)
    img = finish(img, u, 1.03, 560, 1200, vig=(.32, (20, 24, 34)))
    if not HIDE_UI:
        clue(img, 'CLUE 1', u)
        if u > cue(5) - .1:                            # NO TAIL tag + a short pointer to the rump
            x, y, kw = path(min(u, t1 - .01)) if u < t1 else (600 + cam * .6, 1590, {})
            straight_arrow(img, (x - 330, y - 260), (x - 150, y - 50), (196, 80, 60), w=14, head=40, alpha=int(255 * smooth(seg(u, cue(5) - .1, cue(5) + .15))))
            put_chip(img, 'NO TAIL', (196, 80, 60), x - 330, y - 300, pop(u, cue(5) - .1, .3, 2.0), size=56)
    return img, {'faces': [face_box(G['o'], 1.3)], 'avoid': [(0, 160, W, 480)]}


# ---------------------------------------------------------------- s08: CLUE 2: bent in the middle (a frame under a loupe)
def s08(u, D, cue):
    img = Image.new('RGBA', (W, H))
    img.alpha_composite(vgrad([(0, (40, 28, 22)), (1, (22, 16, 14))]))
    radial(img, 540, 900, 900, (255, 200, 130), .35, 1.3)
    # a big frame of the film (sepia) with sprockets, slowly drifting
    kw = dict(C.righting(.3)); kw.update(bend=38, rot=0)
    big = film_frame_img(('s08big',), 760, 620, kw, cy=.5, s=200)
    dx = 10 * math.sin(u * .6); dy = -20 * smooth(u / D)
    fx0, fy0 = 160 + dx, 560 + dy
    d = ImageDraw.Draw(img)
    d.rectangle([fx0 - 70, fy0 - 70, fx0 + 830, fy0 + 690], fill=(28, 20, 16), outline=INK, width=6)
    for y in range(int(fy0 - 50), int(fy0 + 680), 52):
        for x in (fx0 - 50, fx0 + 790):
            d.rounded_rectangle([x, y, x + 26, y + 30], 6, fill=(240, 226, 196))
    img.alpha_composite(big, (int(fx0), int(fy0)))
    # the waist position in the frame (cat drawn at the frame centre)
    wx, wy = fx0 + 380, fy0 + 310
    t_b = cue(8) - .1
    kb = smooth(seg(u, t_b, t_b + .35))
    if kb > 0 and not HIDE_UI:
        m = mask(); ImageDraw.Draw(m).ellipse([wx - 90, wy - 90, wx + 90, wy + 90], fill=255)
        glow(img, m, GOLD, .9 * kb, blur=30, add=True)
        # the V angle mark
        a1, a2 = math.radians(-19), math.radians(180 + 19)
        L = 230 * kb
        for wd, col in ((16, INK), (8, GOLD)):
            d = ImageDraw.Draw(img)
            d.line([(wx + math.cos(a1) * L, wy + math.sin(a1) * L - 40), (wx, wy - 40), (wx + math.cos(a2) * L, wy + math.sin(a2) * L - 40)], fill=col, width=wd, joint='curve')
    # Marey's loupe sweeping over the frames (the lens magnifies the region it covers)
    lx = 300 + 300 * smooth(seg(u, .2, t_b - .35))
    ly = 900 + 30 * math.sin(u * 1.5)
    kw_ = smooth(seg(u, t_b - .35, t_b + .1))
    lx, ly = lx + (wx + 20 * math.sin(u * 2) - lx) * kw_, ly + (wy + 10 - ly) * kw_
    r = 150
    src = img.crop((int(lx - r / 1.4), int(ly - r / 1.4), int(lx + r / 1.4), int(ly + r / 1.4))).resize((2 * r, 2 * r), Image.BICUBIC)
    m = mask(2 * r, 2 * r); ImageDraw.Draw(m).ellipse([0, 0, 2 * r, 2 * r], fill=255)
    img.paste(src, (int(lx - r), int(ly - r)), m)
    d = ImageDraw.Draw(img)
    d.ellipse([lx - r, ly - r, lx + r, ly + r], outline=INK, width=22); d.ellipse([lx - r, ly - r, lx + r, ly + r], outline=(206, 164, 76), width=12)
    hx, hy = lx + r * .7, ly + r * .7
    d.line([(hx, hy), (hx + 160, hy + 260)], fill=INK, width=44); d.line([(hx, hy), (hx + 160, hy + 260)], fill=(110, 70, 44), width=30)
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 540, 900, vig=(.45, (12, 8, 14)))
    if not HIDE_UI:
        clue(img, 'CLUE 2', u)
        stitle(img, 's08', [('BENT IN', 'white', 110), ('THE MIDDLE', GOLD, 130)], 1330, u, t_b, stagger=.25)
    return img, {'faces': [], 'avoid': [(0, 160, W, 360), (0, 480, W, 1300), (0, 1300, W, 1600)]}


# ---------------------------------------------------------------- s09: CLUE 3: 1968, a gymnast in a spacesuit copies it
def _gym_wall():
    """1968 gym back wall (1280 wide): panels, a row of high windows, wall bars, a clock, a NASA-style test banner."""
    Wl = W + 200
    img = vgrad([(0, (30, 72, 80)), (.6, (58, 120, 124)), (1, (44, 92, 98))], Wl, 1310)
    d = ImageDraw.Draw(img)
    for x in range(0, Wl, 160):
        d.rectangle([x, 330, x + 140, 1300], fill=(52, 112, 118), outline=(30, 70, 76), width=4)
    for x in range(40, Wl, 300):                                # high windows with daylight
        d.rectangle([x, 60, x + 220, 250], fill=(196, 226, 236), outline=INK, width=6)
        d.line([(x + 110, 60), (x + 110, 250)], fill=INK, width=5); d.line([(x, 155), (x + 220, 155)], fill=INK, width=5)
    d.rectangle([0, 270, Wl, 300], fill=(40, 60, 66), outline=INK, width=4)
    for x0 in (900, 1010):                                       # wall bars (right)
        d.rectangle([x0, 380, x0 + 22, 1300], fill=(176, 128, 74), outline=INK, width=4)
    for y in range(420, 1300, 64):
        d.line([(900, y), (1032, y)], fill=INK, width=12); d.line([(900, y), (1032, y)], fill=(206, 160, 100), width=6)
    cx, cy = 640, 420                                            # clock
    d.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], fill=(240, 236, 224), outline=INK, width=7)
    d.line([(cx, cy), (cx, cy - 38)], fill=INK, width=6); d.line([(cx, cy), (cx + 28, cy + 10)], fill=INK, width=6)
    return img


def _film_camera_1968():
    """A 1968 16 mm film camera on a tripod (echo of Marey's camera), near foreground left, soft focus."""
    lay = layer(); d = ImageDraw.Draw(lay)
    x, y = 120, 1450
    for lx in (-110, 0, 110):
        d.line([(x, y + 60), (x + lx, y + 470)], fill=INK, width=22); d.line([(x, y + 60), (x + lx, y + 470)], fill=(90, 94, 104), width=12)
    d.rounded_rectangle([x - 90, y - 70, x + 120, y + 70], 14, fill=(60, 62, 72), outline=INK, width=7)
    for c_ in ((x - 40, y - 120), (x + 60, y - 120)):
        d.ellipse([c_[0] - 62, c_[1] - 62, c_[0] + 62, c_[1] + 62], fill=(48, 50, 58), outline=INK, width=6)
        d.ellipse([c_[0] - 14, c_[1] - 14, c_[0] + 14, c_[1] + 14], fill=(150, 150, 160))
    d.rounded_rectangle([x + 110, y - 34, x + 200, y + 30], 8, fill=(30, 30, 36), outline=INK, width=6)
    d.ellipse([x + 186, y - 30, x + 214, y + 26], fill=(80, 110, 150), outline=INK, width=4)
    return lay.filter(ImageFilter.GaussianBlur(3))


def gym_bg(img, u, cam=0.0):
    img.alpha_composite(vgrad([(0, (30, 72, 80)), (1, (44, 92, 98))]))
    img.alpha_composite(_cached('gym_wall', _gym_wall), (int(-100 + cam * .4), 0))
    kit.light_rays(img, 300 + cam * .4, 160, (230, 246, 255), n=6, alpha=.14, spread=(30, 90), length=1600, seed=4, phase=math.sin(u * .5), blur=30)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1300, W, H], fill=(196, 118, 60))
    for k in range(-10, 12):
        d.line([(540 + k * 40 + cam * .8, 1300), (540 + k * 200 + cam, H)], fill=(170, 98, 48), width=4)
    d.rounded_rectangle([700 + cam * .9, 1560, 1180 + cam * .9, 1640], 16, fill=(60, 90, 160), outline=INK, width=6)   # floor mat
    radial(img, 540 + cam * .8, 1420, 520, (255, 236, 200), .22, 1.5)                                                     # floor shine
    haze(img, 1200, 1420, (210, 236, 240), .2)
    # a framed photo of the falling cat on the wall (what they copy)
    fr = film_frame_img(('s09pic',), 260, 200, dict(C.righting(.35), rot=0), cy=.5, s=66)
    px, py = 120 + cam * .4, 430
    d.rectangle([px - 18, py - 18, px + 278, py + 218], fill=(230, 220, 200), outline=INK, width=6)
    img.alpha_composite(fr, (int(px), int(py)))
    return (px + 130, py + 100)
    # ceiling lights
    for x in (200, 540, 880):
        d.rectangle([x - 90 + cam * .3, 120, x + 90 + cam * .3, 150], fill=(250, 250, 230), outline=INK, width=4)
        radial(img, x + cam * .3, 160, 420, (250, 250, 220), .18, 1.5)
    # a framed photo of the falling cat on the wall (what they copy)
    fr = film_frame_img(('s09pic',), 260, 200, dict(C.righting(.35), rot=0), cy=.5, s=66)
    px, py = 120 + cam * .4, 430
    d.rectangle([px - 18, py - 18, px + 278, py + 218], fill=(230, 220, 200), outline=INK, width=6)
    img.alpha_composite(fr, (int(px), int(py)))
    return (px + 130, py + 100)


def trampoline(img, cx, y, dip=0.0, w=520):
    d = ImageDraw.Draw(img)
    for s_ in (-1, 1):
        d.line([(cx + s_ * w / 2, y), (cx + s_ * (w / 2 - 30), y + 180)], fill=INK, width=20)
        d.line([(cx + s_ * w / 2, y), (cx + s_ * (w / 2 - 30), y + 180)], fill=(150, 150, 160), width=10)
    d.ellipse([cx - w / 2, y - 50, cx + w / 2, y + 50], fill=(60, 64, 80), outline=INK, width=8)
    pts = [(cx - w / 2 + 30, y), (cx, y + dip), (cx + w / 2 - 30, y)]
    d.line(pts, fill=(30, 30, 40), width=14, joint='curve')
    d.ellipse([cx - w / 2, y - 50, cx + w / 2, y + 50], outline=(70, 160, 220), width=10)


def spacesuit_gymnast(img, u, cx, cy, s, spin, tuck):
    """A gymnast in a white 1960s spacesuit (puffy limbs, bubble helmet, chest unit) twisting in mid-air:
    the body rolls about its long axis (width squash + mirror), arms and legs swap tucked / wide."""
    lay = layer(700, 900); d = ImageDraw.Draw(lay)
    ox, oy = 350, 420
    sq = .35 + .65 * abs(math.cos(spin)); fl = 1 if math.cos(spin) >= 0 else -1
    X = lambda x: ox + x * sq * fl
    suit, shade = (244, 244, 240), (196, 200, 210)
    aw = 150 * (1 - tuck) + 40 * tuck
    # legs
    for sd in (-1, 1):
        lw = 50 * (1 - tuck) + 20 * tuck
        C._limb(d, [(X(sd * 34), oy + 120), (X(sd * (40 + lw)), oy + 230 - 30 * tuck), (X(sd * (46 + lw * .6)), oy + 330 - 90 * tuck)], 62, 48, suit, INK, 7)
        bx, by = X(sd * (46 + lw * .6)), oy + 330 - 90 * tuck
        d.rounded_rectangle([bx - 34, by - 10, bx + 34, by + 26], 10, fill=(70, 74, 90), outline=INK, width=6)
    # torso
    d.rounded_rectangle([ox - 82 * sq, oy - 120, ox + 82 * sq, oy + 140], 60 * sq + 6, fill=INK)
    d.rounded_rectangle([ox - 74 * sq, oy - 112, ox + 74 * sq, oy + 132], 54 * sq, fill=suit)
    d.rounded_rectangle([ox - 74 * sq, oy + 60, ox + 74 * sq, oy + 84], 8, fill=shade)
    d.rounded_rectangle([min(X(-38), X(38)), oy - 60, max(X(-38), X(38)), oy + 10], 10, fill=(210, 214, 222), outline=INK, width=5)
    for i, c in enumerate(((220, 60, 50), (60, 140, 220), (240, 200, 60))):
        d.ellipse([X(-22 + i * 22) - 8, oy - 34, X(-22 + i * 22) + 8, oy - 18], fill=c)
    # arms
    for sd in (-1, 1):
        sh = (X(sd * 64), oy - 80)
        el = (X(sd * (70 + aw * .55)), oy - 80 - 70 * (1 - tuck) + 40 * tuck)
        hd = (X(sd * (70 + aw)), oy - 150 * (1 - tuck) + 10 * tuck)
        C._limb(d, [sh, el, hd], 50, 40, suit, INK, 7)
        d.ellipse([hd[0] - 26, hd[1] - 26, hd[0] + 26, hd[1] + 26], fill=(70, 74, 90), outline=INK, width=6)
    # helmet
    hx, hy, R = ox, oy - 200, 88
    d.ellipse([hx - R - 8, hy - R - 8, hx + R + 8, hy + R + 8], fill=INK)
    d.ellipse([hx - R, hy - R, hx + R, hy + R], fill=(150, 196, 236))
    d.ellipse([min(X(-58), X(58)), hy - 50, max(X(-58), X(58)), hy + 60], fill=(246, 246, 242), outline=INK, width=5)
    for e in (-1, 1):
        d.ellipse([X(e * 20) - 7, hy - 4, X(e * 20) + 7, hy + 14], fill=INK)
    d.arc([hx - R * .75, hy - R * .8, hx + R * .2, hy + R * .1], 200, 255, fill=(255, 255, 255), width=10)
    d.rounded_rectangle([hx - 70, hy + R - 14, hx + 70, hy + R + 18], 10, fill=shade, outline=INK, width=5)
    lay = lay.rotate(-25 * math.sin(spin * .5) - 10, resample=Image.BICUBIC, center=(ox, oy))
    anim.scaled_paste(img, lay, cx, cy, s)
    hxy = (cx + (hx - 350) * s, cy + (hy - 450) * s)
    return (hxy[0], hxy[1], R * s)


def s09(u, D, cue):
    cam = -16 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    pic = gym_bg(img, u, cam)
    G = {}
    G['sci'] = actor(img, 'thinking' if u < cue(13) else 'surprised', dict(POSES['hold']), 900 + cam, 1900, .62, u, look=-.6,
                     aura=(200, 240, 255), aura_alpha=.3, rim=(220, 250, 255), rim_dir=(-1, -.4), bphase=.2, goggles=False, **SCI_KW)
    # bounce: period 1.3 s; twist in the air (spin about the body axis), arms swap tuck/wide
    per = 1.3; ph = (u % per) / per
    hgt = math.sin(math.pi * ph) ** 1.0
    tcx = 470 + cam * .8; ty = 1640
    dip = 60 * max(0.0, 1 - hgt * 5)
    trampoline(img, tcx, ty, dip, w=640)
    gy = ty - 330 - 420 * hgt
    spin = u * 2.6
    tuck = .5 + .5 * math.sin(u * 2.6 * 2)
    hh = spacesuit_gymnast(img, u, tcx, gy, 1.0, spin, tuck)
    img.alpha_composite(_cached('cam1968', _film_camera_1968), (int(-60 + cam * 1.5), 60))      # near foreground
    G['g'] = {'head': hh[:2], 'R': hh[2] / 1.25}
    # motion arcs
    if hgt > .2:
        arc_arrow(img, tcx, gy, 260, 80, math.pi * .1, math.pi * .9, (255, 255, 255), w=8, head=24, alpha=150)
    img = finish(img, u, 1.0 + .04 * smooth(u / D), 540, 1100, vig=(.3, (10, 30, 40)))
    if not HIDE_UI:
        clue(img, 'CLUE 3', u)
        stitle(img, 's09', [('1968', GOLD, 200)], 330, u, cue(3) - .1)
        chip(img, 'NASA-FUNDED', (40, 70, 160), 540, 600, u, cue(4) - .05, size=52)
        hx, hy = G['g']['head']
        if u > cue(8) - .1: label(img, 'GYMNAST', 800, 820, (60, 140, 200), size=54)
        if u > cue(13) - .15:
            k = smooth(seg(u, cue(13) - .15, cue(13) + .15))
            d = ImageDraw.Draw(img)
            for wd, col in ((16, INK), (8, GOLD)):
                d.rounded_rectangle([pic[0] - 160 - 10 * k, pic[1] - 120 - 10 * k, pic[0] + 160 + 10 * k, pic[1] + 120 + 10 * k], 18, outline=col, width=wd)
            chip(img, 'COPY THE CAT', (196, 120, 30), pic[0] + 110, pic[1] + 175, u, cue(13) - .1, size=50)
    return img, {'faces': [face_box(G['sci'], 1.3), face_box(G['g'], 1.0)], 'avoid': [(0, 160, W, 660)]}


# ---------------------------------------------------------------- explanation stage (s10-s15): velvet + a faint grid
def stage(img, u, cam=0.0, dark=0.0, tint=(6, 6, 12), glow_col=(120, 150, 220)):
    """The explanation stage: the lab darkened under a coloured tint (one per shot), a faint grid, a floor light pool."""
    lab(img, u, cam, velvet_glow=(560, 820), camera=False, mat=False, rays=.6)
    img.alpha_composite(Image.new('RGBA', img.size, tint + (int(150 + 60 * dark),)))
    lay = layer(); d = ImageDraw.Draw(lay)
    for x in range(0, W + 1, 90): d.line([(x + cam * .5 % 90, 0), (x + cam * .5 % 90, H)], fill=glow_col + (24,), width=2)
    for y in range(0, H + 1, 90): d.line([(0, y), (W, y)], fill=glow_col + (24,), width=2)
    img.alpha_composite(lay)
    radial(img, 540, 900, 700, glow_col, .2, 1.4)
    radial(img, 540, 1640, 560, glow_col, .14, 1.6)
    dust(img, 12, 30, (0, 200, W, 1500), (200, 220, 255), 90, size=(2, 4), t=u)


def big_q(img, x, y, s, u):
    lay, _ = tlayer('q', [('?', GOLD, 420)], 420)
    m = mask(); ImageDraw.Draw(m).ellipse([x - 200 * s, y - 220 * s, x + 200 * s, y + 220 * s], fill=255)
    glow(img, m, GOLD, .35 * s, blur=60, add=True)
    anim.scaled_paste(img, lay, x, y, s * (1 + .03 * math.sin(u * 3)), 6 * math.sin(u * 1.4))


def s10(u, D, cue):
    img = Image.new('RGBA', (W, H))
    stage(img, u + 32, 0, dark=.6)
    cy = 960 + 14 * math.sin(u * 1.2)
    C.put_cat(img, 560, cy, 180, phf=math.pi, phb=math.pi, tuckf=.5, tuckb=.5, bend=14 + 4 * math.sin(u), rot=-3 + 3 * math.sin(u * .7), tail_ph=u * 1.4)
    G = {}
    G['m'] = marey(img, u, dict(POSES['think']), 'thinking', 170, 1990, .74, look=.6, label_on=False, aura=(150, 170, 255), rim=(180, 200, 255))
    big_q(img, 560, 520, pop(u, cue(1) - .1, .35, 1.6), u)
    img = finish(img, u, 1.0 + .05 * smooth(u / D), 560, 960, vig=(.5, (6, 6, 14)))
    if not HIDE_UI:
        chip(img, 'NOTHING TO PUSH ON', (70, 70, 110), 540, 1180, u, cue(7) - .1, size=50)
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(300, 260, 800, 760), (180, 1130, 900, 1240)]}


EX = (540, 820)          # the explanation cat's waist
EXS = 300                # its scale


def ex_cat(img, u, kw, glow_k=0.0, split=0.0, spine=0.0, cx=EX[0], cy=EX[1], s=EXS, alpha=1.0):
    """The explanation cat (big, centre). split: halves pull apart (px); spine: a glowing spine line."""
    kw = dict(kw); kw.setdefault('tail_ph', u * 1.2)
    lay, (ox, oy), info = C.render_cat(cx, cy, s, glow=glow_k if glow_k > 0 else None, seam=split > 0, **kw)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    if split > 0:
        mb, mf = info['masks']['back'], info['masks']['front']
        a = lay.split()[3]
        tf, tb = info['tf'], info['tb']
        back = lay.copy(); back.putalpha(ImageChops.multiply(a, ImageChops.subtract(mb, mf).point(lambda v: 255 if v > 0 else 0)))
        front = lay.copy(); front.putalpha(ImageChops.multiply(a, mf))
        C._paste(img, back, int(ox - tb[0] * split), int(oy - tb[1] * split))
        C._paste(img, front, int(ox + tf[0] * split), int(oy + tf[1] * split))
        for k in ('front', 'F'): info[k] = (info[k][0] + tf[0] * split, info[k][1] + tf[1] * split)
        for k in ('back', 'B'): info[k] = (info[k][0] - tb[0] * split, info[k][1] - tb[1] * split)
    else:
        C._paste(img, lay, ox, oy)
    if spine > 0:
        B, F, J = info['B'], info['F'], info['J']
        lay = layer(); d = ImageDraw.Draw(lay)
        pts = [B, J, F]
        d.line(pts, fill=(255, 250, 220, int(220 * spine)), width=16, joint='curve')
        for i in range(9):                                     # vertebrae
            p = (B[0] + (J[0] - B[0]) * i / 4, B[1] + (J[1] - B[1]) * i / 4) if i <= 4 else (J[0] + (F[0] - J[0]) * (i - 4) / 4, J[1] + (F[1] - J[1]) * (i - 4) / 4)
            d.ellipse([p[0] - 13, p[1] - 13, p[0] + 13, p[1] + 13], fill=(255, 255, 255, int(240 * spine)), outline=INK + (int(255 * spine),), width=4)
        img.alpha_composite(lay)
        m = mask(); ImageDraw.Draw(m).ellipse([J[0] - 70, J[1] - 70, J[0] + 70, J[1] + 70], fill=255)
        glow(img, m, (255, 240, 200), .8 * spine, blur=26, add=True)
    return info


def panel(img, y0=1430, y1=1880, col=(14, 16, 30), a=1.0):
    """The lower-third diagram panel (rounded, inked, slightly glassy); a fades it in."""
    if a <= 0: return
    lay = layer(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([40, y0 + 10, W - 40, y1 + 10], 40, fill=(0, 0, 0, 120))
    d.rounded_rectangle([40, y0, W - 40, y1], 40, fill=col + (215,), outline=(200, 210, 240, 160), width=4)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(lay)


def dial(img, x, y, r, deg, col, name, u, t0, ghost=None):
    """A turn gauge: a ring, the start mark, a filled arc of the turn so far, a needle, the degrees and the name."""
    if HIDE_UI or u < t0: return
    s = min(1.0, out_back(seg(u, t0, t0 + .35), 1.6))
    if s <= .02: return
    lay = layer(); d = ImageDraw.Draw(lay); R = r * s
    d.ellipse([x - R - 6, y - R - 6, x + R + 6, y + R + 6], fill=(10, 10, 20, 230), outline=INK + (255,), width=6)
    d.ellipse([x - R, y - R, x + R, y + R], outline=(90, 96, 130, 255), width=10)
    if abs(deg) > 1:
        a0 = -90; a1 = -90 + deg
        d.arc([x - R, y - R, x + R, y + R], min(a0, a1), max(a0, a1), fill=col + (255,), width=18)
    a = math.radians(-90 + deg)
    d.line([(x, y), (x + math.cos(a) * R * .92, y + math.sin(a) * R * .92)], fill=(255, 255, 255, 255), width=9)
    d.line([(x, y - R - 4), (x, y - R + 22)], fill=(255, 255, 255, 255), width=6)
    d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=col + (255,), outline=INK + (255,), width=4)
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    f = font(int(58 * s))
    txt = f'{int(round(deg)):+d}°'.replace('+0', '0')
    d.text((x, y + R + 50 * s), txt, font=f, fill='white', anchor='mm', stroke_width=8, stroke_fill=INK)
    put_chip(img, name, col, x, y - R - 50 * s, s, size=46)


def s11(u, D, cue):
    img = Image.new('RGBA', (W, H))
    stage(img, u + 34, 0, tint=(6, 8, 22), glow_col=(120, 150, 230))
    t_solid, t_obj = cue(4) - .1, cue(5)
    t_two, t_sp = cue(7) - .1, cue(12) - .1
    kg = smooth(seg(u, t_two, t_two + .35))
    ksp = smooth(seg(u, t_sp, t_sp + .4))
    split = 70 * kg * (1 - .75 * ksp)
    kw = dict(phf=math.pi, phb=math.pi, tuckf=.5, tuckb=.5, bend=4 + 34 * ksp, rot=0)
    info = ex_cat(img, u, kw, glow_k=kg, split=split, spine=max(ksp, .6 * kg))
    G = {}
    G['m'] = marey(img, u, dict(POSES['think']), 'thinking', 860, 1960, .62, look=-.6, label_on=False, aura=(150, 170, 255), rim=(180, 200, 255))
    if not HIDE_UI:
        ks = smooth(seg(u, t_solid, t_solid + .25)) * (1 - smooth(seg(u, t_two - .1, t_two + .1)))
        if ks > 0:
            lay = layer(); d = ImageDraw.Draw(lay)
            d.rectangle([EX[0] - 420, EX[1] - 290, EX[0] + 420, EX[1] + 290], outline=(230, 230, 240, int(255 * ks)), width=10)
            img.alpha_composite(lay)
            chip(img, 'ONE SOLID OBJECT?', (90, 90, 110), 540, EX[1] - 360, u, t_solid, size=50)
            if u > t_obj: draw_x(img, EX[0], EX[1], 260, smooth(seg(u, t_obj, t_obj + .35)) * 2 * ks, w=28)
        if kg > 0:
            stitle(img, 's11', [('TWO HALVES', 'white', 120)], 200, u, t_two)
            chip(img, 'FRONT', KEY_B, info['front'][0] + 40, EX[1] - 330, u, t_two + .05, size=54)
            chip(img, 'BACK', KEY_O, info['back'][0] - 40, EX[1] - 330, u, t_two + .2, size=54)
        if ksp > 0:
            J = info['J']
            chip(img, 'BENDY SPINE', (236, 226, 196), J[0], J[1] + 250, u, t_sp + .1, size=50)
            straight_arrow(img, (J[0], J[1] + 205), (J[0], J[1] + 70), (236, 226, 196), w=12, head=34, alpha=int(255 * ksp))
    img = finish(img, u, 1.0, 540, 900, vig=(.45, (6, 6, 14)))
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(0, 160, W, EX[1] + 330)]}


def tuck_icon(img, x, y, r, tucked, col, name, u, t0):
    """Lower-third icon: the half end-on as a disc with its legs; tucked = legs hugging it (small circle),
    stretched = legs straight out (wide circle)."""
    if HIDE_UI or u < t0: return
    s = min(1.0, out_back(seg(u, t0, t0 + .35), 1.6)); R = r * s
    lay = layer(); d = ImageDraw.Draw(lay)
    reach = R * (.8 if tucked else 1.75)
    for k in range(24):
        if k % 2: continue
        d.arc([x - reach - 30, y - reach - 30, x + reach + 30, y + reach + 30], k * 15, k * 15 + 15, fill=col + (230,), width=8)
    for a in (55, 125):
        e = (x + math.cos(math.radians(a)) * reach, y + math.sin(math.radians(a)) * reach)
        d.line([(x, y), e], fill=INK + (255,), width=int(30 * s)); d.line([(x, y), e], fill=(246, 242, 234, 255), width=int(18 * s))
        d.ellipse([e[0] - 14, e[1] - 14, e[0] + 14, e[1] + 14], fill=(246, 242, 234, 255), outline=INK + (255,), width=4)
    d.ellipse([x - R * .6, y - R * .6, x + R * .6, y + R * .6], fill=col + (255,), outline=INK + (255,), width=6)
    img.alpha_composite(lay)
    put_chip(img, name, col, x, y - R * 2.3 - 30, s, size=44)


def s12(u, D, cue):
    img = Image.new('RGBA', (W, H))
    stage(img, u + 38, 0, tint=(4, 16, 20), glow_col=(110, 190, 200))
    t_t, t_s = cue(2) - .1, cue(8) - .1
    kt = smooth(seg(u, t_t, t_t + .5)); ks = smooth(seg(u, t_s, t_s + .5))
    kw = dict(phf=math.pi, phb=math.pi, tuckf=.5 + .5 * kt, tuckb=.5 - .5 * ks, bend=36, rot=0)
    info = ex_cat(img, u, kw, glow_k=1.0, cy=EX[1] + 40)
    if not HIDE_UI:
        F, B = info['front'], info['back']
        if kt > 0:
            straight_arrow(img, (F[0] + 30, F[1] - 330), (F[0] + 30, F[1] - 330 + 150 * kt), KEY_B, w=16, head=40)
        if ks > 0:
            straight_arrow(img, (B[0] - 20, B[1] - 200), (B[0] - 20 - 160 * ks, B[1] - 200 - 160 * ks), KEY_O, w=16, head=40)
        chip(img, 'FRONT LEGS IN', KEY_B, 760, 300, u, t_t + .1, size=50)
        chip(img, 'BACK LEGS OUT', KEY_O, 320, 300, u, t_s + .1, size=50)
        panel(img, 1440, 1880, a=smooth(seg(u, t_t, t_t + .3)))
        tuck_icon(img, 800, 1700, 62, True, KEY_B, 'TUCKED: SMALL', u, t_t + .3)
        tuck_icon(img, 280, 1690, 62, False, KEY_O, 'STRETCHED: WIDE', u, t_s + .3)
    img = finish(img, u, 1.0, 540, 900, vig=(.45, (6, 6, 14)))
    return img, {'faces': [], 'avoid': [(0, 240, W, EX[1] + 330), (0, 1430, W, 1900)]}


def turn_ui(img, u, info, af, ab, kf_on, kb_on, big_front=True):
    """Rotation arcs around each half (around its own axis): big for the half that turns a lot, small for the other."""
    F, B = info['front'], info['back']
    if kf_on > 0:
        arc_arrow(img, F[0] + 30, F[1], 150 if big_front else 110, 360 if big_front else 260, -math.pi / 2, -math.pi / 2 + af, KEY_B, w=26 if big_front else 12, head=64 if big_front else 34,
                  alpha=int(255 * kf_on))
    if kb_on > 0:
        arc_arrow(img, B[0] - 30, B[1], 110 if big_front else 150, 260 if big_front else 360, -math.pi / 2, -math.pi / 2 + ab, KEY_O, w=12 if big_front else 26, head=34 if big_front else 64,
                  alpha=int(255 * kb_on))


def s13(u, D, cue):
    img = Image.new('RGBA', (W, H))
    stage(img, u + 41, 0, tint=(10, 6, 26), glow_col=(150, 130, 240))
    t_turn, t_back = cue(1), cue(8) - .1
    k = smooth(seg(u, t_turn, cue(5) + .6))
    p = .22 + .28 * k
    kw = dict(C.righting(p)); kw.update(rot=0, bend=36, tuckf=1.0, tuckb=0.0)
    info = ex_cat(img, u, kw, glow_k=1.0)
    front_deg = 195 * k; back_deg = 15 * k
    turn_ui(img, u, info, -math.radians(front_deg), math.radians(max(back_deg, 8 * smooth(seg(u, t_back, t_back + .3)))) * 2.2,
            smooth(seg(u, t_turn, t_turn + .2)), smooth(seg(u, t_back, t_back + .2)))
    if not HIDE_UI:
        chip(img, 'TUCKED: TURNS A LOT', KEY_B, 600, 230, u, cue(4) - .1, size=54)
        chip(img, 'STRETCHED: BARELY MOVES', KEY_O, 480, 345, u, t_back, size=54)
        panel(img, 1440, 1880, a=smooth(seg(u, t_turn - .3, t_turn)))
        dial(img, 780, 1640, 120, -front_deg, KEY_B, 'FRONT', u, t_turn + .1)
        dial(img, 300, 1640, 120, back_deg, KEY_O, 'BACK', u, t_back)
    img = finish(img, u, 1.0, 540, 900, vig=(.45, (6, 6, 14)))
    return img, {'faces': [], 'avoid': [(0, 190, W, EX[1] + 330), (0, 1430, W, 1900)]}


def s14(u, D, cue):
    img = Image.new('RGBA', (W, H))
    stage(img, u + 45, 0, tint=(24, 6, 14), glow_col=(230, 130, 110))
    t_sw = cue(2) - .1
    t_bin, t_fout = cue(3) - .1, cue(6) - .1
    t_up = cue(10)
    kbin = smooth(seg(u, t_bin, t_bin + .45)); kfo = smooth(seg(u, t_fout, t_fout + .45))
    k = smooth(seg(u, t_up - .3, cue(14) + .1))
    p = .6 + .28 * k
    kw = dict(C.righting(p)); kw.update(rot=0, bend=36, tuckf=1.0 - kfo, tuckb=kbin)
    if u > t_sw and k < 1:                            # a faint ghost of the s13 pose (before the swap)
        g = dict(C.righting(.5)); g.update(rot=0, bend=36, tuckf=1.0, tuckb=0.0)
        ex_cat(img, u, g, alpha=.18 * (1 - k))
    info = ex_cat(img, u, kw, glow_k=1.0)
    back_deg = 195 * k; front_deg = 15 * k
    turn_ui(img, u, info, math.radians(max(front_deg, 8)) * 2.2, -math.radians(back_deg), smooth(seg(u, t_up, t_up + .2)),
            smooth(seg(u, t_up - .3, t_up)), big_front=False)
    if not HIDE_UI:
        stitle(img, 's14', [('SWAP!', 'white', 140)], 170, u, t_sw)
        chip(img, 'BACK LEGS IN', KEY_O, 320, 420, u, t_bin + .1, size=50)
        chip(img, 'FRONT LEGS OUT', KEY_B, 760, 420, u, t_fout + .1, size=50)
        panel(img, 1440, 1880, a=smooth(seg(u, t_bin, t_bin + .3)))
        if u < t_up - .2:
            tuck_icon(img, 280, 1700, 62, True, KEY_O, 'BACK: SMALL', u, t_bin + .3)
            tuck_icon(img, 800, 1690, 62, False, KEY_B, 'FRONT: WIDE', u, t_fout + .3)
        else:
            dial(img, 300, 1640, 120, -back_deg, KEY_O, 'BACK CATCHES UP', u, t_up - .2)
            dial(img, 780, 1640, 120, front_deg, KEY_B, 'FRONT', u, t_up - .2)
    img = finish(img, u, 1.0, 540, 900, vig=(.45, (6, 6, 14)))
    return img, {'faces': [], 'avoid': [(0, 140, W, EX[1] + 330), (0, 1430, W, 1900)]}


def s15(u, D, cue):
    img = Image.new('RGBA', (W, H))
    lab(img, u + 49, 0, velvet_glow=(560, 1100), camera=False, rays=.8)
    t_c, t_b, t_f = cue(2) - .1, cue(8) - .2, cue(14) - .1
    # the cat is feet-down now; it drops onto the mattress on 'flipped'
    kd = seg(u, t_f - .7, t_f)
    cy = 900 + (1440 - 900) * (kd ** 1.7)
    glow_k = 1 - smooth(seg(u, t_f - .6, t_f))
    G = {}
    v = max(0.0, u - t_f); sq = damp(v, .06, 7, 16)
    kw = dict(phf=0, phb=0, tuckf=.25, tuckb=.25, bend=-4 * smooth(seg(u, 0, .5)), rot=0)
    info = ex_cat(img, u, kw, glow_k=glow_k, cx=EX[0] + 40, cy=cy + 26 * sq, s=EXS - 80 * smooth(kd))
    G['m'] = marey(img, u, dict(POSES['stand'], armL=(40, 30), armR=(-40, -30)) if u < t_f else dict(POSES['stand'], armL=(60, 20), armR=(-60, -20)),
                   'thinking' if u < t_f else 'happy', 170, 1800, .7, look=.6, label_on=False)
    if not HIDE_UI:
        # two opposite twists slide together and cancel: + and - = 0
        kc = smooth(seg(u, t_c, t_c + .6))
        off = 230 * (1 - kc)
        arc_arrow(img, 540 - off, 520, 130, 100, math.pi * .9, math.pi * 2.3, KEY_B, w=16, head=40)
        arc_arrow(img, 540 + off, 520, 130, 100, math.pi * .1, -math.pi * 1.3, KEY_O, w=16, head=40)
        d = ImageDraw.Draw(img)
        if kc < .9:
            for txt, x in (('+', 540 - off), ('−', 540 + off)):
                d.text((x, 520), txt, font=font(100), fill='white', anchor='mm', stroke_width=8, stroke_fill=INK)
        else:
            d.text((540, 520), '= 0', font=font(120), fill='white', anchor='mm', stroke_width=10, stroke_fill=INK)
        chip(img, 'TWISTS CANCEL', (90, 90, 130), 540, 700, u, t_c + .55, size=50)
        chip(img, 'NO LAW BROKEN', GOOD, 540, 810, u, t_b, size=52)
        if u > t_f - .1:
            stitle(img, 's15', [('FLIPPED!', GOLD, 150)], 170, u, t_f)
    img = finish(img, u, 1.0, 540, 900, vig=(.42, (12, 8, 14)))
    return img, {'faces': [face_box(G['m'], 1.3)], 'avoid': [(0, 160, W, 870), (300, 1250, 900, 1650)]}


# ---------------------------------------------------------------- s16: a spinning chair (top view)
def topview_room(img, u):
    img.alpha_composite(vgrad([(0, (156, 110, 70)), (1, (136, 94, 60))]))
    d = ImageDraw.Draw(img)
    for x in range(-40, W + 40, 120):
        d.line([(x, 0), (x, H)], fill=(118, 80, 50), width=5)
        for y in range(int((x * 7) % 400) - 400, H, 400):
            d.line([(x, y), (x + 120, y)], fill=(118, 80, 50), width=4)
    d.ellipse([80, 520, 1000, 1500], fill=(70, 100, 150), outline=INK, width=8)
    d.ellipse([140, 580, 940, 1440], outline=(230, 210, 150), width=10)
    # desk (top), plant (corner), a window light patch
    d.rounded_rectangle([140, -40, 940, 260], 20, fill=(120, 78, 50), outline=INK, width=8)
    d.rectangle([600, 40, 860, 200], fill=(40, 44, 56), outline=INK, width=6)
    d.ellipse([170, 60, 290, 180], fill=(230, 220, 190), outline=INK, width=6)
    for a in range(0, 360, 45):
        x, y = 980 + 70 * math.cos(math.radians(a)), 1720 + 70 * math.sin(math.radians(a))
        d.ellipse([x - 60, y - 40, x + 60, y + 40], fill=(70, 140, 80), outline=INK, width=4)
    d.ellipse([930, 1670, 1030, 1770], fill=(150, 90, 60), outline=INK, width=5)
    radial(img, 200, 1300, 700, (255, 236, 200), .25, 1.4)


def person_top(img, cx, cy, ang, arm_out, leg_out, s=1.0):
    """A person on a swivel chair seen from above, facing direction ang (rad). arm_out / leg_out 0..1."""
    def P(r, a): return (cx + math.cos(ang + a) * r * s, cy + math.sin(ang + a) * r * s)
    d = ImageDraw.Draw(img)
    # chair: base star + seat + backrest
    for k in range(5):
        a = ang + k * 2 * math.pi / 5 + .3
        e = (cx + math.cos(a) * 200 * s, cy + math.sin(a) * 200 * s)
        d.line([(cx, cy), e], fill=INK, width=int(26 * s)); d.line([(cx, cy), e], fill=(70, 70, 80), width=int(14 * s))
        d.ellipse([e[0] - 18 * s, e[1] - 18 * s, e[0] + 18 * s, e[1] + 18 * s], fill=(30, 30, 36))
    d.ellipse([cx - 150 * s, cy - 150 * s, cx + 150 * s, cy + 150 * s], fill=(50, 54, 66), outline=INK, width=8)
    bk = [P(150, math.pi - .8), P(185, math.pi - .5), P(190, math.pi), P(185, math.pi + .5), P(150, math.pi + .8)]
    d.line(bk, fill=INK, width=int(44 * s), joint='curve'); d.line(bk, fill=(70, 74, 90), width=int(30 * s), joint='curve')
    # legs (forward), from tucked to stretched
    for side in (-1, 1):
        hip = P(60, side * .5)
        L = 120 + 170 * leg_out
        knee = P(60 + L * .55, side * (.35 + .25 * leg_out))
        foot = P(60 + L, side * (.3 + .45 * leg_out))
        for col, w in ((INK, 46), (OWNER_KW['pants'], 32)):
            d.line([hip, knee, foot], fill=kit.rgb(col), width=int(w * s), joint='curve')
        d.ellipse([foot[0] - 26 * s, foot[1] - 26 * s, foot[0] + 26 * s, foot[1] + 26 * s], fill=(40, 30, 30), outline=INK, width=4)
    # shoulders + arms
    sh = [P(70, math.pi / 2 + .1), P(70, -math.pi / 2 - .1)]
    d.ellipse([cx - 95 * s, cy - 95 * s, cx + 95 * s, cy + 95 * s], fill=kit.rgb(OWNER_KW['shirt']), outline=INK, width=8)
    for side, shp in zip((1, -1), sh):
        reach = 90 + 190 * arm_out
        elbow = P(80 + reach * .5, side * (math.pi / 2 + .2 - .9 * (1 - arm_out)))
        hand = P(60 + reach, side * (math.pi / 2 + .35 - 1.2 * (1 - arm_out)))
        for col, w in ((INK, 30), ((246, 246, 242), 18)):
            d.line([shp, elbow, hand], fill=col, width=int(w * s), joint='curve')
        d.ellipse([hand[0] - 20 * s, hand[1] - 20 * s, hand[0] + 20 * s, hand[1] + 20 * s], fill=(246, 246, 242), outline=INK, width=5)
    # head (hair from above) + nose direction
    d.ellipse([cx - 62 * s, cy - 62 * s, cx + 62 * s, cy + 62 * s], fill=(246, 246, 242), outline=INK, width=8)
    hc = P(-14, 0)
    d.chord([hc[0] - 58 * s, hc[1] - 58 * s, hc[0] + 58 * s, hc[1] + 58 * s], math.degrees(ang) + 100, math.degrees(ang) + 260, fill=(90, 58, 42))
    n = P(70, 0)
    d.ellipse([n[0] - 14 * s, n[1] - 14 * s, n[0] + 14 * s, n[1] + 14 * s], fill=(246, 246, 242), outline=INK, width=5)


def chair_person(img, cx, seat_y, ang, arm_out, leg_out, s=1.0, swing=0.0, faces=None):
    """SIDE / THREE-QUARTER view of a white stickman on an office swivel chair, turned by ang about the column
    (0 = facing screen right, +pi/2 = facing the camera). A tiny 3D model, projected with the camera a little above.
    arm_out / leg_out 0..1: arms wide vs hugged in, legs stretched forward vs tucked under the seat (feet off the floor)."""
    EL = .32
    def proj(p):                                   # p = (X right, Y up, Z toward camera) -> screen, depth
        return (cx + p[0] * s, seat_y - (p[1] * .95 - p[2] * EL) * s), p[2]
    fa = (math.cos(ang), 0.0, math.sin(ang)); la = (-math.sin(ang), 0.0, math.cos(ang))     # forward, left (toward camera at ang 0)
    def L(f=0.0, l=0.0, y=0.0):
        return (fa[0] * f + la[0] * l, y, fa[2] * f + la[2] * l)
    d = ImageDraw.Draw(img)
    WH = (246, 246, 242)
    # ---- chair base (5-star + casters) and the gas column
    by = -300
    for k in range(5):
        a = ang + k * 2 * math.pi / 5 + .4
        e, ze = proj((math.cos(a) * 170, by, math.sin(a) * 170))
        o, _ = proj((0, by + 10, 0))
        col = (58, 58, 66) if ze < 0 else (78, 78, 88)
        d.line([o, e], fill=INK, width=int(30 * s)); d.line([o, e], fill=col, width=int(17 * s))
        d.ellipse([e[0] - 20 * s, e[1] - 6 * s, e[0] + 20 * s, e[1] + 30 * s], fill=(28, 28, 32), outline=INK, width=4)
    top, _ = proj((0, -40, 0)); bot, _ = proj((0, by + 10, 0))
    d.line([top, bot], fill=INK, width=int(40 * s)); d.line([top, bot], fill=(150, 154, 166), width=int(24 * s))
    # ---- body joints
    H = L(-15, 0, 30)
    SH = L(-25, 0, 300)
    HD = L(-10, 0, 425)
    pts = {}
    for sd in (-1, 1):
        hip = L(-10, sd * 42, 40)
        knee = mix_pt(L(150, sd * 55, 100), L(190, sd * 60, 30), leg_out)
        foot = mix_pt(L(70, sd * 50, -120), L(360, sd * 70, 60), leg_out)
        sh = L(-25, sd * 72, 290)
        elbow = mix_pt(L(40, sd * 110, 190), L(-20, sd * 210, 300), arm_out)
        hand = mix_pt(L(85, sd * 40, 250), L(-15, sd * 330, 320 + 25 * math.sin(swing)), arm_out)
        pts[sd] = (hip, knee, foot, sh, elbow, hand)
    items = []
    def limb(chain, col, w, z_bias=0.0):
        P2 = [proj(p) for p in chain]; z = sum(q[1] for q in P2) / len(P2) + z_bias
        def fn():
            xy = [q[0] for q in P2]
            d.line(xy, fill=INK, width=int((w + 14) * s), joint='curve')
            for q in xy: d.ellipse([q[0] - (w + 14) / 2 * s, q[1] - (w + 14) / 2 * s, q[0] + (w + 14) / 2 * s, q[1] + (w + 14) / 2 * s], fill=INK)
            d.line(xy, fill=col, width=int(w * s), joint='curve')
            for q in xy: d.ellipse([q[0] - w / 2 * s, q[1] - w / 2 * s, q[0] + w / 2 * s, q[1] + w / 2 * s], fill=col)
        items.append((z, fn))
    pants = kit.rgb(OWNER_KW['pants']); shirt = kit.rgb(OWNER_KW['shirt'])
    for sd in (-1, 1):
        hip, knee, foot, sh, elbow, hand = pts[sd]
        limb([hip, knee, foot], pants, 40)
        fp, zf = proj(foot)
        def shoe(fp=fp, foot=foot):
            tip, _ = proj((foot[0] + fa[0] * 40, foot[1], foot[2] + fa[2] * 40))
            d.line([fp, tip], fill=INK, width=int(46 * s)); d.line([fp, tip], fill=(60, 44, 40), width=int(32 * s))
        items.append((zf + .5, shoe))
        limb([sh, elbow, hand], WH, 26, .3)
        hp, zh = proj(hand)
        items.append((zh + .4, lambda hp=hp: d.ellipse([hp[0] - 20 * s, hp[1] - 20 * s, hp[0] + 20 * s, hp[1] + 20 * s], fill=WH, outline=INK, width=5)))
    # seat cushion (a puck) and the backrest behind the hips
    def seat():
        c, _ = proj((0, 0, 0)); rx, ry = 165 * s, 165 * EL * s
        d.rounded_rectangle([c[0] - rx, c[1] - ry * .2, c[0] + rx, c[1] + 38 * s], 20, fill=(40, 42, 52), outline=INK, width=6)
        d.ellipse([c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry], fill=(66, 70, 86), outline=INK, width=6)
    items.append((-60, seat))
    bk = [L(-120, -120, 70), L(-120, 120, 70), L(-140, 125, 380), L(-140, -125, 380)]
    bz = sum(p[2] for p in bk) / 4
    def back():
        q = [proj(p)[0] for p in bk]
        d.polygon(q, fill=(58, 62, 78), outline=INK, width=8)
        a0, _ = proj(L(-110, 0, 0)); a1, _ = proj(L(-120, 0, 80))
        d.line([a0, a1], fill=INK, width=int(26 * s)); d.line([a0, a1], fill=(120, 124, 136), width=int(12 * s))
    items.append((bz * 1.0 - (5 if bz < 0 else -200), back))
    # torso (shirt) + head
    def torso():
        a, _ = proj(H); b, _ = proj(SH)
        d.line([a, b], fill=INK, width=int(132 * s)); d.line([a, b], fill=shirt, width=int(116 * s))
        for q, r in ((a, 58), (b, 58)):
            d.ellipse([q[0] - r * s, q[1] - r * s, q[0] + r * s, q[1] + r * s], fill=shirt)
    items.append((0, torso))
    def head():
        c, _ = proj(HD); R = 78 * s
        n0, _ = proj(L(-25, 0, 330)); d.line([n0, c], fill=INK, width=int(40 * s)); d.line([n0, c], fill=WH, width=int(26 * s))
        d.ellipse([c[0] - R - 5, c[1] - R - 5, c[0] + R + 5, c[1] + R + 5], fill=INK)
        d.ellipse([c[0] - R, c[1] - R, c[0] + R, c[1] + R], fill=WH)
        # hair tuft on the back/top
        hb, _ = proj(L(-40, 0, 470)); d.ellipse([hb[0] - 52 * s, hb[1] - 30 * s, hb[0] + 52 * s, hb[1] + 26 * s], fill=(90, 58, 42))
        # face: eyes + smile on the forward side, only when it faces the camera at all
        for sd in (-1, 1):
            e3 = L(-10 + 62, sd * 30, 438); e, ze = proj(e3)
            if fa[2] * 62 + la[2] * sd * 30 > -10:
                d.ellipse([e[0] - 9 * s, e[1] - 12 * s, e[0] + 9 * s, e[1] + 12 * s], fill=INK)
        if fa[2] > -.2:
            m0, _ = proj(L(60, -22, 395)); m1, _ = proj(L(66, 0, 388)); m2, _ = proj(L(60, 22, 395))
            d.line([m0, m1, m2], fill=INK, width=int(7 * s), joint='curve')
        if faces is not None: faces.append((c[0] - R, c[1] - R, c[0] + R, c[1] + R))
    items.append((40 if fa[2] > -.2 else -2, head))
    for z, fn in sorted(items, key=lambda q: q[0]):
        fn()
    return {sd: (proj(pts[sd][5])[0], proj(pts[sd][2])[0]) for sd in (-1, 1)}


def mix_pt(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def chair_state(u, t0, t1):
    """3 cycles: arms out + legs in, then swap; the chair turns a step on each half-cycle (one way only)."""
    k = seg(u, t0, t1); cyc = k * 3
    arm_out = .5 + .5 * math.cos(2 * math.pi * cyc)
    leg_out = 1 - arm_out
    ang = .55 + math.radians(120) * (cyc - math.sin(4 * math.pi * cyc) / (4 * math.pi) * .8) + .03 * math.sin(u * 2)
    return ang, arm_out, leg_out


def s16(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = -14 * smooth(u / D)
    room(img, u + 3, cam)
    img.alpha_composite(Image.new('RGBA', img.size, (20, 14, 10, 70)))
    radial(img, 540 + cam * .5, 1150, 640, (255, 226, 180), .3, 1.4)           # a soft pool of light on the chair
    cx, seat_y = 540 + cam * .8, 1250
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 260, 1560, cx + 260, 1640], fill=(40, 28, 22, 255))       # floor shadow
    img = Image.alpha_composite(img, Image.new('RGBA', img.size, (0, 0, 0, 0)))
    t0, t1 = cue(5) - .2, cue(13) + .2
    # motion arcs: where the hands and feet were a moment ago (fading white trails)
    trail = layer(); dt = ImageDraw.Draw(trail)
    hist = []
    for j in range(7):
        a_, ao, lo = chair_state(u - j * .05, t0, t1)
        tmp = Image.new('RGBA', (8, 8)); hist.append(chair_person_pts(cx, seat_y, a_, ao, lo))
    for key in ((-1, 0), (1, 0), (-1, 1), (1, 1)):
        pl = [h[key[0]][key[1]] for h in hist]
        for j in range(len(pl) - 1):
            dt.line([pl[j], pl[j + 1]], fill=(255, 244, 214, int(150 * (1 - j / 7))), width=int(12 * (1 - j / 8)))
    img.alpha_composite(trail.filter(ImageFilter.GaussianBlur(2)))
    ang, arm_out, leg_out = chair_state(u, t0, t1)
    faces = []
    # the turn arrow around the column (behind half first, then the person, then the front half)
    k = seg(u, t0, t1)
    if k > 0 and not HIDE_UI:
        arc_arrow(img, cx, seat_y + 120, 330, 96, math.pi + .3, 2 * math.pi - .3, GOLD, w=14, head=1, alpha=150)
    chair_person(img, cx, seat_y, ang, arm_out, leg_out, 1.0, swing=u * 3, faces=faces)
    if k > 0 and not HIDE_UI:
        arc_arrow(img, cx, seat_y + 120, 330, 96, -.2, math.pi - .5, GOLD, w=18, head=48)
    img = finish(img, u, 1.0 + .04 * smooth(u / D), 540, 1100, vig=(.38, (20, 14, 10)))
    if not HIDE_UI:
        stitle(img, 's16', [('A SPINNING CHAIR', 'white', 96)], 170, u, cue(3) - .1)
        chip(img, 'ARMS & LEGS, IN TURNS', (196, 120, 30), 540, 1700, u, cue(7) - .1, size=50)
    return img, {'faces': faces, 'avoid': [(0, 120, W, 340), (0, 1640, W, 1760), (cx - 420, 700, cx + 420, 1600)]}


def chair_person_pts(cx, seat_y, ang, arm_out, leg_out):
    """Hands and feet in screen px (for the motion trails), same model as chair_person."""
    fa = (math.cos(ang), 0.0, math.sin(ang)); la = (-math.sin(ang), 0.0, math.cos(ang))
    def L(f=0.0, l=0.0, y=0.0): return (fa[0] * f + la[0] * l, y, fa[2] * f + la[2] * l)
    def proj(p): return (cx + p[0], seat_y - (p[1] * .95 - p[2] * .32))
    out = {}
    for sd in (-1, 1):
        hand = mix_pt(L(85, sd * 40, 250), L(-15, sd * 330, 320), arm_out)
        foot = mix_pt(L(70, sd * 50, -120), L(360, sd * 70, 60), leg_out)
        out[sd] = (proj(hand), proj(foot))
    return out


# ---------------------------------------------------------------- s17: DIDN'T BREAK PHYSICS. / IT USED IT.
def s17(u, D, cue):
    cam = 6 * smooth(u / D)
    img = Image.new('RGBA', (W, H))
    lab(img, u + 57, cam, velvet_glow=(620, 1300), camera=False, rays=1.6)
    radial(img, 300, 500, 900, (255, 190, 120), .35, 1.3)                       # low sunset light from the window
    G = {}
    G['m'] = marey(img, u, dict(POSES['stand'], armL=(30, 20), armR=(-40, -60)), 'happy', 900 + cam, 1700, .66, look=-.6, label_on=False,
                   lean=2 * math.sin(u * 2.2), rim_dir=(-1, -.4))
    C.put_cat(img, 500 + cam * .8, 1420, 230, phf=0, phb=0, tuckf=.3, tuckb=.3, bend=-4, tail_ph=u * 1.2, head_tilt=.1 * math.sin(u * 1.4))
    img = finish(img, u, 1.05 + .04 * smooth(u / D), 520, 1350, vig=(.45, (12, 8, 14)))
    t_d, t_u = cue(2) - .1, cue(6) - .08
    if not HIDE_UI:
        stitle(img, 's17a', [("DIDN'T BREAK", 'white', 112), ('PHYSICS.', 'white', 150)], 200, u, t_d, stagger=cue(4) - t_d)
        stitle(img, 's17b', [('IT USED IT.', GOLD, 170)], 560, u, t_u)
    sx, sy = shake(u, t_u, 12, .35)
    if sx or sy: img = anim.camera(img, 1.0, None, None, sx, sy)
    flash(img, u, t_u, .2, .3)
    return img, {'faces': [], 'avoid': [(0, 160, W, 800), (200, 1150, 900, 1600)]}


# ---------------------------------------------------------------- s18: every cat still lands that way (loop to 1894)
def s18(u, D, cue):
    cam = -10 * smooth(u / D)
    t0, t_land = cue(1) - .2, cue(4) + .05
    t_strip, t_end = cue(7) - .1, D - .25
    img = Image.new('RGBA', (W, H))
    room(img, u, cam)
    # owner on the right watching
    G = {}
    G['o'] = owner(img, u, dict(POSES['stand'], armL=(40, 70), armR=(-30, -60)) if u > t_land else dict(POSES['stand']),
                   'surprised' if u > t0 else 'neutral', 880 + cam * .9, 1880, .66, look=-.6, label_on=False)
    def path(t):
        p = smooth(seg(t, t0 + .1, t_land - .15))
        x = 240 + 360 * smooth(seg(t, t0, t_land)) + cam * .6
        y = 360 + (1540 - 360) * (seg(t, t0, t_land) ** 1.6) - 120 * math.sin(math.pi * seg(t, t0, t0 + .5)) * (1 - seg(t, t0, t_land))
        kw = dict(C.righting(p)); kw.update(tail_ph=t * 2, rot=-10 * (1 - p))
        return x, y, kw
    if u < t0:                                       # sitting on the top shelf, crouched to jump
        C.put_cat(img, 240 + cam * .6, 360 - 10 * smooth(seg(u, t0 - .4, t0)), 110, phf=0, phb=0, tuckf=.6, tuckb=.6, bend=-6,
                  tail_ph=u * 2, rot=8)
    elif u < t_land:
        x, y, kw = path(u)
        C.put_cat(img, x, y, 130, **kw)
    else:
        v = u - t_land; sq = damp(v, .06, 7, 16)
        C.put_cat(img, 600 + cam * .6, 1620 + 26 * sq, 130, phf=0, phb=0, tuckf=.3, tuckb=.3, bend=-4, tail_ph=u * 2)
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 560, 1200, vig=(.32, (20, 24, 34)))
    # the film strip slides in and the camera dives into one frame, which becomes the 1894 lab (s01 frame 0)
    if u > t_strip:
        k = smooth(seg(u, t_strip, t_strip + .7))
        fr = _cached('s18_frames', marey_strip_frames)
        lay = _cached('s18_strip', lambda: strip_layer(fr[:6], 300, 210))
        x = W + 40 - (W + 40 - (540 - lay.width / 2)) * k
        img.alpha_composite(Image.new('RGBA', img.size, (10, 6, 4, int(150 * k))))
        img.alpha_composite(lay, (int(x), int(960 - lay.height / 2 + 100 * (1 - k))))
        kz = smooth(seg(u, t_strip + .9, t_end))
        if kz > 0:
            # zoom into the first frame (it is centred near frame 0's cat position)
            fy = 960 - lay.height / 2 + 26 + 105
            img = anim.camera(img, 1 + 6 * kz ** 2, 540, fy)
            if kz > .55:
                a = smooth(seg(kz, .55, 1.0))
                s0, _ = s01_frame(0, 0, loop=True)
                b = s0.copy(); b.putalpha(int(255 * a))
                img.alpha_composite(b)
    if u >= t_end:
        img, _ = s01_frame(0, 0, loop=True)          # exactly s01's frame 0: the loop
        return img, {'faces': [], 'avoid': [(0, 150, W, 560)]}
    return img, {'faces': [face_box(G['o'], 1.3)], 'avoid': []}


SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [(f's{i:02d}', i, 0) for i in range(1, 19)]
END = 1958 / 30                 # 65.267 s (length.json)
NO_PUNCH = ()
BAND_AT = {}
STILL_AT = {'s01': .0, 's02': .97, 's03': .9, 's04': .8, 's05': .8, 's06': .75, 's07': .7, 's08': .9, 's09': .7, 's10': .8,
            's11': .9, 's12': .9, 's13': .75, 's14': .85, 's15': .45, 's16': .6, 's17': .95, 's18': .35}

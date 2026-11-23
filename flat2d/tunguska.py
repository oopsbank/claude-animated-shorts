"""Tunguska (video 4, "The Explosion With No Crater"): shots s01a-s14b as `sNN(u, D, cue) -> (img, info)`.

Same contract as blood_falls.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the
shot's voice-over LINE (split shots keep the line's word indexes). info: 'faces' (face boxes; render.py adds body
boxes) and 'avoid' (boxes the caption must not cover).

Render: .venv/bin/python flat2d/render.py audio/tunguska/words.json OUT.mp4 --film tunguska
Every shot keeps moving: wind in the trees, smoke, particles, glow pulses, flowing arrows, a slow camera
push/pan, and characters with breathing, blinks and `anim.secondary`. No comedy (BRIEF tone).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import kit, props, anim
import taiga as T
from kit import (W, H, INK, vgrad, radial, light_rays, cloud_bands, haze, peak_range, snow_ground, rocks,
                 snow_particles, dust, contact_shadow, label, title, pill, font, mask, glow, fill_mask, layer, lerp, rgb,
                 foreground_frame)
from anim import smooth, ease_out, ease_in, out_back, seg, mix, add, chain, damp, slam, pop, shake, actor, STAND, POSES
import blood_falls as B
from blood_falls import finish, slam_title, face_box, _clue_badge
from blood_falls_2 import put_chip, draw_x, partial, stars

SLUG = 'tunguska'
KULIK_BLUE = (52, 112, 222)
TRADER_ORANGE = (232, 118, 36)
KULIK_KW = dict(coat='#6f7a4e', pants='#3e3830')
TRADER_KW = dict(shirt='#c8463c', pants='#34343f', hat='cap')
FIRE = (255, 150, 50)


# ---------------------------------------------------------------- characters
def _pack(img, g, s, cx, gy, side=0.0):
    """Kulik's backpack behind the torso (side -1 = on his back when he faces right) + a rolled blanket."""
    hx, hy = g['head']; R = g['R']
    ax, ay = cx - hx, gy - hy; L = math.hypot(ax, ay); ux, uy = ax / L, ay / L; nx, ny = -uy, ux
    pc = (hx + ux * R * 2.35 + nx * side * R * .55, hy + uy * R * 2.35 + ny * side * R * .55)
    ww, hh = R * (1.45 if side else 2.1), R * 2.1
    lay = layer(int(ww + 60), int(hh + 60)); d = ImageDraw.Draw(lay); o = 30
    d.rounded_rectangle([o, o, o + ww, o + hh], R * .35, fill=(92, 70, 44), outline=INK, width=7)
    d.rounded_rectangle([o + 10, o + 10, o + ww * .45, o + hh - 10], R * .3, fill=(124, 98, 62))
    d.rounded_rectangle([o + ww * .15, o + hh * .55, o + ww * .85, o + hh * .9], R * .15, fill=(78, 58, 38), outline=INK, width=5)
    d.rounded_rectangle([o - 10, o + hh * .9, o + ww + 10, o + hh * .9 + R * .55], R * .27, fill=(160, 58, 48), outline=INK, width=6)
    d.line([(o + ww * .3, o + hh * .9), (o + ww * .3, o + hh * .9 + R * .55)], fill=INK, width=4)
    d.line([(o + ww * .7, o + hh * .9), (o + ww * .7, o + hh * .9 + R * .55)], fill=INK, width=4)
    ang = -math.degrees(math.atan2(ux, uy))
    anim.scaled_paste(img, lay, pc[0], pc[1], 1.0, angle=ang)


def _straps(img, g, cx, gy):
    hx, hy = g['head']; R = g['R']; d = ImageDraw.Draw(img)
    ax, ay = cx - hx, gy - hy; L = math.hypot(ax, ay); ux, uy = ax / L, ay / L; nx, ny = -uy, ux
    for k in (-1, 1):
        a = (hx + ux * R * 1.15 + nx * k * R * .28, hy + uy * R * 1.15 + ny * k * R * .28)
        b = (hx + ux * R * 2.9 + nx * k * R * .22, hy + uy * R * 2.9 + ny * k * R * .22)
        d.line([a, b], fill=INK, width=int(R * .2) + 6); d.line([a, b], fill=(92, 70, 44), width=int(R * .2))


def compass(img, x, y, s, t):
    d = ImageDraw.Draw(img); r = 34 * s
    d.ellipse([x - r - 5, y - r - 5, x + r + 5, y + r + 5], fill=INK)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 160, 70))
    d.ellipse([x - r * .78, y - r * .78, x + r * .78, y + r * .78], fill=(246, 240, 222))
    a = .5 * math.sin(t * 2.1) + .2
    d.polygon([(x + math.sin(a) * r * .7, y - math.cos(a) * r * .7), (x + math.cos(a) * r * .14, y + math.sin(a) * r * .14),
               (x - math.cos(a) * r * .14, y - math.sin(a) * r * .14)], fill=(220, 44, 44))
    d.polygon([(x - math.sin(a) * r * .7, y + math.cos(a) * r * .7), (x + math.cos(a) * r * .14, y + math.sin(a) * r * .14),
               (x - math.cos(a) * r * .14, y - math.sin(a) * r * .14)], fill=(60, 60, 70))


def shovel(img, hand, s, ang=8.0):
    """Kulik's probe shovel, held upright in a hand."""
    x, y = hand; d = ImageDraw.Draw(img); a = math.radians(ang)
    top = (x - math.sin(a) * 120 * s, y - math.cos(a) * 120 * s); bot = (x + math.sin(a) * 330 * s, y + math.cos(a) * 330 * s)
    d.line([top, bot], fill=INK, width=int(24 * s)); d.line([top, bot], fill=(150, 104, 62), width=int(14 * s))
    bx, by = bot; w = 46 * s
    d.polygon([(bx - w, by - 10 * s), (bx + w, by - 10 * s), (bx + w * .8, by + 80 * s), (bx, by + 110 * s), (bx - w * .8, by + 80 * s)],
              fill=(168, 176, 186), outline=INK, width=int(6 * s))


def kulik(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, rim=(255, 210, 160),
          rim_dir=(1, -.3), side=0.0, prop=None, aura_a=.42, bphase=.2):
    """KULIK · 1927: white stickman, fur hat, backpack (identity items), olive field coat. prop: 'compass',
    'shovel' or None."""
    lay = layer()
    g = actor(lay, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=KULIK_BLUE, aura_alpha=aura_a,
              rim=rim, rim_dir=rim_dir, bphase=bphase, **KULIK_KW)
    _pack(img, g, s, cx, gy - hop, side)
    img.alpha_composite(lay)
    if not side: _straps(img, g, cx, gy - hop)
    props.fur_hat(img, g['head'], g['R'], color=(96, 66, 46), fur=(226, 210, 184))
    hx, hy, _ = g['hands']['R']
    if prop == 'compass': compass(img, hx, hy, s * 1.3, t)
    elif prop == 'shovel': shovel(img, (hx, hy), s)
    if prop:
        r = 25 * s; d = ImageDraw.Draw(img)
        d.ellipse([hx - r - 3, hy - r - 3, hx + r + 3, hy + r + 3], fill=INK); d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(246, 246, 242))
    if label_on:
        hx, hy = g['head']
        label(img, 'KULIK · 1927', min(W - 220, max(220, hx)), hy - g['R'] * 1.45 - 92, KULIK_BLUE, size=int(48 * max(.9, min(1.1, s))))
    return g


def trader(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, rim=(255, 220, 170), rim_dir=(-1, -.3),
           heat=0.0):
    """TRADER · 60 KM: white stickman, red peasant shirt and red cap (identity items). heat 0..1: his shirt
    glows hot and steams."""
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=TRADER_ORANGE, aura_alpha=.4,
              rim=rim, rim_dir=rim_dir, bphase=.7, **TRADER_KW)
    hx, hy = g['head']; R = g['R']
    if heat > 0:
        ax, ay = cx - hx, gy - hop - hy; L = math.hypot(ax, ay); ux, uy = ax / L, ay / L
        tx, ty = hx + ux * R * 2.2, hy + uy * R * 2.2
        radial(img, tx, ty, R * 3, (255, 110, 30), .85 * heat * (.85 + .15 * math.sin(t * 13)))
        d = ImageDraw.Draw(img)
        for k in range(5):                                                # heat shimmer rising off the shirt
            v = (t * .9 + k / 5) % 1; x0 = tx + (k - 2) * R * .45
            pts = [(x0 + 14 * math.sin(j * .9 + t * 8 + k), ty - R * .4 - j * 22 - v * 160) for j in range(8)]
            a = int(255 * heat * math.sin(math.pi * v))
            lay = layer(); ImageDraw.Draw(lay).line(pts, fill=(255, 220, 160, a), width=7, joint='curve')
            img.alpha_composite(lay)
    if label_on:
        label(img, 'TRADER · 60 KM', min(W - 230, max(230, hx)), hy - R * 1.4 - 96, TRADER_ORANGE, size=int(48 * max(.9, min(1.1, s))))
    return g


def towns(img, t, pose, expr, cx, gy, s, shirt, look=0.0, bphase=0.0, lean=0.0):
    return actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, rim=(255, 200, 230), rim_dir=(0, -1), bphase=bphase,
                 aura=(160, 90, 220), aura_alpha=.3, shirt=shirt, pants='#33304a')


# ---------------------------------------------------------------- shared pieces
def chip_t(img, txt, fill, x, y, u, t0, size=56, angle=0.0):
    put_chip(img, txt, fill, x, y, pop(u, t0, .3, 2.0), size=size, angle=angle)


HIDE_UI = False                 # thumbnail frames: no CLUE badge


def clue(img, txt, u, t0=.05, y=250):
    if HIDE_UI: return
    s = slam(u, t0, .26, 1.3)
    if s > 0:
        bl, _ = _clue_badge(txt); anim.scaled_paste(img, bl, 540, y, s, angle=-3)


def flash(img, u, t0, dur=.35, a=1.0, col=(255, 250, 235)):
    if t0 <= u < t0 + dur:
        img.alpha_composite(Image.new('RGBA', img.size, col + (int(255 * a * (1 - (u - t0) / dur) ** 1.5),)))


def thought(img, cx, cy, rx, ry, tail, s, fill=(250, 248, 240)):
    """A cloud thought bubble with three trailing dots toward `tail`; returns the inner layer to draw in."""
    if s <= .01: return
    lay = layer(); d = ImageDraw.Draw(lay)
    bumps = 11
    for pass_, (col, grow) in enumerate(((INK, 8), (fill, 0))):
        for i in range(bumps):
            a = 2 * math.pi * i / bumps; bx, by = cx + math.cos(a) * rx * .86, cy + math.sin(a) * ry * .8; q = ry * .36 + grow
            d.ellipse([bx - q, by - q, bx + q, by + q], fill=col)
        d.ellipse([cx - rx - grow, cy - ry - grow, cx + rx + grow, cy + ry + grow], fill=col)
        for k, f in enumerate((.35, .62, .85)):
            px, py = cx + (tail[0] - cx) * (.55 + f * .45), cy + (tail[1] - cy) * (.55 + f * .45); q = 26 - k * 7 + grow
            d.ellipse([px - q, py - q, px + q, py + q], fill=col)
    return lay


def paste_grown(img, lay, ox, oy, s):
    """Paste a full-frame layer scaled by s about (ox, oy) (bubbles grow out of the thinker)."""
    if s <= .01: return
    bb = lay.getbbox()
    if not bb: return
    part = lay.crop(bb); pcx, pcy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    anim.scaled_paste(img, part, ox + (pcx - ox) * s, oy + (pcy - oy) * s, s)


def iron_lump(d, x, y, r, seed=2):
    rng = np.random.default_rng(seed); pts = []
    for i in range(10):
        a = i * 2 * math.pi / 10; rr = r * rng.uniform(.75, 1.05); pts.append((x + math.cos(a) * rr * 1.2, y + math.sin(a) * rr * .85))
    d.polygon(pts, fill=(84, 88, 100), outline=INK, width=7)
    d.polygon([pts[5], pts[6], pts[7], (x, y)], fill=(150, 156, 172))
    d.line([(x - r * .5, y - r * .45), (x - r * .1, y - r * .6)], fill=(230, 236, 246), width=6)
    for i in range(3):
        q = r * .12; cx_, cy_ = x + rng.uniform(-.5, .5) * r, y + rng.uniform(-.3, .4) * r
        d.ellipse([cx_ - q, cy_ - q, cx_ + q, cy_ + q], fill=(56, 58, 70))


def crater_icon(d, x, y, r):
    d.ellipse([x - r - 6, y - r * .42 - 6, x + r + 6, y + r * .42 + 6], fill=INK)
    d.ellipse([x - r, y - r * .42, x + r, y + r * .42], fill=(150, 112, 80))
    d.ellipse([x - r * .75, y - r * .28, x + r * .75, y + r * .3], fill=(84, 58, 44))
    d.ellipse([x - r * .7, y - r * .2, x + r * .4, y + r * .08], fill=(110, 78, 56))


def sky_dawn(img, u, cam, horizon=1260, stops=None):
    img.paste(vgrad(stops or [(0, (26, 34, 86)), (.28, (82, 86, 160)), (.5, (214, 140, 150)), (.62, (255, 186, 130)), (.7, (255, 214, 160))]))
    radial(img, 300 + cam * .95, horizon - 40, 700, (255, 200, 140), .45 + .03 * math.sin(u * 1.3))
    cloud_bands(img, 4, horizon - 900, horizon - 300, (255, 206, 190), .3, n=7, drift=u * 10 + cam * .9)


def taiga_horizon(img, u, cam, horizon=1260, wind=0.0, far=((120, 112, 160), (96, 88, 140)), mid=((70, 94, 104), (48, 66, 82)),
                  near=((48, 84, 66), (28, 50, 44)), haze_col=(240, 170, 150)):
    """Rolling taiga to the horizon: low hills, three forest rows with haze between (parallax by cam)."""
    peak_range(img, 41, horizon + 10, 50, 120, far[0], far[1], n=6, x_shift=cam * .85, snow_frac=0)
    T.forest_row(img, 42, horizon + 20, 40, 70, *far, n=60, x_shift=cam * .8, iw=0, t=u, wind=.01 + wind * .3)
    haze(img, horizon - 80, horizon + 80, haze_col, .5)
    T.forest_row(img, 43, horizon + 110, 90, 150, *mid, n=34, x_shift=cam * .6, iw=2, t=u, wind=.012 + wind * .6)
    haze(img, horizon + 60, horizon + 170, haze_col, .3)


# ---------------------------------------------------------------- s01a: the fireball, the blast (line 1)
BLAST_XY = (720, 1180)


def s01a(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-14, 14, smooth(u / max(D, .1)))
    tb = cue(3) - .06                                                   # "blast"
    sky_dawn(img, u, cam)
    cloud_bands(img, 7, 380, 900, (255, 170, 160), .45, n=5, drift=u * 14 + cam * .8)
    radial(img, 300 + cam * .95, 1180, 420, (255, 236, 190), .35)
    lay = layer(); stars(lay, 19, 70, 760, u)                           # the last dawn stars fade as it gets light
    lay.putalpha(lay.getchannel('A').point(lambda a: int(a * .7 * (1 - smooth(seg(u, -.5, 2.5)))))); img.alpha_composite(lay)
    bx, by = BLAST_XY[0] + cam * .9, BLAST_XY[1]
    k = smooth(seg(u, tb, tb + 1.6))                                     # explosion grows
    if u >= tb:
        v = u - tb
        radial(img, bx, by, 300 + 1100 * ease_out(v / 1.2), (255, 200, 120), .9 * (1 - .4 * smooth(v / 3)))
        radial(img, bx, by, 120 + 260 * ease_out(v / .6), (255, 250, 230), .95 * (1 - .5 * smooth(v / 2.5)), power=.8)
        # the fire column rises and mushrooms
        d = ImageDraw.Draw(img); rng = np.random.default_rng(8)
        top = by - 120 - 360 * ease_out(v / 2.4)
        col_pts = []
        for i in range(26):
            f = i / 25; y = by - (by - top) * f; r = 40 + 70 * f + 90 * f ** 4 * ease_out(v / 2.4)
            x = bx + 30 * math.sin(f * 7 + v * 2) + rng.uniform(-20, 20); col_pts.append((x, y, r, f))
        for x, y, r, f in col_pts:                                       # ink silhouette first: a hard flat-2D edge
            d.ellipse([x - r - 7, y - r * .8 - 7, x + r + 7, y + r * .8 + 7], fill=INK)
        for x, y, r, f in col_pts:
            col = lerp((255, 240, 190), (190, 70, 40), f * .8 + .2 * smooth(v / 3))
            d.ellipse([x - r, y - r * .8, x + r, y + r * .8], fill=col)
        cx_, cy_, cr = col_pts[-1][0], col_pts[-1][1], col_pts[-1][2]   # the cap: banded fire and a hot core
        for j, (kk, cc) in enumerate(((.75, (230, 110, 50)), (.5, (255, 170, 80)), (.28, (255, 236, 170)))):
            d.ellipse([cx_ - cr * kk, cy_ - cr * .8 * kk + cr * .1, cx_ + cr * kk, cy_ + cr * .8 * kk + cr * .1], fill=cc)
        radial(img, cx_, cy_, cr * 1.6, (255, 220, 150), .45)
        T.smoke(img, 3, (bx - 380, top - 60, bx + 380, by), u, color=(120, 70, 70), n=12, alpha=90, rise=.18)
        T.shock_ring(img, bx, by + 40, 80 + 1300 * ease_out(v / 1.4), 30 * (1 - v / 1.6), alpha=.8 * (1 - smooth(v / 1.5)), squash=.1)
    else:
        f = ease_in(seg(u, -.35, tb)) ** .8                               # the bolide streaks in (already in frame at 0)
        x0, y0 = 210, 390
        fx, fy = x0 + (bx - x0) * f, y0 + (by - 60 - y0) * f
        ang = math.atan2(by - 60 - y0, bx - x0); m = mask(); dm = ImageDraw.Draw(m)   # a long glowing trail behind it
        tx, ty = fx - math.cos(ang) * 900, fy - math.sin(ang) * 900; nx, ny = -math.sin(ang), math.cos(ang)
        dm.polygon([(fx + nx * 40, fy + ny * 40), (tx, ty), (fx - nx * 40, fy - ny * 40)], fill=255)
        glow(img, m, (255, 190, 120), .55, blur=30, add=True)
        dm.polygon([(fx + nx * 14, fy + ny * 14), (tx, ty), (fx - nx * 14, fy - ny * 14)], fill=255)
        fill_mask(img, m, (255, 240, 200), .7, blur=6)
        T.fireball(img, fx, fy, 74 + 10 * f, math.atan2(by - 60 - y0, bx - x0), 520 + 200 * f, u)
    wind = 1.0 * smooth(seg(u, tb + .25, tb + .7)) * (1 - .6 * smooth(seg(u, tb + 1.2, tb + 2.8)))
    taiga_horizon(img, u, cam, wind=-wind * .05)
    # near forest, bends away from the blast (left) as the shock arrives
    T.forest_row(img, 44, 1560, 260, 380, (40, 74, 58), (22, 42, 36), n=11, x_shift=cam * .3, iw=4, t=u,
                 wind=.014 - .09 * wind)
    haze(img, 1440, 1620, (240, 170, 150), .35)                          # mist between the rows
    d = ImageDraw.Draw(img); d.rectangle([0, 1600, W, H], fill=(22, 36, 32))
    rg = np.random.default_rng(46)
    for i in range(7):                                                   # tonal bands in the near ground
        y = 1620 + i * 46; d.ellipse([rg.uniform(-300, 600) + cam * .1, y, rg.uniform(700, 1400) + cam * .1, y + 40], fill=(30, 50, 42) if i % 2 else (26, 42, 36))
    for i in range(60):                                                  # grass tufts
        x, y = rg.uniform(0, W) - cam * .2, rg.uniform(1640, H); hgt = 18 + (y - 1600) * .06
        for dx in (-6, 0, 6): d.line([(x, y), (x + dx * 1.5 + 3 * math.sin(u * 2 + i), y - hgt)], fill=(70, 110, 76), width=4)
    for i in range(9):                                                   # rocks catching the dawn light
        x, y, r = rg.uniform(0, W) - cam * .2, rg.uniform(1700, H - 40), rg.uniform(18, 46)
        d.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=(60, 66, 70), outline=INK, width=4)
        d.chord([x - r * .8, y - r * .55, x + r * .8, y + r * .3], 180, 360, fill=(170, 140, 140))
    T.forest_row(img, 45, 1960, 420, 560, (32, 58, 46), (16, 30, 28), n=6, x_shift=cam * -.2, iw=5, t=u, wind=.016 - .12 * wind,
                 fill_below=False)
    if u >= tb:
        radial(img, bx, by, 900, (255, 170, 90), .25 * (1 - smooth(seg(u, tb, tb + 3))))
        dust(img, 5, 40, (0, 900, W, 1800), (255, 220, 170), 160, size=(2, 6), t=u * 3)
    flash(img, u, tb, .4)
    sx, sy = shake(u, tb + .05, 16, .6)
    img = finish(img, u, 1.03 + .05 * smooth(u / max(D, .1)), 540, 1100, dx=-cam + sx, dy=sy, vig=(.4, (20, 10, 30)))
    chip_t(img, '1908 · SIBERIA', (56, 70, 120), 540, 150, u, .1, size=54)
    slam_title(img, 's01a_1', [('A BLAST', 'white', 120)], 270, u, tb + .05)
    slam_title(img, 's01a_2', [('1,000× HIROSHIMA', (255, 176, 60), 92)], 410, u, cue(5) - .05)
    return img, {'faces': [], 'avoid': [(0, 0, W, 560)]}


# ---------------------------------------------------------------- s01b: no crater (line 1, "It left no crater.")
def s01b(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(10, -10, smooth(u / D))
    img.paste(vgrad([(0, (70, 50, 70)), (.35, (180, 112, 96)), (.55, (240, 168, 120)), (.62, (200, 140, 112))]))
    radial(img, 720 + cam * .9, 900, 700, (255, 170, 110), .5 + .04 * math.sin(u * 3))
    T.smoke(img, 11, (0, 300, W, 1000), u + 2, color=(90, 66, 70), n=18, alpha=150, rise=.1, size=(80, 200))
    d = ImageDraw.Draw(img)
    for k, (gy, hh, col) in enumerate(((1060, 170, (96, 70, 70)), (1120, 210, (80, 58, 56)))):   # far bare trunks in smoke
        rng = np.random.default_rng(20 + k)
        for i in range(18):
            x = rng.uniform(-40, W + 40) + cam * (.7 - .2 * k)
            T.bare_trunk(d, x, gy, hh * rng.uniform(.7, 1.1), 10 + 4 * k, col, lerp(col, (200, 150, 130), .3), iw=2 + k, seed=i, stubs=2)
    d.polygon([(0, 1150), (W, 1110), (W, H), (0, H)], fill=(110, 88, 70))
    haze(img, 1040, 1260, (214, 150, 120), .55)
    radial(img, 540 + cam * .5, 1150, 600, (255, 150, 80), .6 + .06 * math.sin(u * 4))   # the scorched centre still glows
    for j, sx in enumerate((180, 760, 980)):                             # smoke columns still rising off the ground
        T.smoke(img, 50 + j, (sx - 120 + cam * .6, 400, sx + 120 + cam * .6, 1150), u + j, color=(70, 52, 56), n=10, alpha=130, rise=.14, size=(50, 130))
    d = ImageDraw.Draw(img); ra = np.random.default_rng(55)
    for i in range(40):                                                  # ash patches and cracks in the scorched ground
        y = ra.uniform(1180, H); x = ra.uniform(-50, W + 50) + cam * .4; r = ra.uniform(30, 110) * (.5 + (y - 1150) / 900)
        d.ellipse([x - r, y - r * .3, x + r, y + r * .3], fill=(88, 70, 58) if i % 2 else (126, 102, 82))
        if i % 3 == 0: d.line([(x - r, y), (x - r * .3, y + 8), (x + r * .2, y - 6), (x + r, y + 4)], fill=(60, 46, 40), width=3)
    for i, (x, hh, w) in enumerate(((50, 640, 40), (200, 540, 30), (890, 560, 34), (1040, 680, 44))):   # near burnt trunks frame the shot
        T.bare_trunk(d, x + cam * 1.2, 1300 + i % 2 * 40, hh, w, (58, 40, 40), (190, 120, 96), iw=5, lean=(-3 if x < 540 else 3) + .5 * math.sin(u + i), seed=40 + i, stubs=4)
    # flattened logs on the ground, all lying away from the centre (left ones point left, right ones right)
    rng = np.random.default_rng(31)
    for i in range(16):
        side = -1 if i % 2 else 1; y = 1180 + i * 42; x = 540 + side * (230 + rng.uniform(0, 160) + i * 14) + cam * .4
        T.fallen_side(d, x, y, 160 + i * 14, 16 + i * 1.3, 0 if side > 0 else 180, seed=i,
                      col=(104, 78, 60), lit=(156, 122, 92))
    # the flat ground where a crater should be: a dashed outline, a "?" probe flag
    cx, cy = 540 + cam * .5, 1580
    k = smooth(seg(u, 0, .6))
    m = mask(); ImageDraw.Draw(m).ellipse([cx - 400 * k, cy - 140 * k, cx + 400 * k, cy + 140 * k], outline=255, width=30)
    glow(img, m, (255, 220, 170), .35 * k * (.85 + .15 * math.sin(u * 3)), blur=24, add=True); d = ImageDraw.Draw(img)
    d.ellipse([cx - 400 * k, cy - 140 * k, cx + 400 * k, cy + 140 * k], outline=(255, 200, 150), width=4)
    for j in range(36):
        if j % 2: continue
        a0, a1 = j * 10 + u * 12, j * 10 + 6 + u * 12
        d.arc([cx - 400 * k, cy - 140 * k, cx + 400 * k, cy + 140 * k], a0, a1, fill=(255, 244, 220), width=14)
    rng = np.random.default_rng(2)
    for i in range(16):                                                  # smouldering spots on the logs
        x, y = rng.uniform(40, W - 40), rng.uniform(1200, 1850)
        if 1280 < y < 1420: continue                                     # keep the caption band calm
        q = 5 + 3 * math.sin(u * 5 + i)
        radial(img, x, y, 80, (255, 120, 40), .6 + .2 * math.sin(u * 3 + i)); d = ImageDraw.Draw(img)
        d.ellipse([x - q * 1.6, y - q, x + q * 1.6, y + q], fill=(255, 200, 120))
    for i in range(30):                                                  # embers float up
        v = (rng.random() + u * .5) % 1; x = rng.uniform(0, W) + 40 * math.sin(u + i); y = 1800 - 1300 * v; q = 3 + 3 * (1 - v)
        d.ellipse([x - q, y - q, x + q, y + q], fill=(255, 190, 110))
    img = finish(img, u, 1.06 + .06 * smooth(u / D), 540, 1300, dx=-cam, vig=(.45, (30, 14, 20)))
    slam_title(img, 's01b', [('NO CRATER', (255, 76, 60), 140)], 330, u, cue(14) - .08)
    return img, {'faces': [], 'avoid': [(0, 0, W, 560)]}


# ---------------------------------------------------------------- s02: 80 million trees (line 2)
def _blob(cx, cy, r, seed, n=40, wob=.12):
    rng = np.random.default_rng(seed); ph = rng.uniform(0, 6, 4)
    return [(cx + r * (1 + wob * math.sin(3 * a + ph[0]) + wob * .6 * math.sin(5 * a + ph[1])) * math.cos(a),
             cy + r * (1 + wob * math.sin(2 * a + ph[2]) + wob * .5 * math.sin(7 * a + ph[3])) * math.sin(a))
            for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def ground_top(img, u, seed=5, base=(82, 96, 58), river=True):
    img.paste(vgrad([(0, lerp(base, (40, 50, 40), .2)), (1, lerp(base, (30, 40, 30), .35))]))
    d = ImageDraw.Draw(img); rng = np.random.default_rng(seed)
    for i in range(70):                                                  # moss / bog patches
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(30, 110)
        d.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=lerp(base, (120, 130, 70) if i % 3 else (60, 70, 50), .4))
    if river:
        pts = [(-40, 1500), (200, 1560), (420, 1700), (640, 1690), (860, 1800), (1120, 1840)]
        d.line(pts, fill=INK, width=44, joint='curve'); d.line(pts, fill=(90, 150, 190), width=32, joint='curve')
        d.line([(x, y - 6) for x, y in pts], fill=(170, 210, 230), width=6, joint='curve')


def counter_text(n):
    return f'{int(n):,}'


def s02(u, D, cue):
    img = Image.new('RGBA', (W, H))
    ground_top(img, u)
    cx, cy = 540, 900
    t_fl = cue(3) - .1
    wave = 40 + 560 * ease_out(seg(u, -.2, t_fl + .9))
    T.radial_treefall(img, cx, cy, 120, 560, seed=3, n=700, standing=40, wave=wave, w=8)
    if wave < 560:                                                       # the blast front sweeping outward
        T.shock_ring(img, cx, cy, wave + 10, 22, (255, 236, 200), .6, squash=1.0)
    rng = np.random.default_rng(9); lay = layer(); dl = ImageDraw.Draw(lay)
    for i in range(6):                                                   # cloud shadows drift over the land
        x = (rng.uniform(0, W) + u * 60) % (W + 600) - 300; y = rng.uniform(0, H); r = rng.uniform(160, 300)
        dl.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=(10, 20, 30, 70))
    img.alpha_composite(kit.soft_layer(lay, 40))
    d = ImageDraw.Draw(img)
    # London outline at "London": a dashed blob, smaller than the flattened forest
    t_lon = cue(12) - .1
    if u > t_lon:
        k = out_back(seg(u, t_lon, t_lon + .35), 1.5)
        pts = _blob(cx + 10, cy + 6, 500 * k, 4)
        m = mask(); ImageDraw.Draw(m).polygon(pts, fill=255); fill_mask(img, m, (60, 90, 170), .18)
        d.line(pts + [pts[0]], fill=INK, width=18); d.line(pts + [pts[0]], fill=(255, 255, 255), width=10)
        chip_t(img, 'LONDON', (40, 60, 120), cx, cy, u, t_lon + .1, size=72, angle=-4)
    # the forest edge (2,150 km²) traced in orange
    pts = _blob(cx, cy, 585, 7, 60, .05)
    d.line(pts + [pts[0]], fill=INK, width=12); d.line(pts + [pts[0]], fill=(255, 150, 60), width=6)
    img = finish(img, u, 1.0 + .07 * smooth(u / D), cx, cy, dx=10 * math.sin(u * .6), vig=(.4, (10, 14, 20)))
    # counter rolls up on "eighty million trees"
    t0, t1 = cue(4) - .1, cue(6) + .3
    if u > t0 - .2:
        n = 80_000_000 * ease_out(seg(u, t0, t1))
        s = pop(u, t0 - .2, .3, 1.6)
        def f(l, n=n):
            title(l, [(counter_text(n), (255, 214, 80), 118)], 40)
            title(l, [('TREES FLATTENED', 'white', 64)], 180)
        lay, (lx, ly) = anim.text_layer(f, W, 320)
        anim.scaled_paste(img, lay, 540, 230, s)
    return img, {'faces': [], 'avoid': [(0, 0, W, 400)]}


# ---------------------------------------------------------------- s03: the trader 60 km away (line 3)
def log_house(img, x0, x1, gy, top, t, shake_k=0.0, broken=0.0):
    """Vanavara trading post: a log house with a porch, a window that shatters (broken 0..1)."""
    d = ImageDraw.Draw(img); jx = shake_k * 6 * math.sin(t * 70)
    xa, xb = x0 + jx, x1 + jx
    d.polygon([(xa - 40, top + 20), ((xa + xb) / 2, top - 220), (xb + 40, top + 20)], fill=INK)
    d.polygon([(xa - 28, top + 12), ((xa + xb) / 2, top - 206), (xb + 28, top + 12)], fill=(120, 60, 46))
    d.polygon([((xa + xb) / 2, top - 206), (xb + 28, top + 12), ((xa + xb) / 2 + 40, top + 12)], fill=(90, 44, 36))
    d.rectangle([xa, top, xb, gy], fill=(150, 98, 60), outline=INK, width=6)
    for k in range(int((gy - top) / 46)):                                # logs
        y = top + 23 + k * 46
        d.line([(xa, y), (xb, y)], fill=(110, 70, 44), width=5)
        d.ellipse([xa - 18, y - 22, xa + 18, y + 22], fill=(186, 140, 96), outline=INK, width=3)
        d.ellipse([xb - 18, y - 22, xb + 18, y + 22], fill=(186, 140, 96), outline=INK, width=3)
    wx, wy = xa + (xb - xa) * .28, top + 90
    radial(img, wx + 70, wy + 80, 160, (255, 210, 140), .25 * (1 - broken))
    d.rectangle([wx, wy, wx + 140, wy + 170], fill=(40, 50, 70) if broken else (255, 214, 150), outline=INK, width=8)
    if not broken:
        d.line([(wx + 70, wy), (wx + 70, wy + 170)], fill=INK, width=6); d.line([(wx, wy + 85), (wx + 140, wy + 85)], fill=INK, width=6)
    else:
        for a in range(7):                                               # jagged remains of the glass
            aa = a * .9; d.line([(wx + 70, wy + 85), (wx + 70 + 80 * math.cos(aa), wy + 85 + 90 * math.sin(aa))], fill=(200, 230, 255), width=4)
    dx_, dy_ = xa + (xb - xa) * .66, top + 60
    d.rectangle([dx_, dy_, dx_ + 130, gy - 4], fill=(96, 60, 40), outline=INK, width=6)
    d.ellipse([dx_ + 100, (dy_ + gy) / 2, dx_ + 116, (dy_ + gy) / 2 + 16], fill=(230, 190, 90))
    return (wx + 70, wy + 85)


def s03(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-12, 12, smooth(u / D))
    t_th = cue(6) - .12; t_sh = cue(11) - .1
    img.paste(vgrad([(0, (120, 150, 200)), (.35, (196, 200, 220)), (.5, (250, 214, 176)), (.56, (255, 226, 190))]))
    # the flash on the far horizon, 60 km away (left)
    fx, fy = 120 + cam * .95, 960
    radial(img, fx, fy, 900, (255, 236, 190), .55 + .2 * math.sin(u * 7) * (u < 1.5))
    radial(img, fx, fy, 260, (255, 255, 240), .9, power=.7)
    cloud_bands(img, 9, 300, 800, (255, 236, 220), .3, n=5, drift=u * 18 + cam)
    T.forest_row(img, 52, 1000, 50, 90, (120, 130, 150), (96, 104, 130), n=40, x_shift=cam * .8, iw=0, t=u, wind=.01)
    haze(img, 930, 1060, (255, 226, 196), .55)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1040, W, H], fill=(150, 160, 104))
    d.polygon([(0, 1040), (W, 1040), (W, 1100), (0, 1120)], fill=(120, 134, 92))
    T.forest_row(img, 53, 1080, 120, 200, (70, 110, 80), (46, 80, 60), n=16, x_shift=cam * .6, iw=3, t=u,
                 wind=.012 - .07 * smooth(seg(u, t_th - .3, t_th)) * (1 - smooth(seg(u, t_th + .8, t_th + 2))), fill_below=False)
    # the shockwave front sweeps in from the left: a dust wall
    if t_th - .45 < u < t_th + .7:
        v = (u - (t_th - .45)) / 1.15; xw = -300 + 1700 * v
        lay = layer(); dl = ImageDraw.Draw(lay)
        for i in range(14):
            y = 1080 + i * 60; r = 140 + 30 * math.sin(i)
            dl.ellipse([xw - r * 1.6, y - r, xw + r * .4, y + r], fill=(230, 200, 160, 120))
        img.alpha_composite(kit.soft_layer(lay, 24))
    hk = smooth(seg(u, t_th - .05, t_th + .1)) * (1 - smooth(seg(u, t_th + .4, t_th + .9)))
    win = log_house(img, 380 + cam * .2, 1000 + cam * .2, 1500, 1060, u, hk, broken=float(u > t_th))
    d = ImageDraw.Draw(img)
    # the porch: raised boards and steps
    px0, px1, py = 330 + cam * .2, 1040 + cam * .2, 1500
    d.rectangle([px0, py, px1, py + 40], fill=(170, 120, 76), outline=INK, width=6)
    for k in range(4): d.line([(px0 + 40 + k * 190, py + 40), (px0 + 40 + k * 190, py + 150)], fill=INK, width=16)
    for k in range(3): d.rectangle([px0 - 70 - k * 0, py + 40 + k * 40, px0 + 40, py + 80 + k * 40], fill=(150, 104, 66), outline=INK, width=5)
    d.rectangle([0, 1650, W, H], fill=(132, 146, 94))
    rng = np.random.default_rng(5)
    for i in range(40):
        x, y = rng.uniform(0, W), rng.uniform(1660, H); d.line([(x, y), (x + 6, y - 22)], fill=(96, 120, 70), width=4)
    if u > t_th:                                                          # glass shards burst from the window
        v = u - t_th; rng = np.random.default_rng(3)
        for i in range(16):
            vx, vy = rng.uniform(80, 520), rng.uniform(-420, 60); q = rng.uniform(8, 18)
            x = win[0] + vx * v; y = win[1] + vy * v + 1300 * v * v
            if y < H: d.polygon([(x, y - q), (x + q * .7, y + q * .4), (x - q * .5, y + q * .6)], fill=(214, 236, 255), outline=INK)
    # the trader: on the porch, startled by the light, then thrown off it (to the right), lands, his shirt hot
    t_land = t_th + .55
    if u < t_th:
        pose = chain(u, [(0, STAND), (.5, add(STAND, armR=(-70, -60)), lambda f: out_back(f, 1.4))])  # shields his eyes
        x, gy, lean, hop, expr = 600 + cam * .2, py, -3 * smooth(seg(u, .3, 1)), 0, 'worried'
    elif u < t_land:
        v = (u - t_th) / (t_land - t_th)
        pose = mix(STAND, dict(POSES['cheer']), smooth(v * 2))
        x = 600 + cam * .2 + 280 * ease_out(v); gy = py + 300 * v * v
        hop = 260 * math.sin(math.pi * v) * (1 - v * .3); lean, expr = 70 * smooth(v), 'scared'
    else:
        v = u - t_land
        grab = dict(STAND, armL=(40, 120), armR=(-40, -120))                      # hands to his hot shirt
        pose = chain(v, [(0, dict(POSES['cheer'])), (.35, STAND), (max(.5, t_sh - t_land), grab, lambda f: out_back(f, 1.6))])
        x, gy = 880 + cam * .2, 1800
        lean = 70 - 62 * out_back(seg(v, .05, .55), 1.4) + 3 * math.sin(v * 9) * smooth(seg(u, t_sh, t_sh + .3))
        hop, expr = 0, 'scared' if u < t_sh else 'worried'
    g = trader(img, u, pose, expr, x, gy, .6, look=-.4, lean=lean, hop=hop, heat=smooth(seg(u, t_sh - .2, t_sh + .4)),
               label_on=u < t_th or u > t_land + .2)
    if u >= t_land and u < t_land + .4:                                  # landing dust
        T.smoke(img, 4, (700, 1640, 1060, 1820), u, color=(210, 190, 150), n=10, alpha=int(180 * (1 - (u - t_land) / .4)), rise=.6, size=(30, 70))
    flash(img, u, t_th, .2, .5, (255, 240, 210))
    sx, sy = shake(u, t_th, 18, .5)
    img = finish(img, u, 1.04 + .04 * smooth(u / D), 600, 1300, dx=-cam + sx, dy=sy, vig=(.38, (30, 20, 30)))
    # 60 KM: a dashed line from the post to the flash
    s = pop(u, cue(0), .3, 1.8)
    if s > .01:
        d = ImageDraw.Draw(img); k = smooth(seg(u, cue(0), cue(2)))
        T.dashed(d, (470, 860), (470 - (470 - 170) * k, 860 + 60 * k), (255, 255, 255), 7, 26, 16, phase=u * 60)
        put_chip(img, '60 KM', (232, 118, 36), 250, 700, s, size=66, angle=-3)
    return img, {'faces': [face_box(g)]}


# ---------------------------------------------------------------- s04a: 1927, Kulik sets out (line 4)
def forest_floor(img, y0, cam, col=(70, 96, 60), moss=(104, 140, 76), snow=(232, 238, 244), seed=8):
    d = ImageDraw.Draw(img); d.rectangle([0, y0, W, H], fill=col)
    rng = np.random.default_rng(seed)
    for i in range(36):
        x = (rng.uniform(0, W * 1.6) + cam) % (W * 1.6) - W * .3; y = rng.uniform(y0 + 20, H); r = rng.uniform(30, 90) * (y - y0 + 200) / 600
        d.ellipse([x - r, y - r * .3, x + r, y + r * .3], fill=moss if i % 4 else snow)


def s04a(u, D, cue):
    img = Image.new('RGBA', (W, H))
    tr = B._walk_cache(round(D + .1, 2)); s = .78
    f = min(len(tr) - 1, int(round(u * 30)))
    travel = (tr[f] - tr[0]) * s                                          # the hip's foot-locked travel (px)
    cam = -travel
    img.paste(vgrad([(0, (120, 170, 200)), (.4, (196, 220, 210)), (.55, (232, 236, 210))]))
    light_rays(img, 860, -100, (255, 246, 210), n=8, alpha=.2 + .03 * math.sin(u * 2), spread=(100, 150), seed=4, phase=math.sin(u * .5))
    T.forest_row(img, 61, 980, 280, 420, (110, 150, 140), (84, 120, 120), n=18, x_shift=cam * .15, iw=0, t=u)
    haze(img, 700, 1060, (226, 236, 220), .5)
    T.forest_row(img, 62, 1180, 420, 600, (64, 112, 84), (40, 80, 62), n=12, x_shift=cam * .35, iw=3, t=u)
    haze(img, 1000, 1240, (210, 226, 206), .35)
    forest_floor(img, 1180, cam * .6)
    T.forest_row(img, 63, 1500, 700, 900, (46, 90, 64), (26, 60, 46), n=5, x_shift=cam * .6, iw=5, t=u, fill_below=False,
                 x_range=(-300, W + 300))
    forest_floor(img, 1700, cam, col=(60, 84, 54), seed=9)
    pose = anim.walk_pose(u + .3)
    g = kulik(img, u, pose, 'determined', 460, 1820, s, look=.7, lean=3, side=-1, prop='compass', label_on=u > cue(5) - .15)
    T.forest_row(img, 64, 2100, 1300, 1500, (22, 44, 34), (12, 28, 24), n=3, x_shift=cam * 1.4, iw=6, t=u, fill_below=False,
                 x_range=(-500, W + 500))
    snow_particles(img, 64, n=(30, 12, 4), wind=(2, 1), t=u, alpha=(140, 150, 120))
    img = finish(img, u, 1.03 + .03 * smooth(u / D), 520, 1300, vig=(.36, (16, 30, 26)))
    s1 = pop(u, cue(0) - .05, .3, 1.8)
    if s1 > .01:
        def f1(l):
            title(l, [('1927', (255, 214, 80), 150)], 30)
            title(l, [('19 YEARS LATER', 'white', 60)], 200)
        lay, _ = anim.text_layer(f1, W, 320)
        anim.scaled_paste(img, lay, 540, 240, s1)
    t_m = cue(10) - .1
    sm = pop(u, t_m, .35, 1.8)
    if sm > .01:                                                         # the target: a meteorite
        lay = layer(300, 300); d = ImageDraw.Draw(lay)
        d.ellipse([20, 20, 280, 280], fill=(250, 246, 236), outline=INK, width=8)
        T.rock(d, 150, 150, 70, ang=u, seed=4)
        for a in range(4):
            aa = a * math.pi / 2; d.line([(150 + math.cos(aa) * 95, 150 + math.sin(aa) * 95), (150 + math.cos(aa) * 128, 150 + math.sin(aa) * 128)], fill=(220, 40, 40), width=10)
        d.ellipse([40, 40, 260, 260], outline=(220, 40, 40), width=7)
        anim.scaled_paste(img, lay, 850, 620, sm * .9, angle=4 * math.sin(u * 2))
        put_chip(img, 'METEORITE', (90, 80, 110), 850, 800, sm, size=44)
    return img, {'faces': [face_box(g)], 'avoid': [(0, 0, W, 420)]}


# ---------------------------------------------------------------- s04b: "find the crater, find the iron"
def campfire(img, x, gy, t, s=1.0):
    d = ImageDraw.Draw(img)
    radial(img, x, gy - 60 * s, 520 * s, (255, 150, 60), .5 + .08 * math.sin(t * 11) * math.sin(t * 3.7))
    for k in (-1, 1):
        d.line([(x - 90 * s * k, gy + 10), (x + 90 * s * k, gy - 20 * s)], fill=INK, width=int(34 * s)); d.line([(x - 86 * s * k, gy + 10), (x + 86 * s * k, gy - 20 * s)], fill=(110, 70, 44), width=int(24 * s))
    for i in range(5):
        ph = t * 9 + i * 1.7; h = (110 + 40 * math.sin(ph)) * s * (1 - abs(i - 2) * .18); w = 30 * s
        xx = x + (i - 2) * 26 * s
        d.polygon([(xx - w, gy - 10), (xx + 6 * math.sin(ph), gy - 10 - h), (xx + w, gy - 10)], fill=(255, 140, 40))
        d.polygon([(xx - w * .5, gy - 10), (xx + 4 * math.sin(ph), gy - 10 - h * .6), (xx + w * .5, gy - 10)], fill=(255, 226, 120))
    rng = np.random.default_rng(1)
    for i in range(10):
        v = (rng.random() + t * .7) % 1; px = x + rng.uniform(-60, 60) * s + 30 * math.sin(t * 2 + i); py = gy - 60 * s - 500 * s * v; q = 4 * (1 - v) + 1
        d.ellipse([px - q, py - q, px + q, py + q], fill=(255, 200, 100))


def s04b(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(10, -10, smooth(u / D))
    img.paste(vgrad([(0, (10, 14, 40)), (.5, (24, 34, 70)), (.62, (40, 50, 80))]))
    stars(img, 7, 90, 1000, u)
    T.forest_row(img, 71, 1180, 260, 420, (24, 34, 52), (16, 24, 40), n=22, x_shift=cam * .5, iw=0, t=u)
    d = ImageDraw.Draw(img); d.rectangle([0, 1200, W, H], fill=(30, 34, 44))
    B.tent(img, 700 + cam * .3, 1420, u)
    campfire(img, 250 + cam * .2, 1660, u, 1.0)
    g = kulik(img, u, chain(u, [(0, dict(POSES['hold'])), (cue(14) - .3, dict(POSES['think']), lambda f: out_back(f, 1.4)),
                                 (cue(17) - .2, dict(POSES['point'], armR=(-120, -150)), lambda f: out_back(f, 1.8))]),
              'thinking' if u < cue(17) else 'determined', 560, 1850, .74, look=.3,
              rim=(255, 170, 90), rim_dir=(-1, -.2), aura_a=.32)
    hx, hy = g['head']
    s = smooth(seg(u, cue(13) - .3, cue(13) + .25)) * (1 + .06 * math.sin(math.pi * seg(u, cue(13) + .05, cue(13) + .45)))
    lay = thought(img, 560, 520, 430, 230, (hx + 40, hy - 160), 1.0)
    if lay is not None:
        dl = ImageDraw.Draw(lay)
        sc = pop(u, cue(14), .3, 2)
        if sc > .01: crater_icon(dl, 330, 470, 120 * min(1.1, sc))
        si = pop(u, cue(17), .3, 2)
        if sc > .01:
            k = smooth(seg(u, cue(16), cue(17)))
            dl.line([(470, 470), (470 + 120 * k, 470)], fill=INK, width=22)
            if k > .9: dl.polygon([(600, 470), (560, 440), (560, 500)], fill=INK)
        if si > .01: iron_lump(dl, 760, 470, 90 * min(1.1, si))
        if sc > .01: pill(lay, 'CRATER', 330, 620, (150, 100, 70), size=40, pad=18)
        if si > .01: pill(lay, 'IRON', 760, 620, (90, 96, 116), size=40, pad=18)
        paste_grown(img, lay, hx + 40, hy - 160, s)
    img = finish(img, u, 1.04 + .04 * smooth(u / D), 540, 1200, dx=-cam, vig=(.45, (6, 8, 20)))
    return img, {'faces': [face_box(g)], 'avoid': [(0, 250, W, 800)]}


# ---------------------------------------------------------------- s05: CLUE 1, no crater, no hole, no rock
def bog_ground(img, y0, cam, sky=(200, 210, 214), base=(110, 116, 84), seed=3):
    d = ImageDraw.Draw(img); d.rectangle([0, y0, W, H], fill=base)
    rng = np.random.default_rng(seed)
    for i in range(14):                                                  # puddles reflect the sky
        y = rng.uniform(y0 + 30, H - 40); x = rng.uniform(-100, W) + cam * (y - y0) / 800; r = rng.uniform(60, 180) * (y - y0 + 300) / 900
        d.ellipse([x - r, y - r * .22, x + r, y + r * .22], fill=lerp(sky, (150, 170, 180), .3), outline=lerp(base, INK, .5), width=3)
    for i in range(60):
        y = rng.uniform(y0, H); x = rng.uniform(0, W) + cam * (y - y0) / 800
        d.line([(x, y), (x + rng.uniform(-8, 8), y - 18 - (y - y0) * .03)], fill=lerp(base, (60, 70, 40), .5), width=4)


def s05(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-14, 14, smooth(u / D))
    img.paste(vgrad([(0, (150, 168, 184)), (.45, (206, 212, 214)), (.58, (226, 226, 216))]))
    cloud_bands(img, 12, 200, 900, (240, 242, 244), .4, n=6, drift=u * 14 + cam)
    d = ImageDraw.Draw(img); rng = np.random.default_rng(14)
    for i in range(22):                                                  # far bare trunks in the mist
        x = rng.uniform(-30, W + 30) + cam * .8
        T.bare_trunk(d, x, 1130, rng.uniform(150, 260), 12, (120, 116, 118), (160, 156, 156), iw=2, seed=i, stubs=2)
    haze(img, 980, 1180, (226, 228, 222), .6)
    bog_ground(img, 1120, cam * .5)
    d = ImageDraw.Draw(img); rng = np.random.default_rng(15)
    for i in range(10):                                                  # fallen logs, lying away from the centre
        side = -1 if i % 2 else 1; y = 1170 + i * 30; x = 540 + side * (380 + i * 30) + cam * .4
        T.fallen_side(d, x, y, 220, 18, 0 if side > 0 else 180, col=(110, 92, 76), lit=(160, 140, 118), seed=i)
    # the dashed ring where a crater should be; a red X draws over it on "no crater"
    cx, cy = 680 + cam * .3, 1560
    for j in range(36):
        if j % 2: continue
        d.arc([cx - 300, cy - 96, cx + 300, cy + 96], j * 10 + u * 10, j * 10 + 6 + u * 10, fill=(255, 255, 255), width=10)
    radial(img, cx, cy, 300, (255, 240, 200), .12 + .05 * math.sin(u * 4))
    draw_x(img, cx, cy, 110, seg(u, cue(4) - .05, cue(5) + .3) * 2, w=26)
    t_p = cue(4) - .2
    pose = chain(u, [(0, dict(POSES['hold'])), (t_p, add(STAND, armR=(-20, -20))), (t_p + .35, dict(POSES['shrug']), lambda f: out_back(f, 1.6))])
    g = kulik(img, u, pose, 'thinking' if u < t_p else 'worried', 300 + cam * .2, 1800, .74, look=.5, rim=(255, 240, 220), prop='shovel',
              lean=2 * math.sin(u * 1.4))
    # NO HOLE / NO ROCK chips with icons
    for t_, txt, y, icon in ((cue(6) - .1, 'NO HOLE', 600, 'hole'), (cue(8) - .1, 'NO ROCK', 820, 'rock')):
        s = pop(u, t_, .3, 2.0)
        if s <= .01: continue
        lay = layer(560, 200); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([10, 16, 550, 190], 60, fill=INK); dl.rounded_rectangle([4, 8, 544, 182], 60, fill=(250, 248, 242), outline=INK, width=6)
        if icon == 'hole': crater_icon(dl, 100, 95, 60)
        else: T.rock(dl, 100, 95, 50, seed=3)
        draw_x(lay, 100, 95, 52, 2, w=14)
        dl.text((190, 98), txt, font=font(66), fill=(200, 40, 40), anchor='lm')
        anim.scaled_paste(lay if False else img, lay, 720, y, s, angle=-2 + 2 * math.sin(u * 2))
    img = finish(img, u, 1.03 + .04 * smooth(u / D), 540, 1300, dx=-cam, vig=(.34, (30, 34, 40)))
    clue(img, 'CLUE 1', u)
    return img, {'faces': [face_box(g)], 'avoid': [(380, 500, W, 920)]}


# ---------------------------------------------------------------- s06: CLUE 2, the survey map
def survey_map(u):
    def build():
        img = Image.new('RGBA', (W + 200, H + 200)); img.paste(vgrad([(0, (236, 222, 186)), (1, (220, 200, 160))], W + 200, H + 200))
        d = ImageDraw.Draw(img); rng = np.random.default_rng(6)
        for i in range(400):                                             # paper fibres
            x, y = rng.uniform(0, W + 200), rng.uniform(0, H + 200); d.line([(x, y), (x + rng.uniform(-14, 14), y + rng.uniform(-3, 3))], fill=(206, 186, 146), width=2)
        for x in range(0, W + 200, 120): d.line([(x, 0), (x, H + 200)], fill=(196, 176, 140), width=2)
        for y in range(0, H + 200, 120): d.line([(0, y), (W + 200, y)], fill=(196, 176, 140), width=2)
        for k in range(7):                                               # contour lines
            pts = _blob(640, 1000, 160 + k * 95, 30 + k, 50, .18)
            d.line(pts + [pts[0]], fill=(176, 140, 100), width=3)
        pts = [(-40, 1640), (240, 1600), (420, 1720), (700, 1700), (900, 1820), (1300, 1860)]
        d.line(pts, fill=(90, 130, 170), width=18, joint='curve')
        d.text((140, 1790), 'R. KHUSHMO', font=font(34, True), fill=(90, 120, 160))
        cx, cy = 1100, 360                                               # compass rose
        for a in range(8):
            aa = a * math.pi / 4; L = 110 if a % 2 == 0 else 60
            d.polygon([(cx + math.cos(aa) * L, cy + math.sin(aa) * L), (cx + math.cos(aa + .3) * 18, cy + math.sin(aa + .3) * 18), (cx, cy), (cx + math.cos(aa - .3) * 18, cy + math.sin(aa - .3) * 18)],
                      fill=(150, 60, 50) if a % 2 == 0 else (120, 100, 80))
        d.text((cx, cy - 140), 'N', font=font(48), fill=(150, 60, 50), anchor='mm')
        radial(img, 300, 1300, 120, (180, 140, 90), .25, add=False)        # a tea stain
        d.text((120, 2000), 'TUNGUSKA SURVEY · 1927', font=font(40, True), fill=(120, 90, 60))
        return img
    return T.cached('survey', build)


def s06(u, D, cue):
    img = Image.new('RGBA', (W, H))
    ox, oy = -100 + 30 * smooth(u / D), -100 - 20 * smooth(u / D)
    img.alpha_composite(survey_map(u), (int(ox), int(oy)))
    cx, cy = 540 + ox + 100, 1000 + oy + 100
    t_tr, t_out, t_spot = cue(3) - .1, cue(7) - .1, cue(10) - .1
    rmax = 140 + 380 * ease_out(seg(u, t_tr - .3, t_tr + 1.0))           # the pencil maps the trunks, ring by ring
    lay = layer(); dl = ImageDraw.Draw(lay)
    logs, poles = T.treefall_items(11, 110, 520, 420, 30)
    for r, a, lk, da in logs:
        if r > rmax: continue
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r; L = 38 * lk; ang = a + da
        dl.line([(x, y), (x + math.cos(ang) * L, y + math.sin(ang) * L)], fill=(60, 44, 36), width=6)
        dl.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(60, 44, 36))
    for r, a in poles:
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r; dl.ellipse([x - 7, y - 7, x + 7, y + 7], outline=(40, 90, 60), width=4)
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    pa = u * 1.1                                                         # the pencil sweeping around the ring edge
    if u < t_out + .3:
        px, py = cx + math.cos(pa) * rmax, cy + math.sin(pa) * rmax
        d.line([(px, py), (px + 140, py - 260)], fill=INK, width=34); d.line([(px, py), (px + 140, py - 260)], fill=(240, 196, 60), width=24)
        d.polygon([(px, py), (px + 8, py - 30), (px + 26, py - 22)], fill=(60, 50, 40))
    for i in range(8):                                                   # red arrows outward from one spot
        k = out_back(seg(u, t_out + i * .05, t_out + .45 + i * .05), 1.3)
        if k <= 0: continue
        a = i * math.pi / 4 + .2; r0, r1 = 70, 70 + 460 * k
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0); p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        d.line([p0, p1], fill=INK, width=24); d.line([p0, p1], fill=(220, 50, 44), width=14)
        nx, ny = -math.sin(a), math.cos(a); tip = (p1[0] + math.cos(a) * 40, p1[1] + math.sin(a) * 40)
        d.polygon([tip, (p1[0] + nx * 30, p1[1] + ny * 30), (p1[0] - nx * 30, p1[1] - ny * 30)], fill=(220, 50, 44), outline=INK)
    s = pop(u, t_spot, .3, 2.0)
    if s > .01:
        for k in range(2):
            v = ((u - t_spot) * .9 + k * .5) % 1
            d.ellipse([cx - 40 - 120 * v, cy - 40 - 120 * v, cx + 40 + 120 * v, cy + 40 + 120 * v], outline=(220, 50, 44), width=int(8 * (1 - v)) + 1)
        r = 34 * s; d.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6], fill=INK); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 50, 44))
        put_chip(img, 'ONE SPOT', (200, 46, 40), cx, cy - 150, s, size=56)
    img = finish(img, u, 1.02 + .05 * smooth(u / D), 540, 1000, vig=(.32, (60, 40, 20)))
    clue(img, 'CLUE 2', u)
    return img, {'faces': [], 'avoid': [(0, 0, W, 380)]}


# ---------------------------------------------------------------- s07: CLUE 3, bare trunks still standing
def telegraph_pole(d, x, gy, h, s=1.0, t=0.0):
    d.line([(x, gy), (x, gy - h)], fill=INK, width=int(30 * s)); d.line([(x, gy), (x, gy - h)], fill=(130, 98, 70), width=int(20 * s))
    for k, yy in enumerate((gy - h + 40 * s, gy - h + 110 * s)):
        w = (130 if k == 0 else 100) * s
        d.line([(x - w, yy), (x + w, yy)], fill=INK, width=int(22 * s)); d.line([(x - w, yy), (x + w, yy)], fill=(120, 90, 64), width=int(13 * s))
        for j in (-1, -.4, .4, 1):
            q = 10 * s; ix = x + j * w * .85
            d.ellipse([ix - q, yy - q * 2, ix + q, yy], fill=(140, 200, 180), outline=INK, width=3)
            sag = 30 * s + 4 * math.sin(t * 2 + j)
            d.line([(ix, yy - q), (ix - 260 * s, yy + sag), ], fill=INK, width=3)
            d.line([(ix, yy - q), (ix + 260 * s, yy + sag)], fill=INK, width=3)


def s07(u, D, cue):
    img = Image.new('RGBA', (W, H))
    tilt = 160 * smooth(seg(u, .3, D))                                   # the camera tilts up the trunks
    img.paste(vgrad([(0, (96, 110, 140)), (.5, (170, 182, 200)), (.75, (206, 212, 218))]))
    cloud_bands(img, 21, 100, 1000, (226, 230, 238), .35, n=6, drift=u * 20)
    d = ImageDraw.Draw(img); rng = np.random.default_rng(7)
    for layer_i, (n, gy, hmin, hmax, w, col, lit) in enumerate((
            (16, 1300, 500, 800, 16, (110, 104, 108), (150, 146, 150)),
            (10, 1480, 800, 1100, 26, (92, 78, 72), (140, 120, 104)),
            (6, 1760, 1300, 1600, 44, (80, 62, 54), (136, 108, 88)))):
        for i in range(n):
            x = rng.uniform(-40, W + 40); lean = (x - 540) / 540 * (6 + layer_i * 4)       # perspective: they splay outward
            T.bare_trunk(d, x, gy + tilt * (.4 + layer_i * .3), rng.uniform(hmin, hmax), w, col, lit, iw=3 + layer_i, lean=lean + .6 * math.sin(u + i), seed=i + 10 * layer_i, stubs=3)
        if layer_i == 0: haze(img, 900, 1340, (210, 214, 220), .5); d = ImageDraw.Draw(img)
    gy0 = 1500 + tilt * .9
    d.rectangle([0, gy0, W, H], fill=(98, 102, 80))
    for i in range(8):                                                   # the ring of fallen logs out at the edges
        side = -1 if i % 2 else 1
        T.fallen_side(d, 540 + side * (420 + i * 20), gy0 + 40 + i * 30, 240, 22, 0 if side > 0 else 180, col=(104, 86, 70), lit=(150, 130, 108), seed=i)
    t_up = cue(9) - .2
    pose = chain(u, [(0, STAND), (t_up, add(STAND, armR=(-20, -10))), (t_up + .4, dict(POSES['point'], armR=(-150, -160)), lambda f: out_back(f, 1.7))])
    g = kulik(img, u, pose, 'surprised' if u > t_up else 'neutral', 520, 1840 + tilt * .9, .7, look=-.2, lean=-6 * smooth(seg(u, t_up, t_up + .5)),
              rim=(220, 230, 255), rim_dir=(0, -1))
    t_tg = cue(14) - .15
    s = pop(u, t_tg, .35, 1.7)
    if s > .01:
        lay = layer(520, 760); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([14, 14, 506, 746], 40, fill=INK); dl.rounded_rectangle([6, 6, 498, 738], 40, fill=(236, 230, 214), outline=INK, width=6)
        T.bare_trunk(dl, 150, 690, 560, 40, (92, 72, 60), (150, 120, 100), seed=4, stubs=3)
        dl.text((255, 400), '=', font=font(110), fill=INK, anchor='mm')
        telegraph_pole(dl, 380, 690, 600, .8, u)
        anim.scaled_paste(img, lay, 830, 760, s * .82, angle=3 + 2 * math.sin(u * 2))
    img = finish(img, u, 1.04 + .04 * smooth(u / D), 540, 1200, dx=8 * math.sin(u * .7), vig=(.36, (30, 34, 50)))
    clue(img, 'CLUE 3', u)
    t_st = cue(9) - .1
    if u > t_st: put_chip(img, 'STILL STANDING', (40, 120, 110), 540, 440, pop(u, t_st, .3, 2), size=58, angle=-3)
    return img, {'faces': [face_box(g)], 'avoid': [(560, 440, W, 1100)]}


# ---------------------------------------------------------------- s08: "So what explodes...?"
def diagram_disc(img, cx, cy, R0, R1, squash, u, glow_ring=1.0, glow_centre=1.0, seed=3, n=150, palette='neon'):
    """The riddle as a phone-readable diagram: a ground disc, a ring of thick fallen logs pointing outward,
    a clear gap, and a cluster of tall upright bare trunks at the centre."""
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R1 - 40, cy - (R1 + 40) * squash, cx + R1 + 40, cy + (R1 + 40) * squash], fill=(20, 34, 60), outline=(60, 90, 140), width=4)
    d.ellipse([cx - R0 * .95, cy - R0 * .95 * squash, cx + R0 * .95, cy + R0 * .95 * squash], fill=(26, 56, 74))
    logs, poles = T.treefall_items(seed, R0 + 60, R1, n, 15)
    ring = (255, 150, 60) if palette == 'neon' else (126, 96, 68)
    for r, a, lk, da in logs:
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * squash
        ang = math.atan2(math.sin(a + da) * squash, math.cos(a + da)); L = 64 * lk
        e = (x + math.cos(ang) * L, y + math.sin(ang) * L)
        d.line([(x, y), e], fill=INK, width=24); d.line([(x, y), e], fill=lerp((110, 80, 60), ring, glow_ring), width=13)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=INK); d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=lerp((140, 100, 70), (255, 210, 140), glow_ring))
    col = lerp((110, 120, 130), (130, 240, 255), glow_centre)
    for r, a in sorted(poles, key=lambda p: math.sin(p[1]) * p[0]):
        x, y = cx + math.cos(a) * r * .95, cy + math.sin(a) * r * .95 * squash; h = 150 + 30 * math.sin(a * 3)
        sw = 2 * math.sin(u * 1.3 + a * 4)                                # a faint sway: they are still standing
        d.ellipse([x - 16, y - 6, x + 16, y + 6], fill=(10, 18, 30))
        d.line([(x, y), (x + sw, y - h)], fill=INK, width=22); d.line([(x, y), (x + sw, y - h)], fill=col, width=11)
        for k in (.45, .7):                                               # broken branch stubs
            sy = y - h * k; dd = 16 if (int(r) + int(k * 10)) % 2 else -16
            d.line([(x + sw * k, sy), (x + sw * k + dd, sy - 12)], fill=INK, width=9); d.line([(x + sw * k, sy), (x + sw * k + dd, sy - 12)], fill=col, width=4)


def _leader(img, a, b, col, k):
    """A thin label leader line drawn from a toward b, k = 0..1 grown."""
    if k <= .01: return
    d = ImageDraw.Draw(img); e = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
    d.line([a, e], fill=INK, width=9); d.line([a, e], fill=col, width=4)
    if k > .95: d.ellipse([b[0] - 10, b[1] - 10, b[0] + 10, b[1] + 10], fill=col, outline=INK, width=3)


def s08(u, D, cue):
    """v3 layout (Director: composition 7 -> one clear composition): a vertical stack on the centre line,
    ? (top) -> fireball -> the diagram disc, with margins on both sides; the two labels sit on the right with
    leader lines, Kulik full figure bottom-left looking up at it; the caption band (~70%) is kept empty."""
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (6, 10, 30)), (.6, (14, 24, 56)), (1, (8, 12, 30))]))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(22, 36, 74), width=2)
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(22, 36, 74), width=2)
    stars(img, 88, 40, H, u)
    cx, cy, sq = 540, 1070, .55
    t_ex, t_fl, t_st = cue(2) - .1, cue(3) - .1, cue(10) - .15
    g_ring = smooth(seg(u, t_fl, t_fl + .4)); g_c = smooth(seg(u, t_st - .5, t_st))
    for j in range(3):                                                   # faint concentric shock rings on the ground
        rr = 470 + j * 70; ImageDraw.Draw(img).ellipse([cx - rr, cy - rr * sq, cx + rr, cy + rr * sq], outline=(40, 60, 110), width=3)
    m = mask(); ImageDraw.Draw(m).ellipse([cx - 420, cy - 420 * sq, cx + 420, cy + 420 * sq], outline=255, width=80)
    glow(img, m, (255, 130, 50), .4 * g_ring * (.8 + .2 * math.sin(u * 4)), blur=50, add=True)
    diagram_disc(img, cx, cy, 160, 400, sq, u, .3 + .5 * g_ring, .4 + .6 * g_c, n=110)
    radial(img, cx, cy - 60, 200, (100, 230, 255), .45 * g_c * (.8 + .2 * math.sin(u * 5)))
    by = 640
    if u > t_ex:                                                         # the burst above the disc
        v = u - t_ex
        radial(img, cx, by, 260 * ease_out(v / .4) + 60, (255, 230, 170), .8 * (1 - .3 * smooth(v / 2)))
        fire_cloud(img, cx, by, u, v, .44)
        T.shock_ring(img, cx, by, 60 + 300 * ease_out(v / .8), 18, (255, 220, 160), .6 * (1 - smooth(v / 1.2)), squash=.4)
        d = ImageDraw.Draw(img)                                           # the dashed blast lines down to the ground
        k = smooth(seg(v, .2, .8))
        for sx in (-1, 0, 1):
            a0 = (cx + sx * 90, by + 120); a1 = (cx + sx * 250, cy - 200 + abs(sx) * 40)
            for j in range(8):
                f0, f1 = j / 8, j / 8 + .07
                if f1 > k: break
                d.line([(a0[0] + (a1[0] - a0[0]) * f0, a0[1] + (a1[1] - a0[1]) * f0), (a0[0] + (a1[0] - a0[0]) * f1, a0[1] + (a1[1] - a0[1]) * f1)], fill=(255, 210, 150), width=6)
    # labels on the right, with leader lines into the diagram
    k1 = smooth(seg(u, t_st, t_st + .3)); k2 = smooth(seg(u, t_fl + .1, t_fl + .4))
    _leader(img, (850, 640), (680, 900), (130, 240, 255), k1)
    _leader(img, (860, 1560), (860, 1250), (255, 170, 80), k2)
    chip_t(img, 'STANDING', (30, 150, 170), 850, 600, u, t_st, size=58, angle=3)
    chip_t(img, 'FLAT', (200, 100, 40), 860, 1600, u, t_fl + .1, size=76, angle=-3)
    g = kulik(img, u, chain(u, [(0, STAND), (.4, dict(POSES['think']), lambda f: out_back(f, 1.4))]), 'thinking', 185, 1830, .62,
              look=.5, label_on=False, rim=(150, 200, 255), aura_a=.5)
    img = finish(img, u, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.45, (2, 4, 14)))
    q = slam(u, cue(1) - .05, .3, 1.5)
    if q > 0:
        lay = layer(520, 700); dl = ImageDraw.Draw(lay)
        dl.text((266, 366), '?', font=font(520), fill=(20, 6, 10), anchor='mm')
        dl.text((260, 350), '?', font=font(520), fill=(240, 60, 54), anchor='mm', stroke_width=14, stroke_fill=INK)
        radial(img, 540, 330, 280, (255, 60, 50), .35 * smooth(seg(u, cue(1), cue(1) + .3)))
        anim.scaled_paste(img, lay, 540, 330, q * .46, angle=damp(u - cue(1), 9, 4, 12) + 3 * math.sin(u * 3))
    return img, {'faces': [face_box(g)], 'avoid': [(0, 120, W, 1360), (700, 1520, W, 1690)]}


# ---------------------------------------------------------------- s09: comet? antimatter? alien ship?
def comet_icon(d, x, y, r, t):
    for k in range(6):
        a = math.radians(200 + k * 6); L = r * (2.6 - k * .2)
        d.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L + 6 * math.sin(t * 3 + k))], fill=(150, 220, 255) if k % 2 else (220, 240, 255), width=int(r * .4))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 236, 255), outline=INK, width=6)
    d.ellipse([x - r * .5, y - r * .6, x + r * .1, y - r * .1], fill='white')


def atom_icon(d, x, y, r, t):
    for k in range(3):
        a = k * math.pi / 3 + t * .6
        pts = [(x + math.cos(s_) * r * math.cos(a) - math.sin(s_) * r * .38 * math.sin(a),
                y + math.cos(s_) * r * math.sin(a) + math.sin(s_) * r * .38 * math.cos(a)) for s_ in np.linspace(0, 2 * math.pi, 40)]
        d.line(pts + [pts[0]], fill=INK, width=10); d.line(pts + [pts[0]], fill=(255, 120, 220), width=5)
        s_ = t * 4 + k * 2; e = (x + math.cos(s_) * r * math.cos(a) - math.sin(s_) * r * .38 * math.sin(a), y + math.cos(s_) * r * math.sin(a) + math.sin(s_) * r * .38 * math.cos(a))
        d.ellipse([e[0] - 10, e[1] - 10, e[0] + 10, e[1] + 10], fill=(255, 230, 255), outline=INK, width=3)
    d.ellipse([x - r * .25, y - r * .25, x + r * .25, y + r * .25], fill=(200, 60, 200), outline=INK, width=5)
    d.text((x, y + 2), '−', font=font(int(r * .4)), fill='white', anchor='mm')


def ufo_icon(d, x, y, r, t):
    a = math.radians(-18)
    d.ellipse([x - r * .45, y - r * .62, x + r * .45, y + r * .05], fill=(170, 230, 230), outline=INK, width=6)
    d.ellipse([x - r * 1.05, y - r * .25, x + r * 1.05, y + r * .3], fill=(170, 176, 196), outline=INK, width=7)
    for k in range(5):
        lx = x - r * .7 + k * r * .35; d.ellipse([lx - 9, y - 2, lx + 9, y + 14], fill=(255, 220, 90) if (k + int(t * 6)) % 2 else (120, 110, 80))
    for k in range(3):
        v = (t * .8 + k / 3) % 1; d.ellipse([x + r * .6 + v * 40 - 20 * v, y - r * .3 - v * 120 - 22, x + r * .6 + v * 40 + 20 + 20 * v, y - r * .3 - v * 120 + 22], fill=(110, 100, 120))
    d.line([(x - r * 1.1, y + r * .55), (x + r * 1.1, y + r * .55)], fill=(90, 70, 60), width=10)


def s09(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-10, 10, smooth(u / D))
    img.paste(vgrad([(0, (30, 16, 60)), (.5, (96, 44, 110)), (.72, (200, 90, 120)), (.8, (230, 130, 120))]))
    stars(img, 9, 70, 900, u)
    T.forest_row(img, 81, 1520, 140, 240, (60, 30, 70), (40, 20, 54), n=30, x_shift=cam * .5, iw=0, t=u)
    d = ImageDraw.Draw(img); d.rectangle([0, 1540, W, H], fill=(40, 22, 50))
    ts = [cue(3) - .15, cue(4) - .15, cue(8) - .15]
    people = [(200, (60, 110, 200), -.4), (540, (200, 120, 60), 0.0), (880, (90, 170, 110), .4)]
    faces = []
    for i, ((x, shirt, look), t_) in enumerate(zip(people, ts)):
        pose = chain(u, [(0, STAND), (t_ - .2, add(STAND, armR=(-14, -14))), (t_ + .15, dict(POSES['point'], armR=(-130, -150)), lambda f: out_back(f, 1.8))])
        g = towns(img, u, pose, 'thinking' if u < t_ else 'surprised', x + cam * .2, 1880, .5, shirt, look=look * -1, bphase=i * .9)
        faces.append(face_box(g))
        s = smooth(seg(u, t_ - .2, t_ + .3)) * (1 + .06 * math.sin(math.pi * seg(u, t_ + .1, t_ + .5)))
        hx, hy = g['head']
        bx, by = [(250, 560), (540, 960), (830, 560)][i]
        lay = thought(img, bx, by, 210, 170, (hx, hy - 120), 1.0)
        dl = ImageDraw.Draw(lay)
        [comet_icon, atom_icon, ufo_icon][i](dl, bx, by - 30, 70, u)
        pill(lay, ['COMET', 'ANTIMATTER', 'ALIEN SHIP'][i], bx, by + 100, [(50, 120, 200), (170, 50, 170), (60, 150, 90)][i], size=36, pad=16)
        paste_grown(img, lay, hx, hy - 120, s)
        q = slam(u, t_ + .45, .25, 1.6)                                   # each guess gets a "?" stamp
        if q > 0:
            ql = layer(220, 260); dq = ImageDraw.Draw(ql)
            dq.ellipse([20, 40, 200, 220], fill=(250, 220, 70), outline=INK, width=8)
            dq.text((110, 130), '?', font=font(130), fill=INK, anchor='mm')
            anim.scaled_paste(img, ql, bx + 150, by - 120, q * .7, angle=12)
    img = finish(img, u, 1.03 + .04 * smooth(u / D), 540, 1100, dx=-cam, vig=(.42, (20, 6, 30)))
    return img, {'faces': faces, 'avoid': [(0, 360, W, 1140)]}


# ---------------------------------------------------------------- s10: the answer, a burst 8 km up
GROUND_Y, KM = 1640, 75
BURST = (540, GROUND_Y - 8 * KM)


def atmo_bg(img, u, cam=0.0):
    img.paste(vgrad([(0, (4, 4, 18)), (.22, (14, 20, 60)), (.55, (40, 90, 170)), (.85, (130, 190, 240)), (.88, (170, 210, 240))]))
    stars(img, 15, 60, 760, u)
    d = ImageDraw.Draw(img)
    for k, y in enumerate((GROUND_Y - 11 * KM, GROUND_Y - 6 * KM, GROUND_Y - 2 * KM)):   # faint layer bands
        d.line([(0, y), (W, y)], fill=(90, 130, 200), width=2)
    cloud_bands(img, 31, GROUND_Y - 300, GROUND_Y - 60, (230, 240, 255), .45, n=6, drift=u * 30)
    T.forest_row(img, 91, GROUND_Y + 10, 50, 100, (40, 90, 70), (24, 60, 50), n=60, iw=3, t=u)
    d = ImageDraw.Draw(img); d.rectangle([0, GROUND_Y + 20, W, H], fill=(52, 70, 50))
    d.line([(0, GROUND_Y + 20), (W, GROUND_Y + 20)], fill=INK, width=6)
    d.rectangle([0, GROUND_Y + 26, W, H], fill=(76, 58, 44))
    for k in range(4): d.line([(0, GROUND_Y + 70 + k * 50), (W, GROUND_Y + 60 + k * 50)], fill=(64, 48, 38), width=5)


ROCK_FROM = (1400, -380)


def fire_cloud(img, x, y, u, v, sc=1.0):
    """The airburst as a flat-2D fireball: lobed red/orange rim, yellow body, white-hot core, darkening with v."""
    k = ease_out(min(1, v / .5)); R = (60 + 190 * k) * sc
    d = ImageDraw.Draw(img); rng = np.random.default_rng(44)
    cool = smooth(v / 2.2)
    for layer_i, (rk, col) in enumerate(((1.0, lerp((240, 90, 40), (150, 60, 50), cool)), (.72, lerp((255, 160, 50), (230, 110, 50), cool)),
                                         (.45, lerp((255, 225, 110), (255, 170, 80), cool)))):
        n = 13
        for i in range(n):
            a = i * 2 * math.pi / n + rng.uniform(-.15, .15) + u * .15 * (1 if layer_i % 2 else -1)
            rr = R * rk * (.62 + .08 * math.sin(u * 3 + i)); q = R * rk * rng.uniform(.38, .5)
            cx_, cy_ = x + math.cos(a) * rr, y + math.sin(a) * rr * .9
            if layer_i == 0: d.ellipse([cx_ - q - 6, cy_ - q - 6, cx_ + q + 6, cy_ + q + 6], fill=INK)
        for i in range(n):
            a = i * 2 * math.pi / n + u * .15 * (1 if layer_i % 2 else -1)
            rr = R * rk * (.62 + .08 * math.sin(u * 3 + i)); q = R * rk * .45
            cx_, cy_ = x + math.cos(a) * rr, y + math.sin(a) * rr * .9
            d.ellipse([cx_ - q, cy_ - q, cx_ + q, cy_ + q], fill=col)
        d.ellipse([x - R * rk * .7, y - R * rk * .65, x + R * rk * .7, y + R * rk * .65], fill=col)
    radial(img, x, y, R * .9, (255, 255, 235), .9 * (1 - .4 * cool), power=.8)




def rock_path(u, t_b):
    """Fraction along the diagonal ROCK_FROM -> BURST: in fast, a slow drift for the size comparison, then the dive."""
    t1 = t_b - .3
    if u < 1.5: return .38 + .42 * ease_out(u / 1.5)
    if u < t1: return .80 + .03 * (u - 1.5) / max(.01, t1 - 1.5)
    return .83 + .17 * ease_in(seg(u, t1, t_b))


def s10(u, D, cue):
    img = Image.new('RGBA', (W, H))
    atmo_bg(img, u)
    T.altitude_ruler(img, 64, GROUND_Y, KM, kms=(0, 2, 4, 6, 8, 10), fs=42)
    t_b, t_8 = cue(10) - .05, cue(13) - .1
    bx, by = BURST
    # the 8 KM line: faint from the start, drawn bright on "eight"
    T.dashed(ImageDraw.Draw(img), (230, by), (W, by), (200, 215, 240), 4, 22, 18, phase=-u * 40)
    k8 = smooth(seg(u, t_8 - .3, t_8 + .3))
    if k8 > 0:
        m8 = mask(); ImageDraw.Draw(m8).line([(230, by), (230 + (W - 230) * k8, by)], fill=255, width=14)
        glow(img, m8, (255, 220, 90), .6, blur=12, add=True)
        T.dashed(ImageDraw.Draw(img), (230, by), (230 + (W - 230) * k8, by), (255, 225, 90), 9, 34, 16, phase=-u * 80)
    ang = math.atan2(by - ROCK_FROM[1], bx - ROCK_FROM[0])
    t_cmp = cue(5) - .1                                                    # "the size of a building"
    cmp_s = pop(u, t_cmp, .35, 1.7) * (1 - smooth(seg(u, t_b - .25, t_b)))
    if u < t_b:                                                           # the rock streaks in, heating up
        f = rock_path(u, t_b)
        x, y = ROCK_FROM[0] + (bx - ROCK_FROM[0]) * f, ROCK_FROM[1] + (by - ROCK_FROM[1]) * f
        heat = .45 + .55 * smooth(seg(u, 0, t_b))
        tm = mask(); tx, ty = x - math.cos(ang) * 1000, y - math.sin(ang) * 1000; nx, ny = -math.sin(ang), math.cos(ang)
        ImageDraw.Draw(tm).polygon([(x + nx * 120, y + ny * 120), (tx + nx * 20, ty + ny * 20), (tx - nx * 20, ty - ny * 20), (x - nx * 120, y - ny * 120)], fill=255)
        glow(img, tm, (255, 96, 30), .85, blur=40, add=False)                   # the long fiery trail
        T.fireball(img, x, y, 80 + 30 * heat, ang, 820 + 260 * heat, u, alpha=.7 + .3 * heat)
        T.rock(ImageDraw.Draw(img), x, y, 140, ang=u * 1.5, col=lerp((150, 104, 80), (255, 120, 50), heat),
               lit=lerp((200, 160, 130), (255, 230, 150), heat), dark=lerp((90, 62, 56), (200, 60, 30), heat), seed=5)
        if cmp_s > .01:                                                   # same-scale building beside the rock
            lay = layer(W, 900); dl = ImageDraw.Draw(lay)
            ox, oy = x, y                                                 # layer centre follows the rock
            lx, ly = W / 2 - 370, 450                                     # building centre-x and rock centre-y in layer coords
            dl.rounded_rectangle([lx - 150, ly - 230, lx + 150, ly + 230], 30, fill=(230, 236, 246, 90), outline=(255, 255, 255, 220), width=5)
            T.building(dl, lx, ly + 165, 160, 330, floors=10)
            dl.text((lx + 185, ly), '≈', font=font(110, True), fill='white', anchor='mm', stroke_width=8, stroke_fill=INK)
            dl.line([(lx - 120, ly - 165), (lx - 120, ly + 165)], fill='white', width=6)
            for yy in (ly - 165, ly + 165): dl.line([(lx - 134, yy), (lx - 106, yy)], fill='white', width=6)
            anim.scaled_paste(img, lay, ox - 40, oy, cmp_s * 1.12, angle=0)
            put_chip(img, '~50-60 M ≈ A BUILDING', (40, 110, 200), 540, 380, cmp_s, size=76, angle=-2)
    else:
        v = u - t_b
        radial(img, bx, by, 420 + 900 * ease_out(v / .8), (255, 220, 150), .95 * (1 - .35 * smooth(v / 2)))
        radial(img, bx, by, 200 + 260 * ease_out(v / .3), (255, 255, 240), 1.0 * (1 - .3 * smooth(v / 1.5)), power=.8)
        T.shock_ring(img, bx, by, 80 + 760 * ease_out(v / 1.1), 40, (255, 235, 190), .85 * (1 - smooth(v / 1.5)), squash=1.0)
        T.shock_ring(img, bx, by, 40 + 420 * ease_out(v / 1.3), 22, (255, 200, 120), .6 * (1 - smooth(v / 1.6)), squash=1.0)
        rng = np.random.default_rng(12); d = ImageDraw.Draw(img)
        for i in range(40):                                               # fragments fly apart and burn out
            a = rng.uniform(0, 2 * math.pi); sp = rng.uniform(260, 700); x = bx + math.cos(a) * sp * v; y = by + math.sin(a) * sp * v + 90 * v * v
            q = max(0, 20 * (1 - v / 1.3)) * rng.uniform(.6, 1.2)
            if q > 1:
                d.line([(x, y), (x - math.cos(a) * q * 3, y - math.sin(a) * q * 3)], fill=(255, 170, 70), width=int(q))
                d.ellipse([x - q, y - q, x + q, y + q], fill=(255, 220 - int(90 * min(1, v)), 110))
        T.smoke(img, 9, (bx - 380, by - 320, bx + 380, by + 260), u, color=(255, 196, 120), n=12, alpha=int(90 * smooth(v / .6)), rise=.06, size=(70, 150))
        fire_cloud(img, bx, by, u, v)
        put_chip(img, '8 KM UP', (220, 130, 30), 830, by - 290, pop(u, t_8, .3, 2), size=76, angle=-3)
    flash(img, u, t_b, .4, 1.0)
    sx, sy = shake(u, t_b, 18, .55)
    zf = smooth(seg(u, 0, t_b))                                           # the camera rides with the rock, then settles on the burst
    img = finish(img, u, 1.14 - .1 * zf + .03 * smooth(seg(u, t_b, D)), anim.lerp(720, bx, zf), anim.lerp(720, by, zf), dx=sx, dy=sy, vig=(.4, (2, 4, 20)))
    chip_t(img, 'THE ANSWER', (40, 150, 90), 540, 150, u, cue(1) - .1, size=64)
    return img, {'faces': [], 'avoid': [(0, 0, W, 1330)]}


# ---------------------------------------------------------------- s11: it never hit the ground
def s11(u, D, cue):
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (60, 20, 30)), (.35, (170, 60, 40)), (.6, (250, 150, 70)), (.7, (255, 196, 120))]))
    bx, by = 560, 720
    t_bl = cue(7) - .1
    radial(img, bx, by, 700, (255, 210, 130), .6 + .05 * math.sin(u * 6))
    radial(img, bx, by, 180, (255, 250, 220), .7 * (1 - .4 * smooth(u / D)), power=.8)
    d = ImageDraw.Draw(img); rng = np.random.default_rng(4)
    for i in range(40):                                                  # the rock's pieces vaporise in the air
        a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(60, 260); v = u + 1.0
        x = bx + math.cos(a) * r0 * (1 + .3 * v); y = by + math.sin(a) * r0 * (1 + .3 * v) * .7 + 40 * v
        q = max(0.0, rng.uniform(5, 14) * (1 - u / 1.2))
        if q > .5: d.ellipse([x - q, y - q, x + q, y + q], fill=(255, 230, 160))
    T.smoke(img, 5, (bx - 420, by - 200, bx + 420, by + 200), u + 3, color=(150, 70, 60), n=14, alpha=110, rise=.05, size=(60, 140))
    # the shock dome comes down: it reaches the treetops on "blast"
    hor = 1380
    k = ease_in(seg(u, -.4, t_bl)) if u < t_bl else 1.0
    r = 200 + (hor - by - 200) * k + (u - t_bl) * 500 * (u > t_bl)
    lay = layer(); dl = ImageDraw.Draw(lay)
    dl.ellipse([bx - r * 1.25, by - r, bx + r * 1.25, by + r], fill=(255, 230, 190, 50))
    img.alpha_composite(lay)
    m = mask(); ImageDraw.Draw(m).ellipse([bx - r * 1.25, by - r, bx + r * 1.25, by + r], outline=255, width=40)
    glow(img, m, (255, 240, 210), .8, blur=26, add=True)
    d = ImageDraw.Draw(img)
    d.ellipse([bx - r * 1.25, by - r, bx + r * 1.25, by + r], outline=(255, 250, 235), width=10)
    for i in range(10):                                                  # pressure arrows ride the front, down and out
        a = math.radians(20 + i * 14); p = (bx + math.cos(a) * r * 1.25, by + math.sin(a) * r)
        if p[1] < 1380: arrow(d, (p[0] - math.cos(a) * 70, p[1] - math.sin(a) * 56), p, (255, 230, 140), 10, 22)
    burst_star(img, bx, by, u, .9)
    hit = smooth(seg(u, t_bl - .1, t_bl + .25))
    taiga_horizon(img, u, 0, horizon=hor, wind=hit * .8, far=((150, 70, 60), (120, 50, 50)), mid=((80, 50, 50), (60, 34, 40)), haze_col=(255, 160, 100))
    d = ImageDraw.Draw(img); d.rectangle([0, hor + 160, W, H], fill=(40, 24, 30))
    for side in (-1, 1):                                                 # near trees bow outward when it hits
        rng = np.random.default_rng(5 + side)
        for i in range(5):
            x = 540 + side * (140 + i * 100); h = rng.uniform(380, 520)
            T.spruce(d, x, 1720 + i * 20, h, (60, 40, 44), (36, 22, 30), iw=4, sway=side * (.01 * math.sin(u * 2 + i) + .22 * hit * (1 - .4 * smooth(seg(u, t_bl + .3, D)))))
    if u > t_bl:
        T.smoke(img, 6, (0, hor - 60, W, hor + 260), u, color=(200, 140, 110), n=16, alpha=int(150 * hit), rise=.3, size=(60, 140))
    flash(img, u, t_bl, .2, .4, (255, 230, 200))
    sx, sy = shake(u, t_bl, 14, .5)
    img = finish(img, u, 1.04 + .03 * smooth(u / D), 540, 1000, dx=sx, dy=sy, vig=(.42, (30, 8, 10)))
    slam_title(img, 's11', [('IT NEVER HIT', 'white', 104), ('THE GROUND', (255, 214, 80), 120)], 230, u, cue(1) - .05)
    return img, {'faces': [], 'avoid': [(0, 160, W, 560)]}


# ---------------------------------------------------------------- s12a/b: the blueprint (shock from above vs sideways)
def blueprint(img, u, pan):
    img.paste(vgrad([(0, (14, 58, 92)), (1, (8, 40, 70))]))
    d = ImageDraw.Draw(img)
    for x in range(-int(pan) % 60, W, 60): d.line([(x, 0), (x, H)], fill=(30, 84, 120), width=1 if (x + int(pan)) % 240 else 3)
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(30, 84, 120), width=1 if y % 240 else 3)
    gy = 1560
    d.line([(0, gy), (W, gy)], fill=(200, 236, 255), width=6)
    for x in range(-int(pan) % 40, W, 40): d.line([(x, gy + 4), (x - 24, gy + 34)], fill=(110, 170, 210), width=3)
    return gy


def tree_parts(d, x, gy, h, u, t_strip, t_fall=None, fall_dir=1, col=((120, 230, 170), (70, 170, 130))):
    """A diagram spruce: stripped (tiers fly off) at t_strip, or knocked flat (rotates about its base) at t_fall."""
    rot = 0.0
    if t_fall is not None: rot = 88 * fall_dir * ease_in(seg(u, t_fall, t_fall + .4)) - 6 * fall_dir * damp(u - t_fall - .4, 1, 6, 16)
    lay = layer(700, 1000); dl = ImageDraw.Draw(lay); bx, by = 350, 950
    T.bare_trunk(dl, bx, by, h * .95, 34, (150, 120, 96), (210, 180, 150), iw=5, seed=3, stubs=0 if t_fall is not None else 3, burnt=False)
    for k in range(5):
        f0 = k / 5; yb = by - h * .15 - h * .8 * f0 * .9; wb = h * .42 * (1 - f0 * .75) / 2
        v = u - t_strip - k * .05 if t_strip is not None else -1
        ox = oy = ang = 0.0; al = 1.0
        if v > 0:
            side = 1 if k % 2 else -1
            ox, oy = side * 300 * v, -60 * v + 900 * v * v; ang = side * 160 * v; al = max(0.0, 1 - v / .9)
        if al <= 0: continue
        tl = layer(700, 1000); dt = ImageDraw.Draw(tl)
        poly = [(bx - wb, yb), (bx, yb - h * .3), (bx + wb, yb)]
        dt.polygon(poly, fill=col[1] + (int(255 * al),), outline=INK + (int(255 * al),))
        dt.polygon([(bx - wb, yb), (bx, yb - h * .3), (bx - wb * .1, yb)], fill=col[0] + (int(255 * al),))
        if ang: tl = tl.rotate(-ang, resample=Image.BICUBIC, center=(bx, yb - h * .1))
        lay.alpha_composite(tl, (int(ox), int(oy)))
    if rot: lay = lay.rotate(-rot, resample=Image.BICUBIC, center=(bx, by))
    return lay, (x - bx, gy - by)


def arrow(d, a, b, col, w=16, head=34):
    d.line([a, b], fill=INK, width=w + 10); d.line([a, b], fill=col, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); nx, ny = -math.sin(ang), math.cos(ang)
    tip = (b[0] + math.cos(ang) * head, b[1] + math.sin(ang) * head)
    d.polygon([tip, (b[0] + nx * head * .8, b[1] + ny * head * .8), (b[0] - nx * head * .8, b[1] - ny * head * .8)], fill=col, outline=INK)


def burst_star(img, x, y, u, s=1.0):
    radial(img, x, y, 260 * s, (255, 220, 140), .7 + .1 * math.sin(u * 7))
    d = ImageDraw.Draw(img)
    pts = [(x + math.cos(i * math.pi / 8) * (90 if i % 2 == 0 else 44) * s * (1 + .06 * math.sin(u * 9 + i)), y + math.sin(i * math.pi / 8) * (90 if i % 2 == 0 else 44) * s * (1 + .06 * math.sin(u * 9 + i))) for i in range(16)]
    d.polygon(pts, fill=(255, 210, 90), outline=INK, width=6)
    d.ellipse([x - 30 * s, y - 30 * s, x + 30 * s, y + 30 * s], fill=(255, 250, 220))


def s12a(u, D, cue):
    img = Image.new('RGBA', (W, H))
    gy = blueprint(img, u, 0)
    bx, by = 540, 330
    burst_star(img, bx, by, u)
    t_dn, t_br = cue(6) - .2, cue(11) - .15
    d = ImageDraw.Draw(img)
    for i in range(5):                                                   # arrows pour straight down, on a loop
        x = bx + (i - 2) * 80
        for j in range(3):
            v = ((u - cue(4) + .2) * .9 + j / 3) % 1 if u > cue(4) - .3 else -1
            if v < 0: continue
            y0 = by + 120 + v * (gy - 700 - by); arrow(d, (x, y0), (x, y0 + 130), (255, 220, 90), 12, 26)
    lay, off = tree_parts(d, 540, gy, 720, u, t_br)
    img.alpha_composite(lay, (int(off[0]), int(off[1])))
    for side in (-1, 1):                                                 # the trees further out, still untouched (s12b)
        for k in range(2):
            l2, o2 = tree_parts(d, 540 + side * (330 + k * 170), gy, 420 - k * 60, u, None)
            img.alpha_composite(l2, (int(o2[0]), int(o2[1])))
    chip_t(img, 'STRAIGHT DOWN', (220, 150, 30), 540, 600, u, t_dn, size=54)
    if u > t_br + .5: chip_t(img, 'STILL STANDING', (40, 150, 110), 540, 1700, u, t_br + .5, size=54)
    img = finish(img, u, 1.02 + .04 * smooth(u / D), 540, 1000, vig=(.38, (2, 16, 30)))
    return img, {'faces': [], 'avoid': [(0, 500, W, 700)]}


def s12b(u, D, cue):
    img = Image.new('RGBA', (W, H))
    pan = 420 + 60 * smooth(u / D)
    gy = blueprint(img, u, pan)
    bx, by = 540 - pan, 330
    burst_star(img, bx, by, u)
    t_side, t_fl = cue(19) - .2, cue(21) - .1
    d = ImageDraw.Draw(img)
    for j in range(4):                                                   # slanted arrows reach the far trees sideways
        v = ((u + .4) * .8 + j / 4) % 1
        a = (bx + 160 + v * 520, by + 140 + v * 720); arrow(d, a, (a[0] + 150, a[1] + 110), (255, 220, 90), 12, 26)
    for i, (x, h) in enumerate(((560, 620), (800, 560), (1010, 500))):
        l2, o2 = tree_parts(d, x, gy, h, u, None, t_fall=t_fl + i * .08, fall_dir=1)
        img.alpha_composite(l2, (int(o2[0]), int(o2[1])))
        if t_side < u < t_fl + .3:                                        # impact arcs on the trunks
            k = (u - t_side) * 3 % 1; d.arc([x - 120 - 40 * k, gy - h * .6 - 60, x - 20, gy - h * .6 + 60], 120, 240, fill=(255, 230, 140), width=8)
    l3, o3 = tree_parts(d, 540 - pan + 0, gy, 720, u, -10)               # the bare trunk under the burst (left edge)
    img.alpha_composite(l3, (int(o3[0]), int(o3[1])))
    chip_t(img, 'SIDEWAYS', (220, 150, 30), 640, 640, u, t_side, size=56)
    chip_t(img, 'FLAT', (200, 70, 50), 820, 1700, u, t_fl + .3, size=60)
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 540, 1000, vig=(.38, (2, 16, 30)))
    return img, {'faces': [], 'avoid': [(0, 560, W, 720)]}


# ---------------------------------------------------------------- s13: the hairdryer and the grass
def s13(u, D, cue):
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (250, 232, 200)), (.6, (240, 214, 170)), (1, (220, 190, 150))]))
    radial(img, 820, 300, 700, (255, 250, 220), .5)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1240, W, H], fill=(120, 86, 60)); d.line([(0, 1240), (W, 1240)], fill=INK, width=6)
    for k in range(5): d.line([(0, 1300 + k * 120), (W, 1300 + k * 120)], fill=(104, 72, 50), width=4)
    cx = 540; gy = 1460
    t_on, t_g = cue(3) - .1, cue(6) - .1
    push = smooth(seg(u, t_on, t_g + .3))
    hx, hy = cx, 820 + 8 * math.sin(u * 2)
    if push > 0:                                                          # airflow: streams down, then out along the grass
        lay = layer(); dl = ImageDraw.Draw(lay)
        for side in (-1, 1):
            for j in range(5):
                for k in range(3):
                    v = ((u * 1.1 + k / 3 + j * .13) % 1)
                    lane = 24 + j * 30
                    pts = []
                    for s_ in np.linspace(max(0, v - .18), v, 8):
                        if s_ < .45: p = (cx + side * lane * (1 + s_), hy + 30 + (gy - 100 - hy) * s_ / .45)
                        else: p = (cx + side * (lane * 1.45 + (s_ - .45) / .55 * 560), gy - 100 + 40 * (s_ - .45) / .55 - j * 8)
                        pts.append(p)
                    dl.line(pts, fill=(255, 255, 255, int(200 * push)), width=7, joint='curve')
        img.alpha_composite(lay)
    rng = np.random.default_rng(3)
    d = ImageDraw.Draw(img)
    d.rectangle([0, gy - 6, W, gy + 60], fill=(96, 70, 44))
    T.grass_side(img, -20, W + 20, gy + 20, u, cx, push, n=70, h=(110, 190), core=70, seed=5)
    T.grass_side(img, -20, W + 20, gy + 50, u + 1, cx, push, n=60, h=(120, 210), core=80, seed=6, col=(60, 140, 60), lit=(120, 196, 90))
    # the dryer, held by a hand that reaches in from the right edge
    grip = T.hairdryer(img, hx, hy, .9, on=float(u > t_on), t=u)
    d = ImageDraw.Draw(img); sh = (W + 60, grip[1] - 420)
    d.line([sh, grip], fill=INK, width=58); d.line([sh, grip], fill=(246, 246, 242), width=48)
    d.ellipse([grip[0] - 36, grip[1] - 36, grip[0] + 36, grip[1] + 36], fill=INK); d.ellipse([grip[0] - 29, grip[1] - 29, grip[0] + 29, grip[1] + 29], fill=(246, 246, 242))
    t_up, t_out = cue(10) - .1, cue(15) - .1
    su = pop(u, t_up, .3, 1.8)
    if su > .01:
        k = su
        d.line([(cx - 90, gy - 210), (cx - 90, gy - 230), (cx + 90, gy - 230), (cx + 90, gy - 210)], fill=(40, 140, 200), width=int(8 * min(1, k)))
        put_chip(img, 'STAYS UP', (40, 140, 200), cx, gy - 300, k, size=48)
    so = pop(u, t_out, .3, 1.8)
    if so > .01:
        for side in (-1, 1):
            arrow(d, (cx + side * 200, gy - 330), (cx + side * (200 + 220 * min(1, so)), gy - 330), (230, 90, 50), 14, 30)
        put_chip(img, 'BLOWN OUTWARD', (230, 90, 50), cx, 1720, so, size=50)
    # top view inset: the same ring pattern as the forest
    si = pop(u, cue(12) - .1, .35, 1.7)
    if si > .01:
        lay = layer(400, 400); dl = ImageDraw.Draw(lay)
        dl.ellipse([10, 10, 390, 390], fill=INK); dl.ellipse([18, 18, 382, 382], fill=(140, 190, 100))
        rr = np.random.default_rng(2)
        for i in range(90):
            r = 60 + 110 * math.sqrt(rr.random()); a = rr.uniform(0, 2 * math.pi); x, y = 200 + math.cos(a) * r, 200 + math.sin(a) * r
            dl.line([(x, y), (x + math.cos(a) * 26, y + math.sin(a) * 26)], fill=(50, 110, 50), width=6)
        for i in range(14):
            r = 50 * math.sqrt(rr.random()); a = rr.uniform(0, 2 * math.pi); x, y = 200 + math.cos(a) * r, 200 + math.sin(a) * r
            dl.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(40, 100, 40))
        anim.scaled_paste(img, lay, 200, 330, si * .72, angle=u * 6)
        put_chip(img, 'FROM ABOVE', (60, 110, 60), 200, 520, si * .8, size=40)
    img = finish(img, u, 1.03 + .04 * smooth(u / D), 540, 1100, dx=6 * math.sin(u * .8), vig=(.3, (60, 30, 10)))
    return img, {'faces': [], 'avoid': [(0, 150, 420, 560), (cx - 300, gy - 360, cx + 300, gy - 200)]}


# ---------------------------------------------------------------- s14a: Kulik never found his iron
def s14a(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-12, 12, smooth(u / D))
    img.paste(vgrad([(0, (60, 60, 110)), (.35, (210, 130, 110)), (.55, (255, 190, 120)), (.62, (255, 210, 150))]))
    radial(img, 820 + cam * .9, 1080, 700, (255, 200, 120), .55 + .03 * math.sin(u * 2))
    stars(img, 41, 50, 520, u)
    cloud_bands(img, 41, 200, 900, (255, 210, 180), .3, n=6, drift=u * 16 + cam)
    d = ImageDraw.Draw(img); rf = np.random.default_rng(77)
    for i in range(34):                                                  # a far row of bare trunks in the haze
        T.bare_trunk(d, rf.uniform(-30, W + 30) + cam * .9, 1150, rf.uniform(120, 220), 8, (150, 96, 104), (200, 140, 130), iw=2, seed=i, stubs=2, burnt=False)
    haze(img, 900, 1160, (255, 190, 150), .45)
    d = ImageDraw.Draw(img); rng = np.random.default_rng(9)
    for k, (n, gy, hmin, hmax, w, col) in enumerate(((14, 1240, 300, 480, 14, (120, 70, 70)), (8, 1420, 600, 900, 26, (70, 40, 44)))):
        for i in range(n):
            x = rng.uniform(-40, W + 40) + cam * (.7 - .4 * k)
            if k == 1 and 300 < x < 780: continue
            T.bare_trunk(d, x, gy, rng.uniform(hmin, hmax), w, col, lerp(col, (255, 180, 120), .45), iw=3 + k, seed=i + 20 * k, stubs=3)
        if k == 0: haze(img, 1080, 1260, (255, 190, 140), .5); d = ImageDraw.Draw(img)
    d.rectangle([0, 1400, W, H], fill=(96, 70, 56))
    ra = np.random.default_rng(66)
    for i in range(26):                                                  # ash and moss on the ground
        y = ra.uniform(1420, H); x = ra.uniform(0, W) + cam * .3; r = ra.uniform(30, 90) * (.5 + (y - 1400) / 600)
        d.ellipse([x - r, y - r * .25, x + r, y + r * .25], fill=(110, 80, 62) if i % 2 else (84, 62, 52))
    haze(img, 1380, 1480, (255, 190, 140), .4); d = ImageDraw.Draw(img)
    for i in range(6):                                                   # long evening shadows
        x = 120 + i * 180 + cam * .3; d.polygon([(x, 1400), (x + 26, 1400), (x - 260, H), (x - 330, H)], fill=(88, 64, 54))
    for i, (x, y, L, ang) in enumerate(((40, 1560, 300, 0), (760, 1520, 280, 0), (180, 1760, 340, 180), (1040, 1800, 360, 180))):
        T.fallen_side(d, x + cam * .6, y, L * 1.2, 34 + i * 6, ang, col=(110, 72, 58), lit=(240, 170, 120), seed=60 + i)   # the ring, out here
    dust(img, 12, 40, (0, 900, W, 1900), (255, 210, 160), 150, size=(2, 5), t=u * 2)
    d = ImageDraw.Draw(img)
    t_ir, t_rock = cue(4) - .1, cue(6) - .2
    pose = chain(u, [(0, dict(POSES['hold'])), (t_ir, dict(POSES['shrug']), lambda f: out_back(f, 1.5)), (t_rock + .1, STAND),
                     (t_rock + .5, dict(POSES['point'], armR=(-150, -160)), lambda f: out_back(f, 1.6))])
    g = kulik(img, u, pose, 'sad' if u < t_rock else 'thinking', 190 + cam * .2, 1840, .66, look=.3,
              lean=-5 * smooth(seg(u, t_rock, t_rock + .5)), rim=(255, 210, 150), rim_dir=(1, -.2), prop='shovel' if u < t_ir - .1 else None, aura_a=.6)
    hx, hy = g['head']
    s = pop(u, cue(1) - .1, .35, 1.6) * (1 - smooth(seg(u, t_rock, t_rock + .3)))
    lay = thought(img, 700, 780, 230, 170, (hx + 190, hy + 10), 1.0)
    if lay is not None and s > .01:
        dl = ImageDraw.Draw(lay); iron_lump(dl, 690, 750, 80); pill(lay, 'IRON', 690, 865, (90, 96, 116), size=40, pad=18)
        draw_x(lay, 690, 770, 110, seg(u, t_ir, t_ir + .35) * 2, w=22)
        paste_grown(img, lay, hx + 190, hy + 10, s)
    if u > t_rock:                                                        # he looks up: the empty sky where it burst
        v = u - t_rock; radial(img, 820, 360, 160 + 30 * math.sin(u * 4), (255, 240, 200), .35 * smooth(v / .5))
    img = finish(img, u, 1.04 + .04 * smooth(u / D), 520, 1300, dx=-cam, vig=(.4, (40, 16, 20)))
    return img, {'faces': [face_box(g)], 'avoid': [(440, 580, W, 1000)]}


# ---------------------------------------------------------------- s14b: no crater, a ring of trees, loop to s01
def ring_scene(u, D, cue):
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (40, 40, 90)), (.25, (180, 110, 110)), (.33, (250, 180, 130)), (.36, (180, 150, 110)), (1, (96, 92, 60))]))
    d = ImageDraw.Draw(img)
    hor = 660
    T.forest_row(img, 101, hor + 10, 30, 60, (110, 90, 100), (90, 72, 86), n=60, iw=0, t=u)
    haze(img, hor - 60, hor + 80, (255, 190, 140), .5)
    radial(img, 640, hor, 380, (255, 190, 120), .4); cloud_bands(img, 81, 380, 620, (255, 190, 170), .35, n=4, drift=u * 20)
    cx, cy = 540, 1120
    ground_top_ring(img, cx, cy)
    haze(img, hor, hor + 260, (220, 160, 120), .35)
    glow_r = smooth(seg(u, cue(17) - .2, cue(17) + .4))
    if glow_r > 0:
        m = mask(); ImageDraw.Draw(m).ellipse([cx - 600, cy - 300, cx + 600, cy + 300], outline=255, width=50)
        glow(img, m, (255, 170, 70), .5 * glow_r * (.85 + .15 * math.sin(u * 4)), blur=40, add=True)
    logs, poles = T.treefall_items(21, 170, 620, 300, 40)
    d = ImageDraw.Draw(img); sq = .48
    for r, a, lk, da in logs:
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * sq
        ang = math.atan2(math.sin(a + da) * sq, math.cos(a + da))
        T.log_top(d, x, y, ang, 54 * lk, 12 * lk, (120, 92, 66), (180, 146, 104), iw=3, twigs=False)
    radial(img, cx, cy - 60, 260, (255, 226, 170), .45 + .05 * math.sin(u * 3)); d = ImageDraw.Draw(img)   # the standing centre lit
    for r, a in sorted(poles, key=lambda p: math.sin(p[1]) * p[0]):
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * sq
        T.bare_trunk(d, x, y, 210 + 40 * math.sin(a * 5), 16, (150, 112, 86), (255, 230, 190), iw=4, seed=int(r), stubs=2, burnt=False)
    radial(img, cx + 20, cy - 20, 140, (255, 250, 230), .5)
    g = kulik(img, u, dict(POSES['point'], armR=(-150, -160)), 'thinking', cx + 20, cy + 70, .48, look=.2, label_on=False, aura_a=.9,
              rim=(255, 240, 200), rim_dir=(1, -.4))
    d = ImageDraw.Draw(img)
    for i, (x, y, L, ang) in enumerate(((-40, 1700, 420, 0), (760, 1660, 400, 0), (80, 1880, 520, 0), (1120, 1860, 500, 180))):
        T.fallen_side(d, x, y, L, 40 + i * 6, ang, col=(92, 70, 52), lit=(200, 150, 104), seed=80 + i)   # near logs frame the bottom
    return img


def ground_top_ring(img, cx, cy):
    d = ImageDraw.Draw(img); rng = np.random.default_rng(4)
    for i in range(70):                                                  # moss and bog patches, smaller toward the horizon
        y = rng.uniform(700, H); f = (y - 660) / (H - 660); x, r = rng.uniform(0, W), rng.uniform(30, 120) * (.4 + f)
        d.ellipse([x - r, y - r * .4, x + r, y + r * .4], fill=(110, 104, 66) if i % 3 == 0 else (84, 82, 54) if i % 3 == 1 else (70, 74, 50))
    m = mask(); ImageDraw.Draw(m).rectangle([0, 1460, W, H], fill=255)
    fill_mask(img, m, (36, 28, 24), .6, blur=90)                      # darker foreground ground


def s14b_frame(u, D, cue):
    A = ring_scene(u, D, cue)
    A = finish(A, u, 1.0 + .06 * smooth(u / D), 540, 1200, vig=(.4, (30, 14, 20)))
    slam_title(A, 's14b', [('NO CRATER', (255, 76, 60), 140)], 260, u, cue(13) - .08)
    return A


def s14b(u, D, cue):
    """The ring, then (last 0.22 s, after "ones,") the camera tilts up into s14c's low-angle shot."""
    A = s14b_frame(u, D, cue)
    k = smooth(seg(u, D - .22, D))
    if k <= 0: return A, {'faces': [], 'avoid': [(0, 160, W, 460), (0, 840, W, 1440)]}
    Bimg, _ = s14c(u - D, 1.0, cue_shift(cue, D))
    return tilt_wipe(A, Bimg.convert('RGBA'), k), {'faces': [], 'avoid': [(0, 160, W, 460)], 'seam': int(k * H)}


def cue_shift(cue, D):
    return lambda i: cue(i) - D


def tilt_wipe(A, Bimg, k):
    """A vertical whip-tilt up: A slides down out of frame, B comes in from the top."""
    out = Image.new('RGBA', (W, H)); off = int(round(k * H))
    if off < H: out.alpha_composite(A.crop((0, 0, W, H - off)), (0, off))
    if off > 0: out.alpha_composite(Bimg.crop((0, H - off, W, H)), (0, 0))
    return out


def lowangle_scene(u):
    """'...pointing at the sky.': worm's-eye view up the bare upright trunks into a rich dusk sky; stars come
    out, a warm glow hangs where the blast was, thin clouds drift; the trunks converge to the glow."""
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (14, 14, 46)), (.3, (44, 34, 92)), (.58, (150, 76, 110)), (.8, (240, 140, 96)), (1, (255, 196, 130))]))
    k_st = smooth(seg(u, .1, 1.0))
    lay = layer(); stars(lay, 140, 90, 1100, u)                         # the stars come out
    lay.putalpha(lay.getchannel('A').point(lambda a: int(a * (.25 + .75 * k_st)))); img.alpha_composite(lay)
    gx, gy = 540, 640                                                     # where the blast was
    radial(img, gx, gy, 520, (255, 170, 110), .45 + .05 * math.sin(u * 3))
    radial(img, gx, gy, 200, (255, 236, 200), .7 + .08 * math.sin(u * 5))
    radial(img, gx, gy, 70, (255, 250, 235), .8)
    T.shock_ring(img, gx, gy, 300 + 30 * u, 10, (255, 210, 170), .22, squash=.9)
    cloud_bands(img, 61, 820, 1350, (255, 170, 140), .35, n=5, drift=u * 30)
    # the trunks: bases along the bottom edge, splaying gently toward a vanishing point high above the frame;
    # far ones short and hazy, near ones tall at the frame edges; the centre stays open on the glow
    d = ImageDraw.Draw(img); rng = np.random.default_rng(14); vx, vy = 540, -2600
    for layer_i, (n, base_y, wmin, wmax, top_lo, top_hi, col, lit) in enumerate((
            (14, 2000, 16, 24, 900, 1150, (96, 58, 80), (190, 120, 120)),
            (9, 2060, 32, 46, 560, 860, (62, 36, 50), (220, 130, 104)),
            (4, 2120, 70, 96, -200, 120, (36, 20, 28), (196, 116, 92)))):
        for i in range(n):
            bx = -100 + (W + 200) * (i + rng.uniform(.15, .85)) / n
            if layer_i == 2: bx = (-30, 170, 900, 1110)[i]
            top_y = rng.uniform(top_lo, top_hi) + 30 * math.sin(u * .5 + i)
            if 380 < bx < 700:                                           # the centre: only short far trunks, under the caption
                if layer_i == 1: bx += 320 if bx > 540 else -320
                elif layer_i == 0: top_y = max(top_y, 1400 + 60 * rng.random())
            bx += 6 * math.sin(u * .9 + i) * (layer_i + 1)
            f = (base_y - top_y) / (base_y - vy); tx = bx + (vx - bx) * f
            L = math.hypot(tx - bx, base_y - top_y); lean = math.degrees(math.atan2(tx - bx, base_y - top_y))
            T.bare_trunk(d, bx, base_y, L, rng.uniform(wmin, wmax), col, lit, iw=3 + layer_i, lean=lean, seed=i + 30 * layer_i, stubs=4 + layer_i)
        if layer_i == 0: haze(img, 1500, 2000, (255, 190, 140), .35); d = ImageDraw.Draw(img)
    dust(img, 9, 50, (0, 300, W, 1900), (255, 220, 180), 170, size=(2, 6), t=u * 2)
    return img


def s14c(u, D, cue):
    """'pointing at the sky.' (low angle), then on the final beat a whip-tilt into the s01a opening frame (the
    loop): the tail is s01a's own lead-in (u < 0), ending one frame before s01a's frame 0."""
    A = finish(lowangle_scene(u), u, 1.02 + .05 * smooth(u / max(D, .1)), 540, 900, dy=-30 * smooth(u / max(D, .1)),
               vig=(.38, (16, 10, 30)))
    t0 = cue(27) + .37 if D > 1.2 else 99.0                              # after "sky." ends
    t1 = D - .28
    k = smooth(seg(u, t0, t1))
    if k <= 0: return A, {'faces': [], 'avoid': [(0, 0, W, 1150)]}
    Bimg, binfo = s01a(min(0.0, u - D), 4.27, lambda i: 99.0)
    Bimg = Bimg.convert('RGBA')
    if k >= 1: return Bimg, {'faces': [], 'avoid': binfo['avoid'], 'seam': None}
    return tilt_wipe(A, Bimg, k), {'faces': [], 'avoid': [(0, 0, W, 1150)], 'seam': int(k * H)}


SHOTS = {'s01a': s01a, 's01b': s01b, 's02': s02, 's03': s03, 's04a': s04a, 's04b': s04b, 's05': s05, 's06': s06,
         's07': s07, 's08': s08, 's09': s09, 's10': s10, 's11': s11, 's12a': s12a, 's12b': s12b, 's13': s13,
         's14a': s14a, 's14b': s14b, 's14c': s14c}
SHOT_LIST = [('s01a', 1, 0), ('s01b', 1, 12), ('s02', 2, 0), ('s03', 3, 0), ('s04a', 4, 0), ('s04b', 4, 11), ('s05', 5, 0),
             ('s06', 6, 0), ('s07', 7, 0), ('s08', 8, 0), ('s09', 9, 0), ('s10', 10, 0), ('s11', 11, 0), ('s12a', 12, 0),
             ('s12b', 12, 14), ('s13', 13, 0), ('s14a', 14, 0), ('s14b', 14, 11), ('s14c', 14, 24)]
END = 65.4                     # 1962 frames; with the 0.1 s cover the posted cut is 65.5 s
BAND_AT = {'s14c': .9}          # caption band read on the low-angle frame, not the loop wipe
NO_PUNCH = ('s14c',)            # s14c is entered by s14b's tilt, not a cut
STILL_AT = {'s01a': .8, 's01b': .85, 's02': .97, 's03': .92, 's04a': .95, 's04b': .97, 's05': .97, 's06': .97, 's07': .97,
            's08': .97, 's09': .97, 's10': .55, 's11': .6, 's12a': .97, 's12b': .97, 's13': .97, 's14a': .5, 's14b': .55, 's14c': .45}

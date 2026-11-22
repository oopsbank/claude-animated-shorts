"""Style frames for blood-falls (s01, s05, s11, s15), built with the flat2d kit.

usage: .venv/bin/python flat2d/style_frames.py OUTDIR [--small DIR] [shot ...]
Each scene() draws back to front; the comment on each layer says how it moves in the animated shot.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
from kit import *  # noqa
import kit, props
import stickman

# shared palette (same across the video)
GEO_BLUE = (52, 112, 222); SCI_GREEN = (40, 168, 92); RUST = (226, 92, 36); BLOOD = (176, 22, 32)
SNOW_SHADE = (178, 198, 232); NAVY = (16, 22, 56)


def geologist(img, cx, gy, s, expr='surprised', pose='point', rim=(255, 196, 150), rim_dir=(1, -.3), label_on=True,
              axe=True, aura=GEO_BLUE):
    card = stick(expr, pose, pants='#3c3a52')
    g = place(img, card, cx, gy, s, aura=aura, aura_alpha=.45, rim=rim, rim_dir=rim_dir)
    props.fur_hat(img, g['head'], g['R'])
    if axe:
        hl = stickman.hand_anchors(pose)['L']; px, py = g['xy']
        props.ice_axe(img, (px + hl[0] * s, py + hl[1] * s), s * .9)
        # redraw the hand over the shaft
        r = stickman.T / 2 * s; hx, hy = px + hl[0] * s, py + hl[1] * s
        ImageDraw.Draw(img).ellipse([hx - r - 3, hy - r - 3, hx + r + 3, hy + r + 3], fill=INK)
        ImageDraw.Draw(img).ellipse([hx - r, hy - r, hx + r, hy + r], fill=(246, 246, 242))
    if label_on:
        hx, hy = g['head']
        label(img, 'GEOLOGIST · 1911', min(W - 250, max(250, hx)), hy - g['R'] * 1.32 - 92, GEO_BLUE, size=int(48 * max(.92, min(1.1, s))))
    return g


def blood_falls(img, x_top, y_top, y_bot, w=60, color=BLOOD, hi=(232, 70, 58), seed=4, rust=False, t=0.0):
    """Stepped red stream down the ice face + glow. Moves: highlight dashes scroll down (t), glow pulses."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    n = 6; ys = np.linspace(y_top, y_bot, n + 1)
    left = []; right = []
    for i, y in enumerate(ys):
        off = math.sin(i * 1.3) * 22 + i * 14; ww = w * (0.6 + i / n * 1.3)
        left.append((x_top + off - ww / 2, y)); right.append((x_top + off + ww / 2, y))
    poly = left + right[::-1]
    gm = mask(); ImageDraw.Draw(gm).polygon(poly, fill=255)
    glow(img, gm, (255, 70, 40) if not rust else (255, 120, 40), .55, blur=50, add=True)
    d.polygon(poly, fill=INK)
    inner = [(x + 5, y) for x, y in left] + [(x - 5, y) for x, y in right[::-1]]
    d.polygon(inner, fill=color)
    core = [(x + (rx - x) * .22, y) for (x, y), (rx, _) in zip(left, right)] + \
           [(x + (rx - x) * .5, y) for (x, y), (rx, _) in zip(left[::-1], right[::-1])]
    d.polygon(core, fill=hi)
    for k in range(16):  # flowing highlight dashes
        u = (rng.random() + t * .6) % 1; i = min(n - 1, int(u * n)); f = u * n - i
        x = left[i][0] + (left[i + 1][0] - left[i][0]) * f + rng.uniform(.25, .7) * (right[i][0] - left[i][0])
        y = ys[i] + (ys[i + 1] - ys[i]) * f
        d.line([(x, y), (x + 4, y + 34)], fill=(255, 170, 140), width=5)
    return left, right


def red_fan(img, apex, spread, color=BLOOD, edge=(214, 74, 52), seed=5, rust=False):
    """Stain spreading over the snow from the foot of the falls. Moves: leading edge creeps outward."""
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    ax, ay = apex; pts = [(ax - 70, ay - 6)]
    for i in range(12):
        u = i / 11; x = ax - spread[0] * .25 + spread[0] * 1.2 * u
        y = ay + spread[1] * (0.35 + 0.65 * math.sin(u * math.pi)) + rng.uniform(-20, 20)
        pts.append((x, y))
    pts.append((ax + 120, ay - 4))
    d.polygon(pts, fill=edge)
    inner = [(ax + (x - ax) * .8, ay + (y - ay) * .78) for x, y in pts]
    d.polygon(inner, fill=color)
    core = [(ax + (x - ax) * .45, ay + (y - ay) * .4) for x, y in pts]
    d.polygon(core, fill=lerp(rgb(color), (60, 0, 10), .25))
    for _ in range(9):  # pools/ripples
        u = rng.uniform(.2, .8); i = int(u * 11)
        x = ax + (pts[i + 1][0] - ax) * rng.uniform(.3, .7); y = ay + (pts[i + 1][1] - ay) * rng.uniform(.3, .7)
        d.ellipse([x - 26, y - 6, x + 26, y + 6], fill=lerp(rgb(color), (255, 255, 255), .25))
    d.line(pts, fill=INK, width=5)


def polar_backdrop(img, sky, sun, mtn_far, mtn_near, haze_col, t=0.0, horizon=1040):
    """Sky + sun + two faceted ranges + haze (s01 and s15 share it). Moves: clouds drift (t*12 px/s),
    far range parallax 0.2x / near 0.45x of the camera pan, haze breathes."""
    img.paste(vgrad(sky))
    radial(img, sun[0], sun[1], 620, sun[2], .55)
    radial(img, sun[0], sun[1], 140, (255, 246, 228), .95, power=.6)
    light_rays(img, sun[0], sun[1], sun[2], alpha=.16, spread=(195, 345), seed=3, phase=t * .5)
    cloud_bands(img, 2, 300, 860, (255, 236, 226), .28, n=6, drift=t * 12)
    peak_range(img, 21, horizon - 40, 140, 300, *mtn_far, n=8)
    haze(img, horizon - 220, horizon + 40, haze_col, .55)
    peak_range(img, 22, horizon + 20, 120, 260, *mtn_near, ink=INK, ink_w=4, n=6)
    haze(img, horizon - 40, horizon + 120, haze_col, .5)


# ------------------------------------------------------------------ s01
def s01(t=0.0):
    img = Image.new('RGBA', (W, H))
    polar_backdrop(img, [(0, (34, 52, 116)), (.3, (70, 112, 190)), (.52, (246, 190, 172)), (.6, (255, 214, 182))],
                   (860, 960, (255, 196, 150)),
                   ((198, 186, 220), (156, 150, 200), (246, 240, 250)),
                   ((168, 182, 226), (110, 128, 196), (250, 250, 255)),
                   (255, 222, 210), t)
    # Dry Valleys moraine: brown faceted slopes behind the character (contrast for the white body)
    peak_range(img, 31, 1330, 160, 330, (170, 122, 96), (112, 78, 74), (240, 236, 244), ink=INK, ink_w=5, n=5,
               snow_frac=.22, ground=(120, 86, 78))
    haze(img, 1180, 1420, (255, 214, 200), .25)
    slope = [(-10, 1170), (120, 1120), (260, 1150), (420, 1210), (420, 1560), (-10, 1560)]
    d = ImageDraw.Draw(img)
    d.polygon(slope, fill=(132, 92, 84))
    d.polygon([(-10, 1170), (120, 1120), (150, 1380), (-10, 1420)], fill=(170, 118, 98))
    d.polygon([(120, 1120), (260, 1150), (200, 1260), (130, 1230)], fill=(244, 238, 246))
    for k in range(5):  # moraine bands
        d.line([(-10, 1260 + k * 52), (200, 1250 + k * 56), (420, 1290 + k * 50)], fill=(104, 70, 70), width=4)
    d.line(slope[:4], fill=INK, width=5)
    rocks(img, 13, [(60, 1330, 44), (300, 1290, 30), (170, 1450, 54), (380, 1420, 26)])
    # glacier tongue: wall on the right two thirds
    top = lambda x: 930 - (x - 360) * .06 + 18 * math.sin(x / 70)
    bot = lambda x: 1530 + (x - 360) * .02
    ice_cliff(img, 360, W + 20, top, bot, seed=8, shade=(118, 164, 220), deep=(52, 92, 160))
    haze(img, 1460, 1600, (230, 238, 252), .5)  # mist at the foot (drifts)
    left, right = blood_falls(img, 720, 960, 1540, w=64, t=t)
    # ground: snow with a band of brown moraine (Dry Valleys) between
    yg = lambda x: 1540 + 12 * math.sin(x / 140) - (x < 360) * 0
    snow_ground(img, yg, seed=6)
    rocks(img, 3, [(140, 1600, 44), (980, 1660, 56), (60, 1830, 70), (1040, 1890, 80), (470, 1590, 26)])
    red_fan(img, (left[-1][0] + 60, 1548), (420, 150))
    props.footprints(img, [(40 + i * 46, 1900 - i * 34) for i in range(5)], s=1.1)
    # 1911 man-hauled sledge with a supply crate (foreground detail; static)
    d = ImageDraw.Draw(img); sx0, sy0 = 660, 1690
    contact_shadow(img, sx0 + 150, sy0 + 40, 360, (90, 100, 150), .45)
    for dx_ in (0, 22):
        d.line([(sx0 - 20, sy0 + 14 + dx_), (sx0 + 300, sy0 + 14 + dx_), (sx0 + 340, sy0 - 16 + dx_)], fill=INK, width=14, joint='curve')
        d.line([(sx0 - 20, sy0 + 14 + dx_), (sx0 + 300, sy0 + 14 + dx_), (sx0 + 340, sy0 - 16 + dx_)], fill=(150, 104, 64), width=7, joint='curve')
    d.rectangle([sx0 + 20, sy0 - 120, sx0 + 170, sy0 + 10], fill=(170, 120, 74), outline=INK, width=6)
    d.line([(sx0 + 20, sy0 - 60), (sx0 + 170, sy0 - 60)], fill=(120, 82, 52), width=6)
    d.rectangle([sx0 + 180, sy0 - 80, sx0 + 290, sy0 + 10], fill=(96, 120, 170), outline=INK, width=6)
    d.line([(sx0 + 235, sy0 - 80), (sx0 + 235, sy0 + 10)], fill=(200, 60, 50), width=8)
    d.polygon([(sx0 + 20, sy0 - 120), (sx0 + 170, sy0 - 120), (sx0 + 160, sy0 - 134), (sx0 + 30, sy0 - 134)], fill=(250, 252, 255), outline=INK)
    # character: big, left third, pointing at the falls
    g = geologist(img, 350, 1800, 0.98)
    foreground_frame(img, [[(820, 1940), (900, 1830), (1010, 1790), (1100, 1820), (1100, 1940)]], color=(150, 170, 214), alpha=.9)
    snow_particles(img, 9, n=(80, 36, 12), wind=(5, 1), t=t)
    vignette(img, .38)
    grain(img)
    title(img, [('THE GLACIER', 'white'), ('IS BLEEDING', (255, 72, 60))], 300, size=112)
    caption(img, 'found it bleeding.', avoid=[face_box(g)])
    return img


def face_box(g):
    hx, hy = g['head']; R = g['R']; return (hx - R, hy - R, hx + R, hy + R)


def body_box(g):
    """Torso column under the head (keep captions off a character's coat when there is room)."""
    hx, hy = g['head']; R = g['R']; return (hx - R * .7, hy + R, hx + R * .7, hy + R * 5.5)


def scientist(img, cx, gy, s, expr='surprised', pose='point', rim=(190, 230, 255), rim_dir=(-.4, -1),
              label_at='above', rim_w=9):
    """Lab goggles up on the forehead + wild grey hair (stickman wardrobe) tell the scientist from the
    fur-hatted geologist at a glance. label_at: 'above' the head, or 'left' / 'right' of it."""
    card = stick(expr, pose, coat='#a6cadb', pants='#3e4a5c', goggles=True, hair='wild')
    g = place(img, card, cx, gy, s, aura=SCI_GREEN, aura_alpha=.5, rim=rim, rim_dir=rim_dir, rim_w=rim_w)
    hx, hy = g['head']; R = g['R']; size = int(48 * max(.92, min(1.1, s)))
    if label_at == 'none': pass
    elif label_at == 'above':
        label(img, 'SCIENTIST', min(W - 170, max(170, hx)), hy - R * 1.45 - 86, SCI_GREEN, size=size)
    else:
        e = 1 if label_at == 'right' else -1
        label(img, 'SCIENTIST', hx + e * (R * 1.5 + 150), hy - R * .55 - size * .8, SCI_GREEN, size=size)
    return g


# ------------------------------------------------------------------ s05
def s05(t=0.0):
    img = vgrad([(0, (30, 42, 56)), (.45, (70, 92, 104)), (.75, (96, 116, 122)), (1, (60, 74, 84))])
    d = ImageDraw.Draw(img)
    # wall tiles (static) and a cold window showing the Antarctic night (snow drifts past: t)
    for y in range(80, 1460, 90): d.line([(0, y), (W, y)], fill=(84, 104, 116), width=2)
    for x in range(0, W, 120):
        for y in range(80, 1460, 180): d.line([(x + (y // 90 % 2) * 60, y), (x + (y // 90 % 2) * 60, y + 90)], fill=(84, 104, 116), width=2)
    wx0, wy0, wx1, wy1 = 60, 520, 330, 900
    d.rounded_rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14], 18, fill=(46, 56, 66), outline=INK, width=6)
    win = vgrad([(0, (24, 40, 96)), (1, (110, 140, 210))], wx1 - wx0, wy1 - wy0)
    peak_range(win, 5, 330, 60, 150, (190, 200, 235), (130, 140, 200), (250, 250, 255), n=4)
    ImageDraw.Draw(win).rectangle([0, 320, wx1 - wx0, wy1 - wy0], fill=(226, 234, 250))
    snow_particles(win, 3, n=(30, 10, 0), sizes=(4, 8, 1), t=t)
    img.paste(win, (wx0, wy0))
    light_rays(img, (wx0 + wx1) / 2, (wy0 + wy1) / 2, (150, 190, 255), n=5, alpha=.14, spread=(10, 70), length=1100, seed=5)
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(46, 56, 66), width=12)
    d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(46, 56, 66), width=12)
    d.rounded_rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14], 18, outline=INK, width=6)
    # shelves with glowing samples (bubbles rise: t)
    for sy in (760, 1080):
        d.rectangle([700, sy, W + 10, sy + 26], fill=(150, 120, 96), outline=INK, width=5)
        d.rectangle([700, sy + 26, W + 10, sy + 40], fill=(40, 34, 40))
    for x, sy, h, c, k in ((760, 760, 150, (220, 50, 50), 'round'), (870, 760, 170, (70, 190, 120), 'bottle'),
                           (990, 760, 140, (90, 150, 240), 'round'), (770, 1080, 160, (240, 160, 60), 'bottle'),
                           (880, 1080, 120, (220, 50, 50), 'tube'), (940, 1080, 120, (220, 60, 60), 'tube'),
                           ):
        props.flask(img, x, sy, h, c, k)
    # lamp: warm cone onto the bench (dust motes drift in the beam: t; lamp sways 1 deg)
    beam = mask(); ImageDraw.Draw(beam).polygon([(150, 140), (310, 140), (760, 1480), (-60, 1480)], fill=255)
    glow(img, beam, (255, 226, 170), .32, blur=40, add=True)
    radial(img, 360, 1450, 520, (255, 214, 150), .35)
    dust(img, 4, 40, (160, 300, 820, 1440), (255, 240, 200), 170, t=t)
    d = ImageDraw.Draw(img)
    d.line([(230, 0), (230, 80)], fill=INK, width=8)
    d.chord([120, 60, 340, 210], 180, 360, fill=(60, 120, 110), outline=INK, width=6)
    d.ellipse([200, 118, 260, 148], fill=(255, 248, 220))
    # scientist behind the bench, pointing up at the microscope view
    pose = dict(armL=(24, 10), armR=(-128, -142), legL=(10, 1), legR=(-10, -1))
    g = scientist(img, 225, 1900, 1.22, expr='surprised', pose=pose)
    # bench (front face hides the legs)
    d = ImageDraw.Draw(img)
    d.polygon([(-10, 1470), (W + 10, 1470), (W + 10, 1530), (-10, 1530)], fill=(196, 206, 206), outline=INK, width=6)
    d.rectangle([-10, 1530, W + 10, H], fill=(74, 84, 98))
    d.line([(-10, 1536), (W + 10, 1536)], fill=(40, 46, 56), width=10)
    for x in (60, 420, 780):
        d.rounded_rectangle([x, 1600, x + 300, 1800], 14, fill=(84, 96, 110), outline=INK, width=5)
        d.rounded_rectangle([x + 110, 1640, x + 190, 1662], 10, fill=(196, 206, 214), outline=INK, width=4)
    ex, ey = props.microscope(img, 950, 1478, 1.0)
    # sample rack + bottle labelled with the site
    props.flask(img, 640, 1474, 84, BLOOD, 'bottle', glow_on=False)
    # magnified view: water with salt + iron, NO algae (circle zooms out of the eyepiece: scale 0 -> 1)
    cx, cy, r = 800, 680, 218
    cone = mask(); ImageDraw.Draw(cone).polygon([(ex - 30, ey), (ex + 30, ey), (cx + r * .9, cy + r * .4), (cx - r * .9, cy + r * .4)], fill=255)
    fill_mask(img, cone, (220, 250, 255), .18, blur=6)
    m = mask(); ImageDraw.Draw(m).ellipse([cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 20], fill=255)
    glow(img, m, (255, 120, 100), .5, blur=50)
    view = vgrad([(0, (255, 236, 230)), (1, (246, 196, 186))], 2 * r, 2 * r)
    vd = ImageDraw.Draw(view); rng = np.random.default_rng(3)
    for _ in range(9):  # salt cubes
        x, y, q = rng.uniform(40, 2 * r - 60), rng.uniform(40, 2 * r - 60), rng.uniform(16, 30)
        vd.polygon([(x, y), (x + q, y - q * .4), (x + 2 * q, y), (x + q, y + q * .4)], fill=(255, 255, 255), outline=INK, width=3)
        vd.polygon([(x, y), (x + q, y + q * .4), (x + q, y + q * 1.3), (x, y + q * .9)], fill=(214, 220, 236), outline=INK, width=3)
        vd.polygon([(x + q, y + q * .4), (x + 2 * q, y), (x + 2 * q, y + q * .9), (x + q, y + q * 1.3)], fill=(180, 190, 214), outline=INK, width=3)
    for _ in range(26):  # iron specks
        x, y, q = rng.uniform(20, 2 * r - 20), rng.uniform(20, 2 * r - 20), rng.uniform(5, 11)
        vd.ellipse([x - q, y - q, x + q, y + q], fill=(196, 86, 44), outline=(110, 40, 20), width=2)
    props.algae_chain(view, r, r, 1.5, color=(40, 150, 70), dashed=True)
    props.big_x(view, r, r, 84, w=24)
    cm = mask(2 * r, 2 * r); ImageDraw.Draw(cm).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    img.paste(view, (cx - r, cy - r), cm)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 24, cy - r - 24, cx + r + 24, cy + r + 24], outline=INK, width=34)
    d.ellipse([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], outline=(120, 140, 152), width=22)
    d.arc([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], 200, 290, fill=(220, 232, 240), width=10)
    d.arc([cx - r + 30, cy - r + 30, cx + r - 30, cy + r - 30], 205, 245, fill=(255, 255, 255), width=10)
    pill(img, '    NO ALGAE', cx + 10, cy - r - 30, (220, 36, 44), size=64)
    props.big_x(img, cx + 10 - 174, cy - r - 28, 20, color=(255, 255, 255), w=12)
    # cracked stamp (slams in at t=0, cracks at 0.6 s)
    st = props.stamp('MYSTERY SOLVED', SCI_GREEN, 50, cracked=True)
    rotated_paste(img, st, 640, 250, 3)
    vignette(img, .42, (10, 12, 24))
    grain(img)
    caption(img, 'no algae in it.', avoid=[face_box(g), body_box(g)], nudge=True)
    return img


def cut_in(img, cx, cy, r, label_xy=None):
    """Round cut-in of the scientist on the ice surface (house lens frame). Returns his geometry in frame coords."""
    lay = Image.new('RGBA', (W, H))
    lay.paste(vgrad([(0, (96, 120, 196)), (.5, (170, 196, 240)), (1, (230, 240, 255))], 2 * r, 2 * r), (cx - r, cy - r))
    radial(lay, cx + r * .6, cy - r * .2, r * 1.2, (150, 255, 230), .35)
    ImageDraw.Draw(lay).rectangle([cx - r, cy + r * .45, cx + r, cy + r], fill=(240, 246, 255))
    ImageDraw.Draw(lay).line([(cx - r, cy + r * .45), (cx + r, cy + r * .45)], fill=INK, width=5)
    g = scientist(lay, cx - 20 * r / 215, cy + r * .22 + (655 - 5) * r / 215, .9 * r / 215, expr='surprised',
                  pose=dict(armL=(24, 10), armR=(-125, -150), legL=(10, 1), legR=(-10, -1)),
                  rim=(150, 255, 230), rim_dir=(1, -.4), label_at='none', rim_w=14)
    m = mask(); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    glow(img, m, (120, 255, 230), .5, blur=40)
    img.paste(lay, (0, 0), m)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 20], outline=INK, width=30)
    d.ellipse([cx - r - 15, cy - r - 15, cx + r + 15, cy + r + 15], outline=(120, 140, 152), width=18)
    d.arc([cx - r - 12, cy - r - 12, cx + r + 12, cy + r + 12], 200, 290, fill=(220, 232, 240), width=8)
    lx, ly = label_xy or (cx, cy - r - 62)
    label(img, 'SCIENTIST', lx, ly, SCI_GREEN, size=48)
    return g


# ------------------------------------------------------------------ s11
def s11(t=0.0):
    """Close cross-section: ice + brine pool fill the frame; the scientist reads in a round cut-in below."""
    img = vgrad([(0, (10, 14, 44)), (.24, (40, 56, 120)), (1, (10, 14, 36))])
    surf = 470; ice_bot = lambda x: 870 + 22 * math.sin(x / 170)
    d = ImageDraw.Draw(img); rng = np.random.default_rng(2)
    for _ in range(60):  # stars (twinkle: alpha by t)
        x, y, q = rng.uniform(0, W), rng.uniform(0, surf - 60), rng.uniform(1.5, 3.5)
        d.ellipse([x - q, y - q, x + q, y + q], fill=(220, 230, 255))
    peak_range(img, 41, surf + 10, 60, 150, (70, 84, 150), (46, 56, 112), (150, 170, 220), n=7)
    # ice body: X-ray translucent bands (scan line sweeps down: t)
    xs = np.arange(-10, W + 11, 10)
    top = [(x, surf + 8 * math.sin(x / 90)) for x in xs]
    body = top + [(x, ice_bot(x)) for x in xs[::-1]]
    ice = vgrad([(0, (190, 234, 250)), (.3, (120, 196, 236)), (.5, (60, 130, 200)), (1, (20, 50, 120))], W, H)
    bm = mask(); ImageDraw.Draw(bm).polygon(body, fill=255)
    img.paste(ice, (0, 0), bm)
    d = ImageDraw.Draw(img)
    for k in range(9):  # strata
        y0 = surf + 30 + k * 40
        pts = [(x, y0 + 14 * math.sin(x / 130 + k) + 6 * math.sin(x / 41 + 2 * k)) for x in xs]
        d.line(pts, fill=(255, 255, 255) if k % 3 == 0 else (70, 134, 200), width=3 if k % 3 else 4)
    for _ in range(46):  # trapped bubbles
        x, y, q = rng.uniform(0, W), rng.uniform(surf + 40, 820), rng.uniform(3, 9)
        d.ellipse([x - q, y - q, x + q, y + q], outline=(230, 248, 255), width=2)
    for _ in range(6):  # cracks
        x, y = rng.uniform(200, W - 200), rng.uniform(surf + 40, 680)
        pts = [(x, y)]
        for _ in range(4): x += rng.uniform(-30, 30); y += rng.uniform(30, 50); pts.append((x, y))
        d.line(pts, fill=(30, 70, 130), width=4)
    # x-ray grid + scanline (inside the ice only)
    gl = layer(); gd = ImageDraw.Draw(gl)
    for x in range(0, W, 60): gd.line([(x, surf), (x, 890)], fill=(180, 240, 255, 26), width=2)
    for y in range(surf, 890, 60): gd.line([(0, y), (W, y)], fill=(180, 240, 255, 26), width=2)
    img.alpha_composite(gl)
    sy = 670 + 170 * math.sin(t)
    m = mask(); ImageDraw.Draw(m).rectangle([0, sy - 4, W, sy + 4], fill=255)
    glow(img, m, (120, 255, 240), .8, blur=10, add=True)
    # bedrock: lifted plum, lit from above by the pool (static strata, kept below the caption band)
    rock = vgrad([(0, (150, 108, 132)), (.4, (122, 86, 116)), (1, (72, 52, 84))], W, H - 850, 0)
    rl = Image.new('RGBA', (W, H)); rl.paste(rock, (0, 850))
    rm = mask(); ImageDraw.Draw(rm).polygon([(x, ice_bot(x) - 4) for x in xs] + [(W + 10, H), (-10, H)], fill=255)
    img.paste(rl, (0, 0), rm)
    d = ImageDraw.Draw(img)
    for k in range(4):
        y0 = 1500 + k * 100
        d.line([(x, y0 + 18 * math.sin(x / 110 + k * 1.7)) for x in xs], fill=(150, 108, 130) if k % 2 else (86, 60, 90), width=6)
    for x, y, q in ((80, 1480, 30), (560, 1500, 22), (1010, 1470, 34), (300, 1640, 26), (780, 1620, 30)):
        d.polygon([(x - q, y), (x - q * .3, y - q * .8), (x + q, y - q * .4), (x + q * .7, y + q * .5)], fill=(160, 118, 136), outline=(40, 26, 42), width=3)
    # brine pool: wide glowing lens under the ice (pulses 0.9-1.0: t; motes drift)
    cx, cy, rx, ry = 560, 1010, 620, 190
    radial(img, cx, cy + 60, 760, (60, 230, 200), .32)           # pool light spills onto the rock below
    pm = mask(); ImageDraw.Draw(pm).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    glow(img, pm, (60, 255, 210), .9, blur=90, add=True)
    glow(img, pm, (160, 255, 230), .6, blur=30, add=True)
    pool = vgrad([(0, (120, 255, 226)), (.5, (24, 170, 160)), (1, (10, 80, 96))], 2 * rx, 2 * ry)
    radial(pool, rx, ry * .6, rx * .7, (220, 255, 240), .6)
    dust(pool, 9, 70, (20, 10, 2 * rx - 20, 2 * ry - 10), (210, 255, 230), 200, size=(2, 7), t=t)
    cm = mask(2 * rx, 2 * ry); ImageDraw.Draw(cm).ellipse([0, 0, 2 * rx - 1, 2 * ry - 1], fill=255)
    img.paste(pool, (cx - rx, cy - ry), cm)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=INK, width=6)
    d.ellipse([cx - rx + 6, cy - ry + 6, cx + rx - 6, cy + ry - 6], outline=(190, 255, 240), width=5)
    d.arc([cx - rx + 60, cy - ry + 18, cx + rx - 60, cy + ry - 20], 200, 250, fill=(240, 255, 250), width=8)
    pill(img, 'SALTY BRINE', 560, 1050, (14, 110, 110), size=54, pad=28)
    # outflow channel up through the ice to Blood Falls (right edge), turning red at the surface
    ch = [(990, cy - 70), (1000, 790), (960, 640), (1010, surf + 40), (W + 20, surf - 10)]
    d.line(ch, fill=INK, width=26, joint='curve'); d.line(ch, fill=(90, 230, 210), width=14, joint='curve')
    d.line(ch[-2:], fill=(220, 60, 40), width=14)
    # surface snow line + plane with radar fan (plane crosses: x = 120 + 90 t; pulses expand down the fan)
    d.line(top, fill=INK, width=8)
    d.polygon(top + [(x, y + 24) for x, y in top[::-1]], fill=(246, 250, 255)); d.line(top, fill=INK, width=6)
    px_, py_ = 380, 350
    fan = mask(); ImageDraw.Draw(fan).polygon([(px_ - 10, py_ + 50), (px_ + 20, py_ + 50), (px_ + 330, cy - 90), (px_ - 300, cy - 90)], fill=255)
    fill_mask(img, fan, (140, 255, 230), .15, blur=8)
    for k in range(4):
        yk = surf + 40 + k * 100
        ImageDraw.Draw(img).arc([px_ + 5 - (yk - py_) * .48, yk - 36, px_ + 5 + (yk - py_) * .48, yk + 36], 20, 160, fill=(170, 255, 236), width=5)
    props.plane(img, px_ - 10, py_, 1.15)
    # depth arrow: surface -> pool (draws downward: t)
    d = ImageDraw.Draw(img); ax = 70
    for y0, y1 in ((surf + 30, 620), (720, ice_bot(ax) - 16)):
        d.line([(ax, y0), (ax, y1)], fill=INK, width=22); d.line([(ax, y0), (ax, y1)], fill='white', width=13)
    for y, s_ in ((surf + 30, 1), (ice_bot(ax) - 16, -1)):
        d.polygon([(ax, y), (ax - 26, y + 40 * s_), (ax + 26, y + 40 * s_)], fill='white', outline=INK, width=4)
    pill(img, '400 m', ax + 84, 670, (36, 120, 200), size=62, pad=24)
    # cut-in: the scientist up on the ice, in a round frame like the s05 lens (pops in: scale 0 -> 1)
    g = cut_in(img, 320, 1610, 250, label_xy=(810, 1470))
    # year counter (digits roll up: t)
    bx0, by0, bx1, by1 = 600, 1560, 1050, 1706
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([bx0, by0 + 8, bx1, by1 + 8], 30, fill=INK)
    d.line([(bx0 - 40, (by0 + by1) / 2), (bx0, (by0 + by1) / 2)], fill=(120, 255, 230), width=8)
    d.rounded_rectangle([bx0, by0, bx1, by1], 30, fill=(20, 30, 60), outline=(120, 255, 230), width=6)
    d.text(((bx0 + bx1) / 2, by0 + 36), 'SEALED FOR', font=font(34, True), fill=(150, 240, 230), anchor='mm')
    d.text(((bx0 + bx1) / 2, by0 + 96), '1,000,000+ YEARS', font=font(44), fill='white', anchor='mm')
    vignette(img, .3, (4, 6, 20))
    grain(img, .03, .04)
    title(img, [('A HIDDEN SEA', 'white', 100), ('UNDER THE ICE', (110, 255, 226), 84)], 64)
    caption(img, 'four hundred', avoid=[face_box(g)], nudge=True)
    return img


# ------------------------------------------------------------------ s15
def s15(t=0.0):
    """Two-shot at the falls. The cliff sits high so the snow field under the rust fan is the caption band;
    the equation chip sits low between the characters."""
    img = Image.new('RGBA', (W, H))
    polar_backdrop(img, [(0, (52, 36, 104)), (.24, (150, 76, 130)), (.42, (250, 140, 110)), (.5, (255, 190, 130))],
                   (220, 820, (255, 170, 110)),
                   ((214, 150, 170), (150, 100, 150), (255, 226, 220)),
                   ((180, 130, 170), (110, 80, 140), (255, 236, 236)),
                   (255, 200, 170), t, horizon=860)
    top = lambda x: 830 + 24 * math.sin(x / 90) + (x - 540) ** 2 / 9000
    bot = lambda x: 1200
    ice_cliff(img, -20, W + 20, top, bot, seed=12, lit=(250, 230, 236), mid=(214, 196, 220), shade=(160, 140, 196),
              deep=(96, 80, 150), snow=(255, 246, 246))
    haze(img, 1150, 1250, (255, 220, 214), .5)
    left, right = blood_falls(img, 520, 850, 1210, w=84, color=(206, 76, 30), hi=(248, 134, 52), rust=True, t=t)
    yg = lambda x: 1210 + 10 * math.sin(x / 120)
    snow_ground(img, yg, color=(238, 222, 234), shade=(196, 170, 204), seed=9)
    # rust terraces (the iron-oxide cone at the foot), kept flat so the snow below stays clean
    d = ImageDraw.Draw(img); ax = left[-1][0] + 40
    for k, (w_, h_, c) in enumerate(((760, 120, (150, 60, 30)), (580, 92, (200, 86, 34)), (400, 66, (234, 118, 44)), (240, 42, (255, 162, 70)))):
        ay = 1212 + k * 3
        d.chord([ax - w_ / 2, ay - h_ * .4, ax + w_ / 2, ay + h_], 180, 360, fill=INK)
        d.chord([ax - w_ / 2 + 6, ay - h_ * .4 + 6, ax + w_ / 2 - 6, ay + h_ - 6], 180, 360, fill=c)
    red_fan(img, (ax, 1222), (760, 44), color=(196, 74, 26), edge=(244, 136, 56))
    # O2 bubbles drift down toward the stream and turn orange on contact (t)
    for x, y, q in ((320, 750, 52), (730, 730, 58), (700, 935, 42)):
        d.ellipse([x - q - 3, y - q - 3, x + q + 3, y + q + 3], fill=(255, 255, 255))
        d.ellipse([x - q, y - q, x + q, y + q], fill=(150, 210, 255), outline=INK, width=6)
        d.arc([x - q * .7, y - q * .7, x + q * .2, y + q * .2], 190, 260, fill='white', width=4)
        d.text((x - q * .12, y + 2), 'O', font=font(int(q * .95), True), fill=(20, 60, 120), anchor='mm')
        d.text((x + q * .38, y + q * .3), '2', font=font(int(q * .5), True), fill=(20, 60, 120), anchor='mm')
    # wind ridges (sastrugi) + warm low sun on the lower snow, below the caption band (static)
    radial(img, 140, 1500, 700, (255, 196, 160), .22)
    for k in range(6):
        y0 = 1430 + k * 80; x0 = 300 + (k % 2) * 160
        pts = [(x0 + u * 14, y0 + 10 * math.sin(u / 3 + k)) for u in range(0, 34)]
        d.line(pts, fill=(214, 186, 214), width=5); d.line([(x, y + 6) for x, y in pts], fill=(255, 250, 250), width=3)
    rng = np.random.default_rng(15)
    for x, y in ((360, 1700), (640, 1790), (520, 1560), (760, 1660)):   # lake-ice cracks in the snow
        pts = [(x, y)]
        for _ in range(5): x += rng.uniform(20, 50); y += rng.uniform(-18, 18); pts.append((x, y))
        d.line(pts, fill=(120, 96, 150), width=5)
        bx, by = pts[2]; d.line([(bx, by), (bx + 20, by + 30)], fill=(120, 96, 150), width=4)
    props.footprints(img, [(900 - i * 60, 1880 - i * 38) for i in range(5)], s=1.0)
    rocks(img, 17, [(470, 1880, 46), (690, 1900, 34)], lit=(170, 110, 100), shade=(104, 64, 80))
    rocks(img, 7, [(70, 1460, 34), (1010, 1470, 40)], lit=(170, 110, 100), shade=(104, 64, 80))
    g1 = geologist(img, 205, 1890, .9, expr='determined', pose='think', rim=(255, 190, 140), rim_dir=(1, -.3))
    g2 = scientist(img, 875, 1890, .9, expr='surprised', pose=dict(armL=(128, 142), armR=(-24, -10), legL=(11, 1), legR=(-11, -1)),
                   rim=(255, 190, 140), rim_dir=(-1, -.3))
    snow_particles(img, 19, n=(60, 24, 8), wind=(5, 1), t=t)
    vignette(img, .36, (30, 10, 40))
    grain(img)
    title(img, [('NOT BLEEDING.', 'white', 104), ('RUSTING.', (255, 128, 44), 150)], 150)
    pill(img, 'IRON + OXYGEN = RUST', 560, 1500, (206, 84, 30), size=40, pad=22)
    caption(img, "It's rusting.", avoid=[face_box(g1), face_box(g2)], nudge=True)
    return img


SHOTS = {'s01': s01, 's05': s05, 's11': s11, 's15': s15}

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    small = None; args = sys.argv[2:]
    if '--small' in args:
        i = args.index('--small'); small = args[i + 1]; args = args[:i] + args[i + 2:]
        os.makedirs(small, exist_ok=True)
    for name in args or SHOTS:
        im = SHOTS[name]().convert('RGB')
        im.save(f'{out}/{name}_style.png', optimize=True)
        if small: im.resize((540, 960), Image.LANCZOS).save(f'{small}/{name}_540.png')
        print(name, 'ok')

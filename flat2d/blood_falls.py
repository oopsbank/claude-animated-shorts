"""Blood Falls shots as functions of time, built from flat2d kit layers (motion test s01-s06).

Each shot is `sNN(u, D, cue)`: u = seconds into the shot, D = shot length, cue(word_index_in_line) =
shot-local time of a spoken word (so actions land on the voice). It returns (img, info), where img is the
finished frame without captions and info['faces'] holds face boxes for caption placement.

Motion per frame (videos/blood-falls/style/NOTES.md): parallax (layers shift by cam*(1 - depth factor),
then the whole frame is panned/pushed by `anim.camera`), particles (snow, dust, bubbles), glow pulses,
character in-betweens (anticipation -> action -> overshoot -> settle), breathing + blinks, stamps and
titles slamming in. Nothing is ever frozen.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageChops
import kit, props, anim
from kit import (W, H, INK, vgrad, radial, light_rays, cloud_bands, haze, peak_range, ice_cliff, snow_ground,
                 rocks, snow_particles, dust, contact_shadow, label, title, pill, font, mask, glow, fill_mask,
                 layer, lerp, rgb, foreground_frame)
from anim import smooth, ease_out, ease_in, out_back, seg, mix, add, chain, damp, slam, pop, shake, actor, STAND, POSES
import style_frames as sf
import stickman

GEO_BLUE, SCI_GREEN, BLOOD, EXP_ORANGE = sf.GEO_BLUE, sf.SCI_GREEN, sf.BLOOD, (236, 128, 34)
SCI_KW = dict(coat='#a6cadb', pants='#3e4a5c', goggles=True, hair='wild')
GEO_KW = dict(pants='#3c3a52')

# ---------------------------------------------------------------- shared pieces
def face_box(g, pad=1.15):
    hx, hy = g['head']; R = g['R'] * pad; return (hx - R, hy - R, hx + R, hy + R)


def geologist(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, axe=True,
              rim=(255, 196, 150), rim_dir=(1, -.3), name='GEOLOGIST · 1911', color=GEO_BLUE, bphase=0.0, pants=None):
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=color, aura_alpha=.45,
              rim=rim, rim_dir=rim_dir, bphase=bphase, pants=pants or GEO_KW['pants'])
    props.fur_hat(img, g['head'], g['R'])
    if axe:
        hx, hy, _ = g['hands']['L']
        props.ice_axe(img, (hx, hy), s * .9)
        r = stickman.T / 2 * s; d = ImageDraw.Draw(img)
        d.ellipse([hx - r - 3, hy - r - 3, hx + r + 3, hy + r + 3], fill=INK)
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(246, 246, 242))
    if label_on:
        hx, hy = g['head']
        label(img, name, min(W - 250, max(250, hx)) if hx > 150 else hx + 100, hy - g['R'] * 1.32 - 92, color, size=int(48 * max(.92, min(1.1, s))))
    return g


def scientist(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, rim=(190, 230, 255),
              rim_dir=(-.4, -1), bphase=0.3):
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=SCI_GREEN, aura_alpha=.5,
              rim=rim, rim_dir=rim_dir, bphase=bphase, **SCI_KW)
    if label_on:
        hx, hy = g['head']
        label(img, 'SCIENTIST', min(W - 170, max(170, hx)), hy - g['R'] * 1.45 - 86, SCI_GREEN, size=int(48 * max(.92, min(1.1, s))))
    return g


def backdrop(img, t, cam, sky, sun, far, near, haze_col, horizon=1040, sun_r=620):
    """Sky + sun + two faceted ranges + haze. Parallax: far range 0.2x, near 0.45x of the camera pan
    (drawn shifted by cam*(1-f) because the whole frame is later panned by cam). Clouds drift t*12 px/s,
    rays rotate and flicker, haze breathes."""
    img.paste(vgrad(sky))
    sx = sun[0] + cam * .95
    radial(img, sx, sun[1], sun_r, sun[2], .52 + .04 * math.sin(t * 1.7))
    radial(img, sx, sun[1], 140, (255, 246, 228), .95, power=.6)
    light_rays(img, sx, sun[1], sun[2], alpha=.15 + .03 * math.sin(t * 2.3), spread=(195, 345), seed=3,
               phase=2 * math.sin(t * .6))
    cloud_bands(img, 2, horizon - 740, horizon - 180, (255, 236, 226), .28, n=6, drift=t * 12 + cam * .9)
    peak_range(img, 21, horizon - 40, 140, 300, *far, n=8, x_shift=cam * .8)
    haze(img, horizon - 220, horizon + 40, haze_col, .5 + .06 * math.sin(t * .9))
    peak_range(img, 22, horizon + 20, 120, 260, *near, ink=INK, ink_w=4, n=6, x_shift=cam * .55)
    haze(img, horizon - 40, horizon + 120, haze_col, .46 + .05 * math.sin(t * .7 + 1))


def falls_glow(img, x, y, t, r=300, a=.16):
    """Red glow pulse at the foot of the falls (0.9-1.0 of the base level)."""
    radial(img, x, y, r, (255, 60, 40), a * (0.82 + 0.18 * math.sin(t * 3.1)))


def mist(img, seed, box, t, color=(255, 236, 236), n=26):
    """Spray rising at the foot of the falls."""
    rng = np.random.default_rng(seed); lay = layer(); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    for _ in range(n):
        ph = rng.uniform(0, 1); sp = rng.uniform(.25, .5)
        u = (ph + t * sp) % 1
        x = rng.uniform(x0, x1) + 30 * math.sin(t + ph * 6) ; y = y1 - (y1 - y0) * u
        s = rng.uniform(10, 26) * (0.6 + u)
        d.ellipse([x - s, y - s * .7, x + s, y + s * .7], fill=rgb(color) + (int(120 * math.sin(math.pi * u)),))
    img.alpha_composite(kit.soft_layer(lay, 6))


def finish(img, t, zoom, fx, fy, dx=0.0, dy=0.0, vig=(.38, (16, 14, 40)), grain_amt=.035):
    img = anim.camera(img, zoom, fx, fy, dx, dy)
    anim.vignette(img, vig[0], vig[1])
    anim.grain(img, grain_amt, t=t)
    return img


_titles = {}
def slam_title(img, key, lines, y, t, t0, size=104, stagger=.16):
    """House title, one line at a time, each slamming 1.18 -> 1 with overshoot (cached layers)."""
    for i, item in enumerate(lines):
        k = (key, i)
        if k not in _titles:
            sz = item[2] if len(item) > 2 else size
            yy = y + sum((lines[j][2] if len(lines[j]) > 2 else size) * 1.12 for j in range(i))
            _titles[k] = anim.text_layer(lambda l: title(l, [item], 60, size=sz), W, int(sz * 2.2)), yy
        (lay, (cx, cy)), yy = _titles[k]
        s = slam(t, t0 + i * stagger)
        anim.scaled_paste(img, lay, cx, yy - 60 + cy, s)


def stamp_layer(text='MYSTERY SOLVED', size=62):
    k = ('stamp', text, size)
    if k not in _titles: _titles[k] = props.stamp(text, SCI_GREEN, size, cracked=False)
    return _titles[k]


def stamp_halves(text='MYSTERY SOLVED', size=62):
    """Split the stamp layer along a jagged crack between the words: (left, right, crack points)."""
    k = ('halves', text, size)
    if k not in _titles:
        lay = stamp_layer(text, size); Wd, Hd = lay.size
        f = font(size); gap = 60 + kit.text_w(text.split(' ')[0], f) + kit.text_w(' ', f) / 2
        crack = [(gap + 8, 0), (gap - 10, Hd * .28), (gap + 10, Hd * .5), (gap - 8, Hd * .74), (gap + 5, Hd)]
        mL = mask(Wd, Hd); ImageDraw.Draw(mL).polygon([(0, 0)] + crack + [(0, Hd)], fill=255)
        L = layer(Wd, Hd); R = layer(Wd, Hd)
        L.paste(lay, (0, 0), mL); R.paste(lay, (0, 0), ImageChops.invert(mL))
        for half, off in ((L, 0), (R, 0)):
            ImageDraw.Draw(half).line(crack, fill=INK + (255,), width=10)
        _titles[k] = (L, R, crack)
    return _titles[k]


STAMP_XY, STAMP_ANG = (540, 270), -5


def draw_stamp(img, t, t_slam, t_crack=None):
    """MYSTERY SOLVED: slams in (1.5 -> 1), then (t_crack) cracks between the words and the halves split
    apart, tilt and sag, with chips falling."""
    if t < t_slam: return
    cx, cy = STAMP_XY
    if t_crack is None or t < t_crack:
        v = t - t_slam
        if v < .12: s = anim.lerp(1.45, .92, ease_in(v / .12))                  # falls onto the page
        elif v < .34: s = anim.lerp(.92, 1.0, out_back((v - .12) / .22, 2.0))   # squash, overshoot, settle
        else: s = 1 + .004 * math.sin(t * 3)
        a = min(1.0, .35 + v / .08)
        if .1 < v < .45:                                                         # ink burst ring on impact
            k = (v - .1) / .35; m = mask(); r = 260 + 260 * ease_out(k)
            ImageDraw.Draw(m).ellipse([cx - r, cy - r * .45, cx + r, cy + r * .45], outline=255, width=int(16 * (1 - k)) + 2)
            fill_mask(img, m, SCI_GREEN, .8 * (1 - k), blur=3)
        anim.scaled_paste(img, stamp_layer(), cx, cy, s, STAMP_ANG, a)
        return
    L, R, crack = stamp_halves(); u = t - t_crack
    sp = out_back(seg(u, 0, .35), 1.8); sag = 26 * ease_in(seg(u, .3, 3.0)) + 6 * math.sin(u * 2)
    fall = max(0.0, u - .65); sag += 1400 * fall * fall                     # the halves drop away with gravity
    if sag > 1500: return
    Wd = L.width
    anim.scaled_paste(img, L, cx - 80 * sp - 12 * u - 120 * fall, cy + 14 * sp + sag * .9, 1.0, STAMP_ANG - 9 * sp - 2 * u - 70 * fall)
    anim.scaled_paste(img, R, cx + 90 * sp + 14 * u + 140 * fall, cy - 4 * sp + sag * 1.1, 1.0, STAMP_ANG + 12 * sp + 3 * u + 85 * fall)
    rng = np.random.default_rng(7); d = ImageDraw.Draw(img)
    gx = cx - Wd / 2 + crack[2][0]
    for i in range(14):  # chips fall with gravity
        vx, vy = rng.uniform(-220, 220), rng.uniform(-320, -80); q = rng.uniform(7, 16)
        x = gx + vx * u; y = cy + vy * u + 900 * u * u
        if y < H:
            d.polygon([(x - q, y), (x, y - q), (x + q * .8, y + q * .3)], fill=(250, 248, 240), outline=SCI_GREEN)
    if u < .12:  # crack flash
        radial(img, gx, cy, 260, (255, 255, 230), .7 * (1 - u / .12))


# ---------------------------------------------------------------- s01: walk in, stop, point
def s01_world(img, u, D, cam, grow=None):
    """The s01 set (also the loop-back framing of s16b): moraine, glacier tongue, the falls, sledge."""
    backdrop(img, u, cam, [(0, (34, 52, 116)), (.3, (70, 112, 190)), (.52, (246, 190, 172)), (.6, (255, 214, 182))],
             (860, 960, (255, 196, 150)), ((198, 186, 220), (156, 150, 200), (246, 240, 250)),
             ((168, 182, 226), (110, 128, 196), (250, 250, 255)), (255, 222, 210))
    peak_range(img, 31, 1330, 160, 330, (170, 122, 96), (112, 78, 74), (240, 236, 244), ink=INK, ink_w=5, n=5,
               snow_frac=.22, ground=(120, 86, 78), x_shift=cam * .3)
    haze(img, 1180, 1420, (255, 214, 200), .22 + .05 * math.sin(u * 1.1))
    d = ImageDraw.Draw(img)
    slope = [(-10, 1170), (120, 1120), (260, 1150), (420, 1210), (420, 1560), (-10, 1560)]
    d.polygon(slope, fill=(132, 92, 84))
    d.polygon([(-10, 1170), (120, 1120), (150, 1380), (-10, 1420)], fill=(170, 118, 98))
    d.polygon([(120, 1120), (260, 1150), (200, 1260), (130, 1230)], fill=(244, 238, 246))
    for k in range(5):
        d.line([(-10, 1260 + k * 52), (200, 1250 + k * 56), (420, 1290 + k * 50)], fill=(104, 70, 70), width=4)
    d.line(slope[:4], fill=INK, width=5)
    rocks(img, 13, [(60, 1330, 44), (300, 1290, 30), (170, 1450, 54), (380, 1420, 26)])
    top = lambda x: 930 - (x - 360) * .06 + 18 * math.sin(x / 70)
    bot = lambda x: 1530 + (x - 360) * .02
    ice_cliff(img, 360, W + 60, top, bot, seed=8, shade=(118, 164, 220), deep=(52, 92, 160))
    haze(img, 1460, 1600, (230, 238, 252), .45 + .08 * math.sin(u * 1.3))
    left, right = sf.blood_falls(img, 720, 960, 1540, w=64, t=u * 1.6)
    yg = lambda x: 1540 + 12 * math.sin(x / 140)
    snow_ground(img, yg, seed=6)
    rocks(img, 3, [(140, 1600, 44), (980, 1660, 56), (60, 1830, 70), (1040, 1890, 80), (470, 1590, 26)])
    grow = .86 + .14 * smooth(u / D) if grow is None else grow       # the red fan creeps outward
    sf.red_fan(img, (left[-1][0] + 60, 1548), (420 * grow, 150 * grow))
    falls_glow(img, left[-1][0] + 80, 1560, u)
    mist(img, 1, (left[-1][0] - 40, 1440, left[-1][0] + 220, 1580), u)
    props.footprints(img, [(40 + i * 46, 1900 - i * 34) for i in range(5)], s=1.1)
    sledge(img, 660, 1690)


def s01(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-16, 16, smooth(u / D))
    s01_world(img, u, D, cam)
    # geologist: walk in (foot-locked), stop with follow-through, turn, anticipate, point with overshoot
    s = .98; t_walk = .825; X_END = 420
    if u <= t_walk:
        tr = _walk_cache(t_walk); f = min(len(tr) - 1, int(round(u * 30)))
        pose = anim.walk_pose(u); x = X_END + tr[f] * s; look = .7; lean = 4.0; expr = 'neutral'
    else:
        v = u - t_walk; last = anim.walk_pose(t_walk)
        down = add(last, legL=(-8, 14), legR=(-8, 14))
        antic = add(STAND, armR=(26, 34), armL=(-6, -8), legL=(4, -3), legR=(-4, 3))
        point = dict(POSES['point'])
        if v < .12: pose = mix(last, down, smooth(v / .12))
        elif v < .5: pose = mix(down, STAND, smooth((v - .12) / .38))
        else: pose = dict(STAND)
        sw = damp(v, 14, 4.5, 14); pose = add(pose, armL=(sw, sw * 1.4), armR=(-sw, -sw * 1.4))
        if v < .3: pose['_side'] = True
        else: pose.pop('_side', None)
        t_a = max(.55, cue(14) - .6)                                       # wind up just before "found"
        if v >= t_a - t_walk + 0 and u >= t_a:
            w_ = u - t_a
            if w_ < .3: pose = mix(STAND, antic, smooth(w_ / .3))
            elif w_ < .8: pose = mix(antic, point, out_back(seg(w_, .3, .8), 2.0))
            else: pose = add(point, armR=(4 * smooth(seg(w_, .72, 1.1)) + 2.5 * math.sin((w_ - .8) * 5), 6 * smooth(seg(w_, .72, 1.1)) + 4 * math.sin((w_ - .8) * 5 - .6)))
        x = X_END + 10 * smooth(v / .4)
        look = .7 * (1 - smooth(v / .5)) + .35 * smooth(seg(u, t_a, t_a + .5))
        lean = 4 * (1 - smooth(v / .5)) + 3 * out_back(seg(u, cue(16) - .1, cue(16) + .35)) if u >= t_a else 4 * (1 - smooth(v / .5))
        expr = 'surprised' if u >= t_a + .1 else ('worried' if u > 1.9 else 'neutral')
        peer = out_back(seg(u, 1.9, 2.4), 1.6) * (1 - smooth(seg(u, t_a, t_a + .3)))   # leans in to peer at the red
        lean += 6 * peer; look += .3 * peer
        lean += 1.2 * math.sin(u * 1.3) * smooth(seg(v, .5, 1.0))                   # weight shift in the hold
        lean -= 4 * math.sin(math.pi * seg(u, t_a, t_a + .3))                      # wind-up: leans back first
    g = geologist(img, u, pose, expr, x, 1800, s, look=look, lean=lean)
    fx = cam * -.6
    foreground_frame(img, [[(820 + fx, 1940), (900 + fx, 1830), (1010 + fx, 1790), (1100 + fx, 1820), (1100 + fx, 1940)]],
                     color=(150, 170, 214), alpha=.9)
    snow_particles(img, 9, n=(80, 36, 12), wind=(5, 1), t=u)
    img = finish(img, u, 1.05 + .04 * smooth(u / D), 700, 1250, dx=-cam * 1.05)
    slam_title(img, 's01', [('THE GLACIER', 'white'), ('IS BLEEDING', (255, 72, 60))], 300, u, .15, size=112)
    return img, {'faces': [face_box(g)]}


_wc = {}
def _walk_cache(t_end):
    if t_end not in _wc: _wc[t_end] = anim.walk_track(t_end)
    return _wc[t_end]


def sledge(img, sx0, sy0):
    """1911 man-hauled sledge with crates (static prop)."""
    d = ImageDraw.Draw(img)
    contact_shadow(img, sx0 + 150, sy0 + 40, 360, (90, 100, 150), .45)
    for dx_ in (0, 22):
        pts = [(sx0 - 20, sy0 + 14 + dx_), (sx0 + 300, sy0 + 14 + dx_), (sx0 + 340, sy0 - 16 + dx_)]
        d.line(pts, fill=INK, width=14, joint='curve'); d.line(pts, fill=(150, 104, 64), width=7, joint='curve')
    d.rectangle([sx0 + 20, sy0 - 120, sx0 + 170, sy0 + 10], fill=(170, 120, 74), outline=INK, width=6)
    d.line([(sx0 + 20, sy0 - 60), (sx0 + 170, sy0 - 60)], fill=(120, 82, 52), width=6)
    d.rectangle([sx0 + 180, sy0 - 80, sx0 + 290, sy0 + 10], fill=(96, 120, 170), outline=INK, width=6)
    d.line([(sx0 + 235, sy0 - 80), (sx0 + 235, sy0 + 10)], fill=(200, 60, 50), width=8)
    d.polygon([(sx0 + 20, sy0 - 120), (sx0 + 170, sy0 - 120), (sx0 + 160, sy0 - 134), (sx0 + 30, sy0 - 134)], fill=(250, 252, 255), outline=INK)


# ---------------------------------------------------------------- s02 / s03: close on the falls
def falls_close(img, u, cam, cold=0.0, ice_grow=0.0, flow=1.0):
    """The ice wall fills the frame; the falls pour down the middle onto the snow. cold 0..1 = colder sky."""
    sky = [(0, lerp((40, 60, 130), (20, 30, 70), cold)), (.18, lerp((120, 150, 214), (60, 84, 150), cold)),
           (.3, lerp((250, 206, 186), (150, 170, 210), cold))]
    img.paste(vgrad(sky))
    radial(img, 900 + cam * .95, 300, 520, lerp((255, 196, 150), (170, 200, 255), cold), .45 + .04 * math.sin(u * 1.5))
    cloud_bands(img, 4, 40, 420, (255, 236, 226), .24, n=4, drift=u * (12 + 60 * cold) + cam * .9)
    peak_range(img, 23, 560, 120, 240, lerp((198, 186, 220), (150, 160, 200), cold), lerp((156, 150, 200), (100, 110, 160), cold),
               (246, 240, 250), n=7, x_shift=cam * .8)
    haze(img, 380, 600, lerp((255, 222, 210), (200, 214, 240), cold), .5 + .05 * math.sin(u))
    top = lambda x: 530 + 26 * math.sin(x / 120) + 10 * math.sin(x / 37)
    bot = lambda x: 1390 + 8 * math.sin(x / 90)
    ice_cliff(img, -40, W + 40, top, bot, seed=14, shade=(118, 164, 220), deep=(52, 92, 160))
    if ice_grow > 0:  # icicles grow along the lip and the ledges (everything freezes but the falls)
        rng = np.random.default_rng(31); d = ImageDraw.Draw(img)
        for i in range(34):
            x = rng.uniform(0, W);
            if 300 < x < 720: continue
            y = top(x) + rng.choice([18, 18, 300, 520]) * 1.0; L = rng.uniform(40, 130) * smooth(ice_grow * rng.uniform(.8, 1.4))
            if L < 4: continue
            wq = rng.uniform(9, 16)
            d.polygon([(x - wq, y), (x + wq, y), (x + 2, y + L)], fill=(236, 248, 255), outline=(90, 130, 190))
            d.line([(x - wq * .3, y + 4), (x, y + L * .7)], fill='white', width=3)
    haze(img, 1320, 1450, (236, 240, 252), .45 + .08 * math.sin(u * 1.4))
    left, right = sf.blood_falls(img, 470, 545, 1400, w=118, t=u * 1.6 * flow)
    yg = lambda x: 1400 + 10 * math.sin(x / 140)
    snow_ground(img, yg, seed=12, drifts=8)
    rocks(img, 5, [(90, 1500, 40), (1000, 1520, 50), (40, 1760, 60), (760, 1880, 44)])
    return left, right


def sign(img, x, gy, u_drop, wob):
    """BLOOD FALLS wooden sign: drops (ease-in fall), plants with a squash, wobbles (damped)."""
    if u_drop < 0: return
    fall = ease_in(seg(u_drop, 0, .26)); y = gy - (1 - fall) * 900
    sq = 1.0
    if u_drop > .26: sq = 1 - damp(u_drop - .26, .08, 7, 22)
    ang = damp(u_drop - .26, 9, 4, 11) + wob
    lay = layer(420, 420); d = ImageDraw.Draw(lay)
    d.rectangle([196, 150, 224, 420], fill=(120, 84, 56), outline=INK, width=5)
    d.polygon([(20, 40), (400, 30), (404, 168), (16, 176)], fill=INK)
    d.polygon([(28, 46), (394, 38), (396, 160), (24, 168)], fill=(176, 128, 82))
    for yy in (78, 118): d.line([(30, yy), (394, yy - 4)], fill=(150, 104, 64), width=3)
    d.polygon([(28, 46), (394, 38), (394, 56), (28, 64)], fill=(250, 252, 255))  # snow on the top edge
    d.text((210, 108), 'BLOOD FALLS', font=font(44), fill=(150, 20, 28), anchor='mm', stroke_width=3, stroke_fill=(70, 10, 16))
    lay = lay.resize((420, int(420 * sq)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, center=(210, 420 * sq))
    contact_shadow(img, x, gy, 160, (90, 110, 160), .45 * fall)
    img.alpha_composite(lay, (int(x - 210), int(y - 420 * sq)))
    if .26 < u_drop < .9:  # snow puff on the plant
        v = (u_drop - .26) / .64; rng = np.random.default_rng(3); d = ImageDraw.Draw(img)
        for i in range(10):
            a = rng.uniform(math.pi, 2 * math.pi); r = 40 + 160 * ease_out(v)
            q = 14 * (1 - v) + 3
            d.ellipse([x + math.cos(a) * r - q, gy + math.sin(a) * r * .35 - q, x + math.cos(a) * r + q, gy + math.sin(a) * r * .35 + q], fill=(255, 255, 255))


def s02(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(14, -14, smooth(u / D))
    left, right = falls_close(img, u, cam)
    grow = .7 + .3 * smooth(u / D)
    sf.red_fan(img, (left[-1][0] + 80, 1408), (620 * grow, 250 * grow), seed=8)
    falls_glow(img, left[-1][0] + 100, 1420, u, r=420, a=.2)
    mist(img, 2, (left[-1][0] - 60, 1280, left[-1][0] + 300, 1440), u, n=34)
    # geologist recoils: point (from s01) -> anticipation -> step back + hand to the mouth (staged), scared
    t0 = cue(7) - .35                                                    # on "pouring"
    point = dict(POSES['point'])
    think = dict(POSES['think']); think['_name'] = 'think'; think['_sh'] = (278, 322)
    st_think = dict(STAND); st_think['_name'] = 'think'; st_think['_sh'] = (300, 300)
    stage1 = mix(think, st_think, 0.0); stage1['armL'] = STAND['armL']
    recoil = add(STAND, armL=(18, 30), armR=(-18, -30))
    w_ = u - t0
    t_sg = cue(19) - .14                                                  # the sign lands: flinch + turn to it
    if w_ < 0: pose = add(point, armR=(2.5 * math.sin(u * 5), 4 * math.sin(u * 5 - .6))); expr = 'surprised'
    elif w_ < .18: pose = mix(point, add(point, armR=(10, 10), legL=(3, -2), legR=(-3, 2)), smooth(w_ / .18)); expr = 'surprised'
    elif w_ < .45: pose = mix(add(point, armR=(10, 10)), recoil, smooth(seg(w_, .18, .45))); expr = 'scared'
    elif w_ < .7: pose = mix(st_think, stage1, smooth(seg(w_, .45, .7))); expr = 'scared'
    elif w_ < .95: pose = mix(stage1, think, out_back(seg(w_, .7, .95), 1.3)); expr = 'scared'
    else: pose = dict(think); expr = 'scared'
    step = out_back(seg(w_, .18, .55), 1.4) if w_ > 0 else 0
    lift = math.sin(math.pi * seg(w_, .18, .46)) if 0 < w_ < .46 else 0
    pose = add(pose, legL=(30 * lift, 4 * lift))                               # a real step back: the left foot lifts
    hop = 34 * math.sin(math.pi * seg(w_, .18, .42)) if 0 < w_ < .42 else 0
    lean = -8 * out_back(seg(w_, .18, .5), 2.2) + 3 * smooth(seg(w_, 1.2, 2.2)) if w_ > 0 else 1.5
    shake_head = .28 * math.sin((u - t0 - 1.3) * 9) * (seg(u, t0 + 1.3, t0 + 1.5) * (1 - seg(u, t0 + 2.2, t0 + 2.5)))
    look = .25 + shake_head + .45 * out_back(seg(u, t_sg, t_sg + .3)) if w_ > 0 else .25
    hop += 18 * math.sin(math.pi * seg(u, t_sg, t_sg + .22)) if t_sg < u < t_sg + .22 else 0
    g = geologist(img, u, pose, expr, 380 - 70 * step, 1830, .84, look=look, lean=lean, hop=hop)
    sign(img, 800, 1770, u - (cue(19) - .4), 1.2 * math.sin(u * 1.3))
    fx = cam * -.6
    foreground_frame(img, [[(-20 + fx, 1940), (-20 + fx, 1800), (90 + fx, 1770), (230 + fx, 1830), (330 + fx, 1940)]],
                     color=(150, 170, 214), alpha=.88)
    snow_particles(img, 21, n=(70, 30, 10), wind=(6, 1), t=u)
    z = 1.0 + .12 * smooth(u / D)
    img = finish(img, u, 1.05 + z - 1, 560, anim.lerp(950, 1150, smooth(u / D)), dx=-cam * 1.05)
    return img, {'faces': [face_box(g)]}


def frost(img, k, seed=5):
    """Frost creeping in from the corners (k 0..1): branching white crystal lines + a pale rim."""
    if k <= 0: return
    rng = np.random.default_rng(seed); lay = layer(); d = ImageDraw.Draw(lay)
    for cx, cy in ((0, 0), (W, 0), (0, H), (W, H)):
        for i in range(16):
            a0 = math.atan2(H / 2 - cy, W / 2 - cx) + rng.uniform(-.9, .9)
            x, y = cx, cy; L = rng.uniform(90, 230) * k
            pts = [(x, y)]
            for j in range(6):
                a = a0 + rng.uniform(-.5, .5); st = L / 6
                x += math.cos(a) * st; y += math.sin(a) * st; pts.append((x, y))
                if j % 2 == 1:
                    b = a + rng.choice([-1, 1]) * rng.uniform(.6, 1.1)
                    d.line([(x, y), (x + math.cos(b) * st * .8, y + math.sin(b) * st * .8)], fill=(240, 250, 255, 150), width=3)
            d.line(pts, fill=(240, 250, 255, 170), width=4)
    img.alpha_composite(kit.soft_layer(lay, 1.2))
    m = mask(); md = ImageDraw.Draw(m)
    for cx, cy in ((0, 0), (W, 0), (0, H), (W, H)):
        r = 360 * k; md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    fill_mask(img, m, (226, 240, 255), .45, blur=80)


def thermometer(img, x, y0, y1, level, deg):
    """Tall thermometer: the red column drops to `level` (0 top .. 1 bottom); the readout rolls."""
    d = ImageDraw.Draw(img); r = 64; w = 70
    m = mask(); ImageDraw.Draw(m).rounded_rectangle([x - w / 2 - 20, y0 - 20, x + w / 2 + 20, y1 + r * 2 + 20], 60, fill=255)
    glow(img, m, (150, 200, 255), .45, blur=30)
    d.rounded_rectangle([x - w / 2, y0, x + w / 2, y1 + 20], w / 2, fill=(230, 240, 250), outline=INK, width=8)
    d.ellipse([x - r, y1, x + r, y1 + 2 * r], fill=(230, 240, 250), outline=INK, width=8)
    for i in range(9):  # ticks
        yy = y0 + 40 + i * (y1 - y0 - 60) / 8
        d.line([(x + w / 2 - 8, yy), (x + w / 2 + 24, yy)], fill=INK, width=6)
    top = y0 + 40 + (y1 - y0 - 60) * level
    d.rounded_rectangle([x - 16, top, x + 16, y1 + 40], 16, fill=(220, 40, 44))
    d.ellipse([x - r + 14, y1 + 14, x + r - 14, y1 + 2 * r - 14], fill=(220, 40, 44))
    d.ellipse([x - r * .5, y1 + r * .4, x - r * .1, y1 + r * .8], fill=(255, 160, 150))
    d.line([(x - 10, y0 + 30), (x - 10, top - 10)], fill='white', width=6)


def s03(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cold = smooth(seg(u, 0, 1.2))
    cam = anim.lerp(-10, 10, smooth(u / D))
    t_yet = cue(9) - .1                                                  # "Yet the red kept coming."
    flow = 1.0 + 1.2 * smooth(seg(u, t_yet, t_yet + .4))
    left, right = falls_close(img, u + 5.0, cam, cold=cold, ice_grow=seg(u, .3, 2.2), flow=flow)
    sf.red_fan(img, (left[-1][0] + 80, 1408), (620, 250), seed=8)
    falls_glow(img, left[-1][0] + 100, 1420, u, r=420, a=.2 + .12 * smooth(seg(u, t_yet, t_yet + .3)))
    # cold grade over the world (the falls keep their red: drawn again on top, below)
    m = mask(); m.paste(255, (0, 0, W, H))
    fill_mask(img, m, (40, 80, 160), .18 * cold)
    sf.blood_falls(img, 470, 545, 1400, w=118, t=(u + 5) * 1.6 * flow)
    if u > t_yet:  # the hook: the falls pulse while everything else freezes
        v = u - t_yet; m2 = mask()
        for k in range(2):
            vv = (v - k * .45) % .9
            r = 120 + 520 * ease_out(vv / .9)
            ImageDraw.Draw(m2).ellipse([520 - r * .6, 980 - r, 520 + r * .6, 980 + r], outline=255, width=10)
        glow(img, m2, (255, 90, 70), .55, blur=8, add=True)
    # geologist shivers, arms wrapped round himself; breath puffs
    hug = {'armL': (10, -95, .72), 'armR': (-10, 95, .72), 'legL': (6, 1), 'legR': (-6, -1), '_name': 'think', '_sh': (282, 318)}
    pose = chain(u, [(0, dict(POSES['think'], _name='think', _sh=(278, 322))), (.35, add(STAND, armL=(6, 6), armR=(-6, -6))),
                     (.75, hug, lambda f: out_back(f, 1.4))])
    shiv = 3.5 * math.sin(u * 55) * smooth(seg(u, .6, 1.0))
    g = geologist(img, u, pose, 'worried', 260 + shiv, 1830, .84, look=.3, lean=1.5 * math.sin(u * 2))
    for k in range(3):  # breath puffs every 1.1 s
        v = (u - .8 - k * 1.1)
        if 0 < v < 1.0:
            hx, hy = g['head']; lay = layer(); dd = ImageDraw.Draw(lay)
            for j in range(3):
                q = (18 + 40 * v) * (1 - j * .2); px = hx + 90 + 140 * v + j * 30; py = hy + 30 - 60 * v - j * 10
                dd.ellipse([px - q, py - q * .7, px + q, py + q * .7], fill=(255, 255, 255, int(170 * (1 - v))))
            img.alpha_composite(kit.soft_layer(lay, 5))
    sign(img, 800, 1770, 5.0, 2.0 * math.sin(u * 7) * cold)           # rattles in the wind
    snow_particles(img, 33, n=(90, 40, 14), sizes=(4, 9, 18), wind=(18 + 10 * cold, 1), t=u + 3)
    frost(img, .35 + .65 * smooth(seg(u, .2, 2.6)))
    z = 1.05 + .03 * smooth(u / D) + .08 * out_back(seg(u, t_yet, t_yet + .45), 1.3)
    sx, sy = shake(u, t_yet, 7)
    img = finish(img, u, z, 520, 1000, dx=-cam * 1.05 + sx, dy=sy, vig=(.44, (10, 20, 50)))
    # thermometer + readout (screen space): the column drops to -17 while the digits roll
    k = ease_out(seg(u, cue(1), cue(5) + .3)); deg = int(round(-17 * k))
    yb = anim.lerp(-260, 0, out_back(seg(u, 0, .4), 1.4))
    thermometer(img, 930, 300 + yb, 980 + yb, .12 + .66 * k, deg)
    rl, (rcx, rcy) = _readout(deg)
    anim.scaled_paste(img, rl, 610, 420 + yb * .6, 1.0 + .06 * (1 - seg(u, 1.4, 1.6)) * (u < 1.6) + damp(u - 1.5, .1, 6, 20))
    return img, {'faces': [face_box(g)]}


_ro = {}
def _readout(deg):
    if deg not in _ro:
        txt = f'{deg}°C'.replace('-', '−')
        _ro[deg] = anim.text_layer(lambda l: title(l, [(txt, (150, 220, 255), 150)], 60), W, 320)
    return _ro[deg]


# ---------------------------------------------------------------- s04: explorers' answer + stamp
def speech_bubble(img, cx, cy, r, tail, s, t):
    """Speech bubble with a red algae chain that wiggles + RED ALGAE pill. Pops with scale s."""
    if s <= .01: return
    lay = layer(); d = ImageDraw.Draw(lay)
    rx, ry = r * 1.25, r * .82
    tx, ty = tail
    d.polygon([(cx - 60, cy + ry * .7), (cx + 30, cy + ry * .8), (tx, ty)], fill=INK)
    d.ellipse([cx - rx - 8, cy - ry - 8, cx + rx + 8, cy + ry + 8], fill=INK)
    d.polygon([(cx - 50, cy + ry * .6), (cx + 20, cy + ry * .7), (tx + 6, ty - 14)], fill=(252, 250, 246))
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(252, 250, 246))
    n = 6; rr = 34
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * rr * 1.75; y = cy - 30 + math.sin(i * 1.3 + t * 3) * rr * .7
        col = (200, 50, 60) if i % 2 == 0 else (226, 82, 70)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col, outline=INK, width=5)
        d.ellipse([x - rr * .45, y - rr * .55, x - rr * .02, y - rr * .12], fill=(255, 170, 160))
        if i < n - 1: d.line([(x + rr * .9, y), (x + rr * .85 + 6, y)], fill=INK, width=5)
    pill(lay, 'RED ALGAE', cx, cy + 74, (196, 40, 52), size=50, pad=24)
    bb = (int(cx - rx - 20), int(cy - ry - 20), int(cx + rx + 20), int(max(cy + ry, ty) + 20))
    part = lay.crop(bb); pcx, pcy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    # scale about the tail tip, so it grows out of the speaker
    ox, oy = tx + (pcx - tx) * s, ty + (pcy - ty) * s
    anim.scaled_paste(img, part, ox, oy, s)


def tent(img, x, gy, t):
    d = ImageDraw.Draw(img)
    contact_shadow(img, x + 150, gy, 380, (80, 70, 110), .45)
    d.polygon([(x, gy), (x + 150, gy - 300), (x + 300, gy)], fill=INK)
    d.polygon([(x + 10, gy - 4), (x + 150, gy - 288), (x + 290, gy - 4)], fill=(222, 112, 50))
    d.polygon([(x + 150, gy - 288), (x + 290, gy - 4), (x + 200, gy - 4)], fill=(176, 80, 40))
    d.polygon([(x + 118, gy - 4), (x + 150, gy - 120), (x + 182, gy - 4)], fill=(60, 30, 30))
    radial(img, x + 150, gy - 50, 160, (255, 190, 110), .42 + .1 * math.sin(t * 6) * math.sin(t * 2.3))  # lantern inside flickers
    d.line([(x + 150, gy - 300), (x + 150, gy - 350)], fill=INK, width=6)
    fl = 8 * math.sin(t * 4)                                             # little flag in the wind
    d.polygon([(x + 150, gy - 350), (x + 200, gy - 338 + fl * .3), (x + 150, gy - 322)], fill=(220, 50, 50), outline=INK)
    for k in (-1, 1):
        d.line([(x + 150 + k * 140, gy), (x + 150 + k * 210, gy + 20)], fill=INK, width=3)


def s04(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-14, 14, smooth(u / D))
    backdrop(img, u + 8, cam, [(0, (44, 40, 112)), (.28, (120, 96, 170)), (.5, (250, 170, 140)), (.58, (255, 206, 160))],
             (300, 900, (255, 180, 120)), ((206, 170, 200), (150, 120, 176), (250, 238, 246)),
             ((176, 150, 200), (112, 96, 160), (250, 244, 252)), (255, 214, 196), horizon=1000)
    top = lambda x: 1010 + (x - 560) * .02 + 10 * math.sin(x / 50)
    ice_cliff(img, 560, W + 60, top, lambda x: 1230, seed=19, shade=(130, 160, 214), deep=(70, 96, 160), ink_w=4)
    sf.blood_falls(img, 820, 1020, 1235, w=34, t=u * 1.6)
    falls_glow(img, 860, 1240, u, r=180, a=.18)
    haze(img, 1150, 1260, (255, 220, 214), .4)
    snow_ground(img, lambda x: 1240 + 8 * math.sin(x / 130), color=(248, 244, 250), shade=(200, 196, 226), seed=14)
    tent(img, 30, 1470, u)
    rocks(img, 9, [(980, 1500, 40), (720, 1880, 50), (60, 1900, 60)])
    t_ans = cue(4) - .15; t_ms = cue(9) - .05                                 # "It's" ; "Mystery"
    # three explorers: the leader (middle) anticipates and points at the bubble; the others nod; all hop on the stamp
    hop_all = 22 * math.sin(math.pi * seg(u, t_ms + .05, t_ms + .35)) if t_ms + .05 < u < t_ms + .35 else 0
    point_up = {'armL': (24, 10), 'armR': (-128, -142), 'legL': (11, 1), 'legR': (-11, -1)}
    lead = chain(u, [(0, STAND), (t_ans - .25, add(STAND, armR=(14, 14), legL=(3, -2), legR=(-3, 2))),
                     (t_ans + .12, point_up, lambda f: out_back(f, 1.8))])
    if u > t_ans + .12: lead = add(lead, armR=(3 * math.sin(u * 6), 5 * math.sin(u * 6 - .7)))
    think = dict(POSES['think'], _name='think', _sh=(278, 322))
    right = chain(u, [(0, STAND), (.25, dict(STAND, _name='think', _sh=(300, 300))), (.6, think, lambda f: out_back(f, 1.2))])
    leftp = chain(u, [(0, STAND), (t_ms - .1, STAND), (t_ms + .2, dict(POSES['cheer']), lambda f: out_back(f, 1.6))])
    nod = 10 * abs(math.sin(u * 4.2)) * (seg(u, .3, .6))
    t_tiny = cue(7) - .05
    nod2 = 9 * abs(math.sin((u - t_tiny) * 9)) * (t_tiny < u < t_tiny + .7)
    if t_tiny < u < t_tiny + .6: lead = add(lead, armR=(10 * math.sin((u - t_tiny) * 16), 14 * math.sin((u - t_tiny) * 16 - .6)))  # beats on "Tiny plants"
    gs = []
    gs.append(geologist(img, u, leftp, 'happy', 250, 1810, .7, hop=nod * .6 + hop_all, lean=1.5 * math.sin(u * 1.2), label_on=False, axe=False,
                        color=EXP_ORANGE, bphase=.7, pants='#4a3a3a', rim_dir=(1, -.4)))
    gs.append(geologist(img, u, right, 'smug', 830, 1810, .7, hop=hop_all + nod2, lean=1.5 * math.sin(u * 1.1 + 1), label_on=False, axe=False, color=EXP_ORANGE,
                        bphase=1.4, pants='#3a4a3a', rim_dir=(-1, -.4)))
    gl = geologist(img, u, lead, 'determined' if u < t_ans else 'happy', 540, 1830, .76, hop=hop_all, label_on=False,
                   axe=False, color=EXP_ORANGE, look=.2, lean=2 * smooth(seg(u, t_ans, t_ans + .4)) - 3 * math.sin(math.pi * seg(u, t_ans - .25, t_ans + .05)) + 1.2 * math.sin(u * 1.4))
    gs.append(gl)
    speech_bubble(img, 700, 620, 215, (gl['hands']['R'][0] + 20, gl['hands']['R'][1] - 30), pop(u, t_ans, .32, 1.8), u)
    hx, hy = gl['head']; label(img, 'EXPLORERS', hx - 90, hy - gl['R'] * 1.32 - 88, EXP_ORANGE, size=50)   # on top of the tail
    fx = cam * -.6
    foreground_frame(img, [[(860 + fx, 1940), (950 + fx, 1850), (1100 + fx, 1830), (1100 + fx, 1940)]], color=(150, 140, 190), alpha=.85)
    snow_particles(img, 41, n=(60, 26, 8), wind=(5, 1), t=u)
    sx, sy = shake(u, t_ms + .08, 12)
    img = finish(img, u, 1.05 + .04 * smooth(u / D), 560, 1200, dx=-cam * 1.05 + sx, dy=sy, vig=(.38, (30, 16, 50)))
    draw_stamp(img, u, t_ms + .02)
    return img, {'faces': [face_box(g) for g in gs]}


# ---------------------------------------------------------------- s05 / s06: the lab
def lab_room(img, t, cam, shelf_bottles=True):
    """Grey lab: tiles, a cold window (snow drifts past), shelves with glowing samples (bubbles rise), warm
    lamp cone with dust motes; the lamp sways 1 deg."""
    img.paste(vgrad([(0, (30, 42, 56)), (.45, (70, 92, 104)), (.75, (96, 116, 122)), (1, (60, 74, 84))]))
    d = ImageDraw.Draw(img); ox = cam * .25
    for y in range(80, 1460, 90): d.line([(0, y), (W, y)], fill=(84, 104, 116), width=2)
    for x in range(-120, W + 120, 120):
        for y in range(80, 1460, 180): d.line([(x + ox + (y // 90 % 2) * 60, y), (x + ox + (y // 90 % 2) * 60, y + 90)], fill=(84, 104, 116), width=2)
    wx0, wy0, wx1, wy1 = int(60 + ox), 520, int(330 + ox), 900
    d.rounded_rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14], 18, fill=(46, 56, 66), outline=INK, width=6)
    win = vgrad([(0, (24, 40, 96)), (1, (110, 140, 210))], wx1 - wx0, wy1 - wy0)
    peak_range(win, 5, 330, 60, 150, (190, 200, 235), (130, 140, 200), (250, 250, 255), n=4, x_shift=cam * .5)
    ImageDraw.Draw(win).rectangle([0, 320, wx1 - wx0, wy1 - wy0], fill=(226, 234, 250))
    snow_particles(win, 3, n=(30, 10, 0), sizes=(4, 8, 1), t=t)
    img.paste(win, (wx0, wy0))
    light_rays(img, (wx0 + wx1) / 2, (wy0 + wy1) / 2, (150, 190, 255), n=5, alpha=.12 + .03 * math.sin(t * 1.3), spread=(10, 70), length=1100, seed=5)
    d = ImageDraw.Draw(img)
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(46, 56, 66), width=12)
    d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(46, 56, 66), width=12)
    d.rounded_rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14], 18, outline=INK, width=6)
    if shelf_bottles:
        for sy in (760, 1080):
            d.rectangle([700 + ox, sy, W + 30, sy + 26], fill=(150, 120, 96), outline=INK, width=5)
            d.rectangle([700 + ox, sy + 26, W + 30, sy + 40], fill=(40, 34, 40))
        for x, sy, h, c, k in ((760, 760, 150, (220, 50, 50), 'round'), (870, 760, 170, (70, 190, 120), 'bottle'),
                               (990, 760, 140, (90, 150, 240), 'round'), (770, 1080, 160, (240, 160, 60), 'bottle'),
                               (880, 1080, 120, (220, 50, 50), 'tube'), (940, 1080, 120, (220, 60, 60), 'tube')):
            props.flask(img, x + ox, sy, h, c, k)
            bubbles(img, x + ox, sy - 14, h * .45, t, seed=int(x))
    sway = math.sin(t * 1.4) * 14
    beam = mask(); ImageDraw.Draw(beam).polygon([(150 + sway * .2, 140), (310 + sway * .2, 140), (760 + sway, 1480), (-60 + sway, 1480)], fill=255)
    glow(img, beam, (255, 226, 170), .3 + .03 * math.sin(t * 2.1), blur=40, add=True)
    radial(img, 360 + sway, 1450, 520, (255, 214, 150), .35)
    dust(img, 4, 44, (160, 300, 820, 1440), (255, 240, 200), 170, t=t)
    d = ImageDraw.Draw(img)
    d.line([(230, 0), (230 + sway * .1, 80)], fill=INK, width=8)
    d.chord([120 + sway * .15, 60, 340 + sway * .15, 210], 180, 360, fill=(60, 120, 110), outline=INK, width=6)
    d.ellipse([200 + sway * .15, 118, 260 + sway * .15, 148], fill=(255, 248, 220))


def bubbles(img, x, base, h, t, seed=0, n=4, color=(255, 255, 255)):
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    for i in range(n):
        ph = rng.uniform(0, 1); sp = rng.uniform(.5, .9); u = (ph + t * sp) % 1
        bx = x + rng.uniform(-12, 12) + 4 * math.sin(t * 5 + i); by = base - h * u; q = rng.uniform(3, 6)
        d.ellipse([bx - q, by - q, bx + q, by + q], outline=color, width=2)


def bench(img, cam):
    d = ImageDraw.Draw(img)
    d.polygon([(-10, 1470), (W + 10, 1470), (W + 10, 1530), (-10, 1530)], fill=(196, 206, 206), outline=INK, width=6)
    d.rectangle([-10, 1530, W + 10, H], fill=(74, 84, 98))
    d.line([(-10, 1536), (W + 10, 1536)], fill=(40, 46, 56), width=10)
    for x in (60, 420, 780):
        d.rounded_rectangle([x, 1600, x + 300, 1800], 14, fill=(84, 96, 110), outline=INK, width=5)
        d.rounded_rectangle([x + 110, 1640, x + 190, 1662], 10, fill=(196, 206, 214), outline=INK, width=4)


def lens_view(r, t, x_prog, show_algae=True):
    """Magnified water: salt cubes + iron specks drift (Brownian), the ghost algae chain, and the red X
    drawn on stroke by stroke (x_prog 0..2)."""
    view = vgrad([(0, (255, 236, 230)), (1, (246, 196, 186))], 2 * r, 2 * r)
    vd = ImageDraw.Draw(view); rng = np.random.default_rng(3)
    for i in range(9):
        x, y, q = rng.uniform(40, 2 * r - 60), rng.uniform(40, 2 * r - 60), rng.uniform(16, 30)
        x += 8 * math.sin(t * .9 + i); y += 6 * math.cos(t * .7 + 2 * i)
        vd.polygon([(x, y), (x + q, y - q * .4), (x + 2 * q, y), (x + q, y + q * .4)], fill=(255, 255, 255), outline=INK, width=3)
        vd.polygon([(x, y), (x + q, y + q * .4), (x + q, y + q * 1.3), (x, y + q * .9)], fill=(214, 220, 236), outline=INK, width=3)
        vd.polygon([(x + q, y + q * .4), (x + 2 * q, y), (x + 2 * q, y + q * .9), (x + q, y + q * 1.3)], fill=(180, 190, 214), outline=INK, width=3)
    for i in range(26):
        x, y, q = rng.uniform(20, 2 * r - 20), rng.uniform(20, 2 * r - 20), rng.uniform(5, 11)
        x += 10 * math.sin(t * 1.3 + i * 1.7); y += 10 * math.cos(t * 1.1 + i)
        vd.ellipse([x - q, y - q, x + q, y + q], fill=(196, 86, 44), outline=(110, 40, 20), width=2)
    if show_algae: props.algae_chain(view, r, r + 6 * math.sin(t * 2), 1.5, color=(40, 150, 70), dashed=True)
    rr = 84; w = 32
    for k, (a, b) in enumerate((((r - rr, r - rr), (r + rr, r + rr)), ((r + rr, r - rr), (r - rr, r + rr)))):
        f = smooth(x_prog - k)
        if f <= 0: continue
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        vd.line([a, e], fill=INK, width=w + 12)
        vd.line([a, e], fill=(230, 40, 44), width=w)
        for p in (a, e): vd.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=(230, 40, 44))
    return view


def s05(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(10, -10, smooth(u / D))
    lab_room(img, u, cam)
    t_test = cue(4) - .2                                                      # "tested"
    t_no = cue(9) - .1                                                       # "no (algae)"
    # scientist: looks at the scope (thinking), anticipates, then points at the view; recoils on the X
    point_up = {'armL': (24, 10), 'armR': (-128, -142), 'legL': (10, 1), 'legR': (-10, -1)}
    pose = chain(u, [(0, dict(POSES['think'], _name='think', _sh=(278, 322))),
                     (t_test - .35, dict(STAND, _name='think', _sh=(300, 300))),
                     (t_test - .1, add(STAND, armR=(14, 14), legL=(3, -2), legR=(-3, 2))),
                     (t_test + .3, point_up, lambda f: out_back(f, 1.9))])
    if u > t_test + .3: pose = add(pose, armR=(2.5 * math.sin(u * 5), 4 * math.sin(u * 5 - .6)))
    recoil = -2.5 * out_back(seg(u, t_no + .1, t_no + .45), 1.6) if u > t_no else 0
    expr = 'thinking' if u < t_test - .1 else ('surprised' if u > t_no + .1 else ('worried' if u > t_no - .1 else 'determined'))
    flinch = 16 * math.sin(math.pi * seg(u, .55, .8)) if .55 < u < .8 else 0       # flinches as the stamp cracks
    g = scientist(img, u, pose, expr, 275, 1900, 1.22, look=.3 if u < t_test else 0, lean=recoil - .12 * flinch, hop=flinch)
    bench(img, cam)
    ex, ey = props.microscope(img, 950, 1478, 1.0)
    props.flask(img, 640, 1474, 84, BLOOD, 'bottle', glow_on=False)
    bubbles(img, 640, 1460, 30, u, seed=4, n=2)
    # magnified view zooms out of the eyepiece (scale 0 -> 1, overshoot), then the X draws on, then NO ALGAE pops
    cx, cy, r = 800, 680, 218
    s = pop(u, t_test, .45, 1.5)
    if s > .01:
        lx, ly = ex + (cx - ex) * min(1, s), ey + (cy - ey) * min(1, s)
        cone = mask(); ImageDraw.Draw(cone).polygon([(ex - 30, ey), (ex + 30, ey), (lx + r * s * .9, ly + r * s * .4), (lx - r * s * .9, ly + r * s * .4)], fill=255)
        fill_mask(img, cone, (220, 250, 255), .18, blur=6)
        lay = layer(2 * r + 120, 2 * r + 120); c0 = r + 60
        m = mask(2 * r + 120, 2 * r + 120); ImageDraw.Draw(m).ellipse([c0 - r - 20, c0 - r - 20, c0 + r + 20, c0 + r + 20], fill=255)
        glow(lay, m, (255, 120, 100), .5 + .1 * math.sin(u * 3), blur=30)
        view = lens_view(r, u, seg(u, t_no - .05, t_no + .45) * 2)
        cm = mask(2 * r, 2 * r); ImageDraw.Draw(cm).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
        lay.paste(view, (c0 - r, c0 - r), cm)
        dl = ImageDraw.Draw(lay)
        dl.ellipse([c0 - r - 24, c0 - r - 24, c0 + r + 24, c0 + r + 24], outline=INK, width=34)
        dl.ellipse([c0 - r - 18, c0 - r - 18, c0 + r + 18, c0 + r + 18], outline=(120, 140, 152), width=22)
        dl.arc([c0 - r - 14, c0 - r - 14, c0 + r + 14, c0 + r + 14], 200, 290, fill=(220, 232, 240), width=10)
        dl.arc([c0 - r + 30, c0 - r + 30, c0 + r - 30, c0 + r - 30], 205, 245, fill=(255, 255, 255), width=10)
        anim.scaled_paste(img, lay, lx, ly, s)
    ps = pop(u, t_no + .48, .3, 1.8)
    if ps > .01:
        pl, (pcx, pcy) = _no_algae()
        anim.scaled_paste(img, pl, cx + 10, cy - r - 12, ps)
    snow_particles(img, 51, n=(0, 0, 6), sizes=(1, 1, 14), alpha=(0, 0, 70), wind=(2, 1), t=u)
    if t_no + .4 < u < t_no + .7:                                               # impact flash as the X completes
        radial(img, 800, 680, 300, (255, 240, 230), .6 * (1 - seg(u, t_no + .4, t_no + .7)))
    sx, sy = shake(u, t_no + .4, 6)
    sx2, sy2 = shake(u, 0.55, 12, seed=2)
    img = finish(img, u, 1.04 + .05 * smooth(u / D), 760, 900, dx=-cam * 1.05 + sx + sx2, dy=sy + sy2, vig=(.42, (10, 12, 24)))
    draw_stamp(img, u + 10, -100, t_crack=10.55)                              # from s04: cracks at 0.55 s
    return img, {'faces': [face_box(g)]}


_na = {}
def _no_algae():
    if 'p' not in _na:
        def f(l):
            pill(l, '    NO ALGAE', 540, 100, (220, 36, 44), size=64)
            props.big_x(l, 540 - 174, 102, 20, color=(255, 255, 255), w=12)
        _na['p'] = anim.text_layer(f, W, 220)
    return _na['p']


def test_tube(img, x, y, h, t, glow_k=1.0, ang=0.0):
    """Hand-held test tube of Blood Falls water: red, glowing, the surface sloshes, iron specks swirl."""
    w = 56; lay = layer(200, int(h + 120)); d = ImageDraw.Draw(lay); cx = 100; top = 40
    m = mask(200, int(h + 120)); ImageDraw.Draw(m).rounded_rectangle([cx - w / 2, top, cx + w / 2, top + h], w / 2, fill=255)
    glow(lay, m, (255, 70, 50), .55 * glow_k, blur=26)
    d.rounded_rectangle([cx - w / 2 - 5, top - 5, cx + w / 2 + 5, top + h + 5], w / 2 + 5, fill=INK)
    d.rounded_rectangle([cx - w / 2, top, cx + w / 2, top + h], w / 2, fill=(226, 238, 246))
    lv = top + h * .3
    surf = [(cx - w / 2 + 3 + i * (w - 6) / 8, lv + 6 * math.sin(t * 6 + i * .8)) for i in range(9)]
    d.polygon(surf + [(cx + w / 2 - 3, top + h - 20), (cx, top + h - 3), (cx - w / 2 + 3, top + h - 20)], fill=(200, 34, 40))
    d.rounded_rectangle([cx - w / 2 + 3, lv + 30, cx + w / 2 - 3, top + h - 3], w / 2 - 3, fill=(200, 34, 40))
    rng = np.random.default_rng(2)
    for i in range(10):
        a = t * 2.4 + i * .63; px = cx + (w / 2 - 12) * math.sin(a + i); py = lv + 20 + (h * .66 - 30) * ((i / 10 + t * .15) % 1)
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 140, 80))
    d.line([(cx - w / 2 + 12, top + 16), (cx - w / 2 + 12, top + h - 30)], fill='white', width=6)
    d.rounded_rectangle([cx - w / 2 - 12, top - 14, cx + w / 2 + 12, top + 4], 6, fill=(196, 206, 214), outline=INK, width=4)
    if ang: lay = lay.rotate(ang, resample=Image.BICUBIC, center=(cx, top + h))
    img.alpha_composite(lay, (int(x - cx), int(y - top - h)))


def meter(img, x, y, k_sea, k_this, show):
    """SALT meter: SEA bar vs. THIS WATER bar (grows past the sea with overshoot)."""
    if show <= .01: return
    lay = layer(520, 330); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([10, 10, 510, 320], 34, fill=INK)
    d.rounded_rectangle([4, 4, 504, 312], 34, fill=(26, 36, 52), outline=(240, 240, 240), width=5)
    # salt cube icon + SALT
    q = 30; sx, sy = 54, 62
    d.polygon([(sx, sy), (sx + q, sy - q * .4), (sx + 2 * q, sy), (sx + q, sy + q * .4)], fill=(255, 255, 255), outline=INK, width=3)
    d.polygon([(sx, sy), (sx + q, sy + q * .4), (sx + q, sy + q * 1.3), (sx, sy + q * .9)], fill=(214, 220, 236), outline=INK, width=3)
    d.polygon([(sx + q, sy + q * .4), (sx + 2 * q, sy), (sx + 2 * q, sy + q * .9), (sx + q, sy + q * 1.3)], fill=(180, 190, 214), outline=INK, width=3)
    d.text((136, 70), 'SALT', font=font(64), fill='white', anchor='lm')
    for i, (name, k, col) in enumerate((('SEA', k_sea, (70, 140, 230)), ('THIS WATER', k_this, (226, 52, 44)))):
        yy = 150 + i * 86
        d.text((30, yy), name, font=font(30, True), fill=(200, 210, 224), anchor='lm')
        d.rounded_rectangle([30, yy + 20, 480, yy + 56], 18, fill=(50, 60, 80))
        if k > .02: d.rounded_rectangle([30, yy + 20, 30 + 450 * min(1.06, k), yy + 56], 18, fill=col, outline=INK, width=3)
    anim.scaled_paste(img, lay, x, y, show)


def fe_tile(img, x, y, s, t):
    if s <= .01: return
    lay = layer(300, 330); d = ImageDraw.Draw(lay)
    m = mask(300, 330); ImageDraw.Draw(m).rounded_rectangle([30, 30, 270, 300], 30, fill=255)
    glow(lay, m, (255, 140, 60), .5 + .12 * math.sin(t * 4), blur=22)
    d.rounded_rectangle([36, 38, 270, 306], 30, fill=INK)
    d.rounded_rectangle([30, 30, 264, 298], 30, fill=(214, 110, 52), outline=INK, width=6)
    d.text((54, 66), '26', font=font(34, True), fill=(255, 226, 200), anchor='lm')
    d.text((147, 160), 'Fe', font=font(120), fill='white', anchor='mm', stroke_width=5, stroke_fill=INK)
    d.text((147, 254), 'IRON', font=font(44), fill=(255, 236, 220), anchor='mm')
    anim.scaled_paste(img, lay, x, y, s, angle=4 * math.sin(t * 1.5) * 0)


def s06(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-12, 12, smooth(u / D))
    lab_room(img, u + 4, cam)
    t_salt = cue(3) - .1; t_sea = cue(4) - .05; t_iron = cue(11) - .1    # "salt," ; "saltier" ; "iron."
    # scientist raises the tube with anticipation and studies it
    hold = {'armL': (24, 10), 'armR': (-34, -112, .95, .9), 'legL': (10, 1), 'legR': (-10, -1)}
    pose = chain(u, [(0, add(STAND, armR=(-8, -20))), (.12, add(STAND, armR=(10, 12))),
                     (.5, hold, lambda f: out_back(f, 1.7))])
    if u > .5: pose = add(pose, armR=(2 * math.sin(u * 3), 3 * math.sin(u * 3 - .6)))
    shake_hand = 6 * damp(u - t_iron, 1, 5, 20)
    expr = 'thinking' if u < t_salt else ('surprised' if u > t_iron else 'determined')
    g = scientist(img, u, pose, expr, 300, 1900, 1.2, look=.45, lean=1.5 * math.sin(u * 1.6))
    hx, hy, _ = g['hands']['R']
    test_tube(img, hx + 4 + shake_hand, hy - 6, 260, u, 1 + .3 * smooth(seg(u, t_iron, t_iron + .3)), ang=-6 + 3 * math.sin(u * 1.6))
    # redraw the fist over the tube (seamless with the forearm)
    r = stickman.T / 2 * g['scale']; d = ImageDraw.Draw(img)
    d.ellipse([hx - r - 4 + shake_hand, hy - r - 4, hx + r + 4 + shake_hand, hy + r + 4], fill=INK)
    d.ellipse([hx - r + shake_hand, hy - r, hx + r + shake_hand, hy + r], fill=(246, 246, 242))
    bench(img, cam)
    props.flask(img, 120, 1474, 110, (90, 150, 240), 'round'); bubbles(img, 120, 1440, 50, u, seed=9)
    props.flask(img, 960, 1474, 96, (70, 190, 120), 'bottle')
    # UI: salt meter (SEA vs THIS WATER), then the Fe tile; iron specks fly from the tube into it
    ms = pop(u, t_salt, .3, 1.8)
    k_sea = .38 * ease_out(seg(u, t_salt + .1, t_salt + .4))
    k_this = out_back(seg(u, t_sea, t_sea + .5), 1.5) * .98
    meter(img, 730, 660, k_sea, k_this, ms * 1.15)
    fs = pop(u, t_iron, .3, 2.0)
    fe_tile(img, 800, 1110, fs, u)
    if u > t_iron - .2:
        rng = np.random.default_rng(5); d = ImageDraw.Draw(img)
        for i in range(12):
            v = (u - t_iron + .2 - i * .05)
            if not 0 < v < .6: continue
            f = ease_in(v / .6); sx0, sy0 = hx + 10, hy - 140; ex, ey = 800, 1110
            px = sx0 + (ex - sx0) * f; py = sy0 + (ey - sy0) * f - 160 * math.sin(math.pi * f) + rng.uniform(-30, 30)
            d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=(240, 120, 60), outline=INK, width=2)
    img = finish(img, u, 1.05 + .04 * smooth(u / D), 520, 1000, dx=-cam * 1.05, vig=(.42, (10, 12, 24)))
    # CLUE 1 badge slams in
    s = slam(u, .05, .26, 1.3)
    if s > 0:
        bl, (bx, by) = _clue_badge('CLUE 1')
        anim.scaled_paste(img, bl, 540, 250, s, angle=-3)
    return img, {'faces': [face_box(g)]}


_cb = {}
def _clue_badge(txt):
    if txt not in _cb:
        def f(l):
            d = ImageDraw.Draw(l); fnt = font(120); w = kit.text_w(txt, fnt)
            x0, x1 = 540 - w / 2 - 140, 540 + w / 2 + 60
            d.rounded_rectangle([x0 + 8, 40 + 12, x1 + 8, 230 + 12], 50, fill=(10, 6, 20))
            d.rounded_rectangle([x0, 40, x1, 230], 50, fill=(255, 196, 40), outline=(40, 18, 44), width=10)
            # magnifier icon
            mx, my = x0 + 90, 128
            d.ellipse([mx - 46, my - 46, mx + 34, my + 34], outline=(40, 18, 44), width=16)
            d.line([(mx + 26, my + 26), (mx + 60, my + 62)], fill=(40, 18, 44), width=20)
            d.text((x0 + 170, 136), txt, font=fnt, fill=(40, 18, 44), anchor='lm')
        _cb[txt] = anim.text_layer(f, W, 300)
    return _cb[txt]


SHOTS = {'s01': s01, 's02': s02, 's03': s03, 's04': s04, 's05': s05, 's06': s06}
SLUG = 'blood-falls'

from blood_falls_2 import *  # noqa: E402,F401,F403  (s07-s16, SHOT_LIST, END)

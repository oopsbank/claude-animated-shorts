"""Blood Falls shots s07-s16 (v4 full video), same contract as blood_falls.py: `sNN(u, D, cue)` -> (img, info).

u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the shot's voice-over LINE (split
shots like s11b keep the line's word indexes). info: 'faces' (face boxes; render.py adds body boxes) and
'avoid' (boxes the caption must not cover, e.g. the brine pool).

Every shot keeps moving in its holds: particles, glow pulses, flowing dashes, a slow camera push/pan, and
characters with breathing, blinks and `anim.secondary` (head leads, shoulder rise, hand beats on speech).
"""
import math
import numpy as np
from PIL import Image, ImageDraw
import kit, props, anim
from kit import (W, H, INK, vgrad, radial, light_rays, cloud_bands, haze, peak_range, ice_cliff, snow_ground,
                 rocks, snow_particles, dust, contact_shadow, label, title, pill, font, mask, glow, fill_mask,
                 layer, lerp, rgb, foreground_frame)
from anim import smooth, ease_out, ease_in, out_back, seg, mix, add, chain, damp, slam, pop, shake, STAND, POSES
import style_frames as sf
import blood_falls as B
from blood_falls import (geologist, scientist, backdrop, falls_glow, mist, finish, slam_title, face_box, lab_room,
                         bench, bubbles, _clue_badge, speech_bubble, SCI_GREEN, BLOOD)

TEAL = (60, 230, 200)
RUST = (214, 92, 34)


# ---------------------------------------------------------------- shared pieces
def clue(img, txt, u, t0=.05, y=250):
    s = slam(u, t0, .26, 1.3)
    if s > 0:
        bl, _ = _clue_badge(txt); anim.scaled_paste(img, bl, 540, y, s, angle=-3)


def draw_x(img, cx, cy, r, prog, w=26, color=(230, 40, 44)):
    """A red X drawn on stroke by stroke (prog 0..2)."""
    d = ImageDraw.Draw(img)
    for k, (a, b) in enumerate((((cx - r, cy - r), (cx + r, cy + r)), ((cx + r, cy - r), (cx - r, cy + r)))):
        f = smooth(prog - k)
        if f <= 0: continue
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, e], fill=INK, width=w + 12); d.line([a, e], fill=color, width=w)
        for p in (a, e): d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=color)


def o2(d, x, y, q, fill=(150, 210, 255), ink=(20, 60, 120)):
    d.ellipse([x - q - 3, y - q - 3, x + q + 3, y + q + 3], fill=(255, 255, 255))
    d.ellipse([x - q, y - q, x + q, y + q], fill=fill, outline=INK, width=max(3, int(q * .11)))
    d.arc([x - q * .7, y - q * .7, x + q * .2, y + q * .2], 190, 260, fill='white', width=max(2, int(q * .08)))
    d.text((x - q * .12, y + 2), 'O', font=font(int(q * .95), True), fill=ink, anchor='mm')
    d.text((x + q * .4, y + q * .32), '2', font=font(int(q * .5), True), fill=ink, anchor='mm')


def microbe(img, x, y, r, t, seed, k_glow=1.0, col=(120, 240, 170), breathe=0.0):
    """A glowing rod-shaped microbe: capsule body, inner granules, a wiggling flagellum. breathe 0..1 swells it."""
    rng = np.random.default_rng(seed)
    a = rng.uniform(0, 2 * math.pi) + .4 * math.sin(t * 1.3 + seed)
    r = r * (1 + .14 * breathe * math.sin(t * 7 + seed))
    L = r * 1.5; ca, sa = math.cos(a), math.sin(a)
    p0 = (x - ca * L / 2, y - sa * L / 2); p1 = (x + ca * L / 2, y + sa * L / 2)
    m = mask(); md = ImageDraw.Draw(m); md.line([p0, p1], fill=255, width=int(r * 2.6))
    glow(img, m, col, .55 * k_glow, blur=int(r * 1.2) + 4, add=True)
    d = ImageDraw.Draw(img)
    tail = []
    for i in range(9):
        s_ = i / 8; tx = p0[0] - ca * s_ * L * 1.3 + -sa * r * .5 * math.sin(t * 10 + i * .9 + seed)
        ty = p0[1] - sa * s_ * L * 1.3 + ca * r * .5 * math.sin(t * 10 + i * .9 + seed)
        tail.append((tx, ty))
    d.line(tail, fill=INK, width=max(3, int(r * .22)) + 3, joint='curve')
    d.line(tail, fill=col, width=max(2, int(r * .22)), joint='curve')
    d.line([p0, p1], fill=INK, width=int(r * 2) + 8)
    for p in (p0, p1): d.ellipse([p[0] - r - 4, p[1] - r - 4, p[0] + r + 4, p[1] + r + 4], fill=INK)
    d.line([p0, p1], fill=col, width=int(r * 2))
    for p in (p0, p1): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    hi = lerp(rgb(col), (255, 255, 255), .55)
    d.line([(p0[0] - sa * r * .45, p0[1] + ca * r * .45 - r * .3), (p1[0] - sa * r * .45, p1[1] + ca * r * .45 - r * .3)], fill=hi, width=max(2, int(r * .35)))
    for i in range(3):
        f = (i + 1) / 4; gx, gy = p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f
        q = r * .28; d.ellipse([gx - q, gy - q, gx + q, gy + q], fill=lerp(rgb(col), (20, 60, 50), .45))


def chip(txt, fill, size=56, icon=None):
    """Cached UI pill layer."""
    k = ('chip', txt, fill, size)
    if k not in _cache:
        def f(l):
            pill(l, txt, 540, 110, fill, size=size, pad=28)
        _cache[k] = anim.text_layer(f, W, 240)
    return _cache[k]
_cache = {}


def put_chip(img, txt, fill, x, y, s, size=56, angle=0.0):
    if s > .01:
        lay, _ = chip(txt, fill, size); anim.scaled_paste(img, lay, x, y, s, angle)


def tile(img, sym, name, x, y, s, t, col=(214, 110, 52), num=''):
    """Element tile (Fe / S), glowing, pops with scale s."""
    if s <= .01: return
    lay = layer(300, 330); d = ImageDraw.Draw(lay)
    m = mask(300, 330); ImageDraw.Draw(m).rounded_rectangle([30, 30, 270, 300], 30, fill=255)
    glow(lay, m, lerp(rgb(col), (255, 255, 255), .2), .5 + .12 * math.sin(t * 4), blur=22)
    d.rounded_rectangle([36, 38, 270, 306], 30, fill=INK)
    d.rounded_rectangle([30, 30, 264, 298], 30, fill=col, outline=INK, width=6)
    if num: d.text((54, 66), num, font=font(34, True), fill=(255, 240, 220), anchor='lm')
    d.text((147, 160), sym, font=font(120), fill='white', anchor='mm', stroke_width=5, stroke_fill=INK)
    d.text((147, 254), name, font=font(44), fill=(255, 246, 230), anchor='mm')
    anim.scaled_paste(img, lay, x, y, s * .8, angle=3 * math.sin(t * 1.7))


def path_point(pts, f):
    """Point at fraction f (0..1) along a polyline."""
    L = [math.dist(a, b) for a, b in zip(pts, pts[1:])]; tot = sum(L); s = f * tot
    for (a, b), l in zip(zip(pts, pts[1:]), L):
        if s <= l: k = s / l if l else 0; return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        s -= l
    return pts[-1]


def partial(pts, f):
    """The first fraction f of a polyline (for things that draw on / spread)."""
    if f <= 0: return [pts[0], pts[0]]
    L = [math.dist(a, b) for a, b in zip(pts, pts[1:])]; tot = sum(L); s = f * tot; out = [pts[0]]
    for (a, b), l in zip(zip(pts, pts[1:]), L):
        if s >= l: out.append(b); s -= l
        else:
            k = s / l if l else 0; out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)); break
    return out


def stars(img, seed, n, y1, t, box=(0, W)):
    d = ImageDraw.Draw(img); rng = np.random.default_rng(seed)
    for i in range(n):
        x, y, q = rng.uniform(*box), rng.uniform(0, y1), rng.uniform(1.5, 3.6)
        q *= .75 + .25 * math.sin(t * rng.uniform(2, 5) + i)        # twinkle
        d.ellipse([x - q, y - q, x + q, y + q], fill=(220, 230, 255))


# ---------------------------------------------------------------- s07: "So if plants aren't making it red, what is?"
def s07(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-10, 10, smooth(u / D))
    lab_room(img, u + 7, cam)
    dark = smooth(seg(u, .2, D))                                          # the room darkens toward the question
    m = mask(); m.paste(255, (0, 0, W, H)); fill_mask(img, m, (8, 10, 30), .5 * dark)
    radial(img, 330, 1300, 620, (255, 214, 150), .22 + .1 * dark)         # a spotlight stays on the scientist
    bench(img, cam)
    t_pl, t_what = cue(2) - .1, cue(7) - .08                               # "plants" ; "what"
    # scientist: from the tube hold (s06) -> scratches his head (staged), then looks up at the "?"
    scratch = dict(STAND, armR=(-150, 200), armL=(30, 14))
    pose = chain(u, [(0, add(STAND, armR=(-34, -112))), (.25, add(STAND, armR=(-100, -175))), (.55, scratch, lambda f: out_back(f, 1.6))])
    if u > .55: pose = add(pose, armR=(0, 13 * math.sin((u - .55) * 17)))  # the scratch itself
    look = .35 + .3 * out_back(seg(u, t_what - .2, t_what + .2))
    expr = 'thinking' if u < t_what - .1 else 'worried'
    g = scientist(img, u, pose, expr, 300, 1900, 1.2, look=look, lean=-2 * smooth(seg(u, t_what - .2, t_what + .3)))
    # "plants aren't making it red": a plant badge with the algae chain, crossed out
    s = pop(u, t_pl, .3, 1.8)
    if s > .01:
        lay = layer(420, 420); d = ImageDraw.Draw(lay)
        d.ellipse([20, 20, 400, 400], fill=(236, 246, 236), outline=INK, width=10)
        props.algae_chain(lay, 210, 210, 1.3, color=(196, 50, 60))
        draw_x(lay, 210, 210, 120, seg(u, cue(3) - .1, cue(5)) * 2, w=24)
        anim.scaled_paste(img, lay, 720, 600, s * .8, angle=6 * math.sin(u * 2))
    # the big red "?" slams in on "what is?"; it wobbles and glows
    q = slam(u, t_what, .3, 1.5)
    if q > 0:
        lay = layer(520, 700); d = ImageDraw.Draw(lay)
        d.text((266, 366), '?', font=font(560), fill=(20, 6, 10), anchor='mm')
        d.text((260, 350), '?', font=font(560), fill=(232, 44, 48), anchor='mm', stroke_width=14, stroke_fill=INK)
        radial(img, 790, 1060, 420, (255, 60, 50), .45 * smooth(seg(u, t_what, t_what + .3)))
        anim.scaled_paste(img, lay, 790, 1060, q * .8, angle=damp(u - t_what, 9, 4, 12) + 3 * math.sin(u * 3))
    for k in range(3):                                                    # little "?"s float off his head
        v = u - .6 - k * .35
        if 0 < v < 1.2:
            hx, hy = g['head']; d = ImageDraw.Draw(img)
            d.text((hx + 60 + k * 50, hy - 150 - 120 * v), '?', font=font(int(70 - 10 * k)), fill=(255, 220, 90), anchor='mm', stroke_width=5, stroke_fill=INK)
    sx, sy = shake(u, t_what + .05, 8)
    img = finish(img, u, 1.05 + .05 * smooth(u / D), 520, 1100, dx=-cam * 1.05 + sx, dy=sy, vig=(.42 + .2 * dark, (6, 6, 20)))
    return img, {'faces': [face_box(g)]}


# ---------------------------------------------------------------- s08: CLUE 2, life without sun or oxygen
MICROBES = [(-210, -80, 34), (40, -200, 30), (230, -40, 36), (-60, 60, 40), (150, 170, 32), (-230, 190, 28),
            (-10, 300, 30), (260, 300, 26), (-280, -250, 24), (120, -330, 26), (330, 120, 24), (-120, -360, 22)]


def droplet(img, cx, cy, r, t, s):
    """Magnified drop of the brine: teardrop with dark teal water, caustic ripples and a rim highlight."""
    if s <= .01: return None
    R = r * s
    pts = []
    for i in range(72):
        a = 2 * math.pi * i / 72; k = 1 + .55 * max(0, -math.sin(a)) ** 6       # pointed top
        pts.append((cx + R * math.cos(a) * (1 - .25 * max(0, -math.sin(a)) ** 3), cy + R * math.sin(a) * k))
    m = mask(); ImageDraw.Draw(m).polygon(pts, fill=255)
    glow(img, m, (80, 230, 210), .55 + .08 * math.sin(t * 2), blur=50, add=True)
    water = vgrad([(0, (40, 96, 108)), (.5, (18, 56, 72)), (1, (10, 30, 46))], W, H)
    wd = ImageDraw.Draw(water)
    for k in range(9):                                                    # caustic ripples drift
        y0 = cy - R + k * R * .24 + 18 * math.sin(t * .8 + k)
        wd.line([(x, y0 + 14 * math.sin(x / 60 + t * 1.6 + k)) for x in range(int(cx - R), int(cx + R), 12)], fill=(70, 140, 150), width=4)
    img.paste(water, (0, 0), m)
    return pts


def s08(u, D, cue):
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (8, 18, 40)), (.5, (16, 40, 66)), (1, (6, 14, 30))]))
    radial(img, 540, 820, 900, (40, 120, 140), .35)
    dust(img, 12, 50, (0, 0, W, H), (150, 220, 230), 110, size=(2, 6), t=u)
    cx, cy, r = 540, 840, 360
    t_alive, t_mic = cue(5) - .1, cue(7) - .1
    t_sun, t_o2 = cue(9) - .05, cue(11) - .05
    t_br, t_fe, t_s = cue(13) - .1, cue(14) - .1, cue(16) - .1
    pts = droplet(img, cx, cy, r, u, pop(u, .15, .5, 1.4))
    if pts:
        # microbes pop in on "alive with microbes", drift, wiggle; they swell and glow when they "breathe"
        br = smooth(seg(u, t_br, t_br + .4))
        for i, (mx, my, mr) in enumerate(MICROBES):
            s = pop(u, t_alive + i * .07, .3, 2.0)
            if s <= .01: continue
            x = cx + mx + 14 * math.sin(u * .9 + i); y = cy + my + 12 * math.cos(u * .8 + 2 * i)
            col = [(120, 240, 170), (110, 220, 250), (250, 200, 110)][i % 3]
            microbe(img, x, y, mr * min(s, 1.15), u, 40 + i, 1 + .6 * br, col, breathe=br)
        d = ImageDraw.Draw(img)
        d.line(pts + [pts[0]], fill=INK, width=12)
        d.line(pts + [pts[0]], fill=(150, 240, 236), width=5)
        d.arc([cx - r * .8, cy - r * .7, cx + r * .2, cy + r * .3], 200, 250, fill=(230, 255, 255), width=12)
    # iron (Fe) and sulfur (S) tiles; specks stream from them into the drop
    for t_, sym, name, x, y, col, num in ((t_fe, 'Fe', 'IRON', 130, 560, (214, 110, 52), '26'), (t_s, 'S', 'SULFUR', 950, 560, (226, 186, 40), '16')):
        tile(img, sym, name, x, y, pop(u, t_, .3, 2.0), u, col, num)
        if u > t_ + .15:
            d = ImageDraw.Draw(img); rng = np.random.default_rng(int(x))
            for i in range(10):
                v = ((u - t_ - .15) * .9 + i / 10) % 1
                tx, ty = cx + MICROBES[i][0] * .9, cy + MICROBES[i][1] * .9
                px = x + (tx - x) * ease_in(v); py = y + (ty - y) * ease_in(v) - 90 * math.sin(math.pi * v)
                q = 9 * (1 - .5 * v)
                d.ellipse([px - q, py - q, px + q, py + q], fill=lerp(rgb(col), (255, 255, 255), .2), outline=INK, width=2)
    # no sunlight, no oxygen: icons pop, then a red X draws over each
    for t_, x, kind in ((t_sun, 690, 'sun'), (t_o2, 920, 'o2')):
        s = pop(u, t_, .3, 1.8)
        if s <= .01: continue
        lay = layer(260, 260); d = ImageDraw.Draw(lay); c = 130
        if kind == 'sun':
            for a in range(0, 360, 45):
                ar = math.radians(a + u * 40)
                d.line([(c + 70 * math.cos(ar), c + 70 * math.sin(ar)), (c + 112 * math.cos(ar), c + 112 * math.sin(ar))], fill=INK, width=20)
                d.line([(c + 70 * math.cos(ar), c + 70 * math.sin(ar)), (c + 110 * math.cos(ar), c + 110 * math.sin(ar))], fill=(255, 200, 60), width=12)
            d.ellipse([c - 62, c - 62, c + 62, c + 62], fill=(255, 210, 70), outline=INK, width=8)
        else:
            o2(d, c, c, 80)
        draw_x(lay, c, c, 92, seg(u, t_ + .25, t_ + .6) * 2, w=22)
        anim.scaled_paste(img, lay, x, 1560, s * .85)
    # the scientist peers up at the drop from the bottom left
    pose = chain(u, [(0, STAND), (t_alive - .2, add(STAND, armR=(12, 12))), (t_alive + .2, dict(POSES['point'], armR=(-110, -128)), lambda f: out_back(f, 1.7))])
    expr = 'surprised' if u > t_mic else 'thinking'
    g = scientist(img, u, pose, expr, 190, 1910, .78, look=.4, lean=-1 + 2 * smooth(seg(u, t_alive, t_alive + .5)))
    z = 1.04 + .07 * smooth(u / D)
    img = finish(img, u, z, cx, cy, dx=6 * math.sin(u * .5), vig=(.45, (4, 8, 20)))
    clue(img, 'CLUE 2', u)
    return img, {'faces': [face_box(g)], 'avoid': [(0, 1440, W, 1700)]}


# ---------------------------------------------------------------- s09: CLUE 3, the water comes out clear
def outlet_scene(img, u, cam, rust_k=1.0, crack_open=1.0, clear_len=170, sky_cold=0.0):
    """Close on the crack at the foot of the glacier: the brine squeezes out (clear), then turns orange and
    red as it runs down onto the snow. rust_k 0..1 = how much of the stream has rusted (0: all clear)."""
    img.paste(vgrad([(0, (60, 80, 150)), (.12, (150, 170, 220)), (.2, (240, 210, 200))]))
    radial(img, 860 + cam * .9, 220, 480, (255, 210, 170), .4 + .04 * math.sin(u * 1.4))
    cloud_bands(img, 7, 40, 330, (255, 240, 236), .25, n=3, drift=u * 14 + cam)
    top = lambda x: 330 + 24 * math.sin(x / 110) + 12 * math.sin(x / 31)
    bot = lambda x: 1330 + 8 * math.sin(x / 80)
    ice_cliff(img, -40, W + 40, top, bot, seed=33, shade=(118, 164, 220), deep=(52, 92, 160))
    # the crack: a dark slot with teal light leaking out
    cx, cy = 520, 860
    slot = [(cx - 14, cy - 260), (cx + 30, cy - 120), (cx + 8, cy - 20), (cx + 46 * crack_open, cy + 40), (cx - 40 * crack_open, cy + 46), (cx - 26, cy - 60), (cx - 40, cy - 170)]
    m = mask(); ImageDraw.Draw(m).polygon(slot, fill=255)
    glow(img, m, TEAL, .6 + .15 * math.sin(u * 3), blur=40, add=True)
    d = ImageDraw.Draw(img); d.polygon(slot, fill=(10, 30, 48), outline=INK)
    d.line([(cx - 14, cy - 250), (cx + 10, cy - 130), (cx - 4, cy - 40)], fill=(120, 255, 230), width=4)
    # the stream: clear -> orange -> red, flowing dashes all the way
    ys = np.linspace(cy + 40, 1340, 9)
    xs = [cx + 6 + 18 * math.sin(i * 1.1) + i * 6 for i in range(9)]
    ws = [40 + i * 9 for i in range(9)]
    clear_end = cy + 40 + clear_len + (1 - rust_k) * 600
    for i in range(8):
        y0, y1 = ys[i], ys[i + 1]
        for j in range(6):                                                 # sub-steps, so the colour runs smooth
            a = y0 + (y1 - y0) * j / 6; b = y0 + (y1 - y0) * (j + 1) / 6
            f = (a - ys[0]) / (ys[-1] - ys[0]); xa = xs[i] + (xs[i + 1] - xs[i]) * j / 6; wa = ws[i] + (ws[i + 1] - ws[i]) * j / 6
            k = smooth((a - clear_end) / 180)                             # 0 = clear, 1 = rusted
            col = lerp((200, 236, 246), lerp((240, 140, 50), (186, 40, 34), smooth((a - clear_end - 180) / 260)), k)
            d.polygon([(xa - wa / 2 - 5, a), (xa + wa / 2 + 5, a), (xa + wa / 2 + 5, b + 1), (xa - wa / 2 - 5, b + 1)], fill=INK)
            d.polygon([(xa - wa / 2, a), (xa + wa / 2, a), (xa + wa / 2, b + 1), (xa - wa / 2, b + 1)], fill=col)
    rng = np.random.default_rng(4)
    for k_ in range(26):                                                  # flowing highlight dashes
        v = (rng.random() + u * .7) % 1; y = ys[0] + (ys[-1] - ys[0]) * v; i = min(7, int(v * 8))
        x = xs[i] + rng.uniform(-.3, .3) * ws[i]
        d.line([(x, y), (x + 2, y + 30)], fill=(255, 255, 255) if y < clear_end else (255, 190, 150), width=5)
    if rust_k > 0:
        radial(img, xs[-1], 1360, 360, (255, 80, 40), .18 * rust_k * (.85 + .15 * math.sin(u * 3)))
    snow_ground(img, lambda x: 1340 + 10 * math.sin(x / 140), seed=31, drifts=6)
    if rust_k > 0:
        sf.red_fan(img, (xs[-1] + 40, 1350), (560 * (.5 + .5 * rust_k), 200 * (.5 + .5 * rust_k)), color=(186, 44, 30), edge=(226, 104, 44), seed=9)
    rocks(img, 23, [(80, 1460, 46), (1010, 1480, 52), (60, 1800, 64), (900, 1880, 50)])
    return (xs[0], ys[0]), clear_end


def s09(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-12, 12, smooth(u / D))
    (ox, oy), clear_end = outlet_scene(img, u, cam)
    t_right, t_red, t_clear = cue(2) - .1, cue(9) - .1, cue(14) - .1
    # the scientist leans in at the outlet (faces left), points at it, and startles on "clear"
    pt = {'armL': (82, 92), 'armR': (-24, -10), 'legL': (11, 1), 'legR': (-11, -1)}
    pose = chain(u, [(0, STAND), (t_right - .3, add(STAND, armL=(-12, -12))), (t_right + .15, pt, lambda f: out_back(f, 1.8))])
    pose = add(pose, armL=(3 * math.sin(u * 4), 5 * math.sin(u * 4 - .6)))
    lean = -6 * smooth(seg(u, t_right - .2, t_right + .4)) + 7 * out_back(seg(u, t_clear, t_clear + .35)) * (u > t_clear)
    hop = 22 * math.sin(math.pi * seg(u, t_clear, t_clear + .25)) if t_clear < u < t_clear + .25 else 0
    g = scientist(img, u, pose, 'surprised' if u > t_clear else 'thinking', 905, 1880, .9, look=-.7, lean=lean, hop=hop, rim=(255, 200, 160), rim_dir=(-1, -.3))
    # magnifier ring on the clear part ("the water isn't red at all"), then CLEAR pops
    s = pop(u, t_red, .35, 1.6)
    if s > .01:
        lx, ly, lr = ox + 10, oy + 110, 150
        lay = layer(2 * lr + 80, 2 * lr + 80); c = lr + 40; d = ImageDraw.Draw(lay)
        view = img.crop((int(lx - lr / 1.8), int(ly - lr / 1.8), int(lx + lr / 1.8), int(ly + lr / 1.8))).resize((2 * lr, 2 * lr), Image.BICUBIC)
        cm = mask(2 * lr, 2 * lr); ImageDraw.Draw(cm).ellipse([0, 0, 2 * lr - 1, 2 * lr - 1], fill=255)
        lay.paste(view, (c - lr, c - lr), cm)
        for i in range(6):                                                # bubbles rise in the clear water
            v = (u * .6 + i / 6) % 1; bx = c - 30 + 60 * math.sin(i * 2.1); by = c + lr * .8 - 1.6 * lr * v
            d.ellipse([bx - 9, by - 9, bx + 9, by + 9], outline=(255, 255, 255), width=3)
        d.ellipse([c - lr - 12, c - lr - 12, c + lr + 12, c + lr + 12], outline=INK, width=26)
        d.ellipse([c - lr - 7, c - lr - 7, c + lr + 7, c + lr + 7], outline=(230, 236, 246), width=12)
        d.line([(c + lr * .72, c + lr * .72), (c + lr * 1.15, c + lr * 1.15)], fill=INK, width=38)
        d.line([(c + lr * .74, c + lr * .74), (c + lr * 1.13, c + lr * 1.13)], fill=(150, 104, 64), width=24)
        anim.scaled_paste(img, lay, lx - 170, ly - 150, s)
    put_chip(img, 'CLEAR!', (40, 150, 200), 250, 540, pop(u, t_clear, .3, 2.0), size=70, angle=-4 + 2 * math.sin(u * 3))
    if u > t_clear:
        d = ImageDraw.Draw(img)
        for i in range(8):                                                # sparkle on "clear"
            v = (u - t_clear) * 1.6 - i * .05
            if 0 < v < 1:
                a = i * .8; x = ox - 150 + 120 * math.cos(a) * (1 + v); y = oy + 70 + 120 * math.sin(a) * (1 + v); q = 14 * (1 - v)
                d.polygon([(x, y - q * 2), (x + q * .5, y), (x, y + q * 2), (x - q * .5, y)], fill='white')
                d.polygon([(x - q * 2, y), (x, y + q * .5), (x + q * 2, y), (x, y - q * .5)], fill='white')
    snow_particles(img, 61, n=(50, 20, 6), wind=(5, 1), t=u)
    img = finish(img, u, 1.04 + .06 * smooth(u / D), 520, 1000, dx=-cam * 1.05)
    clue(img, 'CLUE 3', u)
    return img, {'faces': [face_box(g)]}


# ---------------------------------------------------------------- s10: scanned from the air
def sensor_loop(img, x, y, t, s=1.0):
    d = ImageDraw.Draw(img)
    pts = [(x + 150 * s * math.cos(a), y + 40 * s * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 7)]
    d.line(pts, fill=INK, width=16); d.line(pts, fill=(255, 196, 60), width=8)
    return pts


def s10(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(30, -30, smooth(u / D))
    backdrop(img, u + 3, cam, [(0, (40, 70, 150)), (.25, (110, 150, 220)), (.45, (240, 214, 200)), (.5, (255, 226, 200))],
             (880, 800, (255, 214, 170)), ((200, 196, 226), (150, 150, 200), (246, 244, 252)),
             ((170, 186, 226), (112, 130, 196), (250, 250, 255)), (250, 230, 226), horizon=980)
    # the glacier tongue, cut away below the surface (X-ray band) so the scan has something to find
    surf = lambda x: 1080 + 14 * math.sin(x / 160) + (x - 540) * .03
    snow_ground(img, surf, color=(246, 249, 253), shade=(196, 212, 236), seed=44)
    xs = np.arange(-20, W + 21, 20)
    cut = [(x, surf(x) + 70) for x in xs] + [(W + 20, H), (-20, H)]
    ice = vgrad([(0, (170, 224, 246)), (.35, (110, 170, 224)), (1, (40, 70, 130))], W, H)
    cm = mask(); ImageDraw.Draw(cm).polygon(cut, fill=255); img.paste(ice, (0, 0), cm)
    d = ImageDraw.Draw(img)
    for k in range(9):
        y0 = 1220 + k * 70
        d.line([(x, y0 + 12 * math.sin(x / 120 + k)) for x in xs], fill=(110, 170, 220) if k % 3 else (220, 240, 255), width=3)
    gl = layer(); gd = ImageDraw.Draw(gl)
    for x in range(0, W, 60): gd.line([(x, 1160), (x, H)], fill=(180, 240, 255, 22), width=2)
    img.alpha_composite(gl)
    d.line([(x, y) for x, y in cut[:len(xs)]], fill=INK, width=6)
    # the plane crosses, towing a sensor loop; pulses run down into the ice and the hidden pool starts to glow
    px = -120 + 900 * smooth(seg(u, 0, D + .4)) + cam * .3; py = 560 + 10 * math.sin(u * 2)
    lx, ly = px - 60, 760 + 8 * math.sin(u * 2 + .6)
    d.line([(px - 30, py + 30), (lx - 120, ly - 10)], fill=INK, width=4); d.line([(px - 10, py + 30), (lx + 120, ly - 10)], fill=INK, width=4)
    find = smooth(seg(u, cue(3), D))
    radial(img, 560, 1650, 520, TEAL, .12 + .4 * find * (.85 + .15 * math.sin(u * 4)))
    pm = mask(); ImageDraw.Draw(pm).ellipse([200, 1580, 920, 1720], fill=255)
    glow(img, pm, TEAL, .5 * find, blur=40, add=True)
    for k in range(6):                                                    # scan pulses
        v = (u * 1.4 - k * .33)
        if v < 0: continue
        v = v % 2.0
        r = 60 + 520 * v; a = max(0, 1 - v / 2)
        m = mask(); ImageDraw.Draw(m).arc([lx - r * 1.3, ly - r * .3, lx + r * 1.3, ly + r * 1.1], 20, 160, fill=255, width=10)
        glow(img, m, (160, 255, 236), .7 * a, blur=4, add=True)
    sensor_loop(img, lx, ly, u)
    props.plane(img, px, py, 1.25)
    put_chip(img, 'AIR SCAN', (20, 120, 130), px - 40, py - 120, pop(u, cue(2) - .1, .3, 1.8), size=46)
    # the scientist on the snow watches it pass, pointing up
    pt = dict(STAND, armR=(-140, -160))
    pose = chain(u, [(0, STAND), (.35, add(STAND, armR=(10, 10))), (.7, pt, lambda f: out_back(f, 1.7))])
    g = scientist(img, u, pose, 'surprised', 760, 1290, .66, look=-.3 + .5 * smooth(u / D), rim=(255, 210, 170), rim_dir=(-1, -.4))
    foreground_frame(img, [[(-20 + cam * -.6, 1940), (-20, 1780), (160, 1750), (320, 1840), (420, 1940)]], color=(120, 150, 210), alpha=.85)
    snow_particles(img, 71, n=(50, 20, 6), wind=(6, 1), t=u)
    img = finish(img, u, 1.04 + .04 * smooth(u / D), 540, 1100, dx=-cam * 1.05)
    return img, {'faces': [face_box(g)], 'avoid': [(0, 1560, W, 1740)]}


# ---------------------------------------------------------------- s11a: the X-ray cross-section
def s11a(u, D, cue):
    """Port of style_frames.s11a with motion: the 400 m arrow draws down on "four hundred metres", the pool
    lights up on "hidden pool" and keeps pulsing, brine rises up the outflow channel toward Blood Falls,
    the plane crosses, the scan line sweeps, motes drift, stars twinkle."""
    t = u
    img = vgrad([(0, (10, 14, 44)), (.2, (40, 56, 120)), (1, (10, 14, 36))])
    surf = 420; ice_bot = lambda x: 1060 + 26 * math.sin(x / 170)
    stars(img, 2, 60, surf - 60, t)
    peak_range(img, 41, surf + 10, 60, 150, (70, 84, 150), (46, 56, 112), (150, 170, 220), n=7)
    xs = np.arange(-10, W + 11, 10)
    top = [(x, surf + 8 * math.sin(x / 90)) for x in xs]
    body = top + [(x, ice_bot(x)) for x in xs[::-1]]
    ice = vgrad([(0, (190, 234, 250)), (.25, (120, 196, 236)), (.5, (60, 130, 200)), (1, (20, 50, 120))], W, H)
    bm = mask(); ImageDraw.Draw(bm).polygon(body, fill=255); img.paste(ice, (0, 0), bm)
    d = ImageDraw.Draw(img); rng = np.random.default_rng(2)
    for k in range(13):
        y0 = surf + 34 + k * 44
        d.line([(x, y0 + 14 * math.sin(x / 130 + k) + 6 * math.sin(x / 41 + 2 * k)) for x in xs],
               fill=(255, 255, 255) if k % 3 == 0 else (70, 134, 200), width=3 if k % 3 else 4)
    for _ in range(60):
        x, y, q = rng.uniform(0, W), rng.uniform(surf + 40, 940), rng.uniform(3, 9)
        y -= (t * 6) % 30                                                   # trapped air bubbles creep
        d.ellipse([x - q, y - q, x + q, y + q], outline=(230, 248, 255), width=2)
    gl = layer(); gd = ImageDraw.Draw(gl)
    for x in range(0, W, 60): gd.line([(x, surf), (x, 1020)], fill=(180, 240, 255, 26), width=2)
    for y in range(surf, 1020, 60): gd.line([(0, y), (W, y)], fill=(180, 240, 255, 26), width=2)
    img.alpha_composite(gl)
    sy = 720 + 260 * math.sin(t * 1.6)
    m = mask(); ImageDraw.Draw(m).rectangle([0, sy - 4, W, sy + 4], fill=255); glow(img, m, (120, 255, 240), .8, blur=10, add=True)
    rock = vgrad([(0, (156, 112, 138)), (.35, (126, 88, 120)), (1, (66, 48, 80))], W, H - 1040, 0)
    rl = Image.new('RGBA', (W, H)); rl.paste(rock, (0, 1040))
    rm = mask(); ImageDraw.Draw(rm).polygon([(x, ice_bot(x) - 4) for x in xs] + [(W + 10, H), (-10, H)], fill=255)
    img.paste(rl, (0, 0), rm)
    d = ImageDraw.Draw(img)
    for k in range(4):
        y0 = 1560 + k * 96
        d.line([(x, y0 + 18 * math.sin(x / 110 + k * 1.7)) for x in xs], fill=(150, 108, 130) if k % 2 else (86, 60, 90), width=6)
    for x, y, q in ((80, 1600, 30), (560, 1640, 22), (1010, 1590, 34), (300, 1780, 26), (800, 1760, 30)):
        d.polygon([(x - q, y), (x - q * .3, y - q * .8), (x + q, y - q * .4), (x + q * .7, y + q * .5)], fill=(160, 118, 136), outline=(40, 26, 42), width=3)
    for x, y, q in ((180, 1700, 30), (690, 1860, 26), (930, 1700, 22)):
        d.chord([x - q, y - q, x + q, y + q], 180, 360, fill=(196, 160, 170), outline=(40, 26, 42), width=3)
        for a in range(200, 341, 35):
            d.line([(x, y), (x + q * math.cos(math.radians(a)), y + q * math.sin(math.radians(a)))], fill=(120, 84, 104), width=2)
    # brine pool: lights up on "hidden pool", then pulses 0.85-1.0
    t_pool = cue(8) - .1
    lit = .3 + .7 * smooth(seg(t, t_pool, t_pool + .5))
    pulse = lit * (.85 + .15 * math.sin(t * 3.4))
    cx, cy, rx, ry = 540, 1215, 600, 160
    radial(img, cx, cy + 80, 780, TEAL, .3 * pulse)
    light_rays(img, cx, cy + 60, (80, 240, 210), n=8, alpha=.16 * pulse, spread=(50, 130), length=900, seed=4, phase=2 * math.sin(t))
    pm = mask(); ImageDraw.Draw(pm).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    glow(img, pm, (60, 255, 210), .9 * pulse, blur=90, add=True)
    glow(img, pm, (160, 255, 230), .6 * pulse, blur=30, add=True)
    pool = vgrad([(0, lerp((40, 90, 100), (120, 255, 226), lit)), (.5, lerp((14, 60, 70), (24, 170, 160), lit)), (1, (10, 80, 96))], 2 * rx, 2 * ry)
    radial(pool, rx + 200 * math.sin(t * .7), ry * .6, rx * .7, (220, 255, 240), .6 * pulse)
    pd = ImageDraw.Draw(pool)
    for k in range(5):                                                    # slow ripples across the pool
        yk = ry * (.4 + k * .3) + 6 * math.sin(t * 2 + k)
        pd.line([(x, yk + 8 * math.sin(x / 70 + t * 2.2 + k)) for x in range(0, 2 * rx, 14)], fill=(170, 255, 236), width=3)
    dust(pool, 9, 70, (20, 10, 2 * rx - 20, 2 * ry - 10), (210, 255, 230), 200, size=(2, 7), t=t)
    cm = mask(2 * rx, 2 * ry); ImageDraw.Draw(cm).ellipse([0, 0, 2 * rx - 1, 2 * ry - 1], fill=255)
    img.paste(pool, (cx - rx, cy - ry), cm)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=INK, width=6)
    d.ellipse([cx - rx + 6, cy - ry + 6, cx + rx - 6, cy + ry - 6], outline=(190, 255, 240), width=5)
    d.arc([cx - rx + 60, cy - ry + 18, cx + rx - 60, cy + ry - 20], 200, 250, fill=(240, 255, 250), width=8)
    put_chip(img, 'BRINE POOL', (14, 110, 110), cx, cy + 20, pop(t, t_pool + .2, .3, 1.8), size=54)
    # outflow channel: brine rises up toward Blood Falls (dashes + blobs travel up the channel)
    ch = [(990, cy - 80), (1000, 900), (960, 720), (1010, surf + 40), (W + 20, surf - 10)]
    d.line(ch, fill=INK, width=30, joint='curve'); d.line(ch, fill=(40, 150, 150), width=18, joint='curve')
    for k in range(9):
        f = (k / 9 + t * .32) % 1; x, y = path_point(ch, f); q = 7 + 3 * math.sin(t * 5 + k)
        c = (90, 240, 220) if f < .85 else (240, 90, 60)
        d.ellipse([x - q, y - q, x + q, y + q], fill=c)
    d.line(ch[-2:], fill=(220, 60, 40), width=14)
    d.polygon(top + [(x, y + 24) for x, y in top[::-1]], fill=(246, 250, 255)); d.line(top, fill=INK, width=6)
    # the plane crosses with radar pulses down its fan
    px_, py_ = 200 + 100 * t, 372
    fan = mask(); ImageDraw.Draw(fan).polygon([(px_ - 10, py_ + 50), (px_ + 20, py_ + 50), (px_ + 360, cy - 120), (px_ - 330, cy - 120)], fill=255)
    fill_mask(img, fan, (140, 255, 230), .15, blur=8)
    for k in range(5):
        yk = surf + 40 + ((k * 110 + t * 260) % 550)
        ImageDraw.Draw(img).arc([px_ + 5 - (yk - py_) * .48, yk - 36, px_ + 5 + (yk - py_) * .48, yk + 36], 20, 160, fill=(170, 255, 236), width=5)
    props.plane(img, px_ - 10, py_, 1.0)
    # 400 m arrow draws down on "four hundred metres"
    d = ImageDraw.Draw(img); ax = 76
    k_ar = ease_out(seg(t, cue(1) - .1, cue(3) + .2))
    y_end = surf + 30 + (ice_bot(ax) - 16 - surf - 30) * k_ar
    if k_ar > .02:
        d.line([(ax, surf + 30), (ax, y_end)], fill=INK, width=22); d.line([(ax, surf + 30), (ax, y_end)], fill='white', width=13)
        d.polygon([(ax, surf + 30), (ax - 26, surf + 70), (ax + 26, surf + 70)], fill='white', outline=INK, width=4)
        d.polygon([(ax, y_end), (ax - 26, y_end - 40), (ax + 26, y_end - 40)], fill='white', outline=INK, width=4)
    put_chip(img, '400 m', (36, 120, 200), ax + 96, 720, pop(t, cue(2), .3, 1.8), size=64)
    put_chip(img, 'TO BLOOD FALLS', (200, 50, 44), 860, surf + 70, pop(t, .5, .3, 1.6), size=34)
    img = finish(img, t, 1.03 + .05 * smooth(t / D), 540, 1100, vig=(.3, (4, 6, 20)), grain_amt=.03)
    slam_title(img, 's11a', [('A HIDDEN SEA', 'white', 104), ('UNDER THE ICE', (110, 255, 226), 86)], 60, t, .1)
    return img, {'faces': [], 'avoid': [(0, 1020, W, 1400), (0, 0, W, 480)]}


# ---------------------------------------------------------------- s11b: sealed for over a million years
_crk = {}
def crack_lines():
    if 'l' not in _crk:
        rr = np.random.default_rng(8); out = []
        for a in np.linspace(0, 2 * math.pi, 9, endpoint=False):
            x, y = 0.0, 0.0; pts = [(x, y)]
            for _ in range(5):
                a2 = a + rr.uniform(-.4, .4); x += math.cos(a2) * rr.uniform(60, 110); y += math.sin(a2) * rr.uniform(20, 40); pts.append((x, y))
            out.append(pts)
        _crk['l'] = out
    return _crk['l']


def s11b(u, D, cue):
    img = Image.new('RGBA', (W, H))
    img.paste(vgrad([(0, (8, 12, 40)), (.35, (30, 44, 104)), (.55, (70, 90, 160)), (.62, (150, 170, 220))]))
    stars(img, 5, 90, 1000, u)
    am = mask(); ImageDraw.Draw(am).polygon([(x, 560 + 70 * math.sin(x / 160 + u * .6) + y) for x, y in ((0, 0), (300, -40), (600, 0), (900, -60), (1080, -20))] +
                                            [(1080, 640), (800, 700), (400, 660), (0, 700)], fill=255)
    glow(img, am, TEAL, .5 + .08 * math.sin(u * 1.7), blur=60, add=True)   # the aurora ripples
    peak_range(img, 51, 1010, 140, 300, (120, 130, 190), (70, 80, 140), (220, 230, 250), n=7)
    haze(img, 900, 1060, (150, 170, 220), .5)
    snow_ground(img, lambda x: 1060 + 10 * math.sin(x / 150), color=(150, 168, 214), shade=(112, 128, 184), seed=21)
    d = ImageDraw.Draw(img)
    for k in range(7):
        y0 = 1180 + k * 90; x0 = 60 + (k % 3) * 260
        pts = [(x0 + v * 16, y0 + 10 * math.sin(v / 3 + k)) for v in range(0, 26)]
        d.line(pts, fill=(104, 120, 176), width=5); d.line([(x, y + 6) for x, y in pts], fill=(196, 210, 240), width=3)
    # the cracks spread out from under his boots (draw on), teal light pulsing up through them
    cx0, cy0 = 330, 1790
    grow = ease_out(seg(u, 0, 1.3))
    cr = mask(); cd = ImageDraw.Draw(cr); segs = []
    for i, pts in enumerate(crack_lines()):
        p = partial([(cx0 + x * (1 + .1 * i % 3), cy0 + y) for x, y in pts], min(1, grow * (1.25 - .05 * i)))
        segs.append(p); cd.line(p, fill=255, width=14)
    pulse = .9 + .1 * math.sin(u * 3.2)
    glow(img, cr, TEAL, .95 * pulse, blur=60, add=True)
    glow(img, cr, (140, 255, 230), 1.0, blur=14, add=True)
    radial(img, cx0, cy0, 300 + 260 * grow, TEAL, .45 * pulse)
    d = ImageDraw.Draw(img)
    for p in segs:
        d.line(p, fill=(20, 60, 70), width=12); d.line(p, fill=(170, 255, 236), width=7)
    props.plane(img, 560 + 80 * u, 440, .8)
    for k in range(3):
        r = 120 + ((k * 170 + u * 200) % 510)
        ImageDraw.Draw(img).arc([560 + 80 * u - r * 1.2, 440 + r * .5, 560 + 80 * u + r * 1.2, 440 + r * 1.3], 30, 150, fill=(170, 255, 236), width=4)
    # the scientist: startles as the cracks open, one hand at the cracks, one flung up
    startled = dict(armL=(50, 28), armR=(-118, -150), legL=(16, 2), legR=(-12, -1))
    pose = chain(u, [(0, add(STAND, armL=(-6, -8), armR=(6, 8))), (.12, add(STAND, armL=(-14, -20), armR=(14, 20), legL=(3, -2), legR=(-3, 2))),
                     (.45, startled, lambda f: out_back(f, 1.8))])
    hop = 28 * math.sin(math.pi * seg(u, .12, .4)) if .12 < u < .4 else 0
    g = scientist(img, u, pose, 'surprised', cx0, cy0, 1.0, look=.15, lean=-3 * smooth(seg(u, .1, .5)), hop=hop,
                  rim=(150, 255, 230), rim_dir=(-.6, 1))
    foreground_frame(img, [[(-20, 1940), (-20, 1830), (140, 1800), (300, 1860), (380, 1940)]], color=(120, 140, 200), alpha=.85)
    snow_particles(img, 29, n=(70, 30, 10), wind=(4, 1), t=u)
    img = finish(img, u, 1.04 + .05 * smooth(u / D), 480, 1300, vig=(.36, (4, 6, 24)), grain_amt=.03)
    # counter: SEALED FOR ... rolls up to 1,000,000+ YEARS
    k = ease_out(seg(u, cue(14) - .1, cue(17) + .3)); n = int(round(1_000_000 * k / 1000) * 1000)
    bx0, by0, bx1, by1 = 150, 120, 930, 330
    yb = -260 * (1 - out_back(seg(u, 0, .35), 1.4))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([bx0 + 8, by0 + 12 + yb, bx1 + 8, by1 + 12 + yb], 40, fill=(6, 4, 16))
    d.rounded_rectangle([bx0, by0 + yb, bx1, by1 + yb], 40, fill=(16, 26, 58), outline=(120, 255, 230), width=7)
    d.text(((bx0 + bx1) / 2, by0 + 56 + yb), 'SEALED FOR', font=font(48, True), fill=(150, 240, 230), anchor='mm')
    txt = f'{n:,}' + ('+ YEARS' if k >= 1 else ' YEARS')
    sc = 1 + damp(u - (cue(17) + .3), .12, 6, 20)
    lay, _ = chip_text(txt)
    anim.scaled_paste(img, lay, (bx0 + bx1) / 2, by0 + 140 + yb, sc)
    return img, {'faces': [face_box(g)]}


_ct = {}
def chip_text(txt):
    if txt not in _ct:
        if len(_ct) > 300: _ct.clear()
        _ct[txt] = anim.text_layer(lambda l: ImageDraw.Draw(l).text((540, 100), txt, font=font(92), fill='white', anchor='mm',
                                                                     stroke_width=6, stroke_fill=(10, 6, 20)), W, 200)
    return _ct[txt]


# ---------------------------------------------------------------- s12 / s13: inside the pool
def pool_room(img, u, dark=0.0, crack=0.0):
    """Inside the brine pool: the ice ceiling on top (needle crystals on its underside), teal water with
    caustics and motes, sediment and rocks below. dark 0..1 darkens it (s13); crack 0..1 opens a slot up."""
    img.paste(vgrad([(0, lerp((40, 150, 150), (10, 40, 50), dark)), (.5, lerp((18, 96, 110), (6, 24, 36), dark)), (1, lerp((8, 40, 56), (2, 10, 20), dark))]))
    radial(img, 540 + 160 * math.sin(u * .5), 700, 800, lerp((120, 255, 226), (40, 100, 110), dark), .35)
    d = ImageDraw.Draw(img)
    for k in range(10):                                                   # caustic bands drift
        y0 = 420 + k * 120 + 20 * math.sin(u * .7 + k)
        d.line([(x, y0 + 16 * math.sin(x / 80 + u * 1.5 + k)) for x in range(-20, W + 21, 16)], fill=lerp((80, 200, 190), (20, 60, 70), dark), width=4)
    # ice ceiling
    xs = np.arange(-20, W + 21, 20)
    ceil = [(x, 360 + 26 * math.sin(x / 90) + 14 * math.sin(x / 33)) for x in xs]
    d.polygon([(-20, -10), (W + 20, -10)] + ceil[::-1], fill=lerp((200, 236, 250), (90, 120, 150), dark))
    for k in range(4):
        d.line([(x, 80 + k * 70 + 10 * math.sin(x / 100 + k)) for x in xs], fill=lerp((150, 200, 236), (60, 90, 120), dark), width=4)
    d.line(ceil, fill=INK, width=6)
    if crack > 0:                                                         # the crack opens upward (s13 "Until it escapes")
        cx = 560; w_ = 10 + 60 * crack
        slot = [(cx - w_, 380), (cx - w_ * .4, 220), (cx - w_ * .7, 90), (cx - 10, -10), (cx + 10, -10), (cx + w_ * .7, 90), (cx + w_ * .4, 220), (cx + w_, 380)]
        m = mask(); ImageDraw.Draw(m).polygon(slot, fill=255)
        glow(img, m, (255, 240, 210), .9 * crack, blur=50, add=True)
        d.polygon(slot, fill=lerp((60, 80, 100), (255, 250, 236), crack), outline=INK)
        beam = mask(); ImageDraw.Draw(beam).polygon([(cx - w_, 380), (cx + w_, 380), (cx + 300 * crack + 40, 1500), (cx - 300 * crack - 40, 1500)], fill=255)
        glow(img, beam, (255, 240, 210), .35 * crack, blur=40, add=True)
    # sediment floor
    floor = [(x, 1640 + 20 * math.sin(x / 120) + 10 * math.sin(x / 41)) for x in xs]
    d.polygon(floor + [(W + 20, H + 10), (-20, H + 10)], fill=lerp((96, 74, 96), (30, 24, 36), dark)); d.line(floor, fill=INK, width=6)
    rocks(img, 41, [(120, 1700, 50), (880, 1720, 60), (500, 1790, 34)], lit=lerp((150, 116, 136), (60, 50, 60), dark), shade=lerp((90, 66, 90), (30, 24, 34), dark), snow=lerp((150, 116, 136), (60, 50, 60), dark))
    light_rays(img, 540, 300, lerp((150, 255, 230), (70, 140, 140), dark), n=7, alpha=.13, spread=(55, 125), length=1500, seed=8, phase=3 * math.sin(u * .5))
    dust(img, 13, 60, (0, 380, W, 1640), lerp((200, 255, 236), (90, 130, 140), dark), 150, size=(2, 6), t=u)
    bubbles(img, 200, 1620, 1200, u * .5, seed=3, n=6, color=lerp((210, 255, 240), (120, 170, 170), dark))
    bubbles(img, 880, 1620, 1200, u * .5, seed=4, n=6, color=lerp((210, 255, 240), (120, 170, 170), dark))
    return ceil


def s12(u, D, cue):
    img = Image.new('RGBA', (W, H))
    ceil = pool_room(img, u)
    radial(img, 540, 1100, 700, (120, 255, 226), .25 + .05 * math.sin(u * 2.5))           # the brine glows
    t_salt, t_heat, t_free, t_liq = cue(0) - .1, cue(2) - .1, cue(6) - .1, cue(7) - .1
    d = ImageDraw.Draw(img)
    # needle crystals grow on the ceiling (it freezes) and each one sends heat (red waves) back into the water
    rng = np.random.default_rng(6)
    for i in range(14):
        x = 60 + i * 72 + rng.uniform(-20, 20); y = 360 + 26 * math.sin(x / 90) + 14 * math.sin(x / 33)
        L = (40 + 60 * rng.uniform()) * smooth(seg(u, .1 + i * .08, 1.0 + i * .12))
        if L > 3:
            d.polygon([(x - 10, y), (x + 10, y), (x + 1, y + L)], fill=(236, 250, 255), outline=(90, 150, 200))
        v = (u - t_heat + i * .17) % 1.1
        if u > t_heat and L > 10 and v < 1:                               # latent heat: a red wave leaves each crystal
            pts = [(x + 12 * math.sin(j * 1.4 + u * 9), y + L + 20 + j * 18 + 120 * v) for j in range(6)]
            d.line(pts, fill=INK, width=11, joint='curve'); d.line(pts, fill=(255, 90, 60), width=6, joint='curve')
    radial(img, 540, 520, 600, (255, 90, 60), .2 * smooth(seg(u, t_heat, t_heat + .5)) * (.8 + .2 * math.sin(u * 5)))
    # salt cubes tumble through the water
    for i in range(10):
        q = 20 + (i % 3) * 6; x = 120 + i * 96 + 30 * math.sin(u + i); y = 700 + (i * 137) % 700 + 40 * math.sin(u * .7 + i * 2)
        a = u * 40 + i * 30; s_ = pop(u, t_salt + i * .04, .3, 1.6)
        if s_ <= .01: continue
        q *= s_; c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        sq = [(x + q * (c * px - sn * py), y + q * (sn * px + c * py)) for px, py in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        d.polygon(sq, fill=(250, 250, 255), outline=INK); d.line([sq[0], sq[2]], fill=(200, 210, 230), width=2)
    # a couple of microbes swim through
    for i in range(3):
        microbe(img, (200 + i * 330 + 60 * u) % (W + 200) - 100, 1240 + 120 * math.sin(i * 2 + u), 22, u, 70 + i)
    put_chip(img, 'SALT', (90, 110, 150), 230, 610, pop(u, t_salt, .3, 1.9), size=60, angle=-4)
    put_chip(img, 'HEAT', (220, 70, 50), 850, 610, pop(u, t_heat, .3, 1.9), size=60, angle=4)
    k = pop(u, t_liq, .35, 1.8)
    put_chip(img, 'STILL LIQUID', (14, 130, 120), 540, 1500, k, size=64, angle=2 * math.sin(u * 3))
    img = finish(img, u, 1.04 + .05 * smooth(u / D), 540, 900, dx=10 * math.sin(u * .6), vig=(.4, (2, 12, 20)), grain_amt=.03)
    return img, {'faces': [], 'avoid': [(0, 1430, W, 1580)]}


def s13(u, D, cue):
    img = Image.new('RGBA', (W, H))
    t_iron, t_inv, t_until, t_esc = cue(3) - .1, cue(5) - .1, cue(6) - .15, cue(8) - .1
    dark = .25 + .3 * smooth(seg(u, 0, 1.2))
    crack = smooth(seg(u, t_until, t_until + .45))
    pool_room(img, u + 3, dark=dark, crack=crack)
    # dissolved iron: ghost particles (colourless). They flash on "iron", fade on "invisible", then rush up the crack
    hi = math.exp(-max(0, u - t_iron) * 3) * (u > t_iron)
    fade = 1 - .55 * smooth(seg(u, t_inv, t_inv + .5))
    lay = layer(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(13)
    for i in range(26):
        x0, y0 = rng.uniform(60, W - 60), rng.uniform(520, 1560); q = rng.uniform(30, 46)
        x = x0 + 18 * math.sin(u * .8 + i); y = y0 + 14 * math.cos(u * .7 + 2 * i)
        if crack > 0:                                                     # sucked toward the crack, then up it
            v = ease_in(seg(u, t_until + .05 + (y0 - 520) / 1040 * .5, t_esc + .6))
            x = x + (560 - x) * v; y = y + (300 - y) * v - 300 * v * v
        a = int(255 * fade * (.75 + .25 * hi))
        for ang in range(0, 360, 36):
            d.arc([x - q, y - q, x + q, y + q], ang, ang + 20, fill=(230, 250, 255, a), width=4)
        d.text((x, y), 'Fe', font=font(int(q * .9), True), fill=(230, 250, 255, int(a * .9)), anchor='mm')
    for i in range(4):                                                    # dim microbes: the pool is alive, but dark
        microbe(lay, 150 + i * 260 + 30 * math.sin(u + i), 900 + 260 * math.sin(i * 1.7) + 20 * math.cos(u * .8 + i), 22, u, 120 + i, .5, (90, 170, 150))
    img.alpha_composite(lay)
    if hi > .05: radial(img, 540, 1000, 700, (200, 255, 240), .2 * hi)
    k = pop(u, t_inv, .3, 1.8) * (1 - smooth(seg(u, t_until, t_until + .3)))
    if k > .01:
        lay = layer(560, 200); dl = ImageDraw.Draw(lay)
        pill(lay, '     INVISIBLE', 280, 100, (40, 60, 80), size=60)
        ex, ey = 120, 100                                                 # eye-slash icon
        dl.ellipse([ex - 40, ey - 22, ex + 40, ey + 22], outline='white', width=7); dl.ellipse([ex - 12, ey - 12, ex + 12, ey + 12], fill='white')
        dl.line([(ex - 44, ey + 30), (ex + 44, ey - 30)], fill=(255, 90, 80), width=9)
        anim.scaled_paste(img, lay, 540, 1160, k)
    sx, sy = shake(u, t_esc, 10)
    z = 1.04 + .04 * smooth(u / D) + .08 * smooth(seg(u, t_until, D))
    img = finish(img, u, z, 560, anim.lerp(1000, 500, smooth(seg(u, t_until, D))), dx=sx, dy=sy, vig=(.5, (0, 4, 10)), grain_amt=.035)
    return img, {'faces': [], 'avoid': [(0, 1080, W, 1240)]}


# ---------------------------------------------------------------- s14a: it meets the air and rusts
def s14a(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(10, -10, smooth(u / D))
    t_sq, t_air, t_meet, t_rust = cue(4) - .1, cue(8) - .1, cue(11) - .1, cue(14) - .08
    rust = smooth(seg(u, t_meet - .1, t_rust + .15))
    (ox, oy), clear_end = outlet_scene(img, u + 4, cam, rust_k=rust, crack_open=.6 + .4 * out_back(seg(u, t_sq, t_sq + .4), 1.6), clear_len=150)
    d = ImageDraw.Draw(img)
    # O2 bubbles drift in from the air and hit the stream; each contact sparks orange
    hits = [(-240, 520, 58, 0.0), (250, 470, 64, .25), (-140, 300, 46, .5), (200, 260, 50, .7), (-300, 700, 40, .9)]
    for i, (dx, y0, q, dl) in enumerate(hits):
        a = t_air + dl
        if u < a - .6: continue
        v = smooth(seg(u, a - .6, a + .5))
        tx, ty = ox + 10, oy + 200 + i * 70
        x = ox + dx + (tx - (ox + dx)) * v; y = y0 + (ty - y0) * v + 10 * math.sin(u * 3 + i)
        if v < 1:
            o2(d, x, y, q * (1 - .5 * v), fill=lerp((150, 210, 255), (255, 170, 80), smooth(seg(v, .7, 1))))
        else:
            w_ = u - a - .5
            if w_ < .5:                                                   # contact spark
                r = 30 + 160 * ease_out(w_ / .5); m = mask(); ImageDraw.Draw(m).ellipse([tx - r, ty - r * .6, tx + r, ty + r * .6], outline=255, width=8)
                glow(img, m, (255, 150, 60), .8 * (1 - w_ / .5), blur=4, add=True)
    put_chip(img, 'AIR', (70, 140, 220), 250, 430, pop(u, t_air, .3, 1.8), size=56)
    put_chip(img, 'Fe + O2 = RUST', (206, 84, 30), 540, 1560, pop(u, t_meet, .35, 1.8), size=56, angle=-2 + 1.5 * math.sin(u * 2))
    if u > t_rust:                                                        # "rusts": an orange flash down the stream
        radial(img, ox + 30, 1250, 520, (255, 140, 50), .5 * math.exp(-(u - t_rust) * 4))
    pose = chain(u, [(0, STAND), (t_rust - .3, add(STAND, armL=(-8, -10), armR=(8, 10))), (t_rust + .1, dict(POSES['cheer'], armL=(110, 140), armR=(-110, -140)), lambda f: out_back(f, 1.8))])
    g = scientist(img, u, pose, 'surprised' if u > t_rust else 'thinking', 820, 1880, .88, look=-.6, lean=2 * math.sin(u * 1.2),
                  rim=(255, 190, 140), rim_dir=(-1, -.3))
    snow_particles(img, 63, n=(50, 20, 6), wind=(5, 1), t=u)
    sx, sy = shake(u, t_rust, 10)
    img = finish(img, u, 1.03 + .05 * smooth(u / D), 520, 1100, dx=-cam * 1.05 + sx, dy=sy)
    return img, {'faces': [face_box(g)], 'avoid': [(0, 1480, W, 1640)]}


# ---------------------------------------------------------------- s14b: like a wet nail turning orange
def s14b(u, D, cue):
    img = Image.new('RGBA', (W, H))
    t_nail, t_orange = cue(18) - .1, cue(20) - .1
    tl = u * 2.2                                                          # timelapse: day/night light cycles fast
    day = .5 + .5 * math.sin(tl * 2 * math.pi)
    img.paste(vgrad([(0, lerp((60, 56, 70), (196, 180, 160), day)), (.55, lerp((70, 60, 66), (220, 200, 176), day)), (.56, (120, 80, 50)), (1, (70, 44, 30))]))
    d = ImageDraw.Draw(img)
    for k in range(9):                                                    # wood grain
        y0 = 1090 + k * 95
        d.line([(x, y0 + 10 * math.sin(x / 140 + k)) for x in range(-20, W + 21, 20)], fill=(96, 62, 40), width=4)
    d.line([(0, 1075), (W, 1075)], fill=INK, width=8)
    wx0, wy0, wx1, wy1 = 90, 180, 470, 700                               # window: the sky flicks day/night
    d.rounded_rectangle([wx0 - 16, wy0 - 16, wx1 + 16, wy1 + 16], 16, fill=(90, 66, 48), outline=INK, width=6)
    d.rectangle([wx0, wy0, wx1, wy1], fill=lerp((20, 26, 60), (150, 196, 240), day))
    if day > .5: radial(img, 300, 330, 120, (255, 236, 170), .8 * (day - .5) * 2)
    else: [d.ellipse([wx0 + 40 + i * 70, wy0 + 50 + (i * 53) % 200, wx0 + 46 + i * 70, wy0 + 56 + (i * 53) % 200], fill='white') for i in range(5)]
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(90, 66, 48), width=14); d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(90, 66, 48), width=14)
    d.rectangle([600, 560, 1040, 584], fill=(120, 84, 56), outline=INK, width=5)                       # shelf with jars
    for i, (c_, h_) in enumerate((((200, 120, 60), 120), ((90, 140, 200), 90), ((180, 60, 50), 140))):
        props.flask(img, 680 + i * 130, 560, h_, c_, 'bottle', glow_on=False)
    d = ImageDraw.Draw(img)
    radial(img, 540, 1090, 520, (255, 210, 150), .22 + .2 * (1 - day))                               # lamp pool at night
    # window light sweeps across with the timelapse
    sx_ = 540 + 500 * math.sin(tl * 2 * math.pi - 1)
    radial(img, sx_, 1300, 600, (255, 230, 180), .35 * day)
    # the nail: grey steel -> orange rust with spreading patches
    k = smooth(seg(u, .15, t_orange + .25))
    ang = -18; c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    P = lambda x, y: (540 + 1.25 * (x * c - y * s_), 1330 + 1.25 * (x * s_ + y * c))
    contact_shadow(img, 560, 1420, 900, (40, 20, 10), .5)
    pm = mask(); ImageDraw.Draw(pm).ellipse([200, 1330, 900, 1480], fill=255)          # water puddle under the nail
    fill_mask(img, pm, (150, 190, 210), .45 * (1 - .5 * smooth(u / D)), blur=6)
    gx, gy0 = 860, 1100                                                    # a glass of water behind it
    d.polygon([(gx - 80, gy0 - 300), (gx + 80, gy0 - 300), (gx + 64, gy0), (gx - 64, gy0)], fill=(210, 232, 244), outline=INK)
    d.polygon([(gx - 74, gy0 - 200 + 6 * math.sin(u * 4)), (gx + 74, gy0 - 200 - 6 * math.sin(u * 4)), (gx + 64, gy0), (gx - 64, gy0)], fill=(150, 200, 230))
    d.line([(gx - 80, gy0 - 300), (gx - 64, gy0), (gx + 64, gy0), (gx + 80, gy0 - 300)], fill=INK, width=7)
    d.line([(gx - 50, gy0 - 270), (gx - 42, gy0 - 30)], fill='white', width=8)
    steel, rustc = (170, 176, 186), (214, 96, 36)
    col = lerp(steel, rustc, k)
    shaft = [P(-330, -22), P(300, -22), P(380, 0), P(300, 22), P(-330, 22)]
    d.polygon(shaft, fill=col, outline=INK); d.line(shaft + [shaft[0]], fill=INK, width=8)
    head = [P(-360, -70), P(-320, -70), P(-320, 70), P(-360, 70)]
    d.polygon(head, fill=lerp(col, (0, 0, 0), .1)); d.line(head + [head[0]], fill=INK, width=8)
    d.line([P(-300, -10), P(260, -10)], fill=lerp((236, 240, 246), (255, 180, 120), k), width=6)
    rng = np.random.default_rng(3)
    for i in range(16):                                                   # rust patches spread
        x = rng.uniform(-300, 300); y = rng.uniform(-14, 14); r = (8 + 22 * rng.uniform()) * smooth(seg(k, rng.uniform(0, .5), 1))
        if r > 1: px, py = P(x, y); d.ellipse([px - r, py - r * .6, px + r, py + r * .6], fill=lerp((190, 70, 24), (140, 50, 20), rng.uniform()))
    for i, (x, y, q) in enumerate(((-200, -30, 22), (40, -28, 18), (220, -26, 16))):  # water drops shrink (evaporate)
        q *= 1 - .7 * smooth(seg(u, .3 + i * .1, D)); px, py = P(x, y - q)
        if q > 2:
            d.ellipse([px - q, py - q, px + q, py + q], fill=(200, 230, 250), outline=INK, width=3)
            d.ellipse([px - q * .4, py - q * .5, px, py - q * .1], fill='white')
    # timelapse clock chip
    lay = layer(360, 140); dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle([4, 4, 356, 136], 40, fill=(30, 30, 44), outline=(240, 240, 240), width=5)
    cx_, cy_ = 70, 70; dl.ellipse([cx_ - 42, cy_ - 42, cx_ + 42, cy_ + 42], fill='white', outline=INK, width=5)
    for a, L, w_ in ((tl * 2 * math.pi, 34, 6), (tl * 2 * math.pi / 12, 22, 9)):
        dl.line([(cx_, cy_), (cx_ + L * math.sin(a), cy_ - L * math.cos(a))], fill=INK, width=w_)
    dl.text((236, 72), 'DAYS', font=font(52), fill='white', anchor='mm')
    anim.scaled_paste(img, lay, 800, 300, pop(u, .05, .3, 1.6))
    put_chip(img, 'WET NAIL', (90, 100, 120), 300, 820, pop(u, t_nail, .3, 1.8), size=56, angle=-3)
    img = finish(img, u, 1.05 + .08 * smooth(u / D), 540, 1330, vig=(.4, (20, 10, 6)))
    return img, {'faces': [], 'avoid': [(0, 1180, W, 1460)]}


# ---------------------------------------------------------------- s15: not bleeding, rusting
def s15(u, D, cue):
    img = Image.new('RGBA', (W, H))
    cam = anim.lerp(-12, 12, smooth(u / D))
    backdrop(img, u + 2, cam, [(0, (52, 36, 104)), (.24, (150, 76, 130)), (.42, (250, 140, 110)), (.5, (255, 190, 130))],
             (220, 820, (255, 170, 110)), ((214, 150, 170), (150, 100, 150), (255, 226, 220)),
             ((180, 130, 170), (110, 80, 140), (255, 236, 236)), (255, 200, 170), horizon=860)
    top = lambda x: 830 + 24 * math.sin(x / 90) + (x - 540) ** 2 / 9000
    ice_cliff(img, -20, W + 20, top, lambda x: 1200, seed=12, lit=(250, 230, 236), mid=(214, 196, 220), shade=(160, 140, 196),
              deep=(96, 80, 150), snow=(255, 246, 246))
    haze(img, 1150, 1250, (255, 220, 214), .5 + .05 * math.sin(u))
    left, right = sf.blood_falls(img, 520, 850, 1210, w=84, color=(206, 76, 30), hi=(248, 134, 52), rust=True, t=u * 1.6)
    snow_ground(img, lambda x: 1210 + 10 * math.sin(x / 120), color=(238, 222, 234), shade=(196, 170, 204), seed=9)
    d = ImageDraw.Draw(img); ax = left[-1][0] + 40
    for k, (w_, h_, c) in enumerate(((760, 120, (150, 60, 30)), (580, 92, (200, 86, 34)), (400, 66, (234, 118, 44)), (240, 42, (255, 162, 70)))):
        ay = 1212 + k * 3
        d.chord([ax - w_ / 2, ay - h_ * .4, ax + w_ / 2, ay + h_], 180, 360, fill=INK)
        d.chord([ax - w_ / 2 + 6, ay - h_ * .4 + 6, ax + w_ / 2 - 6, ay + h_ - 6], 180, 360, fill=c)
    sf.red_fan(img, (ax, 1222), (760, 44), color=(196, 74, 26), edge=(244, 136, 56))
    falls_glow(img, ax, 1230, u, r=360, a=.2)
    # O2 bubbles drift down into the stream and turn orange on contact (loop)
    for i, (x0, y0, q) in enumerate(((300, 650, 50), (760, 640, 56), (680, 900, 40))):
        v = (u * .35 + i * .33) % 1
        x = x0 + (ax - 40 - x0) * smooth(v); y = y0 + (1000 - y0) * smooth(v)
        o2(d, x, y, q * (1 - .4 * v), fill=lerp((150, 210, 255), (255, 160, 70), smooth(seg(v, .6, .95))))
    radial(img, 140, 1500, 700, (255, 196, 160), .22)
    for k in range(6):
        y0 = 1430 + k * 80; x0 = 300 + (k % 2) * 160
        pts = [(x0 + v * 14, y0 + 10 * math.sin(v / 3 + k)) for v in range(0, 34)]
        d.line(pts, fill=(214, 186, 214), width=5); d.line([(x, y + 6) for x, y in pts], fill=(255, 250, 250), width=3)
    props.footprints(img, [(900 - i * 60, 1880 - i * 38) for i in range(5)], s=1.0)
    rocks(img, 17, [(470, 1880, 46), (690, 1900, 34)], lit=(170, 110, 100), shade=(104, 64, 80))
    t_not, t_rust = cue(2) - .1, cue(5) - .1
    gpose = chain(u, [(0, dict(POSES['think'], _name='think', _sh=(278, 322))), (t_rust - .2, dict(STAND, _name='think', _sh=(300, 300))),
                      (t_rust + .2, add(STAND, armR=(-60, -70)), lambda f: out_back(f, 1.6))])
    g1 = geologist(img, u, gpose, 'determined' if u < t_rust else 'surprised', 205, 1890, .9, look=.4, rim=(255, 190, 140), rim_dir=(1, -.3), bphase=.4)
    up = dict(armL=(128, 142), armR=(-24, -10), legL=(11, 1), legR=(-11, -1))
    spose = chain(u, [(0, STAND), (t_not - .2, add(STAND, armL=(-10, -12))), (t_not + .25, up, lambda f: out_back(f, 1.7))])
    g2 = scientist(img, u, spose, 'surprised', 875, 1890, .9, look=-.4, rim=(255, 190, 140), rim_dir=(-1, -.3))
    snow_particles(img, 19, n=(60, 24, 8), wind=(5, 1), t=u)
    img = finish(img, u, 1.04 + .04 * smooth(u / D), 540, 1200, dx=-cam * 1.05, vig=(.36, (30, 10, 40)))
    slam_title(img, 's15a', [('NOT BLEEDING.', 'white', 104)], 150, u, t_not)
    slam_title(img, 's15b', [('RUSTING.', (255, 128, 44), 150)], 266, u, t_rust)
    put_chip(img, 'IRON + OXYGEN = RUST', (206, 84, 30), 560, 1290, pop(u, t_rust + .25, .3, 1.8), size=40)
    return img, {'faces': [face_box(g1), face_box(g2)], 'avoid': [(0, 1240, W, 1460)]}


# ---------------------------------------------------------------- s16a: the algae never was; a sealed world of microbes
def microbe_world(img, u):
    img.paste(vgrad([(0, (6, 20, 40)), (.5, (10, 54, 66)), (1, (6, 18, 30))]))
    d = ImageDraw.Draw(img)
    xs = np.arange(-20, W + 21, 20)
    ceil = [(x, 300 + 30 * math.sin(x / 100) + 12 * math.sin(x / 31)) for x in xs]
    d.polygon([(-20, -10), (W + 20, -10)] + ceil[::-1], fill=(150, 200, 236))
    for k in range(4): d.line([(x, 60 + k * 60 + 10 * math.sin(x / 110 + k)) for x in xs], fill=(110, 170, 220), width=4)
    d.line(ceil, fill=INK, width=6)
    radial(img, 540, 1000, 900, TEAL, .35 + .05 * math.sin(u * 2))
    light_rays(img, 540, 280, (150, 255, 230), n=7, alpha=.14, spread=(55, 125), length=1600, seed=6, phase=3 * math.sin(u * .5))
    floor = [(x, 1700 + 24 * math.sin(x / 130) + 10 * math.sin(x / 37)) for x in xs]
    d.polygon(floor + [(W + 20, H + 10), (-20, H + 10)], fill=(70, 56, 80)); d.line(floor, fill=INK, width=6)
    for k in range(3): d.line([(x, 1780 + k * 50 + 12 * math.sin(x / 90 + k)) for x in xs], fill=(100, 80, 110), width=5)
    rocks(img, 51, [(140, 1760, 50), (900, 1770, 60)], lit=(120, 100, 130), shade=(70, 56, 80), snow=(120, 100, 130))
    bubbles(img, 300, 1690, 1300, u * .5, seed=7, n=7, color=(200, 255, 240))
    dust(img, 21, 80, (0, 320, W, H), (160, 255, 230), 140, size=(2, 6), t=u)
    rng = np.random.default_rng(16)
    for i in range(16):
        x = rng.uniform(80, W - 80) + 30 * math.sin(u * .6 + i); y = rng.uniform(480, 1800) + 20 * math.cos(u * .5 + i)
        microbe(img, x, y, rng.uniform(18, 34), u, 90 + i, 1.0, [(120, 240, 170), (110, 220, 250), (250, 200, 110)][i % 3])
    for i in range(30):                                                   # iron specks
        x = (rng.uniform(0, W) + 20 * u) % W; y = rng.uniform(400, 1850) + 10 * math.sin(u + i)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(240, 130, 70))


def s16a(u, D, cue):
    t_never, t_just, t_sealed = cue(4) - .1, cue(6) - .25, cue(8) - .1
    cam = anim.lerp(-10, 10, smooth(u / D))
    img = Image.new('RGBA', (W, H))
    B.falls_close(img, u + 9, cam)
    sf.red_fan(img, (600, 1408), (620, 250), seed=8)
    falls_glow(img, 600, 1420, u, r=420, a=.2)
    mist(img, 4, (480, 1280, 820, 1440), u, n=30)
    # the RED ALGAE bubble from s04 floats in, hangs, then pops on "Never"
    if u < t_never + .02:
        s = pop(u, .0, .35, 1.6)
        speech_bubble(img, 540, 760 + 14 * math.sin(u * 2), 240, (420, 1060), s, u)
    else:
        v = u - t_never
        if v < .6:                                                        # burst: ring + scattering algae cells
            r = 200 + 420 * ease_out(v / .6); m = mask(); ImageDraw.Draw(m).ellipse([540 - r, 760 - r * .7, 540 + r, 760 + r * .7], outline=255, width=int(18 * (1 - v / .6)) + 2)
            glow(img, m, (255, 250, 240), .9 * (1 - v / .6), blur=3, add=True)
            d = ImageDraw.Draw(img); rng = np.random.default_rng(9)
            for i in range(12):
                a = rng.uniform(0, 2 * math.pi); sp = rng.uniform(300, 700); q = 26 * (1 - v / .6)
                x = 540 + math.cos(a) * sp * v; y = 760 + math.sin(a) * sp * v + 500 * v * v
                if q > 2: d.ellipse([x - q, y - q, x + q, y + q], fill=(200, 50, 60), outline=INK, width=3)
        put_chip(img, 'NEVER THERE', (180, 30, 40), 540, 760, pop(u, t_never + .1, .3, 1.9) * (1 - smooth(seg(u, t_just - .1, t_just + .1))), size=72, angle=-4)
    snow_particles(img, 81, n=(60, 26, 8), wind=(5, 1), t=u)
    z = 1.05 + .06 * smooth(seg(u, 0, t_just)) + .5 * ease_in(seg(u, t_just, t_just + .45))
    img = finish(img, u, z, 600, 1380, dx=-cam * 1.05)
    # dive under the ice: an iris opens from the foot of the falls onto the sealed world of microbes
    k = ease_out(seg(u, t_just, t_just + .5))
    if k > 0:
        world = Image.new('RGBA', (W, H)); microbe_world(world, u)
        world = anim.camera(world, 1.25 - .17 * smooth(seg(u, t_just, D)), 540, 1000)
        r = 1400 * k; m = mask(); ImageDraw.Draw(m).ellipse([540 - r, 1100 - r, 540 + r, 1100 + r], fill=255)
        img.paste(world, (0, 0), m)
        if k < 1:
            ImageDraw.Draw(img).ellipse([540 - r, 1100 - r, 540 + r, 1100 + r], outline=(170, 255, 236), width=14)
        anim.vignette(img, .4, (2, 8, 16))
        put_chip(img, 'SEALED WORLD', (14, 110, 110), 540, 560, pop(u, t_sealed, .3, 1.8), size=64, angle=2 * math.sin(u * 2))
    return img, {'faces': [], 'avoid': [(0, 480, W, 640)] if k > 0 else [(0, 480, W, 1080)]}


# ---------------------------------------------------------------- s16b: loop back to the s01 framing (1911)
def s16b(u, D, cue):
    """Back to the s01 set: the 1911 geologist stands where s01 left him, pointing at the falls. The camera
    eases to s01's opening framing (cam -16, zoom 1.05), so the restart reads as the same place."""
    img = Image.new('RGBA', (W, H))
    k = smooth(u / D)
    cam = anim.lerp(10, -16, k)
    B.s01_world(img, u + 30, D, cam, grow=1.0)
    t_like = cue(17) - .1
    point = dict(POSES['point'])
    pose = add(point, armR=(3 * math.sin(u * 2.5), 5 * math.sin(u * 2.5 - .6)))
    g = geologist(img, u, pose, 'determined' if u < t_like else 'surprised', 430, 1800, .98, look=.35 + .1 * math.sin(u * .8), lean=1.2 * math.sin(u * 1.3))
    fx = cam * -.6
    foreground_frame(img, [[(820 + fx, 1940), (900 + fx, 1830), (1010 + fx, 1790), (1100 + fx, 1820), (1100 + fx, 1940)]], color=(150, 170, 214), alpha=.9)
    snow_particles(img, 9, n=(80, 36, 12), wind=(5, 1), t=u + 40)
    # a sepia "1911" memory grade rises on "like in 1911" and clears again before the loop
    sep = math.sin(math.pi * seg(u, t_like - .2, D - .1)) * .22
    if sep > .01:
        m = mask(); m.paste(255, (0, 0, W, H)); fill_mask(img, m, (150, 110, 60), sep)
    img = finish(img, u, anim.lerp(1.16, 1.05, k), anim.lerp(640, 700, k), 1250, dx=-cam * 1.05)
    put_chip(img, '1911', (52, 112, 222), 800, 600, pop(u, cue(19) - .1, .3, 1.9) * (1 - smooth(seg(u, D - .45, D - .1))), size=96, angle=-3)
    return img, {'faces': [face_box(g)], 'avoid': [(0, 1000, W, 1470)]}


B.SHOTS.update({'s07': s07, 's08': s08, 's09': s09, 's10': s10, 's11a': s11a, 's11b': s11b, 's12': s12, 's13': s13,
                's14a': s14a, 's14b': s14b, 's15': s15, 's16a': s16a, 's16b': s16b})
# (shot, voice-over line, first word of the line in this shot)
SHOT_LIST = [('s01', 1, 0), ('s02', 2, 0), ('s03', 3, 0), ('s04', 4, 0), ('s05', 5, 0), ('s06', 6, 0), ('s07', 7, 0),
             ('s08', 8, 0), ('s09', 9, 0), ('s10', 10, 0), ('s11a', 11, 0), ('s11b', 11, 13), ('s12', 12, 0), ('s13', 13, 0),
             ('s14a', 14, 0), ('s14b', 14, 15), ('s15', 15, 0), ('s16a', 16, 0), ('s16b', 16, 12)]
END = 65.5
# still for the review gate: the fraction of each shot where its main beat has landed
STILL_AT = {'s01': .92, 's04': .95, 's05': .97, 's07': .97, 's08': .93, 's12': .95, 's13': .6, 's14a': .97, 's15': .97, 's16a': .9}                     # 1965 frames; with the 0.1 s cover the posted cut is 65.6 s

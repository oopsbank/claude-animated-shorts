"""The Bloop (video 5, "The Sound From the Deep"): shots s01-s14b as `sNN(u, D, cue) -> (img, info)`.

Same contract as tunguska.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the
shot's voice-over LINE. info: 'faces' (face boxes; render.py adds body boxes) and 'avoid' (boxes the caption
must not cover). Every shot keeps moving (waves, sound rings, particles, glow pulses, camera drift, characters
breathing and blinking). Serious mystery, no comedy. The sea monster is only ever an online post or a
question mark, never a fact.

Render: .venv/bin/python flat2d/render.py audio/bloop/words.json OUT.mp4 --film bloop
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import kit, props, anim
import ocean as O
from kit import (W, H, INK, vgrad, radial, cloud_bands, haze, peak_range, dust, label, title, pill, font, mask, glow,
                 fill_mask, layer, lerp, rgb)
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES
from blood_falls import finish, slam_title, face_box
from blood_falls_2 import put_chip, draw_x, stars
import tunguska as TG
from tunguska import chip_t, flash

SLUG = 'bloop'
SONAR = (30, 150, 178)                 # the scientist's label colour
SCI_KW = dict(shirt='#2f5d7c', pants='#33384a')
RED = O.RED
HIDE_UI = False                 # thumbnail frames: no chips or titles


def clue(img, txt, u, t0=.05, y=250):
    TG.clue(img, txt, u, t0, y)


def scientist(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, rim=(150, 220, 255), rim_dir=(-.5, -1),
              bphase=.3, aura=(40, 170, 200), aura_a=.45, cups=(220, 60, 60), phones=True, lbl_dy=0):
    """SCIENTIST: white stickman, navy sweater, over-ear headphones (identity item)."""
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=aura, aura_alpha=aura_a, rim=rim, rim_dir=rim_dir,
              bphase=bphase, **SCI_KW)
    if phones: O.headphones(img, g['head'], g['R'], cup=cups, look=look)
    if label_on:
        hx, hy = g['head']
        label(img, 'SCIENTIST', min(W - 180, max(180, hx)), hy - g['R'] * 1.5 - 92 + lbl_dy, SONAR, size=int(48 * max(.9, min(1.1, s))))
    return g


def faces_of(g, pad=1.25):
    return face_box(g, pad)


# ---------------------------------------------------------------- s01: the sound crosses the Pacific (line 1)
SRC = (560, 1560)                    # where the sound starts (deep, toward the south)
STA = ((170, 1160), (930, 1080))     # the two listening stations


def s01_world(u, cam=0.0):
    """The opening framing (also the loop frame): a dark ocean cross-section, two stations far apart, a red
    sound pulse train already spreading at frame 0."""
    img = Image.new('RGBA', (W, H))
    surf = O.ocean_section(img, u, surface=640, floor=1790, sky=((10, 14, 40), (40, 46, 96)),
                           water=((24, 70, 120), (10, 30, 74), (4, 8, 26)), cam=cam, seed=3)
    lay = layer(); stars(lay, 5, 60, 600, u); img.alpha_composite(lay)
    cloud_bands(img, 8, 380, 600, (90, 100, 170), .3, n=4, drift=u * 8)
    O.depth_ruler(img, 40, surf, 270, a=150)
    # the pulse train: emitted from well before frame 0, so the opening is already in motion
    O.pulse_train(img, SRC[0], SRC[1], u, t0=-6.0, every=.9, speed=300, n=30, w=20, clip=(surf + 14, 1800), rmax=1900, fade=1500)
    radial(img, SRC[0], SRC[1], 260, (255, 90, 70), .55 + .12 * math.sin(u * 5))
    radial(img, SRC[0], SRC[1], 90, (255, 200, 170), .7)
    for i, (x, y) in enumerate(STA):
        r = math.hypot(x - SRC[0], y - SRC[1]); hit = []
        for j in range(30):
            te = -6.0 + j * .9 + r / 300
            if te <= u: hit.append(u - te)
        lit = max([max(0.0, 1 - v / .8) for v in hit] + [0.0])
        O.hydrophone(img, x + cam * .1, y, 1800, u, lit=lit, s=1.25, phase=i)
    return img, surf


def s01(u, D, cue):
    cam = 10 * math.sin(u * .4)
    img, surf = s01_world(u, cam)
    k = smooth(seg(u, cue(12) - .2, cue(12) + .4))                      # "five thousand kilometres": the span
    d = ImageDraw.Draw(img)
    if k > 0:
        (x0, y0), (x1, y1) = STA; yb = 900
        xa, xb = 540 - (540 - x0) * k, 540 + (x1 - 540) * k
        d.line([(xa, yb), (xb, yb)], fill=INK, width=14); d.line([(xa, yb), (xb, yb)], fill=(255, 236, 180), width=6)
        for xx, yy in ((xa, y0), (xb, y1)):
            d.line([(xx, yb - 26), (xx, yb + 26)], fill=(255, 236, 180), width=6)
            TG_dash(d, (xx, yb + 26), (xx, yy - 110), (255, 236, 180))
    img = finish(img, u, 1.03 + .03 * math.sin(u * .5), 540, 1100, vig=(.45, (4, 6, 20)))
    chip_t(img, '1997 · PACIFIC OCEAN', (40, 70, 130), 540, 140, u, .15 if u > -1 else 99, size=52)
    slam_title(img, 's01_t', [('A SOUND', 'white', 112), ('FROM THE DEEP', RED, 104)], 260, u, cue(7) - .12)
    if k > 0: put_chip(img, '4,800 KM APART', (200, 60, 50), 540, 900, pop(u, cue(12) + .1, .3, 2.0), size=54)
    return img, {'faces': [], 'avoid': [(0, 100, W, 560), (100, 840, 980, 960)]}


def TG_dash(d, a, b, col, w=5):
    import taiga
    taiga.dashed(d, a, b, col, w=w, dash=18, gap=14)


# ---------------------------------------------------------------- listening room (s02, s14b)
SCREEN = (560, 300, 1020, 1118)       # the tall sonar display (9:16 so the loop can zoom into it)


def room(img, u, cam=0.0, warm=1.0, dark=0.0):
    """The listening room: dark walls, a rack of glowing equipment, a cable run, a desk with a console.
    Moves: rack LEDs blink, a lamp pool breathes, dust drifts in the light."""
    img.paste(vgrad([(0, lerp((22, 34, 44), (8, 12, 22), dark)), (.7, lerp((36, 52, 62), (14, 20, 34), dark)), (1, (18, 24, 30))]))
    radial(img, 300 + cam * .6, 700, 700, lerp((80, 150, 170), (40, 70, 120), dark), .35)
    d = ImageDraw.Draw(img)
    for i in range(5):                                                   # wall panels
        x = -40 + i * 260 + cam * .5
        d.rectangle([x, 120, x + 230, 1300], outline=lerp((40, 60, 72), (20, 28, 44), dark), width=4)
    # equipment rack (left)
    rx = 40 + cam * .7
    d.rectangle([rx, 360, rx + 330, 1360], fill=(26, 30, 38), outline=INK, width=8)
    for j in range(8):
        y = 390 + j * 118
        d.rectangle([rx + 20, y, rx + 310, y + 96], fill=(42, 48, 60), outline=INK, width=4)
        for q in range(5):
            on = math.sin(u * (2 + q * .7) + j * 1.3 + q) > -.2
            c = [(80, 240, 140), (255, 180, 60), (90, 200, 255)][(j + q) % 3]
            d.ellipse([rx + 40 + q * 26, y + 20, rx + 54 + q * 26, y + 34], fill=c if on else (40, 44, 50))
        lv = .5 + .45 * math.sin(u * 3 + j)
        d.rectangle([rx + 180, y + 56, rx + 180 + 110 * lv, y + 74], fill=(90, 200, 255))
    radial(img, rx + 160, 800, 300, (90, 200, 255), .12)
    return img


def screen_frame(img, box, content=None, glow_col=(90, 200, 255)):
    x0, y0, x1, y1 = box
    m = mask(); ImageDraw.Draw(m).rectangle([x0 - 10, y0 - 10, x1 + 10, y1 + 10], fill=255)
    glow(img, m, glow_col, .45, blur=50)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0 - 26, y0 - 26, x1 + 26, y1 + 26], 18, fill=(30, 32, 40), outline=INK, width=8)
    if content is not None: img.paste(content.convert('RGB').resize((x1 - x0, y1 - y0), Image.BILINEAR), (x0, y0))
    else: d.rectangle([x0, y0, x1, y1], fill=(8, 22, 26))
    d.rectangle([x0, y0, x1, y1], outline=INK, width=5)


def desk(img, cam, y=1380, top=(70, 56, 50), front=(44, 36, 34)):
    d = ImageDraw.Draw(img)
    d.polygon([(-40, y), (W + 40, y), (W + 40, y + 70), (-40, y + 70)], fill=top, outline=INK)
    d.rectangle([-40, y + 70, W + 40, H], fill=front)
    d.line([(-40, y), (W + 40, y)], fill=INK, width=8); d.line([(-40, y + 70), (W + 40, y + 70)], fill=INK, width=6)


def console(img, x, y, u, cam=0.0):
    d = ImageDraw.Draw(img); x += cam
    d.polygon([(x - 260, y), (x + 260, y), (x + 220, y - 90), (x - 220, y - 90)], fill=(56, 62, 76), outline=INK, width=6)
    for i in range(8):
        lv = .5 + .5 * math.sin(u * 2 + i * .8)
        d.rectangle([x - 200 + i * 52, y - 70, x - 176 + i * 52, y - 20], fill=(30, 34, 44))
        d.rectangle([x - 200 + i * 52, y - 20 - 50 * lv, x - 176 + i * 52, y - 20], fill=(90, 220, 160) if i < 6 else (255, 120, 80))


def pitch_trace(x):
    """The Bloop on the display: a call that rises in pitch."""
    return -.7 + 1.5 * x ** 1.6 + .08 * math.sin(x * 60) * (.4 + x)


def s02(u, D, cue):
    """Line 2: the scientist hears it rise in pitch; a VOLUME chart where the Bloop tops every animal."""
    img = Image.new('RGBA', (W, H)); cam = -16 * smooth(u / D)
    room(img, u, cam)
    # display: a spectrogram-ish screen: pitch rising (draws during "rose in pitch like an animal call")
    sc = layer(460, 818); ds = ImageDraw.Draw(sc)
    ds.rectangle([0, 0, 460, 818], fill=(6, 20, 26))
    for j in range(9): ds.line([(0, j * 100 + 9), (460, j * 100 + 9)], fill=(18, 54, 60), width=2)
    for j in range(5): ds.line([(j * 100 + 30, 0), (j * 100 + 30, 818)], fill=(18, 54, 60), width=2)
    kp = smooth(seg(u, cue(2) - .4, cue(9) + .3))
    O.waveform(sc, (30, 120, 440, 520), pitch_trace, max(.02, kp), col=(255, 110, 90), w=8)
    ds = ImageDraw.Draw(sc); f = font(34, True)
    ds.text((30, 40), 'PITCH', font=f, fill=(140, 230, 220))
    if kp > .3:
        ds.polygon([(400, 60), (420, 30), (440, 60)], fill=(255, 110, 90)); ds.rectangle([414, 60, 426, 100], fill=(255, 110, 90))
    # VOLUME bars on the lower part of the screen
    ds.text((30, 560), 'VOLUME', font=f, fill=(140, 230, 220))
    kv = smooth(seg(u, cue(10) - .2, cue(16)))
    bars = [('ANIMALS', .45, (120, 160, 170)), ('BLOOP', 1.0, (255, 80, 60))]
    for i, (nm, lv, c) in enumerate(bars):
        y = 640 + i * 90; L = 400 * lv * (kv if nm == 'BLOOP' else min(1, kv * 2.5))
        if nm == 'BLOOP' and kv > .9: L += 8 * math.sin(u * 20)
        ds.rectangle([30, y, 30 + max(4, L), y + 56], fill=c)
        ds.text((40, y + 28), nm, font=font(30, True), fill=(10, 14, 20), anchor='lm')
    ds.line([(210, 610), (210, 800)], fill=(255, 255, 255), width=3)     # the loudest animal mark
    screen_frame(img, (SCREEN[0] + int(cam), SCREEN[1], SCREEN[2] + int(cam), SCREEN[1] + 818), sc)
    desk(img, cam)
    console(img, 760, 1390, u, cam)
    # scientist at the desk: leans in, then jolts back on "rose", a hand to the headphones
    tj = cue(3) - .05
    hop = 26 * math.exp(-max(0, u - tj) * 5) * math.sin(max(0, u - tj) * 14) if u > tj else 0
    pose = anim.mix(POSES['think'], dict(POSES['stand'], armR=(-100, -170)), smooth(seg(u, tj, tj + .25)))
    expr = 'surprised' if u > tj else 'thinking'
    g = scientist(img, u, pose, expr, 300 + cam * .9, 1560, .64, look=.45, lean=-4 * smooth(seg(u, tj, tj + .3)) + 3,
                  hop=max(0, hop))
    d = ImageDraw.Draw(img)                                               # cable from the headphones to the console
    hx, hy = g['head']; R = g['R']
    d.line([(hx + R, hy + R * .4), (hx + R * 1.6, hy + R * 3), (620 + cam, 1330)], fill=INK, width=9, joint='curve')
    d.line([(hx + R, hy + R * .4), (hx + R * 1.6, hy + R * 3), (620 + cam, 1330)], fill=(60, 64, 80), width=4, joint='curve')
    dust(img, 2, 30, (0, 300, W, 1400), (180, 230, 255), 110, size=(2, 5), t=u)
    sx, sy = shake(u, tj, 6, .3)
    img = finish(img, u, 1.04 + .03 * smooth(u / D), 540, 900, dx=sx, dy=sy, vig=(.45, (6, 10, 20)))
    if HIDE_UI: return img, {'faces': [faces_of(g)], 'avoid': []}
    chip_t(img, 'LIKE AN ANIMAL CALL', (40, 120, 140), 540, 190, u, cue(6) - .1, size=50)
    slam_title(img, 's02_t', [('TOO LOUD', RED, 110)], 1700, u, cue(15) - .1)
    return img, {'faces': [faces_of(g)], 'avoid': [(0, 150, W, 240), (0, 1650, W, 1820)]}


# ---------------------------------------------------------------- s03: BLOOP; the internet's answer (line 3)
def phone_post(u, kpost, kq, likes):
    """A social post (speculation): a dark-water photo with a giant vague silhouette, UNVERIFIED tag, a quote."""
    P = layer(640, 1060); d = ImageDraw.Draw(P)
    d.rounded_rectangle([0, 0, 640, 1060], 70, fill=INK)
    d.rounded_rectangle([18, 18, 622, 1042], 56, fill=(24, 24, 32))
    d.rounded_rectangle([250, 34, 390, 56], 11, fill=INK)
    f = font(30, True); fs = font(26, False)
    d.ellipse([46, 90, 106, 150], fill=(150, 90, 220), outline=INK, width=3)
    d.text((122, 100), 'deepseafan_99', font=f, fill='white'); d.text((122, 134), 'online theory', font=fs, fill=(150, 150, 170))
    # the photo: murky water with a vague shape
    ph = Image.new('RGBA', (580, 560))
    ph.paste(vgrad([(0, (30, 70, 90)), (1, (4, 10, 20))], w=580, h=560))
    O.sea_shadow(ph, 290 + 10 * math.sin(u), 250 + 8 * math.sin(u * .8), .55, u, col=(0, 0, 0), alpha=.75 * kpost, eye=kpost, blur=10)
    kit.dust(ph, 1, 40, (0, 0, 580, 560), (180, 220, 230), 100, size=(2, 4), t=u)
    P.alpha_composite(ph, (30, 180))
    d = ImageDraw.Draw(P)
    d.rectangle([30, 180, 610, 740], outline=INK, width=4)
    # big "?" over the shape and an UNVERIFIED tag: speculation, not a fact
    if kq > 0:
        tl, _ = anim.text_layer(lambda l: title(l, [('?', (255, 210, 80), 200)], 60, size=200), 400, 400)
        anim.scaled_paste(P, tl, 470, 320, out_back(kq) * .9, angle=8)
    d = ImageDraw.Draw(P)
    d.rounded_rectangle([50, 200, 290, 250], 12, fill=(240, 200, 40), outline=INK, width=3)
    d.text((170, 225), 'UNVERIFIED', font=font(28, True), fill=INK, anchor='mm')
    d.text((46, 770), '"Something huge', font=font(44, True), fill='white')
    d.text((46, 830), ' is down there."', font=font(44, True), fill='white')
    d.text((46, 930), f'{likes:,} LIKES   {likes // 7:,} SHARES', font=font(32, True), fill=(255, 120, 140))
    return P


def s03(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 8 * math.sin(u * .5)
    surf = O.ocean_section(img, u, surface=520, floor=1850, sky=((40, 20, 60), (90, 50, 110)),
                           water=((60, 40, 110), (24, 16, 64), (8, 6, 24)), cam=cam, seed=9, rays=True)
    O.pulse_train(img, 540, 1700, u, t0=-4, every=.8, speed=320, n=14, w=16, clip=(surf + 12, 1850), fade=1300)
    tb = cue(4) - .1                                                     # "Bloop."
    flash(img, u, tb, .3, .6, (255, 200, 200))
    ti = cue(7) - .25                                                    # "internet": the phone slides up
    kp = ease_out(seg(u, ti, ti + .55))
    sx, sy = shake(u, tb, 12, .4)
    img = finish(img, u, 1.03 + .03 * smooth(u / D), 540, 1000, dx=sx, dy=sy, vig=(.45, (10, 4, 20)))
    chip_t(img, 'SCIENTISTS NICKNAMED IT', (90, 60, 140), 540, 150, u, .05, size=46)
    if u >= tb - .02:
        sc = slam(u, tb, .3, 1.5)
        tl = _bloop_title()
        anim.scaled_paste(img, tl[0], 540, 330 + 6 * math.sin(u * 3), sc * (1 + .02 * math.sin(u * 6)))
    if kp > 0:
        likes = int(1200 + 98000 * smooth(seg(u, ti, D)))
        P = phone_post(u, smooth(seg(u, ti + .2, ti + 1.0)), smooth(seg(u, cue(11) - .1, cue(11) + .3)), likes)
        y = 1900 + 500 - (1900 + 500 - 1170) * kp
        anim.scaled_paste(img, P, 540, y, .98, angle=-3 + 1.2 * math.sin(u * .9))
        d = ImageDraw.Draw(img)
        if u > cue(11) - .1:
            put_chip(img, 'THE INTERNET\'S GUESS', (150, 80, 200), 540, 560, pop(u, cue(11) - .1, .3, 2), size=46)
    return img, {'faces': [], 'avoid': [(0, 100, W, 600), (180, 620, 900, 1920)] if kp > 0 else [(0, 100, W, 600)]}


_bt = {}
def _bloop_title():
    if 'b' not in _bt:
        _bt['b'] = anim.text_layer(lambda l: title(l, [('"THE BLOOP"', RED, 150)], 60, size=150), W, 400)
    return _bt['b']


# ---------------------------------------------------------------- s04: not even a blue whale (line 4)
def s04(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -40 * u
    surf = O.ocean_section(img, u, surface=300, floor=1880, sky=((150, 200, 240), (200, 230, 250)),
                           water=((60, 170, 220), (24, 110, 180), (8, 44, 100)), cam=cam * .3, seed=12)
    # far school of fish for depth
    d = ImageDraw.Draw(img)
    for i in range(26):
        x = (i * 83 + u * 60) % (W + 200) - 100; y = 600 + 40 * math.sin(i * 1.7) + i % 3 * 30
        d.polygon([(x, y), (x - 26, y - 9), (x - 26, y + 9)], fill=(40, 120, 170)); d.polygon([(x - 26, y), (x - 38, y - 8), (x - 38, y + 8)], fill=(40, 120, 170))
    # the volume scale (right): BLOOP mark at the top, the whale bar rises and stops far below
    x0, yb, yt = 960, 1640, 560
    d.rounded_rectangle([x0 - 50, yt - 70, x0 + 50, yb + 20], 24, fill=(8, 28, 60), outline=INK, width=6)
    kw = smooth(seg(u, cue(6) - .1, cue(11)))
    lvl = yb - (yb - yt) * .42 * kw
    d.rectangle([x0 - 32, lvl, x0 + 32, yb], fill=(90, 160, 230))
    for j in range(10): d.line([(x0 - 50, yb - j * (yb - yt) / 9), (x0 - 30, yb - j * (yb - yt) / 9)], fill=(150, 200, 240), width=3)
    pls = .5 + .5 * math.sin(u * 6)
    d.line([(x0 - 90, yt), (x0 + 60, yt)], fill=INK, width=16); d.line([(x0 - 90, yt), (x0 + 60, yt)], fill=RED, width=8)
    radial(img, x0 - 20, yt, 160, RED, .4 + .2 * pls)
    # the whale crosses, singing (soft rings from its head)
    wx = 1000 - 560 * smooth(seg(u, -.6, D + .6)); wy = 1420 + 20 * math.sin(u * .9)
    O.pulse_train(img, wx - 310, wy - 20, u, t0=-2, every=.7, speed=260, n=12, w=8, col=(160, 230, 255), clip=(surf + 10, 1880), rmax=500, fade=500)
    O.blue_whale(img, wx, wy, .82, u, flip=True)
    kit.dust(img, 4, 50, (0, 320, W, 1880), (220, 240, 255), 140, size=(2, 6), t=u)
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 540, 1000, vig=(.35, (6, 20, 50)))
    slam_title(img, 's04_t', [('NO CREATURE FITS', 'white', 92)], 170, u, cue(2) - .05)
    chip_t(img, 'BLUE WHALE · LOUDEST ANIMAL', (40, 110, 190), 470, 880, u, cue(6) - .1, size=44)
    put_chip(img, 'BLOOP', (200, 50, 44), x0 - 20, yt - 100, pop(u, cue(4), .3, 2), size=46)
    kx = seg(u, cue(12) - .05, cue(12) + .45) * 2
    if kx > 0: draw_x(img, x0, lvl, 46, kx, w=16)
    return img, {'faces': [], 'avoid': [(0, 100, W, 280), (60, 830, 880, 930), (780, 400, 1040, 1700)]}


# ---------------------------------------------------------------- s05: CLUE 1, the bearings meet near Antarctica (line 5)
PAPER = (232, 222, 196); SEA_INK = (176, 204, 206); LAND = (226, 206, 160)
TARGET = (600, 1500)


def chart(img, u, cam=0.0):
    """A nautical chart of the Pacific: grid, the equator, coasts, Antarctica along the bottom."""
    img.paste(vgrad([(0, (196, 216, 214)), (1, (164, 196, 202))]))
    d = ImageDraw.Draw(img)
    for i in range(12): d.line([(i * 100 - 20, 0), (i * 100 - 20, H)], fill=(150, 182, 190), width=2)
    for j in range(20): d.line([(0, j * 100), (W, j * 100)], fill=(150, 182, 190), width=2)
    rng = np.random.default_rng(2)
    def coast(pts, fill):
        d.polygon(pts, fill=fill, outline=INK, width=6)
    # Australia + New Zealand (left), the Americas (right), Antarctica (bottom)
    coast([(-60, 760), (90, 790), (170, 880), (150, 1010), (60, 1080), (-60, 1060)], LAND)
    coast([(210, 1180), (250, 1150), (262, 1230), (232, 1290), (204, 1260)], LAND)
    coast([(1140, 120), (1000, 260), (950, 420), (1010, 600), (990, 820), (1040, 1000), (1020, 1180), (1060, 1300), (1140, 1320)], LAND)
    ant = [(-60, 1620)] + [(x, 1600 + 50 * math.sin(x * .012) + 30 * math.sin(x * .031)) for x in range(-60, 1160, 60)] + [(1160, 1620), (1160, H), (-60, H)]
    coast(ant, (246, 250, 252))
    for i in range(20):                                                  # ice shading on Antarctica
        x = rng.uniform(0, W); y = rng.uniform(1680, 1900); d.line([(x, y), (x + 80, y + 10)], fill=(200, 220, 236), width=4)
    import taiga
    taiga.dashed(d, (0, 560), (W, 560), (200, 80, 60), w=5, dash=26, gap=14)
    f = font(30, True)
    d.text((W - 30, 525), 'EQUATOR', font=f, fill=(200, 80, 60), anchor='rm')
    d.text((540, 1800), 'ANTARCTICA', font=font(54, True), fill=(60, 90, 130), anchor='mm')
    d.text((80, 930), 'AUSTRALIA', font=font(26, True), fill=(120, 90, 50), anchor='mm')
    d.text((540, 820), 'PACIFIC OCEAN', font=font(40, True), fill=(90, 130, 150), anchor='mm')
    # compass rose
    cx, cy = 880, 1420
    d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], outline=(110, 120, 120), width=4)
    d.polygon([(cx, cy - 90), (cx + 16, cy), (cx, cy + 90), (cx - 16, cy)], fill=(110, 120, 120))
    d.text((cx, cy - 110), 'N', font=font(30, True), fill=(110, 120, 120), anchor='mm')


ARRAY = [(260, 560), (430, 560), (620, 560), (800, 560)]


def s05(u, D, cue):
    img = Image.new('RGBA', (W, H))
    chart(img, u)
    d = ImageDraw.Draw(img)
    kb = smooth(seg(u, cue(3) - .2, cue(6) + .2))                         # bearings draw from the stations toward the source
    for i, (x, y) in enumerate(ARRAY):
        ex, ey = x + (TARGET[0] - x) * kb, y + (TARGET[1] - y) * kb
        import taiga
        if kb > .01: taiga.dashed(d, (x, y), (ex, ey), (200, 50, 44), w=7, dash=22, gap=12, phase=u * 40)
        lit = .5 + .5 * math.sin(u * 5 + i)
        radial(img, x, y, 70, RED, .5 * lit); d = ImageDraw.Draw(img)
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(250, 200, 60), outline=INK, width=6)
    put_chip(img, 'LISTENING STATIONS', (60, 100, 130), 540, 470, pop(u, .25, .3, 2), size=40)
    # the source near the edge of Antarctica pulses red
    kt = smooth(seg(u, cue(7) - .2, cue(9)))
    if kt > 0:
        O.pulse_train(img, TARGET[0], TARGET[1], u, t0=cue(7) - .2, every=.45, speed=420, n=8, w=12, rmax=700, fade=700)
        radial(img, TARGET[0], TARGET[1], 140, RED, .7 * kt)
        d = ImageDraw.Draw(img); r = 34 + 6 * math.sin(u * 8)
        d.ellipse([TARGET[0] - r, TARGET[1] - r, TARGET[0] + r, TARGET[1] + r], fill=RED, outline=INK, width=6)
    k = smooth(u / D)
    img = finish(img, u, 1.02 + .1 * k, 540, 1150, vig=(.35, (40, 50, 60)))
    clue(img, 'CLUE 1', u)
    chip_t(img, 'FAR SOUTH', (190, 50, 44), 600, 1390, u, cue(6) - .1, size=50)
    return img, {'faces': [], 'avoid': [(0, 150, W, 360), (380, 1330, 820, 1540)]}


# ---------------------------------------------------------------- s06: CLUE 2, one long rumble, no repeats (line 6)
def song(x):
    ph = (x * 6) % 1
    return .7 * math.sin(ph * 40) * math.exp(-((ph - .3) / .14) ** 2)


def rumble(x):
    if x < .06 or x > .78: return .015 * math.sin(x * 300)
    e = math.sin(math.pi * (x - .06) / .72) ** .5
    return e * (.55 * math.sin(x * 190) + .3 * math.sin(x * 77 + 1)) * (.8 + .2 * math.sin(x * 23))


def s06(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 6 * math.sin(u * .6)
    img.paste(vgrad([(0, (10, 16, 14)), (1, (4, 8, 8))]))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 360, 1040, 1560], 40, fill=(28, 30, 34), outline=INK, width=10)
    d.rounded_rectangle([80, 400, 1000, 1520], 24, fill=(6, 24, 16))
    for i in range(10): d.line([(80 + i * 92, 400), (80 + i * 92, 1520)], fill=(16, 52, 34), width=2)
    for j in range(13): d.line([(80, 400 + j * 93), (1000, 400 + j * 93)], fill=(16, 52, 34), width=2)
    for y in range(400, 1520, 6): d.line([(80, y), (1000, y)], fill=(4, 18, 12), width=1)   # scanlines
    green = (120, 255, 170)
    d.text((110, 450), 'WHALE SONG', font=font(40, True), fill=(140, 220, 200))
    d.text((110, 960), 'THE BLOOP', font=font(40, True), fill=(255, 140, 120))
    ks = smooth(seg(u, cue(2) - .3, cue(7) + .3))
    O.waveform(img, (110, 560, 970, 860), song, max(.02, ks), col=green, w=6)
    kr = smooth(seg(u, cue(8) - .1, cue(14) + .1)) * .8 + .2 * smooth(seg(u, cue(14), cue(15) + .4))
    O.waveform(img, (110, 1080, 970, 1400), rumble, max(.02, kr), col=(255, 110, 90), w=7)
    d = ImageDraw.Draw(img)
    if ks > .5:                                                          # repeat brackets over the song
        for i in range(1, 6):
            x = 110 + 860 * i / 6
            if (i / 6) < ks: d.arc([x - 70, 520, x + 10, 580], 200, 340, fill=(140, 220, 200), width=4)
    km = smooth(seg(u, cue(11) - .1, cue(13) + .2))
    if km > 0:
        xa, xb = 110 + 860 * .06, 110 + 860 * (.06 + .72 * km)
        d.line([(xa, 1440), (xb, 1440)], fill=(255, 200, 160), width=6)
        d.line([(xa, 1420), (xa, 1460)], fill=(255, 200, 160), width=6); d.line([(xb, 1420), (xb, 1460)], fill=(255, 200, 160), width=6)
    radial(img, 540, 960, 700, (60, 200, 120), .08 + .02 * math.sin(u * 7))
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 540, 960, dx=cam, vig=(.5, (0, 0, 0)))
    clue(img, 'CLUE 2', u)
    chip_t(img, 'REPEATS', (40, 130, 100), 780, 465, u, cue(4) - .1, size=40)
    chip_t(img, '~1 MINUTE', (190, 70, 50), 430, 1490, u, cue(13) - .1, size=44)
    chip_t(img, 'THEN SILENCE', (70, 70, 80), 820, 1000, u, cue(15) - .05, size=40)
    return img, {'faces': [], 'avoid': [(0, 150, W, 1560)]}


# ---------------------------------------------------------------- s07: CLUE 3, microphones near Antarctica (line 7)
QUAKES = [(640, 1210), (980, 1260), (780, 1330), (1060, 1200), (700, 1290), (900, 1230)]


def polar_day(img, u, cam, water=1000):
    img.paste(vgrad([(0, (150, 196, 232)), (.45, (214, 232, 246)), (.52, (240, 246, 252))], h=water + 40), (0, 0))
    radial(img, 200 + cam * .9, 300, 500, (255, 250, 230), .5)
    cloud_bands(img, 21, 150, 600, (255, 255, 255), .45, n=5, drift=u * 12 + cam)
    peak_range(img, 22, water - 140, 90, 220, (236, 244, 252), (176, 200, 228), snow=None, n=6, x_shift=cam * .8, snow_frac=0)


def s07(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -20 * smooth(u / D); wy = 1000
    polar_day(img, u, cam, wy)
    # the ice shelf front on the right
    kit.ice_cliff(img, 560 + cam * .5, 1200, lambda x: 780 + (x - 560) * -.03, lambda x: wy + 6, 7, lip_icicles=False, ink_w=5)
    # underwater
    wl = vgrad([(0, (60, 150, 190)), (.5, (24, 80, 130)), (1, (8, 30, 66))], h=H - wy)
    m = mask(); ImageDraw.Draw(m).polygon(O.surface_pts(wy, u, 8) + [(W + 60, H), (-60, H)], fill=255)
    img.paste(wl, (0, wy), m.crop((0, wy, W, H)))
    lay = layer(); ImageDraw.Draw(lay).polygon([(560 + cam * .5, wy), (1200, wy), (1200, 1420), (620, 1330)], fill=(150, 210, 236, 150))
    img.alpha_composite(lay)                                             # the shelf's submerged root
    d = ImageDraw.Draw(img); d.line(O.surface_pts(wy, u, 8), fill=(230, 246, 255), width=6)
    # icequakes: rings from the shelf root, more and more often (the counter climbs)
    th = cue(10) - .1
    if u > th:
        for j, (qx, qy) in enumerate(QUAKES):
            te = th + j * .45
            O.pulse_train(img, qx, qy, u, t0=te, every=2.7, speed=480, n=3, w=12, clip=(wy + 10, H), rmax=900, fade=900)
    # the ship lowers a hydrophone on a cable
    sx, sy = 330 + cam * .3, wy
    tip = O.ship(img, sx, sy, .62, u)
    kd = smooth(seg(u, cue(5) - .2, cue(8) + .2))
    hy = sy + 40 + 520 * kd
    hx = tip[0] + 10 * math.sin(u * 1.2)
    d = ImageDraw.Draw(img); d.line([tip, (hx, hy - 70)], fill=INK, width=6)
    lit = 0.0
    if u > th:
        for j, (qx, qy) in enumerate(QUAKES):
            for n in range(3):
                ta = th + j * .45 + n * 2.7 + math.hypot(qx - hx, qy - hy) / 480
                if 0 <= u - ta < .7: lit = max(lit, 1 - (u - ta) / .7)
    O.hydrophone(img, hx, hy, None, u, lit=lit, s=1.2)
    kit.dust(img, 7, 40, (0, wy + 20, W, H), (220, 240, 255), 120, size=(2, 5), t=u)
    img = finish(img, u, 1.03 + .03 * smooth(u / D), 540, 1000, vig=(.3, (20, 40, 70)))
    clue(img, 'CLUE 3', u)
    chip_t(img, '2005 · NEAR ANTARCTICA', (40, 100, 160), 540, 400, u, cue(3) - .1, size=46)
    if u > th:
        v = u - th; tc = cue(13) - th
        if u < cue(13) - .05: n = int(1 + 99 * smooth(v / max(.1, tc)) ** 2); txt = f'{n:,}'
        else: txt = '1,000s / YEAR'
        sc = 1 + .08 * math.exp(-max(0, u - cue(13)) * 6) if u >= cue(13) - .05 else 1
        put_chip(img, txt, (200, 50, 44), 540, 1720, pop(u, th, .3, 2) * sc, size=70)
    return img, {'faces': [], 'avoid': [(0, 150, W, 460), (200, 1640, 880, 1800)]}


# ---------------------------------------------------------------- s08 / s09: the riddle, then "Not a monster. Ice."
def night_sea(img, u, wy=1000, cam=0.0):
    img.paste(vgrad([(0, (6, 6, 24)), (.35, (22, 18, 60)), (.52, (44, 34, 90))], h=wy + 40), (0, 0))
    lay = layer(); stars(lay, 31, 160, wy - 60, u); img.alpha_composite(lay)
    radial(img, 820 + cam * .9, 300, 260, (220, 220, 255), .35)
    d = ImageDraw.Draw(img); d.ellipse([780 + cam * .9, 260, 860 + cam * .9, 340], fill=(236, 236, 250))
    wl = vgrad([(0, (40, 62, 124)), (.4, (22, 36, 84)), (1, (8, 14, 40))], h=H - wy)
    m = mask(); ImageDraw.Draw(m).polygon(O.surface_pts(wy, u, 9, cam=cam) + [(W + 60, H), (-60, H)], fill=255)
    img.paste(wl, (0, wy), m.crop((0, wy, W, H)))
    d = ImageDraw.Draw(img); d.line(O.surface_pts(wy, u, 9, cam=cam), fill=(150, 160, 220), width=5)
    for i in range(14):                                                  # moonlight glints on the swell
        x = 820 + cam * .9 + (i - 7) * 40 * (1 + i % 3) ; y = wy + 20 + i * 6
        d.line([(x - 30, y), (x + 30, y)], fill=(200, 200, 240), width=3)


def s08(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 10 * math.sin(u * .5)
    night_sea(img, u, cam=cam)
    d = ImageDraw.Draw(img)
    for j, (bx, bw, bh) in enumerate(((120, 220, 60), (380, 120, 34), (930, 260, 80))):   # far icebergs on the horizon
        bx += cam * .6; d.polygon([(bx - bw / 2, 1000), (bx - bw * .2, 1000 - bh), (bx + bw * .1, 1000 - bh * .8), (bx + bw / 2, 1000)], fill=(70, 74, 130), outline=INK, width=4)
    cloud_bands(img, 36, 120, 520, (90, 90, 170), .35, n=4, drift=u * 10)
    sx, sy = 540 + 40 * math.sin(u * .4), 1300 + 20 * math.sin(u * .7)
    O.pulse_train(img, sx, sy, u, t0=cue(4) - .2, every=.5, speed=500, n=8, w=12, clip=(1012, H), rmax=900, fade=800)
    radial(img, sx, sy - 60, 700, (70, 110, 190), .35 + .05 * math.sin(u * 2))
    m = mask(); O.sea_shadow(img, sx, sy, 1.0, u, col=(2, 4, 14), alpha=.95, blur=4, eye=0)
    kit.dust(img, 8, 50, (0, 1020, W, H), (150, 170, 230), 100, size=(2, 4), t=u)
    img = finish(img, u, 1.02 + .05 * smooth(u / D), 540, 1000, vig=(.5, (0, 0, 10)))
    q = slam(u, .05, .3, 1.5)
    tl = _q_title(); anim.scaled_paste(img, tl[0], 540, 560 + 8 * math.sin(u * 2), q, angle=4 * math.sin(u))
    chip_t(img, 'ROARS 1,000s OF TIMES A YEAR', (190, 50, 44), 540, 170, u, cue(4) - .1, size=44)
    chip_t(img, 'NEVER NEEDS TO BREATHE?', (80, 70, 150), 540, 280, u, cue(11) - .1, size=44)
    return img, {'faces': [], 'avoid': [(0, 110, W, 900)]}


_qt = {}
def _q_title():
    if 'q' not in _qt: _qt['q'] = anim.text_layer(lambda l: title(l, [('?', RED, 420)], 60, size=420), 700, 800)
    return _qt['q']


SHARDS = None
def _shards():
    global SHARDS
    if SHARDS is None:
        rng = np.random.default_rng(5); SHARDS = []
        for i in range(130):
            a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0, 1) ** .5
            x, y = math.cos(a) * 300 * r, -40 + math.sin(a) * 200 * r + (rng.uniform(0, 500) if i % 3 == 0 else 0)
            q = rng.uniform(22, 60); pts = [(math.cos(b) * q * rng.uniform(.6, 1.2), math.sin(b) * q * rng.uniform(.6, 1.2)) for b in (0, 2.1, 4.2)]
            SHARDS.append((x, y, pts, rng.uniform(-1, 1), rng.uniform(.6, 1.4)))
    return SHARDS


def s09(u, D, cue):
    ti = cue(3) - .05                                                    # "Ice."
    k = smooth(seg(u, ti, ti + .5))
    img = Image.new('RGBA', (W, H)); cam = 0.0
    night_sea(img, u + 3.9)
    if k > 0:                                                            # the scene floods with cold light
        lay = Image.new('RGBA', (W, H)); lay.paste(vgrad([(0, (120, 200, 240)), (.5, (200, 240, 255)), (1, (60, 140, 200))]))
        lay.putalpha(int(235 * k)); img.alpha_composite(lay)
    sx, sy = 540, 1380
    if u < ti:
        radial(img, sx, sy - 60, 700, (70, 110, 190), .4)
        O.sea_shadow(img, sx, sy, 1.15 + .05 * smooth(seg(u, 0, ti)), u + 3.9, col=(2, 4, 14), alpha=.92, blur=12)
    else:
        v = u - ti; d = ImageDraw.Draw(img)
        radial(img, sx, sy - 100, 600, (255, 255, 255), .6 * (1 - smooth(v / .8)))
        for x, y, pts, spin, sp in _shards():
            px = sx + x * (1 + 1.4 * ease_out(v / 1.2) * sp); py = sy + y * (1 + .9 * ease_out(v / 1.2) * sp) - 160 * v
            a = spin * v * 3
            P = [(px + X * math.cos(a) - Y * math.sin(a), py + X * math.sin(a) + Y * math.cos(a)) for X, Y in pts]
            d.polygon(P, fill=lerp((10, 14, 30), [(226, 246, 255), (170, 220, 245), (255, 255, 255), (120, 190, 230)][int(abs(x * 7 + y)) % 4], smooth(v / .35)), outline=INK, width=4)
            d.line([P[0], P[1]], fill=(255, 255, 255), width=3)
    kit.dust(img, 9, 40, (0, 0, W, H), (255, 255, 255), 150 * k + 60, size=(2, 6), t=u)
    flash(img, u, ti, .35)
    sx_, sy_ = shake(u, ti, 14, .4)
    img = finish(img, u, 1.05 + .04 * smooth(u / D), 540, 1100, dx=sx_, dy=sy_, vig=(.45 * (1 - k) + .2, lerp((0, 0, 10), (40, 90, 140), k)))
    slam_title(img, 's09_a', [('NOT A MONSTER.', 'white', 110)], 300, u, .05)
    slam_title(img, 's09_b', [('ICE.', (120, 220, 255), 260)], 520, u, ti)
    return img, {'faces': [], 'avoid': [(0, 200, W, 820)]}


# ---------------------------------------------------------------- s10: an ice shelf cracks and calves (line 10)
_wall = {}
def _shelf_wall(top=880, water=1300):
    if 'w' not in _wall:
        lay = layer(1400, H)
        kit.ice_cliff(lay, 0, 1400, lambda x: top + 10 * math.sin(x * .01), lambda x: water + 40, 11,
                      lit=(255, 236, 226), mid=(236, 206, 214), shade=(170, 160, 210), deep=(110, 110, 180), lip_icicles=True, ink_w=5)
        _wall['w'] = lay
    return _wall['w']


SLAB_X = (560, 900)


def s10(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -60 * smooth(u / D); wy = 1300
    img.paste(vgrad([(0, (60, 54, 120)), (.3, (170, 110, 150)), (.48, (255, 170, 130)), (.58, (255, 214, 170))], h=wy + 40), (0, 0))
    radial(img, 260 + cam * .9, 760, 520, (255, 210, 150), .6)
    cloud_bands(img, 33, 200, 700, (255, 190, 180), .4, n=6, drift=u * 14 + cam)
    peak_range(img, 34, 900, 120, 260, (255, 220, 214), (170, 140, 190), n=6, x_shift=cam * .7, snow_frac=0)
    haze(img, 780, 920, (255, 200, 180), .5)
    wall = _shelf_wall(); ox = int(-160 + cam * .5)
    kc = smooth(seg(u, cue(6) - .15, cue(6) + .35))                     # "crack"
    kv = smooth(seg(u, cue(8) - .1, cue(12) + .3)) if u > cue(8) - .1 else 0.0   # "break away into the sea"
    a0, a1 = SLAB_X[0] - ox, SLAB_X[1] - ox
    m = mask(1400, H); ImageDraw.Draw(m).polygon([(a0, 0), (a1, 0), (a1 - 10, H), (a0 + 20, H)], fill=255)
    main = wall.copy(); main.putalpha(Image.fromarray(np.minimum(np.asarray(wall.getchannel('A')), 255 - np.asarray(m))))
    d = ImageDraw.Draw(img)                                              # the shelf behind the slab (recessed, in shadow)
    d.rectangle([SLAB_X[0] + 10, 905, SLAB_X[1] - 10, wy], fill=(150, 140, 196))
    for i in range(6): d.line([(SLAB_X[0] + 40 + i * 50, 910), (SLAB_X[0] + 30 + i * 52, wy)], fill=(120, 112, 170), width=4)
    img.alpha_composite(main, (ox, 0))
    slab = wall.copy(); slab.putalpha(Image.fromarray(np.minimum(np.asarray(wall.getchannel('A')), np.asarray(m))))
    slab = slab.crop((a0 - 40, 0, a1 + 40, H))
    drop = 560 * ease_in(kv); ang = -16 * smooth(kv)
    sl = slab.rotate(ang, resample=Image.BICUBIC, center=(slab.width / 2, wy), translate=(20 * kv, drop))
    img.alpha_composite(sl, (ox + a0 - 40, 0))
    d = ImageDraw.Draw(img)
    if kc > 0:                                                           # the cracks run down (their scars stay lit)
        for xx in SLAB_X:
            pts = [(xx + 12 * math.sin(i * 1.7), 880 + (wy - 880) * kc * i / 8) for i in range(9)]
            mm = mask(); ImageDraw.Draw(mm).line(pts, fill=255, width=24); glow(img, mm, (140, 220, 255), .8 * kc * (1 - .5 * kv), blur=16, add=True)
            d = ImageDraw.Draw(img); d.line(pts, fill=INK, width=10)
    # the sea in front (covers the sinking slab)
    wl = vgrad([(0, (120, 110, 170)), (.4, (60, 70, 130)), (1, (24, 30, 70))], h=H - wy)
    m2 = mask(); ImageDraw.Draw(m2).polygon(O.surface_pts(wy, u, 10) + [(W + 60, H), (-60, H)], fill=255)
    img.paste(wl, (0, wy), m2.crop((0, wy, W, H)))
    d = ImageDraw.Draw(img); d.line(O.surface_pts(wy, u, 10), fill=(255, 220, 200), width=5)
    for i in range(10):
        x = 260 + cam * .9 + (i - 5) * 60; y = wy + 30 + i * 18; d.line([(x - 40, y), (x + 40, y)], fill=(255, 200, 170), width=4)
    ks = seg(u, cue(10) - .1, cue(10) + 1.3)
    O.splash(img, (SLAB_X[0] + SLAB_X[1]) / 2 + 10, wy, u, ks, w=380)
    if 0 < ks < 1: O.pulse_train(img, 740, wy + 40, u, t0=cue(10) - .1, every=.4, speed=600, n=4, w=12, clip=(wy + 12, H), rmax=900, fade=800)
    for i in range(6):                                                   # floating ice in front
        x = (i * 230 + u * 20) % (W + 200) - 100; y = 1500 + i % 3 * 120
        d.polygon([(x - 60, y), (x + 70, y), (x + 50, y + 22), (x - 40, y + 26)], fill=(240, 236, 246), outline=INK, width=4)
    kit.snow_particles(img, 4, n=(40, 16, 6), t=u, alpha=(150, 170, 120)) if False else dust(img, 4, 40, (0, 0, W, H), (255, 240, 240), 120, size=(2, 5), t=u)
    sx, sy = shake(u, cue(10), 10, .5)
    img = finish(img, u, 1.03 + .04 * smooth(u / D), 540, 1100, dx=sx, dy=sy, vig=(.38, (40, 20, 50)))
    chip_t(img, 'ANTARCTICA', (60, 90, 160), 540, 170, u, cue(1) - .1, size=56)
    slam_title(img, 's10_t', [('ICE SHELVES', 'white', 100), ('CRACK', (140, 220, 255), 120)], 290, u, cue(6) - .1)
    return img, {'faces': [], 'avoid': [(0, 120, W, 600)]}


# ---------------------------------------------------------------- s11: a city-sized slab splits; the shudder travels (line 11)
def city_outline(d, x0, x1, base, k, col=(255, 236, 160)):
    rng = np.random.default_rng(8); x = x0; pts = [(x0, base)]
    while x < x1:
        w = rng.uniform(26, 60); h = rng.uniform(40, 170) * k
        pts += [(x, base - h), (min(x1, x + w), base - h)]; x += w
    pts.append((x1, base))
    d.polygon(pts, fill=(255, 236, 160, 90))
    d.line(pts, fill=INK, width=9); d.line(pts, fill=col, width=4)
    for i in range(1, len(pts) - 2, 2):                                  # lit windows
        (xa, ya), (xb, _) = pts[i], pts[i + 1]
        for yy in range(int(ya) + 14, int(base) - 8, 22):
            for xx in range(int(xa) + 8, int(xb) - 8, 16): d.rectangle([xx, yy, xx + 6, yy + 9], fill=(255, 236, 160, 200))


def s11(u, D, cue):
    img = Image.new('RGBA', (W, H)); wy = 760
    pan = -420 * smooth(seg(u, cue(13) - .3, cue(21) - .1))
    cam = pan
    O.ocean_section(img, u, surface=wy, floor=1820, sky=((120, 170, 220), (200, 226, 244)),
                    water=((50, 150, 180), (20, 90, 140), (6, 34, 70)), cam=-pan * 0 + pan * .4, seed=21)
    O.depth_ruler(img, 1010, wy, 260, kms=(0, 1, 2, 3), a=120) if False else None
    ks = smooth(seg(u, cue(8) - .1, cue(8) + .5))                        # "splits"
    sep = 120 * ease_out(seg(u, cue(8) - .1, D))
    def block(x0, x1, dx, ang, tag):
        lay = layer(); dl = ImageDraw.Draw(lay)
        if kc > 0: city_outline(dl, x0 + 20, x1 - 20, wy - 210, kc, col=(255, 236, 160, 255))
        top, root = wy - 210, wy + 420
        dl.polygon([(x0, top), (x1, top), (x1 - 10, root), (x0 + 30, root - 30)], fill=(214, 238, 250, 255), outline=INK, width=7)
        dl.polygon([(x0, top), (x1, top), (x1, top + 30), (x0, top + 30)], fill=(250, 252, 255, 255))
        dl.polygon([(x0 + 4, wy + 6), (x1 - 4, wy + 6), (x1 - 10, root), (x0 + 30, root - 30)], fill=(150, 210, 236, 150))
        for i in range(5): dl.line([(x0 + 40 + i * (x1 - x0) / 5, top + 40), (x0 + 30 + i * (x1 - x0) / 5, wy - 6)], fill=(170, 210, 236, 255), width=4)
        lay = lay.rotate(ang, resample=Image.BICUBIC, center=((x0 + x1) / 2, wy), translate=(dx, 0))
        img.alpha_composite(lay)
    kc = smooth(seg(u, cue(4) - .1, cue(7) + .2))
    X0, XC, X1 = 20 + pan, 430 + pan, 840 + pan
    block(X0, XC, -sep * .3, 1.5 * ks, 'L'); block(XC, X1, sep, -2.5 * ks, 'R')
    d = ImageDraw.Draw(img)
    if ks > 0 and ks < 1:
        flash(img, u, cue(8) - .1, .3, .5, (200, 240, 255))
    # the shudder: one big front from the crack, through the water, to a distant station
    tsh = cue(10) - .1; cx, cy = XC + sep * .3, wy + 300
    STX, STY = 1330 + pan, 1260
    if u > tsh:
        O.pulse_train(img, cx, cy, u, t0=tsh, every=.35, speed=560, n=4, w=34, clip=(wy + 12, 1820), rmax=2400, fade=3600)
    r = math.hypot(STX - cx, STY - cy); ta = tsh + r / 560
    lit = max(0.0, 1 - abs(u - ta - .3) / .6) if u > ta else 0.0
    O.hydrophone(img, STX, STY, 1820, u, lit=lit, s=1.3)
    import taiga
    if u > cue(18) - .2:
        k2 = smooth(seg(u, cue(18) - .2, cue(20)))
        d = ImageDraw.Draw(img); ya = 1620
        if k2 > .01: taiga.dashed(d, (cx, ya), (cx + (STX - 60 - cx) * k2, ya), (255, 240, 200), w=7, dash=26, gap=14)
        if k2 > .95: d.polygon([(STX - 60, ya - 20), (STX - 20, ya), (STX - 60, ya + 20)], fill=(255, 240, 200))
    kit.dust(img, 11, 50, (0, wy + 20, W, 1820), (220, 240, 255), 120, size=(2, 5), t=u)
    sx, sy = shake(u, cue(8) - .05, 9, .4)
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 540, 1000, dx=sx, dy=sy, vig=(.35, (10, 30, 60)))
    chip_t(img, 'THE SIZE OF A CITY', (170, 120, 30), 540, 200, u, cue(4) - .1, size=56)
    if u > cue(8) - .1: slam_title(img, 's11_t', [('SPLIT!', 'white', 110)], 330, u, cue(8) - .1)
    if u > cue(19) - .1: put_chip(img, '1,000s OF KM', (190, 50, 44), 540, 1700, pop(u, cue(19) - .1, .3, 2), size=60)
    return img, {'faces': [], 'avoid': [(0, 140, W, 460), (220, 1640, 860, 1760)]}


# ---------------------------------------------------------------- s12: an ice cube cracks; now make it a mountain (line 12)
def kitchen(img, u):
    img.paste(vgrad([(0, (96, 60, 44)), (.6, (160, 100, 60)), (1, (120, 74, 46))]))
    d = ImageDraw.Draw(img)
    d.rectangle([600, 160, 1000, 760], fill=(255, 214, 150), outline=INK, width=10)      # a warm window
    d.line([(800, 160), (800, 760)], fill=INK, width=8); d.line([(600, 460), (1000, 460)], fill=INK, width=8)
    radial(img, 800, 460, 620, (255, 200, 130), .45 + .03 * math.sin(u * 2))
    d = ImageDraw.Draw(img)
    d.rectangle([-40, 1420, W + 40, H], fill=(110, 70, 46)); d.line([(-40, 1420), (W + 40, 1420)], fill=INK, width=8)
    for i in range(8): d.line([(-40, 1480 + i * 60), (W + 40, 1470 + i * 62)], fill=(96, 60, 40), width=4)


def polar_sea(img, u, wy=1150):
    img.paste(vgrad([(0, (90, 140, 200)), (.5, (190, 220, 240)), (.6, (230, 240, 250))], h=wy + 40), (0, 0))
    cloud_bands(img, 41, 200, 800, (255, 255, 255), .4, n=5, drift=u * 15)
    wl = vgrad([(0, (60, 130, 180)), (1, (14, 50, 90))], h=H - wy)
    img.paste(wl, (0, wy))
    d = ImageDraw.Draw(img); d.line(O.surface_pts(wy, u, 8), fill=(230, 246, 255), width=6)


def s12(u, D, cue):
    kg = smooth(seg(u, cue(8) - .1, cue(16)))                            # "Now make that ice cube the size of a mountain"
    A = Image.new('RGBA', (W, H)); kitchen(A, u)
    ly = O.glass(A, 540, 1440, 420, 600, u, fill=.6)
    if kg > 0:
        Bm = Image.new('RGBA', (W, H)); polar_sea(Bm, u)
        if kg > .55:                                                     # a mountain outline for scale + a tiny ship
            km = smooth(seg(u, cue(14) - .2, cue(17)))
            d = ImageDraw.Draw(Bm)
            import taiga
            pk = [(660, 1150), (800, 1150 - 420 * km), (870, 1150 - 340 * km), (960, 1150 - 520 * km), (1100, 1150)]
            d.polygon(pk, fill=(150, 170, 200), outline=INK, width=6)
            d.polygon([pk[1], (830, 1150 - 380 * km), pk[2], (920, 1150 - 470 * km), pk[3], (1000, 1150 - 300 * km), (870, 1150)], fill=(110, 130, 170))
            d.polygon([(780, 1150 - 380 * km), pk[1], (820, 1150 - 390 * km)], fill=(250, 252, 255))
            d.polygon([(935, 1150 - 470 * km), pk[3], (990, 1150 - 460 * km)], fill=(250, 252, 255))
            O.ship(Bm, 150, 1150, .13, u)
            put_chip(Bm, 'MOUNTAIN', (60, 100, 150), 880, 1150 - 520 * km - 50, km, size=36)
        A = Image.blend(A, Bm, kg)
    img = A
    kc = smooth(seg(u, cue(4) - .1, cue(4) + .5))
    r = 100 + (330 - 100) * ease_in(kg) ** .8
    cx = 540 - 150 * kg; cy = ly - 30 + (980 - (ly - 30)) * kg
    jit = 4 * math.sin(u * 40) * math.exp(-max(0, u - cue(4)) * 4) if u > cue(4) else 0
    if kc > 0:
        O.pulse_train(img, cx, cy, u, t0=cue(4) - .1, every=.3, speed=500, n=3, w=8, col=(200, 240, 255), rmax=300, fade=300)
    O.ice_cube(img, cx + jit, cy, r, u, crack=kc + kg * .0, ang=6 + 2 * math.sin(u * 1.4))
    if kg < 1:
        lay = layer(); O.glass(lay, 540, 1440, 420, 600, u, back=False)
        lay.putalpha(lay.getchannel('A').point(lambda a: int(a * (1 - min(1, kg * 2))))); img.alpha_composite(lay)
    if kg > .3:                                                          # the sea's front over the berg's base
        lay = layer(); dl = ImageDraw.Draw(lay)
        dl.polygon(O.surface_pts(1150, u, 8) + [(W + 60, H), (-60, H)], fill=(40, 110, 160, int(170 * kg)))
        img.alpha_composite(lay)
        if u > cue(17) - .2: O.pulse_train(img, cx, 1200, u, t0=cue(17) - .2, every=.4, speed=600, n=4, w=14, clip=(1160, H), rmax=900, fade=900)
    dust(img, 12, 30, (0, 0, W, H), (255, 236, 200) if kg < .5 else (230, 246, 255), 110, size=(2, 5), t=u)
    ki = smooth(seg(u, cue(10), cue(12)))
    if ki > 0:                                                           # inset: the glass it started in
        inset = Image.new('RGBA', (W, H)); kitchen(inset, u); O.glass(inset, 540, 1440, 420, 600, u, fill=.6)
        O.ice_cube(inset, 540, 1440 - 600 * .6 - 30, 100, u, crack=1.0, ang=6); O.glass(inset, 540, 1440, 420, 600, u, back=False)
        ins = inset.crop((240, 600, 840, 1560)).resize((250, 400), Image.LANCZOS)
        mm = mask(250, 400); ImageDraw.Draw(mm).rounded_rectangle([0, 0, 249, 399], 30, fill=255)
        x0, y0 = 60, 1440; d = ImageDraw.Draw(img)
        d.rounded_rectangle([x0 - 8, y0 - 8, x0 + 258, y0 + 408], 34, fill=INK)
        lay = layer(); lay.paste(ins, (x0, y0), mm); lay.putalpha(lay.getchannel('A').point(lambda a: int(a * ki))); img.alpha_composite(lay)
        import taiga; taiga.dashed(d, (x0 + 200, y0 + 40), (cx - r * .8, cy + r * .6), (255, 255, 255), w=5)
    img = finish(img, u, 1.04 - .03 * kg + .02 * math.sin(u * .6), 540, 1100, vig=(.38, lerp((40, 20, 10), (10, 30, 60), kg)))
    chip_t(img, 'IN YOUR DRINK', (170, 100, 40), 540, 190, u, cue(2) - .1, size=50) if kg < .2 else None
    if kg >= .2: slam_title(img, 's12_t', [('THE SIZE OF', 'white', 90), ('A MOUNTAIN', (140, 220, 255), 120)], 200, u, cue(14) - .1)
    return img, {'faces': [], 'avoid': [(0, 120, W, 480)]}


# ---------------------------------------------------------------- s13: official: ICEQUAKE (line 13)
def s13(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -12 * smooth(u / D)
    img.paste(vgrad([(0, (40, 60, 56)), (.6, (70, 92, 82)), (1, (50, 66, 60))]))
    radial(img, 540, 500, 700, (255, 230, 180), .3)
    d = ImageDraw.Draw(img)
    d.rectangle([90 + cam * .5, 260, 450 + cam * .5, 700], fill=(236, 230, 214), outline=INK, width=8)   # a pinned chart on the wall
    O.waveform(img, (120 + cam * .5, 330, 420 + cam * .5, 520), pitch_trace, 1.0, col=(200, 60, 50), w=5, glow_a=.2, head=False)
    d = ImageDraw.Draw(img); d.text((270 + cam * .5, 620), 'BLOOP · 1997', font=font(34, True), fill=INK, anchor='mm')
    d.rectangle([620 + cam * .5, 330, 1000 + cam * .5, 700], fill=(60, 44, 36), outline=INK, width=6)
    for j in range(3):
        y = 350 + j * 115; d.line([(620 + cam * .5, y + 105), (1000 + cam * .5, y + 105)], fill=INK, width=6)
        x = 640 + cam * .5; rb = np.random.default_rng(j)
        while x < 970 + cam * .5:
            bw = rb.uniform(18, 34); bh = rb.uniform(60, 95)
            d.rectangle([x, y + 105 - bh, x + bw, y + 105], fill=[(160, 70, 60), (60, 110, 150), (200, 170, 90), (90, 130, 90)][int(rb.integers(4))], outline=INK, width=3); x += bw + 3
    tn = cue(3) - .1                                                     # the nod on "made it official"
    nod = 14 * math.sin(seg(u, tn, tn + .8) * math.pi * 2) * (1 - seg(u, tn, tn + .8))
    g = scientist(img, u, 'stand', 'determined', 790 + cam, 1980, 1.0, look=-.35, hop=-max(0, nod) * .6,
                  lean=-3)
    # desk + folder
    desk(img, cam * .3, y=1390, top=(120, 84, 56), front=(84, 58, 40))
    fl = layer(); df = ImageDraw.Draw(fl); fx, fy = 470, 1640
    df.rounded_rectangle([fx - 380, fy - 300, fx - 120, fy - 250], 12, fill=(214, 176, 100), outline=INK, width=6)
    df.rounded_rectangle([fx - 400, fy - 270, fx + 400, fy + 260], 16, fill=(226, 190, 112), outline=INK, width=8)
    df.text((fx - 360, fy - 290), 'CASE FILE', font=font(28, True), fill=INK, anchor='lm')
    df.rectangle([fx - 360, fy - 220, fx + 40, fy + 200], fill=(250, 248, 240), outline=INK, width=5)
    df.text((fx - 330, fy - 170), 'THE BLOOP', font=font(52, True), fill=INK, anchor='lm')
    df.text((fx - 330, fy - 110), 'PACIFIC · 1997', font=font(30, True), fill=(90, 90, 100), anchor='lm')
    ph = Image.new('RGBA', (280, 300)); ph.paste(vgrad([(0, (40, 70, 90)), (1, (6, 12, 24))], w=280, h=300))
    O.sea_shadow(ph, 140, 120, .3, u, col=(0, 0, 0), alpha=.8, blur=6)
    fl.alpha_composite(ph, (fx + 80, fy - 200)); df = ImageDraw.Draw(fl)
    df.rectangle([fx + 80, fy - 200, fx + 360, fy + 100], outline=INK, width=6)
    df.text((fx + 220, fy + 140), 'MONSTER?', font=font(36, True), fill=(120, 40, 40), anchor='mm')
    ts = cue(10) - .1                                                    # "icequake."
    if u > ts + .15: draw_x(fl, fx + 220, fy - 50, 120, (u - ts - .15) * 4, w=18)
    img.alpha_composite(fl.rotate(2, resample=Image.BICUBIC, center=(fx, fy), translate=(cam * .3, 10 * math.sin(u * .5))))
    dust(img, 13, 30, (0, 0, W, 1390), (255, 240, 210), 110, size=(2, 5), t=u)
    if u > ts:
        v = u - ts; s = anim.lerp(1.5, .95, ease_in(v / .12)) if v < .12 else anim.lerp(.95, 1.0, out_back(min(1, (v - .12) / .2), 2.0))
        st = _stamp(); anim.scaled_paste(img, st, 300, 1690, s * .72, -8)
    img = finish(img, u, 1.03 + .03 * smooth(u / D), 540, 1200, dy=shake(u, ts, 8, .3)[1], vig=(.38, (20, 30, 24)))
    chip_t(img, 'YEARS LATER', (70, 90, 80), 540, 150, u, .1, size=50)
    chip_t(img, 'OFFICIAL', (40, 120, 90), 540, 250, u, cue(5) - .1, size=56)
    return img, {'faces': [faces_of(g)], 'avoid': [(0, 100, W, 300), (60, 1360, 920, 1920)]}


_st = {}
def _stamp():
    if 's' not in _st: _st['s'] = props.stamp('ICEQUAKE', (40, 140, 210), 96, check=True)
    return _st['s']


# ---------------------------------------------------------------- s14a: the monster was Antarctica breaking (line 14)
def aurora(img, u, y0=150, y1=760):
    for k, (col, ph, amp) in enumerate((((80, 255, 170), 0, 120), ((120, 200, 255), 1.7, 90), ((200, 120, 255), 3.1, 70))):
        m = mask(); dm = ImageDraw.Draw(m)
        pts = [(x, y0 + 160 + k * 110 + amp * math.sin(x * .006 + u * .5 + ph) + 30 * math.sin(x * .02 - u)) for x in range(-50, W + 60, 30)]
        dm.line(pts, fill=255, width=90 - k * 20, joint='curve')
        glow(img, m, col, .55 - k * .1, blur=40, add=True)
        for x, y in pts[::3]:
            mm = mask(); ImageDraw.Draw(mm).line([(x, y - 140 - 30 * math.sin(x + u)), (x, y + 20)], fill=255, width=14)
            glow(img, mm, col, .12, blur=14, add=True)


def s14a(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 30 * smooth(u / D); wy = 980
    img.paste(vgrad([(0, (4, 8, 26)), (.4, (14, 26, 60)), (.5, (24, 40, 76))], h=wy + 40), (0, 0))
    lay = layer(); stars(lay, 51, 160, 800, u); img.alpha_composite(lay)
    aurora(img, u)
    kit.ice_cliff(img, -60, W + 60, lambda x: 760 + 20 * math.sin(x * .007) + cam * 0, lambda x: wy + 6, 15,
                  lit=(190, 236, 230), mid=(130, 180, 200), shade=(80, 110, 160), deep=(40, 60, 110), lip_icicles=True, ink_w=5)
    wl = vgrad([(0, (20, 50, 90)), (.5, (8, 22, 50)), (1, (2, 6, 18))], h=H - wy)
    m = mask(); ImageDraw.Draw(m).polygon(O.surface_pts(wy, u, 8) + [(W + 60, H), (-60, H)], fill=255)
    img.paste(wl, (0, wy), m.crop((0, wy, W, H)))
    d = ImageDraw.Draw(img); d.line(O.surface_pts(wy, u, 8), fill=(140, 230, 210), width=5)
    # cracks flash along the cliff, each sending a red front down into the sea
    for j, (x, t0) in enumerate(((250, -.4), (760, .5), (480, 1.3), (900, 2.1), (150, 2.6))):
        if u > t0:
            v = u - t0
            if v < .5:
                pts = [(x + 14 * math.sin(i * 2 + j), 770 + i * 26) for i in range(9)]
                mm = mask(); ImageDraw.Draw(mm).line(pts, fill=255, width=20); glow(img, mm, (180, 255, 240), .9 * (1 - v / .5), blur=14, add=True)
                d = ImageDraw.Draw(img); d.line(pts, fill=INK, width=8)
            O.pulse_train(img, x, wy + 20, u, t0=t0, every=.5, speed=520, n=3, w=16, clip=(wy + 10, H), rmax=1300, fade=1300)
    kit.dust(img, 14, 60, (0, 0, W, H), (200, 255, 240), 120, size=(2, 5), t=u)
    img = finish(img, u, 1.04 + .03 * smooth(u / D), 540, 1000, vig=(.45, (0, 4, 16)))
    chip_t(img, 'THE "MONSTER" =', (80, 70, 150), 540, 170, u, cue(1) - .1, size=52)
    slam_title(img, 's14a_t', [('ANTARCTICA,', 'white', 100), ('BREAKING', (255, 90, 70), 120)], 290, u, cue(9) - .1)
    return img, {'faces': [], 'avoid': [(0, 110, W, 560)]}


# ---------------------------------------------------------------- s14b: still listening; back into the opening (loop)
def s14b(u, D, cue):
    cam = -10 * smooth(u / D)
    img = Image.new('RGBA', (W, H)); room(img, u, cam * 0, dark=.6)
    content, _ = s01(u - D, 6.0, lambda i: 99.0)
    screen_frame(img, SCREEN, content, glow_col=(255, 90, 70))
    desk(img, 0, top=(50, 42, 44), front=(30, 26, 30))
    radial(img, 790, 1700, 500, (255, 90, 70), .18 + .03 * math.sin(u * 3))  # the display's glow on the floor
    d = ImageDraw.Draw(img)
    for i in range(6): d.line([(-40, 1560 + i * 70), (W + 40, 1550 + i * 74)], fill=(40, 34, 40), width=3)
    console(img, 760, 1390, u)
    d = ImageDraw.Draw(img); d.rounded_rectangle([980, 1300, 1040, 1385], 10, fill=(200, 70, 60), outline=INK, width=5)
    d.arc([1030, 1320, 1070, 1360], 270, 90, fill=INK, width=8)
    g = scientist(img, u, 'think', 'neutral' if u < cue(14) else 'thinking', 360, 1700, .82, look=.4, lean=2, aura=(255, 90, 70), aura_a=.35,
                  rim=(255, 140, 120), rim_dir=(1, -.4))
    hx, hy = g['head']; R = g['R']; d = ImageDraw.Draw(img)
    d.line([(hx + R, hy + R * .4), (hx + R * 1.6, hy + R * 3), (620, 1330)], fill=INK, width=9, joint='curve')
    dust(img, 15, 30, (0, 300, W, 1400), (255, 200, 180), 100, size=(2, 5), t=u)
    img = finish(img, u, 1.0, 540, 900, vig=(.45, (6, 6, 16)))
    chip_t(img, 'EVERY DAY', (190, 60, 50), 300, 300, u, cue(12) - .1, size=52)
    e = smooth(seg(u, D - .6, D))
    if e <= 0:
        return img, {'faces': [faces_of(g)], 'avoid': [(80, 240, 520, 360), (SCREEN[0] - 30, SCREEN[1] - 30, SCREEN[2] + 30, SCREEN[3] + 30)]}
    # the loop: push into the display until it fills the frame with the s01 opening
    x0, y0 = SCREEN[0] * (1 - e), SCREEN[1] * (1 - e); s = 1 + (W / (SCREEN[2] - SCREEN[0]) - 1) * e
    out = img.transform((W, H), Image.AFFINE, (1 / s, 0, SCREEN[0] - x0 / s, 0, 1 / s, SCREEN[1] - y0 / s), resample=Image.BICUBIC)
    cw, ch = int(round((SCREEN[2] - SCREEN[0]) * s)), int(round((SCREEN[3] - SCREEN[1]) * s))
    if e >= .999: return content, {'faces': [], 'avoid': [], 'seam': 1}
    out.paste(content.convert('RGB').resize((cw, ch), Image.BILINEAR), (int(round(x0)), int(round(y0))))
    return out, {'faces': [], 'avoid': [], 'seam': 1}


import re as _re
SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [('s01', 1, 0), ('s02', 2, 0), ('s03', 3, 0), ('s04', 4, 0), ('s05', 5, 0), ('s06', 6, 0), ('s07', 7, 0),
             ('s08', 8, 0), ('s09', 9, 0), ('s10', 10, 0), ('s11', 11, 0), ('s12', 12, 0), ('s13', 13, 0), ('s14a', 14, 0),
             ('s14b', 14, 11)]
END = 65.4                     # 1962 frames; with the 0.1 s cover the posted cut is 65.5 s
BAND_AT = {'s14b': 2.5}        # caption band read before the loop push-in
STILL_AT = {'s01': .9, 's02': .9, 's03': .93, 's04': .92, 's05': .95, 's06': .95, 's07': .97, 's08': .92, 's09': .8, 's10': .9,
            's11': .9, 's12': .95, 's13': .95, 's14a': .85, 's14b': .6}

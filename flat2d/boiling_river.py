"""The Boiling River (video 6, "The River That Boils With No Volcano"): shots s01-s16 as `sNN(u, D, cue) -> (img, info)`.

Same contract as bloop.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the shot's
voice-over LINE. info: 'faces' (face boxes; render.py adds body boxes) and 'avoid' (boxes the caption must not
cover). Every shot keeps moving (steam, bubbles, flow, rain, glow pulses, camera drift, characters breathing and
blinking). Serious mystery, no comedy. The frog never touches the water (the shot cuts before contact) and the
volcano under the river is only ever an imagined ghost.

Render: .venv/bin/python flat2d/render.py audio/boiling-river/words.json OUT.mp4 --film boiling_river
"""
import math, os, sys, re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kit, props, anim
import jungle as J
from kit import W, H, INK, vgrad, radial, haze, dust, label, title, font, mask, glow, fill_mask, layer, lerp, rgb
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES, mix, add, damp
from blood_falls import finish, slam_title, face_box
from blood_falls_2 import put_chip, draw_x, stars
import tunguska as TG
from tunguska import chip_t, flash
import taiga

SLUG = 'boiling-river'
GEO_COL = (226, 118, 36)                 # GEOLOGIST label
SCI_COL = (44, 118, 200)                 # SCIENTIST label
GEO_KW = dict(hat='cowboy', shirt='#b89a62', pants='#56604a')
SCI_KW = dict(shirt='#3b6ea0', pants='#34384a')
HOT, RED, COLD = J.HOT, J.RED, J.COLD
HIDE_UI = False                          # thumbnail frames: no chips or titles


def clue(img, txt, u, t0=.05, y=250):
    if HIDE_UI: return
    TG.clue(img, txt, u, t0, y)


def chip(img, txt, fill, x, y, u, t0, size=50, angle=0.0):
    if HIDE_UI: return
    chip_t(img, txt, fill, x, y, u, t0, size=size, angle=angle)


def stitle(img, key, lines, y, u, t0, size=104):
    if HIDE_UI: return
    slam_title(img, key, lines, y, u, t0, size=size)


def geologist(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, rim=(255, 220, 160), rim_dir=(1, -.6),
              bphase=0.0, aura=(255, 190, 110), aura_a=.4, lbl_dy=0):
    """GEOLOGIST (Andrés Ruzo, dramatised): white stickman, wide-brim hat, khaki shirt, olive trousers."""
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=aura, aura_alpha=aura_a, rim=rim, rim_dir=rim_dir,
              bphase=bphase, **GEO_KW)
    if label_on and not HIDE_UI:
        hx, hy = g['head']
        label(img, 'GEOLOGIST', min(W - 190, max(190, hx)), hy - g['R'] * 1.7 - 96 + lbl_dy, GEO_COL, size=int(48 * max(.9, min(1.1, s))))
    return g


def scientist(img, t, pose, expr, cx, gy, s, look=0.0, lean=0.0, hop=0.0, label_on=True, rim=(200, 230, 255), rim_dir=(-.5, -1),
              bphase=.4, aura=(120, 180, 255), aura_a=.35, lbl_dx=0):
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, hop=hop, aura=aura, aura_alpha=aura_a, rim=rim, rim_dir=rim_dir,
              bphase=bphase, **SCI_KW)
    if label_on and not HIDE_UI:
        hx, hy = g['head']
        label(img, 'SCIENTIST', min(W - 180, max(180, hx + lbl_dx)), hy - g['R'] * 1.4 - 92, SCI_COL, size=int(48 * max(.9, min(1.1, s))))
    return g


_tl = {}
def tlayer(key, lines, size):
    if key not in _tl: _tl[key] = anim.text_layer(lambda l: title(l, lines, 60, size=size), W, int(sum((x[2] if len(x) > 2 else size) for x in lines) * 1.3 + 140))
    return _tl[key]


_fr = {}
def frog_layer(s, look=0.0, blink=False, splay=0.0):
    k = (round(s, 2), round(look, 1), blink, round(splay, 1))
    if k not in _fr:
        if len(_fr) > 80: _fr.clear()
        _fr[k] = J.frog(s, look, blink, splay)
    return _fr[k]


# ---------------------------------------------------------------- s01 (and the loop end): the boiling river
ROOT = [(-80, 1260), (120, 1150), (330, 1080), (500, 1052), (640, 1058), (700, 1072)]
FROG_X, FROG_Y = 545, 1052                # where the frog sits on the root (feet)


def root_branch(img, u, dip=0.0):
    """A mossy root/branch reaching over the river from the left bank (dips a little when the frog slips)."""
    d = ImageDraw.Draw(img)
    pts = [(x, y + dip * (max(0, x - 100) / 600) ** 2) for x, y in ROOT]
    for w, c in ((60, INK), (48, (110, 82, 58)), (14, (150, 118, 84))):
        d.line(pts if c != (150, 118, 84) else [(x, y - 12) for x, y in pts], fill=c, width=w, joint='curve')
    for i, (x, y) in enumerate(pts[1:-1]):                                 # moss tufts + small leaves
        d.ellipse([x - 40, y - 34, x + 30, y - 6], fill=(84, 150, 66), outline=INK, width=3)
        J.broad_leaf(d, x - 10, y + 10, 70, 110 + 20 * math.sin(u * 1.3 + i), iw=3)
    return pts


def frog_state(u, cue):
    """(x, y, angle, splay, look) of the frog in s01. Idle, slips on 'animals', scrabbles, lets go after 'fall'."""
    t_slip, t_go = cue(10) + .1, cue(15) + .15
    x, y, ang, splay, look = FROG_X, FROG_Y, 0.0, 0.0, 0.0
    hop = 0.0
    if u < t_slip:
        y += -2 * math.sin(u * 7)                                         # throat breathing
        look = .3 * math.sin(u * .9)
    elif u < t_go:
        v = (u - t_slip) / (t_go - t_slip)
        x += 120 * smooth(v); y += 6 * smooth(v) + 4 * math.sin(u * 30) * (v < .9)
        ang = -14 * smooth(v) - 6 * math.sin(u * 22)                       # tipping forward, scrabbling
        splay = .3 + .4 * abs(math.sin(u * 14))
        look = 1.0
    else:
        v = u - t_go
        x += 120 + 160 * v; y += 6 + 120 * v + 560 * v * v
        ang = -14 - 60 * v; splay = 1.0; look = 1.0
    return x, y, ang, splay, look


def s01_world(u, cam=0.0, frog=None, steam_k=1.0, geo=None, walls_y1=1300):
    """The opening framing (also the loop's last frame). Moves: steam rolls, bubbles pop, flow streaks, fronds
    and vines sway, rays drift."""
    img = Image.new('RGBA', (W, H))
    J.jungle_back(img, u, cam, horizon=780, sun=(840, 240))
    # far bank: dense trees down to the water
    fb = J.canopy_layer(21, 900, [(26, 60, 110, ((48, 100, 66), (70, 128, 80), (100, 160, 90)), True, (70, 56, 44), 0)])
    img.alpha_composite(fb, (int(-200 + cam * .6), 0))
    poly = J.river_band(img, u, 900, 1960, x_far=(-100, 1180), x_near=(-400, W + 400), cam=cam, heat=1.0)
    radial(img, 560 + cam * .5, 960, 620, (255, 170, 90), .28 + .05 * math.sin(u * 2.3))      # heat glow on the water
    J.boil(img, u, [(180 + cam, 1330, 70), (800 + cam, 1250, 60), (470 + cam, 1500, 95), (930 + cam, 1560, 90),
                    (300 + cam, 1760, 120), (760 + cam, 1820, 120), (640 + cam, 1130, 45), (120 + cam, 1110, 40)], seed=12)
    J.bubbles(img, u, poly, n=90, seed=3, rate=1.7, size=(14, 80))
    J.steam(img, u, [(-60, 520, 930), (480, 1140, 940), (-60, 1140, 1000), (-60, 1140, 1150), (0, 1080, 1400)], rise=820,
            dens=1.3 * steam_k, seed=7, n=90, size=(70, 190), wind=50, warm=.12)
    # near bank, bottom left, with ferns
    d = ImageDraw.Draw(img); c = cam * 1.2
    J.ground_bank(img, [(-60 + c, 1560), (120 + c, 1600), (300 + c, 1700), (420 + c, 1820), (470 + c, 1990), (-60 + c, 1990)])
    d = ImageDraw.Draw(img)
    for i in range(4):
        J.frond(d, -20 + c + i * 90, 1700 + i * 60, 300, -50 + i * 8, u, sway=4 * math.sin(u * 1.1 + i), droop=.5)
    root_branch(img, u, dip=(frog[4] if frog else 0.0))
    if frog:
        x, y, ang, splay, _dip, look = frog
        fl = frog_layer(.95, look=look, blink=anim.blink(u, 2.7, .4) and splay < .1, splay=splay)
        anim.scaled_paste(img, fl, x + cam * .9, y - fl.height * (230 / 300) + fl.height / 2, 1.0, angle=-ang)
    J.wisps(img, u, (0, 1000, W, 1700), n=26, a=170)
    d = ImageDraw.Draw(img)
    J.side_walls(img, u, cam, seed=4, left=True, right=True, y0=-60, y1=walls_y1)
    J.vines(img, u, [120, 260, 830, 960], y1=700, cam=cam * 1.3)
    J.side_walls(img, u, cam, seed=9, left=False, right=True, y0=1350, y1=1980, scale=1.1)
    if geo: geo(img)
    dust(img, 3, 30, (0, 400, W, 1500), (255, 250, 220), 120, size=(2, 5), t=u)
    return img


def opening_title(img, u, t_punch):
    if HIDE_UI: return
    k = 1.0 + .12 * math.exp(-max(0, u - t_punch) * 9) * (u >= t_punch) + .006 * math.sin(u * 2.4)
    lay, _ = tlayer('open', [('THIS RIVER', 'white', 128), ('BOILS', (255, 120, 50), 210)], 128)
    anim.scaled_paste(img, lay, 540, 330, k)


def s01(u, D, cue):
    cam = 10 * math.sin(u * .5) * smooth(u / .8)
    fx, fy, ang, splay, look = frog_state(u, cue)
    dip = 14 * smooth(seg(u, cue(10), cue(12)))
    img = s01_world(u, cam, frog=(fx, fy, ang, splay, dip, look))
    tp = cue(6) - .05                                                    # "river": the title punches
    sx, sy = shake(u, tp, 7, .3)
    img = finish(img, u, 1.0 + .06 * smooth(u / D), 560, 1100, dx=sx, dy=sy, vig=(.3, (20, 40, 30)))
    opening_title(img, u, tp)
    return img, {'faces': [], 'avoid': [(0, 140, W, 560), (fx - 220, fy - 220, fx + 260, fy + 120)]}


# ---------------------------------------------------------------- s02: "scientists called it a legend"
def study(img, u, cam=0.0):
    img.paste(vgrad([(0, (70, 50, 40)), (.6, (104, 76, 56)), (1, (60, 42, 34))]))
    radial(img, 760 + cam * .5, 560, 760, (255, 200, 130), .45 + .03 * math.sin(u * 3))
    d = ImageDraw.Draw(img); rng = np.random.default_rng(5)
    for side, x0 in ((0, -40), (1, 760)):                                # bookshelves
        x0 += cam * .6
        d.rectangle([x0, 140, x0 + 360, 1500], fill=(64, 42, 30), outline=INK, width=8)
        for j in range(6):
            y = 180 + j * 210
            d.rectangle([x0 + 10, y + 180, x0 + 350, y + 200], fill=(90, 62, 44), outline=INK, width=4)
            x = x0 + 24
            while x < x0 + 330:
                bw = rng.uniform(22, 44); bh = rng.uniform(120, 170)
                c = [(150, 60, 50), (60, 90, 130), (180, 150, 80), (70, 110, 80), (120, 80, 120)][int(rng.uniform(0, 5))]
                d.rectangle([x, y + 180 - bh, x + bw, y + 180], fill=c, outline=INK, width=3)
                d.line([(x + 4, y + 180 - bh + 20), (x + bw - 4, y + 180 - bh + 20)], fill=(230, 210, 150), width=3)
                x += bw + 2
    # a framed old map on the back wall (the Amazon)
    mx = 400 + cam * .4
    d.rectangle([mx, 300, mx + 300, 560], fill=(214, 196, 150), outline=INK, width=8)
    d.line([(mx + 30, 360), (mx + 120, 430), (mx + 180, 410), (mx + 270, 500)], fill=(80, 140, 180), width=6)
    d.text((mx + 150, 520), 'AMAZON', font=font(28, True), fill=(110, 80, 50), anchor='mm')
    dust(img, 6, 40, (300, 200, 1080, 1300), (255, 230, 180), 120, size=(2, 5), t=u)


def book(img, x, y, u, kclose, kstamp, flip_t):
    """An old book on the desk: open (a sketch of a steaming river) until kclose, then shut with LEGEND stamped."""
    d = ImageDraw.Draw(img)
    pw, ph = 250, 300
    if kclose < 1:
        L = [(x - pw, y - ph * .2), (x, y), (x, y + ph * .8), (x - pw, y + ph * .6)]
        Rw = pw * (1 - 2 * kclose)                                       # the right page flips over (shrinks then mirrors)
        R = [(x, y), (x + Rw, y - ph * .2), (x + Rw, y + ph * .6), (x, y + ph * .8)]
        d.polygon([(p[0] + 8, p[1] + 10) for p in L], fill=INK)
        d.polygon(L, fill=(236, 222, 186), outline=INK, width=5)
        d.polygon(R, fill=(226, 210, 172) if Rw > 0 else (130, 60, 44), outline=INK, width=5)
        if kclose < .3:                                                  # the sketch: a river with steam curls
            d.line([(x - pw + 30, y + 150), (x - 140, y + 130), (x - 40, y + 170)], fill=(70, 120, 140), width=6)
            for j in range(3):
                bx = x - pw + 60 + j * 60
                d.arc([bx, y + 40 - 10 * math.sin(u * 4 + j), bx + 40, y + 120], 200, 340, fill=(110, 110, 110), width=4)
            for j in range(6):
                d.line([(x + 30, y + 20 + j * 34), (x + pw - 40, y + 4 + j * 34)], fill=(150, 130, 100), width=4)
    else:
        C = [(x - pw, y - ph * .2), (x, y), (x, y + ph * .8), (x - pw, y + ph * .6)]
        C = [(p[0] + pw * .5, p[1] - 30 * math.exp(-(u - flip_t) * 12)) for p in C]
        d.polygon([(p[0] + 10, p[1] + 12) for p in C], fill=INK)
        d.polygon(C, fill=(130, 60, 44), outline=INK, width=6)
        d.polygon([(p[0] + (x + pw * .5 - p[0]) * .1, p[1] + 14) for p in C[:2]] + [C[2], C[3]], outline=(220, 180, 100), width=3)
        if kstamp > .01 and not HIDE_UI:
            st = TG_stamp()
            anim.scaled_paste(img, st, x, y + 100, kstamp, angle=-14)


_st = {}
def TG_stamp():
    if 's' not in _st: _st['s'] = props.stamp('LEGEND', (214, 50, 40), 70, check=False)
    return _st['s']


def s02(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -14 * smooth(u / D)
    study(img, u, cam)
    tc = cue(6) - .25                                                    # "legend": the book shuts, LEGEND stamps
    shake_head = smooth(seg(u, cue(3) - .2, cue(3))) * (1 - smooth(seg(u, tc, tc + .3)))
    look = .45 * math.sin((u - cue(3)) * 11) * shake_head + .4 * smooth(seg(u, tc - .2, tc))
    reach = smooth(seg(u, tc - .25, tc + .05))
    pose = mix(POSES['stand'], dict(POSES['stand'], armR=(-70, -100)), reach)
    pose = add(pose, armL=(10 * shake_head, 30 * shake_head))
    g = scientist(img, u, pose, 'neutral' if u < tc else 'determined', 400 + cam * .9, 1700, .82, look=look,
                  lean=2 * reach)
    d = ImageDraw.Draw(img)                                              # the desk in front (hides the legs)
    d.polygon([(-40, 1360), (W + 40, 1360), (W + 40, 1440), (-40, 1440)], fill=(120, 80, 54), outline=INK, width=8)
    d.rectangle([-40, 1440, W + 40, H], fill=(84, 56, 40), outline=INK, width=6)
    for x0 in (60, 560):                                                 # drawers with brass handles
        d.rectangle([x0 + cam, 1500, x0 + 440 + cam, 1680], fill=(100, 68, 48), outline=INK, width=6)
        d.rectangle([x0 + cam, 1720, x0 + 440 + cam, 1900], fill=(100, 68, 48), outline=INK, width=6)
        for yy in (1590, 1810):
            d.rounded_rectangle([x0 + 180 + cam, yy - 12, x0 + 260 + cam, yy + 12], 10, fill=(214, 170, 80), outline=INK, width=4)
    # papers and an inkwell on the desk top (left), a reading lamp
    for j in range(3):
        d.polygon([(70 + j * 14 + cam, 1352 - j * 6), (300 + j * 14 + cam, 1340 - j * 6), (310 + j * 14 + cam, 1380 - j * 6),
                   (80 + j * 14 + cam, 1392 - j * 6)], fill=(240, 228, 200), outline=INK, width=3)
    d.ellipse([330 + cam, 1330, 380 + cam, 1380], fill=(40, 40, 60), outline=INK, width=4)
    d.line([(360 + cam, 1336), (400 + cam, 1250)], fill=(240, 240, 240), width=5)
    radial(img, 760, 1300, 300, (255, 210, 140), .35)
    kclose = smooth(seg(u, tc, tc + .22))
    book(img, 820 + cam, 1170, u, kclose, pop(u, tc + .24, .3, 2.2), tc + .22)
    sx, sy = shake(u, tc + .24, 6, .25)
    img = finish(img, u, 1.04 + .04 * smooth(u / D), 600, 1000, dx=sx, dy=sy, vig=(.4, (30, 16, 10)))
    chip(img, 'FOR YEARS', (120, 80, 50), 540, 150, u, .05, size=50)
    return img, {'faces': [face_box(g, 1.25)], 'avoid': [(0, 90, W, 220), (560, 1100, 1060, 1500)]}


# ---------------------------------------------------------------- s03a: the geologist goes to see it (line 3, 0-9)
_wc = {}
def walk_x(u, t_walk, x_end, s):
    if t_walk not in _wc: _wc[t_walk] = anim.walk_track(t_walk)
    tr = _wc[t_walk]; f = min(len(tr) - 1, int(round(min(u, t_walk) * 30)))
    return x_end + tr[f] * s


def forest_floor(img, u, cam, y=1560):
    d = ImageDraw.Draw(img)
    pts = [(x, y + 20 * math.sin(x * .01) ) for x in range(-60, W + 80, 40)]
    d.polygon([(p[0] + cam, p[1]) for p in pts] + [(W + 80, H), (-60, H)], fill=(78, 62, 44), outline=INK, width=6)
    d.line([(p[0] + cam, p[1] + 4) for p in pts], fill=(90, 150, 70), width=18)
    rng = np.random.default_rng(8)
    for i in range(16):
        x = rng.uniform(-50, W + 50) + cam; yy = y + rng.uniform(60, 330)
        d.ellipse([x - 20, yy - 8, x + 20, yy + 8], fill=(110, 86, 60))


def s03a(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -60 * smooth(u / D)
    J.jungle_back(img, u, cam, horizon=980, sun=(900, 300))
    # the river is ahead (right): steam rising above the trees
    J.steam(img, u, [(700, 1200, 1150)], rise=900, dens=.8, seed=11, n=34, size=(70, 170), wind=-30, warm=.1)
    mid = J.canopy_layer(31, 1300, [(22, 80, 150, ((40, 86, 56), (60, 116, 70), (92, 150, 84)), True, (66, 52, 40), 0)])
    img.alpha_composite(mid, (int(-200 + cam * .7), 0))
    d = ImageDraw.Draw(img)                                              # the river glimpsed ahead, steaming
    d.polygon([(560 + cam * .7, 1340), (1100, 1320), (1100, 1400), (600 + cam * .7, 1390)], fill=(140, 206, 192), outline=INK, width=4)
    J.boil(img, u, [(820 + cam * .7, 1365, 30), (980 + cam * .7, 1360, 34)], seed=31)
    J.steam(img, u, [(600, 1180, 1340)], rise=1000, dens=1.3, seed=12, n=50, size=(70, 190), wind=-30, warm=.15)
    radial(img, 900, 1250, 360, (255, 170, 100), .3)
    forest_floor(img, u, cam)
    d = ImageDraw.Draw(img)                                              # a trail toward the steam (right)
    d.polygon([(-60 + cam, 1990), (420 + cam, 1990), (980 + cam * .8, 1590), (820 + cam * .8, 1575)], fill=(150, 120, 84), outline=INK, width=4)
    kit.light_rays(img, 900, 120, (255, 250, 210), n=7, alpha=.22, spread=(100, 140), length=1900, seed=8, phase=2 * math.sin(u * .4))
    for i, x in enumerate((60, 1010)):                                   # big trunks in the mid-ground
        xx = x + cam * .9
        d.polygon([(xx - 40, -20), (xx + 40, -20), (xx + 56, 1580), (xx - 60, 1580)], fill=(92, 70, 52), outline=INK, width=6)
        d.line([(xx - 10, 0), (xx - 4, 1560)], fill=(120, 96, 70), width=10)
        d.polygon([(xx - 60, 1580), (xx - 130, 1610), (xx - 40, 1560)], fill=(92, 70, 52), outline=INK, width=4)
    J.vines(img, u, [200, 470, 760], y1=1000, cam=cam * .9)
    t_walk = 2.3; s = 1.08
    if u <= t_walk:
        pose = anim.walk_pose(u); x = walk_x(u, t_walk, 360, s * .5); lean = 4; look = .7; expr = 'determined'
    else:
        v = u - t_walk; last = anim.walk_pose(t_walk)
        pose = mix(last, POSES['stand'], smooth(v / .35)); sw = damp(v, 12, 4.5, 14)
        pose = add(pose, armL=(sw, sw * 1.4), armR=(-sw, -sw * 1.4))
        if v < .25: pose['_side'] = True
        x = walk_x(t_walk, t_walk, 360, s * .5) + 8 * smooth(v / .4); lean = 4 * (1 - smooth(v / .5)) + 2 * math.sin(v * 1.3)
        look = .7; expr = 'determined'
    x += cam * 1.0
    g = geologist(img, u, pose, expr, x, 1780, s, look=look, lean=lean)
    d = ImageDraw.Draw(img)
    for i in range(5):                                                   # foreground ferns
        J.frond(d, -40 + i * 270 + cam * 1.5, 1950, 360, -70 - 10 * (i % 2) + 140 * (i % 2 == 1) * 0, u, sway=5 * math.sin(u + i), droop=.4)
    J.side_walls(img, u, cam, seed=12, left=True, right=False, y0=0, y1=900)
    dust(img, 5, 30, (0, 300, W, 1500), (255, 250, 220), 120, size=(2, 5), t=u)
    img = finish(img, u, 1.03 + .03 * smooth(u / D), 540, 1100, vig=(.32, (20, 40, 26)))
    stitle(img, 's03a_y', [('2011', 'white', 150)], 160, u, cue(2) - .08)
    chip(img, 'ANDRÉS RUZO', (40, 40, 50), min(W - 200, max(200, g['head'][0])), g['head'][1] - g['R'] * 1.7 - 160, u, cue(4) - .08, size=40)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 120, W, 360)]}


# ---------------------------------------------------------------- s03b: the thermometer (line 3, 10-18)
def bank_scene(img, u, cam, warm=0.0, steam_k=1.0, horizon=760):
    J.jungle_back(img, u, cam, horizon=horizon, sun=(760, 240), warm=warm)
    fb = J.canopy_layer(41, horizon + 140, [(26, 60, 110, ((48, 100, 66), (70, 128, 80), (100, 160, 90)), True, (70, 56, 44), 0)])
    img.alpha_composite(fb, (int(-200 + cam * .6), 0))
    poly = J.river_band(img, u, horizon + 140, 1960, x_far=(-100, 1180), x_near=(-300, W + 300), cam=cam, heat=1.0,
                        cols=J.JADE if not warm else ((236, 180, 150), (150, 120, 140), (70, 60, 100)))
    J.boil(img, u, [(560 + cam, 1300, 70), (900 + cam, 1420, 90), (760 + cam, 1700, 110), (1000 + cam, 1820, 110),
                    (400 + cam, 1150, 50), (840 + cam, 1110, 45)], seed=14)
    J.bubbles(img, u, poly, n=50, seed=5, rate=1.5, size=(10, 50))
    J.steam(img, u, [(-60, 1140, horizon + 150), (-60, 1140, horizon + 380)], rise=700, dens=steam_k, seed=13, n=56,
            size=(60, 160), wind=30, warm=warm * .6 + .1)
    return poly


def s03b(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 8 * math.sin(u * .4)
    bank_scene(img, u, cam, steam_k=.9)
    c = cam * 1.2
    J.ground_bank(img, [(-60 + c, 1480), (260 + c, 1520), (470 + c, 1600), (600 + c, 1720), (680 + c, 1990), (-60 + c, 1990)])
    td = cue(11) - .2                                                    # "dipped"
    kd = smooth(seg(u, td, td + .45))
    pose = mix(POSES['stand'], dict(POSES['stand'], armR=(-38, -18)), kd)
    pose = add(pose, armL=(6 * kd, 10 * kd))
    g = geologist(img, u, pose, 'thinking' if u < cue(16) else 'surprised', 250 + c, 1640, .82, look=.55, lean=5 * kd,
                  hop=10 * math.exp(-max(0, u - cue(16)) * 6) * (u > cue(16)))
    hx, hy, ha = g['hands']['R']
    d = ImageDraw.Draw(img)                                              # the probe thermometer into the water
    px, py = hx + 150 * kd + 20, hy + 220 * kd + 40
    d.line([(hx, hy), (px, py)], fill=INK, width=16); d.line([(hx, hy), (px, py)], fill=(220, 226, 230), width=8)
    d.ellipse([hx - 18, hy - 18, hx + 18, hy + 18], fill=(246, 246, 242), outline=INK, width=4)
    if kd > .5:
        for j in range(2):
            v = (u * 1.2 + j * .5) % 1; r = 20 + 60 * v
            d.ellipse([px - r, py - r * .35, px + r, py + r * .35], outline=(240, 255, 250), width=max(1, int(5 * (1 - v))))
    # the big read-out thermometer (right)
    lvl = .1 + .89 * smooth(seg(u, cue(14) - .1, cue(17) + .1)) + .006 * math.sin(u * 9)
    J.steam(img, u, [(560, 1100, 1700)], rise=500, dens=.4, seed=17, n=16, size=(50, 120), wind=-20)
    sx, sy = shake(u, cue(17) - .05, 9, .35)
    img = finish(img, u, 1.03 + .04 * smooth(u / D), 540, 1200, dx=sx, dy=sy, vig=(.32, (20, 40, 30)))
    if not HIDE_UI or True:
        top = J.thermometer(img, 880, 420, 960, lvl, u, w=82, fs=40, label_side=-1)
    stitle(img, 's03b_t', [('NEARLY', 'white', 96), ('100°C', (255, 110, 50), 170)], 120, u, cue(16) - .1)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(0, 80, W, 460), (700, 380, 1060, 1500)]}


# ---------------------------------------------------------------- s04: the obvious answer, a volcano underneath (line 4)
def surface_section(img, u, cam, ground=760, river=(260, 820), depth=120, ft=.55, cold_left=False, hot=1.0, horizon=470,
                    bands=6, steam_k=.8, dark=0.0):
    """Side cutaway: jungle and sky above, a river channel cut into the ground, strata below. Returns the
    river bed points."""
    J.jungle_back(img, u, cam, horizon=horizon, sun=(840, 160), rays=False)
    fb = J.canopy_layer(51, ground + 10, [(26, 50, 100, ((44, 96, 62), (66, 124, 76), (98, 158, 88)), True, (70, 56, 44), 0)])
    img.alpha_composite(fb, (int(-200 + cam * .6), 0))
    J.earth_section(img, u, ground, H, cam, n=bands, ft=ft, dark=dark, glow_bottom=dark < .3)
    d = ImageDraw.Draw(img)
    d.rectangle([-10, ground - 14, W + 10, ground + 10], fill=(84, 140, 64), outline=INK, width=5)
    x0, x1 = river
    bed = [(x0 - 40, ground), (x0 + 30, ground + depth * .8), (x0 + 120, ground + depth), (x1 - 120, ground + depth),
           (x1 - 30, ground + depth * .8), (x1 + 40, ground)]
    d.polygon(bed, fill=(70, 52, 40), outline=INK, width=6)
    water = [(x0 - 22, ground + 16)] + bed[1:-1] + [(x1 + 22, ground + 16)]
    wl = layer(); dw = ImageDraw.Draw(wl)
    if cold_left:
        mid = (x0 + x1) / 2
        for i in range(40):
            xa = x0 - 30 + (x1 - x0 + 60) * i / 40; f = smooth((xa - (mid - 80)) / 200)
            dw.rectangle([xa, ground + 14, xa + (x1 - x0 + 60) / 40 + 1, ground + depth + 10], fill=lerp(J.COLD, (120, 200, 180), f) + (255,))
    else:
        dw.rectangle([x0 - 40, ground + 14, x1 + 40, ground + depth + 10], fill=(110, 196, 180, 255))
    wm = mask(); ImageDraw.Draw(wm).polygon(water, fill=255)
    img.paste(wl, (0, 0), wm)
    d = ImageDraw.Draw(img)
    for i in range(6):                                                   # surface ripples
        xx = x0 + (x1 - x0) * ((i / 6 + u * .2) % 1)
        d.line([(xx - 30, ground + 24), (xx + 30, ground + 24)], fill=(230, 250, 245), width=4)
    d.line(water[0:1] + water[-1:], fill=(220, 245, 240), width=5)
    return bed


def s04(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 6 * math.sin(u * .5)
    bed = surface_section(img, u, cam, ground=700, river=(250, 830), depth=130, ft=.45, dark=.85)
    tv = cue(4) - .2                                                     # "volcano": the imagined volcano glows in
    kv = smooth(seg(u, tv, tv + .5))
    if kv > 0:
        radial(img, 540, 1500, 700, (255, 80, 40), .35 * kv + .06 * kv * math.sin(u * 4))
        m = mask(); ImageDraw.Draw(m).line([(540, 1100), (540, 840)], fill=int(255 * kv), width=30)
        glow(img, m, (255, 140, 60), .7, blur=18)
        taiga.dashed(ImageDraw.Draw(img), (540, 1100), (540, 840), (255, 200, 140), w=10, dash=22, gap=12, phase=u * 60)
        radial(img, 540, 1100, 160, (255, 210, 130), .7 * kv)
        J.volcano_icon(img, 540, 1800, 2.7, u, ghost=True, wr=.75, alpha=kv * (.85 + .1 * math.sin(u * 5)), smoke_on=False)
    J.steam(img, u, [(260, 820, 700)], rise=520, dens=.8, seed=19, n=30, size=(50, 130), wind=20)
    J.bubbles(img, u, [(250, 704), (830, 704), (830, 740), (250, 740)], n=20, seed=6, size=(6, 16))
    sx, sy = shake(u, tv + .05, 10, .4)
    img = finish(img, u, 1.02 + .04 * smooth(u / D), 540, 1000, dx=sx, dy=sy, vig=(.38, (30, 10, 10)))
    chip(img, 'THE OBVIOUS ANSWER?', (90, 70, 60), 540, 170, u, cue(1) - .05, size=50)
    if kv > 0 and not HIDE_UI:
        stitle(img, 's04_v', [('VOLCANO?', (255, 150, 90), 130)], 1120, u, tv + .1)
    return img, {'faces': [], 'avoid': [(0, 100, W, 240), (100, 1080, 980, 1300)]}


# ---------------------------------------------------------------- s05: 700 km away (line 5)
def s05(u, D, cue):
    img = Image.new('RGBA', (W, H))
    J.peru_map(img, u)
    rx, ry = J.ll(J.RIVER_LL); vx, vy = J.ll(J.VOLC_LL)
    # the imagined volcano under the river (small, ghost) until "away", then it breaks
    tb = cue(10) - .05
    kb = smooth(seg(u, tb, tb + .4))
    J.volcano_icon(img, rx + 150, ry + 50, .7, u, ghost=True, alpha=1 - .25 * kb, smoke_on=False)
    J.map_pin(img, rx, ry, u, HOT, 1.0)
    tv = cue(4) - .15
    kv = pop(u, tv, .35, 2)
    if kv > 0:
        J.volcano_icon(img, vx, vy + 40, .42 * min(1.2, kv), u, smoke_on=True)
    tr = cue(7) - .15                                                    # "seven hundred": the ruler draws
    kr = smooth(seg(u, tr, tr + .6))
    if kr > 0:
        d = ImageDraw.Draw(img)
        ex, ey = rx + (vx - rx) * kr, ry + (vy - ry) * kr
        d.line([(rx, ry), (ex, ey)], fill=INK, width=16)
        taiga.dashed(d, (rx, ry), (ex, ey), (255, 236, 160), w=8, dash=26, gap=12, phase=u * 40)
        L = math.dist((rx, ry), (vx, vy)); nx, ny = -(vy - ry) / L, (vx - rx) / L
        for f in (0, kr):
            px, py = rx + (vx - rx) * f, ry + (vy - ry) * f
            d.line([(px - nx * 26, py - ny * 26), (px + nx * 26, py + ny * 26)], fill=(255, 236, 160), width=8)
    if kb > 0:                                                           # the ghost breaks: shards fly, a red X
        d = ImageDraw.Draw(img)
        for j in range(7):
            a = -math.pi / 2 + (j - 3) * .45; dd = 160 * ease_out(kb)
            px, py = rx + 150 + math.cos(a) * dd, ry - 40 + math.sin(a) * dd + 200 * kb * kb
            d.polygon([(px, py - 18), (px + 16, py + 6), (px - 12, py + 14)], fill=(255, 140, 90, 0) if False else (255, 140, 90), outline=INK, width=3)
    sx, sy = shake(u, tb, 8, .3)
    img = finish(img, u, 1.08 - .06 * smooth(u / D), (rx + vx) / 2, (ry + vy) / 2, dx=sx, dy=sy, vig=(.3, (20, 40, 60)))
    if not HIDE_UI:
        chip(img, 'BOILING RIVER', (200, 90, 30), rx - 130, ry - 100, u, .1, size=42)
        if kv > 0: chip(img, 'NEAREST ACTIVE VOLCANO', (150, 40, 34), 560, vy + 150, u, tv, size=40)
        if kr > .6: chip(img, '≈ 700 KM', (30, 30, 40), (rx + vx) / 2 - 150, (ry + vy) / 2, u, tr + .45, size=64)
        if not HIDE_UI and u < tb + .1: chip(img, 'VOLCANO?', (150, 60, 40), rx + 150, ry + 90, u, .2, size=34)
        if kb > 0: draw_x(img, rx + 150, ry - 40, 80, seg(u, tb, tb + .4) * 2, w=18)
    return img, {'faces': [], 'avoid': [(rx - 240, ry - 170, rx + 200, ry + 60), (200, vy + 90, 920, vy + 210),
                                         (vx - 120, vy - 160, vx + 120, vy + 60), (160, 1000, 700, 1140)]}


# ---------------------------------------------------------------- s06: CLUE 1, it starts cold (line 6)
WORLD6 = 1920
RPATH = [(560, -60), (500, 160), (600, 340), (480, 540), (560, 760), (650, 960), (480, 1180), (560, 1400), (680, 1620),
         (540, 1840), (560, 2000)]


def _smooth_path(pts, n=8):
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(len(pts) - 1, i + 2)]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                   (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1]); return out


def heat6(y): return smooth((y - 760) / 640)


def topdown_canopy():
    def mk():
        lay = layer(W, WORLD6); d = ImageDraw.Draw(lay); rng = np.random.default_rng(61)
        d.rectangle([0, 0, W, WORLD6], fill=(40, 84, 52))
        for i in range(900):
            x, y, r = rng.uniform(-40, W + 40), rng.uniform(-40, WORLD6 + 40), rng.uniform(30, 70)
            c = [(52, 108, 62), (70, 130, 70), (90, 150, 80), (60, 120, 90)][i % 4]
            d.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3], fill=INK)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)
            d.ellipse([x - r * .6, y - r * .7, x + r * .1, y - r * .1], fill=lerp(c, (200, 230, 140), .3))
        return lay
    return J.cached('td6', mk)


def river_path_draw(img, pts, wfn, colfn, oy, u, ink=INK):
    d = ImageDraw.Draw(img)
    vis = [(x, y) for x, y in pts if -300 < y - oy < H + 300]
    for x, y in vis:
        r = wfn(y) / 2 + 9; d.ellipse([x - r, y - oy - r, x + r, y - oy + r], fill=(150, 122, 90))
    for x, y in vis:
        r = wfn(y) / 2 + 3 + 5; d.ellipse([x - r + 3, y - oy - r + 3, x + r - 3, y - oy + r - 3], fill=ink)
    for x, y in vis:
        r = wfn(y) / 2; c = colfn(y); d.ellipse([x - r, y - oy - r, x + r, y - oy + r], fill=c)
    # flow streaks
    n = len(pts)
    for i in range(70):
        s = (i / 70 + u * .04) % 1; k = int(s * (n - 1)); x, y = pts[k]
        if not (-50 < y - oy < H + 50): continue
        w = wfn(y); off = ((i * 37) % 10 / 10 - .5) * w * .7
        d.line([(x + off, y - oy - 14), (x + off + 3, y - oy + 14)], fill=(240, 255, 255), width=4)


def s06(u, D, cue):
    """The whole river in one frame: a thin blue stream at the top, wide, orange and steaming at the bottom. The
    camera starts close on the cold source and pulls back down the river ("farther down")."""
    pts = _smooth_path(RPATH, 10)
    img = Image.new('RGBA', (W, H))
    img.alpha_composite(topdown_canopy().crop((0, 0, W, H)))
    wf = lambda y: 18 + 270 * max(0, min(1, (y + 60) / 1980)) ** 1.4
    cf = lambda y: lerp((60, 150, 236), (244, 140, 80), heat6(y))
    river_path_draw(img, pts, wf, cf, 0, u)
    radial(img, 560, 1600, 700, HOT, .35 + .05 * math.sin(u * 3))
    src = [(x - wf(y) * .5, x + wf(y) * .5, y + 40) for x, y in pts[::5] if heat6(y) > .3]
    J.steam(img, u, src, rise=240, dens=1.3, seed=23, n=80, size=(40, 120), rate=.35, wind=60, warm=.15, alpha=.85)
    J.bubbles(img, u, [(330, 1500), (760, 1500), (800, 1950), (300, 1950)], n=30, seed=4, size=(8, 22))
    lc = .22 + .03 * math.sin(u * 3); lh = .95 + .02 * math.sin(u * 4)
    kz = smooth(seg(u, cue(11) - .6, cue(16) + .2))
    img = finish(img, u, 1.3 - .3 * kz, 540, 520 + 440 * kz, vig=(.35, (10, 30, 20)))
    clue(img, 'CLUE 1', u)
    if not HIDE_UI:
        z = 1.3 - .3 * kz; fy = 520 + 440 * kz
        Y = lambda y: fy + (y - fy) * z
        Xx = lambda x: 540 + (x - 540) * z
        chip(img, 'COLD STREAM', (40, 120, 200), Xx(300), Y(560), u, cue(8) - .1, size=48)
        chip(img, 'HOT', (220, 70, 30), Xx(870), Y(1640), u, cue(14) - .1, size=70)
    return img, {'faces': [], 'avoid': [(0, 150, W, 360)]}


# ---------------------------------------------------------------- s07: CLUE 2, heat through the cracks (line 7)
def _jag(F, seed, amp=18, n=5):
    rng = np.random.default_rng(seed); out = []
    for a, b in zip(F, F[1:]):
        for k in range(n):
            f = k / n; j = rng.uniform(-amp, amp) if k else 0
            out.append((a[0] + (b[0] - a[0]) * f + j, a[1] + (b[1] - a[1]) * f + j * .3))
    return out + [F[-1]]


F1 = [(120, 1960), (330, 1500), (470, 1100), (560, 840)]
F2 = [(1020, 1960), (860, 1480), (700, 1100), (610, 840)]
F3 = [(420, 1960), (430, 1720), (330, 1500)]
F4 = [(700, 1960), (760, 1700), (860, 1480)]
F1, F2, F3, F4 = _jag(F1, 1), _jag(F2, 2), _jag(F3, 3, 12, 3), _jag(F4, 4, 12, 3)


def s07(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 6 * math.sin(u * .4)
    bed = surface_section(img, u, cam, ground=720, river=(120, 980), depth=120, ft=.8, cold_left=True, horizon=470, bands=7)
    d = ImageDraw.Draw(img)
    kc = smooth(seg(u, cue(7) - .4, cue(7) + .3))                         # "cracks": the faults open and glow
    for F in (F1, F2, F3, F4):
        J.fault(d, F, w=(12 if F in (F1, F2) else 7) + 6 * kc)
        if kc > 0:
            m = mask(); ImageDraw.Draw(m).line(F, fill=255, width=26)
            glow(img, m, HOT, .55 * kc + .1 * math.sin(u * 5), blur=22)
            d = ImageDraw.Draw(img)
            d.line(F, fill=lerp((40, 22, 20), (255, 150, 60), kc), width=8, joint='curve')
    if kc > 0:
        J.rising(img, u, F1, n=10, speed=.5, r=(9, 16), seed=2, k=kc)
        J.rising(img, u, F2, n=10, speed=.45, r=(9, 16), seed=3, k=kc)
        J.rising(img, u, F3, n=5, speed=.5, r=(7, 12), seed=4, k=kc)
        J.rising(img, u, F4, n=5, speed=.5, r=(7, 12), seed=5, k=kc)
    # where the faults meet the river: the water turns hot and steams downstream (right)
    hk = smooth(seg(u, cue(3) - .3, cue(4) + .4))
    radial(img, 600, 800, 260, HOT, .5 * hk + .08 * math.sin(u * 6))
    J.bubbles(img, u, [(560, 726), (980, 726), (980, 790), (560, 790)], n=int(26 * hk) + 1, seed=7, size=(6, 18))
    J.steam(img, u, [(560, 980, 720)], rise=520, dens=.3 + .7 * hk, seed=29, n=40, size=(50, 130), wind=30, warm=.15)
    sx, sy = shake(u, cue(13) - .05, 5, .25)
    img = finish(img, u, 1.02 + .04 * smooth(u / D), 560, 900, dx=sx, dy=sy, vig=(.36, (40, 14, 10)))
    clue(img, 'CLUE 2', u)
    if not HIDE_UI:
        chip(img, 'COLD', (40, 120, 200), 260, 650, u, .3, size=40)
        chip(img, 'CRACKS', (60, 40, 36), 300, 1300, u, cue(7) - .1, size=48, angle=-8)
        chip(img, 'FAULTS', (200, 70, 30), 800, 1560, u, cue(13) - .1, size=56, angle=6)
    return img, {'faces': [], 'avoid': [(0, 150, W, 360), (160, 1230, 460, 1380), (620, 1480, 980, 1640)]}


# ---------------------------------------------------------------- s08: CLUE 3, no sign of a volcano (line 8)
def lab_bg(img, u, cam):
    img.paste(vgrad([(0, (206, 228, 230)), (.7, (170, 204, 210)), (1, (120, 150, 160))]))
    d = ImageDraw.Draw(img)
    for i in range(12):                                                  # wall tiles
        for j in range(16):
            x = i * 100 - 40 + cam * .5; y = j * 100
            d.rectangle([x, y, x + 96, y + 96], outline=(186, 212, 216), width=3)
    radial(img, 300, 300, 700, (255, 255, 240), .4)
    d.rectangle([-20, 600 + 0, 460 + cam * .6, 640], fill=(140, 160, 170), outline=INK, width=5)         # shelf
    for k, (x, h, c) in enumerate(((60, 120, (90, 200, 120)), (170, 160, (240, 180, 60)), (300, 100, (120, 160, 240)))):
        props.flask(img, x + cam * .6, 600, h, c, kind=['round', 'tube', 'cone'][k % 3] if False else 'round', glow_on=True)


def s08(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -10 * smooth(u / D)
    lab_bg(img, u, cam)
    d = ImageDraw.Draw(img)
    # the analyser screen (right)
    sx0, sy0, sx1, sy1 = 500 + cam, 520, 1040 + cam, 1220
    m = mask(); ImageDraw.Draw(m).rectangle([sx0, sy0, sx1, sy1], fill=255); glow(img, m, (120, 220, 255), .4, blur=40)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([sx0 - 24, sy0 - 24, sx1 + 24, sy1 + 24], 22, fill=(48, 56, 66), outline=INK, width=8)
    d.rectangle([sx0, sy0, sx1, sy1], fill=(10, 30, 40))
    for y in range(sy0, sy1, 6): d.line([(sx0, y), (sx1, y)], fill=(8, 24, 32))
    d.text((sx0 + 30, sy0 + 40), 'RIVER WATER TEST', font=font(36, True), fill=(140, 230, 240))
    rows = [('VOLCANIC GASES', cue(5)), ('MAGMA MINERALS', cue(6))]
    for i, (nm, t0) in enumerate(rows):
        y = sy0 + 140 + i * 150
        d.text((sx0 + 30, y), nm, font=font(32, True), fill=(200, 230, 235))
        ks = seg(u, t0 - .5, t0 + .2)
        if 0 < ks < 1:                                                   # scanning
            bx = sx0 + 30 + (sx1 - sx0 - 120) * ((u * 2.5) % 1)
            d.rectangle([bx, y + 50, bx + 60, y + 90], fill=(120, 230, 255))
        d.rectangle([sx0 + 30, y + 50, sx1 - 30, y + 90], outline=(80, 140, 150), width=3)
        if ks >= 1:
            d.text((sx0 + 50, y + 70), 'NONE', font=font(34, True), fill=(120, 255, 160), anchor='lm')
    # the volcano icon on the screen, crossed on "no"
    J.volcano_icon(img, (sx0 + sx1) / 2, sy1 - 60, .5, u, smoke_on=True)
    tn = cue(7) - .05
    if not HIDE_UI: draw_x(img, (sx0 + sx1) / 2, sy1 - 150, 110, seg(u, tn, tn + .45) * 2, w=20)
    # the scientist holds up a tube of river water (glowing warm)
    lift = smooth(seg(u, .1, .6))
    pose = mix(POSES['stand'], dict(POSES['stand'], armR=(-100, -150)), lift)
    g = scientist(img, u, pose, 'thinking' if u < tn else 'determined', 250 + cam * .9, 1820, .9, look=.5, lean=2, lbl_dx=-70)
    hx, hy, _ = g['hands']['R']
    tl = layer(); dt = ImageDraw.Draw(tl)
    tx, ty = hx + 6, hy - 150
    mt = mask(); ImageDraw.Draw(mt).rounded_rectangle([tx - 30, ty, tx + 30, ty + 210], 30, fill=255)
    glow(img, mt, (255, 190, 90), .55 + .1 * math.sin(u * 4), blur=30)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([tx - 30, ty, tx + 30, ty + 210], 30, fill=(236, 246, 250), outline=INK, width=6)
    d.rounded_rectangle([tx - 22, ty + 70, tx + 22, ty + 202], 22, fill=(150, 210, 190))
    for j in range(3):
        by = ty + 190 - ((u * 60 + j * 40) % 120); d.ellipse([tx - 6 + j * 4, by - 6, tx + 6 + j * 4, by + 6], outline='white', width=3)
    d.ellipse([hx - 18, hy - 18, hx + 18, hy + 18], fill=(246, 246, 242), outline=INK, width=4)
    d.rectangle([-20, 1820, W + 20, H], fill=(210, 220, 224), outline=INK, width=6)     # bench front
    J.wisps(img, u, (tx - 40, ty - 160, tx + 40, ty), n=4, a=160)
    img = finish(img, u, 1.03 + .03 * smooth(u / D), 540, 1000, vig=(.3, (20, 40, 50)))
    clue(img, 'CLUE 3', u)
    if not HIDE_UI:
        stitle(img, 's08_t', [('NO SIGN OF', 'white', 84), ('A VOLCANO', (255, 120, 60), 100)], 1290, u, tn + .1)
    return img, {'faces': [face_box(g, 1.25)], 'avoid': [(0, 150, W, 360), (sx0 - 30, sy0 - 30, sx1 + 30, sy1 + 30), (0, 1260, W, 1520)]}


# ---------------------------------------------------------------- s09: so how? (line 9) - dusk
def s09(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -16 * smooth(u / D)
    J.jungle_back(img, u, cam, horizon=760, sky=((96, 70, 130), (240, 140, 110)), far=(120, 90, 120), mid=(56, 60, 70),
                  haze_col=(240, 170, 150), sun=(540, 700), rays=False, warm=.2)
    fb = J.canopy_layer(91, 900, [(26, 60, 110, ((40, 40, 56), (56, 54, 70), (80, 70, 86)), True, (40, 34, 40), 0)])
    img.alpha_composite(fb, (int(-200 + cam * .6), 0))
    poly = J.river_band(img, u, 900, 1960, x_far=(-100, 1180), x_near=(-300, W + 300), cam=cam, heat=1.0,
                        cols=((250, 180, 150), (170, 110, 130), (70, 50, 90)))
    radial(img, 540 + cam * .3, 920, 500, (255, 170, 110), .5)
    radial(img, 560 + cam * .3, 1500, 520, (255, 150, 110), .35)
    d = ImageDraw.Draw(img)
    for j in range(9):                                                   # the sun's broken reflection on the water
        y = 960 + j * 70; w_ = 60 + j * 26 + 12 * math.sin(u * 2 + j)
        d.line([(560 - w_ + cam * .3, y), (560 + w_ + cam * .3, y)], fill=(255, 200, 150), width=6 + j)
    J.boil(img, u, [(640, 1250, 70), (900, 1450, 90), (720, 1700, 110), (500, 1500, 80)], seed=19, col=(255, 236, 226))
    J.bubbles(img, u, poly, n=40, seed=9, size=(8, 40), col=(255, 230, 220))
    J.steam(img, u, [(-60, 1140, 920), (-60, 1140, 1150)], rise=820, dens=1.1, seed=31, n=60, size=(60, 170), wind=20,
            col=(255, 226, 220), shade=(170, 120, 150), warm=.3)
    tq = cue(1) - .05                                                    # "how": the question mark rises from the steam
    kq = out_back(seg(u, tq, tq + .5), 1.4)
    if kq > 0 and not HIDE_UI:
        lay, _ = tlayer('q9', [('?', (255, 210, 90), 520)], 520)
        anim.scaled_paste(img, lay, 560 + 10 * math.sin(u * 1.7), 1000 - 260 * kq + 14 * math.sin(u * 2.2), .4 + .6 * kq, angle=4 * math.sin(u))
    c = cam * 1.2
    J.ground_bank(img, [(-60 + c, 1500), (180 + c, 1540), (340 + c, 1660), (420 + c, 1800), (440 + c, 1990), (-60 + c, 1990)],
                  top=(60, 44, 44), mid=(54, 40, 46), moss=(70, 80, 70))
    g = geologist(img, u, 'think', 'thinking', 240 + c, 1720, .9, look=.6, rim=(255, 170, 130), rim_dir=(1, -.3),
                  aura=(255, 140, 110))
    img = finish(img, u, 1.03 + .04 * smooth(u / D), 540, 1100, vig=(.45, (30, 10, 40)))
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(260, 260, 860, 1060), (220, 1440, 980, 1560)]}


# ---------------------------------------------------------------- s10: the Earth itself is the stove (line 10)
def space(img, u):
    img.paste(vgrad([(0, (8, 10, 30)), (1, (24, 18, 50))]))
    stars(img, 3, 140, H, u)
    radial(img, 540, 1050, 900, (60, 80, 160), .35)


def s10(u, D, cue):
    img = Image.new('RGBA', (W, H)); space(img, u)
    cx, cy, r = 540, 1080, 440
    kc = smooth(seg(u, .0, cue(2)))                                        # the wedge opens
    J.globe(img, cx, cy, r, u, cut=.35 + .65 * kc, spin=u * .05)
    # "the deeper you go, the hotter": a probe dives from the surface toward the core along the wedge edge
    kd = smooth(seg(u, cue(7) - .2, cue(14)))
    a = math.radians(-45 - 45 * (.35 + .65 * kc) * 0 - 90 + 45 + 2)  # just inside the left edge of the wedge
    a = math.radians(-90 - 45 * (.35 + .65 * kc) + 45 + 10)
    p0 = (cx + r * math.cos(a), cy + r * math.sin(a)); p1 = (cx + r * .28 * math.cos(a), cy + r * .28 * math.sin(a))
    if kd > 0:
        d = ImageDraw.Draw(img)
        e = (p0[0] + (p1[0] - p0[0]) * kd, p0[1] + (p1[1] - p0[1]) * kd)
        col = J.heat_col(kd)
        J.arrow(d, [p0, e], lerp((150, 220, 255), (255, 90, 40), kd), w=20, head=46)
        m = mask(); ImageDraw.Draw(m).ellipse([e[0] - 50, e[1] - 50, e[0] + 50, e[1] + 50], fill=255)
        glow(img, m, lerp((255, 200, 120), (255, 80, 30), kd), .6 * kd, blur=30)
    zoom = 1.0 + .18 * smooth(seg(u, cue(6), D))
    img = finish(img, u, zoom, cx + 120, cy - 160, vig=(.35, (4, 4, 16)))
    stitle(img, 's10_t', [('THE EARTH IS', 'white', 96), ('THE STOVE', (255, 130, 50), 140)], 150, u, cue(3) - .1)
    if not HIDE_UI:
        if kd > .2: chip(img, 'DEEPER = HOTTER', (200, 70, 30), 540, 1640, u, cue(11) - .1, size=56)
        chip(img, 'VOLCANO OR NOT', (40, 40, 60), 540, 1760, u, cue(15) - .1, size=46)
    return img, {'faces': [], 'avoid': [(0, 100, W, 470), (180, 1580, 900, 1820)]}


# ---------------------------------------------------------------- s11: rain soaks in far away and sinks deep (line 11)
RAIN_PATH = [(250, 1000), (230, 1250), (300, 1500), (420, 1720), (620, 1800), (800, 1780)]


def s11(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 8 * math.sin(u * .4)
    img.paste(vgrad([(0, (120, 136, 160)), (.45, (186, 200, 206)), (.55, (190, 210, 200))]))
    kit.peak_range(img, 7, 1000, 380, 640, (96, 128, 112), (58, 82, 84), ink=INK, ink_w=4, n=4, x_shift=-300 + cam * .3)
    J.storm_cloud(img, 260 + cam * .2, 330, 1.25, u)
    J.storm_cloud(img, 520 + cam * .25, 270, .8, u + 2)
    J.rain(img, u, (40, 380, 560, 1010), n=150, seed=3)
    # the jungle and the steaming river, far right
    fb = J.canopy_layer(111, 1000, [(10, 50, 90, ((44, 96, 62), (66, 124, 76), (98, 158, 88)), True, (70, 56, 44), 0)], w=700)
    img.alpha_composite(fb, (int(560 + cam * .6), 0))
    J.steam(img, u, [(740, 1000, 1000)], rise=520, dens=.9, seed=37, n=26, size=(40, 110), wind=10)
    J.earth_section(img, u, 1000, H, cam, n=6, ft=.95, seed=8)
    d = ImageDraw.Draw(img)
    d.rectangle([-10, 986, W + 10, 1012], fill=(84, 140, 64), outline=INK, width=5)
    d.polygon([(600, 992), (1000, 992), (970, 1060), (630, 1060)], fill=(150, 210, 190), outline=INK, width=5)       # the river (right)
    taiga.dashed(d, (860, 1720), (860, 1070), (255, 200, 150), w=6, dash=22, gap=14, phase=-u * 60)
    # depth ruler (right edge)
    for kk, y in ((0, 1000), (1, 1300), (2, 1600), (3, 1900)):
        d.line([(1010, y), (1060, y)], fill=INK, width=8); d.line([(1012, y), (1058, y)], fill=(250, 240, 220), width=4)
        if kk: d.text((1000, y), f'{kk} KM', font=font(30, True), fill='white', anchor='rm', stroke_width=5, stroke_fill=INK)
    d.line([(1035, 1000), (1035, 1920)], fill=INK, width=8); d.line([(1035, 1000), (1035, 1920)], fill=(250, 240, 220), width=4)
    ks = smooth(seg(u, cue(1) - .2, cue(10) + .3))                         # soak in, sink deep, heat up
    pth = _smooth_path(RAIN_PATH, 6)
    vis = pth[:max(2, int(len(pth) * ks))]
    m = mask(); ImageDraw.Draw(m).line(vis, fill=255, width=30)
    glow(img, m, (255, 150, 90), .3, blur=20)
    d = ImageDraw.Draw(img)
    for a_, b_ in zip(vis, vis[1:]):
        f = pth.index(a_) / len(pth)
        d.line([a_, b_], fill=INK, width=30); d.line([a_, b_], fill=lerp(J.COLD, (255, 80, 40), f), width=20)
    J.rising(img, u, pth, n=12, speed=.3, r=(14, 22), cold=J.COLD, hot=(255, 90, 40), seed=4, k=ks, glow_a=.35)
    radial(img, 760, 1790, 320, (255, 110, 50), .4 * smooth(seg(u, cue(13) - .3, cue(14) + .2)) + .05 * math.sin(u * 4))
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 540, 1100, vig=(.32, (20, 24, 40)))
    if not HIDE_UI:
        chip(img, 'RAIN', (60, 110, 170), 300, 560, u, cue(0) - .1, size=56)
        chip(img, 'KILOMETRES DEEP', (40, 40, 60), 600, 1300, u, cue(9) - .1, size=44, angle=-4)
        chip(img, 'THE ROCK HEATS IT', (200, 70, 30), 560, 1620, u, cue(14) - .1, size=44)
    return img, {'faces': [], 'avoid': [(160, 480, 460, 740), (340, 1240, 860, 1360), (260, 1560, 860, 1680)]}


# ---------------------------------------------------------------- s12: pressure pushes it back up (line 12)
CRACK = [(560, 1960), (600, 1740), (500, 1520), (590, 1300), (520, 1080), (575, 860), (545, 700)]


def s12(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = 6 * math.sin(u * .5)
    bed = surface_section(img, u, cam, ground=560, river=(-80, 1160), depth=150, ft=.95, horizon=330, bands=6)
    d = ImageDraw.Draw(img)
    cr = _smooth_path(CRACK, 6)
    # the crack (wide, dark, then glowing inside)
    d.line(cr, fill=INK, width=64, joint='curve'); d.line(cr, fill=(60, 26, 20), width=46, joint='curve')
    m = mask(); ImageDraw.Draw(m).line(cr, fill=255, width=40)
    glow(img, m, HOT, .6 + .15 * math.sin(u * 5), blur=28)
    d = ImageDraw.Draw(img); d.line(cr, fill=(255, 150, 60), width=16, joint='curve')
    rad = radial(img, 545, 1900, 500, (255, 90, 40), .4 + .08 * math.sin(u * 3))
    kp = smooth(seg(u, cue(1) - .3, cue(1) + .3))
    J.rising(img, u, cr, n=14, speed=.6 + .5 * kp, r=(12, 20), seed=5, glow_a=.5)
    # pressure arrows beside the crack, pulsing upward
    if kp > 0:
        for j, x in enumerate((360, 760)):
            for q in range(3):
                v = (u * 1.2 + q / 3 + j * .5) % 1; y = 1800 - 900 * v
                J.arrow(d, [(x, y + 80), (x, y)], (255, 240, 220), w=16, head=36)
    # the river boils where the water comes in; the burst on "river"
    tr = cue(12) - .15
    kb = smooth(seg(u, tr, tr + .3))
    radial(img, 545, 650, 360, HOT, .45 + .3 * kb)
    J.bubbles(img, u, [(-60, 590), (1140, 590), (1140, 690), (-60, 690)], n=int(30 + 30 * kb), seed=8, size=(8, 22), rate=1.6 + kb)
    J.steam(img, u, [(300, 800, 570), (-40, 1120, 580)], rise=520, dens=.7 + .7 * kb, seed=41, n=50, size=(60, 150), wind=10, warm=.15)
    flash(img, u, tr, .25, .35, (255, 230, 200))
    sx, sy = shake(u, tr, 8, .3)
    img = finish(img, u, 1.02 + .05 * smooth(u / D), 545, 900, dx=sx, dy=sy, vig=(.4, (30, 10, 6)))
    if not HIDE_UI:
        chip(img, 'PRESSURE', (60, 40, 36), 270, 1420, u, cue(1) - .1, size=50, angle=-4)
        chip(img, 'BACK UP', (200, 70, 30), 870, 860, u, cue(4) - .1, size=50, angle=4)
    return img, {'faces': [], 'avoid': [(120, 1350, 420, 1490), (700, 790, 1040, 930), (180, 180, 900, 320), (460, 640, 640, 1960)]}


# ---------------------------------------------------------------- s13: like a coffee machine (line 13)
def kitchen(img, u, cam):
    img.paste(vgrad([(0, (246, 232, 206)), (1, (226, 204, 170))]))
    d = ImageDraw.Draw(img)
    for i in range(14):
        for j in range(8):
            x = i * 84 - 40 + cam * .5 + (42 if j % 2 else 0); y = 760 + j * 84
            d.rectangle([x, y, x + 80, y + 80], fill=(150, 200, 196), outline=(120, 170, 166), width=3)
    wx = 70 + cam * .4                                                    # window with the morning
    d.rectangle([wx, 160, wx + 300, 640], fill=(190, 226, 220), outline=INK, width=8)
    radial(img, wx + 150, 400, 360, (255, 240, 200), .5)
    d.line([(wx + 150, 160), (wx + 150, 640)], fill=INK, width=6); d.line([(wx, 400), (wx + 300, 400)], fill=INK, width=6)
    J.frond(d, wx + 40, 640, 200, -70, u, droop=.3, sway=3 * math.sin(u))
    d.rectangle([-20, 1460, W + 20, 1540], fill=(170, 120, 80), outline=INK, width=8)              # counter
    d.rectangle([-20, 1540, W + 20, H], fill=(120, 84, 60), outline=INK, width=6)


def coffee_scene(img, u, cam, kin, kheat, kout, ks):
    kitchen(img, u, cam)
    x, y, s = 480 + cam, 1470, .95
    P = J.coffee_machine(img, x, y, s, u, kin, kheat, kout, heat_glow=.35 + .65 * kheat)
    if kin > 0:
        J.rising(img, u, P['in'], n=6, speed=.7, r=(9, 13), cold=J.COLD, hot=J.COLD, glow_a=0, seed=3, k=kin)
    if kheat > 0:
        J.rising(img, u, P['riser'], n=10, speed=.7, r=(9, 13), cold=(255, 150, 80), hot=HOT, glow_a=.3, seed=4, k=kheat)
    if kout > 0:
        d = ImageDraw.Draw(img); sx, sy = P['shower']
        for j in range(4):
            v = (u * 2.2 + j / 4) % 1; d.ellipse([sx - 8 + (j - 1.5) * 18, sy + 10 + 90 * v, sx + 8 + (j - 1.5) * 18, sy + 30 + 90 * v], fill=(140, 80, 50), outline=INK, width=2)
    J.mug(img, 860 + cam, 1470, 1.0, u)
    J.steam(img, u, [(780 + cam, 940 + cam, 1290), (x - 160 * s, x - 60 * s, 1470 - 560 * s)], rise=480, dens=.15 + .9 * ks,
            seed=43, n=30, size=(40, 100), wind=10, shade=(200, 190, 180))
    return P


def s13(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -10 * smooth(u / D)
    kin = smooth(seg(u, cue(4) - .2, cue(7)))
    kheat = smooth(seg(u, cue(8) - .1, cue(11)))
    kout = smooth(seg(u, cue(12) - .2, cue(15)))
    ks = smooth(seg(u, cue(13) - .3, cue(15)))
    P = coffee_scene(img, u, cam, kin, kheat, kout, ks)
    img = finish(img, u, 1.02 + .03 * smooth(u / D), 540, 1100, vig=(.3, (40, 24, 14)))
    if not HIDE_UI:
        chip(img, 'LIKE A COFFEE MACHINE', (110, 70, 40), 540, 180, u, cue(2) - .1, size=50)
        chip(img, 'COLD IN', (40, 120, 200), 760, 600, u, cue(4) - .1, size=46)
        chip(img, 'SOMETHING HOT', (200, 70, 30), 360, 1300, u, cue(10) - .1, size=44)
        chip(img, 'STEAMING', (220, 90, 50), 880, 1230, u, cue(15) - .1, size=46)
    return img, {'faces': [], 'avoid': [(100, 120, 980, 240), (560, 540, 960, 660), (120, 1240, 600, 1360), (700, 1170, 1060, 1290)]}


# ---------------------------------------------------------------- s14: the hot plate is the planet (line 14)
def s14(u, D, cue):
    """The coffee machine's hot plate zooms in and becomes the planet: the inset keeps the hot plate (top left),
    '=' points to the cutaway Earth with the boiling river pinned on its crust."""
    k = smooth(seg(u, .2, .8))
    base = Image.new('RGBA', (W, H)); cam = -10
    P = coffee_scene(base, u, cam, 1, 1, 1, 1)
    hx, hy = P['heater']
    crop = base.crop((int(hx - 230), int(hy - 140), int(hx + 230), int(hy + 140)))
    img = anim.camera(base, 1 + 4 * ease_in(k), hx, hy)
    kg = smooth(seg(u, .5, .95))
    if kg > 0:
        g = Image.new('RGBA', (W, H))
        g.paste(vgrad([(0, (30, 12, 22)), (.6, (60, 20, 20)), (1, (24, 8, 14))]))
        stars(g, 5, 80, H, u)
        radial(g, 620, 1180, 800, (255, 110, 50), .35)
        J.globe(g, 620, 1200, 420, u, cut=1.0, spin=u * .05, glow_a=.9)
        J.map_pin(g, 620 + 8, 1200 - 420 + 24, u, HOT, 1.1)
        g = anim.camera(g, 1.25 - .25 * smooth(seg(u, .5, D)), 620, 1100)
        ki = out_back(seg(u, .75, 1.15), 1.6)                         # the hot plate inset
        if ki > 0:
            ins = Image.new('RGBA', (440, 270)); ins.paste(crop.resize((440, 270)), (0, 0))
            dd = ImageDraw.Draw(ins); dd.rectangle([0, 0, 439, 269], outline=INK, width=10)
            anim.scaled_paste(g, ins, 330, 540, ki * 1.45, angle=-3)
            if ki > .6:
                J.arrow(ImageDraw.Draw(g), [(560, 640), (620, 700), (628, 740)], (255, 200, 120), w=16, head=40)
        img = Image.blend(img.convert('RGBA'), g, kg)
    flash(img, u, .5, .3, .6, (255, 200, 140))
    img = finish(img, u, 1.0, 540, 960, vig=(.35, (20, 6, 10)))
    if not HIDE_UI:
        chip(img, 'THE HOT PLATE', (200, 70, 30), 330 if u > .75 else 540, 340 if u > .75 else 300, u, .05, size=50)
        stitle(img, 's14_t', [('= THE PLANET', (255, 210, 90), 120)], 1660, u, cue(6) - .1)
    return img, {'faces': [], 'avoid': [(40, 300, 560, 720), (0, 1640, W, 1860)]}


# ---------------------------------------------------------------- s15: the biggest known (line 15) - golden aerial
RIV15 = [(540, 760), (600, 840), (470, 960), (640, 1110), (430, 1300), (600, 1520), (380, 1760), (520, 2000)]


def s15(u, D, cue):
    img = Image.new('RGBA', (W, H)); cam = -30 * smooth(u / D)
    J.jungle_back(img, u, cam, horizon=740, sky=((255, 200, 120), (255, 150, 90)), far=(170, 110, 120), mid=(70, 110, 70),
                  haze_col=(255, 200, 150), sun=(260, 560), warm=.9)
    radial(img, 260, 600, 360, (255, 250, 210), .8)
    for k, (y, rmin, rmax) in enumerate(((820, 30, 50), (980, 40, 70), (1200, 60, 100), (1500, 80, 140))):
        b = J.canopy_layer(150 + k, y, [(40 - 6 * k, rmin, rmax, ((50, 96, 56), (74, 130, 66), (130, 170, 80)), True, None, 0)])
        img.alpha_composite(b, (int(-200 + cam * (.3 + .3 * k)), 0))
    pts = _smooth_path(RIV15, 10)
    wf = lambda yy: 18 + 420 * max(0, (yy - 740) / 1260) ** 1.2
    cf = lambda yy: lerp((255, 214, 140), (110, 200, 190), max(0, (yy - 740) / 1260))
    m = mask(); ImageDraw.Draw(m).line([(x + cam * .5, y_) for x, y_ in pts], fill=255, width=120)
    glow(img, m, (255, 190, 110), .5, blur=40)
    river_path_draw(img, [(x + cam * .5, y_) for x, y_ in pts], wf, cf, 0, u)
    radial(img, 520, 1300, 500, HOT, .25)
    J.steam(img, u, [(x + cam * .5 - wf(y_) / 2, x + cam * .5 + wf(y_) / 2, y_) for x, y_ in pts[::4]], rise=420,
            dens=.9, seed=47, n=70, size=(30, 130), wind=30, warm=.4, col=(255, 244, 236), alpha=.75)
    J.side_walls(img, u, cam, seed=15, left=True, right=True, y0=1500, y1=2000, scale=1.2)
    img = finish(img, u, 1.02 + .05 * smooth(u / D), 540, 1000, vig=(.36, (60, 30, 20)))
    stitle(img, 's15_t', [('BIGGEST KNOWN', 'white', 104)], 150, u, cue(2) - .1)
    if not HIDE_UI:
        chip(img, 'HOT RIVER · NO VOLCANO', (200, 70, 30), 540, 340, u, cue(7) - .1, size=52)
    return img, {'faces': [], 'avoid': [(0, 100, W, 420)]}


# ---------------------------------------------------------------- s16: the reminder; steam pulls back into the opening (line 16)
def s16(u, D, cue):
    w = u - D                                                            # the world clock meets s01's at the last frame
    t_surge = D - 1.55                                                   # steam surge: hides the cut back to frame 0
    ksurge = math.sin(math.pi * seg(u, t_surge, D - .12)) ** 1.2
    geo_on = u < t_surge + .65
    kdeep = smooth(seg(u, cue(10) - .3, cue(13)))
    frog = (FROG_X, FROG_Y - 2 * math.sin(w * 7), 0.0, 0.0, 0.0, .3 * math.sin(w * .9))
    G = {}
    def geo(img):
        if not geo_on: return
        look = -.3 + .5 * smooth(seg(u, cue(2), cue(4)))
        J.ground_bank(img, [(600, 1990), (640, 1760), (760, 1700), (900, 1680), (1100, 1690), (1100, 1990)])
        G['g'] = geologist(img, u, 'stand', 'thinking' if u < cue(14) else 'determined', 880, 1760, .72, look=-look,
                           rim=(255, 200, 150), rim_dir=(1, -.4))
    img = s01_world(w, 0.0, frog=frog, geo=geo, walls_y1=760 if geo_on else 1300)
    # "deep under the jungle, the planet is still cooking": heat glow pulses up through the ground
    if kdeep > 0:
        radial(img, 560, 2100, 1100, (255, 90, 40), .4 * kdeep * (1 - ksurge) + .06 * math.sin(u * 3) * kdeep)
    if ksurge > 0:
        J.steam(img, u, [(-100, 1180, 2100), (-100, 1180, 1700)], rise=1900, dens=1.6 * ksurge, seed=53, n=90, size=(120, 300),
                rate=.5, wind=0, alpha=min(1, 1.2 * ksurge))
        fill_mask(img, Image.new('L', (W, H), int(255 * .8 * ksurge ** 2)), (244, 248, 246))
    zoom = 1.0 + .28 * (1 - smooth(seg(u, .0, t_surge + .7)))
    img = finish(img, w, zoom, 640, 1150, vig=(.3, (20, 40, 30)))
    if u > D - .5: opening_title(img, w, -99)
    elif u > D - .75:
        k = smooth(seg(u, D - .75, D - .5))
        if not HIDE_UI:
            lay, _ = tlayer('open', [('THIS RIVER', 'white', 128), ('BOILS', (255, 120, 50), 210)], 128)
            anim.scaled_paste(img, lay, 540, 330, 1.25 - .25 * k, alpha=k)
    info = {'faces': [face_box(G['g'], 1.3)] if 'g' in G else [], 'avoid': [(fx - 220, fy - 220, fx + 260, fy + 120) for fx, fy in ((FROG_X, FROG_Y),)]}
    if u > cue(18) + .45: info['seam'] = 1
    return img, info


SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [('s01', 1, 0), ('s02', 2, 0), ('s03a', 3, 0), ('s03b', 3, 10), ('s04', 4, 0), ('s05', 5, 0), ('s06', 6, 0),
             ('s07', 7, 0), ('s08', 8, 0), ('s09', 9, 0), ('s10', 10, 0), ('s11', 11, 0), ('s12', 12, 0), ('s13', 13, 0),
             ('s14', 14, 0), ('s15', 15, 0), ('s16', 16, 0)]
END = 1946 / 30                 # 64.867 s (length.json); with the 0.1 s cover ~64.97 s
NO_PUNCH = ()
BAND_AT = {'s16': 2.0}
STILL_AT = {'s01': .55, 's02': .95, 's03a': .8, 's03b': .95, 's04': .9, 's05': .985, 's06': .9, 's07': .95, 's08': .95, 's09': .9,
            's10': .9, 's11': .95, 's12': .95, 's13': .95, 's14': .9, 's15': .95, 's16': .4}

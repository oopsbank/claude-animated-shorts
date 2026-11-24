"""Moth light (video 11, "Why Do Moths Fly Into Lights?"): shots as `sNN(u, D, cue) -> (img, info)`.

Same contract as flamingo_one_leg.py: u = shot-local time, D = shot length, cue(i) = shot-local time of word i of the
shot's voice-over LINE. info: 'faces' (face boxes) and 'avoid' (boxes the caption must not cover).
Hero image: moths orbiting a glowing violet UV lamp in a misty night cloud forest, their paths drawn as long-exposure
light trails. Colour motif: violet-white light against deep blue-green night. Third look: the infrared camera view.
The mechanism (s10-s12) on a clean night-sky stage: the moth seen from behind, its BACK arrow (yellow) and where it
thinks UP is (white): under the sky they agree; a lamp at the side pulls UP sideways and the moth tilts and circles;
a lamp below pulls UP down and the moth rolls over and falls. Serious tone, no comedy. Every shot keeps moving.

Render: .venv/bin/python flat2d/render.py audio/moth-light/words.json OUT.mp4 --film moth_light --size 540x960
"""
import math, os, sys, re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit, anim
import moth as M
import cloudforest as CF
from kit import W, H, INK, vgrad, radial, font, mask, glow, fill_mask, layer, lerp, rgb, label
from anim import smooth, ease_out, ease_in, out_back, seg, slam, pop, shake, actor, POSES, add, damp
from blood_falls import finish, slam_title, face_box
from blood_falls_2 import put_chip, draw_x, path_point
import tunguska as TG
from tunguska import chip_t, flash
import flamingo_one_leg as F

SLUG = 'moth-light'
HIDE_UI = False
KEY = (255, 210, 63)
UPC = (236, 236, 255)
VIO = (150, 110, 255)
SCI_COL = (110, 80, 200)
SCI_A = dict(coat='#3d5a4a', shirt='#c9b48a', pants='#3a3f4e')
SCI_B = dict(coat='#5a4a6a', shirt='#9ab0c8', pants='#44404e', hair=('tuft', '#3a2e28'))
PERSON = dict(shirt='#b8743c', pants='#3e4a6a')
LAMP = (540, 860)
GROUND = 1700


def q(v, step): return round(v / step) * step


# ---------------------------------------------------------------- UI wrappers (HIDE_UI for the thumbnail frame)
def clue(img, txt, u, t0=.05, y=250):
    if not HIDE_UI: TG.clue(img, txt, u, t0, y)


def chip(img, txt, fill, x, y, u, t0, size=50, angle=0.0):
    if not HIDE_UI: chip_t(img, txt, fill, x, y, u, t0, size=size, angle=angle)


def stitle(img, key, lines, y, u, t0, size=104, stagger=.16):
    if not HIDE_UI: slam_title(img, key, lines, y, u, t0, size=size, stagger=stagger)


def tag(img, txt, x, y, size=44, col='white', s=1.0):
    if not HIDE_UI: F.tag(img, txt, x, y, size, col, s)


def qmark(img, x, y, s, u, t0, col=(255, 255, 255)):
    if not HIDE_UI: F.qmark(img, x, y, s, u, t0, col)


def check(img, x, y, r, k):
    if not HIDE_UI: F.check_mark(img, x, y, r, k)


def dashed(img, p0, p1, col=(255, 255, 255), w=6, phase=0.0, frac=1.0):
    if HIDE_UI or frac <= 0: return
    p1 = (p0[0] + (p1[0] - p0[0]) * frac, p0[1] + (p1[1] - p0[1]) * frac)
    F.dashed(img, p0, p1, col, w, 26, 16, phase)


def sci(img, t, who, pose, expr, cx, gy, s, look=0.0, lean=0.0, lamp=True, bphase=0.0, rim=(170, 140, 255), rim_dir=(1, -.4)):
    kw = SCI_A if who == 'A' else SCI_B if who == 'B' else PERSON
    g = actor(img, expr, pose, cx, gy, s, t, look=look, lean=lean, aura=None, rim=rim, rim_dir=rim_dir, rim_w=12,
              bphase=bphase + (0 if who == 'A' else .9), **kw)
    if lamp: CF.headlamp(img, g, True, col=(255, 90, 80), k=.9)        # red headlamps (they don't draw insects)
    return g


# ---------------------------------------------------------------- moths around a lamp
class Orb:
    """One moth's orbit around a lamp: angle a(t) = a0 + om t; 3D circle (X, Z) of radius R, seen from a little
    above (screen y = ly + y0 - Z * tilt); bob and a slow radius breathe."""
    def __init__(self, a0, om, R, y0, tilt=.28, s=70, bob=24, ph=0.0):
        self.a0, self.om, self.R, self.y0, self.tilt, self.s, self.bob, self.ph = a0, om, R, y0, tilt, s, bob, ph

    def p3(self, t):
        a = self.a0 + self.om * t
        R = self.R * (1 + .08 * math.sin(t * .9 + self.ph))
        X, Z = R * math.cos(a), R * math.sin(a)
        Y = self.y0 + self.bob * math.sin(t * 2.1 + self.ph)
        return X, Y, Z

    def scr(self, t, lamp):
        X, Y, Z = self.p3(t)
        return lamp[0] + X, lamp[1] + Y - Z * self.tilt, Z


def orbiters(img, w, lamp, orbs, front, trail_t=1.1, scale=1.0, lamp_col=VIO, lamp_k=.7, trail_col=(196, 170, 255),
             core=(255, 250, 255), trail_w=4.0, moths=True, blur=.5, alpha=1.0):
    """Draw the trails and moths on one side of the lamp (front: Z < 0, nearer the camera)."""
    for i, o in enumerate(orbs):
        X, Y, Z = o.p3(w)
        if (Z < 0) != front: continue
        n = 22
        pts = [o.scr(w - trail_t * (1 - j / n), lamp)[:2] for j in range(n + 1)]
        dk = 1 - .45 * max(0, Z) / o.R
        M.trail(img, pts, trail_col, trail_w * dk * scale, .9 * dk * alpha, core, wave=2.5 * scale, phase=w * 9 + i)
        if not moths: continue
        x, y, _ = o.scr(w, lamp)
        x2, y2, Z2 = o.scr(w + .02, lamp)
        vx, vz = (x2 - x), (Z2 - Z)
        yaw = math.degrees(math.atan2(vz, vx))
        roll = 62 if o.om > 0 else -62
        sz = max(16, q(o.s * scale * (1 - .28 * Z / o.R), 4))
        lv = (lamp[0] - x, lamp[1] - y, -Z * .6)
        M.put(img, x, y, sz, view='side', elev=16, yaw=q(yaw, 3), roll=roll, flap=q((w * 23 + i * .37) % 1, 1 / 24), blur=blur,
              lamp=lv, lamp_k=lamp_k, lamp_col=lamp_col, alpha=alpha)


def default_orbs(seed=1, n=8, R=(240, 400), s=(56, 84), y=(-120, 140), om=(1.4, 2.4)):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        sg = 1 if i % 3 else -1
        out.append(Orb(rng.uniform(0, 6.28), sg * rng.uniform(*om), rng.uniform(*R), rng.uniform(*y), .28, rng.uniform(*s), 22, rng.uniform(0, 6)))
    return out


ORBS = default_orbs(1, 9)


def opening_title(img, u, k=1.0, t_pop=None):
    if HIDE_UI: return
    s = 1.0 + .006 * math.sin(u * 2.4)
    if t_pop is not None and t_pop <= u < t_pop + .3: s = max(s, slam(u, t_pop, .3, 1.12))
    lay, _ = F.tlayer('open_m', [('2024', KEY, 230)], 230)
    anim.scaled_paste(img, lay, 540, 240, s * k)
    put_chip(img, 'COSTA RICA', (40, 120, 90), 540, 410, k, size=60)


# ---------------------------------------------------------------- s01: the hook / loop frame
HERO_PATH = [(980, 1180), (760, 1120), (520, 1150), (300, 1110), (120, 1060)]


def hero_flyby(img, w, f, s=230, lamp=LAMP, trail=True, slow=1.0):
    """A big moth crossing in front of the lamp from right to left (f 0..1 along its path), wings beating in slow
    motion, its long-exposure trail behind it."""
    pts = [F_path(HERO_PATH, max(0, f - .5 * k / 20)) for k in range(21)][::-1]
    if trail: M.trail(img, pts, (210, 186, 255), 7, .9, wave=3, phase=w * 4)
    x, y = F_path(HERO_PATH, f)
    x2, y2 = F_path(HERO_PATH, min(1, f + .01))
    hd = math.degrees(math.atan2(y2 - y, x2 - x)) if f < .99 else 186
    yaw = 180 - 12
    return M.put(img, x, y, s, view='side', elev=28, yaw=yaw, roll=-18, flap=(w * 1.6 * slow) % 1, blur=.06,
                 lamp=(lamp[0] - x, lamp[1] - y, .3), lamp_k=.8, lamp_col=(170, 140, 255))


def F_path(pts, f):
    return path_point(pts, max(0, min(1, f)))


def forest_scene(w, cam=0.0, lamp=LAMP, orbs=ORBS, chars=True, hero_f=None, lamp_k=1.0, props=True, sci_t=None):
    img = Image.new('RGBA', (W, H))
    CF.forest(img, w, cam, lamp=lamp, lamp_k=lamp_k)
    G = {}
    orbiters(img, w, (lamp[0] + cam * .8, lamp[1]), orbs, front=False)
    CF.uv_lamp(img, lamp[0] + cam * .8, lamp[1], 1.0, t=w, k=lamp_k, ground=GROUND)
    CF.spores(img, w, (lamp[0] + cam * .8, lamp[1]), 70)
    if props:
        CF.camera_rig(img, 150 + cam * 1.0, 1830, .9, face=1, t=w, h=470)
        CF.ir_lamp(img, 950 + cam * 1.0, 1800, .85, t=w, face=-1, h=520)
    orbiters(img, w, (lamp[0] + cam * .8, lamp[1]), orbs, front=True)
    if chars:
        st = w if sci_t is None else sci_t
        G['a'] = sci(img, st, 'A', 'hold', 'thinking', 330 + cam * 1.1, 1930, .5, look=.55, rim_dir=(1, -.5))
        G['b'] = sci(img, st, 'B', dict(POSES['stand'], armL=(40, 60)), 'neutral', 790 + cam * 1.1, 1950, .48, look=-.6, bphase=.4, rim_dir=(-1, -.5))
        CF.laptop(img, 900 + cam * 1.1, 1700, .7, w)
    if hero_f is not None: G['hero'] = hero_flyby(img, w, hero_f)
    CF.foreground(img, w, cam)
    return img, G


def s01_frame(u, w, cue=None):
    cue = cue or (lambda i: [0, .21, .68, 1.31, 1.83, 2.46, 2.83, 3.04, 3.4][min(i, 8)])
    cam = 10 * math.sin(w * .4)
    img, G = forest_scene(w, cam, hero_f=.06 + u * .065)
    img = finish(img, w, 1.0 + .035 * smooth(u / 4), 540, 1000, vig=(.32, (6, 4, 20)))
    if not HIDE_UI:
        opening_title(img, u, t_pop=cue(1))
        if u > cue(5) - .1: put_chip(img, 'SLOW-MOTION FILMS', (110, 80, 200), 540, 540, pop(u, cue(5) - .1, .3), size=50)
    faces = [face_box(G['a'], 1.3), face_box(G['b'], 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 120, W, 600)]}


def s01(u, D, cue):
    return s01_frame(u, u, cue)


def s01b(u, D, cue):
    """Closer on the lamp: the moths' long-exposure orbits, a big moth turning in slow motion in front of the lamp,
    a camera filming in the foreground; MONTEVERDE CLOUD FOREST."""
    w = u + 4
    lamp = (560, 820)
    img = Image.new('RGBA', (W, H))
    cam = -20 * smooth(u / D)
    CF.forest(img, w, cam, lamp=lamp, lamp_r=1.1)
    orbs = default_orbs(5, 12, R=(220, 430), s=(64, 96), y=(-200, 200))
    orbiters(img, w, (lamp[0] + cam * .8, lamp[1]), orbs, front=False, trail_t=1.6, scale=1.15)
    CF.uv_lamp(img, lamp[0] + cam * .8, lamp[1], 1.25, t=w, ground=2100)
    CF.spores(img, w, (lamp[0] + cam * .8, lamp[1]), 90, r=520)
    orbiters(img, w, (lamp[0] + cam * .8, lamp[1]), orbs, front=True, trail_t=1.6, scale=1.15)
    # the slow-motion hero: a big moth banking round the lamp, back toward the light
    a = math.radians(200 + 26 * u)
    hx, hy = lamp[0] + cam * .8 + 330 * math.cos(a), lamp[1] + 400 + 60 * math.sin(a)
    pts = [(lamp[0] + cam * .8 + 330 * math.cos(math.radians(200 + 26 * (u - k * .1))), lamp[1] + 400 + 60 * math.sin(math.radians(200 + 26 * (u - k * .1)))) for k in range(14)][::-1]
    M.trail(img, pts, (210, 186, 255), 8, .8, wave=3, phase=w * 3)
    hero = M.put(img, hx, hy, 270, view='side', elev=24, yaw=150 - 14 * u, roll=-48, flap=(w * 1.3) % 1, blur=.05,
                 lamp=(lamp[0] - hx, lamp[1] - hy, .2), lamp_k=.9)
    CF.camera_rig(img, 140 + cam * 1.4, 2060, 1.6, face=1, t=w, h=520)
    CF.foreground(img, w, cam, seed=12)
    img = finish(img, w, 1.02 + .04 * smooth(u / D), 560, 900, vig=(.32, (6, 4, 20)))
    if not HIDE_UI:
        chip(img, 'AROUND A LAMP', (110, 80, 200), 540, 260, u, cue(8) - .1, size=52)
        chip(img, 'MONTEVERDE CLOUD FOREST', (40, 120, 90), 540, 380, u, cue(17) - .1, size=46)
    return img, {'faces': [], 'avoid': [(80, 180, 1000, 440)]}


# ---------------------------------------------------------------- s02: flames and lights through time
def flame_moths(img, w, c, n, R, s, col=(255, 190, 110), seed=3):
    rng = np.random.default_rng(seed)
    orbs = [Orb(rng.uniform(0, 6.28), (1 if i % 2 else -1) * rng.uniform(1.6, 2.6), rng.uniform(R * .6, R), rng.uniform(-R * .4, R * .2), .3,
                rng.uniform(s * .8, s * 1.2), 18, rng.uniform(0, 6)) for i in range(n)]
    for front in (False, True):
        orbiters(img, w, c, orbs, front, trail_t=.8, lamp_col=col, lamp_k=.9, trail_col=(255, 200, 130), core=(255, 246, 220), trail_w=3)
    return orbs


def s02(u, D, cue):
    w = u + 10
    img = Image.new('RGBA', (W, H))
    cam = -20 * smooth(u / D)
    fx, fy = CF.candle_room(img, w, cam)
    flame_moths(img, w, (fx, fy - 40), 5, 220, 70, seed=4)
    # one moth flutters right into the flame on "flames"
    k = smooth(seg(u, cue(5) - .6, cue(6) + .1))
    mx = fx - 260 * (1 - k) + 6 * math.sin(w * 20); my = fy - 60 - 120 * (1 - k) * math.sin(k * 3)
    M.put(img, mx, my, 110, view='side', elev=20, yaw=20 - 30 * k, roll=-20, flap=(w * 9) % 1, blur=.3, lamp=(fx - mx, fy - my, .2),
          lamp_k=1.0, lamp_col=(255, 190, 110))
    if u > cue(6):
        kk = u - cue(6)
        if kk < .5:
            m = mask(); ImageDraw.Draw(m).ellipse([fx - 60, fy - 90, fx + 60, fy + 30], fill=255)
            glow(img, m, (255, 220, 140), .8 * (1 - kk / .5), blur=30, add=True)
    g = sci(img, w, 'P', 'think', 'thinking', 860 + cam * 1.2, 1930, .62, look=-.7, lamp=False, rim=(255, 190, 110), rim_dir=(-1, -.4))
    CF_hat(img, g)
    img = finish(img, w, 1.03 + .03 * smooth(u / D), 540, 1100, vig=(.3, (30, 10, 0)))
    if not HIDE_UI:
        chip(img, 'FLAMES', (200, 90, 40), 540, 300, u, cue(6) - .1, size=60)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(300, 220, 780, 380)]}


def CF_hat(img, g):
    """An old-style wide-brimmed hat (a watcher from long ago)."""
    hx, hy = g['head']; R = g['R']
    d = ImageDraw.Draw(img)
    d.ellipse([hx - R * 1.7, hy - R * .95, hx + R * 1.7, hy - R * .45], fill=(50, 36, 30), outline=INK, width=max(3, int(R * .12)))
    d.rounded_rectangle([hx - R * .9, hy - R * 1.9, hx + R * .9, hy - R * .7], int(R * .3), fill=(60, 44, 36), outline=INK, width=max(3, int(R * .12)))
    d.rectangle([hx - R * .9, hy - R * .98, hx + R * .9, hy - R * .8], fill=(130, 60, 50))


def s02b(u, D, cue):
    w = u + 14
    img = Image.new('RGBA', (W, H))
    cam = 24 * smooth(u / D)
    hx, hy = CF.street_lamp(img, w, cam)
    flame_moths(img, w, (hx, hy), 9, 300, 64, seed=7)
    sh = smooth(seg(u, cue(16) - .4, cue(16) + .1))
    g = sci(img, w, 'P', anim.mix(dict(POSES['stand']), dict(POSES['shrug']), sh), 'thinking' if sh < .5 else 'worried', 300 + cam * 1.2, 1900, .62,
            look=.5, lamp=False, rim=(255, 190, 110), rim_dir=(1, -.5))
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1000, vig=(.3, (20, 10, 20)))
    if not HIDE_UI:
        chip(img, 'THOUSANDS OF YEARS', (200, 110, 40), 540, 250, u, cue(10) - .1, size=54)
        if u > cue(16) - .1: qmark(img, 820, 1050, 1.0, u, cue(16) - .1, KEY)
        chip(img, 'WHY?', (110, 80, 200), 820, 1260, u, cue(16) - .05, size=58)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(200, 180, 880, 330), (680, 900, 960, 1320)]}


# ---------------------------------------------------------------- s03: the usual answers
def s03(u, D, cue):
    w = u + 20
    img = Image.new('RGBA', (W, H))
    cam = -16 * smooth(u / D)
    mx, my = 790, 400
    CF.moon_sky(img, w, mx, my, 120, cam)
    CF.treeline(img, 33, 1500, 260, (12, 20, 26), 30)
    lamp = (220 + cam, 1330)
    CF.uv_lamp(img, lamp[0], lamp[1], .6, t=w, ground=1700)
    d = ImageDraw.Draw(img); d.rectangle([0, 1700, W, H], fill=(8, 12, 16))
    CF.mist(img, w, 1300, 1800, (100, 120, 170), .25, seed=3, lamp=lamp, lamp_k=.8)
    # the moth in the middle, flying, looking for the way
    bx, by = 600 + 20 * math.sin(w * .9), 1000 + 30 * math.sin(w * 1.3)
    k1 = smooth(seg(u, cue(4) - .2, cue(4) + .5)); k2 = smooth(seg(u, cue(10) - .2, cue(10) + .5))
    dashed(img, (bx - 40, by + 40), (lamp[0] + 30, lamp[1] - 60), (255, 255, 255), 7, w, k1)
    dashed(img, (bx + 40, by - 60), (mx - 90, my + 90), (255, 255, 255), 7, w, k2)
    M.put(img, bx, by, 240, view='side', elev=22, yaw=150 + 30 * math.sin(w * .5), roll=-10, flap=(w * 8) % 1, blur=.35,
          lamp=(lamp[0] - bx, lamp[1] - by, 0), lamp_k=.5, light=(.3, -.7, -.6))
    if u > cue(13):
        kk = u - cue(13)
        if kk < .8: kit.light_rays(img, mx + cam * .1, my, (230, 230, 255), n=12, alpha=.25 * (1 - kk / .8), spread=(0, 360), length=360, seed=2)
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1000, vig=(.28, (6, 8, 30)))
    if not HIDE_UI:
        chip(img, 'THE USUAL ANSWER', (70, 80, 120), 540, 200, u, .0, size=46)
        chip(img, 'DRAWN TO THE LIGHT?', (110, 80, 200), 360, 1520, u, cue(4) - .1, size=50)
        chip(img, "THINKS IT'S THE MOON?", (60, 110, 170), 600, 640, u, cue(10) - .1, size=50)
    return img, {'faces': [], 'avoid': [(80, 1440, 700, 1600), (230, 570, 970, 710), (300, 150, 780, 250)]}


# ---------------------------------------------------------------- s04: on camera: around, not at
def ir_scene(w, lamp, orbs, cam=0.0, chars=False, trail_t=1.2, scale=1.0):
    img = Image.new('RGBA', (W, H))
    CF.forest(img, w, cam, lamp=lamp, lamp_k=.8)
    orbiters(img, w, lamp, orbs, front=False, trail_t=trail_t, scale=scale, moths=True)
    CF.uv_lamp(img, lamp[0], lamp[1], 1.0, t=w, ground=GROUND)
    orbiters(img, w, lamp, orbs, front=True, trail_t=trail_t, scale=scale, moths=True)
    return img


def s04(u, D, cue):
    w = u + 30
    lamp = (540, 900)
    orbs = default_orbs(11, 7, R=(260, 380), s=(70, 96), y=(-80, 100))
    img = ir_scene(w, lamp, orbs, trail_t=.9)
    img = CF.ir_view(img, w, 'IR CAM 2', 'SLOW MOTION', clock=19.4 + u * .25)
    # the straight line that never happened: a moth heading straight at the lamp, crossed out
    p0, p1 = (140, 520), (lamp[0] - 40, lamp[1] - 40)
    k1 = smooth(seg(u, .1, cue(5) - .2))
    if not HIDE_UI:
        dashed(img, p0, p1, (255, 255, 255), 8, w, k1)
        if u > cue(4) - .1:
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            draw_x(img, mx, my, 70, seg(u, cue(4) - .1, cue(4) + .3) * 2)
    # the real path: a ring drawn round the lamp, twice
    kr = seg(u, cue(11) - .2, cue(15) + .2)
    if kr > 0 and not HIDE_UI:
        tot = kr * 2.0
        pts = []
        for j in range(int(tot * 80) + 2):
            a = -math.pi / 2 + j / 80 * 2 * math.pi
            r = 330 - 18 * (j / 80)
            pts.append((lamp[0] + r * math.cos(a), lamp[1] + r * .42 * math.sin(a) + 10 * math.sin(a * 3)))
        M.trail(img, pts, KEY, 8, 1.0, (255, 250, 220))
        hx, hy = pts[-1]; hx2, hy2 = pts[-2]
        ang = math.atan2(hy - hy2, hx - hx2)
        F.arrow(img, (hx - math.cos(ang) * 50, hy - math.sin(ang) * 50), (hx + math.cos(ang) * 20, hy + math.sin(ang) * 20), 26, KEY)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 900, vig=(.3, (0, 10, 0)))
    if not HIDE_UI:
        chip(img, 'NOT AT IT', (200, 50, 50), 300, 400, u, cue(4) + .1, size=54)
        chip(img, 'AROUND IT', (190, 150, 30), 540, 1320, u, cue(11) - .1, size=60)
        chip(img, 'AGAIN AND AGAIN', (60, 120, 90), 540, 1450, u, cue(13) - .1, size=50)
    return img, {'faces': [], 'avoid': [(200, 330, 520, 470), (200, 1250, 880, 1510)]}


# ---------------------------------------------------------------- s05: CLUE 1 (from above, slow motion)
_GROUND = {}


def ground_top(seed=3, tint=(20, 26, 22)):
    """The forest floor seen from straight above: leaf litter, fern fronds, a mossy log (cached)."""
    if seed in _GROUND: return _GROUND[seed]
    img = Image.new('RGBA', (W + 200, H + 200), tint + (255,))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    for k in range(420):
        x, y = rng.uniform(0, W + 200), rng.uniform(0, H + 200)
        CF.leaf(d, x, y, rng.uniform(40, 90), rng.uniform(0, 6.28), lerp((70, 54, 34), tint, rng.uniform(.2, .7)), lerp((40, 30, 20), tint, .3), .34)
    for k in range(10):
        base = (rng.uniform(0, W + 200), rng.uniform(0, H + 200))
        for j in range(6):
            a = rng.uniform(0, 6.28)
            CF.fern_frond(d, base, a, rng.uniform(220, 360), rng.uniform(-.6, .6), (34, 70, 50), (20, 44, 32), .9)
    img = img.filter(ImageFilter.GaussianBlur(2.2))
    _GROUND[seed] = img
    return img


def top_scene(w, lamp, cam=(0, 0), k_light=1.0, seed=3, hud=True, tint=(20, 26, 22)):
    img = Image.new('RGBA', (W, H))
    g = ground_top(seed, tint)
    img.alpha_composite(g, (int(-100 + cam[0]), int(-100 + cam[1])))
    a = np.asarray(img, np.float32)
    a[..., :3] *= .55
    img = Image.fromarray(a.astype(np.uint8), 'RGBA')
    radial(img, lamp[0], lamp[1], 900, (110, 80, 230), .6 * k_light)
    radial(img, lamp[0], lamp[1], 380, VIO, .6 * k_light)
    # the lamp seen from above: the tube's end and its glow
    radial(img, lamp[0], lamp[1], 140, (240, 230, 255), .95)
    d = ImageDraw.Draw(img)
    d.ellipse([lamp[0] - 46, lamp[1] - 46, lamp[0] + 46, lamp[1] + 46], fill=(110, 114, 128), outline=INK, width=6)
    d.ellipse([lamp[0] - 26, lamp[1] - 26, lamp[0] + 26, lamp[1] + 26], fill=(250, 248, 255))
    return img


def s05(u, D, cue):
    """CLUE 1 from above, slow motion: a big moth banks round the lamp, its back tilted toward the light."""
    w = u + 40
    lamp = (430, 980)
    img = top_scene(w, lamp, (-10 * u, -6 * u))
    CF.spores(img, w, lamp, 50, r=520)
    R = 360
    a0 = math.radians(-20)
    def pos(t):
        a = a0 + .42 * t
        return lamp[0] + R * math.cos(a), lamp[1] + R * 1.0 * math.sin(a), a
    pts = [pos(u - k * .12)[:2] for k in range(26)][::-1]
    M.trail(img, pts, (210, 186, 255), 9, .9, wave=3, phase=w * 2)
    x, y, a = pos(u)
    hd = math.degrees(a) + 90                                     # tangent (counter-clockwise on screen)
    kb = smooth(seg(u, cue(5) - .6, cue(6)))
    roll = 30 + 30 * kb
    inf = M.put(img, x, y, 300, heading=hd, view='top', roll=-roll, flap=(w * 1.1) % 1, blur=.05, lamp=(lamp[0] - x, lamp[1] - y, .6),
                lamp_k=.9, glow=(150, 110, 255), glow_a=.25)
    if not HIDE_UI and u > cue(6) - .2:
        M.back_arrow(img, inf['back'], inf['up'], 190 * smooth(seg(u, cue(6) - .2, cue(6) + .2)) + 1, label='BACK', label_side=1)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 960, vig=(.3, (6, 4, 20)))
    if not HIDE_UI:
        clue(img, 'CLUE 1', u, .05)
        tag(img, 'SLOW MOTION · FROM ABOVE', 540, 380, 34, (220, 210, 255))
        chip(img, 'BACK TOWARD THE LIGHT', (190, 150, 30), 540, 1600, u, cue(9) - .1, size=50)
    return img, {'faces': [], 'avoid': [(200, 170, 880, 420), (150, 1530, 930, 1680)]}


# ---------------------------------------------------------------- s06: CLUE 2 (a lamp pointing up)
def ground_lamp(img, x, gy, t, k=1.0, beam=True, s=1.0):
    """A UV lamp lying on the ground, pointing up: a box with a glowing face and an upward beam."""
    if beam:
        m = mask(); ImageDraw.Draw(m).polygon([(x - 80 * s, gy - 60 * s), (x + 80 * s, gy - 60 * s), (x + 420 * s, -200), (x - 420 * s, -200)], fill=255)
        glow(img, m, (130, 100, 240), .3 * k, blur=60, add=True)
    radial(img, x, gy - 70 * s, 600 * s, VIO, .6 * k)
    radial(img, x, gy - 70 * s, 200 * s, (240, 230, 255), .8 * k)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - 110 * s, gy - 70 * s, x + 110 * s, gy + 10 * s], int(14 * s), fill=(70, 74, 88), outline=INK, width=6)
    d.rounded_rectangle([x - 90 * s, gy - 86 * s, x + 90 * s, gy - 62 * s], int(10 * s), fill=(250, 246, 255), outline=INK, width=5)


def s06(u, D, cue):
    w = u + 50
    img = Image.new('RGBA', (W, H))
    lamp_gx, gy = 600, 1640
    CF.forest(img, w, 0, lamp=(lamp_gx, gy - 300), lamp_k=.7, mist_a=.8)
    ground_lamp(img, lamp_gx, gy, w)
    # the moth: flies in level, flips over the lamp on "flipped", falls on "fell"
    t_in, t_flip, t_fall = cue(2) - .9, cue(8) - .15, cue(12) - .1
    fx = lamp_gx - 40
    kx = smooth(seg(u, t_in, t_flip + .2))
    x = 60 + (fx - 60) * kx + 6 * math.sin(w * 5)
    y = 640 + 30 * math.sin(w * 2.2) * (1 - kx)
    kf = smooth(seg(u, t_flip, t_flip + .45))
    roll = 180 * kf
    kd = ease_in(seg(u, t_fall, t_fall + .55))
    land = gy - 40
    y = y + (land - y) * kd
    x = x + 60 * kd
    spin = 40 * kd
    if kd >= 1: y = land
    hist = []
    for j in range(18):
        tt = u - j * .06
        kx_ = smooth(seg(tt, t_in, t_flip + .2)); kd_ = ease_in(seg(tt, t_fall, t_fall + .55))
        xx = 60 + (fx - 60) * kx_ + 60 * kd_; yy = 640 + 30 * math.sin((tt + 50) * 2.2) * (1 - kx_)
        hist.append((xx, yy + (land - yy) * kd_))
    pre = img.copy()
    M.trail(img, hist[::-1], (210, 190, 255), 6, .8)
    inf = M.put(img, x, y, 190, view='side', elev=18, yaw=-18, roll=roll, pitch=-spin, flap=(w * 6) % 1 if kd < 1 else .5,
                blur=.25 if kd < 1 else 0, lamp=(lamp_gx - x, gy - y, 0), lamp_k=.8)
    img = CF.ir_view(img, w, 'IR CAM 4', 'SLOW MOTION', clock=24.1 + u * .25)
    if not HIDE_UI and u > t_in + .3:
        M.back_arrow(img, inf['back'], inf['up'], 150, label='BACK', label_side=1 if roll < 90 else -1)
    if u > t_fall + .55 and u < t_fall + 1.0:
        m = mask(); ImageDraw.Draw(m).ellipse([x - 140, land - 30, x + 140, land + 40], fill=255)
        fill_mask(img, m, (220, 236, 220), .4 * (1 - (u - t_fall - .55) / .45), blur=20)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.3, (0, 10, 0)))
    if not HIDE_UI:
        clue(img, 'CLUE 2', u, .05)
        chip(img, 'LAMP POINTING UP', (110, 80, 200), 600, 1800, u, cue(5) - .1, size=48)
        chip(img, 'FLIPS', (200, 60, 60), 860, 440, u, cue(8) - .05, size=60)
        chip(img, 'FALLS', (200, 60, 60), 860, 560, u, cue(12) - .05, size=60)
    return img, {'faces': [], 'avoid': [(200, 170, 880, 330), (700, 380, 1020, 620), (300, 1740, 900, 1860)]}


# ---------------------------------------------------------------- s07: CLUE 3 (a glowing sheet overhead)
def s07(u, D, cue):
    w = u + 60
    img = Image.new('RGBA', (W, H))
    CF.forest(img, w, -20 * smooth(u / D), lamp=(540, 300), lamp_k=.45, mist_a=.7)
    ks = smooth(seg(u, cue(5) - .3, cue(6) + .2))
    a = np.asarray(img, np.float32); a[..., :3] *= (.75 + .25 * ks)
    img = Image.fromarray(a.astype(np.uint8), 'RGBA')
    CF.sheet(img, 120, 330, 960, 640, w, .3 + .7 * ks)
    radial(img, 540, 560, 1200, (200, 200, 255), .3 * ks)
    # moths fly straight through underneath, level, backs up toward the bright sheet
    lanes = [(900, 230, 0.0), (1150, 190, .55), (1380, 210, 1.1)]
    infs = []
    for i, (yl, s, ph) in enumerate(lanes):
        sp = 420
        x = -260 + ((u + ph) * sp + i * 300) % (W + 520)
        y = yl + 14 * math.sin(w * 3 + i)
        pts = [(x - k * 26, y + 14 * math.sin((w - k * .06) * 3 + i)) for k in range(22)][::-1]
        M.trail(img, pts, (220, 214, 255), 5, .8, wave=2, phase=w * 8)
        infs.append(M.put(img, x, y, s, view='side', elev=14, yaw=0, roll=0, flap=(w * 7 + i * .3) % 1, blur=.3,
                          lamp=(0, -1, -.2), lamp_k=.6 * ks, lamp_col=(220, 220, 255)))
    if not HIDE_UI and u > cue(12) - .3:
        b = infs[1]
        if 120 < b['back'][0] < 960:
            M.back_arrow(img, b['back'], b['up'], 150, label='BACK', label_side=1, alpha=smooth(seg(u, cue(12) - .3, cue(12))))
    img = finish(img, w, 1.02 + .02 * smooth(u / D), 540, 1000, vig=(.3, (6, 4, 20)))
    if not HIDE_UI:
        clue(img, 'CLUE 3', u, .05)
        chip(img, 'GLOWING SHEET = SKY', (90, 90, 160), 540, 720, u, cue(11) - .1, size=50)
        chip(img, 'NOT TRAPPED', (40, 140, 80), 480, 1640, u, cue(14) - .1, size=56)
        if u > cue(14): check(img, 760, 1640, 44, seg(u, cue(14), cue(14) + .3))
    return img, {'faces': [], 'avoid': [(200, 170, 880, 330), (200, 650, 880, 790), (200, 1570, 840, 1710)]}


# ---------------------------------------------------------------- s08: the riddle
def s08(u, D, cue):
    w = u + 70
    lamp = (240, 800)
    img = Image.new('RGBA', (W, H))
    CF.forest(img, w, 0, lamp=lamp, lamp_k=1.0)
    CF.uv_lamp(img, lamp[0], lamp[1], 1.1, t=w, ground=1900)
    CF.spores(img, w, lamp, 60)
    x, y = 680 + 16 * math.sin(w * .8), 1000 + 24 * math.sin(w * 1.1)
    inf = M.put(img, x, y, 330, view='rear', elev=48, roll=-62 + 4 * math.sin(w * 1.3), flap=(w * 1.2) % 1, blur=.05,
                lamp=(lamp[0] - x, lamp[1] - y, .3), lamp_k=.9)
    if not HIDE_UI:
        M.back_arrow(img, inf['back'], inf['up'], 220 * smooth(seg(u, cue(5) - .3, cue(7))) + 1, label='BACK', label_side=-1)
    CF.foreground(img, w, 0, seed=14)
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1000, vig=(.32, (6, 4, 20)))
    if not HIDE_UI:
        qmark(img, 860, 480, 1.1, u, cue(1) - .1, KEY)
        chip(img, 'WHY TURN ITS BACK?', (110, 80, 200), 540, 260, u, cue(5) - .1, size=50)
    return img, {'faces': [], 'avoid': [(160, 190, 920, 330), (720, 320, 1000, 640)]}


# ---------------------------------------------------------------- s09: millions of years: the sky is the brightest
def s09(u, D, cue):
    w = u + 80
    img = Image.new('RGBA', (W, H))
    CF.ancient_night(img, w, -20 * smooth(u / D))
    # brightness markers
    ks = smooth(seg(u, cue(12) - .2, cue(12) + .3)); kg = smooth(seg(u, cue(15) - .2, cue(15) + .3))
    if ks > 0: radial(img, 540, 300, 900, (150, 160, 255), .25 * ks)
    x, y = 540 + 220 * math.sin(w * .25), 1080 + 30 * math.sin(w * 1.1)
    inf = M.put(img, x, y, 150, view='rear', elev=50, roll=6 * math.sin(w * .9), flap=(w * 5) % 1, blur=.3, light=(0, -1, -.4))
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 900, vig=(.28, (4, 4, 20)))
    if not HIDE_UI:
        chip(img, 'MILLIONS OF YEARS', (70, 80, 140), 540, 220, u, cue(1) - .1, size=54)
        chip(img, 'NO LAMPS', (90, 60, 60), 540, 340, u, cue(4) - .1, size=44)
        if ks > 0: tag(img, 'SKY: BRIGHTEST', 540, 560, 64, KEY, pop(u, cue(12) - .1, .3))
        if kg > 0: tag(img, 'GROUND: DARK', 540, 1640, 56, (180, 190, 230), pop(u, cue(15) - .1, .3))
    return img, {'faces': [], 'avoid': [(150, 150, 930, 620), (200, 1580, 880, 1700)]}


# ---------------------------------------------------------------- the mechanism stage: UP and BACK
def up_arrow(img, base, ang, length, alpha=1.0, label='UP', col=UPC, w=34):
    """'Where up is' for the moth: a white outlined arrow from the moth toward the brightest light. ang in deg,
    0 = screen up, + = clockwise."""
    if HIDE_UI or alpha <= .01: return
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)
    p0 = (base[0] + ux * 60, base[1] + uy * 60); p1 = (base[0] + ux * length, base[1] + uy * length)
    lay = layer()
    F.arrow(lay, p0, p1, w, col)
    if label:
        d = ImageDraw.Draw(lay)
        lx, ly = p1[0] + ux * 70, p1[1] + uy * 60
        d.text((lx, ly), label, font=font(76), fill=col, anchor='mm', stroke_width=8, stroke_fill=INK)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)


def s10(u, D, cue):
    """Under the open sky the moth keeps its back to the brightest light: the sky. Back = up."""
    w = u + 90
    img = Image.new('RGBA', (W, H))
    CF.night_stage(img, w, 0, moon_xy=(830, 280))
    radial(img, 540, 120, 1000, (150, 160, 255), .3)
    x, y = 540 + 16 * math.sin(w * .7), 1080 + 20 * math.sin(w * 1.2)
    inf = M.put(img, x, y, 330, view='rear', elev=52, roll=4 * math.sin(w * .9), flap=(w * 1.1) % 1, blur=.04, light=(0, -1, -.5))
    kb = smooth(seg(u, cue(4) - .3, cue(4) + .2))
    if not HIDE_UI and kb > 0:
        M.back_arrow(img, inf['back'], inf['up'], 300 * kb + 1, label='BACK', label_side=1)
    ku = smooth(seg(u, cue(16) - .3, cue(16) + .1))
    up_arrow(img, (x - 230, y - 60), 0, 420, ku, 'UP')
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.26, (4, 4, 20)))
    if not HIDE_UI:
        chip(img, 'BACK TO THE BRIGHTEST LIGHT', (190, 150, 30), 540, 240, u, cue(5) - .1, size=46)
        if ku > 0: chip(img, 'BACK = UP', (60, 110, 170), 540, 1560, u, cue(16) - .1, size=60)
    return img, {'faces': [], 'avoid': [(100, 170, 980, 320), (300, 1490, 780, 1640), (240, 380, 840, 1300)]}


def stage_lamp(img, x, y, t, s=.9, k=1.0):
    CF.uv_lamp(img, x, y, s, t=t, k=k, stand=True, ground=1700)


def s11(u, D, cue):
    """A lamp beside the moth: UP swings sideways to the lamp, then the moth tilts its back toward it."""
    w = u + 100
    img = Image.new('RGBA', (W, H))
    CF.night_stage(img, w, 0, moon_xy=(830, 280), grid=True)
    a = np.asarray(img, np.float32); a[..., :3] *= .7; img = Image.fromarray(a.astype(np.uint8), 'RGBA')
    lamp = (930, 1000)
    stage_lamp(img, lamp[0], lamp[1], w)
    x, y = 420 + 10 * math.sin(w * .7), 1000 + 14 * math.sin(w * 1.2)
    k_up = smooth(seg(u, cue(5) - .5, cue(5) + .1))                 # "sideways"
    k_tilt = smooth(seg(u, cue(8) - .15, cue(9) + .1))              # "tilts"
    roll = 70 * k_tilt + 3 * math.sin(w * 1.3)
    x += 70 * smooth(seg(u, cue(9), D))
    inf = M.put(img, x, y, 300, view='rear', elev=52, roll=roll, flap=(w * 1.1) % 1, blur=.04, light=(.6, -.3, -.5),
                lamp=(lamp[0] - x, lamp[1] - y, 0), lamp_k=.9)
    up_arrow(img, (x, y), 90 * ease_out(k_up) if k_up < 1 else 90, 330, 1.0, 'UP')
    if not HIDE_UI:
        M.back_arrow(img, inf['back'], inf['up'], 230, label='BACK', label_side=-1 if roll > 35 else 1)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.26, (4, 4, 20)))
    if not HIDE_UI:
        chip(img, '"UP" POINTS SIDEWAYS', (60, 110, 170), 540, 260, u, cue(4) - .1, size=50)
        chip(img, 'IT TILTS', (190, 150, 30), 420, 1540, u, cue(8) - .1, size=56)
    return img, {'faces': [], 'avoid': [(160, 180, 920, 340), (220, 1470, 640, 1610), (100, 600, 1060, 1400)]}


def s11b(u, D, cue):
    """From above: tilting toward the lamp turns the moth; its path curls into a circle round the lamp."""
    w = u + 110
    lamp = (560, 1060)
    img = top_scene(w, lamp, (0, 0), seed=5, tint=(16, 20, 40))
    d = ImageDraw.Draw(img)
    for gx in range(60, W, 120): d.line([(gx, 0), (gx, H)], fill=(120, 140, 220, 18), width=2)
    for gy in range(60, H, 120): d.line([(0, gy), (W, gy)], fill=(120, 140, 220, 18), width=2)
    def pos(t):
        # straight in from the bottom-left, then a spiral round the lamp
        k = smooth(seg(t, 0, .6))
        if t < .6:
            return (120 + 300 * t / .6, 1700 - 300 * t / .6, None)
        a = math.radians(200 - 210 * (t - .6))
        r = 300 + 80 * math.exp(-(t - .6) * 2)
        return (lamp[0] + r * math.cos(a), lamp[1] - r * math.sin(a), a)
    p_start = pos(.6)[:2]
    def P(t):
        if t < .6:
            f = t / .6
            return (120 + (p_start[0] - 120) * f, 1760 + (p_start[1] - 1760) * f)
        return pos(t)[:2]
    pts = [P(max(0, u - k * .05)) for k in range(int(min(u, 2.5) / .05) + 2)][::-1]
    M.trail(img, pts, (210, 186, 255), 8, .95, wave=2, phase=w * 4)
    x, y = P(u); x2, y2 = P(u + .03)
    hd = math.degrees(math.atan2(y2 - y, x2 - x))
    inf = M.put(img, x, y, 190, heading=hd, view='top', roll=-50 * smooth(seg(u, .4, .8)), flap=(w * 6) % 1, blur=.3,
                lamp=(lamp[0] - x, lamp[1] - y, .6), lamp_k=.9)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.28, (4, 4, 20)))
    if not HIDE_UI:
        tag(img, 'FROM ABOVE', 540, 230, 40, (210, 210, 255))
        chip(img, 'TURNS...', (190, 150, 30), 300, 380, u, .05, size=54)
        chip(img, 'ENDS UP CIRCLING', (110, 80, 200), 540, 520, u, cue(15) - .1, size=56)
    return img, {'faces': [], 'avoid': [(120, 180, 960, 600)]}


def s12(u, D, cue):
    """A lamp below: UP points down, the moth rolls belly-up and falls."""
    w = u + 120
    img = Image.new('RGBA', (W, H))
    CF.forest(img, w, 0, lamp=(540, 1500), lamp_k=.9, mist_a=1.0)
    img = img.filter(ImageFilter.GaussianBlur(6))
    a = np.asarray(img, np.float32); a[..., :3] *= .55; img = Image.fromarray(a.astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(img)
    for gx in range(60, W, 120): d.line([(gx, 0), (gx, H)], fill=(120, 140, 220, 16), width=2)
    for gy in range(60, H, 120): d.line([(0, gy), (W, gy)], fill=(120, 140, 220, 16), width=2)
    ground_lamp(img, 540, 1640, w, 1.0, s=1.1)
    k_up = smooth(seg(u, cue(5) - .2, cue(7) + .1))                 # "up" points "down"
    k_roll = smooth(seg(u, cue(10) - .15, cue(11)))                 # "rolls over"
    k_fall = ease_in(seg(u, cue(12), cue(13) + .5))                 # "and falls"
    x = 520 + 12 * math.sin(w * .8)
    y = 760 + 14 * math.sin(w * 1.2) + 700 * k_fall
    roll = 180 * k_roll + 10 * math.sin(w * 1.3) * (1 - k_roll)
    inf = M.put(img, x, y, 290 - 60 * k_fall, view='rear', elev=50, roll=roll, pitch=-30 * k_fall, flap=(w * 1.2) % 1 if k_fall < .2 else (w * 4) % 1,
                blur=.04 + .3 * k_fall, lamp=(540 - x, 1600 - y, 0), lamp_k=.9)
    up_arrow(img, (x, y), 180 * k_up, 330, 1.0 - .6 * k_fall, 'UP')
    if not HIDE_UI and k_fall < .6:
        M.back_arrow(img, inf['back'], inf['up'], 230, label='BACK', label_side=1, alpha=1 - k_fall)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 540, 1000, vig=(.26, (4, 4, 20)))
    if not HIDE_UI:
        chip(img, 'LAMP BELOW', (110, 80, 200), 540, 250, u, .05, size=50)
        chip(img, '"UP" POINTS DOWN', (60, 110, 170), 540, 370, u, cue(6) - .1, size=50)
        chip(img, 'ROLLS OVER', (190, 150, 30), 820, 600, u, cue(10) - .1, size=50)
        chip(img, 'FALLS', (200, 60, 60), 820, 1220, u, cue(13) - .1, size=60)
    return img, {'faces': [], 'avoid': [(160, 180, 920, 440), (600, 540, 1040, 660), (600, 1150, 1040, 1290)]}


# ---------------------------------------------------------------- s13: the analogy (a compass beside a magnet)
def compass(img, x, y, r, ang, t=0.0):
    """A brass compass seen from above at a slant (ellipse), its needle at angle ang (deg, 0 = up/north)."""
    ry = r * .62
    d = ImageDraw.Draw(img)
    d.ellipse([x - r - 10, y - ry + 26, x + r + 10, y + ry + 40], fill=(60, 40, 24))
    d.ellipse([x - r - 10, y - ry - 10, x + r + 10, y + ry + 18], fill=(170, 130, 60), outline=INK, width=8)
    d.ellipse([x - r + 14, y - ry + 10, x + r - 14, y + ry - 4], fill=(240, 234, 214), outline=(120, 90, 40), width=6)
    f = font(int(r * .2))
    for lbl, a in (('N', 0), ('E', 90), ('S', 180), ('W', 270)):
        aa = math.radians(a)
        d.text((x + math.sin(aa) * r * .72, y - math.cos(aa) * ry * .72), lbl, font=f, fill=(60, 40, 30), anchor='mm')
    for k in range(36):
        aa = math.radians(k * 10); r0 = .82 if k % 3 else .76
        d.line([(x + math.sin(aa) * r * r0, y - math.cos(aa) * ry * r0), (x + math.sin(aa) * r * .88, y - math.cos(aa) * ry * .88)], fill=(120, 100, 80), width=3)
    aa = math.radians(ang)
    tip = (x + math.sin(aa) * r * .66, y - math.cos(aa) * ry * .66)
    tail = (x - math.sin(aa) * r * .66, y + math.cos(aa) * ry * .66)
    n = (-math.cos(aa) * r * .08, -math.sin(aa) * ry * .08)
    d.polygon([tip, (x + n[0], y + n[1]), (x - n[0], y - n[1])], fill=(220, 50, 50), outline=INK)
    d.polygon([tail, (x + n[0], y + n[1]), (x - n[0], y - n[1])], fill=(230, 230, 236), outline=INK)
    d.ellipse([x - 12, y - 10, x + 12, y + 10], fill=(200, 160, 70), outline=INK, width=3)
    # glass glint
    d.arc([x - r * .8, y - ry * .8, x + r * .5, y + ry * .4], 200, 250, fill=(255, 255, 255), width=6)
    return tip


def magnet(img, x, y, s=1.0, ang=0.0):
    lay = layer(420, 420); d = ImageDraw.Draw(lay)
    cx, cy = 210, 210
    d.arc([cx - 140, cy - 150, cx + 140, cy + 130], 180, 360, fill=INK, width=110)
    d.arc([cx - 140 + 8, cy - 150 + 8, cx + 140 - 8, cy + 130 - 8], 180, 360, fill=(210, 50, 50), width=94)
    d.rectangle([cx - 140, cy - 10, cx - 34, cy + 120], fill=(210, 50, 50), outline=INK, width=8)
    d.rectangle([cx + 34, cy - 10, cx + 140, cy + 120], fill=(210, 50, 50), outline=INK, width=8)
    d.rectangle([cx - 140, cy + 80, cx - 34, cy + 140], fill=(220, 220, 226), outline=INK, width=8)
    d.rectangle([cx + 34, cy + 80, cx + 140, cy + 140], fill=(220, 220, 226), outline=INK, width=8)
    anim.scaled_paste(img, lay, x, y, s, angle=ang)


def s13(u, D, cue):
    w = u + 130
    img = Image.new('RGBA', (W, H))
    CF.desk_wall(img, w, -10 * smooth(u / D))
    g = sci(img, w, 'P', 'think', 'thinking', 260, 1240, .55, look=.6, lamp=False, rim=(255, 200, 140), rim_dir=(1, -.4))
    CF.desk_top(img, w, 0)
    km = smooth(seg(u, cue(5) - .5, cue(7) + .1))
    mx, my = 1240 - 340 * km, 1270
    cx, cy, r = 560, 1300, 270
    # the needle: north, then swings to the magnet with a damped wobble
    target = math.degrees(math.atan2(mx - 150 - cx, -(my - cy) / .62))
    ang = target * smooth(seg(u, cue(7) - .1, cue(7) + .5)) + damp(u - cue(7) - .5, 14, 4, 12) + 3 * math.sin(w * 2) * (1 - km)
    radial(img, cx, cy, 500, (255, 210, 140), .2)
    compass(img, cx, cy, r, ang, w)
    magnet(img, mx, my - 20, .75, ang=90)
    img = finish(img, w, 1.0 + .03 * smooth(u / D), 560, 1200, vig=(.28, (30, 14, 0)))
    if not HIDE_UI:
        chip(img, 'COMPASS + MAGNET', (60, 110, 170), 540, 780, u, cue(3) - .1, size=50)
        chip(img, 'NOTHING BROKEN', (40, 140, 80), 540, 1700, u, cue(8) - .1, size=52)
        if u > cue(11): check(img, 840, 1700, 40, seg(u, cue(11), cue(11) + .3))
        chip(img, 'WRONG WAY', (200, 60, 60), 540, 1820, u, cue(16) - .1, size=56)
    return img, {'faces': [face_box(g, 1.3)], 'avoid': [(200, 710, 880, 850), (200, 1630, 900, 1890)]}


# ---------------------------------------------------------------- s14: the flip (the biggest title)
def s14(u, D, cue):
    w = u + 140
    lamp = (540, 1120)
    img = Image.new('RGBA', (W, H))
    CF.forest(img, w, 0, lamp=lamp, lamp_k=1.0)
    orbs = default_orbs(21, 11, R=(220, 420), s=(64, 96), y=(-160, 200))
    orbiters(img, w, lamp, orbs, front=False, trail_t=1.6)
    CF.uv_lamp(img, lamp[0], lamp[1], 1.1, t=w, ground=2000)
    CF.spores(img, w, lamp, 80)
    orbiters(img, w, lamp, orbs, front=True, trail_t=1.6)
    CF.foreground(img, w, 0, seed=15)
    a = np.asarray(img, np.float32)
    yy = np.linspace(0, 1, H)[:, None, None]
    a[..., :3] *= (.55 + .45 * np.clip((yy - .05) / .35, 0, 1))          # darken the top for the title
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    img = finish(img, w, 1.02 + .03 * smooth(u / D), 540, 1100, vig=(.3, (6, 4, 20)))
    if not HIDE_UI:
        stitle(img, 's14_a', [('NOT', 'white', 130), ('ATTRACTED.', 'white', 150)], 110, u, cue(2) - .1, stagger=.12)
        stitle(img, 's14_b', [('TRAPPED.', KEY, 260)], 520, u, cue(7) - .1)
    sx, sy = shake(u, cue(7), 10, .3)
    if sx or sy: img = anim.camera(img, 1.0, None, None, sx, sy)
    return img, {'faces': [], 'avoid': [(0, 90, W, 860)]}


# ---------------------------------------------------------------- s15: the loop back to 2024
def s15(u, D, cue):
    w = u - D
    if u > D - 1.5 / 30:
        now = anim.NOW; anim.NOW = 0.0
        try: return s01_frame(0.0, 0.0)
        finally: anim.NOW = now
    kz = smooth(seg(u, .2, D - .4))
    z = 1.45 - .45 * kz
    cam = 10 * math.sin(w * .4)
    img, G = forest_scene(w, cam, hero_f=.06 + (u - D) * .065)
    fx = 540 + (LAMP[0] - 540) * (1 - kz); fy = 1000 + (LAMP[1] - 1000) * (1 - kz)
    img = finish(img, w, z * (1.0 + .035 * smooth(0)), fx, fy, vig=(.32, (6, 4, 20)))
    if not HIDE_UI:
        k = smooth(seg(u, D - .9, D - .2))
        if k > 0: opening_title(img, 0.0, k)
        if u < D - 1.0:
            chip(img, 'THE 2024 FILMS', (110, 80, 200), 540, 300, u, cue(2) - .1, size=52)
            chip(img, 'TRAPPED, NOT ATTRACTED', (190, 150, 30), 540, 430, u, cue(9) - .1, size=48)
    faces = [face_box(G['a'], 1.3), face_box(G['b'], 1.3)]
    return img, {'faces': faces, 'avoid': [(0, 120, W, 600)]}


SHOTS = {k: v for k, v in list(globals().items()) if _re.match(r'^s\d\d[a-z]?$', k) and callable(v)}
SHOT_LIST = [('s01', 1, 0), ('s01b', 1, 8), ('s02', 2, 0), ('s02b', 2, 8), ('s03', 3, 0), ('s04', 4, 0), ('s05', 5, 0),
             ('s06', 6, 0), ('s07', 7, 0), ('s08', 8, 0), ('s09', 9, 0), ('s10', 10, 0), ('s11', 11, 0), ('s11b', 11, 11),
             ('s12', 12, 0), ('s13', 13, 0), ('s14', 14, 0), ('s15', 15, 0)]
END = 1915 / 30                  # 63.833 s (length.json)
NO_PUNCH = ()
BAND_AT = {}
BAND_FIX = {}
STILL_AT = {'s01': .02, 's01b': .85, 's02': .9, 's02b': .95, 's03': .92, 's04': .92, 's05': .9, 's06': .8, 's07': .9,
            's08': .9, 's09': .95, 's10': .95, 's11': .92, 's11b': .9, 's12': .7, 's13': .92, 's14': .95, 's15': .5}

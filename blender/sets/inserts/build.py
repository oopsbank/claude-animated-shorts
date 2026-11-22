# Inserts set (sailing-stones): full-frame 2D cards drawn in PIL, in our palette with plum ink, no brands.
#   alien_cam   : the guide's FANTASY cutaways inside a thought bubble with a cheesy green ALIEN CAM filter.
#                 inserts__alien_cam__day.png is leaf_blower_aliens (s09); the other panels are
#                 inserts__alien_cam__day__rock_racing_league.png (s12) and ...__alien_air_hockey_final.png (s16)
#                 (shots pick them with "plate"; see BACKLOG).
#   gps_screen  : reused as the livestream screen (s19): a phone with LIVE · 1.2M, comments "ICE??" "REFUND", and
#                 the real ice shot (a playa frost plate) of rocks sliding in sunshine.
#   sprites/    : price cards $30/$40/$50 (the engine flips them in the corner), the ICE TOURS sign, tour_sign_free.
# usage: .venv/bin/python blender/sets/inserts/build.py [--out DIR]
import os, sys, math, json, random, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
W, H, SS = 1080, 1920, 2                         # drawn at 2x, downsampled (anti-aliasing)
INK = (36, 23, 38); CREAM = (246, 226, 190); SUN = (255, 197, 51); LIME = (111, 209, 106); PURPLE = (122, 34, 214)
ORANGE = (232, 97, 60); BLUE = (58, 143, 209); TEAL = (47, 179, 201); PINK = (232, 93, 138); TAN = (226, 186, 132)
FB = os.path.join(ROOT, 'engine/fonts/Poppins-Bold.ttf'); FXB = os.path.join(ROOT, 'engine/fonts/Poppins-ExtraBold.ttf')

def font(size, xb=False): return ImageFont.truetype(FXB if xb else FB, int(size * SS))
def S(*v): return [x * SS for x in v]
def lw(w): return max(1, int(w * SS))

def text_c(d, xy, t, f, fill, stroke=0, sfill=INK, anchor='mm'):
    d.text((xy[0] * SS, xy[1] * SS), t, font=f, fill=fill, anchor=anchor, stroke_width=lw(stroke) if stroke else 0, stroke_fill=sfill)

def ell(d, cx, cy, rx, ry, fill, w=5, outline=INK):
    d.ellipse(S(cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=outline, width=lw(w) if outline else 0)

def poly(d, pts, fill, w=5, outline=INK):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)
    if outline: d.line([(x * SS, y * SS) for x, y in pts + [pts[0]]], fill=outline, width=lw(w), joint='curve')

def line(d, pts, fill=INK, w=5): d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=lw(w), joint='curve')

def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)

# ---------------------------------------------------------------- characters and props
def alien(d, x, y, s=1.0, body=LIME, vest=None, arm=None, cheer=False, face=1):
    """Our little alien: a bean body, a big head with two black almond eyes, two springy antenna balls. (x, y) = feet."""
    h = 150 * s; hw = 46 * s
    ell(d, x, y - h * 0.32, hw * 0.8, h * 0.32, shade(body, 0.92), 4 * s)                          # body
    if vest: poly(d, [(x - hw * 0.62, y - h * 0.5), (x + hw * 0.62, y - h * 0.5), (x + hw * 0.7, y - h * 0.12), (x - hw * 0.7, y - h * 0.12)], vest, 3 * s)
    if vest:
        for yy in (0.24, 0.38): line(d, [(x - hw * 0.66, y - h * yy), (x + hw * 0.66, y - h * yy)], (235, 240, 245), 7 * s)
    for sx in (-1, 1): line(d, [(x + sx * hw * 0.3, y - h * 0.02), (x + sx * hw * 0.34, y + 4 * s)], INK, 6 * s)            # legs
    if cheer:
        for sx in (-1, 1): line(d, [(x + sx * hw * 0.6, y - h * 0.45), (x + sx * hw * 1.2, y - h * 0.95)], INK, 6 * s); ell(d, x + sx * hw * 1.2, y - h * 0.95, 7 * s, 7 * s, body, 3 * s)
    hx, hy = x, y - h * 0.82
    for sx in (-1, 1):                                                                              # antennae
        line(d, [(hx + sx * 14 * s, hy - 40 * s), (hx + sx * 26 * s, hy - 78 * s)], INK, 4 * s); ell(d, hx + sx * 27 * s, hy - 82 * s, 10 * s, 10 * s, SUN, 3 * s)
    ell(d, hx, hy, hw, 48 * s, body, 5 * s)                                                         # head
    ell(d, hx + hw * 0.3, hy - 20 * s, hw * 0.35, 12 * s, shade(body, 1.18), 0, None)               # sheen
    for sx in (-1, 1):
        poly(d, [(hx + sx * 6 * s, hy + 2 * s), (hx + sx * 34 * s, hy - 14 * s), (hx + sx * 32 * s, hy + 6 * s), (hx + sx * 12 * s, hy + 16 * s)], INK, 0, None)
        ell(d, hx + sx * 24 * s, hy - 6 * s, 4 * s, 4 * s, (255, 255, 255), 0, None)
    if face == 2: ell(d, hx, hy + 24 * s, 10 * s, 12 * s, (120, 30, 50), 4 * s)            # open mouth, yelling
    elif face: d.arc(S(hx - 12 * s, hy + 12 * s, hx + 12 * s, hy + 32 * s), 20, 160, fill=INK, width=lw(4 * s))
    return hx, hy

def rock(d, cx, cy, rx, ry, seed=0, col=(62, 52, 58)):
    rnd = random.Random(seed); n = 9
    pts = [(cx + rx * math.cos(2 * math.pi * k / n) * rnd.uniform(0.82, 1.08), cy + ry * math.sin(2 * math.pi * k / n) * rnd.uniform(0.75, 1.05)) for k in range(n)]
    pts = [(x, min(y, cy + ry * 0.55)) for x, y in pts]
    poly(d, pts, col, 6)
    poly(d, [(cx - rx * 0.6, cy - ry * 0.55), (cx + rx * 0.1, cy - ry * 0.85), (cx + rx * 0.5, cy - ry * 0.5), (cx - rx * 0.1, cy - ry * 0.35)], shade(col, 1.45), 0, None)
    return pts

def helmet(d, cx, cy, r, col, num=None):
    d.chord(S(cx - r, cy - r, cx + r, cy + r), 180, 360, fill=col, outline=INK, width=lw(5)); line(d, [(cx - r * 1.1, cy), (cx + r * 1.15, cy)], INK, 7)
    d.chord(S(cx - r * 0.75, cy - r * 0.62, cx + r * 0.6, cy - r * 0.05), 180, 360, fill=(255, 255, 255))
    if num: text_c(d, (cx, cy - r * 0.6), str(num), font(r * 0.55, True), INK)

def bib(d, cx, cy, w, h, num):
    poly(d, [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)], (250, 250, 245), 4)
    text_c(d, (cx, cy + 2), str(num), font(h * 0.7, True), INK)

def leaf_blower(d, x, y, ang, s=1.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def P(u, v): return (x + u * ca - v * sa, y + u * sa + v * ca)
    poly(d, [P(-26 * s, -18 * s), P(10 * s, -18 * s), P(10 * s, 18 * s), P(-26 * s, 18 * s)], ORANGE, 4 * s)
    poly(d, [P(10 * s, -7 * s), P(70 * s, -9 * s), P(70 * s, 9 * s), P(10 * s, 7 * s)], (90, 90, 100), 4 * s)
    return P(74 * s, 0)

def puff(d, x, y, r, col=(240, 225, 200)):
    for k, (dx, dy, kr) in enumerate(((0, 0, 1), (r * 0.7, -r * 0.3, 0.8), (-r * 0.7, -r * 0.2, 0.75), (r * 0.2, -r * 0.7, 0.7))):
        ell(d, x + dx, y + dy, r * kr, r * kr, col, 4)

def stars(d, n, box, seed, col=(255, 255, 255)):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(box[0], box[2]), rnd.uniform(box[1], box[3]); r = rnd.uniform(2, 6)
        poly(d, [(x, y - r * 2), (x + r * 0.5, y - r * 0.5), (x + r * 2, y), (x + r * 0.5, y + r * 0.5), (x, y + r * 2), (x - r * 0.5, y + r * 0.5), (x - r * 2, y), (x - r * 0.5, y - r * 0.5)], col, 0, None)

# ---------------------------------------------------------------- fantasy panels (drawn into the bubble box)
BX0, BY0, BX1, BY1 = 60, 300, 1020, 1620          # bubble content box (1x coords)

def bg_desert(d, sky=((90, 190, 255), (255, 170, 120))):
    for y in range(BY0, BY1):   # sunset sky gradient, then desert floor
        t = (y - BY0) / (BY1 - BY0)
        c = tuple(int(sky[0][i] + (sky[1][i] - sky[0][i]) * min(1, t / 0.45)) for i in range(3))
        d.line([(BX0 * SS, y * SS), (BX1 * SS, y * SS)], fill=c, width=SS + 1)
    poly(d, [(BX0, 780), (200, 680), (330, 740), (470, 640), (640, 750), (800, 660), (BX1, 740), (BX1, 820), (BX0, 820)], (150, 70, 120), 5)
    poly(d, [(BX0, 800), (BX1, 790), (BX1, BY1), (BX0, BY1)], TAN, 0, None)
    rnd = random.Random(3)
    for k in range(40):   # mud cracks
        x, y = rnd.uniform(BX0, BX1), rnd.uniform(920, BY1); L = rnd.uniform(30, 90) * (y - 860) / 600
        line(d, [(x, y), (x + L, y + rnd.uniform(-6, 6)), (x + L * 1.4, y + rnd.uniform(-10, 10))], shade(TAN, 0.75), 3)
    ell(d, 820, 540, 70, 70, SUN, 0, None)

def leaf(d, x, y, r, col, ang):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(x + u * ca - v * sa, y + u * sa + v * ca) for u, v in ((-r, 0), (0, -r * 0.45), (r, 0), (0, r * 0.45))]
    poly(d, pts, col, 3)

def panel_leaf_blower(d):
    bg_desert(d)
    # the boulder sliding off to the right on a jet of air, a dust plume and its groove trail behind it
    line(d, [(720, 1215), (300, 1270)], shade(TAN, 0.6), 22)
    rock(d, 820, 1110, 185, 140, seed=5)
    for k in range(4): line(d, [(980, 1040 + k * 34), (1010, 1040 + k * 34)], INK, 6)                 # motion ticks
    puff(d, 700, 1220, 40); puff(d, 960, 1225, 26)
    rnd = random.Random(12)
    for k in range(14):   # leaves and grit flying in the blast
        leaf(d, rnd.uniform(470, 760), rnd.uniform(980, 1260), rnd.uniform(9, 16), [(240, 150, 40), (200, 90, 40), (150, 190, 60)][k % 3], rnd.uniform(0, 180))
    # three aliens in hi-vis vests, blasting it with oversized leaf blowers
    for (x, y, s, a) in ((200, 1110, 1.0, -2), (330, 1290, 1.25, -8), (210, 1480, 1.4, -14)):
        hx, hy = alien(d, x, y, s, vest=(255, 120, 10), face=2 if s > 1.2 else 1)
        tip = leaf_blower(d, x + 30 * s, y - 70 * s, a, s * 1.5)
        for k in range(5):   # air blasts
            t0 = (tip[0] + 10, tip[1] + (k - 2) * 16)
            line(d, [t0, (t0[0] + 230, t0[1] - 40 + (k - 2) * 34)], (255, 255, 255), 10)
    sx_, sy_ = 800, 1380   # the site supervisor: a rock in a hard hat with a clipboard
    rock(d, sx_, sy_, 115, 95, seed=61, col=(100, 86, 84))
    d.chord(S(sx_ - 70, sy_ - 140, sx_ + 60, sy_ - 40), 180, 360, fill=SUN, outline=INK, width=lw(6)); line(d, [(sx_ - 85, sy_ - 90), (sx_ + 75, sy_ - 90)], INK, 9)
    for ex in (-26, 14): ell(d, sx_ + ex, sy_ - 55, 12, 12, (255, 255, 255), 4); ell(d, sx_ + ex + 3, sy_ - 53, 5, 5, INK, 0, None)
    poly(d, [(sx_ - 130, sy_ - 50), (sx_ - 60, sy_ - 50), (sx_ - 60, sy_ + 40), (sx_ - 130, sy_ + 40)], (250, 246, 230), 5)
    for k in range(3): line(d, [(sx_ - 120, sy_ - 25 + k * 22), (sx_ - 72, sy_ - 25 + k * 22)], INK, 3)
    title_plate(d, 'PROPULSION DEPT.', 420, SUN)

def title_plate(d, t, y, col=(255, 255, 255), bg=(60, 20, 90), size=50):
    f = font(size, True); bb = d.textbbox((0, 0), t, font=f); w = (bb[2] - bb[0]) / SS / 2 + 30
    poly(d, [(540 - w, y - 38), (540 + w, y - 38), (540 + w, y + 38), (540 - w, y + 38)], bg, 6)
    text_c(d, (540, y), t, f, col)

def panel_rock_racing(d):
    for y in range(BY0, BY1):
        t = (y - BY0) / (BY1 - BY0); c = (int(40 + 40 * t), int(20 + 20 * t), int(80 + 50 * t))
        d.line([(BX0 * SS, y * SS), (BX1 * SS, y * SS)], fill=c, width=SS + 1)
    for k, x in enumerate((180, 540, 900)):   # floodlights
        ell(d, x, 360, 46, 24, (255, 250, 210), 4)
        poly(d, [(x - 40, 380), (x + 40, 380), (x + 260, 900), (x - 260, 900)], (255, 250, 210, 60) if False else (90, 70, 130), 0, None)
    rnd = random.Random(7)
    for row in range(3):   # the cheering alien stadium
        y = 580 + row * 105
        poly(d, [(BX0, y + 30), (BX1, y + 30), (BX1, y + 70), (BX0, y + 70)], (70, 40, 110) if row % 2 else (90, 50, 140), 0, None)
        for k in range(7 - row):
            x = BX0 + 90 + k * (BX1 - BX0 - 180) / (6 - row) + rnd.uniform(-10, 10)
            ch = rnd.random() < 0.6; alien(d, x, y + 60, 0.68 + 0.06 * row, body=[LIME, (150, 230, 120), (90, 200, 160)][k % 3], cheer=ch)
            if ch and k % 2 == 0:   # foam finger
                fx_, fy_ = x + 40 * (0.68 + 0.06 * row), y - 40
                poly(d, [(fx_ - 14, fy_ + 10), (fx_ + 14, fy_ + 10), (fx_ + 14, fy_ - 20), (fx_ + 4, fy_ - 20), (fx_ + 4, fy_ - 58), (fx_ - 6, fy_ - 58), (fx_ - 6, fy_ - 20), (fx_ - 14, fy_ - 20)], SUN, 4)
    poly(d, [(640, 820), (980, 820), (980, 905), (640, 905)], (250, 250, 245), 6); text_c(d, (810, 862), 'GO #3!', font(58, True), ORANGE)
    poly(d, [(BX0, 940), (BX1, 940), (BX1, BY1), (BX0, BY1)], TAN, 0, None)
    for k in range(4): line(d, [(BX0, 1040 + k * 150), (BX1, 1000 + k * 165)], (255, 255, 255), 6)   # lanes
    for k in range(10):   # chequered finish line on the right
        for j in range(2): poly(d, [(800 + j * 30, 960 + k * 56), (830 + j * 30, 960 + k * 56), (830 + j * 30, 1016 + k * 56), (800 + j * 30, 1016 + k * 56)], (255, 255, 255) if (k + j) % 2 else INK, 0, None)
    for n, (x, y, sz) in enumerate(((700, 1050, 90), (430, 1180, 110), (600, 1400, 170)), 1):   # the racers
        for k in range(4): line(d, [(x - sz - 40 - k * 30, y - 40 + k * 22), (x - sz - 140 - k * 30, y - 40 + k * 22)], (255, 255, 255), 6)
        puff(d, x - sz * 1.1, y + sz * 0.3, sz * 0.3)
        rock(d, x, y, sz, sz * 0.7, seed=20 + n, col=[(70, 58, 62), (88, 70, 64), (60, 56, 70)][n - 1])
        helmet(d, x + sz * 0.05, y - sz * 0.55, sz * 0.48, [ORANGE, BLUE, PINK][n - 1])
        bib(d, x, y - sz * 0.02, sz * 0.85, sz * 0.62, n)
    tx, ty = 200, 1020   # the trophy: a golden rock on a cup
    poly(d, [(tx - 60, ty + 95), (tx + 60, ty + 95), (tx + 45, ty + 40), (tx - 45, ty + 40)], (120, 70, 30), 6)
    d.chord(S(tx - 75, ty - 70, tx + 75, ty + 60), 0, 180, fill=SUN, outline=INK, width=lw(6)); line(d, [(tx, ty + 50), (tx, ty + 40)], INK, 10)
    rock(d, tx, ty - 30, 60, 45, seed=77, col=(240, 180, 40))
    stars(d, 6, (tx - 90, ty - 120, tx + 90, ty - 40), 5, (255, 250, 200))
    title_plate(d, 'ROCK RACING LEAGUE', 470, (255, 255, 255), ORANGE, 40)

def panel_air_hockey(d):
    poly(d, [(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)], (28, 14, 48), 0, None)
    rnd = random.Random(9)
    for k in range(70):   # crowd silhouettes with glowing eyes
        x = rnd.uniform(BX0, BX1); y = rnd.uniform(560, 700)
        ell(d, x, y, 26, 30, (120, 76, 160), 0, None); ell(d, x - 8, y, 5, 3, LIME, 0, None); ell(d, x + 8, y, 5, 3, LIME, 0, None)
    ell(d, 540, 730, 40, 26, (255, 70, 60), 5)   # goal lamp
    for k in range(6): a = math.radians(200 + k * 28); line(d, [(540 + 52 * math.cos(a), 730 + 34 * math.sin(a)), (540 + 90 * math.cos(a), 730 + 58 * math.sin(a))], (255, 120, 90), 6)
    # scoreboard
    poly(d, [(200, 350), (880, 350), (880, 560), (200, 560)], (14, 8, 24), 8)
    text_c(d, (540, 400), 'AIR HOCKEY FINAL', font(44, True), SUN)
    text_c(d, (420, 492), '3', font(100, True), (80, 255, 200)); text_c(d, (540, 487), ':', font(86, True), (255, 255, 255)); text_c(d, (660, 492), '2', font(100, True), (255, 90, 170))
    # the neon rink in perspective
    rink = [(200, 760), (880, 760), (960, 1600), (120, 1600)]
    poly(d, rink, (70, 130, 210), 14, (170, 250, 255))
    poly(d, [(200, 790), (880, 790), (900, 900), (180, 900)], (100, 165, 235), 0, None)   # ice sheen
    line(d, [(150, 1130), (930, 1130)], (255, 90, 170), 8)                                      # centre line
    d.ellipse(S(400, 1060, 680, 1200), outline=(255, 90, 170), width=lw(8))
    for (gx, gy, gw) in ((540, 770, 150), (540, 1560, 230)): poly(d, [(gx - gw, gy - 14), (gx + gw, gy - 14), (gx + gw, gy + 14), (gx - gw, gy + 14)], (120, 240, 255), 4)   # goals
    for k in range(7): line(d, [(320 + k * 70, 1546), (340 + k * 70, 1600)], (170, 250, 255), 4)   # goal net
    text_c(d, (420, 1430), 'SAVE?!', font(84, True), SUN, stroke=8)
    # the boulder puck flying, with a neon streak
    for k in range(5): line(d, [(860 + k * 30, 1300 + k * 18), (800 + k * 20, 1240 + k * 12)], (120, 240, 255), 7)
    ell(d, 690, 1215, 200, 125, (150, 250, 255), 0, None); ell(d, 690, 1215, 185, 112, (90, 200, 240), 0, None)   # puck glow
    rock(d, 690, 1210, 170, 100, seed=31)
    # two alien players with mallets
    for (x, y, s, col) in ((330, 960, 1.0, (80, 255, 200)), (830, 1500, 1.5, (255, 90, 170))):
        alien(d, x, y, s)
        ell(d, x + 70 * s, y - 40 * s, 40 * s, 22 * s, col, 5); ell(d, x + 70 * s, y - 58 * s, 16 * s, 16 * s, shade(col, 0.8), 4)
    # the referee: a rock in a striped shirt with a whistle
    rx, ry = 360, 1130
    rock(d, rx, ry, 135, 150, seed=40, col=(96, 84, 88))
    for k in range(5):
        x0 = rx - 95 + k * 40; poly(d, [(x0, ry - 30), (x0 + 20, ry - 30), (x0 + 20, ry + 70), (x0, ry + 70)], INK if k % 2 == 0 else (250, 250, 250), 0, None)
    d.rectangle(S(rx - 100, ry - 32, rx + 100, ry + 72), outline=INK, width=lw(6))
    for sx in (-1, 1): ell(d, rx + sx * 32, ry - 82, 16, 16, (255, 255, 255), 5); ell(d, rx + sx * 32, ry - 79, 7, 7, INK, 0, None)
    ell(d, rx + 40, ry - 48, 30, 18, SUN, 6); line(d, [(rx + 20, ry - 40), (rx - 10, ry - 20)], INK, 3)
    for k in range(3): line(d, [(rx + 52 + k * 6, ry - 56 - k * 14), (rx + 80 + k * 10, ry - 66 - k * 20)], (255, 255, 255), 5)   # tweet!

# ---------------------------------------------------------------- thought bubble + ALIEN CAM filter
def bubble_mask():
    m = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(m)
    cx, cy, rx, ry = 540, 960, 480, 660
    d.ellipse(S(cx - rx + 40, cy - ry + 40, cx + rx - 40, cy + ry - 40), fill=255)
    n = 22
    for k in range(n):   # cloud scallops along the rim
        a = 2 * math.pi * k / n; x, y = cx + (rx - 40) * math.cos(a), cy + (ry - 40) * math.sin(a); r = 78 + 18 * math.sin(k * 2.3)
        d.ellipse(S(x - r, y - r, x + r, y + r), fill=255)
    return m

def alien_cam(panel_fn, tag):
    bg = Image.new('RGB', (W * SS, H * SS)); d = ImageDraw.Draw(bg)
    for y in range(H):   # dreamy outside: plum to violet, a few sparkles
        t = y / H; c = (int(60 + 50 * t), int(30 + 20 * t), int(90 + 60 * t)); d.line([(0, y * SS), (W * SS, y * SS)], fill=c, width=SS + 1)
    stars(d, 40, (0, 0, W, H), 2, (255, 230, 160))
    scene = Image.new('RGB', (W * SS, H * SS), (0, 0, 0)); ds = ImageDraw.Draw(scene); panel_fn(ds)
    k_in = 0.88   # pull the art inside the cloud edge: shrink the content box about its centre, pad with its own blurred edges
    box = (BX0 * SS, BY0 * SS, BX1 * SS, BY1 * SS); crop = scene.crop(box); bw, bh = crop.size
    pad = crop.resize((bw, bh)).filter(ImageFilter.GaussianBlur(30 * SS))
    sm = crop.resize((int(bw * k_in), int(bh * k_in)), Image.LANCZOS); pad.paste(sm, ((bw - sm.width) // 2, (bh - sm.height) // 2))
    scene = Image.new('RGB', (W * SS, H * SS), (0, 0, 0)); scene.paste(pad.resize((int(bw * 1.08), int(bh * 1.08))), (box[0] - int(bw * 0.04), box[1] - int(bh * 0.04)))
    # ALIEN CAM filter: green cast, scanlines, vignette, REC overlay
    g = Image.new('RGB', scene.size, (60, 255, 90)); scene = Image.blend(scene, ImageChops.multiply(scene, g), 0.12)
    sl = Image.new('L', scene.size, 0); dsl = ImageDraw.Draw(sl)
    for y in range(0, H * SS, 8 * SS): dsl.rectangle([0, y, W * SS, y + 2 * SS], fill=40)
    scene = Image.composite(Image.new('RGB', scene.size, (0, 30, 0)), scene, sl)
    vg = Image.new('L', (W, H), 0); dv = ImageDraw.Draw(vg); dv.ellipse([W * 0.12, H * 0.2, W * 0.88, H * 0.75], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(160)).resize(scene.size)
    scene = Image.composite(scene, ImageChops.multiply(scene, Image.new('RGB', scene.size, (120, 150, 120))), vg)
    do = ImageDraw.Draw(scene)
    m = bubble_mask(); bg.paste(scene, (0, 0), m)
    # bubble rim (ink + cream) and the trailing thought dots toward the thinker (bottom left)
    edge = m.filter(ImageFilter.MaxFilter(2 * 10 * SS + 1)); ring = ImageChops.subtract(edge, m)
    bg.paste(Image.new('RGB', bg.size, CREAM), (0, 0), ring)
    edge2 = edge.filter(ImageFilter.MaxFilter(2 * 6 * SS + 1)); ring2 = ImageChops.subtract(edge2, edge)
    bg.paste(Image.new('RGB', bg.size, INK), (0, 0), ring2)
    db = ImageDraw.Draw(bg)
    for (x, y, r) in ((200, 1700, 44), (135, 1790, 30), (90, 1860, 19)): ell(db, x, y, r, r, CREAM, 8)
    # the ALIEN CAM camcorder HUD over the whole frame, clear of the bubble art
    for (x, y, sx, sy) in ((50, 90, 1, 1), (1030, 90, -1, 1), (50, 1870, 1, -1), (1030, 1870, -1, -1)):
        line(db, [(x, y + sy * 80), (x, y), (x + sx * 80, y)], (190, 255, 180), 8)
    ell(db, 110, 165, 16, 16, (255, 50, 50), 0, None); text_c(db, (140, 165), 'REC', font(48, True), (230, 255, 225), anchor='lm')
    db.rounded_rectangle(S(640, 132, 1000, 198), radius=14 * SS, fill=(30, 110, 45), outline=(190, 255, 180), width=lw(4))
    text_c(db, (820, 165), 'ALIEN CAM', font(40, True), (200, 255, 190))
    text_c(db, (1000, 1800), '00:41:27', font(48, True), (230, 255, 225), anchor='rm')
    for k in range(4): db.rectangle(S(780 + k * 40, 1730, 810 + k * 40, 1752), fill=(190, 255, 180))   # battery bars
    im = bg.resize((W, H), Image.LANCZOS)
    return im

# ---------------------------------------------------------------- livestream screen
def livestream(out_dir):
    im = Image.new('RGB', (W * SS, H * SS)); d = ImageDraw.Draw(im)
    for y in range(H): t = y / H; d.line([(0, y * SS), (W * SS, y * SS)], fill=(int(46 + 30 * t), int(24 + 10 * t), int(60 + 30 * t)), width=SS + 1)
    px0, py0, px1, py1 = 150, 120, 930, 1800                                                      # the phone
    d.rounded_rectangle(S(px0 - 22, py0 - 22, px1 + 22, py1 + 22), radius=110 * SS, fill=(20, 16, 24), outline=INK, width=lw(8))
    d.rounded_rectangle(S(px0, py0, px1, py1), radius=90 * SS, fill=(250, 246, 238))
    # the video: the real frost plate (rocks sliding on sunlit ice), cropped to the phone's top area
    src = None
    for cand in ('playa__playa_wide__frost.png', 'playa__rock_low__frost.png'):
        p = os.path.join(os.environ.get('PLAYA_PLATES', os.path.join(ROOT, 'blender/sets/playa/plates')), cand)
        if os.path.exists(p): src = Image.open(p).convert('RGB'); break
    vx0, vy0, vx1, vy1 = px0 + 24, py0 + 110, px1 - 24, py0 + 1020
    vw, vh = (vx1 - vx0) * SS, (vy1 - vy0) * SS
    if src:
        k = max(vw / src.width, vh / src.height); s2 = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
        ox = (s2.width - vw) // 2; oy = int((s2.height - vh) * 0.62); vid = s2.crop((ox, oy, ox + vw, oy + vh))
    else: vid = Image.new('RGB', (vw, vh), (170, 210, 235))
    mk = Image.new('L', (vw, vh), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, vw, vh], radius=40 * SS, fill=255)
    im.paste(vid, (vx0 * SS, vy0 * SS), mk); d = ImageDraw.Draw(im)
    d.rounded_rectangle(S(px0 + 330, py0 + 26, px0 + 450, py0 + 60), radius=17 * SS, fill=(20, 16, 24))        # camera notch
    # top bar on the video: LIVE pill + viewer counter
    d.rounded_rectangle(S(vx0 + 30, vy0 + 30, vx0 + 200, vy0 + 104), radius=16 * SS, fill=(235, 40, 60))
    text_c(d, (vx0 + 115, vy0 + 67), 'LIVE', font(46, True), (255, 255, 255))
    d.rounded_rectangle(S(vx0 + 215, vy0 + 30, vx0 + 480, vy0 + 104), radius=16 * SS, fill=(20, 16, 24, 180))
    ell(d, vx0 + 250, vy0 + 67, 11, 11, (255, 80, 90), 0, None); text_c(d, (vx0 + 365, vy0 + 67), '1.2M', font(46, True), (255, 255, 255))
    for k, (hx_, hy_, r) in enumerate(((vx1 - 70, vy1 - 90, 26), (vx1 - 120, vy1 - 190, 20), (vx1 - 60, vy1 - 270, 30), (vx1 - 110, vy1 - 380, 18), (vx1 - 70, vy1 - 470, 22))):   # heart spam
        col = [(255, 70, 110), (255, 140, 60), (255, 70, 110), (160, 110, 255), (255, 70, 110)][k]
        d.ellipse(S(hx_ - r, hy_ - r, hx_, hy_), fill=col); d.ellipse(S(hx_, hy_ - r, hx_ + r, hy_), fill=col)
        d.polygon([(x * SS, y * SS) for x, y in ((hx_ - r, hy_ - r / 2), (hx_ + r, hy_ - r / 2), (hx_, hy_ + r))], fill=col)
    # channel row under the video (no brand): an alien avatar, a made-up handle, a sad follow button
    ay = vy1 + 70
    ell(d, px0 + 90, ay, 42, 42, LIME, 5); ell(d, px0 + 78, ay - 2, 8, 12, INK, 0, None); ell(d, px0 + 102, ay - 2, 8, 12, INK, 0, None)
    text_c(d, (px0 + 150, ay - 14), 'AlienRockTours', font(34, True), INK, anchor='lm')
    text_c(d, (px0 + 150, ay + 24), 'ice?? who ordered ice', font(26), (120, 110, 130), anchor='lm')
    # comments flooding in
    cy = ay + 70
    for name, msg, col in (('rocklover', 'ICE??', BLUE), ('dusty_d', 'REFUND', ORANGE), ('m00nwalk', 'its literally ice', TEAL),
                           ('qq_77', 'REFUND', PINK)):
        ell(d, px0 + 70, cy + 22, 24, 24, col, 4)
        text_c(d, (px0 + 110, cy + 2), name, font(30, True), (120, 110, 130), anchor='lm')
        f = font(58 if msg in ('ICE??', 'REFUND') else 42, True)
        if msg == 'ICE??': d.rounded_rectangle(S(px0 + 96, cy + 18, px0 + 320, cy + 78), radius=16 * SS, fill=(255, 220, 90))
        text_c(d, (px0 + 110, cy + 48), msg, f, INK, anchor='lm'); cy += 104
    d.rounded_rectangle(S(px0 + 40, py1 - 110, px1 - 40, py1 - 40), radius=35 * SS, fill=(236, 230, 240))
    text_c(d, (px0 + 80, py1 - 75), 'Add a comment...', font(30), (150, 140, 160), anchor='lm')
    return im.resize((W, H), Image.LANCZOS)

# ---------------------------------------------------------------- sprites the engine composites
def price_card(price):
    w, h = 300, 190; im = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle(S(8, 14, w - 8, h - 6), radius=22 * SS, fill=(0, 0, 0, 90))
    d.rounded_rectangle(S(4, 4, w - 12, h - 16), radius=22 * SS, fill=SUN, outline=INK, width=lw(7))
    d.ellipse(S(22, 20, 44, 42), fill=CREAM, outline=INK, width=lw(4))                              # string hole
    text_c(d, (w / 2 - 4, h / 2 - 8), price, font(92, True), INK)
    return im.resize((w, h), Image.LANCZOS)

def wood_sign(lines, strike=None, w=760, h=380):
    """Hand-painted plank sign sprite on two posts (RGBA): `strike` crosses out that line's first word."""
    ph = 300; im = Image.new('RGBA', (w * SS, (h + ph) * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for x in (90, w - 120): d.rectangle(S(x, h - 40, x + 30, h + ph), fill=(107, 74, 46), outline=INK, width=lw(5))
    d.rounded_rectangle(S(6, 6, w - 6, h - 6), radius=18 * SS, fill=(128, 78, 40), outline=INK, width=lw(8))
    for y in (h * 0.36, h * 0.68): line(d, [(16, y), (w - 16, y)], (96, 56, 30), 4)
    sz = [90, 120]; ys = [h * 0.30, h * 0.70]
    for i, t in enumerate(lines):
        fs_ = sz[i]
        while d.textbbox((0, 0), t, font=font(fs_, True))[2] > (w - 70) * SS: fs_ -= 4
        sz[i] = fs_; text_c(d, (w / 2, ys[i]), t, font(fs_, True), (250, 236, 200))
        if strike == i:
            f = font(sz[i], True); first = t.split(' ')[0]; bb = d.textbbox((0, 0), t, font=f); fb = d.textbbox((0, 0), first, font=f)
            x0 = w / 2 - (bb[2] - bb[0]) / SS / 2; x1 = x0 + (fb[2] - fb[0]) / SS
            line(d, [(x0 - 12, ys[i] + 20), (x1 + 12, ys[i] - 24)], (215, 20, 30), 26)
    return im.resize((w, h + ph), Image.LANCZOS)

def plate_json(path, extra=None):
    js = {'ground_y': 1900, 'px_per_m': 300, 'horizon_y': -1, 'light_dir': 'top', 'tint': '#ffffff', 'view': 'insert',
          'note': 'full-frame 2D insert, no characters'}
    js.update(extra or {}); json.dump(js, open(os.path.splitext(path)[0] + '.json', 'w'), indent=1)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out'); a = ap.parse_args()
    out = a.out or os.path.join(ROOT, 'blender/sets/inserts/plates'); os.makedirs(out, exist_ok=True)
    spr = os.path.join(os.path.dirname(out), 'sprites') if not a.out else os.path.join(out, 'sprites'); os.makedirs(spr, exist_ok=True)
    for tag, fn in (('leaf_blower_aliens', panel_leaf_blower), ('rock_racing_league', panel_rock_racing), ('alien_air_hockey_final', panel_air_hockey)):
        im = alien_cam(fn, tag)
        names = [f'inserts__alien_cam__day__{tag}.png'] + (['inserts__alien_cam__day.png'] if tag == 'leaf_blower_aliens' else [])
        for nm in names:
            p = os.path.join(out, nm); im.save(p, optimize=True); plate_json(p, {'panel': tag, 'price_card_xy': [860, 1500]}); print('PLATE', p)
    p = os.path.join(out, 'inserts__gps_screen__day.png'); livestream(out).save(p, optimize=True); plate_json(p, {'panel': 'livestream_screen', 'counter_xy': [471, 290]}); print('PLATE', p)
    for v in ('$30', '$40', '$50'): price_card(v).save(os.path.join(spr, f'price_card_{v[1:]}.png'))
    wood_sign(['ICE TOURS', '$5']).save(os.path.join(spr, 'tour_sign_ice.png'))
    wood_sign(['ALIEN ICE TOURS', '$5'], strike=0).save(os.path.join(spr, 'tour_sign_ice_strike.png'))
    wood_sign(['ALIEN ROCK TOURS', 'NIGHT ONLY']).save(os.path.join(spr, 'tour_sign_free.png'))
    print('SPRITES', spr)

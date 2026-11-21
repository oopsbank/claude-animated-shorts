# Held props for the bean cast (video 2 and later), drawn in the cast ink style (ink.py) at the dot hand.
# draw(C, kind, hand, u, side, two): hand = (x, y) design units, u = head width / 100, side = -1 left hand / +1 right
# hand / 0 centred, two = (left_hand, right_hand) for a two-handed grip (arm_pose=('hold', 'hold')).
# Parameterised names: 'flag:<text>', 'gary_rock:askew', 'phone:<badge>'.
import math
from ink import stamp, text, rpoly, rock_pts, googly, INK, fx

GREY = (154, 163, 173); DARK = (52, 55, 68); WHITE = (250, 248, 242)
RED = (224, 74, 58); GREEN = (111, 191, 106); YEL = (242, 194, 48)
ROCK = (140, 127, 114)


def _scr(x, y, w, h, col, r=2.0): return ('p', rpoly(x, y, w, h, r), col)


def gps_box(C, x, y, u, d, two, e):
    w, h = (62 * u, 40 * u) if two else (46 * u, 32 * u)
    cx, cy = (x, y) if two else (x - d * 2 * u, y - h / 2 + 2 * u)
    ax, ay = cx + (d if not two else 1) * w * (0.32 if not two else 0.4), cy - h / 2
    tx = ax + (14 if two else 4) * u; ty = ay - (20 if two else 26) * u
    stamp(C, [('s', [(ax, ay + 2 * u, 3.2 * u), (tx, ty, 3.2 * u)], DARK),
              ('c', tx, ty - 2 * u, 4.6 * u, RED),
              ('p', rpoly(cx, cy, w, h, 6 * u), GREY)], e,
          details=[_scr(cx - w * 0.12, cy - h * 0.05, w * 0.52, h * 0.5, (38, 40, 62), 2.5 * u),
                   ('c', cx + w * 0.33, cy - h * 0.18, 3 * u, (255, 120, 90)),
                   ('p', rpoly(cx + w * 0.33, cy + h * 0.2, 7 * u, 4 * u, 1.5 * u), DARK)])
    text(C, cx - w * 0.12, cy - h * 0.05, 'GPS', h * 0.3, (255, 196, 70))


def mug(C, x, y, u, d, two, e):
    k = 1.3; cx, cy = x + d * 7 * u, y - 6 * u      # the hand wraps the mug's near side
    stamp(C, [('s', [(cx + d * 13 * k * u, cy - 6 * k * u, 3.4 * u), (cx + d * 20 * k * u, cy - 1 * k * u, 3.4 * u), (cx + d * 13 * k * u, cy + 5 * k * u, 3.4 * u)], (236, 236, 230)),
              ('p', rpoly(cx, cy, 26 * k * u, 28 * k * u, 4 * u), (236, 236, 230))], e * 0.85,
          details=[('p', rpoly(cx, cy - 11 * k * u, 20 * k * u, 4 * u, 2 * u), (120, 70, 40)), ('p', rpoly(cx + d * 2 * u, cy + 3 * u, 10 * k * u, 10 * k * u, 3 * u), (232, 90, 80))])


def screwdriver(C, x, y, u, d, two, e):
    a = math.radians(-62); dx, dy = math.cos(a) * d, math.sin(a)
    p0 = (x - dx * 10 * u, y - dy * 10 * u); p1 = (x + dx * 20 * u, y + dy * 20 * u); p2 = (x + dx * 56 * u, y + dy * 56 * u)
    stamp(C, [('s', [(p1[0], p1[1], 4.6 * u), (p2[0], p2[1], 3.6 * u)], (190, 196, 206)),
              ('s', [(p0[0], p0[1], 13 * u), (p1[0], p1[1], 12 * u)], RED)], e * 0.85,
          details=[('s', [(p0[0] + dx * 4 * u, p0[1] + dy * 4 * u, 2.2 * u), (p1[0] - dx * 3 * u, p1[1] - dy * 3 * u, 2.2 * u)], (255, 140, 120))])


def googly_eyes(C, x, y, u, d, two, e):
    r = 13 * u
    s1, d1 = googly(x - d * 6 * u, y - 12 * u, r, look=(-0.6, 0.6))
    s2, d2 = googly(x + d * 20 * u, y - 22 * u, r, look=(0.7, -0.5))
    stamp(C, [s1, s2], e * 0.8, details=[d1, d2], shade=True)


def laptop(C, x, y, u, d, two, e):
    w, h = 70 * u, 46 * u
    cx = x if two else x - d * 4 * u; cy = y - h / 2 - 7 * u
    stamp(C, [('p', [(cx - w * 0.56, cy + h / 2 + 2 * u), (cx + w * 0.56, cy + h / 2 + 2 * u),
                     (cx + w * 0.62, cy + h / 2 + 11 * u), (cx - w * 0.62, cy + h / 2 + 11 * u)], (120, 126, 140)),
              ('p', rpoly(cx, cy, w, h, 4 * u), DARK)], e,
          details=[_scr(cx, cy - 1 * u, w * 0.86, h * 0.8, (228, 210, 172), 2 * u)])
    # the screen: a map of the playa with a dotted trail ending at a rock
    pts = [(cx - w * 0.34, cy + h * 0.25), (cx - w * 0.12, cy + h * 0.1), (cx + w * 0.02, cy - h * 0.02), (cx + w * 0.22, cy - h * 0.16)]
    for i in range(len(pts) - 1):
        for k in range(4):
            f = k / 4; C.dot(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f, 1.6 * u, RED)
    stamp(C, [('p', rock_pts(cx + w * 0.27, cy - h * 0.2, 6 * u, 4.5 * u, seed=3), ROCK)], e * 0.5)


def frying_pan(C, x, y, u, d, two, e):
    if two:   # a paddle: handle across both hands, pan dipping on the right
        (lx, ly), (rx, ry) = two
        L = math.hypot(rx - lx, ry - ly) or 1; ux, uy = (rx - lx) / L, (ry - ly) / L
        h0 = (lx - ux * 12 * u, ly - uy * 12 * u); h1 = (rx + ux * 14 * u, ry + uy * 14 * u)
        pc = (h1[0] + ux * 20 * u, h1[1] + uy * 20 * u)
        stamp(C, [('s', [(h0[0], h0[1], 7 * u), (h1[0], h1[1], 7 * u)], (58, 50, 46)),
                  ('p', [fx.rot(pc[0] + 13 * u * math.cos(t), pc[1] + 22 * u * math.sin(t), pc[0], pc[1], -35) for t in (i * math.pi / 14 for i in range(28))], DARK)], e,
              details=[('p', [fx.rot(pc[0] + 8 * u * math.cos(t), pc[1] + 16 * u * math.sin(t), pc[0], pc[1], -35) for t in (i * math.pi / 14 for i in range(28))], (82, 86, 100))])
        return
    a = math.radians(-70); dx, dy = math.cos(a) * d, math.sin(a)
    p1 = (x + dx * 30 * u, y + dy * 30 * u); pc = (x + dx * 52 * u, y + dy * 52 * u)
    stamp(C, [('s', [(x - dx * 6 * u, y - dy * 6 * u, 7 * u), (p1[0], p1[1], 6 * u)], (58, 50, 46)), ('c', pc[0], pc[1], 24 * u, DARK)], e,
          details=[('c', pc[0], pc[1], 17 * u, (82, 86, 100)), ('c', pc[0] - 6 * u, pc[1] - 6 * u, 4 * u, (120, 124, 140))])


def ticket(C, x, y, u, d, two, e):
    cx, cy = x + d * 4 * u, y - 14 * u
    stamp(C, [('p', rpoly(cx, cy, 52 * u, 25 * u, 2 * u, ang=-12 * d), (247, 180, 196))], e * 0.8,
          details=[('c', *fx.rot(cx - 26 * u, cy, cx, cy, -12 * d), 4 * u, INK), ('c', *fx.rot(cx + 26 * u, cy, cx, cy, -12 * d), 4 * u, INK)])
    text(C, cx, cy, 'ADMIT 1', 8.5 * u, (150, 40, 70), rot=12 * d, maxw=42 * u)


def cash_fan(C, x, y, u, d, two, e):
    for i, ang in enumerate((-118, -100, -82, -64, -46)):
        a = ang if d >= 0 else -180 - ang
        r = math.radians(a); cx, cy = x + math.cos(r) * 24 * u, y + math.sin(r) * 24 * u
        stamp(C, [('p', rpoly(cx, cy, 44 * u, 20 * u, 1.5 * u, ang=a), GREEN)], e * 0.7,
              details=[('p', rpoly(cx, cy, 34 * u, 12 * u, 1 * u, ang=a), (88, 160, 84)), ('c', *fx.rot(cx + 9 * u, cy, cx, cy, a), 4.5 * u, (170, 225, 160))])
        tx, ty = fx.rot(cx + 9 * u, cy, cx, cy, a)
        text(C, tx, ty, '$', 6 * u, (40, 100, 44), rot=-a)
    C.dot(x, y, 5.5 * u)


def camera(C, x, y, u, d, two, e):
    cx, cy = (x, y) if two else (x - d * 2 * u, y - 13 * u)
    stamp(C, [('p', rpoly(cx - 8 * u, cy - 17 * u, 16 * u, 10 * u, 2 * u), DARK),
              ('p', rpoly(cx, cy, 48 * u, 30 * u, 5 * u), DARK), ('c', cx + 4 * u, cy + 1 * u, 12 * u, (150, 156, 170))], e,
          details=[('c', cx + 4 * u, cy + 1 * u, 7.5 * u, (34, 36, 52)), ('c', cx + 1 * u, cy - 2 * u, 2.6 * u, (230, 240, 255)),
                   ('p', rpoly(cx - 15 * u, cy - 8 * u, 8 * u, 5 * u, 1 * u), WHITE), ('c', cx + 17 * u, cy - 9 * u, 2.4 * u, RED)])


def flashlight(C, x, y, u, d, two, e):
    a = math.radians(-35); dx, dy = math.cos(a) * d, math.sin(a)
    tip = (x + dx * 30 * u, y + dy * 30 * u)
    # flat beam cone (no outline, low alpha, no blur)
    from PIL import Image, ImageDraw
    nx, ny = -dy, dx
    L, Wb = 150 * u, 44 * u
    cone = [(tip[0] + nx * 7 * u, tip[1] + ny * 7 * u), (tip[0] + dx * L + nx * Wb, tip[1] + dy * L + ny * Wb),
            (tip[0] + dx * L - nx * Wb, tip[1] + dy * L - ny * Wb), (tip[0] - nx * 7 * u, tip[1] - ny * 7 * u)]
    lay = Image.new('RGBA', C.im.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).polygon(C.P(cone), fill=(255, 236, 150, 70))
    C.im.alpha_composite(lay)
    stamp(C, [('s', [(x - dx * 8 * u, y - dy * 8 * u, 9 * u), (x + dx * 20 * u, y + dy * 20 * u, 9 * u)], YEL),
              ('s', [(x + dx * 22 * u, y + dy * 22 * u, 14 * u), (tip[0], tip[1], 15 * u)], YEL)], e * 0.85,
          details=[('s', [(tip[0] + dx * 1 * u, tip[1] + dy * 1 * u, 9 * u), (tip[0] + dx * 2 * u, tip[1] + dy * 2 * u, 9 * u)], (255, 250, 220))])


def phone(C, x, y, u, d, two, e, badge='LIVE'):
    if two: cx, cy, w, h = x, y, 46 * u, 28 * u
    else: cx, cy, w, h = x + d * 8 * u, y - 20 * u, 26 * u, 46 * u
    stamp(C, [('p', rpoly(cx, cy, w, h, 4 * u), DARK)], e * 0.85,
          details=[_scr(cx, cy, w - 6 * u, h - 6 * u, (120, 190, 235), 2 * u),
                   ('p', rock_pts(cx, cy + h * 0.16, w * 0.2, h * 0.12 if not two else h * 0.16, seed=5), ROCK),
                   ('p', rpoly(cx - w * 0.1, cy - h * 0.28, 19 * u, 8.5 * u, 4 * u), RED)])
    text(C, cx - w * 0.1, cy - h * 0.28, badge, 5.5 * u, (255, 255, 255))


def selfie_stick(C, x, y, u, d, two, e):
    dd = d or -1
    top = (x + dd * 22 * u, y - 150 * u)
    stamp(C, [('s', [(x - dd * 2 * u, y + 10 * u, 5.5 * u), (top[0], top[1] + 14 * u, 4.5 * u)], (110, 114, 126)),
              ('p', rpoly(top[0], top[1], 24 * u, 40 * u, 4 * u, ang=dd * 10), DARK)], e * 0.85,
          details=[('c', *fx.rot(top[0] - 5 * u, top[1] - 12 * u, top[0], top[1], dd * 10), 3.4 * u, (120, 124, 140)),
                   ('c', *fx.rot(top[0] + 5 * u, top[1] - 12 * u, top[0], top[1], dd * 10), 1.6 * u, RED)])


def megaphone(C, x, y, u, d, two, e):
    a = math.radians(-38); dx, dy = math.cos(a) * d, math.sin(a); nx, ny = -dy, dx
    def P(f, w): return (x + dx * f * u + nx * w * u, y + dy * f * u + ny * w * u)
    bell = P(44, 0)
    stamp(C, [('p', [P(4, 6), P(44, 18), P(44, -18), P(4, -6)], WHITE),
              ('s', [(x - dx * 4 * u, y - dy * 4 * u, 8 * u), (x + dx * 6 * u, y + dy * 6 * u, 8 * u)], DARK),
              ('e', bell[0], bell[1], 6 * u, 18 * u, RED)], e,
          details=[('p', [P(18, 9.5), P(28, 13), P(28, -13), P(18, -9.5)], RED), ('e', bell[0] + dx * 1 * u, bell[1], 3 * u, 12 * u, (150, 40, 34))])


def flag(C, x, y, u, d, two, e, label=''):
    dd = d or 1
    top = (x + dd * 4 * u, y - 150 * u)
    fl = [(top[0], top[1] + 2 * u), (top[0] + dd * 62 * u, top[1] + 20 * u), (top[0], top[1] + 40 * u)]   # the pennant flies over the head side
    stamp(C, [('s', [(x - dd * 1 * u, y + 12 * u, 5 * u), (top[0], top[1], 5 * u)], (122, 84, 50)),
              ('p', fl, (60, 190, 210)), ('c', top[0], top[1] - 2 * u, 4.5 * u, YEL)], e * 0.85)
    if label: text(C, top[0] + dd * 24 * u, top[1] + 18 * u, label, 8 * u, (255, 255, 255), maxw=38 * u, rot=-dd * 13)


def air_hockey_mallet(C, x, y, u, d, two, e):
    k = 1.0; cx, cy = x, y + 8 * k * u     # gripped by the knob, the disc hangs under the hand
    stamp(C, [('e', cx, cy + 16 * k * u, 28 * k * u, 13 * k * u, RED), ('s', [(cx, cy + 12 * k * u, 12 * k * u), (cx, cy - 2 * k * u, 10 * k * u)], RED),
              ('c', cx, cy - 8 * k * u, 10 * k * u, RED)], e,
          details=[('e', cx, cy + 13 * k * u, 23 * k * u, 8 * k * u, (240, 104, 88)), ('c', cx - 3 * u, cy - 11 * k * u, 3 * u, (255, 160, 150))])


def gary_rock(C, x, y, u, d, two, e, askew=False):
    cx, cy = (x, y - 4 * u) if two else (x + d * 14 * u, y - 24 * u)
    rx, ry = 40 * u, 29 * u
    s1, d1 = googly(cx - 11 * u, cy - 8 * u, 9 * u, look=(0.2, 0.5))
    s2, d2 = googly(cx + 13 * u, cy - (14 if askew else 8) * u, (8 if askew else 9) * u, look=((0.8, -0.6) if askew else (0.2, 0.5)))
    stamp(C, [('p', rock_pts(cx, cy, rx, ry, seed=7, flat=0.2), ROCK)], e,
          details=[('p', rock_pts(cx - 14 * u, cy + 12 * u, 8 * u, 3 * u, seed=2), (120, 108, 96))])
    stamp(C, [s1, s2], e * 0.6, details=[d1, d2])


NAMES = {'mug': mug, 'gps_box': gps_box, 'screwdriver': screwdriver, 'googly_eyes': googly_eyes, 'laptop': laptop,
         'frying_pan': frying_pan, 'ticket': ticket, 'cash_fan': cash_fan, 'camera': camera, 'flashlight': flashlight,
         'phone': phone, 'selfie_stick': selfie_stick, 'megaphone': megaphone, 'flag': flag,
         'air_hockey_mallet': air_hockey_mallet, 'gary_rock': gary_rock}
TWO_HANDED = {'gps_box', 'laptop', 'frying_pan', 'camera', 'phone', 'gary_rock'}   # centred between the hands
K = 1.25                                    # props read big (video size), like the reference
TWO_W = dict(gps_box=30, laptop=38, frying_pan=20, camera=23, phone=22, gary_rock=37)   # the hands clamp the side edges   # hands sit on the fill, inside the edge   # half-width at the grip (u)


def two_halfwidth(base): return TWO_W.get(base, 26) * K


def draw(C, kind, hand, u, side=1, two=None):
    base, _, arg = kind.partition(':')
    fn = NAMES[base]
    d = side if side else 1
    if two and base in TWO_HANDED:
        x, y = (two[0][0] + two[1][0]) / 2, (two[0][1] + two[1][1]) / 2
    else:
        two = None; x, y = hand
    e = 4.4 * u; u = u * K
    kw = {}
    if base == 'flag': kw['label'] = arg
    if base == 'gary_rock': kw['askew'] = arg == 'askew'
    if base == 'phone' and arg: kw['badge'] = arg
    fn(C, x, y, u, d, two, e, **kw)
    # the caller draws the arm and dot hand over the prop afterwards, so the grip reads

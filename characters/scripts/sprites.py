# Engine-composited prop sprites for video 2 (sailing-stones), in the bean cast style (plum ink, flat fills, crescent).
#     sprite(name, t=0.0, k=1.0, **kw) -> RGBA PIL image
# Units: design units of the 600x1000 character card (an adult is ~780 units tall, 1 m ~ 450 units), so pass the
# same k the engine uses to scale character cards (k=0.5 -> half size). im.info['anchor'] = (x, y) output px of the
# ground contact point (bottom centre) for standing props; for UI cards ('banner', 'livestream_counter',
# 'price_card') the anchor is the centre. t animates the props that move (0..1 over the beat); static props ignore it.
# Names (parameterised with ':'): see NAMES at the bottom.  usage: sprites.py <name> <t> out.png
import math, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageChops
from ink import stamp, text, rpoly, rock_pts, googly, INK, S, fx
import bean

ROCK = (140, 127, 114); ROCK_DK = (112, 100, 90); DUST = (214, 182, 140); DUST_DK = (184, 150, 108)
WOOD = (176, 122, 70); WOOD_DK = (132, 88, 52); PAPER = (250, 244, 226); RED = (214, 64, 52); GREEN = (111, 191, 106)
GOLD = (242, 196, 64)
clamp, smooth, seg, lerp, out_back, bump = fx.clamp, fx.smooth, fx.seg, fx.lerp, fx.out_back, fx.bump


class Card:
    """A bean-style canvas of w x h design units (S supersampled); same interface as bean.Canvas for ink.stamp/text."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (int(w * S), int(h * S)), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def P(self, pts): return [(x * S, y * S) for x, y in pts]
    def dot(self, x, y, r, col=INK): self.d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=col)
    def out(self, k, anchor):
        im = self.im.resize((max(1, int(self.w * k)), max(1, int(self.h * k))), Image.LANCZOS)
        im.info['anchor'] = (anchor[0] * k, anchor[1] * k); return im


E = 10.0      # ink width in design units (the cast's outline is ~12 at the head, props ~10)


# ------------------------------------------------------------------ rocks
def _gary(C, cx, gy, t, askew=False, look=None, w=200):
    rx, ry = w / 2, w * 0.36
    cy = gy - ry * 0.8
    wob = math.sin(t * 2 * math.pi * 3) * 0.8 if t else 0.0          # pupils roll as he moves
    lk = look or (0.25 + 0.5 * wob, 0.55 - 0.3 * abs(wob))
    s1, d1 = googly(cx - 0.26 * rx, cy - 0.35 * ry, 0.2 * rx, look=lk)
    lk2 = (0.85, -0.55) if askew else (lk[0] - 0.2 * wob, lk[1])
    s2, d2 = googly(cx + 0.3 * rx, cy - (0.55 if askew else 0.35) * ry, (0.17 if askew else 0.2) * rx, look=lk2)
    stamp(C, [('p', rock_pts(cx, cy, rx, ry, seed=7, flat=0.3), ROCK)], E,
          details=[('p', rock_pts(cx - 0.35 * rx, cy + 0.42 * ry, 0.18 * rx, 0.07 * rx, seed=2), ROCK_DK),
                   ('p', rock_pts(cx + 0.45 * rx, cy + 0.15 * ry, 0.1 * rx, 0.05 * rx, seed=4), ROCK_DK)])
    stamp(C, [s1, s2], E * 0.6, details=[d1, d2])


def gary_rock(t=0.0, k=1.0, eyes='front', look=None, **kw):
    """Gary: a mid-size rock (~0.45 m) with two googly eyes. eyes='askew' tilts one; t>0 rolls the pupils."""
    C = Card(260, 200); _gary(C, 130, 185, t, eyes == 'askew', look); return C.out(k, (130, 185))


def rock(t=0.0, k=1.0, seed=1, w=180, **kw):
    """A plain playa rock (no eyes), for rows and sliding."""
    C = Card(w + 60, w * 0.8 + 40); gy = w * 0.8 + 25
    stamp(C, [('p', rock_pts(C.w / 2, gy - w * 0.29, w / 2, w * 0.36, seed=seed, flat=0.3), ROCK)], E)
    return C.out(k, (C.w / 2, gy))


def gary_buried(t=0.0, k=1.0, **kw):
    """Gary under the dust-storm drift: a dust mound with one googly eye poking out (pupil spins slowly with t)."""
    C = Card(320, 170); gy = 155; cx = 160
    mound = [(cx - 150 + 300 * i / 30, gy - 70 * math.sin(math.pi * i / 30) ** 1.4 * (1 + 0.08 * math.sin(i * 1.7))) for i in range(31)]
    a = t * 2 * math.pi
    s1, d1 = googly(cx + 18, gy - 78, 34, look=(math.cos(a) * 0.8, math.sin(a) * 0.8 if t else 0.6))
    stamp(C, [('p', rock_pts(cx + 18, gy - 66, 60, 26, seed=7), ROCK)], E)      # a sliver of rock under the eye
    stamp(C, [s1], E * 0.6, details=[d1])
    stamp(C, [('p', mound + [(cx + 150, gy), (cx - 150, gy)], DUST)], E,
          details=[('p', rock_pts(cx - 60, gy - 24, 26, 6, seed=3), DUST_DK), ('p', rock_pts(cx + 70, gy - 14, 20, 5, seed=5), DUST_DK)])
    # the eye pokes OUT of the dust: redraw it over the mound edge
    stamp(C, [s1], E * 0.6, details=[d1])
    return C.out(k, (cx, gy))


def gps_box(t=0.0, k=1.0, **kw):
    """The tracker: a small grey box with a whip antenna and a green LED (blinks with t)."""
    C = Card(160, 190); cx, gy = 80, 175; cy = gy - 34
    led = (120, 230, 110) if (t == 0 or (t * 8) % 1 < 0.5) else (40, 90, 50)
    stamp(C, [('s', [(cx + 34, cy - 30, 6), (cx + 42, cy - 140, 5)], (52, 55, 68)), ('c', cx + 42, cy - 146, 9, RED),
              ('p', rpoly(cx, cy, 110, 72, 12), (154, 163, 173))], E,
          details=[('p', rpoly(cx - 12, cy - 4, 56, 34, 5), (40, 70, 52)), ('c', cx + 36, cy - 14, 6, led)])
    text(C, cx - 12, cy - 4, 'GPS', 9, (150, 240, 140))
    return C.out(k, (cx, gy))


# ------------------------------------------------------------------ camp
def cooler(t=0.0, k=1.0, label=None, bob=0.0, **kw):
    """The picnic cooler (their boat home). bob=amplitude in units: rocks with t when floating."""
    C = Card(340, 230); cx, gy = 170, 215
    dy = bob * math.sin(t * 2 * math.pi * 2)
    bean.draw_cooler(C, cx, gy - 175 + dy, gy + dy, 280, 2.4, label=label)
    return C.out(k, (cx, gy))


def cooler_trophy(t=0.0, k=1.0, label="S.S. GARY", **kw):
    """The cooler as a trophy: on a stepped plinth with a brass plaque and a gold rosette (glints with t)."""
    C = Card(380, 470); cx, gy = 190, 455
    stamp(C, [('p', rpoly(cx, gy - 30, 330, 60, 6), (120, 110, 150)), ('p', rpoly(cx, gy - 120, 290, 130, 6), (150, 140, 182))], E,
          details=[('p', rpoly(cx, gy - 120, 170, 52, 4), GOLD)])
    text(C, cx, gy - 120, label, 20, (90, 60, 20), maxw=150)
    bean.draw_cooler(C, cx, gy - 185 - 165, gy - 185, 250, 2.4)
    rx, ry = cx + 70, gy - 265
    rib = [(rx - 18, ry + 10), (rx - 30, ry + 70), (rx - 8, ry + 58), (rx + 4, ry + 74), (rx + 14, ry + 10)]
    stamp(C, [('p', rib, (60, 120, 210)), ('p', fx.star_pts(rx, ry, 12, 40, 32), GOLD)], E * 0.8,
          details=[('c', rx, ry, 22, (255, 222, 120))])
    text(C, rx, ry, '1st', 15, (120, 80, 20))
    g = bump(seg(t, 0.2, 0.6)) if t else 0
    if g > 0.02:
        stamp(C, [('p', fx.star_pts(rx - 28, ry - 30, 4, 18 * g, 4 * g), (255, 255, 255))], 3 * g, shade=False)
    return C.out(k, (cx, gy))


def _tent_card(C, cx, gy, ang=0.0, col=(242, 140, 52)):
    w, h = 300, 190
    def R(p): return fx.rot(p[0], p[1], cx, gy, ang)
    dome = [R((cx - w / 2 + w * i / 24, gy - h * math.sin(math.pi * i / 24) ** 0.8)) for i in range(25)]
    door = [R((cx - 40 + 80 * i / 12, gy - 120 * math.sin(math.pi * i / 12) ** 0.9)) for i in range(13)]
    poles = [('s', [(*R((cx - w / 2 + w * i / 16, gy - h * math.sin(math.pi * i / 16) ** 0.8 * 0.98)), 4) for i in range(17)], mix(col, INK, 0.4))]
    stamp(C, [('p', dome, col)], E, details=[('p', door, mix(col, INK, 0.55))] + poles)


def mix(a, b, x): return tuple(int(a[i] + (b[i] - a[i]) * x) for i in range(3))


def tent(t=0.0, k=1.0, color='#f28c34', **kw):
    """The cousins' dome tent (orange), door zipped open."""
    C = Card(360, 240); _tent_card(C, 180, 225, 0, bean.hexrgb(color)); return C.out(k, (180, 225))


def tent_floating(t=0.0, k=1.0, color='#f28c34', **kw):
    """The tent carried off by the flash flood: tilted, bobbing and rocking with t. Anchor = the waterline centre."""
    C = Card(420, 320); a = 14 * math.sin(t * 2 * math.pi * 1.5) - 8; dy = 10 * math.sin(t * 2 * math.pi * 3)
    _tent_card(C, 210, 260 + dy, a, bean.hexrgb(color))
    wl = 268                                     # muddy water hiding the tent's foot, with a wave and spray
    wave = [(210 - 200 + 400 * i / 30, wl + 8 * math.sin(i * 0.9 + t * 20)) for i in range(31)]
    stamp(C, [('p', wave + [(410, 318), (10, 318)], (138, 104, 66))], E,
          details=[('s', [(x, y + 10, 5) for x, y in wave[2:-2]], (246, 240, 226))])
    for i, dx in enumerate((-150, 150)):
        g = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 3 + i * 2)
        stamp(C, [('c', 210 + dx, wl - 18 - 10 * g, 9 * g + 3, (120, 190, 230))], 4, shade=False)
    return C.out(k, (210, 270))


def timelapse_cam(t=0.0, k=1.0, **kw):
    """A time-lapse camera on a tripod; the red tally light blinks with t."""
    C = Card(220, 420); cx, gy = 110, 405; top = gy - 300
    legs = [('s', [(cx, top, 7), (cx + dx, gy, 6)], (80, 84, 96)) for dx in (-80, 0, 80)]
    tally = RED if (t == 0 or (t * 6) % 1 < 0.5) else (110, 40, 36)
    stamp(C, legs + [('p', rpoly(cx, top - 40, 130, 80, 10), (60, 64, 80)), ('c', cx + 50, top - 40, 32, (150, 156, 170))], E,
          details=[('c', cx + 50, top - 40, 20, (34, 36, 52)), ('c', cx + 44, top - 46, 6, (220, 230, 255)), ('c', cx - 44, top - 62, 7, tally)])
    return C.out(k, (cx, gy))


# ------------------------------------------------------------------ the guide's sign
def _sign(C, cx, gy, lines, w=440, h=210, post_h=170, cross=None):
    bt = gy - post_h - h
    stamp(C, [('p', rpoly(cx - w * 0.3, gy - (post_h + h / 2) / 2, 26, post_h + h / 2, 4), WOOD_DK),
              ('p', rpoly(cx + w * 0.3, gy - (post_h + h / 2) / 2, 26, post_h + h / 2, 4), WOOD_DK),
              ('p', rpoly(cx, bt + h / 2, w, h, 8), WOOD)], E,
          details=[('p', rpoly(cx, bt + h / 2, w - 26, h - 26, 6), PAPER)] +
                  [('c', cx + sx * (w / 2 - 22), bt + sy, 5, (120, 120, 130)) for sx in (-1, 1) for sy in (22, h - 22)])
    n = len(lines); lh = (h - 50) / n
    cols = [(150, 40, 150), (40, 140, 70), (210, 60, 40), (40, 90, 170)]
    for i, ln in enumerate(lines):
        text(C, cx, bt + 25 + lh * (i + 0.5), ln, lh * 0.5, cols[i % len(cols)], maxw=w - 60)
    if cross is not None:      # a hand-painted strike through one line
        y = bt + 25 + lh * (cross + 0.5)
        C.d.line([((cx - w * 0.36) * S, (y + 6) * S), ((cx + w * 0.36) * S, (y - 8) * S)], fill=RED, width=int(9 * S))
    return bt


def tour_sign(t=0.0, k=1.0, text_='ALIEN ROCK TOURS|NIGHT ONLY', cross=None, **kw):
    """The guide's hand-painted sign on two posts. Lines split by '|'; cross=<line index> paints a red strike."""
    C = Card(500, 440); _sign(C, 250, 425, text_.split('|'), cross=cross); return C.out(k, (250, 425))


def tour_sign_free(t=0.0, k=1.0, text_='ALIEN ROCK TOURS|NIGHT ONLY', **kw):
    """The NIGHT ONLY sign as its own sprite. t 0..0.18 shudders (the hit), a jagged crack runs down the middle by 0.3,
    then the two halves topple outward on their posts and land flat (bounce) by ~0.85; 0.85..1 settles."""
    W_, H_ = 1240, 520; cx, gy = 620, 480
    base = Card(W_, H_); _sign(base, cx, gy, text_.split('|'))
    full = base.im
    rnd = random.Random(4)
    crack = [(cx + rnd.uniform(-14, 14), y) for y in range(0, H_ + 1, 26)]
    crack[0] = (cx, 0); crack[-1] = (cx + 8, H_)
    p_crack = clamp((t - 0.12) / 0.18)
    sh = (math.sin(t * 2 * math.pi * 9) * 6 * (1 - seg(t, 0.0, 0.2))) if t < 0.2 else 0
    out = Card(W_, H_)
    if t < 0.3:
        out.im.alpha_composite(full, (int(sh * S), 0))
        if p_crack > 0:       # the crack grows down from the top
            n = max(2, int(len(crack) * p_crack))
            gy_top = gy - 170 - 210
            pts = [(x, y) for x, y in crack if y >= gy_top - 5][:n]
            if len(pts) >= 2:
                out.d = ImageDraw.Draw(out.im)
                out.d.line([((x + sh) * S, y * S) for x, y in pts], fill=INK, width=int(7 * S), joint='curve')
        return out.out(k, (cx, gy))
    # split into two halves along the crack and topple each outward about its post foot
    m = Image.new('L', full.size, 0)
    ImageDraw.Draw(m).polygon([(0, 0)] + [(x * S, y * S) for x, y in crack] + [(0, H_ * S)], fill=255)
    halves = []
    for side, mask in ((-1, m), (1, ImageChops.invert(m))):
        h = full.copy(); h.putalpha(ImageChops.multiply(full.getchannel('A'), mask))
        # ink along the broken edge
        edge = Image.new('RGBA', full.size, (0, 0, 0, 0)); ImageDraw.Draw(edge).line([(x * S, y * S) for x, y in crack], fill=INK + (255,), width=int(9 * S))
        edge.putalpha(ImageChops.multiply(edge.getchannel('A'), ImageChops.multiply(full.getchannel('A'), mask)))
        h.alpha_composite(edge); halves.append((side, h))
    f = seg(t, 0.3, 0.78)
    ang = 86 * f * f                                     # gravity: accelerates, lands at 86 deg
    if t > 0.78: ang = 86 - 7 * bump(seg(t, 0.78, 0.9)) - 2 * bump(seg(t, 0.9, 0.97))   # bounce on landing
    if t > 0.76:     # a dust puff where each half lands (behind the boards)
        g = bump(seg(t, 0.76, 1.0))
        for side in (-1, 1):
            x0 = cx + side * (0.3 * 440 + 330)
            stamp(out, [('c', x0 + dx, gy - 26 - 22 * g, (34 + 22 * g) * g, DUST) for dx in (-80, -30, 20, 70)], 6 * g, shade=True)
    lift = 98 * math.sin(math.radians(ang))     # a falling half ends up resting on its board edge, not in the ground
    for side, h in halves:
        px, py = cx + side * 0.3 * 440, gy
        r = h.rotate(-side * ang, resample=Image.BICUBIC, center=(px * S, py * S), translate=(0, -lift * S))
        out.im.alpha_composite(r)
    return out.out(k, (cx, gy))


# ------------------------------------------------------------------ cash, UI cards, scale cues
def flying_bills(t=0.0, k=1.0, count=7, direction='right', seed=3, **kw):
    """His refund cash blowing away on the breeze: bills flutter out of a bunch at the bottom-left (or right) and
    tumble off across the card. Empty at t=0 and t=1. Card 1000x700 units, anchor = where the bunch starts."""
    W_, H_ = 1000, 700; sgn = 1 if direction == 'right' else -1
    C = Card(W_, H_); rnd = random.Random(seed)
    ox, oy = (W_ / 2 - sgn * 380), H_ - 120
    for i in range(count):
        d0 = 0.04 + 0.05 * i
        p = seg(t, d0, d0 + 0.5)
        if p <= 0 or p >= 1: continue
        g = smooth(seg(p, 0, 0.05)) * (1 - smooth(seg(p, 0.85, 1.0)))
        x = ox + sgn * (820 * p ** 1.2 + 40 * math.sin(p * 9 + i))
        y = oy - (480 + rnd.uniform(-80, 80)) * math.sin(p * 1.6) + 40 * math.sin(p * 12 + i * 2)
        spin = rnd.uniform(200, 500) * p * sgn + rnd.uniform(-30, 30)
        flip = math.cos(p * rnd.uniform(8, 14) + i)
        bw, bh = 190 * g, 88 * g
        if bw < 4: continue
        fw = max(8, bw * (0.35 + 0.65 * abs(flip)))
        stamp(C, [('p', rpoly(x, y, fw, bh, 4, ang=spin), GREEN)], E * 0.8 * g,
              details=[('p', rpoly(x, y, fw * 0.8, bh * 0.62, 3, ang=spin), (88, 160, 84)), ('c', x, y, bh * 0.26, (170, 225, 160))])
    return C.out(k, (ox, oy))


def banner(t=0.0, k=1.0, text_='FINAL FAIL · LIVE', **kw):
    """A swallow-tail red banner with white Poppins text; it waves gently with t. Anchor = centre."""
    W_, H_ = 900, 220; C = Card(W_, H_); cx, cy = W_ / 2, H_ / 2; w, h = 720, 120
    wav = lambda x: 10 * math.sin(x / 120 + t * 2 * math.pi * 2)
    top = [(cx - w / 2 + w * i / 20, cy - h / 2 + wav(w * i / 20)) for i in range(21)]
    bot = [(x, y + h) for x, y in top][::-1]
    for side in (-1, 1):
        x0 = cx + side * w / 2
        tail = [(x0, cy - h / 2 + 30 + wav(0)), (x0 + side * 90, cy - h / 2 + 30), (x0 + side * 60, cy + 30), (x0 + side * 90, cy + h / 2 + 30), (x0, cy + h / 2 + 30)]
        stamp(C, [('p', tail, (160, 40, 36))], E)
    stamp(C, [('p', top + bot, RED)], E)
    text(C, cx, cy + wav(w / 2), text_, 44, (255, 255, 255), maxw=w - 60)
    return C.out(k, (cx, cy))


def livestream_counter(t=0.0, k=1.0, n='3', **kw):
    """A LIVE pill + viewer count (an eye and the number), our own UI. The LIVE dot pulses with t. Anchor = centre."""
    W_, H_ = 460, 120; C = Card(W_, H_); cy = H_ / 2
    stamp(C, [('p', rpoly(140, cy, 220, 80, 40), RED), ('p', rpoly(340, cy, 170, 80, 40), (40, 30, 48))], 6)
    pulse = 0.7 + 0.3 * math.cos(t * 2 * math.pi * 3)
    C.dot(70, cy, 13 * pulse, (255, 255, 255))
    text(C, 155, cy, 'LIVE', 34, (255, 255, 255))
    C.d.ellipse(((290 - 22) * S, (cy - 13) * S, (290 + 22) * S, (cy + 13) * S), outline=(255, 255, 255), width=int(5 * S))
    C.dot(290, cy, 7, (255, 255, 255))
    text(C, 360, cy, str(n), 36, (255, 255, 255))
    return C.out(k, (W_ / 2, cy))


def price_card(t=0.0, k=1.0, text_='$40', **kw):
    """A yellow starburst price sticker, slightly tilted, that throbs once with t. Anchor = centre."""
    C = Card(320, 320); g = 1 + 0.06 * bump(seg(t, 0.0, 0.3))
    stamp(C, [('p', fx.star_pts(160, 160, 16, 140 * g, 112 * g, ang=8), (255, 214, 64))], E)
    text(C, 160, 160, text_, 70 * g, (200, 40, 40), rot=10, maxw=200 * g)
    return C.out(k, (160, 160))


def _ghosted(C, ghost):
    if ghost:      # a translucent scale cue: the same drawing at 55% so the rock shows through
        a = C.im.getchannel('A').point(lambda v: int(v * 0.55)); C.im.putalpha(a)


def fridge_silhouette(t=0.0, k=1.0, ghost=False, **kw):
    """Scale cue: a cartoon fridge (~1.8 m), the size of the biggest sliding rocks. ghost=True draws it see-through."""
    C = Card(420, 860); cx, gy = 210, 840; top = gy - 790; w = 340
    stamp(C, [('p', rpoly(cx, top + 395, w, 790, 34), (236, 240, 244))], E,
          details=[('p', rpoly(cx, top + 270, w - 8, 7, 3), (150, 160, 175)),
                   ('p', rpoly(cx - w * 0.36, top + 160, 14, 120, 7), (150, 160, 175)),
                   ('p', rpoly(cx - w * 0.36, top + 400, 14, 150, 7), (150, 160, 175)),
                   ('p', rpoly(cx + w * 0.18, top + 120, 70, 44, 6), (255, 210, 90)),
                   ('c', cx + w * 0.3, top + 360, 16, (220, 70, 60))])
    _ghosted(C, ghost)
    return C.out(k, (cx, gy))


def phone_silhouette(t=0.0, k=1.0, ghost=False, **kw):
    """Scale cue for the ice panes' thickness: a phone seen edge-on (side buttons, camera bump), lying flat."""
    C = Card(460, 120); cx, gy = 230, 105
    stamp(C, [('p', rpoly(cx, gy - 18, 380, 30, 13), (52, 55, 68))], E * 0.8,
          details=[('p', rpoly(cx + 60, gy - 35, 60, 6, 3), (120, 126, 140)), ('p', rpoly(cx - 110, gy - 18, 150, 6, 3), (90, 180, 230))])
    _ghosted(C, ghost)
    return C.out(k, (cx, gy))


NAMES = {
    'gary_rock': (gary_rock, "Gary: mid-size rock with googly eyes. eyes='front'|'askew', look=(x, y); t rolls the pupils"),
    'gary_buried': (gary_buried, 'dust mound with one googly eye poking out; t spins the pupil'),
    'rock': (rock, 'plain playa rock. seed, w'),
    'gps_box': (gps_box, 'grey tracker box with an antenna; t blinks the LED'),
    'cooler': (cooler, 'picnic cooler. label, bob (units, floating bob with t)'),
    'cooler_trophy': (cooler_trophy, "the cooler on a plinth with a plaque and a 1st rosette. label (default 'S.S. GARY'); t glints"),
    'tent': (tent, 'orange dome tent. color'),
    'tent_floating': (tent_floating, 'the tent tilted and bobbing on flood water (anchor = waterline). t rocks it'),
    'timelapse_cam': (timelapse_cam, 'tripod time-lapse camera; t blinks the tally light'),
    'tour_sign': (tour_sign, "the guide's sign on two posts. 'tour_sign:LINE 1|LINE 2', cross=<line index>"),
    'tour_sign_free': (tour_sign_free, 'the NIGHT ONLY sign alone: shudder, crack, both halves topple flat over t'),
    'flying_bills': (flying_bills, 'refund cash fluttering away on the breeze. count, direction=right|left; empty at both ends'),
    'banner': (banner, "red swallow-tail banner. 'banner:TEXT'; waves with t"),
    'livestream_counter': (livestream_counter, "LIVE pill + viewer count. 'livestream_counter:3'"),
    'price_card': (price_card, "yellow starburst price sticker. 'price_card:$40'"),
    'fridge_silhouette': (fridge_silhouette, 'cartoon fridge (~1.8 m) as a scale cue. ghost=True draws it see-through'),
    'phone_silhouette': (phone_silhouette, 'phone seen edge-on lying flat: the ice-pane thickness cue. ghost'),
}
ARG = {'tour_sign': 'text_', 'tour_sign_free': 'text_', 'banner': 'text_', 'livestream_counter': 'n', 'price_card': 'text_',
       'gary_rock': 'eyes'}


def sprite(name, t=0.0, k=1.0, **kw):
    """Render prop sprite `name` (may carry ':arg', e.g. 'banner:FINAL FAIL · LIVE'). Unknown text in parentheses
    (shots.json notes such as 'tour_sign_free:... (a separate sprite ...)') is ignored; ' · ' separates sign lines."""
    base, _, arg = name.partition(':')
    if base not in NAMES: raise KeyError(f'unknown sprite {base!r}; known: {", ".join(NAMES)}')
    if arg:
        arg = arg.split(' (')[0].strip()
        if base.startswith('tour_sign'):
            if 'crossed out' in name: kw.setdefault('cross', 0)
            arg = arg.replace(' · ', '|')
            if base == 'tour_sign' and 'ICE TOURS' in arg and 'ALIEN' not in arg: arg = 'ALIEN|' + arg; kw.setdefault('cross', 0)
        kw[ARG.get(base, 'label')] = arg
    return NAMES[base][0](float(t), k, **kw)


if __name__ == '__main__':
    sprite(sys.argv[1], float(sys.argv[2])).save(sys.argv[3])

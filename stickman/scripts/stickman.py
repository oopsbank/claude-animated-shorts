# Original solid-colour stickman (v2): ~5 heads tall, tube body, smooth bent limbs,
# thin dark outline, lit head, expressive face. Parametric colour / pose / expression / hat / look.
# Canvas 600x1000, soles at y=975 (same contract as the card in scene2.py).
# usage: python stickman.py out.png [expr] [pose] [hex colour] [hat] [look -1..1]
import sys, math
from PIL import Image, ImageDraw, ImageChops, ImageFilter

S = 4
W, H = 600, 1000

def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mixc(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# angles in degrees from straight down; + swings toward viewer's LEFT. (upper, lower)
POSES = {
    'stand': dict(armL=(24, 10), armR=(-24, -10), legL=(10, 1), legR=(-10, -1)),
    'wave':  dict(armL=(24, 10), armR=(-125, -168), legL=(10, 1), legR=(-10, -1)),
    'walk':  dict(armL=(-22, -42), armR=(26, 10), legL=(-20, 0), legR=(18, 40)),
    'run':   dict(armL=(-55, -125), armR=(45, -15), legL=(-38, 8), legR=(30, 85)),
    'point': dict(armL=(24, 10), armR=(-82, -88), legL=(11, 1), legR=(-11, -1)),
    'shrug': dict(armL=(60, -35), armR=(-60, 35), legL=(10, 1), legR=(-10, -1)),
    'think': dict(armL=(10, -84, 0.72), armR=(-30, 160), legL=(10, 1), legR=(-10, -1)),   # arm across the belly, other hand on the chin
    'cheer': dict(armL=(145, 160), armR=(-145, -160), legL=(16, 2), legR=(-16, -2)),
}

SIDE_POSES = {'walk', 'run'}

def draw(expr='neutral', pose='stand', color='#4a86e0', hat=None, look=0.0):
    if pose in SIDE_POSES and look == 0.0: look = 0.7      # side-on body: face turns toward the direction of travel
    C = hexrgb(color); INK = (18, 16, 26); hi = mixc(C, (255, 255, 255), 0.22)
    im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = POSES[pose]

    R = 98                                  # head radius -> ~5 heads tall
    T = 50                                  # limb thickness
    TB = 56                                 # torso thickness
    OUT = 3.2                               # outline width
    head = [300, 140]
    hip = (300, 520); shoulder = (300, 262)
    seg_arm, seg_leg = 124, 205

    def limb(root, ang, seg):              # ang = (upper, lower[, lower-length factor])
        a1, a2 = math.radians(ang[0]), math.radians(ang[1]); seg2 = seg * (ang[2] if len(ang) > 2 else 1.0)
        j = (root[0] - math.sin(a1) * seg, root[1] + math.cos(a1) * seg)
        e = (j[0] - math.sin(a2) * seg2, j[1] + math.cos(a2) * seg2)
        return root, j, e

    def path(root, j, e, n=60):            # smooth quadratic through the joint
        cx, cy = 2 * j[0] - (root[0] + e[0]) / 2, 2 * j[1] - (root[1] + e[1]) / 2
        return [((1 - t) ** 2 * root[0] + 2 * (1 - t) * t * cx + t * t * e[0],
                 (1 - t) ** 2 * root[1] + 2 * (1 - t) * t * cy + t * t * e[1]) for t in (i / n for i in range(n + 1))]

    legs = [limb(hip, P['legL'], seg_leg), limb(hip, P['legR'], seg_leg)]
    arms = [limb(shoulder, P['armL'], seg_arm), limb(shoulder, P['armR'], seg_arm)]
    lowest = max(max(p[1] for p in path(*l)) for l in legs) + T / 2
    dy = 975 - lowest
    xs = [p[0] for l in legs + arms for p in path(*l)] + [300 - R, 300 + R]
    dx = 300 - (min(xs) + max(xs)) / 2
    def mv(pts): return [(x + dx, y + dy) for x, y in pts]
    head[0] += dx; head[1] += dy

    def stamp(pts, w, col):
        r = w * S / 2
        for x, y in pts: d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=col)
    def part(pts, w, col):                 # outline then fill, so front parts read over back parts
        stamp(pts, w + 2 * OUT, INK); stamp(pts, w, col)
    def lpts(l): return mv(path(*l))
    def front_arm(pts):                     # outline only where the arm leaves the torso; fill from the root
        stamp(pts[10:], T + 2 * OUT, INK); stamp(pts, T, C)

    torso = mv([(300, 232 + i * (520 - 232) / 40) for i in range(41)])
    # back arm + legs + torso as ONE merged silhouette (no inner seams), like the reference
    # Facing the viewer: both arms belong to the one merged silhouette (symmetric, nothing turned).
    # Side-on poses (walk/run) layer a back arm behind and a front arm over the torso.
    side = pose in SIDE_POSES
    body = [(lpts(legs[1]), T), (lpts(legs[0]), T), (torso, TB)]
    if side: body.insert(0, (lpts(arms[1]), T))
    else: body = [(lpts(arms[0]), T), (lpts(arms[1]), T)] + body
    for pts, w in body: stamp(pts, w + 2 * OUT, INK)
    for pts, w in body: stamp(pts, w, C)
    hx, hy = head
    d.ellipse([(hx - R - OUT) * S, (hy - R - OUT) * S, (hx + R + OUT) * S, (hy + R + OUT) * S], fill=INK)
    d.ellipse([(hx - R) * S, (hy - R) * S, (hx + R) * S, (hy + R) * S], fill=C)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse([(hx - R) * S, (hy - R) * S, (hx + R) * S, (hy + R) * S], fill=255)
    cap = Image.new('L', im.size, 0); ImageDraw.Draw(cap).ellipse([(hx - R * 1.25) * S, (hy - R * 1.9) * S, (hx + R * 1.25) * S, (hy + R * 0.15) * S], fill=150)
    cap = ImageChops.multiply(cap.filter(ImageFilter.GaussianBlur(26 * S)), m)
    lay = Image.new('RGBA', im.size, hi + (255,)); lay.putalpha(cap); im.alpha_composite(lay); d = ImageDraw.Draw(im)
    if side or pose == 'think':
        front_arm(lpts(arms[0]))           # think: the crossed arm sits in front of the torso

    # ---------------- face ----------------
    K = (16, 14, 22, 255); WH = (255, 255, 255, 255)
    fx = hx + look * 34; ey = hy + 2; my = hy + 48
    gap = 34
    def eye(cx, kind, h=26):
        if kind == 'dot':   d.ellipse([(cx - 10) * S, (ey - h / 2) * S, (cx + 10) * S, (ey + h / 2) * S], fill=K)
        elif kind == 'wide':
            d.ellipse([(cx - 19) * S, (ey - 22) * S, (cx + 19) * S, (ey + 22) * S], fill=WH, outline=K, width=4 * S)
            d.ellipse([(cx - 7 + look * 6) * S, (ey - 8) * S, (cx + 7 + look * 6) * S, (ey + 8) * S], fill=K)
        elif kind == 'happy': d.arc([(cx - 15) * S, (ey - 8) * S, (cx + 15) * S, (ey + 20) * S], 200, 340, fill=K, width=6 * S)
        elif kind == 'flat':  d.line([(cx - 14) * S, ey * S, (cx + 14) * S, ey * S], fill=K, width=6 * S)
        elif kind == 'squint': d.line([(cx - 14) * S, (ey + 2) * S, (cx + 14) * S, (ey - 2) * S], fill=K, width=7 * S)
    def brow(cx, tilt, y=-30, w=7):
        d.line([(cx - 17) * S, (ey + y - tilt) * S, (cx + 17) * S, (ey + y + tilt) * S], fill=K, width=w * S)
    def teeth(x0, x1, yc, h, skew=0.0):     # gritted teeth, lens-shaped and a bit lopsided
        top = [(x0, yc), (x0 + (x1 - x0) * 0.3, yc - h * (0.55 + skew)), (x0 + (x1 - x0) * 0.7, yc - h * 0.6), (x1, yc - h * 0.15)]
        bot = [(x1, yc + h * 0.1), (x0 + (x1 - x0) * 0.65, yc + h * 0.55), (x0 + (x1 - x0) * 0.3, yc + h * (0.5 - skew)), (x0, yc)]
        poly = [(x * S, y * S) for x, y in top + bot]
        d.polygon(poly, fill=WH); d.line(poly + [poly[0]], fill=K, width=4 * S, joint='curve')
        d.line([(x0 + 4) * S, yc * S, (x1 - 4) * S, (yc - h * 0.02) * S], fill=K, width=3 * S)
        for t in (0.33, 0.62): d.line([(x0 + (x1 - x0) * t) * S, (yc - h * 0.45) * S, (x0 + (x1 - x0) * t) * S, (yc + h * 0.4) * S], fill=K, width=3 * S)

    eL, eR = fx - gap, fx + gap
    if expr == 'neutral':
        eye(eL, 'dot'); eye(eR, 'dot')
        d.line([(fx - 16) * S, my * S, (fx + 16) * S, my * S], fill=K, width=5 * S)
    elif expr == 'happy':
        eye(eL, 'happy'); eye(eR, 'happy')
        d.chord([(fx - 30) * S, (my - 22) * S, (fx + 30) * S, (my + 26) * S], 0, 180, fill=K)
        d.chord([(fx - 18) * S, (my + 6) * S, (fx + 18) * S, (my + 24) * S], 0, 180, fill=(225, 95, 105, 255))
    elif expr == 'angry':
        eye(eL, 'dot', 22); eye(eR, 'dot', 22); brow(eL, 8, -26, 8); brow(eR, -8, -26, 8)
        teeth(fx - 34, fx + 36, my, 26, 0.1)
    elif expr == 'surprised':
        eye(eL, 'wide'); eye(eR, 'wide'); brow(eL, -3, -38, 5); brow(eR, 3, -38, 5)
        d.ellipse([(fx - 12) * S, (my - 10) * S, (fx + 12) * S, (my + 22) * S], fill=K)
    elif expr == 'worried':
        eye(eL, 'dot'); eye(eR, 'dot'); brow(eL, -7, -28); brow(eR, 7, -28)
        d.arc([(fx - 20) * S, (my - 2) * S, (fx + 20) * S, (my + 24) * S], 200, 340, fill=K, width=5 * S)
        d.ellipse([(hx + R - 38) * S, (hy - 62) * S, (hx + R - 22) * S, (hy - 38) * S], fill=(160, 215, 255, 255))
    elif expr == 'smug':
        eye(eL, 'flat'); eye(eR, 'flat'); brow(eL, 0, -22, 5); brow(eR, -6, -28, 5)
        d.arc([(fx - 14) * S, (my - 18) * S, (fx + 26) * S, (my + 6) * S], 20, 120, fill=K, width=5 * S)
    elif expr == 'scared':
        eye(eL, 'wide'); eye(eR, 'wide'); brow(eL, -8, -40, 5); brow(eR, 8, -40, 5)
        teeth(fx - 30, fx + 30, my + 4, 22, -0.05)
    elif expr == 'sad':
        eye(eL, 'dot', 20); eye(eR, 'dot', 20); brow(eL, -6, -24, 5); brow(eR, 6, -24, 5)
        d.arc([(fx - 18) * S, (my + 2) * S, (fx + 18) * S, (my + 26) * S], 200, 340, fill=K, width=5 * S)
        d.ellipse([(eL - 5) * S, (ey + 18) * S, (eL + 5) * S, (ey + 34) * S], fill=(140, 200, 255, 255))
    elif expr == 'thinking':               # eyes glance up-right, one brow raised, small skewed mouth
        for cx in (eL, eR): d.ellipse([(cx + 2) * S, (ey - 20) * S, (cx + 20) * S, (ey + 4) * S], fill=K)
        brow(eL, 0, -32, 6); brow(eR, -6, -40, 6)
        d.line([(fx - 4) * S, (my + 4) * S, (fx + 20) * S, (my - 2) * S], fill=K, width=5 * S)
    elif expr == 'determined':
        eye(eL, 'squint'); eye(eR, 'squint'); brow(eL, 6, -20, 8); brow(eR, -6, -20, 8)
        d.line([(fx - 18) * S, (my + 2) * S, (fx + 18) * S, (my - 2) * S], fill=K, width=6 * S)

    # ---------------- hats ----------------
    if hat == 'helmet':
        G = (78, 112, 64); Gd = (52, 78, 44); band = (70, 52, 56)
        top = hy - R - 30; rim = hy - 34
        d.chord([(hx - R - 12 - OUT) * S, (top - OUT) * S, (hx + R + 12 + OUT) * S, (rim + (rim - top) + OUT) * S], 180, 360, fill=INK)
        d.chord([(hx - R - 12) * S, top * S, (hx + R + 12) * S, (rim + (rim - top)) * S], 180, 360, fill=G)
        d.rounded_rectangle([(hx - R - 26) * S, (rim - 6) * S, (hx + R + 26) * S, (rim + 12) * S], radius=9 * S, fill=Gd, outline=INK, width=int(OUT * S))
        d.line([(hx - R - 4) * S, (rim - 22) * S, (hx + R + 4) * S, (rim - 22) * S], fill=band, width=10 * S)
    elif hat == 'sailor':
        d.rounded_rectangle([(hx - 74) * S, (hy - R - 22) * S, (hx + 74) * S, (hy - R + 26) * S], radius=18 * S, fill=(244, 244, 240, 255), outline=INK, width=int(OUT * S))
        d.rectangle([(hx - 76) * S, (hy - R + 12) * S, (hx + 76) * S, (hy - R + 28) * S], fill=(38, 52, 104, 255))

    if pose == 'think':                    # hand to chin drawn over the face
        front_arm(lpts(arms[1]))
    return im.resize((W, H), Image.LANCZOS)

if __name__ == '__main__':
    a = sys.argv
    draw(a[2] if len(a) > 2 else 'neutral', a[3] if len(a) > 3 else 'stand',
         a[4] if len(a) > 4 else '#4a86e0', a[5] if len(a) > 5 and a[5] != 'none' else None,
         float(a[6]) if len(a) > 6 else 0.0).save(a[1])

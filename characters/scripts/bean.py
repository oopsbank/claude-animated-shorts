# Bean-head cartoon characters (the channel's main cast style), built from the measured spec in
# references/reports/characters.md (§2). Our own characters: the STYLE is shared, no reference character is copied.
# Canvas 600x1000 design units, soles at y=975.
import math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 4
W, H = 600, 1000
INK = (36, 23, 38)                                      # #241726 plum ink
SH_SKIN, SH_WHITE, SH_CLOTH = (0.96, 0.86, 0.84), (0.92, 0.90, 0.96), (0.64, 0.66, 0.74)
MOUTH, TONGUE, SWEAT = (90, 30, 40), (232, 110, 120), (159, 212, 255)

def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mul(c, k): return tuple(max(0, min(255, int(c[i] * k[i]))) for i in range(3))
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

BUILDS = {   # head a/b, chin->torso bottom (HH), legs (HH), torso width (W)
    'adult': dict(a=118, b=111, torso=1.10, legs=1.40, tw=0.80),
    'stout': dict(a=118, b=111, torso=1.15, legs=1.32, tw=0.94),
    'kid':   dict(a=112, b=108, torso=0.85, legs=1.00, tw=0.72),
}

def blob(cx, cy, a, b, nTop=1.75, nBot=2.3, egg=-0.12, asym=0.0, rot=0.0, seed=0, noise=0.008, n=180):
    """Superellipse with separate crown/jaw exponents, egg taper, side bulge, tilt and a tiny hand-drawn wobble."""
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    pts = []
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        nn = nTop if s < 0 else nBot                     # canvas y down: s<0 is the top half
        X = math.copysign(abs(c) ** (2 / nn), c); Y = math.copysign(abs(s) ** (2 / nn), s)
        X *= (1 + egg * Y) * (1 + asym * (1 if X > 0 else -1) * 0.5)
        r = 1 + noise * sum(math.sin(k * t + ph[k - 2]) for k in (2, 3, 4)) / 3
        x, y = a * X * r, b * Y * r
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return pts

class Canvas:
    def __init__(self, w=None):
        self.im = Image.new('RGBA', ((w or W) * S, H * S), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def P(self, pts): return [(x * S, y * S) for x, y in pts]
    def mask(self, pts):
        m = Image.new('L', self.im.size, 0); ImageDraw.Draw(m).polygon(self.P(pts), fill=255); return m
    def fill_shaded(self, pts, col, shadow_k, shift, blur, cx, cy, light=(-0.7, -0.7), rim=None):
        """Flat colour + soft crescent shadow on the side away from the light (spec §2.8)."""
        m = self.mask(pts)
        sh = mul(col, shadow_k)
        lit = self.mask([(x + light[0] * shift, y + light[1] * shift) for x, y in pts]).filter(ImageFilter.GaussianBlur(blur * S))
        lit = ImageChops.multiply(lit, m)
        layer = Image.new('RGBA', self.im.size, sh + (255,)); layer.putalpha(m)
        self.im.alpha_composite(layer)
        top = Image.new('RGBA', self.im.size, col + (255,)); top.putalpha(lit)
        self.im.alpha_composite(top)
        if rim:   # thin light sliver just inside the shadow-side edge
            inner = self.mask([(x - light[0] * 3, y - light[1] * 3) for x, y in pts])
            sl = ImageChops.subtract(m, inner).filter(ImageFilter.GaussianBlur(1.2 * S))
            r = Image.new('RGBA', self.im.size, mix(col, (255, 255, 255), 0.45) + (255,)); r.putalpha(sl.point(lambda v: int(v * 0.55)))
            self.im.alpha_composite(r)
        self.d = ImageDraw.Draw(self.im)
    def outline(self, pts, cx, cy, w0, thick_deg=64):
        """Variable-width plum ink: ~3x thicker on the bottom/shadow side (spec §1.2 / §2.3)."""
        tt = math.radians(thick_deg)
        for i, (x, y) in enumerate(pts):
            th = math.atan2(y - cy, x - cx)
            w = w0 * (1 + 0.45 * math.cos(th - tt))
            x2, y2 = pts[(i + 1) % len(pts)]
            self.d.line([(x * S, y * S), (x2 * S, y2 * S)], fill=INK, width=max(1, int(w * S)))
            r = w * S / 2; self.d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=INK)
    def stroke(self, pts, w, col):
        self.d.line(self.P(pts), fill=col, width=int(w * S), joint='curve')
        for x, y in (pts[0], pts[-1]):
            r = w * S / 2; self.d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=col)
    def dot(self, x, y, r, col=INK): self.d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=col)
    def clip_layer(self, draw_fn, clip_pts):
        lay = Image.new('RGBA', self.im.size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(lay))
        a = ImageChops.multiply(lay.getchannel('A'), self.mask(clip_pts)); lay.putalpha(a)
        self.im.alpha_composite(lay); self.d = ImageDraw.Draw(self.im)

def bow(p0, p1, amt, n=16):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / L * amt, my + dx / L * amt
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t * t * p1[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * p1[1])
            for t in (i / n for i in range(n + 1))]

def character(build='adult', skin='#ffe2c2', shirt='#f08a2c', pants='#3b5b9a', expr='neutral', facing=0.0,
              hat=None, hat_col='#e2453c', hair=None, hair_col='#5a3b2a', outfit=(), glasses=False,
              arm_pose='hang', prop=None, seed=1, white_head=False, moustache=None, lean=0.0,
              view='front', pose=None, mouth=None, blink=False, tilt=0.0, ground=True,
              antennae='up', antennae_sway=0.0, seated=None):
    # view: 'front' (default), 'side' or '3q'. In side/3q, facing < 0 faces left, otherwise right.
    # pose (side/3q): joint angles / IK targets, see turned(). mouth: lip-sync shape from MOUTHS. blink: eyes shut.
    # antennae (hat='antennae'): 'up' | 'droop' | 0..1 droop amount; antennae_sway: spring sway in degrees (+ = right).
    # seated: None | 'cooler' (sits on a drawn cooler) | 'bare' (same pose, no seat: the engine supplies the prop).
    #   The seat top is at seat_top(build) on the card (soles stay at y=975).
    if view != 'front':
        return turned(view=view, build=build, skin=skin, shirt=shirt, pants=pants, expr=expr, facing=facing, hat=hat,
                      hat_col=hat_col, hair=hair, hair_col=hair_col, outfit=outfit, glasses=glasses, prop=prop, seed=seed,
                      white_head=white_head, moustache=moustache, pose=pose, mouth=mouth, blink=blink, tilt=tilt,
                      lean=lean, ground=ground, antennae=antennae, antennae_sway=antennae_sway)
    B = BUILDS[build]; a, b = B['a'], B['b']; HH, Wd = 2 * b, 2 * a; u = Wd / 100
    rnd = random.Random(seed)
    total = 1.0 * HH + B['torso'] * HH + B['legs'] * HH
    crown = 975 - total
    if seated: crown += seat_drop(build)
    cx = 300; hy = crown + b; chin = hy + b
    torso_bot = chin + B['torso'] * HH
    C = Canvas()
    skin_c = hexrgb(skin); shirt_c = hexrgb(shirt); pants_c = hexrgb(pants)
    head_sh = SH_WHITE if white_head else SH_SKIN
    # ---- head & torso shapes
    hrot = rnd.uniform(-4, 4) + facing * 3
    head = blob(cx + facing * 4 * u, hy, a, b * (1 + rnd.uniform(-0.03, 0.03)),
                nTop=1.75 + rnd.uniform(-0.12, 0.12), nBot=2.3 + rnd.uniform(-0.12, 0.12), egg=-0.12,
                asym=(0.08 * facing if facing else rnd.choice([-1, 1]) * 0.07), rot=hrot, seed=seed)
    Ta = B['tw'] * Wd / 2
    tb_top = chin - 0.25 * HH
    tcy = (tb_top + torso_bot) / 2; tb = (torso_bot - tb_top) / 2
    torso = blob(cx + lean * 0.5, tcy, Ta, tb, nTop=2.2, nBot=2.6, egg=0.12, asym=0.04 * facing, rot=lean, seed=seed + 7, noise=0.005)
    w0 = 5 * u
    # ---- legs & feet (single ink-tinted strokes, slight bow, A-stance)
    leg_c = mix(pants_c, INK, 0.55)
    hip_y = torso_bot - 0.12 * HH
    if seated:
        if seated == 'cooler': draw_cooler(C, cx, seat_top(build), 975, Ta * 2.5, u)
        seat_legs(C, cx, hip_y, torso_bot, u, leg_c, facing)
    else:
      for sgn in (-1, 1):
        hip = (cx + sgn * 15 * u, hip_y); ft = (cx + sgn * 22 * u, 975 - 3.5 * u)
        C.stroke(bow(hip, ft, sgn * 2 * u), 5.8 * u, leg_c)
        C.stroke([ft, (ft[0] + sgn * 14 * u + facing * 8 * u, ft[1] + 0.5 * u)], 7.5 * u, INK)
    # ---- arms (thin strokes from just inside the torso sides, dot hands)
    arm_c = mix(shirt_c, INK, 0.5)
    sh_y = chin + 0.12 * HH
    def arm(sgn, pose):
        s0 = (cx + sgn * 0.85 * Ta, sh_y)
        if pose == 'hang':
            el = (cx + sgn * (1.12 * Ta + 4 * u), sh_y + 0.48 * HH); hd = (el[0] + sgn * 3 * u, chin + 1.04 * HH)
        elif pose == 'wave':
            el = (cx + sgn * (1.25 * Ta + 10 * u), sh_y + 0.05 * HH); hd = (el[0] + sgn * 6 * u, sh_y - 0.42 * HH)
        elif pose == 'point':
            el = (cx + sgn * (1.25 * Ta + 22 * u), sh_y + 0.10 * HH); hd = (el[0] + sgn * 30 * u, sh_y + 0.02 * HH)
        elif pose == 'hold':     # forearm forward, hand in front of the belly
            el = (cx + sgn * (1.1 * Ta + 4 * u), sh_y + 0.42 * HH); hd = (cx + sgn * 0.45 * Ta, sh_y + 0.62 * HH)
        elif pose == 'hip':      # hand on hip
            el = (cx + sgn * (1.45 * Ta + 10 * u), sh_y + 0.28 * HH); hd = (cx + sgn * 0.95 * Ta, sh_y + 0.55 * HH)
        elif pose == 'palm':     # hand out at shoulder height, palm up (balancing a broom beside the head)
            el = (cx + sgn * (1.3 * Ta + 12 * u), sh_y + 0.22 * HH); hd = (el[0] + sgn * 16 * u, sh_y - 0.02 * HH)
        elif pose == 'chin':     # hand to chin
            el = (cx + sgn * (0.9 * Ta), sh_y + 0.55 * HH); hd = (cx + sgn * 0.12 * Ta + facing * 6 * u, chin - 2 * u)
        return [s0, el, hd]
    poses = tuple(arm_pose) if isinstance(arm_pose, (tuple, list)) else (arm_pose, arm_pose)
    both_hold = poses[0] == 'hold' and poses[1] == 'hold'
    front = []; late_prop = []
    for sgn, ps in zip((-1, 1), poses):
        pts = arm(sgn, ps)
        if ps in ('hold', 'chin'): front.append((pts, ps)); continue      # hands in front of the body: draw after the torso
        C.stroke(bow(pts[0], pts[1], -sgn * 1.5 * u, 8) + bow(pts[1], pts[2], -sgn * 1.0 * u, 8)[1:], 5.2 * u, arm_c)
        C.dot(*pts[2], 5.5 * u)
        if prop and ps in ('wave', 'point', 'hang', 'palm') and (sgn == 1 or ps == 'palm') and 'hold' not in poses: late_prop.append(pts[2])   # one prop, one hand; drawn after the head
    # ---- torso: shaded fill -> clothing (clipped) -> ink
    C.fill_shaded(torso, shirt_c, SH_CLOTH, 0.55 * Ta, 0.18 * Ta, cx, tcy, rim=True)
    def clothes(dd):
        def P(x, y): return (x * S, y * S)
        DEF = dict(buttons=(3, '#f1efe6'), tie=('#c0353a',), belt=('#3b2a22',), apron=('#f1efe6',), overalls=('#2f5aa8',),
                   coat_open=('#f4f4f0',), stripes=('#f1efe6',), collar=('#f1efe6',))
        for item in outfit:
            if isinstance(item, str): item = (item,)           # a bare name ('collar',) gets the default colour
            if len(item) == 1 and item[0] in DEF: item = (item[0],) + DEF[item[0]]
            kind = item[0]
            if kind == 'buttons':
                for k in range(item[1]):
                    y = chin + 0.18 * HH + k * 0.2 * HH; r = 2.4 * u
                    dd.ellipse((P(cx + facing * 3 * u - r, y - r)) + P(cx + facing * 3 * u + r, y + r), fill=hexrgb(item[2]))
            elif kind == 'tie':
                col = hexrgb(item[1]); x0 = cx + facing * 3 * u
                dd.polygon([P(x0 - 4 * u, chin - 2 * u), P(x0 + 4 * u, chin - 2 * u), P(x0 + 6 * u, chin + 0.55 * HH), P(x0, chin + 0.66 * HH), P(x0 - 6 * u, chin + 0.55 * HH)], fill=col)
            elif kind == 'belt':
                y = torso_bot - 0.28 * HH; dd.rectangle(P(cx - 200, y) + P(cx + 200, y + 7 * u), fill=hexrgb(item[1]))
                dd.rectangle(P(cx + facing * 3 * u - 5 * u, y - 1 * u) + P(cx + facing * 3 * u + 5 * u, y + 8 * u), outline=hexrgb('#e8c45a'), width=int(1.8 * u * S))
            elif kind == 'apron':
                col = hexrgb(item[1]); dd.rounded_rectangle(P(cx - 0.62 * Ta, chin + 0.22 * HH) + P(cx + 0.62 * Ta, torso_bot + 10), radius=int(10 * u * S), fill=col)
            elif kind == 'overalls':
                col = hexrgb(item[1])
                dd.rectangle(P(cx - 200, torso_bot - 0.45 * HH) + P(cx + 200, torso_bot + 10), fill=col)
                for sg in (-1, 1): dd.line([P(cx + sg * 0.55 * Ta, chin - 5), P(cx + sg * 0.42 * Ta, torso_bot - 0.45 * HH)], fill=col, width=int(7 * u * S))
                for sg in (-1, 1): dd.ellipse(P(cx + sg * 0.42 * Ta - 2.5 * u, torso_bot - 0.45 * HH - 2.5 * u) + P(cx + sg * 0.42 * Ta + 2.5 * u, torso_bot - 0.45 * HH + 2.5 * u), fill=hexrgb('#e8c45a'))
            elif kind == 'coat_open':       # open lab coat over the shirt: two side panels
                col = hexrgb(item[1])
                for sg in (-1, 1): dd.polygon([P(cx + sg * 0.18 * Ta, chin - 10), P(cx + sg * 300, chin - 10), P(cx + sg * 300, torso_bot + 20), P(cx + sg * 0.30 * Ta, torso_bot + 20)], fill=col)
                for sg in (-1, 1): dd.line([P(cx + sg * 0.18 * Ta, chin - 10), P(cx + sg * 0.30 * Ta, torso_bot + 20)], fill=INK, width=int(1.6 * u * S))
            elif kind == 'stripes':
                col = hexrgb(item[1])
                for k in range(4): y = chin + 0.25 * HH + k * 0.22 * HH; dd.rectangle(P(cx - 200, y) + P(cx + 200, y + 7 * u), fill=col)
            elif kind == 'collar':
                col = hexrgb(item[1])
                for sg in (-1, 1): dd.polygon([P(cx, chin + 6 * u), P(cx + sg * 0.5 * Ta, chin - 4 * u), P(cx + sg * 0.35 * Ta, chin + 12 * u)], fill=col)
    C.clip_layer(clothes, torso)
    C.outline(torso, cx, tcy, w0)
    # ---- head
    head_col = hexrgb('#fbf8f4') if white_head else skin_c
    C.fill_shaded(head, head_col, head_sh, 0.30 * a, 0.09 * a, cx, hy)
    if hair:   # hair cap on the skull, clipped to the head, drawn under the outline
        hc = hexrgb(hair_col)
        def hair_fn(dd):
            if hair == 'short':
                dd.ellipse(((cx - a * 1.05) * S, (hy - b * 1.25) * S, (cx + a * 1.05) * S, (hy - b * 0.15) * S), fill=hc)
            elif hair == 'side':
                dd.ellipse(((cx - a * 1.1 - facing * 20) * S, (hy - b * 1.3) * S, (cx + a * 0.9 - facing * 20) * S, (hy - b * 0.25) * S), fill=hc)
                dd.ellipse(((cx - a * 1.1) * S, (hy - b * 0.6) * S, (cx - a * 0.72) * S, (hy + b * 0.15) * S), fill=hc)
            elif hair == 'bun':
                dd.ellipse(((cx - a * 1.05) * S, (hy - b * 1.2) * S, (cx + a * 1.05) * S, (hy - b * 0.35) * S), fill=hc)
        C.clip_layer(hair_fn, head)
        if hair == 'bun':
            bun = blob(cx - facing * 10, hy - b * 1.12, 0.32 * a, 0.28 * b, seed=seed + 3, egg=0)
            C.fill_shaded(bun, hc, SH_CLOTH, 6, 4, cx, hy - b * 1.1); C.outline(bun, cx, hy - b * 1.1, 0.8 * w0)
    C.outline(head, cx + facing * 4 * u, hy, w0)
    # ---- hat (sits low; base edge follows the skull)
    if hat: draw_hat(C, hat, hexrgb(hat_col), cx + facing * 4 * u, hy, a, b, u, w0, facing, hrot, antennae=antennae, sway=antennae_sway)
    # ---- face
    draw_face(C, expr, cx + facing * 4 * u, hy, u, facing, glasses, moustache, hat is not None, mouth, blink)
    for hp_ in late_prop: draw_prop(C, prop, hp_, u, side=1)      # a raised prop (a broom) must sit over the head and hat
    # ---- arms in front of the body
    for pts, ps in front:
        sgn = 1 if pts[0][0] > cx else -1
        C.stroke(bow(pts[0], pts[1], -sgn * 1.5 * u, 8) + bow(pts[1], pts[2], sgn * 1.0 * u, 8)[1:], 5.2 * u, arm_c)
        C.dot(*pts[2], 5.5 * u)
        if prop and ps == 'hold' and not both_hold: draw_prop(C, prop, pts[2], u, side=sgn)
    if prop and both_hold:          # one prop, two hands (DRAWING rule 23): drawn once between the hands
        hands = sorted((p[0][2] for p in front), key=lambda q: q[0])
        draw_prop(C, prop, hands[0], u, side=0, two=tuple(hands))
    return C.im.resize((W, H), Image.LANCZOS)

def draw_hat(C, kind, col, cx, hy, a, b, u, w0, facing, rot, rear=False, sticker=None, antennae='up', sway=0.0):
    if kind == 'helmet': return draw_helmet(C, col, cx, hy, a, b, u, w0, facing, rear, sticker)
    if kind == 'antennae': return draw_antennae(C, col, cx, hy, a, b, u, w0, facing, rot, rear, antennae, sway)
    base_y = hy - b + 0.52 * b                # covers the top ~25% of the head; brows sit just under the base
    sag = 0.05 * 2 * a
    dk = mul(col, (0.75, 0.75, 0.8))
    if kind in ('cap', 'beanie', 'hardhat'):
        dome = blob(cx, base_y - 0.02 * b, a * (1.02 if kind != 'hardhat' else 1.06), b * (0.62 if kind != 'beanie' else 0.7),
                    nTop=2.2, nBot=2.0, egg=0, rot=rot * 0.6, seed=11, noise=0.004)
        dome = [p for p in dome if p[1] <= base_y + sag * (1 - ((p[0] - cx) / a) ** 2)]
        dome = dome + [(cx + a * 1.02, base_y), (cx, base_y + sag), (cx - a * 1.02, base_y)]
        C.fill_shaded(dome, col, (0.8, 0.8, 0.85), 0.2 * a, 0.08 * a, cx, base_y - 0.3 * b)
        if kind == 'beanie':
            C.d.rectangle(((cx - a * 1.02) * S, (base_y - 9 * u) * S, (cx + a * 1.02) * S, (base_y + 2 * u) * S), fill=dk)
        C.outline(dome, cx, base_y - 0.3 * b, 0.85 * w0)
        if kind == 'cap' and not rear:     # brim sticks out on the facing side (hidden behind the head from the rear)
            sgn = 1 if facing >= 0 else -1
            brim = blob(cx + sgn * a * 0.85, base_y - 1 * u, a * 0.62, 5 * u, nTop=2, nBot=2, egg=0, seed=12, noise=0)
            C.fill_shaded(brim, dk, (0.8, 0.8, 0.85), 3, 2, cx, base_y); C.outline(brim, cx + sgn * a * 0.75, base_y, 0.85 * w0)
        if kind == 'hardhat':
            turn = facing if abs(facing) >= 1 else 0.0          # side / 3q: brim juts forward, ridge moves to the front
            rim = blob(cx + turn * 0.16 * a, base_y - 1 * u, a * 1.22, 4.5 * u, nTop=2, nBot=2, egg=0, seed=13, noise=0)
            C.fill_shaded(rim, col, (0.8, 0.8, 0.85), 3, 2, cx, base_y); C.outline(rim, cx, base_y, 0.85 * w0)
            rx = cx - 3 * u + turn * 0.3 * a
            C.d.line([(rx * S, (base_y - 0.55 * b) * S), (rx * S, (base_y - 2 * u) * S)], fill=dk, width=int(5 * u * S))
    elif kind == 'tophat':
        crown_pts = [(cx - 0.62 * a, base_y - 1.25 * b), (cx + 0.62 * a, base_y - 1.25 * b), (cx + 0.58 * a, base_y), (cx - 0.58 * a, base_y)]
        crown_pts = [p for i, p in enumerate(crown_pts)]
        C.fill_shaded(crown_pts, col, (0.75, 0.75, 0.8), 0.15 * a, 0.05 * a, cx, base_y - 0.6 * b)
        C.d.rectangle(((cx - 0.585 * a) * S, (base_y - 0.32 * b) * S, (cx + 0.585 * a) * S, (base_y - 0.18 * b) * S), fill=hexrgb('#c0353a'))
        C.outline(crown_pts, cx, base_y - 0.6 * b, 0.85 * w0)
        brim = blob(cx, base_y, a * 0.95, 6 * u, nTop=2, nBot=2, egg=0, seed=14, noise=0)
        C.fill_shaded(brim, col, (0.75, 0.75, 0.8), 3, 2, cx, base_y); C.outline(brim, cx, base_y, 0.85 * w0)

def draw_face(C, expr, cx, cy, u, facing, glasses, moustache, has_hat, mouth=None, blink=False):
    M = mouth is None                     # the expression's own mouth, unless a lip-sync mouth replaces it
    d = C.d; K = INK
    ex = cx + 7 * u * facing; eL, eR = ex - 13 * u, ex + 13 * u
    by = cy - (15 if has_hat else 20) * u
    mx, my = cx + 8 * u * facing, cy + 20 * u
    def L(pts, w): d.line([(x * S, y * S) for x, y in pts], fill=K, width=max(1, int(w * S)), joint='curve')
    def closed(x): d.arc(((x - 8 * u) * S, (cy - 6 * u) * S, (x + 8 * u) * S, (cy + 3 * u) * S), 20, 160, fill=K, width=int(3.8 * u * S))
    def lidded(x):
        if blink: return closed(x)
        L([(x - 9 * u, cy - 1 * u), (x + 9 * u, cy - 1 * u)], 3.8 * u)
        d.chord(((x - 7 * u) * S, (cy - 6 * u) * S, (x + 7 * u) * S, (cy + 6 * u) * S), 0, 180, fill=K)
    def dotv(x, rx=3.8, ry=5.5): closed(x) if blink else d.ellipse(((x - rx * u) * S, (cy - ry * u) * S, (x + rx * u) * S, (cy + ry * u) * S), fill=K)
    def happy(x): closed(x) if blink else d.arc(((x - 8 * u) * S, (cy - 4 * u) * S, (x + 8 * u) * S, (cy + 8 * u) * S), 200, 340, fill=K, width=int(3.8 * u * S))
    def brow(x, inner, outer, side):     # tapered: thick inner end -> thin outer end; inner/outer offsets in u (+ = down)
        x_in, x_out = x - side * 8 * u, x + side * 9 * u
        y_in, y_out = by + inner * u, by + outer * u
        for k in range(12):
            t = k / 11; w = (5 - 2.5 * t) * u
            px, py = x_in + (x_out - x_in) * t, y_in + (y_out - y_in) * t
            d.ellipse(((px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S), fill=K)
    if expr == 'neutral':
        lidded(eL); lidded(eR); brow(eL, 0, -1, -1); brow(eR, 0, -1, 1)
        if M: L([(mx - 5.5 * u, my + 0.4 * u), (mx + 5.5 * u, my - 0.4 * u)], 4 * u)
    elif expr == 'stern':
        lidded(eL); lidded(eR); brow(eL, 3, -2, -1); brow(eR, 3, -2, 1)
        if M: d.arc(((mx - 7 * u) * S, my * S, (mx + 7 * u) * S, (my + 7 * u) * S), 200, 340, fill=K, width=int(4 * u * S))
    elif expr == 'grin':
        happy(eL); happy(eR); brow(eL, -3, -3, -1); brow(eR, -3, -3, 1)
        if M: d.chord(((mx - 12 * u) * S, (my - 8 * u) * S, (mx + 12 * u) * S, (my + 8 * u) * S), 0, 180, fill=MOUTH)
        if M: d.rectangle(((mx - 11 * u) * S, my * S, (mx + 11 * u) * S, (my + 2.6 * u) * S), fill=(255, 255, 255))
        if M: d.arc(((mx - 12 * u) * S, (my - 8 * u) * S, (mx + 12 * u) * S, (my + 8 * u) * S), 0, 180, fill=K, width=int(2.5 * u * S))
        if M: L([(mx - 12 * u, my), (mx + 12 * u, my)], 2.5 * u)
    elif expr == 'shock':
        if blink: closed(ex - 11.5 * u); closed(ex + 11.5 * u)
        for x in (() if blink else (ex - 11.5 * u, ex + 11.5 * u)):
            d.ellipse(((x - 11 * u) * S, (cy - 11 * u) * S, (x + 11 * u) * S, (cy + 11 * u) * S), fill=(255, 255, 255), outline=K, width=int(2.6 * u * S))
            d.ellipse(((x - 3 * u + facing * 3 * u) * S, (cy - 3 * u) * S, (x + 3 * u + facing * 3 * u) * S, (cy + 3 * u) * S), fill=K)
        brow(eL, -7, -8, -1); brow(eR, -7, -8, 1)
        if M: d.ellipse(((mx - 9 * u) * S, (my - 5 * u) * S, (mx + 9 * u) * S, (my + 17 * u) * S), fill=MOUTH, outline=K, width=int(2.5 * u * S))
    elif expr == 'nervous':
        dotv(eL, 3, 4.5); dotv(eR, 3, 4.5); brow(eL, -3, 2, -1); brow(eR, -3, 2, 1)
        if M: pts = [(mx - 9 * u + k * 1.8 * u, my + math.sin(k * 1.3) * 1.5 * u) for k in range(11)]; L(pts, 3.5 * u)
        C.d.ellipse(((cx + 34 * u) * S, (cy - 30 * u) * S, (cx + 41 * u) * S, (cy - 19 * u) * S), fill=SWEAT, outline=K, width=int(1.5 * u * S))
    elif expr == 'smile':
        dotv(eL); dotv(eR); brow(eL, 0, -1, -1); brow(eR, 0, -1, 1)
        if M: d.arc(((mx - 7 * u) * S, (my - 5 * u) * S, (mx + 7 * u) * S, (my + 3 * u) * S), 20, 160, fill=K, width=int(4 * u * S))
    elif expr == 'smug':
        lidded(eL); lidded(eR); brow(eL, 0, 0, -1); brow(eR, -4, -6, 1)
        if M: d.arc(((mx - 4 * u) * S, (my - 6 * u) * S, (mx + 10 * u) * S, (my + 2 * u) * S), 20, 120, fill=K, width=int(4 * u * S))
    elif expr == 'pained':
        lidded(eR)
        L([(eL - 7 * u, cy - 4 * u), (eL + 5 * u, cy), (eL - 7 * u, cy + 4 * u)], 3.8 * u)
        brow(eL, -3, 2, -1); brow(eR, -3, 2, 1)
        if M: d.rectangle(((mx - 12 * u) * S, (my - 4 * u) * S, (mx + 12 * u) * S, (my + 4 * u) * S), fill=(255, 255, 255), outline=K, width=int(2.4 * u * S))
        if M:
            for k in (-6, 0, 6): L([(mx + k * u, my - 4 * u), (mx + k * u, my + 4 * u)], 1.6 * u)
        if M: L([(mx - 12 * u, my), (mx + 12 * u, my)], 1.6 * u)
    if mouth: mouth_shape(d, CLOSED_FOR.get(expr, 'dash') if mouth == 'closed' else mouth, mx, my, u, 1.0, 1)
    if glasses:
        for x in (eL, eR):
            d.ellipse(((x - 10 * u) * S, (cy - 9 * u) * S, (x + 10 * u) * S, (cy + 9 * u) * S), outline=K, width=int(2.6 * u * S))
        L([(eL + 10 * u, cy - 1 * u), (eR - 10 * u, cy - 1 * u)], 2.6 * u)
    if moustache:
        col = hexrgb(moustache)
        for sg in (-1, 1):
            for k in range(10):
                t = k / 9; w = (4.5 - 3 * t) * u
                px, py = mx + sg * (1 + 9 * t) * u, my - 7 * u + 2.5 * u * t * t
                d.ellipse(((px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S), fill=col)

def draw_prop(C, kind, hand, u, side=1, two=None):
    """Held props, gripped by the dot hand. Parameterised names:
       'broom_upright' / 'broom_tip_left' / 'broom_tip_right' / 'broom:<deg>' - a broom balanced handle-down on the palm
           (+ deg tips it to screen right);  'clipboard:<text>' - a clipboard whose sheet carries readable text;
       'helmet' or 'helmet:<sticker text>' - an open-face helmet held by its edge, sticker large enough to read."""
    import held
    if kind.split(':', 1)[0] in held.NAMES: return held.draw(C, kind, hand, u, side, two)
    if two: hand = ((two[0][0] + two[1][0]) / 2, (two[0][1] + two[1][1]) / 2)
    x, y = hand
    if kind.startswith('broom'):
        tilt = {'broom_upright': 0, 'broom_tip_left': -18, 'broom_tip_right': 18}.get(kind)
        if tilt is None: tilt = float(kind.split(':', 1)[1]) if ':' in kind else 0.0
        return _broom(C, x, y, u, tilt)
    if kind.startswith('helmet'):
        return _held_helmet(C, x, y, u, kind.split(':', 1)[1] if ':' in kind else None)
    if kind.startswith('clipboard:'):
        uu = u * 4.4; txt = kind.split(':', 1)[1]; x = x + 5 * uu   # the hand grips the board's left edge
        y = y + 6 * uu
        C.d.rectangle(((x - 6 * uu) * S, (y - 22 * uu) * S, (x + 14 * uu) * S, (y + 4 * uu) * S), fill=(176, 122, 70), outline=INK, width=int(0.9 * uu * S))
        C.d.rectangle(((x - 3.5 * uu) * S, (y - 19 * uu) * S, (x + 11.5 * uu) * S, (y + 1.5 * uu) * S), fill=(250, 248, 240))
        C.d.rectangle(((x + 0.5 * uu) * S, (y - 23.5 * uu) * S, (x + 7.5 * uu) * S, (y - 20 * uu) * S), fill=(200, 204, 212), outline=INK, width=int(0.6 * uu * S))
        _text_block(C, x + 4 * uu, y - 9 * uu, 13.5 * uu, 17 * uu, txt)
        C.dot(x - 5 * uu, y - 6 * uu, 5.5 * u); return
    u = u * 1.7            # props read big and clear, like the reference
    if kind == 'mug':
        C.d.rounded_rectangle(((x - 2 * u) * S, (y - 9 * u) * S, (x + 12 * u) * S, (y + 6 * u) * S), radius=int(2 * u * S), fill=(240, 240, 235), outline=INK, width=int(2.4 * u * S))
        C.d.arc(((x + 9 * u) * S, (y - 6 * u) * S, (x + 17 * u) * S, (y + 2 * u) * S), 270, 90, fill=INK, width=int(2.4 * u * S))
        C.dot(x, y, 5.5 * u / 1.7)
    elif kind == 'clipboard':
        C.d.rectangle(((x - 6 * u) * S, (y - 22 * u) * S, (x + 14 * u) * S, (y + 4 * u) * S), fill=(176, 122, 70), outline=INK, width=int(2.4 * u * S))
        C.d.rectangle(((x - 3 * u) * S, (y - 19 * u) * S, (x + 11 * u) * S, (y + 1 * u) * S), fill=(250, 248, 240))
        for k in range(3): C.d.line(((x - 1 * u) * S, (y - (15 - 5 * k) * u) * S, (x + 9 * u) * S, (y - (15 - 5 * k) * u) * S), fill=INK, width=int(1.2 * u * S))
        C.dot(x, y, 5.5 * u / 1.7)
    elif kind == 'wrench':
        C.d.line(((x) * S, (y) * S, (x + 4 * u) * S, (y - 28 * u) * S), fill=(150, 156, 166), width=int(5 * u * S))
        C.d.ellipse(((x - 1 * u) * S, (y - 36 * u) * S, (x + 11 * u) * S, (y - 24 * u) * S), fill=(150, 156, 166), outline=INK, width=int(2 * u * S))
        C.dot(x, y, 5.5 * u / 1.7)

# ============================ video 2 additions: seated pose, cooler, antennae hat ============================
def seat_top(build='adult'):
    """Card y of the seat top for seated= (the lid of the cooler); soles stay at y=975."""
    B = BUILDS[build]; HH = 2 * B['b']
    return 975 - 0.55 * B['legs'] * HH

def seat_drop(build='adult'):
    B = BUILDS[build]; HH = 2 * B['b']
    return (seat_top(build) + 0.07 * HH) - (975 - B['legs'] * HH)

def seat_legs(C, cx, hip_y, torso_bot, u, leg_c, facing=0.0):
    """Front-view sitting: thighs point at the camera (foreshortened under the torso), knees out, shins straight down."""
    for sgn in (-1, 1):
        hip = (cx + sgn * 15 * u, hip_y); kn = (cx + sgn * 30 * u, torso_bot + 2 * u); ft = (cx + sgn * 30 * u, 975 - 3.5 * u)
        C.stroke(bow(hip, kn, sgn * 1 * u, 8) + bow(kn, ft, -sgn * 1.5 * u, 12)[1:], 5.8 * u, leg_c)
        C.dot(kn[0], kn[1], 3.6 * u, leg_c)
        C.stroke([ft, (ft[0] + sgn * 12 * u + facing * 8 * u, ft[1] + 0.5 * u)], 7.5 * u, INK)

COOLER = dict(body='#d9453a', lid='#f4f1ea', trim='#9e2b24')

def draw_cooler(C, cx, top, bot, w, u, body=None, lid=None, label=None):
    """A picnic cooler box seen from the front: white lid, coloured tub, side handle, drain plug."""
    from ink import stamp, rpoly, text
    bc, lc, tc = hexrgb(body or COOLER['body']), hexrgb(lid or COOLER['lid']), hexrgb(COOLER['trim'])
    h = bot - top; e = 4.2 * u
    stamp(C, [('p', rpoly(cx, top + h * 0.58, w, h * 0.84, 7 * u), bc), ('p', rpoly(cx, top + h * 0.1, w * 1.05, h * 0.2, 6 * u), lc),
              ('p', rpoly(cx + w * 0.54, top + h * 0.42, 9 * u, h * 0.22, 3 * u), lc)], e,
          details=[('p', rpoly(cx, top + h * 0.215, w * 0.97, 3 * u, 1 * u), tc), ('c', cx + w * 0.36, bot - h * 0.16, 3.2 * u, tc)])
    if label: text(C, cx, top + h * 0.56, label, h * 0.2, (255, 255, 255), maxw=w * 0.8)

def antenna_geo(root, a, b, sgn, droop, sway):
    """Stalk centre line (bezier) and tip for one antenna. droop 0 = up and springy, 1 = sagging beside the head."""
    up_tip = (root[0] + sgn * 0.22 * a, root[1] - 0.95 * b); dn_tip = (root[0] + sgn * 0.92 * a, root[1] + 0.55 * b)
    up_c = (root[0] + sgn * 0.02 * a, root[1] - 0.5 * b); dn_c = (root[0] + sgn * 0.55 * a, root[1] - 0.6 * b)
    L = lambda p, q: (p[0] + (q[0] - p[0]) * droop, p[1] + (q[1] - p[1]) * droop)
    tip, ctl = L(up_tip, dn_tip), L(up_c, dn_c)
    tip = rot_pt(tip, root, sway); ctl = rot_pt(ctl, root, sway * 0.5)
    return ctl, tip

def draw_antennae(C, col, cx, hy, a, b, u, w0, facing, rot, rear, antennae='up', sway=0.0):
    """hat='antennae': a headband with two springy antenna stalks topped with balls (the alien-tour guide and his fans).
    antennae='up' | 'droop' | float droop 0..1; sway: degrees (+ = toward screen right) for spring wobble."""
    from ink import stamp
    droop = {'up': 0.0, 'droop': 1.0, None: 0.0}.get(antennae, antennae)
    droop = max(0.0, min(1.0, float(droop)))
    dk = mul(col, (0.62, 0.62, 0.7)); stalk = mix(col, INK, 0.6)
    base_y = hy - 0.48 * b; f = facing if abs(facing) >= 1 else facing * 0.5
    def hw(y):   # half-width of the skull at height y (crown exponent 1.75)
        t = min(1.0, abs((y - hy) / b)); return a * (1 - t ** 1.75) ** (1 / 1.75)
    # headband: a strip that follows the skull, sagging a little at the front
    yt, yb = base_y - 9 * u, base_y + 1 * u
    n = 14; top, botm = [], []
    for i in range(n + 1):
        X = -1 + 2 * i / n; sag = 0.1 * a * (1 - X * X) * (0 if rear else 1)
        top.append((cx + X * hw(yt) * 1.02, yt + sag)); botm.append((cx + X * hw(yb) * 1.03, yb + sag))
    band = top + botm[::-1]
    # stalks + balls (far one first in turned views)
    spread = 0.40 * a * (1 - 0.45 * abs(f)); off = f * 0.12 * a
    order = (-1, 1) if f >= 0 else (1, -1)
    if abs(f) >= 1: order = order   # near stalk = facing side, drawn last
    parts = []
    for sgn in order:
        rx = cx + off + sgn * spread
        root = (rx, yt + 0.1 * a * (1 - (sgn * spread / (hw(yt) or 1)) ** 2) * (0 if rear else 1) + 2 * u)
        ctl, tip = antenna_geo(root, a, b, sgn, droop, sway)
        pts = []
        m = 40
        for k in range(m + 1):
            t = k / m
            x = (1 - t) ** 2 * root[0] + 2 * (1 - t) * t * ctl[0] + t * t * tip[0]
            y = (1 - t) ** 2 * root[1] + 2 * (1 - t) * t * ctl[1] + t * t * tip[1]
            dx = 2 * (1 - t) * (ctl[0] - root[0]) + 2 * t * (tip[0] - ctl[0]); dy = 2 * (1 - t) * (ctl[1] - root[1]) + 2 * t * (tip[1] - ctl[1])
            L = math.hypot(dx, dy) or 1
            amp = 4.2 * u * math.sin(math.pi * min(1, t * 1.25)) * (1 - 0.6 * droop)     # the spring coil, slacker when drooping
            wob = amp * math.sin(t * 2 * math.pi * 4.5)
            pts.append((x - dy / L * wob, y + dx / L * wob, 3.4 * u))
        rb = 0.17 * a
        parts.append((pts, tip, rb))
    for pts, tip, rb in parts:
        stamp(C, [('s', pts, stalk), ('e', tip[0], tip[1], rb, rb * (1 - 0.1 * droop), col)], 0.7 * w0,
              details=[('c', tip[0] - rb * 0.38, tip[1] - rb * 0.4, rb * 0.22, mix(col, (255, 255, 255), 0.55))])
    stamp(C, [('p', band, dk)], 0.8 * w0, shade=False)

if __name__ == '__main__':
    import sys
    character().save(sys.argv[1] if len(sys.argv) > 1 else 'bean.png')

# ============================ side and 3/4 views ============================
# Joint angles are in degrees from straight down; + swings FORWARD (toward the facing direction).
# A limb is (upper, lower) absolute angles. IK targets (canvas units) override angles: handN/handF/footN/footF.
MOUTHS = ('closed', 'small', 'open', 'wide', 'O', 'smile_talk')
VIEWS = ('front', 'side', '3q')
SIDE_STAND = dict(legN=(7, 2), legF=(-6, -3), armN=(4, 18), armF=(-6, 6), lean=0.0, tilt=0.0)   # feet apart: two legs, not one stilt
Q3_STAND = dict(legN=(1, -1), legF=(-2, 0), armN=(3, 14), armF=(-3, 8), lean=0.0, tilt=0.0)
# eyes, brows (inner, outer in u, + = down), mouth for every expression in the turned views
EXPR_TURNED = {
    'neutral': ('lidded', (0, -1), 'dash'), 'stern': ('lidded', (3, -2), 'frown'), 'grin': ('happy', (-3, -3), 'grin'),
    'shock': ('shock', (-7, -8), 'shockO'), 'nervous': ('oval', (-3, 2), 'wave'), 'smile': ('dot', (0, -1), 'smirk'),
    'smug': ('lidded', (0, -4), 'smirk'), 'pained': ('squeeze', (-3, 2), 'teeth')}

def rot_pt(p, c, deg):
    """Rotate p about c by deg, clockwise on screen (y points down)."""
    t = math.radians(deg); dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(t) - dy * math.sin(t), c[1] + dx * math.sin(t) + dy * math.cos(t))

def limb2(root, a1, a2, L1, L2, s):
    j = (root[0] + s * math.sin(math.radians(a1)) * L1, root[1] + math.cos(math.radians(a1)) * L1)
    e = (j[0] + s * math.sin(math.radians(a2)) * L2, j[1] + math.cos(math.radians(a2)) * L2)
    return j, e

def ik2(root, tgt, L1, L2, bend_x):
    """Two-bone IK. bend_x = +1/-1 puts the joint on the +x / -x side of the root->target line.
    An unreachable target is approached along the same line (the limb straightens, never stretches)."""
    dx, dy = tgt[0] - root[0], tgt[1] - root[1]; D = math.hypot(dx, dy) or 1e-6
    d = max(abs(L1 - L2) + 1e-3, min(D, L1 + L2 - 0.5))
    a = math.atan2(dy, dx); t = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    cands = [(root[0] + L1 * math.cos(a + k * t), root[1] + L1 * math.sin(a + k * t)) for k in (1, -1)]
    e = (root[0] + dx / D * d, root[1] + dy / D * d)
    mid = ((root[0] + e[0]) / 2, (root[1] + e[1]) / 2)
    j = max(cands, key=lambda q: (q[0] - mid[0]) * bend_x)
    return j, e

def bend_path(root, j, e, n=24):
    """Smooth bend through the joint (never a polyline corner): quadratic that passes through j."""
    cx, cy = 2 * j[0] - (root[0] + e[0]) / 2, 2 * j[1] - (root[1] + e[1]) / 2
    return [((1 - t) ** 2 * root[0] + 2 * (1 - t) * t * cx + t * t * e[0],
             (1 - t) ** 2 * root[1] + 2 * (1 - t) * t * cy + t * t * e[1]) for t in (i / n for i in range(n + 1))]

def _rot_layer(im, deg, center, translate=(0, 0)):
    if abs(deg) < 1e-6 and translate == (0, 0): return im
    return im.rotate(-deg, resample=Image.BICUBIC, center=(center[0] * S, center[1] * S),
                     translate=(translate[0] * S, translate[1] * S))

# 'closed' follows the expression, so a smiling face does not drop to a neutral dash on every closed-mouth frame
CLOSED_FOR = {'grin': 'smile_closed', 'smile': 'smile_closed', 'smug': 'smirk', 'stern': 'frown', 'pained': 'frown', 'nervous': 'wave'}

def mouth_shape(d, kind, mx, my, u, sx=1.0, s=1, far=1.0):
    """Mouths shared by expressions and lip sync. sx squeezes the width (3/4 and side views); far < 1 shrinks the
    half of the mouth on the far side of a 3/4 face (the +s side)."""
    K = INK
    def X(v): return mx + v * u * sx * (far if v * s > 0 else 1.0)
    def L(pts, w): d.line([(x * S, y * S) for x, y in pts], fill=K, width=max(1, int(w * S)), joint='curve')
    def box(x0, y0, x1, y1): return ((X(x0)) * S, (my + y0 * u) * S, (X(x1)) * S, (my + y1 * u) * S)
    if kind in ('dash', 'closed'):
        L([(X(-5.5), my + 0.4 * u * s), (X(5.5), my - 0.4 * u * s)], 4 * u)
    elif kind == 'frown': d.arc(box(-7, 0, 7, 7), 200, 340, fill=K, width=int(4 * u * S))
    elif kind == 'smirk': d.arc(box(-7, -5, 7, 3), 20, 160, fill=K, width=int(4 * u * S))
    elif kind == 'smile_closed': d.arc(box(-8, -5, 8, 4), 15, 165, fill=K, width=int(4 * u * S))
    elif kind == 'wave': L([(X(-9 + k * 1.8), my + math.sin(k * 1.3) * 1.5 * u) for k in range(11)], 3.5 * u)
    elif kind == 'grin':
        d.chord(box(-12, -8, 12, 8), 0, 180, fill=MOUTH)
        d.rectangle((X(-11) * S, my * S, X(11) * S, (my + 2.6 * u) * S), fill=(255, 255, 255))
        d.arc(box(-12, -8, 12, 8), 0, 180, fill=K, width=int(2.5 * u * S)); L([(X(-12), my), (X(12), my)], 2.5 * u)
    elif kind == 'shockO': d.ellipse(box(-9, -5, 9, 17), fill=MOUTH, outline=K, width=int(2.5 * u * S))
    elif kind == 'teeth':
        d.rectangle(box(-12, -4, 12, 4), fill=(255, 255, 255), outline=K, width=int(2.4 * u * S))
        for k in (-6, 0, 6): L([(X(k), my - 4 * u), (X(k), my + 4 * u)], 1.6 * u)
        L([(X(-12), my), (X(12), my)], 1.6 * u)
    # ---- lip-sync shapes: one anchor, similar sizes, so they swap cleanly frame to frame
    elif kind == 'small':                                   # a short open slit (a dot read as 'closed' at video size)
        d.ellipse(box(-5.5, -3.1, 5.5, 3.9), fill=MOUTH, outline=K, width=int(2.2 * u * S))
        d.chord(box(-3, 0.9, 3, 3.9), 180, 360, fill=TONGUE)
    elif kind == 'open':
        d.ellipse(box(-7, -4, 7, 9), fill=MOUTH, outline=K, width=int(2.5 * u * S))
        d.chord(box(-4.5, 3, 4.5, 9), 180, 360, fill=TONGUE)
    elif kind == 'wide':                                    # capped near 20u wide; it grows in height, not width
        d.rounded_rectangle(box(-10, -6, 10, 9), radius=int(4.5 * u * S), fill=MOUTH, outline=K, width=int(2.5 * u * S))
        d.rectangle((X(-8.2) * S, (my - 4.6 * u) * S, X(8.2) * S, (my - 2.0 * u) * S), fill=(255, 255, 255))
        d.chord(box(-5.5, 3, 5.5, 9.5), 180, 360, fill=TONGUE)
    elif kind == 'O':                                       # taller than 'open', with a lighter inside
        d.ellipse(box(-4.6, -4.5, 4.6, 10), fill=MOUTH, outline=K, width=int(2.6 * u * S))
        d.ellipse(box(-2.2, -0.5, 2.2, 6.5), fill=mix(MOUTH, TONGUE, 0.55))
    elif kind == 'smile_talk':
        d.chord(box(-10, -6, 10, 8), 0, 180, fill=MOUTH)
        d.arc(box(-10, -6, 10, 8), 0, 180, fill=K, width=int(2.5 * u * S)); L([(X(-10), my + u), (X(10), my + u)], 2.5 * u)
        d.chord(box(-5, 3.5, 5, 8), 180, 360, fill=TONGUE)
    else: raise ValueError(f'unknown mouth {kind!r}; lip-sync mouths are {MOUTHS}')

def profile_mouth(d, kind, hx, my, u, s):
    """Side view mouths. Every shape shares one anchor: hinged at the back corner (hx+27u) and reaching the front
    at hx+37u, >= 3u inside the head's ink ring. Front shapes squeezed onto a profile read as pasted on."""
    K = INK; bx, fx = hx + s * 27 * u, hx + s * 37 * u
    def L(pts, w=4): d.line([(x * S, y * S) for x, y in pts], fill=K, width=int(w * u * S), joint='curve')
    def poly(pts, col): q = [(x * S, y * S) for x, y in pts]; d.polygon(q, fill=col); d.line(q + q[:1], fill=K, width=int(2.3 * u * S), joint='curve')
    def curve(y_back, y_front, sag, n=10):
        return [(bx + (fx - bx) * t, y_back + (y_front - y_back) * t + sag * 4 * t * (1 - t)) for t in (i / n for i in range(n + 1))]
    if kind in ('dash', 'closed'): L(curve(my + 0.8 * u, my, 0))
    elif kind == 'frown': L(curve(my + 2.5 * u, my, -1.2 * u))
    elif kind in ('smirk', 'smile_closed'): L(curve(my - 2.6 * u, my + 0.5 * u, 1.4 * u))
    elif kind == 'wave': L([(bx + (fx - bx) * k / 10, my + math.sin(k * 1.3) * 1.5 * u) for k in range(11)], 3.5)
    elif kind == 'small': poly([(bx + s * 1 * u, my), (fx, my - 3.4 * u), (fx, my + 4.4 * u)], MOUTH)
    elif kind == 'open':
        poly([(bx, my), (fx, my - 4.5 * u), (fx, my + 9 * u)], MOUTH)
        d.polygon([(x * S, y * S) for x, y in [(fx - s * 4.5 * u, my + 4 * u), (fx - s * 0.8 * u, my + 3 * u), (fx - s * 0.8 * u, my + 6 * u)]], fill=TONGUE)
    elif kind == 'wide':
        poly([(bx - s * 1 * u, my - 0.5 * u), (fx, my - 6 * u), (fx, my + 8.5 * u)], MOUTH)
        d.polygon([(x * S, y * S) for x, y in [(bx + s * 3 * u, my - 1.2 * u), (fx - s * 0.9 * u, my - 4.9 * u), (fx - s * 0.9 * u, my - 2.6 * u), (bx + s * 4 * u, my - 0.2 * u)]], fill=(255, 255, 255))
        d.polygon([(x * S, y * S) for x, y in [(fx - s * 6 * u, my + 5 * u), (fx - s * 0.9 * u, my + 3.5 * u), (fx - s * 0.9 * u, my + 7.5 * u)]], fill=TONGUE)
    elif kind == 'O':                                     # a pucker: lips pushed out to (and a little past) the face edge
        cx_ = hx + s * 41 * u
        d.ellipse(((cx_ - 5.4 * u) * S, (my - 6 * u) * S, (cx_ + 5.4 * u) * S, (my + 7 * u) * S), fill=mix(MOUTH, TONGUE, 0.25), outline=K, width=int(3.2 * u * S))
        d.ellipse(((cx_ + s * 1 * u - 1.6 * u) * S, (my - 1.6 * u) * S, (cx_ + s * 1 * u + 1.6 * u) * S, (my + 2.4 * u) * S), fill=MOUTH)
    elif kind == 'smile_talk':                            # upturned back corner + an upper-lip line: unlike 'small'
        poly([(bx - s * 1 * u, my - 4.5 * u), (fx, my - 1.5 * u), (fx - s * 1 * u, my + 6.5 * u)], MOUTH)
        L([(bx - s * 2 * u, my - 5.4 * u), (fx + s * 0.5 * u, my - 2 * u)], 3)
        d.polygon([(x * S, y * S) for x, y in [(fx - s * 4 * u, my + 3.8 * u), (fx - s * 1.2 * u, my + 3 * u), (fx - s * 1.5 * u, my + 5.6 * u)]], fill=TONGUE)
    else: return False
    return True

def draw_face_turned(C, expr, hx, hy, u, s, view, glasses, moustache, has_hat, mouth=None, blink=False):
    d = C.d; K = INK
    eyes_k, (bi, bo), mk = EXPR_TURNED.get(expr, EXPR_TURNED['neutral'])
    cy = hy; by = hy - (15 if has_hat else 20) * u
    if view == 'side': eyes = [(hx + s * 27 * u, 1.0, s)]                 # (x, width scale, inner-end direction)
    elif view == 'front': eyes = [(hx - 13 * u, 1.0, 1), (hx + 13 * u, 1.0, -1)]
    else: eyes = [(hx + s * 2 * u, 1.0, s), (hx + s * 25 * u, 0.8, -s)]   # near (back) eye, far eye squeezed
    def L(pts, w): d.line([(x * S, y * S) for x, y in pts], fill=K, width=max(1, int(w * S)), joint='curve')
    def ell(x, rx, ry, **kw): d.ellipse(((x - rx) * S, (cy - ry) * S, (x + rx) * S, (cy + ry) * S), **kw)
    for x, sx, ind in eyes:
        kind = 'closed' if blink else eyes_k
        if kind == 'lidded':
            L([(x - 9 * u * sx, cy - 1 * u), (x + 9 * u * sx, cy - 1 * u)], 3.8 * u)
            d.chord(((x - 7 * u * sx) * S, (cy - 6 * u) * S, (x + 7 * u * sx) * S, (cy + 6 * u) * S), 0, 180, fill=K)
        elif kind == 'dot': ell(x, 3.8 * u * sx, 5.5 * u, fill=K)
        elif kind == 'oval': ell(x, 3 * u * sx, 4.5 * u, fill=K)
        elif kind == 'happy': d.arc(((x - 8 * u * sx) * S, (cy - 4 * u) * S, (x + 8 * u * sx) * S, (cy + 8 * u) * S), 200, 340, fill=K, width=int(3.8 * u * S))
        elif kind == 'closed': d.arc(((x - 8 * u * sx) * S, (cy - 6 * u) * S, (x + 8 * u * sx) * S, (cy + 3 * u) * S), 20, 160, fill=K, width=int(3.8 * u * S))
        elif kind == 'shock':
            ell(x, 11 * u * sx, 11 * u, fill=(255, 255, 255), outline=K, width=int(2.6 * u * S))
            px = x + s * 4 * u * sx; d.ellipse(((px - 3 * u) * S, (cy - 3 * u) * S, (px + 3 * u) * S, (cy + 3 * u) * S), fill=K)
        elif kind == 'squeeze': L([(x - s * 7 * u * sx, cy - 4 * u), (x + s * 5 * u * sx, cy), (x - s * 7 * u * sx, cy + 4 * u)], 3.8 * u)
        # tapered brow: thick inner end (toward the nose) -> thin outer end
        x_in, x_out = x + ind * 8 * u * sx, x - ind * 9 * u * sx
        for k in range(12):
            t = k / 11; w = (5 - 2.5 * t) * u
            px, py = x_in + (x_out - x_in) * t, by + (bi + (bo - bi) * t) * u
            d.ellipse(((px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S), fill=K)
        if glasses:
            ell(x, 10 * u * sx, 9 * u, outline=K, width=int(2.6 * u * S))
    if glasses:
        if view == 'side': L([(eyes[0][0] - s * 10 * u, cy - 1 * u), (hx - s * 26 * u, cy - 3 * u)], 2.6 * u)
        elif view == 'front': L([(eyes[0][0] + 10 * u, cy - 1 * u), (eyes[1][0] - 10 * u, cy - 1 * u)], 2.6 * u)
        else: L([(eyes[0][0] + s * 10 * u, cy - 1 * u), (eyes[1][0] - s * 8 * u, cy - 1 * u)], 2.6 * u)
    # nose tick (no skin bump, no ear)
    # nose: a small open arc bulging forward. A '>' tick read as a third, squinting eye.
    ncx, ncy, nr = (hx + s * 42 * u, hy + 9 * u, 4.6 * u) if view == 'side' else (hx + s * 18 * u, hy + 9 * u, 3.8 * u)
    if view != 'front': L([(ncx + s * nr * math.cos(math.radians(t)), ncy + nr * math.sin(math.radians(t))) for t in range(-110, 111, 10)], 3.2 * u)
    mx = hx + s * (31 if view == 'side' else 17 if view == '3q' else 0) * u; my = hy + (21 if view == 'side' else 20) * u
    sx = 0.62 if view == 'side' else 0.85 if view == '3q' else 1.0
    mk2 = (CLOSED_FOR.get(expr, 'dash') if mouth == 'closed' else mouth) if mouth else mk
    if not (view == 'side' and mouth and profile_mouth(d, mk2, hx, my, u, s)):
        mouth_shape(d, mk2, mx, my, u, sx, s, far=0.85 if view == '3q' else 1.0)
    if moustache:
        col = hexrgb(moustache)
        for sg in ((s,) if view == 'side' else (-1, 1)):
            for k in range(10):
                t = k / 9; w = (4.5 - 3 * t) * u
                px, py = mx + sg * (1 + 9 * t) * u * sx, my - 7 * u + 2.5 * u * t * t
                d.ellipse(((px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S), fill=col)
    if expr == 'nervous':
        sx_ = hx + 37 * u if view == 'front' else hx - s * 34 * u
        C.d.ellipse(((sx_ - 3.5 * u) * S, (hy - 30 * u) * S, (sx_ + 3.5 * u) * S, (hy - 19 * u) * S), fill=SWEAT, outline=K, width=int(1.5 * u * S))

FRONT_STAND = dict(legN=(3, 1), legF=(3, 1), armN=(20, 9), armF=(20, 9), lean=0.0, tilt=0.0)   # front/rear: + = outward

def turned(view='side', build='adult', skin='#ffe2c2', shirt='#f08a2c', pants='#3b5b9a', expr='neutral', facing=1.0,
           hat=None, hat_col='#e2453c', hair=None, hair_col='#5a3b2a', outfit=(), glasses=False, prop=None, seed=1,
           white_head=False, moustache=None, pose=None, mouth=None, blink=False, tilt=0.0, lean=0.0, ground=True,
           rig=None, layers=None, sticker=None, pad=0, prop_hand='N', antennae='up', antennae_sway=0.0):
    """Rig views: 'side', '3q', 'rear', and 'front' (a jointed front body; character(view='front') keeps the legacy one).
       pose keys (all optional):
         legN, legF, armN, armF: (upper, lower[, upper-length factor]) angles in degrees from straight down.
             side/3q: + = forward.  front/rear: + = outward.  A factor < 1 foreshortens a segment pointing at the camera.
         lean: side/3q = torso lean forward; front/rear = sideways lean, + = toward screen right (deg).  tilt: head tilt (deg).
         footN/footF/handN/handF: IK targets in canvas units (override the angles).  hip: absolute hip position (no grounding).
         knee_out: front/rear knees bow further out.  arms_front: front/rear arms drawn in front of the torso.
       N/F: side/3q = near/far limb (far is darker and behind the body); front/rear = screen-right/screen-left limb.
       pad: widen the card by pad on each side (x coordinates shift by pad), for leaning riders.
       rig: dict that receives the solved joints.  layers: dict that receives the 4 draw layers
         ('far', 'legs', 'upper', 'near'), so a vehicle can be slotted between them."""
    B = BUILDS[build]; a, b = B['a'], B['b']; HH, Wd = 2 * b, 2 * a; u = Wd / 100
    flat = view in ('front', 'rear')
    s = -1 if facing < 0 else 1
    rnd = random.Random(seed)
    P = dict(SIDE_STAND if view == 'side' else Q3_STAND if view == '3q' else FRONT_STAND); P.update(pose or {})
    lean = P.get('lean', 0.0) + lean; tilt = P.get('tilt', 0.0) + tilt
    total = HH * (1 + B['torso'] + B['legs']); crown = 975 - total
    cx = 300 + pad; hy = crown + b; chin = hy + b; torso_bot = chin + B['torso'] * HH
    hip_y = torso_bot - 0.12 * HH
    foot_r = 3.75 * u
    Lleg = (975 - foot_r - hip_y) / 2
    arm_len = min(0.85, B['torso'] - 0.28) * HH        # hands end above the torso hem (short builds too)
    La1, La2 = 0.51 * arm_len, 0.49 * arm_len
    Ta = (0.31 if view == 'side' else 0.36 if view == '3q' else B['tw'] / 2) * Wd
    if flat:
        sd = {'N': 1, 'F': -1}                          # screen side of each limb
        hip0 = (cx, hip_y)
        hips0 = {k: (cx + sd[k] * 15 * u, hip_y) for k in 'NF'}
        sh_y = chin + 0.12 * HH
        sh0 = {k: (cx + sd[k] * 0.85 * Ta, sh_y) for k in 'NF'}
    else:
        sd = {'N': s, 'F': s}                           # side/3q: angles are measured toward the facing direction
        hip0 = (cx - s * 2 * u, hip_y)
        hips0 = {'N': (hip0[0] + (s * 2 * u if view == 'side' else -s * 7 * u), hip_y), 'F': (hip0[0] - (s * 3 * u if view == 'side' else -s * 10 * u), hip_y)}
        sh_y = chin + (0.16 if view == 'side' else 0.12) * HH
        sh0 = {'N': (cx - s * (0.15 if view == 'side' else 0.62) * Ta, sh_y), 'F': (cx + s * (0.0 if view == 'side' else 0.50) * Ta, sh_y)}

    def limb_ang(root, ang, L1, L2, side):
        f1 = ang[2] if len(ang) > 2 else 1.0
        return limb2(root, ang[0], ang[1], L1 * f1, L2, side)
    def flat_ik(root, tgt, L1, L2, side, bow):
        """Front/rear views: spare length bends the joint TOWARD or AWAY from the camera, which the screen shows as a
        shorter limb, not as a sideways loop. So keep the joint near the midline, bowed out by `bow` only."""
        dx, dy = tgt[0] - root[0], tgt[1] - root[1]; D = math.hypot(dx, dy) or 1e-6; d = min(D, L1 + L2 - 0.5)
        e = (root[0] + dx / D * d, root[1] + dy / D * d)
        return ((root[0] + e[0]) / 2 + side * bow, (root[1] + e[1]) / 2), e
    def legs_at(T):
        out = {}
        for k in 'NF':
            root = (hips0[k][0] + T[0], hips0[k][1] + T[1])
            bend = sd[k] if not flat else sd[k] * (1 if P.get('knee_out', True) else -1)
            if ('foot' + k) in P and flat: j, e = flat_ik(root, P['foot' + k], Lleg, Lleg, sd[k], (26 if P.get('knee_out_' + k) else 6) * u)
            elif ('foot' + k) in P: j, e = ik2(root, P['foot' + k], Lleg, Lleg, bend)
            else: j, e = limb_ang(root, P['leg' + k], Lleg, Lleg, sd[k])
            if flat:                                    # feet point outward (front) / short stubs seen from behind (rear)
                L0, L1_ = (3, 13) if view == 'front' else (2, 7)
                heel = (e[0] - sd[k] * L0 * u, e[1]); toe = (e[0] + sd[k] * L1_ * u, e[1])
            else:
                a2 = math.atan2(s * (e[0] - j[0]), e[1] - j[1]); fk = P.get('foot_k', 0.85)   # >1: clearer heel strike / push-off
                f = (s * math.cos(a2 * fk), -math.sin(a2 * fk))
                heel = (e[0] - f[0] * 3 * u, e[1] - f[1] * 3 * u); toe = (e[0] + f[0] * 13 * u, e[1] + f[1] * 13 * u)
            out[k] = (root, j, e, heel, toe)
        return out
    if 'hip' in P: T = (P['hip'][0] - hip0[0], P['hip'][1] - hip0[1])
    elif ground and not ('footN' in P or 'footF' in P):
        lg = legs_at((0, 0)); low = max(max(v[2][1], v[3][1], v[4][1]) for v in lg.values())
        T = (0.0, 975 - foot_r - low)
    else: T = (0.0, 0.0)
    legs = legs_at(T)
    hip = (hip0[0] + T[0], hip0[1] + T[1])
    rs = 1 if flat else s                                # screen direction of a positive lean
    def up(p): q = rot_pt(p, hip0, rs * lean); return (q[0] + T[0], q[1] + T[1])   # upper-body point -> canvas
    arms = {}
    for k in 'NF':
        root = up(sh0[k])
        if ('hand' + k) in P and flat:          # arm_reach > 1: an arm reaching toward/away from the camera (riding) covers more screen
            rr = P.get('arm_reach', 1.0); j, e = flat_ik(root, P['hand' + k], La1 * rr, La2 * rr, sd[k], 9 * u)
        elif ('hand' + k) in P: j, e = ik2(root, P['hand' + k], La1, La2, -s)
        else: j, e = limb_ang(root, P['arm' + k], La1, La2, sd[k])
        arms[k] = (root, j, e)

    CWd = W + 2 * pad
    LY = {k: Canvas(CWd) for k in ('far', 'legs', 'near')}
    skin_c, shirt_c, pants_c = hexrgb(skin), hexrgb(shirt), hexrgb(pants)
    if flat:
        legc = {k: mix(pants_c, INK, 0.55) for k in 'NF'}; armc = {k: mix(shirt_c, INK, 0.5) for k in 'NF'}
    else:
        legc = {'N': mix(pants_c, INK, 0.55), 'F': mix(pants_c, INK, 0.8)}
        armc = {'N': mix(shirt_c, INK, 0.5), 'F': mix(shirt_c, INK, 0.7)}
    def draw_leg(C, k):
        root, j, e, heel, toe = legs[k]
        C.stroke(bend_path(root, j, e), 5.8 * u, legc[k]); C.stroke([heel, toe], 7.5 * u, INK)
    def draw_arm(C, k):
        root, j, e = arms[k]
        C.stroke(bend_path(root, j, e), 5.2 * u, armc[k]); C.dot(*e, 5.5 * u)

    if flat:
        arm_layer = LY['near'] if P.get('arms_front', view == 'front' and ('handN' in P or 'handF' in P)) else LY['far']
        draw_arm(arm_layer, 'F'); draw_arm(arm_layer, 'N')
        draw_leg(LY['legs'], 'F'); draw_leg(LY['legs'], 'N')
    else:
        draw_arm(LY['far'], 'F'); draw_leg(LY['far'], 'F'); draw_leg(LY['legs'], 'N')

    # ---- upper body drawn upright on its own layer, then leaned about the hip
    U = Canvas(CWd)
    tb_top = chin - 0.25 * HH; tcy = (tb_top + torso_bot) / 2; tb = (torso_bot - tb_top) / 2
    if flat:
        torso = blob(cx, tcy, Ta, tb, nTop=2.2, nBot=2.6, egg=0.12, asym=0.0, rot=0, seed=seed + 7, noise=0.005)
    else:
        torso = blob(cx, tcy, Ta, tb, nTop=2.2, nBot=2.6, egg=(0.10 if view == 'side' else 0.12),
                     asym=(0.06 if view == 'side' else 0.05) * s, rot=0, seed=seed + 7, noise=0.005)
    U.fill_shaded(torso, shirt_c, SH_CLOTH, 0.55 * Ta, 0.18 * Ta, cx, tcy, rim=True)
    fe = (0.62 if view == 'side' else 0.30 if view == '3q' else 0.0) * Ta   # x offset of the body's front line
    def clothes(dd):
        def Pp(x, y): return (x * S, y * S)
        for item in outfit:
            kind = item[0]
            if kind == 'buttons' and view != 'rear':
                for k in range(item[1]):
                    y = chin + 0.18 * HH + k * 0.2 * HH; r = 2.4 * u * (0.8 if view == 'side' else 1)
                    dd.ellipse(Pp(cx + s * fe - r, y - r) + Pp(cx + s * fe + r, y + r), fill=hexrgb(item[2]))
            elif kind == 'tie' and view != 'rear':
                col = hexrgb(item[1]); x0 = cx + s * (fe + (0.15 * Ta if fe else 0)); k_ = 0.5 if view == 'side' else 0.85 if view == '3q' else 1
                dd.polygon([Pp(x0 - 4 * u * k_, chin - 2 * u), Pp(x0 + 4 * u * k_, chin - 2 * u), Pp(x0 + 6 * u * k_, chin + 0.55 * HH), Pp(x0, chin + 0.66 * HH), Pp(x0 - 6 * u * k_, chin + 0.55 * HH)], fill=col)
            elif kind == 'belt':
                y = torso_bot - 0.28 * HH; dd.rectangle(Pp(cx - 200, y) + Pp(cx + 200, y + 7 * u), fill=hexrgb(item[1]))
                if view != 'rear':
                    x0 = cx + s * fe; w = 3 * u if view == 'side' else 5 * u
                    dd.rectangle(Pp(x0 - w, y - 1 * u) + Pp(x0 + w, y + 8 * u), outline=hexrgb('#e8c45a'), width=int(1.8 * u * S))
            elif kind == 'apron':
                col = hexrgb(item[1])
                if view == 'rear':                     # ties and a bow at the back
                    y = torso_bot - 0.42 * HH
                    dd.rectangle(Pp(cx - 200, y) + Pp(cx + 200, y + 4 * u), fill=col)
                    for sg in (-1, 1): dd.ellipse(Pp(cx + sg * 6 * u - 5 * u, y - 3 * u) + Pp(cx + sg * 6 * u + 5 * u, y + 7 * u), fill=col)
                elif view == 'front':
                    dd.rounded_rectangle(Pp(cx - 0.62 * Ta, chin + 0.22 * HH) + Pp(cx + 0.62 * Ta, torso_bot + 10), radius=int(10 * u * S), fill=col)
                else:
                    x_back = cx + s * (fe - (0.75 if view == 'side' else 1.0) * Ta); xs_ = sorted([x_back, cx + s * 2 * Ta])
                    dd.rounded_rectangle(Pp(xs_[0], chin + 0.22 * HH) + Pp(xs_[1], torso_bot + 10), radius=int(10 * u * S), fill=col)
            elif kind == 'overalls':
                col = hexrgb(item[1])
                dd.rectangle(Pp(cx - 200, torso_bot - 0.45 * HH) + Pp(cx + 200, torso_bot + 10), fill=col)
                straps = (0.05,) if view == 'side' else (-0.35, 0.55) if view == '3q' else (-0.55, 0.55)
                for k in straps:
                    x1 = cx + s * k * Ta; x2 = cx + s * (k + 0.05) * Ta if view != 'rear' else cx - k * 0.5 * Ta   # crossed at the back
                    dd.line([Pp(x1, chin - 5), Pp(x2, torso_bot - 0.45 * HH)], fill=col, width=int(7 * u * S))
                    if view != 'rear':
                        dd.ellipse(Pp(x2 - 2.5 * u, torso_bot - 0.45 * HH - 2.5 * u) + Pp(x2 + 2.5 * u, torso_bot - 0.45 * HH + 2.5 * u), fill=hexrgb('#e8c45a'))
            elif kind == 'coat_open':
                col = hexrgb(item[1])
                if view == 'rear': dd.rectangle(Pp(cx - 300, chin - 10) + Pp(cx + 300, torso_bot + 20), fill=col); continue
                if view == 'front':
                    for sg in (-1, 1): dd.polygon([Pp(cx + sg * 0.18 * Ta, chin - 10), Pp(cx + sg * 300, chin - 10), Pp(cx + sg * 300, torso_bot + 20), Pp(cx + sg * 0.30 * Ta, torso_bot + 20)], fill=col)
                    for sg in (-1, 1): dd.line([Pp(cx + sg * 0.18 * Ta, chin - 10), Pp(cx + sg * 0.30 * Ta, torso_bot + 20)], fill=INK, width=int(1.6 * u * S))
                    continue
                op = cx + s * (fe - 0.12 * Ta)
                dd.polygon([Pp(op, chin - 10), Pp(cx - s * 300, chin - 10), Pp(cx - s * 300, torso_bot + 20), Pp(op + s * 0.1 * Ta, torso_bot + 20)], fill=col)
                dd.line([Pp(op, chin - 10), Pp(op + s * 0.1 * Ta, torso_bot + 20)], fill=INK, width=int(1.6 * u * S))
                if view == '3q':
                    dd.polygon([Pp(op + s * 0.42 * Ta, chin - 10), Pp(cx + s * 300, chin - 10), Pp(cx + s * 300, torso_bot + 20), Pp(op + s * 0.5 * Ta, torso_bot + 20)], fill=col)
                    dd.line([Pp(op + s * 0.42 * Ta, chin - 10), Pp(op + s * 0.5 * Ta, torso_bot + 20)], fill=INK, width=int(1.6 * u * S))
            elif kind == 'stripes':
                col = hexrgb(item[1] if len(item) > 1 else '#f1efe6')
                for k in range(4): y = chin + 0.25 * HH + k * 0.22 * HH; dd.rectangle(Pp(cx - 200, y) + Pp(cx + 200, y + 7 * u), fill=col)
            elif kind == 'collar':
                col = hexrgb(item[1] if len(item) > 1 else '#f1efe6')
                if view == 'rear': dd.rectangle(Pp(cx - 0.55 * Ta, chin - 6 * u) + Pp(cx + 0.55 * Ta, chin + 5 * u), fill=col); continue
                x0 = cx + s * fe
                if view == 'front':
                    for sg in (-1, 1): dd.polygon([Pp(cx, chin + 6 * u), Pp(cx + sg * 0.5 * Ta, chin - 4 * u), Pp(cx + sg * 0.35 * Ta, chin + 12 * u)], fill=col)
                    continue
                dd.polygon([Pp(x0, chin + 6 * u), Pp(x0 - s * 0.45 * Ta, chin - 4 * u), Pp(x0 - s * 0.3 * Ta, chin + 12 * u)], fill=col)
                if view == '3q': dd.polygon([Pp(x0, chin + 6 * u), Pp(x0 + s * 0.3 * Ta, chin - 4 * u), Pp(x0 + s * 0.22 * Ta, chin + 10 * u)], fill=col)
    U.clip_layer(clothes, torso)
    U.outline(torso, cx, tcy, 5 * u)

    # ---- head on its own layer: tilted about the neck, then leaned with the body
    Hd = Canvas(CWd)
    hx = cx + (0 if flat else s * (3 if view == 'side' else 4) * u)
    if view == 'side':
        head = blob(hx, hy, a, b * (1 + rnd.uniform(-0.03, 0.03)), nTop=1.8, nBot=2.3, egg=-0.10, asym=0.12 * s, rot=3 * s, seed=seed)
    elif view == '3q':
        head = blob(hx, hy, a * 0.97, a * 0.97 * 1.02 * (1 + rnd.uniform(-0.02, 0.02)), nTop=2.2, nBot=1.9, egg=0.0, asym=0.08 * s, rot=6 * s, seed=seed)
    else:
        head = blob(hx, hy, a, b, nTop=1.75, nBot=2.3, egg=-0.12, asym=rnd.choice([-1, 1]) * 0.05, rot=rnd.uniform(-3, 3), seed=seed)
    head_col = hexrgb('#fbf8f4') if white_head else skin_c
    Hd.fill_shaded(head, head_col, SH_WHITE if white_head else SH_SKIN, 0.30 * a, 0.09 * a, hx, hy)
    if hair:
        hc = hexrgb(hair_col)
        def hair_fn(dd):
            def E(x0, y0, x1, y1): dd.ellipse((min(x0, x1) * S, y0 * S, max(x0, x1) * S, y1 * S), fill=hc)
            if view == 'rear': E(hx - 1.1 * a, hy - 1.3 * b, hx + 1.1 * a, hy + 0.45 * b); return    # the back of the head is all hair
            if view == 'front': E(hx - 1.05 * a, hy - 1.25 * b, hx + 1.05 * a, hy - 0.15 * b); return
            E(hx - s * 1.15 * a, hy - b * 1.25, hx + s * 0.9 * a, hy - b * (0.15 if hair != 'bun' else 0.35))
            E(hx - s * 1.2 * a, hy - b * 0.9, hx - s * 0.05 * a, hy + b * (0.25 if hair == 'short' else 0.1))   # back of the skull
        Hd.clip_layer(hair_fn, head)
        if hair == 'bun':
            bx = hx if flat else hx - s * 0.62 * a
            bun = blob(bx, hy - b * (1.12 if flat else 0.98), 0.32 * a, 0.28 * b, seed=seed + 3, egg=0)
            Hd.fill_shaded(bun, hc, SH_CLOTH, 6, 4, hx, hy - b); Hd.outline(bun, hx, hy - b, 0.8 * 5 * u)
    Hd.outline(head, hx, hy, 5 * u)
    if hat: draw_hat(Hd, hat, hexrgb(hat_col), hx, hy, a, b, u, 5 * u, 0 if flat else s, 0 if flat else 3 * s,
                     rear=(view == 'rear'), sticker=sticker, antennae=antennae, sway=antennae_sway)
    if view != 'rear':
        draw_face_turned(Hd, expr, hx, hy, u, s, view, glasses, moustache, hat is not None, mouth, blink)
    neck = (cx, chin - 0.1 * HH)
    U.im.alpha_composite(_rot_layer(Hd.im, (rs if not flat else 1) * tilt, neck))
    upper = _rot_layer(U.im, rs * lean, hip0, T)

    # ---- the near arm in front of the body, with the held prop
    if not flat: draw_arm(LY['near'], 'N')
    hand_p = arms[prop_hand][2]
    if prop: draw_prop(LY['near'], prop, hand_p, u, side=(s if not flat else (1 if prop_hand == 'N' else -1)))
    if rig is not None:
        rig.update(hip=hip, neck=up(neck), head=up((hx, hy)), u=u, s=s, HH=HH,
                   handN=arms['N'][2], handF=arms['F'][2], shoulderN=arms['N'][0], shoulderF=arms['F'][0],
                   elbowN=arms['N'][1], elbowF=arms['F'][1], kneeN=legs['N'][1], kneeF=legs['F'][1],
                   ankleN=legs['N'][2], ankleF=legs['F'][2], hipN=legs['N'][0], hipF=legs['F'][0], Lleg=Lleg, Larm=(La1, La2))
    if layers is not None:
        layers.update(far=LY['far'].im, legs=LY['legs'].im, upper=upper, near=LY['near'].im)
    out = LY['far'].im.copy(); out.alpha_composite(LY['legs'].im); out.alpha_composite(upper); out.alpha_composite(LY['near'].im)
    return out.resize((CWd, H), Image.LANCZOS)


def _mask_outline(C, m, w, col_fill, shade=(0.8, 0.8, 0.85), cx=0, cy=0, light=(-0.7, -0.7), shift=12, blur=6):
    """Fill an L mask (canvas size) with a soft crescent-shaded colour and ring it with plum ink of width w."""
    bb = m.getbbox()
    if not bb: return
    pad = int(w * S * 2 + 8); box = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(m.width, bb[2] + pad), min(m.height, bb[3] + pad))
    mc = m.crop(box)
    grow = mc.filter(ImageFilter.GaussianBlur(w * S * 0.5)).point(lambda v: 255 if v > 6 else 0)   # cheap dilation
    ink = Image.new('RGBA', mc.size, INK + (255,)); ink.putalpha(grow)
    sh = Image.new('RGBA', mc.size, mul(col_fill, shade) + (255,)); sh.putalpha(mc)
    lit_m = ImageChops.offset(mc, int(light[0] * shift * S), int(light[1] * shift * S)).filter(ImageFilter.GaussianBlur(blur * S))
    lit = Image.new('RGBA', mc.size, col_fill + (255,)); lit.putalpha(ImageChops.multiply(lit_m, mc))
    lay = Image.new('RGBA', mc.size, (0, 0, 0, 0)); lay.alpha_composite(ink); lay.alpha_composite(sh); lay.alpha_composite(lit)
    C.im.alpha_composite(lay, (box[0], box[1])); C.d = ImageDraw.Draw(C.im)

def _sticker(C, cx, cy, wdt, hgt, text, rot=0.0, font_px=None):
    """A white rounded label with dark text, drawn (and optionally rotated) at (cx, cy) in design units."""
    from PIL import ImageFont
    lab = Image.new('RGBA', (int(wdt * S), int(hgt * S)), (0, 0, 0, 0)); dd = ImageDraw.Draw(lab)
    dd.rounded_rectangle((0, 0, lab.width - 1, lab.height - 1), radius=int(hgt * S * 0.22), fill=(252, 250, 242, 255), outline=INK, width=max(2, int(hgt * S * 0.06)))
    lines = text.split('\n') if '\n' in text else _wrap2(text)
    fs = font_px or hgt * S * 0.8 / len(lines) * 0.82
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', max(6, int(fs)))
    while max(dd.textlength(l, font=F) for l in lines) > lab.width * 0.88 and F.size > 6:
        F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', F.size - 1)
    tot = len(lines) * F.size * 1.08; y0 = (lab.height - tot) / 2
    for i, l in enumerate(lines):
        w_ = dd.textlength(l, font=F); dd.text(((lab.width - w_) / 2, y0 + i * F.size * 1.08 - F.size * 0.08), l, font=F, fill=(192, 40, 48, 255))
    if rot: lab = lab.rotate(-rot, resample=Image.BICUBIC, expand=True)
    C.im.alpha_composite(lab, (int(cx * S - lab.width / 2), int(cy * S - lab.height / 2))); C.d = ImageDraw.Draw(C.im)

def _wrap2(t):
    w = t.split()
    if len(w) < 3: return [t]
    best = min(range(1, len(w)), key=lambda k: abs(len(' '.join(w[:k])) - len(' '.join(w[k:]))))
    return [' '.join(w[:best]), ' '.join(w[best:])]

def draw_helmet(C, col, hx, hy, a, b, u, w0, facing, rear=False, sticker=None):
    """Open-face motorcycle helmet: a shell a little bigger than the skull, a face opening that keeps the eyes AND
    brows clear (the opening's top edge sits above the brow line), cheek guards, and a short peak."""
    s = 1 if facing >= 0 else -1; turn = abs(facing) >= 1          # side / 3q only when |facing| >= 1
    view = 'front' if not turn else ('side' if abs(facing) >= 1.5 else '3q')
    sh_rx, sh_ry = 1.08 * a, 1.07 * b
    base_y = hy - 0.42 * b                                           # top of the face opening (brows sit at about hy-0.32b)
    m = Image.new('L', C.im.size, 0); dm = ImageDraw.Draw(m)
    dm.ellipse(((hx - sh_rx) * S, (hy - sh_ry) * S, (hx + sh_rx) * S, (hy + sh_ry) * S), fill=255)
    dm.rectangle((0, (hy + 0.42 * b) * S, m.width, m.height), fill=0)                 # ends at the jaw line
    if not rear:
        oc, ow = {'front': (hx, 0.70 * a), '3q': (hx + s * 0.32 * a, 0.66 * a), 'side': (hx + s * 0.80 * a, 0.62 * a)}[view]
        dm.rounded_rectangle(((oc - ow) * S, base_y * S, (oc + ow) * S, (hy + 2 * b) * S), radius=int(0.25 * a * S), fill=0)
    _mask_outline(C, m, 0.85 * w0, col, cx=hx, cy=hy)
    dk = mul(col, (0.72, 0.72, 0.78))
    if not rear:                                                      # peak over the opening
        if view == 'side':
            pk = [(oc - s * ow, base_y - 2 * u), (oc + s * (ow * 0.2), base_y - 5 * u), (oc + s * (ow * 0.2 + 22 * u), base_y - 1 * u), (oc - s * ow, base_y + 3 * u)]
        else:
            pk = [(x, base_y - 3 * u + 7 * u * (1 - ((x - oc) / (ow * 1.05)) ** 2)) for x in [oc - ow * 1.05 + k * ow * 2.1 / 16 for k in range(17)]]
            pk = pk + [(x, y - 7 * u) for x, y in pk[::-1]]
        C.d.polygon([(x * S, y * S) for x, y in pk], fill=dk); C.d.line([(x * S, y * S) for x, y in pk + pk[:1]], fill=INK, width=int(0.6 * w0 * S), joint='curve')
    # a stripe over the crown, and the sticker on the side of the shell
    stx = hx if not turn else hx - s * 0.15 * a
    C.d.line([(stx * S, (hy - sh_ry + 2 * u) * S), (stx * S, (base_y - 8 * u if not rear else hy + 0.2 * b) * S)], fill=mix(col, (255, 255, 255), 0.0) if False else dk, width=int(6 * u * S))
    if sticker:
        if rear: _sticker(C, hx, hy - 0.02 * b, 1.45 * a, 0.62 * b, sticker)   # big: it must read at video size
        elif view == 'side': _sticker(C, hx - s * 0.35 * a, hy - 0.05 * b, 0.62 * a, 0.3 * b, sticker, rot=-s * 8)
        elif view == '3q': _sticker(C, hx - s * 0.62 * a, hy - 0.2 * b, 0.42 * a, 0.24 * b, sticker, rot=-s * 18)
        else: _sticker(C, hx - 0.86 * a, hy - 0.05 * b, 0.26 * a, 0.36 * b, sticker, rot=-70)


def _text_block(C, cx, cy, w, h, text, col=(36, 23, 38)):
    """Bold text wrapped into a box (design units), as large as fits: words on separate lines when needed."""
    from PIL import ImageFont
    words = text.split(); lines_opts = [[text]] + ([_wrap2(text)] if len(words) > 1 else []) + ([words] if len(words) > 2 else [])
    best = None
    for lines in lines_opts:
        for fs in range(int(h * S), 6, -2):
            F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fs)
            tw = max(C.d.textlength(l, font=F) for l in lines); th = len(lines) * fs * 1.12
            if tw <= w * S and th <= h * S: break
        if best is None or fs > best[0]: best = (fs, lines)
    fs, lines = best; F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fs)
    y0 = cy * S - len(lines) * fs * 1.12 / 2
    for i, l in enumerate(lines):
        tw = C.d.textlength(l, font=F); C.d.text((cx * S - tw / 2, y0 + i * fs * 1.12), l, font=F, fill=col)

def _broom(C, x, y, u, tilt, k=1.0, palm=True, wide=1.0):
    """Handle-down on a flat open palm: the handle rises from the palm, a big bristle head on top; tilt rotates it about
    the palm. About 1.6 head-heights tall: hold it from a hand at shoulder height (arm pose 'palm') so it fits the card."""
    L, HL, HW = 250 * k, 105 * k, 52 * k * wide
    t = math.radians(tilt)
    def P(a, b): return (x + math.sin(t) * a + math.cos(t) * b, y - math.cos(t) * a + math.sin(t) * b)   # a: up the handle, b: across
    top = P(L, 0)
    C.stroke([(x, y - 4 * u), top], 5.2 * u * k + 2 * 3.5 * k, INK); C.stroke([(x, y - 4 * u), top], 5.2 * u * k, (176, 122, 70))
    head = [P(L + 6 * k, -22 * k), P(L + HL - 6 * k, -HW), P(L + HL, -HW * 0.3), P(L + HL, HW * 0.3), P(L + HL - 6 * k, HW), P(L + 6 * k, 22 * k)]
    C.d.polygon([(px * S, py * S) for px, py in head], fill=(232, 196, 92))
    for kk in (-0.65, -0.3, 0.05, 0.4, 0.75):  # straw lines
        a0, a1 = P(L + 24 * k, kk * 22 * k), P(L + HL - 6 * k, kk * HW * 1.25)
        C.d.line([(a0[0] * S, a0[1] * S), (a1[0] * S, a1[1] * S)], fill=(176, 140, 60), width=int(2.4 * k * S))
    C.d.line([(px * S, py * S) for px, py in head + head[:1]], fill=INK, width=int(3.6 * k * S), joint='curve')
    for a0 in (L - 2 * k, L + 16 * k):        # two binding bands
        g = (a0 - L) * 0.3
        band = [P(a0, -18 * k - g), P(a0 + 10 * k, -20 * k - g), P(a0 + 10 * k, 20 * k + g), P(a0, 18 * k + g)]
        C.d.polygon([(px * S, py * S) for px, py in band], fill=(192, 53, 58)); C.d.line([(px * S, py * S) for px, py in band + band[:1]], fill=INK, width=int(3 * k * S), joint='curve')
    if palm:                                  # a flat open palm under the handle tip (the dot hand flattened)
        C.d.ellipse(((x - 8 * u) * S, (y - 3.4 * u) * S, (x + 8 * u) * S, (y + 2.6 * u) * S), fill=INK)

def _held_helmet(C, x, y, u, sticker):
    """An open-face helmet held by its edge and hanging below the hand (off the chin), with the dark face opening
    visible and a sticker that covers most of the shell, so its text reads at video size."""
    a = 50 * u * 1.05; cx, cy = x, y + 0.88 * a
    circ = [(cx + a * math.cos(k * math.pi / 60), cy + a * math.sin(k * math.pi / 60)) for k in range(120)]
    m = Image.new('L', C.im.size, 0); ImageDraw.Draw(m).polygon([(px * S, py * S) for px, py in circ], fill=255)
    _mask_outline(C, m, 5 * u * 0.85, hexrgb('#f4f1e8'), cx=cx, cy=cy)
    def opening(dd):                                       # the padded inside, seen through the face opening
        box = ((cx - 1.3 * a) * S, (cy - 0.25 * a) * S, (cx - 0.12 * a) * S, (cy + 1.4 * a) * S)
        dd.rounded_rectangle(box, radius=int(0.3 * a * S), fill=(62, 56, 70)); dd.rounded_rectangle(box, radius=int(0.3 * a * S), outline=INK, width=int(3.4 * S))
        dd.rounded_rectangle(((cx - 1.3 * a) * S, (cy - 0.36 * a) * S, (cx - 0.02 * a) * S, (cy - 0.2 * a) * S), radius=int(0.06 * a * S), fill=(176, 174, 186), outline=INK, width=int(3 * S))   # peak over the opening
    C.clip_layer(opening, circ)
    C.d.line([(px * S, py * S) for px, py in circ + circ[:1]], fill=INK, width=int(4 * S), joint='curve')
    C.d.line([((cx - 0.05 * a) * S, (cy - a + 4 * u) * S), ((cx + 0.6 * a) * S, (cy - 0.55 * a) * S)], fill=(176, 174, 186), width=int(6 * u * S))
    strap = [(cx - 0.35 * a, cy + 0.9 * a), (cx - 0.1 * a, cy + 1.32 * a), (cx + 0.35 * a, cy + 1.38 * a), (cx + 0.62 * a, cy + 0.78 * a)]
    C.stroke(bend_path(strap[0], strap[2], strap[3], 16), 4.5 * u + 5, INK); C.stroke(bend_path(strap[0], strap[2], strap[3], 16), 4.5 * u, (70, 66, 78))   # chin strap
    C.d.rectangle(((cx + 0.2 * a) * S, (cy + 1.3 * a) * S, (cx + 0.44 * a) * S, (cy + 1.46 * a) * S), fill=(200, 204, 212), outline=INK, width=int(2.4 * S))   # buckle
    if sticker: _sticker(C, cx + 0.22 * a, cy + 0.1 * a, 1.5 * a, 0.78 * a, sticker, rot=-4)
    C.dot(x, y, 5.5 * u)

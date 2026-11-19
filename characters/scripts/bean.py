# Bean-head cartoon characters (the channel's main cast style), built from the measured spec in
# references/reports/characters.md (§2). Our own characters: the STYLE is shared, no reference character is copied.
# Canvas 600x1000 design units, soles at y=975.
import math, random
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
    def __init__(self):
        self.im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
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
              view='front', pose=None, mouth=None, blink=False, tilt=0.0, ground=True):
    # view: 'front' (default), 'side' or '3q'. In side/3q, facing < 0 faces left, otherwise right.
    # pose (side/3q): joint angles / IK targets, see turned(). mouth: lip-sync shape from MOUTHS. blink: eyes shut.
    if view != 'front':
        return turned(view=view, build=build, skin=skin, shirt=shirt, pants=pants, expr=expr, facing=facing, hat=hat,
                      hat_col=hat_col, hair=hair, hair_col=hair_col, outfit=outfit, glasses=glasses, prop=prop, seed=seed,
                      white_head=white_head, moustache=moustache, pose=pose, mouth=mouth, blink=blink, tilt=tilt,
                      lean=lean, ground=ground)
    B = BUILDS[build]; a, b = B['a'], B['b']; HH, Wd = 2 * b, 2 * a; u = Wd / 100
    rnd = random.Random(seed)
    total = 1.0 * HH + B['torso'] * HH + B['legs'] * HH
    crown = 975 - total
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
        elif pose == 'chin':     # hand to chin
            el = (cx + sgn * (0.9 * Ta), sh_y + 0.55 * HH); hd = (cx + sgn * 0.12 * Ta + facing * 6 * u, chin - 2 * u)
        return [s0, el, hd]
    poses = arm_pose if isinstance(arm_pose, tuple) else (arm_pose, arm_pose)
    front = []
    for sgn, ps in zip((-1, 1), poses):
        pts = arm(sgn, ps)
        if ps in ('hold', 'chin'): front.append((pts, ps)); continue      # hands in front of the body: draw after the torso
        C.stroke(bow(pts[0], pts[1], -sgn * 1.5 * u, 8) + bow(pts[1], pts[2], -sgn * 1.0 * u, 8)[1:], 5.2 * u, arm_c)
        C.dot(*pts[2], 5.5 * u)
        if prop and ps in ('wave', 'point', 'hang') and sgn == 1: draw_prop(C, prop, pts[2], u)
    # ---- torso: shaded fill -> clothing (clipped) -> ink
    C.fill_shaded(torso, shirt_c, SH_CLOTH, 0.55 * Ta, 0.18 * Ta, cx, tcy, rim=True)
    def clothes(dd):
        def P(x, y): return (x * S, y * S)
        for item in outfit:
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
    if hat: draw_hat(C, hat, hexrgb(hat_col), cx + facing * 4 * u, hy, a, b, u, w0, facing, hrot)
    # ---- face
    draw_face(C, expr, cx + facing * 4 * u, hy, u, facing, glasses, moustache, hat is not None)
    # ---- arms in front of the body
    for pts, ps in front:
        sgn = 1 if pts[0][0] > cx else -1
        C.stroke(bow(pts[0], pts[1], -sgn * 1.5 * u, 8) + bow(pts[1], pts[2], sgn * 1.0 * u, 8)[1:], 5.2 * u, arm_c)
        C.dot(*pts[2], 5.5 * u)
        if prop and ps == 'hold': draw_prop(C, prop, pts[2], u)
    return C.im.resize((W, H), Image.LANCZOS)

def draw_hat(C, kind, col, cx, hy, a, b, u, w0, facing, rot):
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
        if kind == 'cap':     # brim sticks out on the facing side
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

def draw_face(C, expr, cx, cy, u, facing, glasses, moustache, has_hat):
    d = C.d; K = INK
    ex = cx + 7 * u * facing; eL, eR = ex - 13 * u, ex + 13 * u
    by = cy - (15 if has_hat else 20) * u
    mx, my = cx + 8 * u * facing, cy + 20 * u
    def L(pts, w): d.line([(x * S, y * S) for x, y in pts], fill=K, width=max(1, int(w * S)), joint='curve')
    def lidded(x):
        L([(x - 9 * u, cy - 1 * u), (x + 9 * u, cy - 1 * u)], 3.8 * u)
        d.chord(((x - 7 * u) * S, (cy - 6 * u) * S, (x + 7 * u) * S, (cy + 6 * u) * S), 0, 180, fill=K)
    def dotv(x, rx=3.8, ry=5.5): d.ellipse(((x - rx * u) * S, (cy - ry * u) * S, (x + rx * u) * S, (cy + ry * u) * S), fill=K)
    def happy(x): d.arc(((x - 8 * u) * S, (cy - 4 * u) * S, (x + 8 * u) * S, (cy + 8 * u) * S), 200, 340, fill=K, width=int(3.8 * u * S))
    def brow(x, inner, outer, side):     # tapered: thick inner end -> thin outer end; inner/outer offsets in u (+ = down)
        x_in, x_out = x - side * 8 * u, x + side * 9 * u
        y_in, y_out = by + inner * u, by + outer * u
        for k in range(12):
            t = k / 11; w = (5 - 2.5 * t) * u
            px, py = x_in + (x_out - x_in) * t, y_in + (y_out - y_in) * t
            d.ellipse(((px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S), fill=K)
    if expr == 'neutral':
        lidded(eL); lidded(eR); brow(eL, 0, -1, -1); brow(eR, 0, -1, 1)
        L([(mx - 5.5 * u, my + 0.4 * u), (mx + 5.5 * u, my - 0.4 * u)], 4 * u)
    elif expr == 'stern':
        lidded(eL); lidded(eR); brow(eL, 3, -2, -1); brow(eR, 3, -2, 1)
        d.arc(((mx - 7 * u) * S, my * S, (mx + 7 * u) * S, (my + 7 * u) * S), 200, 340, fill=K, width=int(4 * u * S))
    elif expr == 'grin':
        happy(eL); happy(eR); brow(eL, -3, -3, -1); brow(eR, -3, -3, 1)
        d.chord(((mx - 12 * u) * S, (my - 8 * u) * S, (mx + 12 * u) * S, (my + 8 * u) * S), 0, 180, fill=MOUTH)
        d.rectangle(((mx - 11 * u) * S, my * S, (mx + 11 * u) * S, (my + 2.6 * u) * S), fill=(255, 255, 255))
        d.arc(((mx - 12 * u) * S, (my - 8 * u) * S, (mx + 12 * u) * S, (my + 8 * u) * S), 0, 180, fill=K, width=int(2.5 * u * S))
        L([(mx - 12 * u, my), (mx + 12 * u, my)], 2.5 * u)
    elif expr == 'shock':
        for x in (ex - 11.5 * u, ex + 11.5 * u):
            d.ellipse(((x - 11 * u) * S, (cy - 11 * u) * S, (x + 11 * u) * S, (cy + 11 * u) * S), fill=(255, 255, 255), outline=K, width=int(2.6 * u * S))
            d.ellipse(((x - 3 * u + facing * 3 * u) * S, (cy - 3 * u) * S, (x + 3 * u + facing * 3 * u) * S, (cy + 3 * u) * S), fill=K)
        brow(eL, -7, -8, -1); brow(eR, -7, -8, 1)
        d.ellipse(((mx - 9 * u) * S, (my - 5 * u) * S, (mx + 9 * u) * S, (my + 17 * u) * S), fill=MOUTH, outline=K, width=int(2.5 * u * S))
    elif expr == 'nervous':
        dotv(eL, 3, 4.5); dotv(eR, 3, 4.5); brow(eL, -3, 2, -1); brow(eR, -3, 2, 1)
        pts = [(mx - 9 * u + k * 1.8 * u, my + math.sin(k * 1.3) * 1.5 * u) for k in range(11)]; L(pts, 3.5 * u)
        C.d.ellipse(((cx + 34 * u) * S, (cy - 30 * u) * S, (cx + 41 * u) * S, (cy - 19 * u) * S), fill=SWEAT, outline=K, width=int(1.5 * u * S))
    elif expr == 'smile':
        dotv(eL); dotv(eR); brow(eL, 0, -1, -1); brow(eR, 0, -1, 1)
        d.arc(((mx - 7 * u) * S, (my - 5 * u) * S, (mx + 7 * u) * S, (my + 3 * u) * S), 20, 160, fill=K, width=int(4 * u * S))
    elif expr == 'smug':
        lidded(eL); lidded(eR); brow(eL, 0, 0, -1); brow(eR, -4, -6, 1)
        d.arc(((mx - 4 * u) * S, (my - 6 * u) * S, (mx + 10 * u) * S, (my + 2 * u) * S), 20, 120, fill=K, width=int(4 * u * S))
    elif expr == 'pained':
        lidded(eR)
        L([(eL - 7 * u, cy - 4 * u), (eL + 5 * u, cy), (eL - 7 * u, cy + 4 * u)], 3.8 * u)
        brow(eL, -3, 2, -1); brow(eR, -3, 2, 1)
        d.rectangle(((mx - 12 * u) * S, (my - 4 * u) * S, (mx + 12 * u) * S, (my + 4 * u) * S), fill=(255, 255, 255), outline=K, width=int(2.4 * u * S))
        for k in (-6, 0, 6): L([(mx + k * u, my - 4 * u), (mx + k * u, my + 4 * u)], 1.6 * u)
        L([(mx - 12 * u, my), (mx + 12 * u, my)], 1.6 * u)
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

def draw_prop(C, kind, hand, u):
    x, y = hand
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

def mouth_shape(d, kind, mx, my, u, sx=1.0, s=1):
    """Mouths shared by expressions and lip sync. sx squeezes the width (3/4 and side views)."""
    K = INK
    def X(v): return mx + v * u * sx
    def L(pts, w): d.line([(x * S, y * S) for x, y in pts], fill=K, width=max(1, int(w * S)), joint='curve')
    def box(x0, y0, x1, y1): return ((X(x0)) * S, (my + y0 * u) * S, (X(x1)) * S, (my + y1 * u) * S)
    if kind in ('dash', 'closed'):
        L([(X(-5.5), my + 0.4 * u * s), (X(5.5), my - 0.4 * u * s)], 4 * u)
    elif kind == 'frown': d.arc(box(-7, 0, 7, 7), 200, 340, fill=K, width=int(4 * u * S))
    elif kind == 'smirk': d.arc(box(-7, -5, 7, 3), 20, 160, fill=K, width=int(4 * u * S))
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
    elif kind == 'small': d.ellipse(box(-4.5, -2.5, 4.5, 3.5), fill=MOUTH, outline=K, width=int(2.2 * u * S))
    elif kind == 'open':
        d.ellipse(box(-7, -4, 7, 9), fill=MOUTH, outline=K, width=int(2.5 * u * S))
        d.chord(box(-4.5, 3, 4.5, 9), 180, 360, fill=TONGUE)
    elif kind == 'wide':
        d.rounded_rectangle(box(-12, -5, 12, 7), radius=int(4.5 * u * S), fill=MOUTH, outline=K, width=int(2.5 * u * S))
        d.rectangle((X(-10) * S, (my - 3.6 * u) * S, X(10) * S, (my - 1.2 * u) * S), fill=(255, 255, 255))
        d.chord(box(-6, 2, 6, 7.5), 180, 360, fill=TONGUE)
    elif kind == 'O':
        d.ellipse(box(-5, -5, 5, 8), fill=MOUTH, outline=K, width=int(2.6 * u * S))
    elif kind == 'smile_talk':
        d.chord(box(-10, -6, 10, 8), 0, 180, fill=MOUTH)
        d.arc(box(-10, -6, 10, 8), 0, 180, fill=K, width=int(2.5 * u * S)); L([(X(-10), my + u), (X(10), my + u)], 2.5 * u)
        d.chord(box(-5, 3.5, 5, 8), 180, 360, fill=TONGUE)
    else: raise ValueError(f'unknown mouth {kind!r}; lip-sync mouths are {MOUTHS}')

def draw_face_turned(C, expr, hx, hy, u, s, view, glasses, moustache, has_hat, mouth=None, blink=False):
    d = C.d; K = INK
    eyes_k, (bi, bo), mk = EXPR_TURNED.get(expr, EXPR_TURNED['neutral'])
    cy = hy; by = hy - (15 if has_hat else 20) * u
    if view == 'side': eyes = [(hx + s * 27 * u, 1.0, s)]                 # (x, width scale, inner-end direction)
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
        else: L([(eyes[0][0] + s * 10 * u, cy - 1 * u), (eyes[1][0] - s * 8 * u, cy - 1 * u)], 2.6 * u)
    # nose tick (no skin bump, no ear)
    # nose: a small open arc bulging forward. A '>' tick read as a third, squinting eye.
    ncx, ncy, nr = (hx + s * 42 * u, hy + 9 * u, 4.6 * u) if view == 'side' else (hx + s * 18 * u, hy + 9 * u, 3.8 * u)
    L([(ncx + s * nr * math.cos(math.radians(t)), ncy + nr * math.sin(math.radians(t))) for t in range(-110, 111, 10)], 3.2 * u)
    mx = hx + s * (31 if view == 'side' else 17) * u; my = hy + (21 if view == 'side' else 20) * u
    sx = 0.62 if view == 'side' else 0.85
    mouth_shape(d, mouth or mk, mx, my, u, sx, s)
    if moustache:
        col = hexrgb(moustache)
        for sg in ((1,) if view == 'side' else (-1, 1)):
            for k in range(10):
                t = k / 9; w = (4.5 - 3 * t) * u
                px, py = mx + sg * (1 + 9 * t) * u * sx, my - 7 * u + 2.5 * u * t * t
                d.ellipse(((px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S), fill=col)
    if expr == 'nervous':
        C.d.ellipse(((hx - s * 34 * u - 3.5 * u) * S, (hy - 30 * u) * S, (hx - s * 34 * u + 3.5 * u) * S, (hy - 19 * u) * S), fill=SWEAT, outline=K, width=int(1.5 * u * S))

def turned(view='side', build='adult', skin='#ffe2c2', shirt='#f08a2c', pants='#3b5b9a', expr='neutral', facing=1.0,
           hat=None, hat_col='#e2453c', hair=None, hair_col='#5a3b2a', outfit=(), glasses=False, prop=None, seed=1,
           white_head=False, moustache=None, pose=None, mouth=None, blink=False, tilt=0.0, lean=0.0, ground=True,
           rig=None):
    """Side / 3/4 view. pose keys (all optional):
         legN, legF, armN, armF: (upper, lower) angles, + = forward;  lean: torso lean forward (deg);  tilt: head nod forward (deg)
         footN/footF/handN/handF: IK targets (canvas units) that override the angles;  hip: absolute hip position (disables grounding)
       N = the near limb (in front of the body), F = the far limb (behind it, darker).
       rig: pass a dict to receive the solved joints (hands, feet, hip, shoulders, neck) in canvas units."""
    B = BUILDS[build]; a, b = B['a'], B['b']; HH, Wd = 2 * b, 2 * a; u = Wd / 100
    s = -1 if facing < 0 else 1
    rnd = random.Random(seed)
    P = dict(SIDE_STAND if view == 'side' else Q3_STAND); P.update(pose or {})
    lean = P.get('lean', 0.0) + lean; tilt = P.get('tilt', 0.0) + tilt
    total = HH * (1 + B['torso'] + B['legs']); crown = 975 - total
    cx = 300; hy = crown + b; chin = hy + b; torso_bot = chin + B['torso'] * HH
    hip_y = torso_bot - 0.12 * HH
    foot_r = 3.75 * u
    Lleg = (975 - foot_r - hip_y) / 2
    arm_len = min(0.85, B['torso'] - 0.28) * HH        # hands end above the torso hem (short builds too)
    La1, La2 = 0.51 * arm_len, 0.49 * arm_len
    Ta = (0.31 if view == 'side' else 0.36) * Wd
    hip0 = (cx - s * 2 * u, hip_y)
    hips0 = {'N': (hip0[0] + (s * 2 * u if view == 'side' else -s * 7 * u), hip_y), 'F': (hip0[0] - (s * 3 * u if view == 'side' else -s * 10 * u), hip_y)}
    sh_y = chin + (0.16 if view == 'side' else 0.12) * HH
    sh0 = {'N': (cx - s * (0.15 if view == 'side' else 0.62) * Ta, sh_y), 'F': (cx + s * (0.0 if view == 'side' else 0.50) * Ta, sh_y)}

    def legs_at(T):
        out = {}
        for k in 'NF':
            root = (hips0[k][0] + T[0], hips0[k][1] + T[1])
            if ('foot' + k) in P: j, e = ik2(root, P['foot' + k], Lleg, Lleg, s)
            else: j, e = limb2(root, *P['leg' + k], Lleg, Lleg, s)
            a2 = math.atan2(s * (e[0] - j[0]), e[1] - j[1])
            f = (s * math.cos(a2 * 0.85), -math.sin(a2 * 0.85))
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
    def up(p): q = rot_pt(p, hip0, s * lean); return (q[0] + T[0], q[1] + T[1])   # upper-body point -> canvas
    arms = {}
    for k in 'NF':
        root = up(sh0[k])
        if ('hand' + k) in P: j, e = ik2(root, P['hand' + k], La1, La2, -s)
        else: j, e = limb2(root, *P['arm' + k], La1, La2, s)
        arms[k] = (root, j, e)

    C = Canvas()
    skin_c, shirt_c, pants_c = hexrgb(skin), hexrgb(shirt), hexrgb(pants)
    legc = {'N': mix(pants_c, INK, 0.55), 'F': mix(pants_c, INK, 0.8)}
    armc = {'N': mix(shirt_c, INK, 0.5), 'F': mix(shirt_c, INK, 0.7)}
    def draw_leg(k):
        root, j, e, heel, toe = legs[k]
        C.stroke(bend_path(root, j, e), 5.8 * u, legc[k]); C.stroke([heel, toe], 7.5 * u, INK)
    def draw_arm(k):
        root, j, e = arms[k]
        C.stroke(bend_path(root, j, e), 5.2 * u, armc[k]); C.dot(*e, 5.5 * u)

    # ---- far limbs behind the body
    draw_arm('F'); draw_leg('F'); draw_leg('N')

    # ---- upper body drawn upright on its own layer, then leaned about the hip
    U = Canvas()
    tb_top = chin - 0.25 * HH; tcy = (tb_top + torso_bot) / 2; tb = (torso_bot - tb_top) / 2
    torso = blob(cx, tcy, Ta, tb, nTop=2.2, nBot=2.6, egg=(0.10 if view == 'side' else 0.12),
                 asym=(0.06 if view == 'side' else 0.05) * s, rot=0, seed=seed + 7, noise=0.005)
    U.fill_shaded(torso, shirt_c, SH_CLOTH, 0.55 * Ta, 0.18 * Ta, cx, tcy, rim=True)
    fe = (0.62 if view == 'side' else 0.30) * Ta        # x offset of the body's front line (buttons, tie, opening)
    def clothes(dd):
        def Pp(x, y): return (x * S, y * S)
        for item in outfit:
            kind = item[0]
            if kind == 'buttons':
                for k in range(item[1]):
                    y = chin + 0.18 * HH + k * 0.2 * HH; r = 2.4 * u * (0.8 if view == 'side' else 1)
                    dd.ellipse(Pp(cx + s * fe - r, y - r) + Pp(cx + s * fe + r, y + r), fill=hexrgb(item[2]))
            elif kind == 'tie':
                col = hexrgb(item[1]); x0 = cx + s * (fe + 0.15 * Ta); k_ = 0.5 if view == 'side' else 0.85
                dd.polygon([Pp(x0 - 4 * u * k_, chin - 2 * u), Pp(x0 + 4 * u * k_, chin - 2 * u), Pp(x0 + 6 * u * k_, chin + 0.55 * HH), Pp(x0, chin + 0.66 * HH), Pp(x0 - 6 * u * k_, chin + 0.55 * HH)], fill=col)
            elif kind == 'belt':
                y = torso_bot - 0.28 * HH; dd.rectangle(Pp(cx - 200, y) + Pp(cx + 200, y + 7 * u), fill=hexrgb(item[1]))
                x0 = cx + s * fe; w = 3 * u if view == 'side' else 5 * u
                dd.rectangle(Pp(x0 - w, y - 1 * u) + Pp(x0 + w, y + 8 * u), outline=hexrgb('#e8c45a'), width=int(1.8 * u * S))
            elif kind == 'apron':
                col = hexrgb(item[1]); x_back = cx + s * (fe - (0.75 if view == 'side' else 1.0) * Ta)
                xs_ = sorted([x_back, cx + s * 2 * Ta])
                dd.rounded_rectangle(Pp(xs_[0], chin + 0.22 * HH) + Pp(xs_[1], torso_bot + 10), radius=int(10 * u * S), fill=col)
            elif kind == 'overalls':
                col = hexrgb(item[1])
                dd.rectangle(Pp(cx - 200, torso_bot - 0.45 * HH) + Pp(cx + 200, torso_bot + 10), fill=col)
                straps = (0.05,) if view == 'side' else (-0.35, 0.55)
                for k in straps: dd.line([Pp(cx + s * k * Ta, chin - 5), Pp(cx + s * (k + 0.05) * Ta, torso_bot - 0.45 * HH)], fill=col, width=int(7 * u * S))
                for k in straps:
                    x0 = cx + s * (k + 0.05) * Ta; y0 = torso_bot - 0.45 * HH
                    dd.ellipse(Pp(x0 - 2.5 * u, y0 - 2.5 * u) + Pp(x0 + 2.5 * u, y0 + 2.5 * u), fill=hexrgb('#e8c45a'))
            elif kind == 'coat_open':     # the coat covers the back of the bean; the shirt shows at the front opening
                col = hexrgb(item[1]); op = cx + s * (fe - 0.12 * Ta)
                dd.polygon([Pp(op, chin - 10), Pp(cx - s * 300, chin - 10), Pp(cx - s * 300, torso_bot + 20), Pp(op + s * 0.1 * Ta, torso_bot + 20)], fill=col)
                dd.line([Pp(op, chin - 10), Pp(op + s * 0.1 * Ta, torso_bot + 20)], fill=INK, width=int(1.6 * u * S))
                if view == '3q':          # far lapel: a narrow strip past the opening
                    dd.polygon([Pp(op + s * 0.42 * Ta, chin - 10), Pp(cx + s * 300, chin - 10), Pp(cx + s * 300, torso_bot + 20), Pp(op + s * 0.5 * Ta, torso_bot + 20)], fill=col)
                    dd.line([Pp(op + s * 0.42 * Ta, chin - 10), Pp(op + s * 0.5 * Ta, torso_bot + 20)], fill=INK, width=int(1.6 * u * S))
            elif kind == 'stripes':
                col = hexrgb(item[1])
                for k in range(4): y = chin + 0.25 * HH + k * 0.22 * HH; dd.rectangle(Pp(cx - 200, y) + Pp(cx + 200, y + 7 * u), fill=col)
            elif kind == 'collar':
                col = hexrgb(item[1]); x0 = cx + s * fe
                dd.polygon([Pp(x0, chin + 6 * u), Pp(x0 - s * 0.45 * Ta, chin - 4 * u), Pp(x0 - s * 0.3 * Ta, chin + 12 * u)], fill=col)
                if view == '3q': dd.polygon([Pp(x0, chin + 6 * u), Pp(x0 + s * 0.3 * Ta, chin - 4 * u), Pp(x0 + s * 0.22 * Ta, chin + 10 * u)], fill=col)
    U.clip_layer(clothes, torso)
    U.outline(torso, cx, tcy, 5 * u)

    # ---- head on its own layer: tilted about the neck, then leaned with the body
    Hd = Canvas()
    hx = cx + s * (3 if view == 'side' else 4) * u
    if view == 'side':
        head = blob(hx, hy, a, b * (1 + rnd.uniform(-0.03, 0.03)), nTop=1.8, nBot=2.3, egg=-0.10, asym=0.12 * s, rot=3 * s, seed=seed)
    else:
        head = blob(hx, hy, a * 0.97, a * 0.97 * 1.02 * (1 + rnd.uniform(-0.02, 0.02)), nTop=2.2, nBot=1.9, egg=0.0, asym=0.08 * s, rot=6 * s, seed=seed)
    head_col = hexrgb('#fbf8f4') if white_head else skin_c
    Hd.fill_shaded(head, head_col, SH_WHITE if white_head else SH_SKIN, 0.30 * a, 0.09 * a, hx, hy)
    if hair:
        hc = hexrgb(hair_col)
        def hair_fn(dd):
            def E(x0, y0, x1, y1): dd.ellipse((min(x0, x1) * S, y0 * S, max(x0, x1) * S, y1 * S), fill=hc)
            E(hx - s * 1.15 * a, hy - b * 1.25, hx + s * 0.9 * a, hy - b * (0.15 if hair != 'bun' else 0.35))
            E(hx - s * 1.2 * a, hy - b * 0.9, hx - s * 0.05 * a, hy + b * (0.25 if hair == 'short' else 0.1))   # back of the skull
        Hd.clip_layer(hair_fn, head)
        if hair == 'bun':
            bun = blob(hx - s * 0.62 * a, hy - b * 0.98, 0.32 * a, 0.28 * b, seed=seed + 3, egg=0)
            Hd.fill_shaded(bun, hc, SH_CLOTH, 6, 4, hx, hy - b); Hd.outline(bun, hx, hy - b, 0.8 * 5 * u)
    Hd.outline(head, hx, hy, 5 * u)
    if hat: draw_hat(Hd, hat, hexrgb(hat_col), hx, hy, a, b, u, 5 * u, s, 3 * s)
    draw_face_turned(Hd, expr, hx, hy, u, s, view, glasses, moustache, hat is not None, mouth, blink)
    neck = (cx, chin - 0.1 * HH)
    U.im.alpha_composite(_rot_layer(Hd.im, s * tilt, neck))
    C.im.alpha_composite(_rot_layer(U.im, s * lean, hip0, T)); C.d = ImageDraw.Draw(C.im)

    # ---- near arm in front of the body, with the held prop
    draw_arm('N')
    if prop: draw_prop(C, prop, arms['N'][2], u)
    if rig is not None:
        rig.update(hip=hip, neck=up(neck), head=up((hx, hy)), u=u, s=s,
                   handN=arms['N'][2], handF=arms['F'][2], shoulderN=arms['N'][0], shoulderF=arms['F'][0],
                   ankleN=legs['N'][2], ankleF=legs['F'][2], hipN=legs['N'][0], hipF=legs['F'][0], Lleg=Lleg, Larm=(La1, La2))
    return C.im.resize((W, H), Image.LANCZOS)

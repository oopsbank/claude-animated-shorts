# Original solid-colour stickman (v3): ~5 heads tall, tube body, smooth bent limbs,
# thin dark outline, lit head, expressive face. Parametric colour / pose / expression / hat / look,
# plus wardrobe: outfits (shirt, coat, uniform, apron, pants), hats, held props and lip-sync mouths.
# Canvas 600x1000, soles at y=975 (same contract as the card in scene2.py).
# usage: python stickman.py out.png [expr] [pose] [hex colour] [hat] [look -1..1] [key=value ...]
#   e.g. python stickman.py a.png happy wave '#4a86e0' chef 0 outfit=chef prop=cup mouth=open
import sys, math
from PIL import Image, ImageDraw, ImageChops, ImageFilter

S = 4
W, H = 600, 1000
INK = (18, 16, 26)

def hexrgb(h):
    if isinstance(h, tuple): return h[:3]
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mixc(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# angles in degrees from straight down; + swings toward viewer's LEFT. (upper, lower)
POSES = {
    'stand': dict(armL=(24, 10), armR=(-24, -10), legL=(10, 1), legR=(-10, -1)),
    'wave':  dict(armL=(24, 10), armR=(-125, -168), legL=(10, 1), legR=(-10, -1)),
    'walk':  dict(armL=(-22, -42), armR=(26, 10), legL=(-20, 0), legR=(18, 40)),
    'run':   dict(armL=(-55, -125), armR=(45, -15), legL=(-38, 8), legR=(30, 85)),
    'point': dict(armL=(24, 10), armR=(-82, -88), legL=(11, 1), legR=(-11, -1)),
    'shrug': dict(armL=(60, -35), armR=(-60, 35), legL=(10, 1), legR=(-10, -1)),
    'think': dict(armL=(10, -93, 0.72), armR=(7, 175, 0.97, 0.8), legL=(10, 1), legR=(-10, -1)),   # arm across the belly, other hand on the chin
    'cheer': dict(armL=(145, 160), armR=(-145, -160), legL=(16, 2), legR=(-16, -2)),
    'hold':  dict(armL=(24, 10), armR=(-30, -95, 0.95, 0.9), legL=(10, 1), legR=(-10, -1)),     # forearm raised forward to show a held prop
}

SIDE_POSES = {'walk', 'run'}

# ---------------- wardrobe ----------------
OUTFIT_DEFAULTS = dict(shirt='#f3f1ea', coat='#8b5a3c', uniform='#2e3f6e', apron='#f7f4ec', pants='#3a4058')
OUTFITS = {                                  # presets for shots.json "outfit"
    'sailor':    dict(shirt='#f4f4f0', pants='#26346a'),
    'captain':   dict(uniform='#24305e'),
    'soldier':   dict(uniform='#4e6a3e'),
    'chef':      dict(shirt='#ffffff', apron='#c6d4e4', pants='#3a3a44'),
    'detective': dict(coat='#9a7048'),
    'worker':    dict(shirt='#f08a2c', pants='#3b4a6b'),
    'farmer':    dict(shirt='#c8463c', pants='#4d6fa0', apron='#7a8a52'),
}
HATS = ('helmet', 'sailor', 'cap', 'tophat', 'captain', 'cowboy', 'chef', 'hardhat', 'crown')
PROPS = ('bag', 'rock', 'phone', 'lantern', 'sword', 'paper', 'cup')
MOUTHS = ('closed', 'small', 'open', 'wide', 'O', 'smile_talk')
HAIRS = ('wild', 'tuft', 'swept')
GOGGLE_FRAME = '#e8892a'; HAIR_COL = '#8e94a4'
FACE_STYLE = 'house'                     # 'house' (videos 1-12) or 'ref' (the Director's reference look, 2026-11-25)
HAT_CLEAR = 50                                 # every hat stays above hy - HAT_CLEAR over the face (brows reach hy-49)
SHOE = (58, 48, 46); GOLD = (238, 192, 64); BELT = (52, 40, 36)

def _col(v, key):
    if v is None or v is False: return None
    return hexrgb(OUTFIT_DEFAULTS[key] if v is True else v)

# ---------------- skeleton ----------------
R = 98                                  # head radius -> ~5 heads tall
T = 50                                  # limb thickness
TB = 56                                 # torso thickness
OUT = 3.2                               # outline width
SEG_ARM, SEG_LEG = 124, 205

def _limb(root, ang, seg):              # ang = (upper, lower[, lower-length factor[, upper-length factor]])
    a1, a2 = math.radians(ang[0]), math.radians(ang[1]); seg2 = seg * (ang[2] if len(ang) > 2 else 1.0)
    seg1 = seg * (ang[3] if len(ang) > 3 else 1.0)       # < 1 = foreshortened (limb pointing at the viewer)
    j = (root[0] - math.sin(a1) * seg1, root[1] + math.cos(a1) * seg1)
    e = (j[0] - math.sin(a2) * seg2, j[1] + math.cos(a2) * seg2)
    return root, j, e

def _path(root, j, e, n=60):            # smooth quadratic through the joint
    cx, cy = 2 * j[0] - (root[0] + e[0]) / 2, 2 * j[1] - (root[1] + e[1]) / 2
    return [((1 - t) ** 2 * root[0] + 2 * (1 - t) * t * cx + t * t * e[0],
             (1 - t) ** 2 * root[1] + 2 * (1 - t) * t * cy + t * t * e[1]) for t in (i / n for i in range(n + 1))]

def _pose(pose):
    name = pose if isinstance(pose, str) else pose.get('_name', 'custom')
    P = POSES[pose] if isinstance(pose, str) else pose
    side = name in SIDE_POSES or (not isinstance(pose, str) and pose.get('_side', False))
    return name, P, side

def _rig(P, name):
    hip = (300, 520); shoulder = (300, 262)
    legs = [_limb(hip, P['legL'], SEG_LEG), _limb(hip, P['legR'], SEG_LEG)]
    if name == 'think':                    # each arm from its OWN shoulder (left arm from the left, right from the right)
        shx = P.get('_sh', (278, 322))      # shoulder x (animatable: 300,300 -> 278,322 while moving into the pose)
        arms = [_limb((shx[0], 262), P['armL'], SEG_ARM), _limb((shx[1], 262), P['armR'], SEG_ARM)]
    else:
        arms = [_limb(shoulder, P['armL'], SEG_ARM), _limb(shoulder, P['armR'], SEG_ARM)]
    return arms, legs

def _hand_frame(pts):                   # hand centre + unit forearm direction (elbow -> hand) from the path tangent
    e = pts[-1]; b = pts[-6]
    dx, dy = e[0] - b[0], e[1] - b[1]; n = math.hypot(dx, dy) or 1.0
    return e, (dx / n, dy / n)

# ---------------- props (local frame: v along the forearm / down, u across) ----------------
def _ell(cx, cy, rx, ry, a0=0, a1=360, n=36):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def _rrect(u0, v0, u1, v1, r, n=6):
    pts = []
    for cx, cy, a in ((u1 - r, v0 + r, -90), (u1 - r, v1 - r, 0), (u0 + r, v1 - r, 90), (u0 + r, v0 + r, 180)):
        pts += _ell(cx, cy, r, r, a, a + 90, n)
    return pts

PROP_MODE = {'sword': 'rigid', 'phone': 'rigid', 'paper': 'rigid', 'rock': 'rigid',
             'bag': 'hang', 'lantern': 'hang', 'cup': 'upright'}

def _prop_shapes(kind, mir):
    """Primitives in local coords: ('poly', pts, fill) with ink outline, ('line', pts, colour, width) for details.
    mir = +1/-1 flips u so the prop opens away from the body."""
    G = []
    def poly(p, c): G.append(('poly', [(u * mir, v) for u, v in p], c))
    def line(p, c, w): G.append(('line', [(u * mir, v) for u, v in p], c, w))
    if kind == 'sword':
        poly([(-11, 40), (11, 40), (11, 222), (0, 252), (-11, 222)], (214, 222, 232))
        line([(0, 50), (0, 218)], (168, 178, 192), 3)
        poly(_rrect(-34, 28, 34, 42, 5), GOLD)
        poly(_rrect(-8, -34, 8, 30, 4), (120, 72, 44))
        poly(_ell(0, -38, 11, 11), GOLD)
    elif kind == 'phone':
        poly(_rrect(-22, -18, 22, 72, 9), (44, 46, 58))
        poly(_rrect(-16, -8, 16, 60, 4), (120, 196, 240))
        line([(-8, 4), (8, 4)], (255, 255, 255), 3)
    elif kind == 'paper':
        poly([(-12, -14), (82, -14), (82, 100), (-12, 100)], (250, 248, 238))
        for k, v in enumerate((14, 32, 50, 68)): line([(6, v), (66 - 18 * (k == 3), v)], (150, 150, 162), 3)
    elif kind == 'rock':
        poly([(-30, -6), (-14, -30), (16, -32), (38, -12), (40, 22), (22, 44), (-14, 46), (-38, 24)], (138, 134, 128))
        line([(8, -16), (2, 2), (16, 14)], (100, 96, 92), 3)
    elif kind == 'bag':
        line(_ell(0, 16, 22, 30, 180, 360) , INK, 9); line(_ell(0, 16, 22, 30, 180, 360), (110, 70, 42), 5)
        poly(_rrect(-46, 14, 46, 104, 14), (150, 96, 56))
        poly([(-46, 22), (46, 22), (46, 50), (0, 62), (-46, 50)], (128, 80, 46))
        poly(_ell(0, 56, 7, 7), GOLD)
    elif kind == 'lantern':
        G.append(('ring', _ell(0, 0, 14, 14), INK))
        line([(0, 10), (0, 30)], INK, 4)
        poly([(-18, 30), (18, 30), (26, 42), (-26, 42)], (60, 58, 66))
        poly(_rrect(-24, 42, 24, 104, 6), (255, 208, 96))
        poly(_ell(0, 74, 9, 15), (255, 244, 200))
        for u in (-12, 12): line([(u, 44), (u, 102)], (60, 58, 66), 3)
        poly(_rrect(-28, 102, 28, 114, 4), (60, 58, 66))
    elif kind == 'cup':                    # upright mug held from the side; handle hidden in the fist
        poly([(10, -30), (66, -30), (62, 32), (14, 32)], (226, 88, 72))
        poly(_ell(38, -30, 28, 7), (92, 58, 40))
        line([(13, -8), (64, -8)], (255, 236, 222), 5)
    return G

def _prop_world(kind, anchor, fdir, mir):
    mode = PROP_MODE[kind]
    if mode == 'rigid': v = fdir
    else: v = (0.0, 1.0)                     # hanging and upright props keep gravity's direction
    u = (v[1], -v[0])
    def tf(p): return [(anchor[0] + a * u[0] + b * v[0], anchor[1] + a * u[1] + b * v[1]) for a, b in p]
    return [(g[0], tf(g[1])) + tuple(g[2:]) for g in _prop_shapes(kind, mir)]

def _props_of(prop, prop_hand):
    if not prop: return {}
    if isinstance(prop, dict): return {k: v for k, v in prop.items() if v}
    return {prop_hand: prop}

def _layout(P, name, props, fixed):
    """Skeleton in canvas coords (after grounding + centring), plus the props' world primitives."""
    arms, legs = _rig(P, name)
    lowest = max(max(p[1] for p in _path(*l)) for l in legs) + T / 2
    dy = 975 - lowest
    pre = {}
    for h, kind in props.items():
        pts = _path(*arms[0 if h == 'L' else 1]); a, f = _hand_frame(pts)
        pre[h] = _prop_world(kind, a, f, -1 if h == 'L' else 1)
    xs = [p[0] for l in legs + arms for p in _path(*l)] + [300 - R, 300 + R]
    xs += [x for g in pre.values() for prim in g for x, _ in prim[1]]
    dx = 0 if fixed else 300 - (min(xs) + max(xs)) / 2
    shift = lambda pts: [(x + dx, y + dy) for x, y in pts]
    world = {h: [(g[0], shift(g[1])) + tuple(g[2:]) for g in prims] for h, prims in pre.items()}
    return arms, legs, dx, dy, world

def hand_anchors(pose='stand', fixed=False, prop=None, prop_hand='R'):
    """{'L'/'R': (x, y, forearm_angle_deg)} in card pixels: the centre of each round hand and the forearm's
    direction (atan2 of elbow -> hand, 0 = pointing right, 90 = pointing down). Pass the same prop as draw()
    so auto-centring matches."""
    name, P, side = _pose(pose)
    arms, legs, dx, dy, _ = _layout(P, name, _props_of(prop, prop_hand), fixed)
    out = {}
    for h, a in zip('LR', arms):
        (x, y), (fx, fy) = _hand_frame(_path(*a))
        out[h] = (x + dx, y + dy, math.degrees(math.atan2(fy, fx)))
    return out

def draw(expr='neutral', pose='stand', color='#4a86e0', hat=None, look=0.0, fixed=False,
         shirt=None, coat=None, uniform=None, apron=None, pants=None, outfit=None,
         prop=None, prop_hand='R', mouth=None, goggles=None, hair=None, hat_col=None, glasses=None):
    # pose: a name from POSES, or a dict of joint angles (for animation); dict keys '_name' / '_side' set the style.
    # fixed=True keeps the hip at x=300 (no auto-centring) so animated frames don't jitter sideways.
    # Outfits: shirt / coat / uniform / apron / pants take a colour ('#rrggbb') or True for the default colour;
    #   outfit='chef' etc. applies a preset from OUTFITS (explicit keywords win).
    # prop: a name from PROPS held in prop_hand ('R' or 'L'), or a dict {'L': 'bag', 'R': 'sword'}.
    # mouth: a name from MOUTHS; replaces the expression's mouth (lip sync) and keeps its eyes and brows.
    # goggles: lab goggles pushed up on the forehead (True or a frame colour); never over the eyes.
    # hat_col: the cowboy hat's colour ('#rrggbb' or an rgb tuple; default tan).
    # hair: a name from HAIRS ('wild' = scientist tufts at the sides and top), True for 'wild', or (name, colour).
    name, P, side = _pose(pose)
    if side and look == 0.0: look = 0.7      # side-on body: face turns toward the direction of travel
    if outfit:
        pre = OUTFITS[outfit]
        shirt = shirt if shirt is not None else pre.get('shirt'); coat = coat if coat is not None else pre.get('coat')
        uniform = uniform if uniform is not None else pre.get('uniform'); apron = apron if apron is not None else pre.get('apron')
        pants = pants if pants is not None else pre.get('pants')
    cS, cC, cU, cA, cP = _col(shirt, 'shirt'), _col(coat, 'coat'), _col(uniform, 'uniform'), _col(apron, 'apron'), _col(pants, 'pants')
    props = _props_of(prop, prop_hand)

    C = hexrgb(color); hi = mixc(C, (255, 255, 255), 0.22)
    im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)

    arms, legs, dx, dy, propw = _layout(P, name, props, fixed)
    def mv(pts): return [(x + dx, y + dy) for x, y in pts]
    head = [300 + dx, 140 + dy]
    def X(x): return x + dx
    def Y(y): return y + dy

    def stamp(pts, w, col):
        r = w * S / 2
        for x, y in pts: d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=col)
    def lpts(l): return mv(_path(*l))

    # --- colour bands along a limb: [(f0, f1, colour)] over the path's index fraction, cut straight at inner ends
    tC = C
    sleeve = cC or cU or cS
    sleeve_to = 0.80 if (cC or cU) else 0.36
    trousers = cU or cP
    ARM_B = [(0.0, sleeve_to, sleeve)] if sleeve else []
    LEG_B = [(0.0, 0.88, trousers), (0.88, 1.0, SHOE)] if trousers else []
    torso_col = cC or cU or cS
    TORSO_B = []
    if torso_col:
        if cS and not (cC or cU):            # a shirt ends at a straight hem above the hip
            TORSO_B = [(0.0, 0.91, cS)] + ([(0.91, 1.0, cP)] if cP else [])
        else: TORSO_B = [(0.0, 1.0, torso_col)]
    elif cP: TORSO_B = [(0.91, 1.0, cP)]

    def cum(pts):
        L = [0.0]
        for a, b in zip(pts, pts[1:]): L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        return L
    def strip(pts, w, col):              # straight-ended band along a short run of points
        if len(pts) < 2: return
        l, r = [], []
        for i, p in enumerate(pts):
            a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, ty) or 1
            nx, ny = -ty / n * w / 2, tx / n * w / 2
            l.append(((p[0] + nx) * S, (p[1] + ny) * S)); r.append(((p[0] - nx) * S, (p[1] - ny) * S))
        d.polygon(l + r[::-1], fill=col)
    def band(pts, i0, i1, w, col, cut0, cut1):
        """fill pts[i0..i1] with col; ends flagged cut are straight (perpendicular), others round."""
        L = cum(pts); rr = w / 2
        a = L[i0] + (rr if cut0 else 0); b = L[i1] - (rr if cut1 else 0)
        stamp([p for p, l in zip(pts[i0:i1 + 1], L[i0:i1 + 1]) if a - 1e-6 <= l <= b + 1e-6], w, col)
        if cut0: strip([p for p, l in zip(pts, L) if L[i0] <= l <= a + 4], w, col)
        if cut1: strip([p for p, l in zip(pts, L) if b - 4 <= l <= L[i1]], w, col)
    def fill(pts, w, bands, i0=0, i1=None):
        """flat body colour over pts[i0..i1], then garment bands on top (straight cuts where a band ends mid-limb)."""
        n = len(pts) - 1; i1 = n if i1 is None else i1
        stamp(pts[i0:i1 + 1], w, tC)
        for f0, f1, col in bands:
            if col is None: continue
            j0, j1 = max(i0, round(f0 * n)), min(i1, round(f1 * n))
            if j1 <= j0: continue
            band(pts, j0, j1, w, col, j0 > i0, j1 < i1)

    def part(pts, w, bands, i0=0, i1=None):            # outline then fill, so front parts read over back parts
        i1 = len(pts) - 1 if i1 is None else i1
        stamp(pts[i0:i1 + 1], w + 2 * OUT, INK); fill(pts, w, bands, i0, i1)

    torso = mv([(300, 232 + i * (520 - 232) / 40) for i in range(41)])
    LA, RA = lpts(arms[0]), lpts(arms[1]); LL, RL = lpts(legs[0]), lpts(legs[1])

    # --- garment shapes that widen the silhouette (they join the merged outline)
    def sym(half, k_side=0.62, front=True):   # [(halfwidth, y), ...] -> closed polygon, symmetric about the body axis
        sh = look * 12 if (side and front) else 0.0   # side view: an apron sits on the front of the body
        k = k_side if side else 1.0                   # ... while a coat skirt spreads to cover both striding legs
        half = [(min(hw, 26) + max(0, hw - 26) * k, y) for hw, y in half]   # the top stays inside the torso tube (no step)
        left = [(X(300 - hw + sh), Y(y)) for hw, y in half]
        right = [(X(300 + hw + sh), Y(y)) for hw, y in half[::-1]]
        return left + right
    def leg_x(pts, y):                  # x where a leg path first crosses height y (None if it never does)
        for a, b in zip(pts, pts[1:]):
            if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
                return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
        return None
    sg = 1 if look >= 0 else -1                 # side-on: +1 faces right
    def stride_skirt(y0, y1, m0, flare, front_only=False, width=None):
        # side-on skirt that follows the stride: its edges track the outer edges of both thighs
        L, Rr = [], []
        for i in range(13):
            y = Y(y0 + (y1 - y0) * i / 12)
            xs_ = [x for x in (leg_x(LL, y), leg_x(RL, y)) if x is not None] or [X(300)]
            m = m0 + flare * i / 12
            lo, hi = min(xs_) - T / 2 - m, max(xs_) + T / 2 + m
            if i == 0: lo, hi = X(300) - 26, X(300) + 26
            if front_only:                      # an apron hangs from the waist in front: the back edge drops
                back = X(300) - sg * (8 + 6 * i / 12)          # almost straight down, the front drapes over the leading thigh
                front = max(xs_) + T / 2 + 5 if sg > 0 else min(xs_) - T / 2 - 5
                front = max(front, X(300) + 30) if sg > 0 else min(front, X(300) - 30)
                if i == 0: front = X(300) + sg * 26
                lo, hi = (back, front) if sg > 0 else (front, back)
            L.append((lo, y)); Rr.append((hi, y))
        hem = Y(y1) + 5
        return L + [((L[-1][0] + Rr[-1][0]) / 2, hem)] + Rr[::-1]
    skirts = []                          # (polygon, colour)
    if cC:
        skirts.append((stride_skirt(440, 680, 2, 12) if side else
                       sym([(26, 440), (30, 490), (38, 540), (49, 590), (60, 640), (68, 676), (52, 681), (26, 684), (0, 685)]), cC))
    if cA:
        skirts.append((stride_skirt(452, 696, 0, 4, True) if side else
                       sym([(24, 452), (31, 510), (42, 570), (52, 640), (58, 696), (42, 701), (20, 703), (0, 704)]), cA))

    def polyline_ink(pg): d.line([(x * S, y * S) for x, y in pg + pg[:1]], fill=INK, width=int(2 * OUT * S), joint='curve')
    def polyfill(pg, col): d.polygon([(x * S, y * S) for x, y in pg], fill=col)

    def draw_prop(h):
        for g in propw[h]:
            pts = [(x * S, y * S) for x, y in g[1]]
            if g[0] == 'poly':
                d.polygon(pts, fill=g[2]); d.line(pts + pts[:1], fill=INK, width=int(OUT * S), joint='curve')
            elif g[0] == 'line':
                d.line(pts, fill=g[2], width=int(g[3] * S), joint='curve')
            elif g[0] == 'ring':
                d.line(pts, fill=g[2], width=int(7 * S), joint='curve')
    def hand_over(pts):                 # redraw the fist over the prop's grip, seamless with the forearm
        stamp(pts[-12:], T + 2 * OUT, INK); fill(pts, T, ARM_B, len(pts) - 25)

    # a prop in the BACK hand of a side-on pose sits behind the whole body
    if side and 'R' in props: draw_prop('R')

    # --- back arm + legs + torso (+ garment skirts) as ONE merged silhouette (no inner seams), like the reference
    # Facing the viewer: both arms belong to the one merged silhouette (symmetric, nothing turned).
    # Side-on poses (walk/run) layer a back arm behind and a front arm over the torso.
    outl = [(RL, T), (LL, T), (torso, TB)] + ([(RA, T)] if side else [(LA, T), (RA, T)])
    for pts, w in outl: stamp(pts, w + 2 * OUT, INK)
    for pg, _ in skirts: polyline_ink(pg)
    if side: fill(RA, T, ARM_B)
    fill(RL, T, LEG_B); fill(LL, T, LEG_B)
    fill(torso, TB, TORSO_B)
    for pg, col in skirts: polyfill(pg, col)

    if not side:                             # both arms last, so hands read over a coat or apron
        fill(LA, T, ARM_B); fill(RA, T, ARM_B)
    # --- garment details inside the silhouette (darker garment tone, never black seams)
    def tone(c, k=0.32): return mixc(c, INK, k)
    def rect(x0, y0, x1, y1, col): d.rectangle([X(x0) * S, Y(y0) * S, X(x1) * S, Y(y1) * S], fill=col)
    def dot(x, y, r, col, ol=None):
        d.ellipse([(X(x) - r) * S, (Y(y) - r) * S, (X(x) + r) * S, (Y(y) + r) * S], fill=col,
                  outline=ol, width=int(2 * S) if ol else 0)
    sx = look * 7 if side else 0.0           # front details move a little toward the facing side
    if cA:                                   # bib (narrower than the torso), waist tie, pocket
        tA = tone(cA, 0.22)
        if side:                             # side-on: bib on the leading half of the torso, one strap
            b0, b1 = (300 - 6, 300 + TB / 2 - 3) if sg > 0 else (300 - TB / 2 + 3, 300 + 6)
            sx_ = (b0 + b1) / 2
            d.line([X(sx_) * S, Y(304) * S, X(300) * S, Y(230) * S], fill=INK, width=int(10 * S))
            d.line([X(sx_) * S, Y(304) * S, X(300) * S, Y(230) * S], fill=cA, width=int(4.5 * S))
        else:
            b0, b1 = 300 - 23, 300 + 23
            for e in (-1, 1):                # neck straps from the bib up under the head
                d.line([X(300 + e * 18) * S, Y(304) * S, X(300 + e * 9) * S, Y(230) * S], fill=INK, width=int(10 * S))
                d.line([X(300 + e * 18) * S, Y(304) * S, X(300 + e * 9) * S, Y(230) * S], fill=cA, width=int(4.5 * S))
        d.rounded_rectangle([X(b0) * S, Y(298) * S, X(b1) * S, Y(458) * S], radius=6 * S, fill=cA, outline=INK, width=int(2.6 * S))
        rect(300 - TB / 2, 452, 300 + TB / 2, 464, tA)
        if not side:
            d.rounded_rectangle([X(300 - 22) * S, Y(540) * S, X(300 + 22) * S, Y(584) * S], radius=5 * S, outline=tone(cA, 0.5), width=int(2.6 * S))
    if cU:                                   # buttons + belt with buckle
        for y in (300, 342, 384, 426): dot(300 + sx, y, 6, GOLD, tone(GOLD, 0.45))
        rect(300 - TB / 2, 470, 300 + TB / 2, 490, BELT)
        d.rounded_rectangle([X(300 - 11 + sx) * S, Y(467) * S, X(300 + 11 + sx) * S, Y(493) * S], radius=3 * S, fill=GOLD, outline=tone(GOLD, 0.5), width=int(2 * S))
        d.rectangle([X(300 - 4 + sx) * S, Y(474) * S, X(300 + 4 + sx) * S, Y(486) * S], fill=BELT)
    if cC:                                   # buttons + back vent of the coat skirt
        for y in (318, 380, 442): dot(300 + sx, y, 6, tone(cC, 0.45))
        d.line([X(300 + sx * 1.5) * S, Y(616) * S, X(300 + sx * 1.5) * S, Y(674) * S], fill=tone(cC), width=int(3 * S))
    if cS and not (cC or cU) and not cA:     # a placket line keeps a plain shirt from reading as a bare body band
        for y in (318, 372, 426): dot(300 + sx, y, 4.5, tone(cS, 0.28))

    if cC and not side:                      # collar V (light shirt showing) over the arm roots, under the head
        lc = cS or (236, 232, 222)
        d.polygon([(X(300 - 19 + sx) * S, Y(232) * S), (X(300 + 19 + sx) * S, Y(232) * S), (X(300 + sx) * S, Y(300) * S)], fill=lc)
        d.line([(X(300 - 19 + sx) * S, Y(232) * S), (X(300 + sx) * S, Y(300) * S), (X(300 + 19 + sx) * S, Y(232) * S)], fill=tone(cC, 0.45), width=int(3 * S))

    if name == 'think':
        # right upper arm down to its elbow, then the left arm whose forearm crosses the belly under that elbow,
        # then the right forearm rising in front to the chin
        n2 = len(RA) // 2
        part(RA, T, ARM_B, 0, n2)
        part(LA, T, ARM_B)
        stamp(RA[n2 + 3:], T + 2 * OUT, INK); fill(RA, T, ARM_B, n2 - 2)

    if side:                                  # front arm: outline only where it leaves the torso; fill from the root,
        # drawn before the head so a coloured sleeve root hides under it (no knot at the shoulder)
        stamp(LA[10:], T + 2 * OUT, INK); fill(LA, T, ARM_B)
    hx, hy = head
    front_hair = None
    if hair:                                  # hair tufts sit behind the head outline (only the tips show)
        hn, hc = (hair if isinstance(hair, (tuple, list)) else ('wild' if hair is True else hair, HAIR_COL))
        if hn not in HAIRS: raise ValueError(f'unknown hair {hn!r}; use one of {HAIRS}')
        hc = hexrgb(hc) if isinstance(hc, str) else tuple(hc)
        if hn == 'wild':                      # two side puffs above the ears + a spiky crown
            spikes = []
            for i in range(15):
                a = math.radians(200 + i * 140 / 14); rr = R + (30 if i % 2 else 8)
                spikes.append((hx + math.cos(a) * rr * 1.04, hy + math.sin(a) * rr))
            tufts = [spikes]
            for e in (-1, 1):
                tufts.append([(hx + e * (R - 18), hy - 70), (hx + e * (R + 34), hy - 64), (hx + e * (R + 22), hy - 44),
                              (hx + e * (R + 42), hy - 28), (hx + e * (R + 20), hy - 14), (hx + e * (R + 30), hy + 4),
                              (hx + e * (R - 14), hy - 6)])
        elif hn == 'swept':                   # drawn over the head after it (a cap of hair with a side part)
            tufts = []; front_hair = hc
        else:                                  # 'tuft': one swept quiff on top
            tufts = [[(hx - 60, hy - 70), (hx - 40, hy - R - 34), (hx - 4, hy - R - 18), (hx + 30, hy - R - 46),
                      (hx + 40, hy - R - 10), (hx + 70, hy - 60)]]
        for tp in tufts:
            q = [(x * S, y * S) for x, y in tp]
            d.line(q + q[:1], fill=INK, width=int(2 * OUT * S), joint='curve'); d.polygon(q, fill=hc)
    d.ellipse([(hx - R - OUT) * S, (hy - R - OUT) * S, (hx + R + OUT) * S, (hy + R + OUT) * S], fill=INK)
    d.ellipse([(hx - R) * S, (hy - R) * S, (hx + R) * S, (hy + R) * S], fill=C)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse([(hx - R) * S, (hy - R) * S, (hx + R) * S, (hy + R) * S], fill=255)
    cap = Image.new('L', im.size, 0); ImageDraw.Draw(cap).ellipse([(hx - R * 1.25) * S, (hy - R * 1.9) * S, (hx + R * 1.25) * S, (hy + R * 0.15) * S], fill=150)
    cap = ImageChops.multiply(cap.filter(ImageFilter.GaussianBlur(26 * S)), m)
    lay = Image.new('RGBA', im.size, hi + (255,)); lay.putalpha(cap); im.alpha_composite(lay); d = ImageDraw.Draw(im)
    if front_hair is not None:               # 'swept': a hair cap over the crown, fringe swept to one side, a part line
        pts = []
        for i in range(25):
            a = math.radians(196 + i * 148 / 24); pts.append((hx + math.cos(a) * (R + OUT * .5), hy + math.sin(a) * (R + OUT * .5)))
        fr = [(hx + R * .97, hy - R * .22), (hx + R * .55, hy - R * .5), (hx + R * .12, hy - R * .44), (hx - R * .2, hy - R * .58),
              (hx - R * .6, hy - R * .5), (hx - R * .96, hy - R * .25)]
        poly = [(x * S, y * S) for x, y in pts + fr]
        d.polygon(poly, fill=front_hair); d.line(poly + poly[:1], fill=INK, width=int(2 * OUT * S), joint='curve')
        d.line([((hx - R * .2) * S, (hy - R * .58) * S), ((hx - R * .05) * S, (hy - R * .95) * S)], fill=INK, width=int(1.4 * OUT * S))
        d.arc([(hx - R * .9) * S, (hy - R * 1.0) * S, (hx + R * .2) * S, (hy - R * .2) * S], 200, 300, fill=mixc(front_hair, (255, 255, 255), .35) + (255,), width=int(2.2 * OUT * S))

    # ---------------- face ----------------
    K = (16, 14, 22, 255); WH = (255, 255, 255, 255); TONGUE = (225, 95, 105, 255)
    fx = hx + look * 34; ey = hy + 2; my = hy + 48
    gap = 34
    late = []                                # face details drawn after the hat (sweat drops)
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
    def happy_mouth():
        d.chord([(fx - 30) * S, (my - 22) * S, (fx + 30) * S, (my + 26) * S], 0, 180, fill=K)
        d.chord([(fx - 18) * S, (my + 6) * S, (fx + 18) * S, (my + 24) * S], 0, 180, fill=TONGUE)
    def M(fn):                               # the expression's own mouth, unless a lip-sync mouth overrides it
        if mouth is None: fn()


    def ref_face():
        """The 'ref' face style (2026-11-25, the Director's reference look): small white eyes with a black rim and a
        dark pupil set close together, heavy half-lids for calm/smug looks, short thick rounded brows, a small mouth,
        no nose. Sizes scale with the head radius R (bigger heads in the chibi proportions)."""
        k = R / 98.0
        g = 30 * k; ery = 18 * k; erx = 17 * k; pr = 8 * k
        cy = hy + 8 * k; mY = hy + 52 * k; cx0 = hx + look * 30 * k
        L, Rr = cx0 - g, cx0 + g
        lw_ = max(3, int(3.6 * k))
        def eye(cx, lid=0.0, size=1.0, pup=(0.0, 0.0), pupil=True):
            rx, ry = erx * size, ery * size
            box_ = [(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S]
            d.ellipse(box_, fill=WH, outline=K, width=lw_ * S)
            if pupil:
                px, py = cx + (look * 5 + pup[0]) * k, cy + (2 + pup[1]) * k
                d.ellipse([(px - pr * size ** .5) * S, (py - pr * size ** .5) * S, (px + pr * size ** .5) * S, (py + pr * size ** .5) * S], fill=K)
            if lid > 0:                      # upper lid: head-coloured cover + a thick lid line
                yl = cy - ry + 2 * ry * lid
                d.rectangle([(cx - rx - 3) * S, (cy - ry - 4) * S, (cx + rx + 3) * S, yl * S], fill=C)
                d.line([(cx - rx - 2 * k) * S, yl * S, (cx + rx + 2 * k) * S, yl * S], fill=K, width=int(5 * k) * S)
        def brow(cx, tilt, dy=-31, w=10.5, ln=16):
            y0 = cy + dy * k
            d.line([(cx - ln * k) * S, (y0 - tilt * k) * S, (cx + ln * k) * S, (y0 + tilt * k) * S], fill=K, width=int(w * k) * S)
            for (ex, ey_) in ((cx - ln * k, y0 - tilt * k), (cx + ln * k, y0 + tilt * k)):
                rr = w * k / 2; d.ellipse([(ex - rr) * S, (ey_ - rr) * S, (ex + rr) * S, (ey_ + rr) * S], fill=K)
        def pill(w, h, dy=0, col=K):
            d.rounded_rectangle([(cx0 - w * k) * S, (mY + dy - h * k) * S, (cx0 + w * k) * S, (mY + dy + h * k) * S], radius=int(h * k) * S, fill=col)
        def grin(w=23, h=14):
            box_ = [(cx0 - w * k) * S, (mY - h * k) * S, (cx0 + w * k) * S, (mY + h * k) * S]
            d.chord(box_, 0, 180, fill=WH, outline=K, width=lw_ * S)
            d.line([(cx0 - (w - 3) * k) * S, (mY + 1 * k) * S, (cx0 + (w - 3) * k) * S, (mY + 1 * k) * S], fill=K, width=max(2, int(2.5 * k)) * S)
        def smirk():
            d.arc([(cx0 - 12 * k) * S, (mY - 12 * k) * S, (cx0 + 14 * k) * S, (mY + 6 * k) * S], 25, 140, fill=K, width=int(5 * k) * S)
        if expr in ('neutral', 'blink'):
            if expr == 'blink': eye(L, 1.0); eye(Rr, 1.0)
            else: eye(L, .38); eye(Rr, .38)
            brow(L, 0, -25, 7.5); brow(Rr, 0, -25, 7.5)
            M(lambda: pill(13, 5))
        elif expr == 'smug':
            eye(L, .5); eye(Rr, .5); brow(L, 3, -21, 8); brow(Rr, -4, -26, 8)
            M(lambda: pill(18, 6))
        elif expr in ('happy', 'blink_happy'):
            eye(L, .18 if expr == 'happy' else 1.0); eye(Rr, .18 if expr == 'happy' else 1.0)
            brow(L, -2, -27, 7); brow(Rr, 2, -27, 7)
            M(grin)
        elif expr == 'angry':
            eye(L, .42); eye(Rr, .42); brow(L, 6, -20, 9); brow(Rr, -6, -20, 9)
            M(lambda: teeth(cx0 - 24 * k, cx0 + 25 * k, mY, 18 * k, 0.1))
        elif expr == 'surprised':
            eye(L, 0, 1.18); eye(Rr, 0, 1.18); brow(L, -3, -34, 7); brow(Rr, 3, -34, 7)
            M(lambda: d.ellipse([(cx0 - 7 * k) * S, (mY - 7 * k) * S, (cx0 + 7 * k) * S, (mY + 10 * k) * S], fill=K))
        elif expr == 'scared':
            eye(L, 0, 1.22, pupil=True); eye(Rr, 0, 1.22); brow(L, -6, -35, 7); brow(Rr, 6, -35, 7)
            M(lambda: teeth(cx0 - 20 * k, cx0 + 20 * k, mY + 3 * k, 15 * k, -0.05))
        elif expr == 'worried':
            eye(L, .12); eye(Rr, .12); brow(L, -6, -28, 7.5); brow(Rr, 6, -28, 7.5)
            M(lambda: d.arc([(cx0 - 12 * k) * S, (mY - 1 * k) * S, (cx0 + 12 * k) * S, (mY + 14 * k) * S], 200, 340, fill=K, width=int(5 * k) * S))
            late.append(lambda: d.ellipse([(hx + R - 38 * k) * S, (hy - 62 * k) * S, (hx + R - 22 * k) * S, (hy - 38 * k) * S], fill=(160, 215, 255, 255)))
        elif expr == 'sad':
            eye(L, .3, pup=(0, 3)); eye(Rr, .3, pup=(0, 3)); brow(L, -5, -24, 7); brow(Rr, 5, -24, 7)
            M(lambda: d.arc([(cx0 - 11 * k) * S, (mY + 1 * k) * S, (cx0 + 11 * k) * S, (mY + 15 * k) * S], 200, 340, fill=K, width=int(5 * k) * S))
        elif expr == 'thinking':
            eye(L, .3, pup=(4, -4)); eye(Rr, .3, pup=(4, -4)); brow(L, 0, -27, 7.5); brow(Rr, -5, -32, 7.5)
            M(lambda: d.line([(cx0 - 3 * k) * S, (mY + 2 * k) * S, (cx0 + 12 * k) * S, (mY - 2 * k) * S], fill=K, width=int(5 * k) * S))
        elif expr == 'determined':
            eye(L, .45); eye(Rr, .45); brow(L, 5, -21, 9); brow(Rr, -5, -21, 9)
            M(lambda: pill(11, 3.5))
        else:
            eye(L, .38); eye(Rr, .38); M(lambda: pill(9, 4))
        if glasses:
            gc = K if glasses is True else hexrgb(glasses) + (255,)
            for cx in (L, Rr):
                rr = ery * 1.25
                d.ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], outline=gc, width=max(3, int(3.2 * k)) * S)
            d.line([(L + ery * 1.25) * S, cy * S, (Rr - ery * 1.25) * S, cy * S], fill=gc, width=max(3, int(3.2 * k)) * S)

    eL, eR = fx - gap, fx + gap
    if FACE_STYLE == 'ref':
        ref_face()
    else:
        if expr == 'neutral':
            eye(eL, 'dot'); eye(eR, 'dot')
            M(lambda: d.line([(fx - 16) * S, my * S, (fx + 16) * S, my * S], fill=K, width=5 * S))
        elif expr == 'happy':
            eye(eL, 'happy'); eye(eR, 'happy'); M(happy_mouth)
        elif expr == 'angry':
            eye(eL, 'dot', 22); eye(eR, 'dot', 22); brow(eL, 8, -26, 8); brow(eR, -8, -26, 8)
            M(lambda: teeth(fx - 34, fx + 36, my, 26, 0.1))
        elif expr == 'surprised':
            eye(eL, 'wide'); eye(eR, 'wide'); brow(eL, -3, -38, 5); brow(eR, 3, -38, 5)
            M(lambda: d.ellipse([(fx - 12) * S, (my - 10) * S, (fx + 12) * S, (my + 22) * S], fill=K))
        elif expr == 'worried':
            eye(eL, 'dot'); eye(eR, 'dot'); brow(eL, -7, -28); brow(eR, 7, -28)
            M(lambda: d.arc([(fx - 20) * S, (my - 2) * S, (fx + 20) * S, (my + 24) * S], 200, 340, fill=K, width=5 * S))
            late.append(lambda: d.ellipse([(hx + R - 38) * S, (hy - 62) * S, (hx + R - 22) * S, (hy - 38) * S], fill=(160, 215, 255, 255),
                                          outline=(16, 14, 22, 255) if hat else None, width=int(2 * S) if hat else 0))
        elif expr == 'smug':
            eye(eL, 'flat'); eye(eR, 'flat'); brow(eL, 0, -22, 5); brow(eR, -6, -28, 5)
            M(lambda: d.arc([(fx - 14) * S, (my - 18) * S, (fx + 26) * S, (my + 6) * S], 20, 120, fill=K, width=5 * S))
        elif expr == 'scared':
            eye(eL, 'wide'); eye(eR, 'wide'); brow(eL, -8, -40, 5); brow(eR, 8, -40, 5)
            M(lambda: teeth(fx - 30, fx + 30, my + 4, 22, -0.05))
        elif expr == 'sad':
            eye(eL, 'dot', 20); eye(eR, 'dot', 20); brow(eL, -6, -24, 5); brow(eR, 6, -24, 5)
            M(lambda: d.arc([(fx - 18) * S, (my + 2) * S, (fx + 18) * S, (my + 26) * S], 200, 340, fill=K, width=5 * S))
            d.ellipse([(eL - 5) * S, (ey + 18) * S, (eL + 5) * S, (ey + 34) * S], fill=(140, 200, 255, 255))
        elif expr == 'thinking':               # eyes glance up-right, one brow raised, small skewed mouth
            for cx in (eL, eR): d.ellipse([(cx + 2) * S, (ey - 20) * S, (cx + 20) * S, (ey + 4) * S], fill=K)
            brow(eL, 0, -32, 6); brow(eR, -6, -40, 6)
            M(lambda: d.line([(fx - 4) * S, (my + 4) * S, (fx + 20) * S, (my - 2) * S], fill=K, width=5 * S))
        elif expr in ('blink', 'blink_happy'):  # eyes closed for one or two frames
            eye(eL, 'flat'); eye(eR, 'flat')
            if expr == 'blink':
                M(lambda: d.line([(fx - 16) * S, my * S, (fx + 16) * S, my * S], fill=K, width=5 * S))
            else: M(happy_mouth)
        elif expr == 'determined':
            eye(eL, 'squint'); eye(eR, 'squint'); brow(eL, 6, -20, 8); brow(eR, -6, -20, 8)
            M(lambda: d.line([(fx - 18) * S, (my + 2) * S, (fx + 18) * S, (my - 2) * S], fill=K, width=6 * S))

    # ---------------- lip-sync mouths (same anchor and similar size, so they swap cleanly) ----------------
    if mouth == 'closed':
        d.line([(fx - 15) * S, (my + 1) * S, (fx + 15) * S, (my + 1) * S], fill=K, width=5 * S)
    elif mouth == 'small':
        d.ellipse([(fx - 12) * S, (my - 5) * S, (fx + 12) * S, (my + 8) * S], fill=K)
    elif mouth == 'open':
        d.ellipse([(fx - 18) * S, (my - 10) * S, (fx + 18) * S, (my + 20) * S], fill=K)
        d.chord([(fx - 11) * S, (my + 6) * S, (fx + 11) * S, (my + 20) * S], 180, 360, fill=TONGUE)
    elif mouth == 'wide':
        d.rounded_rectangle([(fx - 30) * S, (my - 12) * S, (fx + 30) * S, (my + 20) * S], radius=13 * S, fill=K)
        d.chord([(fx - 26) * S, (my - 10) * S, (fx + 26) * S, (my + 2) * S], 180, 360, fill=WH)
        d.chord([(fx - 14) * S, (my + 8) * S, (fx + 14) * S, (my + 22) * S], 180, 360, fill=TONGUE)
    elif mouth == 'O':
        d.ellipse([(fx - 13) * S, (my - 13) * S, (fx + 13) * S, (my + 21) * S], fill=K)
        d.ellipse([(fx - 6) * S, (my - 4) * S, (fx + 6) * S, (my + 12) * S], fill=(92, 30, 40, 255))
    elif mouth == 'smile_talk':
        d.chord([(fx - 26) * S, (my - 16) * S, (fx + 26) * S, (my + 22) * S], 0, 180, fill=K)
        d.chord([(fx - 14) * S, (my + 8) * S, (fx + 14) * S, (my + 20) * S], 0, 180, fill=TONGUE)
    elif mouth is not None:
        raise ValueError(f'unknown mouth {mouth!r}; use one of {MOUTHS}')

    # ---------------- hats (nothing below hy - HAT_CLEAR over the face) ----------------
    def hp(pts): return [((hx + u) * S, (hy + v) * S) for u, v in pts]
    def hpoly(pts, col, ol=True):
        q = hp(pts); d.polygon(q, fill=col)
        if ol: d.line(q + q[:1], fill=INK, width=int(OUT * S), joint='curve')
    def hline(pts, col, w): d.line(hp(pts), fill=col, width=int(w * S), joint='curve')
    lk = max(-1.0, min(1.0, look))
    if goggles:                               # lab goggles up on the forehead: strap across, two lenses above the brows
        gf = hexrgb(GOGGLE_FRAME if goggles is True else goggles); gy = -78
        hw = math.sqrt(max(0.0, R * R - gy * gy)) - 1
        hline([(-hw, gy + 4), (-hw * .5, gy - 2), (hw * .5, gy - 2), (hw, gy + 4)], INK, 15)
        hline([(-hw, gy + 4), (-hw * .5, gy - 2), (hw * .5, gy - 2), (hw, gy + 4)], tone(gf, 0.35), 9)
        gx = lk * 20
        for e in (-1, 1):
            u = gx + e * 30
            q = hp(_rrect(u - 26, gy - 20, u + 26, gy + 16, 12)); d.polygon(q, fill=gf); d.line(q + q[:1], fill=INK, width=int(OUT * S), joint='curve')
            q = hp(_rrect(u - 18, gy - 13, u + 18, gy + 9, 8)); d.polygon(q, fill=(150, 220, 246)); d.line(q + q[:1], fill=INK, width=int(2 * S), joint='curve')
            hline([(u - 10, gy - 6), (u - 2, gy - 10)], (255, 255, 255), 4)
        hline([(gx - 4, gy - 2), (gx + 4, gy - 2)], INK, 8)
    if hat == 'helmet':
        G = (78, 112, 64); Gd = (52, 78, 44); band_c = (70, 52, 56)
        top = hy - R - 30; rim = hy - 34
        d.chord([(hx - R - 12 - OUT) * S, (top - OUT) * S, (hx + R + 12 + OUT) * S, (rim + (rim - top) + OUT) * S], 180, 360, fill=INK)
        d.chord([(hx - R - 12) * S, top * S, (hx + R + 12) * S, (rim + (rim - top)) * S], 180, 360, fill=G)
        d.rounded_rectangle([(hx - R - 26) * S, (rim - 6) * S, (hx + R + 26) * S, (rim + 12) * S], radius=9 * S, fill=Gd, outline=INK, width=int(OUT * S))
        d.line([(hx - R - 4) * S, (rim - 22) * S, (hx + R + 4) * S, (rim - 22) * S], fill=band_c, width=10 * S)
    elif hat == 'sailor':
        d.rounded_rectangle([(hx - 74) * S, (hy - R - 22) * S, (hx + 74) * S, (hy - R + 26) * S], radius=18 * S, fill=(244, 244, 240, 255), outline=INK, width=int(OUT * S))
        d.rectangle([(hx - 76) * S, (hy - R + 12) * S, (hx + 76) * S, (hy - R + 28) * S], fill=(38, 52, 104, 255))
    elif hat == 'cap':
        Cc = (214, 64, 58); Cd = tone(Cc, 0.28)
        hpoly(_ell(0, -58, 100, 50, 180, 360) + [(100, -58), (-100, -58)], Cc)        # crown: half-dome ending at hy-58
        hline([(0, -107), (0, -60)], Cd, 3); hline(_ell(0, -58, 52, 48, 205, 335), Cd, 3)
        if abs(lk) < 0.35:                                                            # visor seen from the front
            hpoly(_ell(lk * 30, -58, 82, 9, 0, 180) + [(-82 + lk * 30, -58)], Cd)
        else:                                                                         # visor in profile, toward the look
            s = 1 if lk > 0 else -1
            hpoly([(s * 40, -66), (s * 150, -60), (s * 152, -54), (s * 40, -54)], Cd)
        hpoly(_ell(0, -108, 9, 6), Cd)
    elif hat == 'tophat':
        Tc = (50, 48, 60); Tb = (186, 52, 60)
        hpoly([(-52, -66), (-58, -150), (58, -150), (52, -66)], Tc)
        hpoly([(-53.5, -96), (53.5, -96), (52.5, -78), (-52.5, -78)], Tb)
        hpoly(_ell(0, -68, 98, 10), Tc)
    elif hat == 'captain':
        Wc = (246, 246, 242); Nv = (34, 42, 76)
        hpoly(_ell(0, -104, 106, 24), Wc)                                              # white top seen from below
        hpoly(_rrect(-84, -96, 84, -64, 6), Nv)                                        # dark band
        hline([(-80, -72), (80, -72)], GOLD, 4)                                        # braid
        hpoly(_ell(0, -64, 70, 13, 0, 180) + [(-70, -64)], (24, 24, 30))               # visor, bottom at hy-51
        hpoly(_ell(0, -96, 14, 16), GOLD)                                              # badge
    elif hat == 'cowboy':
        Cb = hexrgb(hat_col) if hat_col else (196, 140, 82); Cbd = tone(Cb, 0.3)
        hpoly([(-60, -76), (-54, -138), (-22, -150), (0, -138), (22, -150), (54, -138), (60, -76)], Cb)
        hpoly([(-59, -96), (59, -96), (60, -80), (-60, -80)], Cbd)
        top = [(x, -64 - 34 * (x / 150) ** 2 - 12) for x in range(-150, 151, 10)]
        bot = [(x, -56 - 34 * (x / 150) ** 2) for x in range(150, -151, -10)]
        hpoly(top + bot, Cb)
    elif hat == 'chef':
        Wc = (255, 255, 255); Wd = (196, 198, 208)
        puffs = [(-46, -104, 38), (46, -104, 38), (0, -112, 40)]
        for u, v, r in puffs: d.ellipse([(hx + u - r - OUT) * S, (hy + v - r - OUT) * S, (hx + u + r + OUT) * S, (hy + v + r + OUT) * S], fill=INK)
        for u, v, r in puffs: d.ellipse([(hx + u - r) * S, (hy + v - r) * S, (hx + u + r) * S, (hy + v + r) * S], fill=Wc)
        hpoly(_rrect(-74, -88, 74, -56, 6), Wc)
        for u in (-40, 0, 40): hline([(u, -84), (u, -60)], Wd, 3)
        hline(_ell(-46, -104, 22, 20, 200, 260), Wd, 3); hline(_ell(46, -104, 22, 20, 280, 340), Wd, 3)
    elif hat == 'hardhat':
        Y_ = (246, 196, 44); Yd = tone(Y_, 0.22)
        hpoly(_ell(0, -66, 92, 80, 180, 360) + [(92, -66), (-92, -66)], Y_)
        hpoly([(-14, -145), (14, -145), (16, -68), (-16, -68)], mixc(Y_, (255, 255, 255), 0.3))
        hpoly(_rrect(-112, -72, 112, -56, 7), Yd)
    elif hat == 'crown':
        Gd_ = tone(GOLD, 0.25)
        pts = [(-72, -62), (-80, -132), (-48, -98), (-26, -142), (0, -104), (26, -142), (48, -98), (80, -132), (72, -62)]
        hpoly(pts, GOLD)
        hpoly([(-74.5, -86), (74.5, -86), (72, -62), (-72, -62)], Gd_)
        for u, v in ((-80, -132), (-26, -142), (26, -142), (80, -132)): hpoly(_ell(u, v, 8, 8), GOLD)
        hpoly(_ell(0, -74, 9, 8), (220, 50, 70)); hpoly(_ell(-40, -74, 7, 6), (60, 120, 220)); hpoly(_ell(40, -74, 7, 6), (60, 120, 220))
    elif hat is not None:
        raise ValueError(f'unknown hat {hat!r}; use one of {HATS}')
    for f in late: f()

    if name == 'think':                    # hand over the chin, seamlessly joined to the forearm drawn earlier
        stamp(RA[-12:], T + 2 * OUT, INK); fill(RA, T, ARM_B, len(RA) - 25)

    # ---------------- held props: grip at the hand centre, the fist redrawn over the grip ----------------
    for h in props:
        if h not in ('L', 'R'): raise ValueError('prop hand must be L or R')
        if props[h] not in PROPS: raise ValueError(f'unknown prop {props[h]!r}; use one of {PROPS}')
        if side and h == 'R': continue        # already drawn behind the body
        draw_prop(h); hand_over(LA if h == 'L' else RA)
    out = im.resize((W, H), Image.LANCZOS)
    out.info['head'] = (hx, hy)              # the true head centre (card px); alpha-based guesses fail when hands are raised above the head
    return out

if __name__ == '__main__':
    a = sys.argv
    pos = [x for x in a[2:] if '=' not in x]; kw = dict(x.split('=', 1) for x in a[2:] if '=' in x)
    draw(pos[0] if len(pos) > 0 else 'neutral', pos[1] if len(pos) > 1 else 'stand',
         pos[2] if len(pos) > 2 else '#4a86e0', pos[3] if len(pos) > 3 and pos[3] != 'none' else None,
         float(pos[4]) if len(pos) > 4 else 0.0, **kw).save(a[1])

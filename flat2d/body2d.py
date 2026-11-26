"""Purpose-drawn 2D figures from joint positions + natural-motion helpers (video 13 fix pass 2).

The stickman cards (stickman.draw) are posed by joint ANGLES on an upright card, so lying, kneeling or sprawled bodies
end up as rotated standing cards. `figure` instead draws the round-body stickman (egg torso, round-capped limbs with a
black outline, the card's head pasted on top) from screen-space JOINTS, so any pose can be drawn on purpose:
prone with the head turned, kneeling astride, propped on one elbow, sliding on the back, or a leg chain solved by IK so
the feet plant exactly on a 3D tread (`stair_descent`).

Proportions (metres, the 1.75 m big-head card, 930 card px = 1.75 m): head radius .248, neck->pelvis .54, upper/lower
arm .21, thigh/shin .41, limb width .094, torso half width .10. Callers give k = px per metre.

Natural-motion data used here (LESSONS.md > Natural motion): stair descent = the support knee flexes to lower the
body while the lead foot reaches down toe-first (ankle plantar-flexed ~20 deg), contact, the heel settles ~.15 s
later, the pelvis dips ~3 cm past the new tread then recovers; the trunk leans a little forward (5-10 deg), the head
pitches down 20-30 deg toward the next treads; the hand on the wall/rail slides with a lag. A creep is ~1.2 s per
step with a held double-support pause (weight on both feet) between steps.
"""
import math
from PIL import Image, ImageDraw

INK = (22, 20, 28)
HEAD_R, TORSO, ARM, THIGH, SHIN, LIMB_W, TORSO_HW = .248, .54, .23, .41, .41, .12, .17


def shade(c, k): return tuple(int(max(0, min(255, v * k))) for v in c[:3])
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def sm(t): t = clamp(t); return t * t * (3 - 2 * t)
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= b)
def lerp(a, b, t): return a + (b - a) * t
def lerpv(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
def add(a, b, s=1.0): return tuple(x + y * s for x, y in zip(a, b))


def polar(p, ang, L):
    """Screen point L px from p at angle ang (deg; 0 = right, 90 = down)."""
    a = math.radians(ang); return (p[0] + L * math.cos(a), p[1] + L * math.sin(a))


def ik2(root, target, l1, l2, bend=1):
    """Two-bone IK in the screen plane: returns (joint, end). bend = +1 / -1 picks the side the joint goes."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = max(abs(l1 - l2) + 1e-3, min(math.hypot(dx, dy), l1 + l2 - 1e-3))
    a = math.atan2(dy, dx)
    b = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    j = (root[0] + l1 * math.cos(a + bend * b), root[1] + l1 * math.sin(a + bend * b))
    return j, (root[0] + d * math.cos(a), root[1] + d * math.sin(a))


def ik3(root, target, l1, l2, pole):
    """Two-bone IK in 3D: the joint bends toward the pole direction (e.g. the knee forward). Returns (joint, end)."""
    v = tuple(b - a for a, b in zip(root, target)); D = math.sqrt(sum(c * c for c in v)) or 1e-6
    d = max(abs(l1 - l2) + 1e-3, min(D, l1 + l2 - 1e-3)); u = tuple(c / D for c in v)
    pd = sum(p * c for p, c in zip(pole, u)); w = tuple(p - pd * c for p, c in zip(pole, u))
    wn = math.sqrt(sum(c * c for c in w)) or 1e-6; w = tuple(c / wn for c in w)
    x = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = math.sqrt(max(0.0, l1 * l1 - x * x))
    j = tuple(r + u_ * x + w_ * h for r, u_, w_ in zip(root, u, w))
    return j, tuple(r + u_ * d for r, u_ in zip(root, u))


def _qpath(p0, j, e, n=16):
    if n: return [p0, j, e]                                    # a crisp joint (the line join rounds it)
    cx, cy = 2 * j[0] - (p0[0] + e[0]) / 2, 2 * j[1] - (p0[1] + e[1]) / 2
    cx, cy = lerp(j[0], cx, .8), lerp(j[1], cy, .8)          # a soft bend, not a hinge
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t * t * e[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * e[1]) for t in (i / n for i in range(n + 1))]


def limb(d, p0, j, e, w, col, o, stripes=None):
    """A round-capped limb through its joint (shoulder-elbow-hand / hip-knee-ankle) with a black outline."""
    pts = _qpath(p0, j, e)
    d.line(pts, fill=INK, width=int(w + 2 * o), joint='curve')
    for p in (p0, e): d.ellipse((p[0] - w / 2 - o, p[1] - w / 2 - o, p[0] + w / 2 + o, p[1] + w / 2 + o), fill=INK)
    d.line(pts, fill=col, width=int(w), joint='curve')
    for p in (p0, e): d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=col)
    if stripes:
        for jj in (-.27, .27):
            q = []
            for i in range(len(pts)):
                a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
                L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1; nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
                q.append((pts[i][0] + nx * w * jj, pts[i][1] + ny * w * jj))
            d.line(q[1:-1], fill=stripes, width=max(1, int(w * .09)), joint='curve')


def torso(d, top, bot, hw, col, o, stripes=None, zip_=None, back=False):
    """The egg torso from top (neck) to bot (pelvis): widest at ~60 %, rounded ends."""
    L = math.hypot(bot[0] - top[0], bot[1] - top[1]) or 1
    ux, uy = (bot[0] - top[0]) / L, (bot[1] - top[1]) / L; nx, ny = -uy, ux
    prof = [(0, .42), (.08, .78), (.25, .95), (.55, 1.0), (.8, .93), (.95, .7), (1.0, .35), (1.04, 0)]
    side1 = [(top[0] + ux * L * t + nx * hw * f, top[1] + uy * L * t + ny * hw * f) for t, f in prof]
    side2 = [(top[0] + ux * L * t - nx * hw * f, top[1] + uy * L * t - ny * hw * f) for t, f in prof][::-1]
    cap = [(top[0] - ux * hw * .45 * math.sin(a) + nx * hw * .42 * math.cos(a), top[1] - uy * hw * .45 * math.sin(a) + ny * hw * .42 * math.cos(a))
           for a in [math.pi * (i / 8) for i in range(1, 8)]][::-1]
    poly = side1 + side2 + cap
    d.polygon(poly, fill=INK); d.line(poly + poly[:1], fill=INK, width=int(2 * o), joint='curve')
    d.polygon(poly, fill=col)
    if stripes:
        for jj in (-.62, -.31, .31, .62):
            d.line([(top[0] + ux * L * .1 + nx * hw * jj, top[1] + uy * L * .1 + ny * hw * jj),
                    (top[0] + ux * L * .95 + nx * hw * jj * .9, top[1] + uy * L * .95 + ny * hw * jj * .9)], fill=stripes, width=max(1, int(hw * .09)))
    if zip_:
        d.line([(top[0] + ux * L * .12, top[1] + uy * L * .12), (top[0] + ux * L * .92, top[1] + uy * L * .92)], fill=zip_, width=max(1, int(hw * .08)))
    if back:
        d.line([(top[0] + ux * L * .12, top[1] + uy * L * .12), (top[0] + ux * L * .88, top[1] + uy * L * .88)], fill=shade(col, .75), width=max(1, int(hw * .06)))
    return poly


def foot(d, ank, toe, w, col, o):
    d.line([ank, toe], fill=INK, width=int(w + 2 * o))
    for p in (ank, toe): d.ellipse((p[0] - w / 2 - o, p[1] - w / 2 - o, p[0] + w / 2 + o, p[1] + w / 2 + o), fill=INK)
    d.line([ank, toe], fill=col, width=int(w))
    for p in (ank, toe): d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=col)


def hand(d, p, r, col, o):
    d.ellipse((p[0] - r - o, p[1] - r - o, p[0] + r + o, p[1] + r + o), fill=INK)
    d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col)


def figure(lay, J, k, style, order=None):
    """Draw a figure from screen joints J (px): head, neck, pelvis, shL elL haL, shR elR haR, hipL knL anL toeL, hipR
    knR anR toeR. k = px per metre (widths). style: dict(top, bottom, skin, feet (None = barefoot skin), stripes,
    zip, back, head=callable(lay, J, k), dim (far side shade)). order: list of parts drawn back to front
    (default: far arm, far leg, near leg, torso, near arm, head); far side = style['far'] ('L' or 'R')."""
    d = ImageDraw.Draw(lay)
    o = max(1.5, k * .009); w = LIMB_W * k
    far = style.get('far', 'L'); near = 'R' if far == 'L' else 'L'; dim = style.get('dim', .82)
    top, bot, skin = style['top'], style['bottom'], style.get('skin', (236, 240, 252))
    fcol = style.get('feet') or skin
    st_t = shade(top, 1.22) if style.get('stripes') else None
    st_b = shade(bot, 1.22) if style.get('stripes') else None
    def arm(s, f):
        if 'sh' + s not in J: return
        c = shade(top, f); limb(d, J['sh' + s], J['el' + s], J['ha' + s], w * .92, c, o, st_t and shade(st_t, f))
        if style.get('hands', True): hand(d, J['ha' + s], w * .62, shade(skin, f), o)
    def leg(s, f):
        if 'hip' + s not in J: return
        if 'toe' + s in J: foot(d, J['an' + s], J['toe' + s], w * .8, shade(fcol, f), o)
        limb(d, J['hip' + s], J['kn' + s], J['an' + s], w, shade(bot, f), o, st_b and shade(st_b, f))
    def body():
        torso(d, J['neck'], J['pelvis'], TORSO_HW * k, top, o, st_t, style.get('zip'), style.get('back', False))
    parts = order or ['arm_far', 'leg_far', 'leg_near', 'body', 'arm_near', 'head']
    for p in parts:
        if p == 'arm_far': arm(far, dim)
        elif p == 'arm_near': arm(near, 1.0)
        elif p == 'leg_far': leg(far, dim)
        elif p == 'leg_near': leg(near, 1.0)
        elif p == 'body': body()
        elif p == 'head' and style.get('head'): style['head'](lay, J, k); d = ImageDraw.Draw(lay)
        elif callable(p): p(lay, J, k); d = ImageDraw.Draw(lay)


# ------------------------------------------------------------------ 2D pose builders (screen px, k = px per metre)
def chain(root, a1, a2, l1, l2, k):
    """Forward kinematics: absolute screen angles (deg) of the upper and lower segment."""
    j = polar(root, a1, l1 * k); return j, polar(j, a2, l2 * k)


def build(pelvis, k, body_ang, legs, arms, head_off=0.0, sh_w=.05, hip_w=.035):
    """A pose from absolute segment angles. body_ang = direction pelvis -> neck (deg, -90 = up).
    legs = {'L': (thigh, shin, foot), 'R': ...}; arms = {'L': (upper, fore), ...} (deg).
    sh_w / hip_w = shoulder / hip offsets across the body (screen, m), + = toward the 'R' side normal."""
    J = {'pelvis': pelvis}
    J['neck'] = polar(pelvis, body_ang, TORSO * k)
    ux, uy = math.cos(math.radians(body_ang)), math.sin(math.radians(body_ang)); nx, ny = -uy, ux
    J['head'] = polar(J['neck'], body_ang + head_off, HEAD_R * .35 * k)
    for s, sg in (('L', -1), ('R', 1)):
        if s in legs:
            t, sh_, fa = legs[s]
            hp = (pelvis[0] + nx * hip_w * k * sg - ux * .03 * k, pelvis[1] + ny * hip_w * k * sg - uy * .03 * k)
            J['hip' + s] = hp; J['kn' + s], J['an' + s] = chain(hp, t, sh_, THIGH, SHIN, k)
            J['toe' + s] = polar(J['an' + s], fa, .1 * k)
        if s in arms:
            a, b = arms[s][:2]
            sp = polar(J['neck'], body_ang + 180, .13 * k); sp = (sp[0] + nx * sh_w * k * sg, sp[1] + ny * sh_w * k * sg)
            J['sh' + s] = sp; J['el' + s], J['ha' + s] = chain(sp, a, b, ARM, ARM, k)
    return J


def reach(J, s, target, k, bend=1):
    """Re-solve the arm s so its hand lands on target (px)."""
    J['el' + s], J['ha' + s] = ik2(J['sh' + s], target, ARM * k, ARM * k, bend)
    return J


def plant(J, s, ankle, k, bend=-1, toe_ang=None):
    """Re-solve the leg s so its ankle lands on a fixed floor point (no foot sliding)."""
    J['kn' + s], J['an' + s] = ik2(J['hip' + s], ankle, THIGH * k, SHIN * k, bend)
    if toe_ang is not None: J['toe' + s] = polar(J['an' + s], toe_ang, .1 * k)
    return J


# ------------------------------------------------------------------ stair descent gait (3D, metres)
def stair_descent(T, contacts, tread, lateral=.075, creep=True):
    """Feet + pelvis (3D) for a step-over-step stair descent, each foot contact on its time.
    contacts: sorted contact times; contact i puts foot ('L' if i even else 'R') on tread i (tread(i) -> (y, z) of
    that tread's foot spot, tread(-1) = the landing). Returns dict(feet={'L': (pos, toe_drop)}, pelvis, lower, lean).
    Phases per step (creep): the support knee bends and the lead foot swings forward over the nosing from
    contact - .6 s, reaches down toe first (toe_drop ~ .06 m), contact, heel settles by +.15 s; the pelvis lowers from
    contact - .45 s to a dip 3 cm under its new height at +.12 s, recovers by +.4 s, then holds (the creep's pause)."""
    feet = {}
    for side, par in (('L', 0), ('R', 1)):
        mine = [i for i in range(len(contacts)) if i % 2 == par]
        prev = -1 if par == 0 else -1                     # both feet start on the landing
        pos_i, toe = prev, 0.0; swing = None
        for i in mine:
            t0, t1 = contacts[i] - .6, contacts[i]
            if T >= t1: pos_i = i; toe = .06 * (1 - sm(seg(T, t1, t1 + .15)))
            elif T > t0: swing = (pos_i, i, seg(T, t0, t1)); break
            else: break
        x = lateral * (-1 if side == 'L' else 1)
        if swing:
            a, b, f = swing; ya, za = tread(a); yb, zb = tread(b)
            fy = lerp(ya, yb, sm(f)); lift = .05 * math.sin(math.pi * min(1, f * 1.3))
            # clear the nosing first (forward), then reach DOWN: z follows late (eased in)
            fz = lerp(za, zb, sm(seg(f, .35, 1.0))) + lift
            feet[side] = ((x, fy, fz), .06 * sm(seg(f, .3, .8)))
        else:
            y, z = tread(pos_i); feet[side] = ((x, y, z), toe)
    # pelvis: over the lower foot, lowered by the bending support knee before each contact
    n = sum(1 for c in contacts if T >= c - .45)
    lower = 0.0; fwd = 0.0
    for c in contacts:
        lower += sm(seg(T, c - .45, c + .12)); fwd += sm(seg(T, c - .55, c + .3))
    dip = sum(.03 * math.sin(math.pi * seg(T, c, c + .4)) for c in contacts)
    i0 = int(math.floor(fwd)); f = fwd - i0
    ya, za = tread(i0 - 1); yb, zb = tread(i0)
    py = lerp(ya, yb, f) - .05
    zz0 = tread(int(math.floor(lower)) - 1)[1]; zz1 = tread(int(math.floor(lower)))[1]
    pz = lerp(zz0, zz1, lower - math.floor(lower)) - dip
    return dict(feet=feet, pelvis=(0.0, py, pz), lower=lower, dip=dip)

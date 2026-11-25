"""flat2d.anim: motion helpers for flat2d shots (easing, pose in-betweens, cached stickman cards,
foot-locked walk, breathing/blinks, camera push/pan, cached post).

Rules (stickman/DRAWING_RULES.md 20-29): anticipation -> action (ease) -> overshoot -> settle
(`out_back`); never a linear blend between poses; moving holds (0.6% breath, blinks every 2-4 s);
foot locking on walks; transitions that would cross limbs go in stages.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
import stickman

# ---------------------------------------------------------------- easing
def clamp(t): return max(0.0, min(1.0, t))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in(t): t = clamp(t); return t ** 3
def out_back(t, s=1.6):
    """Overshoot then settle."""
    t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)
def lerp(a, b, t): return a + (b - a) * t
def damp(u, amp, k=5.0, w=14.0):
    """Damped follow-through swing after an event at u=0."""
    return 0.0 if u < 0 else amp * math.exp(-u * k) * math.sin(u * w)
def slam(t, t0, dur=0.28, s0=1.18):
    """Scale for a title/stamp slam: s0 -> 1 with overshoot below 1, then settle. 0 before t0."""
    if t < t0: return 0.0
    u = (t - t0) / dur
    if u >= 1: return 1.0 + 0.004 * math.sin((t - t0) * 2.4)   # moving hold: a slow 0.4% breathe
    return lerp(s0, 1.0, out_back(u, 2.2))
def pop(t, t0, dur=0.3, s=2.0):
    """0 -> 1 scale with overshoot (cut-ins, pills, bubbles)."""
    return 0.0 if t < t0 else out_back((t - t0) / dur, s)
def shake(t, t0, amp=10, dur=0.35, seed=0):
    """Camera shake offset after an impact at t0."""
    u = t - t0
    if u < 0 or u > dur: return 0.0, 0.0
    k = (1 - u / dur) ** 2 * amp
    return k * math.sin(u * 83 + seed), k * math.cos(u * 61 + 2 * seed)

# ---------------------------------------------------------------- poses
JOINTS = ('armL', 'armR', 'legL', 'legR')
POSES = stickman.POSES
STAND = dict(POSES['stand'])

def pad(v): v = list(v); v += [1.0] * (4 - len(v)); return v

def mix(A, B, t):
    """In-between two pose dicts (t may overshoot past 1 with out_back)."""
    out = {k: tuple(lerp(a, b, t) for a, b in zip(pad(A[k]), pad(B[k]))) for k in JOINTS}
    for meta in ('_side', '_name'):
        src = B if t >= 0.5 else A
        if meta in src: out[meta] = src[meta]
    if '_sh' in A or '_sh' in B:
        a, b = A.get('_sh', (300, 300)), B.get('_sh', (300, 300))
        out['_sh'] = (lerp(a[0], b[0], t), lerp(a[1], b[1], t))
    return out

def add(Pz, **d):
    """Offset joint angles: add(P, armR=(du, dl))."""
    out = dict(Pz)
    for k, (du, dl) in d.items():
        v = pad(out[k]); v[0] += du; v[1] += dl; out[k] = tuple(v)
    return out

def P(**k):
    return {**STAND, **k}

def chain(t, keys):
    """Pose timeline. keys = [(t0, pose), (t1, pose, ease), ...]; each segment eases from the previous
    pose with `ease` (default smooth; use out_back for the arrival of an action)."""
    if t <= keys[0][0]: return dict(keys[0][1])
    for (ta, pa, *_), (tb, pb, *e) in zip(keys, keys[1:]):
        if t < tb:
            f = (e[0] if e else smooth)(seg(t, ta, tb))
            return mix(pa, pb, f)
    return dict(keys[-1][1])

# ---------------------------------------------------------------- walk (anim_v2, rule 20-24)
STRIDE = 1.1
def walk_pose(t):
    ph = 2 * math.pi * t / STRIDE
    s, c = math.sin(ph), math.cos(ph)
    u = -21 * s
    swingL, swingR = max(0.0, c) ** 1.5, max(0.0, -c) ** 1.5
    downL = 9 * max(0.0, math.sin(ph - math.pi / 2)) ** 3 * (1 - swingL)
    downR = 9 * max(0.0, math.sin(ph + math.pi / 2)) ** 3 * (1 - swingR)
    legL = (u - 0.45 * 34 * swingL - downL, u + 0.75 * 34 * swingL + downL)
    legR = (-u - 0.45 * 34 * swingR - downR, -u + 0.75 * 34 * swingR + downR)
    a = 24 * math.sin(ph - 0.35); fa = 18 + 10 * math.sin(ph - 0.85)
    return {'_side': True, 'legL': legL, 'legR': legR, 'armL': (a, a - fa), 'armR': (-a, -a - fa)}

def _foot(leg):
    a1, a2 = math.radians(leg[0]), math.radians(leg[1]); L = stickman.SEG_LEG
    return (-math.sin(a1) * L - math.sin(a2) * L, math.cos(a1) * L + math.cos(a2) * L)

def walk_track(t_end, fps=30):
    """Foot-locked hip x (design units, 0 at t_end) per frame: the hip travels exactly as far as the
    planted foot slides back (rule 21). Facing right (+x)."""
    xs, anchor, stance, hip = [], None, None, 0.0
    for f in range(int(t_end * fps) + 2):
        p = walk_pose(f / fps); fL, fR = _foot(p['legL']), _foot(p['legR'])
        st = 'L' if fL[1] >= fR[1] else 'R'; rel = fL[0] if st == 'L' else fR[0]
        if st != stance: anchor = hip + rel; stance = st
        hip = anchor - rel; xs.append(hip)
    end = xs[int(t_end * fps)]
    return [x - end for x in xs]

# ---------------------------------------------------------------- cards (cached)
_cards = {}
def _key(pose):
    if isinstance(pose, str): return pose
    return tuple(sorted((k, tuple(round(x, 1) for x in v) if isinstance(v, (tuple, list)) else v)
                        for k, v in pose.items()))

def card(expr, pose, look=0.0, **kw):
    k = (expr, _key(pose), round(look, 2), tuple(sorted(kw.items())))
    if k not in _cards:
        if len(_cards) > 400: _cards.clear()
        c = stickman.draw(expr=expr, pose=pose, color='#f6f6f2', look=look, fixed=True, **kw)
        if kw.get('hair'):
            bare = dict(kw); bare.pop('hair')
            c.info['head'] = kit.head_of(stickman.draw(expr=expr, pose=pose, color='#f6f6f2', look=look, fixed=True, **bare))
        else:
            c.info['head'] = kit.head_of(c)
        _cards[k] = c
    return _cards[k]

def blink(t, period=3.1, phase=0.0, dur=0.1):
    """True during a blink (every ~period s, slightly irregular)."""
    u = (t + phase) % period
    return u < dur or (period > 2.6 and abs(u - period * 0.61) < dur * 0.5 and int((t + phase) / period) % 3 == 1)

def breath(t, period=2.6, amp=0.006, phase=0.0):
    return 1 + amp * math.sin(2 * math.pi * (t + phase) / period)

# ---------------------------------------------------------------- secondary action in holds (v4)
NOW = 0.0          # global film time, set by the renderer per frame (speech beats key off it)
BEATS = []         # global start times of stressed voice-over words (len >= 5 letters)

def secondary(pose, t, phase=0.0, amt=1.0):
    """Secondary action at the rig, layered on any pose (NOTES v3 open note):
    - the head leads: a slow look drift; the body follows 0.35 s later (returned lean);
    - the shoulders rise on each in-breath (upper arms open a little, in step with `breath`);
    - the hands move on speech: a damped forearm beat on every stressed voice-over word.
    Returns (pose, d_look, d_lean, d_hop)."""
    if amt <= 0: return pose, 0.0, 0.0, 0.0
    ph = phase * 2.3
    w = 2 * math.pi / 3.9
    d_look = amt * (.11 * math.sin(w * NOW + ph) + .04 * math.sin(2 * math.pi * NOW / 1.7 + 2 * ph))
    d_lean = amt * 1.5 * math.sin(w * (NOW - .35) + ph)
    br = math.sin(2 * math.pi * (t + phase) / 2.6)
    sh = amt * 3.0 * br                                         # shoulder rise with the breath
    beat = 0.0
    for b in BEATS:
        if 0 <= NOW - b < .7: beat += damp(NOW - b, 1.0, 6.0, 13.0)
    bt = amt * 9.0 * beat
    p = dict(pose)
    try:
        p = add(p, armL=(sh * .6 - bt * .3, sh + bt * .5), armR=(-sh * .6 + bt * .3, -sh - bt))
    except KeyError:
        pass
    return p, d_look, d_lean, amt * (1.2 * max(0.0, br) + 1.5 * abs(beat))


def actor(img, expr, pose, cx, gy, s, t=0.0, look=0.0, lean=0.0, hop=0.0, blink_ok=True, bphase=0.0,
          aura=None, aura_alpha=.5, rim=None, rim_dir=(1, -.4), rim_w=9, idle=1.0, quant=None, **kw):
    """Draw a stickman with a moving hold (breathing + blinks + `secondary` action), lean (deg, + = toward
    screen right) and hop (px). Returns kit.place geometry + 'hands' {'L'/'R': (x, y, ang)} in frame px.
    quant (deg): round the joint angles (and the look) so small figures reuse cached cards across frames (speed)."""
    if isinstance(pose, str): pose = dict(POSES[pose])
    pose, dl, dn, dh = secondary(pose, t, bphase, idle)
    look = max(-1.0, min(1.0, look + dl)); lean += dn; hop += dh
    if quant:
        pose = {k: (tuple(round(x / quant) * quant if i < 2 else x for i, x in enumerate(v)) if k in JOINTS else v)
                for k, v in pose.items()}
        look = round(look / .05) * .05
    e = expr
    if blink_ok and blink(t, phase=bphase) and expr not in ('blink',):
        e = 'blink'
    c = card(e, pose, look, **kw)
    head = c.info['head']
    b = breath(t, phase=bphase)
    if abs(lean) > .05:
        c2 = c.rotate(-lean, resample=Image.BICUBIC, center=(300, 975)); c2.info = dict(c.info)
        c = c2
    g = kit.place(img, c, cx, gy - hop, s * b, aura=aura, aura_alpha=aura_alpha, rim=rim, rim_dir=rim_dir,
                  rim_w=rim_w, shadow_alpha=.5 * (1 - min(.6, hop / 300)))
    sc = s * b; px, py = g['xy']
    def tr(x, y):  # card px -> frame px (with lean rotation about the soles)
        if abs(lean) > .05:
            a = math.radians(lean); x0, y0 = x - 300, y - 975
            x, y = 300 + x0 * math.cos(a) - y0 * math.sin(a), 975 + x0 * math.sin(a) + y0 * math.cos(a)
        return px + x * sc, py + y * sc
    g['head'] = tr(*head)
    ha = stickman.hand_anchors(pose, fixed=True)
    g['hands'] = {h: tr(v[0], v[1]) + (v[2] + lean,) for h, v in ha.items()}
    g['look'], g['lean'] = look, lean           # the effective values (after the idle sway) for face add-ons
    return g

# ---------------------------------------------------------------- camera + post (cached)
def camera(img, zoom=1.0, fx=None, fy=None, dx=0.0, dy=0.0):
    """Push in by `zoom` about focus (fx, fy) and offset (dx, dy) px (pan/shake). Returns a new image."""
    W, H = img.size; fx = W / 2 if fx is None else fx; fy = H / 2 if fy is None else fy
    if abs(zoom - 1) < 1e-4 and abs(dx) < .01 and abs(dy) < .01: return img
    # inverse affine: output (u, v) -> input ((u - fx)/z + fx - dx/z, ...)
    a = 1 / zoom
    return img.transform(img.size, Image.AFFINE, (a, 0, fx - fx * a - dx * a, 0, a, fy - fy * a - dy * a),
                         resample=Image.BICUBIC)

_vig = {}
def vignette(img, strength=0.35, color=(16, 14, 40), rx=0.75, ry=0.62, power=2.2):
    k = (img.size, strength, tuple(color), rx, ry, power)
    if k not in _vig:
        W, H = img.size; yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W * rx)) ** 2 + ((yy - H / 2) / (H * ry)) ** 2)
        a = (np.clip(d, 0, 1.6) ** power * strength).clip(0, 1)[..., None].astype(np.float32)
        _vig[k] = (a, (np.array(kit.rgb(color), np.float32) * a))
    a, ca = _vig[k]
    base = np.asarray(img, np.float32).copy()
    base[..., :3] = base[..., :3] * (1 - a) + ca
    img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)))

_grain = {}
def grain(img, amount=0.035, paper=0.05, seed=11, t=None):
    """Cached paper + grain multiply. t given: the fine grain re-seeds every 2 frames (film boil)."""
    W, H = img.size; k = (img.size, amount, paper, seed)
    if k not in _grain:
        rng = np.random.default_rng(seed)
        low = Image.fromarray(((rng.normal(0, 1, (H // 24 + 1, W // 24 + 1)) * 40 + 128).clip(0, 255)).astype(np.uint8))
        low = np.asarray(low.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6)), np.float32)
        fines = [rng.normal(0, 1, (H, W)).astype(np.float32) * amount for _ in range(3)]
        _grain[k] = ((low - 128) / 128 * paper, fines)
    low, fines = _grain[k]
    fine = fines[0 if t is None else int(t * 15) % 3]
    a = np.asarray(img, np.float32).copy()
    a[..., :3] *= (1 + fine + low)[..., None]
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8)))

def scaled_paste(img, lay, cx, cy, s, angle=0.0, alpha=1.0):
    """Paste an RGBA layer centred at (cx, cy) with scale s (slams, pops) and rotation."""
    if s <= 0.01 or alpha <= 0.01: return
    w, h = max(1, int(lay.width * s)), max(1, int(lay.height * s))
    l = lay.resize((w, h), Image.BICUBIC)
    if angle: l = l.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = l.split()[3].point(lambda v: int(v * alpha)); l.putalpha(a)
    img.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))

def text_layer(fn, w=1080, h=600):
    """Draw UI (title, pill) into a transparent layer via fn(layer) and crop to its bbox. Returns
    (layer, (cx, cy)) with the centre in the layer's original coords."""
    lay = kit.layer(w, h); fn(lay); bb = lay.getbbox() or (0, 0, 1, 1)
    return lay.crop(bb), ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)

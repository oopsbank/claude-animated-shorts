# 10 s stickman motion test, v2: rebuilt on standard animation principles.
#   - walk: contact / down / passing / up, hip bob, forward lean (line of action), FOOT LOCKING (no sliding)
#   - arms: pendulum from the shoulder, opposite the legs, lagging behind them; forearm lags the upper arm
#   - stop: last contact -> down -> settle, with damped follow-through on the arms
#   - every action: anticipation -> action (ease) -> overshoot -> settle; moving holds (breathing, blinks)
# usage: python anim_v2.py <plate.png> <outdir> [frames,comma,separated]
import sys, os, math
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stickman import draw, POSES

PLATE, OUT = sys.argv[1], sys.argv[2]
FPS = 30; N = 10 * FPS
W, H = 1080, 1920
GROUND_Y = 1430; SCALE = 0.55; COLOR = '#4a86e0'
SEG_LEG = 205

# ---------------- easing ----------------
def clamp(t): return max(0.0, min(1.0, t))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def out_back(t, s=1.6):                        # overshoot then settle
    t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def lerp(a, b, t): return a + (b - a) * t
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0))

JOINTS = ('armL', 'armR', 'legL', 'legR')
def P(**k): return k
def pad(v): v = list(v); v += [1.0] * (4 - len(v)); return v
def mix(A, B, t):
    out = {k: tuple(lerp(a, b, t) for a, b in zip(pad(A[k]), pad(B[k]))) for k in JOINTS}
    for meta in ('_side', '_name'):
        src = B if t >= 0.5 else A
        if meta in src: out[meta] = src[meta]
    if '_sh' in A or '_sh' in B:
        a, b = A.get('_sh', (300, 300)), B.get('_sh', (300, 300))
        out['_sh'] = (lerp(a[0], b[0], t), lerp(a[1], b[1], t))
    return out
def add(Pz, **d):                              # add angle offsets to joints
    out = dict(Pz)
    for k, (du, dl) in d.items():
        v = pad(out[k]); v[0] += du; v[1] += dl; out[k] = tuple(v)
    return out

STAND = dict(POSES['stand'])

# ---------------- walk cycle (one stride = 2 steps per second) ----------------
STRIDE = 1.2           # seconds per full cycle (an unhurried walk)
def walk_pose(t):
    ph = 2 * math.pi * t / STRIDE
    s, c = math.sin(ph), math.cos(ph)
    u = -21 * s                                           # legL thigh; negative = forward (to the right)
    swingL, swingR = max(0.0, c) ** 1.5, max(0.0, -c) ** 1.5
    # stance leg gets a small knee bend right after contact (the DOWN pose), swing leg bends while passing
    downL = 9 * max(0.0, math.sin(ph - math.pi / 2)) ** 3 * (1 - swingL)
    downR = 9 * max(0.0, math.sin(ph + math.pi / 2)) ** 3 * (1 - swingR)
    legL = (u - 0.45 * 34 * swingL - downL, u + 0.75 * 34 * swingL + downL)
    legR = (-u - 0.45 * 34 * swingR - downR, -u + 0.75 * 34 * swingR + downR)
    lag = 0.35                                            # arms peak a little after the legs (overlap)
    a = 24 * math.sin(ph - lag)
    fa = 18 + 10 * math.sin(ph - lag - 0.5)               # forearm trails the upper arm
    return {'_side': True, 'legL': legL, 'legR': legR, 'armL': (a, a - fa), 'armR': (-a, -a - fa)}

def foot(leg):                                            # foot position relative to the hip (design units)
    a1, a2 = math.radians(leg[0]), math.radians(leg[1])
    return (-math.sin(a1) * SEG_LEG - math.sin(a2) * SEG_LEG, math.cos(a1) * SEG_LEG + math.cos(a2) * SEG_LEG)

WALK_END = 3.3         # = STRIDE * 2.75: ends on a contact pose (legs spread)
def simulate_walk():
    """Foot locking: the hip moves exactly as much as the planted foot slides back."""
    xs, anchor, stance = [], None, None
    hip = 0.0
    for f in range(int(WALK_END * FPS) + 1):
        p = walk_pose(f / FPS)
        fL, fR = foot(p['legL']), foot(p['legR'])
        st = 'L' if fL[1] >= fR[1] else 'R'              # the lower foot carries the weight
        rel = fL[0] if st == 'L' else fR[0]
        if st != stance: anchor = hip + rel; stance = st
        hip = anchor - rel
        xs.append(hip)
    end_px = 600           # start just off the left edge so the walk-in begins at once
    return [end_px + (x - xs[-1]) * SCALE for x in xs]
WALK_X = simulate_walk()

# ---------------- the performance after the walk ----------------
def act(t):
    """pose, expr, look, x, hop(px), lean(deg)"""
    x = 600
    if t <= WALK_END:
        f = int(round(t * FPS))
        return walk_pose(t), 'neutral', 0.7, WALK_X[f], 0.0, 4.0
    last = walk_pose(WALK_END)
    # STOP: contact -> down (sink) -> feet together + settle with arm follow-through
    if t < 4.0:
        u = t - WALK_END
        down = add(last, legL=(-8, 14), legR=(-8, 14))
        p = mix(last, down, smooth(u / 0.12)) if u < 0.12 else mix(down, STAND, smooth((u - 0.12) / 0.4))
        k = smooth(u / 0.5)
        # damped arm swing (follow-through) after stopping
        sw = 14 * math.exp(-u * 4.5) * math.sin(u * 14)
        p = add(p, armL=(sw, sw * 1.4), armR=(-sw, -sw * 1.4))
        side = u < 0.3                                   # turn to face us once the arms hang near the body
        if not side: p.pop('_side', None)
        else: p['_side'] = True
        return p, 'neutral', 0.7 * (1 - k), x + 10 * smooth(u / 0.4), 0.0, 4.0 * (1 - k)
    x += 10
    # BLINK, then WAVE: anticipation (arm dips) -> raise with overshoot -> 3 waves -> lower
    if t < 6.1:
        u = t - 4.0
        wave_up = dict(POSES['wave'])
        if u < 0.3:
            p = mix(STAND, add(STAND, armR=(10, 8)), smooth(u / 0.3))               # anticipation
            e = 'blink' if 0.05 <= u < 0.15 else 'neutral'
        elif u < 0.7:
            p = mix(add(STAND, armR=(10, 8)), wave_up, out_back(seg(u, 0.3, 0.7)))   # raise + overshoot
            e = 'happy'
        elif u < 1.8:
            ph = 2 * math.pi * (u - 0.7) / 0.38
            p = add(wave_up, armR=(10 * math.sin(ph), 30 * math.sin(ph - 0.7)))      # forearm leads the hand flick
            e = 'blink_happy' if 1.2 <= u < 1.27 else 'happy'
        else:
            p = mix(wave_up, STAND, smooth(seg(u, 1.8, 2.1))); e = 'happy'
        return p, e, 0.0, x, 0.0, 0.0
    # SURPRISE HOP: anticipation crouch -> take-off stretch -> air -> land crouch -> recover with overshoot
    if t < 7.6:
        u = t - 6.1
        crouch = add(STAND, legL=(24, -15), legR=(-24, 15), armL=(-15, -10), armR=(15, 10))   # knees out, feet stay apart
        air = {'armL': (150, 170), 'armR': (-150, -170), 'legL': (20, 6), 'legR': (-20, -6)}             # stretched, legs apart
        shock = {'armL': (95, 140), 'armR': (-95, -140), 'legL': (12, 1), 'legR': (-12, -1)}
        hop = 0.0
        if u < 0.25:   p = mix(STAND, crouch, smooth(u / 0.25)); e = 'surprised'
        elif u < 0.65:
            v = seg(u, 0.25, 0.65); hop = 150 * 4 * v * (1 - v)
            p = mix(crouch, air, smooth(v * 2)) if v < 0.5 else mix(air, crouch, smooth((v - 0.5) * 2))
            e = 'surprised'
        elif u < 0.85: p = mix(crouch, shock, out_back(seg(u, 0.65, 0.85), 2.0)); e = 'surprised'
        else:          p = shock; e = 'surprised'
        return p, e, 0.0, x, hop, 0.0
    # THINK: arms come down, then the right hand rises to the chin while the left arm crosses (two stages)
    if t < 9.1:
        u = t - 7.6
        shock = {'armL': (95, 140), 'armR': (-95, -140), 'legL': (12, 1), 'legR': (-12, -1)}
        think = dict(POSES['think']); think['_name'] = 'think'; think['_sh'] = (278, 322)
        st_think = dict(STAND); st_think['_name'] = 'think'; st_think['_sh'] = (300, 300)
        stage1 = mix(think, st_think, 0.0); stage1['armL'] = STAND['armL']   # right hand at the chin, left still down
        if u < 0.3:   p = mix(shock, STAND, smooth(u / 0.3)); e = 'neutral'
        elif u < 0.6: p = mix(st_think, stage1, smooth(seg(u, 0.3, 0.6))); e = 'thinking'
        elif u < 0.85: p = mix(stage1, think, out_back(seg(u, 0.6, 0.85), 1.2)); e = 'thinking'
        else:
            p = dict(think); e = 'blink' if 1.2 <= u < 1.27 else 'thinking'
        if e == 'blink': e = 'thinking'
        return p, e, 0.0, x, 0.0, 0.0
    # SHRUG: small dip (anticipation) -> shoulders up with overshoot -> hold
    u = t - 9.1
    think = dict(POSES['think']); think['_name'] = 'think'; think['_sh'] = (278, 322)
    st = dict(STAND); st['_name'] = 'think'; st['_sh'] = (300, 300)
    if u < 0.25: p = mix(think, st, smooth(u / 0.25))
    else:
        p = mix(STAND, add(dict(POSES['shrug']), legL=(4, -6), legR=(-4, 6)), out_back(seg(u, 0.25, 0.55), 1.8))
    return p, 'smug', 0.0, x, 0.0, 0.0

# ---------------- compositing ----------------
PLATE_IM = None
def render(f):
    global PLATE_IM
    if PLATE_IM is None: PLATE_IM = Image.open(PLATE).convert('RGB').resize((W, H), Image.LANCZOS)
    t = f / FPS
    pose, expr, look, x, hop, lean = act(t)
    card = draw(expr, pose, COLOR, None, look, fixed=True)
    breath = 1 + 0.006 * math.sin(2 * math.pi * t / 2.6)          # moving hold: breathing
    if abs(lean) > 0.01:                                           # line of action: lean into the walk
        card = card.rotate(-lean, resample=Image.BICUBIC, center=(300, 975))
    cw, ch = int(600 * SCALE), int(1000 * SCALE * breath)
    card = card.resize((cw, ch), Image.LANCZOS)
    z = 1.0 + 0.05 * smooth(f / N)
    pw, ph = int(W / z), int(H / z)
    ox, oy = (W - pw) / 2, (H - ph) * 0.6
    bg = PLATE_IM.crop((int(ox), int(oy), int(ox) + pw, int(oy) + ph)).resize((W, H), Image.LANCZOS).convert('RGBA')
    gx, gy = (x - ox) * z, (GROUND_Y - oy) * z
    sh = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(sh)
    k = min(1.0, hop / 150); r = 95 * z * (1 - 0.45 * k)
    sd.ellipse((gx - r, gy - 0.22 * r, gx + r, gy + 0.22 * r), fill=int(120 * (1 - 0.5 * k)))
    bg.paste(Image.new('RGBA', (W, H), (10, 8, 30, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
    cz = card.resize((int(cw * z), int(ch * z)), Image.LANCZOS)
    hip_card_x = 300 * SCALE * z                                   # fixed=True keeps the hip at card x=300
    bg.alpha_composite(cz, (int(gx - hip_card_x), int(gy - 975 * SCALE * breath * z - hop * z)))
    bg.convert('RGB').save(os.path.join(OUT, f'f_{f:04d}.png'))
    return f

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    frames = [int(a) for a in sys.argv[3].split(',')] if len(sys.argv) > 3 else range(N)
    with Pool(4) as pool:
        for _ in pool.imap_unordered(render, frames): pass
    print('frames done', WALK_X[0], WALK_X[-1])

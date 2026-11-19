# 10 s motion test: the 2D stickman over a rendered background plate.
# usage: python anim_test.py <plate.png> <outdir> [fps]
# Beats: walk in from the left -> stop and face us -> blink -> wave -> surprised hop -> think -> shrug.
import sys, os, math
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stickman import draw, POSES

PLATE, OUT = sys.argv[1], sys.argv[2]
FPS = int(sys.argv[3]) if len(sys.argv) > 3 else 30
N = 10 * FPS
W, H = 1080, 1920
GROUND_Y = 1430          # soles on the square, matched to the plate's perspective
SCALE = 0.55             # card 600x1000 -> on-screen size (~510 px tall figure)
COLOR = '#4a86e0'

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

def lerp_pose(A, B, t):
    out = {}
    for k in ('armL', 'armR', 'legL', 'legR'):
        a, b = list(A[k]), list(B[k])
        while len(a) < 4: a.append(1.0)
        while len(b) < 4: b.append(1.0)
        out[k] = tuple(lerp(a[i], b[i], t) for i in range(4))
    return out

def walk_pose(f):
    ph = 2 * math.pi * f / (FPS * 1.0)          # one full stride cycle per second
    s = math.sin(ph)
    u = -24 * s                                 # legL upper: negative = forward (to the right)
    c = math.cos(ph)                            # a leg swings forward while its angle is decreasing
    kneeL = 34 * max(0.0, c) ** 1.5             # knee bends only during the swing (max as it passes under the hip);
    kneeR = 34 * max(0.0, -c) ** 1.5            # the supporting leg stays straight
    a = 22 * s                                  # arms swing opposite to the legs
    return {'_side': True,
            # passing position: the swinging thigh lifts slightly forward while its shin trails back
            'legL': (u - 0.45 * kneeL, u + 0.75 * kneeL), 'legR': (-u - 0.45 * kneeR, -u + 0.75 * kneeR),
            'armL': (a, a - 28), 'armR': (-a, -a - 28)}

def frame_spec(f):
    """Returns pose dict, expression, look, screen x, hop (px up), squash, camera shake."""
    t = f / FPS
    hop, squash, shake = 0.0, 1.0, 0.0
    stand = dict(POSES['stand'])
    # 0.0-3.2 s: walk in
    if t < 3.2:
        x = lerp(-330, 540, ease(t / 3.2) * 0.25 + (t / 3.2) * 0.75)
        return walk_pose(f), 'neutral', 0.7, x, 0, 1.0, 0
    x = 540
    # 3.2-3.7 s: settle into a stand, turn to face us
    if t < 3.7:
        k = ease((t - 3.2) / 0.5)
        p = lerp_pose(walk_pose(int(3.2 * FPS)), stand, k)
        return p, 'neutral', 0.7 * (1 - k), x, 0, 1.0, 0
    # 3.7-4.0 s: blink
    if t < 4.0:
        e = 'blink' if 3.8 <= t < 3.9 else 'neutral'
        return stand, e, 0, x, 0, 1.0, 0
    # 4.0-6.0 s: wave
    if t < 6.0:
        k = ease((t - 4.0) / 0.3)
        w = dict(POSES['wave']); ph = 2 * math.pi * (t - 4.0) / 0.5
        w['armR'] = (-125 + 12 * math.sin(ph), -168 + 26 * math.sin(ph + 0.6))
        p = lerp_pose(stand, w, k)
        e = 'blink_happy' if 5.2 <= t < 5.3 else 'happy'
        return p, e, 0, x, 0, 1.0, 0
    # 6.0-7.3 s: surprised hop (anticipation squash, jump, land, settle)
    if t < 7.3:
        u = t - 6.0
        surprise = {'armL': (70, 120), 'armR': (-70, -120), 'legL': (10, 1), 'legR': (-10, -1)}
        p = lerp_pose(lerp_pose(dict(POSES['wave']), stand, ease(u / 0.1)), surprise, ease((u - 0.1) / 0.15))
        if u < 0.15: squash = 1 - 0.07 * ease(u / 0.15)
        elif u < 0.65:
            v = (u - 0.15) / 0.5; hop = 140 * 4 * v * (1 - v); squash = 1.05
        elif u < 0.8: squash = 1 - 0.08 * math.sin(math.pi * (u - 0.65) / 0.15); shake = 14 * (1 - (u - 0.65) / 0.15)
        return p, 'surprised', 0, x, hop, squash, shake
    # 7.3-9.0 s: think
    if t < 9.0:
        k = ease((t - 7.3) / 0.35)
        surprise = {'armL': (70, 120), 'armR': (-70, -120), 'legL': (10, 1), 'legR': (-10, -1)}
        p = lerp_pose(surprise, POSES['think'], k)
        if k >= 0.999: p['_name'] = 'think'
        e = 'blink' if 8.4 <= t < 8.5 else 'thinking'
        if e == 'blink' and k >= 0.999: e = 'thinking'   # keep the thinking face; blink reads oddly mid-thought
        return p, e, 0, x, 0, 1.0, 0
    # 9.0-10 s: shrug
    k = ease((t - 9.0) / 0.3)
    p = lerp_pose(POSES['think'], POSES['shrug'], k)
    return p, 'smug', 0, x, 0, 1.0, 0

PLATE_IM = None
def render(f):
    global PLATE_IM
    if PLATE_IM is None: PLATE_IM = Image.open(PLATE).convert('RGB').resize((W, H), Image.LANCZOS)
    pose, expr, look, x, hop, squash, shake = frame_spec(f)
    card = draw(expr, pose, COLOR, None, look, fixed=True)
    cw, ch = int(600 * SCALE), int(1000 * SCALE * squash)
    card = card.resize((cw, ch), Image.LANCZOS)
    # slow camera push-in + landing shake
    z = 1.0 + 0.05 * f / N
    pw, ph = int(W / z), int(H / z)
    sx = int((W - pw) / 2 + (shake * (1 if f % 2 else -1)))
    bg = PLATE_IM.crop((sx, int((H - ph) * 0.6), sx + pw, int((H - ph) * 0.6) + ph)).resize((W, H), Image.LANCZOS).convert('RGBA')
    # map character from plate coordinates through the same zoom
    def P(px, py): return ((px - sx) * z, (py - int((H - ph) * 0.6)) * z)
    gx, gy = P(x, GROUND_Y)
    # soft contact shadow (shrinks while airborne)
    sh = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(sh)
    r = 95 * z * (1 - 0.45 * min(1, hop / 140))
    sd.ellipse((gx - r, gy - 0.22 * r, gx + r, gy + 0.22 * r), fill=int(120 * (1 - 0.5 * min(1, hop / 140))))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    bg.paste(Image.new('RGBA', (W, H), (10, 8, 30, 255)), (0, 0), sh)
    cz = card.resize((int(cw * z), int(ch * z)), Image.LANCZOS)
    sole = 975 * SCALE * squash * z
    bg.alpha_composite(cz, (int(gx - cz.width / 2), int(gy - sole - hop * z)))
    bg.convert('RGB').save(os.path.join(OUT, f'f_{f:04d}.png'))
    return f

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    frames = [int(a) for a in sys.argv[4].split(',')] if len(sys.argv) > 4 else range(N)
    with Pool(4) as pool:
        for f in pool.imap_unordered(render, frames): pass
    print('frames done')

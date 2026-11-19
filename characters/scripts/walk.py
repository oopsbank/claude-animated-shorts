# Side-view walk cycle for the bean cast, following stickman/DRAWING_RULES.md 20-29:
#   contact -> down -> passing -> up; only the swinging knee bends (most while passing under the hip);
#   foot locking (the hip travels exactly as far as the planted foot slides back); arms swing opposite the legs,
#   a little AFTER them, with the forearm trailing; a small lean into the walk; blinks; a settle on the stop.
# walk_pose(t) -> turned() pose dict;  walk_track(seconds) -> per-frame (pose, x_offset_px, planted, expr_kw)
# usage: walk.py <out_dir>   (writes a contact strip, a GIF and prints the foot-lock check)
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bean import turned, BUILDS

FPS = 30
STRIDE = 1.1           # seconds per full cycle (two steps)

def leg_len(build):
    B = BUILDS[build]; HH = 2 * B['b']; u = 2 * B['a'] / 100
    hip_y = 975 - HH * (1 + B['torso'] + B['legs']) + 2 * B['b'] + B['torso'] * HH - 0.12 * HH
    return (975 - 3.75 * u - hip_y) / 2

def walk_pose(t, amp=21.0):
    """Angles: + = forward. N leg leads at t=0 (contact, N in front)."""
    ph = 2 * math.pi * t / STRIDE
    s, c = math.sin(ph), math.cos(ph)
    thN, thF = amp * c, -amp * c                                  # thigh: N forward at ph=0
    swN, swF = max(0.0, -s) ** 1.4, max(0.0, s) ** 1.4            # a leg swings while its thigh moves forward
    downN = 8 * max(0.0, s) ** 3 * (1 - swN)                       # the stance knee gives a little after contact (DOWN)
    downF = 8 * max(0.0, -s) ** 3 * (1 - swF)
    legN = (thN + 0.35 * 30 * swN + downN * 0.3, thN - 0.9 * 34 * swN - downN)   # swing: thigh lifts forward, shin trails
    legF = (thF + 0.35 * 30 * swF + downF * 0.3, thF - 0.9 * 34 * swF - downF)
    lag = 0.4                                                       # arms peak a little after the legs (overlap)
    a = 20 * math.cos(ph - lag)                                     # opposite the legs: near arm goes back when the near leg goes forward
    fa = 14 + 8 * math.cos(ph - lag - 0.6)                          # forearm trails and stays bent forward
    return dict(legN=legN, legF=legF, armN=(-a, -a + fa), armF=(a, a + fa), lean=4.0, tilt=-1.0)

def _foot_x(leg, L, s=1):
    a1, a2 = math.radians(leg[0]), math.radians(leg[1])
    return s * (math.sin(a1) + math.sin(a2)) * L, (math.cos(a1) + math.cos(a2)) * L

def walk_track(seconds, build='adult', start_x=0.0):
    """Foot locking: the stance foot (the lower one) stays put; the hip moves by exactly its slide."""
    L = leg_len(build); out = []; anchor = None; stance = None; hip = start_x
    for f in range(int(seconds * FPS) + 1):
        p = walk_pose(f / FPS)
        xN, yN = _foot_x(p['legN'], L); xF, yF = _foot_x(p['legF'], L)
        st = 'N' if yN >= yF else 'F'
        rel = xN if st == 'N' else xF
        if st != stance: anchor = hip + rel; stance = st
        hip = anchor - rel
        out.append((p, hip, st))
    return out

def blink_at(t, every=(2.3, 3.1, 2.7)):
    """Blink for ~2 frames every 2-4 s (moving holds never fully freeze)."""
    acc = 0.6
    for k in range(100):
        acc += every[k % len(every)]
        if acc <= t < acc + 2.5 / FPS: return True
        if acc > t: return False
    return False

if __name__ == '__main__':
    from PIL import Image, ImageDraw
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    char = dict(build='adult', skin='#f6d2b0', shirt='#3fb37f', pants='#2f3f6b', hat='beanie', hat_col='#f2c230', seed=11)
    track = walk_track(STRIDE)
    frames = []; rig_x = []
    for f, (p, hx, st) in enumerate(track):
        rig = {}
        im = turned('side', facing=1, pose=p, rig=rig, blink=blink_at(f / FPS), **char)
        frames.append((im, hx)); rig_x.append((rig['ankleN'][0] + hx, rig['ankleF'][0] + hx, rig['ankleN'][1], rig['ankleF'][1], st))
    # foot-lock check (QA: a planted foot moves <= 2 px while planted)
    worst = 0.0; prev = None
    for xn, xf, yn, yf, st in rig_x:
        x = xn if st == 'N' else xf
        if prev and prev[1] == st: worst = max(worst, abs(x - prev[0]))
        prev = (x, st)
    print(f'foot lock: planted foot moves at most {worst:.2f} px per frame')
    # contact strip: 8 poses over one stride, side by side on one ground line, plus a GIF that walks across
    sel = [round(i * (len(frames) - 1) / 8) for i in range(8)]
    strip = Image.new('RGBA', (8 * 300, 560), (240, 237, 230, 255)); d = ImageDraw.Draw(strip)
    for i, k in enumerate(sel):
        im = frames[k][0].resize((300, 500), Image.LANCZOS); strip.alpha_composite(im, (i * 300, 40))
        d.text((i * 300 + 10, 8), f'f{k}', fill=(60, 60, 70))
    d.line([(0, 40 + 487), (2400, 40 + 487)], fill=(150, 140, 130), width=2)
    strip.save(os.path.join(out, 'walk_strip.png'))
    gif = []; track2 = walk_track(2 * STRIDE)
    for f, (p, hx, st) in enumerate(track2):
        bg = Image.new('RGBA', (900, 520), (240, 237, 230, 255))
        im = turned('side', facing=1, pose=p, blink=blink_at(f / FPS), **char).resize((300, 500), Image.LANCZOS)
        bg.alpha_composite(im, (int(-150 + hx * 0.5), 10)); ImageDraw.Draw(bg).line([(0, 497), (900, 497)], fill=(150, 140, 130), width=2)
        gif.append(bg.convert('P', palette=Image.ADAPTIVE))
    gif[0].save(os.path.join(out, 'walk.gif'), save_all=True, append_images=gif[1:], duration=int(1000 / FPS), loop=0)
    print('ok', len(gif), 'frames')

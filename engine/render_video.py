# Engine: shots.json + words.json -> frames -> mp4 (picture only; --audio muxes a track for previews).
# usage: python engine/render_video.py shots.json words.json out_dir [--plates DIR ...] [--frames A:B[:step] | f1,f2,...] [--workers 4]
#                                      [--audio voice.wav] [--png] [--no-mp4]
# Contracts: PIPELINE.md (shots.json, plates + JSON, characters, fx). Motion grammar: engine/anim.py.
import os, sys, json, math, argparse, subprocess, importlib.util, zlib
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import anim  # noqa: E402
import captions as CAP  # noqa: E402
import grade as GRADE  # noqa: E402
import parallax as PX  # noqa: E402
import props as PROPS  # noqa: E402
from anim import W, H, FPS, smooth, clamp, lerp  # noqa: E402

PLATE_DEFAULTS = {'horizon_y': H * 0.4, 'light_dir': 'left', 'tint': '#fff8f0'}
XFADE, WHIP = 6, 8
_T = os.path.join(HERE, 'test', 'plates')
STANDIN_PLATES = {}
if os.environ.get('ENGINE_STANDIN', '1') == '1' and os.path.exists(os.path.join(_T, 'village__M__day.jpg')):
    STANDIN_PLATES = {'medium': os.path.join(_T, 'village__M__day.jpg'), 'close': os.path.join(_T, 'village__M__day.jpg'),
                      'wide': os.path.join(_T, 'village__A__day.jpg')}                 # transition lengths in frames, centred on the cut


# ---------------------------------------------------------------- loading
def find_plate(shot, dirs):
    if shot.get('plate'):
        cands = [shot['plate']] + [os.path.join(d, shot['plate']) for d in dirs]
    else:
        name = f"{shot['set']}__{shot['cam']}__{shot['light']}"
        # plate variants: "variant": tag on the shot, or a "fantasy:<tag>" prop -> <set>__<cam>__<light>__<tag>
        var = shot.get('variant') or next((p.split(':', 1)[1].strip() for p in shot.get('props', []) if isinstance(p, str) and p.startswith('fantasy:')), None)
        names = ([name + '__' + var] if var else []) + [name]
        cands = [os.path.join(ROOT, 'blender', 'sets', shot['set'], 'plates', n + ext) for n in names for ext in ('.png', '.jpg')]
        cands += [os.path.join(d, n + ext) for d in dirs for n in names for ext in ('.png', '.jpg')]
    for p in cands:
        if os.path.exists(p): return p
    if STANDIN_PLATES:                # sets not built yet: stand-in plate by shot size
        size = shot.get('size') or ('wide' if 'wide' in shot.get('cam', '') else 'medium')
        if size == 'medium' and len(shot.get('characters', [])) >= 2:      # the M stand-in is too tight for a two-shot
            size = 'wide'; shot['_standin_zoom'] = 1.3
        p = STANDIN_PLATES.get(size) or STANDIN_PLATES['medium']
        if os.environ.get('ENGINE_QUIET') != '1': print(f"  [plate stand-in] {shot.get('id')}: {shot.get('set')}/{shot.get('cam')}/{shot.get('light')} missing -> {os.path.basename(p)}")
        return p
    raise SystemExit(f"plate not found for shot {shot.get('id')}: tried {cands}")


def load_plate(path):
    im = Image.open(path).convert('RGB')
    js = os.path.splitext(path)[0] + '.json'
    meta = dict(PLATE_DEFAULTS); meta.update(json.load(open(js)) if os.path.exists(js) else {})
    if 'ground_y' not in meta or 'px_per_m' not in meta: raise SystemExit(f'{js}: needs ground_y and px_per_m')
    k = W / im.width
    if im.size != (W, H):            # plates rendered at another size: scale the image and the JSON together
        im = im.resize((W, int(round(im.height * k))), Image.LANCZOS)
        if im.height != H:
            top = max(0, (im.height - H) // 2); im = im.crop((0, top, W, top + H))
        for key in ('ground_y', 'horizon_y', 'px_per_m', 'ground_x'):
            if key in meta and isinstance(meta[key], (int, float)): meta[key] = meta[key] * k
    return im, meta


def load_fx():
    path = os.environ.get('ENGINE_FX', os.path.join(ROOT, 'fx', 'fx.py'))
    if not os.path.exists(path): return None
    spec = importlib.util.spec_from_file_location('fx_area', path); mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod); return mod


def stub_fx(name, t, size, **kw):
    """Stand-in until fx/fx.py exists: an ink-outlined star that pops (anticipation, overshoot) and shrinks out."""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    if t <= 0 or t >= 1: return im
    k = anim.out_back(clamp(t / 0.3), 2.0) * (1 - smooth(clamp((t - 0.6) / 0.4)))
    if k <= 0.01: return im
    d = ImageDraw.Draw(im); c = size / 2; r = size * 0.42 * k; pts = []
    for i in range(16):
        rr = r if i % 2 == 0 else r * 0.5; a = math.pi * 2 * i / 16 + t
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts, fill=(255, 226, 90, 255), outline=(36, 23, 38, 255), width=max(2, int(size / 80)))
    return im


# ---------------------------------------------------------------- per-process state
G = {}


def setup(shots_path, words_path, plate_dirs):
    import rig
    anim.RIG_OK = rig.bikes is not None
    doc = json.load(open(shots_path)); words = json.load(open(words_path))
    if isinstance(words, dict): words = words.get('words', [])
    shots = doc['shots']; spans = anim.shot_spans(shots, words)
    G.update(doc=doc, words=words, shots=shots, spans=spans, rig=rig, fx=load_fx(), plates={}, tracks={}, cams={}, mouths={})
    for k, (s, sp) in enumerate(zip(shots, spans)):
        p = find_plate(s, plate_dirs)
        if p not in G['plates']: G['plates'][p] = load_plate(p)
        s['_plate'] = p
        for c in s.get('characters', []):
            ins = c.get('insert')
            if ins and not s.get('_insert'):
                alt = dict(s, cam=ins.get('cam', s['cam']), size='wide' if 'top' in ins.get('cam', '') else 'close')
                q = find_plate(alt, plate_dirs)
                if q not in G['plates']: G['plates'][q] = load_plate(q)
                a0 = anim.beat_frame((sp['w0'], sp['w1']), words, ins.get('at_word', 0))[1]
                a1 = anim.beat_frame((sp['w0'], sp['w1']), words, ins['until_word'])[1] if 'until_word' in ins else sp['f1']
                s['_insert'] = (a0 - anim.LEAD, a1 - anim.LEAD, q)
        resolve_points_at(s, G['plates'][p][1])
        layout_shot(s, G['plates'][p][1])
        # two-shots: characters with no facing turn a little toward each other
        cs = s.get('characters', [])
        if len(cs) >= 2:
            for c in cs:
                if 'facing' not in c and c.get('view', 'front') == 'front':
                    others = [o.get('x', 0.5) for o in cs if o is not c]
                    c['facing'] = 0.35 if sum(others) / len(others) > c.get('x', 0.5) else -0.35
        G['tracks'][k] = [anim.Track(c, sp, words, seed=zlib.crc32(f"{c.get('id', '')}/{k}".encode())) for c in s.get('characters', [])]
        # the countersteer must read even when the rider's body hides the bars: an arrow at handlebar height, peaking
        # with each automatic flick (direction in the rider's sense, as fx steer_arrow expects)
        s['_auto_fx'] = []
        for c, tr in zip(s.get('characters', []), G['tracks'][k]):
            if not tr.rig: continue
            for fr, d in tr.flick_cues():
                if sp['f0'] <= fr < sp['f1']:
                    s['_auto_fx'].append({'name': 'steer_arrow', 'direction': 'right' if d > 0 else 'left', '_frame': fr,
                                          'on': c.get('id'), 'anchor': 'bars', 'size': 0.3, 'dur': 0.8})
        # air_hockey_overlay listed as a prop is an fx (it flickers over the real ice)
        for pr in s.get('props', []):
            if (pr if isinstance(pr, str) else pr.get('name', '')).startswith('air_hockey_overlay') and not any(e['name'] == 'air_hockey_overlay' for e in s.get('fx', [])):
                s.setdefault('fx', []).append(dict({'name': 'air_hockey_overlay', 'at_word': 0, 'x': 0.5, 'y': 0.8, 'size': 1.0, 'aspect': 0.32},
                                                   **({} if isinstance(pr, str) else {kk: v for kk, v in pr.items() if kk != 'name'})))
        # ice_pane stages chain in one framing: each stage but the last holds its full sheet (t 0.91, before its fade)
        # until the next stage starts, and the last plays to the end of the shot
        ip = [e for e in s.get('fx', []) if e['name'] == 'ice_pane']
        for a_, b_ in zip(ip, ip[1:]):
            a_['_hold_until'] = anim.beat_frame((sp['w0'], sp['w1']), words, b_.get('at_word', 0))[1]
        kicks = []
        for e in s.get('fx', []):
            if e.get('kick'): kicks.append(anim.beat_frame((sp['w0'], sp['w1']), words, e.get('at_word', 0))[1])
        cam = dict(s.get('camera') or {})
        if s.get('_standin_zoom') and 'zoom' not in cam: cam['zoom'] = s['_standin_zoom']
        if 'focus' not in cam and s.get('characters'):      # aim the push at the characters' chests, not the plate centre
            pm = G['plates'][p][1]; fig = pm['px_per_m'] * 1.75
            xs = [float(c.get('x', 0.5)) for c in s['characters']]
            cam['focus'] = [sum(xs) / len(xs), (pm['ground_y'] - 0.62 * fig) / H]
        G['cams'][k] = anim.Camera(cam, sp, words, kicks)
        s['_props'] = PROPS.plan(s)
        s['_ant'] = [antennae_keys(c, sp, words) for c in s.get('characters', [])]
        G['mouths'][k] = [rig.mouth_track(words[sp['w0']:sp['w1']], sp['f0'] - 30, sp['f1'] + 30) if c.get('talk') else {}
                          for c in s.get('characters', [])]
    n = spans[-1]['f1'] if spans else 0
    G['n'] = n
    cap = doc.get('captions', {})
    G['captions'] = [] if cap.get('enabled') is False else CAP.schedule(words, doc, 10 ** 9, cap.get('case', 'upper'))
    gp = os.environ.get('ENGINE_GRADE_FILE')
    G['grades'] = json.load(open(gp)) if gp and os.path.exists(gp) else {}
    return G


BIKES = ('bicycle', 'motorbike', 'nobs_bike')
ANT = {'up': 0.0, 'droop': 1.0}


def antennae_keys(c, sp, words):
    """Antennae droop keys [(frame, value)] for hat='antennae': the spec's start value, then each beat's "antennae"
    ('up'|'droop'|0..1) eased in over 10 f from its word. Spring sway kicks [(frame, amp)] on every beat and hop."""
    if c.get('hat') != 'antennae': return None
    v0 = c.get('antennae', 'up'); v0 = ANT.get(v0, v0)
    keys = [(-10 ** 9, float(v0))]; kicks = []
    for b in sorted(c.get('beats', []), key=lambda b: b.get('at_word', 0)):
        land, wf = anim.beat_frame((sp['w0'], sp['w1']), words, b.get('at_word', 0))
        if 'antennae' in b:
            v = b['antennae']; keys.append((wf, float(ANT.get(v, v))))
        if land > sp['f0'] + 1 and any(kk in b for kk in ('pose', 'arm_pose', 'lean', 'x', 'action', 'antennae')):
            kicks.append((land, 9.0 if ('x' in b or b.get('action')) else 6.0))
    return {'keys': keys, 'kicks': kicks}


def antennae_at(ak, f, sign=1.0):
    """(droop 0..1, sway deg) at frame f: smooth 10 f ease between keys; damped spring after each kick."""
    v = ak['keys'][0][1]
    for fr, val in ak['keys'][1:]:
        if f >= fr: v = lerp(v, val, smooth((f - fr) / 10.0))
    sw = 0.0
    for fr, amp in ak['kicks']:
        d = f - fr
        if 0 <= d < 30: sw += amp * math.exp(-d / 9.0) * math.sin(d * 2 * math.pi / 11.0)
    return round(v, 1), sign * round(sw / 2) * 2


def layout_shot(shot, meta):
    """Staging fixes that need the plate: over-the-shoulder near characters, and two-shots spread so bodies never
    overlap. A shot with no characters but a bike in "props" shows the bike alone."""
    cs = shot.get('characters', []); s = meta['px_per_m'] * 1.75 / 777
    for c in cs:     # over the shoulder: the rear-view character is the near one, large and cut by the frame edge
        if 'ots' in shot.get('cam', '') and c.get('view') == 'rear' and not c.get('rig'):
            c.setdefault('scale', 1.7); c['_near'] = True
    stand = [c for c in cs if not c.get('rig') and not c.get('_near')]
    if len(stand) >= 2:
        stand.sort(key=lambda c: float(c.get('x', 0.5)))
        def points(c): return any('point' in json.dumps(b.get('arm_pose', '')) or b.get('pose') == 'point' for b in [c] + c.get('beats', []))
        m_ = 0.05                                                            # room for the push-in zoom
        def widths(k):
            hw = [200 * s * k * float(c.get('scale', 1.0)) / W for c in stand]     # half body width, frame fractions
            reach = [(275 if points(c) else 200) * s * k * float(c.get('scale', 1.0)) / W for c in stand]   # pointing arm
            need = [hw[i] + hw[i + 1] + 0.02 for i in range(len(stand) - 1)]
            return hw, reach, need
        # too tight for the plate: step both characters back in depth (smaller, standing higher toward the horizon)
        k = 1.0
        while k > 0.7:
            hw, reach, need = widths(k)
            if reach[0] + sum(need) + reach[-1] + 2 * m_ <= 1.0: break
            k -= 0.02
        hw, reach, need = widths(k)
        if k < 1.0:
            for c in stand: c['_depth'] = round(k, 3)
            if os.environ.get('ENGINE_QUIET') != '1': print(f"  [layout] {shot.get('id')}: two-shot too wide for the plate -> characters stepped back to {k:.2f}x")
        xs = [float(c.get('x', 0.5)) for c in stand]
        for i, d in enumerate(need):
            if xs[i + 1] - xs[i] < d:
                mid = (xs[i] + xs[i + 1]) / 2; xs[i], xs[i + 1] = mid - d / 2, mid + d / 2
        shift = max(0.0, reach[0] + m_ - xs[0]) - max(0.0, xs[-1] + reach[-1] + m_ - 1.0)
        xs = [x + shift for x in xs]
        for c, x in zip(stand, xs):
            if abs(x - float(c.get('x', 0.5))) > 1e-3:
                if os.environ.get('ENGINE_QUIET') != '1': print(f"  [layout] {shot.get('id')}/{c.get('id')}: x {c.get('x')} -> {x:.3f} (bodies overlapped)")
                c['x'] = round(x, 3)
    sticker = next((p.split(':', 1)[1] for p in shot.get('props', []) if p.startswith('helmet_sticker:')), None)
    for c in cs:
        if sticker: c['_sticker'] = sticker
    if not cs:
        kind = next((p for p in shot.get('props', []) if p in BIKES), None)
        if kind: shot['_bike_prop'] = (kind, float(meta.get('stand_x', 0.5)))


def resolve_points_at(shot, meta):
    """Beats with "points_at": <target> turn toward the target and point with the arm on its side. Targets: the plate
    JSON's "targets": {name: [x, y]} (fractions), another character's id, or, if unknown, off-screen past the nearer
    edge (the thing is out of shot)."""
    chars = shot.get('characters', [])
    for c in chars:
        for b in c.get('beats', []):
            tgt = b.get('points_at')
            if not tgt: continue
            cx = float(c.get('x', 0.5))
            if tgt in meta.get('targets', {}):
                tx = float(meta['targets'][tgt][0]); tx = tx / W if tx > 1.5 else tx     # sets writes px; fractions also work
            elif any(o.get('id') == tgt for o in chars): tx = float(next(o for o in chars if o.get('id') == tgt).get('x', 0.5))
            else:
                tx = 1.2 if cx >= 0.5 else -0.2
                if os.environ.get('ENGINE_QUIET') != '1':
                    print(f"  [points_at] {shot.get('id')}/{c.get('id')}: target {tgt!r} not in plate JSON 'targets' -> off-screen {'right' if tx > 1 else 'left'}")
            right = tx > cx; b.setdefault('facing', 0.4 if right else -0.4)
            ap = b.get('arm_pose') or c.get('arm_pose') or ['hang', 'hang']
            if isinstance(ap, str): ap = [ap, ap]
            other = next((a for a in ap if a != 'point'), 'hang')
            front = anim.screen_side(c.get('view', 'front')) < 0    # facing us: rider-left = screen right
            b['arm_pose'] = (['point', other] if right == front else [other, 'point'])


def init_worker(*a):
    os.environ['ENGINE_QUIET'] = '1'; setup(*a)
    n = int(os.environ.get('ENGINE_LENGTH', 0))
    if n: G['spans'][-1]['f1'] = n; G['n'] = n


# ---------------------------------------------------------------- compositing
def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint_card(im, tint):
    """Mild multiply toward the plate's light colour; the lightest pixels (faces) keep their white (style rule 7)."""
    t = hexrgb(tint) if isinstance(tint, str) else tuple(tint)
    m = max(t) or 1; f = [0.82 + 0.18 * c / m for c in t]
    if min(f) > 0.995: return im
    r, g, b, a = im.split()
    lum = im.convert('L').point(lambda v: 255 if v > 225 else 0)     # protect near-white face highlights
    out = Image.merge('RGBA', (r.point(lambda v: int(v * f[0])), g.point(lambda v: int(v * f[1])), b.point(lambda v: int(v * f[2])), a))
    out.paste(im, (0, 0), lum)
    return out


def feet_of(alpha, sole_x):
    """Lowest opaque row and the x centroids of the left/right foot strokes in the bottom band."""
    a = np.asarray(alpha) > 128
    rows = np.nonzero(a.any(1))[0]
    if len(rows) == 0: return None
    yb = rows[-1]; band = a[max(0, yb - 6):yb + 1]
    cols = np.nonzero(band.any(0))[0]
    L, R = cols[cols < sole_x], cols[cols >= sole_x]
    return {'y': float(yb), 'l': float(L.mean()) if len(L) else None, 'r': float(R.mean()) if len(R) else None}


def plate_depth(meta, k):
    """Camera distance (m) of the shot's plate, cached per worker (sets: build.py --depth)."""
    pkey = G['shots'][k]['_plate']; cache = G.setdefault('_depth', {})
    if pkey not in cache:
        info = meta['depth']; cache.clear()
        cache[pkey] = PX.load_depth(os.path.join(os.path.dirname(pkey), info['file']), info)
    return cache[pkey]


def occlude(base, clean, im, ox, oy, gx, ground, meta, k, f, margin=0.6):
    """Depth-tested compositing: plate pixels nearer to the camera than the character's ground point are drawn back
    over the character (door frames, counters, signs, rocks in front). Off when the shot rides (the plate is warped)."""
    if ride_distance(k, f, meta) > 1e-3: return
    dep = plate_depth(meta, k); h, w = dep.shape
    fx_, fy_ = int(clamp(gx, 0, w - 1)), int(clamp(ground - 3, 0, h - 1))
    d_char = float(np.median(dep[max(0, fy_ - 2):fy_ + 1, max(0, fx_ - 3):fx_ + 4]))
    x0, y0 = max(0, ox), max(0, oy); x1, y1 = min(W, ox + im.width), min(min(H, oy + im.height), int(ground) - 4)
    if x1 <= x0 or y1 <= y0: return
    near = dep[y0:y1, x0:x1] < (d_char - margin - 0.05 * d_char)
    if not near.any(): return
    a = np.asarray(im.getchannel('A'))[y0 - oy:y1 - oy, x0 - ox:x1 - ox] > 8
    m = near & a
    if not m.any(): return
    mask = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    base.paste(clean.crop((x0, y0, x1, y1)), (x0, y0), mask)


def place_characters(base, k, f, meta):
    rig = G['rig']; shot = G['shots'][k]; out = []
    clean = base.copy() if ('depth' in meta and not shot.get('no_occlusion')) else None   # the plate before any character: occluders come from here
    order = sorted(range(len(G['tracks'][k])), key=lambda i: shot['characters'][i].get('z', 0))
    for i in order:
        tr = G['tracks'][k][i]; spec = shot['characters'][i]
        ins = spec.get('insert')
        if ins and shot.get('_insert') and shot['_insert'][0] <= f < shot['_insert'][1]:
            spec = dict(spec, **{kk: ins[kk] for kk in ('rig', 'view', 'path') if kk in ins})
        if spec.get('rig') in rig.INSERT_RIGS:         # a full-frame insert card (e.g. the broom on the palm) over a soft plate
            pose = 'broom_upright'; sw = (G['spans'][k]['w0'], G['spans'][k]['w1'])
            seq = []
            for b in sorted(spec.get('beats', []), key=lambda b: b.get('at_word', 0)):
                key_ = next((kk for kk in b if kk.startswith('broom_')), None)
                if key_: seq.append([anim.beat_frame(sw, G['words'], b.get('at_word', 0))[0], key_, b])
            # physics order: the hand flicks first, the broom tips as the result. A tip announced before an opposite
            # flick ("to tip it left, flick your hand right first") plays 10 f after the flick.
            for t_ in seq:
                if 'tip' in t_[1]:
                    fl = next((x for x in seq if 'flick' in x[1] and x[0] > t_[0]), None)
                    if fl: t_[0] = fl[0] + 10
            for t0_, key_, b in sorted(seq, key=lambda x: x[0]):
                if t0_ <= f:
                    pose = key_ if b[key_] is True else f"broom_{b[key_]}" if key_ in ('broom_tip', 'broom_flick') else key_
                    if key_ in ('broom_tip', 'broom_flick'): pose = f"{key_}_{b[key_]}"
            card_ = rig.insert_card(spec['rig'], pose, spec, W, H)
            if card_ is not None:
                soft = base.filter(ImageFilter.GaussianBlur(14)); base.paste(soft); base.alpha_composite(card_)
                out.append({'id': spec.get('id', f'c{i}'), 'grounded': False, 'moving': False, 'planted': False, 'near': True,
                            'foot_y': None, 'foot_l': None, 'foot_r': None, 'ground_y': meta['ground_y'], 'bbox': None,
                            'face': None, 'head': [W / 2, 0], 'scale': 1.0, 'rig': None, 'pose': [pose], 'facing': 0,
                            'expr': None, 'mouth': None, 'lid': 0})
            continue
        if spec.get('path') and spec.get('view') == 'top' and any(e['name'] == 'path_line' for e in shot.get('fx', [])) and G['fx']:
            continue                                   # drawn by path_riders() on the track diagram
        st = tr.state_at(f)
        if spec.get('enter_at_word') is not None:
            wf = anim.beat_frame((G['spans'][k]['w0'], G['spans'][k]['w1']), G['words'], spec['enter_at_word'])[0]
            if f < wf: continue
        dk = float(spec.get('_depth', 1.0))                     # stepped back in depth: smaller, ground nearer the horizon
        s = meta['px_per_m'] * float(spec.get('height_m', 1.75)) / (3.5 * 2 * 111) * float(spec.get('scale', 1.0)) * dk
        mouth = G['mouths'][k][i].get(f, 'closed') if spec.get('talk') else None
        if st.get('rig'):            # rider on a bike (bikes.ride): 1000x1000 card, ground at 975, no breathing (it's riding)
            rs = dict(spec)
            if spec.get('_sticker') and spec.get('hat') == 'helmet': rs.setdefault('sticker', spec['_sticker'])
            im = rig.ride_card(rs, s, st['rig'], st['expr'], mouth, st['lid'], crank=f * 14.0)
            g = {'crown': 0}; breath = 1.0; sx, sy = 500 * s, 975 * s
            bb0 = im.getchannel('A').getbbox(); g['crown'] = bb0[1] if bb0 else 0
        else:
            ak = shot.get('_ant', [None] * (i + 1))[i]
            if ak:                         # antennae droop eases in; the balls spring after beats and hops
                dv, sw = antennae_at(ak, f); spec = dict(spec, antennae=dv, antennae_sway=sw)
            im, g = rig.card(spec, st['pose'], st['expr'], st['facing'], s, st['lid'], mouth, prop=st.get('prop'))
            breath = 1 + 0.004 * math.sin(2 * math.pi * (f / FPS) / 2.8 + i)            # rule 28, anchored at the soles
            if abs(breath - 1) > 1e-4:
                im = im.resize((im.width, int(round(im.height * breath))), Image.BICUBIC)
            sx, sy = 300 * s, 975 * s * breath
        ft0 = feet_of(im.getchannel('A'), sx)                 # feet measured before the lean rotation (stable stroke band)
        if abs(st['lean']) > 0.05: im = im.rotate(-st['lean'], resample=Image.BICUBIC, center=(sx, sy))
        im = tint_card(im, meta.get('tint', '#fff8f0'))
        fig_h = 777 * s
        ground = meta['horizon_y'] + dk * (meta['ground_y'] - meta['horizon_y']) if dk != 1.0 else meta['ground_y']
        gx = st['x'] * W; gy = ground - st['lift'] * fig_h
        if spec.get('_near'): gy = H + 0.28 * fig_h                    # near OTS character: feet below the frame
        if st.get('rig') and (shot.get('camera') or {}).get('move') == 'follow':   # follow cam: the rider stays put
            gx += (G['cams'][k].at(f)['x'] - 0.5) * W                                 # while the plate scrolls past
        if st.get('rig'):
            sg = anim.screen_side(spec.get('view', 'rear'))     # rider-side -> screen: rear view keeps the side
            r = st['rig']; tot = r['lean'] if r.get('lean') is not None else (r.get('bike_lean') or 0) + 0.6 * (r.get('body_lean') or 0)
            if spec.get('view', 'rear') in ('rear', 'front'):  # chase cam: keep the rider's hips where the shot puts them,
                gx -= sg * 0.45 * fig_h * math.sin(math.radians(tot))   # so the wheels swing out under a lean
            gx += (r.get('contact_dx') or 0) * fig_h * sg
        ox, oy = int(round(gx - sx)), int(round(gy - sy))
        ft = feet_of(im.getchannel('A'), sx)
        if ft and (abs(st['lean']) > 0.05 or st.get('rig')): oy += int(round(sy - ft['y'])) - 1   # re-plant: lean drops a foot; bike cards' wheels sit above 975
        if ft0 and ft:     # report the foot strokes' x after the rotation, from the unrotated band (rotation about the soles)
            th = math.radians(st['lean'])
            rx = lambda x: None if x is None else sx + (x - sx) * math.cos(th)
            ft = {'y': ft['y'], 'l': rx(ft0['l']), 'r': rx(ft0['r'])}
        # contact shadow: soft blue-grey ellipse, shrinks and fades as the character leaves the ground
        kk = clamp(st['lift'] / 0.1); r = 75 * s * (1 - 0.4 * kk)
        sh = Image.new('L', (int(4 * r) + 4, int(r) + 4), 0)
        ImageDraw.Draw(sh).ellipse((r, sh.height / 2 - 0.16 * r, 3 * r, sh.height / 2 + 0.16 * r), fill=int(105 * (1 - 0.5 * kk)))
        sh = sh.filter(ImageFilter.GaussianBlur(max(1, r * 0.08)))
        col = Image.new('RGBA', sh.size, (52, 50, 78, 255))
        base.paste(col, (int(gx - 2 * r), int(ground - sh.height / 2)), sh)
        base.alpha_composite(im, (ox, oy))
        if clean is not None and not spec.get('_near') and not st.get('rig'): occlude(base, clean, im, ox, oy, gx, ground, meta, k, f)
        bb = im.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
        out.append({'id': spec.get('id', f'c{i}'), 'grounded': st['grounded'] and not st['moving'] and not spec.get('_near'), 'moving': st['moving'],
                    'planted': st['grounded'] and not st['moving'] and not st.get('rig') and not spec.get('_near'),   # a riding bike rolls: no foot lock
                    'near': bool(spec.get('_near')),
                    'foot_y': ft['y'] + oy if ft else None, 'foot_l': ft['l'] + ox if ft and ft['l'] is not None else None,
                    'foot_r': ft['r'] + ox if ft and ft['r'] is not None else None, 'ground_y': ground,
                    'bbox': [bb[0] + ox, bb[1] + oy, bb[2] + ox, bb[3] + oy] if bb else None,
                    'face': None if spec.get('view') in ('rear', 'top') else
                            [gx - 125 * s, oy + g['crown'], gx + 125 * s, oy + g['crown'] + 240 * s],   # head ~2a x 2b card units
                    'head': [gx, oy + g['crown']], 'scale': s, 'rig': {k: (round(v, 1) if isinstance(v, float) else v) for k, v in st['rig'].items()} if st.get('rig') else None, 'pose': list(st['pose']), 'facing': st['facing'], 'expr': st['expr'], 'mouth': mouth, 'lid': st['lid']})
    return out


FULL_FX = {'dust_storm', 'flash_flood', 'rain'}                       # placed full-frame
LONG_FX = FULL_FX | {'ice_pane', 'air_hockey_overlay'}               # last from their word to the end of the shot


def place_fx(base, k, f, chars):
    shot = G['shots'][k]; sp = G['spans'][k]; mod = G['fx']; out = []
    for e in shot.get('fx', []) + shot.get('_auto_fx', []):
        land, wf = anim.beat_frame((sp['w0'], sp['w1']), G['words'], e.get('at_word', 0))
        if '_frame' in e: land = wf = e['_frame']
        if e['name'] == 'path_line' and 'dur' not in e:     # a track diagram plays across the rest of the shot (or cut-in)
            end = sp['f1']
            ins_ = shot.get('_insert')
            if ins_ and ins_[0] <= land < ins_[1]: end = ins_[1]
            start = land; dur = max(8, end - land + 6)
        elif e['name'] in LONG_FX and 'dur' not in e:     # environment fx start on their word and fill the shot
            start = wf - int(round(float(e.get('peak', 0.0)) * FPS))
            end = e.get('_hold_until', sp['f1'] + 2)
            dur = max(8, int(round((end - start) / (0.91 if '_hold_until' in e else 1.0))))
        else:
            dur = max(4, int(round(float(e.get('dur', 0.8)) * FPS)))
            peak = float(e.get('peak', 0.0 if e['name'] in LONG_FX else 0.3))
            start = wf - int(round(peak * dur))         # the effect peaks on the word onset
        hold = e.get('_hold_until')
        if not (start <= f < start + dur or (hold is not None and start <= f < hold)): continue
        ins_ = shot.get('_insert')
        if e['name'] == 'path_line' and ins_ and ins_[0] <= land < ins_[1] and f >= ins_[1]: continue   # the diagram ends with its cut-in
        t = (f - start + 0.5) / dur
        if hold is not None: t = min(t, 0.91)                # chained stage: hold the full sheet, the next takes over
        size = int(float(e.get('size', 0.9 if e['name'] == 'path_line' else 0.35)) * W)
        if e['name'] in FULL_FX: size = H; e = dict(e, x=0.5, y=0.5)          # full-frame: the square covers the frame
        kw = {kk: v for kk, v in e.items() if kk not in ('name', 'at_word', 'x', 'y', 'size', 'dur', 'peak', 'kick', 'on', 'anchor', 'dx') and not kk.startswith('_')}
        if e['name'] == 'path_line':          # racing lines named in the plate JSON follow the real road (sets: paths.py)
            ins_ = shot.get('_insert'); pl = ins_[2] if (ins_ and ins_[0] <= f < ins_[1]) else shot['_plate']
            ppaths = G['plates'][pl][1].get('paths', {})
            if any(isinstance(kw.get(kk), str) and kw[kk] in ppaths for kk in ('planned', 'actual')):
                size = H; e = dict(e, x=0.5, y=0.5); kw.setdefault('scale', 0.5)
                u_ = size / 2 * 0.9 * float(kw['scale']); o_x = W / 2 - size / 2
                for kk in ('planned', 'actual'):
                    if isinstance(kw.get(kk), str) and kw[kk] in ppaths:
                        kw[kk] = [((px * W - o_x - size / 2) / u_, (py * H - size / 2) / u_) for px, py in ppaths[kw[kk]]]
        if mod and 'line' not in kw and chars: kw['line'] = 10 * chars[0].get('scale', 0.5)   # fx area: line = 10 x card scale
        if e['name'] == 'sliding_rock' and isinstance(kw.get('path'), list):     # shots.json: frame fractions -> canvas
            pts = kw['path']; xs = [p_[0] * W for p_ in pts]; ys = [p_[1] * H for p_ in pts]
            cxp, cyp = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            size = int(max(size, 1.5 * max(max(xs) - min(xs), max(ys) - min(ys)) + 0.2 * W))
            e = dict(e, x=cxp / W, y=cyp / H)
            kw['path'] = [((px - cxp) / size + 0.5, (py - cyp) / size + 0.5) for px, py in zip(xs, ys)]
        try:
            im = (mod.render if mod else stub_fx)(e['name'], t, size, **kw)
        except KeyError:
            im = stub_fx(e['name'], t, size)
        x, y = float(e.get('x', 0.5)) * W, float(e.get('y', 0.5)) * H
        if e.get('on'):
            c = next((c for c in chars if c['id'] == e['on']), None)
            if c and c['bbox']:
                if e.get('anchor', 'head') == 'head': x, y = c['head'][0] + float(e.get('dx', 0)) * W, c['head'][1] - size * 0.15
                elif e['anchor'] == 'above': x, y = c['head'][0] + float(e.get('dx', 0)) * W, c['head'][1] - size * 0.5   # symbol clear of the head
                elif e['anchor'] == 'bars': x, y = (c['bbox'][0] + c['bbox'][2]) / 2, c['bbox'][1] + 0.42 * (c['bbox'][3] - c['bbox'][1])
                else: x, y = (c['bbox'][0] + c['bbox'][2]) / 2, c['ground_y']
        cy = {'dust_puff': 0.72, 'splash': 0.72, 'lean_arc': 1.0}.get(e['name'], 0.5)             # ground-anchored effects
        dx_, dy_ = int(x - size / 2), int(y - size * cy); im = im.convert('RGBA')
        if dx_ < 0 or dy_ < 0:                # a canvas bigger than the frame (plate-sized path_line): crop the overhang
            im = im.crop((max(0, -dx_), max(0, -dy_), im.width, im.height)); dx_, dy_ = max(0, dx_), max(0, dy_)
        base.alpha_composite(im, (dx_, dy_))
        out.append({'name': e['name'], 't': round(t, 3)})
        if e['name'] == 'path_line' and mod: path_riders(base, k, f, e, t, size, x - size / 2, y - size * cy, kw)
    return out


def path_riders(base, k, f, e, t, size, ox, oy, kw):
    """Top-view riders with "path" ride the fx path_line's actual track, in step with its drawn-on head
    (fx.fx_path_line: af = smooth(seg(t, 0.28, 0.78)), chaikin(PATHS[...]), sub_path), nose along the heading."""
    mod = G['fx']; shot = G['shots'][k]
    for i, spec in enumerate(shot.get('characters', [])):
        ins = spec.get('insert'); ii = shot.get('_insert')
        if ins and ii and ii[0] <= f < ii[1]: spec = dict(spec, **{kk: ins[kk] for kk in ('rig', 'view', 'path') if kk in ins})
        if not spec.get('path') or spec.get('view') != 'top' or not spec.get('rig'): continue
        act = kw.get('actual', 'wide_arc')
        src = act if isinstance(act, list) else mod.PATHS[spec['path'] if spec['path'] in getattr(mod, 'PATHS', {}) else act]
        n = size; u = n / 2 * 0.9 * float(kw.get('scale', 1.0)); c = n / 2
        pts = [(c + px * u, c + py * u, 1.0) for px, py in mod.chaikin(src)]
        af = max(0.004, mod.smooth(mod.seg(t, 0.28, 0.78)))
        head = mod.sub_path(pts, 0, af); hx, hy = head[-1][0], head[-1][1]
        px, py = (head[-2][0], head[-2][1]) if len(head) > 1 else (hx, hy + 1)
        ang = math.degrees(math.atan2(hx - px, -(hy - py))) if (hx, hy) != (px, py) else 0.0
        st = G['tracks'][k][i].state_at(f)
        sc = 0.17 * W / 1000 / 0.35                         # the bike is ~17 % of the frame width long
        im = G['rig'].ride_card(spec, sc, st['rig'] or {}, st['expr'], None, st['lid'])
        bb = im.getchannel('A').getbbox() or (0, 0, im.width, im.height)
        im = im.crop(bb); pad = int(max(im.size) * 0.75)                    # pivot = the drawing's centre
        sq = Image.new('RGBA', (2 * pad, 2 * pad), (0, 0, 0, 0)); sq.paste(im, (pad - im.width // 2, pad - im.height // 2))
        sq = sq.rotate(-ang, resample=Image.BICUBIC)
        px_, py_ = int(ox + hx - pad), int(oy + hy - pad)
        if px_ <= -sq.width or py_ <= -sq.height or px_ >= W or py_ >= H: continue     # rider off the frame
        if px_ < 0 or py_ < 0: sq = sq.crop((max(0, -px_), max(0, -py_), sq.width, sq.height)); px_, py_ = max(0, px_), max(0, py_)
        base.alpha_composite(sq, (px_, py_))


def camera_xform(img, c):
    """Zoom c['zoom'] about the view centre (fractions), roll in degrees, plus kick offsets in px. Never shows a border."""
    th = math.radians(c['roll']); cs, sn = abs(math.cos(th)), abs(math.sin(th))
    z = max(c['zoom'], cs + (H / W) * sn, (W / H) * sn + cs)
    hx = (W / z * cs + H / z * sn) / 2; hy = (W / z * sn + H / z * cs) / 2
    cx = clamp(c['x'] * W + c['dx'], hx, W - hx); cy = clamp(c['y'] * H + c['dy'], hy, H - hy)
    co, si = math.cos(th), math.sin(th)
    # output (u, v) -> input (x, y) = centre + R(th) * ((u, v) - screen centre) / z
    a, b = co / z, -si / z; d, e = si / z, co / z
    coeffs = (a, b, cx - a * W / 2 - b * H / 2, d, e, cy - d * W / 2 - e * H / 2)
    out = img.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    def to_screen(x, y):          # inverse of the mapping above
        dx, dy = x - cx, y - cy
        return W / 2 + z * (co * dx + si * dy), H / 2 + z * (-si * dx + co * dy)
    return out, to_screen, {'zoom': round(z, 4), 'cx': round(cx, 1), 'cy': round(cy, 1), 'roll': round(c['roll'], 3)}


RIDE_SPEED, RIDE_MAX = 1.0, 3.0      # m/s and metres of camera travel per shot (2.5D parallax breaks down beyond ~3 m)


def ride_distance(k, f, meta):
    """How far the chase camera has moved into the plate at frame f. On for shots with a rider seen from behind
    (or "ride": {"speed": m/s, "max": m} on the shot; "ride": false turns it off) when the plate has a depth map."""
    shot = G['shots'][k]; r = shot.get('ride')
    if r is False or 'depth' not in meta: return 0.0
    if r is None and not any(c.get('rig') and c.get('view') == 'rear' for c in shot.get('characters', [])): return 0.0
    r = r if isinstance(r, dict) else {}
    t = (f - G['spans'][k]['f0']) / FPS
    return min(float(r.get('max', RIDE_MAX)), float(r.get('start', 0.0)) + float(r.get('speed', RIDE_SPEED)) * t)   # start: carry on from the previous shot


def ride_warper(pkey, plate, meta):
    """One parallax rig per worker, for the plate in use (frames come in contiguous chunks)."""
    cache = G.setdefault('_rider', {})
    if pkey not in cache:
        cache.clear(); info = meta['depth']
        dep = PX.load_depth(os.path.join(os.path.dirname(pkey), info['file']), info)
        cache[pkey] = PX.Rider(np.asarray(plate.convert('RGB')), dep, info['f_px'], info['ride_dir'])
    return cache[pkey]


def prop_t(k, f, e):
    """A prop sprite's t at frame f (None = hidden): from its at_word over dur s (default the rest of the shot)."""
    sp = G['spans'][k]; sw = (sp['w0'], sp['w1'])
    a = anim.beat_frame(sw, G['words'], e['at_word'])[1] if 'at_word' in e else sp['f0']
    if 'until_word' in e and f >= anim.beat_frame(sw, G['words'], e['until_word'])[1]: return None
    if e.get('enter') and f < a: return None
    if 't' in e: return float(e['t'])
    dur = float(e['dur']) * FPS if 'dur' in e else max(1, sp['f1'] - a)
    return clamp((f - a) / dur)


def render_shot(k, f):
    shot = G['shots'][k]; pkey = shot['_plate']
    ins = shot.get('_insert'); crop_any = False
    if ins and ins[0] <= f < ins[1]: pkey = ins[2]; crop_any = 'close' in os.path.basename(pkey)   # close cut-ins crop freely
    plate, meta = G['plates'][pkey]
    d_ride = ride_distance(k, f, meta) if pkey == shot['_plate'] else 0.0
    if d_ride > 1e-3:      # resampling softens the ink lines: a light unsharp mask puts the plate's edge density back
        base = Image.fromarray(ride_warper(pkey, plate, meta).warp(d_ride)).filter(ImageFilter.UnsharpMask(1.5, 90, 2)).convert('RGBA')
    else: base = plate.convert('RGBA')
    if shot.get('_bike_prop'):
        kind, sx_ = shot['_bike_prop']; s = meta['px_per_m'] * 1.75 / 777
        im = G['rig'].bike_card(kind, s, view=shot.get('bike_view', '3q'))
        bb = im.getchannel('A').getbbox()
        if bb: base.alpha_composite(im, (int(sx_ * W - 500 * s), int(meta['ground_y'] - bb[3])))
    if shot.get('_props'): PROPS.draw(base, shot['_props'], 'back', f, lambda e: prop_t(k, f, e), meta, W, H)
    chars = place_characters(base, k, f, meta)
    if shot.get('_props'): PROPS.draw(base, shot['_props'], 'front', f, lambda e: prop_t(k, f, e), meta, W, H)
    fxs = place_fx(base, k, f, chars)
    img, to_screen, cam = camera_xform(base.convert('RGB'), G['cams'][k].at(f))
    gk = f'{k}:insert' if (ins and ins[0] <= f < ins[1]) else str(k)          # cut-ins have their own plate grade
    if G['grades'].get(gk): img = GRADE.apply(img, G['grades'][gk])
    if os.environ.get('ENGINE_FINISH', '1') == '1':      # vignette + warm/cool split (+ sepia flashbacks), every frame
        img = GRADE.finish(img, sepia=(shot.get('grade') == 'sepia' and not (ins and ins[0] <= f < ins[1])))
    for c in chars:
        if c['bbox']:
            x0, y0, x1, y1 = c['bbox']; pts = [to_screen(x, y) for x in (x0, x1) for y in (y0, y1)]
            c['screen_bbox'] = [round(min(p[0] for p in pts), 1), round(min(p[1] for p in pts), 1),
                                round(max(p[0] for p in pts), 1), round(max(p[1] for p in pts), 1)]
            if c.get('face'):                     # face box (plate coords) -> screen, for caption placement
                fx0, fy0, fx1, fy1 = c['face']; q = [to_screen(x, y) for x in (fx0, fx1) for y in (fy0, fy1)]
                c['face_screen'] = [round(min(p[0] for p in q)), round(min(p[1] for p in q)), round(max(p[0] for p in q)), round(max(p[1] for p in q))]
    return img, {'shot': shot.get('id', k), 'chars': chars, 'fx': fxs, 'cam': cam, 'crop_any': crop_any}


def motion_blur_x(img, length):
    """Directional box blur along x (whip pans)."""
    n = int(length)
    if n < 2: return img
    a = np.asarray(img).astype(np.float32)
    c = np.cumsum(np.pad(a, ((0, 0), (n, n), (0, 0)), mode='edge'), axis=1)
    out = (c[:, n + n // 2:n + n // 2 + a.shape[1]] - c[:, n // 2:n // 2 + a.shape[1]]) / n
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def shot_of(f):
    for k, sp in enumerate(G['spans']):
        if sp['f0'] <= f < sp['f1']: return k
    return len(G['spans']) - 1


def render_frame(f):
    k = shot_of(f); spans = G['spans']
    # transitions are owned by the incoming shot's "transition": "cut" | "crossfade" | "whip"
    for kk in (k, k + 1):
        if kk == 0 or kk >= len(spans): continue
        tr = G['shots'][kk].get('transition', 'cut'); B = spans[kk]['f0']
        L = XFADE if tr == 'crossfade' else WHIP if tr == 'whip' else 0
        if L and B - L // 2 <= f < B + L // 2:
            u = (f - (B - L // 2) + 0.5) / L
            A, ma = render_shot(kk - 1, f); Bm, mb = render_shot(kk, f)
            if tr == 'crossfade':
                img = Image.blend(A, Bm, smooth(u)); meta = mb if u >= 0.5 else ma
            else:
                d = int(round(W * anim.smoother(u))); direction = G['shots'][kk].get('whip_dir', 1)
                strip = Image.new('RGB', (W * 2, H))
                if direction > 0: strip.paste(A, (0, 0)); strip.paste(Bm, (W, 0)); img = strip.crop((d, 0, d + W, H))
                else: strip.paste(Bm, (0, 0)); strip.paste(A, (W, 0)); img = strip.crop((W - d, 0, 2 * W - d, H))
                speed = W * (anim.smoother(u + 0.5 / L) - anim.smoother(u - 0.5 / L))
                img = motion_blur_x(img, speed * 0.5)
                meta = mb if u >= 0.5 else ma
            meta = dict(meta, transition=tr, transition_u=round(u, 3))
            return f, img, add_caption(img, meta, f)
    img, meta = render_shot(k, f)
    return f, img, add_caption(img, meta, f)


def add_caption(img, meta, f):
    faces = [c['face_screen'] for c in meta.get('chars', []) if c.get('face_screen')]
    box = CAP.draw(img, G['captions'], f, faces, W, H) if G['captions'] else None
    return dict(meta, caption=list(box) if box else None)


def work(args):
    f, out, ext = args
    f, img, meta = render_frame(f)
    p = os.path.join(out, 'frames', f'f_{f:05d}.{ext}')
    if ext == 'png': img.save(p, optimize=False, compress_level=3)
    else: img.save(p, quality=94, subsampling=0)
    meta['f'] = f
    return meta


def beats_report():
    """Every beat's landing frame vs its word, for qa.py."""
    out = []
    for k, trs in G['tracks'].items():
        for c, tr in zip(G['shots'][k].get('characters', []), trs):
            for e in tr.events:
                out.append({'shot': G['shots'][k].get('id', k), 'char': c.get('id'), 'land': e['land'], 'word_frame': e['word'],
                            'word': G['words'][min(len(G['words']) - 1, G['spans'][k]['w0'] + int(e['beat'].get('at_word', 0)))]['word'],
                            'shot_f0': G['spans'][k]['f0'], 'shot_f1': G['spans'][k]['f1']})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('shots'); ap.add_argument('words'); ap.add_argument('out')
    ap.add_argument('--plates', action='append', default=[]); ap.add_argument('--frames', default=None)
    ap.add_argument('--workers', type=int, default=4); ap.add_argument('--audio', default=None)
    ap.add_argument('--png', action='store_true'); ap.add_argument('--length', type=int, default=None); ap.add_argument('--no-grade', action='store_true'); ap.add_argument('--no-mp4', action='store_true')
    a = ap.parse_args()
    a.plates.append(os.path.join(HERE, 'test', 'plates'))
    os.makedirs(os.path.join(a.out, 'frames'), exist_ok=True)
    setup(a.shots, a.words, a.plates)
    lj = os.path.join(os.path.dirname(os.path.abspath(a.words)), 'length.json')
    if a.length is None and os.path.exists(lj): a.length = int(json.load(open(lj))['frames'])
    if a.length:                      # audio owns the picture length: stretch/trim the last shot to match
        G['spans'][-1]['f1'] = max(G['spans'][-1]['f0'] + 1, a.length); G['n'] = a.length
        if a.length < G['spans'][-1]['f0']: raise SystemExit(f'--length {a.length} ends before the last shot starts')
    n = G['n']
    for sh in G['shots']:                       # report rig stand-ins once, in the main process
        for c in sh.get('characters', []):
            G['rig'].bean_kwargs(c)
            if c.get('rig') and G['rig'].bikes: continue          # riders' arms come from bikes.ride()
            for b in [c] + c.get('beats', []):
                ap = b.get('arm_pose')
                for p in (ap if isinstance(ap, list) else [ap] if ap else []): G['rig'].arm_ok(p)
    ext = 'png' if a.png else 'jpg'
    if a.frames and ',' in a.frames:          # a frame list (storyboards: tools/storyboard.py)
        frames = sorted({int(v) for v in a.frames.split(',') if v.strip() and int(v) < n})
    else:
        rng = [int(v) for v in a.frames.split(':')] if a.frames else [0, n]
        frames = list(range(rng[0], min(rng[1], n), rng[2] if len(rng) > 2 else 1))
    print(f"{len(G['shots'])} shots, {n} frames ({n / FPS:.2f} s); fx: {'fx/fx.py' if G['fx'] else 'stub'}; "
          f"mouth: {'bean' if G['rig'].HAS_MOUTH else 'overlay'}; lid: {'bean' if G['rig'].HAS_LID else 'overlay'}", flush=True)
    metas = []
    os.environ['ENGINE_LENGTH'] = str(n)
    if not a.no_grade:                # per-shot grade, solved once from each shot's middle frame
        gp = os.path.join(a.out, 'grade.json'); grades = {}
        for k, (sh, sp) in enumerate(zip(G['shots'], G['spans'])):
            ins = sh.get('_insert')
            mid = [(str(k), (sp['f0'] + sp['f1']) // 2)]
            if ins:
                mid.append((f'{k}:insert', (ins[0] + ins[1]) // 2))
                if ins[0] <= mid[0][1] < ins[1]: mid[0] = (str(k), sp['f0'] + 3 if ins[0] > sp['f0'] + 3 else sp['f1'] - 3)
            for key, fm in mid:
                img, _ = render_shot(k, fm)
                grades[key] = GRADE.solve(img, golden=sh.get('light') == 'golden')
        json.dump(grades, open(gp, 'w'), indent=1); os.environ['ENGINE_GRADE_FILE'] = gp
        print('  grade:', ', '.join(f"{k} {v['before']['lum']:.2f}->g{v['gamma']:.2f}" for k, v in grades.items()), flush=True)
    # ProcessPoolExecutor, not Pool: if a worker dies (e.g. out of memory) Pool.imap waits forever; this raises.
    # Contiguous chunks keep consecutive frames in one worker, so its card cache hits.
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(a.workers, initializer=init_worker, initargs=(a.shots, a.words, a.plates)) as pool:
        for i, m in enumerate(pool.map(work, [(f, a.out, ext) for f in frames], chunksize=12)):
            metas.append(m)
            if i % 150 == 0: print(f'  frame {m["f"]}/{n}', flush=True)
    track = {'fps': FPS, 'size': [W, H], 'n': n, 'spans': [dict(sp, id=s.get('id'), crop=s.get('crop') or s.get('size') == 'close') for s, sp in zip(G['shots'], G['spans'])],
             'beats': beats_report(), 'frames': metas, 'captions': G['captions'], 'words': G['words'], 'transitions': [s.get('transition', 'cut') for s in G['shots']]}
    json.dump(track, open(os.path.join(a.out, 'track.json'), 'w'))
    if not a.no_mp4 and not a.frames:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(a.out, 'frames', f'f_%05d.{ext}')]
        if a.audio: cmd += ['-i', a.audio, '-c:a', 'aac', '-b:a', '192k']
        cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart',
                os.path.join(a.out, 'video.mp4')]
        subprocess.run(cmd, check=True)
        print('wrote', os.path.join(a.out, 'video.mp4'))


if __name__ == '__main__':
    main()

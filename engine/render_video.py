# Engine: shots.json + words.json -> frames -> mp4 (picture only; --audio muxes a track for previews).
# usage: python engine/render_video.py shots.json words.json out_dir [--plates DIR ...] [--frames A:B[:step]] [--workers 4]
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
        cands = [os.path.join(ROOT, 'blender', 'sets', shot['set'], 'plates', name + ext) for ext in ('.png', '.jpg')]
        cands += [os.path.join(d, name + ext) for d in dirs for ext in ('.png', '.jpg')]
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
        G['mouths'][k] = [rig.mouth_track(words[sp['w0']:sp['w1']], sp['f0'] - 30, sp['f1'] + 30) if c.get('talk') else {}
                          for c in s.get('characters', [])]
    n = spans[-1]['f1'] if spans else 0
    G['n'] = n
    return G


BIKES = ('bicycle', 'motorbike', 'nobs_bike')


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
        hw = [175 * s * float(c.get('scale', 1.0)) / W for c in stand]        # half body+arm width, frame fractions
        need = [hw[i] + hw[i + 1] + 0.02 for i in range(len(stand) - 1)]
        xs = [float(c.get('x', 0.5)) for c in stand]
        for i, d in enumerate(need):
            if xs[i + 1] - xs[i] < d:
                mid = (xs[i] + xs[i + 1]) / 2; xs[i], xs[i + 1] = mid - d / 2, mid + d / 2
        shift = max(0.0, hw[0] + 0.01 - xs[0]) - max(0.0, xs[-1] + hw[-1] + 0.01 - 1.0)
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


def place_characters(base, k, f, meta):
    rig = G['rig']; shot = G['shots'][k]; out = []
    order = sorted(range(len(G['tracks'][k])), key=lambda i: shot['characters'][i].get('z', 0))
    for i in order:
        tr = G['tracks'][k][i]; spec = shot['characters'][i]
        ins = spec.get('insert')
        if ins and shot.get('_insert') and shot['_insert'][0] <= f < shot['_insert'][1]:
            spec = dict(spec, **{kk: ins[kk] for kk in ('rig', 'view') if kk in ins})
        if spec.get('path') and spec.get('view') == 'top' and any(e['name'] == 'path_line' for e in shot.get('fx', [])) and G['fx']:
            continue                                   # drawn by path_riders() on the track diagram
        st = tr.state_at(f)
        if spec.get('enter_at_word') is not None:
            wf = anim.beat_frame((G['spans'][k]['w0'], G['spans'][k]['w1']), G['words'], spec['enter_at_word'])[0]
            if f < wf: continue
        s = meta['px_per_m'] * float(spec.get('height_m', 1.75)) / (3.5 * 2 * 111) * float(spec.get('scale', 1.0))
        mouth = G['mouths'][k][i].get(f, 'closed') if spec.get('talk') else None
        if st.get('rig'):            # rider on a bike (bikes.ride): 1000x1000 card, ground at 975, no breathing (it's riding)
            rs = dict(spec)
            if spec.get('_sticker') and spec.get('hat') == 'helmet': rs.setdefault('sticker', spec['_sticker'])
            im = rig.ride_card(rs, s, st['rig'], st['expr'], mouth, st['lid'], crank=f * 14.0)
            g = {'crown': 0}; breath = 1.0; sx, sy = 500 * s, 975 * s
            bb0 = im.getchannel('A').getbbox(); g['crown'] = bb0[1] if bb0 else 0
        else:
            im, g = rig.card(spec, st['pose'], st['expr'], st['facing'], s, st['lid'], mouth, prop=st.get('prop'))
            breath = 1 + 0.004 * math.sin(2 * math.pi * (f / FPS) / 2.8 + i)            # rule 28, anchored at the soles
            if abs(breath - 1) > 1e-4:
                im = im.resize((im.width, int(round(im.height * breath))), Image.BICUBIC)
            sx, sy = 300 * s, 975 * s * breath
        ft0 = feet_of(im.getchannel('A'), sx)                 # feet measured before the lean rotation (stable stroke band)
        if abs(st['lean']) > 0.05: im = im.rotate(-st['lean'], resample=Image.BICUBIC, center=(sx, sy))
        im = tint_card(im, meta.get('tint', '#fff8f0'))
        fig_h = 777 * s
        gx = st['x'] * W; gy = meta['ground_y'] - st['lift'] * fig_h
        if spec.get('_near'): gy = H + 0.28 * fig_h                    # near OTS character: feet below the frame
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
        base.paste(col, (int(gx - 2 * r), int(meta['ground_y'] - sh.height / 2)), sh)
        base.alpha_composite(im, (ox, oy))
        bb = im.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
        out.append({'id': spec.get('id', f'c{i}'), 'grounded': st['grounded'] and not st['moving'] and not spec.get('_near'), 'moving': st['moving'],
                    'planted': st['grounded'] and not st['moving'] and not st.get('rig') and not spec.get('_near'),   # a riding bike rolls: no foot lock
                    'near': bool(spec.get('_near')),
                    'foot_y': ft['y'] + oy if ft else None, 'foot_l': ft['l'] + ox if ft and ft['l'] is not None else None,
                    'foot_r': ft['r'] + ox if ft and ft['r'] is not None else None, 'ground_y': meta['ground_y'],
                    'bbox': [bb[0] + ox, bb[1] + oy, bb[2] + ox, bb[3] + oy] if bb else None,
                    'head': [gx, oy + g['crown']], 'scale': s, 'rig': {k: (round(v, 1) if isinstance(v, float) else v) for k, v in st['rig'].items()} if st.get('rig') else None, 'pose': list(st['pose']), 'facing': st['facing'], 'expr': st['expr'], 'mouth': mouth, 'lid': st['lid']})
    return out


def place_fx(base, k, f, chars):
    shot = G['shots'][k]; sp = G['spans'][k]; mod = G['fx']; out = []
    for e in shot.get('fx', []):
        land, wf = anim.beat_frame((sp['w0'], sp['w1']), G['words'], e.get('at_word', 0))
        if e['name'] == 'path_line' and 'dur' not in e:     # a track diagram plays across the rest of the shot
            start = land; dur = max(8, sp['f1'] - land + 6)
        else:
            dur = max(4, int(round(float(e.get('dur', 0.8)) * FPS)))
            peak = float(e.get('peak', 0.3))
            start = wf - int(round(peak * dur))         # the effect peaks on the word onset
        if not start <= f < start + dur: continue
        t = (f - start + 0.5) / dur
        size = int(float(e.get('size', 0.9 if e['name'] == 'path_line' else 0.35)) * W)
        kw = {kk: v for kk, v in e.items() if kk not in ('name', 'at_word', 'x', 'y', 'size', 'dur', 'peak', 'kick', 'on', 'anchor')}
        if mod and 'line' not in kw and chars: kw['line'] = 10 * chars[0].get('scale', 0.5)   # fx area: line = 10 x card scale
        try:
            im = (mod.render if mod else stub_fx)(e['name'], t, size, **kw)
        except KeyError:
            im = stub_fx(e['name'], t, size)
        x, y = float(e.get('x', 0.5)) * W, float(e.get('y', 0.5)) * H
        if e.get('on'):
            c = next((c for c in chars if c['id'] == e['on']), None)
            if c and c['bbox']:
                if e.get('anchor', 'head') == 'head': x, y = c['head'][0] + float(e.get('dx', 0)) * W, c['head'][1] - size * 0.15
                else: x, y = (c['bbox'][0] + c['bbox'][2]) / 2, c['ground_y']
        cy = {'dust_puff': 0.72, 'splash': 0.72, 'lean_arc': 1.0}.get(e['name'], 0.5)             # ground-anchored effects
        base.alpha_composite(im.convert('RGBA'), (int(x - size / 2), int(y - size * cy)))
        out.append({'name': e['name'], 't': round(t, 3)})
        if e['name'] == 'path_line' and mod: path_riders(base, k, f, e, t, size, x - size / 2, y - size * cy, kw)
    return out


def path_riders(base, k, f, e, t, size, ox, oy, kw):
    """Top-view riders with "path" ride the fx path_line's actual track, in step with its drawn-on head
    (fx.fx_path_line: af = smooth(seg(t, 0.28, 0.78)), chaikin(PATHS[...]), sub_path), nose along the heading."""
    mod = G['fx']; shot = G['shots'][k]
    for i, spec in enumerate(shot.get('characters', [])):
        if not spec.get('path') or spec.get('view') != 'top' or not spec.get('rig'): continue
        spec_path = spec['path'] if spec['path'] in getattr(mod, 'PATHS', {}) else kw.get('actual', 'wide_arc')
        n = size; u = n / 2 * 0.9 * float(kw.get('scale', 1.0)); c = n / 2
        pts = [(c + px * u, c + py * u, 1.0) for px, py in mod.chaikin(mod.PATHS[spec_path])]
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
        base.alpha_composite(sq, (int(ox + hx - pad), int(oy + hy - pad)))


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


def render_shot(k, f):
    shot = G['shots'][k]; pkey = shot['_plate']
    ins = shot.get('_insert')
    if ins and ins[0] <= f < ins[1]: pkey = ins[2]
    plate, meta = G['plates'][pkey]
    base = plate.convert('RGBA')
    if shot.get('_bike_prop'):
        kind, sx_ = shot['_bike_prop']; s = meta['px_per_m'] * 1.75 / 777
        im = G['rig'].bike_card(kind, s, view=shot.get('bike_view', '3q'))
        bb = im.getchannel('A').getbbox()
        if bb: base.alpha_composite(im, (int(sx_ * W - 500 * s), int(meta['ground_y'] - bb[3])))
    chars = place_characters(base, k, f, meta)
    fxs = place_fx(base, k, f, chars)
    img, to_screen, cam = camera_xform(base.convert('RGB'), G['cams'][k].at(f))
    for c in chars:
        if c['bbox']:
            x0, y0, x1, y1 = c['bbox']; pts = [to_screen(x, y) for x in (x0, x1) for y in (y0, y1)]
            c['screen_bbox'] = [round(min(p[0] for p in pts), 1), round(min(p[1] for p in pts), 1),
                                round(max(p[0] for p in pts), 1), round(max(p[1] for p in pts), 1)]
    return img, {'shot': shot.get('id', k), 'chars': chars, 'fx': fxs, 'cam': cam}


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
            return f, img, meta
    img, meta = render_shot(k, f)
    return f, img, meta


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
    ap.add_argument('--png', action='store_true'); ap.add_argument('--length', type=int, default=None); ap.add_argument('--no-mp4', action='store_true')
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
    rng = [int(v) for v in a.frames.split(':')] if a.frames else [0, n]
    ext = 'png' if a.png else 'jpg'
    frames = list(range(rng[0], min(rng[1], n), rng[2] if len(rng) > 2 else 1))
    print(f"{len(G['shots'])} shots, {n} frames ({n / FPS:.2f} s); fx: {'fx/fx.py' if G['fx'] else 'stub'}; "
          f"mouth: {'bean' if G['rig'].HAS_MOUTH else 'overlay'}; lid: {'bean' if G['rig'].HAS_LID else 'overlay'}", flush=True)
    metas = []
    os.environ['ENGINE_LENGTH'] = str(n)
    # ProcessPoolExecutor, not Pool: if a worker dies (e.g. out of memory) Pool.imap waits forever; this raises.
    # Contiguous chunks keep consecutive frames in one worker, so its card cache hits.
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(a.workers, initializer=init_worker, initargs=(a.shots, a.words, a.plates)) as pool:
        for i, m in enumerate(pool.map(work, [(f, a.out, ext) for f in frames], chunksize=12)):
            metas.append(m)
            if i % 150 == 0: print(f'  frame {m["f"]}/{n}', flush=True)
    track = {'fps': FPS, 'size': [W, H], 'n': n, 'spans': [dict(sp, id=s.get('id'), crop=s.get('crop') or s.get('size') == 'close') for s, sp in zip(G['shots'], G['spans'])],
             'beats': beats_report(), 'frames': metas, 'transitions': [s.get('transition', 'cut') for s in G['shots']]}
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

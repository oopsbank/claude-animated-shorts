# Character cards for the engine: wraps characters/scripts/bean.py `character()`.
#   - renders at the size the plate needs, from bean's 4x supersampled canvas (no upscaling blur in medium shots);
#   - caches cards per worker process;
#   - lip sync: viseme sequence from the letters of each word (words.json), drawn through bean's `mouth=` when wardrobe
#     ships it, otherwise with a stand-in overlay that paints over the expression's mouth;
#   - blinks: bean's `lid=` (0 open .. 1 shut) when available, otherwise a stand-in overlay.
# The overlays copy bean.py's face geometry (cx, hy, u, facing offsets). They are temporary: delete them once
# bean.py takes `mouth=` and `lid=`, which `inspect.signature` detects automatically.
import os, sys, inspect, math
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'characters', 'scripts'))
import bean  # noqa: E402

PARAMS = set(inspect.signature(bean.character).parameters)
HAS_MOUTH, HAS_LID, HAS_BLINK = 'mouth' in PARAMS, 'lid' in PARAMS, 'blink' in PARAMS
ADULT_H = 975 - (975 - 3.5 * 2 * 111)       # adult figure height in card units (crown -> soles) = 777
SOLE_Y = 975
INK = bean.INK
MOUTH_C, TONGUE_C = bean.MOUTH, bean.TONGUE

# ---------------------------------------------------------------- hi-res capture of bean's supersampled canvas


try:
    import bikes                         # rider rigs (wardrobe); imported after the patch so it sees _Grab
except Exception as e:                   # noqa: BLE001
    bikes = None; print('  [rig] bikes.py unavailable:', e)


def _hires(fn, kw, size, scale):
    """Run a card function and downsample its final 4x supersampled image to `scale`: the image is caught at the
    card function's own last resize (4x -> design size), so layered views (rear, side, riders) come out whole."""
    _final.clear()
    Image.Image.resize = _spy
    try: lo = fn(**kw)
    finally: Image.Image.resize = _resize
    out = (max(1, int(size[0] * scale)), max(1, int(size[1] * scale)))
    big = next((im for im in reversed(_final) if im.size == (size[0] * bean.S, size[1] * bean.S)), None)
    if scale <= 1.0 or big is None: return lo.resize(out, Image.LANCZOS)
    return big.resize(out, Image.LANCZOS)


_final = []
_resize = Image.Image.resize


def _spy(self, size, *a, **k):
    if self.mode == 'RGBA' and tuple(size) in ((600, 1000), (1000, 1000)) and self.size == (size[0] * bean.S, size[1] * bean.S): _final.append(self)
    return _resize(self, size, *a, **k)


def _render(kw, scale):
    """bean card at `scale` x the 600x1000 design size, downsampled from the 4x canvas."""
    return _hires(bean.character, kw, (600, 1000), scale)


# ---------------------------------------------------------------- spec -> bean kwargs
import re
_SRC = open(bean.__file__).read()
ARM_POSES = set(re.findall(r"pose == '(\w+)'", _SRC)) | {'hang'}
HATS = set(re.findall(r"kind (?:==|in) \(?'(\w+)'", _SRC)) | {'cap', 'beanie', 'hardhat', 'tophat'}
STANDIN = {'arm': {'ride': 'hold'}, 'hat': {'helmet': 'hardhat'}}
OUTFIT_COL = {'stripes': '#f2f2f2', 'buttons': '#e8c45a', 'tie': '#c0353a', 'belt': '#3a2a20', 'apron': '#f4f1e8',
              'overalls': '#3b5b9a', 'coat_open': '#f4f4f4', 'collar': '#f4f4f4'}
_warned = set()


def _warn(msg):
    if msg not in _warned and os.environ.get('ENGINE_QUIET') != '1': _warned.add(msg); print('  [rig stand-in]', msg, flush=True)


def arm_ok(p):
    if p in ARM_POSES: return p
    sub = STANDIN['arm'].get(p, 'hang'); _warn(f'arm pose {p!r} not in bean.py yet -> {sub!r}'); return sub


def bean_kwargs(spec):
    kw = {k: v for k, v in spec.items() if k in PARAMS and v is not None}
    if 'color' in spec and 'shirt' not in kw: kw['shirt'] = spec['color']
    if isinstance(kw.get('outfit'), str): kw.pop('outfit')            # named outfits come with wardrobe; ignore for now
    if isinstance(kw.get('outfit'), (list, tuple)):
        kw['outfit'] = tuple((i, OUTFIT_COL.get(i, '#f2f2f2')) if isinstance(i, str) else tuple(i) for i in kw['outfit'])
    if kw.get('hat') and kw['hat'] not in HATS:
        sub = STANDIN['hat'].get(kw['hat']); _warn(f"hat {kw['hat']!r} not in bean.py yet -> {sub!r}")
        if sub: kw['hat'] = sub
        else: kw.pop('hat')
    return kw


def face_geom(kw, scale):
    """Face anchor points in card pixels, mirroring bean.character()'s layout."""
    B = bean.BUILDS[kw.get('build', 'adult')]; a, b = B['a'], B['b']; HH = 2 * b; u = 2 * a / 100
    total = HH * (1 + B['torso'] + B['legs']); crown = 975 - total; hy = crown + b
    facing = float(kw.get('facing', 0.0)); fcx = 300 + facing * 4 * u
    return {'u': u * scale, 'ex': (fcx + 7 * u * facing) * scale, 'cy': hy * scale, 'mx': (fcx + 8 * u * facing) * scale,
            'my': (hy + 20 * u) * scale, 'crown': crown * scale, 'head': (300 * scale, hy * scale, a * scale, b * scale)}


def _skin_at(card, box):
    """Median non-ink, non-white colour inside box (the shaded skin under a face feature)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    a = np.asarray(card.crop((x0, y0, x1, y1))).reshape(-1, 4).astype(np.int32)
    lum = a[:, :3].mean(1)
    sel = a[(a[:, 3] > 250) & (lum > 120) & (lum < 250) & (np.abs(a[:, 0] - a[:, 2]) > 6)]
    if len(sel) < 10: sel = a[(a[:, 3] > 250) & (lum > 120)]
    if len(sel) == 0: return (255, 226, 194)
    return tuple(int(v) for v in np.median(sel[:, :3], 0))


def _erase(card, box, pad):
    """Remove a face feature inside ellipse `box`: ink/mouth pixels are replaced by the surrounding skin, then the area
    is blurred so the crescent shading gradient carries through, and pasted back with a feathered edge (no seam)."""
    from PIL import ImageFilter
    x0, y0, x1, y1 = [int(v) for v in box]; p = int(pad)
    reg = card.crop((x0 - p, y0 - p, x1 + p, y1 + p)); a = np.asarray(reg).astype(np.float32)
    lum = a[..., :3].mean(-1); skin = (a[..., 3] > 250) & (lum > 120) & (np.abs(a[..., 0] - a[..., 2]) > 6)
    fill = np.median(a[skin][:, :3], 0) if skin.sum() > 10 else np.array([255, 226, 194], np.float32)
    b = a.copy(); b[~skin, :3] = fill; b[..., 3] = a[..., 3]
    for _ in range(3):            # spread skin into the holes, keep the real skin pixels
        bl = np.asarray(Image.fromarray(b.astype(np.uint8)).filter(ImageFilter.GaussianBlur(p / 2))).astype(np.float32)
        b[~skin, :3] = bl[~skin, :3]
    patch = Image.fromarray(b.astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(1, p / 4)))
    m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).ellipse((p, p, p + x1 - x0, p + y1 - y0), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(max(1, p / 3)))
    out = card.copy(); out.paste(patch.convert('RGB'), (x0 - p, y0 - p), m)
    return out


# ---------------------------------------------------------------- overlays (stand-ins)
def draw_lid(card, g, lid, expr):
    if lid <= 0: return card
    card = card.copy()
    u = g['u']; cy = g['cy']
    big = expr == 'shock'
    for x in (g['ex'] - (11.5 if big else 13) * u, g['ex'] + (11.5 if big else 13) * u):
        rx, ry = (12.5 if big else 11) * u, (12.5 if big else 7.5) * u
        if lid >= 1:
            card = _erase(card, (x - rx, cy - ry, x + rx, cy + ry), 3 * u); d = ImageDraw.Draw(card)
            d.arc((x - 8 * u, cy - 6 * u, x + 8 * u, cy + 5 * u), 15, 165, fill=INK, width=max(1, int(3.6 * u)))
        else:   # half: upper lid comes down to the middle of the eye
            skin = _skin_at(card, (x - 16 * u, cy - 15 * u, x + 16 * u, cy + 15 * u)); d = ImageDraw.Draw(card)
            d.chord((x - rx, cy - ry, x + rx, cy + ry), 180, 360, fill=skin)
            d.line((x - 9 * u, cy + 0.5 * u, x + 9 * u, cy + 0.5 * u), fill=INK, width=max(1, int(3.8 * u)))
    return card


HAPPY = {'grin', 'smile', 'smug'}


def draw_mouth(card, g, shape, expr, moustache=False):
    """Stand-in viseme: paint over the expression's mouth with sampled skin, then draw the shape."""
    u = g['u']; mx, my = g['mx'], g['my']
    top = my - (3 if moustache else 9.5) * u
    card = _erase(card, (mx - 14 * u, top, mx + 14 * u, my + 19 * u), 4 * u); d = ImageDraw.Draw(card)
    w = max(1, int(2.6 * u)); lw = max(1, int(4 * u))
    if shape == 'closed':
        if expr in HAPPY: d.arc((mx - 7 * u, my - 5 * u, mx + 7 * u, my + 3 * u), 20, 160, fill=INK, width=lw)
        else: d.line((mx - 6 * u, my, mx + 6 * u, my), fill=INK, width=lw)
    elif shape == 'small':
        d.ellipse((mx - 5 * u, my - 2 * u, mx + 5 * u, my + 3.5 * u), fill=MOUTH_C, outline=INK, width=w)
    elif shape == 'open':
        d.ellipse((mx - 8 * u, my - 4 * u, mx + 8 * u, my + 10 * u), fill=MOUTH_C, outline=INK, width=w)
        d.chord((mx - 5 * u, my + 3 * u, mx + 5 * u, my + 9 * u), 180, 360, fill=TONGUE_C)
    elif shape == 'wide':
        d.rounded_rectangle((mx - 11 * u, my - 4 * u, mx + 11 * u, my + 6 * u), radius=int(4 * u), fill=MOUTH_C, outline=INK, width=w)
        d.rectangle((mx - 9.5 * u, my - 2.6 * u, mx + 9.5 * u, my - 0.2 * u), fill=(255, 255, 255))
    elif shape == 'O':
        d.ellipse((mx - 5 * u, my - 5 * u, mx + 5 * u, my + 8 * u), fill=MOUTH_C, outline=INK, width=w)
    elif shape == 'smile':     # smile-talk: open grin
        d.chord((mx - 10 * u, my - 6 * u, mx + 10 * u, my + 8 * u), 0, 180, fill=MOUTH_C)
        d.rectangle((mx - 9 * u, my - 0.5 * u, mx + 9 * u, my + 1.8 * u), fill=(255, 255, 255))
        d.arc((mx - 10 * u, my - 6 * u, mx + 10 * u, my + 8 * u), 0, 180, fill=INK, width=w)
        d.line((mx - 10 * u, my + 1, mx + 10 * u, my + 1), fill=INK, width=w)
    return card


# ---------------------------------------------------------------- lip sync
VOWEL = {'a': 'open', 'h': 'open', 'e': 'wide', 'i': 'wide', 'y': 'wide', 'o': 'O', 'u': 'O', 'w': 'O', 'q': 'O'}
LIPS = {'m': 'closed', 'b': 'closed', 'p': 'closed', 'f': 'small', 'v': 'small'}


def visemes(word):
    """Mouth shapes for a word from its letters: vowels open the mouth, m/b/p close it, f/v and the rest stay small."""
    w = ''.join(c for c in word.lower() if c.isalpha())
    seq = []
    for c in w:
        s = VOWEL.get(c) or LIPS.get(c) or 'small'
        if c == 'e' and seq and c == w[-1] and len(w) > 2: continue        # silent final e
        if not seq or seq[-1] != s: seq.append(s)
    return seq or ['small']


def mouth_track(words, f0, f1, fps=30, lead=1, min_hold=2):
    """Per-frame mouth shape for frames f0..f1 (global), from word timings. Mouth leads the voice by `lead` frames."""
    out = {}
    for w in words:
        a, b = int(round(w['start'] * fps)) - lead, int(round(w['end'] * fps)) - lead
        if b < f0 or a > f1: continue
        seq = visemes(w['word']); n = max(1, b - a)
        k = max(1, min(len(seq), n // min_hold)); seq = seq[:k] if k == len(seq) else [seq[int(i * len(seq) / k)] for i in range(k)]
        for f in range(a, b):
            out[f] = seq[min(k - 1, (f - a) * k // n)]
    return out


# ---------------------------------------------------------------- card cache
from collections import OrderedDict


class Budget(OrderedDict):
    """LRU cache of images bounded by total bytes (shared by every card cache in this worker). Close-up cards are
    ~4000 px square (64 MB); a count limit let 4 workers grow to 16 GB and get OOM-killed."""
    total = 0
    LIMIT = int(float(os.environ.get('ENGINE_CACHE_MB', 900)) * 2 ** 20)
    caches = []

    def __init__(self): super().__init__(); Budget.caches.append(self)

    def get(self, k):
        v = OrderedDict.get(self, k)
        if v is not None: self.move_to_end(k)
        return v

    def put(self, k, im):
        self[k] = im; Budget.total += im.width * im.height * 4
        while Budget.total > Budget.LIMIT:
            victim = max((c for c in Budget.caches if c), key=len, default=None)
            if victim is None or (victim is self and len(self) == 1): break
            _, old = victim.popitem(last=False); Budget.total -= old.width * old.height * 4
        return im


_cache = Budget()


def card(spec, pose, expr, facing, scale, lid=0.0, mouth=None, prop='keep'):
    pr = spec.get('prop') if prop == 'keep' else prop
    if pr == 'helmet' and spec.get('_sticker'): pr = 'helmet:' + spec['_sticker']      # the held helmet shows the joke
    kw = bean_kwargs(dict(spec, prop=pr))
    kw.update(arm_pose=tuple(arm_ok(p) for p in pose), expr=expr, facing=float(facing))
    if mouth and HAS_MOUTH: kw['mouth'] = BEAN_MOUTH.get(mouth, mouth)
    if lid and HAS_LID: kw['lid'] = lid
    elif lid >= 1 and HAS_BLINK: kw['blink'] = True
    key = (repr(sorted(kw.items())), round(scale, 3))
    im = _cache.get(key)
    if im is None:
        im = _cache.put(key, _render(kw, scale))
    g = face_geom(kw, scale)
    if mouth and not HAS_MOUTH:
        im = draw_mouth(im, g, 'smile' if expr in HAPPY and mouth in ('open', 'wide') else mouth, expr, bool(kw.get('moustache')))
    if lid and not HAS_LID and not (lid >= 1 and HAS_BLINK): im = draw_lid(im, g, lid, expr)    # half-lid frames
    return im, g


BEAN_MOUTH = {'smile': 'smile_talk'}
RIDE_PARAMS = set(inspect.signature(bikes.ride).parameters) if bikes else set()
_rcache = Budget()


def ride_card(spec, scale, rp, expr, mouth=None, lid=0.0, crank=30.0):
    """A rider on a bike (characters/scripts/bikes.py). rp: dict(lean, body_lean, bike_lean, steer, knee_out), rider-side
    degrees. Cached per (expr, mouth, blink, 1-degree buckets) so a held lean costs one render. 1000x1000 card, ground 975."""
    char = bean_kwargs(spec); char.pop('arm_pose', None)
    if char.get('hat') == 'hardhat' and spec.get('hat') == 'helmet': char['hat'] = 'helmet'
    b = lambda v: round(float(v or 0.0))
    kw = dict(char=char, bike=spec['rig'], view=spec.get('view', 'rear'), steer=b(rp.get('steer')), expr=expr,
              hold=spec.get('hold', 'fixed' if spec['rig'] == 'nobs_bike' else 'steer'), knee_out=bool(rp.get('knee_out')))
    if rp.get('bike_lean') is not None or rp.get('body_lean'):
        kw['bike_lean'] = b(rp.get('bike_lean', rp.get('lean', 0))); kw['body_lean'] = b(rp.get('body_lean'))
    else: kw['lean'] = b(rp.get('lean'))
    if spec.get('sticker'): kw['sticker'] = spec['sticker']
    if spec['rig'] == 'bicycle': kw['crank'] = round(crank / 30) * 30 % 360
    if mouth: kw['mouth'] = BEAN_MOUTH.get(mouth, mouth)
    if lid >= 1: kw['blink'] = True
    kw = {k: v for k, v in kw.items() if k in RIDE_PARAMS}
    key = (repr(sorted((k, v if k != 'char' else repr(sorted(v.items()))) for k, v in kw.items())), round(scale, 3))
    im = _rcache.get(key)
    if im is None:
        im = _rcache.put(key, _hires(bikes.ride, kw, (1000, 1000), scale))
    return im


_bcache = Budget()


def bike_card(kind, scale, view='3q', steer=0.0):
    """A bike alone as a prop (bikes.draw_bike): 1000x1000 card, ground at 975."""
    key = (kind, view, round(steer), round(scale, 3))
    im = _bcache.get(key)
    if im is None: im = _bcache.put(key, _hires(bikes.draw_bike, dict(kind=kind, view=view, steer=round(steer)), (1000, 1000), scale))
    return im


try:
    import inserts                        # full-frame insert cards (wardrobe), e.g. broom_insert
except Exception as e:                    # noqa: BLE001
    inserts = None
_icache = {}
INSERT_RIGS = ('broom_insert',)


def insert_card(kind, pose, spec, W, H):
    """Full-frame transparent insert card (hands + prop), cached per pose."""
    key = (kind, pose, spec.get('shirt'), spec.get('skin'))
    if key not in _icache:
        fn = getattr(inserts, kind) if inserts else None
        if fn is None: return None
        poses = getattr(inserts, 'POSES', {})
        _icache[key] = fn(pose if pose in poses else 'broom_upright', w=W, h=H,
                          sleeve=spec.get('shirt', '#2f6fb3'), skin=spec.get('skin', '#c98e63'))
    return _icache[key]

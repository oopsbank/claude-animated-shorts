# Prop sprites for the engine: shots.json "props" entries drawn with characters/scripts/sprites.py.
# An entry is a string ("gary_rock", "tour_sign:ICE TOURS $5 (ALIEN crossed out)") or a dict:
#   {"name": "gary_rock", "x": 0.4, "y": 0.8, "scale": 1.0, "layer": "back"|"front", "at_word": 3, "until_word": 9,
#    "dur": 1.5, "path": [[x, y], ...], "t": 0.5, "flip": true, "kw": {...sprite kwargs}}
#   x, y: frame fractions of the sprite's anchor (ground contact for standing props, the centre for UI cards).
#   scale: x the character-card scale at that ground depth (standing props) or x the frame-width fit (UI cards).
#   at_word/dur: t runs 0..1 from the word over dur seconds (default: the rest of the shot); path moves the anchor
#   along the points with an ease-in-out over the same t (a rock shoved by a pane). t: a fixed t.
# String entries are sprites only on SPRITE_SETS (dicts work anywhere). They take their placement from DEFAULTS[(name, cam)] or DEFAULTS[name]. Props the plate already shows
# (BAKED) and props a character holds in the shot are skipped. Names the sprite module does not know are ignored
# (scenery words such as "rock_trail_hero"), with one warning.
import os, sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'characters', 'scripts'))
try:
    import sprites
except Exception as e:                       # noqa: BLE001
    sprites = None; print('  [props] sprites.py unavailable:', e)

SPRITE_SETS = {'playa', 'inserts'}      # sets whose plain-string props are sprites (video 1 sets bake theirs: keep them identical)
UI = {'banner', 'livestream_counter', 'price_card'}           # anchored at their centre, sized to the frame
# Already in the plates (blender/sets/playa/build.py): the camp, the rock row, the van, the overlook sign and banner,
# the frost ice and the night pond. Keyed by name -> cams where the plate has it (None = every cam).
BAKED = {'tent': {'playa_med', 'playa_wide'}, 'timelapse_cam': {'playa_med', 'playa_wide'}, 'rock_row_15': None,
         'rock_trail_hero': None, 'tour_van': None, 'ice_sheet': None, 'pond_water': None,
         'tour_sign': {'overlook_med'}, 'banner': {'overlook_med'},
         'fantasy': None, 'livestream_screen': None, 'air_hockey_overlay': None, 'flood_water': None}   # plate variants / fx
# Default placement per (name, cam) or name. UI 'w' = width as a fraction of the frame.
DEFAULTS = {     # tuned on the playa plates: ground rows wide 0.55, med 0.65, rock_low 0.56 (camera 0.38 m up), overlook 0.63
    'gary_rock': dict(x=0.6, y=0.7, scale=1.0),
    ('gary_rock', 'rock_low'): dict(x=0.5, y=0.6, scale=1.0),
    ('gary_rock', 'playa_med'): dict(x=0.5, y=0.69, scale=1.0),
    'gary_buried': dict(x=0.6, y=0.7, scale=1.0),
    'gps_box': dict(x=0.45, y=0.7, scale=1.0),
    'cooler': dict(x=0.5, y=0.7, scale=1.0),
    'cooler_trophy': dict(x=0.78, y=0.69, scale=1.0),
    'tent': dict(x=0.2, y=0.66, scale=1.0),
    'tent_floating': dict(x=0.55, y=0.62, scale=1.1, layer='front'),
    'timelapse_cam': dict(x=0.8, y=0.66, scale=1.0),
    'tour_sign': dict(x=0.82, y=0.68, scale=1.0),
    'tour_sign_free': dict(x=0.66, y=0.575, scale=0.55),
    'flying_bills': dict(x=0.6, y=0.6, scale=1.0, layer='front'),
    'fridge_silhouette': dict(target='rock', dx=-0.17, dy=0.0, scale=0.8, kw={'ghost': True}),
    'phone_silhouette': dict(x=0.3, y=0.72, scale=2.0, layer='front'),
    'banner': dict(x=0.5, y=0.22, w=0.8, layer='front'),
    'livestream_counter': dict(x=0.72, y=0.1, w=0.3, layer='front'),
    'price_card': dict(x=0.8, y=0.24, w=0.3, layer='front'),
}
_warned = set()


def _warn(msg):
    if msg not in _warned and os.environ.get('ENGINE_QUIET') != '1': _warned.add(msg); print('  [props]', msg, flush=True)


def base_name(name): return name.split(':', 1)[0].split(' (')[0].strip()


def held_by_cast(shot):
    out = set()
    for c in shot.get('characters', []):
        if c.get('prop'): out.add(c['prop'])
        for b in c.get('beats', []):
            if b.get('prop'): out.add(b['prop'])
    return out


def plan(shot):
    """The sprite entries of a shot, resolved to dicts (placement merged), in draw order."""
    out = []; held = held_by_cast(shot); cam = shot.get('cam')
    for e in shot.get('props', []):
        if isinstance(e, str) and shot.get('set') not in SPRITE_SETS: continue
        e = {'name': e} if isinstance(e, str) else dict(e)
        b = base_name(e['name'])
        if sprites is None or b not in sprites.NAMES:
            if b not in BAKED: _warn(f"{shot.get('id')}: {b!r} is not a sprite (scenery or fx) -> skipped")
            continue
        if e.get('sprite') is False: continue
        if not e.get('sprite') and b in BAKED and (BAKED[b] is None or cam in BAKED[b]): continue   # in the plate
        if not e.get('sprite') and b in held: continue                                           # in a hand
        if not e.get('sprite') and b == 'cooler' and any(c.get('seated') == 'cooler' for c in shot.get('characters', [])): continue   # bean draws it
        d = dict(DEFAULTS.get(b, {})); d.update(DEFAULTS.get((b, cam), {})); d.update(e); d['_base'] = b
        d['_auto'] = 'x' not in e                       # placement may come from the plate JSON ("<name>_xy", px)
        out.append(d)
    return out


_cache = {}


def _sprite(name, t, k, kw):
    key = (name, round(t, 3), round(k, 3), repr(sorted(kw.items())))
    im = _cache.get(key)
    if im is None:
        if len(_cache) > 64: _cache.clear()
        im = sprites.sprite(name, t, k, **kw); _cache[key] = im
    return im


def card_scale(meta, y_px, W):
    """Character-card scale (bean units -> px) at ground row y_px: perspective from the plate's horizon."""
    s0 = meta['px_per_m'] * 1.75 / 777
    if meta.get('top') or meta.get('view') == 'top': return s0
    hz, gy = meta['horizon_y'], meta['ground_y']
    return s0 * max(0.08, (y_px - hz) / max(1.0, gy - hz))


def draw(base, entries, layer, f, t_of, meta, W, H):
    """Composite the entries of one layer. t_of(entry) -> t (None = hidden this frame)."""
    from anim import smooth
    for e in entries:
        if e.get('layer', 'back') != layer: continue
        t = t_of(e)
        if t is None: continue
        x, y = float(e.get('x', 0.5)), float(e.get('y', 0.8))
        if e.get('target') and e['target'] in meta.get('targets', {}):     # a plate target (px or fractions) + dx, dy
            tx, ty = meta['targets'][e['target']]; tx, ty = (tx / W, ty / H) if tx > 1.5 else (tx, ty)
            x, y = tx + float(e.get('dx', 0)), ty + float(e.get('dy', 0))
        elif e.get('_auto') and meta.get(e['_base'] + '_xy'):
            px_, py_ = meta[e['_base'] + '_xy']; x, y = (px_ / W, py_ / H) if px_ > 1.5 else (px_, py_)
        if e.get('path'):
            pts = e['path']; u = smooth(t) * (len(pts) - 1); i = min(int(u), len(pts) - 2); r = u - i
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r; y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r
        b = e['_base']
        if b in UI:
            im0 = _sprite(e['name'], t, 1.0, e.get('kw', {}))
            k = float(e.get('w', 0.3)) * W / im0.width * float(e.get('scale', 1.0))
        else:
            k = card_scale(meta, y * H, W) * float(e.get('scale', 1.0))
        im = _sprite(e['name'], t, k, e.get('kw', {}))
        ax, ay = im.info.get('anchor', (im.width / 2, im.height))
        if e.get('flip'): im = im.transpose(Image.FLIP_LEFT_RIGHT); ax = im.width - ax
        ox, oy = int(round(x * W - ax)), int(round(y * H - ay))
        if ox >= W or oy >= H or ox + im.width <= 0 or oy + im.height <= 0: continue
        if ox < 0 or oy < 0:
            im = im.crop((max(0, -ox), max(0, -oy), im.width, im.height)); ox, oy = max(0, ox), max(0, oy)
        base.alpha_composite(im.convert('RGBA'), (ox, oy))

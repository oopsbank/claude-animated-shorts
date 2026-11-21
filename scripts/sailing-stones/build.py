# Builds shots.json from the shot list below and runs the automatic script checks (QA.md › scripts).
# Usage: python3 scripts/sailing-stones/build.py   (exits non-zero if a check fails)
# Beats/fx/glides name an anchor word; it is converted to a 0-based word index within the shot's text ("at_word").
# Sets: `playa` (cams playa_wide, playa_med, rock_low, playa_top, overlook_med; lights day, golden, night, frost)
# and the insert set `inserts` (cams gps_screen, logbook, ticket; light day). Both are requested in BACKLOG.md (sets P1).
import json, re, sys, pathlib

HERE = pathlib.Path(__file__).parent
EXPRS = {'neutral', 'stern', 'grin', 'shock', 'nervous', 'smile', 'smug', 'pained'}       # characters/scripts/bean.py
ARMS = {'hang', 'wave', 'point', 'hold', 'hip', 'chin'}
NEW_ARMS = {'sleep'}                                   # requested from characters (BACKLOG)
FX_OK = {'explosion', 'impact_star', 'dust_puff', 'speed_lines', 'sweat_drop', 'anger_vein', 'glow_eyes',
         'sparkle', 'splash', 'question_mark', 'exclaim', 'music_note', 'whoosh'}
FX_NEW = {'ice_pane', 'ice_crack', 'sliding_rock', 'gps_ping', 'zzz', 'year_badge'}   # requested from fx (BACKLOG)
SETS = {'playa': {'cams': {'playa_wide', 'playa_med', 'rock_low', 'playa_top', 'overlook_med'},
                  'lights': {'day', 'golden', 'night', 'frost'}},
        'inserts': {'cams': {'gps_screen', 'logbook', 'ticket'}, 'lights': {'day'}}}

CAST = {   # our own designs, built with characters/scripts/bean.py character(...); nobody is drawn as a real person
    'kip':    dict(build='adult', skin='#f1c9a5', shirt='#3a8fd1', pants='#3b3b4f', hat='beanie', hat_col='#e8613c', seed=21),
    'lou':    dict(build='stout', skin='#8d5a3b', shirt='#f2b134', pants='#2f4b3a', hat='cap', hat_col='#2f6b4f', glasses=True, seed=22),
    'guide':  dict(build='stout', skin='#ffd9b8', shirt='#7a3fb0', pants='#2b2f3a', hat='antennae', hat_col='#6fd16a',
                   moustache='#5a3a22', outfit=('collar',), seed=23),
    'geo48':  dict(build='adult', skin='#e9b48a', shirt='#c9a46a', pants='#6b5a3e', hat='cap', hat_col='#8a6d3b', glasses=True,
                   prop='clipboard', seed=24),
    'geo70':  dict(build='adult', skin='#d79a6c', shirt='#d96a3a', pants='#3e4a6b', hat='beanie', hat_col='#2f6fb3',
                   moustache='#3b2a1a', outfit=('stripes',), seed=25),
    'tour1':  dict(build='adult', skin='#f6d2b0', shirt='#3fb37f', pants='#2f3f6b', hat='antennae', hat_col='#6fd16a', seed=31),
    'tour2':  dict(build='kid', skin='#b87a55', shirt='#e85d8a', pants='#30343f', hat='antennae', hat_col='#6fd16a', seed=32),
    'tour3':  dict(build='stout', skin='#ffe2c2', shirt='#2fb3c9', pants='#4a3b2f', hat='antennae', hat_col='#6fd16a', seed=33),
}

def C(cid, x, beats=(), **kw): return dict(id=cid, x=x, beats=list(beats), **kw)
def B(word, **kw): return dict(word=word, **kw)
def F(name, word, x, y, **kw): return dict(name=name, word=word, x=x, y=y, **kw)
def G(word, dur=10, **to): return dict(at_word=word, to=to, dur=dur)
def glide(*gs, **base): return dict(move='glide', glides=list(gs), **base)

SHOTS = [
 # --- HOOK: mid-action extreme close-up on the tracker going into the rock, then two pull-outs before 3 s
 dict(text="Two cousins hid GPS trackers inside fifteen rocks, then waited for the rocks to run away.",
      set='playa', cam='playa_med', light='day', size='medium', grammar=['xcu', 'insert'],
      camera=glide(G('fifteen', 8, zoom=1.25, y=0.62), G('waited', 10, zoom=1.0), zoom=1.9, x=0.42, y=0.72),
      note='Opens as an extreme close-up of the hands pushing the GPS box into a hollowed rock (zoom 1.9), pulls out to the cousins at "fifteen", to the camp with the rock row at "waited": 3 picture changes, the first two before 3 s.',
      characters=[C('kip', 0.34, [B('Two', arm=('hold', 'hold'), prop='gps_box', lean=8), B('fifteen', arm=('hip', 'hold'), expr='smug'), B('run', arm=('hip', 'hip'), expr='grin')]),
                  C('lou', 0.68, [B('Two', arm=('hold', 'hang'), prop='screwdriver', expr='neutral'), B('waited', arm=('chin', 'hang'), expr='neutral', lean=-6)])],
      fx=[F('gps_ping', 'trackers', 0.42, 0.74, size=0.45), F('sparkle', 'fifteen', 0.5, 0.8)], props=['gps_box', 'rock_row_15', 'tent', 'timelapse_cam']),
 dict(text="You see, in a dry Death Valley lake,",
      set='playa', cam='playa_wide', light='day', size='wide', grammar=['depth'], camera=dict(move='glide', direction='right', amount=0.06),
      note='Depth-layered: a rock and its trail in the near foreground, the cracked playa mid, the mountains far. No characters.',
      characters=[], fx=[], props=['rock_trail_hero']),
 dict(text="some rocks heavier than a man leave long trails,",
      set='playa', cam='rock_low', light='day', size='medium', grammar=['low_angle'], camera=dict(move='push_in', amount=0.06),
      characters=[C('lou', 0.70, [B('some', arm=('hold', 'hold'), lean=18, expr='pained'), B('trails', arm=('hip', 'hang'), lean=0, expr='nervous')])],
      fx=[F('sweat_drop', 'heavier', 0.70, 0.30, on='lou', size=0.45)], props=['rock_trail_hero']),
 dict(text="and nobody had seen one move.",
      set='playa', cam='rock_low', light='golden', size='close', grammar=['xcu'], camera=glide(G('seen', 12, zoom=1.6), zoom=1.3),
      characters=[], fx=[F('question_mark', 'move', 0.62, 0.32, size=0.45)], props=['rock_trail_hero']),
 # --- THE RIVAL
 dict(text="A local guide sells tours to see the culprits.",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('tours', 10, zoom=1.12)),
      characters=[C('guide', 0.58, [B('A', arm=('wave', 'hang'), expr='grin'), B('culprits', arm=('point', 'hip'), expr='smug', points_at='tour_sign')])],
      fx=[], props=['tour_sign:ALIEN ROCK TOURS (a green alien dragging a rock)', 'tour_van']),
 dict(text="\"Rocks don't walk, pal,\" he laughs.",
      set='playa', cam='overlook_med', light='day', size='close', grammar=['xcu', 'dutch'], camera=glide(G('laughs', 8, zoom=1.7, roll=8), zoom=1.45, roll=8, y=0.4),
      note='Dutch angle (roll 8) on the rival, ending on his face filling half the frame.',
      characters=[C('guide', 0.5, [B('Rocks', arm=('hip', 'hip'), expr='smug'), B('laughs', arm=('hip', 'wave'), expr='grin', lean=-8)], talk=True)],
      fx=[], props=['tour_sign:ALIEN ROCK TOURS (a green alien dragging a rock)']),
 dict(text="\"Aliens drag them at night.",
      set='playa', cam='overlook_med', light='night', size='medium', camera=dict(move='push_in', amount=0.06),
      characters=[C('guide', 0.42, [B('Aliens', arm=('hold', 'point'), prop='flashlight', expr='grin')], talk=True)],
      fx=[F('glow_eyes', 'drag', 0.76, 0.55)], props=['alien_cutout', 'tour_sign:ALIEN ROCK TOURS (a green alien dragging a rock)']),
 dict(text="Twenty bucks a ticket.\"",
      set='inserts', cam='ticket', light='day', size='close', grammar=['pov'], camera=dict(move='push_in', amount=0.08),
      characters=[], fx=[F('sparkle', 'bucks', 0.5, 0.45)], props=['ticket:ALIEN ROCK TOUR · ADMIT ONE · $20 (a hand tears the stub)']),
 dict(text="And his tours sell out.",
      set='playa', cam='overlook_med', light='day', size='wide', grammar=['crowd'], camera=dict(move='glide', direction='left', amount=0.06),
      note='Crowd: three tourists in antenna headbands in a row with the guide, at 0.8x so four fit.',
      characters=[C('tour1', 0.20, [B('And', arm=('wave', 'hang'), expr='grin')], scale=0.8), C('tour2', 0.40, [B('And', arm=('wave', 'wave'), expr='grin')], scale=0.8),
                  C('guide', 0.60, [B('sell', arm=('hold', 'hip'), prop='cash_fan', expr='smug')], scale=0.8), C('tour3', 0.80, [B('And', arm=('hold', 'hang'), prop='camera', expr='smile')], scale=0.8)],
      fx=[F('sparkle', 'out', 0.6, 0.3)], props=['tour_sign:SOLD OUT']),
 # --- STAGE 1: 1948 (visual surprise: a whirlwind spins right past the rock, which doesn't budge)
 dict(text="In 1948, geologists blamed whirlwinds.",
      set='playa', cam='playa_med', light='golden', size='medium', camera=dict(move='push_in', amount=0.05), grade='sepia',
      characters=[C('geo48', 0.36, [B('In', arm=('hold', 'hang'), expr='neutral'), B('whirlwinds', arm=('hold', 'point'), expr='smug')])],
      fx=[F('year_badge', 'In', 0.5, 0.14, label='1948'), F('whoosh', 'blamed', 0.72, 0.6, angle=90), F('dust_puff', 'whirlwinds', 0.72, 0.85, direction='both')], props=[]),
 dict(text="They never caught one pushing a rock.",
      set='playa', cam='rock_low', light='golden', size='medium', grade='sepia', camera=dict(move='shake', amount=0.012),
      note='Visual surprise: a dust devil whirls right over the hero rock, blows the geologist\'s hat off, and the rock doesn\'t budge.',
      characters=[C('geo48', 0.30, [B('They', arm=('hold', 'hang'), lean=-14, expr='shock'), B('rock.', arm=('hold', 'chin'), lean=0, expr='pained')])],
      fx=[F('whoosh', 'caught', 0.6, 0.55, angle=90), F('dust_puff', 'pushing', 0.62, 0.86, direction='both')], props=['rock_trail_hero']),
 dict(text="\"Told ya,\" grins the guide. \"Aliens.\"",
      set='playa', cam='overlook_med', light='day', size='close', grammar=['dutch'], camera=glide(G('Aliens', 6, zoom=1.5, roll=-8), zoom=1.3, roll=-8),
      characters=[C('guide', 0.5, [B('Told', arm=('hip', 'hold'), prop='postcards', expr='smug'), B('Aliens', arm=('point', 'hold'), expr='grin', lean=6)], talk=True)],
      fx=[F('sparkle', 'Aliens', 0.6, 0.3)], props=['tour_sign:ALIEN ROCK TOURS']),
 # --- STAGE 2: the sixties (visual surprise: the fenced rock escapes)
 dict(text="In the sixties, a geologist named thirty rocks",
      set='inserts', cam='logbook', light='day', size='close', grammar=['insert'], camera=glide(G('named', 10, zoom=1.2, y=0.55)),
      note='Prop insert: an old field logbook, a hand writes our own rock names (DORIS, HUGO, PEARL...) beside sketch maps.',
      characters=[], fx=[F('year_badge', 'In', 0.5, 0.14, label='1960s')], props=['logbook:ROCK NAMES 1-30 (DORIS, HUGO, PEARL, ...)']),
 dict(text="and fenced some in. One escaped anyway.",
      set='playa', cam='playa_top', light='day', size='medium', grammar=['top'], camera=glide(G('One', 10, zoom=1.25)),
      note='Top view: a ring of stakes around a rock; at "escaped" the rock sits outside the ring at the end of a fresh trail. Directions are only shown from above.',
      characters=[], fx=[F('sliding_rock', 'escaped', 0.5, 0.5, path=[(0.5, 0.5), (0.72, 0.38)], dur=1.2), F('exclaim', 'anyway.', 0.74, 0.28, size=0.45)], props=['stake_corral']),
 dict(text="In seven years, nobody saw it move.",
      set='playa', cam='playa_med', light='golden', size='medium', camera=glide(G('nobody', 10, zoom=1.2)),
      characters=[C('geo70', 0.40, [B('In', arm=('hold', 'hang'), prop='clipboard', expr='neutral'), B('nobody', arm=('chin', 'hang'), expr='pained', lean=6)])],
      fx=[F('year_badge', 'seven', 0.5, 0.14, label='7 YEARS')], props=['rock_trail_hero', 'stake_corral']),
 dict(text="The guide doubles his prices. \"Aliens don't do fences.\"",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('Aliens', 8, zoom=1.3)),
      characters=[C('guide', 0.5, [B('The', arm=('hold', 'hang'), prop='paintbrush', expr='smug'), B('Aliens', arm=('point', 'hip'), expr='grin', points_at='tour_sign')], talk=True)],
      fx=[F('sparkle', 'prices', 0.62, 0.3)], props=['tour_sign:ALIEN ROCK TOURS $40 ("$20" crossed out)']),
 # --- STAGE 3: 2011
 dict(text="So in 2011, the cousins set up trackers and cameras,",
      set='playa', cam='playa_med', light='day', size='medium', camera=glide(G('trackers', 8, zoom=1.15, x=0.45)),
      characters=[C('kip', 0.36, [B('So', arm=('hold', 'hold'), prop='gps_box', expr='neutral'), B('cameras', arm=('point', 'hang'), expr='smile', points_at='timelapse_cam')]),
                  C('lou', 0.68, [B('So', arm=('hold', 'hold'), prop='tripod', expr='neutral')])],
      fx=[F('year_badge', 'So', 0.5, 0.14, label='2011'), F('gps_ping', 'trackers', 0.30, 0.78, size=0.45)], props=['tent', 'timelapse_cam', 'rock_row_15', 'weather_station']),
 dict(text="ready to wait ten years.",
      set='playa', cam='playa_wide', light='golden', size='wide', grammar=['depth'], camera=dict(move='push_in', amount=0.06),
      note='Depth-layered: weather-station mast near, the cousins on folding chairs mid, the playa and mountains far.',
      characters=[C('kip', 0.42, [B('ready', arm=('hold', 'hang'), prop='mug', expr='smile')]), C('lou', 0.60, [B('wait', arm=('chin', 'hang'), expr='neutral')])],
      fx=[], props=['weather_station', 'tent', 'folding_chairs']),
 dict(text="\"See you in ten years, nerds!\" yells the guide.",
      set='playa', cam='overlook_med', light='golden', size='medium', camera=glide(G('nerds', 8, zoom=1.2)),
      characters=[C('guide', 0.56, [B('See', arm=('wave', 'hold'), prop='cash_fan', expr='grin'), B('yells', arm=('wave', 'hip'), expr='smug', lean=-8)], talk=True)],
      fx=[], props=['tour_van', 'tour_sign:ALIEN ROCK TOURS $40']),
 # --- THE REVERSAL
 dict(text="Two years later, dozens of rocks start sliding",
      set='playa', cam='playa_wide', light='frost', size='wide', camera=glide(G('sliding', 10, zoom=1.2)),
      characters=[C('kip', 0.44, [B('Two', arm=('hold', 'hang'), prop='mug', expr='neutral')]), C('lou', 0.58, [B('Two', arm=('chin', 'hang'), expr='neutral')])],
      fx=[F('year_badge', 'Two', 0.5, 0.14, label='2 YEARS LATER'), F('sliding_rock', 'sliding', 0.5, 0.6, count=5, path='away', dur=2.0)], props=['ice_sheet']),
 dict(text="right there, in broad daylight.",
      set='playa', cam='playa_med', light='frost', size='close', grammar=['depth'], camera=glide(G('broad', 6, zoom=1.4, y=0.42), zoom=1.15),
      note='Depth-layered: cousins in the foreground facing camera, rocks sliding behind them with growing trails; punch-in on their shocked faces at "broad". Rocks slide away from camera (no left/right claim).',
      characters=[C('kip', 0.32, [B('right', arm=('point', 'hang'), expr='shock', lean=-6)]), C('lou', 0.70, [B('broad', arm=('wave', 'wave'), expr='shock')])],
      fx=[F('sliding_rock', 'right', 0.5, 0.62, count=3, path='away', dur=1.6), F('exclaim', 'broad', 0.5, 0.2, size=0.45)], props=['ice_sheet']),
 # --- THE MECHANISM (visual-metaphor set piece, top view of one rock)
 dict(text="Winter rain had left a shallow pond",
      set='playa', cam='playa_top', light='frost', size='medium', grammar=['metaphor'], camera=dict(move='push_in', amount=0.06),
      characters=[], fx=[F('splash', 'rain', 0.4, 0.4), F('splash', 'shallow', 0.62, 0.62), F('ice_pane', 'pond', 0.5, 0.5, stage='water')], props=['rock_trail_hero']),
 dict(text="that froze overnight into ice millimetres thick.",
      set='playa', cam='rock_low', light='frost', size='close', grammar=['xcu'], camera=glide(G('millimetres', 10, zoom=1.7, y=0.8), zoom=1.2),
      note='Extreme close-up at ground level: the thin ice edge against the rock, glinting.',
      characters=[], fx=[F('ice_pane', 'froze', 0.5, 0.8, stage='freeze', view='side'), F('sparkle', 'millimetres', 0.5, 0.78)], props=['ice_sheet']),
 dict(text="The late-morning sun cracked it into huge floating panes.",
      set='playa', cam='playa_top', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('huge', 12, zoom=0.9)),
      characters=[], fx=[F('ice_crack', 'cracked', 0.5, 0.5), F('ice_pane', 'panes.', 0.5, 0.5, stage='panes')], props=['ice_sheet']),
 dict(text="A light breeze pushed the panes,",
      set='playa', cam='playa_top', light='frost', size='medium', grammar=['metaphor'], camera=dict(move='glide', direction='right', amount=0.05),
      note='Top view, so the drift direction is unambiguous: wind lines and panes all move screen-right.',
      characters=[], fx=[F('whoosh', 'breeze', 0.3, 0.5, angle=0), F('ice_pane', 'pushed', 0.5, 0.5, stage='drift', direction='right')], props=[]),
 dict(text="and the panes pushed the rocks,",
      set='playa', cam='playa_top', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('rocks,', 8, zoom=1.3, x=0.6)),
      characters=[], fx=[F('ice_pane', 'and', 0.5, 0.5, stage='drift', direction='right'), F('sliding_rock', 'pushed', 0.55, 0.5, path=[(0.55, 0.5), (0.75, 0.5)], dur=1.5, trail=True)], props=[]),
 dict(text="a few metres a minute.",
      set='inserts', cam='gps_screen', light='day', size='close', grammar=['pov'], camera=dict(move='push_in', amount=0.08),
      note='POV insert: the cousins\' laptop/GPS screen, a dot drawing a track with a readout ticking "3 m/min".',
      characters=[], fx=[F('gps_ping', 'few', 0.55, 0.5, size=0.45)], props=['gps_screen:TRACK 07 · 3 m/min']),
 dict(text="Like a giant window sliding across a wet kitchen floor",
      set='playa', cam='playa_med', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('wet', 10, zoom=1.2)),
      note='The analogy staged as a gag on the playa: a giant house window (glass in a frame) slides across the wet mud toward a fridge. Lou watches.',
      characters=[C('lou', 0.72, [B('Like', arm=('hang', 'hang'), expr='neutral'), B('wet', arm=('chin', 'hang'), expr='smug')])],
      fx=[F('whoosh', 'giant', 0.25, 0.55, angle=0)], props=['giant_window', 'fridge']),
 dict(text="and shoving the fridge.",
      set='playa', cam='rock_low', light='frost', size='medium', camera=dict(move='shake', amount=0.01),
      characters=[C('kip', 0.72, [B('and', arm=('hold', 'hang'), expr='smile'), B('fridge.', arm=('point', 'hang'), expr='grin')])],
      fx=[F('splash', 'shoving', 0.4, 0.85), F('sliding_rock', 'shoving', 0.4, 0.75, sprite='fridge', path='away', dur=1.2, trail=True)], props=['giant_window', 'fridge']),
 # --- THE RIVAL'S SPECTACULAR FAILURE + LOOP BACK TO THE TRACKERS
 dict(text="And the guide? Snoring in his van,",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('Snoring', 8, zoom=1.3, x=0.6)),
      note='The van with the guide asleep in the driver\'s seat (sleep pose), the sun high.',
      characters=[C('guide', 0.60, [B('And', arm=('sleep', 'sleep'), expr='neutral')], seated='van')],
      fx=[F('zzz', 'Snoring', 0.66, 0.3, size=0.45)], props=['tour_van', 'tour_sign:ALIEN ROCK TOURS · NIGHT ONLY']),
 dict(text="while an ice pane shoves a rock over his alien sign.",
      set='playa', cam='rock_low', light='frost', size='medium', camera=dict(move='glide', glides=[dict(at_word=3, to=dict(zoom=1.15), dur=8), dict(at_word=8, to=dict(zoom=1.35, y=0.55), dur=6)]),
      note='Spectacle: low angle, an ice pane drives the hero rock into the sign standing on the playa; at "over" the sign tips flat with a crack and a splash, the alien cut-out face-down in the water. Seen from the low side, the rock moves away from camera (no left/right claim). Physically: slow (a few m/min), so the shot is the topple moment; the sign is our fiction.',
      characters=[], fx=[F('ice_pane', 'ice', 0.45, 0.75, stage='drift', view='side'), F('sliding_rock', 'shoves', 0.45, 0.72, path='away', dur=1.6, trail=True),
                         F('impact_star', 'over', 0.55, 0.55), F('splash', 'sign.', 0.55, 0.82)], props=['tour_sign_free:ALIEN ROCK TOURS · NIGHT ONLY (a separate sprite that can topple)', 'alien_cutout']),
 dict(text="The cousins' trackers caught the real culprit.",
      set='playa', cam='playa_med', light='golden', size='medium', camera=glide(G('culprit.', 8, zoom=1.25)),
      note='Loop: back to the cousins and the rock row of shot 1. Kip holds the laptop with the track ending at the flattened sign; Lou fist-pumps. Ends on the gag image, no fade.',
      characters=[C('kip', 0.36, [B('The', arm=('hold', 'hold'), prop='laptop', expr='smile'), B('culprit.', arm=('hold', 'point'), expr='grin')]),
                  C('lou', 0.68, [B('The', arm=('hang', 'hang'), expr='neutral'), B('real', arm=('wave', 'hip'), expr='grin', lean=-6)])],
      fx=[F('gps_ping', 'trackers', 0.36, 0.6, size=0.45), F('sparkle', 'culprit.', 0.5, 0.3)], props=['laptop', 'rock_row_15', 'tent']),
]

def words(t): return t.split()
def idx(text, w, sid):
    if isinstance(w, int): return w
    norm = lambda x: x.strip('.,:;!?"\'').lower()
    ws = [norm(x) for x in words(text)]
    if norm(w) not in ws: sys.exit(f'{sid}: anchor word {w!r} not in text')
    return ws.index(norm(w))

errors, out = [], []
for i, s in enumerate(SHOTS, 1):
    sid = f's{i:02d}'; s = json.loads(json.dumps(s))
    st = SETS.get(s['set'])
    if not st or s['cam'] not in st['cams'] or s['light'] not in st['lights']: errors.append(f'{sid}: unknown set/cam/light')
    for c in s['characters']:
        if c['id'] not in CAST: errors.append(f'{sid}: unknown character {c["id"]}'); continue
        c.update({k: v for k, v in CAST[c['id']].items() if k not in c})
        for b in c['beats']:
            b['at_word'] = idx(s['text'], b.pop('word'), sid)
            if 'expr' in b and b['expr'] not in EXPRS: errors.append(f'{sid}: expr {b["expr"]}')
            for a in ([b['arm']] if isinstance(b.get('arm'), str) else list(b.get('arm', ()))):
                if a not in ARMS | NEW_ARMS: errors.append(f'{sid}: arm {a}')
            if 'arm' in b: b['arm_pose'] = b.pop('arm')
        if not (0.15 <= c['x'] <= 0.85): errors.append(f'{sid}: {c["id"]} x={c["x"]} near the edge')
    cam = s['camera']
    if isinstance(cam.get('at_word'), str): cam['at_word'] = idx(s['text'], cam['at_word'], sid)
    for g in cam.get('glides', []): g['at_word'] = idx(s['text'], g['at_word'], sid)
    for f in s['fx']:
        f['at_word'] = idx(s['text'], f.pop('word'), sid)
        if f['name'] not in FX_OK | FX_NEW: errors.append(f'{sid}: fx {f["name"]}')
    out.append(dict(id=sid, **s))

hook = SHOTS[0]['text']; n_hook = len(words(hook))
total = sum(len(words(s['text'])) for s in SHOTS)
vo_sec = (HERE / 'SCRIPT.md').read_text().split('## Voice-over', 1)[1].split('\n## ', 1)[0]
vo = [l.split('. ', 1)[1] for l in vo_sec.splitlines() if re.match(r'^\d+\. ', l)]
sizes = [s['size'] for s in SHOTS]
gram = [g for s in SHOTS for g in s.get('grammar', [])]
spoken_years = 3                       # "nineteen forty-eight" (+2), "twenty eleven" (+1)
checks = {
    'hook 10-16 words': 10 <= n_hook <= 16,
    'total 225-240 words': 225 <= total <= 240,
    'every SCRIPT.md line has a shot with identical text': vo == [s['text'] for s in SHOTS],
    'contains "You see,"': any(s['text'].startswith('You see,') for s in SHOTS),
    'shot mix: medium >= 50%, close 15-30%, wide <= 25%': sizes.count('medium') / len(sizes) >= 0.5 and 0.15 <= sizes.count('close') / len(sizes) <= 0.3 and sizes.count('wide') / len(sizes) <= 0.25,
    'shot grammar: xcu, pov/insert, dutch/low angle, crowd/depth, metaphor': all(any(g in gram for g in grp) for grp in (('xcu',), ('pov', 'insert'), ('dutch', 'low_angle'), ('crowd', 'depth'), ('metaphor',))),
    'no validation errors': not errors,
}
json.dump(dict(slug='sailing-stones', title='The Rocks That Walk Across the Desert', words_per_s=3.7,
               captions={'style': 'sentence'},
               note='Directions (pane drift, rock slides) are only shown in the top view (playa_top) or as "away from camera". '
                    'at_word = 0-based word index within the shot text (split on spaces). grammar = shot-grammar tags for the '
                    'replication playbook §3E count. New sets/cams/lights, props, fx (ice_pane, ice_crack, sliding_rock, gps_ping, zzz, '
                    'year_badge), hat "antennae", arm_pose "sleep", seated, and grade "sepia" are requested in BACKLOG.md.',
               shots=out), open(HERE / 'shots.json', 'w'), indent=1, ensure_ascii=False)
print(f'hook {n_hook} words, total {total} words (+{spoken_years} spoken in the years) = {(total + spoken_years) / 3.7:.1f} s at 3.7 w/s, '
      f'{len(SHOTS)} shots, mix', {k: sizes.count(k) for k in set(sizes)}, 'grammar', sorted(set(gram)))
for e in errors: print('ERROR', e)
for k, v in checks.items(): print('PASS' if v else 'FAIL', k)
sys.exit(0 if all(checks.values()) else 1)

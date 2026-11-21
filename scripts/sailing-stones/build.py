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
FX_NEW = {'ice_pane', 'ice_crack', 'sliding_rock', 'gps_ping', 'zzz', 'year_badge', 'dust_storm', 'rain', 'heat_haze'}   # requested from fx (BACKLOG)
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
 # --- HOOK (loops from the last line): mid-action XCU of a tracker going into a rock, two pull-outs before 3 s
 dict(text="Two cousins hid GPS trackers inside fifteen rocks, then waited for the rocks to run away.",
      set='playa', cam='playa_med', light='day', size='medium', grammar=['xcu', 'insert'],
      camera=glide(G('fifteen', 8, zoom=1.25, y=0.62), G('waited', 10, zoom=1.0), zoom=1.9, x=0.42, y=0.72),
      note='Opens on an extreme close-up of hands pushing the GPS box into a hollowed rock (zoom 1.9); pull-out to the cousins at "fifteen", to the camp and the rock row at "waited". Matches the last shot for the loop.',
      characters=[C('kip', 0.34, [B('Two', arm=('hold', 'hold'), prop='gps_box', lean=8), B('fifteen', arm=('hip', 'hold'), expr='smug'), B('run', arm=('hip', 'hip'), expr='grin')]),
                  C('lou', 0.68, [B('Two', arm=('hold', 'hang'), prop='screwdriver', expr='neutral'), B('waited', arm=('chin', 'hang'), expr='neutral', lean=-6)])],
      fx=[F('gps_ping', 'trackers', 0.42, 0.74, size=0.45), F('sparkle', 'fifteen', 0.5, 0.8)], props=['gps_box', 'rock_row_15', 'tent', 'timelapse_cam']),
 dict(text="You see, on a Death Valley lake bed,",
      set='playa', cam='playa_wide', light='day', size='wide', grammar=['depth'], camera=dict(move='glide', direction='right', amount=0.06),
      note='Depth-layered: a rock and its trail in the near foreground, the cousins small at their camp mid, the mountains far.',
      characters=[C('kip', 0.46, [B('You', arm=('hold', 'hang'), prop='mug')]), C('lou', 0.56, [B('You', arm=('chin', 'hang'))])], fx=[], props=['rock_trail_hero', 'tent']),
 dict(text="some rocks heavier than a fridge leave long trails,",
      set='playa', cam='rock_low', light='day', size='medium', grammar=['low_angle'], camera=dict(move='push_in', amount=0.06),
      characters=[C('lou', 0.70, [B('some', arm=('hold', 'hold'), lean=18, expr='pained'), B('trails', arm=('hip', 'hang'), lean=0, expr='nervous')])],
      fx=[F('sweat_drop', 'heavier', 0.70, 0.30, on='lou', size=0.45)], props=['rock_trail_hero']),
 dict(text="and nobody's ever seen one move.",
      set='playa', cam='rock_low', light='golden', size='close', grammar=['xcu'], camera=glide(G('seen', 12, zoom=1.6), zoom=1.3),
      characters=[], fx=[F('question_mark', 'move', 0.62, 0.32, size=0.45)], props=['rock_trail_hero']),
 # --- THE RIVAL: all the history in one mocking rant
 dict(text="Nearby, an antenna-wearing guide mocks the cousins.",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('mocks', 8, zoom=1.12)),
      characters=[C('guide', 0.58, [B('Nearby', arm=('wave', 'hang'), expr='grin'), B('mocks', arm=('point', 'hip'), expr='smug', points_at='tour_sign')]),
                  C('kip', 0.22, [B('Nearby', arm=('hold', 'hang'), prop='gps_box')], view='rear')],
      fx=[], props=['tour_sign:ALIEN ROCK TOURS (a green alien dragging a rock)', 'tour_van']),
 dict(text="\"Scientists blamed the wind!\" he laughs.",
      set='playa', cam='overlook_med', light='day', size='close', grammar=['xcu', 'dutch'], camera=glide(G('laughs', 8, zoom=1.7, roll=8), zoom=1.45, roll=8, y=0.4),
      note='Dutch angle (roll 8) on the rival, ending on his face filling half the frame.',
      characters=[C('guide', 0.5, [B('Scientists', arm=('hip', 'wave'), expr='smug'), B('laughs', arm=('hip', 'hip'), expr='grin', lean=-8)], talk=True)],
      fx=[F('year_badge', 'Scientists', 0.5, 0.14, label='1948')], props=['tour_sign:ALIEN ROCK TOURS']),
 dict(text="\"They fenced rocks in! Sixty years, zero witnesses!",
      set='inserts', cam='logbook', light='day', size='close', grammar=['insert'], camera=dict(move='push_in', amount=0.08),
      note='Three quick flashback cards on the logbook page, (sepia): a stake fence around named rocks, then "60 YEARS" and a big "0" in the witnesses column. (The whirlwind is on shot 6, behind the guide.)',
      characters=[], fx=[F('impact_star', 'fenced', 0.5, 0.5), F('year_badge', 'Sixty', 0.5, 0.14, label='60 YEARS'), F('exclaim', 'zero', 0.5, 0.4, size=0.45)],
      props=['logbook:WHIRLWINDS? (1948) / FENCED ROCKS: DORIS, HUGO, PEARL (1960s) / WITNESSES: 0']),
 dict(text="It's aliens, pal. Twenty bucks.\"",
      set='inserts', cam='ticket', light='day', size='close', grammar=['pov'], camera=dict(move='push_in', amount=0.08),
      characters=[], fx=[F('sparkle', 'Twenty', 0.5, 0.45)], props=['ticket:ALIEN ROCK TOUR · ADMIT ONE · $20 (a hand tears the stub)']),
 dict(text="And his tours sell out.",
      set='playa', cam='overlook_med', light='day', size='wide', grammar=['crowd'], camera=dict(move='glide', direction='left', amount=0.06),
      note='Crowd: three tourists in antenna headbands in a row with the guide, at 0.8x so four fit.',
      characters=[C('tour1', 0.20, [B('And', arm=('wave', 'hang'), expr='grin')], scale=0.8), C('tour2', 0.40, [B('And', arm=('wave', 'wave'), expr='grin')], scale=0.8),
                  C('guide', 0.60, [B('sell', arm=('hold', 'hip'), prop='cash_fan', expr='smug')], scale=0.8), C('tour3', 0.80, [B('And', arm=('hold', 'hang'), prop='camera', expr='smile')], scale=0.8)],
      fx=[F('sparkle', 'out', 0.6, 0.3)], props=['tour_sign:SOLD OUT']),
 # --- STAGE 1: month one
 dict(text="Month one: they stare at the rocks.",
      set='playa', cam='playa_med', light='day', size='medium', camera=glide(G('stare', 8, zoom=1.15)),
      characters=[C('kip', 0.36, [B('Month', arm=('hold', 'hold'), prop='binoculars', expr='neutral'), B('stare', arm=('hold', 'hold'), expr='nervous', lean=6)]),
                  C('lou', 0.66, [B('Month', arm=('chin', 'hang'), expr='neutral'), B('rocks.', arm=('hip', 'hip'), expr='stern')])],
      fx=[F('year_badge', 'Month', 0.5, 0.14, label='MONTH 1')], props=['rock_row_15', 'folding_chairs', 'timelapse_cam']),
 dict(text="Nothing moves except a dust storm,",
      set='playa', cam='playa_wide', light='golden', size='wide', camera=dict(move='shake', amount=0.012),
      characters=[C('kip', 0.40, [B('Nothing', arm=('hold', 'hold'), expr='neutral'), B('storm,', arm=('wave', 'wave'), lean=-12)]), C('lou', 0.58, [B('storm,', arm=('hold', 'hold'), lean=-14)])],
      fx=[F('dust_storm', 'except', 0.5, 0.5)], props=['tent', 'timelapse_cam']),
 dict(text="which buries their camera.",
      set='playa', cam='rock_low', light='golden', size='close', grammar=['xcu'], camera=glide(G('camera.', 6, zoom=1.6, y=0.7), zoom=1.2),
      characters=[], fx=[F('dust_puff', 'buries', 0.5, 0.75, direction='both')], props=['timelapse_cam_buried']),
 dict(text="\"Rocks one, nerds zero,\" says the guide. \"Thirty bucks.\"",
      set='playa', cam='overlook_med', light='golden', size='medium', camera=glide(G('Thirty', 8, zoom=1.3)),
      characters=[C('guide', 0.56, [B('Rocks', arm=('point', 'hip'), expr='smug'), B('Thirty', arm=('hold', 'hip'), prop='paintbrush', expr='grin', lean=-6)], talk=True)],
      fx=[F('sparkle', 'Thirty', 0.66, 0.3)], props=['tour_sign:ALIEN ROCK TOURS $30 ("$20" crossed out)']),
 # --- STAGE 2: year one
 dict(text="Year one: summer bakes the lake bed.",
      set='playa', cam='playa_med', light='golden', size='medium', camera=dict(move='push_in', amount=0.06),
      note='Heat: the plate golden light plus a shimmer fx; both cousins wilt in their chairs.',
      characters=[C('kip', 0.36, [B('Year', arm=('hang', 'hang'), expr='pained', lean=10)]), C('lou', 0.66, [B('summer', arm=('hold', 'hang'), prop='fan', expr='pained', lean=-8)])],
      fx=[F('year_badge', 'Year', 0.5, 0.14, label='YEAR 1'), F('heat_haze', 'summer', 0.5, 0.55), F('sweat_drop', 'bakes', 0.36, 0.3, on='kip', size=0.45)], props=['folding_chairs', 'tent']),
 dict(text="They fry an egg on a tracker rock.",
      set='playa', cam='rock_low', light='day', size='close', grammar=['xcu'], camera=glide(G('egg', 8, zoom=1.6, y=0.75), zoom=1.2),
      characters=[C('lou', 0.70, [B('They', arm=('hold', 'hang'), prop='egg', expr='smile'), B('egg', arm=('point', 'hang'), expr='grin')])],
      fx=[F('sparkle', 'rock.', 0.42, 0.72)], props=['fried_egg_on_rock']),
 dict(text="Only the yolk runs.",
      set='playa', cam='playa_top', light='day', size='medium', grammar=['top'], camera=glide(G('runs.', 6, zoom=1.3)),
      note='Gag beat: the hero rock with the fried egg on top, still; only the yolk slides down the rock\'s side (the pun on line 1\'s "run away").',
      characters=[], fx=[F('sliding_rock', 'runs.', 0.5, 0.5, sprite='egg_yolk', path=[(0.5, 0.5), (0.58, 0.62)], dur=1.0)], props=['fried_egg_on_rock']),
 dict(text="\"Aliens only drive at night,\" snorts the guide. \"Forty bucks.\"",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('Forty', 8, zoom=1.3)),
      characters=[C('guide', 0.56, [B('Aliens', arm=('chin', 'hip'), expr='smug'), B('Forty', arm=('wave', 'hold'), prop='cash_fan', expr='grin', lean=-6)], talk=True)],
      fx=[F('sparkle', 'Forty', 0.66, 0.3)], props=['tour_sign:ALIEN ROCK TOURS $40 ("$30" crossed out)', 'tour_van']),
 # --- STAGE 3: year two
 dict(text="Year two: winter rain floods the lake bed ankle-deep,",
      set='playa', cam='playa_wide', light='golden', size='wide', camera=glide(G('ankle-deep', 10, zoom=1.2)),
      characters=[C('kip', 0.42, [B('Year', arm=('hold', 'hang'), prop='umbrella', expr='neutral'), B('ankle-deep', arm=('hold', 'point'), expr='shock')]), C('lou', 0.58, [B('rain', arm=('wave', 'hang'), expr='smile')])],
      fx=[F('year_badge', 'Year', 0.5, 0.14, label='YEAR 2 · WINTER'), F('rain', 'rain', 0.5, 0.4), F('splash', 'ankle-deep', 0.5, 0.86)], props=['pond_water']),
 dict(text="and cold nights freeze it over.",
      set='playa', cam='playa_top', light='night', size='medium', grammar=['metaphor'], camera=dict(move='push_in', amount=0.06),
      characters=[], fx=[F('ice_pane', 'freeze', 0.5, 0.5, stage='freeze')], props=['rock_trail_hero']),
 dict(text="One sunny morning, the ice crackles.",
      set='playa', cam='rock_low', light='frost', size='close', grammar=['xcu'], camera=glide(G('crackles.', 6, zoom=1.7, y=0.78), zoom=1.3),
      note='Extreme close-up at ground level: crack lines race through the thin ice past the rock; the cousins\' boots in the background, one turns.',
      characters=[], fx=[F('ice_crack', 'ice', 0.5, 0.78), F('exclaim', 'crackles.', 0.6, 0.3, size=0.45)], props=['ice_sheet']),
 dict(text="Dozens of rocks start sliding in broad daylight, tracker rocks among them.",
      set='playa', cam='playa_med', light='frost', size='medium', grammar=['depth'], camera=glide(G('broad', 8, zoom=1.35, y=0.42)),
      note='Depth-layered: cousins in the foreground facing camera, rocks sliding behind them on the ice with growing trails, away from camera (no left/right claim); punch-in on their shocked faces at "broad".',
      characters=[C('kip', 0.32, [B('Dozens', arm=('hold', 'hang'), prop='laptop', expr='shock'), B('broad', arm=('point', 'hold'), expr='grin', lean=-6)]),
                  C('lou', 0.70, [B('Dozens', arm=('hang', 'hang'), expr='shock'), B('broad', arm=('wave', 'wave'), expr='grin')])],
      fx=[F('sliding_rock', 'Dozens', 0.5, 0.62, count=5, path='away', dur=2.4), F('exclaim', 'sliding', 0.5, 0.2, size=0.45), F('gps_ping', 'tracker', 0.32, 0.6, size=0.45)], props=['ice_sheet']),
 # --- THE MECHANISM (≤ 10 s, visual-metaphor set piece in top view)
 dict(text="The sun breaks the phone-thin ice into huge panes,",
      set='playa', cam='playa_top', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('phone-thin', 8, zoom=1.4), G('huge', 8, zoom=0.9)),
      note='Top view: crack lines race across the sheet; at "phone-thin" a punch-in on a pane edge with a phone silhouette beside it for scale; pull back to the panes.',
      characters=[], fx=[F('ice_crack', 'breaks', 0.5, 0.5), F('ice_pane', 'panes,', 0.5, 0.5, stage='panes')], props=['ice_sheet', 'phone_silhouette']),
 dict(text="a light breeze shoves them, and they shove the rocks.",
      set='playa', cam='playa_top', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('rocks.', 8, zoom=1.3, x=0.6)),
      note='Top view, so the drift direction is unambiguous: wind lines, panes and the rock all move screen-right; the trail draws on behind the rock.',
      characters=[], fx=[F('whoosh', 'breeze', 0.3, 0.5, angle=0), F('ice_pane', 'shoves', 0.5, 0.5, stage='drift', direction='right'),
                         F('sliding_rock', 'rocks.', 0.55, 0.5, path=[(0.55, 0.5), (0.75, 0.5)], dur=1.5, trail=True)], props=[]),
 dict(text="Picture a giant window skating across a wet kitchen floor, pushing your fridge.",
      set='playa', cam='playa_med', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('pushing', 8, zoom=1.25, x=0.4)),
      note='The analogy staged as a gag on the playa: a giant house window slides across the wet mud and shoves a fridge; Lou watches deadpan, Kip films it.',
      characters=[C('lou', 0.72, [B('Picture', arm=('hang', 'hang'), expr='neutral'), B('fridge.', arm=('chin', 'hang'), expr='smug')]),
                  C('kip', 0.22, [B('Picture', arm=('hold', 'hold'), prop='camera', expr='grin')])],
      fx=[F('whoosh', 'giant', 0.35, 0.55, angle=0), F('sliding_rock', 'pushing', 0.45, 0.75, sprite='fridge', path=[(0.45, 0.75), (0.6, 0.75)], dur=1.2, trail=True), F('splash', 'pushing', 0.45, 0.85)],
      props=['giant_window', 'fridge']),
 # --- COMEUPPANCE + LOOP
 dict(text="And the guide? Snoring in his van,",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('Snoring', 8, zoom=1.3, x=0.6)),
      characters=[C('guide', 0.60, [B('And', arm=('sleep', 'sleep'), expr='neutral')], seated='van')],
      fx=[F('zzz', 'Snoring', 0.66, 0.3, size=0.45)], props=['tour_van', 'tour_sign:ALIEN ROCK TOURS $40 · NIGHT ONLY']),
 dict(text="while daylight ice shoves a rock through his NIGHT ONLY sign.",
      set='playa', cam='rock_low', light='frost', size='medium', camera=dict(move='glide', glides=[dict(at_word=3, to=dict(zoom=1.15), dur=8), dict(at_word=8, to=dict(zoom=1.35, y=0.55), dur=6)]),
      note='Spectacle: low angle, an ice pane drives the hero rock into the sign standing on the playa; at "through" the sign splits and falls flat with a splash, the alien cut-out face-down in the water. The rock moves away from camera (no left/right claim). Draw the push slow (real rocks crept at 2-5 m/min); the sign is our fiction.',
      characters=[], fx=[F('ice_pane', 'ice', 0.45, 0.75, stage='drift', view='side'), F('sliding_rock', 'shoves', 0.45, 0.72, path='away', dur=1.6, trail=True),
                         F('impact_star', 'through', 0.55, 0.55), F('splash', 'sign.', 0.55, 0.82)], props=['tour_sign_free:ALIEN ROCK TOURS $40 · NIGHT ONLY (a separate sprite that splits and topples)', 'alien_cutout']),
 dict(text="Nerds one, aliens zero.",
      set='playa', cam='playa_top', light='frost', size='medium', camera=dict(move='push_in', amount=0.1),
      note='Callback to his own taunt: top view of the flattened sign lying under the rock, the alien cut-out face-down in the water, a scoreboard badge NERDS 1 · ALIENS 0 (flips his own "Rocks one, nerds zero").',
      characters=[], fx=[F('year_badge', 'Nerds', 0.5, 0.14, label='NERDS 1 · ALIENS 0'), F('sparkle', 'zero.', 0.5, 0.5)], props=['tour_sign_flat', 'alien_cutout']),
 dict(text="He wakes, spits out his coffee,",
      set='playa', cam='overlook_med', light='day', size='close', grammar=['dutch'], camera=dict(move='shake', amount=0.015, roll=-6, zoom=1.4),
      characters=[C('guide', 0.5, [B('He', arm=('hold', 'hang'), prop='mug', expr='neutral'), B('spits', arm=('hold', 'wave'), expr='shock', lean=8)], seated='van')],
      fx=[F('splash', 'spits', 0.42, 0.42), F('exclaim', 'coffee,', 0.58, 0.22, size=0.45)], props=['tour_van']),
 dict(text="and now sells ice tours. Five bucks. And he starts every one the same way:",
      set='playa', cam='playa_med', light='day', size='medium', camera=glide(G('ice', 6, zoom=1.15), G('starts', 10, zoom=1.9, x=0.42, y=0.72)),
      note='Loop: the guide, in a new ICE TOURS cap-with-antennae, leads tourists to the rock row; at "starts" the camera pushes to the same XCU as shot 1 (a hand pushing a GPS box into a rock) so the last frame matches the first.',
      characters=[C('guide', 0.40, [B('and', arm=('point', 'hold'), prop='flag', expr='grin'), B('starts', arm=('hold', 'hold'), prop='gps_box', expr='smug', lean=8)]),
                  C('tour1', 0.70, [B('and', arm=('hold', 'hang'), prop='camera', expr='smile')], scale=0.9)],
      fx=[F('sparkle', 'ice', 0.6, 0.3)], props=['tour_sign:ICE TOURS $5 (ALIEN crossed out, $40 crossed out)', 'rock_row_15', 'gps_box']),
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
spoken_years = 0                       # v5 says no years aloud
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

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
FX_NEW = {'ice_pane', 'ice_crack', 'sliding_rock', 'gps_ping', 'zzz', 'year_badge', 'dust_storm', 'rain', 'heat_haze', 'flash_flood'}   # requested from fx (BACKLOG)
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
 # --- HOOK (the last line loops into it)
 dict(text="Two cousins hid GPS trackers inside fifteen rocks, then waited for the rocks to run away.",
      set='playa', cam='playa_med', light='day', size='medium', grammar=['xcu', 'insert'],
      camera=glide(G('fifteen', 8, zoom=1.25, y=0.62), G('waited', 10, zoom=1.0), zoom=1.9, x=0.42, y=0.72),
      note='Opens on an extreme close-up of hands pushing the GPS box into a hollowed rock (zoom 1.9); pull-out to the cousins at "fifteen", to the camp and the rock row at "waited". Matches the last shot for the loop.',
      characters=[C('kip', 0.34, [B('Two', arm=('hold', 'hold'), prop='gps_box', lean=8), B('fifteen', arm=('hip', 'hold'), expr='smug'), B('run', arm=('hip', 'hip'), expr='grin')]),
                  C('lou', 0.68, [B('Two', arm=('hold', 'hang'), prop='screwdriver', expr='neutral'), B('waited', arm=('chin', 'hang'), expr='neutral', lean=-6)])],
      fx=[F('gps_ping', 'trackers', 0.42, 0.74, size=0.45), F('sparkle', 'fifteen', 0.5, 0.8)], props=['gps_box', 'rock_row_15', 'tent', 'timelapse_cam']),
 dict(text="On a Death Valley lake bed, some rocks heavier than a fridge leave long trails.",
      set='playa', cam='playa_wide', light='day', size='wide', grammar=['depth'], camera=glide(G('heavier', 8, zoom=1.2, x=0.45)),
      note='Depth-layered: a mid-size rock and its trail near, the cousins small at camp mid, mountains far; punch-in on the rock at "heavier" with a fridge silhouette beside it for scale.',
      characters=[C('kip', 0.46, [B('On', arm=('hold', 'hang'), prop='mug')]), C('lou', 0.56, [B('On', arm=('chin', 'hang'))])], fx=[], props=['rock_trail_hero', 'tent', 'fridge_silhouette']),
 dict(text="You see, nobody had ever seen one move.",
      set='playa', cam='rock_low', light='golden', size='close', grammar=['low_angle', 'xcu'], camera=glide(G('nobody', 8, zoom=1.6), zoom=1.15),
      characters=[], fx=[F('question_mark', 'move.', 0.62, 0.32, size=0.45)], props=['rock_trail_hero']),
 # --- THE RIVAL
 dict(text="A guide in alien antennae laughs at the cousins.",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('laughs', 8, zoom=1.12)),
      characters=[C('guide', 0.58, [B('A', arm=('wave', 'hang'), expr='grin'), B('laughs', arm=('point', 'hip'), expr='smug', lean=-8)]),
                  C('kip', 0.22, [B('A', arm=('hold', 'hang'), prop='gps_box')], view='rear')],
      fx=[], props=['tour_sign:ALIEN ROCK TOURS · NIGHT ONLY · $20', 'tour_van']),
 dict(text="\"Scientists blamed wind, then ice. A fenced-in rock escaped anyway!",
      set='playa', cam='overlook_med', light='day', size='close', grammar=['xcu', 'dutch'], camera=glide(G('fenced-in', 6, zoom=1.7, roll=8), zoom=1.45, roll=8, y=0.4),
      note='Dutch angle on the rival, ending on his face filling half the frame. Sepia thought-bubble cards pop beside him: a whirlwind (1948), ice (1950s), a small rock walking out of a stake fence (1960s). Draw the corral rock small (it was ~0.5 kg).',
      characters=[C('guide', 0.5, [B('Scientists', arm=('hip', 'wave'), expr='smug'), B('fenced-in', arm=('hip', 'point'), expr='grin', lean=-8)], talk=True)],
      fx=[F('year_badge', 'Scientists', 0.5, 0.14, label='1948'), F('whoosh', 'wind,', 0.75, 0.45, angle=90), F('sliding_rock', 'escaped', 0.75, 0.6, path=[(0.72, 0.6), (0.82, 0.55)], dur=0.8)], props=['tour_sign:ALIEN ROCK TOURS']),
 dict(text="It's aliens, pal. Twenty bucks a ticket.\"",
      set='inserts', cam='ticket', light='day', size='close', grammar=['pov'], camera=dict(move='push_in', amount=0.08),
      note='POV ticket insert; at "ticket" a hand tears the stub.',
      characters=[], fx=[F('sparkle', 'Twenty', 0.5, 0.45)], props=['ticket:ALIEN ROCK TOUR · NIGHT ONLY · ADMIT ONE · $20']),
 dict(text="And his night tours sell out.",
      set='playa', cam='overlook_med', light='night', size='wide', grammar=['crowd'], camera=dict(move='glide', direction='left', amount=0.06),
      note='Crowd at night: tourists in antenna headbands with flashlights in a row with the guide, at 0.8x so four fit.',
      characters=[C('tour1', 0.20, [B('And', arm=('wave', 'hold'), prop='flashlight', expr='grin')], scale=0.8), C('tour2', 0.40, [B('And', arm=('wave', 'wave'), expr='grin')], scale=0.8),
                  C('guide', 0.60, [B('sell', arm=('hold', 'hip'), prop='cash_fan', expr='smug')], scale=0.8), C('tour3', 0.80, [B('And', arm=('hold', 'hang'), prop='camera', expr='smile')], scale=0.8)],
      fx=[F('sparkle', 'out.', 0.6, 0.3)], props=['tour_sign:SOLD OUT']),
 # --- STAGE 1: month one (he mocks)
 dict(text="Month one: a dust storm buries their camera.",
      set='playa', cam='playa_wide', light='golden', size='wide', camera=dict(move='shake', amount=0.012, glides=[dict(at_word=6, to=dict(zoom=1.4, x=0.6, y=0.7), dur=6)]),
      note='The storm rolls over the camp; punch-in on the time-lapse tripod vanishing under dust at "buries"; the cousins cling to the tent poles.',
      characters=[C('kip', 0.40, [B('Month', arm=('hold', 'hold'), expr='neutral'), B('dust', arm=('wave', 'wave'), lean=-14, expr='shock')]), C('lou', 0.58, [B('storm', arm=('hold', 'hold'), lean=-16, expr='pained')])],
      fx=[F('year_badge', 'Month', 0.5, 0.14, label='MONTH 1'), F('dust_storm', 'dust', 0.5, 0.5), F('dust_puff', 'buries', 0.62, 0.8, direction='both')], props=['tent', 'timelapse_cam']),
 dict(text="\"Rocks one, nerds zero,\" says the guide.",
      set='playa', cam='overlook_med', light='golden', size='medium', camera=glide(G('nerds', 6, zoom=1.3)),
      note='He holds up their dusty camera like a trophy, then repaints the price to $30.',
      characters=[C('guide', 0.56, [B('Rocks', arm=('hold', 'hip'), prop='dusty_camera', expr='smug'), B('guide.', arm=('hold', 'hold'), prop='paintbrush', expr='grin', lean=-6)], talk=True)],
      fx=[F('sparkle', 'zero,', 0.66, 0.3)], props=['tour_sign:ALIEN ROCK TOURS · NIGHT ONLY · $30 ("$20" crossed out)']),
 # --- STAGE 2: year one (he profits)
 dict(text="Year one: a flash flood carries off their tent, cousins included.",
      set='playa', cam='playa_wide', light='golden', size='wide', camera=dict(move='follow', direction='right', glides=[dict(at_word=8, to=dict(zoom=1.35), dur=6)]),
      note='Slapstick: a brown wall of water sweeps the tent off its pegs and away (screen-right, camera follows); at "included" two heads pop out of the tent door. A generic comic setback at the camp (flash floods are a Death Valley hazard), not the playa pond and not the real team\'s history.',
      characters=[C('kip', 0.45, [B('Year', arm=('hold', 'hang'), prop='mug', expr='neutral'), B('included.', arm=('wave', 'wave'), expr='shock')]), C('lou', 0.56, [B('included.', arm=('wave', 'hang'), expr='shock')])],
      fx=[F('year_badge', 'Year', 0.5, 0.14, label='YEAR 1'), F('flash_flood', 'flash', 0.5, 0.7, direction='right'), F('splash', 'tent,', 0.5, 0.75)], props=['tent_floating']),
 dict(text="He sells ringside seats: \"Watch nerds float! Forty bucks.\"",
      set='playa', cam='overlook_med', light='golden', size='medium', grammar=['crowd'], camera=glide(G('Forty', 6, zoom=1.3, x=0.4)),
      note='Bleachers on the bank, tourists with popcorn; the guide with a megaphone; the sign repainted to $40.',
      characters=[C('guide', 0.36, [B('He', arm=('hold', 'point'), prop='megaphone', expr='grin'), B('Forty', arm=('wave', 'hold'), prop='cash_fan', expr='smug', lean=-6)], talk=True),
                  C('tour1', 0.66, [B('He', arm=('hold', 'hang'), prop='popcorn', expr='smile')], scale=0.85), C('tour2', 0.84, [B('float!', arm=('wave', 'hold'), prop='popcorn', expr='grin')], scale=0.85)],
      fx=[F('sparkle', 'Forty', 0.4, 0.3)], props=['bleachers', 'tour_sign:ALIEN ROCK TOURS · NIGHT ONLY · $40 ("$30" crossed out)']),
 dict(text="They paddle home on a cooler.",
      set='playa', cam='rock_low', light='golden', size='medium', camera=dict(move='follow', direction='right'),
      note='Both cousins on a floating cooler, paddling with a frying pan and a tracker antenna, past the cheering bleachers.',
      characters=[C('kip', 0.40, [B('They', arm=('hold', 'hold'), prop='frying_pan', expr='stern')], seated='cooler'), C('lou', 0.62, [B('They', arm=('hold', 'hold'), prop='gps_box', expr='pained')], seated='cooler')],
      fx=[F('splash', 'paddle', 0.5, 0.85), F('sweat_drop', 'cooler.', 0.62, 0.32, on='lou', size=0.45)], props=['cooler', 'flood_water']),
 # --- STAGE 3: year two (he puts on a show)
 dict(text="Year two, last try: he brings a vanload of fans to film their final failure, live.",
      set='playa', cam='overlook_med', light='frost', size='medium', grammar=['crowd'], camera=glide(G('film', 6, zoom=1.15), G('live.', 6, zoom=1.35, x=0.4)),
      note='The van at the road edge (never on the playa), a FINAL FAIL banner, fans raising phones; the guide speaks to a livestream phone on a stick.',
      characters=[C('guide', 0.34, [B('Year', arm=('hold', 'point'), prop='selfie_stick', expr='grin'), B('live.', arm=('hold', 'wave'), expr='smug', lean=-6)], talk=True),
                  C('tour1', 0.62, [B('film', arm=('hold', 'hold'), prop='phone', expr='grin')], scale=0.85), C('tour3', 0.82, [B('film', arm=('hold', 'hold'), prop='phone', expr='smile')], scale=0.85)],
      fx=[F('year_badge', 'Year', 0.5, 0.14, label='YEAR 2 · LAST TRY'), F('gps_ping', 'live.', 0.36, 0.3, size=0.45)], props=['tour_van', 'banner:FINAL FAIL · LIVE']),
 dict(text="Rain floods the lake bed; cold nights freeze it.",
      set='playa', cam='playa_top', light='night', size='medium', grammar=['metaphor'], camera=glide(G('cold', 8, zoom=1.2)),
      note='Top view: rain rings on an ankle-deep pond, then frost creeps over it at "freeze".',
      characters=[], fx=[F('rain', 'Rain', 0.5, 0.4), F('ice_pane', 'freeze', 0.5, 0.5, stage='freeze')], props=['rock_trail_hero', 'pond_water']),
 dict(text="One sunny morning, the ice crackles. Dozens of rocks start sliding, trackers included.",
      set='playa', cam='playa_med', light='frost', size='medium', grammar=['depth'], camera=glide(G('crackles.', 6, zoom=1.6, y=0.78), G('Dozens', 6, zoom=1.0), G('trackers', 6, zoom=1.3, y=0.45)),
      note='Starts as an XCU of crack lines racing through the thin ice; pulls back at "Dozens": the cousins in the foreground facing camera, rocks sliding behind them away from camera (no left/right claim); their laptop pings at "trackers".',
      characters=[C('kip', 0.32, [B('One', arm=('hold', 'hang'), prop='laptop', expr='neutral'), B('Dozens', arm=('point', 'hold'), expr='shock', lean=-6)]),
                  C('lou', 0.70, [B('One', arm=('hang', 'hang'), expr='neutral'), B('trackers', arm=('wave', 'wave'), expr='grin')])],
      fx=[F('ice_crack', 'ice', 0.5, 0.78), F('sliding_rock', 'Dozens', 0.5, 0.62, count=5, path='away', dur=2.4), F('gps_ping', 'trackers', 0.32, 0.6, size=0.45)], props=['ice_sheet']),
 # --- THE REVEAL (characters see it and react; mechanism + one analogy)
 dict(text="\"It's the ice!\" yell the cousins.",
      set='playa', cam='rock_low', light='frost', size='close', grammar=['low_angle'], camera=glide(G("It's", 6, zoom=1.4, y=0.6)),
      note='Low angle across the ice: both cousins at the edge, nose-to-nose with a pane as it bumps a rock; punch-in on their faces.',
      characters=[C('kip', 0.36, [B("It's", arm=('point', 'hang'), lean=20, expr='shock'), B('yell', arm=('wave', 'hang'), lean=10, expr='grin')], talk=True),
                  C('lou', 0.64, [B("It's", arm=('hold', 'hold'), lean=20, expr='shock'), B('cousins.', arm=('wave', 'wave'), lean=10, expr='grin')], talk=True)],
      fx=[F('ice_pane', "It's", 0.5, 0.8, stage='drift', view='side'), F('exclaim', 'ice!', 0.5, 0.25, size=0.45)], props=['ice_sheet']),
 dict(text="Sun cracks the phone-thin ice into huge panes; a light breeze shoves them into rocks.",
      set='playa', cam='playa_top', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('phone-thin', 6, zoom=1.4), G('huge', 6, zoom=0.9), G('rocks.', 8, zoom=1.3, x=0.6)),
      note='Top view: crack lines race across the sheet; at "phone-thin" a punch-in on a pane edge with a phone silhouette for scale; pull back to the panes; wind lines, panes and a rock move screen-right, the trail drawing on behind it.',
      characters=[], fx=[F('ice_crack', 'Sun', 0.5, 0.5), F('ice_pane', 'panes;', 0.5, 0.5, stage='panes'), F('whoosh', 'breeze', 0.3, 0.5, angle=0),
                         F('ice_pane', 'shoves', 0.5, 0.5, stage='drift', direction='right'), F('sliding_rock', 'rocks.', 0.55, 0.5, path=[(0.55, 0.5), (0.75, 0.5)], dur=1.5, trail=True)],
      props=['ice_sheet', 'phone_silhouette']),
 dict(text="Air hockey for boulders: a steady shove, and even a fridge glides.",
      set='playa', cam='playa_med', light='frost', size='medium', grammar=['metaphor'], camera=glide(G('fridge', 8, zoom=1.25, x=0.4)),
      note='Air-hockey overlay on the ice: a big pane "mallet" pushes a rock, then a fridge, which glides off on its own furrow at "glides"; Lou watches deadpan, Kip films it.',
      characters=[C('lou', 0.72, [B('Air', arm=('hang', 'hang'), expr='neutral'), B('fridge', arm=('chin', 'hang'), expr='smug')]),
                  C('kip', 0.22, [B('Air', arm=('hold', 'hold'), prop='camera', expr='grin')])],
      fx=[F('whoosh', 'shove,', 0.35, 0.55, angle=0), F('sliding_rock', 'glides.', 0.45, 0.75, sprite='fridge', path=[(0.45, 0.75), (0.6, 0.75)], dur=1.2, trail=True)],
      props=['air_hockey_overlay', 'fridge']),
 # --- THE RIVAL'S SHOW BACKFIRES + LOOP
 dict(text="His livestream shows the world rocks sliding in broad daylight.",
      set='inserts', cam='gps_screen', light='day', size='close', grammar=['pov'], camera=glide(G('world', 6, zoom=1.2), G('daylight.', 6, zoom=1.4)),
      note='POV insert: his livestream phone screen, "LIVE · 1.2M watching", comments flying ("ICE??", "REFUND"), the shot showing rocks sliding in sunshine; then the guide\'s horrified face in the selfie camera.',
      characters=[], fx=[F('sparkle', 'world', 0.5, 0.3), F('exclaim', 'daylight.', 0.5, 0.3, size=0.45)], props=['livestream_screen:LIVE · 1.2M WATCHING · "ICE??" "REFUND"']),
 dict(text="An ice pane drives one through his NIGHT ONLY sign,",
      set='playa', cam='rock_low', light='frost', size='medium', camera=dict(move='glide', glides=[dict(at_word=2, to=dict(zoom=1.15), dur=8), dict(at_word=5, to=dict(zoom=1.35, y=0.55), dur=6)]),
      note='Spectacle: low angle, an ice pane drives a MID-SIZE rock into the sign standing at the playa edge; at "through" the sign splits and falls flat. Draw the push slow (real rocks crept at 2-5 m/min); the sign is our fiction.',
      characters=[], fx=[F('ice_pane', 'ice', 0.45, 0.75, stage='drift', view='side'), F('sliding_rock', 'drives', 0.45, 0.72, path='away', dur=1.6, trail=True), F('impact_star', 'through', 0.55, 0.55)],
      props=['tour_sign_free:ALIEN ROCK TOURS · NIGHT ONLY (a separate sprite that splits and topples)', 'alien_cutout']),
 dict(text="and his refund cash blows away on the same breeze.",
      set='playa', cam='overlook_med', light='frost', size='medium', camera=dict(move='glide', direction='right', glides=[dict(at_word=4, to=dict(zoom=1.3, x=0.35), dur=6)]),
      note='Slapstick button: the guide clutching a fan of bills; the breeze peels them off one by one and they flutter after the panes; his fans hold out torn tickets.',
      characters=[C('guide', 0.34, [B('and', arm=('hold', 'hold'), prop='cash_fan', expr='nervous'), B('blows', arm=('wave', 'wave'), expr='shock', lean=12)]),
                  C('tour1', 0.62, [B('refund', arm=('point', 'hold'), prop='ticket', expr='stern')], scale=0.85), C('tour3', 0.82, [B('refund', arm=('hold', 'point'), prop='ticket', expr='stern')], scale=0.85)],
      fx=[F('whoosh', 'blows', 0.5, 0.4, angle=0), F('sweat_drop', 'cash', 0.34, 0.32, on='guide', size=0.45)], props=['flying_bills']),
 dict(text="\"Nerds one, aliens zero,\" say the cousins.",
      set='playa', cam='overlook_med', light='day', size='medium', camera=glide(G('cousins.', 6, zoom=1.2, x=0.55)),
      note='The cousins deliver the callback to his face, holding up a piece of the broken sign; scoreboard badge NERDS 1 · ALIENS 0 (flips his "Rocks one, nerds zero").',
      characters=[C('kip', 0.30, [B('Nerds', arm=('hold', 'hold'), prop='sign_piece', expr='smug')], talk=True), C('lou', 0.52, [B('aliens', arm=('point', 'hang'), expr='grin')], talk=True),
                  C('guide', 0.78, [B('Nerds', arm=('hang', 'hang'), expr='pained', lean=8)])],
      fx=[F('year_badge', 'Nerds', 0.5, 0.14, label='NERDS 1 · ALIENS 0')], props=['tour_van', 'tour_sign_flat']),
 dict(text="Now he sells ice tours, five bucks, and opens every one the same way:",
      set='playa', cam='playa_med', light='day', size='medium', camera=glide(G('five', 6, zoom=1.15), G('opens', 10, zoom=1.9, x=0.42, y=0.72)),
      note='Loop: the guide in an ICE TOURS cap-with-antennae leads tourists along the road edge (they stay off the wet playa), sign "ICE TOURS $5"; at "opens" the camera pushes to the same XCU as shot 1 (a hand pushing a GPS box into a rock), so the last frame matches the first.',
      characters=[C('guide', 0.40, [B('Now', arm=('point', 'hold'), prop='flag', expr='grin'), B('opens', arm=('hold', 'hold'), prop='gps_box', expr='smug', lean=8)]),
                  C('tour1', 0.70, [B('Now', arm=('hold', 'hang'), prop='camera', expr='smile')], scale=0.9)],
      fx=[F('sparkle', 'five', 0.6, 0.3)], props=['tour_sign:ICE TOURS $5 (ALIEN crossed out)', 'rock_row_15', 'gps_box']),
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
    'contains "You see,"': any('You see,' in s['text'] for s in SHOTS),
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

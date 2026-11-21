# Builds shots.json from the shot list below and runs the automatic script checks (QA.md › scripts).
# Usage: python3 scripts/bike-countersteer/build.py   (exits non-zero if a check fails)
# Beats/fx name an anchor word; it is converted to a 0-based word index within the shot's text ("at_word").
import json, re, sys, pathlib

HERE = pathlib.Path(__file__).parent
EXPRS = {'neutral', 'stern', 'grin', 'shock', 'nervous', 'smile', 'smug', 'pained'}       # characters/scripts/bean.py
ARMS = {'hang', 'wave', 'point', 'hold', 'hip', 'chin'}
NEW_ARMS = {'ride'}                                     # requested from characters (BACKLOG)
FX_OK = {'explosion', 'impact_star', 'dust_puff', 'speed_lines', 'sweat_drop', 'anger_vein', 'glow_eyes',
         'sparkle', 'splash', 'question_mark', 'exclaim', 'music_note'}
FX_NEW = {'steer_arrow', 'path_line'}                  # requested from fx (BACKLOG)

CAST = {   # our own designs, built with characters/scripts/bean.py character(...)
    'you':        dict(build='adult', skin='#f6d2b0', shirt='#3fb37f', pants='#2f3f6b', hat='beanie', hat_col='#f2c230', seed=11),
    'dale':       dict(build='stout', skin='#ffe2c2', shirt='#d9452f', pants='#30343f', hat='helmet', hat_col='#f4f1e8',
                       moustache='#6b4426', outfit=('stripes',), seed=4),
    'instructor': dict(build='adult', skin='#c98e63', shirt='#2f6fb3', pants='#e8e2d0', hat='cap', hat_col='#2b2f3a',
                       glasses=True, outfit=('collar',), prop='clipboard', seed=9),
}

def C(cid, x, beats=(), **kw):
    return dict(id=cid, x=x, beats=list(beats), **kw)
def B(word, **kw): return dict(word=word, **kw)
def F(name, word, x, y, **kw): return dict(name=name, word=word, x=x, y=y, **kw)

SHOTS = [
 dict(text="Ride into a left turn, and your bike steers right first, without you knowing it.",
      set='village', cam='street_med', light='day', size='medium', camera=dict(move='push_in', amount=0.05),
      characters=[C('you', 0.5, [B('Ride', arm='ride', lean=0), B('first,', lean=-18)], rig='bicycle', view='rear')],
      fx=[F('steer_arrow', 'right', 0.62, 0.62, direction='right'), F('speed_lines', 'Ride', 0.2, 0.6)], props=['bicycle']),
 dict(text="Meet Dale. Twenty years on motorcycles, and he swears he steers by leaning.",
      set='track', cam='rider_close', light='day', size='close', camera=dict(move='glide', at_word='swears', to=dict(zoom=1.10), dur=8),
      characters=[C('dale', 0.5, [B('Meet', arm=('hip', 'hang'), expr='smug'), B('leaning', lean=-10, expr='grin')])],
      fx=[F('sparkle', 'twenty', 0.4, 0.3)], props=['helmet_sticker:I STEER WITH MY HIPS', 'motorbike']),
 dict(text="So a riding school hands him a strange bike.",
      set='track', cam='track_med', light='day', size='medium', camera=dict(move='glide', direction='right', amount=0.06),
      characters=[C('instructor', 0.308, [B('hands', arm=('point', 'hold'), expr='neutral')]), C('dale', 0.768, [B('strange', arm=('chin', 'hang'), expr='nervous')])],
      fx=[F('question_mark', 'strange', 0.768, 0.38, on='dale', size=0.45)], props=['banner:BODY-STEERING CHALLENGE', 'nobs_bike']),
 dict(text="It has two handlebars: a normal one, and one bolted to the frame that can't steer.",
      set='track', cam='bike_close', light='day', size='close', camera=dict(move='tilt_up', amount=0.06),
      characters=[], fx=[F('sparkle', 'normal', 0.45, 0.55), F('exclaim', 'bolted', 0.55, 0.30, size=0.45), F('steer_arrow', "can't", 0.5, 0.36, direction='blocked')],
      props=['nobs_bike']),
 dict(text="\"Hold the fixed bars,\" says the instructor, \"and take that corner.\"",
      set='track', cam='pit_ots', light='day', size='medium', camera=dict(move='push_in', amount=0.04),
      characters=[C('instructor', 0.64, [B('Hold', arm=('hang', 'hold'), expr='stern'), B('corner', arm=('hold', 'point'), expr='smug')], talk=True, scale=1.15),
                  C('dale', 0.15, [B('Hold', arm=('hip', 'hip'))], view='rear')],
      fx=[], props=['nobs_bike']),
 dict(text="Dale laughs, rolls onto the track, and leans hard left.",
      set='track', cam='track_med', light='day', size='medium', camera=dict(move='follow', direction='left'),
      characters=[C('dale', 0.5, [B('laughs', arm='ride'), B('leans', body_lean=-28, bike_lean=3)], rig='nobs_bike', view='rear')],
      fx=[F('dust_puff', 'rolls', 0.62, 0.86, direction='right'), F('speed_lines', 'track', 0.25, 0.55)], props=['nobs_bike']),
 dict(text="Almost nothing happens.",
      set='track', cam='bike_chase', light='day', size='medium', camera=dict(move='glide', at_word='Almost', to=dict(zoom=1.35), dur=10),
      characters=[C('dale', 0.5, [B('Almost', arm='ride', body_lean=-28, bike_lean=3)], rig='nobs_bike', view='rear')],
      fx=[], props=['nobs_bike']),
 dict(text="He leans harder, sticks his knee out, and wiggles his hips like he's at a wedding.",
      set='track', cam='track_med', light='day', size='medium', camera=dict(move='shake', amount=0.01),
      characters=[C('dale', 0.5, [B('He', arm='ride', body_lean=-28, bike_lean=3), B('leans', body_lean=-32, bike_lean=4), B('knee', knee_out=True), B(8, body_lean=-20), B(9, body_lean=-34), B(10, body_lean=-20), B(11, body_lean=-34), B(12, body_lean=-22)], rig='nobs_bike', view='rear')],
      fx=[F('sweat_drop', 'harder', 0.58, 0.32, size=0.45), F('music_note', 'wedding', 0.3, 0.4, size=0.45)], props=['helmet_sticker:I STEER WITH MY HIPS']),
 dict(text="The bike barely turns and runs wide across the whole track.",
      set='track', cam='track_top', light='day', size='wide', camera=dict(move='hold'),
      characters=[C('dale', 0.5, [B('barely', body_lean=-20, bike_lean=-5)], rig='nobs_bike', view='top', path='wide_arc')],
      fx=[F('path_line', 'The', 0.5, 0.5, planned='tight_left', actual='wide_arc'), F('dust_puff', 'across', 0.82, 0.3)], props=[]),
 dict(text="Twenty years of riding, and he can't make the corner.",
      set='track', cam='rider_close', light='day', size='close', camera=dict(move='glide', at_word='corner', to=dict(zoom=1.12), dur=8),
      characters=[C('dale', 0.5, [B('Twenty', expr='pained', arm='hang'), B('corner', arm=('chin', 'hang'), expr='nervous')])],
      fx=[F('sweat_drop', 'corner', 0.62, 0.30, on='dale', dx=0.12, size=0.45)], props=[]),
 dict(text="Wait, if leaning your body doesn't turn the bike, what does?",
      set='track', cam='track_med', light='day', size='medium', camera=dict(move='push_in', amount=0.06),
      characters=[C('dale', 0.5, [B('Wait', arm=('chin', 'hang'), expr='nervous')])],
      fx=[F('question_mark', 'does', 0.65, 0.25, on='dale', dx=0.14, size=0.5)], props=[]),
 dict(text="You see, bikes turn by leaning the whole bike, and to lean it left, you steer right for a split second.",
      set='track', cam='bike_chase', light='golden', size='medium', camera=dict(move='glide', at_word='You', to=dict(zoom=1.35), dur=12),
      characters=[C('dale', 0.5, [B('You', arm='ride', lean=0)], rig='motorbike', view='rear', insert=dict(at_word='steer', until_word='split', cam='track_top', view='top'))],
      fx=[F('steer_arrow', 'right', 0.5, 0.42, direction='right'), F('path_line', 'steer', 0.5, 0.5, planned='tight_left', actual='kink_right_then_left')], props=[]),
 dict(text="That nudge pulls the wheels out from under you, so the bike tips left, then turns left.",
      set='track', cam='bike_chase', light='golden', size='close', camera=dict(move='glide', zoom=1.35, glides=[dict(at_word='turns', to=dict(zoom=1.2, x=0.45), dur=14)]),
      characters=[C('dale', 0.5, [B('That', arm='ride', lean=0), B('pulls', contact_shift='right'), B('tips', lean=-24), B('turns', lean=-26)], rig='motorbike', view='rear')],
      fx=[F('steer_arrow', 'nudge', 0.5, 0.6, direction='right', size=0.55, dur=1.4, color='#ffd23f'), F('dust_puff', 'wheels', 0.56, 0.9, direction='right')], props=[]),
 dict(text="It's like balancing a broom on your palm: to tip it left, flick your hand right first.",
      set='track', cam='rider_close', light='golden', size='close', camera=dict(move='hold'),
      characters=[C('dale', 0.5, [B("It's", arm=('hang', 'hang'), expr='neutral'), B('tip', broom_tip_left=True), B('flick', broom_flick_right=True)],
                    insert=dict(at_word='broom', rig='broom_insert', cam='grips_close'))],
      fx=[F('speed_lines', 'flick', 0.58, 0.55), F('sparkle', 'first', 0.4, 0.2)], props=['broom']),
 dict(text="Riders do it without noticing, but the fixed bars stopped Dale's hands from doing it.",
      set='track', cam='track_med', light='golden', size='medium', camera=dict(move='push_in', amount=0.06),
      characters=[C('dale', 0.5, [B('Riders', arm='ride', lean=0), B('noticing,', lean=-22)], rig='motorbike', view='rear', insert=dict(at_word='fixed', rig='nobs_bike', cam='grips_close', view='front'))],
      fx=[F('steer_arrow', 'Riders', 0.62, 0.5, direction='right', scale=0.6), F('sparkle', 'hands', 0.6, 0.55), F('steer_arrow', 'stopped', 0.5, 0.5, direction='blocked')], props=['motorbike', 'nobs_bike']),
 dict(text="Motorcycle schools teach it on purpose: push the left grip forward to go left.",
      set='track', cam='pit_med', light='golden', size='medium', camera=dict(move='hold'),
      note='pit_med is the only cam with the chalkboard, so the two-shot steps back to 0.86x; the engine grade lifts the dark golden plate (g0.64).',
      characters=[C('instructor', 0.678, [B('Motorcycle', arm=('hang', 'hold'), expr='stern'), B('push', arm=('point', 'hold'), expr='smug', points_at='chalkboard')]),
                  C('dale', 0.248, [B('Motorcycle', arm=('chin', 'hang'), expr='nervous'), B('left.', arm=('hip', 'hip'), expr='shock')])],
      fx=[F('exclaim', 'left', 0.248, 0.3, on='dale', anchor='above', size=0.45)], props=['chalkboard:PUSH LEFT → GO LEFT (drawing from above: left grip pushed forward, front wheel points right, bike leans left)']),
 dict(text="And yes, bicycles too.",
      set='village', cam='street_med', light='golden', size='medium', camera=dict(move='glide', direction='left', amount=0.06),
      characters=[C('you', 0.5, [B('And', arm='ride', lean=0), B('bicycles', lean=-18)], rig='bicycle', view='rear')],
      fx=[F('speed_lines', 'And', 0.2, 0.6), F('exclaim', 'too.', 0.62, 0.28, size=0.45), F('steer_arrow', 'yes,', 0.6, 0.62, direction='right', scale=0.6)], props=['bicycle']),
 dict(text="So Dale's been steering the wrong way for twenty years, and it's the only way he ever turned.",
      set='track', cam='pit_ots', light='golden', size='medium', camera=dict(move='glide', at_word='only', to=dict(zoom=1.10), dur=8),
      characters=[C('dale', 0.40, [B('So', arm=('hold', 'hang'), expr='pained', prop='helmet'), B('wrong', arm=('hold', 'chin'), expr='nervous'), B('only', arm=('hold', 'hip'), expr='smile')], hat=None, scale=1.2),
                  C('instructor', 0.84, [B('So', arm=('hold', 'hang'))], view='rear')],
      fx=[], props=['helmet_sticker:I STEER WITH MY HIPS']),
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
    sid = f's{i:02d}'; s = dict(s)
    for c in s['characters']:
        if c['id'] not in CAST: errors.append(f'{sid}: unknown character {c["id"]}')
        c.update({k: v for k, v in CAST[c['id']].items() if k not in c})
        for b in c['beats']:
            b['at_word'] = idx(s['text'], b.pop('word'), sid)
            if 'expr' in b and b['expr'] not in EXPRS: errors.append(f'{sid}: expr {b["expr"]}')
            for a in ([b['arm']] if isinstance(b.get('arm'), str) else list(b.get('arm', ()))):
                if a not in ARMS | NEW_ARMS: errors.append(f'{sid}: arm {a}')
            if 'arm' in b: b['arm_pose'] = b.pop('arm')
        if 'insert' in c:
            for k in ('at_word', 'until_word'):
                if k in c['insert']: c['insert'][k] = idx(s['text'], c['insert'][k], sid)
        if not (0.15 <= c['x'] <= 0.85): errors.append(f'{sid}: {c["id"]} x={c["x"]} near the edge')
    if 'cut' in s: s['cut']['at_word'] = idx(s['text'], s['cut']['at_word'], sid)
    if isinstance(s['camera'].get('at_word'), str): s['camera']['at_word'] = idx(s['text'], s['camera']['at_word'], sid)
    for g in s['camera'].get('glides', []): g['at_word'] = idx(s['text'], g['at_word'], sid)
    for f in s['fx']:
        f['at_word'] = idx(s['text'], f.pop('word'), sid)
        if f['name'] not in FX_OK | FX_NEW: errors.append(f'{sid}: fx {f["name"]}')
    out.append(dict(id=sid, **s))

hook = SHOTS[0]['text']; n_hook = len(words(hook))
total = sum(len(words(s['text'])) for s in SHOTS)
vo_sec = (HERE / 'SCRIPT.md').read_text().split('## Voice-over', 1)[1].split('\n## ', 1)[0]
vo = [l.split('. ', 1)[1] for l in vo_sec.splitlines() if re.match(r'^\d+\. ', l)]
sizes = [s['size'] for s in SHOTS]
checks = {
    'hook 10-16 words': 10 <= n_hook <= 16,
    'total 170-240 words': 170 <= total <= 240,
    'every SCRIPT.md line has a shot with identical text': vo == [s['text'] for s in SHOTS],
    'contains "You see,"': any(s['text'].startswith('You see,') for s in SHOTS),
    'shot mix: medium >= 50%, close 15-30%, wide <= 25%': sizes.count('medium') / len(sizes) >= 0.5 and 0.15 <= sizes.count('close') / len(sizes) <= 0.3 and sizes.count('wide') / len(sizes) <= 0.25,
    'no validation errors': not errors,
}
json.dump(dict(slug='bike-countersteer', title='Why Your Bike Steers Backwards First', words_per_s=3.7,
               note='Left/right/lean signs are always the RIDER\'s: negative lean = rider leans to their left; steer_arrow direction = rider\'s side; view rear = chase cam behind the rider. insert = cut-in of another rig/cam at that word; shot-level cut = switch cam at that word; contact_shift = slide the tyre contact patch sideways (rider side). at_word = 0-based word index within the shot text (split on spaces). Character look fields are kwargs of characters/scripts/bean.py character(); arm_pose "ride", hat "helmet", rig/view, knee_out, broom_* and props marked in SCRIPT.md are requested in BACKLOG.md.',
               shots=out), open(HERE / 'shots.json', 'w'), indent=1, ensure_ascii=False)
print(f'hook {n_hook} words, total {total} words = {total / 3.7:.1f} s at 3.7 w/s, {len(SHOTS)} shots, mix', {k: sizes.count(k) for k in set(sizes)})
for e in errors: print('ERROR', e)
for k, v in checks.items(): print('PASS' if v else 'FAIL', k)
sys.exit(0 if all(checks.values()) else 1)

# Stand-in test inputs for the engine until scripts/ and audio/ ship the real ones:
#   - shots.json: a placeholder cut of "Why Your Bike Steers Backwards First" on the stand-in village plates
#     (the real script and shots.json come from branch claude/area-scripts; this text is NOT the voice-over);
#   - words.json: fake word timings at 3.7 words/s with a pause after each sentence.
# usage: python engine/test/make_test.py engine/test/bike_standin
import json, os, sys

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bike_standin')
os.makedirs(out, exist_ok=True)
RIDER = {'id': 'rider', 'build': 'adult', 'skin': '#ffe2c2', 'shirt': '#4a86e0', 'pants': '#2f3540', 'hat': 'cap',
         'hat_col': '#e2453c', 'outfit': [['stripes', '#f2f2f2']], 'seed': 5}
KID = {'id': 'kid', 'build': 'kid', 'skin': '#c99067', 'shirt': '#f08a2c', 'pants': '#3b5b9a', 'hair': 'bun',
       'hair_col': '#1f1a1a', 'seed': 9}
shots = [
    {'id': 's01', 'text': 'Every cyclist steers the wrong way first, and almost nobody knows it.',
     'set': 'village', 'cam': 'M', 'light': 'day', 'camera': {'move': 'push_in', 'amount': 0.05},
     'characters': [dict(RIDER, x=0.5, facing=0.3, expr='neutral',
                         beats=[{'at_word': 2, 'pose': 'point', 'expr': 'smug'}, {'at_word': 9, 'pose': 'idle', 'expr': 'shock', 'action': 'jolt'}])]},
    {'id': 's02', 'text': 'Watch a rider turn left at speed.', 'transition': 'crossfade',
     'set': 'village', 'cam': 'A', 'light': 'day', 'camera': {'move': 'push_in', 'amount': 0.04, 'focus': [0.5, 0.62]},
     'characters': [dict(RIDER, x=0.40, facing=0.4, expr='smile'),
                    dict(KID, x=0.63, facing=-0.4, expr='neutral', beats=[{'at_word': 3, 'pose': 'think', 'expr': 'nervous'}])]},
    {'id': 's03', 'crop': True, 'text': 'Just before the turn, the handlebars flick right.', 'transition': 'whip',
     'set': 'village', 'cam': 'M', 'light': 'day',
     'camera': {'move': 'push_in', 'amount': 0.03, 'glides': [{'at_word': 6, 'dur': 10, 'ease': 'out', 'to': {'zoom': 1.12, 'y': 0.42}}]},
     'characters': [dict(RIDER, x=0.5, facing=0.0, expr='neutral', beats=[{'at_word': 6, 'pose': 'point', 'expr': 'stern', 'facing': 0.5}])],
     'fx': [{'name': 'exclaim', 'at_word': 6, 'on': 'rider', 'anchor': 'head', 'dx': 0.16, 'size': 0.22, 'dur': 0.9, 'kick': True}]},
    {'id': 's04', 'text': 'The tyres slide out to the right, so the bike leans left.',
     'set': 'village', 'cam': 'M', 'light': 'day', 'camera': {'move': 'push_in', 'amount': 0.04},
     'characters': [dict(RIDER, x=0.56, facing=-0.4, expr='nervous',
                         beats=[{'at_word': 3, 'action': 'shake'}, {'at_word': 10, 'x': 0.44, 'pose': 'hips', 'expr': 'stern'}])],
     'fx': [{'name': 'sweat_drop', 'at_word': 3, 'on': 'rider', 'anchor': 'head', 'dx': -0.13, 'size': 0.14, 'dur': 1.0}]},
    {'id': 's05', 'text': 'And a leaning bike turns toward its lean.', 'transition': 'crossfade',
     'set': 'village', 'cam': 'A', 'light': 'day', 'camera': {'move': 'push_in', 'amount': 0.04, 'focus': [0.5, 0.62]},
     'characters': [dict(RIDER, x=0.40, facing=0.4, expr='neutral', talk=True, beats=[{'at_word': 4, 'pose': 'present', 'expr': 'smile'}]),
                    dict(KID, x=0.63, facing=-0.4, expr='nervous', beats=[{'at_word': 5, 'pose': 'cheer', 'expr': 'grin', 'action': 'hop'}])]},
    {'id': 's06', 'text': 'Push left, go left. Your body knew it all along.',
     'set': 'village', 'cam': 'M', 'light': 'day', 'camera': {'move': 'push_in', 'amount': 0.05},
     'characters': [dict(RIDER, x=0.5, facing=0.0, expr='smile', talk=True,
                         beats=[{'at_word': 2, 'facing': -0.5, 'pose': 'point'}, {'at_word': 5, 'facing': 0.0, 'pose': 'cheer', 'expr': 'grin', 'action': 'hop'}])],
     'fx': [{'name': 'sparkle', 'at_word': 6, 'x': 0.5, 'y': 0.2, 'size': 0.45, 'dur': 1.2}]},
]
json.dump({'slug': 'bike-countersteer-standin', 'title': 'Why Your Bike Steers Backwards First (engine stand-in)', 'shots': shots},
          open(os.path.join(out, 'shots.json'), 'w'), indent=1)
words, t = [], 0.3
for s in shots:
    for w in s['text'].split():
        words.append({'word': w.strip('.,!?'), 'start': round(t, 3), 'end': round(t + 0.22, 3)})
        t += 1 / 3.7 + (0.35 if w[-1] in '.!?' else 0.12 if w[-1] == ',' else 0)
json.dump(words, open(os.path.join(out, 'words.json'), 'w'), indent=0)
print(len(words), 'words', round(t, 2), 's')

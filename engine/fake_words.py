# Fake words.json for a shots.json, until audio ships the real one: 3.7 words/s, a pause after each sentence.
# usage: python engine/fake_words.py shots.json words.json [words_per_s]
import json, sys
shots = json.load(open(sys.argv[1]))['shots']; wps = float(sys.argv[3]) if len(sys.argv) > 3 else 3.7
words, t = [], 0.3
for s in shots:
    for w in s['text'].split():
        words.append({'word': w.strip('.,!?:;"'), 'start': round(t, 3), 'end': round(t + 0.8 / wps, 3)})
        t += 1 / wps + (0.35 if w.rstrip('"')[-1] in '.!?' else 0.12 if w.rstrip('"')[-1] in ',:;' else 0)
json.dump(words, open(sys.argv[2], 'w'), indent=0)
print(len(words), 'words', round(t, 2), 's')

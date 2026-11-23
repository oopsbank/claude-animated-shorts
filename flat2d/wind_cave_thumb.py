"""Caption-free thumbnail frame for Wind Cave: the hole blowing out hard, Tom's hat flying off, Tom reacting
(s03, HIDE_UI, the gust at its peak). Headline added by tools/thumbnail.py.

usage: .venv/bin/python flat2d/wind_cave_thumb.py OUT.png
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wind_cave as B

B.HIDE_UI = True
ws = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio/wind-cave/words.json')))
line3 = ws[27:38]                                      # line 3 words (lines 1-2 have 14 + 13 words)
t0 = line3[0]['start'] - .1
cue = lambda i: line3[min(i, len(line3) - 1)]['start'] - t0
u = cue(9) - .3 + float(sys.argv[2]) if len(sys.argv) > 2 else cue(9) - .3 + .32
img, _ = B.s03(u, 2.84, cue)
img.convert('RGB').save(sys.argv[1])

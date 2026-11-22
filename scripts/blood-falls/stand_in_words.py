"""Stand-in words.json for blood-falls (no voice yet): SCRIPT.md voice-over at 3.7 words/s.

usage: .venv/bin/python scripts/blood-falls/stand_in_words.py OUT.json
Each word gets a duration by its length (spoken years count as 2-3 words, LESSONS), with a 0.22 s gap
between lines and 0.14 s after a sentence end inside a line. Each line plus its gap keeps n_words / 3.7 s.
Output: [{"word", "start", "end", "line"}] (the engine's words.json, plus the line index).
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RATE = 3.7; LINE_GAP = 0.22; STOP_GAP = 0.14


def lines():
    txt = open(os.path.join(ROOT, 'scripts/blood-falls/SCRIPT.md')).read()
    body = txt.split('## Voice-over')[1].split('##')[0]
    return [m.group(1).strip() for m in re.finditer(r'^\d+\. (.+)$', body, re.M)]


def spoken(w):
    core = re.sub(r'[^\w]', '', w)
    if re.fullmatch(r'1[89]\d\d', core): return 2.0          # "nineteen eleven"
    return 1.0


def build():
    out, t = [], 0.15
    for li, line in enumerate(lines(), 1):
        words = line.split()
        n = sum(spoken(w) for w in words); dur = n / RATE - LINE_GAP  # gaps sit inside the 3.7 w/s budget
        stops = sum(1 for w in words[:-1] if re.search(r'[.?!:]["”]?$', w))
        speak = dur - stops * STOP_GAP
        wts = [spoken(w) * (0.55 + 0.45 * len(re.sub(r'\W', '', w)) / 5.0) for w in words]
        k = speak / sum(wts)
        for w, wt in zip(words, wts):
            d = wt * k
            out.append({'word': w, 'start': round(t, 3), 'end': round(t + d * 0.92, 3), 'line': li})
            t += d
            if re.search(r'[.?!:]["”]?$', w) and w is not words[-1]: t += STOP_GAP
        t += LINE_GAP
    return out


if __name__ == '__main__':
    ws = build(); json.dump(ws, open(sys.argv[1], 'w'), indent=0)
    print(len(ws), 'words, ends', ws[-1]['end'])
    for li in range(1, 17):
        l = [w for w in ws if w['line'] == li]; print(li, l[0]['start'], l[-1]['end'])

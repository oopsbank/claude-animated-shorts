import json, sys
a = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "alignment.json"))
ch, st, en = a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]
words, cur = [], None
for c, s, e in zip(ch, st, en):
    if c.isspace():
        if cur: words.append(cur); cur = None
        continue
    if cur is None: cur = {"w": "", "s": s, "e": e}
    cur["w"] += c; cur["e"] = e
if cur: words.append(cur)
json.dump(words, open(sys.argv[2] if len(sys.argv) > 2 else "words.json", "w"), indent=0)
for i, w in enumerate(words):
    gap = w["s"] - words[i-1]["e"] if i else 0
    print(f"{w['s']:6.2f} {w['e']:6.2f} {'  GAP %.2f' % gap if gap > 0.25 else ''} {w['w']}")

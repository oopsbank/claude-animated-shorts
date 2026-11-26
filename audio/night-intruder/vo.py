"""The whispered narration (ME, the Director's 4 lines) for build.py: cached eleven_v3 takes (vo_raw/lineN.json) ->
phrases cut at the take's own silences -> placed one by one in the foley gaps -> close-mic processing.

Each phrase is a punctuation group of the line ("Midnight," / "exactly..." / "a noise downstairs." ...); the take's
energy segments are matched 1:1 to these groups. PLACE gives the speech onset of every phrase on the picture.
Word times: the phrase's energy segment split by letter weights (the v3 alignment runs early and stretches the last
word over the pause, so it only sets the first word's onset when that is later than the energy onset, e.g. after
an [exhales]).
"""
import base64
import json
import os
import re
import subprocess

import numpy as np
from dsp import SR, ns, dbg, hp, lp, bp, shelf, peq, fades, momentary_max, pan, convolve_st

OD = os.path.dirname(os.path.abspath(__file__))
PRE, POST = 0.16, 0.12          # s kept before each phrase onset (the breath in) / after its end
FLOOR = 38.0                    # dB under the take's peak (10 ms RMS) = silence
BRIDGE = 0.12                   # s: shorter dips stay inside a phrase

# speech onset of each phrase on the picture (s)
PLACE = {
    1: [0.85, 1.62, 3.05, 5.35],      # Midnight, | exactly... | (clack 2.55) a noise downstairs. | (wind) Not the wind.
    2: [14.30, 16.55, 18.60],         # There was a child in the house. | I grabbed the desk lamp... | praying ...
    3: [23.60, 25.90],                # He was alone. | [exhales] If I could just get behind him...
    4: [60.55, 61.55, 64.40],         # I got it wrong. | They... | (elbow, huff, groan) weren't alone.
}
LEVEL = -16.5                   # max momentary LUFS of the narration stem before the master gain
MODEL, VOICE = "eleven_v3", "Will (premade, bIHbv24MWmeRgasZH58o)"
DUCK_DB = -4.0                  # foley / body / amb under the narration


def decode(b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "mp3", "-i", "-", "-ac", "1", "-ar", str(SR), "-f", "f32le",
                          "-"], input=b, check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def segments(a):
    h = SR // 100
    e = np.array([20 * np.log10(np.sqrt(np.mean(a[i:i + h] ** 2)) + 1e-9) for i in range(0, len(a) - h, h)])
    on = e > e.max() - FLOOR
    br = int(BRIDGE * 100)
    segs, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and (on[j] or on[j:j + br].any()):
                j += 1
            if j - i >= 8:          # ignore blips shorter than 80 ms
                segs.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    return segs


def groups(text):
    words = re.sub(r"\[[^\]]*\]", " ", text).split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[,.?!]$", w):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def align_starts(d):
    al = d["alignment"]
    ch, s = al["characters"], al["character_start_times_seconds"]
    txt = "".join(ch)
    return [s[m.start()] for m in re.finditer(r"\[[^\]]*\]|\S+", txt) if not m.group().startswith("[")]


def process(x):
    """close mic: proximity low shelf, gentle de-ess, light compression, almost no room"""
    x = hp(x, 55)
    x = shelf(x, 160, 4.0, "low")
    x = peq(x, 320, -1.5, 1.0)           # keep the boost from getting boomy
    # de-esser: 5-9 kHz band, gain-reduced where it pokes 6 dB above its smoothed level
    s = bp(x, 5000, 9500, 2)
    env = np.sqrt(np.convolve(s ** 2, np.ones(ns(0.005)) / ns(0.005), "same"))
    ref = np.sqrt(np.convolve(x ** 2, np.ones(ns(0.03)) / ns(0.03), "same"))
    over = np.maximum(0.0, 20 * np.log10((env + 1e-9) / (ref + 1e-9)) + 6.0)
    g = dbg(-np.minimum(over * 0.6, 8.0))
    g = np.convolve(g, np.ones(ns(0.003)) / ns(0.003), "same")
    x = x - s + s * g
    # gentle 2:1 compression above -18 dB (re peak), 5 / 120 ms
    a = np.abs(x) / (np.abs(x).max() + 1e-12)
    lev = np.zeros_like(a)
    ka, kr = 1 - np.exp(-1 / (0.005 * SR)), 1 - np.exp(-1 / (0.12 * SR))
    v = 0.0
    for i in range(len(a)):
        v += (a[i] - v) * (ka if a[i] > v else kr)
        lev[i] = v
    ldb = 20 * np.log10(lev + 1e-9)
    gr = np.where(ldb > -18, (ldb + 18) * 0.5, 0.0)
    return x * dbg(-gr)


def build(NS, irs):
    """-> (stereo narration stem, word list, line table, duck gain curve (NS,))"""
    track = np.zeros(NS)
    words, lines = [], []
    for li in sorted(PLACE):
        d = json.load(open(os.path.join(OD, "vo_raw", f"line{li}.json")))
        text = d["request"]["text"]
        a = decode(base64.b64decode(d["audio_base64"]))
        segs = segments(a)
        grp = groups(text)
        if len(segs) != len(grp):
            raise SystemExit(f"line {li}: {len(segs)} speech segments vs {len(grp)} phrases {segs}")
        al = align_starts(d)
        wi = 0
        for (s0, s1), g, at in zip(segs, grp, PLACE[li]):
            k0, k1 = ns(max(0.0, s0 - PRE)), ns(min(len(a) / SR, s1 + POST))
            ph = fades(a[k0:k1], 0.03, 0.06)
            off = at - (s0 - k0 / SR)            # where sample k0 lands
            i = ns(off)
            track[i:i + len(ph)] += ph[: NS - i]
            first = al[wi]
            on = first if s0 < first < s1 - 0.3 else s0
            wts = [len(re.sub(r"[^A-Za-z']", "", w)) + 1.5 for w in g]
            span = s1 - on
            x = on
            for w, wt in zip(g, wts):
                dur = span * wt / sum(wts)
                words.append({"word": w, "start": round(at + (x - s0), 3), "end": round(at + (x - s0) + dur * 0.94, 3),
                              "line": li})
                x += dur
            wi += len(g)
        lw = [w for w in words if w["line"] == li]
        lines.append({"line": li, "text": text, "start": lw[0]["start"], "end": lw[-1]["end"]})
    track = process(track)
    st_ = pan(track, 0.0) + 0.04 * convolve_st(track, irs["room"])   # almost dry: a hint of space only
    st_ *= dbg(LEVEL - momentary_max(st_))
    # duck curve from the phrase spans
    duck = np.zeros(NS)
    for w in words:
        duck[ns(w["start"] - 0.12): ns(w["end"] + 0.15)] = 1.0
    k = ns(0.25)
    duck = np.convolve(duck, np.ones(k) / k, "same")
    gain = dbg(DUCK_DB * np.clip(duck, 0, 1))
    return st_, words, lines, gain

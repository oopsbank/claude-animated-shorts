#!/usr/bin/env python3
"""Mix for one short: voice + original music bed + synthesized SFX -> mix.wav, stems, cues.md.

    .venv/bin/python audio/build_mix.py audio/<slug> --shots scripts/<slug>/shots.json [--frames N]

Inputs in out_dir: voice.wav + words.json (from tts.py), optional sfx.json (topic cues, see below).
Length: exactly --frames picture frames at 30 fps (1600 samples/frame). Without --frames: last word end + RING s,
rounded up to a whole frame (the engine must then render that many frames; length.json says how many).

sfx.json (optional, hand-placed topic cues):
    [{"cue": "bike_bell", "word": 12, "offset": -0.05, "level": -11, "pan": 0.3, "note": "kid rings the bell"},
     {"cue": "lean", "shot": "s04", "at_word": 2}]
  word = global index into words.json, or shot + at_word (index inside that shot, like shots.json beats).
  cue names: see lib/sfx_x.py GEN. level = LU vs the voice (max momentary), default per cue.
     {"mute": "s17:speed_lines"}      <- silence an automatic fx cue of one shot
Automatic cues from shots.json: an ambience bed per set, a whoosh on each set/cam change, and every fx entry
(camera shakes get no automatic sound: add a cue if the shake is an impact).

Mix: voice high-passed + gently compressed (no EQ colour, no pitch); music ducked -3 dB under words (keyed by
words.json) with per-section levels relative to the voice; SFX events at their LU-vs-voice level; master gain to
-14 LUFS integrated; 4x-oversampled look-ahead limiter, ceiling -1.2 dBTP. 48 kHz / stereo / 24-bit.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from scipy import ndimage, signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
from dsp import (SR, ns, st, dbg, rng, hp, pan, place, read_wav, write_wav, integrated, momentary, short_term, lra,  # noqa
                 true_peak, fades)
import score as SC  # noqa
import sfx_x as X  # noqa

FPS = 30
TARGET_LUFS = -14.0
CEIL_DBTP = -1.2                 # margin for codec overshoot (QA asks <= -1 dBTP)
DUCK_DB = -3.0
FINAL_DIP_DB = -3.0              # extra music dip under the last word of every sentence
RING = 0.8                       # s after the last word when no --frames is given (sting rings out)
BED_LU = -30.0                   # ambience bed, integrated LU vs the voice
MUSIC_LU = {"hook": -8.5, "body": -9.0, "mystery": -10.0, "explain": -9.5, "payoff": -8.5, "sting": -7.0}


# ================================================================ words / structure
def clean(w):
    return re.sub(r"[^\w']", "", w.lower())


def sentences(words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if re.search(r"[.!?][\"'”’)]*$", w["word"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def sections(words, end):
    """hook = sentence 1; mystery = last question (or 'Wait') sentence before 'You see'; explain = 'You see' ->
    payoff; payoff = last sentence; sting = end of the last word. Missing parts are simply skipped."""
    S = sentences(words)
    t = lambda i: words[i]["start"]
    sec = {}
    piv = next((i for i in range(len(words) - 1) if clean(words[i]["word"]) == "you" and clean(words[i + 1]["word"]) == "see"), None)
    pay = S[-1][0] if len(S) > 2 else None
    myst = None
    for s in S[1:]:
        if piv is not None and s[0] >= piv:
            break
        if words[s[-1]]["word"].rstrip("\"'”’)").endswith("?") or clean(words[s[0]]["word"]) == "wait":
            myst = s[0]
    hook_end = S[1][0] if len(S) > 1 else len(words) - 1
    sec["hook"] = (0.0, t(hook_end))
    nxt = [x for x in (myst, piv, pay) if x is not None]
    sec["body"] = (t(hook_end), t(nxt[0]) if nxt else end)
    if myst is not None:
        sec["mystery"] = (t(myst), t(piv) if piv is not None else (t(pay) if pay else end))
    if piv is not None:
        sec["explain"] = (t(piv), t(pay) if pay is not None and pay > piv else words[-1]["start"])
    if pay is not None and (piv is None or pay > piv):
        sec["payoff"] = (t(pay), words[-1]["start"])
    sec["sting"] = words[-1]["end"] - 0.04       # after the punchline word, so it lands dry and is never masked
    return {k: v for k, v in sec.items() if k == "sting" or v[1] - v[0] > 0.2}


def tokens(text):
    out = []
    for w in text.split():
        if out and not re.search(r"\w", w):
            continue
        out.append(w)
    return out


def shot_word_index(shots, words):
    """first global word index of every shot; checks the word count against words.json"""
    first, k = {}, 0
    for s in shots:
        first[s["id"]] = k
        k += len(tokens(s.get("text", "")))
    if k != len(words):
        print(f"WARNING: shots.json has {k} words, words.json {len(words)}: shot word indexes scaled to fit")
        sc = len(words) / max(k, 1)
        first = {i: int(round(v * sc)) for i, v in first.items()}
    return first


# ================================================================ voice
def load_voice(path, n):
    x, sr = read_wav(path)
    assert sr == SR, f"voice must be {SR} Hz, got {sr}"
    v = x.mean(0)
    out = np.zeros(n)
    out[: min(n, len(v))] = v[:n]
    return out


def compress(x, thr_rel=-4.0, ratio=2.0, att=0.005, rel=0.12):
    """gentle feed-forward RMS compressor (threshold relative to the speech level), smooth gain at 1 kHz control"""
    ctrl = 1000
    w = SR // ctrl
    m = len(x) // w
    p = (x[: m * w] ** 2).reshape(m, w).mean(1)
    lev = 10 * np.log10(ndimage.uniform_filter1d(p, 10) + 1e-12)
    speech = np.percentile(lev[lev > lev.max() - 40], 60)
    thr = speech + thr_rel
    over = np.maximum(lev - thr, 0)
    gr = -over * (1 - 1 / ratio)
    ka, kr = 1 - math.exp(-1 / (att * ctrl)), 1 - math.exp(-1 / (rel * ctrl))
    g = np.zeros(m)
    e = 0.0
    for i in range(m):
        e += (gr[i] - e) * (ka if gr[i] < e else kr)
        g[i] = e
    gs = np.interp(np.arange(len(x)) / SR, (np.arange(m) + 0.5) / ctrl, g)
    return x * dbg(gs), float(-g.min())


# ================================================================ automation
def duck_curve(words, n, depth=DUCK_DB, pre=0.08, post=0.12, att=0.07, rel=0.45, merge=0.3):
    ctrl = 1000
    nc = int(n / SR * ctrl) + 2
    va = np.zeros(nc)
    for w in words:
        va[max(0, int((w["start"] - pre) * ctrl)): int((w["end"] + post) * ctrl)] = 1.0
    if merge > 0:
        va = ndimage.maximum_filter1d(va, int(merge * ctrl))
    ka, kr = 1 - np.exp(-1 / (att * ctrl)), 1 - np.exp(-1 / (rel * ctrl))
    env = np.zeros(nc)
    e = 0.0
    for i in range(nc):
        e += (va[i] - e) * (ka if va[i] > e else kr)
        env[i] = e
    return np.interp(np.arange(n) / SR, np.arange(nc) / ctrl, depth * env)


def section_curve(m, v, sec, n, v_int):
    gains, pts = {}, []
    for name, ab in sec.items():
        if name == "sting":
            continue
        a, b = ab
        seg = slice(ns(a), ns(b))
        Lm, Lv = integrated(m[:, seg]), integrated(st(v[seg]))
        if not np.isfinite(Lv):
            Lv = v_int
        gains[name] = (Lv + MUSIC_LU[name] - Lm) if np.isfinite(Lm) else 0.0
        pts.append((a, gains[name]))
    ts = sec["sting"]
    Lm = integrated(m[:, ns(ts): ns(ts + 1.5)])
    gains["sting"] = (v_int + MUSIC_LU["sting"] - Lm) if np.isfinite(Lm) else 0.0
    pts.append((ts - 0.02, gains["sting"]))
    pts.sort()
    # piecewise ramps that start AT each section's first word: a cut takes 0.25 s; a raise takes 1.2 s, so the
    # previous section's ringing tails and reverb are not boosted under the new line's first words
    t = np.arange(n) / SR
    c = np.full(n, pts[0][1])
    for (a, g0), (b, g1) in zip(pts, pts[1:]):
        r = 1.2 if g1 > g0 else 0.25
        u = np.clip((t - b) / r, 0, 1)
        c = np.where(t >= b, g0 + (g1 - g0) * (0.5 - 0.5 * np.cos(np.pi * u)), c)
    return c, gains


# ================================================================ limiter (from templates/audio/mix.py)
def limiter(x, ceil_db=CEIL_DBTP, look=0.003, rel=0.08):
    c = dbg(ceil_db)
    n = x.shape[1]
    up = np.abs(signal.resample_poly(x, 4, 1, axis=-1)).max(0)
    pk = np.pad(up, (0, max(0, 4 * n - len(up))))[: 4 * n].reshape(n, 4).max(1)
    gr = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    La = max(1, ns(look))
    g1 = ndimage.minimum_filter1d(gr, 2 * La + 1, mode="nearest")
    g2 = g1.copy()
    idx = np.flatnonzero(g1 < 1.0)
    if len(idx):
        kr = 1 - np.exp(-1 / (rel * SR))
        gap = ns(rel * 8)
        brk = np.flatnonzero(np.diff(idx) > gap)
        starts = np.concatenate([[idx[0]], idx[brk + 1]])
        ends = np.concatenate([idx[brk], [idx[-1]]])
        for a, b_ in zip(starts, ends):
            e = min(n, b_ + gap)
            seg = g1[a:e]
            out = np.empty(len(seg))
            g = 1.0
            for k in range(len(seg)):
                g = min(seg[k], g + (1 - g) * kr)
                out[k] = g
            g2[a:e] = out
    g3 = np.minimum(ndimage.uniform_filter1d(g2, 2 * La + 1, mode="nearest"), 1.0)
    return x * g3[None, :], g3


# ================================================================ sfx
def sfx_events(words, shots, cues, sec):
    """-> list of dict(t, cue, level, pan, what)"""
    ev = []
    muted = {c["mute"] for c in cues if "mute" in c}          # {"mute": "s17:speed_lines"} silences one shot's fx
    cues = [c for c in cues if "cue" in c]
    wt = lambda i: words[max(0, min(len(words) - 1, i))]["start"]
    if shots:
        first = shot_word_index(shots, words)
        prev = None
        for s in shots:
            i0 = first[s["id"]]
            if prev is not None and (s.get("set"), s.get("cam")) != (prev.get("set"), prev.get("cam")):
                ev.append(dict(t=wt(i0) - 0.06, cue="whoosh", off=-0.2, what=f"transition {prev['id']}->{s['id']} ({s.get('set')}/{s.get('cam')})"))
            for fx in s.get("fx", []):
                name = fx["name"]
                if name in X.SILENT or f"{s['id']}:{name}" in muted:
                    continue
                if name not in X.GEN:
                    print(f"WARNING: no sound for fx '{name}' in {s['id']}")
                    continue
                ev.append(dict(t=wt(i0 + fx.get("at_word", 0)), cue=name, pan=(fx.get("x", 0.5) - 0.5) * 1.2,
                               what=f"fx {name} ({s['id']} word {fx.get('at_word', 0)})"))
            prev = s
    for c in cues:
        if "word" in c:
            i = c["word"]
        elif shots and "shot" in c:
            i = shot_word_index(shots, words)[c["shot"]] + c.get("at_word", 0)
        else:
            i = 0
        ev.append(dict(t=wt(i) + c.get("offset", 0.0), cue=c["cue"], level=c.get("level"), pan=c.get("pan", 0.0),
                       what=c.get("note", c["cue"]) + f" (word {i} '{words[min(i, len(words) - 1)]['word']}')"))
    return sorted(ev, key=lambda e: e["t"])


def render_sfx(ev, words, shots, n, v_int, seed):
    R = rng(seed)
    out = np.zeros((2, n))
    rows = []
    for k, e in enumerate(ev):
        gen, lvl0, desc = X.GEN[e["cue"]]
        x = gen(rng(int(R.integers(1 << 30))))
        xs = pan(x, e.get("pan", 0.0)) if np.ndim(x) == 1 else x
        lvl = e.get("level") if e.get("level") is not None else lvl0
        M = momentary(xs).max()
        g = dbg(v_int + lvl - M)
        t = e["t"] + e.get("off", 0.0)
        if e["cue"] == "riser":
            t -= x.shape[-1] / SR
        place(out, xs, t, g)
        rows.append((t, e["cue"], desc, e["what"], lvl, e.get("pan", 0.0)))
    beds = []
    if shots:
        first = shot_word_index(shots, words)
        # one bed per run of shots on the same set
        runs, cur = [], None
        for s in shots:
            b = X.BEDS.get(s.get("set"), X.amb_outdoor)
            t0 = 0.0 if cur is None else words[first[s["id"]]]["start"] - 0.06
            if cur is None or b is not cur[0]:
                if cur:
                    cur[2] = t0
                cur = [b, t0, n / SR, s.get("set")]
                runs.append(cur)
        for b, a, z, setname in runs:
            d = z - a + 0.3
            x = b(d, rng(int(R.integers(1 << 30))))
            x = fades(x, 0.3 if a > 0 else 0.0, 0.3)
            L = integrated(x)
            place(out, x, a, dbg(v_int + BED_LU - L))
            beds.append((a, z, setname, b.__name__))
    return out, rows, beds


# ================================================================ report
def lufs(x):
    v = integrated(x)
    return float(v) if np.isfinite(v) else -99.0


def ffmpeg_ebur(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    i = r.stderr.rfind("Summary:")
    return r.stderr[i:].strip() if i >= 0 else r.stderr[-800:]


def section_rows(v, m, s, words, sec):
    Mv, Mb = momentary(v), momentary(m + s)
    tc = np.arange(len(Mv)) * 0.01 + 0.2
    speak = np.zeros(len(tc), bool)
    for w in words:
        speak |= (tc >= w["start"] + 0.03) & (tc <= w["end"] - 0.03)
    speak &= Mv > lufs(v) - 10
    rows = []
    items = [(k, *sec[k]) for k in ("hook", "body", "mystery", "explain", "payoff") if k in sec]
    items.append(("sting+tail", sec["sting"], v.shape[1] / SR))
    for name, a, b in items:
        seg = slice(ns(a), ns(b))
        k = speak & (tc >= a) & (tc < b) & (Mb > -70)
        med = float(np.median(Mv[k] - Mb[k])) if k.sum() > 5 else float("nan")
        p10 = float(np.percentile(Mv[k] - Mb[k], 10)) if k.sum() > 5 else float("nan")
        Lv, Lm, Ls, Lb = lufs(v[:, seg]), lufs(m[:, seg]), lufs(s[:, seg]), lufs(m[:, seg] + s[:, seg])
        rows.append((name, a, b, Lv, Lm, Ls, Lb, Lv - Lb, med, p10))
    return rows


def pacing(words):
    gaps = [words[i + 1]["start"] - words[i]["end"] for i in range(len(words) - 1)]
    span = words[-1]["end"] - words[0]["start"]
    big = [g for g in gaps if g > 0.25]
    return len(words), span, len(words) / span, len(big), sum(big), max(gaps) if gaps else 0.0


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--shots")
    ap.add_argument("--frames", type=int)
    ap.add_argument("--sfx", help="topic cue list (default out_dir/sfx.json if present)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--title", default=None)
    a = ap.parse_args()
    od = a.out_dir
    words = json.load(open(os.path.join(od, "words.json")))
    shots_doc = json.load(open(a.shots)) if a.shots else {}
    shots = shots_doc.get("shots", [])
    cues_path = a.sfx or os.path.join(od, "sfx.json")
    cues = json.load(open(cues_path)) if os.path.exists(cues_path) else []
    title = a.title or shots_doc.get("title") or os.path.basename(os.path.abspath(od))

    frames = a.frames or int(math.ceil((words[-1]["end"] + RING) * FPS - 1e-9))
    n = frames * SR // FPS
    dur = n / SR
    if words[-1]["end"] > dur:
        raise SystemExit(f"picture ({frames} frames = {dur:.3f} s) is shorter than the voice ({words[-1]['end']:.3f} s)")
    print(f"length: {frames} frames = {dur:.3f} s = {n} samples")

    # voice
    v = load_voice(os.path.join(od, "voice.wav"), n)
    v = hp(v, 70, 2)
    v, comp_gr = compress(v)
    v_st = st(v)
    v_int = lufs(v_st)

    # music
    sec = sections(words, dur)
    m, mrows = SC.build(sec, n, seed=a.seed)
    duck = duck_curve(words, n)
    # sentence-final words trail off quietly: an extra dip under each one keeps them on top
    finals = [words[s_[-1]] for s_ in sentences(words)]
    duck += duck_curve(finals, n, depth=FINAL_DIP_DB, pre=0.05, post=0.1, merge=0.0)
    m_d = m * dbg(duck)[None, :]
    curve, mgains = section_curve(m_d, v, sec, n, v_int)
    m = m_d * dbg(curve)[None, :]
    m = fades(m, 0.0, 0.25)

    # sfx
    ev = sfx_events(words, shots, cues, sec)
    s, srows, beds = render_sfx(ev, words, shots, n, v_int, a.seed + 1)
    s = fades(s, 0.0, 0.25)

    # master: gain to target, limit, correct
    pre = v_st + m + s
    G = TARGET_LUFS - lufs(pre)
    for _ in range(3):
        y, gcurve = limiter(pre * dbg(G))
        err = TARGET_LUFS - lufs(y)
        if abs(err) < 0.05:
            break
        G += err
    y = fades(y, 0.0, 0.02)
    write_wav(os.path.join(od, "mix.wav"), y)
    for name, x in (("voice", v_st), ("music", m), ("sfx", s)):
        write_wav(os.path.join(od, f"stem_{name}.wav"), x * dbg(G))
    json.dump({"frames": frames, "fps": FPS, "seconds": dur, "samples": n, "sample_rate": SR},
              open(os.path.join(od, "length.json"), "w"), indent=1)

    # report
    gr_db = -20 * np.log10(gcurve.min())
    I_ = lufs(y)
    TP = true_peak(y)
    LRA = lra(y)
    vs, ms, ss = (x * dbg(G) for x in (v_st, m, s))
    rows = section_rows(vs, ms, ss, words, sec)
    eb = ffmpeg_ebur(os.path.join(od, "mix.wav"))
    pw = pacing(words)
    L = []
    L.append(f"# {title}: soundtrack cue sheet\n")
    L.append("All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, "
             "template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), "
             f"high-passed at 70 Hz and gently compressed (2:1, max {comp_gr:.1f} dB), no EQ colour or pitch change.\n")
    L.append("## Files\n| file | content |\n|---|---|")
    L.append(f"| `mix.wav` | final mix, 48 kHz stereo 24-bit, {n} samples = {frames} frames @ 30 fps = {dur:.3f} s |")
    L.append("| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |")
    L.append("| `length.json` | the picture length the engine must render |\n")
    L.append("## Master loudness (own BS.1770-4 meter)")
    L.append(f"- Integrated **{I_:.1f} LUFS** (target {TARGET_LUFS}), true peak **{TP:.1f} dBTP** (ceiling {CEIL_DBTP}), LRA {LRA:.1f} LU")
    L.append(f"- Stems at mix gain: voice {lufs(vs):.1f}, music {lufs(ms):.1f}, sfx {lufs(ss):.1f} LUFS; master gain {G:+.2f} dB")
    L.append(f"- Limiter: max gain reduction {gr_db:.2f} dB, active (>0.1 dB) on {100 * np.mean(gcurve < dbg(-0.1)):.2f} % of samples\n")
    L.append("ffmpeg ebur128 cross-check:\n```\n" + eb + "\n```\n")
    L.append("## Voice pacing (words.json)")
    L.append(f"- {pw[0]} words over {pw[1]:.2f} s = **{pw[2]:.2f} words/s** (reference 3.5-4.1, median 3.7)")
    L.append(f"- gaps > 0.25 s: {pw[3]}, total {pw[4]:.2f} s (reference < 1 s); longest gap {pw[5]:.2f} s")
    L.append(f"- first word at {words[0]['start']:.3f} s (frame {words[0]['start'] * FPS:.1f}); last word ends {words[-1]['end']:.3f} s\n")
    L.append("## Voice on top, per section (LUFS at mix gain)")
    L.append("bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.\n")
    L.append("| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |\n|---|---|---|---|---|---|---|---|---|")
    for r_ in rows:
        L.append(f"| {r_[0]} | {r_[1]:.2f}-{r_[2]:.2f} | {r_[3]:.1f} | {r_[4]:.1f} | {r_[5]:.1f} | {r_[6]:.1f} | {r_[7]:.1f} | {r_[8]:.1f} | {r_[9]:.1f} |")
    L.append("\n## Music map (original, G major, 112 bpm)")
    L.append(f"Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): "
             + ", ".join(f"{k} {v_}" for k, v_ in MUSIC_LU.items() if k in mgains) + ". Applied section gains (dB): "
             + ", ".join(f"{k} {v_:+.1f}" for k, v_ in mgains.items()) + ".\n")
    L.append("| time s | frame | music |\n|---|---|---|")
    for t, what in sorted(mrows):
        L.append(f"| {t:.2f} | {t * FPS:.0f} | {what} |")
    L.append("\n## SFX events\nlevel = target LU vs the voice stem (max momentary of the event). Beds are integrated.\n")
    L.append("| # | time s | frame | cue | sound | why | level LU | pan |\n|---|---|---|---|---|---|---|---|")
    for i, (t, cue, desc, what, lvl, p) in enumerate(srows, 1):
        L.append(f"| {i} | {t:.3f} | {t * FPS:.1f} | {cue} | {desc} | {what} | {lvl} | {p:+.2f} |")
    for a_, z, setname, bn in beds:
        L.append(f"| bed | {a_:.3f}-{z:.3f} | {a_ * FPS:.1f} | {bn} | ambience for set '{setname}' | shots on that set | {BED_LU} (int.) | 0 |")
    open(os.path.join(od, "cues.md"), "w").write("\n".join(L) + "\n")
    print(f"I {I_:.2f} LUFS  TP {TP:.2f} dBTP  LRA {LRA:.1f}  limiter max GR {gr_db:.2f} dB  voice comp {comp_gr:.1f} dB")
    for r_ in rows:
        print(f"  {r_[0]:<11} margin {r_[7]:5.1f}  speech median {r_[8]:5.1f}  p10 {r_[9]:5.1f}")
    print(f"pacing: {pw[2]:.2f} w/s, gaps>0.25: {pw[3]} = {pw[4]:.2f} s")


if __name__ == "__main__":
    main()

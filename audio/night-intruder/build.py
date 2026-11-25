#!/usr/bin/env python3
"""night-intruder soundtrack: sfx.json cues (audio/lib/sfx_night.py) + THIEF 2's Kokoro line -> mix.wav, stems,
voice.wav, words.json, length.json, cues.md, qa_mix.png.

    .venv/bin/python audio/night-intruder/build.py

Needs voice_raw24k.wav + words_raw.json from voice_kokoro.py (run once with a kokoro-onnx venv). No music bed, no
narrator. Exactly 2400 frames @ 30 fps = 80.000 s. Master: gain to -14 LUFS integrated with the 4x-oversampled
look-ahead limiter from build_mix.py (ceiling -1.2 dBTP), then the hard silences are re-zeroed.
"""
import inspect
import json
import os
import subprocess
import sys

import numpy as np

OD = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(OD)
sys.path.insert(0, os.path.join(AUDIO, "lib"))
sys.path.insert(0, AUDIO)
from dsp import (SR, ns, dbg, rng, lp, hp, shelf, pan, place, fades, make_ir, convolve_st, integrated, momentary,  # noqa
                 momentary_max, lra, true_peak, read_wav, write_wav, st)
import sfx_night as N  # noqa
from build_mix import limiter, ffmpeg_ebur, TARGET_LUFS, CEIL_DBTP  # noqa

FPS, FRAMES = 30, 2400
DUR = FRAMES / FPS
NS = ns(DUR)
VOICE_AT = 56.65          # "You" starts here; the line ends ~59.10, the slam is at 60.00
VOICE_LEVEL = -15.0       # max momentary LUFS before the master gain
VOICE_WAV_AT = 56.40     # voice.wav starts here on the picture (words.json times are absolute)
SEED = 1313
EVENT_GR = 5.0          # dB of master limiting allowed on any one event; above that the event is limited alone

SHOTS = [(1, 0, 4), (2, 4, 8), (3, 8, 13), (4, 13, 22), (5, 22, 27), (6, 27, 32), (7, 32, 35), (8, 35, 38),
         (9, 38, 42), (10, 42, 47), (11, 47, 55), (12, 55, 62), (13, 62, 68), (14, 68, 74), (15, 74, 80)]

IRS = {"house": make_ir(1.25, 7, hf=1.6, pre=0.02, density_lp=5000,
                        early=[(0.011, 0.5, -0.4), (0.019, 0.4, 0.5), (0.031, 0.3, -0.2)]),
       "room": make_ir(0.6, 11, hf=1.2, pre=0.006, early=[(0.005, 0.6, 0.3), (0.012, 0.45, -0.4)])}


def lufs(x):
    v = integrated(x)
    return v if np.isfinite(v) else -120.0


def render(c, i):
    r = rng(SEED + 17 * i)
    fn = getattr(N, c["cue"])
    args = dict(c.get("args", {}))
    x = fn(r, **args)
    x = np.asarray(x, float)
    d = c.get("dist", 0.0)
    if d > 0:  # distance: darker and thinner
        x = lp(x, float(np.exp(np.log(14000) * (1 - d) + np.log(1100) * d)), 2)
        x = hp(x, 60 + 120 * d)
    if x.ndim == 1:
        x = pan(x, c.get("pan", 0.0))
    v = c.get("verb", "none")
    if v != "none":
        tail = np.zeros((2, ns(1.6 if v == "house" else 0.8)))
        xp = np.concatenate([x, tail], axis=1)
        x = xp + c.get("wet", 0.3) * convolve_st(xp.mean(0), IRS[v])
    if "gain_pts" in c:
        g = c["gain_pts"]
        tt_ = np.arange(x.shape[1]) / SR
        x = x * dbg(np.interp(tt_, [p[0] for p in g], [p[1] for p in g]))[None, :]
    if "fade" in c:
        x = fades(x, *c["fade"])
    cur = lufs(x) if c.get("bed") else momentary_max(x)
    return x * dbg(c["level"] - cur)


def place_cut(buf, x, t, cuts, through=False):
    """place x at t, hard-cut at the next picture cut (8 ms fade into it)"""
    end = t + x.shape[1] / SR
    if not through:
        for cu in cuts:
            if t < cu < end:
                k = ns(cu - t)
                x = fades(x[:, :k], 0.0, 0.008)
                break
    place(buf, x, t)


def voice_track():
    raw = os.path.join(OD, "voice_raw24k.wav")
    tmp = os.path.join(OD, "_voice48k.wav")
    # 1.5 semitones down (rubberband, formants kept), 48 kHz
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    "aresample=48000,rubberband=pitch=0.917:formant=preserved:transients=smooth", "-ar", "48000",
                    "-ac", "1", tmp], check=True)
    v, sr = read_wav(tmp)
    os.remove(tmp)
    v = v[0]
    v = hp(v, 75)
    v = shelf(v, 160, 2.5, "low")     # a touch more chest
    v = shelf(v, 6000, -3.0, "high")  # colder, less sibilant air
    meta = json.load(open(os.path.join(OD, "words_raw.json")))
    words = [{"word": w["word"], "start": round(VOICE_AT + w["start"], 3), "end": round(VOICE_AT + w["end"], 3)}
             for w in meta["words"]]
    dry = np.zeros(NS)
    k = ns(VOICE_AT - meta["words"][0]["start"])
    dry[k:k + len(v)] += v[: NS - k]
    dry_st = pan(dry, 0.0)
    wet = convolve_st(dry, IRS["house"]) * 0.22 + convolve_st(dry, IRS["room"]) * 0.12
    out = dry_st + wet
    out *= dbg(VOICE_LEVEL - momentary_max(out))
    return out, words, meta


def main():
    spec = json.load(open(os.path.join(OD, "sfx.json")))
    cuts = spec["cuts"]
    events = [(c, render(c, i)) for i, c in enumerate(spec["cues"])]
    rows = [c for c, _ in events]
    v, words, vmeta = voice_track()

    def assemble(G_est):
        """per-event peak cap: no single event asks the master limiter for more than EVENT_GR dB (impacts are
        limited on their own, so nothing else ducks under them)"""
        cap = dbg(CEIL_DBTP + EVENT_GR - G_est)
        out = {k: np.zeros((2, NS)) for k in ("amb", "foley", "body", "voice")}
        for c, x in events:
            if np.abs(x).max() > cap:
                x = limiter(x, ceil_db=20 * np.log10(cap), look=0.002, rel=0.05)[0]
            place_cut(out[c.get("stem", "foley")], x, c["t"], cuts, c.get("through", False))
        out["voice"] += v
        return out

    stems = assemble(0.0)
    G0 = TARGET_LUFS - lufs(sum(stems.values()))
    for _ in range(2):
        stems = assemble(G0)
        G1 = TARGET_LUFS - lufs(sum(stems.values()))
        if abs(G1 - G0) < 0.3:
            break
        G0 = G1

    def shape_master(x):
        x = x.copy()
        a, b = spec["silence"]
        x[:, ns(a):ns(b)] = 0.0
        f0, f1 = spec["end_fade"]
        k0, k1 = ns(f0), ns(f1)
        x[:, k0:k1] *= np.cos(np.linspace(0, np.pi / 2, k1 - k0)) ** 2
        x[:, k1:] = 0.0
        return x

    for k in stems:
        stems[k] = shape_master(stems[k])
    pre = sum(stems.values())
    G = TARGET_LUFS - lufs(pre)
    for _ in range(4):
        y, gcurve = limiter(pre * dbg(G), ceil_db=CEIL_DBTP - 0.25)
        y = shape_master(y)
        err = TARGET_LUFS - lufs(y)
        if abs(err) < 0.05:
            break
        G += err
    write_wav(os.path.join(OD, "mix.wav"), y)
    # stems at mix gain (pre-limiter) as 24-bit FLAC to keep the repo small
    for k, x in stems.items():
        tmp = os.path.join(OD, f"_stem_{k}.wav")
        write_wav(tmp, x * dbg(G))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-c:a", "flac", "-sample_fmt", "s32",
                        os.path.join(OD, f"stem_{k}.flac")], check=True)
        os.remove(tmp)
    write_wav(os.path.join(OD, "voice.wav"), (stems["voice"] * dbg(G))[:, ns(VOICE_WAV_AT):ns(VOICE_WAV_AT + 3.6)])
    json.dump(words, open(os.path.join(OD, "words.json"), "w"), indent=0)
    json.dump({"frames": FRAMES, "fps": FPS, "seconds": DUR, "samples": NS, "sample_rate": SR},
              open(os.path.join(OD, "length.json"), "w"), indent=1)

    # ---------------------------------------------------------------- checks
    I_, TP, LRA = lufs(y), true_peak(y), lra(y)
    gr = -20 * np.log10(gcurve.min())
    a, b = spec["silence"]
    sil = y[:, ns(a):ns(b)]
    sil_ok = bool(np.all(sil == 0.0))
    tail_ok = bool(np.all(y[:, ns(spec["end_fade"][1]):] == 0.0))
    eb = ffmpeg_ebur(os.path.join(OD, "mix.wav"))
    M = momentary(y)
    tm = np.arange(len(M)) * 0.01 + 0.4
    per_shot = []
    for s, t0, t1 in SHOTS:
        sel = (tm > t0) & (tm <= t1)
        seg = y[:, ns(t0):ns(t1)]
        pk = 20 * np.log10(np.abs(seg).max() + 1e-12)
        per_shot.append((s, t0, t1, float(M[sel].max()) if sel.any() else -99, pk))
    print(f"I {I_:.2f} LUFS  TP {TP:.2f} dBTP  LRA {LRA:.1f}  limiter max GR {gr:.2f} dB  master {G:+.2f} dB  "
          f"silence zero {sil_ok}  tail zero {tail_ok}")
    for p in per_shot:
        print("shot %2d %5.1f-%5.1f  Mmax %6.1f  peak %6.1f dBFS" % p)

    # ---------------------------------------------------------------- cues.md
    fm = lambda t: "%d:%05.2f" % (int(t // 60), t % 60)
    L = ["# Night Intruder: soundtrack cue sheet\n",
         "Original short film, no narrator, no music bed (a very low drone under shots 2-5 and 12-15). Every sound is "
         "procedural numpy/scipy synthesis written for this film (`audio/lib/sfx_night.py`, on the template "
         "`dsp.py` / `sfx_gen.py`); no third-party samples or packs were used. THIEF 2's line: Kokoro-82M "
         f"(Apache-2.0, kokoro-onnx v1.0 model files), voice **{vmeta['voice']}** at speed {vmeta['speed']}, pitched "
         "down 1.5 semitones (rubberband, formants preserved), low shelf +2.5 dB, high shelf -3 dB, hallway + room "
         "reverb. Rebuild: `voice_kokoro.py` (once) then `build.py`; the cue list is `sfx.json`.\n",
         "## Files", "| file | content |", "|---|---|",
         f"| `mix.wav` | final mix, 48 kHz stereo 24-bit, {NS} samples = {FRAMES} frames @ {FPS} fps = {DUR:.3f} s |",
         "| `stem_amb.flac` / `stem_foley.flac` / `stem_body.flac` / `stem_voice.flac` | stems at mix gain, pre-limiter "
         "(24-bit FLAC; their sum + the master limiter = the mix) |",
         f"| `voice.wav` | THIEF 2's line with its room, at mix gain (48 kHz stereo); sample 0 = {VOICE_WAV_AT:.2f} s on the picture |",
         "| `words.json` | the line's 7 words with absolute times (for the caption) |",
         "| `length.json` | the picture length: 2400 frames |",
         "| `sfx.json` | the hand-placed cue list (time, generator, level, pan, distance, reverb) |",
         "| `voice_kokoro.py`, `voice_raw24k.wav`, `words_raw.json` | the Kokoro take and its word split |",
         "| `qa_mix.png` | waveform + momentary loudness overview with the shot grid |\n",
         "## Master loudness (own BS.1770-4 meter)",
         f"- Integrated **{I_:.1f} LUFS** (target {TARGET_LUFS}), true peak **{TP:.1f} dBTP** (ceiling {CEIL_DBTP}), "
         f"LRA {LRA:.1f} LU",
         f"- Master gain {G:+.2f} dB; limiter max gain reduction {gr:.2f} dB (only on the transients: clang, thwack, "
         "slam, final impact)",
         f"- **35.000-37.000 s is digital zero: {sil_ok}** (every sample of both channels); "
         f"{spec['end_fade'][1]:.1f}-80.000 s is digital zero: {tail_ok}",
         "\nffmpeg ebur128 cross-check:\n```", eb.strip(), "```\n",
         "## Per shot (max momentary LUFS, sample peak)", "| shot | time | M max | peak dBFS |", "|---|---|---|---|"]
    for s, t0, t1, mm, pk in per_shot:
        L.append(f"| {s} | {fm(t0)}-{fm(t1)} | {mm:.1f} | {pk:.1f} |")
    L += ["\n## Dialogue", "| word | start | end |", "|---|---|---|"]
    L += [f"| {w['word']} | {w['start']:.3f} | {w['end']:.3f} |" for w in words]
    L += ["\n## Cues", "time = start on the picture; level = max momentary LUFS of the event before the master gain "
          f"({G:+.1f} dB) (bed = integrated). Hard cuts at 35.000 (into digital silence) and 76.000 (cut to black).\n",
          "| time | shot | sound | level | stem |", "|---|---|---|---|---|"]
    allc = sorted(rows + [{"t": VOICE_AT, "shot": 12, "note": "THIEF 2 (Kokoro am_onyx): \"You done yet? What's all "
                                                              "the noise?\" (ends ~%.2f)" % words[-1]["end"],
                           "level": VOICE_LEVEL, "stem": "voice", "cue": "voice"}], key=lambda c: c["t"])
    for c in allc:
        L.append(f"| {fm(c['t'])} | {c['shot']} | {c.get('note', c['cue'])} (`{c['cue']}`) | {c['level']}"
                 f"{' bed' if c.get('bed') else ''} | {c.get('stem', 'foley')} |")
    L.append(f"| {fm(a)}-{fm(b)} | 8 | **ABSOLUTE DIGITAL SILENCE** | -inf | all |")
    open(os.path.join(OD, "cues.md"), "w").write("\n".join(L) + "\n")
    qa_sheet(y, stems, G, words, spec)


def qa_sheet(y, stems, G, words, spec):
    from PIL import Image, ImageDraw, ImageFont
    W, ROW = 2400, 150
    fp = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    f = ImageFont.truetype(fp, 18) if os.path.exists(fp) else ImageFont.load_default()
    rows = [("mix", y, (40, 40, 40))] + [(k, stems[k] * dbg(G), c) for k, c in
                                         (("foley", (30, 150, 80)), ("body", (200, 60, 60)), ("amb", (200, 120, 30)),
                                          ("voice", (40, 90, 200)))]
    H = ROW * (len(rows) + 1) + 70
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    X = lambda t: t / DUR * W
    a, b = spec["silence"]
    d.rectangle([X(a), 0, X(b), H - 40], fill=(255, 225, 225))
    d.rectangle([X(76.0), 0, W, H - 40], fill=(232, 232, 240))
    for s, t0, t1 in SHOTS:
        d.line([(X(t0), 0), (X(t0), H - 40)], fill=(170, 170, 210))
        d.text((X(t0) + 3, H - 64), str(s), fill=(60, 60, 150), font=f)
    for k, (lab, x, col) in enumerate(rows):
        m = x.mean(0)
        e = np.linspace(0, len(m), W + 1).astype(int)
        y0 = 10 + k * ROW
        h = ROW - 12
        sc = 1.0 if lab == "mix" else 1.0 / (np.abs(m).max() + 1e-9)
        for i in range(W):
            seg = m[e[i]:e[i + 1]] * sc
            d.line([(i, y0 + h / 2 - seg.max() * h / 2), (i, y0 + h / 2 - seg.min() * h / 2)], fill=col)
        d.text((6, y0 + 2), lab + ("" if lab == "mix" else " (normalised)"), fill=(20, 20, 20), font=f)
    y0 = 10 + len(rows) * ROW
    M = momentary(y)
    tm = np.arange(len(M)) * 0.01 + 0.4
    Ly = lambda v: y0 + (ROW - 12) * (1 - (np.clip(v, -60, -5) + 60) / 55)
    for v in (-10, -20, -30, -40, -50):
        d.line([(0, Ly(v)), (W, Ly(v))], fill=(220, 220, 220))
        d.text((W - 50, Ly(v) - 18), str(v), fill=(140, 140, 140), font=f)
    d.line([(X(t), Ly(v)) for t, v in zip(tm[::4], M[::4])], fill=(40, 40, 40), width=2)
    d.text((6, y0 + 2), "mix momentary LUFS (pink = 35-37 s digital zero, grey = black from 76 s)", fill=(20, 20, 20), font=f)
    for w in words:
        d.rectangle([X(w["start"]), H - 44, X(w["end"]), H - 38], fill=(40, 90, 200))
    for t in range(0, 81):
        d.line([(X(t), H - 36), (X(t), H - 30)], fill=(0, 0, 0))
        if t % 5 == 0:
            d.text((X(t) + 2, H - 28), f"{t}s", fill=(0, 0, 0), font=f)
    img.save(os.path.join(OD, "qa_mix.png"))


if __name__ == "__main__":
    main()

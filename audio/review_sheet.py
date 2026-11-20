#!/usr/bin/env python3
"""Visual listen-check of a mix: stems waveforms, 400 ms momentary loudness voice vs bed, word spans, sections,
and a voice-only zoom with word boundaries. Writes out_dir/qa_mix.png (+ qa_voice_zoom.png).

    .venv/bin/python audio/review_sheet.py audio/<slug>
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
from dsp import SR, read_wav, momentary  # noqa

W, ROW = 2400, 170


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def wave_row(d, x, y0, h, col, dur, label, f):
    m = x.mean(0) if x.ndim == 2 else x
    n = len(m)
    edges = np.linspace(0, n, W + 1).astype(int)
    for i in range(W):
        seg = m[edges[i]:edges[i + 1]]
        if len(seg):
            lo, hi = seg.min(), seg.max()
            d.line([(i, y0 + h / 2 - hi * h / 2), (i, y0 + h / 2 - lo * h / 2)], fill=col)
    d.text((6, y0 + 4), label, fill=(30, 30, 30), font=f)


def main():
    od = sys.argv[1]
    words = json.load(open(os.path.join(od, "words.json")))
    mix, _ = read_wav(os.path.join(od, "mix.wav"))
    v, _ = read_wav(os.path.join(od, "stem_voice.wav"))
    m, _ = read_wav(os.path.join(od, "stem_music.wav"))
    s, _ = read_wav(os.path.join(od, "stem_sfx.wav"))
    dur = mix.shape[1] / SR
    f = font(18)
    H = ROW * 5 + 60
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    X = lambda t: t / dur * W
    for k, (x, c, lab) in enumerate([(mix, (40, 40, 40), "mix"), (v, (40, 90, 200), "voice"),
                                     (m, (200, 120, 30), "music"), (s, (30, 150, 80), "sfx")]):
        wave_row(d, x, 10 + k * ROW, ROW - 10, c, dur, lab, f)
    # loudness row: voice vs bed momentary
    y0 = 10 + 4 * ROW
    Mv, Mb = momentary(v), momentary(m + s)
    tc = np.arange(len(Mv)) * 0.01 + 0.2
    Ly = lambda L: y0 + (ROW - 10) * (1 - (np.clip(L, -50, -5) + 50) / 45)
    for L in (-10, -20, -30, -40):
        d.line([(0, Ly(L)), (W, Ly(L))], fill=(225, 225, 225))
        d.text((W - 60, Ly(L) - 18), f"{L}", fill=(150, 150, 150), font=f)
    for arr, c in ((Mb, (200, 120, 30)), (Mv, (40, 90, 200))):
        pts = [(X(t), Ly(L)) for t, L in zip(tc[::5], arr[::5])]
        d.line(pts, fill=c, width=2)
    d.text((6, y0 + 4), "momentary LUFS: voice (blue) vs bed (orange)", fill=(30, 30, 30), font=f)
    # words and seconds
    for w in words:
        d.rectangle([X(w["start"]), H - 44, max(X(w["end"]), X(w["start"]) + 1), H - 36], fill=(40, 90, 200))
    for t in range(int(dur) + 1):
        d.line([(X(t), H - 34), (X(t), H - 28)], fill=(0, 0, 0))
        if t % 5 == 0:
            d.text((X(t) + 2, H - 26), f"{t}s", fill=(0, 0, 0), font=f)
    img.save(os.path.join(od, "qa_mix.png"))

    # voice zoom: first ~6 s with word boundaries and labels
    zt = min(6.0, dur)
    vz = v.mean(0)[: int(zt * SR)]
    img2 = Image.new("RGB", (W, 360), "white")
    d2 = ImageDraw.Draw(img2)
    Xz = lambda t: t / zt * W
    wave_row(d2, vz / (np.abs(vz).max() + 1e-9), 40, 260, (40, 90, 200), zt, "voice zoom 0-%.0f s" % zt, f)
    for i, w in enumerate(words):
        if w["start"] > zt:
            break
        d2.line([(Xz(w["start"]), 30), (Xz(w["start"]), 310)], fill=(0, 160, 0))
        d2.line([(Xz(w["end"]), 30), (Xz(w["end"]), 310)], fill=(220, 0, 0))
        d2.text((Xz(w["start"]) + 2, 315 + 18 * (i % 2)), w["word"], fill=(0, 0, 0), font=f)
    img2.save(os.path.join(od, "qa_voice_zoom.png"))
    print("wrote qa_mix.png, qa_voice_zoom.png")


if __name__ == "__main__":
    main()

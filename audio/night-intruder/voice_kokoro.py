#!/usr/bin/env python3
"""THIEF 2's one line with Kokoro (local ONNX, CC/Apache model) -> voice_raw24k.wav + words_raw.json.

    <venv with kokoro-onnx + soundfile>/bin/python audio/night-intruder/voice_kokoro.py <models_dir> [voice] [speed]

Models: kokoro-v1.0.onnx + voices-v1.0.bin from github.com/thewh1teagle/kokoro-onnx release model-files-v1.0.
Each sentence is rendered on its own (exact sentence edges), trimmed, joined with a short pause; word times inside a
sentence are split by an energy-valley search around letter-weighted guesses. build.py then pitches it down 1.5
semitones (rubberband, formants kept), adds the hallway room and places it at VOICE_AT.
"""
import json
import os
import re
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

LINE = ["You done yet?", "What's all the noise?"]
OUT = os.path.dirname(os.path.abspath(__file__))
models = sys.argv[1]
voice = sys.argv[2] if len(sys.argv) > 2 else "am_onyx"
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 0.9
k = Kokoro(os.path.join(models, "kokoro-v1.0.onnx"), os.path.join(models, "voices-v1.0.bin"))

parts, words, t = [], [], 0.0
sr = 24000
for si, s in enumerate(LINE):
    a, sr = k.create(s, voice=voice, speed=speed, lang="en-us")
    nz = np.nonzero(np.abs(a) > 0.01)[0]
    a = a[max(0, nz[0] - 240): nz[-1] + 480]
    dur = len(a) / sr
    ws = s.split()
    wts = [len(re.sub(r"[^A-Za-z]", "", w)) + 2 for w in ws]
    # 10 ms RMS envelope for valley snapping
    hop = sr // 100
    env = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    bounds = [0.0]
    acc = 0
    for wt in wts[:-1]:
        acc += wt
        g = dur * acc / sum(wts)
        lo, hi = int((g - 0.08) * 100), int((g + 0.08) * 100)
        lo, hi = max(1, lo), min(len(env) - 1, hi)
        b = (lo + int(np.argmin(env[lo:hi]))) / 100 if hi > lo else g
        bounds.append(b)
    bounds.append(dur)
    for i, w in enumerate(ws):
        words.append({"word": w, "start": round(t + bounds[i] + 0.01, 3), "end": round(t + bounds[i + 1] - 0.02, 3)})
    parts.append(a)
    t += dur
    if si < len(LINE) - 1:
        gap = 0.32
        parts.append(np.zeros(int(gap * sr)))
        t += gap
# hand-checked against the 20 ms energy/HF envelope of the am_onyx 0.9 take (the valley search put "the" too long)
HAND = {("am_onyx", 0.9): {"What's": (1.200, 1.470), "all": (1.480, 1.690), "the": (1.710, 1.810), "noise?": (1.820, 2.440)}}
for w in words:
    if w["word"] in HAND.get((voice, speed), {}):
        w["start"], w["end"] = HAND[(voice, speed)][w["word"]]
y = np.concatenate(parts).astype(np.float32)
sf.write(os.path.join(OUT, "voice_raw24k.wav"), y, sr)
json.dump({"voice": voice, "speed": speed, "words": words}, open(os.path.join(OUT, "words_raw.json"), "w"), indent=1)
print(voice, speed, round(len(y) / sr, 3), "s", [(w["word"], w["start"], w["end"]) for w in words])

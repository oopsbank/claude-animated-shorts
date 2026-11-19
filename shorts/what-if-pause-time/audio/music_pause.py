# Original score for "What If You Could Pause Time, But Only You Got Older?", composed and synthesized here
# (instruments.py). Hook: a ticking music-box figure that warps as he ages | a cheeky pizzicato + vibes tune in C for
# the fun of pausing (it stops dead on every click and hangs on a held chord while time is frozen) | a hush for the
# grey hair | the maths: a slow ticking minor pulse | friends + mum: lonely vibes in A minor | the bus: urgent brass
# and snare, cut to a suspended chord on the click | a heroic little horn for the rescue | the old man: a mysterious
# music box, then a comic low tuba on the moustache | "I saw that." a stab | play: the tune comes back, button ending.
import numpy as np
from dsp import SR, ns, rng, pan, place, dbg, make_ir, convolve_st, integrated, hp, write_wav
import instruments as I

DUR = 1935 / 30
N = ns(DUR)
F = I.m2f
R = rng(4242)
r = lambda: rng(int(R.integers(1 << 30)))
tracks = {}


def add(name, x, t, p=0.0, g=1.0):
    buf = tracks.setdefault(name, np.zeros((2, N)))
    x = np.asarray(x, float)
    place(buf, pan(x, p) if x.ndim == 1 else x, t, g)


T_OLD, T_MON, T_CLICK1, T_SLEEP, T_HOME, T_TEST, T_PAUSE2, T_TOP, T_LATE, T_PAUSE3 = 2.69, 3.56, 5.02, 7.4, 10.14, 17.14, 18.14, 19.54, 20.4, 21.33
T_PERFECT, T_WHILE, T_MORNING, T_GREY, T_MATHS, T_BODY, T_FRIENDS, T_STOP, T_BUS = 23.35, 24.44, 25.41, 27.05, 28.08, 34.87, 35.65, 40.03, 42.14
T_CLICK4, T_RUN, T_ACROSS, T_MOVING, T_DRAWN, T_TEACH, T_SAW, T_UNPAUSE = 44.93, 46.84, 49.04, 50.49, 53.83, 55.95, 60.39, 62.4
Q = 0.25  # 16th at 120 bpm (beat 0.5 s)

# A) hook: a music-box figure; on "older" it bends down and slows
fig = [72, 76, 79, 84, 79, 76]
for k, t in enumerate(np.arange(0.15, 3.4, 0.25)):
    bend = 0 if t < T_OLD else -int((t - T_OLD) * 6)
    add("box", I.musicbox(F(fig[k % 6] + bend), 0.5, r(), dur=0.6), t, 0.2 * (k % 2 * 2 - 1))
add("pad", I.pad([F(60), F(64), F(67)], T_OLD - 0.1, 0.35, r(), att=0.8, rel=0.1, warm=1200), 0.1)
add("pad", I.pad([F(55), F(58), F(61)], 0.9, 0.4, r(), att=0.05, rel=0.4, warm=800), T_OLD)
add("tuba", I.brass(F(36), 0.8, 0.6, r(), "tuba", fall=-3), T_OLD + 0.05)


# B) the fun: a cheeky tune (pizz + vibes + tuba on the beat); hangs on a held chord while frozen
MEL = [(0, 1, 72), (1, 1, 74), (2, 2, 76), (4, 1, 79), (5, 1, 76), (6, 2, 72), (8, 1, 74), (9, 1, 76), (10, 1, 77), (11, 1, 76), (12, 4, 74)]
CH = [(48, [64, 67, 72]), (43, [62, 67, 71]), (45, [64, 69, 72]), (41, [65, 69, 72])]


def tune(t0, t1, transpose=0, mel=True):
    beats = int((t1 - t0) / (2 * Q))
    for k in range(beats):
        t = t0 + k * 2 * Q
        bass, ch = CH[(k // 4) % 4]
        if k % 2 == 0: add("tuba", I.brass(F(bass + transpose), 0.22, 0.45, r(), "tuba"), t, -0.1)
        for j, m in enumerate(ch): add("pluck", I.pluck(F(m + transpose), 0.35, r(), dur=0.3, bright=0.7), t + Q + 0.005 * j, 0.25 - 0.15 * j)
    if mel:
        for (b, d, m) in MEL:
            tb = t0 + b * 2 * Q
            if tb < t1 - 0.1: add("vibes", I.vibes(F(m + transpose), 0.55, r(), dur=d * 2 * Q * 1.6), tb, 0.15)


def held(t0, dur, root=60):
    add("pad", I.pad([F(root), F(root + 7), F(root + 11), F(root + 14)], dur, 0.35, r(), att=0.15, rel=0.3, warm=1600, trem=None), t0)
    add("glock", I.glock(F(root + 24), 0.5, r()), t0 + 0.05)


add("vibes", I.vibes(F(79), 0.5, r(), dur=1.0), T_MON, 0.1)
tune(3.6, T_CLICK1 - 0.05, mel=False)
held(T_CLICK1 + 0.05, T_SLEEP - T_CLICK1 - 0.2, 60)
tune(T_SLEEP + 0.4, T_TEST - 0.1)
add("stab", I.brass(F(55), 0.4, 0.6, r(), "stab", fall=-2), T_TEST)
held(T_PAUSE2 + 0.05, T_TOP - T_PAUSE2 - 0.1, 62)
for m in [60, 64, 67, 72]: add("stab", I.brass(F(m), 0.35, 0.7, r(), "stab"), T_TOP)
tune(T_LATE, T_PAUSE3 - 0.05, 2, mel=False)
for t in np.arange(T_LATE, T_PAUSE3 - 0.1, 0.125): add("snare", I.snare(0.25, r(), dur=0.08), t)
held(T_PAUSE3 + 0.05, 1.4, 60)
tune(22.8, T_MORNING - 0.1)
add("vibes", I.vibes(F(84), 0.5, r(), dur=1.4), T_WHILE + 0.4, 0.2)

# C) the mirror: hush, then a stark note on the grey hair
add("pad", I.pad([F(57), F(60), F(64)], T_GREY - T_MORNING, 0.25, r(), att=0.6, rel=0.3, warm=700), T_MORNING)
add("glock", I.glock(F(81), 0.6, r()), T_GREY)
add("pad", I.pad([F(56), F(59), F(62), F(65)], T_MATHS - T_GREY + 0.4, 0.35, r(), att=0.05, rel=0.5, warm=900), T_GREY)

# D) the maths: a slow ticking minor pulse building to "twenty-six"
for k, t in enumerate(np.arange(T_MATHS, T_BODY, 0.5)):
    add("pluck", I.pluck(F([57, 64, 60, 64][k % 4]), 0.35 + 0.01 * k, r(), dur=0.4, bright=0.4), t, 0.2 if k % 2 else -0.2)
    if k % 4 == 0: add("timp", I.timpani(F(45), 0.3 + 0.02 * k, r(), dur=1.0), t)
add("pad", I.pad([F(45), F(52), F(57), F(60)], T_BODY - T_MATHS, 0.4, r(), att=3.0, rel=0.2, warm=900), T_MATHS)
for m in [41, 48, 53, 56]: add("stab", I.brass(F(m), 0.6, 0.6, r(), "stab", fall=-4), T_BODY)

# E) friends, mum, stop: lonely vibes in A minor
for k, (b, m) in enumerate([(0, 69), (1, 72), (2, 76), (3, 74), (4.5, 72), (5, 71), (6, 69), (8, 64), (9, 67), (10, 69), (11, 67), (12.5, 64)]):
    add("vibes", I.vibes(F(m), 0.4, r(), dur=1.6), 35.8 + b * 0.5, 0.2 * (k % 2 * 2 - 1))
add("pad", I.pad([F(45), F(52), F(57), F(60)], 4.2, 0.3, r(), att=0.8, rel=0.8, warm=700), 35.6)
add("pad", I.pad([F(41), F(48), F(53), F(57)], 2.4, 0.3, r(), att=0.5, rel=0.6, warm=700), 39.7)
add("tuba", I.brass(F(45), 1.0, 0.4, r(), "tuba"), T_STOP + 1.0)

# F) the bus: urgent brass pulses + snare, cut by the click to a suspended chord
for k, t in enumerate(np.arange(T_BUS, T_CLICK4 - 0.05, 0.25)):
    m = [38, 38, 41, 38, 43, 38, 44, 38][k % 8]
    add("tuba", I.brass(F(m), 0.16, 0.5 + 0.03 * k, r(), "tuba"), t)
    if k % 4 == 0: add("timp", I.timpani(F(38), 0.5 + 0.03 * k, r(), dur=0.8), t)
for t, v in I.snare_roll(T_BUS + 1.2, T_CLICK4 - 0.03, 0.15, 0.6, r()):
    add("snare", I.snare(v, r(), dur=0.1, buzz=True), t)
for m in [50, 57, 62]: add("horn", I.brass(F(m), 0.3, 0.6, r(), "horn"), 43.47)
add("pad", I.pad([F(50), F(57), F(60), F(64)], T_RUN - T_CLICK4, 0.4, r(), att=0.05, rel=0.3, warm=1500), T_CLICK4 + 0.05)
add("glock", I.glock(F(86), 0.5, r()), T_CLICK4 + 0.06)

# G) the rescue: a heroic little horn line
for k, (b, d, m) in enumerate([(0, 0.5, 62), (0.5, 0.25, 67), (0.75, 0.25, 69), (1.0, 1.0, 71), (2.0, 0.5, 69), (2.5, 1.5, 74)]):
    add("horn", I.brass(F(m), d * 0.5 * 1.6, 0.6, r(), "horn"), T_RUN + b * 0.5)
for t in np.arange(T_RUN, T_ACROSS - 0.2, 0.5): add("timp", I.timpani(F(43), 0.35, r(), dur=0.6), t)
add("pad", I.pad([F(55), F(62), F(67), F(71)], 1.8, 0.35, r(), att=0.3, rel=0.5, warm=1200), 47.4)

# H) someone else is moving: a mysterious music box over a low drone
for k, t in enumerate(np.arange(T_ACROSS, T_DRAWN, 0.375)):
    add("box", I.musicbox(F([69, 72, 76, 75, 72, 69, 68, 72][k % 8]), 0.4, r(), dur=0.9), t, 0.3 * (k % 2 * 2 - 1))
add("pad", I.pad([F(45), F(52), F(56)], T_DRAWN - T_ACROSS, 0.35, r(), att=1.5, rel=0.3, warm=600), T_ACROSS)
# the moustache: a comic tuba
for k, m in enumerate([41, 45, 48, 40]):
    add("tuba", I.brass(F(m), 0.25 if k < 3 else 0.9, 0.7, r(), "tuba", fall=-1.5 if k == 3 else 0), T_DRAWN + 0.15 + k * 0.26)
add("pad", I.pad([F(48), F(52), F(55), F(58)], T_SAW - 55.0, 0.3, r(), att=0.6, rel=0.3, warm=800), 55.0)
add("glock", I.glock(F(84), 0.5, r()), T_TEACH + 0.1)
# "I saw that." a stab, then a held breath
for m in [43, 50, 55, 58]: add("stab", I.brass(F(m), 0.45, 0.8, r(), "stab", fall=-3), T_SAW + 0.55)
add("pad", I.pad([F(43), F(50), F(58)], T_UNPAUSE - T_SAW - 0.6, 0.3, r(), att=0.3, rel=0.2, warm=700), T_SAW + 0.9)
# I) play: the tune comes back and buttons
tune(T_UNPAUSE + 0.05, 64.3, 0)
for m in [48, 60, 64, 67, 72]: add("stab", I.brass(F(m), 0.5, 0.8, r(), "stab"), 64.3 - 0.02)
add("cym", I.cymbal(0.5, r()), 64.3)

TARGET = {"vibes": -2.0, "pluck": -4.0, "tuba": -3.0, "glock": -6.0, "stab": -1.5, "timp": -4.0, "cym": -10.0, "pad": -5.0,
          "snare": -7.0, "horn": -4.0, "box": -3.0}
mix = np.zeros((2, N)); wet = np.zeros(N)
for k, x in tracks.items():
    g = dbg(-20 + TARGET.get(k, -6) - integrated(x))
    mix += x * g; wet += (x * g).mean(0) * 0.18
mix = hp(mix + 0.7 * convolve_st(wet, make_ir(1.3, 7, pre=0.016, hf=1.4)), 30, 2)
write_wav("music.wav", mix, 24)
print("music.wav", mix.shape[1] / SR, "s, LUFS", round(integrated(mix), 1))

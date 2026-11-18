# Original score for "The Street That Drowned in Beer", composed and synthesized here (instruments.py): a jaunty
# Regency-London tune in D major (fife + plucked strings + tuba oompah, 120 bpm) that follows the picture:
# hook stab | brewery tune | tension cluster | crash hits under the flood | a hushed D minor pad for the cellars |
# curious pizzicato for the explanation (cut dead on "pop") | pompous court fanfare + oompah | sad brass slide on
# "Unluckily" | the tune again, cut dead when the hoop falls | a frantic scramble to the end. Writes music.wav.
import numpy as np
from dsp import SR, ns, rng, pan, place, fades, dbg, make_ir, convolve_st, integrated, hp, write_wav
import instruments as I

DUR = 1948 / 30
N = ns(DUR)
Q = 0.5
F = I.m2f
R = rng(1814)
r = lambda: rng(int(R.integers(1 << 30)))
tracks = {}


def add(name, x, t, p=0.0, g=1.0):
    buf = tracks.setdefault(name, np.zeros((2, N)))
    x = np.asarray(x, float)
    place(buf, pan(x, p) if x.ndim == 1 else x, t, g)


# theme: (beat, length in beats, midi) over 4 bars of 4 beats
THEME = [(0, 1, 74), (1, 1, 78), (2, 1, 81), (3, 1, 78), (4, 1, 79), (5, 1, 76), (6, 1, 73), (7, 1, 69),
         (8, 1, 74), (9, 1, 78), (10, 1, 81), (11, 1, 86), (12, 1, 85), (13, 0.5, 81), (13.5, 0.5, 76), (14, 2, 74)]
THEME2 = [(0, 0.5, 81), (0.5, 0.5, 79), (1, 1, 78), (2, 1, 76), (3, 1, 74), (4, 1, 76), (5, 1, 78), (6, 1, 79), (7, 1, 76),
          (8, 0.5, 78), (8.5, 0.5, 79), (9, 1, 81), (10, 1, 83), (11, 1, 85), (12, 1, 86), (13, 1, 81), (14, 2, 74)]
CHORDS = ["D", "D", "A", "A", "D", "D", "A", "D"]  # per 2 beats
CH = {"D": (38, [62, 66, 69]), "A": (45, [61, 64, 69]), "G": (43, [62, 67, 71]), "Dm": (38, [62, 65, 69]), "A7": (45, [61, 64, 67])}


def tune(t0, theme=THEME, fife=True, glock=False, vel=0.7, bars=4):
    for (b, d, m) in theme:
        if b >= bars * 4:
            continue
        t = t0 + b * Q
        if fife:
            add("fife", I.fife(F(m), d * Q * 0.9, vel, r()), t, 0.15)
        if glock:
            add("glock", I.glock(F(m + 12), vel * 0.6, r()), t, -0.2)
    for k in range(bars * 2):
        bass, ch = CH[CHORDS[k % 8]]
        t = t0 + k * 2 * Q
        add("tuba", I.brass(F(bass), 0.3, 0.6, r(), "tuba"), t, -0.1)
        for j, m in enumerate(ch):
            add("pluck", I.pluck(F(m), 0.45, r(), dur=0.5), t + Q + 0.006 * j, 0.25 - 0.15 * j)


# A) hook: timpani rolls up into a brass stab on "beer"
for k, t in enumerate(np.arange(0.4, 3.2, 0.09)):
    add("timp", I.timpani(F(38), 0.15 + 0.6 * k / 31, r(), dur=0.6), t)
for m in [38, 50, 57, 62, 66]:
    add("stab", I.brass(F(m), 0.7, 0.9, r(), "stab", fall=-4), 3.25)
add("cym", I.cymbal(0.7, r()), 3.25)
# B) the brewery tune, 8 bars from the flash
tune(4.4, THEME, glock=False, vel=0.65)
tune(4.4 + 16 * Q, THEME2, glock=True, vel=0.7)
# C) "An hour later": a creeping tension cluster, cut by the burst
add("pad", I.pad([F(57), F(58), F(63), F(64)], 0.95, 0.5, r(), att=0.8, rel=0.02, warm=1200), 20.78)
# D) the flood: brass blasts falling on each burst and the wall, a snare roll under the wave
for tb in [21.7, 22.74, 24.8, 26.06]:
    for m in [33, 45, 52]:
        add("stab", I.brass(F(m), 0.6, 0.8, r(), "stab", fall=-5), tb)
for t, v in I.snare_roll(26.3, 31.9, 0.15, 0.5, r()):
    add("snare", I.snare(v, r(), dur=0.14, buzz=True), t)
add("cym", I.cymbal(0.5, r()), 31.95)
# E) the cellars: a hushed D minor pad, nothing else
add("pad", I.pad([F(50), F(57), F(62), F(65)], 4.0, 0.35, r(), att=1.2, rel=1.4, warm=700), 33.1)
# F) explanation: curious pizzicato, a glock ding on each growth of the arrows; dead stop on "pop"
for k, t in enumerate(np.arange(37.2, 46.7, Q)):
    m = [62, 69, 66, 69, 64, 69, 67, 69][k % 8] + (0 if t < 42 else 2 if t < 44.3 else 4)
    add("pluck", I.pluck(F(m), 0.4 + 0.25 * (t > 44.3), r(), dur=0.35, bright=0.7), t, 0.2 if k % 2 else -0.2)
    if k % 2 == 0:
        add("tuba", I.brass(F(38 + (0 if t < 42 else 2 if t < 44.3 else 4)), 0.22, 0.45, r(), "tuba"), t)
for t in [39.27, 40.25, 41.03]:
    add("glock", I.glock(F(86), 0.7, r()), t)
add("glock", I.glock(F(93), 0.8, r()), 46.74)
# G) court: fanfare on the gavel, then a pompous oompah through the refund
for t in [48.68, 49.62]:
    for m in [50, 57, 62, 66]:
        add("stab", I.brass(F(m), 0.35, 0.7, r(), "horn"), t)
for k, t in enumerate(np.arange(50.35, 53.9, Q)):
    bass, ch = CH["D" if (k // 2) % 2 == 0 else "A"]
    if k % 2 == 0:
        add("tuba", I.brass(F(bass), 0.28, 0.65, r(), "tuba"), t)
    else:
        for j, m in enumerate(ch):
            add("horn", I.brass(F(m), 0.16, 0.4, r(), "horn", scoop=-12), t + 0.004 * j, 0.3 - 0.15 * j)
for k, m in enumerate([74, 78, 81, 86]):
    add("glock", I.glock(F(m), 0.5, r()), 51.98 + k * 0.12)
# H) "Unluckily": a sad brass slide down; coins sparkle on "seven thousand pounds"
for k, m in enumerate([57, 56, 55, 52]):
    add("horn", I.brass(F(m), 0.45 if k < 3 else 1.1, 0.6, r(), "soft", fall=-1.0 if k == 3 else 0), 54.25 + k * 0.5, -0.1)
for k in range(8):
    add("glock", I.glock(F([86, 90, 93, 98][k % 4]), 0.35, r()), 55.98 + k * 0.07, 0.4 * (k % 2 * 2 - 1))
# I) the lesson: the tune again (two bars), cut dead when the hoop falls
tune(57.6, THEME, vel=0.6, bars=2)
add("fife", I.fife(F(74), 0.25, 0.6, r()), 61.0)
# J) not fine: a frantic scramble to the end
for k, t in enumerate(np.arange(62.3, 64.2, Q / 2)):
    m = [74, 76, 78, 79, 81, 79, 78, 76][k % 8] + (12 if k >= 8 else 0)
    add("fife", I.fife(F(m), Q / 2 * 0.8, 0.75, r()), t, 0.15)
    if k % 2 == 0:
        add("tuba", I.brass(F([38, 45][(k // 2) % 2]), 0.2, 0.7, r(), "tuba"), t)
for t, v in I.snare_roll(62.3, 64.2, 0.3, 0.7, r()):
    add("snare", I.snare(v, r(), dur=0.12), t)
for m in [38, 50, 57, 62, 66, 74]:
    add("stab", I.brass(F(m), 0.4, 0.95, r(), "stab"), 64.25)
add("cym", I.cymbal(0.6, r()), 64.25)

# balance and room
TARGET = {"fife": 0.0, "pluck": -4.0, "tuba": -3.0, "glock": -6.0, "stab": -1.5, "timp": -4.0, "cym": -10.0, "pad": -5.0,
          "snare": -7.0, "horn": -4.0}
mix = np.zeros((2, N)); wet = np.zeros(N)
for k, x in tracks.items():
    g = dbg(-20 + TARGET.get(k, -6) - integrated(x))
    mix += x * g; wet += (x * g).mean(0) * 0.18
mix = hp(mix + 0.7 * convolve_st(wet, make_ir(1.3, 7, pre=0.016, hf=1.4)), 30, 2)
write_wav("music.wav", mix, 24)
print("music.wav", mix.shape[1] / SR, "s, LUFS", round(integrated(mix), 1))

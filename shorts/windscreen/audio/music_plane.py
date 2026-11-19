# Original score for "What If Your Plane's Windscreen Blew Out?", composed and synthesized here (instruments.py).
# hook: rising tension + stab | a breezy holiday tune (vibes + pluck, F major) | tension cluster | the blow-out stab,
# then urgent pulses + snare under the gale | a hushed pad for "they think he's dead" | brass build to the landing hit |
# warm vibes for "Alive" + a little horn for "back to flying" | curious pizzicato for the investigation (dings on the
# bolts, a sad tuba "wrong") | a slow crescendo under the cutaway, cut dead when the bolts go | a lone low note. Writes music.wav.
import numpy as np
from dsp import SR, ns, rng, pan, place, fades, dbg, make_ir, convolve_st, integrated, hp, write_wav
import instruments as I

DUR = 1990 / 30
N = ns(DUR)
F = I.m2f
R = rng(5390)
r = lambda: rng(int(R.integers(1 << 30)))
tracks = {}


def add(name, x, t, p=0.0, g=1.0):
    buf = tracks.setdefault(name, np.zeros((2, N)))
    x = np.asarray(x, float)
    place(buf, pan(x, p) if x.ndim == 1 else x, t, g)


T_HOOK, T_BLOW, T_DEAD, T_TD, T_ALIVE, T_THUMB = 2.33, 11.66, 25.95, 30.6, 34.55, 37.6
T_RED, T_SHORT, T_MATCH, T_WRONG, T_PUSH, T_FAIL = 43.15, 46.1, 48.75, 50.45, 55.65, 62.55

# A) hook: a rising cluster into a stab on "left?"
add("pad", I.pad([F(57), F(58), F(64)], 2.3, 0.6, r(), att=1.6, rel=0.05, warm=1400), 0.1)
for k, t in enumerate(np.arange(0.6, 2.3, 0.1)):
    add("timp", I.timpani(F(45), 0.15 + 0.5 * k / 17, r(), dur=0.5), t)
for m in [45, 52, 57, 60]:
    add("stab", I.brass(F(m), 0.5, 0.9, r(), "stab", fall=-3), T_HOOK)
add("cym", I.cymbal(0.6, r()), T_HOOK)
# B) the holiday tune: vibes melody over plucked chords, 120 bpm, F major, 3.3 .. 9.7
Q = 0.5
MEL = [(0, 1, 77), (1, 0.5, 76), (1.5, 0.5, 77), (2, 1, 79), (3, 1, 81), (4, 1.5, 84), (5.5, 0.5, 81), (6, 1, 79), (7, 1, 77),
       (8, 1, 76), (9, 0.5, 77), (9.5, 0.5, 79), (10, 2, 81)]
CHD = [(41, [65, 69, 72]), (46, [65, 70, 74]), (48, [64, 67, 72]), (41, [65, 69, 72])]
t0 = 3.35
for (b, d, m) in MEL:
    add("vibes", I.vibes(F(m), 0.6, r(), dur=d * Q * 1.8), t0 + b * Q, 0.15)
for k in range(12):
    bass, ch = CHD[(k // 3) % 4]
    t = t0 + k * Q
    if k % 2 == 0: add("tuba", I.brass(F(bass), 0.25, 0.5, r(), "tuba"), t, -0.1)
    for j, m in enumerate(ch): add("pluck", I.pluck(F(m), 0.4, r(), dur=0.4), t + 0.25 + 0.006 * j, 0.25 - 0.15 * j)
# C) 17,000 ft: a creeping cluster, cut by the blow-out
add("pad", I.pad([F(50), F(51), F(57), F(58)], 1.95, 0.6, r(), att=1.2, rel=0.02, warm=1100), 9.72)
# D) the blow-out: stab + cymbal, then urgent low pulses and a snare roll under the gale until "dead"
for m in [38, 45, 50, 53, 57]:
    add("stab", I.brass(F(m), 0.7, 1.0, r(), "stab", fall=-6), T_BLOW)
add("cym", I.cymbal(0.8, r()), T_BLOW)
for k, t in enumerate(np.arange(12.0, T_DEAD - 0.4, 0.25)):
    m = [38, 38, 41, 38, 43, 38, 41, 36][k % 8]
    add("tuba", I.brass(F(m), 0.16, 0.55 + 0.15 * (k % 4 == 0), r(), "tuba"), t)
    if k % 4 == 0: add("timp", I.timpani(F(38), 0.6, r(), dur=0.8), t)
for t, v in I.snare_roll(18.9, 22.5, 0.15, 0.45, r()):
    add("snare", I.snare(v, r(), dur=0.12, buzz=True), t)
for t in [T_BLOW + 2.55, 20.25, 24.15]:
    for m in [50, 57, 62]: add("horn", I.brass(F(m), 0.4, 0.6, r(), "horn"), t)
# E) "they think the captain is dead": everything drops to a hushed D minor pad
add("pad", I.pad([F(50), F(57), F(62), F(65)], 3.4, 0.4, r(), att=0.5, rel=0.8, warm=700), 25.9)
# F) the co-pilot alone: a brass build to the touchdown hit, resolving on "later"
for k, t in enumerate(np.arange(29.15, T_TD, 0.25)):
    add("horn", I.brass(F([50, 52, 53, 55, 57, 58][min(5, k // 1)]), 0.2, 0.4 + 0.08 * k, r(), "horn"), t, 0.1)
for m in [41, 53, 57, 60, 65]:
    add("stab", I.brass(F(m), 0.9, 0.9, r(), "stab"), T_TD)
add("cym", I.cymbal(0.7, r()), T_TD)
add("pad", I.pad([F(53), F(57), F(60), F(65)], 2.4, 0.4, r(), att=0.4, rel=1.0, warm=1200), 31.0)
# G) "Alive.": warm vibes, then a proud little horn on "back to flying"
for k, (b, m) in enumerate([(0, 72), (0.5, 76), (1.0, 79), (1.5, 84), (2.5, 81), (3.0, 79), (3.5, 77), (4.0, 76)]):
    add("vibes", I.vibes(F(m), 0.5, r(), dur=1.0), T_ALIVE + b * 0.5, 0.2 * (k % 2 * 2 - 1))
add("pad", I.pad([F(48), F(55), F(60), F(64)], 3.0, 0.35, r(), att=0.6, rel=0.8, warm=900), T_ALIVE)
for k, m in enumerate([67, 72, 76, 79]):
    add("horn", I.brass(F(m), 0.25 if k < 3 else 0.9, 0.55, r(), "horn"), T_THUMB + 0.1 + k * 0.16)
# H) the investigation: curious pizzicato + tuba, dings on the bolts, a sad tuba fall on "wrong too"
for k, t in enumerate(np.arange(39.1, 51.8, Q)):
    m = [62, 65, 69, 65, 64, 67, 70, 67][k % 8] + (2 if t > 46 else 0)
    add("pluck", I.pluck(F(m), 0.4, r(), dur=0.35, bright=0.7), t, 0.2 if k % 2 else -0.2)
    if k % 2 == 0 and not (T_WRONG - 0.2 < t < T_WRONG + 1.2): add("tuba", I.brass(F(38 + (2 if t > 46 else 0)), 0.2, 0.45, r(), "tuba"), t)
for t, m in [(T_RED, 93), (44.6, 88), (T_SHORT, 91), (T_MATCH + 0.3, 96)]:
    add("glock", I.glock(F(m), 0.75, r()), t)
for k, m in enumerate([45, 44, 43, 40]):
    add("tuba", I.brass(F(m), 0.3 if k < 3 else 0.9, 0.7, r(), "tuba", fall=-1.5 if k == 3 else 0), T_WRONG + 0.1 + k * 0.28)
# I) the cutaway: a slow crescendo (pad + timpani + snare), cut dead when the bolts go
add("pad", I.pad([F(45), F(52), F(57), F(60)], T_FAIL - 52.0, 0.55, r(), att=6.0, rel=0.02, warm=1300), 52.0)
for k, t in enumerate(np.arange(T_PUSH, T_FAIL - 0.05, 0.5 - 0.25 * min(1, (np.arange(T_PUSH, T_FAIL, 0.5).size and 0)))):
    add("timp", I.timpani(F(45), 0.25 + 0.6 * (t - T_PUSH) / (T_FAIL - T_PUSH), r(), dur=0.6), t)
for t, v in I.snare_roll(59.9, T_FAIL - 0.03, 0.1, 0.7, r()):
    add("snare", I.snare(v, r(), dur=0.1), t)
for m in [33, 45, 52, 57]:
    add("stab", I.brass(F(m), 0.6, 1.0, r(), "stab", fall=-8), T_FAIL)
add("cym", I.cymbal(0.9, r()), T_FAIL)
# J) nobody checked: a lone low note, then nothing
add("tuba", I.brass(F(33), 1.6, 0.5, r(), "tuba", fall=-0.5), 63.4)
add("pad", I.pad([F(45), F(48), F(52)], 2.6, 0.3, r(), att=0.4, rel=1.2, warm=600), 63.3)

TARGET = {"vibes": -2.0, "pluck": -4.0, "tuba": -3.0, "glock": -6.0, "stab": -1.5, "timp": -4.0, "cym": -10.0, "pad": -5.0,
          "snare": -7.0, "horn": -4.0}
mix = np.zeros((2, N)); wet = np.zeros(N)
for k, x in tracks.items():
    g = dbg(-20 + TARGET.get(k, -6) - integrated(x))
    mix += x * g; wet += (x * g).mean(0) * 0.18
mix = hp(mix + 0.7 * convolve_st(wet, make_ir(1.3, 7, pre=0.016, hf=1.4)), 30, 2)
# hard silence after the lights go out
cut = np.ones(N); cut[ns(65.3):] = np.linspace(1, 0, N - ns(65.3)) ** 2
mix *= cut
write_wav("music.wav", mix, 24)
print("music.wav", mix.shape[1] / SR, "s, LUFS", round(integrated(mix), 1))

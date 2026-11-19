# Soundtrack for "What If Night Never Came Again?": original whimsical score (C major plucks, glock, music box) that
# turns tense for the heat and the ice, warms up for the ring of sunset and ends on a soft lullaby; synthesized SFX.
# House rules: music ~17 dB under the voice (+3), SFX -6; master -14 LUFS, true peak <= -1 dBTP. Voice starts at 0.25 s.
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "templates", "audio"))
from dsp import SR, ns, tt, rng, dbg, lp, hp, bp, place, pan, fades, colored, read_wav, write_wav, integrated, true_peak, make_ir, convolve_st  # noqa: E402
import instruments as I  # noqa: E402
import sfx_gen as G  # noqa: E402

FPS, TOTAL, VO = 30, 1875, 0.25
DUR = TOTAL / FPS
N = ns(DUR)
T = lambda v: v + VO
BPM = 104
B = 60 / BPM
m2f = I.m2f

mus = np.zeros((2, N))
r = rng(33)
def note(fn, t, *a, p=0.0, g=1.0, **k):
    if t >= DUR - 0.05: return
    x = fn(*a, r=r, **k)
    place(mus, pan(fades(x), p) if x.ndim == 1 else x, t, g)

C, F, G7, Am = [48, 52, 55], [53, 57, 60], [43, 47, 50, 53], [45, 48, 52]
Cm, Ab, Fm, Gm = [48, 51, 55], [44, 48, 51], [41, 44, 48], [43, 46, 50]
MEL = [72, 76, 79, 76, 77, 74, 71, 74, 72, None, 67, None]

def melody(t0, t1, fn=I.glock, vel=0.4, tr=0, p=0.15, step=0.5, **kw):
    t, i = t0, 0
    while t < t1 - 0.05:
        n = MEL[i % len(MEL)]
        if n is not None: note(fn, t, m2f(n + tr), vel=vel, p=p, **kw)
        t += B * step; i += 1

def pads(t0, t1, chords, vel=0.25, beats=4):
    t, k = t0, 0
    while t < t1 - 0.2:
        d = min(B * beats, t1 - t)
        note(I.pad, t, [m2f(n) for n in chords[k % len(chords)]], d, vel=vel, att=0.4, rel=0.5)
        t += d; k += 1

def bounce(t0, t1, chords, vel=0.3, detune=0):
    t, k = t0, 0
    while t < t1 - 0.05:
        ch = chords[(k // 8) % len(chords)]
        note(I.pluck, t, m2f(ch[0] - 12) * (1 + detune * 0.01 * (k % 2)), vel=vel, dur=0.25, p=-0.2)
        if k % 2: note(I.pluck, t, m2f(ch[1 + (k // 2) % 2] + 12), vel=vel * 0.8, dur=0.2, p=0.25)
        t += B / 2; k += 1

# hook (0 - 2.3)
melody(0.0, 2.2, I.musicbox, vel=0.4)
note(I.pad, 0.0, [m2f(n) for n in C], 2.4, vel=0.22, att=0.8, rel=0.6)
# the sun climbs (2.3 - 5.04) and stops
for k in range(12): note(I.glock, T(3.0) + k * 0.15, m2f([60, 64, 67, 72][k % 4] + 12 * (k // 4)), vel=0.3 + 0.03 * k)
note(I.cymbal, T(3.2), vel=0.3, dur=2.0)
note(I.timpani, T(4.79), m2f(36), vel=0.9, dur=2.0); note(I.glock, T(4.79), m2f(96), vel=0.5)
note(I.pad, T(4.85), [m2f(n) for n in [60, 64, 67, 71]], 2.8, vel=0.22, att=0.05, rel=1.0)  # frozen chord
# day one (7.8 - 14.4): happy bounce
bounce(T(7.6), T(14.4), [C, F, G7, C], vel=0.32)
melody(T(7.6), T(14.4), I.glock, vel=0.36)
note(I.cymbal, T(7.75), vel=0.35, dur=1.6)
# body clock (14.4 - 18.4): sparse ticks + low pad
pads(T(14.4), T(18.4), [Am, F], vel=0.22)
for k in range(int(4.0 / 0.5)): note(I.pluck, T(14.5) + k * 0.5, m2f(84), vel=0.18, dur=0.1, bright=0.9)
# grumpy (18.5 - 21.4): detuned bounce
bounce(T(18.5), T(21.4), [Am, Fm], vel=0.26, detune=3)
note(I.timpani, T(19.75), m2f(40), vel=0.6, dur=1.0)
# nature (21.4 - 28.4): curious vibes
melody(T(21.5), T(27.3), I.vibes, vel=0.3, tr=-12, step=1.0, dur=1.2)
pads(T(21.5), T(27.3), [F, C, Am, G7], vel=0.2)
for k, n in enumerate([67, 66, 65, 64]): note(I.brass, T(27.5) + k * 0.28, m2f(n - 24), 0.3 if k < 3 else 0.9, vel=0.4, kind="soft")
# heat (28.5 - 37.1): tense minor pads, rising drone
pads(T(28.5), T(37.1), [Cm, Ab, Fm, Gm], vel=0.3)
for k in range(8): note(I.timpani, T(28.6) + k * B * 2, m2f(36), vel=0.25 + 0.05 * k, dur=0.8)
note(I.pad, T(33.0), [m2f(60), m2f(61)], 4.0, vel=0.18, att=3.0, rel=0.3)
# the crazy part / ice (37.2 - 44.5): sting, cold glassy music box
note(I.cymbal, T(37.2), vel=0.45, dur=2.2); note(I.timpani, T(37.2), m2f(36), vel=0.8, dur=2.0)
melody(T(38.4), T(44.4), I.musicbox, vel=0.32, tr=-1, step=1.0)
pads(T(38.4), T(44.4), [Am, [41, 45, 48, 52]], vel=0.22)
# ring of sunset (44.5 - 52.9): warm swell
pads(T(44.5), T(52.9), [F, C, G7, C], vel=0.3)
melody(T(46.3), T(52.8), I.glock, vel=0.33)
note(I.cymbal, T(45.5), vel=0.3, dur=2.0)
for t, n in [(T(49.4), 48), (T(51.2), 43)]: note(I.brass, t, m2f(n), 1.4, vel=0.35, kind="tuba")
# a normal sunset (53.0 - 58.4): gentle resolution
melody(T(53.0), T(58.3), I.vibes, vel=0.3, step=1.0, dur=1.4)
pads(T(53.0), T(58.4), [F, G7, C], vel=0.24, beats=6)
# lullaby (58.4 - end)
melody(T(58.6), DUR, I.musicbox, vel=0.3, step=1.0)
note(I.pad, T(58.5), [m2f(n) for n in C], DUR - T(58.5), vel=0.16, att=1.0, rel=1.2)

ir = make_ir(1.2, 4)
mus = 0.75 * mus + 0.25 * convolve_st(mus, ir)[:, :N]

# ---------------- sfx ----------------
fx = np.zeros((2, N))
rs = rng(9)
def sx(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    if t >= DUR: return
    place(fx, pan(fades(x), p) if x.ndim == 1 else fades(x), t, g)
def mono(x): return x if x.ndim == 1 else x.mean(axis=0)
def boing(t, g=0.5, f0=180):
    x = tt(0.5); y = np.sin(2 * np.pi * (f0 * x + 40 * np.sin(2 * np.pi * 9 * x) / (2 * np.pi * 9))) * np.exp(-x / 0.15)
    sx(y, t, g)
def tick(t, g=0.3):
    x = tt(0.04); sx(bp(rs.standard_normal(len(x)), 2500, 7000) * np.exp(-x / 0.004), t, g)
def thud(t, g=0.7):
    x = tt(0.3); sx(np.sin(2 * np.pi * (90 * x - 60 * x ** 2)) * np.exp(-x / 0.06) + 0.3 * lp(rs.standard_normal(len(x)), 400) * np.exp(-x / 0.03), t, g)
def hoot(t, g=0.4):
    for k, d in enumerate([0.25, 0.5]):
        x = tt(d); f = 380 * (1 - 0.08 * x / d)
        sx(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x / d) ** 1.5 + 0.05 * lp(rs.standard_normal(len(x)), 900), t + k * 0.35, g)
def buzz(t, dur, g=0.15):
    x = tt(dur); f = 210 + 15 * np.sin(2 * np.pi * 3 * x)
    sx(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 * np.sin(np.pi * x / dur), t, g, 0.2)
def sizzle(t, dur, g=0.2):
    n = ns(dur); sx(hp(colored(n, rs, 0.0), 4000) * (0.5 + 0.5 * np.sin(np.linspace(0, np.pi, n))), t, g)
def crackle(t, dur, g=0.35):
    for k in range(int(dur * 7)): sx(hp(G.wood_crack(rs), 1500) * 0.6, t + rs.uniform(0, dur), g, rs.uniform(-0.5, 0.5))
def sparkle(t, g=0.25):
    for k in range(5): x = tt(0.4); sx(np.sin(2 * np.pi * (2400 + 500 * k) * x) * np.exp(-x / 0.08), t + k * 0.06, g, rs.uniform(-0.6, 0.6))

# golden evening: birds + breeze
sx(mono(G.bird_chirps(2.3, rs, density=0.4)), 0.0, 0.25); sx(mono(G.breeze(2.4, rs, level=0.5)), 0.0, 0.25)
sx(G.whoosh(1.8, rs, peak=0.7, f_lo=200, f_hi=1500), T(3.0), 0.35)
boing(T(4.79), 0.55, 160)
# day one: birds, kids
sx(mono(G.bird_chirps(6.6, rs, density=0.8)), T(7.8), 0.3)
for k in range(3): sx(mono(G.hurrah(rs, 330 + 40 * k, 1.0, kid=True)), T(8.3) + k * 1.4, 0.35, -0.4 + 0.4 * k)
sx(mono(G.babble(3.0, rs, 300, 1.0)), T(10.4), 0.18)
sx(mono(G.hurrah(rs, 360, 1.0, kid=True)), T(11.9), 0.3)
# body clock ticking
for k in range(int(4.0 / 0.25)): tick(T(14.4) + k * 0.25, 0.28)
# grumpy: thud + twinkle
thud(T(19.75), 0.8); sparkle(T(19.85), 0.2)
sx(mono(G.oof(rs, kind="oof")), T(19.8), 0.35, -0.3)
# nature: hoot, buzz, sad flower
hoot(T(22.9), 0.45)
buzz(T(23.8), 1.8, 0.12)
sx(G.whoosh(0.8, rs, peak=0.4, f_lo=300, f_hi=900), T(27.4), 0.2)
# heat: cicada-ish crickets, sizzle, the lake drains
sx(mono(G.crickets(8.5, rs, voices=4)), T(28.6), 0.15)
sizzle(T(29.0), 8.0, 0.12)
sx(mono(G.water_bed(2.5, rs, close=0.6, slosh_rate=0.5)), T(33.9), 0.25)
# ice: cold wind, crackle
sx(mono(G.breeze(7.0, rs, level=1.3, bright=1400)), T(37.4), 0.35)
crackle(T(42.6), 1.8, 0.35)
# ring: crowd murmur + sparkles
sparkle(T(45.5), 0.2)
sx(mono(G.babble(4.0, rs, 260, 1.1)), T(49.3), 0.22)
# sunset: birds, evening crickets, the lantern out
sx(mono(G.bird_chirps(4.0, rs, density=0.3)), T(53.0), 0.2)
sx(mono(G.crickets(DUR - T(56.0), rs, voices=2)), T(56.0), 0.12)
sx(hp(colored(ns(0.5), rs, 0.0), 3000) * np.linspace(1, 0, ns(0.5)) ** 2, T(60.3), 0.12)

# ---------------- mix ----------------
voice = read_wav(os.path.join(HERE, "..", "voice", "voice.wav"))[0]
voice = np.vstack([voice[0], voice[0]]) if voice.shape[0] == 1 else voice
vo = np.zeros((2, N)); place(vo, voice[:, : N - ns(VO)], VO)
env = np.abs(vo[0]); win = ns(0.06)
env = np.convolve(env, np.ones(win) / win, mode="same")
duck = 1 - 0.4 * np.clip(env / (env.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(ns(0.3)) / ns(0.3), mode="same")
v_l = integrated(vo)
mus *= dbg((v_l - 20.0) - integrated(mus) + 3.0)
fx *= dbg((v_l - 18.0) - integrated(fx) - 6.0)
mus *= duck
mix = vo + mus + fx
mix[:, -ns(0.6):] *= np.linspace(1, 0, ns(0.6))
mix *= dbg(-14.0 - integrated(mix))
if true_peak(mix) > -1.0:
    c = dbg(-1.0); mix = np.where(np.abs(mix) > c * 0.8, np.sign(mix) * (c * 0.8 + (np.abs(mix) - c * 0.8) * 0.3), mix)
    mix = np.clip(mix, -c, c)
write_wav(os.path.join(HERE, "mix.wav"), mix)
print(f"voice {v_l:.1f} LUFS | mix {integrated(mix):.1f} LUFS, true peak {true_peak(mix):.1f} dBTP | {mix.shape[1] / SR:.3f} s")

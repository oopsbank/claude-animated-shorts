# Soundtrack for "The Lake That Killed 1,700 People in One Night": original eerie music-box / pad score in D minor +
# synthesized SFX, mixed under the ElevenLabs voice. Music drops out completely for the quiet beat (story.QUIET).
# Same house rules as the water short: music ~17 dB under the voice (+3), SFX -6; master -14 LUFS, true peak <= -1 dBTP.
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "templates", "audio"))
from dsp import SR, ns, tt, rng, dbg, lp, hp, bp, place, pan, fades, colored, read_wav, write_wav, integrated, true_peak, make_ir, convolve_st  # noqa: E402
import instruments as I  # noqa: E402
import sfx_gen as G  # noqa: E402

FPS, TOTAL = 30, 1560
DUR = TOTAL / FPS
N = ns(DUR)
QUIET = (33.75, 39.1)
BPM = 84
B = 60 / BPM
m2f = I.m2f

mus = np.zeros((2, N))
r = rng(21)
def note(fn, t, *a, p=0.0, g=1.0, **k):
    if QUIET[0] - 0.05 < t < QUIET[1]:
        return
    x = fn(*a, r=r, **k)
    place(mus, pan(fades(x), p) if x.ndim == 1 else x, t, g)

DM = [50, 53, 57]; BB = [46, 50, 53]; GM = [43, 46, 50]; A7 = [45, 49, 52, 55]
CH = [DM, BB, GM, A7]
BOX = [74, 77, 81, 77, 76, 74, 73, 76, 74, None, 69, None]   # music-box motif (loops every 12 eighths)

def box(t0, t1, fn=I.musicbox, vel=0.45, tr=0, p=0.2, **kw):
    t, i = t0, 0
    while t < t1 - 0.05:
        n = BOX[i % len(BOX)]
        if n is not None: note(fn, t, m2f(n + tr), vel=vel, p=p, **kw)
        t += B / 2; i += 1

def pads(t0, t1, vel=0.3, bars=2):
    t, k = t0, 0
    while t < t1 - 0.2:
        d = min(B * 4 * bars / 2, t1 - t)
        note(I.pad, t, [m2f(n) for n in CH[k % 4]], d, vel=vel, att=0.6, rel=0.5)
        t += d; k += 1

def tick(t0, t1, vel=0.25):  # light pizzicato ticks for the "explainer" part
    t, k = t0, 0
    while t < t1 - 0.05:
        note(I.pluck, t, m2f(CH[(k // 8) % 4][k % 3] + 12), vel=vel, dur=0.3, p=-0.3 + 0.6 * (k % 2)); t += B / 2; k += 1

# hook (0 - 7.4): music box alone over a low drone, glock sting on "seventeen hundred", drop out on "breathed out"
box(0.0, 6.2, vel=0.42)
note(I.pad, 0.0, [m2f(38), m2f(45)], 7.2, vel=0.22, att=1.0, rel=1.0)
note(I.glock, 2.65, m2f(86), vel=0.55); note(I.glock, 2.65, m2f(81), vel=0.4)
note(I.timpani, 6.25, m2f(38), vel=0.45, dur=2.0)
# silent village (7.5 - 14.2): sparse low pads only
pads(7.6, 14.2, vel=0.22)
note(I.vibes, 11.7, m2f(69), vel=0.3, dur=2.2)
# the crazy part (14.3 - 22.9): pizz ticks + music box an octave down, pads
note(I.cymbal, 14.35, vel=0.25, dur=1.4)
tick(14.4, 22.8, vel=0.28)
box(14.4, 22.8, I.vibes, vel=0.32, tr=-12, dur=1.0)
pads(14.4, 22.8, vel=0.25)
# trigger (22.9 - 26.05): timpani roll rising into the pop
for k in range(int(3.1 / 0.08)):
    t = 22.95 + k * 0.08
    note(I.timpani, t, m2f(38), vel=0.1 + 0.55 * (t - 22.9) / 3.1, dur=0.4)
note(I.pad, 22.9, [m2f(50), m2f(51), m2f(57)], 3.15, vel=0.3, att=1.5, rel=0.2)
note(I.timpani, 26.03, m2f(38), vel=1.0, dur=2.2); note(I.cymbal, 26.03, vel=0.6, dur=2.6)
# eruption + roll downhill (27.1 - 33.7): low brass swells, descending line
for t, n in [(27.4, 38), (29.0, 36), (30.8, 34), (32.3, 33)]:
    note(I.brass, t, m2f(n), 1.5, vel=0.45, kind="tuba"); note(I.pad, t, [m2f(n + 12), m2f(n + 15), m2f(n + 19)], 1.6, vel=0.25, att=0.3, rel=0.4)
# QUIET (33.75 - 39.1): nothing
# the lake turned red (39.1 - 44.6): music box returns, gentle
box(39.4, 44.6, vel=0.38)
pads(39.4, 44.6, vel=0.2)
note(I.glock, 41.75, m2f(81), vel=0.45)
# today (44.7 - end): warmer, ticks again, then the hook motif returns for the loop
tick(44.8, 49.4, vel=0.22)
pads(44.8, 49.5, vel=0.22)
box(49.5, DUR, vel=0.42)
note(I.pad, 49.5, [m2f(38), m2f(45)], DUR - 49.5, vel=0.22, att=0.8, rel=0.1)

ir = make_ir(1.4, 4)
mus = 0.72 * mus + 0.28 * convolve_st(mus, ir)[:, :N]

# ---------------- sfx ----------------
fx = np.zeros((2, N))
rs = rng(8)
def sx(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    place(fx, pan(fades(x), p) if x.ndim == 1 else fades(x), t, g)
def mono(x):
    return x if x.ndim == 1 else x.mean(axis=0)
def lapping(t0, t1, g=0.25):
    sx(mono(G.water_bed(t1 - t0, rs, close=0.4, slosh_rate=0.35)), t0, g)
def rumble(t0, dur, g=0.5, f=120):
    n = ns(dur); e = np.sin(np.linspace(0, np.pi, n)) ** 0.7
    sx(lp(colored(n, rs, -1.5), f) * e, t0, g)
def bloop(t, g=0.4, f0=300):
    x = tt(0.18); y = np.sin(2 * np.pi * (f0 * x + 900 * x ** 2)) * np.exp(-x / 0.05)
    sx(y, t, g, rs.uniform(-0.3, 0.3))

# night lake: crickets + lapping
for a, b in [(0, 7.4), (22.7, 25.9), (27.4, 31.3), (49.5, DUR)]:
    sx(mono(G.crickets(b - a, rs)), a, 0.18); lapping(a, b, 0.2)
bloop(5.6, 0.35, 220); bloop(6.0, 0.4, 260); bloop(6.35, 0.6, 180)
sx(G.whoosh(0.6, rs, peak=0.3, f_lo=150, f_hi=900), 6.3, 0.35)
# silent village: just a thin breeze
sx(mono(G.breeze(6.8, rs, level=0.5)), 7.4, 0.35)
# cutaway: magma rumble + rising bubbles
rumble(14.3, 4.1, 0.55, 90)
sx(mono(G.bubbles(4.0, rs, 8, f_lo=200, f_hi=900)), 14.4, 0.35)
# soda: slosh on the shake, packed bubbles
sx(mono(G.water_bed(1.0, rs, close=1.0, slosh_rate=4.0)), 19.7, 0.5)
sx(mono(G.bubbles(4.0, rs, 14)), 18.4, 0.18)
# landslide
rumble(23.9, 1.9, 0.9, 200)
for k in range(12): sx(G.wood_crack(rs) * 0.5, 23.95 + k * 0.12 + rs.uniform(0, 0.05), 0.25, rs.uniform(-0.4, 0.4))
sx(mono(G.splash_big(rs)), 25.3, 0.6)
# pop + fizz
x = tt(0.25); pop = np.sin(2 * np.pi * (500 * x - 600 * x ** 2)) * np.exp(-x / 0.02) + bp(rs.standard_normal(len(x)), 800, 6000) * np.exp(-x / 0.01)
sx(pop, 26.05, 0.9)
sx(hp(colored(ns(1.2), rs, 0.0), 2500) * np.exp(-tt(1.2) / 0.5), 26.1, 0.35)
# eruption: roar + fizz, then the cloud's low wind
rumble(27.3, 4.5, 1.0, 160)
sx(G.whoosh(2.2, rs, peak=0.25, f_lo=200, f_hi=1600), 27.6, 0.6)
sx(mono(G.bubbles(3.0, rs, 40)), 27.4, 0.3)
sx(mono(G.breeze(4.0, rs, level=1.2, bright=500)), 29.5, 0.45)
# QUIET: faint crickets, the lantern fizzles out, then nothing
sx(mono(G.crickets(2.1, rs, voices=2)), QUIET[0], 0.08)
sx(hp(colored(ns(0.6), rs, 0.0), 3000) * np.linspace(1, 0, ns(0.6)) ** 2, 35.95, 0.12)
# red lake: soft water
lapping(39.1, 44.6, 0.18); sx(mono(G.breeze(5.4, rs, level=0.4)), 39.1, 0.25)
# degassing pipe: jet hiss + a bloop per bubble
sx(hp(colored(ns(4.9), rs, -0.5), 600) * np.minimum(1, np.arange(ns(4.9)) / ns(0.3)), 44.55, 0.12)
for i in range(9): bloop(45.3 + i * 0.55, 0.45, 240 + 30 * (i % 3))

# ---------------- mix ----------------
voice = read_wav(os.path.join(HERE, "..", "voice", "voice.wav"))[0]
voice = np.vstack([voice[0], voice[0]]) if voice.shape[0] == 1 else voice
vo = np.zeros((2, N)); place(vo, voice[:, : N], 0.0)
env = np.abs(vo[0]); win = ns(0.06)
env = np.convolve(env, np.ones(win) / win, mode="same")
duck = 1 - 0.4 * np.clip(env / (env.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(ns(0.3)) / ns(0.3), mode="same")
v_l = integrated(vo)
mus *= dbg((v_l - 20.0) - integrated(mus) + 3.0)
fx *= dbg((v_l - 18.0) - integrated(fx) - 6.0)
mus *= duck
# hard music gate for the quiet beat (short fades)
g = np.ones(N); a, b = ns(QUIET[0]), ns(QUIET[1]); g[a:b] = 0
g = np.convolve(g, np.ones(ns(0.25)) / ns(0.25), mode="same"); mus *= g
mix = vo + mus + fx
mix *= dbg(-14.0 - integrated(mix))
if true_peak(mix) > -1.0:
    c = dbg(-1.0); mix = np.where(np.abs(mix) > c * 0.8, np.sign(mix) * (c * 0.8 + (np.abs(mix) - c * 0.8) * 0.3), mix)
    mix = np.clip(mix, -c, c)
write_wav(os.path.join(HERE, "mix.wav"), mix)
write_wav(os.path.join(HERE, "stem_music.wav"), mus)
write_wav(os.path.join(HERE, "stem_sfx.wav"), fx)
print(f"voice {v_l:.1f} LUFS | mix {integrated(mix):.1f} LUFS, true peak {true_peak(mix):.1f} dBTP | {mix.shape[1] / SR:.3f} s")

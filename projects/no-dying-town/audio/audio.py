# Soundtrack for "The Town Where You're Not Allowed to Die": original creepy-cute music-box waltz in D minor +
# synthesized SFX (Arctic wind, snow steps, freezer door, stamp, digging, propeller plane), mixed under the
# ElevenLabs voice (gain only). Reuses the shared DSP kit and instruments (templates/audio).
# Mix rules as the water short: music ~17 dB under the voice (+3 dB), SFX -6 dB; master -14 LUFS, true peak <= -1 dBTP.
# usage: python audio.py   (writes mix.wav + stems next to this file)
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "templates", "audio"))
from dsp import SR, ns, tt, rng, dbg, lp, hp, bp, place, pan, fades, colored, read_wav, write_wav, integrated, true_peak, make_ir, convolve_st  # noqa: E402
import instruments as I  # noqa: E402
import sfx_gen as G  # noqa: E402

FPS, TOTAL = 30, 1665
DUR = TOTAL / FPS
N = ns(DUR)
BPM = 104
B = 60 / BPM
m2f = I.m2f

# ---------------- music ----------------
mus = np.zeros((2, N))
r = rng(23)

def note(fn, t, *a, p=0.0, g=1.0, **k):
    if t >= DUR - 0.02:
        return
    x = fn(*a, r=r, **k)
    place(mus, pan(fades(x), p) if x.ndim == 1 else x, t, g)

DM = [50, 53, 57]; BB = [46, 50, 53]; GM = [43, 46, 50]; A7 = [45, 49, 52, 55]; F = [41, 45, 48]
CH = [DM, DM, BB, A7, DM, GM, A7, DM]
MEL = [74, 77, 76, 74, 73, 74, 76, None, 72, 74, 70, 69, 70, 73, 74, None]

def waltz(t0, t1, vel=0.45, bass=I.pluck, chord=I.pluck):
    """oom-pah-pah: bass on 1, chord on 2 and 3"""
    t, k = t0, 0
    while t < t1 - 0.05:
        ch = CH[(k // 3) % 8]
        if k % 3 == 0:
            note(bass, t, m2f(ch[0] - 12), vel=vel, dur=0.7, p=-0.1)
        else:
            for j, n in enumerate(ch[1:3]):
                note(chord, t, m2f(n + 12), vel=vel * 0.45, dur=0.35, p=0.25 + 0.05 * j)
        t += B; k += 1

def tune(t0, t1, fn=I.musicbox, vel=0.5, tr=0, p=-0.2, **kw):
    t, i = t0, 0
    while t < t1 - 0.05:
        n = MEL[i % len(MEL)]
        if n is not None:
            note(fn, t, m2f(n + tr), vel=vel, p=p, **kw)
        t += B * (1.5 if i % 4 == 3 else 1.0) * 0.75
        i += 1

# hook (0 - 5): music box alone, a low pluck on "die", a sting on "honestly?"
tune(0.0, 4.9, I.musicbox, vel=0.5)
note(I.pluck, 2.2, m2f(38), vel=0.6, dur=1.2)
note(I.glock, 3.0, m2f(81), vel=0.45); note(I.glock, 3.0, m2f(74), vel=0.35)
# town (5 - 11): the waltz with glock tune; tuba "bwomp" on the polar bear
waltz(5.0, 10.9, vel=0.42)
tune(5.0, 10.9, I.glock, vel=0.3, dur=1.0)
note(I.brass, 9.95, m2f(38), 0.5, vel=0.5, kind="tuba"); note(I.brass, 10.45, m2f(37), 0.6, vel=0.5, kind="tuba", fall=-3)
# crazy part (11 - 16): timpani hit, cold pad, deep pulse
note(I.timpani, 11.0, m2f(38), vel=0.75, dur=2.0); note(I.cymbal, 11.0, vel=0.3, dur=2.4, bright=0.6)
note(I.pad, 11.1, [m2f(50), m2f(57), m2f(62)], 4.8, vel=0.32, att=0.8, rel=0.6)
for k in range(int(4.8 / (2 * B))): note(I.pluck, 11.2 + k * 2 * B, m2f(26), vel=0.5, dur=1.0)
note(I.vibes, 13.8, m2f(86), vel=0.35, dur=2.0)
# 1918 (16 - 21.5): slow music box, then near silence for the miners
tune(16.0, 18.4, I.musicbox, vel=0.35, tr=-12)
note(I.pad, 18.5, [m2f(50), m2f(53), m2f(57)], 3.0, vel=0.22, att=1.0, rel=0.8)
# creepy (21.5 - 31): vibes tremolo + pad, freezer door, little sting on "neighbor"
note(I.pad, 21.5, [m2f(46), m2f(50), m2f(53)], 4.6, vel=0.3, att=0.6, rel=0.5)
note(I.pad, 26.0, [m2f(49), m2f(52), m2f(57)], 5.0, vel=0.3, att=0.3, rel=0.8)
for k in range(int(9.0 / B)): note(I.vibes, 21.6 + k * B, m2f([62, 65, 61, 64][k % 4]), vel=0.22, dur=1.2, trem_depth=0.5)
note(I.glock, 26.6, m2f(86), vel=0.5); note(I.glock, 26.6, m2f(81), vel=0.35)
for t, n in [(30.1, 74), (30.35, 73)]: note(I.pluck, t, m2f(n), vel=0.6, dur=0.4)
# 1950 / 1998 (31 - 39.5): stamp hit, march of the scientists, toll hit
note(I.timpani, 32.4, m2f(38), vel=0.9, dur=1.6); note(I.snare, 32.4, vel=0.7, dur=0.4)
waltz(33.5, 39.4, vel=0.38)
for k in range(int((39.4 - 33.5) / B)): note(I.snare, 33.5 + k * B, vel=0.16 + 0.1 * (k % 3 == 0), dur=0.2, p=0.15)
note(I.timpani, 38.05, m2f(33), vel=1.0, dur=2.0); note(I.cymbal, 38.05, vel=0.55, dur=2.4)
# mainland (39.5 - 49): lighter, major-ish (F), ticket ding
waltz(39.6, 48.9, vel=0.36)
tune(39.6, 48.9, I.pluck, vel=0.32, tr=-12 + 3, dur=0.6)
note(I.glock, 43.9, m2f(84), vel=0.6); note(I.glock, 43.9, m2f(89), vel=0.4)
# counters (49 - 52): two dings
note(I.glock, 49.95, m2f(81), vel=0.6); note(I.vibes, 49.95, m2f(69), vel=0.4)
note(I.glock, 51.4, m2f(74), vel=0.6); note(I.vibes, 51.4, m2f(62), vel=0.4)
note(I.pad, 49.2, [m2f(50), m2f(53), m2f(57), m2f(62)], 3.0, vel=0.25, att=0.4, rel=0.5)
# loop (52.1 - end): music box hook again, pickup into frame 0
tune(52.1, DUR - 0.1, I.musicbox, vel=0.5)
note(I.pluck, 54.4, m2f(38), vel=0.6, dur=1.0)

ir = make_ir(1.4, 3)
mus = 0.75 * mus + 0.25 * convolve_st(mus, ir)[:, :N]

# ---------------- sfx ----------------
fx = np.zeros((2, N))
rs = rng(8)
def sx(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    if t >= DUR:
        return
    place(fx, pan(fades(x), p) if x.ndim == 1 else fades(x), t, g)

def crunch(t, g=0.18, p=0.0):  # a step in snow: short band-passed noise with a gritty grain
    n = ns(0.12); e = np.exp(-np.arange(n) / ns(0.03))
    x = bp(rs.standard_normal(n) * (rs.random(n) < 0.35), 900, 5000) * e
    sx(x, t, g, p)

def steps(t0, t1, rate=1.8, g=0.16, p=0.0):
    t = t0
    while t < t1: crunch(t + rs.uniform(0, 0.02), g, p); t += 1 / rate

def stamp(t, g=0.7):
    t_ = tt(0.22)
    x = np.sin(2 * np.pi * 80 * t_) * np.exp(-t_ / 0.04) + bp(rs.standard_normal(len(t_)), 300, 2500) * np.exp(-t_ / 0.012) * 0.6
    sx(x, t, g)

def growl(t, dur=1.0, g=0.4):
    n = ns(dur); e = np.sin(np.linspace(0, np.pi, n)) ** 0.7
    am = 1 + 0.6 * np.sin(2 * np.pi * 23 * np.arange(n) / SR)
    sx(lp(colored(n, rs, -1.0), 260) * am * e, t, g, 0.4)

def engine(t0, dur, rise=0.0, g=0.3):
    n = ns(dur); k = np.arange(n) / SR
    f = 28 + 10 * rise * np.clip((k - 2.0) / max(dur - 2.0, 0.1), 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    buzz = np.sign(np.sin(ph)) * 0.3 + np.sin(2 * ph) * 0.3
    x = lp(buzz + 0.3 * colored(n, rs, -1.0), 700) * np.minimum(1, k / 0.8)
    sx(x, t0, g, -0.2)

# Arctic wind under every outdoor shot (quiet in the 1918 miners beat)
for t0, t1, lv in [(0, 16.0, 0.8), (16.0, 18.4, 0.6), (18.4, 21.4, 0.35), (25.5, 49, 0.7), (49, DUR, 0.8)]:
    sx(G.breeze(t1 - t0, rs, level=lv, bright=700), t0, 0.5)
# ice: low hollow rumble under the cutaways
for t0, d in [(12.2, 3.8), (21.4, 4.1)]:
    n = ns(d); sx(lp(colored(n, rs, -1.5), 140) * np.sin(np.linspace(0, np.pi, n)), t0, 0.5)
    sx(G.creak(d * 0.6, rs, rate0=30, rate1=60, rough=0.3), t0 + 0.6, 0.15, 0.3)
# town: walkers, the bear
steps(5.0, 10.2, 1.9, 0.14, -0.2); steps(5.4, 11.0, 1.6, 0.08, 0.3)
growl(10.0, 1.1, 0.45)
# 1918: miners shuffle; a cough-like puff on "flu"
steps(16.0, 18.4, 1.3, 0.1)
# freezer: door creak + hum + cold breath; germs giggle-squeak
sx(G.creak(0.9, rs, rate0=60, rate1=140, rough=0.2), 26.25, 0.5, -0.2)
hum = np.sin(2 * np.pi * 50 * tt(4.5)) * 0.006 + np.sin(2 * np.pi * 100 * tt(4.5)) * 0.003
sx(hum, 26.4, 1.0)
sx(G.whoosh(1.0, rs, peak=0.3, f_lo=600, f_hi=4000), 26.4, 0.45)
for t in [28.2, 28.45, 28.7]: sx(G.clink(rs, f0=2600, dur=0.08, bright=0.3), t, 0.3, 0.2)
# 1950: CLOSED stamp
stamp(32.4)
# 1998: digging thuds, the germ popping out, the toll
for k in range(9): sx(G.hammer_hit(rs, big=0.5), 33.6 + k * 0.62, 0.25, 0.2 if k % 2 else -0.2)
sx(G.whoosh(0.6, rs, peak=0.2), 37.2, 0.5)
# airfield: ticket print, steps, propeller plane taxiing and taking off
for k in range(4): sx(G.clink(rs, f0=3400, dur=0.05, bright=0.6), 43.75 + k * 0.05, 0.2)
steps(39.6, 42.5, 1.4, 0.1); steps(45.0, 46.7, 2.0, 0.12)
engine(44.2, 5.0, rise=1.0, g=0.35)
sx(G.whoosh(2.2, rs, peak=0.5, f_lo=200, f_hi=1500), 47.3, 0.6, -0.5)
# counters: two soft clicks
for t in [49.9, 51.35]: sx(G.clink(rs, f0=1800, dur=0.1, bright=0.4), t, 0.4)
# loop: same road ambience
steps(52.2, DUR, 0.6, 0.06)

# ---------------- mix ----------------
voice = read_wav(os.path.join(HERE, "..", "voice", "voice.wav"))[0]
voice = np.vstack([voice[0], voice[0]]) if voice.shape[0] == 1 else voice
vo = np.zeros((2, N)); place(vo, voice[:, : N], 0.0)
env = np.abs(vo[0]); win = ns(0.06)
env = np.convolve(env, np.ones(win) / win, mode="same")
duck = 1 - 0.45 * np.clip(env / (env.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(ns(0.3)) / ns(0.3), mode="same")
v_l = integrated(vo)
mus *= dbg((v_l - 20.0) - integrated(mus) + 3.0)
fx *= dbg((v_l - 18.0) - integrated(fx) - 6.0)
mus *= duck
mix = vo + mus + fx
mix *= dbg(-14.0 - integrated(mix))
if true_peak(mix) > -1.0:
    c = dbg(-1.0); mix = np.where(np.abs(mix) > c * 0.8, np.sign(mix) * (c * 0.8 + (np.abs(mix) - c * 0.8) * 0.3), mix)
    mix = np.clip(mix, -c, c)
write_wav(os.path.join(HERE, "mix.wav"), mix)
write_wav(os.path.join(HERE, "stem_music.wav"), mus)
write_wav(os.path.join(HERE, "stem_sfx.wav"), fx)
print(f"voice {v_l:.1f} LUFS | mix {integrated(mix):.1f} LUFS, true peak {true_peak(mix):.1f} dBTP | {mix.shape[1] / SR:.3f} s")
